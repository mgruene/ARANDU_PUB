# app/ui/components/theme.py
# Zentrales Theme/Branding:
# - Setzt Page-Config (Titel, Favicon)
# - Injektiert CSS aus design_dir
# - Liefert Hilfsfunktionen für Logo/Favicon-Pfade

from __future__ import annotations
import os
import streamlit as st
from typing import Dict, Any
from app.modules.logging_setup import get_logger

log = get_logger("ui.theme")


def _design_dir(app_cfg: Dict[str, Any]) -> str:
    return app_cfg.get("paths", {}).get("design_dir", "data/design")


def favicon_path(app_cfg: Dict[str, Any]) -> str | None:
    path = os.path.join(_design_dir(app_cfg), "arandu_favicon.png")
    return path if os.path.exists(path) else None


def logo_path(app_cfg: Dict[str, Any]) -> str | None:
    path = os.path.join(_design_dir(app_cfg), "arandu_logo.png")
    return path if os.path.exists(path) else None


def _inject_css(app_cfg: Dict[str, Any]) -> None:
    css_file = os.path.join(_design_dir(app_cfg), "arandu.css")
    if os.path.exists(css_file):
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            log.info("css_injected", extra={"extra_fields": {"css": css_file}})
        except Exception as e:
            log.warning(
                "css_inject_failed",
                extra={"extra_fields": {"css": css_file, "error": str(e)}},
            )
    else:
        log.debug("css_missing", extra={"extra_fields": {"css_expected": css_file}})


def _inject_favicon(app_cfg: Dict[str, Any], page: str = "unknown") -> None:
    """Sorgt dafür, dass das Favicon nach jedem Seitenwechsel aktiv bleibt und loggt Details."""
    icon = favicon_path(app_cfg)
    if icon:
        st.markdown(
            f"<link rel='shortcut icon' href='file://{icon}'/>",
            unsafe_allow_html=True,
        )
        log.info(
            "favicon_injected",
            extra={"extra_fields": {"page": page, "icon": icon, "exists": os.path.exists(icon)}},
        )
    else:
        log.warning(
            "favicon_missing",
            extra={"extra_fields": {"page": page, "expected": os.path.join(_design_dir(app_cfg), 'arandu_favicon.png')}},
        )


def page_config(app_cfg: Dict[str, Any], title: str) -> None:
    """Nur auf der Startseite (App.py) aufrufen: setzt Favicon & Layout und injiziert CSS."""
    icon = favicon_path(app_cfg)
    try:
        st.set_page_config(
            page_title=title, layout="wide", page_icon=icon if icon else None
        )
    except Exception:
        # set_page_config darf nur 1x pro Session aufgerufen werden – wenn schon gesetzt, ignorieren
        pass
    _inject_css(app_cfg)
    _inject_favicon(app_cfg, page="App.py")


def apply_css_only(app_cfg: Dict[str, Any]) -> None:
    """Auf Unterseiten aufrufen: kein set_page_config, nur CSS + Favicon injizieren."""
    _inject_css(app_cfg)
    _inject_favicon(app_cfg, page="Subpage")

