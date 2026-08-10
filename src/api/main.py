from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.ingestion.github_fetcher import fetch_repo_files
from src.chunking.chunker import chunk_all_files
from src.embeddings.vector_store import get_chroma_client, get_or_create_collection, add_chunks_to_store
from src.agents.graph import run_agent

app = FastAPI(title="AgentMap API", root_path="/")

# TODO: tighten this to Vercel domain once frontend phase start ho (Backend Plan item 3)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ek hi Chroma client poore server process ke liye — collections disk pe
# ./chroma_db mein persist hoti hain, repo name se keyed. Isliye /ask ko
# same request mein /index chalne ki zaroorat nahi.
_chroma_client = get_chroma_client()


class IndexRequest(BaseModel):
    repo_name: str  # "owner/repo" format
    github_token: str = None


class AskRequest(BaseModel):
    repo_name: str
    question: str
    n_results: int = 5


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/index")
def index_repo(req: IndexRequest):
    if "/" not in req.repo_name:
        raise HTTPException(status_code=400, detail="repo_name must be in 'owner/repo' format")

    try:
        files = fetch_repo_files(req.repo_name, github_token=req.github_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch repo: {e}")

    if not files:
        raise HTTPException(status_code=404, detail="No matching files found in this repo")

    chunks = chunk_all_files(files)
    collection_name = req.repo_name.replace("/", "_")
    collection = get_or_create_collection(_chroma_client, collection_name=collection_name)
    add_chunks_to_store(collection, chunks)

    return {
        "repo_name": req.repo_name,
        "collection_name": collection_name,
        "file_count": len(files),
        "chunk_count": len(chunks),
    }


@app.post("/ask")
def ask_question(req: AskRequest):
    collection_name = req.repo_name.replace("/", "_")
    collection = get_or_create_collection(_chroma_client, collection_name=collection_name)

    if collection.count() == 0:
        raise HTTPException(
            status_code=400,
            detail=f"'{req.repo_name}' isn't indexed yet. Call /index first.",
        )

    result = run_agent(collection, req.question, n_results=req.n_results)
    return result