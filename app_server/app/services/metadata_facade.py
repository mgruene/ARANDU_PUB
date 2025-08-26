# app/services/metadata_facade.py
# Orchestriert Preview (Regex → LLM-Fallback) und liefert Status.
# Minimal-invasive Robustheit:
# - akzeptiert dict ODER (dict, list[, ...]) für regex & LLM
# - WICHTIG: LLM-Fallback wird mit (llm_cfg, app_cfg) in DER REIHENFOLGE aufgerufen,
#            die dein llm_fallback erwartet (app_cfg enthält "ollama").

from typing import Dict, Any, Tuple, List
from app.modules.logging_setup import get_logger
from app.modules.model_registry import ModelRegistry
from app.modules.extract_metadata import (
    extract_first_page_text,
    extract_by_regex,
)

# LLM-Fallback kann in deinem Stand unterschiedlich heißen:
try:
    from app.modules.extract_metadata import llm_fill_missing as _llm_fallback_fn
except Exception:
    from app.modules.extract_metadata import extract_by_llm_fallback as _llm_fallback_fn  # Fallback auf alten Namen

log = get_logger("metadata_facade")

# Pflichtfelder analog Ingest (nur lokal genutzt, kein Import -> keine Zyklen)
REQUIRED_KEYS = [
    "student_name","thesis_title","matriculation_number","study_program",
    "examiner_first","examiner_second","submission_date","work_type"
]

def _compute_missing(md: Dict[str, Any]) -> List[str]:
    return [k for k in REQUIRED_KEYS if not (str(md.get(k) or "").strip())]

def _norm_regex_result(res: Any) -> Tuple[Dict[str, Any], List[str]]:
    # Fälle: dict  | (dict, list) | (dict, list, …)
    if isinstance(res, tuple):
        if len(res) >= 2 and isinstance(res[0], dict):
            md = res[0]
            missing = res[1] if isinstance(res[1], list) else list(res[1]) if res[1] is not None else []
            return md, missing
        raise TypeError(f"extract_by_regex: unerwartetes Tuple-Format (len={len(res)})")
    if isinstance(res, dict):
        return res, _compute_missing(res)
    raise TypeError(f"extract_by_regex: unerwarteter Rückgabetyp {type(res).__name__}")

def _norm_llm_result(res: Any, prev_missing: List[str]) -> Tuple[Dict[str, Any], List[str]]:
    # Fälle: dict  | (dict, list) | (dict, list, …)
    if isinstance(res, tuple):
        if len(res) >= 2 and isinstance(res[0], dict):
            md = res[0]
            missing = res[1] if isinstance(res[1], list) else list(res[1]) if res[1] is not None else []
            return md, missing
        raise TypeError(f"{_llm_fallback_fn.__name__}: unerwartetes Tuple-Format (len={len(res)})")
    if isinstance(res, dict):
        md = res
        still_missing = [k for k in prev_missing if not (str(md.get(k) or "").strip())]
        return md, still_missing
    raise TypeError(f"{_llm_fallback_fn.__name__}: unerwarteter Rückgabetyp {type(res).__name__}")

def _choose_llm_cfg(model_reg: ModelRegistry) -> Dict[str, Any]:
    """
    Wählt das LLM für den Metadaten-Fallback:
    - wenn retrieval.metadata_llm_alias existiert -> dieses
    - sonst 'llama3-instruct' falls vorhanden
    - sonst das erste aus der Liste
    """
    retrieval = model_reg.retrieval() or {}
    alias = retrieval.get("metadata_llm_alias")
    if alias:
        try:
            return model_reg.llm_by_alias(alias)
        except Exception:
            pass
    try:
        return model_reg.llm_by_alias("llama3-instruct")
    except Exception:
        lst = model_reg.list_llms()
        if not lst:
            raise RuntimeError("Keine LLMs in model_config.json definiert.")
        return model_reg.llm_by_alias(lst[0])

class MetadataFacade:
    def __init__(self, app_cfg: Dict[str, Any], model_reg: ModelRegistry, examiners_cfg: Dict[str, Any]):
        self.app_cfg = app_cfg
        self.model_reg = model_reg
        self.examiners_cfg = examiners_cfg

    def preview_metadata(self, pdf_bytes: bytes) -> Dict[str, Any]:
        head_text = extract_first_page_text(pdf_bytes)

        # 1) Regex
        md_regex, missing = _norm_regex_result(extract_by_regex(head_text, self.examiners_cfg))
        used = ["regex"]

        # 2) LLM-Fallback nur für wirklich fehlende Felder
        if missing:
            llm_cfg = _choose_llm_cfg(self.model_reg)
            # >>> WICHTIG: Dein llm_fallback erwartet (first_page_text, missing, llm_cfg, app_cfg)
            md_llm, still_missing = _norm_llm_result(
                _llm_fallback_fn(head_text, missing, llm_cfg, self.app_cfg),
                missing,
            )
            md = {**md_regex, **md_llm}
            used.append("llm")
        else:
            md = md_regex
            still_missing = []

        log.info("metadata_preview", extra={"extra_fields": {
            "used": used, "missing": still_missing, "keys": list(md.keys())
        }})
        return {"metadata": md, "used": used, "missing": still_missing}
