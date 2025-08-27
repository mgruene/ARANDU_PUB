# Ingest-Pipeline

## Schritte
1. **Upload**: PDF lesen → Bytes speichern → Vorschau.
2. **Metadaten**: Regex (Seite 1); Fallback LLM nur für fehlende Felder.
3. **Review**: Nutzer ergänzt/überschreibt → Finalisierung (Pflichtfelder gesetzt).
4. **Chunking**: konfigurierbare Strategie; saubere Grenzen.
5. **Embeddings**: laut `model_config.json`.
6. **Upsert (Chroma)**: Collection = `retrieval.default_collection`.
7. **Quittung/Index**: `ingest_doc_<docid>.json` + `ingests_index.json`.
