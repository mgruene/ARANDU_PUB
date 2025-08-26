# app/modules/state_repo.py
# Datei-basiertes State-Repository mit atomaren JSON-Writes.
# Legt an:
#   data/app_state/ingest_doc_<docid>.json
#   data/app_state/ingests_index.json
#   data/app_state/current_thesis.json
from __future__ import annotations

import os
import json
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.modules.logging_setup import get_logger
log = get_logger("state_repo")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class StateRepo:
    def __init__(self, app_state_dir: str):
        self.dir = app_state_dir
        os.makedirs(self.dir, exist_ok=True)
        self.index_path = os.path.join(self.dir, "ingests_index.json")
        self.current_path = os.path.join(self.dir, "current_thesis.json")
        log.info("state_repo_init", extra={"extra_fields": {"dir": self.dir}})

    # --------- Low level ---------
    def _atomic_write_json(self, path: str, data: Any) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=os.path.dirname(path))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass

    def _read_json(self, path: str) -> Optional[Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    # --------- Receipts ---------
    def receipt_path(self, docid: str) -> str:
        return os.path.join(self.dir, f"ingest_doc_{docid}.json")

    def write_receipt(self, receipt: Dict[str, Any]) -> str:
        docid = receipt.get("docid")
        if not docid:
            raise ValueError("Receipt ohne docid.")
        path = self.receipt_path(docid)
        self._atomic_write_json(path, receipt)
        return path

    def read_receipt(self, docid: str) -> Optional[Dict[str, Any]]:
        return self._read_json(self.receipt_path(docid))

    # --------- Index ---------
    def _empty_index(self) -> Dict[str, Any]:
        return {"updated_at": _utcnow(), "items": []}

    def read_index(self) -> List[Dict[str, Any]]:
        data = self._read_json(self.index_path)
        if not data:
            return []
        return data.get("items", [])

    def upsert_index_entry_from_receipt(self, receipt: Dict[str, Any]) -> str:
        """Aktualisiert/ergänzt den Index-Eintrag für die docid – angereichert mit fachlichen & technischen Feldern."""
        docid = (receipt.get("docid") or "").strip()
        if not docid:
            raise ValueError("Receipt ohne docid.")

        idx = self._read_json(self.index_path) or self._empty_index()
        items: List[Dict[str, Any]] = list(idx.get("items", []))

        meta = receipt.get("metadata") or {}
        entry = {
            "docid": docid,
            # Datei/Arbeitsart
            "filename": receipt.get("filename") or receipt.get("file"),
            "work_type": receipt.get("work_type"),
            # fachliche Kurzinfos
            "student_name": meta.get("student_name"),
            "thesis_title": meta.get("thesis_title"),
            # technische Kurzinfos
            "embedding_alias": receipt.get("embedding_alias"),
            "ingest_at": receipt.get("ingest_at"),
            # Zusammenfassung (nützlich für UI/Diagnose)
            "collections": receipt.get("collections") or {},
            "counts": receipt.get("counts") or {},
        }

        # ersetzen/anhängen
        replaced = False
        for i, it in enumerate(items):
            if it.get("docid") == docid:
                items[i] = entry
                replaced = True
                break
        if not replaced:
            items.append(entry)

        idx["items"] = items
        idx["updated_at"] = _utcnow()
        self._atomic_write_json(self.index_path, idx)
        return self.index_path

    # --------- Current Selection ---------
    def set_current(self, docid: str) -> str:
        rec = self.read_receipt(docid)
        if not rec:
            raise ValueError(f"Keine Receipt-Datei für docid '{docid}' gefunden.")
        cur = {
            "docid": docid,
            "filename": rec.get("filename") or rec.get("file"),
            "work_type": rec.get("work_type"),
            "collections": rec.get("collections"),
            "counts": rec.get("counts"),
            "metadata": rec.get("metadata"),
            "embedding_alias": rec.get("embedding_alias"),
            "ingest_at": rec.get("ingest_at"),
            "selected_at": _utcnow(),
        }
        self._atomic_write_json(self.current_path, cur)
        return self.current_path

    def get_current(self) -> Optional[Dict[str, Any]]:
        return self._read_json(self.current_path)
