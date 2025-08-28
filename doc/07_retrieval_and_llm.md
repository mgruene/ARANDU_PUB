# Retrieval & LLM‑Aufrufe

## Retrieval (Chroma)
- **Embedding**: aus `retrieval.embedding_alias_default`, Fallbacks aus Liste, sonst erstes Embedding
- **Einbettung** via `EmbeddingsFactory(app_cfg, embedding_cfg)` (benötigt `ollama.base_url`)
- **Suche**: `collection.query(query_embeddings=[vec], n_results=top_k, where={"docid": doc_id})`
- **Kontextlimit**: `retrieval.max_context_chars` (Trimmen, keine Formatzerstörung)

## LLM‑Aufrufe (Ollama)
- Einheitlich über `OllamaClient` (Chat/Generate/Embeddings)
- **`rubric_eval_service`**:
  - `_ollama_chat` robust (URL‑Fallback: `base_url` → `url` → Env → Default)
  - Rückgabe **immer** `{ ok, answer, raw }` (Text unter `answer`)
- **`ModelRegistry`**
  - `list_llms(supports_rubrics=None)`, `list_embeddings()`, Aliasse, `get_retrieval_cfg()`
  - `llm_by_alias`/`embedding_by_alias` akzeptieren **String oder Dict**
- **`llm_router.resolve_model`**
  - Legacy‑Alias‑Map, Fallbacks
