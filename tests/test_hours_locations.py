from footfall import db
from footfall.domain import hours as hours_mod
from footfall.domain import insights as insights_mod
from footfall.scout.refresh import run_prepared

from .conftest import NOW


def build(con, **changes):
    """Apply schedule changes to every location (hours now live on locations)."""
    run_prepared(con, at=NOW)
    b = db.get_business(con)
    b["locations"] = [{**loc, **changes} for loc in b["locations"]]
    return insights_mod.build(b, db.get_events(con, NOW), db.get_suppliers(con, b["id"]), {}, NOW)


def find(items, title):
    return next(x for x in items if x.title == title)


def test_holiday_closure_filters_the_event(con):
    r = build(con, special_hours=[{"date": "2026-11-12", "label": "Staff training", "ranges": []}])
    assert find(r["excluded"], "Graduation ceremony").reason == "You're closed for Staff training"


def test_split_day_sums_overlap_across_ranges(con):
    week = hours_mod.weekly(db.get_business(con))
    g = find(build(con, hours={**week, "thu": [["08:00", "11:00"], ["13:00", "16:00"]]})["insights"], "Graduation ceremony")
    assert g.overlap_min == 60 + 60  # window 10:00-14:00 meets 10:00-11:00 and 13:00-14:00


def test_special_hours_replace_weekly_hours(con):
    r = build(con, special_hours=[{"date": "2026-11-12", "label": "Half day", "ranges": [["15:00", "18:00"]]}])
    assert "before you open (you're open 15:00–18:00)" in find(r["excluded"], "Graduation ceremony").reason


def test_nearest_location_sets_distance_and_reason(con):
    run_prepared(con, at=NOW)
    b = db.get_business(con)
    campus = {**b["locations"][0], "name": "Campus kiosk", "address": "College Road, Cork", "lat": 51.8936, "lon": -8.4915}
    b["locations"] = [*b["locations"], campus]
    r = insights_mod.build(b, db.get_events(con, NOW), db.get_suppliers(con, b["id"]), {}, NOW)
    g = find(r["insights"], "Graduation ceremony")
    assert g.distance_m < 50 and g.location["name"] == "Campus kiosk"
    assert g.reasons[0].startswith(f"It's {g.distance_m} m from Campus kiosk")


def test_summary_groups_days():
    b = {"hours": {"mon": [["08:00", "16:00"]], "tue": [["08:00", "16:00"]], "wed": [], "thu": [], "fri": [],
                   "sat": [["09:00", "12:00"], ["13:00", "15:00"]], "sun": []}}
    assert hours_mod.summary(b) == [("Mon–Tue", "08:00–16:00"), ("Wed–Fri", "Closed"),
                                    ("Sat", "09:00–12:00, 13:00–15:00"), ("Sun", "Closed")]


def test_nearest_location_uses_its_own_hours(con):
    run_prepared(con, at=NOW)
    b = db.get_business(con)
    week = hours_mod.weekly(b["locations"][0])
    campus = {"name": "Campus kiosk", "address": "College Road, Cork", "lat": 51.8936, "lon": -8.4915,
              "hours": {**week, "thu": []}, "special_hours": []}
    b["locations"] = [*b["locations"], campus]
    r = insights_mod.build(b, db.get_events(con, NOW), db.get_suppliers(con, b["id"]), {}, NOW)
    assert find(r["excluded"], "Graduation ceremony").reason == "You're closed at Campus kiosk on Thu 12 Nov"


def test_timeline_shows_when_any_location_is_open(con):
    from footfall.week import build_week
    run_prepared(con, at=NOW)
    b = db.get_business(con)
    week = hours_mod.weekly(b["locations"][0])
    b["locations"] = [{**b["locations"][0], "hours": {**week, "mon": [["08:00", "12:00"]]}},
                      {**b["locations"][0], "address": "Quay", "hours": {**week, "mon": [["11:00", "18:00"]]}}]
    r = insights_mod.build(b, db.get_events(con, NOW), db.get_suppliers(con, b["id"]), {}, NOW)
    mon = next(d for d in build_week(b, r, db.get_events(con, NOW), NOW)["days"] if d["date"] == "2026-11-09")
    assert [h["label"] for h in mon["hours"]] == ["08:00–18:00"]


def test_locations_without_own_hours_fall_back_to_the_business(con):
    con.execute("UPDATE locations SET hours=NULL, special_hours=NULL")
    b = db.get_business(con)
    assert b["locations"][0]["hours"]["mon"] == [["08:00", "16:00"]]
    assert [x["label"] for x in b["locations"][0]["special_hours"]] == ["Christmas Day", "St Stephen's Day"]
