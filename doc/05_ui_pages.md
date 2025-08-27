# UI-Seiten & Verantwortlichkeiten (tatsächlicher Stand)

> Quelle: `app_server/app/ui/pages/`

| Datei | Seite | Zweck | Datenabhängigkeiten |
|---|---:|---|---|
| `01_upload_ingest.py` | 01 | **Upload & Ingest**: PDF-Upload, Metadaten-Preview/-Bearbeitung, Chunking & Upsert nach Chroma, Quittung/Index | `app_config`, `examiners.json`, `model_config.json`, `uploads_dir`, `state_facade`, `ingest_facade`, `metadata_facade` |
| `02_select_thesis.py` | 02 | **Arbeit auswählen**: Quittungen/Index lesen, Auswahl persistieren | `ingest_doc_*.json`, `ingests_index.json`, schreibt `current_thesis.json` |
| `03_ask_thesis.py` | 03 | **Freitextfragen** gegen die **aktuelle Arbeit** | liest `current_thesis.json`, Retrieval (Chroma) |
| `06_admin_rubrics.py` | 06 | **Rubriken-Admin**: Rubriken/Subkategorien/Beispiele (CRUD); Doc-ID bei Beispielen sinnvollerweise aus State vorbelegen | optional `current_thesis.json`, `rubrics_facade`, `rubric_examples_facade` |
| `07_rubric_eval.py` | 07 | **Rubrik-Fragen**: Abfragen mit docid-Filter | **muss** `current_thesis.json` lesen, Retrieval (Chroma), `rubric_eval_service` |

## Nicht vorhanden (Stand heute)
- **04** – separater *Metadata Review*-Screen: Funktion in **Seite 01** integriert.
- **05** – separater *Chunk & Upsert*-Screen: Funktion in **Seite 01** integriert.
