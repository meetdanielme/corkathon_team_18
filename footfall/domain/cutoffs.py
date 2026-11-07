"""Supplier cutoffs as explicit weekly rules, never naive hour subtraction.

Rule shapes (stored as JSON on each supplier constraint):
  {"type": "weekday", "day": "thu", "time": "16:00"}
  {"type": "business_days_before", "n": 2, "time": "16:00", "closed": ["sun"]}
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from .timeutil import at, weekday


def cutoff_for(rule: dict, delivery_date: date, holidays: frozenset[date] = frozenset()) -> datetime:
    if rule["type"] == "weekday":
        day = delivery_date - timedelta(days=1)
        while weekday(day) != rule["day"]:
            day -= timedelta(days=1)
        return at(day, rule["time"])
    if rule["type"] == "business_days_before":
        day, left = delivery_date, int(rule["n"])
        closed = set(rule.get("closed", []))
        while left:
            day -= timedelta(days=1)
            if weekday(day) not in closed and day not in holidays:
                left -= 1
        return at(day, rule["time"])
    raise ValueError(f"unknown cutoff rule type: {rule['type']}")


def serving_delivery(delivery_days: set[str], trading_day: date) -> date | None:
    """The delivery that stocks a trading day: same morning, else the day before."""
    for back in (0, 1):
        d = trading_day - timedelta(days=back)
        if weekday(d) in delivery_days:
            return d
    return None
