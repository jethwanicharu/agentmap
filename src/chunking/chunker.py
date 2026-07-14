def chunk_file(file_path: str, content: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Splits a single file's content into overlapping chunks.
    Simple character-based chunking (upgrade to AST-based later).
    
    Returns: list of dicts with {path, chunk_text, chunk_index}
    """
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(content):
        end = start + chunk_size
        chunk_text = content[start:end]

        chunks.append({
            "path": file_path,
            "chunk_text": chunk_text,
            "chunk_index": chunk_index
        })

        chunk_index += 1
        start = end - overlap  # overlap so we don't lose context at boundaries

    return chunks


def chunk_all_files(files_data: list, chunk_size: int = 1000, overlap: int = 200):
    """
    files_data: list of {path, content} from github_fetcher
    Returns: flat list of all chunks across all files
    """
    all_chunks = []
    for file in files_data:
        file_chunks = chunk_file(file["path"], file["content"], chunk_size, overlap)
        all_chunks.extend(file_chunks)
    return all_chunks


if __name__ == "__main__":
    # quick test with dummy content
    dummy_content = "def hello():\n    print('hello world')\n" * 50
    chunks = chunk_file("test.py", dummy_content)
    print(f"Created {len(chunks)} chunks")
    print(chunks[0])