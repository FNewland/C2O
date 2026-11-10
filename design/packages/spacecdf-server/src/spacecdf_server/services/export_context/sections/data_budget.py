"""Section ``data_budget``: the daily data budget of the study (W3.02 ``services/data_budget.py``):
daily closure and its cases, real-time and stored HK, the SIDs, the stores, the pass classes, the
day in the life, one real operations pass and the backlog. Owner: H.

Shape read by the packs, the master budget workbook and the ConOps (W3.05)::

    daily:  flat figures of the closure case (capacity, demand, margin, contact minutes, HK and
            science per day; ``closure``: the closure case itself)
    cases:  [{id, label, capacity, rt_hk, stored_hk, science, other, demand, margin_pct, status}]
            (MB/day; ``label`` in the document language; key names as in NUMBERS.yaml)
    gate_check: the PDR/CDR question "daily budget closes with margin, stores hold N days"
"""
from __future__ import annotations

#: case keys of services/data_budget -> the export names (NUMBERS.yaml data_budget.cases)
CASE_KEYS = (("capacity_mb", "capacity"), ("rt_hk_mb", "rt_hk"), ("stored_hk_mb", "stored_hk"), ("science_mb", "science"),
             ("other_mb", "other"), ("demand_mb", "demand"), ("margin_pct", "margin_pct"))


def empty() -> dict:
    return {"status": "empty", "daily": {}, "cases": [], "stores": [], "hk": {}, "framing": {}, "pass_classes": [],
            "day_in_the_life": {}, "ops_pass": None, "backlog": {}, "gate_check": {}, "link": None, "warnings": []}


def _label(v, lang: str) -> str:
    if isinstance(v, dict):
        return str(v.get(lang) or v.get("en") or "")
    return str(v or "")


def export_case(c: dict, lang: str = "en") -> dict:
    out = {"id": c.get("id"), "label": _label(c.get("label"), lang)}
    out.update({new: c.get(old) for old, new in CASE_KEYS})
    out["status"] = c.get("status")
    return out


def daily_figures(b: dict) -> dict:
    """Flat daily figures of the closure case (scalars only, plus ``closure``)."""
    cl = b.get("closure") or {}
    cap = b.get("capacity") or {}
    sci = b.get("science") or {}
    st = b.get("stored") or {}
    return {"closure_case": cl.get("id"), "capacity_mb_per_day": cl.get("capacity_mb"), "demand_mb_per_day": cl.get("demand_mb"),
            "margin_pct": cl.get("margin_pct"), "margin_required_percent": b.get("margin_required_percent"),
            "closure_status": cl.get("status"),
            "union_min_per_day": cap.get("union_min_per_day"), "usable_min_per_day": cap.get("usable_min_per_day"),
            "raw_channel_mb_per_day": cap.get("raw_mb_per_day"),
            "rt_hk_mb_per_day": cl.get("rt_hk_mb"), "stored_hk_mb_per_day": st.get("mb_per_day", cl.get("stored_hk_mb")),
            "science_delivered_mb_per_day": sci.get("delivered_mb_per_day"), "science_on_channel_mb_per_day": cl.get("science_mb"),
            "largest_science_with_margin_mb_per_day": sci.get("largest_with_margin_mb_per_day"),
            "closure": cl}


async def collect(ctx) -> dict:
    from ...data_budget import for_study, gate_check, ops_pass
    b = await for_study(ctx.study_id, gate=ctx.gate)
    lang = getattr(ctx, "lang", "en") or "en"
    return {"status": b.get("status"), "daily": daily_figures(b),
            "cases": [export_case(c, lang) for c in b.get("cases") or []],
            "capacity": b.get("capacity"), "science": b.get("science"),
            "stores": b["stores"],
            "hk": {"sids": b["sids"], "modes": b["modes"], "profiles": b["profiles"], "realtime": b["realtime"],
                   "stored": b["stored"], "packet": b["packet"], "services": b["services"]},
            "framing": b["framing"], "pass_classes": b["pass_classes"], "day_in_the_life": b["day_in_the_life"],
            "ops_pass": ops_pass(b), "backlog": b["backlog"], "gate_check": gate_check(b, ctx.gate or b.get("margin_gate")),
            "link": b.get("link"), "warnings": b.get("warnings") or []}
