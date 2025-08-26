# app/modules/ingest/parent_grouping.py
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

def build_parents(
    children_docs: List[str],
    children_mds: List[Dict[str, Any]],
    docid: str,
    group_size: int,
    group_overlap: int,
    final_md: Dict[str, Any],
    source_file: str,
) -> Dict[str, Any]:
    """Gruppiert aufbereitete Children zu Parents und erzeugt Parent-Metadaten."""
    # defensiv: None-Metadaten -> {}, chunk_index fallback
    kept = []
    for pos, (d, m) in enumerate(zip(children_docs or [], children_mds or [])):
        md = m if isinstance(m, dict) else {}
        idx = md.get("chunk_index")
        if idx in (None, ""):
            idx = pos
            md["chunk_index"] = idx
        kept.append({"text": d, "index": idx})

    parents = make_parents_from_children(
        kept, group_size=group_size, group_overlap=group_overlap
    ) or make_parents_from_children(kept, group_size=0, group_overlap=0)

    documents = [p["text"] for p in parents]
    ids = [f"{docid}_p_{p['parent_index']:04d}" for p in parents]
    metadatas = []
    for p in parents:
        metadatas.append(
            {
                "level": "parent",
                "docid": docid,
                "parent_index": p["parent_index"],
                "child_indices_str": json.dumps(p["child_indices"], ensure_ascii=False),
                "children_count": len(p["child_indices"]),
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
        )
    log.info(
        "parents_built",
        extra={
            "extra_fields": {
                "docid": docid,
                "count": len(ids),
                "group_size": group_size,
                "overlap": group_overlap,
            }
        },
    )
    return {"documents": documents, "ids": ids, "metadatas": metadatas, "raw": parents}
