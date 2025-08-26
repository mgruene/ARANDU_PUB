# services/ingest/upsert_facade.py
# Verantwortlich für: Upsert in Chroma (Parents + Children)
from typing import Dict, Any, Tuple
from modules.logging_setup import get_logger
from modules.chroma_client import ChromaWrapper
from modules.ingest.upsert_ops import upsert_parent_child

log = get_logger("ingest.upsert_facade")

class UpsertIngestFacade:
    """Kapselt den Upsert-Schritt nach ChromaDB."""

    def __init__(self, chroma: ChromaWrapper) -> None:
        self.chroma = chroma

    def run(
        self,
        docid: str,
        final_md: Dict[str, Any],
        parents: Dict[str, Any],
        emb_res: Dict[str, Any],
        children: Dict[str, Any],
    ) -> Tuple[Dict[str, str], Dict[str, int]]:
        collections, counts = upsert_parent_child(
            chroma=self.chroma,
            work_type=final_md["work_type"],
            docid=docid,
            parents_docs=parents["documents"],
            parents_ids=emb_res["filtered_ids_parent"],
            parents_mds=parents["metadatas"],
            parents_vectors=emb_res["vectors_parent"],
            childs_docs=children["documents"],
            childs_ids=children["ids"],
            childs_mds=children["metadatas"],
        )
        log.info("ingest_upsert_done", extra={"extra_fields": {
            "docid": docid, "collections": collections, "counts": counts
        }})
        return collections, counts
