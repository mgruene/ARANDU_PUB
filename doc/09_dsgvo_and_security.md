# DSGVO & Sicherheit

## Datenlokalität
- Verarbeitung lokal: Dateien, ChromaDB (Docker), Ollama (Host). Keine Cloud-APIs.

## Personenbezug minimieren
- Nur notwendige Metadaten speichern (Student, Titel, Prüfer).
- Keine sensiblen Daten ohne Erforderlichkeit.

## Rechte & Löschung
- Löschfunktion für Upload + Chroma-Einträge + State/Quittungen vorsehen.
- Protokollierung von Löschvorgängen (Audit).

## Zugriffsschutz
- Lokale Entwicklungsumgebung; für Serverbetrieb Reverse-Proxy + Basic-Auth/SSO.
- Logs ohne PII.

## Transparenz
- Dokumentiere Datenfelder und Speicherorte in der Doku (siehe State & Config).
