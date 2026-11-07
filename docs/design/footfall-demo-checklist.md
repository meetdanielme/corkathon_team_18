# Footfall demo checklist

## Before starting

- Open the [deployed app](https://footfall-team18.vercel.app/) and state what it shows. On 2026-11-07 it was `Partly updated`; refresh status varied between three source checks incomplete and one refresh issue. Neither observed state proves a clean four-source live run.
- Confirm the fictional café profile is the one driving the flow.
- Confirm the prepared-data label is visible; do not describe prepared events as live extraction.
- If showing live records, say the latest audit is a cumulative database snapshot: 8 live rows, 9 evidence rows, 10 refresh summaries and 4 source states. The latest recorded run was partial after the shared model allowance was reached.
- Use prepared data for the café journey unless current live records are available; keep live, stale and prepared findings distinct.

## Walkthrough

- Show the relevant graduation event on Thu 12 Nov, 10:00–14:00.
- Show its effect, impact, confidence, and the reasons for the recommendation.
- Show Bakery's cutoff: Wed 11 Nov, 16:00 (Europe/Dublin).
- Show why the concert is outside opening hours, the far festival is outside the radius, and the private function is restricted.
- Edit the draft, approve it, and copy it. Point out the “not sent” message.

## Close

- State that the demo uses fictional prepared data.
- State that the 11 human-visible source listings are the comparison baseline. Five titles are represented in the cumulative saved state; four have named historical rejections and two absences have unconfirmed causes. Do not turn this into an accuracy percentage because raw candidates and complete per-run membership were not retained.
- Stored start times for Creative Workshop, Soul of Mexico, Max Richter and Harry Clarke match the source. The displayed demand windows include a 60-minute arrival buffer and, where the source omits an end, an assumed duration. Explain them as planning windows, not extracted or published event times.
- Pan's Labyrinth is stored with date-only precision and midnight bounds; don't present those bounds as screening times. Its Sunday start is filtered although the run continues to Wednesday.
- Three historical St Peter's venue spelling variants remain separate and are flagged for review by PRs #49 and #50; do not count them as separate demand signals.
- Keep unconfirmed absences, false positives, attendance, sales and all unpublished details unknown.
