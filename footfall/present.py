"""Presentation helpers: relative times, cutoff urgency and icons (Remix Icon class names).

Display only. Rules, scoring and deadlines stay in footfall.domain.
"""
from __future__ import annotations

from datetime import datetime

from .domain.timeutil import TZ, parse_dt

SOON_H = 72   # under this many hours to a cutoff it is "soon" (amber)
NOW_H = 24    # under this it is "now" (red)

CATEGORY_ICONS = {
    "conferring": "ri-graduation-cap-line", "market": "ri-store-3-line", "road_closure": "ri-traffic-light-line",
    "concert": "ri-music-2-line", "festival": "ri-sparkling-2-line", "community": "ri-group-line",
    "sport": "ri-football-line",
}


def category_icon(category: str | None) -> str:
    return CATEGORY_ICONS.get(category or "", "ri-calendar-event-line")


def reason_icon(text: str) -> str:
    t = text.lower()
    if "walk" in t or " from " in t:
        return "ri-map-pin-range-line"
    if "while you're open" in t:
        return "ri-time-line"
    if "rain" in t:
        return "ri-showers-line"
    if "cancel" in t:
        return "ri-error-warning-line"
    return "ri-information-line"


def confidence_icon(text: str) -> str:
    t = text.lower()
    if "how many people" in t:
        return "ri-group-line"
    if "finish time" in t:
        return "ri-time-line"
    if "recently" in t:
        return "ri-cloud-off-line"
    if "details written" in t:
        return "ri-file-unknow-line"
    if "event's own page" in t:
        return "ri-global-line"
    return "ri-information-line"


def dist(metres) -> str:
    m = int(metres or 0)
    if m < 1000:
        return f"{m}\u00a0m"
    km = m / 1000
    return f"{km:.0f}\u00a0km" if km == int(km) else f"{km:.1f}\u00a0km"


def walk_minutes(metres) -> int:
    return max(1, round((metres or 0) / 80))  # about 80 m per minute on foot


def ago(value, now: datetime) -> str:
    dt = parse_dt(value) if isinstance(value, str) else value
    if not dt:
        return "never"
    secs = (now - dt).total_seconds()
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{int(secs // 60)} min ago"
    if secs < 86400:
        return f"{int(secs // 3600)} h ago"
    days = int(secs // 86400)
    return "yesterday" if days == 1 else f"{days} days ago"


def _until(hours: float) -> str:
    if hours < 1:
        return "within the hour"
    if hours < NOW_H:
        return f"in {int(hours)} hour{'s' if int(hours) != 1 else ''}"
    days = int(hours // 24)
    return "tomorrow" if days == 1 else f"in {days} days"


def countdown(deadline: dict | None, now: datetime, draft: dict | None = None) -> dict:
    """Attention state for an insight's supplier cutoff.

    level: done (message approved), missed, now (<24 h), soon (<72 h), later, none (no cutoff).
    """
    if draft and draft.get("approved_at"):
        sub = f"Order due {deadline['cutoff_label']}" if deadline else "No order to change"
        return {"level": "done", "icon": "ri-checkbox-circle-fill", "label": "Message ready to send", "sub": sub}
    if not deadline:
        return {"level": "none", "icon": "ri-calendar-check-line", "label": "No order to change", "sub": ""}
    hours = (parse_dt(deadline["cutoff"]) - now).total_seconds() / 3600
    sub = deadline["cutoff_label"]
    if hours <= 0:
        return {"level": "missed", "icon": "ri-close-circle-fill", "label": "Order deadline passed", "sub": sub}
    level = "now" if hours < NOW_H else "soon" if hours < SOON_H else "later"
    icon = {"now": "ri-alarm-warning-fill", "soon": "ri-time-fill", "later": "ri-calendar-event-fill"}[level]
    label = f"Order due {_until(hours)}"
    if draft:
        label += ", message not approved yet"
    return {"level": level, "icon": icon, "label": label, "sub": sub, "hours": hours}


DEFAULT_UPLIFT = {"low": 5, "medium": 10, "high": 20}  # % more customers per impact level, owner-editable


def revenue_estimate(impact: str, direction: str, overlap_min: int, business: dict) -> dict:
    """Apply the owner's own assumptions to one insight. Arithmetic on their numbers, not a forecast."""
    base = business.get("sales_baseline") or {}
    uplift = {**DEFAULT_UPLIFT, **(base.get("uplift_pct") or {})}
    sign = 1 if direction == "increase" else -1
    pct = sign * uplift[impact]
    hours = overlap_min / 60
    cph, spend = base.get("customers_per_hour"), business.get("avg_spend")
    out = {"pct": pct, "hours": hours, "customers_per_hour": cph, "avg_spend": spend,
           "usual": None, "extra": None, "revenue": None}
    if cph:
        out["usual"] = round(cph * hours)
        out["extra"] = round(cph * hours * pct / 100)
        if spend:
            out["revenue"] = round(cph * hours * pct / 100 * spend)
    return out


def local_iso(value) -> str:
    dt = parse_dt(value) if isinstance(value, str) else value
    return dt.astimezone(TZ).isoformat() if dt else ""
