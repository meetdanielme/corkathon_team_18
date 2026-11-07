# Footfall: team milestones and gates (7 Nov 2026)

**Hard times:** feature freeze **17:45** · submission ready **18:30** · official deadline **19:00** (subject to
organisers).
**Rules:**
- One owner per GitHub Issue, each with an observable done condition.
- Stuck for 20 minutes means ask a mentor.
- `main` stays demo-able; work on branches and merge only when tests pass (`pytest -q`).
- No milestone is "done" until every box in its gate is ticked by someone **other** than the person who built it.

| | Rajeev (backend and frontend) | Daniel (PM and design) | Olan (scouting and research) |
|---|---|---|---|
| Owns | Rules, Flask, templates, refresh, LLM adapter | Issues, scope calls, CSS, demo script, recording, AI provider call | Sources directory, prepared events, scout prompt testing |

---

## M0 · 12:15–12:45 · Contract and setup locked

**Goal:** everyone builds against the same records and the same fictional scenario.

- **Rajeev**
  - [ ] Push the starter to your branch; open a PR to `main`.
  - [ ] Run `pip install -r requirements.txt && pytest -q` and confirm 26 passed.
  - [ ] Run the app and load prepared data; share a screenshot in the channel.
- **Daniel**
  - [ ] Create the GitHub Issues from the backlog at the bottom of this file and assign owners.
  - [ ] Confirm three decisions in the channel: the 1000 m radius, the impact mapping (design doc §6), and that Rajeev owns the frontend.
  - [ ] Check Azure: endpoint, deployment name, quota. Set a numeric spend cap.
- **Olan**
  - [ ] Read design doc §5 (the `sources` fields) and the scout prompt in `footfall/scout/extract.py`.
  - [ ] Start a list of 8–12 candidate Cork city-centre sources: university calendar, council notices, venues, markets, churches, hotels.

**Gate M0 (Daniel ticks):**
- [ ] `pytest -q` passes on at least one teammate's machine.
- [ ] The radius, impact mapping and ownership are agreed in writing.
- [ ] Azure works or doesn't, and the answer is known. If it doesn't, the decision is made: Claude fallback, or prepared-only.

---

## M1 · 12:45–14:00 · Prepared flow complete in the browser

**Goal:** the whole demo flow (steps 1–7) works on prepared data. This is the safety net.

- **Rajeev**
  - [ ] Walk the flow: refresh (prepared) → graduation card → detail → draft → edit → approve → copy.
  - [ ] Fix anything that blocks Daniel's styling (class names, layout hooks).
  - [ ] Add the `FOOTFALL_LLM=azure` env vars locally and confirm `LLM().complete_json` returns JSON in a one-line test.
- **Daniel**
  - [ ] Wireframe the 3 screens (home, insight detail, draft) and replace `footfall/static/style.css`.
  - [ ] Write the demo script v1, using design doc §3, step by step.
- **Olan**
  - [ ] Verify 4+ real sources: a public page, permitted to fetch, listing dated events. Record each in `footfall/seed/sources.json` with coordinates and provenance (how and when it was found).
  - [ ] Replace the two `EXAMPLE ROW` entries.

**Gate M1 (Olan ticks, using the PDF acceptance list):**
- [ ] One fictional café profile drives the full flow.
- [ ] A relevant event shows effect, impact, confidence and reasons.
- [ ] An irrelevant event is excluded with an explainable reason (the concert, the far festival, the private function).
- [ ] The supplier deadline is correct: graduation Thu 12 Nov, bakery cutoff **Wed 11 Nov 16:00**.
- [ ] The draft can be edited, approved and copied, and the page says "not sent".
- [ ] Prepared data is visibly labelled "prepared".

---

## M2 · 14:00–15:30 · Live refresh from saved sources

**Goal:** the Refresh button pulls real events from Olan's sources, with provenance, dedupe and failure handling.

- **Rajeev**
  - [ ] Run `POST /refresh mode=live` against Olan's sources with Azure on; fix extraction and validation issues.
  - [ ] Run the live refresh twice and confirm no duplicate events (`SELECT COUNT(*) FROM events` is unchanged).
  - [ ] Break one source URL and confirm the run is `partial`, the source shows `error`, and cached events show **stale**.
  - [ ] Check that weather loads (Open-Meteo); if it fails, a refresh error is shown, not a crash.
- **Daniel**
  - [ ] Style the refresh status, the error list and the stale badge so the honesty labels read clearly.
  - [ ] Review three live insights for grounding: does every claim match its excerpt?
- **Olan**
  - [ ] For each source, read the page and write down which events a human sees in the next 7 days, then compare with what Footfall extracted. Log misses and false positives in the issue.
  - [ ] Tune the scout prompt wording in `extract.py` if needed (coordinate with Rajeev; keep the "untrusted text" lines).

