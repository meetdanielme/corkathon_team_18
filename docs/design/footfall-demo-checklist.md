# Footfall demo checklist

## Before starting

- Open the [deployed app](https://footfall-team18.vercel.app/) and state what it shows. On 2026-11-07 it was `Partly updated`; refresh status varied between three source checks incomplete and one refresh issue. Neither observed state proves a clean four-source live run.
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
- If discussing the deployed refresh, mention the earlier observed date-window rejections for The Nutcracker and Disco Pigs, the St Peter's duplicate event ID error, and the displayed/source start-time differences. A later page check showed only one refresh issue and Harry Clarke from Triskel, so the earlier misses/error need reproduction. Do not describe either snapshot as a complete comparison.
- For St Peter's listings, quote only the published start time. The deployed app adds or shifts times: Creative Workshop shows 14:00–17:00 while its source says 15:00; Soul of Mexico shows 16:00–19:00 vs source 17:00; Max Richter shows 18:30–21:30 vs source 19:30. The source pages do not publish those end times.
- Keep model misses, false positives, attendance, and sales unknown until supported by evidence.
