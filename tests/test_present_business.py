from datetime import timedelta

from footfall import db
from footfall.app import create_app
from footfall.present import ago, countdown, dist, revenue_estimate

from .conftest import NOW, FakeLLM, sign_in

DEADLINE = {"supplier": "Bakery", "cutoff_label": "Wed 11 Nov 16:00", "delivery_day": "Thu 12 Nov"}


def at(hours):
    return {**DEADLINE, "cutoff": (NOW + timedelta(hours=hours)).isoformat()}


def test_countdown_colours_by_time_left_and_approval():
    assert countdown(at(100), NOW)["level"] == "later"
    assert countdown(at(48), NOW)["level"] == "soon"
    assert countdown(at(5), NOW) == {**countdown(at(5), NOW), "level": "now", "label": "Order due in 5 hours"}
    assert countdown(at(-1), NOW)["level"] == "missed"
    assert countdown(at(100), NOW, {"approved_at": None})["label"].endswith("message not approved yet")
    assert countdown(at(5), NOW, {"approved_at": "2026-11-07T21:00:00+00:00"})["level"] == "done"
    assert countdown(None, NOW)["level"] == "none"


def test_relative_time_and_distance():
    assert ago(NOW - timedelta(minutes=12), NOW) == "12 min ago"
    assert ago(NOW - timedelta(seconds=5), NOW) == "just now"
    assert ago(None, NOW) == "never"
    assert dist(941) == "941 m" and dist(1000) == "1 km" and dist(7566) == "7.6 km"


class FakeGeocoder:
    def __init__(self, results=None, down=False):
        self.results, self.down, self.calls = results or {}, down, []

    def __call__(self, address):
        self.calls.append(address)
        if self.down:
            from footfall.geocode import GeocodeUnavailable
            raise GeocodeUnavailable("offline")
        return self.results.get(address)


def app_client(tmp_path, geocoder=None):
    app = create_app(db_path=str(tmp_path / "b.sqlite3"), clock=lambda: NOW, llm=FakeLLM(enabled=False),
                     geocoder=geocoder or FakeGeocoder())
    return app, sign_in(app.test_client())


def week(key, days=("mon", "tue", "wed", "thu", "fri"), start="08:00", end="16:00"):
    return {f"{key}_{d}_{k}": v for d in days for k, v in (("start", start), ("end", end))}


VALID = {"name": "Bríd's Kitchen", "radius_m": "800", "avg_spend": "7,50", "customers_per_hour": "15",
         "uplift_low": "4", "uplift_medium": "12", "uplift_high": "25", "loc_key": ["l0", "n1"],
         "l0_name": "Washington St", "l0_address": "Washington Street, Cork", **week("l0"),
         "l0_sat_start": ["09:00", "13:00"], "l0_sat_end": ["12:00", "15:00"],
         "l0_special_date": ["2026-12-24"], "l0_special_label": ["Christmas Eve"], "l0_special_mode": ["hours"],
         "l0_special_start": ["09:00"], "l0_special_end": ["13:00"],
         "n1_name": "Quay", "n1_address": "Lavitt's Quay, Cork", **week("n1", ("sat", "sun"), "10:00", "18:00")}


def test_business_page_saves_each_locations_own_hours(tmp_path):
    geo = FakeGeocoder({"Lavitt's Quay, Cork": (51.9006, -8.4718)})
    app, c = app_client(tmp_path, geo)
    assert c.get("/business").status_code == 200
    r = c.post("/business", data=VALID)
    assert r.status_code == 302, r.get_data(as_text=True)
    assert geo.calls == ["Lavitt's Quay, Cork"]  # the unchanged seeded address is not looked up again
    with db.connect(app.config["DB_PATH"]) as con:
        b = db.get_business(con)
    main, quay = b["locations"]
    assert (main["name"], quay["name"], quay["address"]) == ("Washington St", "Quay", "Lavitt's Quay, Cork")
    assert main["hours"]["sat"] == [["09:00", "12:00"], ["13:00", "15:00"]] and main["hours"]["sun"] == []
    assert quay["hours"]["mon"] == [] and quay["hours"]["sun"] == [["10:00", "18:00"]]
    assert main["special_hours"] == [{"date": "2026-12-24", "label": "Christmas Eve", "ranges": [["09:00", "13:00"]]}]
    assert quay["special_hours"] == []
    assert (b["address"], b["lat"], b["hours"]) == ("Washington Street, Cork", 51.8977, main["hours"])  # main mirrored
    assert (b["opens"], b["closes"], b["open_days"]) == ("08:00", "16:00", ["mon", "tue", "wed", "thu", "fri", "sat"])
    assert (b["radius_m"], b["avg_spend"]) == (800, 7.5)
    assert b["sales_baseline"] == {"customers_per_hour": 15, "uplift_pct": {"low": 4, "medium": 12, "high": 25}}
    home = c.get("/app").get_data(as_text=True)
    assert "Lavitt&#39;s Quay, Cork" in home and "Sat–Sun</b> 10:00–18:00" in home