**Gate M2 (Daniel ticks):**
- [ ] A backend refresh persists events and weather with provenance and freshness.
- [ ] A repeat refresh updates records without visible duplicates.
- [ ] A fetch failure keeps cached records and makes staleness visible.
- [ ] Live, cached and prepared data can be told apart.
- [ ] At least one live event with real evidence appears (if none exist in the 7-day window, document that and demo prepared data, labelled).

---

## M3 · 15:30–16:45 · Explainability and polish

**Goal:** every number and label can be explained in one sentence by its owner.

- **Rajeev**
  - [ ] Turn on the LLM rephrase for drafts; confirm the guardrail rejects any added number (`tests/test_drafts_app.py`).
  - [ ] Show a conflict on screen (market vs road closure) and confirm the effects aren't netted.
  - [ ] Confirm a missing-date event shows under "Needs review".
- **Daniel**
  - [ ] Final visual pass; mobile check at 380 px width; colour plus icon plus words for every status.
  - [ ] Demo script v2, with the irrelevant-event moment and the "approval is not sending" moment.
- **Olan**
  - [ ] Prepare a 1-slide "data story": sources monitored, events found, rejected findings and why.
  - [ ] Check that every displayed source link opens and its excerpt is on the page.

**Gate M3 (Rajeev ticks):**
- [ ] Missing or conflicting evidence produces an honest limitation.
- [ ] The draft uses only supported facts and leaves quantities to the owner.
- [ ] Each owner can explain their rules, assumptions and limitations, out loud in 30 seconds.

---

## M4 · 16:45–17:45 · Full acceptance run, then FEATURE FREEZE

- **All:** run the complete flow together from a fresh database (`del footfall.sqlite3`, then start the app) on the demo laptop.
- **Rajeev:** fix only gate blockers; merge to `main`; tag `v1-freeze`.
- **Daniel:** tick the full PDF §11 checklist below; anything unticked becomes a known limitation in the pitch, not a late feature.
- **Olan:** final source refresh about 17:30 so the data is fresh for judging.

**Gate M4 (all three):** every item below is ticked, or written down as a known limitation.
- [ ] One fictional café profile drives the full flow
- [ ] A backend refresh persists events and weather with provenance and freshness
- [ ] A repeat refresh updates records without visible duplicates
- [ ] A relevant event is highlighted with effect, impact, confidence and reasons
- [ ] An irrelevant event is excluded for an explainable reason
- [ ] Missing or conflicting evidence produces an honest limitation
- [ ] The supplier deadline is calculated correctly for the configured date and timezone
- [ ] The draft uses supported facts and leaves order quantities to the owner
- [ ] The owner can edit, approve and copy; approval is not labelled delivery
- [ ] A fetch failure preserves cached records and makes staleness visible
- [ ] Live, cached and prepared data are distinguishable
- [ ] The browser demo is rehearsed and a backup recording exists (finished in M5)

---

## M5 · 17:45–18:30 · Rehearse, record, package

- **Daniel:** 3 timed rehearsals; record the backup video of the full flow; final pitch deck (startup potential first, then the data story, then the demo, then limits).
- **Rajeev:** README run commands verified on a clean clone; `pytest -q` green on `main`; no secrets in the repo (`git grep -i "api_key="` shows only `.env.example`).
- **Olan:** the "data story" slide is final; credit all sources used.

**Gate M5 (Daniel):** submission ready at 18:30: repo link, demo link or instructions, video, deck.

## M6 · 18:30–19:00 · Submit and buffer

- [ ] Submit by 18:45 at the latest. Confirm judges can access the repo and video without changing repo visibility automatically.

---

## Issue backlog (Daniel creates these at M0)

| # | Title | Owner | Done when |
|---|---|---|---|
| 1 | Starter runs on all machines | Rajeev | `pytest -q` shows 26 passed on 2 machines |
| 2 | Azure adapter verified | Rajeev + Daniel | `LLM('azure').complete_json(...)` returns a dict |
| 3 | Real sources directory | Olan | ≥ 4 verified rows in `sources.json`, no EXAMPLE rows |
| 4 | Visual design for 3 screens | Daniel | `style.css` replaced; screenshot posted |
| 5 | Live refresh against real sources | Rajeev | Gate M2 ticked |
| 6 | Extraction accuracy check | Olan | Human vs Footfall comparison logged per source |
| 7 | Drafts with guarded LLM rephrase | Rajeev | Rephrase on; guardrail test passes |
| 8 | Demo script and backup recording | Daniel | Video file linked in the issue |
| 9 | Data story slide | Olan | Slide in the deck |
| 10 | README verified on a clean clone | Rajeev | A teammate follows the README with no help |
