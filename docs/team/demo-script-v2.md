# Footfall demo script v2

Target: about 2 minutes for the app inside a 3-minute pitch. Demo on Rajeev’s laptop with local Ollama; keep the prepared path ready. Do not run slow extraction during the timed pitch unless rehearsed.

1. **0:00–0:15 — Problem and setup.** “A café owner needs to spot nearby events before supplier deadlines. Footfall turns monitored sources into an explainable week and an owner-approved message.” Show the fictional café, opening hours and 1000 m radius. Load prepared data; say every prepared event is fictional.
2. **0:15–0:40 — A useful signal.** Open graduation: Thu 12 Nov 10:00–14:00 demand window; actual published ceremony 11:00–13:00. Show source excerpt and assumed buffer. “Medium impact is a ranking, not a sales forecast. Medium confidence reflects prepared evidence; attendance is unknown.” Point to Bakery cutoff Wed 11 Nov 16:00.
3. **0:40–1:00 — Ignore the irrelevant.** Back to week; show concert filtered out because café closes at 16:00, far festival outside radius, private function restricted. “Nearby does not automatically mean relevant.” Show community talk needs start time/location.
4. **1:00–1:15 — Conflicting signals.** Show market and road closure on Friday. “Both effects remain visible. We do not turn opposing evidence into a made-up net forecast.”
5. **1:15–1:45 — Owner controls the action.** Graduation → draft. Edit, save, approve, copy. “Quantities remain my decision. Approval is not sending: this says not sent. I paste and send it myself.” Never imply an order or email was delivered.
6. **1:45–2:00 — Real data and limits.** “In our earlier real-source run, four monitored sources fetched successfully. Two validated events were excluded because they happen after closing. No live insight emerged from that run.” Attribute this to the team’s earlier run unless repeated successfully. “Prepared mode gives a reliable demonstration; local Ollama supports extraction on the demo laptop.”

## Before recording or judging

Rajeev verifies Ollama and the provider selection on his laptop; rehearse the full flow from a fresh DB. If live refresh fails or yields nothing relevant, show its honest status, then load prepared data. Never describe prepared findings as live, or cached findings as newly fetched. Keep the limitations in `daniel-acceptance.md` visible to the team. Record a backup after the final laptop rehearsal; this script is not evidence that recording exists.
