# app/ui/pages/01_upload_ingest.py
# Seite 01 · Arbeit einlesen und in Datenbank speichern
import os
import uuid
import streamlit as st

from app.services.config_facade import ConfigFacade
from app.services.metadata_facade import MetadataFacade
from app.services.ingest_facade import IngestFacade
from app.services.state_facade import StateFacade
from app.modules.model_registry import ModelRegistry
from app.modules.logging_setup import setup_logging, get_logger
from app.ui.components.upload_form import render_upload_form
from app.ui.components.metadata_editor import render_metadata_editor
from app.ui.components.theme import apply_css_only
from app.modules.validators import missing_required

# --- Setup ---
CFG_DIR = os.environ.get("ARANDU_CFG_DIR", "data/config")
cfg_facade = ConfigFacade(CFG_DIR)
app_cfg = cfg_facade.load_app_config()
setup_logging(app_cfg["paths"])
apply_css_only(app_cfg)
log = get_logger("ui.upload_ingest")

st.title("01 · Arbeit einlesen und in Datenbank speichern")

# Modelle/Services initialisieren
model_reg = ModelRegistry(app_cfg["paths"]["config_dir"])
try:
    examiners_cfg = cfg_facade.load_examiners()
except Exception:
    examiners_cfg = {"examiners": []}
meta_srv = MetadataFacade(app_cfg, model_reg, examiners_cfg)
ingest = IngestFacade(app_cfg, model_reg)
state = StateFacade(app_cfg["paths"]["app_state_dir"])

# Session-State
st.session_state.setdefault("md_preview", None)
st.session_state.setdefault("last_filename", None)

# --- Upload ---
pdf_bytes, filename = render_upload_form()

# --- Metadaten erkennen (Texte angepasst, Aufrufe unverändert) ---
if st.button("Metadaten erkennen --> Stammdaten lesen", key="btn_meta_detect"):
    if not pdf_bytes:
        st.warning("Bitte zunächst eine PDF hochladen.")
    else:
        try:
            prev = meta_srv.preview_metadata(pdf_bytes)
            md = prev.get("metadata") or {}
            st.session_state.md_preview = md
            st.session_state.last_filename = filename
            st.success("Metadaten erkannt. Bitte prüfen/ergänzen und anschließend ingest starten.")
            log.info("meta_preview_ok", extra={"extra_fields": {
                "missing": prev.get("missing") or [], "used": prev.get("used") or []
            }})
        except Exception as e:
            log.error("meta_preview_fail", extra={"extra_fields": {"err": str(e)}})
            st.error(f"Metadaten-Erkennung fehlgeschlagen: {e}")

# --- Metadaten editieren/prüfen ---
current_md = st.session_state.md_preview or {}
if current_md:
    current_md = render_metadata_editor(current_md)
    missing = missing_required(current_md)
    if missing:
        st.warning("Fehlende Pflichtfelder: " + ", ".join(missing))
    else:
        st.success("Alle Pflichtfelder sind ausgefüllt.")
else:
    # Platzhalter solange nichts erkannt wurde -> Button unten bleibt deaktiviert
    missing = [
        "student_name", "thesis_title", "matriculation_number", "study_program",
        "examiner_first", "examiner_second", "submission_date", "work_type"
    ]
meta_complete = len(missing) == 0

# --- Ingest starten (Texte/Enablement angepasst, Calls unverändert) ---
if st.button(
    "Ingest starten --> Datei verarbeiten und speichern",
    key="btn_ingest_start",
    disabled=not meta_complete
):
    if not pdf_bytes:
        st.warning("Bitte zunächst eine PDF hochladen.")
    elif not current_md or not meta_complete:
        st.warning("Metadaten sind unvollständig. Bitte erst alle Pflichtfelder ausfüllen.")
    else:
        try:
            # DocID übernehmen oder erzeugen
            docid = (current_md.get("docid") or uuid.uuid4().hex[:8]).strip()

            # -> unveränderter Fassade-Call
            receipt = ingest.ingest(
                pdf_bytes,
                st.session_state.last_filename or (filename or "upload.pdf"),
                current_md,
                docid
            )

            # Nach erfolgreichem Ingest: Auswahl für andere Seiten setzen (Header nutzt das)
            try:
                state.set_current(docid)
            except Exception as e2:
                log.warning("state_current_set_failed", extra={"extra_fields": {"err": str(e2), "docid": docid}})

            st.success("Ingest erfolgreich.")
            with st.expander("Quittung"):
                st.json(receipt)
            log.info("ingest_success", extra={"extra_fields": {
                "docid": docid, "collections": receipt.get("collections", {})
            }})

            # Reset für nächsten Upload
            st.session_state.md_preview = None
            st.session_state.last_filename = None

        except Exception as e:
            log.error("ingest_failed", extra={"extra_fields": {"error": str(e)}})
            st.error(f"Ingest fehlgeschlagen: {e}")
