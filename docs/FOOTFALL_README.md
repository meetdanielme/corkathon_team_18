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

Configure AI (optional; the prepared demo works without it):

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

- **Prepared** data is fictional demo data and is always labelled as such.
- **Stale** means the last check of a source failed or is older than its refresh interval. Cached events are kept, never deleted.
- "No events" means none were found in the monitored sources, not complete local coverage.
- Impact is an ordinal heuristic (see the design doc §6), not a forecast. Approving a draft does not send it.
