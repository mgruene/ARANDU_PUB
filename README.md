# Willkommen

![Latest tag](https://img.shields.io/github/v/tag/mgruene/ARANDU_PUB?label=latest%20tag)
![Releases](https://img.shields.io/github/v/release/mgruene/ARANDU_PUB?include_prereleases)


##  Zum Projekt ARANDU
Diese Projekt versucht, einen Prototypen einer RAG-Anwendung zu bauen, die Prüferinnen und Prüfer bei der Bewertung wissenschaftlicher Arbeiten unterstützt.

Dabei sollen nur lokale KI-Sprachmodelle eingesetzt werden, um die Datensicherheit und Vertrauchlichkeit der Inhalte zu gewährleisten. 

Die Anwendung ist nicht als alleiniger Ersatz für eine umfassende Bewertung zu verstehen. 


## 🚀 Starten

### Voraussetzungen
- Docker & Docker Compose installiert
- Git (für den Code)

### Schritte
1. Repository klonen:

```bash
   git clone https://github.com/mgruene/ARANDU_PUB.git
   cd ARANDU_PUB
```
Beispiel-Konfiguration kopieren (lokale Anpassungen in examiners.json vornehmen):

``` bash
cp data/config/examiners.json.example data/config/examiners.json
```
Container starten:

``` bash
docker-compose up -d
```

Anwendung aufrufen:

* Streamlit-App: http://localhost:8501
* ChromaDB-API: http://localhost:8000

Stoppen:

``` bash
docker-compose down
```

## 📦 Versionsgeschichte

<!--VERSIONS:START-->
* publish: 2025-08-27T15:18:32+02:00 (4f442ef)* sync mit online-change an README.md (d81bc91)* Merge pull request #1 from mgruene/codex/create-github-actions-workflow-for-update-readme (e18ca77)<!--VERSIONS:END-->
