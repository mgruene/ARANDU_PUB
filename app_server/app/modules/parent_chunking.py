# modules/parent_chunking.py
# Bildet Parent-Einheiten aus bereits erstellten Child-Chunks.
# Jede Parent-Einheit fasst N aufeinanderfolgende Child-Chunks zusammen (mit Überlappung).

from typing import List, Dict, Any

def make_parents_from_children(
    children: List[Dict[str, Any]],
    group_size: int = 5,
    group_overlap: int = 1,
) -> List[Dict[str, Any]]:
    """
    children: Liste von Dicts mit Keys: {"text": str, "index": int, ...}
    Rückgabe: Liste von Parents mit Keys:
      {
        "parent_index": int,
        "text": str,
        "child_indices": List[int]
      }
    """
    if group_size <= 0:
        # ein Parent aus allen
        all_text = " ".join((c.get("text") or "").strip() for c in children if (c.get("text") or "").strip())
        return [{"parent_index": 0, "text": all_text, "child_indices": [c["index"] for c in children]}]

    parents: List[Dict[str, Any]] = []
    start = 0
    parent_idx = 0
    n = len(children)
    step = max(1, group_size - group_overlap)

    while start < n:
        end = min(n, start + group_size)
        chunk_slice = children[start:end]
        text = " ".join((c.get("text") or "").strip() for c in chunk_slice if (c.get("text") or "").strip())
        child_ids = [c["index"] for c in chunk_slice]
        if text.strip():
            parents.append({
                "parent_index": parent_idx,
                "text": text,
                "child_indices": child_ids
            })
            parent_idx += 1
        if end == n:
            break
        start = start + step

    return parents
