# Footfall data story talk track

## 30-second version

Four Cork pages feed Footfall. Our human baseline has 11 listings for 7–13 November. The deployed app is partly updated, and its refresh status changed between checks. One observed view rejected The Nutcracker and Disco Pigs as out of window although both overlap; a later check showed one refresh issue and Harry Clarke from Triskel, but not those rejection messages. The app also shifts several displayed start times from the source pages. PR #27 reports two findings filtered by café hours. Demo events are fictional, and the full comparison is still incomplete.

## Delivery notes

- Keep the distinction clear: 11 is a count of human-visible listing entries, not extracted event count.
- One deployed-app snapshot rejected The Nutcracker and Disco Pigs as out of window despite the source dates overlapping the window; a later snapshot did not show those messages. Report both observations and say the rejection needs reproduction.
- If asked about other misses or false positives, say the changing partial refresh and missing per-source output leave the full comparison incomplete.
- If asked about customer numbers or sales, say the sources do not state attendance and Footfall does not infer sales.
