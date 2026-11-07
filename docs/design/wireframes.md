# Footfall - wireframes for the prepared journey (issue #12)

Low-fidelity layout for the three screens, applied in `footfall/templates/` and `footfall/static/style.css` using visual direction 01 (`docs/design/visual-direction.md`, not yet committed). Desktop shown; below 820px the two columns stack (deadline beneath the insight), and below 640px buttons go full width.

## 1. Home - "Your week, in context"

```
Footfall (mark)                                   Local signals. Thoughtful decisions.
---------------------------------------------------------------------------------
[flash: Refresh (prepared) finished: ok]
BRÍD'S KITCHEN (FICTIONAL DEMO CAFÉ) · CORK
Your week, in context
demo label · open 08:00–16:00 · radius 1000 m · Europe/Dublin
[prepared data]
[Load prepared demo data] [Refresh saved sources (live)]
+-- refresh status (sage) -----------------------------------------------------+
| Last refresh · prepared · ok · time · sources n/n · events upserted n        |
| "No events" means none found in the monitored sources, not complete coverage |
+------------------------------------------------------------------------------+
Next 7 days
+-- insight card (left border = direction) ----------------+-- deadline -------+
| Graduation ceremony (fictional demo)         [prepared]   | ACT BEFORE        |
| Thu 12 Nov 10:00-14:00 · 941 m away                       | Wed 11 Nov 16:00  |
| [Expected: increase] [||. Potential impact: medium]       | Bakery cutoff ·   |
| [ Confidence: medium ] [Conflicting signals]              | upcoming          |
+-----------------------------------------------------------+-------------------+
(more cards)
---------------------------------------------------------------------------------
Filtered out (quiet list: title | reason)
Needs review (quiet list: title | missing fields)
```

## 2. Insight detail

```
← Your week
INSIGHT · RULES R1
Graduation ceremony (fictional demo)
Thu 12 Nov 10:00-14:00 · 941 m away
[prepared data]
+-- summary ------------------------------------+  +-- action deadline ------+
| EXPECTED EFFECT        POTENTIAL IMPACT       |  | ACT BEFORE              |
| [increase]             [||. medium]           |  | Wed 11 Nov 16:00        |
|                        heuristic points; not  |  | Bakery cutoff for       |
|                        a measured uplift      |  | delivery Thu 12 Nov     |
| CONFIDENCE             RELEVANT WINDOW        |  | demo assumption note    |
| [ medium ]             Thu 12 Nov 10:00-14:00 |  | ---------------------   |
| - reasons              assumed buffer basis   |  | suggested response      |
+-----------------------------------------------+  | [Draft a message]       |
                                                   +-------------------------+
Why this matters
| Reasons               | proximity, overlap                                   |
| Conflicts (if any)    | ...                                                  |
| Sources and freshness | link · retrieved time · stale flag · > excerpt       |
▸ Optional revenue scenario (illustrative)
```

## 3. Draft review

```
← Back to insight
SUPPLIER MESSAGE · TEMPLATE DRAFT
Message to Declan (bakery)
Footfall never sends messages: edit, approve, then copy it yourself.
(✓ Edit) (2. Approve) (3. Copy)
+-- editor ---------------------------------------------------------+
| Status: Not approved · not sent  /  Approved <time>, not sent     |
| Review and edit your message                                      |
| [ textarea                                                      ] |
| [Save edits]  Editing clears approval.                            |
| ----------------------------------------------------------------- |
| [Approve] [Copy message]  (copy disabled until approved)          |
| Copied. Paste it into WhatsApp or email. Not sent.                |
+-------------------------------------------------------------------+
```

## Design rules carried over

- Impact (filled amber badge with ordinal bars) and confidence (outlined badge) use different shapes, not colour alone.
- Direction is always written as a word; the left border only repeats it.
- Prepared data is labelled on the page and on each card. Approval always reads "not sent"; there is no delivered state.
- Fonts: Manrope headings, DM Sans body, loaded from Google Fonts with system sans-serif fallbacks if offline.

Screenshots of the implemented screens (prepared data, desktop and 390px mobile) are in [screenshots/issue-12](screenshots/issue-12/).
