# Konfigurationen (JSON)

Alle Konfigurationen liegen unter `data/config/`.

## `app_config.json` (Beispiel)
```json
{
  "branding": {"app_name": "ARANDU"},
  "paths": {
    "app_state_dir": "data/app_state",
    "uploads_dir": "data/uploads",
    "logs_dir": "data/logs"
  },
  "chroma": {"host": "chroma", "port": 8000, "api": "/api/v2"},
  "ollama": {"base_url": "http://host.docker.internal:11434"},
  "ui": {"default_top_k": 5},
  "features": {"rubrics": true}
}
```

## `model_config.json` (Beispiel)
```json
{
  "embeddings": [
    {"alias": "e5-base", "provider": "sentence-transformers",
     "model": "intfloat/e5-base-v2", "dim": 768, "normalize": true}
  ],
  "llms": [
    {"alias": "llama3.1:8b", "provider": "ollama",
     "model": "llama3.1:8b", "params": {"temperature": 0.2, "max_tokens": 1024}}
  ],
  "retrieval": {"default_collection": "theses_v1", "top_k_default": 5, "max_context_chars": 8000}
}
```

## `examiners.json` (Beispiel)
```json
{
  "examiners": [
    {"name": "Prof. Dr. A. Beispiel", "variants": ["A Beispiel", "Prof Beispiel"]},
    {"name": "Prof. Dr. B. Muster", "variants": ["B Muster", "Prof Muster"]}
  ]
}
```
