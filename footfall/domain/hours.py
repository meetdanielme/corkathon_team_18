"""Opening hours: weekly ranges per day plus dated special days (holidays). Europe/Dublin local times.

place["hours"]          {"mon": [["08:00", "12:00"], ["13:00", "16:00"]], ..., "sun": []}
place["special_hours"]  [{"date": "2026-12-25", "label": "Christmas Day", "ranges": []}, ...]

A place is a location (each has its own hours) or, for older data, the business itself. Places without
"hours" fall back to the single opens/closes range on open_days.
"""
from __future__ import annotations

from datetime import date, datetime

from .timeutil import WEEKDAYS, at, weekday


def weekly(business: dict) -> dict[str, list[list[str]]]:
    if business.get("hours"):
        return {d: [list(r) for r in business["hours"].get(d, [])] for d in WEEKDAYS}
    return {d: [[business["opens"], business["closes"]]] if d in business.get("open_days", []) else []
            for d in WEEKDAYS}


def special(business: dict, day: date) -> dict | None:
    return next((s for s in business.get("special_hours") or [] if s["date"] == day.isoformat()), None)


def ranges_for(business: dict, day: date) -> tuple[list[list[str]], str | None]:
    """The day's opening ranges, and the special day's label when one applies."""
    s = special(business, day)
    if s:
        return [list(r) for r in s.get("ranges", [])], s.get("label") or "Special hours"
    return weekly(business)[weekday(day)], None


def merge(ranges: list[list[str]]) -> list[list[str]]:
    """Union of ranges, overlapping or touching ones joined."""
    out: list[list[str]] = []
    for a, b in sorted(list(r) for r in ranges):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def any_open(places: list[dict], day: date) -> tuple[list[list[str]], str | None]:
    """When at least one place is open, and the first special-day label among them."""
    found = [ranges_for(p, day) for p in places]
    return merge([r for rs, _ in found for r in rs]), next((label for _, label in found if label), None)


def windows(business: dict, day: date) -> list[tuple[datetime, datetime]]:
    return [(at(day, a), at(day, b)) for a, b in ranges_for(business, day)[0]]


def label(ranges: list[list[str]]) -> str:
    return ", ".join(f"{a}-{b}" for a, b in ranges) if ranges else "closed"


def legacy_fields(week: dict[str, list[list[str]]]) -> dict:
    """Summary columns kept for older code (weather): earliest open, latest close, days with any hours."""
    starts = [r[0] for d in WEEKDAYS for r in week.get(d, [])]
    ends = [r[1] for d in WEEKDAYS for r in week.get(d, [])]
    return {"opens": min(starts) if starts else "00:00", "closes": max(ends) if ends else "00:00",
            "open_days": [d for d in WEEKDAYS if week.get(d)]}


def summary(business: dict) -> list[tuple[str, str]]:
    """Group consecutive days with identical hours: [("Mon–Fri", "08:00–16:00"), ("Sun", "Closed")]."""
    week, out, i = weekly(business), [], 0
    while i < 7:
        j = i
        while j + 1 < 7 and week[WEEKDAYS[j + 1]] == week[WEEKDAYS[i]]:
            j += 1
        days = WEEKDAYS[i].capitalize() + (f"–{WEEKDAYS[j].capitalize()}" if j > i else "")
        rng = ", ".join(f"{a}–{b}" for a, b in week[WEEKDAYS[i]]) or "Closed"
        out.append((days, rng))
        i = j + 1
    return out
