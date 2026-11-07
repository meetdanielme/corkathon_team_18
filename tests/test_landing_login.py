from footfall.app import create_app

from .conftest import NOW, FakeLLM


def client(tmp_path):
    return create_app(db_path=str(tmp_path / "l.sqlite3"), clock=lambda: NOW, llm=FakeLLM(enabled=False)).test_client()


def test_landing_is_public_and_links_to_login(tmp_path):
    page = client(tmp_path).get("/").get_data(as_text=True)
    assert "before your order is due" in page and 'href="/login"' in page and "Illustrative example" in page


def test_app_pages_redirect_to_login_until_signed_in(tmp_path):
    c = client(tmp_path)
    r = c.get("/business")
    assert r.status_code == 302 and r.headers["Location"].endswith("/login?next=/business")
    assert c.post("/refresh", data={"mode": "prepared"}).headers["Location"].endswith("/login")
    assert c.get("/api/insights").status_code == 200


def test_empty_or_invalid_credentials_show_inline_errors(tmp_path):
    c = client(tmp_path)
    r = c.post("/login", data={"email": "", "password": ""})
    page = r.get_data(as_text=True)
    assert r.status_code == 400 and "Enter your email address." in page and "Enter your password." in page
    page = c.post("/login", data={"email": "not-an-email", "password": "x"}).get_data(as_text=True)
    assert "Enter an email address like" in page and 'value="not-an-email"' in page
    assert c.get("/app").status_code == 302


def test_any_credentials_sign_in_then_sign_out(tmp_path):
    c = client(tmp_path)
    r = c.post("/login", data={"email": "olan.h@example.ie", "password": "anything", "next": "/business"})
    assert r.headers["Location"] == "/business"
    with c.session_transaction() as s:
        assert s["user"] == "Olan" and "password" not in s and "email" not in s
    page = c.get("/app").get_data(as_text=True)
    assert "The Week Ahead" in page and "Log Out Olan" in page
    assert c.get("/login").headers["Location"] == "/app"
    r = c.post("/logout", follow_redirects=True)
    assert "been logged out." in r.get_data(as_text=True)
    assert c.get("/app").status_code == 302


def test_demo_button_and_unsafe_next(tmp_path):
    c = client(tmp_path)
    r = c.post("/login", data={"demo": "1", "next": "//evil.example"})
    assert r.headers["Location"] == "/app"
    with c.session_transaction() as s:
        assert s["user"] == "Bríd"


def test_forgot_password_explains_demo(tmp_path):
    assert "no password to reset" in client(tmp_path).get("/login?forgot=1").get_data(as_text=True)


def test_landing_has_login_and_signup_and_broad_audience(tmp_path):
    page = client(tmp_path).get("/").get_data(as_text=True)
    assert 'href="/login">Log in</a>' in page and 'href="/signup">Sign up</a>' in page
    assert "Pubs and bars" in page and "Independent shops" in page and 'href="/pricing"' in page


def test_pricing_page_is_public_and_labels_proposed_prices(tmp_path):
    page = client(tmp_path).get("/pricing").get_data(as_text=True)
    assert "€19" in page and "Essentials" in page and "no payments are taken" in page
    assert 'href="/signup?plan=essentials"' in page


def test_signup_validates_then_signs_in_without_storing(tmp_path):
    c = client(tmp_path)
    r = c.post("/signup", data={"name": "", "business": "", "type": "Spaceship", "email": "x", "password": "short"})
    page = r.get_data(as_text=True)
    assert r.status_code == 400 and "Use at least 8 characters." in page and "Choose the kind of business" in page
    r = c.post("/signup", data={"name": "Aoife Murphy", "business": "The Corner Shop", "type": "Independent shop",
                                "email": "aoife@cornershop.ie", "password": "longenough", "plan": "essentials"})
    assert r.headers["Location"] == "/app"
    with c.session_transaction() as s:
        assert s["user"] == "Aoife" and set(s) <= {"user", "_flashes", "_permanent"}
    assert "Plan: <b>Multi-site</b>" in c.get("/signup?plan=multi").get_data(as_text=True)


def test_favicon_served(tmp_path):
    r = client(tmp_path).get("/favicon.ico")
    assert r.status_code == 200 and r.data[:4] == b"\x00\x00\x01\x00"
