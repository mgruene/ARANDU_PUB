# Rubriken – Datenmodell & Verwaltung

## Zieldarstellung
Bewertung entlang **Kategorien** (Rubriken) mit optionalen Unterkategorien (max. **2 Ebenen** unter der Wurzel; Gesamtmax: **1.1.1**). Jede Rubrik kann optional einen **LLM‑Alias** und **top_k** hinterlegen.

## JSON‑Struktur (`rubrics_config.json`)
```json
{
  "version": "1.0",
  "updated_at": "2025-08-28T00:00:00Z",
  "defaults": {
    "llm_alias": "chat-qwen2.5-7b",
    "top_k": 5
  },
  "rubrics": [
    {
      "id": "form",
      "name": "Form",
      "description": "Formale Kriterien",
      "llm_alias": "chat-qwen2.5-7b",
      "top_k": 5,
      "children": [
        {
          "id": "form_struktur",
          "name": "Struktur",
          "description": "Aufbau, Gliederung"
        }
      ]
    }
  ]
}
```

### Regeln
- **Nummerierung**: implizit über Position (1, 1.1, 1.1.1)
- **Max. 3 Ebenen** (z.B. 1 → 1.1 → 1.1.1)
- **Max. 2 Kinder** pro Knoten
- **LLM‑Alias**: nur Alias (String), kein Modell‑Dict

## LLM‑Selektion
- Priorität: Rubrik‑Alias → `defaults.llm_alias` → erstes `supports_rubrics=true`‑LLM → erstes LLM
- `llm_router.resolve_model`:
  - akzeptiert **String oder Dict**
  - kennt **Legacy‑Aliasse** (z.B. `style-llm → chat-qwen2.5-7b`)
  - Fallbacks wie oben

## UI – Admin
- CRUD, Verschieben, max. 2 Kinder / 3 Ebenen durchgesetzt
- Dropdown der Aliasse aus `model_config.json` (gefiltert)

## Typische Fehler & Abwehr
- **Alt‑Aliasse** (z.B. `style-llm`): Router mappt automatisch  
  → optional `scripts/migrate_rubric_aliases.py` ausführen, um JSON zu bereinigen.
- **Gemischte Typen** in `top_k`: Tabelle castet auf String (Admin‑Seite fix).
