# app/services/config/schema_validator.py
# Aufgabe: Minimal-valide Pflichtfelder prüfen und klare Fehlermeldungen liefern.

from __future__ import annotations
from typing import Dict, Any, List
from app.modules.logging_setup import get_logger

log = get_logger("config.validator")


class SchemaValidator:
    def validate_app(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(cfg, dict):
            errors.append("App-Config ist kein Objekt (dict).")

        paths = cfg.get("paths")
        if not isinstance(paths, dict):
            errors.append("Pfadblock 'paths' fehlt oder ist ungültig.")
        else:
            if not paths.get("config_dir"):
                errors.append("'paths.config_dir' fehlt.")

        chroma = cfg.get("chroma")
        if chroma is None:
            log.warning("chroma_missing", extra={"extra_fields": {"hint": "App-Config ohne 'chroma' – prüfen Docker/ENV."}})
        elif not isinstance(chroma, dict):
            errors.append("'chroma' muss ein Objekt sein.")

        ollama = cfg.get("ollama")
        if (ollama is not None) and (not isinstance(ollama, dict)):
            errors.append("'ollama' muss ein Objekt sein.")

        if errors:
            raise ValueError("App-Config ungültig: " + "; ".join(errors))
        log.info("app_config_valid", extra={"extra_fields": {"paths": True, "chroma": chroma is not None}})
        return cfg

    def validate_model(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(cfg, dict):
            errors.append("Model-Config ist kein Objekt (dict).")

        embs = cfg.get("embeddings")
        if not isinstance(embs, list) or len(embs) == 0:
            errors.append("'embeddings' fehlt oder ist leer (Liste erwartet).")

        retr = cfg.get("retrieval")
        if retr is None:
            log.warning("retrieval_missing", extra={"extra_fields": {"hint": "No 'retrieval' – Defaults greifen im Code."}})
        elif not isinstance(retr, dict):
            errors.append("'retrieval' muss ein Objekt sein.")

        if errors:
            raise ValueError("Model-Config ungültig: " + "; ".join(errors))
        log.info("model_config_valid", extra={"extra_fields": {
            "embeddings": len(embs or []),
            "has_retrieval": isinstance(retr, dict)
        }})
        return cfg
