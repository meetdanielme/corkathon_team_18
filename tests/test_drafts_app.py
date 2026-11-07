from footfall import db
from footfall.app import create_app
from footfall.domain import drafts
from footfall.scout.refresh import run_prepared

from .conftest import NOW, FakeLLM

INSIGHT = {"title": "Graduation ceremony (fictional demo)", "window_label": "Thu 12 Nov 10:00-14:00",
           "direction": "increase", "action_deadline": {"supplier": "Bakery", "contact_label": "Declan (bakery)",
           "delivery_day": "Thu 12 Nov", "cutoff_label": "Wed 11 Nov 16:00", "status": "upcoming"}}


def test_template_has_no_quantities_and_passes_guardrail():
    who, text = drafts.template_draft(INSIGHT)
    assert who == "Declan (bakery)" and "Wed 11 Nov 16:00" in text
    assert drafts.unsupported_numbers(text, INSIGHT) == []


def test_llm_rephrase_with_new_number_is_rejected():
    d = drafts.draft(INSIGHT, llm=FakeLLM([{"text": "Hi Declan, can you send 40 extra loaves Thu 12 Nov?"}]))
    assert d["source"] == "template" and "40" not in d["text"]


def test_llm_rephrase_without_new_numbers_is_kept():
    good = "Hi Declan, graduation nearby Thu 12 Nov 10:00-14:00; I may tweak the order before Wed 11 Nov 16:00."
    assert drafts.draft(INSIGHT, llm=FakeLLM([{"text": good}]))["source"] == "llm"


def test_full_browser_flow(tmp_path):
    app = create_app(db_path=str(tmp_path / "a.sqlite3"), clock=lambda: NOW, llm=FakeLLM(enabled=False))
    c = app.test_client()
    assert c.get("/").status_code == 200
    page = c.post("/refresh", data={"mode": "prepared"}, follow_redirects=True).get_data(as_text=True)
    assert "prepared data" in page and "Graduation ceremony" in page and "Filtered out" in page
    data = c.get("/api/insights").get_json()
    iid = next(i["id"] for i in data["insights"] if "Graduation" in i["title"])
    detail = c.get(f"/insights/{iid}").get_data(as_text=True)
    assert "Wed 11 Nov 16:00" in detail and "Confidence" in detail
    r = c.post(f"/insights/{iid}/draft")
    draft_url = r.headers["Location"]
    did = int(draft_url.rstrip("/").split("/")[-1])
    c.post(f"/drafts/{did}/approve")
    with db.connect(app.config["DB_PATH"]) as con:
        assert db.get_draft(con, did)["approved_at"]
    c.post(f"/drafts/{did}", data={"text": "Edited text"})
    with db.connect(app.config["DB_PATH"]) as con:
        d = db.get_draft(con, did)
        assert d["text"] == "Edited text" and d["approved_at"] is None  # edit resets approval
    c.post(f"/drafts/{did}/approve")
    html = c.get(f"/drafts/{did}").get_data(as_text=True)
    assert "not sent" in html and "delivered" not in html.lower()