def test_business_page_rejects_bad_input_inline(tmp_path):
    app, c = app_client(tmp_path, FakeGeocoder())
    bad = {**VALID, "radius_m": "50", "uplift_high": "150", "l0_mon_start": ["08:00", "11:00"],
           "l0_mon_end": ["12:00", "14:00"], "l0_special_date": [""], "l0_special_label": ["Bank holiday"]}
    r = c.post("/business", data=bad)
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert "These opening times overlap." in html and "between 100 and 5000" in html
    assert "Enter a percentage from 0 to 100." in html and "Choose a date for this special day." in html
    assert "Couldn&#39;t find this address." in html  # the new Quay address is unknown to the fake geocoder
    with db.connect(app.config["DB_PATH"]) as con:
        assert db.get_business(con)["radius_m"] == 1000  # nothing saved


def test_business_page_reports_lookup_outage(tmp_path):
    _app, c = app_client(tmp_path, FakeGeocoder(down=True))
    html = c.post("/business", data=VALID).get_data(as_text=True)
    assert "look up this address right now" in html


def test_init_adds_address_column_to_old_databases(tmp_path):
    path = str(tmp_path / "old.sqlite3")
    with db.connect(path) as con:
        con.execute("CREATE TABLE businesses (id TEXT PRIMARY KEY, name TEXT NOT NULL, lat REAL NOT NULL, "
                    "lon REAL NOT NULL, timezone TEXT NOT NULL DEFAULT 'Europe/Dublin', opens TEXT NOT NULL, "
                    "closes TEXT NOT NULL, open_days TEXT NOT NULL, radius_m INTEGER NOT NULL, sales_baseline TEXT, "
                    "avg_spend REAL, demo_label TEXT)")
        db.init(con)
        assert "address" in {r["name"] for r in con.execute("PRAGMA table_info(businesses)")}


def test_home_shows_approved_message_as_done(tmp_path):
    _app, c = app_client(tmp_path)
    c.post("/refresh", data={"mode": "prepared"})
    iid = next(i["id"] for i in c.get("/api/insights").get_json()["insights"] if i["title"] == "Graduation ceremony")
    did = int(c.post(f"/insights/{iid}/draft").headers["Location"].rstrip("/").split("/")[-1])
    assert "Message ready to send" not in c.get("/app").get_data(as_text=True)
    c.post(f"/drafts/{did}/approve")
    assert "Message ready to send" in c.get("/app").get_data(as_text=True)


def test_revenue_estimate_applies_owner_assumptions():
    b = {"sales_baseline": {"customers_per_hour": 12, "uplift_pct": {"medium": 10}}, "avg_spend": 7.5}
    r = revenue_estimate("medium", "increase", 240, b)
    assert (r["pct"], r["usual"], r["extra"], r["revenue"]) == (10, 48, 5, 36)
    assert revenue_estimate("high", "decrease", 60, b)["pct"] == -20  # default for an unset level
    bare = revenue_estimate("low", "increase", 120, {"sales_baseline": None, "avg_spend": None})
    assert bare["pct"] == 5 and bare["extra"] is None and bare["revenue"] is None


def test_insight_shows_revenue_metric(tmp_path):
    _app, c = app_client(tmp_path)
    c.post("/refresh", data={"mode": "prepared"})
    iid = next(i["id"] for i in c.get("/api/insights").get_json()["insights"] if i["title"] == "Graduation ceremony")
    html = c.get(f"/insights/{iid}").get_data(as_text=True)
    assert "+10%" in html and "≈ +€36" in html and "A rough guide, not a prediction." in html
