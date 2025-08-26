# app/services/search_facade.py
# Fassade für Retrieval + Kontextaufbau (docid-gefiltert). Öffentliche API unverändert.

from __future__ import annotations
from typing import Dict, Any, List, Optional
import os, json

from app.modules.logging_setup import get_logger
from app.modules.model_registry import ModelRegistry
from app.modules.chroma_client import ChromaWrapper
from app.modules.embeddings_factory import EmbeddingsFactory

log = get_logger("search_facade")


class SearchFacade:
    def __init__(
        self,
        app_cfg: Dict[str, Any],
        model_reg: ModelRegistry,
        embedding_cfg: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.app_cfg = app_cfg
        self.model_reg = model_reg
        self.chroma = ChromaWrapper(app_cfg.get("chroma") or {})

        # Retrieval-Defaults
        try:
            retrieval = self.model_reg.retrieval() or {}
        except Exception:
            retrieval = (getattr(self.model_reg, "_cfg", {}) or {}).get("retrieval", {}) or {}

        alias = (
            retrieval.get("embedding_alias_default")
            or retrieval.get("embedding_alias")
            or "default"
        )

        # Embedding-Config auflösen (falls nicht direkt übergeben)
        if embedding_cfg is None:
            cfg = getattr(self.model_reg, "_cfg", {}) or {}
            emb_list = cfg.get("embeddings", []) or []
            hit = [e for e in emb_list if e.get("alias") == alias]
            if not hit:
                raise ValueError(f"Embedding-Config für Alias '{alias}' nicht gefunden")
            embedding_cfg = hit[0]

        # EmbeddingsFactory erwartet app_cfg + embedding_cfg
        self._emb_fac = EmbeddingsFactory(self.app_cfg, embedding_cfg)

        # weitere Retrieval-Parameter
        self._top_k_default = int(retrieval.get("top_k_default", 5))
        self._parent_collection_prefix = retrieval.get("parent_collection_prefix", "thesis")
        self._parent_collection_suffix = retrieval.get("parent_collection_suffix", "parents")

        # Pfad für Receipt-Dateien
        self._state_dir = (self.app_cfg.get("paths") or {}).get("app_state_dir") or "data/app_state"

        log.info(
            "search_facade_init",
            extra={
                "extra_fields": {
                    "emb_alias": embedding_cfg.get("alias"),
                    "emb_model": embedding_cfg.get("model"),
                    "top_k_default": self._top_k_default,
                    "parent_prefix": self._parent_collection_prefix,
                    "parent_suffix": self._parent_collection_suffix,
                }
            },
        )

    @staticmethod
    def _flatten_first(items: Any) -> List[Any]:
        if isinstance(items, list) and items and isinstance(items[0], list):
            return items[0]
        if isinstance(items, list):
            return items
        return []

    def _read_receipt(self, docid: str) -> Dict[str, Any]:
        try:
            p = os.path.join(self._state_dir, f"ingest_doc_{docid}.json")
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh) or {}
        except Exception:
            return {}

    def _collection_from_state_or_receipt(self, work_type: str, docid: Optional[str]) -> Optional[str]:
        if not docid:
            return None
        # 1) StateFacade (aktuelle Arbeit)
        try:
            from app.services.state_facade import StateFacade
            cur = StateFacade(self._state_dir).get_current() or {}
            parents = (cur.get("collections") or {}).get("parents")
            if parents:
                return parents
        except Exception:
            pass
        # 2) Receipt-Datei
        rec = self._read_receipt(docid)
        parents = (rec.get("collections") or {}).get("parents")
        return parents or None

    def _best_existing_collection(self, work_type: str) -> str:
        """Fallback-Heuristik: probiert zwei Namensschemata und nimmt die Collection mit der größeren count()."""
        wt = (work_type or "default").strip().lower()
        cand1 = f"{self._parent_collection_prefix}_{wt}_{self._parent_collection_suffix}"  # z.B. thesis_bachelor_parents
        cand2 = f"{wt}_parents"  # z.B. bachelor_parents (so erzeugt dein Ingest)

        best_name, best_cnt = cand1, -1
        for name in dict.fromkeys([cand1, cand2]):  # de-dupe, Reihenfolge bewahren
            try:
                col = self.chroma.get_or_create_collection(name)
                cnt = col.count()
            except Exception:
                cnt = -1
            if cnt > best_cnt:
                best_name, best_cnt = name, cnt

        log.info("collection_fallback_choice", extra={"extra_fields": {"chosen": best_name, "count": best_cnt}})
        return best_name

    def _collection_for(self, work_type: str, docid: Optional[str]) -> str:
        via_state = self._collection_from_state_or_receipt(work_type, docid)
        if via_state:
            return via_state
        return self._best_existing_collection(work_type)

    def search(
        self,
        query: str,
        *,
        docid: Optional[str] = None,
        top_k: Optional[int] = None,
        work_type: str = "default",
    ) -> Dict[str, Any]:
        q = (query or "").strip()
        k = int(top_k or self._top_k_default)
        if not q:
            return {"context": "", "sources": [], "collection": "", "top_k": k, "docid": docid or ""}

        collection = self._collection_for(work_type, docid)

        # 1) Query-Embedding
        vec = self._emb_fac.embed_robust([q])[0]

        # 2) Chroma: über Collection abfragen (0.6.3 API)
        where = {"docid": docid} if docid else None
        col = self.chroma.get_or_create_collection(collection)
        try:
            res = col.query(query_embeddings=[vec], n_results=k, where=where)
        except Exception as e:
            log.error(
                "chroma_query_failed",
                extra={"extra_fields": {"err": str(e), "collection": collection, "k": k, "where": where}},
            )
            return {"context": "", "sources": [], "collection": collection, "top_k": k, "docid": docid or ""}

        docs = self._flatten_first(res.get("documents"))
        metas = self._flatten_first(res.get("metadatas"))
        dists = self._flatten_first(res.get("distances"))

        sources: List[Dict[str, Any]] = []
        for i, text in enumerate(docs):
            m = metas[i] if i < len(metas) else {}
            dist = dists[i] if i < len(dists) else None
            score = None
            if dist is not None:
                try:
                    score = 1.0 - float(dist)  # Cosine-Distanz -> Score
                except Exception:
                    score = None
            sources.append(
                {
                    "docid": (m.get("docid") or m.get("doc_id") or ""),
                    "page": m.get("page"),
                    "score": score,
                    "text": text,
                }
            )

        context = "\n\n".join(docs) if docs else ""
        out = {"context": context, "sources": sources, "collection": collection, "top_k": k, "docid": docid or ""}
        log.info(
            "search_ok",
            extra={"extra_fields": {"collection": collection, "docid": docid or "", "k": k, "hits": len(sources), "ctx_len": len(context)}},
        )
        return out
