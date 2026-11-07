# Footfall: design doc (MVP)

**Corkathon Team 18 · 7 November 2026 · rules version r1**
Source of truth for scope: `footfall-mvp.pdf` (Daniel's planning interview). This doc turns it into concrete
architecture, data contract, rules and routes. Where this doc and the PDF disagree, the PDF wins on *scope* and
this doc wins on *implementation detail*, and the difference gets raised in the team channel.

## 1. One sentence

Footfall helps café owners see local demand changes coming, understand why they matter, and act before their
ordering deadlines.

## 2. Team and ownership (as of 12:04)

| Person | Role | Owns | Observable handoff |
|---|---|---|---|
| Rajeev | Backend and frontend | Rules, Flask app, templates, refresh plumbing, LLM adapter | Shared records produce explainable insights, correct deadlines and editable grounded drafts in the browser |
| Daniel | PM and designer | GitHub Issues, scope calls, visual design (CSS/wireframes), demo script, backup recording, AI provider decision | Every milestone gate checked; demo rehearsed; recording exists |
| Olan | Scouting data and research | `seed/sources.json`, verified Cork sources, prepared demo events, scout prompt testing | Saved sources refresh into validated, deduplicated records with evidence and failure status |

> Change from the PDF: the PDF lists Daniel as interface owner. Per the 12:04 decision, Rajeev builds the
> frontend templates and Daniel owns the visual design and demo. Confirm in the channel.

## 3. Demo flow (from the PDF, unchanged)

1. Open the prefilled fictional café profile (Bríd's Kitchen, Washington Street, 08:00–16:00).
2. Trigger a backend refresh of saved sources and weather.
3. See upcoming insights ranked by relevance.
4. Open a highlighted event: time window, effect, impact, evidence, confidence, freshness.
5. See a supplier deadline that falls before the trading window.
6. Review the suggested preparation decision and its evidence.
7. Edit, approve and copy a supplier message. Nothing is sent.

Also show one irrelevant event being filtered out, with its reason.

## 4. Architecture

```
[Refresh button] → refresh.run_live / run_prepared
     → fetch.fetch_text (public-only, redirect-checked, 1 MB, 10 s)
     → extract.extract_events (LLM adapter, scout prompt contract)
     → validate.validate_finding (verbatim excerpt, date window, types)
     → db.upsert_event (norm_key dedupe, evidence appended, near-duplicates flagged)
     → SQLite
[Page load] → db.get_events (+stale flags) → insights.build (deterministic r1 rules)
     → Jinja templates (index, insight detail, draft)
[Draft] → drafts.template_draft → optional LLM rephrase → numeric guardrail → drafts table
```

- **Stack:** Python 3.11+, Flask 3, SQLite, Jinja server-rendered pages, `zoneinfo` (`tzdata` on Windows).
- **AI:** behind `footfall/llm.py`. `FOOTFALL_LLM=azure` is primary. `anthropic` is a manual fallback, Daniel's
  call. There is no automatic fallback. `none` keeps the app fully usable in prepared mode.
- **Insights are computed on read**, not stored. Each insight's `id` is `business:event:rule_version`, so drafts
  can reference it. That keeps rules changes instant and reproducible.
- **Refresh is synchronous** with hard limits (`max_sources=15`, `max_seconds=90`, `max_llm_calls=15`). A
  `running` row blocks overlapping runs for 5 minutes. There's no queue and no agent platform.

## 5. Data contract (SQLite, `footfall/schema.sql`)

| Table | Key fields | Notes |
|---|---|---|
| businesses | id, name, lat, lon, timezone, opens, closes, open_days, radius_m, avg_spend | Optional values are NULL |
| supplier_constraints | id, business_id, supplier, contact_label, delivery_day, delivery_window, cutoff_rule (JSON), evidence, demo_label | One row per supplier per delivery weekday |
| sources | id, org_name, venue_name, url, type, lat, lon, access_notes, refresh_interval_h, last_attempt_at, last_success_at, status, last_error, provenance | Identity (org) is separate from location (lat/lon) |
| events | id, title, norm_key (unique), start_at, end_at, time_precision, venue_name, lat, lon, category, access, status, verification, attendance, possible_duplicate_of, data_mode, first_seen_at, last_seen_at | `status` is never set to cancelled by inference |
| event_evidence | event_id, source_id, url, retrieved_at, excerpt, extracted_json, uncertainty | Append-only; unique per (event, url, excerpt) |
| weather | lat, lon, day, temp_max, rain_prob_max, wind_max, units, provider, retrieved_at, kind | Forecast vs observation is explicit |
| drafts | id, insight_id, recipient_label, text, source, created_at, updated_at, approved_at | No delivered state exists |
| refresh_runs | id, started_at, ended_at, mode, status, sources_attempted/succeeded, events_upserted, llm_calls, errors | `mode` is live or prepared |

**Cutoff rule JSON:** `{"type":"weekday","day":"thu","time":"16:00"}` or
`{"type":"business_days_before","n":2,"time":"16:00","closed":["sun"]}`.

**Dedupe:** `norm_key = normalised title | local date | normalised venue`. An exact match updates the event and
appends evidence. The same date and venue with a title similarity of 0.6–0.99 is inserted and flagged
`possible_duplicate_of`, for review, never auto-merged.

**Staleness:** a live event is stale when every source that evidences it either has `status=error` or last
succeeded more than `refresh_interval_h` ago (default 24). Prepared events are labelled *prepared*, not stale.

## 6. Rules r1 (documented mapping; must stay reproducible from visible inputs)

**Gates, in order. The first match decides:**

| # | Condition | Result |
|---|---|---|
| 1 | No start time, or no coordinates | Review finding ("missing …"), not an insight |
| 2 | access = restricted | Excluded: private or restricted |
| 3 | Distance > business radius (default 1000 m) | Excluded with the distance |
| 4 | Event date outside [today, today+7) | Excluded: outside the 7-day view |
| 5 | Café closed that weekday | Excluded |
| 6 | Demand window doesn't overlap opening hours | Excluded with the window |
| 7 | Otherwise | Insight |

**Demand window (always labelled assumed):** 60 min before the start to 60 min after the published end. If no
end is published: 60 min before to 120 min after the start, labelled "end time not published… review".

**Effect:** `road_closure` gives a decrease. Everything else gives an increase. When increase and decrease
insights overlap on the same day, both show a conflict note. Effects are never netted.

**Impact (ordinal heuristic, not an uplift):**

| Points | 0 | 1 | 2 |
|---|---|---|---|
| Distance | — | 301 m to radius | ≤ 300 m |
| Overlap with opening hours | < 30 min | 30–119 min | ≥ 120 min |
| Attendance (only if published) | unknown or < 200 | 200–999 | ≥ 1000 |

Total ≥ 5 is **high**, 3–4 is **medium**, and 0–2 is **low**. The breakdown is shown in the UI.

**Confidence (separate from impact):**
- **Low** if any of these apply: the source is stale or failed, or there's no supporting excerpt.
- **Medium** if any of these apply: prepared demo data, not verified against the source page, or no published
  end time.
- **High** otherwise.
- Unknown attendance is always shown as a note.

**Weather:** context only. Rain probability ≥ 60% adds a reason line. There's no weather-to-sales coefficient.

**Deadlines:**
- For each supplier, take the delivery serving the event day (same day, else the day before) and compute its
  cutoff from the rule.
- It's only shown if the cutoff falls before the window start.
- Status: `missed` if the cutoff ≤ now, `urgent` if ≤ 24 h away, otherwise `upcoming`.

**Suggested response:** names the supplier and cutoff. It always leaves quantities to the owner ("Whether to
change quantities is your call").

## 7. LLM boundaries

| LLM may | LLM must not |
|---|---|
| Extract structured events from one fetched page | Invent attendance, end times, sales, customer counts or business facts |
| Rephrase a template draft | Add any number not already in the draft's facts (guardrail rejects it) |
| Report uncertainties | Decide relevance, impact, confidence or deadlines (Python does) |

The page text is untrusted. Extraction output passes `validate_finding`: the excerpt must appear verbatim on the
page, the dates must parse, and the start date must fall within the 7-day window (±1 day). Anything else is a
visible refresh error.

## 8. Routes

| Method and path | Purpose |
|---|---|
| GET `/` | Profile, data-mode badges, last refresh status and errors, 7-day insights, filtered-out list, review list |
| POST `/refresh` (`mode=prepared` or `live`) | Bounded refresh; flashes the status |
| GET `/insights/<id>` | All 8 insight fields, sources and excerpts, deadline, suggestion, optional revenue scenario |
| POST `/insights/<id>/draft` | Creates a draft, then redirects |
| GET `/drafts/<id>` | Editable text, approval status, copy button (enabled after approval) |
| POST `/drafts/<id>` | Save edits (resets approval) |
| POST `/drafts/<id>/approve` | Records `approved_at`; the UI says "approved, not sent" |
| GET `/api/insights` | JSON of insights, exclusions and review findings, for checks |

## 9. Security and safety

- Fetch only `http`/`https` hosts that resolve to public IPs. Every redirect hop is re-checked. Bodies are
  capped at 1 MB with a 10 s timeout.
- The app has no send, purchase or form-submit capability. Approval is not delivery.
- Secrets only go in a local `.env`. `.env.example` holds placeholders only.

## 10. Open setup checks (owners in brackets)

- [ ] Azure deployment name, auth, JSON output and quota; set a numeric spend cap before paid calls (Daniel and
  Rajeev)
- [ ] Open-Meteo reachable from the demo laptop (Rajeev)
- [ ] Real Cork sources with permitted public calendar pages replace the two `EXAMPLE ROW` entries (Olan)
- [ ] Radius (1000 m) and the impact mapping above agreed by all three (Daniel)
- [ ] Judge access to the repo, demo and video, without changing repo visibility automatically (Daniel)

## 11. Out of scope today

Accounts and billing, scheduled refresh, push notifications, inbox or WhatsApp ingestion, sending messages,
ordering, ads and campaigns, numerical demand forecasts, holidays and roadworks integrations, mobile traders,
and the scout's **discover** mode (broad web search for new sources; only **refresh** mode over the saved
directory is built today).
"Promote this rush" ad briefs stay future work.
