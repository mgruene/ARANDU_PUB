# modules/ingest/embed_ops.py
from typing import Dict, Any, List, Tuple
from modules.logging_setup import get_logger
from modules.embeddings_factory import EmbeddingsFactory
from modules.model_registry import ModelRegistry

log = get_logger("ingest.embed_ops")

def _count_empty(vectors: List[List[float]]) -> Tuple[int,int]:
    total = len(vectors or [])
    empty = sum(1 for v in (vectors or []) if not v or len(v)==0)
    return total, empty

def _avg_vectors(vs: List[List[float]]) -> List[float]:
    if not vs: return []
    n = len(vs[0]) if vs[0] else 0
    if n == 0: return []
    acc = [0.0]*n; k = 0
    for v in vs:
        if not v or len(v)!=n: return []
        for i,x in enumerate(v): acc[i]+=x
        k += 1
    return [x/max(1,k) for x in acc]

def embed_parents_with_fallback(app_cfg: Dict[str, Any], model_reg: ModelRegistry,
                                retrieval_cfg: Dict[str, Any],
                                parents: Dict[str, Any], children: Dict[str, Any]) -> Dict[str, Any]:
    """Erzeugt Parent-Embeddings mit Alias-Fallbacks, ggf. Mittelung aus Child-Embeddings.
       Gibt IMMER ein Dict zurück."""
    try:
        docs_p = parents.get("documents") or []
        ids_p  = parents.get("ids") or []
        mds_p  = parents.get("metadatas") or []

        emb_alias = model_reg.default_embedding_alias() or retrieval_cfg.get("embedding_alias_default")
        fallbacks = retrieval_cfg.get("embedding_alias_fallbacks", []) or []
        max_chars = int(retrieval_cfg.get("max_chars_per_embedding", 2000))
        agg = retrieval_cfg.get("embedding_agg", "mean")

        tried: List[str] = []
        vectors_parent: List[List[float]] = []

        def _embed_alias(alias: str, texts: List[str]) -> List[List[float]]:
            try:
                emb_cfg = model_reg.embedding_by_alias(alias)
                emb = EmbeddingsFactory(app_cfg, emb_cfg)
                log.info("embedding_parents_start", extra={"extra_fields":{"alias": alias, "model": emb_cfg.get("model"), "count": len(texts), "max_chars": max_chars, "agg": agg}})
                return emb.embed_robust(texts, max_chars=max_chars, agg=agg) or []
            except Exception as e:
                log.error("embedding_alias_failed", extra={"extra_fields":{"alias": alias, "error": str(e)}})
                return []

        # 1) Primär + Fallbacks
        for alias in [emb_alias] + fallbacks:
            tried.append(alias)
            vectors_parent = _embed_alias(alias, docs_p)
            total, empty = _count_empty(vectors_parent)
            if empty < total:
                # leere Einträge rausfiltern
                if empty > 0:
                    nd, ni, nm, nv = [], [], [], []
                    for d, i, m, v in zip(docs_p, ids_p, mds_p, vectors_parent):
                        if v and len(v)>0:
                            nd.append(d); ni.append(i); nm.append(m); nv.append(v)
                    docs_p, ids_p, mds_p, vectors_parent = nd, ni, nm, nv
                    log.info("empty_parent_embeddings_removed", extra={"extra_fields":{"remaining": len(docs_p), "alias_used": alias}})
                log.info("embedding_parents_ok", extra={"extra_fields":{"alias_used": alias, "tried": tried}})
                emb_alias = alias
                break
            else:
                log.warning("embedding_parents_all_empty_on_alias", extra={"extra_fields":{"alias": alias}})

        # 2) Fallback: Mittelung aus Child-Embeddings, wenn noch leer
        total, empty = _count_empty(vectors_parent)
        if total == 0 or empty == total:
            try:
                last = tried[-1] if tried else emb_alias
                emb_cfg = model_reg.embedding_by_alias(last)
                emb = EmbeddingsFactory(app_cfg, emb_cfg)
                child_vecs = emb.embed_robust(children.get("documents") or [], max_chars=max_chars, agg=agg) or []
                idx_by_chunk = {m.get("chunk_index"): i for i, m in enumerate(children.get("metadatas") or [])}
                parent_vecs = []
                for raw in parents.get("raw") or []:
                    idxs = [idx_by_chunk.get(ci) for ci in raw.get("child_indices") or [] if idx_by_chunk.get(ci) is not None]
                    subs = [child_vecs[i] for i in idxs if i is not None and i < len(child_vecs) and child_vecs[i]]
                    parent_vecs.append(_avg_vectors(subs))
                vectors_parent = parent_vecs
                total, empty = _count_empty(vectors_parent)
            except Exception as e:
                log.error("embedding_children_averaging_failed", extra={"extra_fields":{"error": str(e)}})
                vectors_parent = []

        return {
            "vectors_parent": vectors_parent,
            "filtered_ids_parent": ids_p,
            "alias_used": emb_alias,
            "tried": tried,
            "all_empty": (len(vectors_parent)==0) or (sum(1 for v in vectors_parent if not v or len(v)==0) == len(vectors_parent)),
        }
    except Exception as e:
        log.error("embed_parents_with_fallback_fatal", extra={"extra_fields":{"error": str(e)}})
        # Garantierter Rückgabevertrag
        return {
            "vectors_parent": [],
            "filtered_ids_parent": parents.get("ids") if isinstance(parents, dict) else [],
            "alias_used": (retrieval_cfg.get("embedding_alias_default") if isinstance(retrieval_cfg, dict) else None),
            "tried": [],
            "all_empty": True,
        }
