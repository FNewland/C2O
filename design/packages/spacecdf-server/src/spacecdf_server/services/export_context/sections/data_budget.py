"""Section ``data_budget``: the daily data budget of the study (W3.02 ``services/data_budget.py``):
daily closure and its cases, real-time and stored HK, the SIDs, the stores, the pass classes, the
day in the life and the backlog. Owner: H."""
from __future__ import annotations



def empty() -> dict:
    return {"status": "empty", "daily": {}, "stores": [], "hk": {}, "framing": {}, "pass_classes": [],
            "day_in_the_life": {}, "backlog": {}, "link": None, "warnings": []}


async def collect(ctx) -> dict:
    from ...data_budget import for_study
    b = await for_study(ctx.study_id)
    return {"status": b.get("status"), "daily": {"closure": b["closure"], "cases": b["cases"], "capacity": b["capacity"],
                                                  "science": b["science"], "margin_required_percent": b["margin_required_percent"]},
            "stores": b["stores"],
            "hk": {"sids": b["sids"], "modes": b["modes"], "profiles": b["profiles"], "realtime": b["realtime"],
                   "stored": b["stored"], "packet": b["packet"], "services": b["services"]},
            "framing": b["framing"], "pass_classes": b["pass_classes"], "day_in_the_life": b["day_in_the_life"],
            "backlog": b["backlog"], "link": b.get("link"), "warnings": b.get("warnings") or []}
