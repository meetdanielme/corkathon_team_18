from footfall import db, weather

PAYLOAD = {"hourly": {
    "time": ["2026-11-12T07:00", "2026-11-12T09:00", "2026-11-12T15:00", "2026-11-12T17:00"],
    "temperature_2m": [6.0, 9.5, 11.0, 14.0],
    "precipitation_probability": [90, 40, 70, 100],
    "wind_speed_10m": [10.0, 22.0, 18.0, 40.0]}}


def test_summary_only_counts_opening_hours():
    s = weather.summarise(PAYLOAD, "08:00", "16:00")
    assert s == {"2026-11-12": {"temp_max": 11.0, "rain_prob_max": 70, "wind_max": 22.0}}


def test_refresh_stores_provider_and_retrieval_time(con):
    b = db.get_business(con)
    assert weather.refresh(con, b, fetcher=lambda lat, lon: PAYLOAD) == 1
    w = db.get_weather(con, b["lat"], b["lon"])["2026-11-12"]
    assert w["provider"] == "open-meteo" and w["kind"] == "forecast" and w["retrieved_at"]
    weather.refresh(con, b, fetcher=lambda lat, lon: PAYLOAD)  # second run updates, no duplicate
    assert con.execute("SELECT COUNT(*) FROM weather").fetchone()[0] == 1
