"""Flask app: server-rendered pages plus a small JSON API for checks.

Run:  flask --app "footfall.app:create_app()" run --debug
"""
from __future__ import annotations

import os
import json
import re

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template, request, send_from_directory,
                   session, url_for)

from . import business_form, db, present
from . import weather as weather_mod
from .config import load_env
from .domain import clashes as clashes_mod
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
PUBLIC = {"landing", "pricing", "login", "signup", "logout", "favicon", "static", "api_insights"}
PLANS = {"starter": "Starter (free)", "essentials": "Essentials", "multi": "Multi-site", "group": "Group"}
BUSINESS_TYPES = ["Café or coffee shop", "Restaurant or takeaway", "Bakery or deli", "Pub or bar",
                  "Independent shop", "Food truck or market stall", "Other"]


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
        if request.endpoint in {"landing", "login"}:
            return {"user": session.get("user")}
        c = con()
        run = db.last_run(c)
        modes = {r["data_mode"] for r in c.execute("SELECT DISTINCT data_mode FROM events").fetchall()}
        state = "none" if not run else {"ok": "ok", "partial": "partial"}.get(run["status"], "error")
        return {"run": run, "run_state": state, "modes": modes, "llm_enabled": model.enabled,
                "shell_business": business_data(), "now": clock(), "user": session.get("user")}

    @app.before_request
    def _require_login():
        if request.endpoint is None or request.endpoint in PUBLIC or session.get("user"):
            return None
        return redirect(url_for("login", next=request.path if request.method == "GET" else None))

    def business_data():
        if "business_data" not in g:
            g.business_data = db.get_business(con())
        return g.business_data

    def event_data():
        if "event_data" not in g:
            g.event_data = db.get_events(con(), clock())
        return g.event_data

    def compute():
        if "computed" in g:
            return g.computed
        c = con()
        b = business_data()
        at = clock()
        events = [{**e, "title": short_title(e["title"])} for e in event_data()]
        result = insights_mod.build(b, events, db.get_suppliers(c, b["id"]),
                                    db.get_weather(c, b["lat"], b["lon"]), at)
        g.computed = (b, result)
        return g.computed

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
                errors["email"] = "Enter an email address like name@yourbusiness.ie."
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

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        plan = request.values.get("plan", "starter")
        plan = plan if plan in PLANS else "starter"
        f, errors = {k: request.form.get(k, "").strip() for k in ("name", "business", "type", "email")}, {}
        if request.method == "POST":
            if not f["name"]:
                errors["name"] = "Enter your name."
            if not f["business"]:
                errors["business"] = "Enter your business name."
            if f["type"] not in BUSINESS_TYPES:
                errors["type"] = "Choose the kind of business you run."
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", f["email"]):
                errors["email"] = "Enter an email address like name@yourbusiness.ie."
            if len(request.form.get("password", "")) < 8:
                errors["password"] = "Use at least 8 characters."
            if not errors:
                session.clear()
                session["user"] = f["name"].split()[0][:24]
                flash(f"Welcome, {session['user']}! This demo doesn't save accounts, "
                      "so you're exploring Bríd's Kitchen, a fictional Cork café.")
                return redirect(url_for("index"))
        return render_template("signup.html", f=f, errors=errors, plan=plan, plans=PLANS,
                               types=BUSINESS_TYPES), (400 if errors else 200)

    @app.get("/pricing")
    def pricing():
        return render_template("pricing.html")

    @app.get("/favicon.ico")
    def favicon():
        return send_from_directory(os.path.join(app.static_folder, "brand"), "favicon.ico",
                                   mimetype="image/vnd.microsoft.icon", max_age=86400)

    @app.post("/logout")
    def logout():
        session.clear()
        flash("You've been logged out.")
        return redirect(url_for("landing"))

    @app.get("/app")
    def index():
        b, result = compute()
        c = con()
        states = db.draft_states(c)
        week = build_week(b, result, event_data(), clock(), drafts=states)
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
        week = build_week(b, result, event_data(), clock(), only_day=i.day, drafts=db.draft_states(c),
                          places=[here] if here else None)
        event = next((e for e in event_data() if e["id"] == i.event_id), {})
        # Deliveries a nearby closure would block. Access only: never a demand or sales claim.
        clashes = [x for x in clashes_mod.clashes_for(b, event_data(),
                                                      db.get_suppliers(c, b["id"]), clock())
                   if x.event_id == i.event_id]
        return render_template("insight.html", i=i, draft=draft, business=b, week=week, event=event,
                               clashes=clashes,
                               cd=present.countdown(i.action_deadline, clock(), draft),
                               rev=present.revenue_estimate(i.impact, i.direction, i.overlap_min, b))

    @app.post("/insights/<path:iid>/draft")
    def make_draft(iid):
        i = find_insight(iid)
        d = drafts_mod.draft({**i.to_dict(), "title": short_title(i.title)}, llm=model if model.enabled else None)
        draft_id = db.create_draft(con(), iid, d["recipient_label"], d["text"], d["source"])
        return redirect(url_for("draft", draft_id=draft_id))

    @app.post("/clashes/<path:cid>/draft")
    def make_clash_draft(cid):
        c = con()
        b, _ = compute()
        found = next((x for x in clashes_mod.clashes_for(b, event_data(),
                                                         db.get_suppliers(c, b["id"]), clock())
                      if x.id == cid), None) or abort(404)
        who, text = clashes_mod.template_draft(found.to_dict())
        draft_id = db.create_draft(c, cid, who, text, "template")
        return redirect(url_for("draft", draft_id=draft_id))
    @app.get("/orders")
    def orders():
        rows = con().execute("SELECT * FROM drafts ORDER BY updated_at DESC, id DESC").fetchall()
        return render_template("orders.html", orders=[dict(r) for r in rows])

    @app.route("/suppliers/<sid>/edit", methods=["GET", "POST"])
    def edit_supplier(sid):
        c = con()
        b = db.get_business(c)
        s = next((s for s in db.get_suppliers(c, b["id"]) if s["id"] == sid), None)
        if s is None:
            abort(404)
        errors = []
        if request.method == "POST":
            v = request.form
            rule_type = v.get("rule_type", "")
            rule = {"type": rule_type, "time": v.get("cutoff_time", "")}
            s.update(supplier=v.get("supplier", "").strip(), contact_label=v.get("contact_label", "").strip(),
                     delivery_day=v.get("delivery_day", ""), delivery_window=v.get("delivery_window", "").strip())
            if not s["supplier"] or len(s["supplier"]) > 200:
                errors.append("Enter a supplier name (up to 200 characters).")
            if s["delivery_day"] not in WEEKDAYS:
                errors.append("Choose a delivery day.")
            time_pattern = r"(?:[01]\d|2[0-3]):[0-5]\d"
            if not re.fullmatch(time_pattern, rule["time"]):
                errors.append("Enter a valid order cutoff time.")
            window = s["delivery_window"]
            if window and (not re.fullmatch(time_pattern + "-" + time_pattern, window) or window[:5] >= window[6:]):
                errors.append("Use a delivery window such as 07:30-08:00, with the end after the start.")
            if rule_type == "weekday":
                rule["day"] = v.get("cutoff_day", "")
                if rule["day"] not in WEEKDAYS:
                    errors.append("Choose the cutoff weekday.")
            elif rule_type == "business_days_before":
                rule["closed"] = v.getlist("closed")
                try:
                    rule["n"] = int(v.get("days_before", ""))
                    if not 1 <= rule["n"] <= 30 or len(set(rule["closed"])) == 7 or any(d not in WEEKDAYS for d in rule["closed"]):
                        raise ValueError
                except ValueError:
                    errors.append("Use 1–30 working days before delivery and leave at least one working day open.")
            else:
                errors.append("Choose a cutoff rule.")
            s["cutoff_rule"] = rule
            if not errors:
                c.execute("UPDATE supplier_constraints SET supplier=?, contact_label=?, delivery_day=?, delivery_window=?, cutoff_rule=? WHERE id=? AND business_id=?",
                          (s["supplier"], s["contact_label"] or None, s["delivery_day"], window or None, json.dumps(rule), sid, b["id"]))
                c.commit()
                flash("Supplier details saved. Order deadlines now use these settings. Existing order messages are unchanged.")
                return redirect(url_for("business", _anchor="sup-h"))
        return render_template("supplier_edit.html", s=s, errors=errors, weekdays=WEEKDAYS), (400 if errors else 200)

    @app.get("/drafts/<int:draft_id>")
    def draft(draft_id):
        d = db.get_draft(con(), draft_id) or abort(404)
        i = find_insight(d["insight_id"], missing_ok=True)
        cd = present.countdown(i.action_deadline, clock(), d) if i else None
        return render_template("draft.html", d=d, i=i, cd=cd)

    @app.post("/drafts/<int:draft_id>")
    def save_draft(draft_id):
        d = db.get_draft(con(), draft_id) or abort(404)
        text = request.form.get("text", "").strip()
        recipient = request.form.get("recipient_label", d["recipient_label"]).strip()
        if not text or not recipient or len(recipient) > 200 or len(text) > 20000:
            d.update(text=text, recipient_label=recipient)
            return render_template("draft.html", d=d, i=None, cd=None,
                                   error="Enter a recipient (up to 200 characters) and a message (up to 20,000 characters)."), 400
        db.update_draft(con(), draft_id, text, recipient)
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
