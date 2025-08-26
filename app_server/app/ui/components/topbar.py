# app/ui/components/topbar.py
# Obere Leiste: links Logo, rechts aktuelle Arbeit (Name, Titel + Metadaten-Expander).

import streamlit as st
from typing import Dict, Any
from app.ui.components.theme import logo_path
from app.services.state_facade import StateFacade


def render_topbar(app_cfg: Dict[str, Any]) -> None:
    left, right = st.columns([0.25, 0.75], vertical_alignment="center")

    # Links: Logo (falls vorhanden)
    with left:
        lp = logo_path(app_cfg)
        if lp:
            st.image(lp, caption=None, use_container_width=False, width=140)
        else:
            st.markdown("### ARANDU")

    # Rechts: Aktuelle Arbeit
    with right:
        st.markdown("#### Aktuelle Arbeit")
        state = StateFacade(app_cfg["paths"]["app_state_dir"])
        current = state.get_current() or {}
        md: Dict[str, Any] = current.get("metadata") or {}
        student = md.get("student_name") or "—"
        title = md.get("thesis_title") or "—"
        st.write(f"**{student}** — {title}")
        with st.expander("Metadaten"):
            st.json(md)
