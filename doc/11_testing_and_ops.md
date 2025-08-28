# Testing, Betrieb & Troubleshooting

## Smoke‑Tests (Container)

### ModelRegistry
```bash
CID=$(docker compose ps -q app_server)
docker exec -it "$CID" sh -lc 'python3 - <<PY
from app.modules.model_registry import ModelRegistry
mr = ModelRegistry("/code/data/config")
print("LLMs:", [m.get("alias") for m in mr.list_llms()])
print("LLMs (rubrics):", [m.get("alias") for m in mr.list_llms(True)])
print("Embeddings:", mr.list_embedding_aliases())
print("Retrieval:", mr.get_retrieval_cfg().get("default_collection"))
PY'
```

### Ollama – Chat & Embeddings
```bash
docker exec -it "$CID" sh -lc 'python3 - <<PY
from app.modules.llm_client import OllamaClient
c=OllamaClient("http://host.docker.internal:11434")
print(c.chat(model="qwen2.5:7b-instruct", messages=[{"role":"user","content":"Sag Hallo auf Deutsch."}], options={"temperature":0.2})["response"][:60])
print(len(c.embed(["Hallo Welt"], model="jina/jina-embeddings-v2-base-de:latest")[0]))
PY'
```

### Router – Legacy‑Alias
```bash
docker exec -it "$CID" sh -lc 'python3 - <<PY
from app.modules.llm_router import resolve_model
print("legacy:", resolve_model("style-llm")["model"])
PY'
```

## Typische Fehler & Lösungen

- **Weißes UI / leere Seite** → Es gab früher ungefangene Exceptions.
  - Jetzt: Fehlerpanel im UI (Expander zeigt Trace)
- **Arrow/Pandas**: „Could not convert … top_k …“  
  → Tabelle castet `top_k` als String (Admin‑Seite fix)
- **`AttributeError: NoneType.rstrip`**  
  → `_ollama_chat` robust gegen `None` (URL‑Fallback + `OllamaClient`)
- **`LLM alias '…' nicht gefunden`**  
  → `llm_router` mappt Legacy‑Aliasse; `ModelRegistry.llm_by_alias` vorhanden

## GitHub Actions (README‑Auto‑Update)
- Deaktiviert (Workflows nach `/.github/workflows_disabled/…` verschoben).
- Reaktivierung: zurück nach `/.github/workflows/` verschieben.

## Docker/Volumes – Hinweis
- `app_server` mountet `./app_server → /code` (rw), `./data → /data` (rw)
- `ARANDU_CFG_DIR` steuert das Konfig‑Verzeichnis (z.B. `"config"`)
