# Rubriken – Admin & Auswertung

## Admin (Seite 06)
- CRUD für Rubriken (`id`, `name`, `description`, `llm_alias`, `top_k`).
- Subkategorien (`id`, `name`, `description`).
- Beispiele mit Label (`positive`/`negative`) und **Quelle**:
```json
{"rubric_id": "methodik", "label":"positive",
 "text": "Beispielauszug ...",
 "source": {"doc_id": "68adadb7c191", "chunk_id": "c-00042"}}
```
- **Doc-ID** standardmäßig aus `current_thesis.json` vorbelegt.

## Rubrik-Fragen (Seite 07)
- Pflicht: `current_thesis` existiert → Doc-ID setzen.
- Retrieval **mit docid-Filter** (`where={"docid": <doc_id>}`).
- `evaluate_rubric_question(...)` erhält `question`, `rubric_id`, optional `subcategory_id`, `top_k`.
- Antwort + Belege/Diagnose anzeigen.
