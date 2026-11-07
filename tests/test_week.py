from footfall import db
from footfall.domain import insights as insights_mod
from footfall.scout.refresh import run_prepared
from footfall.week import build_week, short_title

from .conftest import NOW


def week_for(con):
    run_prepared(con, at=NOW)
    b = db.get_business(con)
    result = insights_mod.build(b, db.get_events(con, NOW), db.get_suppliers(con, b["id"]), {}, NOW)
    return build_week(b, result, db.get_events(con, NOW), NOW)


def test_week_lays_out_prepared_events(con):
    days = {d["date"]: d for d in week_for(con)["days"]}
    assert len(days) == 7 and not days["2026-11-08"]["open"]  # Sunday closed
    wed, thu, fri = days["2026-11-11"], days["2026-11-12"], days["2026-11-13"]
    concert = next(b for b in wed["bars"] if b["title"] == "Evening concert")
    assert concert["kind"] == "excluded" and concert["left"] > wed["hours"][-1]["left"] + wed["hours"][-1]["width"]
    assert [(c["time"], c["for_day"]) for c in wed["cutoffs"]] == [("16:00", "Thu 12 Nov")]
    assert any(b["kind"] == "insight" and b["label"] == "10:00–14:00" for b in thu["bars"])
    assert fri["lanes"] == 2  # road closure and street market overlap


def test_short_title_drops_demo_suffix():
    assert short_title("Street market (fictional demo)") == "Street market"
    assert short_title("Graduation") == "Graduation"


def test_split_day_gives_one_band_per_range(con):
    run_prepared(con, at=NOW)
    b = db.get_business(con)
    b["hours"] = {**b["hours"], "mon": [["08:00", "12:00"], ["13:00", "16:00"]]}
    result = insights_mod.build(b, db.get_events(con, NOW), db.get_suppliers(con, b["id"]), {}, NOW)
    mon = next(d for d in build_week(b, result, db.get_events(con, NOW), NOW)["days"] if d["date"] == "2026-11-09")
    assert [h["label"] for h in mon["hours"]] == ["08:00–12:00", "13:00–16:00"]
