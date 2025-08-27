# Retrieval, Embeddings & LLM

## Embeddings
- `EmbeddingsFactory`: liest `model_config.json.embeddings` (alias, model, dim, normalize).
- Einbettung: `embed(texts: list[str]) -> list[list[float]]`.

## Chroma
- `ChromaWrapper`: `get_or_create_collection(name)`.
- Query: `collection.query(query_embeddings=[vec], n_results=K, where={"docid": DOC})`.

## Kontextbildung
- Dokumente aus Treffern verketten (\n\n), auf `max_context_chars` kürzen.
- Belege/Metadaten in der UI mit anzeigen.

## LLM (Ollama)
- In `model_config.json.llms` konfiguriert (alias, model, params).
- Temperatur niedrig (z. B. 0.2) für Reproduzierbarkeit.
