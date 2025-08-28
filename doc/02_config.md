# Konfiguration

Alle Konfigurationen liegen unter `data/config/`. Die wichtigsten Dateien:

## `app_config.json`
```json
{
  "paths": {
    "app_state_dir": "/data/app_state"
  },
  "ollama": {
    "base_url": "http://host.docker.internal:11434"
  },
  "chroma": {
    "host": "chroma",
    "port": 8000,
    "tenant": "default_tenant",
    "database": "default_database"
  }
}
```
> **Ollama‑URL**: Die Anwendung akzeptiert `base_url` **oder** `url`. Fallback: `OLLAMA_BASE_URL` Env → `http://host.docker.internal:11434`.

## `model_config.json` – Schema

### Embeddings
- `alias` (String, eindeutig)
- `provider` (`ollama`)
- `model` (exakter Ollama‑Modelname)
- `dim` (z.B. 768, 1024)
- `normalize` (bool)
- `usage` = `"embedding"`
- `type` = `"embedding"`
- `notes` (optional)

### LLMs
- `alias` (String, eindeutig)
- `provider` (`ollama`)
- `model` (exakter Ollama‑Modelname)
- `usage` = `"llm"`
- `type` ∈ {`"chat"`, `"completion"`, `"llm"`}
- `supports_rubrics` (bool; steuert Sichtbarkeit im Rubriken‑Admin)
- `context_window` (optional, z.B. 4096/8192)
- `params` (z.B. `{"temperature": 0.2, "num_ctx": 4096}`)
- `notes` (optional)

### Retrieval
- `default_collection` (z.B. `theses_v1`)
- `embedding_alias_default` (z.B. `jina-de`)
- `embedding_alias_fallbacks` (Array)
- `top_k_default` (z.B. 5)
- `max_context_chars` (z.B. 8000)

#### Beispiel‑Ausschnitt
```json
{
  "embeddings": [
    {"alias": "jina-de", "provider": "ollama", "model": "jina/jina-embeddings-v2-base-de:latest", "dim": 768, "normalize": true, "usage": "embedding", "type": "embedding"},
    {"alias": "nomic",   "provider": "ollama", "model": "nomic-embed-text:latest", "dim": 768, "normalize": true, "usage": "embedding", "type": "embedding"},
    {"alias": "mxbai-large","provider": "ollama", "model": "mxbai-embed-large:latest", "dim": 1024, "normalize": true, "usage": "embedding", "type": "embedding"}
  ],
  "llms": [
    {"alias": "chat-qwen2.5-7b", "provider": "ollama", "model": "qwen2.5:7b-instruct", "usage": "llm", "type": "chat", "supports_rubrics": true, "context_window": 4096, "params": {"temperature": 0.2, "num_ctx": 4096}},
    {"alias": "chat-llama3-instruct", "provider": "ollama", "model": "llama3:instruct", "usage": "llm", "type": "chat", "supports_rubrics": true, "context_window": 8192, "params": {"temperature": 0.2, "num_ctx": 8192}},
    {"alias": "chat-mistral", "provider": "ollama", "model": "mistral:latest", "usage": "llm", "type": "chat", "supports_rubrics": true, "context_window": 4096, "params": {"temperature": 0.2}}
  ],
  "retrieval": {
    "default_collection": "theses_v1",
    "embedding_alias_default": "jina-de",
    "embedding_alias_fallbacks": ["nomic","mxbai-large"],
    "top_k_default": 5,
    "max_context_chars": 8000
  }
}
```

### Klassifizierung installierter Modelle (Beispiele)
- **Embeddings:** `jina/jina-embeddings-v2-base-de:latest`, `nomic-embed-text:latest`, `mxbai-embed-large:latest`
- **LLM/Chat (Rubriken geeignet):** `qwen2.5:7b-instruct`, `llama3:instruct`, `mistral:latest`, `mistral:7b-instruct`, `hf.co/TheBloke/em_german_leo_mistral-GGUF:Q4_K_M`, `llama2:latest`, `jobautomation/OpenEuroLLM-German:latest`
- **Nicht empfohlen für Rubriken (zu klein/experimentell):** `gemma3:1b`, `llama3.2:1b`, `llama3.2:3b`, `llama3.2:latest`, `hf.co/tensorblock/SauerkrautLM-Nemo-12b-Instruct-GGUF:Q4_K_M` (zunächst `supports_rubrics=false`)
