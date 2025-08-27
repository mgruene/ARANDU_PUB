# app/modules/llm_router.py
# Selektiert das LLM gemäß Rubrik (alias) aus model_config.json
import json, os
from typing import Dict, Any

MODEL_CFG = os.getenv("MODEL_CONFIG_PATH", "/data/config/model_config.json")

def resolve_model(alias: str=None) -> Dict[str, Any]:
    with open(MODEL_CFG, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    llms = cfg.get("llms", {})
    mapping = {x.get("alias"): x for x in llms} if isinstance(llms, list) else llms
    if not alias:
        alias = cfg.get("defaults", {}).get("llm_alias") or next(iter(mapping.keys()))
    m = mapping.get(alias)
    if not m:
        raise ValueError(f"LLM alias '{alias}' nicht gefunden")
    return {"alias": alias, "provider": m.get("provider","ollama"),
            "model": m.get("model"), "params": m.get("params",{})}
