# app/ui/components/app_header.py
# Zeigt oben rechts die aktuell ausgewählte Arbeit (Name, Titel)
# + aufklappbare Metadaten. Minimal-invasive, wiederverwendbare Kopf-Komponente.

from typing import Dict, Any, Optional
import streamlit as st
from app.services.state_facade import StateFacade

def render_app_header(app_cfg: Dict[str, Any]) -> None:
    """
    Plaziert rechts oben eine Box mit der aktuellen Arbeit.
    Erwartet app_cfg wie aus ConfigFacade.load_app_config().
    """
    state = StateFacade(app_cfg["paths"]["app_state_dir"])
    current = state.get_current() or {}

    left, right = st.columns([0.62, 0.38], vertical_alignment="center")
    with right:
        st.markdown("#### Aktuelle Arbeit")
        if not current:
            st.info("Keine aktuelle Arbeit ausgewählt.")
            return

        md: Dict[str, Any] = current.get("metadata") or {}
        student = md.get("student_name") or "—"
        title   = md.get("thesis_title") or "—"

        st.write(f"**{student}** — {title}")
        with st.expander("Metadaten"):
            st.json(md)
