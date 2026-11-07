"""Flask app: server-rendered pages plus a small JSON API for checks.

Run:  flask --app "footfall.app:create_app()" run --debug
"""
from __future__ import annotations

import os

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, url_for

from . import db
from .domain import drafts as drafts_mod
from .domain import insights as insights_mod
from .domain.timeutil import fmt, now, parse_dt
from .llm import LLM
from .scout import refresh as refresh_mod
from . import weather as weather_mod
from .week import build_week, short_title


def create_app(db_path: str | None = None, clock=None, llm: LLM | None = None, fetcher=None,
               weather_fetcher=None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-not-secret")
    app.config["DB_PATH"] = db_path or os.getenv("FOOTFALL_DB", "footfall.sqlite3")
    clock = clock or now
    model = llm or LLM()

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

    def compute():
        c = con()
        b = db.get_business(c)
        at = clock()
        result = insights_mod.build(b, db.get_events(c, at), db.get_suppliers(c, b["id"]),
                                    db.get_weather(c, b["lat"], b["lon"]), at)
        return b, result

    def find_insight(iid: str):
        _, result = compute()
        for i in result["insights"]:
            if i.id == iid:
                return i
        abort(404)

    @app.get("/")
    def index():
        b, result = compute()
        c = con()
        modes = {r["data_mode"] for r in c.execute("SELECT DISTINCT data_mode FROM events").fetchall()}
        week = build_week(b, result, db.get_events(c, clock()), clock())
        return render_template("index.html", business=b, run=db.last_run(c), modes=modes, now=clock(),
                               llm_enabled=model.enabled, week=week, **result)

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
            flash(f"Refresh ({run['mode']}) finished: {run['status']}")
        except refresh_mod.RefreshBusy as e:
            flash(str(e))
        return redirect(url_for("index"))

    @app.get("/insights/<path:iid>")
    def insight(iid):
        i = find_insight(iid)
        c = con()
        existing = c.execute("SELECT * FROM drafts WHERE insight_id=? ORDER BY id DESC LIMIT 1", (iid,)).fetchone()
        b, result = compute()
        week = build_week(b, result, db.get_events(c, clock()), clock(), only_day=i.day)
        return render_template("insight.html", i=i, draft=dict(existing) if existing else None,
                               business=b, week=week)

    @app.post("/insights/<path:iid>/draft")
    def make_draft(iid):
        i = find_insight(iid)
        d = drafts_mod.draft(i.to_dict(), llm=model if model.enabled else None)
        draft_id = db.create_draft(con(), iid, d["recipient_label"], d["text"], d["source"])
        return redirect(url_for("draft", draft_id=draft_id))

    @app.get("/drafts/<int:draft_id>")
    def draft(draft_id):
        d = db.get_draft(con(), draft_id) or abort(404)
        return render_template("draft.html", d=d)

    @app.post("/drafts/<int:draft_id>")
    def save_draft(draft_id):
        db.get_draft(con(), draft_id) or abort(404)
        db.update_draft(con(), draft_id, request.form["text"].strip())
        flash("Saved. Approve again after editing.")
        return redirect(url_for("draft", draft_id=draft_id))

    @app.post("/drafts/<int:draft_id>/approve")
    def approve(draft_id):
        db.get_draft(con(), draft_id) or abort(404)
        db.approve_draft(con(), draft_id)
        flash("Approved. Not sent: copy it into WhatsApp or email yourself.")
        return redirect(url_for("draft", draft_id=draft_id))

    @app.get("/api/insights")
    def api_insights():
        _, r = compute()
        return jsonify({"insights": [i.to_dict() for i in r["insights"]],
                        "excluded": [vars(e) for e in r["excluded"]], "review": [vars(x) for x in r["review"]]})

    return app
