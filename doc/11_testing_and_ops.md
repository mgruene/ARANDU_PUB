# Testing & Betrieb

## Smoke-Tests
1. **Upload** einer Beispiel-PDF → Vorschau-Metadaten sichtbar.
2. **Review**: Felder ergänzen → Finalisieren.
3. **Chunking/Upsert**: Erfolgsmeldung + Quittung vorhanden.
4. **Select**: Arbeit auswählen → Header zeigt Titel/Student/Doc-ID.
5. **Freitextfrage**: Antwort + Belege; Diagnosepanel zeigt docid-Filter.
6. **Rubrikfrage**: Rubrik wählen → Antwort kontextbezogen.

## Fehlerbilder & Checks
- Kein `current_thesis.json` → UI stoppt mit Hinweis.
- `docid` nicht in Chroma → Warnung, Seiten neu aufbauen.
- Embedding/LLM-Fehler → Logs prüfen (`data/logs/app.log`).

## Backups
- `data/app_state/`, `data/uploads/`, `data/chroma/` sichern.
