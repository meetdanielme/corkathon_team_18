from datetime import timedelta

from footfall import db
from footfall.domain import insights as ins
from footfall.domain.timeutil import parse_dt
from footfall.scout.refresh import run_prepared

from .conftest import NOW


def build(con, at=NOW):
    b = db.get_business(con)
    return ins.build(b, db.get_events(con, at), db.get_suppliers(con, b["id"]), {}, at)


def by_title(items, word):
    return next(x for x in items if word in x.title)


def test_prepared_scenario_classifies_every_event(con):
    run_prepared(con, at=NOW)
    r = build(con)
    assert {i.title.split(" (")[0] for i in r["insights"]} == {"Graduation ceremony", "Street market",
                                                              "Road closure for filming"}
    reasons = {e.title.split(" (")[0]: e.reason for e in r["excluded"]}
    assert "does not overlap opening hours" in reasons["Evening concert"]
    assert "outside the 1000 m radius" in reasons["Suburban festival"]
    assert "restricted" in reasons["Private function"]
    assert r["review"][0].missing == ["start time", "location"]


def test_graduation_window_impact_and_deadline(con):
    run_prepared(con, at=NOW)
    g = by_title(build(con)["insights"], "Graduation")
    assert g.window_label == "Thu 12 Nov 10:00-14:00"
    assert g.impact == "medium" and g.impact_points == {"distance": 1, "overlap": 2, "attendance": 0, "total": 3}
    assert g.confidence == "medium" and any("live source" in r for r in g.confidence_reasons)
    assert g.action_deadline["supplier"] == "Bakery"
    assert g.action_deadline["cutoff"] == "2026-11-11T16:00:00+00:00"
    assert g.action_deadline["status"] == "upcoming"
    assert "your call" in g.suggested_action


def test_market_high_impact_assumed_window_and_conflict(con):
    run_prepared(con, at=NOW)
    r = build(con)
    m = by_title(r["insights"], "market")
    assert m.impact == "high" and "end time not published" in m.window_basis
    assert any("End time not published" in x for x in m.confidence_reasons)
    assert m.conflicts and "Road closure" in m.conflicts[0]
    closure = by_title(r["insights"], "closure")
    assert closure.direction == "decrease" and closure.conflicts


def test_deadline_boundaries(con):
    run_prepared(con, at=NOW)
    cutoff = parse_dt("2026-11-11T16:00:00+00:00")
    at_cutoff = by_title(build(con, cutoff)["insights"], "Graduation")
    assert at_cutoff.action_deadline["supplier"] == "Bakery"
    assert all(d["status"] == "missed" for d in at_cutoff.deadlines if d["cutoff"] == cutoff.isoformat())
    just_before = by_title(build(con, cutoff - timedelta(minutes=1))["insights"], "Graduation")
    assert just_before.action_deadline["status"] == "urgent"


def test_window_touching_opening_time_is_excluded():
    b = {"id": "b", "lat": 51.9, "lon": -8.48, "radius_m": 1000, "opens": "08:00", "closes": "16:00",
         "open_days": ["mon", "tue", "wed", "thu", "fri", "sat"]}
    ev = {"id": "e", "title": "Early thing", "start_at": "2026-11-12T05:00:00+00:00",
          "end_at": "2026-11-12T07:00:00+00:00", "lat": 51.9, "lon": -8.48, "access": "public",
          "evidence": [{"url": "u", "retrieved_at": NOW.isoformat(), "excerpt": "x"}]}
    r = ins.evaluate(b, ev, [], {}, NOW)
    assert isinstance(r, ins.Exclusion) and "does not overlap" in r.reason


def test_rain_is_context_only(con):
    run_prepared(con, at=NOW)
    b = db.get_business(con)
    r = ins.build(b, db.get_events(con, NOW), db.get_suppliers(con, b["id"]),
                  {"2026-11-12": {"rain_prob_max": 80}}, NOW)
    g = by_title(r["insights"], "Graduation")
    assert any("Context only" in x for x in g.reasons) and g.impact == "medium"
