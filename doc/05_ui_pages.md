# UI‑Seiten

## 01 – Upload & Ingest
- Upload PDF → **Metadaten‑Preview** (Regex‑Extraktion, Fallback LLM nur für fehlende Felder)
- Manuelle Korrekturen möglich, ohne unvollständige Metadaten kein Ingest
- Chunking (konfigurierbar) → Embeddings → Chroma Upsert → Receipt

## 02 – Arbeit auswählen
- Listet vorhandene **Receipts** (`data/app_state/…`) und prüft Existenz in Chroma
- Auswahl schreibt `current_thesis.json`

## 03 – Freie Fragen (ask_thesis)
- docid‑gefilterte Chroma‑Suche
- Kontexttrimmen gemäß `retrieval.max_context_chars`
- Antwort via LLM (aus UI wählbar)

## 06 – Rubriken verwalten (admin_rubrics)
- **Mittiges Layout**, Tabelle mit Spalten: Nummer, ID, Name, Beschreibung, LLM‑Alias, top_k, Kinder
- **Nummerierung** automatisch: 1 / 1.1 / 1.1.1
- **Regeln**: max. **3 Ebenen**, pro Knoten **max. 2** Kinder
- **CRUD**: Anlegen, Bearbeiten, Löschen, Verschieben (↑/↓)
- **LLM‑Alias**: Dropdown aus `model_config.json` (nur `llms` mit `supports_rubrics=true`)
- Speichert **nur den Alias** in `rubrics_config.json`
- Typische Fehlerquellen:
  - Gemischte Typen (z.B. `top_k` int/leer) → Tabelle castet auf String (behoben)
  - `use_container_width` → ersetzt durch `width="stretch"`

## 07 – Rubrik‑Evaluierung (rubric_eval)
- Header analog **ask_thesis**
- Auswahl: Rubrik, optionale Unterkategorie, Frage, Top‑K
- **Retrieval**: docid‑Filter (nur die aktive Arbeit), Embedding aus `retrieval.embedding_alias_default`
- Antwort via `rubric_eval_service.evaluate_rubric_question`
- Robust: UI zeigt Fehlerpanels (kein „weißes“ Rendering)
