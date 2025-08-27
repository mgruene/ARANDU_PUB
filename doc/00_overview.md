# ARANDU – Überblick & Ziele

**Stand:** 2025-08-27

**Ziel:** Lokales RAG-System zur Verarbeitung wissenschaftlicher Arbeiten mit **Streamlit-Frontend**, **ChromaDB** (Docker) und **Ollama** (Host) für LLMs. **DSGVO-Compliance** ist verbindlich.

## Leitprinzipien
- **Trennung von Code & Konfiguration** (JSON unter `data/config/`).
- **Deterministische I/O**: Funktionen/Services erhalten & liefern **Dicts**.
- **Reproduzierbare Pipeline**: Upload → Metadaten → Chunking → Upsert → Quittung/Index.
- **Expliziter App-State**: Datei-basiert per Fassade (`data/app_state/`).
- **Logging & Observability**: strukturierte Logs, klare Fehlermeldungen.
- **Lokalität**: Keine Cloud-APIs; Chroma (Container), Ollama (Host).
