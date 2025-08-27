# Logging & Observability

## Grundsätze
- Strukturierte Logs (JSON-fähig), Level: DEBUG/INFO/WARN/ERROR.
- Jeder Service loggt: Input-Parameter (ohne PII), Ergebnis-Keys, Pfade.

## Beispiel-Logzeilen
```json
{"ts":"2025-08-25T12:22:46Z","level":"INFO","logger":"state_facade",
 "msg":"write_current","docid":"68adadb7c191","path":"data/app_state/current_thesis.json"}

{"ts":"2025-08-25T12:22:47Z","level":"INFO","logger":"chroma_client",
 "msg":"upsert","collection":"theses_v1","chunks":342,"docid":"68adadb7c191"}
```

## Diagnose-Panels in UI
- Anzeigen: `collection`, `embedding_alias`, `top_k`, `docid`, Kontextlänge.
