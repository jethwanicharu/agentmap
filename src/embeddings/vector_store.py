import chromadb
from chromadb.utils import embedding_functions

# HuggingFace sentence-transformers model — free, runs locally
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def get_chroma_client(persist_directory: str = "./chroma_db"):
    """
    Creates a persistent ChromaDB client — data survives across runs.
    """
    client = chromadb.PersistentClient(path=persist_directory)
    return client


def get_or_create_collection(client, collection_name: str = "codebase"):
    """
    Sets up the embedding function and creates/fetches a collection.
    """
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )
    return collection


def add_chunks_to_store(collection, chunks: list):
    """
    chunks: list of {path, chunk_text, chunk_index} from chunker
    Adds them to ChromaDB with metadata for source tracking.
    """
    documents = []
    metadatas = []
    ids = []

    for chunk in chunks:
        unique_id = f"{chunk['path']}::chunk_{chunk['chunk_index']}"
        documents.append(chunk["chunk_text"])
        metadatas.append({
            "path": chunk["path"],
            "chunk_index": chunk["chunk_index"]
        })
        ids.append(unique_id)

    # ChromaDB handles embedding generation internally via embedding_fn
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Added {len(documents)} chunks to vector store")


def query_store(collection, query_text: str, n_results: int = 5):
    """
    Retrieves top-n most similar chunks for a given query.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results


if __name__ == "__main__":
    # quick test
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    dummy_chunks = [
        {"path": "test.py", "chunk_text": "def calculate_total(items): return sum(items)", "chunk_index": 0},
        {"path": "utils.py", "chunk_text": "def format_currency(amount): return f'${amount:.2f}'", "chunk_index": 0},
    ]
    add_chunks_to_store(collection, dummy_chunks)

    results = query_store(collection, "how do I sum a list of numbers?")
    print(results)