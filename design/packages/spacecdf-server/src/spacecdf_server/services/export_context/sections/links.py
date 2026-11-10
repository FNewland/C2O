"""Section ``links``: link-budget cases. Today only the design case ``study.requirements.link``
exists; W4.04 adds the named cases (per station, tier, direction). Owner: D."""
from __future__ import annotations

from ._util import dump


def empty() -> dict:
    return {"design_case": {}, "items": [], "status": "partial"}


async def collect(ctx) -> dict:
    req = getattr(ctx.study, "requirements", None) if ctx.study is not None else None
    link = dump(getattr(req, "link", None)) if req is not None else None
    return {"design_case": link or {}, "items": [], "status": "partial", "owner": "D", "work_package": "W4.04"}
