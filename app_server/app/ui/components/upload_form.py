# app/ui/components/upload_form.py
# ÄNDERUNG: Pflichtfelder aus der Upload-Form entfernt – die Pflege erfolgt jetzt im separaten Metadata-Editor.
#           Diese Komponente liefert NUR die Datei (bytes, filename).

import streamlit as st
from typing import Optional, Tuple

def render_upload_form() -> Tuple[Optional[bytes], Optional[str]]:
    st.subheader("Neue Arbeit hochladen")
    up = st.file_uploader("PDF der Arbeit", type=["pdf"], accept_multiple_files=False)
    if up is None:
        return None, None
    # Streamlit liefert beim Re-Run erneut den Upload; das Lesen ist hier bewusst direkt.
    return up.read(), up.name
