"""Supplier message drafts: grounded wording variants, optional model style selection."""
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


def styled_draft(insight: dict, style: str) -> str:
    """All factual clauses are rendered locally; the model only chooses a style."""
    _, baseline = template_draft(insight)
    if style == "standard":
        return baseline
    f = facts_for(insight)
    hi = f"Hi {f['contact']}," if f["contact"] else "Hi,"
    if insight["direction"] == "decrease":
        body = (f"{f['title']} may affect access near us ({f['window']}). "
                "Could we check delivery timing for that day?")
    elif f["status"] == "missed":
        body = (f"{f['title']} is nearby ({f['window']}). The cutoff has passed. "
                f"Would a late change to our {f['delivery_day']} order be possible?")
    else:
        body = (f"{f['title']} is nearby ({f['window']}). "
                f"I may adjust our {f['delivery_day']} order before the cutoff ({f['cutoff']}). "
                "I'll confirm quantities separately.")
    closing = "Many thanks!" if style == "warm" else "Thanks!"
    return f"{hi} {body} {closing}"


def draft(insight: dict, llm=None) -> dict:
    """Choose grounded wording; never accept model-authored factual prose."""
    recipient, text = template_draft(insight)
    source = "template"
    if llm is not None:
        try:
            out = llm.complete_json(
                "Choose a wording style for this supplier message: standard, concise, or warm. "
                'Return ONLY JSON {"style": "standard|concise|warm"}. Do not write message text.', text)
            # Reject added prose/fields as well as malformed or unknown selections.
            if (isinstance(out, dict) and set(out) == {"style"}
                    and isinstance(out["style"], str)
                    and out["style"] in {"standard", "concise", "warm"}):
                text, source = styled_draft(insight, out["style"]), "llm"
        except Exception:
            pass
    return {"recipient_label": recipient, "text": text, "source": source}
