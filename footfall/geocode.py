"""Address lookup with OpenStreetMap Nominatim (free; max 1 request per second, identifying User-Agent).

Only called when an owner saves a new or changed address, never on page views.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "Footfall/0.1 (Corkathon 2026 team 18 demo)"


class GeocodeUnavailable(Exception):
    """The lookup service could not be reached."""


def geocode(address: str, timeout: float = 8) -> tuple[float, float] | None:
    """Return (lat, lon) for the best match, or None when nothing matches."""
    query = urllib.parse.urlencode({"q": address, "format": "jsonv2", "limit": 1})
    req = urllib.request.Request(f"{URL}?{query}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except (OSError, ValueError) as e:
        raise GeocodeUnavailable(str(e)) from e
    return (float(data[0]["lat"]), float(data[0]["lon"])) if data else None
