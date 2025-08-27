# Bewertungskategorien & Unterkategorien

_Quelle: `data/config/rubrics_config.json` · Version: **1** · Stand: **2025-08-27T00:00:00Z**_

## Globale Defaults

| Parameter | Wert |
|---|---:|
| `llm_alias` | `critique-llm` |
| `top_k` | `6` |
| `max_context_chars` | `8000` |

## Kategorien (Übersicht)

| Kategorie-ID | Name | Beschreibung | LLM-Alias (effektiv) | top_k (effektiv) | max_context_chars (effektiv) |
|---|---|---|---|---:|---:|
| `content` | Inhalt | Inhaltliche Qualität der Arbeit (Fragestellung, Theorie, Methode, Analyse, Fazit). | `critique-llm` | `6` | `8000` |
| `form` | Formalia | Formale Qualität (Aufbau, Stil, Zitation, Layout). | `style-llm` | `4` | `8000` |
| `autonomy` | Eigenständigkeit | Originalität und Arbeitsweise. | `critique-llm` | `6` | `8000` |
| `presentation` | Vortrag (optional) | Bewertung einer begleitenden Präsentation. | `critique-llm` | `6` | `8000` |

### Inhalt (`content`)

_Effektive Kategorie-Parameter_: `llm_alias=critique-llm`, `top_k=6`, `max_context_chars=8000`

| Sub-ID | Name | Beschreibung | top_k (effektiv) |
|---|---|---|---:|
| `content_problem` | Fragestellung & Zielsetzung | Problem/These, Relevanz, Zielklarheit, Vorgehensplan. | `5` |
| `content_theory` | Theorie & Literatur | Stand der Forschung, Quellenqualität, theoretische Fundierung. | `6` |
| `content_method` | Methode/Analyse & Fazit | Methodik/Vorgehen, Analyse, Schlussfolgerungen, Implikationen. | `6` |

### Formalia (`form`)

_Effektive Kategorie-Parameter_: `llm_alias=style-llm`, `top_k=4`, `max_context_chars=8000`

| Sub-ID | Name | Beschreibung | top_k (effektiv) |
|---|---|---|---:|
| `form_structure` | Struktur & Verständlichkeit | Gliederung, roter Faden, Leseführung. | `4` |
| `form_citation` | Zitation & Quellen | Belege, Konsistenz, Aktualität/Qualität der Quellen. | `3` |
| `form_language` | Sprache & Formalia | Stil, Rechtschreibung/Grammatik, Abbildungen/Tabellen. | `3` |

### Eigenständigkeit (`autonomy`)

_Effektive Kategorie-Parameter_: `llm_alias=critique-llm`, `top_k=6`, `max_context_chars=8000`

| Sub-ID | Name | Beschreibung | top_k (effektiv) |
|---|---|---|---:|
| `autonomy_originality` | Originalität | Eigenständige Ideen, kritische Perspektive, Beitrag. | `6` |
| `autonomy_process` | Prozessfaktoren | Umgang mit Feedback, Termin-/Selbstorganisation. | `6` |

### Vortrag (optional) (`presentation`)

_Effektive Kategorie-Parameter_: `llm_alias=critique-llm`, `top_k=6`, `max_context_chars=8000`

| Sub-ID | Name | Beschreibung | top_k (effektiv) |
|---|---|---|---:|
| `pres_content` | Inhaltliche Darstellung | Sachliche Richtigkeit, Schwerpunktsetzung. | `6` |
| `pres_delivery` | Sprache & Auftreten | Verständlichkeit, Stimme, Blickkontakt, Sprechweise. | `6` |
| `pres_slides` | Folien & Zeit | Visualisierung, Struktur, Zeitmanagement. | `6` |

## Nutzung (kurz)

- Für jede Frage zu einer Rubrik/Unterkategorie wird **docid-gefiltert** aus Chroma abgerufen (siehe `07_rubric_eval.py`).
- **top_k** bestimmt die Anzahl zu ladender Kontexte; **llm_alias** wählt das LLM-Profil aus.
- **max_context_chars** begrenzt den zusammengefügten Kontext für das LLM.
