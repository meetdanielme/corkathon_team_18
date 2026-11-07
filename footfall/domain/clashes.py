"""Delivery-blocked clashes (rule version r1).

A road closure near the business can block a supplier's drop even when it has no effect on
customers. This is an access problem, not a sales prediction: nothing here estimates demand,
revenue or quantities. Python does every time and distance comparison; no model is involved.

See docs/design/footfall-design.md for the surrounding rules.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta

from .geo import haversine_m
from .insights import HORIZON_DAYS, overlap_minutes
from .timeutil import TZ, at as at_time, fmt_day, parse_dt, weekday

CLOSURE_CATEGORIES = {"road_closure"}
CLASH_RADIUS_M = 200      # a closure further away than this does not block our door
EARLIER_DROP_MIN = 30     # suggested drop time: this many minutes before the closure starts


@dataclass
class DeliveryClash:
    id: str
    business_id: str
    event_id: str
    supplier: str
    contact_label: str | None
    delivery_day: str
    delivery_window: str
    closure_title: str
    closure_window_label: str
    closure_start: str
    closure_end: str
    day: str
    day_label: str
    distance_m: int
    suggested_drop_label: str
    data_mode: str
    sources: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _window_times(window: str, day_start: datetime) -> tuple[datetime, datetime] | None:
    """Parse a '08:30-09:00' delivery window into datetimes on the closure's own day."""
    try:
        start_s, end_s = window.split("-", 1)
        start = at_time(day_start, start_s.strip())
        end = at_time(day_start, end_s.strip())
    except (AttributeError, ValueError):
        return None
    return (start, end) if end > start else None


def clashes_for(business: dict, events: list[dict], suppliers: list[dict],
                now: datetime) -> list[DeliveryClash]:
    """Every delivery a nearby road closure would block, in the 7-day view.

    A clash needs all of: a closure category, a published start and end, coordinates within
    CLASH_RADIUS_M, a supplier delivering that weekday, and a real overlap. Touching edges are
    not an overlap: a closure starting exactly when the drop window ends still lets the van in.
    """
    out: list[DeliveryClash] = []
    horizon = now + timedelta(days=HORIZON_DAYS)
    for ev in events:
        if ev.get("category") not in CLOSURE_CATEGORIES:
            continue
        start, end = parse_dt(ev.get("start_at")), parse_dt(ev.get("end_at"))
        if not start or not end or ev.get("lat") is None or ev.get("lon") is None:
            continue
        if not (now.date() <= start.date() < horizon.date()):
            continue
        distance = haversine_m(business["lat"], business["lon"], ev["lat"], ev["lon"])
        if distance > CLASH_RADIUS_M:
            continue
        day_key = weekday(start)
        for s in suppliers:
            if s.get("delivery_day") != day_key:
                continue
            window = _window_times(s.get("delivery_window") or "", start)
            if not window:
                continue
            if overlap_minutes(start, end, *window) <= 0:
                continue
            drop = start - timedelta(minutes=EARLIER_DROP_MIN)
            out.append(DeliveryClash(
                id=f"{business['id']}:{ev['id']}:{s['id']}",
                business_id=business["id"], event_id=ev["id"],
                supplier=s["supplier"], contact_label=s.get("contact_label"),
                delivery_day=day_key, delivery_window=s["delivery_window"],
                closure_title=ev["title"],
                closure_window_label=f"{start.astimezone(TZ):%H:%M}-{end.astimezone(TZ):%H:%M}",
                closure_start=start.isoformat(), closure_end=end.isoformat(),
                day=start.astimezone(TZ).date().isoformat(), day_label=fmt_day(start.astimezone(TZ).date()),
                distance_m=int(round(distance)),
                suggested_drop_label=f"{drop.astimezone(TZ):%H:%M}",
                data_mode=ev.get("data_mode", "prepared"),
                sources=list(ev.get("evidence") or []),
            ))
    out.sort(key=lambda c: (c.day, c.delivery_window, c.supplier))
    return out


def clash_facts(clash: dict) -> dict:
    """The only values a draft about this clash may contain."""
    return {"contact": clash.get("contact_label") or "", "supplier": clash.get("supplier", ""),
            "title": clash.get("closure_title", ""), "day": clash.get("day_label", ""),
            "closure_window": clash.get("closure_window_label", ""),
            "delivery_window": clash.get("delivery_window", ""),
            "drop": clash.get("suggested_drop_label", "")}


def template_draft(clash: dict) -> tuple[str, str]:
    """Returns (recipient_label, text). Access and timing only: never quantities."""
    f = clash_facts(clash)
    who = f["contact"] or f["supplier"] or "Supplier"
    hi = f"Hi {f['contact']}," if f["contact"] else "Hi,"
    start = f["closure_window"].split("-")[0]
    return who, (f"{hi} heads-up: {f['title']} closes the road near us on {f['day']} from {start}. "
                 f"Our usual drop is {f['delivery_window']}. Could you get to us before {f['drop']} "
                 f"that day? Thanks!")
