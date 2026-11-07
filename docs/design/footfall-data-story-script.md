# Footfall data story talk track

Use [the v3 slide](footfall-data-story-v3.pptx). It supersedes v2’s local-model account.

## 30-second version

Footfall uses Azure Luna to read four Cork event pages. Our human check found eleven listings. Saved evidence represents five titles: two relevant insights and three exclusions. Six titles are absent; four have recorded rejection reasons. We retain source excerpts, flag possible duplicates and leave attendance unknown. Coverage and multi-day handling are incomplete, so this is decision support, not a forecast. The owner reviews every supplier message; nothing is sent automatically.

## Delivery notes

- This is a cumulative saved-record audit, not one extraction run or an accuracy percentage. Eleven counts listing entries, not individual performances.
- Eight live rows represent five titles. Three St Peter’s titles have historical venue-spelling variants; the app flags them for review. Do not count them twice.
- Nutcracker and Disco Pigs have historical date-window rejection messages despite overlapping baseline date ranges. The Devils and CIFF failed excerpt validation. Mexican Offering and Zine Fest have no retained named rejection reason.
- Stored start times match the four timed listings. The earlier displayed offsets are arrival/duration assumptions, not shifted published start times. Unknown attendance stays unknown; assumed windows are not published finish times.
- Multi-day runs do not reliably cover each screening or later open day. Raw rejected candidates were not retained, so a full accuracy assessment cannot be reconstructed.
- The latest saved live run reached the shared AI allowance. Use cached records and deterministic supplier drafts; do not promise a fresh extraction or reset the allowance.
- AI chooses a constrained wording style for drafts; the app renders factual clauses. Quantities remain the owner’s decision. Signing in is simulated; approval never sends a message.
- Revenue illustrations use owner-supplied assumptions and are not forecasts or observed sales.

## Evidence and credits

Audit and accepted limitations, checked 7 November 2026:

- [Production database comparison](https://github.com/meetdanielme/corkathon_team_18/issues/14#issuecomment-6709890259)
- [Source and code review](https://github.com/meetdanielme/corkathon_team_18/issues/14#issuecomment-6709909279)
- [Human baseline and source selection](../../footfall/seed/source_assessment.md)

Public sources: [St Peter’s Cork](https://stpeterscork.ie/events), [Cork Opera House](https://www.corkoperahouse.ie/whats-on/), [Triskel Arts Centre](https://triskelartscentre.ie/whats-on/), [The Everyman](https://everymancork.com/).

Rehearsal remains to be done with a teammate. The word count is intended for roughly 30 seconds; no timed rehearsal is claimed.
