"""Parse and validate the Business page form.

Each location card posts a hidden loc_key (l0, l1, n3, ...) and fields prefixed with it:
{key}_name, {key}_address, {key}_{day}_start/_end (repeated per range),
{key}_special_date/_label/_mode/_start/_end (repeated per special day).
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


def _special_state(specials: list[dict]) -> list[dict]:
    return [{"date": x["date"], "label": x.get("label", ""), "mode": "hours" if x.get("ranges") else "closed",
             "start": x["ranges"][0][0] if x.get("ranges") else "", "end": x["ranges"][0][1] if x.get("ranges") else ""}
            for x in specials]


def state_from_business(b: dict) -> dict:
    """What the form shows on first load."""
    base = b.get("sales_baseline") or {}
    uplift = {**DEFAULT_UPLIFT, **(base.get("uplift_pct") or {})}
    return {
        "name": b["name"], "radius_m": b["radius_m"],
        "avg_spend": "" if b.get("avg_spend") is None else b["avg_spend"],
        "customers_per_hour": base.get("customers_per_hour") or "",
        **{f"uplift_{k}": v for k, v in uplift.items()},
        "locations": [{"key": f"l{i}", "name": loc.get("name") or "", "address": loc["address"],
                       "hours": hours_mod.weekly(loc), "special": _special_state(loc.get("special_hours") or [])}
                      for i, loc in enumerate(b.get("locations") or [])],
    }


def _location(form, key: str, errors: dict) -> dict:
    """One location card: name, address, weekly ranges and special days (validated, not yet looked up)."""
    loc = {"key": key, "name": form.get(f"{key}_name", "").strip(), "address": form.get(f"{key}_address", "").strip(),
           "hours": {}, "special": [], "special_hours": []}
    for d in WEEKDAYS:
        rng, err = _ranges(form.getlist(f"{key}_{d}_start"), form.getlist(f"{key}_{d}_end"))
        loc["hours"][d] = rng
        if err:
            errors[f"{key}_hours_{d}"] = err
    if not any(loc["hours"].values()):
        errors[f"{key}_hours"] = "Add opening hours for at least one day."
    seen = set()
    cols = [form.getlist(f"{key}_special_{c}") for c in ("date", "label", "mode", "start", "end")]
    for d, label, mode, a, b in zip(*cols):
        row = {"date": d.strip(), "label": label.strip(), "mode": mode, "start": a.strip(), "end": b.strip()}
        if not row["date"] and not row["label"]:
            continue
        loc["special"].append(row)
        err_key = f"{key}_special_{len(loc['special']) - 1}"
        try:
            date.fromisoformat(row["date"])
        except ValueError:
            errors[err_key] = "Choose a date for this special day."
            continue
        if row["date"] in seen:
            errors[err_key] = "This date is already listed."
            continue
        seen.add(row["date"])
        ranges = []
        if mode == "hours":
            ranges, err = _ranges([row["start"]], [row["end"]])
            if err or not ranges:
                errors[err_key] = err or "Enter the opening and closing time, or mark the day closed."
                continue
        loc["special_hours"].append({"date": row["date"], "label": row["label"] or "Special hours", "ranges": ranges})
    loc["special_hours"].sort(key=lambda x: x["date"])
    return loc


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

    # Locations, each with its own hours. Look up only addresses that are new or changed.
    known = {loc["address"].strip().lower(): loc for loc in existing_locations}
    cards = [_location(form, key, errors) for key in form.getlist("loc_key")]
    cards = [c for c in cards if c["address"] or c["name"]]
    state["locations"] = cards
    locations = []
    for c in cards:
        k = c["key"]
        if not c["address"]:
            errors[f"{k}_address"] = "Enter an address, or remove this location."
            continue
        match = known.get(c["address"].lower())
        if match:
            coords = (match["lat"], match["lon"])
        else:
            try:
                coords = geocoder(c["address"])
            except GeocodeUnavailable:
                errors[f"{k}_address"] = "Couldn't look up this address right now. Check your connection and save again."
                continue
            if not coords:
                errors[f"{k}_address"] = "Couldn't find this address. Add the street and town, for example Washington Street, Cork."
                continue
        locations.append({"name": c["name"], "address": c["address"], "lat": coords[0], "lon": coords[1],
                          "hours": c["hours"], "special_hours": c["special_hours"]})
    if not cards:
        errors["locations"] = "Add at least one location."
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
