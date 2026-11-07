from footfall import db
from footfall.domain.insights import confidence_for
from tests.conftest import NOW


def listing(**kwargs):
    return dict(title="Workshop", start_at="2026-11-10T11:00:00+00:00",
                venue_name=kwargs.pop("venue_name", "Hall"), **kwargs)


def save(con, event, url="https://venue.example/events"):
    return db.upsert_event(con, event, dict(url=url, retrieved_at=NOW.isoformat(), excerpt="Workshop"), NOW)


def test_missing_venue_refresh_preserves_id_and_evidence(con):
    eid, _ = save(con, listing(lat=51.9, lon=-8.4))
    again, created = save(con, listing(venue_name=None))
    assert (again, created) == (eid, False)
    row = dict(con.execute("SELECT * FROM events WHERE id=?", (eid,)).fetchone())
    assert row["venue_name"] == "Hall" and row["lat"] == 51.9


def test_location_enrichment_matches_again_afterwards(con):
    eid, _ = save(con, listing(venue_name=None))
    assert save(con, listing(lat=51.9, lon=-8.4)) == (eid, False)
    assert save(con, listing()) == (eid, False)
    assert con.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1


def test_conflicting_venues_times_modes_and_sources_stay_separate(con):
    first, _ = save(con, listing())
    different_time = listing(); different_time["start_at"] = "2026-11-10T15:00:00+00:00"
    others = [save(con, listing(venue_name="Other Hall")), save(con, different_time),
              save(con, listing(data_mode="prepared")),
              save(con, listing(venue_name=None), "https://other.example/events")]
    assert all(created and eid != first for eid, created in others)
    assert save(con, different_time) == (others[1][0], False)


def test_ambiguous_missing_venue_is_not_auto_merged(con):
    save(con, listing())
    save(con, listing(venue_name="Other Hall"))
    _, created = save(con, listing(venue_name=None))
    assert created
    events = db.get_events(con, NOW)
    missing = next(e for e in events if e["venue_name"] is None)
    assert missing["possible_duplicate_of"]
    assert any("another listing" in reason for reason in confidence_for(missing)[1])
