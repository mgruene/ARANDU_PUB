# app/modules/model_registry.py
# Liest model_config.json und liefert robuste, rückgabesichere Konfigurationen.
# Änderungen:
# - retrieval() merged Defaults, niemals None.
# - default_embedding_alias() nutzt retrieval().
# - embedding_by_alias(): klare Fehlermeldung, wenn Alias nicht existiert.
#
# Ergänzt (neu, ohne bestehende Signaturen zu ändern):
# - list_llms(supports_rubrics: Optional[bool] = None) -> List[Dict[str, Any]]
# - list_llm_aliases(supports_rubrics: Optional[bool] = None) -> List[str]
# - list_embeddings() -> List[Dict[str, Any]]
# - list_embedding_aliases() -> List[str]
# - get_retrieval_cfg() -> Dict[str, Any]   (Convenience-Alias auf retrieval())

import os, json
from typing import Dict, Any, Optional, List
from modules.logging_setup import get_logger

log = get_logger("model_registry")


class ModelRegistry:
    def __init__(self, config_dir: str):
        self._path = os.path.join(config_dir, "model_config.json")
        with open(self._path, "r", encoding="utf-8") as f:
            self._cfg = json.load(f)

    # --- Defaults für Retrieval ---
    def _retrieval_defaults(self) -> Dict[str, Any]:
        # Vorsichtige, sinnvolle Defaults. Sie werden mit dem JSON gemerged.
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

            # Hinweis: diese Aliase müssen in embeddings[] existieren.
            "embedding_alias_default": "nomic",
            "embedding_alias_fallbacks": ["mxbai", "jina-de"],
        }

    def retrieval(self) -> Dict[str, Any]:
        r = self._cfg.get("retrieval") or {}
        if not isinstance(r, dict):
            log.warning("retrieval_non_dict", extra={"extra_fields": {"type": str(type(r))}})
            r = {}
        merged = {**self._retrieval_defaults(), **r}
        log.debug("retrieval_cfg", extra={"extra_fields": merged})
        return merged

    # Convenience-Alias (neu)
    def get_retrieval_cfg(self) -> Dict[str, Any]:
        return self.retrieval()

    def default_embedding_alias(self) -> Optional[str]:
        return self.retrieval().get("embedding_alias_default")

    def embedding_by_alias(self, alias: str) -> Dict[str, Any]:
        if not alias:
            raise ValueError("embedding_by_alias: leerer Alias.")
        emb_list: List[Dict[str, Any]] = self._cfg.get("embeddings", []) or []
        for e in emb_list:
            if e.get("alias") == alias:
                return e
        # nicht gefunden → klare Meldung + verfügbare Aliase loggen
        available = [e.get("alias") for e in emb_list if e.get("alias")]
        log.error("embedding_alias_not_found", extra={"extra_fields": {"alias": alias, "available": available}})
        raise KeyError(f"Embedding-Alias '{alias}' nicht in model_config.json vorhanden. Verfügbar: {available}")

    def llm_by_alias(self, alias: str) -> Dict[str, Any]:
        llms: List[Dict[str, Any]] = self._cfg.get("llms", []) or []
        for l in llms:
            if l.get("alias") == alias:
                return l
        available = [l.get("alias") for l in llms if l.get("alias")]
        raise KeyError(f"LLM-Alias '{alias}' nicht gefunden. Verfügbar: {available}")

    # ------------------------ Ergänzungen (neu) ------------------------

    def list_embeddings(self) -> List[Dict[str, Any]]:
        """
        Liste aller Embedding-Modelle (robust).
        Falls 'usage'/'type' fehlen, werden Einträge trotzdem zurückgegeben.
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
                # Wenn 'type' gesetzt, aber nicht 'embedding', überspringen
                continue
            out.append(m)
        # Fallback: wenn obige Filter alles leeren und es trotzdem Einträge gibt, nimm roh
        return out or [m for m in emb_list if isinstance(m, dict)]

    def list_embedding_aliases(self) -> List[str]:
        return [m.get("alias") for m in self.list_embeddings() if m.get("alias")]

    def list_llms(self, supports_rubrics: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Liste LLM-Modelle für Generierung/Chat.
        Filter: usage=='llm' (falls gesetzt) und type in {'chat','completion','llm'}.
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
