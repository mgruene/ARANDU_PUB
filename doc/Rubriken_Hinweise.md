# Hinweise zu Bewertungsrastern (Rubriken) – ARANDU

**Ziel:** Verwaltung und Nutzung von Bewertungskategorien (Rubriken) mit optionalen Unterkategorien für die Begutachtung wissenschaftlicher Arbeiten. Pro (Unter)Kategorie können **LLM** und **Top‑K** individuell festgelegt werden. Zusätzlich können **Bewertungsbeispiele** (positiv/negativ) gepflegt werden, die dem LLM als Few‑Shot‑Kontext dienen.

## 1. Raster (Default)
- **Inhalt**: Fragestellung & Zielsetzung · Theorie & Literatur · Methode/Analyse & Fazit  
- **Formalia**: Struktur & Verständlichkeit · Zitation & Quellen · Sprache & Formalia  
- **Eigenständigkeit**: Originalität · Prozessfaktoren  
- **Vortrag (optional)**: Inhaltliche Darstellung · Sprache & Auftreten · Folien & Zeit

> Das Default‑Raster liegt in `data/config/rubrics_config.json` und kann im Admin‑Frontend angepasst werden.

## 2. LLM/Top‑K je Rubrik
- Jede Rubrik/Unterkategorie kann einen **LLM‑Alias** (aus `data/config/model_config.json`) sowie einen **Top‑K**‑Wert (Retriever) besitzen.
- Fallback: `rubrics_config.defaults`.

## 3. Bewertungsbeispiele
- Label: **positive**/**negative**.  
- Optional: `source.doc_id` und `source.chunk_id` als Referenz auf die Arbeit (DSGVO: nur lokal).
- Gute Beispiele sind **konkret**, **kurz** (≤ 3 Sätze) und **kriterienspezifisch**.

**Beispiel (positiv):** „Die Forschungsfrage ist präzise operationalisiert; der Arbeitsplan ist stringent.“  
**Beispiel (negativ):** „Zielsetzung bleibt unklar; es fehlt eine methodische Begründung.“

## 4. Frontend-Bedienung
- **Rubriken-Admin** (`06_admin_rubrics.py`): Anlegen/Ändern/Löschen von Rubriken/Unterkategorien; Beispiele pflegen.
- **Rubrik‑Fragen** (`07_rubric_eval.py`): Rubrik auswählen, ggf. Unterkategorie/Doc‑ID setzen, Frage formulieren → LLM‑Antwort mit Kontext.

## 5. Architekturhinweise
- **Trennung von Code/Config:** Rubriken und Beispiele liegen in `data/config/*.json`.
- **Deterministische I/O:** Fassaden/Services arbeiten mit einfachen Dicts.
- **Ports/Adapter:** `modules/retrieval_port.py` nutzt vorhandene Suche (sofern vorhanden).
- **DSGVO:** Alle Daten lokal (JSON/Chroma), LLM via **Ollama** lokal.

## 6. Troubleshooting
- **Kein LLM gefunden:** LLM‑Alias in `rubrics_config.json` existiert nicht in `model_config.json`. → Alias anpassen.
- **Kein Kontext:** Retrieval‑Adapter findet keine Chunks (Doc‑ID/Top‑K prüfen). Funktioniert auch ohne Kontext.
- **Berechtigungen:** Schreibrechte auf `data/config/` sicherstellen.

## 7. Änderungsverlauf
- **2025‑08‑27:** Ersteinführung der Rubriken‑Funktionalität.
