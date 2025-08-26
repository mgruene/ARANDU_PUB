# modules/ingest/file_ops.py
from typing import Tuple, Dict, Any
import hashlib, os, json

from modules.logging_setup import get_logger
log = get_logger("ingest.file_ops")

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def save_upload_and_hash(pdf_bytes: bytes, uploads_dir: str, docid: str, filename: str) -> Tuple[str, str]:
    os.makedirs(uploads_dir, exist_ok=True)
    safe_name = (filename or "upload.pdf").replace("/", "_")
    pdf_path = os.path.join(uploads_dir, f"{docid}_{safe_name}")
    with open(pdf_path, "wb") as f: f.write(pdf_bytes)
    h = sha256_hex(pdf_bytes)
    log.info("file_saved", extra={"extra_fields": {"path": pdf_path, "sha256": h}})
    return pdf_path, h

def save_metadata_json(out_dir: str, docid: str, file_basename: str, filehash: str,
                       final_metadata: Dict[str, Any], confidence: Dict[str, Any], source: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    md_path = os.path.join(out_dir, f"{docid}.metadata.json")
    with open(md_path, "w", encoding="utf-8") as f:
        json.dump({
            "docid": docid,
            "file": file_basename,
            "filehash": filehash,
            "metadata": final_metadata,
            "confidence": confidence,
            "source": source
        }, f, ensure_ascii=False, indent=2)
    log.info("metadata_saved", extra={"extra_fields": {"path": md_path}})
    return md_path
