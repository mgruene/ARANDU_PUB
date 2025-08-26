# modules/metadata_extraction/utils.py
# ÄNDERUNG: Gemeinsame Utilities (Spaces/Trim/Datum/Name)

from __future__ import annotations
import re
from datetime import datetime
from typing import Optional

WS = r"[\s\u00A0]"                 # NBSP-tolerant
SEP = r"[:：\-–—]"
HYP = r"[-\u2010\u2011]"

_MONATSNAMEN = "Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember"
_DE_DATE_NUMERIC = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b")
_DE_DATE_NAMED   = re.compile(rf"\b(\d{{1,2}})\.\s*({_MONATSNAMEN})\s*(\d{{4}})\b", re.IGNORECASE)
_MONAT2NUM = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6,
    "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}

_SMALL = {"von","van","de","der","den","zu","zur","zum","und","di","da"}

def normalize_spaces(s: str) -> str:
    return re.sub(r"[ \t]+", " ", (s or "")).strip()

def trim_value(v: str) -> str:
    v = (v or "").strip()
    v = re.sub(r"\s{2,}", " ", v)
    return v.rstrip(" \t;,:.")

def iso_date(s: str) -> str:
    """Akzeptiert 12.03.24 / 12.03.2024 sowie 12. März 2024 / 12. Maerz 2024."""
    if not s:
        return ""
    s = normalize_spaces(s)
    m = _DE_DATE_NUMERIC.search(s)
    if m:
        d, mth, y = map(int, m.groups())
        if y < 100:
            y += 2000 if y < 50 else 1900
        try:
            return datetime(y, mth, d).strftime("%Y-%m-%d")
        except ValueError:
            return ""
    m = _DE_DATE_NAMED.search(s)
    if m:
        d = int(m.group(1))
        mon = m.group(2).lower().replace("ae","ä").replace("oe","ö").replace("ue","ü")
        y = int(m.group(3))
        mth = _MONAT2NUM.get(mon)
        if mth:
            try:
                return datetime(y, mth, d).strftime("%Y-%m-%d")
            except ValueError:
                return ""
    return ""

def normalize_person_name(name: str) -> str:
    """'Nachname, Vorname' → 'Vorname Nachname', Kleinwörter, Prof./Dr., Initialismen."""
    n = (name or "").strip()
    if not n:
        return n
    if "," in n:
        parts = [p.strip() for p in n.split(",")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            n = f"{parts[1]} {parts[0]}"
    toks = [t for t in re.split(r"\s+", n) if t]
    def _tc(tok: str) -> str:
        low = tok.lower()
        if low in _SMALL:
            return low
        if len(tok) <= 3 and tok.isupper():
            return tok
        if low.startswith("prof"):
            return "Prof."
        if low.startswith("dr"):
            return "Dr."
        return tok[:1].upper() + tok[1:].lower()
    return " ".join(_tc(t) for t in toks).strip()
