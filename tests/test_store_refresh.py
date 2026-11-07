import json

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


def _prepared_count() -> int:
    """How many events the prepared seed file holds."""
    return len(json.loads(rf.PREPARED.read_text(encoding="utf-8")))


def test_repeat_prepared_refresh_creates_no_duplicates(con):
    rf.run_prepared(con, at=NOW)
    n1 = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    e1 = con.execute("SELECT COUNT(*) FROM event_evidence").fetchone()[0]
    rf.run_prepared(con, at=NOW)
    # Count comes from the seed file, so adding a demo event does not break this test.
    assert con.execute("SELECT COUNT(*) FROM events").fetchone()[0] == n1 == _prepared_count()
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


def _clean_finding():
    """One valid finding, no invented second event, so a run has no expected errors."""
    return {"events": [FINDING], "uncertainties": []}


def test_repeat_live_refresh_creates_no_duplicate_events_or_evidence(con):
    """Gate M2: a repeat refresh updates records without visible duplicates."""
    first = rf.run_live(con, FakeLLM([_clean_finding()]), at=NOW, fetcher=fetcher_ok)
    events_1 = con.execute("SELECT COUNT(*) FROM events WHERE data_mode='live'").fetchone()[0]
    evidence_1 = con.execute("SELECT COUNT(*) FROM event_evidence").fetchone()[0]
    assert first["events_upserted"] >= 1 and events_1 == 1

    second = rf.run_live(con, FakeLLM([_clean_finding()]), at=NOW, fetcher=fetcher_ok)

    events_2 = con.execute("SELECT COUNT(*) FROM events WHERE data_mode='live'").fetchone()[0]
    evidence_2 = con.execute("SELECT COUNT(*) FROM event_evidence").fetchone()[0]
    assert events_2 == events_1, "the same event was inserted twice instead of being matched on norm_key"
    # Evidence is append-only but unique per (event, url, excerpt), so an identical re-read adds nothing.
    assert evidence_2 == evidence_1, "identical evidence was appended twice"
    assert second["status"] == first["status"]


def test_live_event_carries_url_and_retrieval_time(con):
    """Gate M2: a refresh persists events with provenance and freshness."""
    rf.run_live(con, FakeLLM([_clean_finding()]), at=NOW, fetcher=fetcher_ok)

    row = con.execute("""SELECT v.url, v.retrieved_at, v.excerpt, e.first_seen_at, e.last_seen_at
                         FROM event_evidence v JOIN events e ON e.id = v.event_id
                         WHERE e.data_mode='live'""").fetchone()
    assert row is not None, "a live event was stored with no evidence row"
    assert row["url"].startswith("http") and row["retrieved_at"]
    assert row["excerpt"] in PAGE, "the stored excerpt is not verbatim from the fetched page"
    assert row["first_seen_at"] and row["last_seen_at"]


def test_live_and_prepared_events_stay_distinguishable(con):
    """Gate M2: live, cached and prepared data can be told apart."""
    rf.run_prepared(con, at=NOW)
    rf.run_live(con, FakeLLM([_clean_finding()]), at=NOW, fetcher=fetcher_ok)

    modes = dict(con.execute("SELECT data_mode, COUNT(*) FROM events GROUP BY data_mode").fetchall())
    assert modes.get("prepared", 0) >= 1 and modes.get("live", 0) == 1
    # A live run must not relabel or drop the prepared demo rows.
    assert sorted(modes) == ["live", "prepared"]


def test_call_limit_is_per_refresh_on_a_reused_worker(con):
    llm = FakeLLM([{'events': [], 'uncertainties': []}] * 2)
    for _ in range(2):
        run = rf.run_live(con, llm, at=NOW, fetcher=lambda url: (url, PAGE),
                          limits={'max_sources': 1, 'max_llm_calls': 1})
        assert run['sources_succeeded'] == 1
        assert run['llm_calls'] == 1
    assert llm.calls == 2


def test_outside_window_is_successful_source_check_not_warning(con):
    old = {**FINDING, 'start_at': '2026-10-01T19:30:00+00:00'}
    count = len(db.get_sources(con))
    model = FakeLLM([{'events': [old], 'uncertainties': []}] * count)
    run = rf.run_live(con, model, at=NOW, fetcher=lambda url: (url, PAGE))
    assert run['status'] == 'ok'
    assert run['sources_succeeded'] == count
    assert run['events_upserted'] == 0
    assert run['errors'] == []
    assert all(s['status'] == 'ok' and s['last_success_at'] for s in db.get_sources(con))


def test_long_event_ids_include_date_and_venue_without_prefix_collisions(con):
    title = 'Creative Workshop Write and Paint Your Own Calaverita ' * 2
    evidence = {'url': 'https://example.org/event', 'retrieved_at': NOW.isoformat(), 'excerpt': title}
    first = {'title': title, 'start_at': '2026-11-10T15:00:00+00:00', 'venue_name': "St Peter's Cork"}
    second = {**first, 'start_at': '2026-11-11T15:00:00+00:00'}
    a, made_a = db.upsert_event(con, first, evidence, NOW)
    b, made_b = db.upsert_event(con, second, evidence, NOW)
    assert made_a and made_b and a != b
    assert db.upsert_event(con, first, evidence, NOW) == (a, False)
    assert db.upsert_event(con, second, evidence, NOW) == (b, False)
    assert con.execute('SELECT count(*) FROM events').fetchone()[0] == 2


def test_existing_legacy_event_id_is_preserved_on_refresh(con):
    legacy = 'ev_legacy_truncated_id'
    key = db.norm_key(FINDING['title'], FINDING['start_at'], FINDING['venue_name'])
    con.execute('''INSERT INTO events (id,title,norm_key,start_at,venue_name,first_seen_at,last_seen_at)
                   VALUES (?,?,?,?,?,?,?)''',
                (legacy,FINDING['title'],key,FINDING['start_at'],FINDING['venue_name'],NOW.isoformat(),NOW.isoformat()))
    evidence = {'url': 'https://example.org/event', 'retrieved_at': NOW.isoformat(), 'excerpt': PAGE}
    assert db.upsert_event(con,FINDING,evidence,NOW) == (legacy,False)
