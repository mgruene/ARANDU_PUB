# modules/ingest/upsert_ops.py
from typing import Dict, Any, Tuple
from modules.logging_setup import get_logger
from modules.chroma_client import ChromaWrapper

log = get_logger("ingest.upsert_ops")

def upsert_parent_child(chroma: ChromaWrapper, work_type: str, docid: str,
                        parents_docs, parents_ids, parents_mds, parents_vectors,
                        childs_docs, childs_ids, childs_mds) -> Tuple[Dict[str, str], Dict[str, int]]:
    parents_col = f"{work_type}_parents"
    chunks_col  = f"{work_type}_chunks"

    chroma.upsert(
        parents_col,
        documents=parents_docs, metadatas=parents_mds,
        ids=parents_ids, embeddings=parents_vectors
    )
    log.info("chroma_upsert_parents", extra={"extra_fields":{"docid": docid, "collection": parents_col, "count": len(parents_ids)}})

    chroma.upsert(
        chunks_col,
        documents=childs_docs, metadatas=childs_mds,
        ids=childs_ids, embeddings=None
    )
    log.info("chroma_upsert_children", extra={"extra_fields":{"docid": docid, "collection": chunks_col, "count": len(childs_ids)}})

    return {"parents": parents_col, "children": chunks_col}, {"parents": len(parents_ids), "children": len(childs_ids)}
