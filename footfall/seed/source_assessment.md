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
