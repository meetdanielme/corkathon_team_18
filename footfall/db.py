"""SQLite access. One small module so every owner reads and writes the same contract."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from .domain.timeutil import TZ, now, parse_dt

SCHEMA = Path(__file__).parent / "schema.sql"
SEED = Path(__file__).parent / "seed"


def connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    con.commit()


def seed(con: sqlite3.Connection, seed_dir: Path = SEED) -> None:
    """Load the fictional café, its supplier constraints and the source directory. Idempotent."""
    b = json.loads((seed_dir / "business.json").read_text(encoding="utf-8"))
    con.execute("INSERT OR REPLACE INTO businesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (b["id"], b["name"], b["lat"], b["lon"], b["timezone"], b["opens"], b["closes"],
                 json.dumps(b["open_days"]), b["radius_m"], None, b.get("avg_spend"), b.get("demo_label")))
    for s in json.loads((seed_dir / "suppliers.json").read_text(encoding="utf-8")):
        con.execute("INSERT OR REPLACE INTO supplier_constraints VALUES (?,?,?,?,?,?,?,?,?)",
                    (s["id"], b["id"], s["supplier"], s.get("contact_label"), s["delivery_day"],
                     s.get("delivery_window"), json.dumps(s["cutoff_rule"]), s.get("evidence"),
                     s.get("demo_label")))
    for s in json.loads((seed_dir / "sources.json").read_text(encoding="utf-8")):
        con.execute("""INSERT INTO sources (id, org_name, venue_name, url, type, lat, lon, access_notes,
                       refresh_interval_h, provenance) VALUES (?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(id) DO UPDATE SET org_name=excluded.org_name, venue_name=excluded.venue_name,
                       url=excluded.url, type=excluded.type, lat=excluded.lat, lon=excluded.lon,
                       access_notes=excluded.access_notes, refresh_interval_h=excluded.refresh_interval_h,
                       provenance=excluded.provenance""",
                    (s["id"], s["org_name"], s.get("venue_name"), s["url"], s["type"], s.get("lat"), s.get("lon"),
                     s.get("access_notes"), s.get("refresh_interval_h", 24), s.get("provenance")))
    con.commit()


def get_business(con, business_id: str | None = None) -> dict:
    row = (con.execute("SELECT * FROM businesses WHERE id=?", (business_id,)) if business_id
           else con.execute("SELECT * FROM businesses LIMIT 1")).fetchone()
    b = dict(row)
    b["open_days"] = json.loads(b["open_days"])
    return b


def get_suppliers(con, business_id: str) -> list[dict]:
    rows = con.execute("SELECT * FROM supplier_constraints WHERE business_id=?", (business_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["cutoff_rule"] = json.loads(d["cutoff_rule"])
        out.append(d)
    return out


def get_sources(con) -> list[dict]:
    return [dict(r) for r in con.execute("SELECT * FROM sources ORDER BY id").fetchall()]


def source_is_stale(src: dict, at: datetime) -> bool:
    if src["status"] == "error":
        return True
    last = parse_dt(src["last_success_at"])
    return last is None or at - last > timedelta(hours=src["refresh_interval_h"])


def get_events(con, at: datetime | None = None) -> list[dict]:
    at = at or now()
    sources = {s["id"]: s for s in get_sources(con)}
    events = []
    for r in con.execute("SELECT * FROM events").fetchall():
        e = dict(r)
        ev = [dict(x) for x in con.execute("SELECT * FROM event_evidence WHERE event_id=? ORDER BY retrieved_at",
                                           (e["id"],)).fetchall()]
        e["evidence"] = ev
        if e["data_mode"] == "prepared":
            e["stale"] = False
        else:
            srcs = [sources[x["source_id"]] for x in ev if x["source_id"] in sources]
            e["stale"] = not srcs or all(source_is_stale(s, at) for s in srcs)
        events.append(e)
    return events


def get_weather(con, lat: float, lon: float) -> dict[str, dict]:
    rows = con.execute("SELECT * FROM weather WHERE lat=? AND lon=?", (lat, lon)).fetchall()
    return {r["day"]: dict(r) for r in rows}


# ---------- events: normalisation + dedupe ----------

def normalise(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def norm_key(title: str, start_at: str | None, venue: str | None) -> str:
    start = parse_dt(start_at)
    day = start.astimezone(TZ).date().isoformat() if start else "nodate"
    return f"{normalise(title)}|{day}|{normalise(venue)}"


def upsert_event(con, ev: dict, evidence: dict, at: datetime) -> tuple[str, bool]:
    """Insert or update by norm_key. Returns (event_id, created). Evidence is appended, never replaced."""
    from difflib import SequenceMatcher

    key = norm_key(ev["title"], ev.get("start_at"), ev.get("venue_name"))
    row = con.execute("SELECT id FROM events WHERE norm_key=?", (key,)).fetchone()
    created = row is None
    if created:
        eid = "ev_" + re.sub(r"[^a-z0-9]+", "_", key)[:60]
        dup = None
        title_n, rest = key.split("|", 1)
        for other in con.execute("SELECT id, norm_key FROM events").fetchall():
            o_title, o_rest = other["norm_key"].split("|", 1)
            if o_rest == rest and 0.6 <= SequenceMatcher(None, title_n, o_title).ratio() < 1.0:
                dup = other["id"]
                break
        con.execute("""INSERT INTO events (id,title,norm_key,start_at,end_at,time_precision,venue_name,lat,lon,
                       category,access,status,verification,attendance,possible_duplicate_of,data_mode,
                       first_seen_at,last_seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (eid, ev["title"], key, ev.get("start_at"), ev.get("end_at"), ev.get("time_precision", "datetime"),
                     ev.get("venue_name"), ev.get("lat"), ev.get("lon"), ev.get("category"),
                     ev.get("access", "unknown"), "listed", ev.get("verification", "unverified"),
                     ev.get("attendance"), dup, ev.get("data_mode", "live"), at.isoformat(), at.isoformat()))
    else:
        eid = row["id"]
        con.execute("""UPDATE events SET end_at=COALESCE(?, end_at), lat=COALESCE(?, lat), lon=COALESCE(?, lon),
                       category=COALESCE(?, category), attendance=COALESCE(?, attendance),
                       verification=CASE WHEN ?='verified' THEN 'verified' ELSE verification END,
                       last_seen_at=? WHERE id=?""",
                    (ev.get("end_at"), ev.get("lat"), ev.get("lon"), ev.get("category"), ev.get("attendance"),
                     ev.get("verification"), at.isoformat(), eid))
    con.execute("""INSERT OR IGNORE INTO event_evidence (event_id, source_id, url, retrieved_at, excerpt,
                   extracted_json, uncertainty) VALUES (?,?,?,?,?,?,?)""",
                (eid, evidence.get("source_id"), evidence["url"], evidence["retrieved_at"], evidence.get("excerpt"),
                 json.dumps(evidence.get("extracted") or {}), evidence.get("uncertainty")))
    return eid, created


# ---------- drafts ----------

def create_draft(con, insight_id: str, recipient: str, text: str, source: str) -> int:
    t = now().isoformat()
    cur = con.execute("INSERT INTO drafts (insight_id, recipient_label, text, source, created_at, updated_at) "
                      "VALUES (?,?,?,?,?,?)", (insight_id, recipient, text, source, t, t))
    con.commit()
    return cur.lastrowid


def get_draft(con, draft_id: int) -> dict | None:
    r = con.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
    return dict(r) if r else None


def update_draft(con, draft_id: int, text: str) -> None:
    con.execute("UPDATE drafts SET text=?, updated_at=?, approved_at=NULL WHERE id=?",
                (text, now().isoformat(), draft_id))
    con.commit()


def approve_draft(con, draft_id: int) -> None:
    con.execute("UPDATE drafts SET approved_at=? WHERE id=?", (now().isoformat(), draft_id))
    con.commit()


def last_run(con) -> dict | None:
    r = con.execute("SELECT * FROM refresh_runs ORDER BY id DESC LIMIT 1").fetchone()
    if not r:
        return None
    d = dict(r)
    d["errors"] = json.loads(d["errors"])
    return d
