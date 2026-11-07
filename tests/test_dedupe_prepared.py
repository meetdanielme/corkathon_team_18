"""The cleanup for pre-#31 duplicate prepared rows."""
import runpy
import sys

import pytest

from footfall import db
from footfall.domain.timeutil import now
from footfall.scout.refresh import run_prepared

STALE_TITLE = "Graduation ceremony (fictional demo)"


def _add_stale_row(con):
    at = now()
    db.upsert_event(con, {"title": STALE_TITLE, "start_at": "2026-11-12T11:00:00+00:00", "end_at": None,
                          "venue_name": "University campus hall", "lat": 51.8935, "lon": -8.4919,
                          "category": "other", "access": "public", "attendance": None,
                          "data_mode": "prepared", "verification": "prepared"},
                    {"url": "https://example.org/old", "retrieved_at": at.isoformat(),
                     "excerpt": "old row", "source_id": None, "uncertainty": "Prepared demo data"}, at)
    con.commit()


def _run(monkeypatch, path, *args):
    monkeypatch.setenv("FOOTFALL_DB", str(path))
    monkeypatch.setattr(sys, "argv", ["dedupe_prepared", *args])
    with pytest.raises(SystemExit) as e:
        runpy.run_module("scripts.dedupe_prepared", run_name="__main__")
    return e.value.code


def test_dry_run_reports_but_deletes_nothing(tmp_path, monkeypatch, capsys):
    path = tmp_path / "d.sqlite3"
    con = db.connect(str(path)); db.init(con); db.seed(con); run_prepared(con); _add_stale_row(con)
    before = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    con.close()

    assert _run(monkeypatch, path) == 0
    assert "dry run" in capsys.readouterr().out

    con = db.connect(str(path))
    assert con.execute("SELECT COUNT(*) FROM events").fetchone()[0] == before


def test_apply_removes_stale_rows_and_leaves_no_orphan_evidence(tmp_path, monkeypatch):
    path = tmp_path / "d.sqlite3"
    con = db.connect(str(path)); db.init(con); db.seed(con); run_prepared(con); _add_stale_row(con)
    before = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    con.close()

    assert _run(monkeypatch, path, "--apply") == 0

    con = db.connect(str(path))
    assert con.execute("SELECT COUNT(*) FROM events").fetchone()[0] == before - 1
    assert not con.execute("SELECT 1 FROM events WHERE id LIKE '%fictional_demo%'").fetchone()
    orphans = con.execute("""SELECT COUNT(*) FROM event_evidence v
                             LEFT JOIN events e ON e.id = v.event_id WHERE e.id IS NULL""").fetchone()[0]
    assert orphans == 0
    # The current seed survives untouched.
    assert con.execute("SELECT 1 FROM events WHERE title='Graduation ceremony'").fetchone()


def test_refuses_to_touch_anything_that_is_not_prepared(tmp_path, monkeypatch, capsys):
    path = tmp_path / "d.sqlite3"
    con = db.connect(str(path)); db.init(con); db.seed(con)
    at = now()
    db.upsert_event(con, {"title": "Live thing (fictional demo)", "start_at": "2026-11-12T11:00:00+00:00",
                          "end_at": None, "venue_name": "Somewhere", "lat": 51.89, "lon": -8.48,
                          "category": "other", "access": "public", "attendance": None,
                          "data_mode": "live", "verification": "verified"},
                    {"url": "https://example.org/live", "retrieved_at": at.isoformat(),
                     "excerpt": "x", "source_id": None, "uncertainty": None}, at)
    con.commit(); con.close()

    assert _run(monkeypatch, path, "--apply") == 1
    assert "Refusing to run" in capsys.readouterr().out
    con = db.connect(str(path))
    assert con.execute("SELECT 1 FROM events WHERE data_mode='live'").fetchone()
