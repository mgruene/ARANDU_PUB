# app/modules/ingest/splitters.py
# Auto-generated split from original chunk_ops.py — no logic changes, only relocation.

# app/modules/ingest/chunk_ops.py
# Child-/Parent-Aufbereitung für den Ingest.
# - align_and_prune_children: richtet Tripel (docs/ids/metadatas) aus, repariert None-Metadaten
#   und füllt fehlende chunk_index-Werte.
# - filter_chunks_minlen: entfernt sehr kurze Chunks.
# - build_children: erzeugt Child-Docs/IDs/Metadaten.
# - build_parents: gruppiert Children zu Parents und legt Parent-Metadaten an.

from typing import Dict, Any, List, Tuple
import json
import re

from modules.logging_setup import get_logger
from modules.chunking import chunk_text
from modules.parent_chunking import make_parents_from_children

log = get_logger("ingest.chunk_ops")

_ID_IDX_RE = re.compile(r"_c_(\d{4})$")

def _infer_chunk_index(chunk_id: str, fallback_idx: int) -> int:
    """Versucht, die 4-stellige Chunk-Index-Endung aus der ID zu lesen; sonst fallback_idx."""
    if isinstance(chunk_id, str):
        m = _ID_IDX_RE.search(chunk_id)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                pass
    return fallback_idx


def build_children(
    full_text: str,
    docid: str,
    final_md: Dict[str, Any],
    source_file: str,
    child_size: int,
    child_overlap: int,
) -> Dict[str, Any]:
    """Erzeugt Child-Dokumente, -IDs und -Metadaten aus Volltext."""
    ch = chunk_text(full_text, chunk_size=child_size, overlap=child_overlap)
    documents = [c["text"] for c in ch]
    ids = [f"{docid}_c_{i:04d}" for i, _ in enumerate(ch)]
    metadatas = [
        {
            "level": "child",
            "docid": docid,
            "chunk_index": c.get("index", idx),
            "chunk_id": f"{docid}_c_{c.get('index', idx):04d}",
            "student_name": final_md.get("student_name", ""),
            "thesis_title": final_md.get("thesis_title", ""),
            "work_type": final_md.get("work_type", ""),
            "matriculation_number": final_md.get("matriculation_number", ""),
            "study_program": final_md.get("study_program", ""),
            "examiner_first": final_md.get("examiner_first", ""),
            "examiner_second": final_md.get("examiner_second", ""),
            "submission_date": final_md.get("submission_date", ""),
            "source_file": source_file,
        }
        for idx, c in enumerate(ch)
    ]
    log.info(
        "children_built",
        extra={
            "extra_fields": {
                "docid": docid,
                "count": len(ids),
                "size": child_size,
                "overlap": child_overlap,
            }
        },
    )
    return {"documents": documents, "ids": ids, "metadatas": metadatas, "raw": ch}
