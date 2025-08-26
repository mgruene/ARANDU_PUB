# modules/metadata_extraction/pdf_io.py
# ÄNDERUNG: PDF lesen (Seite 1 / Volltext)

from __future__ import annotations
from io import BytesIO
from typing import Tuple
from pypdf import PdfReader
from .utils import normalize_spaces

def extract_first_page_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    if len(reader.pages) == 0:
        return ""
    text = reader.pages[0].extract_text() or ""
    return normalize_spaces(text)

def extract_all_text(pdf_bytes: bytes) -> Tuple[str, int]:
    reader = PdfReader(BytesIO(pdf_bytes))
    texts = []
    for p in reader.pages:
        try:
            t = p.extract_text() or ""
        except Exception:
            t = ""
        texts.append(normalize_spaces(t))
    return "\n".join(texts), len(reader.pages)
