"""Section ``contacts``: per-station and union contact statistics (min/day, passes/day, mean and
maximum pass, longest gap, data per day) and the leave-one-out unions (W4.05,
``ground_closure.contact_table``). Owner: H."""
from __future__ import annotations



def empty() -> dict:
    return {"status": "empty", "stations": [], "union": {}, "leave_one_out": [], "method": {}, "link": None, "warnings": []}


async def collect(ctx) -> dict:
    from ...analysis_context import build_context
    from ...ground_closure import contact_table
    t = contact_table(await build_context(ctx.study_id), [])
    return {"status": "computed" if t["stations"] else "empty", "stations": t["stations"], "union": t["union"], "leave_one_out": t["leave_one_out"], "method": t["method"],
            "link": t["link"], "warnings": t["warnings"]}
