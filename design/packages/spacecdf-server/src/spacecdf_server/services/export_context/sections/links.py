"""Section ``links``: link budgets. ``design_case`` is ``study.requirements.link`` (what the
analyses read); ``items`` are the named link cases (W4.04, table ``link_budgets``: direction, band,
station, elevation, rate tier, coding, powers, gains, losses, T_sys, required Eb/N0, margin and the
computed cascade in ``results``), in display order. ``by_direction`` groups the case ids. Owner: D."""
from __future__ import annotations

from ._util import dump


def empty() -> dict:
    return {"design_case": {}, "items": [], "by_direction": {"downlink": [], "uplink": []}}


async def collect(ctx) -> dict:
    req = getattr(ctx.study, "requirements", None) if ctx.study is not None else None
    link = dump(getattr(req, "link", None)) if req is not None else None
    from ....routers.link_budgets import list_cases
    items = await list_cases(ctx.study_id)
    return {"design_case": link or {}, "items": items,
            "by_direction": {d: [c["id"] for c in items if c["direction"] == d] for d in ("downlink", "uplink")}}
