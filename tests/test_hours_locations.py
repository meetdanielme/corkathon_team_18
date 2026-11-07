from footfall import db
from footfall.domain import hours as hours_mod
from footfall.domain import insights as insights_mod
from footfall.scout.refresh import run_prepared

from .conftest import NOW


def build(con, **changes):
    run_prepared(con, at=NOW)
    b = {**db.get_business(con), **changes}
    return insights_mod.build(b, db.get_events(con, NOW), db.get_suppliers(con, b["id"]), {}, NOW)


def find(items, title):
    return next(x for x in items if x.title == title)


def test_holiday_closure_filters_the_event(con):
    r = build(con, special_hours=[{"date": "2026-11-12", "label": "Staff training", "ranges": []}])
    assert find(r["excluded"], "Graduation ceremony").reason == "Café is closed for Staff training"


def test_split_day_sums_overlap_across_ranges(con):
    week = hours_mod.weekly(db.get_business(con))
    g = find(build(con, hours={**week, "thu": [["08:00", "11:00"], ["13:00", "16:00"]]})["insights"], "Graduation ceremony")
    assert g.overlap_min == 60 + 60  # window 10:00-14:00 meets 10:00-11:00 and 13:00-14:00


def test_special_hours_replace_weekly_hours(con):
    r = build(con, special_hours=[{"date": "2026-11-12", "label": "Half day", "ranges": [["15:00", "18:00"]]}])
    assert "does not overlap opening hours 15:00-18:00" in find(r["excluded"], "Graduation ceremony").reason


def test_nearest_location_sets_distance_and_reason(con):
    b = db.get_business(con)
    campus = {"name": "Campus kiosk", "address": "College Road, Cork", "lat": 51.8936, "lon": -8.4915}
    g = find(build(con, locations=[*b["locations"], campus])["insights"], "Graduation ceremony")
    assert g.distance_m < 50 and g.location["name"] == "Campus kiosk"
    assert g.reasons[0].startswith(f"{g.distance_m} m from Campus kiosk")


def test_summary_groups_days():
    b = {"hours": {"mon": [["08:00", "16:00"]], "tue": [["08:00", "16:00"]], "wed": [], "thu": [], "fri": [],
                   "sat": [["09:00", "12:00"], ["13:00", "15:00"]], "sun": []}}
    assert hours_mod.summary(b) == [("Mon–Tue", "08:00–16:00"), ("Wed–Fri", "Closed"),
                                    ("Sat", "09:00–12:00, 13:00–15:00"), ("Sun", "Closed")]
