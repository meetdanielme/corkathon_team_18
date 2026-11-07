# Footfall data story talk track

## 30-second version

Four Cork pages feed Footfall. Our human baseline has 11 listings for 7–13 November. A read-only production database audit found eight live rows representing five baseline titles; four other titles have named historical rejections, and two are absent with the cause unknown. The earlier one-hour display offsets were planning windows; stored starts match the source. The retained history is incomplete, so we cannot claim an accuracy score. Demo events are fictional.

## Delivery notes

- Keep the distinction clear: 11 is a count of human-visible listing entries, not extracted event count.
- Do not report the display windows as incorrect extracted start times: the stored starts match the source, while `demand_window` applies an arrival buffer and an assumed duration.
- Four baseline titles have named historical rejection records; two absent titles have no retained rejection reason. Explain that rejected candidates are not fully retained, so false positives and a complete accuracy score cannot be established.
- PRs #49 and #50 flag three old St Peter's spelling-variant pairs without merging them. Production verification of the new warning behavior is still pending.
- If asked about customer numbers or sales, say the sources do not state attendance and Footfall does not infer sales.
