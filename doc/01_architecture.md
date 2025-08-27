# Architektur & Verzeichnisstruktur

## Verzeichnisse (Top-Level)
- `app_server/app/ui` – Streamlit-Seiten & UI-Komponenten
- `app_server/app/services` – Fassaden (State, Config, Ingest, Search, Rubrics, …)
- `app_server/app/modules` – Adapter/Ports (Chroma, Embeddings, LLM, Chunking, …)
- `data/` – `config/`, `uploads/`, `app_state/`, `logs/`, `tmp/`

## Komponentenübersicht
- **UI (Streamlit)**: Schlanke Seiten, die Dicts an/aus Services geben.
- **Services (Fassaden)**: Use-Cases; orchestrieren Module; validieren I/O.
- **Modules (Ports/Adapter)**: Chroma/Ollama/Embeddings, Chunking, Model-Registry.
- **Repository (JSON)**: State & Config via `state_facade`/`config_facade`.

## Entwurfsmuster
- **Fassade** (UI ↔ Services) – stabile API gegenüber der UI.
- **Repository** (JSON-Dateien) – atomare Writes, validierte Schemas.
- **Ports/Adapter** – sauberer Rand zu Chroma/LLM/Embedding.
- **Transaction Script** – klar sequenzierte Schritte je Use-Case.
