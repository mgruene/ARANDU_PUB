# app/services/config/config_repository.py
# Aufgabe: Reines Laden der JSON-Konfigurationen; minimale Pfadpflege für config_dir.

from __future__ import annotations
from typing import Dict, Any
import os, json
from app.modules.logging_setup import get_logger

log = get_logger("config.repository")


class ConfigRepository:
    def __init__(self, config_dir: str) -> None:
        # Speichere den Pfad so, wie er übergeben wurde (bereits von der Fassade normalisiert).
        self._config_dir = os.path.abspath(config_dir)
        os.makedirs(self._config_dir, exist_ok=True)
        log.info("config_repo_init", extra={"extra_fields": {"config_dir": self._config_dir}})

    @property
    def config_dir(self) -> str:
        return self._config_dir

    # ---------- Low-level I/O ----------

    def _read_json(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self._config_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Konfigurationsdatei fehlt: {path}")
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Ungültiges JSON in {path}: {e}")
        if not isinstance(data, dict):
            raise ValueError(f"Ungültiges JSON-Format (dict erwartet) in: {path}")
        log.info("config_json_loaded", extra={"extra_fields": {"file": filename, "bytes": os.path.getsize(path)}})
        return data

    # ---------- Public API ----------

    def load_app_config(self) -> Dict[str, Any]:
        cfg = self._read_json("app_config.json")
        # Pfadblock sicherstellen + config_dir setzen
        paths = dict(cfg.get("paths") or {})
        paths["config_dir"] = self._config_dir
        cfg["paths"] = paths
        log.info("app_config_loaded", extra={"extra_fields": {"has_paths": True}})
        return cfg

    def load_model_config(self) -> Dict[str, Any]:
        data = self._read_json("model_config.json")
        log.info("model_config_loaded", extra={"extra_fields": {
            "embeddings": len(data.get("embeddings", []) or []),
            "llms": len(data.get("llms", []) or []),
            "has_retrieval": bool(data.get("retrieval"))
        }})
        return data

    def load_examiners(self) -> Dict[str, Any]:
        try:
            return self._read_json("examiners.json")
        except FileNotFoundError:
            log.warning("examiners_missing", extra={"extra_fields": {"file": "examiners.json"}})
            return {"examiners": []}
