# UI-Seiten & Verantwortlichkeiten

| Seite | Zweck | Datenabhängigkeiten |
|---|---|---|
| 01_upload | Dateien hochladen, Preview | `app_config`, Uploads-Pfad |
| 02_select_thesis | Arbeit aus Quittungen auswählen | `ingest_doc_*.json`, `ingests_index.json`, schreibt `current_thesis.json` |
| 03_ask_thesis | Freitextfragen gegen aktuelle Arbeit | liest `current_thesis.json`, Retrieval (Chroma) |
| 04_metadata_review | Metadaten prüfen/ergänzen | `examiners.json`, LLM-Fallback |
| 05_chunk_and_upsert | Chunking & Upsert in Chroma | `model_config.json` |
| 06_admin_rubrics | Rubriken & Beispiele | liest `current_thesis.json` (Doc-ID Vorbelegung) |
| 07_rubric_eval | Rubrik-basierte Fragen | **muss** `current_thesis.json` lesen (Doc-ID-Filter) |

### Header-Pattern (Topbar)
- `render_topbar(app_cfg)` und `apply_css_only(app_cfg)` in jeder Seite aufrufen.
- In Seiten mit Abfragen **immer** `current_thesis.json` lesen und anzeigen.
