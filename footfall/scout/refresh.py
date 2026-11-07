"""Manual, bounded refresh of the saved source directory (plus weather). Synchronous by design."""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from .. import db
from ..domain.timeutil import now as tz_now, parse_dt
from .extract import extract_events
from .fetch import FetchError, fetch_text
from .validate import OutsideWindow, validate_finding

# A refresh stays bounded. 90 s suits a hosted model; a model running locally is slower, so the
# wall-clock budget is overridable rather than silently truncating the run at two sources.
DEFAULT_LIMITS = {"max_sources": int(os.getenv("FOOTFALL_MAX_SOURCES", "15")),
                  "max_seconds": float(os.getenv("FOOTFALL_REFRESH_MAX_SECONDS", "90")),
                  "max_llm_calls": int(os.getenv("FOOTFALL_MAX_LLM_CALLS", "15"))}
PREPARED = Path(__file__).parent.parent / "seed" / "prepared_events.json"


class RefreshBusy(Exception):
    pass


def _venue_matches(event_venue: str | None, src: dict) -> bool:
    if not event_venue:
        return True
    a, b = db.normalise(event_venue), db.normalise(src.get("venue_name") or src["org_name"])
    return bool(a and b) and (a in b or b in a)


def _start_run(con, mode: str, at: datetime) -> int:
    running = con.execute("SELECT id, started_at FROM refresh_runs WHERE status='running' "
                          "ORDER BY id DESC LIMIT 1").fetchone()
    if running and at - parse_dt(running["started_at"]) < timedelta(minutes=5):
        raise RefreshBusy("a refresh is already running")
    cur = con.execute("INSERT INTO refresh_runs (started_at, mode, status) VALUES (?,?, 'running')",
                      (at.isoformat(), mode))
    con.commit()
    return cur.lastrowid


def run_prepared(con, at: datetime | None = None, path: Path = PREPARED) -> dict:
    at = at or tz_now()
    run_id = _start_run(con, "prepared", at)
    n = 0
    for item in json.loads(path.read_text(encoding="utf-8")):
        ev = {**item["event"], "data_mode": "prepared", "verification": "prepared"}
        _, created = db.upsert_event(con, ev, {"url": item["evidence"]["url"], "retrieved_at": at.isoformat(),
                                               "excerpt": item["evidence"].get("excerpt"), "source_id": None,
                                               "uncertainty": "Prepared demo data"}, at)
        n += 1
    con.execute("UPDATE refresh_runs SET ended_at=?, status='ok', events_upserted=? WHERE id=?",
                (tz_now().isoformat(), n, run_id))
    con.commit()
    return db.last_run(con)


def run_live(con, llm, at: datetime | None = None, fetcher=fetch_text, limits: dict | None = None,
             weather_refresh=None) -> dict:
    at = at or tz_now()
    lim = {**DEFAULT_LIMITS, **(limits or {})}
    run_id = _start_run(con, "live", at)
    t0, errors, attempted, ok, upserted = time.monotonic(), [], 0, 0, 0
    calls_before = llm.calls
    w0, w1 = at, at + timedelta(days=7)
    for src in db.get_sources(con)[: lim["max_sources"]]:
        if time.monotonic() - t0 > lim["max_seconds"] or llm.calls - calls_before >= lim["max_llm_calls"]:
            errors.append("Execution limit reached; remaining sources not checked")
            break
        attempted += 1
        stamp = tz_now().isoformat()
        con.execute("UPDATE sources SET last_attempt_at=? WHERE id=?", (stamp, src["id"]))
        con.commit()  # release the write lock before network/model calls
        try:
            final_url, text = fetcher(src["url"])
            found = extract_events(llm, src, text, w0.date().isoformat(), w1.date().isoformat())
            kept = 0
            for f in found["events"]:
                clean, why = validate_finding(f, text, w0, w1)
                if not clean:
                    if isinstance(why, OutsideWindow):
                        logging.getLogger(__name__).info("Skipped finding from %s: %s", src["id"], why)
                        continue
                    errors.append(f"{src['id']}: rejected finding ({why})")
                    continue
                match = _venue_matches(clean["venue_name"], src)
                ev = {**clean, "venue_name": clean["venue_name"] or src.get("venue_name"),
                      "lat": src.get("lat") if match else None, "lon": src.get("lon") if match else None,
                      "verification": "verified", "data_mode": "live"}
                _, created = db.upsert_event(con, ev, {
                    "url": final_url, "retrieved_at": stamp, "excerpt": clean["excerpt"], "source_id": src["id"],
                    "extracted": clean, "uncertainty": "; ".join(found.get("uncertainties", [])) or None}, at)
                kept += 1
                upserted += 1
            con.execute("UPDATE sources SET status='ok', last_success_at=?, last_error=NULL WHERE id=?",
                        (stamp, src["id"]))
            ok += 1
        except (FetchError, ValueError, KeyError) as e:
            con.execute("UPDATE sources SET status='error', last_error=? WHERE id=?", (str(e)[:300], src["id"]))
            errors.append(f"{src['id']}: {e}")
        except Exception as e:  # LLM/network errors must not wipe cached records
            con.execute("UPDATE sources SET status='error', last_error=? WHERE id=?", (str(e)[:300], src["id"]))
            errors.append(f"{src['id']}: {type(e).__name__}: {e}")
        con.commit()
    if weather_refresh:
        try:
            weather_refresh()
        except Exception as e:
            errors.append(f"weather: {e}")
    status = "ok" if ok == attempted and not errors else "partial" if ok else "failed"
    con.execute("""UPDATE refresh_runs SET ended_at=?, status=?, sources_attempted=?, sources_succeeded=?,
                   events_upserted=?, llm_calls=?, errors=? WHERE id=?""",
                (tz_now().isoformat(), status, attempted, ok, upserted, llm.calls - calls_before, json.dumps(errors), run_id))
    con.commit()
    return db.last_run(con)
