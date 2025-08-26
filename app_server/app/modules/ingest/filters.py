# app/modules/ingest/filters.py
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
