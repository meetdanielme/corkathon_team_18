import pytest

from footfall import db
from footfall.scout import refresh as rf
from footfall.scout.fetch import FetchError, check_public
from footfall.scout.validate import validate_finding

from .conftest import NOW, FakeLLM

PAGE = "What's on. Recomposed By Max Richter: Vivaldi: The Four Seasons Thu 12 Nov 2026 19:30 at St Peter's Cork."
FINDING = {"title": "Recomposed By Max Richter: Vivaldi: The Four Seasons", "start_at": "2026-11-12T19:30:00+00:00",
           "end_at": None, "venue_name": "St Peter's Cork", "category": "music", "access": "public", "attendance": None,
           "excerpt": "Recomposed By Max Richter: Vivaldi: The Four Seasons Thu 12 Nov 2026 19:30 at St Peter's Cork."}
FAKE = {"events": [FINDING, {**FINDING, "title": "Invented", "excerpt": "not on the page"}], "uncertainties": []}


def fetcher_ok(url):
    if "stpeterscork" in url:
        return url, PAGE
    raise FetchError("simulated outage")


def test_repeat_prepared_refresh_creates_no_duplicates(con):
    rf.run_prepared(con, at=NOW)
    n1 = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    e1 = con.execute("SELECT COUNT(*) FROM event_evidence").fetchone()[0]
    rf.run_prepared(con, at=NOW)
    assert con.execute("SELECT COUNT(*) FROM events").fetchone()[0] == n1 == 7
    assert con.execute("SELECT COUNT(*) FROM event_evidence").fetchone()[0] == e1


def test_live_refresh_validates_persists_and_records_failure(con):
    llm = FakeLLM([FAKE])
    source_count = len(db.get_sources(con))
    run = rf.run_live(con, llm, at=NOW, fetcher=fetcher_ok)
    assert run["status"] == "partial" and run["sources_attempted"] == source_count and run["sources_succeeded"] == 1
    assert any("excerpt not found" in e for e in run["errors"])
    assert any("simulated outage" in e for e in run["errors"])
    evs = db.get_events(con, NOW)
    assert [e["title"] for e in evs] == ["Recomposed By Max Richter: Vivaldi: The Four Seasons"]
    assert evs[0]["lat"] == 51.8995487  # Venue point from the refreshed St Peter's source record.
    assert evs[0]["verification"] == "verified" and evs[0]["stale"] is False


def test_failed_source_keeps_cached_events_and_marks_stale(con):
    rf.run_live(con, FakeLLM([FAKE]), at=NOW, fetcher=fetcher_ok)
    def all_down(url):
        raise FetchError("down")
    run = rf.run_live(con, FakeLLM([]), at=NOW, fetcher=all_down)
    assert run["status"] == "failed"
    evs = db.get_events(con, NOW)
    assert len(evs) == 1 and evs[0]["stale"] is True


def test_overlapping_runs_are_blocked(con):
    con.execute("INSERT INTO refresh_runs (started_at, mode, status) VALUES (?, 'live', 'running')",
                (NOW.isoformat(),))
    with pytest.raises(rf.RefreshBusy):
        rf.run_prepared(con, at=NOW)


def test_similar_title_same_day_venue_is_flagged_not_merged(con):
    ev = {"title": "Christmas market", "start_at": "2026-11-13T10:00:00+00:00", "venue_name": "Grand Parade"}
    evid = {"url": "https://a.example", "retrieved_at": NOW.isoformat(), "excerpt": "x"}
    first, _ = db.upsert_event(con, ev, evid, NOW)
    second, created = db.upsert_event(con, {**ev, "title": "Christmas markets"}, evid, NOW)
    assert created and second != first
    row = con.execute("SELECT possible_duplicate_of FROM events WHERE id=?", (second,)).fetchone()
    assert row[0] == first


def test_validate_rejects_out_of_window_and_unverbatim():
    from datetime import timedelta
    ok, _ = validate_finding(FINDING, PAGE, NOW, NOW + timedelta(days=7))
    assert ok and ok["start_at"].startswith("2026-11-12")
    bad, why = validate_finding({**FINDING, "start_at": "2027-01-01T10:00:00"}, PAGE, NOW, NOW + timedelta(days=7))
    assert bad is None and "outside" in why


@pytest.mark.parametrize("url", ["http://127.0.0.1/", "http://localhost/", "file:///etc/passwd",
                                 "http://169.254.169.254/latest"])
def test_fetch_blocks_non_public(url):
    with pytest.raises(FetchError):
        check_public(url)
