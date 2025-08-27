# Zustands- & Header-Logik in ARANDU

Dieses Dokument beschreibt, wie die Seiten **`02_select_thesis.py`** und **`03_ask_thesis.py`** den Anwendungszustand
verwalten, wie die **Metadaten der aktuell ausgewählten Arbeit** gehalten und im **Header** dargestellt werden –
und wie andere Seiten (hier **Seite 06 & 07**) diesen Zustand konsistent verwenden.

## 1. Persistenter App-State (Datei-basiert)

- **State-Fassade:** `app/services/state_facade.py` kapselt das Datei-Repository `app/modules/state_repo.py`.
- **Zentrale Dateien unter** `data/app_state/` (Container-intern `/data/app_state/`):
  - `ingest_doc_<docid>.json`  → Quittung je Arbeit (finalisierte Metadaten, Zähler, Collections).
  - `ingests_index.json`       → Liste aller Ingests (UI-Listing).
  - `current_thesis.json`      → *Aktuell ausgewählte Arbeit* (enthält mindestens `docid` & `metadata:{...}`).

Die **State-Fassade** stellt u. a. zur Verfügung:
- `set_current(docid) -> str`  → Persistiert die Auswahl.
- `get_current() -> dict|None` → Liefert den aktuellen Kontext (oder `None`).

**Wichtig:** Der App-State wird **explizit** über die Fassade gelesen/geschrieben (keine versteckten Seiteneffekte).
Logs sind strukturiert (JSON-fähig), I/O deterministisch (Dict rein, Dict raus).

## 2. Header-Darstellung (Topbar/App-Header)

Die UI-Komponenten
- `app/ui/components/topbar.py` (Topbar inkl. Logo) und
- `app/ui/components/app_header.py` (kompakter Header-Block)
lesen den aktuellen Kontext über `StateFacade.get_current()` und zeigen oben rechts:

- **Student** (z. B. `student_name`),
- **Titel** (`thesis_title`),
- sowie einen **Expander "Metadaten"** mit dem gesamten `metadata`-Dict.

Falls **keine Auswahl** getroffen wurde (`current_thesis.json` fehlt), erscheint ein Hinweis.

## 3. Seite „02_select_thesis“ – Auswahl & Diagnose

- Listet Quittungen `ingest_doc_*.json` als Tabelle oder Select/Radio.
- Optional prüft sie den Status in Chroma (Anzahl & Sample-Metadaten).
- Beim Klick auf „Als aktuell setzen“ ruft sie `StateFacade.set_current(docid)` auf.
- Der Header aktualisiert sich, indem er stets **on render** `get_current()` liest.

## 4. Seite „03_ask_thesis“ – Freitextfragen gegen aktuelle Arbeit

- Lädt beim Start `current_thesis` und zeigt den Header (siehe oben).
- UI-Parameter: LLM-Auswahl, `top_k`, ggf. Kontextfenstergröße (aus JSON-Konfiguration).
- **Retrieval:** Fragetext wird eingebettet und in Chroma **mit `where={"docid": <current.docid>}`** gesucht.
- Antwort-Panel zeigt **Belege** (erste Treffer, Metadaten) und ein Diagnose-Panel (`collection`, `embedding_alias`, `top_k`, `docid`).

## 5. Übertragung auf Seiten 06 & 07 (Rubriken)

Damit die Nutzer jederzeit sehen, **wogegen Abfragen laufen**, wurden die Seiten angepasst:

- Beide Seiten laden `app_config.json` (für Pfade & Branding) und rufen `apply_css_only(app_cfg)` sowie `render_topbar(app_cfg)` auf.
- Beide Seiten lesen den aktuellen Kontext `current = StateFacade(app_state_dir).get_current()`.
- **Seite 06 (Admin Rubriken):** Beim Anlegen von Beispielen wird das **`doc_id`-Feld** standardmäßig mit `current["docid"]` vorbelegt.
- **Seite 07 (Rubrik-Fragen):** Die Anfrage verwendet automatisch `doc_id = current["docid"]`.
  Optional kann `top_k` angepasst werden; die Retrieval-Funktion nutzt Chroma **mit docid-Filter**, analog zu Seite 03.

## 6. DSGVO, Logging, Robustheit

- Alle Daten verbleiben lokal; keine externen Services außer lokaler ChromaDB & Ollama (Host).
- Umfangreiches Logging (INFO/WARN/DEBUG) mit strukturierten Feldern.
- Fehlerfälle: Fehlt `current_thesis`, stoppen Seiten 07 und zeigen einen Hinweis; Seite 06 zeigt Header „Keine Auswahl“ und erlaubt dennoch generische Admin-Aktionen.

---

**Kurzreferenz der wichtigsten Komponenten:**

- `services/state_facade.py`  → `get_current() / set_current(docid)`
- `modules/state_repo.py`     → Datei-I/O, atomare JSON-Writes
- `ui/components/topbar.py`   → Header inkl. Metadaten-Expander
- `ui/components/app_header.py` → Alternative, kompakte Header-Box
- `ui/pages/03_ask_thesis.py` → docid-gefiltertes Retrieval (Chroma)
- `services/rubric_eval_service.py` → Bewertungsfragen inkl. Retrieval-Port
