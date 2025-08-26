# modules/metadata_extraction/core.py
# ÄNDERUNG: Zusammensetzen der Heuristiken → EN-Keys & Confidence

from __future__ import annotations
from typing import Dict, Any, List
from .utils import iso_date, normalize_person_name
from .labels import looks_like_any_label
from .block_mapping import scan_line_same, collect_label_block, collect_value_block
from .head_extractors import extract_author_strict, extract_matric_strict, extract_title_multiline
from .examiners import match_known_name

def _assign(meta: Dict[str, Any], key: str, value: str) -> None:
    value = (value or "").strip()
    if not value:
        return
    if key == "submission_date":
        iso = iso_date(value)
        meta[key] = iso or value
        return
    if key == "matriculation_number":
        digits = "".join(ch for ch in value if ch.isdigit())
        if 5 <= len(digits) <= 12:
            meta[key] = digits
        return
    if key in ("student_name","examiner_first","examiner_second"):
        meta[key] = normalize_person_name(value)
        return
    meta[key] = value

def extract_by_regex(text: str, examiners_cfg: Dict[str, Any]) -> Dict[str, Any]:
    lines = [ln for ln in (text or "").splitlines()]
    md = {
        "student_name": "",
        "thesis_title": "",
        "matriculation_number": "",
        "study_program": "",
        "examiner_first": "",
        "examiner_second": "",
        "submission_date": "",
        "work_type": ""  # bachelor|master|seminararbeit|praxisarbeit|projektarbeit
    }
    conf = {k: 0.0 for k in md.keys()}

    # 1) Head-Extractor
    a = extract_author_strict(text)
    if a:
        md["student_name"] = a; conf["student_name"] = 0.8
    mnr = extract_matric_strict(text)
    if mnr:
        md["matriculation_number"] = mnr; conf["matriculation_number"] = 0.85
    ttl = extract_title_multiline(text)
    if ttl:
        md["thesis_title"] = ttl; conf["thesis_title"] = 0.75

    # 2) Inline-Zuordnungen
    for key_map in [
        ("study_program","study_program"),
        ("submission_date","submission_date"),
        ("examiner_first","examiner_first"),
        ("examiner_second","examiner_second"),
        ("student_name","student_name"),
        ("thesis_title","thesis_title"),
        ("matriculation_number","matriculation_number"),
    ]:
        key, out_key = key_map
        if not md[out_key]:
            v = scan_line_same(lines, key)
            if v:
                if out_key in ("examiner_first","examiner_second"):
                    v = match_known_name(v, examiners_cfg)
                _assign(md, out_key, v)
                conf[out_key] = max(conf[out_key], 0.65)

    # 3) Block-Paarung (mehrspaltige Layouts)
    i = 0
    while i < len(lines):
        line = (lines[i] or "").strip()
        if not line:
            i += 1; continue
        from .labels import is_pure_label_line
        k = is_pure_label_line(line)
        if k is not None:
            keys, last_label_idx = collect_label_block(lines, i)
            if len(keys) >= 2:
                vals, last_val_idx = collect_value_block(lines, last_label_idx + 1, len(keys))
                if len(vals) == len(keys) and len(vals) > 0:
                    tmp = {}
                    for kk, vv in zip(keys, vals):
                        # Map DE->EN
                        map_key = {
                            "student_name": "student_name",
                            "thesis_title": "thesis_title",
                            "matriculation_number": "matriculation_number",
                            "study_program": "study_program",
                            "examiner_first": "examiner_first",
                            "examiner_second": "examiner_second",
                            "submission_date": "submission_date",
                        }.get(kk, kk)
                        tmp[map_key] = vv
                    for kk, vv in tmp.items():
                        if kk in ("examiner_first","examiner_second"):
                            vv = match_known_name(vv, examiners_cfg)
                        if vv and not md.get(kk):
                            _assign(md, kk, vv)
                            conf[kk] = max(conf[kk], 0.7)
                    i = max(i, last_val_idx) + 1
                    continue
        i += 1

    # 4) Abgabedatum frei aus Text
    if not md["submission_date"]:
        iso = iso_date(text)
        if iso:
            md["submission_date"] = iso; conf["submission_date"] = max(conf["submission_date"], 0.7)

    # 5) Work-Type Heuristik
    t = (text or "").lower()
    if not md["work_type"]:
        if "bachelor" in t:
            md["work_type"] = "bachelor"; conf["work_type"] = 0.7
        elif "master" in t:
            md["work_type"] = "master"; conf["work_type"] = 0.7
        elif "seminar" in t:
            md["work_type"] = "seminararbeit"; conf["work_type"] = 0.6
        elif "praxis" in t:
            md["work_type"] = "praxisarbeit"; conf["work_type"] = 0.6
        elif "projekt" in t:
            md["work_type"] = "projektarbeit"; conf["work_type"] = 0.6

    return {"metadata": md, "confidence": conf, "source": "regex"}
