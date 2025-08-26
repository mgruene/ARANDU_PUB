# modules/ingest/pdf_ops.py
from typing import Optional
from io import BytesIO
from pypdf import PdfReader
from modules.logging_setup import get_logger

log = get_logger("ingest.pdf_ops")

def read_all_text(pdf_bytes: bytes) -> str:
    r = PdfReader(BytesIO(pdf_bytes))
    pages = []
    for p in r.pages:
        pages.append(p.extract_text() or "")
    txt = "\n".join(pages)
    log.info("pdf_text_extracted", extra={"extra_fields": {"chars": len(txt), "pages": len(pages)}})
    return txt
