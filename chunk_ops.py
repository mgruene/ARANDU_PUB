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


def align_and_prune_children(
    documents: List[str],
    ids: List[str],
    metadatas: List[Dict[str, Any]],
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """
    Richtet Child-Tripel aus, entfernt invalide Einträge und stellt sicher,
    dass jede Metadata ein 'chunk_index' besitzt.
    """
    keep_d: List[str] = []
    keep_i: List[str] = []
    keep_m: List[Dict[str, Any]] = []

    dropped = {"empty_doc": 0, "empty_id": 0, "fixed_none_md": 0, "filled_idx": 0}

    for pos, (d, i, m) in enumerate(zip(documents or [], ids or [], metadatas or [])):
        txt = (d or "").strip()
        if not txt:
            dropped["empty_doc"] += 1
            continue
        if not i:
            dropped["empty_id"] += 1
            continue

        md = m if isinstance(m, dict) else {}
        if m is None:
            dropped["fixed_none_md"] += 1

        # chunk_index sicherstellen (aus ID ableiten, sonst pos)
        if "chunk_index" not in md or md["chunk_index"] in (None, ""):
            md["chunk_index"] = _infer_chunk_index(str(i), pos)
            dropped["filled_idx"] += 1

        keep_d.append(d)
        keep_i.append(i)
        keep_m.append(md)

    if any(dropped.values()):
        log.warning(
            "children_align_prune",
            extra={"extra_fields": dropped | {"kept": len(keep_d), "total_in": len(documents or [])}},
        )
    return keep_d, keep_i, keep_m


def filter_chunks_minlen(
    documents: List[str], ids: List[str], metadatas: List[Dict[str, Any]], min_chars: int
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """Filtert Child-Chunks < min_chars Zeichen heraus."""
    keep_d, keep_i, keep_m = [], [], []
    dropped = 0
    for d, i, m in zip(documents or [], ids or [], metadatas or []):
        if len((d or "").strip()) >= min_chars:
            keep_d.append(d)
            keep_i.append(i)
            keep_m.append(m)
        else:
            dropped += 1
    if dropped:
        log.info(
            "chunk_filter_result",
            extra={
                "extra_fields": {
                    "total": len(documents or []),
                    "kept": len(keep_d),
                    "dropped": dropped,
                    "min_chars": min_chars,
                }
            },
        )
    return keep_d, keep_i, keep_m


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
