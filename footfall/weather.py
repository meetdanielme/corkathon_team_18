"""Open-Meteo forecast (free, no key). Stored with provider and retrieval time; context only."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections import defaultdict

from .domain.timeutil import now

URL = "https://api.open-meteo.com/v1/forecast"
UNITS = {"temp_max": "°C", "rain_prob_max": "%", "wind_max": "km/h"}


def fetch_forecast(lat: float, lon: float) -> dict:
    q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "timezone": "Europe/Dublin",
                                "forecast_days": 7,
                                "hourly": "temperature_2m,precipitation_probability,wind_speed_10m"})
    with urllib.request.urlopen(f"{URL}?{q}", timeout=10) as r:
        return json.load(r)


def summarise(payload: dict, opens: str, closes: str) -> dict[str, dict]:
    oh, ch = int(opens[:2]), int(closes[:2])
    h = payload.get("hourly") or {}
    out: dict[str, dict] = defaultdict(lambda: {"temp_max": None, "rain_prob_max": None, "wind_max": None})
    for i, t in enumerate(h.get("time", [])):
        day, hour = t[:10], int(t[11:13])
        if not oh <= hour < ch:
            continue
        d = out[day]
        for key, src in (("temp_max", "temperature_2m"), ("rain_prob_max", "precipitation_probability"),
                         ("wind_max", "wind_speed_10m")):
            v = h.get(src, [None] * (i + 1))[i]
            if v is not None:
                d[key] = v if d[key] is None else max(d[key], v)
    return dict(out)


def refresh(con, business: dict, fetcher=fetch_forecast) -> int:
    days = summarise(fetcher(business["lat"], business["lon"]), business["opens"], business["closes"])
    stamp = now().isoformat()
    for day, d in days.items():
        con.execute("""INSERT INTO weather (lat, lon, day, temp_max, rain_prob_max, wind_max, units, provider,
                       retrieved_at, kind) VALUES (?,?,?,?,?,?,?,?,?, 'forecast')
                       ON CONFLICT(lat, lon, day, kind) DO UPDATE SET temp_max=excluded.temp_max,
                       rain_prob_max=excluded.rain_prob_max, wind_max=excluded.wind_max,
                       retrieved_at=excluded.retrieved_at""",
                    (business["lat"], business["lon"], day, d["temp_max"], d["rain_prob_max"], d["wind_max"],
                     json.dumps(UNITS), "open-meteo", stamp))
    con.commit()
    return len(days)
