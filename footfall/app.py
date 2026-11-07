"""Flask app: server-rendered pages plus a small JSON API for checks.

Run:  flask --app "footfall.app:create_app()" run --debug
"""
from __future__ import annotations

import os
import re

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for

from . import business_form, db, present
from . import weather as weather_mod
from .config import load_env
from .domain import drafts as drafts_mod
from .domain import hours as hours_mod
from .domain import insights as insights_mod
from .domain.timeutil import WEEKDAYS, fmt, now, parse_dt
from .geocode import geocode
from .llm import LLM
from .scout import refresh as refresh_mod
from .week import build_week, short_title

# Simulated sign-in for the demo: any credentials work, nothing is stored server-side.
DEMO_EMAIL = "brid@bridskitchen.ie"
PUBLIC = {"landing", "login", "logout", "static", "api_insights"}


def display_name(email: str) -> str:
    first = re.split(r"[._+-]", email.split("@")[0])[0]
    return "Bríd" if email == DEMO_EMAIL else (first[:1].upper() + first[1:]) or "Owner"


def create_app(db_path: str | None = None, clock=None, llm: LLM | None = None, fetcher=None,
               weather_fetcher=None, geocoder=None) -> Flask:
    load_env()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-not-secret")
    app.config["DB_PATH"] = db_path or os.getenv("FOOTFALL_DB", "footfall.sqlite3")
    clock = clock or now
    model = llm or LLM()
    geocoder = geocoder or geocode

    with db.connect(app.config["DB_PATH"]) as con:
        db.init(con)
        if not con.execute("SELECT 1 FROM businesses LIMIT 1").fetchone():
            db.seed(con)

    def con():
        if "con" not in g:
            g.con = db.connect(app.config["DB_PATH"])
        return g.con

    @app.teardown_appcontext
    def _close(_exc):
        c = g.pop("con", None)
        if c is not None:
            c.close()

    @app.template_filter("when")
    def _when(value):
        dt = parse_dt(value) if isinstance(value, str) else value
        return fmt(dt) if dt else "unknown"

    app.add_template_filter(short_title, "short")
    app.add_template_filter(present.local_iso, "iso")
    app.add_template_filter(present.dist, "dist")
    app.add_template_filter(insights_mod.duration_words, "duration")
    app.add_template_filter(present.walk_minutes, "walk")
    app.add_template_filter(present.category_icon, "category_icon")
    app.add_template_filter(present.reason_icon, "reason_icon")
    app.add_template_filter(present.confidence_icon, "confidence_icon")

    @app.template_filter("ago")
    def _ago(value):
        return present.ago(value, clock())

    @app.context_processor
    def _shell():
        """Header status and business, shown on every page."""
        c = con()
        run = db.last_run(c)
        modes = {r["data_mode"] for r in c.execute("SELECT DISTINCT data_mode FROM events").fetchall()}
        state = "none" if not run else {"ok": "ok", "partial": "partial"}.get(run["status"], "error")
        return {"run": run, "run_state": state, "modes": modes, "llm_enabled": model.enabled,
                "shell_business": db.get_business(c), "now": clock(), "user": session.get("user")}

    @app.before_request
    def _require_login():
        if request.endpoint is None or request.endpoint in PUBLIC or session.get("user"):
            return None
        return redirect(url_for("login", next=request.path if request.method == "GET" else None))

    def compute():
        c = con()
        b = db.get_business(c)
        at = clock()
        result = insights_mod.build(b, db.get_events(c, at), db.get_suppliers(c, b["id"]),
                                    db.get_weather(c, b["lat"], b["lon"]), at)
        return b, result

    def find_insight(iid: str, missing_ok: bool = False):
        _, result = compute()
        for i in result["insights"]:
            if i.id == iid:
                return i
        if missing_ok:
            return None
        abort(404)

    def safe_next(default: str, nxt: str | None = None) -> str:
        nxt = request.form.get("next", "") if nxt is None else nxt
        return nxt if nxt.startswith("/") and not nxt.startswith("//") else default

    @app.get("/")
    def landing():
        return render_template("landing.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        nxt = safe_next(url_for("index"), request.values.get("next", ""))
        email, errors = "", {}
        if request.method == "POST":
            demo = bool(request.form.get("demo"))
            email = DEMO_EMAIL if demo else request.form.get("email", "").strip()
            if not email:
                errors["email"] = "Enter your email address."
            elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                errors["email"] = "Enter an email address like name@yourcafe.ie."
            if not demo and not request.form.get("password"):
                errors["password"] = "Enter your password."
            if not errors:
                session.clear()
                session["user"] = display_name(email)
                session.permanent = bool(request.form.get("remember"))
                return redirect(nxt)
        if session.get("user") and request.method == "GET":
            return redirect(nxt)
        return render_template("login.html", email=email, errors=errors, next=nxt,
                               forgot="forgot" in request.args), (400 if errors else 200)

    @app.post("/logout")
    def logout():
        session.clear()
        flash("You have been signed out.")
        return redirect(url_for("landing"))

    @app.get("/app")
    def index():
        b, result = compute()
        c = con()
        states = db.draft_states(c)
        week = build_week(b, result, db.get_events(c, clock()), clock(), drafts=states)
        cards = [{"i": i, "cd": present.countdown(i.action_deadline, clock(), states.get(i.id))}
                 for i in result["insights"]]
        attention = sum(1 for x in cards if x["cd"]["level"] in ("now", "soon", "missed"))
        today = clock().date().isoformat()
        places = [{"loc": loc, "hours": hours_mod.summary(loc),
                   "special": next((x for x in loc["special_hours"] if x["date"] >= today), None)}
                  for loc in b["locations"]]
        return render_template("index.html", business=b, week=week, cards=cards, attention=attention, places=places,
                               cutoffs=sum(1 for x in cards if x["cd"]["level"] not in ("none", "done")),
                               done=sum(1 for x in cards if x["cd"]["level"] == "done"), **result)

    @app.post("/refresh")
    def refresh():
        mode = request.form.get("mode", "prepared")
        c = con()
        try:
            if mode == "live":
                b = db.get_business(c)
                kwargs = {"weather_refresh": lambda: weather_mod.refresh(
                    c, b, **({"fetcher": weather_fetcher} if weather_fetcher else {}))}
                if fetcher:
                    kwargs["fetcher"] = fetcher
                run = refresh_mod.run_live(c, model, at=clock(), **kwargs)
            else:
                run = refresh_mod.run_prepared(c, at=clock())
            flash({"ok": f"Up to date. We found {run['events_upserted']} events near you.",
                   "partial": "Partly up to date: we couldn't check some event listings. Try again later."}
                  .get(run["status"], "We couldn't check for new events just now. Try again shortly."))
        except refresh_mod.RefreshBusy as e:
            flash(str(e))
        return redirect(safe_next(url_for("index")))

    @app.get("/insights/<path:iid>")
    def insight(iid):
        i = find_insight(iid)
        c = con()
        existing = c.execute("SELECT * FROM drafts WHERE insight_id=? ORDER BY id DESC LIMIT 1", (iid,)).fetchone()
        draft = dict(existing) if existing else None
        b, result = compute()
        here = next((loc for loc in b["locations"] if i.location and loc["address"] == i.location.get("address")), None)
        week = build_week(b, result, db.get_events(c, clock()), clock(), only_day=i.day, drafts=db.draft_states(c),
                          places=[here] if here else None)
        event = next((e for e in db.get_events(c, clock()) if e["id"] == i.event_id), {})
        return render_template("insight.html", i=i, draft=draft, business=b, week=week, event=event,
                               cd=present.countdown(i.action_deadline, clock(), draft),
                               rev=present.revenue_estimate(i.impact, i.direction, i.overlap_min, b))

    @app.post("/insights/<path:iid>/draft")
    def make_draft(iid):
        i = find_insight(iid)
        d = drafts_mod.draft(i.to_dict(), llm=model if model.enabled else None)
        draft_id = db.create_draft(con(), iid, d["recipient_label"], d["text"], d["source"])
        return redirect(url_for("draft", draft_id=draft_id))

    @app.get("/drafts/<int:draft_id>")
    def draft(draft_id):
        d = db.get_draft(con(), draft_id) or abort(404)
        i = find_insight(d["insight_id"], missing_ok=True)
        cd = present.countdown(i.action_deadline, clock(), d) if i else None
        return render_template("draft.html", d=d, i=i, cd=cd)

    @app.post("/drafts/<int:draft_id>")
    def save_draft(draft_id):
        db.get_draft(con(), draft_id) or abort(404)
        db.update_draft(con(), draft_id, request.form["text"].strip())
        flash("Saved. Approve the message again when you're happy with it.")
        return redirect(url_for("draft", draft_id=draft_id))

    @app.post("/drafts/<int:draft_id>/approve")
    def approve(draft_id):
        db.get_draft(con(), draft_id) or abort(404)
        db.approve_draft(con(), draft_id)
        flash("Approved. Not sent: copy it into WhatsApp or email yourself.")
        return redirect(url_for("draft", draft_id=draft_id))

    @app.route("/business", methods=["GET", "POST"])
    def business():
        c = con()
        b = db.get_business(c)
        errors, state = {}, business_form.state_from_business(b)
        if request.method == "POST":
            fields, locations, errors, state = business_form.parse(request.form, b["locations"], geocoder)
            if not errors:
                db.update_business(c, b["id"], fields)
                db.set_locations(c, b["id"], locations)
                flash("Business details saved.")
                return redirect(url_for("business"))
        suppliers = db.get_suppliers(c, b["id"])
        sources = c.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        return render_template("business.html", b=b, f=state, errors=errors, suppliers=suppliers, sources=sources,
                               weekdays=WEEKDAYS), (400 if errors else 200)

    @app.get("/api/insights")
    def api_insights():
        _, r = compute()
        return jsonify({"insights": [i.to_dict() for i in r["insights"]],
                        "excluded": [vars(e) for e in r["excluded"]], "review": [vars(x) for x in r["review"]]})

    return app
