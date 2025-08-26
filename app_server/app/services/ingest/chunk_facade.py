# services/ingest/chunk_facade.py
# Verantwortlich für: Children bauen/filtern/alignen → Parents bauen
from typing import Dict, Any, Tuple, List
import os
from modules.logging_setup import get_logger
from modules.ingest.chunk_ops import (
    build_children,
    filter_chunks_minlen,
    align_and_prune_children,
    build_parents,
)

log = get_logger("ingest.chunk_facade")

class ChunkIngestFacade:
    """
    Erzeugt Child-Chunks und Parent-Blöcke.
    Erwartet explizite Parameter (deterministische I/O).
    """

    def build(
        self,
        full_text: str,
        final_md: Dict[str, Any],
        docid: str,
        source_file: str,
        child_size: int,
        child_overlap: int,
        parent_group_size: int,
        parent_group_overlap: int,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        # Children
        children = build_children(
            full_text=full_text,
            docid=docid,
            final_md=final_md,
            source_file=os.path.basename(source_file),
            child_size=int(child_size),
            child_overlap=int(child_overlap),
        )
        d, i, m = filter_chunks_minlen(
            children.get("documents") or [], children.get("ids") or [], children.get("metadatas") or [], min_chars=20
        )
        d, i, m = align_and_prune_children(d, i, m)
        children["documents"], children["ids"], children["metadatas"] = d, i, m
        if not children["documents"]:
            raise ValueError("Keine Children nach Filterung.")
        log.info("ingest_children_ready", extra={"extra_fields": {"docid": docid, "n": len(d)}})

        # Parents
        parents = build_parents(
            children_docs=children["documents"],
            children_mds=children["metadatas"],
            docid=docid,
            group_size=int(parent_group_size),
            group_overlap=int(parent_group_overlap),
            final_md=final_md,
            source_file=os.path.basename(source_file),
        )
        if not parents.get("documents"):
            raise ValueError("Keine Parents erzeugt (Parameter prüfen).")
        log.info("ingest_parents_ready", extra={"extra_fields": {"docid": docid, "n": len(parents['documents'])}})

        return children, parents
