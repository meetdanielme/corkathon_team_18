"""Timezone helpers. All business display and deadlines use Europe/Dublin."""
from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Dublin")
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def now() -> datetime:
    return datetime.now(TZ)


def parse_dt(value: str | None) -> datetime | None:
    """Parse ISO 8601. Naive values are interpreted as Europe/Dublin local time."""
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=TZ)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def at(d: date, hhmm: str) -> datetime:
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime.combine(d, time(h, m), tzinfo=TZ)


def weekday(d: date) -> str:
    return WEEKDAYS[d.weekday()]


def fmt(dt: datetime) -> str:
    d = dt.astimezone(TZ)
    return f"{d:%a} {d.day} {d:%b %H:%M}"  # no %-d: Windows strftime doesn't support it


def fmt_day(d: date) -> str:
    return f"{d:%a} {d.day} {d:%b}"
