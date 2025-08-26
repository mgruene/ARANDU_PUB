# services/ingest/file_facade.py
# Verantwortlich für: PDF speichern & hashen, Metadaten-JSON persistieren
from typing import Dict, Any
import os
from modules.logging_setup import get_logger
from modules.ingest.file_ops import save_upload_and_hash, save_metadata_json

log = get_logger("ingest.file_facade")

class FileIngestFacade:
    """
    Persistiert Artefakte im Uploads-Verzeichnis.
    Benötigt app_cfg['paths']['uploads_dir'] (aus app_config.json via ConfigFacade).
    """

    def __init__(self, app_cfg: Dict[str, Any]) -> None:
        self.uploads_dir = app_cfg["paths"]["uploads_dir"]
        os.makedirs(self.uploads_dir, exist_ok=True)

    def save(
        self,
        pdf_bytes: bytes,
        filename: str,
        docid: str,
        final_md: Dict[str, Any],
        confidence_md: Dict[str, Any],
        source_md: str,
    ) -> Dict[str, Any]:
        pdf_path, filehash = save_upload_and_hash(
            pdf_bytes=pdf_bytes,
            uploads_dir=self.uploads_dir,
            docid=docid,
            filename=filename,
        )
        meta_json = save_metadata_json(
            out_dir=self.uploads_dir,
            docid=docid,
            file_basename=os.path.basename(pdf_path),
            filehash=filehash,
            final_metadata=final_md,
            confidence=confidence_md,
            source=source_md,
        )
        log.info("ingest_file_saved", extra={"extra_fields": {
            "docid": docid, "pdf": os.path.basename(pdf_path), "meta_json": os.path.basename(meta_json)
        }})
        return {"pdf_path": pdf_path, "filehash": filehash, "metadata_json": meta_json}
