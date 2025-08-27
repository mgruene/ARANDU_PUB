# DSGVO & Sicherheit

## Datenlokalität
- Verarbeitung lokal: Dateien, ChromaDB (Container), Ollama (Host). Keine Cloud-APIs.

## Datenminimierung
- Nur notwendige Metadaten speichern (Student, Titel, Prüfer).

## Rechte/Löschung
- Funktionen zum Löschen von Upload + Chroma-Einträgen + State/Quittungen vorsehen.

## Zugriffsschutz
- Lokale Nutzung; bei Serverbetrieb: Reverse-Proxy + Auth, TLS.

## Transparenz
- Felder & Speicherorte in **02_config.md** und **04_state_and_header.md** dokumentiert.
