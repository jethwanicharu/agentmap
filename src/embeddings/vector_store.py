import os
import math
import requests
import chromadb

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
_client = None
_collections = {}

GEMINI_MODEL = "gemini-embedding-001"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:batchEmbedContents"
EMBED_DIM = 768


def _normalize(vec):
    n = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / n for x in vec]


def get_embeddings(texts: list[str]) -> list[list[float]]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY missing (env me add karo)")

    body = {
        "requests": [
            {
                "model": f"models/{GEMINI_MODEL}",
                "content": {"parts": [{"text": t}]},
                "outputDimensionality": EMBED_DIM,
            }
            for t in texts
        ]
    }
    response = requests.post(
        GEMINI_URL,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json=body,
        timeout=60,
    )
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.status_code} — {response.text}")

    return [_normalize(e["values"]) for e in response.json()["embeddings"]]


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        print("[SINGLETON] Chroma client created ✓")
    return _client


def get_or_create_collection(client=None, collection_name="codebase"):
    if collection_name not in _collections:
        c = client or get_chroma_client()
        _collections[collection_name] = c.get_or_create_collection(name=collection_name)
    return _collections[collection_name]


def add_chunks_to_store(collection, chunks, batch_size=32):
    texts = [c["text"] for c in chunks]
    ids = [
        c.get("id") or c.get("chunk_id") or f"chunk_{i}"
        for i, c in enumerate(chunks)
    ]
    metadatas = [c.get("metadata") or c.get("meta") or {} for c in chunks]

    print(f"[INDEX] Total chunks: {len(chunks)}, batch_size={batch_size}")

    for i in range(0, len(texts), batch_size):
        embeddings = get_embeddings(texts[i:i + batch_size])
        collection.add(
            documents=texts[i:i + batch_size],
            embeddings=embeddings,
            ids=ids[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
        )
        print(f"[INDEX] Batch done: {min(i + batch_size, len(texts))}/{len(chunks)}")