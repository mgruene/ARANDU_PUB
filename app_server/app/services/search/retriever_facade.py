# services/search/retriever_facade.py
from typing import Dict, Any, List, Optional
from app.modules.logging_setup import get_logger

log = get_logger("search.retriever_facade")


class RetrieverFacade:
    """Parent-Retrieval + optionales Children-Expanding über Chroma."""

    def search_parents(
        self, chroma: Any, embedder: Any, collection: str, query: str, k: int,
        where: Optional[Dict[str, Any]], max_chars: int, agg: str = "mean"
    ) -> Dict[str, Any]:
        qvec = embedder.embed_robust([query], max_chars=max_chars, agg=agg)[0]
        if not qvec:
            raise ValueError("Query-Embedding leer.")
        col = chroma.get_or_create_collection(collection)
        res = col.query(
            query_embeddings=[qvec], n_results=k, where=where,
            include=["documents", "metadatas", "ids", "distances"]
        )
        n = len(res.get("ids", [[]])[0])
        hits: List[Dict[str, Any]] = []
        for i in range(n):
            hits.append({
                "id": res["ids"][0][i],
                "distance": float(res["distances"][0][i]),
                "document": res["documents"][0][i] or "",
                "metadata": res["metadatas"][0][i] or {},
            })
        out = {"hits": hits, "count": n}
        log.info("parents_retrieved", extra={"extra_fields": {"collection": collection, "k": k, "count": n}})
        return out

    def fetch_children_for_parents(
        self, chroma: Any, children_collection: str, parent_ids: List[str], k_per_parent: int = 3
    ) -> Dict[str, Any]:
        if not parent_ids:
            return {"hits": [], "count": 0}
        col = chroma.get_or_create_collection(children_collection)
        hits: List[Dict[str, Any]] = []
        for pid in parent_ids:
            res = col.query(
                query_texts=[pid], n_results=k_per_parent, where={"parent_id": pid},
                include=["documents", "metadatas", "ids", "distances"]
            )
            n = len(res.get("ids", [[]])[0])
            for i in range(n):
                hits.append({
                    "id": res["ids"][0][i],
                    "distance": float(res["distances"][0][i]),
                    "document": res["documents"][0][i] or "",
                    "metadata": res["metadatas"][0][i] or {},
                })
        out = {"hits": hits, "count": len(hits)}
        log.info("children_expanded", extra={"extra_fields": {"parents": len(parent_ids), "children": len(hits)}})
        return out
