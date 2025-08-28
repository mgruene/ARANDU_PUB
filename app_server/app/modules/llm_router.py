# app_server/app/modules/llm_router.py
# -----------------------------------------------------------------------------
# ARANDU – LLM Router (rückwärtskompatibel)
# - resolve_model(alias_or_dict) akzeptiert:
#     * String-Alias (neu/alt)
#     * bereits aufgelöstes LLM-Dict (Pass-Through)
# - Legacy-Aliasse werden auf neue Aliasse gemappt
# - Auflösung über ModelRegistry (model_config.json)
# -----------------------------------------------------------------------------

from __future__ import annotations
from typing import Any, Dict, Optional
import os
from app.modules.model_registry import ModelRegistry

# Historische/alte Aliasse -> neue Aliasse
LEGACY_ALIAS_MAP = {
    "style-llm":    "chat-qwen2.5-7b",
    "default-llm":  "chat-qwen2.5-7b",
    "analysis-llm": "chat-llama3-instruct",
    "eval-llm":     "chat-mistral",
}

def _cfg_dir_abs() -> str:
    v = os.getenv("ARANDU_CFG_DIR", "config")
    if v.startswith("/"):
        return v
    for base in ("/code/data", "/data"):
        p = os.path.join(base, v)
        if os.path.isdir(p):
            return p
    return v

def resolve_model(alias_or_dict: Any) -> Dict[str, Any]:
    """
    Liefert das LLM-Config-Dict (inkl. 'model', 'params', ...).
    Akzeptiert auch bereits ein LLM-Dict (Pass-Through).
    Fallbacks:
      - Legacy-Alias-Mapping
      - erstes supports_rubrics==true LLM
      - erstes beliebiges LLM
    Raises ValueError, wenn GAR kein LLM verfügbar ist.
    """
    # 1) Bereits aufgelöstes Dict? -> direkt zurückgeben
    if isinstance(alias_or_dict, dict):
        if alias_or_dict.get("model"):
            return alias_or_dict
        # falls nur alias enthalten, extrahiere ihn
        alias = (alias_or_dict.get("alias") or "").strip()
    else:
        alias = (alias_or_dict or "").strip()

    cfg_dir = _cfg_dir_abs()
    registry = ModelRegistry(cfg_dir)

    # 2) Direkter Alias-Treffer?
    if alias:
        try:
            return registry.llm_by_alias(alias)
        except Exception:
            # 2b) Legacy-Mapping versuchen
            mapped = LEGACY_ALIAS_MAP.get(alias)
            if mapped:
                try:
                    return registry.llm_by_alias(mapped)
                except Exception:
                    pass  # fällt in Fallbacks

    # 3) Fallbacks
    llms_sr = registry.list_llms(supports_rubrics=True)
    if llms_sr:
        return llms_sr[0]
    llms_all = registry.list_llms()
    if llms_all:
        return llms_all[0]

    raise ValueError(f"LLM alias '{alias}' nicht gefunden und kein Fallback verfügbar")
