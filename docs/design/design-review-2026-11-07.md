# Design review, 7 November 2026: Figma comments and web interface guidelines

Changes on branch `feat/attention-visuals`. Screenshots: [screenshots/attention-visuals](screenshots/attention-visuals/).

## Direction

Colour now means attention, and only attention:

| Colour | Meaning | Where |
| --- | --- | --- |
| Red | Act now: cutoff within 24 h, conflicts, failures | Decision status, action card, status dot |
| Amber | Soon (cutoff within 72 h), needs checking, partial refresh | Same, plus "Needs checking" cards |
| Blue | Planned: cutoff later than 72 h; also brand and actions | Decision status, buttons, "more customers" |
| Green | Done: supplier message approved; refresh OK | Decision status, draft pill, status dot |
| Plum | Fewer customers (direction, not urgency) | Timeline bars, effect chips |

Impact uses a separate coloured meter (teal, amber, red segments). Icons come from Remix Icon 4.5.0.

## Figma comments (file WY1WFAQ5QDR8nqrvf8kq4r)

| # | Comment (short) | Change |
| --- | --- | --- |
| 1 | Impact pips look like signal bars; want colourful urgency | Coloured 3-segment impact meter; urgency moved to the coloured cutoff status |
| 2, 5, 7, 16 | Drop "demo"/"fictional" labels | Removed from seed titles, venues, business name and page copy (the header's Sample data tag was removed in the second review) |
| 3 | Status top right: refresh button, green indicator, "Last updated" | Header status pill: coloured dot, "Updated 12 min ago", refresh icon button, on every page |
| 4 | Remove filler header text | Removed |
| 6 | Business as a card with change options | Business card on Home with address and radius, hours, Change links |
| 8 | Too much refresh text | Moved to the status pill and the Business page Data panel |
| 9 | What are these buttons for? | Single refresh button; "Load Sample Data" and "Check Live Sources" now on the Business page with an explanation |
| 10 | "Prepared" looked like readiness; yellow date felt urgent | Data-mode tag removed from cards; cutoff colour follows time left; approved message shows a green check |
| 11 | Metrics hard to read | Effect chip with arrow, impact meter, confidence chip with shield icon |
| 12 | Filtered events only in the timeline | List removed; timeline bars show a short reason, full reason in the accessible name |
| 13 | Needs checking belongs in Decisions due | Amber "Needs checking" cards in Decisions Due |
| 14, 17, 22 | More visual, less text | Insight header chips, metric tiles, icon lists; draft header with avatar and status pill |
| 15 | Map, or address with link and distance | Leaflet map with café, venue, radius and walking line; venue name, distance, walk time, Directions link |
| 18 | Deadline card: more visual, urgent; "Draft Message to Supplier" | Action card coloured by urgency with countdown; button renamed |
| 19 | Revenue estimate hidden; "Potential Impact on Revenue" | Prominent card led by a percentage (e.g. **+10% customers**), then ≈ extra customers and ≈ € from the owner's usual customers per hour and average spend. The % per impact level (default 5 / 10 / 20) and the baseline are owner assumptions, editable under Business → Revenue Assumptions, and the card says "Not a forecast". Follow-up from Daniel: a percentage metric, not a calculator |
| 20 | Draft looks like a notebook; make copying easy | Plain composer, Copy button in its toolbar plus a main Copy Message button |
| — | Follow-up: no latitude/longitude; allow several addresses | Locations are address rows only, looked up on OpenStreetMap Nominatim when saved (unchanged addresses are never re-looked-up). A business can have several; events are measured from the nearest, which the reason and map name |
| — | Follow-up: several opening hours, and holidays | Weekly ranges per day (split days allowed) plus dated special days (closed, or different hours) that replace them. The rules use the real schedule: overlap sums across ranges, closures filter events with the holiday name, and the timeline shows each range |
| 21 | Business / settings page | New `/business` page: profile, location, radius, hours, days, average spend, supplier rules, data controls, inline validation |

## Second Figma review (5 comments, 7 November)

| Comment | Change |
| --- | --- |
| Two locations aren't clearly separate (Home) | One numbered block per location: pin badge, name, address, its own hours and next special day |
| Each location should have its own opening hours; hours per location (Business) | Weekly ranges and holidays now belong to each location. Business page: one card per location with Opening Hours and Holidays & Special Days. Rules use the nearest location's schedule; the timeline shades when any location is open |
| Refresh button breaks / scaling | The global button rule (44 px min-height, padding) stretched the 36 px circle into an oval. Now a 30 px circle that sits evenly in the status pill, in the app and in Figma |
| No "Sample data" labels | Removed from the header and the update message; the confidence reason reads "Not yet checked against a live source". The source is still listed under Business → Data. Gate M1's "prepared data visibly labelled" needs the team's agreement to this |

## Web interface guidelines (vercel-labs/web-interface-guidelines, fetched 7 Nov 2026)

Findings on the merged `main` templates before the change, and their status now.

| Finding (before) | Status |
| --- | --- |
| `base.html`: no skip link, no `theme-color` | Fixed |
| `_timeline.html`: horizontal scroll container not keyboard-focusable; gesture-only hint | Fixed: `tabindex="0"`, `role="region"`, label |
| `_timeline.html`: filtered reason only in `title` (hover-only) | Fixed: short reason visible, full reason in hidden text |
| `index.html`: unclear button labels | Fixed (see comment 9) |
| `insight.html`: revenue inputs lack `name`, `inputmode`, `autocomplete`; result not announced; hardcoded € format | Superseded: the calculator was replaced by a server-rendered metric; the assumption inputs on the Business page have names, `inputmode`, `autocomplete="off"` and inline errors |
| `draft.html`: no unsaved-changes warning; textarea `autocomplete` | Fixed: `beforeunload` guard, `autocomplete="off"` |
| Buttons and headings not Title Case | Fixed |
| No `touch-action`, tap highlight or pointer overscroll rules | Fixed |
| Disabled Copy explained only by `title` | Fixed: visible hint linked with `aria-describedby` |

Remaining, accepted for the hackathon:

- Server-rendered dates use a fixed Europe/Dublin format (`fmt`), not `Intl.DateTimeFormat`. They are consistent and in the café's own timezone.
- `font-variant-numeric: tabular-nums` is not used: Schibsted Grotesk's tabular forms also space out colons and commas.
- Google Fonts, Remix Icon, Leaflet and map tiles load from CDNs; offline, the page falls back to system fonts, missing icons and a "Map unavailable" note.

## Figma file

The Figma file (WY1WFAQ5QDR8nqrvf8kq4r) was reworked to match: page "Footfall v2" has the Colour variables, text styles, 49 Remix Icon components, the component library and the screens (desktop Home, Home after approval, Insight, Draft review, Draft approved, Business; mobile Home, Insight, Draft approved). The v1 design and its comments are on "Archive · v1 (your comments)".
