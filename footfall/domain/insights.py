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
from .timeutil import at, fmt, fmt_day, parse_dt, weekday

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
    reason: str      # one plain sentence for the owner
    short: str = ""  # a few words for the timeline bar


def distance_words(metres: float) -> str:
    m = round(metres)
    return f"{m} m" if m < 1000 else f"{m / 1000:.1f} km".replace(".0 km", " km")


def duration_words(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    hours = f"{h} hour{'s' if h != 1 else ''}" if h else ""
    mins = f"{m} minutes" if m else ""
    return " ".join(x for x in (hours, mins) if x)


def walk_words(metres: float) -> str:
    mins = max(1, round(metres / 80))  # about 80 m a minute on foot
    return f"about a {mins}-minute walk"


@dataclass
class ReviewFinding:
    event_id: str
    title: str
    missing: list[str]
    possible_duplicate: bool = False


def demand_window(start: datetime, end: datetime | None) -> tuple[datetime, datetime, str]:
    if end:
        return (start - timedelta(minutes=PRE_BUFFER_MIN), end + timedelta(minutes=POST_BUFFER_MIN),
                "Includes the hour before it starts and the hour after it ends, while people arrive and leave.")
    return (start - timedelta(minutes=PRE_BUFFER_MIN), start + timedelta(minutes=UNKNOWN_END_SPAN_MIN),
            "No finish time has been published, so we've assumed it runs for about two hours. Worth checking.")


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
    if event.get("possible_duplicate_of"):
        low.append("This may be another listing of an event already saved; check before planning for it twice")
    if event.get("stale"):
        low.append("We couldn't check the event page recently, so details may have changed")
    if not any(e.get("excerpt") for e in event.get("evidence", [])):
        low.append("We couldn't find the details written on the event page")
    if event.get("data_mode") == "prepared":
        medium.append("We haven't checked the event's own page yet")
    elif event.get("verification") != "verified":
        medium.append("We haven't confirmed this on the event's own page yet")
    if not event.get("end_at"):
        medium.append("No finish time published, so we've guessed how long it runs")
    notes = []
    if event.get("attendance") is None:
        notes.append("We don't know how many people are going")
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
                    "status": status, "evidence": row.get("evidence") or "Order cutoff from saved supplier settings; confirm with your supplier"})
    return sorted(out, key=lambda d: d["cutoff"])


def evaluate(business: dict, event: dict, suppliers: list[dict], weather: dict[str, dict],
             now: datetime) -> Insight | Exclusion | ReviewFinding:
    title, eid = event["title"], event["id"]
    start = parse_dt(event.get("start_at"))
    missing = [k for k, v in (("start time", start), ("location", event.get("lat"))) if v is None]
    if missing:
        return ReviewFinding(eid, title, missing, bool(event.get("possible_duplicate_of")))
    end = parse_dt(event.get("end_at"))
    if event.get("access") == "restricted":
        return Exclusion(eid, title, "It's a private event, so it won't bring passing trade", "Private event")
    locations = business.get("locations") or [business]
    near = min(locations, key=lambda loc: haversine_m(loc["lat"], loc["lon"], event["lat"], event["lon"]))
    dist = haversine_m(near["lat"], near["lon"], event["lat"], event["lon"])
    place = (near.get("name") or near.get("address") or "your café") if len(locations) > 1 else "your café"
    if dist > business["radius_m"]:
        return Exclusion(eid, title, f"It's {distance_words(dist)} away, too far to bring people past your door",
                         f"{distance_words(dist)} away")
    day = start.date()
    if not (now.date() <= day < now.date() + timedelta(days=HORIZON_DAYS)):
        return Exclusion(eid, title, "It isn't happening this week", "Not this week")
    sched = near if near.get("hours") is not None else business  # the nearest location's own hours
    ranges, special = hours_mod.ranges_for(sched, day)
    where = f" at {place}" if place != "your café" else ""
    if not ranges:
        return Exclusion(eid, title, f"You're closed{where} for {special}" if special
                         else f"You're closed{where} on {fmt_day(day)}", "You're closed")
    w0, w1, basis = demand_window(start, end)
    ov = sum(overlap_minutes(w0, w1, o0, o1) for o0, o1 in hours_mod.windows(sched, day))
    label = f"{w0:%H:%M}-{w1:%H:%M}"
    if ov == 0:
        when = ("after you close" if w0 >= at(day, ranges[-1][1]) else
                "before you open" if w1 <= at(day, ranges[0][0]) else "while you're closed")
        return Exclusion(eid, title, f"People will be around {w0:%H:%M}–{w1:%H:%M}, {when} "
                                     f"(you're open {hours_mod.label(ranges).replace('-', '–')})",
                         when.capitalize())

    direction = "decrease" if event.get("category") in DECREASE_CATEGORIES else "increase"
    impact, pts = impact_for(dist, ov, event.get("attendance"))
    conf, conf_reasons = confidence_for(event)
    hours_open = duration_words(ov)
    reasons = [f"It's {distance_words(dist)} from {place}, {walk_words(dist)}. Being close helps, but it "
               f"doesn't guarantee extra customers",
               f"People will be around for {hours_open} while you're open ({w0:%H:%M}–{w1:%H:%M})"]
    wx = weather.get(day.isoformat())
    if wx and wx.get("rain_prob_max") is not None and wx["rain_prob_max"] >= 60:
        reasons.append(f"Rain is likely that day ({wx['rain_prob_max']}% chance). Worth bearing in mind; it doesn't change the estimate above")

    dls = deadlines_for(day, w0, suppliers, now)
    live = [d for d in dls if d["status"] != "missed"]
    action = live[0] if live else (dls[0] if dls else None)
    if direction == "decrease":
        suggestion = (f"Check whether your deliveries or customers can still reach you on "
                      f"{fmt_day(day)}, {w0:%H:%M}–{w1:%H:%M}.")
    elif action and action["status"] != "missed":
        suggestion = (f"Have a look at your {action['supplier'].lower()} order for {action['delivery_day']}. "
                      f"Changes need to reach them by {action['cutoff_label']}. How much to change is up to you.")
    elif action:
        suggestion = (f"The {action['supplier'].lower()} order for {action['delivery_day']} closed at "
                      f"{action['cutoff_label']}. You could ask if a late change is possible.")
    else:
        suggestion = f"Think about staff and stock for {fmt_day(day)}, {w0:%H:%M}–{w1:%H:%M}."

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
                effect = "bring more customers" if b.direction == "increase" else "keep customers away"
                a.conflicts.append(f"{b.title} could {effect} at the same time, so the two may cancel each other out")
    insights.sort(key=lambda i: (i.day, -IMPACT_RANK[i.impact], i.window_start))
    return {"insights": insights, "excluded": excluded, "review": review}
