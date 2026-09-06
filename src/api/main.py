from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
import httpx
import re

from src.ingestion.github_fetcher import fetch_repo_files
from src.chunking.chunker import chunk_all_files
from src.embeddings.vector_store import get_chroma_client, get_or_create_collection, add_chunks_to_store
from src.agents.graph import run_agent

app = FastAPI(title="AgentMap API", root_path="/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_chroma_client = get_chroma_client()




ERROR_CODES = {
    "INVALID_REPO_FORMAT":  "Repo must be in 'owner/repo' format (e.g. 'vercel/next.js')",
    "INVALID_REPO_NAME":    "Repo name contains invalid characters",
    "REPO_NOT_FOUND":       "Repository not found. Check the owner/repo name.",
    "REPO_PRIVATE":         "This repo is private. Provide a valid GitHub token.",
    "BAD_TOKEN":            "GitHub token is invalid or expired.",
    "RATE_LIMITED":         "GitHub API rate limit hit. Wait a few minutes or use a token.",
    "GITHUB_UNREACHABLE":   "Could not reach GitHub. Check your internet connection.",
    "EMPTY_REPO":           "No supported files found in this repo.",
    "NOT_INDEXED":          "This repo hasn't been indexed yet. Call /index first.",
    "CHUNKING_FAILED":      "Failed to process repo files.",
    "AGENT_ERROR":          "Agent failed to process the question.",
    "QUESTION_EMPTY":       "Question cannot be empty.",
}

def api_error(code: str, status: int, detail: str = None) -> HTTPException:
    """Standardized error response with code + human message."""
    return HTTPException(
        status_code=status,
        detail={
            "error_code": code,
            "message": detail or ERROR_CODES.get(code, "Unknown error"),
        }
    )




class IndexRequest(BaseModel):
    repo_name: str
    github_token: str = None

    @field_validator("repo_name")
    @classmethod
    def validate_repo_name(cls, v: str) -> str:
        v = v.strip()
        if "/" not in v:
            raise ValueError("INVALID_REPO_FORMAT")
        parts = v.split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("INVALID_REPO_FORMAT")
        pattern = r'^[a-zA-Z0-9_.\-]+/[a-zA-Z0-9_.\-]+$'
        if not re.match(pattern, v):
            raise ValueError("INVALID_REPO_NAME")
        return v


class AskRequest(BaseModel):
    repo_name: str
    question: str
    n_results: int = 5

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("QUESTION_EMPTY")
        return v.strip()




@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions — never expose raw tracebacks."""
    return JSONResponse(
        status_code=500,
        content={"detail": {"error_code": "INTERNAL_ERROR", "message": str(exc)}},
    )



def parse_github_error(exc: Exception, token: str = None) -> HTTPException:
    """
    Convert raw GitHub/httpx exceptions into user-friendly API errors.
    Handles: 401, 403 (rate limit vs auth), 404, network issues.
    """
    err_str = str(exc).lower()

    if any(k in err_str for k in ["connect", "timeout", "network", "name resolution", "unreachable"]):
        return api_error("GITHUB_UNREACHABLE", 503)

   
    if "401" in err_str or "bad credentials" in err_str:
        return api_error("BAD_TOKEN", 401)

    
    if "403" in err_str:
        if "rate limit" in err_str or "x-ratelimit" in err_str:
            return api_error("RATE_LIMITED", 429)
        if not token:
            return api_error("REPO_PRIVATE", 403,
                "This may be a private repo. Provide a GitHub token to access it.")
        return api_error("BAD_TOKEN", 403, "Access denied. Check your token's permissions.")

    
    if "404" in err_str or "not found" in err_str:
        return api_error("REPO_NOT_FOUND", 404)

    
    return api_error("GITHUB_UNREACHABLE", 502, f"GitHub error: {exc}")




@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/index")
def index_repo(req: IndexRequest):
    #  Fetch files from GitHub
    try:
        files = fetch_repo_files(req.repo_name, github_token=req.github_token)
    except httpx.HTTPStatusError as e:
        raise parse_github_error(e, req.github_token)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
        raise api_error("GITHUB_UNREACHABLE", 503)
    except Exception as e:
        raise parse_github_error(e, req.github_token)

    #  Empty repo guard
    if not files:
        raise api_error("EMPTY_REPO", 404,
            f"No supported files found in '{req.repo_name}'. "
            "Make sure the repo has code files (py, js, ts, etc.)")

    # Chunk files
    try:
        chunks = chunk_all_files(files)
    except Exception as e:
        raise api_error("CHUNKING_FAILED", 500, f"File processing error: {e}")

    if not chunks:
        raise api_error("EMPTY_REPO", 404,
            "Files were found but could not be chunked. The repo may only contain binary files.")

    #  Store in vector DB
    try:
        collection_name = req.repo_name.replace("/", "_")
        collection = get_or_create_collection(_chroma_client, collection_name=collection_name)
        add_chunks_to_store(collection, chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error_code": "STORAGE_ERROR",
            "message": f"Vector store error: {e}",
        })

    return {
        "success": True,
        "repo_name": req.repo_name,
        "collection_name": collection_name,
        "file_count": len(files),
        "chunk_count": len(chunks),
        "message": f"Successfully indexed {len(files)} files ({len(chunks)} chunks) from '{req.repo_name}'",
    }


@app.post("/ask")
def ask_question(req: AskRequest):
    
    if "/" not in req.repo_name:
        raise api_error("INVALID_REPO_FORMAT", 400)

    collection_name = req.repo_name.replace("/", "_")

   
    try:
        collection = get_or_create_collection(_chroma_client, collection_name=collection_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error_code": "STORAGE_ERROR",
            "message": f"Vector store error: {e}",
        })

    if collection.count() == 0:
        raise api_error(
            "NOT_INDEXED", 400,
            f"'{req.repo_name}' isn't indexed yet. "
            "Submit this repo via /index before asking questions."
        )

    #  Run agent
    try:
        result = run_agent(collection, req.question, n_results=req.n_results)
    except Exception as e:
        raise api_error("AGENT_ERROR", 500, f"Agent error: {e}")

    return result



import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

STATIC_DIR = "out"

if os.path.isdir(STATIC_DIR):
    app.mount("/_next", StaticFiles(directory=f"{STATIC_DIR}/_next"), name="next-static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(STATIC_DIR, full_path)

        if os.path.isfile(file_path):
            return FileResponse(file_path)

        index_path = os.path.join(STATIC_DIR, full_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)

        return FileResponse(os.path.join(STATIC_DIR, "index.html"))