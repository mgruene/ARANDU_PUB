# modules/chroma_client.py
# Simpler, robuster HTTP-Client für Chroma 0.6.x – ohne Telemetrie & ohne Legacy-Settings.

from typing import List, Dict, Any
from urllib.parse import urlparse
import chromadb

try:
    from chromadb import HttpClient as _HttpClient
except Exception:
    _HttpClient = None

class ChromaWrapper:
    def __init__(self, chroma_cfg: Dict[str, Any]):
        url = chroma_cfg.get("server_url", "http://chroma:8000")
        parsed = urlparse(url)
        host = parsed.hostname or "chroma"
        port = parsed.port or 8000

        if _HttpClient:
            # HttpClient nutzt die neuen Defaults; Telemetrie ist serverseitig bereits aus
            self.client = _HttpClient(host=host, port=port)
        else:
            # Fallback (sollte bei 0.6.x selten nötig sein)
            from chromadb.config import Settings
            self.client = chromadb.Client(Settings(
                chroma_api_impl="rest",
                chroma_server_host=host,
                chroma_server_http_port=port,
                anonymized_telemetry=False,
            ))

    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(name=name)

    def upsert(self, collection_name: str,
               documents: List[str],
               metadatas: List[Dict[str, Any]],
               ids: List[str],
               embeddings: List[List[float]] = None):
        n = len(ids)
        if not (len(documents) == len(metadatas) == n and (embeddings is None or len(embeddings) == n)):
            raise ValueError(f"Upsert-Arrays müssen gleiche Länge haben: ids={len(ids)}, docs={len(documents)}, metas={len(metadatas)}, embeds={0 if embeddings is None else len(embeddings)}")
        if embeddings is not None and any((not v or len(v) == 0) for v in embeddings):
            raise ValueError("Mindestens ein Embedding-Vektor ist leer.")
        col = self.get_or_create_collection(collection_name)
        if embeddings is not None:
            col.upsert(documents=documents, metadatas=metadatas, ids=ids, embeddings=embeddings)
        else:
            col.upsert(documents=documents, metadatas=metadatas, ids=ids)
        return {"ok": True, "count": n}
