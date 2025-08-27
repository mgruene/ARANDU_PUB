# Deployment & Laufzeit

## Docker & Endpunkte
- `chromadb/chroma:0.6.3` als Container (persistentes Volume).
- App-Container greift auf `http://chroma:8000` (API v2) zu.
- **Ollama** auf dem Host: `http://host.docker.internal:11434`.
- Streamlit-App: `http://localhost:8501`.

## Start
1. `docker-compose up -d`
2. App öffnen, Chroma/Logs prüfen

## Verfügbare Python-Pakete
- `chromadb==0.6.3`
- `sentence-transformers==3.0.1`
- `langchain>=0.3,<0.4`, `langchain-community>=0.3,<0.4`
- `langchain-ollama`
- `streamlit`
- `torch==2.4.1 (CUDA 12.4 Wheel)`
- `pypdf`
- `huggingface-hub==0.23.4`
