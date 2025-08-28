# ARANDU – Überblick

ARANDU ist eine RAG‑Anwendung für Abschlussarbeiten mit lokaler **ChromaDB** und lokalen **Ollama‑LLMs**.  
Zentrale Prinzipien: **Trennung von Code & Konfiguration**, **deterministische I/O**, **transparenter State**, **robustes Logging**.

## Architektur auf einen Blick

- **UI (Streamlit)**: Upload/Ingest, Auswahl der Arbeit, freie Fragen, Rubriken‑Verwaltung, Rubriken‑Evaluierung
- **Services (Fassaden)**: `config_facade`, `state_facade`, `ingest_facade`, `search_facade`, `rubrics_facade`, `rubric_eval_service`
- **Modules (Ports/Adapter)**: `model_registry`, `llm_router`, `llm_client` (Ollama), `embeddings_factory`, `chroma_client`, `extract_metadata`
- **Persistenz**: ChromaDB (Container), App‑State & Konfig (`data/…`), strukturierte Logs

## Wichtige Verzeichnisse

```
app_server/app/ui/pages/…          # Streamlit-Seiten
app_server/app/services/…          # Fassaden, Transaction Scripts
app_server/app/modules/…           # Ports/Adapter/Clients
data/config/…                      # zentrale JSON-Konfigurationen
data/app_state/…                   # App-Zustand (current_thesis.json, Receipts)
data/chroma/…                      # ChromaDB Persistenz
data/logs/app.log                  # strukturierte Logs
```

## Neue/aktualisierte Bausteine (Stand: 2025‑08‑28)

- **Rubriken-Admin (Seite 06)**  
  - Mittiges Layout, Tabelle mit Nummerierung (1 / 1.1 / 1.1.1)  
  - CRUD inkl. **max. 2 Unterkategorien pro Knoten**, **max. 3 Ebenen**  
  - **LLM‑Alias** aus `data/config/model_config.json` (nur `supports_rubrics=true`)  
  - Speichern **nur des Alias** in `rubrics_config.json` (keine Modelldetails)

- **Rubriken‑Evaluierung (Seite 07)**  
  - Headerblock wie in *ask_thesis* (Titel, Student/in, Expander‑Metadaten)  
  - docid‑gefiltertes Retrieval (Chroma), robustes Fehler‑Handling (kein Weißbild mehr)  
  - Bewertung via `rubric_eval_service.evaluate_rubric_question`

- **`model_config.json` überarbeitet**  
  - Pro Modell: `usage` (`llm`/`embedding`), `type`, optional `supports_rubrics`  
  - `retrieval`‑Defaults zentral (z.B. `top_k_default`, `default_collection`)  
  - Klassifizierung der lokal installierten Modelle inkl. Embeddings

- **`ModelRegistry` erweitert**  
  - `list_llms(supports_rubrics=None)`, `list_embeddings()`, Aliasse, `get_retrieval_cfg()`  
  - `llm_by_alias` & `embedding_by_alias` akzeptieren **String oder Dict** (UI‑Resilienz)

- **`llm_router.resolve_model`**  
  - Legacy‑Alias‑Mapping (z.B. `style-llm → chat-qwen2.5-7b`)  
  - Fallbacks: erstes freigegebenes Rubriken‑LLM → erstes LLM

- **`rubric_eval_service`**  
  - Robustes `_ollama_chat`: kein `.rstrip()` auf `None`, konsolidierte Rückgabe `{ok, answer, raw}`  
  - URL‑Ermittlung: `base_url` → `url` → `OLLAMA_BASE_URL` → Default

- **UI‑Stabilität**  
  - Arrow/Pandas Casting fix (z.B. `top_k` in Tabellen als String)  
  - `width="stretch"` statt `use_container_width` (Deprecation)

Siehe Details in den folgenden Dokumenten.
