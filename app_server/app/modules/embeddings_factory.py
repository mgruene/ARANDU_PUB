# app/modules/embeddings_factory.py
# Robuster direkter Ollama-Embeddings-Client:
# - Erst Versuch mit "prompt" (stabil in Praxis/Docs), Fallback auf "input"
# - Akzeptiert Antwortschema {"embedding":[...]} und {"embeddings":[[...], ...]}
# - Unterstützt Chunking langer Texte + Aggregation (mean/sum)
# - Detailliertes Logging (strukturierte Felder)
#
# Änderung ggü. Vorversion:
# - Import-Pfad korrigiert: from app.modules.logging_setup import get_logger

from typing import Dict, List, Any, Callable
import requests

from app.modules.logging_setup import get_logger  # <-- Import konsistent gemacht

log = get_logger("embeddings_factory")

def _mean(vectors: List[List[float]]) -> List[float]:
    if not vectors:
        return []
    n = len(vectors[0]) if vectors[0] else 0
    if n == 0:
        return []
    acc = [0.0] * n
    k = 0
    for v in vectors:
        if not v or len(v) != n:
            return []
        for i, x in enumerate(v):
            acc[i] += float(x)
        k += 1
    return [x / max(1, k) for x in acc]

def _sum(vectors: List[List[float]]) -> List[float]:
    if not vectors:
        return []
    n = len(vectors[0]) if vectors[0] else 0
    if n == 0:
        return []
    acc = [0.0] * n
    for v in vectors:
        if not v or len(v) != n:
            return []
        for i, x in enumerate(v):
            acc[i] += float(x)
    return acc

class EmbeddingsFactory:
    def __init__(self, app_cfg: Dict[str, Any], embedding_cfg: Dict[str, Any]):
        self.base = app_cfg["ollama"]["base_url"].rstrip("/")
        self.model = embedding_cfg["model"]
        self.max_timeout = int(app_cfg.get("timeouts", {}).get("embeddings_seconds", 120))
        self.normalize = embedding_cfg.get("normalize", True)  # Platzhalter für evtl. spätere Normalisierung

    def _parse_vec(self, j: Dict[str, Any]) -> List[float]:
        # Schema 1: {"embedding": [...]}
        emb = j.get("embedding")
        if isinstance(emb, list):
            return emb
        # Schema 2: {"embeddings":[ [...], ... ]}
        embs = j.get("embeddings")
        if isinstance(embs, list) and embs and isinstance(embs[0], list):
            return embs[0]
        return []

    def _request_embed(self, text: str, prefer_prompt: bool = True) -> List[float]:
        url = f"{self.base}/api/embeddings"
        primary = {"model": self.model, "prompt": text} if prefer_prompt else {"model": self.model, "input": text}
        try:
            r = requests.post(url, json=primary, timeout=self.max_timeout)
            if r.status_code != 200:
                log.error("ollama_http_error", extra={"extra_fields": {
                    "status": r.status_code, "body": (r.text or "")[:200], "model": self.model, "phase": "primary"
                }})
                return []
            v = self._parse_vec(r.json())
            if v:
                return v
            # Alternate key probieren (prompt <-> input)
            alt = {"model": self.model, "input": text} if prefer_prompt else {"model": self.model, "prompt": text}
            r2 = requests.post(url, json=alt, timeout=self.max_timeout)
            if r2.status_code != 200:
                log.error("ollama_http_error", extra={"extra_fields": {
                    "status": r2.status_code, "body": (r2.text or "")[:200], "model": self.model, "phase": "alternate"
                }})
                return []
            v2 = self._parse_vec(r2.json())
            if not v2:
                log.warning("ollama_empty_embedding", extra={"extra_fields": {
                    "model": self.model, "len_text": len(text), "tried": ["prompt", "input"]
                }})
            return v2 or []
        except Exception as e:
            log.error("ollama_embed_exception", extra={"extra_fields": {"error": str(e), "model": self.model}})
            return []

    def embed(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for t in texts:
            t = t or ""
            v = self._request_embed(t, prefer_prompt=True)
            out.append(v or [])
        return out

    def embed_robust(self, texts: List[str], max_chars: int = 2000, agg: str = "mean") -> List[List[float]]:
        agg_fn: Callable[[List[List[float]]], List[float]] = _mean if agg == "mean" else _sum
        out: List[List[float]] = []
        for t in texts:
            t = t or ""
            if len(t) <= max_chars:
                v = self._request_embed(t, prefer_prompt=True)
                out.append(v or [])
                continue
            # Stückeln
            parts: List[str] = []
            s = 0
            n = len(t)
            while s < n:
                e = min(n, s + max_chars)
                parts.append(t[s:e])
                s = e
            sub = [self._request_embed(p, prefer_prompt=True) for p in parts]
            vec = agg_fn(sub)
            if not vec:
                lens = [len(v) for v in sub]
                log.warning("agg_empty_embedding", extra={"extra_fields": {
                    "parts": len(parts), "sub_vec_lens": lens, "model": self.model
                }})
            out.append(vec or [])
        return out
