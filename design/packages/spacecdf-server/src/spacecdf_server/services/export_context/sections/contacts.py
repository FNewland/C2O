"""Section ``contacts``: per-station and union contact statistics (min/day, passes/day, mean and
maximum pass, longest gap, data per day) and the leave-one-out unions (W4.05,
``ground_closure.contact_table``). Owner: H.

Shape read by the packs and the ConOps (W3.05)::

    stations: [{name, min_per_day, passes_per_day, mean_pass_min, max_pass_min, ...}]
    union:    {min_per_day, longest_gap_h, passes_per_day, mean_pass_min, max_pass_min, ...}

(the union's ``passes_per_day`` / ``mean_pass_min`` / ``max_pass_min`` are its windows: the
overlapping passes of several stations count once.)
"""
from __future__ import annotations


def empty() -> dict:
    return {"status": "empty", "stations": [], "union": {}, "leave_one_out": [], "method": {}, "link": None, "warnings": []}


def union_view(u: dict) -> dict:
    u = dict(u or {})
    if u:
        u.setdefault("passes_per_day", u.get("windows_per_day"))
        u.setdefault("mean_pass_min", u.get("mean_window_min"))
        u.setdefault("max_pass_min", u.get("max_window_min"))
    return u


async def collect(ctx) -> dict:
    from ...analysis_context import build_context
    from ...ground_closure import contact_table
    t = contact_table(await build_context(ctx.study_id), [])
    return {"status": "computed" if t["stations"] else "empty", "stations": t["stations"], "union": union_view(t["union"]),
            "leave_one_out": t["leave_one_out"], "method": t["method"], "link": t["link"], "warnings": t["warnings"]}
