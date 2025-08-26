# modules/chunking.py
# Einfache char-basierte Chunking-Strategie mit Überlappung
from typing import List, Dict, Any

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    chunks = []
    if chunk_size <= 0:
        return [{"text": text, "index": 0}]
    start = 0
    idx = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end]
        chunks.append({"text": chunk, "index": idx})
        idx += 1
        if end == n:
            break
        start = end - overlap if overlap > 0 else end
    return chunks
