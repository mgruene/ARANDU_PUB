# ARANDU – Überblick & Ziele

**Stand:** 2025-08-27  
**Ziel:** Weiterentwicklung eines lokalen RAG-Systems mit Streamlit-Frontend, zentralen JSON-Konfigurationen und ChromaDB (Docker). LLMs laufen lokal über **Ollama**. DSGVO-Compliance ist Pflicht.

## Leitprinzipien
- **Trennung von Code & Konfiguration** (JSON unter `data/config/`).
- **Deterministische I/O**: Funktionen nehmen/liefern einfache Dicts.
- **Reproduzierbare Pipelines**: Upload → Metadaten → Chunking → Upsert → Quittung.
- **Keine verdeckten Seiteneffekte**: State via Fassade, Datei-basiert.
- **Logging & Observability**: strukturierte Logs, klare Fehlermeldungen.
- **Lokale Verarbeitung**: ChromaDB im Container; Ollama auf dem Host.

## Grobarchitektur (ohne LangGraph)
- **UI (Streamlit)**: Upload, Metadaten-Review, Chunking/Upsert, Arbeit auswählen, Freitextfragen, Rubriken-Admin, Rubrik-Fragen.
- **Services (Fassaden)**: `metadata_facade`, `ingest_facade`, `search_facade`, `state_facade`, `config_facade`, `rubrics_facade`.
- **Modules (Adapter/Ports)**: `extract_metadata`, `chunking`, `embeddings_factory`, `chroma_client`, `llm_client`, `model_registry`.
- **Persistenz**: ChromaDB + Datei-State (`data/app_state/*.json`), Logs (`data/logs/app.log`), Uploads (`data/uploads/`).

## Dataflow – High Level
1. **Upload** → Dateibytes lesen → Vorschau-Metadaten (Regex, Fallback LLM).
2. **Review** → Nutzer korrigiert/komplettiert → Finalisierung.
3. **Chunking/Upsert** → Embeddings erzeugen → Chroma Upsert.
4. **Quittung** → `ingest_doc_<docid>.json` + Index aktualisieren.
5. **Auswahl** → `current_thesis.json` setzen.
6. **Fragen** → docid-gefilterte Retrievals → LLM-Antwort + Belege.

## Entwurfsmuster
- **Fassade** (UI ↔ Services), **Repository** (JSON), **Ports/Adapter** (Chroma/Ollama), **Transaction Script** (Pipelineschritte).
