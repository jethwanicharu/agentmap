import os
import requests
import chromadb

# ─── Constants ───────────────────────────────────────────
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_MODEL}"

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

# ─── Singleton ───────────────────────────────────────────
_client = None
_collection = None
_collections = {}

# ─── HF API Embedding ────────────────────────────────────
def get_embeddings(texts: list[str]) -> list[list[float]]:
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    response = requests.post(
        HF_API_URL,
        headers=headers,
        json={"inputs": texts, "options": {"wait_for_model": True}}
    )

    print(f"[HF API] Status: {response.status_code}")
    print(f"[HF API] Response: {response.text[:200]}")

    if response.status_code != 200:
        raise Exception(f"HF API error: {response.status_code} — {response.text}")

    return response.json()

# ─── Chroma Client ───────────────────────────────────────
def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        print("[SINGLETON] Chroma client created ✓")
    return _client

def get_collection():
    global _client, _collection
    if _collection is not None:
        print("[SINGLETON] Reusing collection ✓")
        return _collection
    _client = get_chroma_client()
    _collection = _client.get_or_create_collection(name="codebase")
    print("[SINGLETON] Collection created ✓")
    return _collection

def get_or_create_collection(client=None, collection_name="codebase"):
    global _collections
    if collection_name not in _collections:
        c = _client or get_chroma_client()
        _collections[collection_name] = c.get_or_create_collection(name=collection_name)
        print(f"[SINGLETON] Collection '{collection_name}' created ✓")
    else:
        print(f"[SINGLETON] Reusing collection '{collection_name}' ✓")
    return _collections[collection_name]

# ─── Add Chunks ──────────────────────────────────────────
def add_chunks(chunks: list[dict], batch_size: int = 32):
    collection = get_collection()

    texts = [c["text"] for c in chunks]
    ids = [
        c.get("id") or c.get("chunk_id") or f"chunk_{i}"
        for i, c in enumerate(chunks)
    ]
    metadatas = [c.get("metadata", {}) for c in chunks]

    print(f"[INDEX] Total chunks: {len(chunks)}, batch_size={batch_size}")

    for i in range(0, len(texts), batch_size):
        embeddings = get_embeddings(texts[i:i+batch_size])
        collection.add(
            documents=texts[i:i+batch_size],
            embeddings=embeddings,
            ids=ids[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )
        print(f"[INDEX] Batch done: {min(i+batch_size, len(texts))}/{len(chunks)}")

    print(f"[DONE] Added {len(chunks)} chunks ✓")

def add_chunks_to_store(collection, chunks, batch_size=32):
    texts = [c["text"] for c in chunks]
    ids = [
        c.get("id") or c.get("chunk_id") or f"chunk_{i}"
        for i, c in enumerate(chunks)
    ]
    metadatas = [c.get("metadata") or c.get("meta") or {} for c in chunks]

    for i in range(0, len(texts), batch_size):
        embeddings = get_embeddings(texts[i:i+batch_size])
        collection.add(
            documents=texts[i:i+batch_size],
            embeddings=embeddings,
            ids=ids[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )
        print(f"[INDEX] Batch done: {min(i+batch_size, len(texts))}/{len(texts)}")

    print(f"[DONE] Added {len(chunks)} chunks ✓")

# ─── Query ───────────────────────────────────────────────
def query_chunks(query: str, n_results: int = 5) -> list[dict]:
    collection = get_collection()
    query_embedding = get_embeddings([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    return [
        {"text": doc, "metadata": results["metadatas"][0][i]}
        for i, doc in enumerate(results["documents"][0])
    ]