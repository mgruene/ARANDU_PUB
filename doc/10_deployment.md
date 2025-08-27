# Deployment & Laufzeit

## Docker
- `chromadb/chroma:0.6.3` als separater Container (persistentes Volume).
- App-Container mit Zugriff auf `http://chroma:8000` (API v2).
- Ollama läuft auf dem Host und ist via `http://host.docker.internal:11434` erreichbar.

## Startablauf
1. `docker-compose up -d`
2. App unter `http://localhost:8501`
3. Chroma-API unter `http://localhost:8000`

## Umgebungsvariablen
- `ARANDU_CFG_DIR` (Default `data/config`)
- Weitere per `.env`/Compose zuweisen.
