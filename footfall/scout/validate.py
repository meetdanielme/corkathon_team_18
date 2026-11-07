"""Validate extracted findings before anything is persisted or shown."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from ..domain.timeutil import TZ, parse_dt


class OutsideWindow(str):
    """Normal eligibility exclusion, distinct from invalid source evidence."""


def _squash(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def validate_finding(f: dict, page_text: str, window_start: datetime, window_end: datetime) -> tuple[dict | None, str]:
    """Returns (clean_event, '') or (None, reason). A clean event may still lack location: that's
    allowed and becomes a review finding downstream, not an insight."""
    title = (f.get("title") or "").strip()
    if not title:
        return None, "missing title"
    excerpt = (f.get("excerpt") or "").strip()
    if not excerpt or _squash(excerpt) not in _squash(page_text):
        return None, f"excerpt not found verbatim on page for '{title}'"
    try:
        start = parse_dt(f.get("start_at"))
        end = parse_dt(f.get("end_at"))
    except ValueError:
        return None, f"unparseable date for '{title}'"
    if start and not (window_start - timedelta(days=1) <= start <= window_end + timedelta(days=1)):
        return None, OutsideWindow(f"'{title}' is outside the date window")
    if start and end and end < start:
        end = None
    clean = {
        "title": title[:200],
        "start_at": start.astimezone(TZ).isoformat() if start else None,
        "end_at": end.astimezone(TZ).isoformat() if end else None,
        "time_precision": f.get("time_precision") if f.get("time_precision") in ("datetime", "date") else (
            "datetime" if start else "unknown"),
        "venue_name": (f.get("venue_name") or None),
        "category": f.get("category") or "other",
        "access": f.get("access") if f.get("access") in ("public", "restricted") else "unknown",
        "attendance": f.get("attendance") if isinstance(f.get("attendance"), int) else None,
        "excerpt": excerpt[:500],
        "inferred_fields": [x for x in f.get("inferred_fields", []) if isinstance(x, str)],
    }
    return clean, ""
