# Ingest-Pipeline

## Schritte
1. **Upload** (`upload_ingest`): PDF lesen → Bytes speichern → Voransicht.
2. **Metadaten** (`metadata_facade`): Regex auf Seite 1; Fallback LLM für fehlende Felder.
3. **Review**: Benutzer ergänzt/überschreibt → `finalize_with_overrides`.
4. **Chunking** (`chunking`): konfigurierbare Strategie; saubere Grenzen.
5. **Embeddings** (`embeddings_factory`): laut `model_config.json`.
6. **Upsert** (`chroma_client`): `collection` aus `retrieval.default_collection`.
7. **Quittung** (`state_facade`): `ingest_doc_<docid>.json` + Index.

## I/O-Verträge (vereinfacht)
- **Input (finale Metadaten)**:
```json
{
  "docid": "68adadb7c191",
  "metadata": {
    "thesis_title": "Titel der Arbeit",
    "student_name": "Nachname, Vorname",
    "year": 2024,
    "examiners": {"first": "Erstprüfer", "second": "Zweitprüfer"},
    "study_program": "B.Sc. ...",
    "num_pages": 73
  },
  "upload_filename": "Bachelorarbeit_X.pdf"
}
```
- **Output (Quittung)**:
```json
{
  "docid": "68adadb7c191",
  "collection": "theses_v1",
  "chunk_count": 342,
  "metadata": { "...": "..." },
  "ingest_ts": "2025-08-25T12:22:46Z"
}
```
