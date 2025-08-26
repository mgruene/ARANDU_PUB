# app/services/config_facade.py
# Öffentliche Fassade (stabile API), intern: Repository + Validator.
# WICHTIG: /data ist Datenwurzel im Container; 'data/...' und 'app/data/...'
# werden auf '/data/...' normalisiert. *_dir werden bei Bedarf angelegt.

from __future__ import annotations
from typing import Dict, Any, Optional
import os
from app.modules.logging_setup import get_logger
from app.services.config.config_repository import ConfigRepository
from app.services.config.schema_validator import SchemaValidator

log = get_logger("config_facade")

DATA_ROOT = "/data"


def _abs_from_data(path_like: str) -> str:
    """Normalisiert 'data/...'/ 'app/data/...' → '/data/...'; absolute Pfade bleiben."""
    p = (path_like or "").lstrip("./")
    if p.startswith("app/data/"):
        p = p[len("app/"):]  # -> data/...
    if p.startswith("data/"):
        return os.path.join(DATA_ROOT, p[len("data/"):])
    return p if os.path.isabs(p) else os.path.join(DATA_ROOT, p)


class ConfigFacade:
    def __init__(self, config_dir: Optional[str] = None) -> None:
        # Priorität: Parameter > ENV > Default
        raw_dir = config_dir or os.environ.get("ARANDU_CFG_DIR", "data/config")
        norm_dir = _abs_from_data(raw_dir)
        # Falls der normalisierte Pfad nicht existiert, aber der rohe absolut ist: benutze den rohen.
        cfg_dir = norm_dir if os.path.isdir(norm_dir) or not os.path.isabs(raw_dir) else raw_dir
        self._repo = ConfigRepository(cfg_dir)
        self._validator = SchemaValidator()
        log.info("config_facade_init", extra={"extra_fields": {"config_dir": self._repo.config_dir}})

    # ---- Public API (unverändert) ----

    def load_app_config(self) -> Dict[str, Any]:
        """Lädt app_config.json, validiert Minimalstruktur, normalisiert Pfade, erstellt *_dir."""
        cfg = self._repo.load_app_config()  # enthält bereits paths.config_dir
        cfg = self._validator.validate_app(cfg)

        raw_paths = dict(cfg.get("paths") or {})
        norm_paths: Dict[str, str] = {}
        for k, v in raw_paths.items():
            norm_paths[k] = _abs_from_data(v)

        # Verzeichnisse anlegen (nur *_dir)
        for k, v in norm_paths.items():
            if k.endswith("_dir"):
                try:
                    os.makedirs(v, exist_ok=True)
                except Exception as e:
                    log.warning("mkdir_failed", extra={"extra_fields": {"key": k, "dir": v, "err": str(e)}})

        cfg["paths_raw"] = raw_paths
        cfg["paths"] = norm_paths
        log.info("config_app_loaded", extra={"extra_fields": {"config_dir": norm_paths.get("config_dir")}})
        return cfg

    def load_model_config(self) -> Dict[str, Any]:
        """Lädt model_config.json und validiert Minimalstruktur."""
        cfg = self._repo.load_model_config()
        cfg = self._validator.validate_model(cfg)
        log.info("config_model_loaded", extra={"extra_fields": {"embeddings": len(cfg.get('embeddings', []) or [])}})
        return cfg

    # Optional, kompatibel zu Altbestand
    def load_examiners(self) -> Dict[str, Any]:
        return self._repo.load_examiners()

    # Helfer
    def config_dir(self) -> str:
        return self._repo.config_dir
