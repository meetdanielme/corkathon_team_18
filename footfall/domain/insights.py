"""Deterministic insight rules (rule version r1).

Every label here is reproducible from visible inputs and is a heuristic, not a forecast.
See docs/design/footfall-design.md section "Rules r1" for the documented mapping.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta

from . import hours as hours_mod
from .cutoffs import cutoff_for, serving_delivery
from .geo import haversine_m
from .timeutil import fmt, fmt_day, parse_dt, weekday

RULE_VERSION = "r1"
PRE_BUFFER_MIN = 60          # assumed arrival buffer before an event
POST_BUFFER_MIN = 60         # assumed dispersal buffer after a published end
UNKNOWN_END_SPAN_MIN = 120   # assumed span when no end time is published
NEAR_M = 300
HORIZON_DAYS = 7
DECREASE_CATEGORIES = {"road_closure"}


@dataclass
class Insight:
    id: str
    business_id: str
    event_id: str
    title: str
    category: str
    day: str
    window_start: str
    window_end: str
    window_label: str
    window_basis: str
    distance_m: int
    overlap_min: int
    direction: str
    impact: str
    impact_points: dict
    confidence: str
    confidence_reasons: list[str]
    reasons: list[str]
    sources: list[dict]
    data_mode: str
    deadlines: list[dict]
    action_deadline: dict | None
    suggested_action: str
    conflicts: list[str] = field(default_factory=list)
    location: dict | None = None  # the business location nearest the event
    rule_version: str = RULE_VERSION

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Exclusion:
    event_id: str
    title: str
    reason: str


@dataclass
class ReviewFinding:
    event_id: str
    title: str
    missing: list[str]


def demand_window(start: datetime, end: datetime | None) -> tuple[datetime, datetime, str]:
    if end:
        return (start - timedelta(minutes=PRE_BUFFER_MIN), end + timedelta(minutes=POST_BUFFER_MIN),
                f"Assumed: {PRE_BUFFER_MIN} min before start to {POST_BUFFER_MIN} min after published end")
    return (start - timedelta(minutes=PRE_BUFFER_MIN), start + timedelta(minutes=UNKNOWN_END_SPAN_MIN),
            f"Assumed: end time not published, so {PRE_BUFFER_MIN} min before to "
            f"{UNKNOWN_END_SPAN_MIN} min after start. Review before relying on it")


def overlap_minutes(a0: datetime, a1: datetime, b0: datetime, b1: datetime) -> int:
    return max(0, int((min(a1, b1) - max(a0, b0)).total_seconds() // 60))


def impact_for(distance_m: float, overlap_min: int, attendance: int | None) -> tuple[str, dict]:
    pts = {
        "distance": 2 if distance_m <= NEAR_M else 1,
        "overlap": 2 if overlap_min >= 120 else 1 if overlap_min >= 30 else 0,
        "attendance": 0 if attendance is None else 2 if attendance >= 1000 else 1 if attendance >= 200 else 0,
    }
    total = sum(pts.values())
    pts["total"] = total
    return ("high" if total >= 5 else "medium" if total >= 3 else "low"), pts


def confidence_for(event: dict) -> tuple[str, list[str]]:
    low, medium = [], []
    if event.get("stale"):
        low.append("Source data is stale or the last check failed")
    if not any(e.get("excerpt") for e in event.get("evidence", [])):
        low.append("No supporting excerpt from the source")
    if event.get("data_mode") == "prepared":
        medium.append("Not yet checked against a live source")
    elif event.get("verification") != "verified":
        medium.append("Not yet verified against the source page")
    if not event.get("end_at"):
        medium.append("End time not published, so the window is assumed")
    notes = []
    if event.get("attendance") is None:
        notes.append("Attendance unknown, so it did not raise impact")
    level = "low" if low else "medium" if medium else "high"
    return level, low + medium + notes


def deadlines_for(day: date, window_start: datetime, suppliers: list[dict], now: datetime) -> list[dict]:
    by_supplier: dict[str, list[dict]] = {}
    for s in suppliers:
        by_supplier.setdefault(s["supplier"], []).append(s)
    out = []
    for name, rows in by_supplier.items():
        days = {r["delivery_day"] for r in rows}
        delivery = serving_delivery(days, day)
        if delivery is None:
            continue
        row = next(r for r in rows if r["delivery_day"] == weekday(delivery))
        cutoff = cutoff_for(row["cutoff_rule"], delivery)
        if cutoff > window_start:
            continue
        status = "missed" if cutoff <= now else "urgent" if cutoff - now <= timedelta(hours=24) else "upcoming"
        out.append({"supplier": name, "supplier_id": row["id"], "contact_label": row.get("contact_label"),
                    "delivery_day": fmt_day(delivery), "cutoff": cutoff.isoformat(), "cutoff_label": fmt(cutoff),
                    "status": status, "evidence": row.get("evidence") or row.get("demo_label")})
    return sorted(out, key=lambda d: d["cutoff"])


def evaluate(business: dict, event: dict, suppliers: list[dict], weather: dict[str, dict],
             now: datetime) -> Insight | Exclusion | ReviewFinding:
    title, eid = event["title"], event["id"]
    start = parse_dt(event.get("start_at"))
    missing = [k for k, v in (("start time", start), ("location", event.get("lat"))) if v is None]
    if missing:
        return ReviewFinding(eid, title, missing)
    end = parse_dt(event.get("end_at"))
    if event.get("access") == "restricted":
        return Exclusion(eid, title, "Private or restricted event, so not a public demand signal")
    locations = business.get("locations") or [business]
    near = min(locations, key=lambda loc: haversine_m(loc["lat"], loc["lon"], event["lat"], event["lon"]))
    dist = haversine_m(near["lat"], near["lon"], event["lat"], event["lon"])
    place = (near.get("name") or near.get("address") or "the café") if len(locations) > 1 else "the café"
    if dist > business["radius_m"]:
        return Exclusion(eid, title, f"{round(dist)} m away, outside the {business['radius_m']} m radius")
    day = start.date()
    if not (now.date() <= day < now.date() + timedelta(days=HORIZON_DAYS)):
        return Exclusion(eid, title, "Outside the 7-day view")
    sched = near if near.get("hours") is not None else business  # the nearest location's own hours
    ranges, special = hours_mod.ranges_for(sched, day)
    where = f" at {place}" if place != "the café" else ""
    if not ranges:
        return Exclusion(eid, title, f"Café is closed{where} for {special}" if special
                         else f"Café is closed{where} on {fmt_day(day)}")
    w0, w1, basis = demand_window(start, end)
    ov = sum(overlap_minutes(w0, w1, o0, o1) for o0, o1 in hours_mod.windows(sched, day))
    label = f"{w0:%H:%M}-{w1:%H:%M}"
    if ov == 0:
        return Exclusion(eid, title, f"Window {label} does not overlap opening hours {hours_mod.label(ranges)}")

    direction = "decrease" if event.get("category") in DECREASE_CATEGORIES else "increase"
    impact, pts = impact_for(dist, ov, event.get("attendance"))
    conf, conf_reasons = confidence_for(event)
    reasons = [f"{round(dist)} m from {place} (radius {business['radius_m']} m). Proximity is relevance "
               f"evidence, not proof of extra customers",
               f"Window {label} overlaps opening hours by {ov} min"]
    wx = weather.get(day.isoformat())
    if wx and wx.get("rain_prob_max") is not None and wx["rain_prob_max"] >= 60:
        reasons.append(f"Rain likely ({wx['rain_prob_max']}%). Context only; no sales effect assumed")

    dls = deadlines_for(day, w0, suppliers, now)
    live = [d for d in dls if d["status"] != "missed"]
    action = live[0] if live else (dls[0] if dls else None)
    if direction == "decrease":
        suggestion = f"Check whether deliveries or customer access are affected {fmt_day(day)} {label}."
    elif action and action["status"] != "missed":
        suggestion = (f"Review your {action['supplier']} order for {action['delivery_day']} before "
                      f"{action['cutoff_label']}. Whether to change quantities is your call.")
    elif action:
        suggestion = (f"The {action['supplier']} cutoff ({action['cutoff_label']}) has passed. "
                      f"Consider asking whether a late change is possible.")
    else:
        suggestion = f"Consider staffing and stock for {fmt_day(day)} {label}."

    sources = [{"url": e["url"], "retrieved_at": e["retrieved_at"], "excerpt": e.get("excerpt"),
                "stale": bool(event.get("stale"))} for e in event.get("evidence", [])]
    return Insight(
        id=f"{business['id']}:{eid}:{RULE_VERSION}", business_id=business["id"], event_id=eid, title=title,
        category=event.get("category") or "other", day=day.isoformat(), window_start=w0.isoformat(),
        window_end=w1.isoformat(), window_label=f"{fmt_day(day)} {label}", window_basis=basis,
        distance_m=round(dist), overlap_min=ov, direction=direction, impact=impact, impact_points=pts,
        confidence=conf, confidence_reasons=conf_reasons, reasons=reasons, sources=sources,
        data_mode=event.get("data_mode", "live"), deadlines=dls, action_deadline=action,
        suggested_action=suggestion,
        location={k: near.get(k) for k in ("name", "address", "lat", "lon")})


IMPACT_RANK = {"high": 3, "medium": 2, "low": 1}


def build(business: dict, events: list[dict], suppliers: list[dict], weather: dict[str, dict],
          now: datetime) -> dict:
    insights, excluded, review = [], [], []
    for ev in events:
        r = evaluate(business, ev, suppliers, weather, now)
        (insights if isinstance(r, Insight) else excluded if isinstance(r, Exclusion) else review).append(r)
    for a in insights:
        for b in insights:
            if a is not b and a.direction != b.direction and a.day == b.day and overlap_minutes(
                    parse_dt(a.window_start), parse_dt(a.window_end),
                    parse_dt(b.window_start), parse_dt(b.window_end)) > 0:
                a.conflicts.append(f"Competing signal: {b.title} may {b.direction} demand in an overlapping "
                                   f"window. Effects are shown separately, not netted.")
    insights.sort(key=lambda i: (i.day, -IMPACT_RANK[i.impact], i.window_start))
    return {"insights": insights, "excluded": excluded, "review": review}
