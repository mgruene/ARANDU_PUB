# app/modules/model_registry.py
# Liest model_config.json und liefert robuste, rückgabesichere Konfigurationen.
# Änderungen:
# - retrieval() merged Defaults, niemals None.
# - default_embedding_alias() nutzt retrieval().
# - embedding_by_alias(): klare Fehlermeldung, wenn Alias nicht existiert.

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
