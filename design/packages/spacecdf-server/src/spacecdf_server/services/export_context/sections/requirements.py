"""Section ``requirements``: every non-retired requirement of the study, sorted by level
(mission, system, subsystem, then any other level) and code, with counts. Interface requirements
generated from links (code ``IR-*``) are flagged ``generated_interface``. Every row carries
``parent_ids`` and ``objective_ids`` (``routers.requirements.with_lists``: the further parents and
objectives of W2.03 after the stored one) and ``parent_codes``. Owner: X (collector);
the requirement fields themselves belong to R (W2)."""
from __future__ import annotations

LEVEL_ORDER = ("stakeholder", "mission", "segment", "system", "subsystem", "interface")


def empty() -> dict:
    return {"items": [], "counts": {"total": 0, "by_level": {}, "user": 0, "generated_interface": 0}}


def _key(r: dict) -> tuple:
    lvl = str(r.get("level") or "")
    return (LEVEL_ORDER.index(lvl) if lvl in LEVEL_ORDER else len(LEVEL_ORDER), str(r.get("code") or "~"),
            str(r.get("id") or ""))


async def collect(ctx) -> dict:
    from ....routers.requirements import _requirements, ensure_requirements_loaded
    try:
        await ensure_requirements_loaded()
    except Exception:  # noqa: BLE001 — DB unavailable: use what is cached
        pass
    rows = [dict(r) for r in _requirements.values()
            if r.get("study_id") == ctx.study_id and r.get("status") != "retired"]
    rows.sort(key=_key)
    try:
        from ....routers.requirements import with_lists
        rows = await with_lists(ctx.study_id, rows)
    except Exception:  # noqa: BLE001 — relations unavailable: the stored parent only
        rows = [{**r, "parent_ids": [p for p in [r.get("parent_id") or r.get("derived_from_requirement_id")] if p],
                 "objective_ids": [o for o in [r.get("objective_id")] if o]} for r in rows]
    codes = {r.get("id"): r.get("code") or r.get("id") for r in rows}
    for r in rows:
        r["parent_codes"] = [codes.get(p, p) for p in r.get("parent_ids") or []]
    by_level: dict[str, int] = {}
    gen = 0
    for r in rows:
        lvl = str(r.get("level") or "")
        by_level[lvl] = by_level.get(lvl, 0) + 1
        r["generated_interface"] = str(r.get("code") or "").startswith("IR-")
        gen += r["generated_interface"]
    return {"items": rows, "counts": {"total": len(rows), "by_level": by_level, "user": len(rows) - gen,
                                      "generated_interface": gen}}
