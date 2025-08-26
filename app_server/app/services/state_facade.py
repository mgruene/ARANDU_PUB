# services/state_facade.py
# Fassade über dem Datei-basierten State-Repository.
# Aufgaben:
#  - Quittungen (Receipts) speichern/lesen
#  - Index pflegen (Liste aller Ingests)
#  - aktuelle Auswahl (current_thesis) setzen/lesen
#
# Intensives Logging: alle öffentlichen Methoden loggen Eingaben & Pfade.

from typing import Dict, Any, List, Optional
from app.modules.logging_setup import get_logger
from app.modules.state_repo import StateRepo  # <-- absoluter Import ab 'app.'

log = get_logger("state_facade")


class StateFacade:
    def __init__(self, app_state_dir: str):
        self.repo = StateRepo(app_state_dir)
        log.info("state_facade_init", extra={"extra_fields": {"app_state_dir": app_state_dir}})

    # --- Ingest-Quittungen ---
    def save_ingest_receipt(self, receipt: Dict[str, Any]) -> str:
        if not isinstance(receipt, dict) or not receipt.get("docid"):
            raise ValueError("Ungültige Receipt-Struktur (dict mit docid erwartet).")
        path = self.repo.write_receipt(receipt)
        log.info("state_receipt_saved", extra={"extra_fields": {"path": path, "docid": receipt.get("docid")}})
        return path

    def update_index_from_receipt(self, receipt: Dict[str, Any]) -> str:
        path = self.repo.upsert_index_entry_from_receipt(receipt)
        log.info("state_index_updated", extra={"extra_fields": {"path": path, "docid": receipt.get("docid")}})
        return path

    def get_receipt(self, docid: str) -> Optional[Dict[str, Any]]:
        rec = self.repo.read_receipt(docid)
        log.debug("state_receipt_read", extra={"extra_fields": {"docid": docid, "found": bool(rec)}})
        return rec

    # --- Index ---
    def list_index(self) -> List[Dict[str, Any]]:
        items = self.repo.read_index()
        log.info("state_index_list", extra={"extra_fields": {"count": len(items)}})
        return items

    # --- Auswahl (current_thesis) ---
    def set_current(self, docid: str) -> str:
        path = self.repo.set_current(docid)
        log.info("state_current_set", extra={"extra_fields": {"docid": docid, "path": path}})
        return path

    def get_current(self) -> Optional[Dict[str, Any]]:
        cur = self.repo.get_current()
        log.debug("state_current_get", extra={"extra_fields": {"exists": bool(cur)}})
        return cur
