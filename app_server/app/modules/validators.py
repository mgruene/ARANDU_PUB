# app/modules/validators.py
from typing import Dict, Any, List

REQUIRED = [
    "student_name","thesis_title","matriculation_number","study_program",
    "examiner_first","examiner_second","submission_date","work_type"
]

def missing_required(md: Dict[str, Any]) -> List[str]:
    return [k for k in REQUIRED if not md.get(k)]
