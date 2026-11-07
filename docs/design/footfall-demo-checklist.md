# Footfall demo checklist

## Before starting

- Confirm the fictional café profile is the one driving the flow.
- Confirm the prepared-data label is visible; do not describe prepared events as live extraction.
- If showing the live-model path, note that PR #27 reports a local-model extraction across all four sources; this laptop currently has no Ollama command or local daemon available.
- Use prepared demo data for the café journey unless live extraction results have been made available; keep live findings distinct from prepared events.

## Walkthrough

- Show the relevant graduation event on Thu 12 Nov, 10:00–14:00.
- Show its effect, impact, confidence, and the reasons for the recommendation.
- Show Bakery's cutoff: Wed 11 Nov, 16:00 (Europe/Dublin).
- Show why the concert is outside opening hours, the far festival is outside the radius, and the private function is restricted.
- Edit the draft, approve it, and copy it. Point out the “not sent” message.

## Close

- State that the demo uses fictional prepared data.
- State that the 11 human-visible source listings are the comparison baseline. PR #27 reports two in-window extracted findings passed validation but were filtered by the café opening-hours rule; the per-source records are still needed to complete the comparison.
- Keep model misses, false positives, attendance, and sales unknown until supported by evidence.
