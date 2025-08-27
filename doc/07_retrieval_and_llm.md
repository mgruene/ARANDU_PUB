# Retrieval, Embeddings & LLM

## Embeddings
- `EmbeddingsFactory`: liest `model_config.json.embeddings` (alias, model, dim, normalize).
- `embed(texts: list[str]) -> list[list[float]]`.

## Chroma
- `ChromaWrapper.get_or_create_collection(name)`.
- **Query mit DocID-Filter** (z. B. in Seite 03/07):
```python
raw = collection.query(
    query_embeddings=[vec],
    n_results=K,
    where={"docid": DOC_ID}
)
```
- Kontext bilden (`"\n\n".join(docs)`), ggf. kürzen.

## LLM (Ollama)
- In `model_config.json.llms` konfiguriert (alias, model, params).
- Niedrige Temperatur (z. B. 0.2) für reproduzierbare Antworten.
