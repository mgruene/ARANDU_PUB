# app_server/app/modules/model_registry.py
# -----------------------------------------------------------------------------
# ARANDU – ModelRegistry
# - Liest data/config/model_config.json
# - Liefert Retrieval-Defaults, Embeddings-/LLM-Listen, Lookups per Alias
# - Robust gegen fehlerhafte Aufrufer: llm_by_alias / embedding_by_alias akzeptieren
#   sowohl String-Alias als auch bereits-aufgelöste Dicts (z.B. aus UI-Selectboxen).
# -----------------------------------------------------------------------------
from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple, Union
import os, json

# Falls euer Logger woanders liegt: dieses get_logger ist in ARANDU vorhanden.
try:
    from app.modules.logging_setup import get_logger      # übliche Struktur
except Exception:
    try:
        from modules.logging_setup import get_logger      # Fallback
    except Exception:
        def get_logger(name: str):
            import logging; logging.basicConfig(level=logging.INFO)
            return logging.getLogger(name)

log = get_logger("model_registry")


class ModelRegistry:
    def __init__(self, config_dir: str):
        self._path = os.path.join(config_dir, "model_config.json")
        with open(self._path, "r", encoding="utf-8") as f:
            self._cfg: Dict[str, Any] = json.load(f)

    # --------------------------- Retrieval ---------------------------

    def _retrieval_defaults(self) -> Dict[str, Any]:
        # Vorsichtige Defaults, werden mit JSON gemerged.
        return {
            "default_collection": "bachelor",
            "top_k_default": 5,
            "max_context_chars": 12000,
            "child_chunk_size": 1200,
            "child_chunk_overlap": 200,
            "parent_group_size": 3,
            "parent_group_overlap": 1,
            "max_chars_per_embedding": 2000,
            "embedding_agg": "mean",
            # Diese Aliasse müssen in embeddings[] existieren:
            "embedding_alias_default": "nomic",
            "embedding_alias_fallbacks": ["mxbai-large", "jina-de"],
        }

    def retrieval(self) -> Dict[str, Any]:
        r = self._cfg.get("retrieval") or {}
        if not isinstance(r, dict):
            log.warning("retrieval_non_dict", extra={"extra_fields": {"type": str(type(r))}})
            r = {}
        merged = {**self._retrieval_defaults(), **r}
        log.debug("retrieval_cfg", extra={"extra_fields": merged})
        return merged

    # Convenience-Alias
    def get_retrieval_cfg(self) -> Dict[str, Any]:
        return self.retrieval()

    def default_embedding_alias(self) -> Optional[str]:
        return self.retrieval().get("embedding_alias_default")

    # --------------------------- Helpers -----------------------------

    @staticmethod
    def _coerce_alias(alias_or_dict: Union[str, Dict[str, Any]], kind: str) -> str:
        """
        Nimmt entweder einen String-Alias oder bereits ein Modell-Dict entgegen
        und liefert den Alias-String zurück. kind: "llm" | "embedding" (nur fürs Logging).
        """
        if isinstance(alias_or_dict, dict):
            al = alias_or_dict.get("alias")
            if isinstance(al, str) and al.strip():
                return al.strip()
            # Als Diagnose: häufig wurde statt Alias das komplette Dict durchgereicht
            raise KeyError(f"{kind}_by_alias: Dict ohne 'alias' übergeben: {alias_or_dict}")
        if isinstance(alias_or_dict, str):
            s = alias_or_dict.strip()
            if s:
                return s
        raise ValueError(f"{kind}_by_alias: ungültiger Alias: {alias_or_dict!r}")

    # --------------------------- Embeddings -------------------------

    def list_embeddings(self) -> List[Dict[str, Any]]:
        """
        Liste aller Embedding-Modelle.
        Filtert auf usage/type, lässt aber alte Configs ohne diese Felder durch.
        """
        emb_list = self._cfg.get("embeddings", []) or []
        out: List[Dict[str, Any]] = []
        for m in emb_list:
            if not isinstance(m, dict):
                continue
            usage = str(m.get("usage", "")).lower()
            mtype = str(m.get("type", "")).lower()
            if usage and usage != "embedding":
                continue
            if mtype and mtype != "embedding":
                continue
            out.append(m)
        return out or [m for m in emb_list if isinstance(m, dict)]

    def list_embedding_aliases(self) -> List[str]:
        return [m.get("alias") for m in self.list_embeddings() if m.get("alias")]

    def embedding_by_alias(self, alias: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Robust: akzeptiert String-Alias oder bereits-aufgelöstes Modell-Dict.
        """
        if isinstance(alias, dict):
            # Schon ein Modell-Dict? Dann direkt zurück.
            if alias.get("alias"):
                return alias
            raise KeyError(f"Embedding-Dict ohne 'alias': {alias}")
        al = self._coerce_alias(alias, "embedding")
        emb_list: List[Dict[str, Any]] = self._cfg.get("embeddings", []) or []
        for e in emb_list:
            if e.get("alias") == al:
                return e
        available = [e.get("alias") for e in emb_list if e.get("alias")]
        log.error("embedding_alias_not_found", extra={"extra_fields": {"alias": al, "available": available}})
        raise KeyError(f"Embedding-Alias '{al}' nicht in model_config.json vorhanden. Verfügbar: {available}")

    # --------------------------- LLMs --------------------------------

    def list_llms(self, supports_rubrics: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Liste LLM-Modelle (usage=='llm', type in {'chat','completion','llm'}).
        Optional: supports_rubrics==True/False filtern.
        """
        llm_list = self._cfg.get("llms", []) or []
        out: List[Dict[str, Any]] = []
        for m in llm_list:
            if not isinstance(m, dict):
                continue
            alias = m.get("alias")
            if not alias:
                continue
            usage = str(m.get("usage", "")).lower()
            mtype = str(m.get("type", "")).lower()
            if usage and usage != "llm":
                continue
            if mtype and mtype not in ("chat", "completion", "llm"):
                continue
            if supports_rubrics is not None:
                if bool(m.get("supports_rubrics", False)) != supports_rubrics:
                    continue
            out.append(m)
        return out

    def list_llm_aliases(self, supports_rubrics: Optional[bool] = None) -> List[str]:
        return [m.get("alias") for m in self.list_llms(supports_rubrics) if m.get("alias")]

    def llm_by_alias(self, alias: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Robust: akzeptiert String-Alias oder bereits-aufgelöstes Modell-Dict.
        Das erlaubt, dass UI-Selectboxen (die Dicts zurückgeben) direkt durchgereicht werden.
        """
        if isinstance(alias, dict):
            if alias.get("alias"):
                return alias
            raise KeyError(f"LLM-Dict ohne 'alias': {alias}")
        al = self._coerce_alias(alias, "llm")
        llms: List[Dict[str, Any]] = self._cfg.get("llms", []) or []
        for l in llms:
            if l.get("alias") == al:
                return l
        available = [l.get("alias") for l in llms if l.get("alias")]
        raise KeyError(f"LLM-Alias '{al}' nicht gefunden. Verfügbar: {available}")
