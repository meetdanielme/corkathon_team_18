# Footfall

Footfall helps café owners see local demand changes coming, understand why they matter, and act before their
ordering deadlines. Corkathon Team 18 MVP. It uses one fictional café: Bríd's Kitchen, Washington Street, Cork.

## Run it

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -q                                    # expect: 32 passed
python -m scripts.reset_demo                 # fresh DB with prepared demo data
flask --app "footfall.app:create_app()" run --debug
# open http://127.0.0.1:5000
```

Configure AI (optional; the prepared demo works without it).

The easiest option is a model running locally through [Ollama](https://ollama.com): free, no API key and no
billing. Azure stays the preferred hosted option when a deployment is available.

```bash
ollama serve                                   # in another terminal
ollama pull qwen3:4b-instruct-2507-q4_K_M
export FOOTFALL_LLM=ollama                     # PowerShell: $env:FOOTFALL_LLM="ollama"
python -m scripts.check_llm                    # expect: OK (ollama): {'ok': True}
```

A local model is slower than a hosted one, roughly 40 s per source, so a four-source refresh needs a bigger
budget than the 90 s default or it stops early and reports a partial run:

```bash
export FOOTFALL_REFRESH_MAX_SECONDS=400
```

For Azure instead:

```bash
cp .env.example .env        # fill in locally, never commit
python -m scripts.check_llm   # expect: OK (azure): {'ok': True}
```

`.env` is read at startup by the app and both scripts. Real environment variables take precedence, so you
can still override a single run without editing the file:

```bash
# PowerShell: $env:FOOTFALL_LLM="azure"; $env:AZURE_OPENAI_ENDPOINT="..."  (etc.)
FOOTFALL_LLM=none python -m scripts.check_llm   # expect: NOT CONFIGURED
```

## What's where

| Path | What |
|---|---|
| `footfall/domain/` | Deterministic rules: time, distance, cutoffs, insights r1, drafts and guardrail |
| `footfall/scout/` | Refresh: public-only fetch, LLM extraction, validation, live and prepared runs |
| `footfall/db.py`, `schema.sql` | SQLite data contract, dedupe, staleness, drafts |
| `footfall/app.py`, `templates/`, `static/` | Flask server-rendered UI |
| `footfall/seed/` | Fictional café, demo supplier rules, source directory, prepared demo events |
| `docs/design/footfall-design.md` | Architecture, data contract, rules r1 mapping |
| `docs/team/milestones.md` | Milestones, owners, gates |
| `docs/superpowers/plans/2026-11-07-footfall-mvp.md` | Task-by-task implementation plan |

## Honesty labels

- **Prepared** data is fictional sample data. By Daniel's decision the interface doesn't label it; Business → Data shows the source (sample data or live sources).
- **Stale** means the last check of a source failed or is older than its refresh interval. Cached events are kept, never deleted.
- "No events" means none were found in the monitored sources, not complete local coverage.
- Impact is an ordinal heuristic (see the design doc §6), not a forecast. Approving a draft does not send it.

After pulling changes to `footfall/seed/`, run `python -m scripts.reset_demo` so your local database picks up the new sample data.

## Credits

- [Remix Icon](https://remixicon.com/) 4.5.0, Apache License 2.0, loaded from jsDelivr.
- [Leaflet](https://leafletjs.com/) 1.9.4, BSD 2-Clause, loaded from cdnjs; map tiles © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (ODbL), shown with attribution on the map.
- Address lookup: [OpenStreetMap Nominatim](https://nominatim.org/) (data © OpenStreetMap contributors, ODbL). Footfall calls it only when a new or changed address is saved, with an identifying User-Agent, in line with the [usage policy](https://operations.osmfoundation.org/policies/nominatim/).
- [Schibsted Grotesk](https://fonts.google.com/specimen/Schibsted+Grotesk), SIL Open Font License, from Google Fonts.
