# Zustands- & Header-Logik

## Dateien unter `data/app_state/`
- `ingest_doc_<docid>.json` – Quittung je Arbeit
- `ingests_index.json` – Index aller Ingests
- `current_thesis.json` – aktuell ausgewählte Arbeit

## Lesen/Schreiben (State-Fassade)
- `get_current() -> dict|None`
- `set_current(docid: str) -> str`

Atomare JSON-Writes, strukturierte Logs.

## Header/Topbar
- `app_server/app/ui/components/topbar.py` zeigt Status/Metadaten-Expander; liest on render den State.
- Bei fehlender Auswahl: Hinweis im Header.
