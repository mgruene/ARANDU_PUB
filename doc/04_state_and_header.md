# State & Header‑Darstellung

## App‑State
- `data/app_state/current_thesis.json`: aktive Arbeit (inkl. `docid`, `metadata`)
- `data/app_state/ingest_doc_<docid>.json`: Quittungen für Ingest
- Zugriff via `StateFacade` (liest/schreibt Verzeichnis aus `app_config.paths.app_state_dir`)

## Header‑Block (einheitlich)
Seiten **02_select_thesis**, **03_ask_thesis**, **07_rubric_eval** verwenden denselben Headerstil:
- Kopf: **Studierende/r**, **Titel**
- darunter ein **Expander** „Metadaten der Arbeit“ mit:
  - `docid`
  - Arbeitstyp, Abgabedatum
  - Erst-/Zweitprüfer
  - Studiengang

> Ziel: konsistente Orientierung & Kontext für alle Interaktionen.
