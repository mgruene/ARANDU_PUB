# modules/metadata_extraction/labels.py
# ÄNDERUNG: Label-Varianten & Matcher

from __future__ import annotations
import re
from typing import Dict, List, Optional
from .utils import WS, SEP, HYP

# interne Schlüssel (EN) → Labelvarianten (DE/EN)
LABELS: Dict[str, List[str]] = {
    "study_program":   [rf"(?:im{WS}+)studiengang", r"studiengang", r"degree{WS}*program", r"course{WS}*of{WS}*study"],
    "matriculation_number": [
        rf"matrikel(?:nummer|{WS}nr\.?)",
        rf"matr(?:\.|ikel)?{WS}?(?:{HYP})?{WS}?nr\.?",  # „Matr.-Nr.“ / „Matrikel-Nr.“
        r"matrikelnr\.?", r"matrikel", r"matriculation{WS}*no\.?",
    ],
    "submission_date": [r"abgabedatum", rf"eingereicht{WS}am", rf"datum{WS}der{WS}abgabe", r"date"],
    "examiner_first":  [r"erstprüfer", rf"1\.{WS}prüfer", r"erstgutachter", r"erstreferent", r"referent", r"first{WS}*supervisor"],
    "examiner_second": [r"zweitprüfer", rf"2\.{WS}prüfer", r"zweitgutachter", r"korreferent", rf"2\.{WS}referent", r"second{WS}*supervisor"],
    "thesis_title":    [r"thema", r"titel", r"title"],
    "student_name":    [rf"vorgelegt{WS}von", rf"eingereicht{WS}von", r"autor", r"kandidat", r"name", r"author"],
}

def build_label_regex(patterns: List[str]) -> re.Pattern:
    lbl = r"(?:%s)" % "|".join(patterns)
    return re.compile(rf"^\s*(?:{lbl})\s*(?:{SEP}\s*)?(?P<val>.*)\s*$", re.IGNORECASE)

LABEL_RX = {k: build_label_regex(v) for k, v in LABELS.items()}

def looks_like_any_label(line: str) -> bool:
    s = (line or "").strip().lower()
    for pats in LABELS.values():
        for p in pats:
            if re.match(rf"^\s*(?:{p})\b", s, re.IGNORECASE):
                return True
    return False

def is_pure_label_line(line: str) -> Optional[str]:
    s = (line or "").strip()
    for key, rx in LABEL_RX.items():
        m = rx.match(s)
        if m:
            inline = (m.group("val") or "").strip()
            if inline == "":
                return key
    return None
