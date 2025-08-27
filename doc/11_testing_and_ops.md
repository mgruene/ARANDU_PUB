# Testing & Betrieb

## Smoke-Tests
1. Upload einer Beispiel-PDF → Vorschau-Metadaten sichtbar.
2. Review: Pflichtfelder setzen → Finalisieren.
3. Chunking/Upsert: Erfolgsmeldung, Quittung & Index erstellt.
4. Select: Arbeit auswählen → Header zeigt Titel/Student/Doc-ID.
5. Freitextfrage: Antwort + Belege; Diagnose zeigt docid-Filter.
6. Rubrikfrage: Rubrik wählen → Antwort kontextbezogen.

## Fehlerbilder
- Kein `current_thesis.json` → Hinweis, Seite stoppt.
- DocID nicht in Chroma → Warnung, ggf. neu ingesten.
- Embedding/LLM-Fehler → Logs prüfen (`data/logs/app.log`).
