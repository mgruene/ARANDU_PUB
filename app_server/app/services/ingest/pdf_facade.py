# services/ingest/pdf_facade.py
# Verantwortlich für: PDF → Volltext
from modules.logging_setup import get_logger
from modules.ingest.pdf_ops import read_all_text

log = get_logger("ingest.pdf_facade")

class PDFIngestFacade:
    """Kapselt die PDF-Text-Extraktion."""

    def extract(self, pdf_bytes: bytes) -> str:
        full_text = read_all_text(pdf_bytes)
        if not full_text:
            raise ValueError("PDF-Text leer.")
        log.info("ingest_pdf_read", extra={"extra_fields": {"chars": len(full_text)}})
        return full_text
