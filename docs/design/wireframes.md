# Footfall - prepared journey design (issue #12)

> Superseded on 7 November 2026 by the attention-colour redesign. See [design-review-2026-11-07.md](design-review-2026-11-07.md).

Layout and visual rules for the three screens, implemented in `footfall/templates/` and `footfall/static/style.css`. Produced with the `frontend-design` skill, replacing the first pass that read as templated.

## Concept

A café owner plans the week in a diary and orders on a supplier docket. Footfall borrows that world: cool paper, ballpoint-blue ink, and a highlighter that marks supplier cutoffs only. The one bold element is the week timeline. It draws every event against opening hours, so the reason an evening concert is filtered out is visible rather than just stated.

| Token | Value | Use |
| --- | --- | --- |
| Page / sheet | `#F1F3F6` / `#FBFCFD` | Background and paper surfaces |
| Graphite / pencil | `#1D232B` / `#566170` | Text and secondary text |
| Ballpoint | `#2B44A8` | Links, buttons, "could bring more customers" |
| Highlighter | `#FFE76A` | Supplier cutoffs, nothing else |
| Red pen | `#B3261E` | "Could reduce customers", conflicts, stale |

Type: Schibsted Grotesk only (Google Fonts, system sans fallback), sentence case throughout. Avoided on purpose: cream and terracotta, uppercase eyebrow labels, middle-dot metadata strings, identical rounded cards, arrows on links.

## 1. Home - "The week ahead"

```
Footfall.                                           For independent cafés in Cork
The week ahead                                [Load prepared data][Refresh from sources]
Bríd's Kitchen, open 08:00 to 16:00 ...        Last refreshed ... 7 events from 0 of 0
[Showing prepared data: every event is fictional]   An empty week means nothing turned up...
+-- week timeline ------------------------------------------------------------------+
|         06    08    10    12    14    16    18    20    22    24                   |
| Sat 7        [====== opening hours ======]                                         |
| Sun 8   ///////////////// closed /////////////////////                             |
| Mon 9        [         :Private function :  ]          (dashed = filtered out)     |
| Wed 11       [                            ]|Bakery order for Thu closes 16:00      |
|                                             |          :Evening concert:          |
| Thu 12       [      ■Graduation■          ]|Bakery order for Fri closes 16:00      |
| Fri 13   ■Road closure (red)■  ■Street market■                                     |
| key: opening hours, more customers, fewer customers, filtered out, order cutoff    |
+------------------------------------------------------------------------------------+
Decisions due
Order by           | Graduation ceremony [prepared]        Expected increase
▓Wed 11 Nov 16:00▓ | Thu 12 Nov 10:00-14:00, 941 m away    ▮▮▯ Impact medium
Bakery, upcoming   |                                       Confidence medium
-------------------------------------------------------------------------------
Filtered out (title, reason)                    Needs checking (title, missing fields)
```

## 2. Insight detail

```
Back to the week
Graduation ceremony (fictional demo)
Thu 12 Nov 10:00-14:00, 941 m from the café.   [Prepared data ... Rules r1.]
+-- the same timeline, this day only, current bar outlined in highlighter ---------+
What this could mean                          +== docket ==================+
 Expected effect   Increase ...               | Order by                   |
 Potential impact  ▮▮▯ Medium, a ranking...   | ▓Wed 11 Nov 16:00▓         |
 Confidence        Medium + reasons           | Bakery cutoff for delivery |
 Relevant window   ... + assumed basis        | - - - - - - - - - - - - -  |
Why it showed up (reasons, conflicts)         | suggested response         |
Source (quoted clipping, link, retrieved)     | [Draft a message]          |
Try a revenue scenario with your own numbers  +----------------------------+
```

## 3. Draft review

```
Back to the insight
Message to Declan (bakery)
Footfall doesn't send anything. Edit, approve, then copy it yourself.
(✓) Edit the wording   (2) Approve it   (3) Copy and send it yourself
+-- order sheet ---------------------------------------------+
| To Declan (bakery)                  Drafted from: template |
|============================================================|
| message on faint ruled lines                               |
| [Save edits]  Saving an edit clears any approval.          |
+------------------------------------------------------------+
Not approved yet. Not sent.   /   Approved <time>, not sent
[Approve] [Copy message]   (copy disabled until approved)
```

## Responsive

Below 900px the columns stack and the docket follows the reading column. Below 600px buttons go full width, and the timeline keeps its scale and scrolls sideways inside its frame, with a hint. The page itself never scrolls sideways.

Screenshots of the implemented screens (prepared data, desktop and 390px mobile) are in [screenshots/issue-12](screenshots/issue-12/).
