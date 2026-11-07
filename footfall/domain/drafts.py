"""Supplier message drafts: a deterministic template, optional LLM rephrase, numeric guardrail."""
from __future__ import annotations

import re

NUM = re.compile(r"\d+")


def facts_for(insight: dict) -> dict:
    d = insight.get("action_deadline") or {}
    return {"title": insight["title"], "window": insight["window_label"],
            "supplier": d.get("supplier", ""), "contact": d.get("contact_label") or "",
            "delivery_day": d.get("delivery_day", ""), "cutoff": d.get("cutoff_label", ""),
            "status": d.get("status", "")}


def template_draft(insight: dict) -> tuple[str, str]:
    """Returns (recipient_label, text). Never states quantities: the owner decides."""
    f = facts_for(insight)
    who = f["contact"] or f["supplier"] or "Supplier"
    hi = f"Hi {f['contact']}," if f["contact"] else "Hi,"
    if insight["direction"] == "decrease":
        text = (f"{hi} just a heads-up: {f['title']} may affect access near us {f['window']}. "
                f"Could we check our delivery timing for that day? Thanks!")
    elif f["status"] == "missed":
        text = (f"{hi} I know the cutoff has passed, but there's {f['title']} nearby ({f['window']}). "
                f"Is a late change to our {f['delivery_day']} order possible? Thanks!")
    else:
        text = (f"{hi} there's {f['title']} nearby ({f['window']}). I may adjust our {f['delivery_day']} "
                f"order before your cutoff ({f['cutoff']}). I'll confirm quantities shortly. Thanks!")
    return who, text


def unsupported_numbers(text: str, insight: dict) -> list[str]:
    allowed = set(NUM.findall(" ".join(str(v) for v in facts_for(insight).values())))
    return [n for n in NUM.findall(text) if n not in allowed]


def draft(insight: dict, llm=None) -> dict:
    """Template first. If an LLM rephrase adds any number not in the facts, keep the template."""
    recipient, text = template_draft(insight)
    source = "template"
    if llm is not None:
        try:
            out = llm.complete_json(
                "Rephrase this supplier message to sound natural and brief. Keep every fact. "
                "Add no numbers, quantities, dates or times that are not already in it. "
                'Return JSON {"text": "..."}.', text)
            candidate = (out or {}).get("text", "").strip()
            if candidate and not unsupported_numbers(candidate, insight):
                text, source = candidate, "llm"
        except Exception:
            pass
    return {"recipient_label": recipient, "text": text, "source": source}
