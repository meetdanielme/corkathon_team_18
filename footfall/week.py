"""Presentation helper: lay out the 7-day view as a timeline (no rules or scoring here).

Positions are percentages of a 06:00-24:00 axis in Europe/Dublin local time.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from .domain import hours as hours_mod
from .domain.insights import HORIZON_DAYS, demand_window
from .domain.timeutil import TZ, at, parse_dt
from .present import countdown

AXIS_START_H, AXIS_END_H = 6, 24
TICKS = list(range(AXIS_START_H, AXIS_END_H + 1, 2))


def short_title(title: str) -> str:
    return re.sub(r"\s*\((fictional )?demo\)\s*$", "", title)


def _pct(dt: datetime, day) -> float:
    local = dt.astimezone(TZ)
    hours = (local - at(day, "00:00")).total_seconds() / 3600
    return max(0.0, min(100.0, (hours - AXIS_START_H) / (AXIS_END_H - AXIS_START_H) * 100))


def _span(day, start: datetime, end: datetime) -> dict:
    left = _pct(start, day)
    return {"left": round(left, 2), "width": round(max(_pct(end, day) - left, 1.5), 2),
            "label": f"{start.astimezone(TZ):%H:%M}–{end.astimezone(TZ):%H:%M}"}


def _assign_lanes(bars: list[dict]) -> int:
    lanes: list[float] = []
    for b in sorted(bars, key=lambda b: b["left"]):
        for i, right in enumerate(lanes):
            if b["left"] >= right:
                b["lane"], lanes[i] = i, b["left"] + b["width"]
                break
        else:
            b["lane"] = len(lanes)
            lanes.append(b["left"] + b["width"])
    return max(1, len(lanes))


def build_week(business: dict, result: dict, events: list[dict], now: datetime, only_day: str | None = None,
               drafts: dict | None = None, places: list[dict] | None = None) -> dict:
    """places: whose opening hours to shade. Default: every location (open anywhere)."""
    places = places or business.get("locations") or [business]
    by_id = {e["id"]: e for e in events}
    days = []
    for n in range(HORIZON_DAYS):
        day = (now.astimezone(TZ) + timedelta(days=n)).date()
        if only_day and day.isoformat() != only_day:
            continue
        ranges, special = hours_mod.any_open(places, day)
        row = {"date": day.isoformat(), "weekday": f"{day:%a}", "daynum": day.day, "month": f"{day:%b}",
               "today": n == 0, "open": bool(ranges), "special": special, "bars": [], "cutoffs": [],
               "hours": [_span(day, at(day, a), at(day, b)) for a, b in ranges]}
        for i in result["insights"]:
            if i.day == row["date"]:
                bar = _span(day, parse_dt(i.window_start), parse_dt(i.window_end))
                bar.update(kind="insight", id=i.id, title=short_title(i.title), direction=i.direction)
                row["bars"].append(bar)
        for x in result["excluded"]:
            ev = by_id.get(x.event_id) or {}
            start = parse_dt(ev.get("start_at"))
            if start and start.astimezone(TZ).date() == day:
                w0, w1, _ = demand_window(start, parse_dt(ev.get("end_at")))
                bar = _span(day, w0, w1)
                bar.update(kind="excluded", title=short_title(x.title), reason=x.reason, why=x.short or "Not relevant")
                row["bars"].append(bar)
        seen = set()
        for i in result["insights"]:
            d = i.action_deadline
            if not d or (d["supplier"], d["cutoff"]) in seen:
                continue
            cutoff = parse_dt(d["cutoff"])
            if cutoff.astimezone(TZ).date() == day:
                seen.add((d["supplier"], d["cutoff"]))
                cd = countdown(d, now, (drafts or {}).get(i.id))
                row["cutoffs"].append({"left": round(_pct(cutoff, day), 2), "supplier": d["supplier"],
                                       "time": f"{cutoff.astimezone(TZ):%H:%M}", "for_day": d["delivery_day"],
                                       "status": d["status"], "level": cd["level"], "icon": cd["icon"]})
        row["lanes"] = _assign_lanes(row["bars"])
        days.append(row)
    ticks = [{"label": f"{h:02d}:00" if h < 24 else "24:00",
              "left": round((h - AXIS_START_H) / (AXIS_END_H - AXIS_START_H) * 100, 2)} for h in TICKS]
    return {"days": days, "ticks": ticks}
