# modules/metadata_extraction/block_mapping.py
# ÄNDERUNG: Block-Paarung (mehrspaltige Layouts)

from __future__ import annotations
import re
from typing import List, Tuple, Optional, Dict
from .labels import looks_like_any_label, is_pure_label_line, LABELS
from .utils import SEP, trim_value

def build_inline_patterns(key: str):
    pats = [
        rf"^\s*(?:{'|'.join(LABELS[key])})\s*(?:{SEP}\s*)?(?P<val>.+)$",
        rf"^\s*(?:{'|'.join(LABELS[key])})\s{{3,}}(?P<val>.+)$",
        rf"^\s*(?P<val>.+?)\s{{3,}}(?:{'|'.join(LABELS[key])})\s*$",
    ]
    return [re.compile(p, re.IGNORECASE) for p in pats]

INLINE_RX = {k: build_inline_patterns(k) for k in LABELS.keys()}

def scan_line_same(lines: List[str], key: str) -> Optional[str]:
    for ln in lines:
        for rx in INLINE_RX[key]:
            m = rx.search(ln)
            if m:
                v = trim_value(m.group("val") or "")
                if v:
                    return v
    return None

def collect_label_block(lines: List[str], start_idx: int) -> Tuple[List[str], int]:
    keys: List[str] = []
    i = start_idx
    while i < len(lines):
        k = is_pure_label_line(lines[i])
        if not k:
            break
        keys.append(k)
        i += 1
    return keys, i - 1

def collect_value_block(lines: List[str], start_idx: int, n: int) -> Tuple[List[str], int]:
    vals: List[str] = []
    j = start_idx
    last = start_idx - 1
    while j < len(lines) and len(vals) < n:
        cand = (lines[j] or "").strip()
        if cand and not looks_like_any_label(cand):
            vals.append(cand)
            last = j
        j += 1
    return vals, last
