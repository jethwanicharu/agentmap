def chunk_file(path: str, content: str, chunk_size: int = 1000, overlap: int = 200):
    """Split a single file's content into overlapping character-based chunks."""
    chunks = []
    start = 0
    content_len = len(content)

    if content_len == 0:
        return chunks

    while start < content_len:
        end = start + chunk_size
        chunk_text = content[start:end]
        chunks.append({
            "text": chunk_text,
            "metadata": {
                "path": path,
                "start": start,
                "end": min(end, content_len),
            }
        })
        start += (chunk_size - overlap)

    return chunks


def chunk_all_files(files_data: list, chunk_size: int = 1000, overlap: int = 200):
    import psutil, os
    def log_memory(step):
        mem_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        print(f"[MEMORY] {step}: {mem_mb:.2f} MB")
    log_memory("Before chunking")
    all_chunks = []
    for file in files_data:
        file_chunks = chunk_file(file["path"], file["content"], chunk_size, overlap)
        all_chunks.extend(file_chunks)
    log_memory(f"After chunking ({len(all_chunks)} total chunks)")
    return all_chunks

# def chunk_all_files(files_data: list, chunk_size: int = 1000, overlap: int = 200):
#     import psutil, os
#     def log_memory(step):
#         mem_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
#         print(f"[MEMORY] {step}: {mem_mb:.2f} MB")

#     log_memory("Before chunking")
#     all_chunks = []
#     for file in files_data:
#         file_chunks = chunk_file(file["path"], file["content"], chunk_size, overlap)
#         all_chunks.extend(file_chunks)
#     log_memory(f"After chunking ({len(all_chunks)} total chunks)")
#     return all_chunks