# Zustands- & Header-Logik

## Dateien unter `data/app_state/`
- `ingest_doc_<docid>.json` – Quittung je Arbeit
- `ingests_index.json` – Index aller Ingests
- `current_thesis.json` – aktuell ausgewählte Arbeit

### Beispiel `current_thesis.json`
```json
{
  "docid": "68adadb7c191",
  "collection": "theses_v1",
  "chunk_count": 342,
  "metadata": {
    "thesis_title": "Titel der Arbeit",
    "student_name": "Nachname, Vorname",
    "year": 2024,
    "examiners": {"first": "Erstprüfer", "second": "Zweitprüfer"},
    "num_pages": 73,
    "study_program": "B.Sc. ...",
    "upload_filename": "Bachelorarbeit_X.pdf"
  },
  "updated_at": "2025-08-26T18:32:11Z"
}
```

## Lesen/Schreiben (State-Fassade)
- `get_current() -> dict|None`
- `set_current(docid: str) -> str`

Atomare JSON-Writes, strukturierte Logs.

## Header-Darstellung
- Oben rechts kurze Zusammenfassung (Titel, Student, Jahr, Prüfer).
- Expander „Metadaten“ zeigt komplettes `metadata`-Dict.
- Falls **kein** `current_thesis.json`: Warnhinweis.

## Mermaid – Zustandsfluss
```mermaid
flowchart LR
  A[select_thesis] -->|set_current(docid)| B[state_facade]
  B -->|writes| C[current_thesis.json]
  C -->|read| D[ask_thesis]
  C -->|read| E[rubric_eval]
```
