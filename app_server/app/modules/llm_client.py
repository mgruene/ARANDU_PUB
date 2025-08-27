# app_server/app/modules/llm_client.py
# Robuster Ollama-Client (Stdlib, keine Fremdpakete) für 0.9.6
# - /api/embed (nicht /api/embeddings)
# - generate(), chat(), embed()  (embed: Single -> Batch-Fallback)
from typing import Any, Dict, List, Optional
import json, os, time
import urllib.request, urllib.error

DEFAULT_BASE = os.getenv("OLLAMA_BASE_URL") or "http://host.docker.internal:11434"

class OllamaHTTPError(RuntimeError):
    pass

def _post_json(url: str, payload: Dict[str, Any], timeout: float = 120.0) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try: body = e.read().decode("utf-8")
        except Exception: pass
        raise OllamaHTTPError(f"HTTP {e.code} {url}: {body}") from e
    except urllib.error.URLError as e:
        raise OllamaHTTPError(f"Connection error to {url}: {e}") from e

def _extract_single(res: Dict[str, Any]) -> List[float]:
    # Erwartet {"embedding":[...]} (kann bei manchen Builds leer sein)
    emb = res.get("embedding")
    if isinstance(emb, list):
        return emb
    # Fallbacks (selten)
    embs = res.get("embeddings")
    if isinstance(embs, list) and embs and isinstance(embs[0], list):
        return embs[0]
    data = res.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        e = data[0].get("embedding")
        if isinstance(e, list):
            return e
    return []

def _extract_batch(res: Dict[str, Any]) -> List[List[float]]:
    # Erwartet {"embeddings":[[...],[...],...]}
    embs = res.get("embeddings")
    if isinstance(embs, list) and (not embs or isinstance(embs[0], list)):
        return embs or []
    # Fallback-Formate
    data = res.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        outs: List[List[float]] = []
        for item in data:
            e = item.get("embedding")
            if isinstance(e, list):
                outs.append(e)
        return outs
    # Single in Batch-Antwort?
    single = _extract_single(res)
    return [single] if single else []

class OllamaClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")
        self._gen  = f"{self.base_url}/api/generate"
        self._chat = f"{self.base_url}/api/chat"
        self._emb  = f"{self.base_url}/api/embed"     # << wichtig: /api/embed

    @classmethod
    def from_app_config(cls, app_cfg: Dict[str, Any]) -> "OllamaClient":
        base = ((app_cfg or {}).get("ollama") or {}).get("base_url") or DEFAULT_BASE
        return cls(base)

    def generate(self, model: str, prompt: str,
                 options: Optional[Dict[str, Any]] = None,
                 timeout: float = 120.0) -> Dict[str, Any]:
        payload = {"model": model, "prompt": prompt, "stream": False}
        if options: payload["options"] = options
        res = _post_json(self._gen, payload, timeout=timeout)
        return {"ok": True, "model": model, "response": res.get("response", ""), "raw": res}

    def chat(self, model: str, messages: List[Dict[str, str]],
             options: Optional[Dict[str, Any]] = None,
             timeout: float = 120.0) -> Dict[str, Any]:
        payload = {"model": model, "messages": messages, "stream": False}
        if options: payload["options"] = options
        res = _post_json(self._chat, payload, timeout=timeout)
        msg = res.get("message") or {}
        return {"ok": True, "model": model, "response": (msg.get("content") or ""), "raw": res}

    def embed(self, texts: List[str], model: str, timeout: float = 120.0) -> List[List[float]]:
        """Single-Calls; wenn leere Vektoren -> kurzer Warmup -> Batch-Fallback."""
        if not texts:
            return []
        # 1) Single
        out: List[List[float]] = []
        try:
            for t in texts:
                res = _post_json(self._emb, {"model": model, "input": t}, timeout=timeout)
                v = _extract_single(res)
                if not v:  # Beobachtung: einige Builds liefern leeres embedding im Single-Pfad
                    out = []
                    break
                out.append(v)
            if out:
                return out
        except OllamaHTTPError:
            out = []  # weiter mit Batch

        # 2) kurze Pause (Warmup)
        time.sleep(0.2)

        # 3) Batch-Fallback
        res = _post_json(self._emb, {"model": model, "input": texts}, timeout=timeout)
        vecs = _extract_batch(res)
        if not vecs or (vecs and not vecs[0]):
            raise OllamaHTTPError(f"Empty embeddings for model={model}; keys={list(res.keys())}")
        return vecs

    # Abwärtskompatibel
    def embed_batch(self, model: str, inputs: List[str], timeout: float = 120.0) -> List[List[float]]:
        return self.embed(inputs, model=model, timeout=timeout)
