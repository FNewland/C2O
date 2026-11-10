"""Section ``cdr``: the CDR design model (TM/TC database, FDIR, AOCS modes, operations products)
as the team accepted it, with the model checks and the housekeeping downlink budget. Rows are
grouped by kind; rejected rows are left out. Owner: X (collector); the CDR model itself is H's
(``routers/cdr.py``, ``services/cdr_*``)."""
from __future__ import annotations

GROUPS = ("tmtc", "fdir", "aocs", "ops")


def empty() -> dict:
    return {"dataset": None, "rows": {}, "counts": {}, "groups": {g: 0 for g in GROUPS},
            "checks": [], "summary": {}, "budget": {}}


async def collect(ctx) -> dict:
    from ....routers.cdr import cdr_view
    from ...cdr_model import KINDS
    v = await cdr_view(ctx.study_id)
    rows = {k: [r for r in (v.get("rows") or {}).get(k) or [] if r.get("status") != "rejected"]
            for k in KINDS}
    rows = {k: sorted(rs, key=lambda r: str(r.get("key") or "")) for k, rs in rows.items() if rs}
    counts = {k: len(rs) for k, rs in rows.items()}
    groups = {g: 0 for g in GROUPS}
    for k, n in counts.items():
        g = KINDS[k]["group"]
        groups[g] = groups.get(g, 0) + n
    return {"dataset": v.get("dataset"), "rows": rows, "counts": counts, "groups": groups,
            "checks": list(v.get("checks") or []), "summary": dict(v.get("summary") or {}),
            "budget": dict(v.get("budget") or {})}
