# modules/metadata_extraction/head_extractors.py
# ÄNDERUNG: Strikte Head-Extraktion (Autor/Matrikel/Titel mehrzeilig)

from __future__ import annotations
import re
from typing import List, Optional
from .utils import WS, SEP, normalize_person_name, trim_value
from .labels import looks_like_any_label

RX_AUTHOR_LABEL = re.compile(rf"\b(vorgelegt{WS}+von|eingereicht{WS}+von|author)\b(?:{SEP}\s*)?(?P<val>.*)$", re.IGNORECASE)
RX_MATRIKEL_LABEL = re.compile(
    rf"\b(?:Matr\.\-?Nr\.|Matrikelnr\.|Matr\.{WS}?Nr\.|Matrikel{WS}?Nr\.|Matrikelnummer|Matriculation{WS}?No\.?)\b(?:{SEP}\s*)?(?P<val>.*)$",
    re.IGNORECASE
)
RX_TITEL_LABEL = re.compile(rf"\b(?:Thema|Titel|Title)\b(?:{SEP}\s*)?(?P<val>.*)$", re.IGNORECASE)
RX_NUMERIC_5_12 = re.compile(r"\b(\d{5,12})\b")
RX_AUTHOR_START = re.compile(rf"^\s*(?:vorgelegt{WS}+von|eingereicht{WS}+von|author)\b", re.IGNORECASE)

def _next_nonempty(lines: List[str], start: int) -> Optional[str]:
    for j in range(start, min(start+3, len(lines))):
        s = (lines[j] or "").strip()
        if s:
            return s
    return None

def extract_author_strict(head: str) -> Optional[str]:
    lines = (head or "").splitlines()
    for i, raw in enumerate(lines):
        m = RX_AUTHOR_LABEL.search(raw or "")
        if not m:
            continue
        val = trim_value(m.group("val") or "")
        if not val:
            val = _next_nonempty(lines, i+1) or ""
        val = re.split(r"\b(?:Matr|Matrikel|Matriculation|Studiengang|Course|Thema|Titel|Title|Abgabe|Date|Erstprüfer|Zweitprüfer)\b", val, 1)[0]
        toks = [t for t in re.split(r"\s+", val) if t]
        if len(toks) >= 2:
            return normalize_person_name(" ".join(toks[:4]))
    return None

def extract_matric_strict(head: str) -> Optional[str]:
    lines = (head or "").splitlines()
    for i, raw in enumerate(lines):
        m = RX_MATRIKEL_LABEL.search(raw or "")
        if not m:
            continue
        val = trim_value(m.group("val") or "")
        cand_line = val if val else (_next_nonempty(lines, i+1) or "")
        m2 = RX_NUMERIC_5_12.search(cand_line)
        if m2:
            return m2.group(1)
    return None

def extract_title_multiline(head: str) -> Optional[str]:
    lines = (head or "").splitlines()
    for i, raw in enumerate(lines):
        m = RX_TITEL_LABEL.search(raw or "")
        if not m:
            continue
        first = trim_value(m.group("val") or "")
        out_parts: List[str] = []
        if first:
            out_parts.append(first)
        j = i + 1
        blank_run = 0
        while j < len(lines):
            s = lines[j].rstrip()
            if not s.strip():
                blank_run += 1
                if blank_run >= 2:
                    break
                j += 1
                continue
            blank_run = 0
            if RX_AUTHOR_START.match(s) or looks_like_any_label(s):
                break
            out_parts.append(s.strip())
            j += 1
        cand = trim_value(" ".join(out_parts))
        if len(cand) >= 5:
            return cand
    return None
