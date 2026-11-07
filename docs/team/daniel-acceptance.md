# Daniel handoff acceptance — 7 November 2026

Baseline: merged main `ede2446`, isolated branch `chore/daniel-demo-acceptance` on Daniel’s machine. No model, paid API, credentials or existing local database used. Original visual-design checkout preserved.

## Decisions recorded

The supplied team handoff specifies the 1000 m radius, design §6 rules r1 impact mapping, and ownership: Rajeev owns backend and template behaviour; Daniel owns CSS and visual design; Olan owns sources and scout testing. This records the supplied contract; it does not invent a new team vote.

Impact: distance ≤300 m scores 2, otherwise within radius 1; overlap ≥120 min scores 2, 30–119 min 1, otherwise 0; published attendance ≥1000 scores 2, 200–999 scores 1, otherwise 0. Total ≥5 high, 3–4 medium, 0–2 low. Effects are separate, never netted.

Daniel explicitly selected **Rajeev’s laptop with local Ollama for live extraction**. No Azure deployment or paid fallback is authorized. Daniel’s validation uses `none`; prepared data is the backup. Ollama execution on the final laptop is not independently verified here.

## Gate M4 outcomes

| Checklist item | Result and evidence |
| --- | --- |
| One fictional café profile | PASS: Bríd’s Kitchen, 08:00–16:00, radius 1000 m; same profile through detail and draft. |
| Backend event/weather persistence, provenance/freshness | PASS for prepared events and real weather: fresh reset stores 7 events with excerpt/retrieval metadata; Open-Meteo fetched and stored 7 forecast days. Live extraction persistence has automated fixture coverage only on this machine. |
| Repeat refresh without visible duplicates | PASS: prepared reload 7 → 7; repeat live refresh covered by existing deterministic tests, not actual Ollama. |
| Relevant event with effect, impact, confidence, reasons | PASS: graduation Thu 12 Nov 10:00–14:00, increase, medium impact and confidence; source excerpt and assumptions visible. |
| Explainable irrelevant event | PASS: concert has no opening-hours overlap; festival 7566 m away exceeds radius; private function restricted. |
| Honest missing/conflicting evidence | PASS: community talk missing start time and location; high-impact market and decreasing road closure each show conflict, never netted. |
| Correct date/timezone deadline | PASS: graduation Bakery cutoff Wed 11 Nov 16:00, Europe/Dublin. |
| Supported draft, quantities left to owner | PASS: template names known event/window/cutoff, asks owner to confirm quantities; guardrail tests pass. |
| Edit, approve and copy; approval ≠ delivery | PASS in actual browser: edited/saved draft, approved, clicked copy; success says “Copied… Not sent.” Editing clears approval in existing test. |
| Fetch failure retains cached records and exposes stale state | PASS in deterministic existing tests; actual outage on final laptop not rehearsed. Prepared events correctly remain prepared, not falsely stale. |
| Live/cached/prepared distinguishable | PASS in data-layer tests and prepared browser labels. LIMITATION: mixed-mode home banner emphasizes prepared data when both exist; individual insight labels remain distinct. |
| Rehearsal and backup recording | LIMITATION / M5: browser flow exercised here, but no final team rehearsal or backup recording produced. Final laptop and all-three-team signoff still outstanding. |

## M3 visual check

380 CSS px: home, graduation detail and edited/approved draft each have document scroll width 380; timeline scrolls within its own container with a swipe instruction. Draft screenshot visually inspected. Confidence now has colour, a distinct symbol (△ low, ◐ medium, ● high), and words on home/detail. Impact retains its ordinal bars and words.

LIMITATION: the broader “every status has colour plus icon plus words” requirement is not fully satisfied: refresh outcomes, deadline states and some data-mode/stale labels still rely on wording and styling without distinct icons. Treat as a known polish limitation, not a completed gate. Low/high confidence are not naturally present in the prepared scenario.

## Checks and limits

- `pytest -q`: 46 passed before changes; rerun required before commit.
- Fresh isolated DB: `FOOTFALL_DB=/tmp/footfall-daniel-acceptance.sqlite3 python3 -m scripts.reset_demo` → ok, 7 events.
- `FOOTFALL_LLM=none python3 -m scripts.check_llm` → NOT CONFIGURED, expected exit 2.
- Real Open-Meteo refresh: 7 days persisted, provider and retrieval timestamp present.
- Browser console: no application errors in observed prepared flow. Initial navigation failed before the dev server started; retry succeeded.
- No model installed, no `.env` created, no paid calls. Prepared source URLs are fictional examples, not verified live source pages.
- Real-source extraction outcome is handoff evidence only: four sources fetched; two validated events excluded because they occur after café closing. Do not claim live insights were found.
- No freeze tag or gate-wide signoff: Rajeev/team must review this change and rehearse on the actual demo laptop.
