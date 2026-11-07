# Cork event-source assessment

Assessed 2026-11-07 against the scout task's rules: a page that lists dated events, within 1,000 m of the Washington Street café (51.8977, -8.4800), with an event during 7–13 November 2026. Twelve candidates were assessed; the four selected source rows are in `sources.json`.

## Selected sources

| Source page (publisher → venue) | Type | Venue point | Distance from café | Dated event visible in fetched text | Access check / decision |
| --- | --- | --- | ---: | --- | --- |
| [St Peter's Cork events](https://stpeterscork.ie/events) (St Peter's Cork → St Peter's Cork) | church | 51.8995487, -8.4788617 | 220 m | Recomposed by Max Richter: Vivaldi: The Four Seasons — Thu 12 Nov, 19:30 | Public; no login; fetcher returned readable event text; robots.txt HTTP 200 permits bot. No site-wide automated-fetch restriction located. Selected. Point is an OSM-mapped place result for the venue name/address, not a surveyed entrance pin. |
| [Cork Opera House What’s On](https://www.corkoperahouse.ie/whats-on/) (Cork Opera House → Cork Opera House) | venue | 51.9003, -8.4726 | 584 m | Cork City Ballet presents The Nutcracker — Thurs 5–Sat 7 Nov (includes 7 Nov) | Public; no login; fetcher returned readable event text; robots.txt HTTP 200 permits bot. Ticket terms reviewed and contain no automated-fetch restriction. Selected. Official venue coordinates. |
| [Triskel What’s On](https://triskelartscentre.ie/whats-on/) (Triskel Arts Centre → Triskel Arts Centre) | venue | 51.8978138, -8.4776339 | 163 m | The Devils and Pan’s Labyrinth — Sun 8–Wed 11 Nov; Harry Clarke event — Tue 10 Nov | Public; no login; fetcher returned readable dated listings; robots.txt HTTP 200 permits bot. Published ticket terms contain no automated-fetch restriction. Selected. Point from the Google Maps embed on Triskel’s official directions page. |
| [The Everyman What’s On](https://everymancork.com/) (The Everyman → The Everyman) | venue | 51.9014229, -8.4684970 | 891 m | Disco Pigs — Sat 31 Oct–Sat 14 Nov, so it is running during 7–13 Nov | Public; no login; fetcher returned readable event text; robots.txt HTTP 200 permits bot. Ticket terms reviewed and contain no automated-fetch restriction. Selected. Point geocoded from its published address with OpenStreetMap Photon. |

The source itself is the recurring event-listing page in every selected row, not a single event detail page. Distance is straight-line haversine distance from the café point. Each selected page was retrieved with `footfall.scout.fetch.fetch_text` on 2026-11-07 using the repository's bounded fetcher and normal TLS verification; the check output contained the event names and dates shown above. Robots checks used `FootfallHackathonBot/0.1`; all four selected paths were allowed. All four pages were public and fetched without authentication. Refresh interval is 24 hours.

## Issue #14 human-visible baseline (7–13 November 2026)

Re-fetched all four saved pages with `footfall.scout.fetch.fetch_text` on 2026-11-07. This baseline records listing entries visible in readable page text, not inferred show counts. Dates are Europe/Dublin. For every row, the page did **not** state an attendance figure; a ticket price or sold-out label is not an attendance count. `Unknown` means no start time or event-level venue was printed on the listing.

| Source | Human-visible listing title | Listed date(s) intersecting 7–13 Nov | Start time as printed | Venue as printed / safe attribution | Attendance stated? |
| --- | --- | --- | --- | --- | --- |
| [St Peter's Cork events](https://stpeterscork.ie/events) | Day Of The Dead Mexican Offering | On now, until Sat 7 Nov | Unknown | St Peter's Cork (venue calendar) | No |
| [St Peter's Cork events](https://stpeterscork.ie/events) | Creative Workshop – Write and Paint Your Own Calaverita | Sat 7 Nov | 15:00 | St Peter's Cork (venue calendar) | No |
| [St Peter's Cork events](https://stpeterscork.ie/events) | The Soul Of Mexico: A Day Of The Dead Dance Celebration | Sat 7 Nov | 17:00 | St Peter's Cork (venue calendar) | No |
| [St Peter's Cork events](https://stpeterscork.ie/events) | Recomposed By Max Richter: Vivaldi: The Four Seasons | Thu 12 Nov | 19:30 | St Peter's Cork (venue calendar) | No; €35 ticket price is listed, not attendance |
| [Cork Opera House What’s On](https://www.corkoperahouse.ie/whats-on/) | Cork City Ballet presents The Nutcracker | Thu 5–Sat 7 Nov (the listing overlaps the window on 7 Nov) | “Various Times”; individual starts unknown | Cork Opera House (venue What’s On page) | No; sold-out status is shown, no headcount |
| [Triskel What’s On](https://triskelartscentre.ie/whats-on/) | Cork Zine Fest Residency / Festival / Workshops | Thu 29 Oct–Sun 29 Nov (calendar shows it on each day 7–13 Nov) | Unknown | Triskel Arts Centre calendar; event-level venue not repeated | No |
| [Triskel What’s On](https://triskelartscentre.ie/whats-on/) | The Devils 55th Anniversary | Sun 8–Wed 11 Nov | Unknown | Triskel Arts Centre calendar; event-level venue not repeated | No |
| [Triskel What’s On](https://triskelartscentre.ie/whats-on/) | Pan’s Labyrinth 20th Anniversary | Sun 8–Wed 11 Nov | Unknown | Triskel Arts Centre calendar; event-level venue not repeated | No |
| [Triskel What’s On](https://triskelartscentre.ie/whats-on/) | 2 – Portrait of Harry Clarke (Famous Paintings and their Hidden Histories: Autumn 2026) | Tue 10 Nov | 11:00 | Triskel Arts Centre calendar; event-level venue not repeated | No |
| [Triskel What’s On](https://triskelartscentre.ie/whats-on/) | Cork International Film Festival 2026 | Fri 13–Sun 22 Nov (the listing overlaps the window on 13 Nov) | Unknown | Triskel Arts Centre calendar; specific screening venue not printed | No |
| [The Everyman What’s On](https://everymancork.com/) | Disco Pigs by Enda Walsh | Sat 31 Oct–Sat 14 Nov (the listing overlaps 7–13 Nov) | Unknown on the listing | The Everyman (venue What’s On section) | No |

**Baseline count:** 11 human-visible listing entries across the four selected source pages. Daniel's [read-only production comparison](https://github.com/meetdanielme/corkathon_team_18/issues/14#issuecomment-6709856443) used a cumulative Turso snapshot (8 live event rows, 9 evidence rows, 10 refresh summaries, 4 source states), not one complete extraction run. A separate [source/code review](https://github.com/meetdanielme/corkathon_team_18/issues/14#issuecomment-6709909279) re-fetched the four pages and checked stored fields and relevant implementation limits. Neither review made production writes or changed the scout prompt.

### Extraction comparison worksheet

Classifications below compare the 11 human-visible listings with saved production records and retained rejection errors. This is not a single-run accuracy measure: the database snapshot is cumulative and the system does not retain every raw candidate or a complete source-to-run event ledger. `Not captured; cause unconfirmed` means no event and no named rejection were present in retained state; it is not a confirmed model miss. Unknown facts remain unknown.

| Source | Human-visible listing | Human date/time from baseline | Saved record / retained rejection evidence | Comparison and limits |
| --- | --- | --- | --- | --- |
| St Peter's | Day Of The Dead Mexican Offering | Until Sat 7 Nov; start unknown | No saved event or named rejection in retained errors | Not captured in saved state; cause unconfirmed. |
| St Peter's | Creative Workshop – Write and Paint Your Own Calaverita | Sat 7 Nov, 15:00 | Saved start 15:00; end and attendance NULL; excerpt prints 15:00 | Date/time match. Duplicate venue spelling variant (`St Peter's Cork` vs `St Peters Cork`) exists; the latter lacks coordinates and is flagged for review. |
| St Peter's | The Soul Of Mexico: A Day Of The Dead Dance Celebration | Sat 7 Nov, 17:00 | Saved start 17:00; end and attendance NULL; excerpt prints 17:00 | Date/time match; correctly excluded by opening-hours rules. Same duplicate venue issue. |
| St Peter's | Recomposed By Max Richter: Vivaldi: The Four Seasons | Thu 12 Nov, 19:30 | Saved start 19:30; end and attendance NULL; excerpt prints 19:30 | Date/time match; correctly excluded by opening-hours rules. Same duplicate venue issue. |
| Cork Opera House | Cork City Ballet presents The Nutcracker | Thu 5–Sat 7 Nov; listing overlaps 7 Nov; “Various Times” | No saved event; runs 2, 3 and 4 explicitly report outside-window rejection; raw candidate not retained | Confirmed historical rejection despite the human date range overlapping the seven-day window. Exact extracted date unavailable. |
| Triskel | Cork Zine Fest Residency / Festival / Workshops | Thu 29 Oct–Sun 29 Nov; calendar shows it 7–13 Nov | No saved event or named rejection in retained errors | Not captured in saved state; cause unconfirmed. |
| Triskel | The Devils 55th Anniversary | Sun 8–Wed 11 Nov; start unknown | No saved event; runs 6 and 7 report evidence-validation rejection: excerpt not found verbatim | Confirmed rejection reason. Raw rejected excerpt unavailable. |
| Triskel | Pan’s Labyrinth 20th Anniversary | Sun 8–Wed 11 Nov; performance times unknown | Saved 8 Nov 00:00–11 Nov 00:00 with `time_precision=date`; excerpt gives the date range | Date range captured, not screening times. Rules evaluate the Sunday start when the café is closed, so later open-day screenings in this multi-day run are not represented. |
| Triskel | 2 – Portrait of Harry Clarke (Famous Paintings and their Hidden Histories: Autumn 2026) | Tue 10 Nov, 11:00 | Saved start 11:00; end and attendance NULL; excerpt prints 11:00; venue inferred from calendar; evidence now stale | Date/time match. Calendar-level venue attribution is inferred rather than repeated in the excerpt. |
| Triskel | Cork International Film Festival 2026 | Fri 13–Sun 22 Nov; screening times and venue unknown | No saved event; run 7 reports evidence-validation rejection: excerpt not found verbatim | Confirmed rejection reason. Raw rejected excerpt unavailable. |
| The Everyman | Disco Pigs by Enda Walsh | Sat 31 Oct–Sat 14 Nov; overlaps all of 7–13 Nov; exact performance times unknown | No saved event; runs 2, 3 and 4 explicitly report outside-window rejection; raw candidate not retained | Confirmed historical rejection despite human date range overlapping the window. Exact extracted date unavailable. |

### Stored-data and run findings

- The snapshot contains 8 live rows and 9 evidence rows. The four timed baseline titles retain their published starts (15:00, 17:00, 19:30 and 11:00); their `end_at` values are NULL. Attendance is NULL on all eight live rows. No attendance or end times were invented in stored records.
- The previously reported one-hour display offsets are **demand-window planning bounds**, not extracted start times. Rules subtract a 60-minute arrival buffer; when a source gives no end time, the window assumes a duration ending two hours after the published start and records its `window_basis`. This explains 15:00 → 14:00–17:00, 17:00 → 16:00–19:00, 19:30 → 18:30–21:30, and 11:00 → 10:00–13:00.
- Pan's Labyrinth is stored with date precision and midnight bounds. The midnights are date encoding, not known screening times. Because relevance checks use the run's start date, the Sunday start is excluded for a Sunday-closed café even though the listing continues through Wednesday.
- Three historical St Peter's duplicates differ only in venue spelling/punctuation: `St Peter's Cork` versus `St Peters Cork`; the unpunctuated variants lack coordinates. The matching logic treated these venue keys as different. PRs [#49](https://github.com/meetdanielme/corkathon_team_18/pull/49) and [#50](https://github.com/meetdanielme/corkathon_team_18/pull/50) preserve separate IDs and flag possible duplicates for review. They were not deleted or manually merged; production verification of the new warning behavior remains pending.
- Run 6 (15:10:18–15:10:48 UTC) attempted all four sources, made four model calls and recorded five upserts; it was partial because the Devils excerpt failed verbatim-evidence validation. Five evidence retrieval times fall within that run, but there is no explicit run/event foreign key, so this is timestamp correlation only. Run 7 recorded The Devils and CIFF excerpt rejections. Runs 8, 10 and 12 report `ok` with three upserts; `ok` does not mean all 11 baseline listings were captured. Run 13 (15:45:27–15:45:51 UTC) was partial because Triskel hit the shared AI allowance. No reset or increase was made.
- Refresh history stores error strings, not every raw extracted or rejected candidate. Ordinary outside-window findings are omitted from error arrays; accepted evidence has no run foreign key. The complete candidate/rejection set and a full accuracy or confusion-matrix score cannot be reconstructed from retained data.

### Deployed app observations (historical)

Earlier 7 Nov dashboard checks showed a partial refresh, stale evidence, outside-window rejection messages for Nutcracker and Disco Pigs, and a duplicate-key error. Those snapshots preceded the merged duplicate-handling changes in PRs #49/#50. Daniel's later database-backed comparison corrected the interpretation of the displayed time windows: the stored extraction starts match the human sources; the hour offsets are planning buffers. Treat the earlier snapshots as historical evidence, not as verified current production behavior.

### Review and remaining limits

Daniel's independent database comparison and separate source/code review are recorded in issue comments [6709856443](https://github.com/meetdanielme/corkathon_team_18/issues/14#issuecomment-6709856443) and [6709909279](https://github.com/meetdanielme/corkathon_team_18/issues/14#issuecomment-6709909279). The latter explicitly identifies itself as an assistant review and says it is not Olan's signoff or a recorded team agreement. Production verification of PR #50's duplicate warnings is still pending. No prompt changes were made. Keep final extraction-quality signoff open until the independent teammate review and production check are recorded.

## Other candidates assessed

| Candidate | Type | Finding | Decision |
| --- | --- | --- | --- |
| [UCC Chemistry UnCORKed](https://www.ucc.ie/en/study/upcomingeventsinucc/chemistry-uncorked-exhibition.html) | university | Single event detail page for 12–13 Nov at The Hub; not a recurring/listing page. UCC's terms limit website content use beyond browsing/temporary storage for viewing without written consent. | Reject: wrong page shape; UCC terms also make automated reuse unclear. |
| [UCC FUAIM – The Vanbrugh & Friends](https://www.ucc.ie/en/fmt/music/events/13-nov---the-vanbrugh--friends.html) | university | Single event detail page for 13 Nov at The Hub; not a source listing page. Same UCC terms apply. | Reject: wrong page shape and reuse not cleared. |
| [UCC Autumn Conferrings](https://www.ucc.ie/en/conferrings/) | university | Official dated page, but conferrings end 9 Nov and UCC is at the 1 km boundary (about 941 m to the campus reference point). | Reject: location is borderline and no event listing relevant beyond 9 Nov; terms constrain automated reuse. |
| [Cork City Council November events](https://www.corkcity.ie/en/our-city-is-changing/festivals-and-events/november-events/) | council | Public listing says CIFF runs 7–17 Nov, but lacks event-level venues/times and its dates conflict with the festival organiser's 12–22 Nov programme. | Reject: citywide venue ambiguity; doesn't provide reliable venue points for the radius filter. |
| [Cork International Film Festival 2026 programme announcement](https://corkfilmfest.org/cork-international-film-festival-unveils-full-film-event-programme-for-71st-edition/) | event organiser | Lists dated events across multiple venues for 12–22 Nov. | Reject: mixed venues require per-event venue coordinates; not a single venue source. |
| [Marina Market events](https://www.marinamarket.ie/events) | market | Public calendar; source venue point is roughly 2.0 km from the café. Next listed event in the checked window was Science at the Marina on 14 Nov. | Reject: beyond radius and the dated event is outside 7–13 Nov. |
| [Cork Zine Festival at Crawford Art Gallery](https://crawfordartgallery.ie/cork-zine-festival-2026/) | gallery / event organiser | Dated article for 3–25 Nov, describing festival activities at several locations. | Reject: article is not a venue's multi-event listing and activities span multiple places. |
| [St Fin Barre's Cathedral events](https://www.stfinbarres.ie/events/) | church | Page showed no upcoming events on the check date. | Reject: no dated event in the requested window. |

## Coordinate and access notes

- Café point and radius come from `footfall/seed/business.json`: 51.8977, -8.4800 and 1,000 m.
- Cork Opera House publishes 51.9003°N, 8.4726°W on its [How to Find Us page](https://www.corkoperahouse.ie/your-visit/parking/).
- Triskel's official [Map & Directions page](https://triskelartscentre.ie/map-and-directions/) embeds a Google Map centered at 51.8978138, -8.4776339.
- The Everyman lists 15 MacCurtain Street, T23 E094; OpenStreetMap Photon resolves that address to the mapped theatre point used above.
- St Peter's publishes 87a North Main Street. OpenStreetMap Photon resolves the venue name and street to the mapped place point used above. It is an approximate mapped point; the exact entrance was not independently surveyed. It is about 220 m from the café, leaving substantial room inside the 1,000 m radius.
- Robots.txt is a crawl-policy signal, not a legal ruling. The selected pages were allowed for the project user agent, public, login-free and successfully fetched. Public ticket terms for Triskel and The Everyman and venue terms for Cork Opera House were checked; none contains a restriction on automated fetching. No site-wide terms governing automated fetching were found for St Peter's. Confirm with the teammate reviewer that this evidence is sufficient for the demo.
- UCC was not selected because its [website terms](https://www.ucc.ie/en/legal/) expressly permit browsing and temporary storage for viewing, while requiring prior written consent for other content use. Do not use UCC for recurring extraction without written clearance.
