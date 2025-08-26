# services/ingest/metadata_facade.py
# Verantwortlich für: Flatten → Pflichtfelder prüfen
from typing import Dict, Any, Tuple
from modules.logging_setup import get_logger
from modules.ingest.metadata_ops import (
    flatten_final_metadata,
    validate_required,
)

log = get_logger("ingest.metadata_facade")

class MetadataIngestFacade:
    """
    Kapselt die Metadaten-Vorbereitung.
    I/O deterministisch: nimmt raw 'metadata_in', gibt (final, confidence, source) zurück.
    """

    def prepare(self, metadata_in: Dict[str, Any], docid: str) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        final_md, confidence_md, source_md = flatten_final_metadata(metadata_in)
        if not isinstance(final_md, dict) or not final_md:
            raise ValueError("Finale Metadaten leer/ungültig.")
        missing = validate_required(final_md)
        if missing:
            raise ValueError(f"Metadaten unvollständig: {missing}")
        log.info("ingest_meta_ready", extra={"extra_fields": {
            "docid": docid,
            "work_type": final_md.get("work_type"),
            "student": final_md.get("student_name"),
        }})
        return final_md, confidence_md, source_md
