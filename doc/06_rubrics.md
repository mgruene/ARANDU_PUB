# Rubriken – Admin & Auswertung

## Admin (Seite 06)
- CRUD für Rubriken (`id`, `name`, `description`, `llm_alias`, `top_k`).
- Subkategorien (`id`, `name`, `description`).
- Beispiele (Label `positive|negative`) inkl. Quelle:
```json
{"rubric_id":"methodik","label":"positive","text":"Auszug ...","source":{"doc_id":"<docid>","chunk_id":"c-00042"}}
```
- **Doc-ID** nach Möglichkeit aus `current_thesis.json` vorbelegen.

## Rubrik-Fragen (Seite 07)
- Erfordert gesetzte **aktuelle Arbeit** (`current_thesis.json`).
- **DocID-gefiltertes** Retrieval (siehe **07_retrieval_and_llm.md**).
- `evaluate_rubric_question(...)` erhält `rubric_id`, optional `subcategory_id`, `question`, optional `top_k`.
