# Architektur & Verzeichnisstruktur

## Verzeichnisse
- `/app/ui` – Streamlit-Seiten & UI-Komponenten
- `/app/services` – Fassaden (State, Config, Ingest, Search, Rubrics, …)
- `/app/modules` – Adapter/Ports (Chroma, Embeddings, LLM, Chunking, …)
- `/app/data` – `config/`, `uploads/`, `app_state/`, `logs/`, `tmp/`

## Komponentenübersicht
- **UI**: einfache Seiten, die nur Dicts von/zu Services bewegen.
- **Services (Fassaden)**: implementieren Business-Use-Cases; rufen Modules.
- **Modules**: umschließen externe Systeme/Bibliotheken (Chroma, Ollama).
- **Repository**: JSON-Dateien (Konfig/State) über State-/Config-Fassade.

## Entwurfsmuster
- **Fassade**: UI sieht nur wenige Service-Methoden (stabile API).
- **Repository**: Datei-I/O als explizite Abhängigkeit, atomare Writes.
- **Ports/Adapter**: `ChromaWrapper`, `EmbeddingsFactory`, `LLMClient`.
- **Transaction Script**: klar sequenzierte Schritte je Anwendungsfall.

## Abhängigkeiten (relevant)
- `chromadb==0.6.3`, `sentence-transformers==3.0.1`, `langchain>=0.3,<0.4`,
  `langchain-community>=0.3,<0.4`, `langchain-ollama`, `streamlit`,
  `torch==2.4.1 (cu124)`, `pypdf`, `huggingface-hub==0.23.4`.
