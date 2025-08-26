# app/ui/App.py
# Multipage-Start. Links erscheinen die Seiten aus /ui/pages.
import os
import streamlit as st
from app.services.config_facade import ConfigFacade
from app.modules.logging_setup import setup_logging
from app.ui.components.theme import page_config
from app.ui.components.topbar import render_topbar

# ÄNDERUNG: CFG_DIR zuerst aus ENV lesen
CFG_DIR = os.environ.get("ARANDU_CFG_DIR", "data/config")

cfg = ConfigFacade(CFG_DIR).load_app_config()
setup_logging(cfg["paths"])

# Setzt Titel, Favicon, CSS (nur hier!)
page_config(cfg, title="ARANDU")

# Sidebar-Beschriftung
st.sidebar.title("ARANDU")
st.sidebar.caption("Navigation: 01 · Ingest, 02 · Arbeit auswählen")

# Topbar: Logo links, Auswahl rechts
render_topbar(cfg)

st.title("Willkommen zu ARANDU")
st.write("Links findest du **01 · Ingest** und **02 · Arbeit auswählen**. "
         "Oben steht das Logo, rechts die aktuelle Arbeit.")
