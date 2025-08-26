# services/search/query_facade.py
from typing import Dict, Any, Optional
from app.modules.logging_setup import get_logger

log = get_logger("search.query_facade")


class QueryFacade:
    """Deterministische Aufbereitung von Suchparametern (DocID-Filter, K, Limits)."""

    def prepare(
        self, query: str, retrieval_cfg: Dict[str, Any], docid: Optional[str] = None, top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        q = " ".join((query or "").strip().split())
        k = int(top_k) if top_k is not None else int(retrieval_cfg.get("top_k_default", 5))
        where = {"docid": docid} if docid else None
        out = {
            "query": q,
            "k": max(1, k),
            "where": where,
            "max_context_chars": int(retrieval_cfg.get("max_context_chars", 6000)),
            "embedding_alias": retrieval_cfg.get("embedding_alias_default"),
        }
        log.info("query_prepared", extra={"extra_fields": out})
        return out
