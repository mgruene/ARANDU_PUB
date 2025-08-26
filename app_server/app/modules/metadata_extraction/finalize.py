# modules/metadata_extraction/finalize.py
# ÄNDERUNG: Finalisierung + Pflichtfelder

from __future__ import annotations
from typing import Dict, Any

REQUIRED = ["student_name","thesis_title","matriculation_number","study_program","examiner_first","examiner_second","submission_date","work_type"]

def finalize_with_overrides(md: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    out = {**md}
    out.update({k: v for k, v in overrides.items() if v not in (None, "", [])})
    missing = [k for k in REQUIRED if not out.get(k)]
    return {"metadata": out, "missing": missing, "complete": len(missing) == 0}
