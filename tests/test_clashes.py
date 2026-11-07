"""Delivery-blocked clash rules: a nearby road closure that overlaps a supplier's drop window."""
from datetime import datetime

import pytest

from footfall.domain import clashes as cl
from footfall.domain.timeutil import TZ

NOW = datetime(2026, 11, 7, 22, 0, tzinfo=TZ)   # Saturday night, same clock as the other suites
BUSINESS = {"id": "brids-kitchen", "lat": 51.8977, "lon": -8.4800}

# Friday 13 Nov, 08:00-12:00, 41 m from the café: the prepared demo closure.
CLOSURE = {"id": "ev_closure", "title": "Road closure for filming", "category": "road_closure",
           "start_at": "2026-11-13T08:00:00+00:00", "end_at": "2026-11-13T12:00:00+00:00",
           "lat": 51.8979, "lon": -8.4805, "data_mode": "prepared",
           "evidence": [{"url": "https://example.org/closure", "excerpt": "Washington Street closed"}]}

DAIRY_FRI = {"id": "dairy-fri", "supplier": "Dairy", "contact_label": None,
             "delivery_day": "fri", "delivery_window": "08:30-09:00"}
BAKERY_FRI = {"id": "bakery-fri", "supplier": "Bakery", "contact_label": "Declan (bakery)",
              "delivery_day": "fri", "delivery_window": "07:30-08:00"}
DAIRY_MON = {**DAIRY_FRI, "id": "dairy-mon", "delivery_day": "mon"}


def test_delivery_inside_the_closure_is_a_clash():
    out = cl.clashes_for(BUSINESS, [CLOSURE], [DAIRY_FRI], NOW)
    assert len(out) == 1
    c = out[0]
    assert c.supplier == "Dairy" and c.delivery_window == "08:30-09:00"
    assert c.closure_window_label == "08:00-12:00"
    assert c.distance_m == 41
    # Suggested drop is 30 minutes before the closure starts.
    assert c.suggested_drop_label == "07:30"
    assert c.day_label == "Fri 13 Nov"
    assert c.sources and c.sources[0]["url"] == "https://example.org/closure"


def test_touching_edges_are_not_a_clash():
    """The bakery drop ends at 08:00 and the closure starts at 08:00, so the van still gets in."""
    assert cl.clashes_for(BUSINESS, [CLOSURE], [BAKERY_FRI], NOW) == []


def test_a_closure_a_kilometre_away_is_not_a_clash():
    far = {**CLOSURE, "lat": 51.9067, "lon": -8.4800}   # ~1 km north
    assert cl.clashes_for(BUSINESS, [far], [DAIRY_FRI], NOW) == []


def test_supplier_not_delivering_that_day_is_not_a_clash():
    assert cl.clashes_for(BUSINESS, [CLOSURE], [DAIRY_MON], NOW) == []


def test_non_closure_events_never_clash():
    market = {**CLOSURE, "category": "market"}
    assert cl.clashes_for(BUSINESS, [market], [DAIRY_FRI], NOW) == []


def test_a_closure_with_no_end_time_is_not_guessed_at():
    open_ended = {**CLOSURE, "end_at": None}
    assert cl.clashes_for(BUSINESS, [open_ended], [DAIRY_FRI], NOW) == []


def test_a_closure_outside_the_seven_day_view_is_ignored():
    later = {**CLOSURE, "start_at": "2026-11-27T08:00:00+00:00", "end_at": "2026-11-27T12:00:00+00:00"}
    assert cl.clashes_for(BUSINESS, [later], [DAIRY_FRI], NOW) == []


def test_the_draft_contains_only_supported_numbers():
    c = cl.clashes_for(BUSINESS, [CLOSURE], [DAIRY_FRI], NOW)[0].to_dict()
    who, text = cl.template_draft(c)
    assert who == "Dairy"
    import re
    allowed_numbers = set(re.findall(r"\d+", " ".join(str(v) for v in cl.clash_facts(c).values())))
    assert all(n in allowed_numbers for n in re.findall(r"\d+", text)), text
    # No quantities, and nothing claiming the message was sent.
    for banned in ("crate", "loaf", "litre", "sent", "delivered"):
        assert banned not in text.lower()


def test_the_draft_names_the_contact_when_there_is_one():
    c = cl.clashes_for(BUSINESS, [CLOSURE], [{**BAKERY_FRI, "delivery_window": "08:15-08:45"}], NOW)[0]
    who, text = cl.template_draft(c.to_dict())
    assert who == "Declan (bakery)" and text.startswith("Hi Declan (bakery),")
    assert "08:15-08:45" in text and "07:30" in text


def test_the_closure_insight_page_shows_the_clash_and_drafts_a_message(tmp_path):
    """End to end: the clash card renders with its honesty labels and the draft reuses the
    existing edit / approve / copy flow."""
    from tests.test_present_business import app_client

    _app, client = app_client(tmp_path)
    client.post("/refresh", data={"mode": "prepared"})
    insights = client.get("/api/insights").get_json()["insights"]
    cid = next(i["id"] for i in insights if "Road closure" in i["title"])

    page = client.get(f"/insights/{cid}").get_data(as_text=True)
    assert "Deliveries This Could Block" in page
    assert "Dairy" in page and "08:30-09:00" in page      # supplier and its delivery window
    assert "08:00-12:00" in page                           # closure window
    assert "07:30" in page                                 # suggested earlier drop
    assert "Access only." in page                          # not a sales claim
    assert "Prepared demo closure" in page                 # prepared data stays labelled
    # The bakery drop ends exactly when the closure starts, so it must not be listed.
    section = page.split("Deliveries This Could Block")[1].split("Why It Showed Up")[0]
    assert "Bakery" not in section

    import re
    action = re.search(r'action="(/clashes/[^"]+/draft)"', page).group(1).replace("&amp;", "&")
    created = client.post(action, follow_redirects=True).get_data(as_text=True)
    assert "closes the road near us" in created
    assert "Could you get to us before 07:30" in created
    for banned in ("crate", "litre", "sent to", "delivered"):
        assert banned not in created.lower()
