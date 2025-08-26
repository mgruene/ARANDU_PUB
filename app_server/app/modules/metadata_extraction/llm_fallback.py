# modules/metadata_extraction/llm_fallback.py
# ÄNDERUNG: LLM-Fallback (Ollama) – unverändert zur Außenwelt

from __future__ import annotations
import re, json
from typing import Dict, Any, List
from app.modules.llm_client import OllamaClient  # nutzt bestehende Fassade


def llm_fill_missing(first_page_text: str, missing_fields: List[str], llm_cfg: Dict[str, Any], app_cfg: Dict[str, Any]) -> Dict[str, Any]:
    client = OllamaClient(app_cfg["ollama"]["base_url"])
    sys_prompt = (
        "Extrahiere fehlende Metadaten einer wissenschaftlichen Arbeit aus folgendem Text der Titelseite. "
        "Gib ausschließlich valides JSON im folgenden Schema zurück: "
        "{\"student_name\":\"...\",\"thesis_title\":\"...\",\"matriculation_number\":\"...\",\"study_program\":\"...\","
        "\"examiner_first\":\"...\",\"examiner_second\":\"...\",\"submission_date\":\"YYYY-MM-DD\",\"work_type\":\"bachelor|master|seminararbeit|praxisarbeit|projektarbeit\"}"
    )
    user = f"TEXT:\n{first_page_text}\n\nFELDER:{','.join(missing_fields)}"
    prompt = sys_prompt + "\n" + user
    resp = client.generate(model=llm_cfg["model"], prompt=prompt, options=llm_cfg.get("params"))
    m = re.search(r"\{.*\}", resp, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}
