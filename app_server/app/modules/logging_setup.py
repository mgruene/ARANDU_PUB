# modules/logging_setup.py
# Initialisiert strukturiertes Logging (JSON-Lines) in Datei und Konsole.
import json
import logging
import os
from datetime import datetime
from typing import Dict

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage()
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            base.update(record.extra_fields)
        return json.dumps(base, ensure_ascii=False)

def ensure_dirs(paths: Dict[str, str]) -> None:
    for p in paths.values():
        os.makedirs(p, exist_ok=True)

def setup_logging(paths_cfg: Dict[str, str], level: int = logging.INFO) -> None:
    ensure_dirs({"logs_dir": paths_cfg["logs_dir"]})
    log_file = os.path.join(paths_cfg["logs_dir"], "app.log")

    root = logging.getLogger()
    root.setLevel(level)

    # Konsole
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(JsonFormatter())

    # Datei
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(JsonFormatter())

    # Doppelte Handler vermeiden
    root.handlers = []
    root.addHandler(ch)
    root.addHandler(fh)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
