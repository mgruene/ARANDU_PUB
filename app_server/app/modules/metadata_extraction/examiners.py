# modules/metadata_extraction/examiners.py
# ÄNDERUNG: Prüfernamen gegen Stammdaten normalisieren

from __future__ import annotations
from typing import Dict, Any
from .utils import normalize_person_name

def match_known_name(raw: str, examiners_cfg: Dict[str, Any]) -> str:
    raw_norm = normalize_person_name(raw)
    for e in examiners_cfg.get("examiners", []):
        if raw_norm.lower() == e["name"].lower():
            return e["name"]
        for v in e.get("variants", []):
            if raw_norm.lower() == normalize_person_name(v).lower():
                return e["name"]
    return raw_norm
