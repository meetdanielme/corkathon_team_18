"""Parse and validate the Business page form.

Repeated rows (addresses, opening ranges, special days) arrive as parallel lists:
loc_name/loc_address, {day}_start/{day}_end, special_date/special_label/special_mode/special_start/special_end.
"""
from __future__ import annotations

import re
from datetime import date
from itertools import pairwise

from .domain import hours as hours_mod
from .domain.timeutil import WEEKDAYS
from .geocode import GeocodeUnavailable
from .present import DEFAULT_UPLIFT

TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _ranges(starts: list[str], ends: list[str]) -> tuple[list[list[str]], str | None]:
    """Pair start/end times, skip empty pairs, and check each range and their order."""
    pairs = [[a.strip(), b.strip()] for a, b in zip(starts, ends) if a.strip() or b.strip()]
    for a, b in pairs:
        if not (TIME_RE.match(a) and TIME_RE.match(b)):
            return pairs, "Enter times as HH:MM, for example 08:00."
        if a >= b:
            return pairs, f"{a} to {b}: the closing time must be after the opening time."
    pairs.sort()
    for (_, end), (start, _) in pairwise(pairs):
        if start < end:
            return pairs, "These opening times overlap. Merge them or change one."
    return pairs, None


def state_from_business(b: dict) -> dict:
    """What the form shows on first load."""
    base = b.get("sales_baseline") or {}
    uplift = {**DEFAULT_UPLIFT, **(base.get("uplift_pct") or {})}
    return {
        "name": b["name"], "radius_m": b["radius_m"],
        "avg_spend": "" if b.get("avg_spend") is None else b["avg_spend"],
        "customers_per_hour": base.get("customers_per_hour") or "",
        **{f"uplift_{k}": v for k, v in uplift.items()},
        "locations": [{"name": loc.get("name") or "", "address": loc["address"]} for loc in b.get("locations") or []]
        or [{"name": "", "address": ""}],
        "hours": hours_mod.weekly(b),
        "special": [{"date": s["date"], "label": s.get("label", ""), "mode": "hours" if s.get("ranges") else "closed",
                     "start": s["ranges"][0][0] if s.get("ranges") else "",
                     "end": s["ranges"][0][1] if s.get("ranges") else ""} for s in b.get("special_hours") or []],
    }


def parse(form, existing_locations: list[dict], geocoder) -> tuple[dict, list[dict], dict, dict]:
    """Returns (business fields, locations, errors, form state for re-rendering)."""
    fields, errors = {}, {}
    state = {k: form.get(k, "") for k in ("name", "radius_m", "avg_spend", "customers_per_hour",
                                          "uplift_low", "uplift_medium", "uplift_high")}

    name = state["name"].strip()
    if name:
        fields["name"] = name
    else:
        errors["name"] = "Enter the business name."

    # Locations: look up only addresses that are new or changed
    known = {loc["address"].strip().lower(): loc for loc in existing_locations}
    rows = [{"name": n.strip(), "address": a.strip()} for n, a in zip(form.getlist("loc_name"), form.getlist("loc_address"))]
    rows = [r for r in rows if r["address"] or r["name"]]
    state["locations"] = rows or [{"name": "", "address": ""}]
    locations = []
    for i, r in enumerate(rows):
        if not r["address"]:
            errors[f"loc_{i}"] = "Enter an address, or remove this location."
            continue
        match = known.get(r["address"].lower())
        if match:
            locations.append({**r, "lat": match["lat"], "lon": match["lon"]})
            continue
        try:
            found = geocoder(r["address"])
        except GeocodeUnavailable:
            errors[f"loc_{i}"] = "Couldn't look up this address right now. Check your connection and save again."
            continue
        if not found:
            errors[f"loc_{i}"] = "Couldn't find this address. Add the street and town, for example Washington Street, Cork."
            continue
        locations.append({**r, "lat": found[0], "lon": found[1]})
    if not rows:
        errors["locations"] = "Add at least one address."

    # Weekly opening hours
    week = {}
    for d in WEEKDAYS:
        rng, err = _ranges(form.getlist(f"{d}_start"), form.getlist(f"{d}_end"))
        week[d] = rng
        if err:
            errors[f"hours_{d}"] = err
    state["hours"] = week
    if not any(week.values()):
        errors["hours"] = "Add opening hours for at least one day."
    fields["hours"] = week
    fields.update(hours_mod.legacy_fields(week))

    # Special days (holidays): closed, or one range of different hours
    specials, seen = [], set()
    cols = [form.getlist(k) for k in ("special_date", "special_label", "special_mode", "special_start", "special_end")]
    state["special"] = []
    for i, (d, label, mode, a, b) in enumerate(zip(*cols)):
        row = {"date": d.strip(), "label": label.strip(), "mode": mode, "start": a.strip(), "end": b.strip()}
        if not row["date"] and not row["label"]:
            continue
        state["special"].append(row)
        idx = len(state["special"]) - 1
        try:
            date.fromisoformat(row["date"])
        except ValueError:
            errors[f"special_{idx}"] = "Choose a date for this special day."
            continue
        if row["date"] in seen:
            errors[f"special_{idx}"] = "This date is already listed."
            continue
        seen.add(row["date"])
        ranges = []
        if mode == "hours":
            ranges, err = _ranges([row["start"]], [row["end"]])
            if err or not ranges:
                errors[f"special_{idx}"] = err or "Enter the opening and closing time, or mark the day closed."
                continue
        specials.append({"date": row["date"], "label": row["label"] or "Special hours", "ranges": ranges})
    fields["special_hours"] = sorted(specials, key=lambda s: s["date"])

    try:
        radius = int(state["radius_m"])
        if not 100 <= radius <= 5000:
            raise ValueError
        fields["radius_m"] = radius
    except ValueError:
        errors["radius_m"] = "Enter a radius between 100 and 5000 metres."

    spend = str(state["avg_spend"]).strip().replace(",", ".")
    fields["avg_spend"] = None
    if spend:
        try:
            fields["avg_spend"] = round(float(spend), 2)
            if fields["avg_spend"] < 0:
                raise ValueError
        except ValueError:
            errors["avg_spend"] = "Enter an amount in euro, for example 7.50."

    baseline = {"uplift_pct": {}}
    cph = str(state["customers_per_hour"]).strip()
    if cph:
        try:
            baseline["customers_per_hour"] = int(cph)
            if not 0 < baseline["customers_per_hour"] <= 1000:
                raise ValueError
        except ValueError:
            errors["customers_per_hour"] = "Enter a whole number of customers per hour, for example 12."
    for level in ("low", "medium", "high"):
        try:
            pct = int(state[f"uplift_{level}"])
            if not 0 <= pct <= 100:
                raise ValueError
            baseline["uplift_pct"][level] = pct
        except ValueError:
            errors[f"uplift_{level}"] = "Enter a percentage from 0 to 100."
    fields["sales_baseline"] = baseline
    return fields, locations, errors, state
