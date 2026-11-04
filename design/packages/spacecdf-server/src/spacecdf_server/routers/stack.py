"""CubeSat stack builder API (design rules §4; services/stack_builder.py).

    GET    /api/studies/{id}/stack                 layout: approved + open proposal, each evaluated
    POST   /api/studies/{id}/stack/auto-place      rule placement + swap search -> proposal (rule:STACK-AUTO)
    PUT    /api/studies/{id}/stack/proposal        {spec, base_version?} user edit -> proposal
    POST   /api/studies/{id}/stack/preview         {spec} evaluate only (live checks while dragging)
    POST   /api/studies/{id}/stack/approve         Structures seat: proposal -> approved, writes position_json
    POST   /api/studies/{id}/stack/reject          drop the proposal
    GET    /api/studies/{id}/stack/geometry        ?which=approved|proposal&format=json|yaml -> c2o.geometry/1

Ownership (REDESIGN_DECISIONS.md ruling 5): placement is the Structures & configuration
seat's (``seats.yaml`` structures_engineer owns ``structure.*``). Anyone who may edit
proposes; only that seat (or its fallback when the study does not use it, or the
instructor) approves. Until approval the approved layout - and the positions it wrote -
stand. Studies without seats are open: anyone approves.

The approved layout also feeds the rule engines: ``cds_stack_checks`` adds the STACK-*
results to the CDS compliance matrix (services/cds_checks.py) and ``stack_gate_check``
is GC-STACK at PDR (services/gate_checks.py).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..services import rule_config as rc
from ..services import stack_builder as sb

logger = logging.getLogger(__name__)
router = APIRouter()

STRUCTURES_SEAT = "structures_engineer"

#: study id -> {"form_factor", "approved", "proposal", "version"}; write-through to stack_layouts.
#: The dict lives in the service so the CDS / gate hooks can read it without importing routers.
_layouts: dict[str, dict[str, Any]] = sb.LAYOUT_CACHE


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ───────────────────────────────────────────────────────────── persistence

async def _load(study_id: str) -> dict[str, Any]:
    if study_id in _layouts:
        return _layouts[study_id]
    lay: dict[str, Any] = {"form_factor": "", "approved": None, "proposal": None, "version": 0}
    try:
        from ..db.engine import get_session_factory
        from ..db.models import StackLayoutRow
        async with get_session_factory()() as s:
            row = await s.get(StackLayoutRow, study_id)
            if row is not None:
                lay = {"form_factor": row.form_factor or "", "approved": row.approved_json,
                       "proposal": row.proposal_json, "version": int(row.version or 0)}
    except Exception:  # noqa: BLE001 — DB unavailable: start empty, never crash the view
        logger.warning("stack layout load failed for %s", study_id, exc_info=True)
    _layouts[study_id] = lay
    return lay


async def _save(study_id: str, lay: dict[str, Any]) -> None:
    lay["version"] = int(lay.get("version") or 0) + 1
    _layouts[study_id] = lay
    try:
        from ..db.engine import get_session_factory
        from ..db.models import StackLayoutRow
        async with get_session_factory()() as s:
            row = await s.get(StackLayoutRow, study_id)
            if row is None:
                row = StackLayoutRow(study_id=study_id)
                s.add(row)
            row.form_factor = lay.get("form_factor") or ""
            row.approved_json = lay.get("approved")
            row.proposal_json = lay.get("proposal")
            row.version = lay["version"]
            await s.commit()
    except Exception:  # noqa: BLE001
        logger.warning("stack layout save failed for %s", study_id, exc_info=True)
    try:
        from .ws import _broadcast_study
        await _broadcast_study(study_id, {"type": "stack_updated", "version": lay["version"]})
    except Exception:  # noqa: BLE001
        logger.debug("stack broadcast failed", exc_info=True)


async def init_stack_cache() -> None:
    """Load every stored layout (app start-up), so the CDS and gate hooks see them."""
    from sqlalchemy import select

    from ..db.engine import get_session_factory
    from ..db.models import StackLayoutRow
    async with get_session_factory()() as s:
        for row in (await s.execute(select(StackLayoutRow))).scalars():
            _layouts[row.study_id] = {"form_factor": row.form_factor or "", "approved": row.approved_json,
                                      "proposal": row.proposal_json, "version": int(row.version or 0)}


def reset_stack_cache() -> None:
    _layouts.clear()


# ───────────────────────────────────────────────────────────── context

async def _context(study_id: str, form_factor: str | None) -> dict[str, Any]:
    from ..services.rule_inputs import param
    from . import rules as rules_router
    ctx = await rules_router._context(study_id, form_factor)
    lay = await _load(study_id)
    ff = ctx["form_factor"] or lay.get("form_factor") or None
    # one CubeSat per layout: the primary spacecraft when the space segment holds several
    from ..services.product_tree import primary_spacecraft, scope_to_spacecraft, spacecraft_systems
    from ..services.rule_inputs import form_factor as find_form_factor
    scs = spacecraft_systems(ctx["elements"])
    sc = primary_spacecraft(ctx["elements"])
    ctx["spacecraft"] = ({"id": sc["id"], "name": sc.get("name"), "count": len(scs)} if sc else None)
    if len(scs) > 1:
        ctx["elements"] = scope_to_spacecraft(ctx["elements"])
        ff = find_form_factor(ctx["elements"], ctx["params"], form_factor) or lay.get("form_factor") or None
    ctx["layout"] = lay
    ctx["ff"] = ff
    alt = param(ctx["params"], "orbit.altitude_km")
    if alt is None and ctx.get("study") is not None:
        req = getattr(ctx["study"], "requirements", None)
        orbit = getattr(req, "orbit", None) if req is not None else None
        alt = getattr(orbit, "altitude_km", None) if orbit is not None else None
    ctx["alt_km"] = float(alt) if isinstance(alt, (int, float)) else None
    return ctx


def _applicable(ff: str | None) -> bool:
    return sb.applicable(ff)


def _evaluate(entry: dict | None, units: list[dict], env: dict, ctx: dict) -> dict | None:
    if not entry:
        return None
    spec, notes = sb.normalise_spec(entry.get("spec") or {}, units, env)
    spec["origins"] = (entry.get("spec") or {}).get("origins") or {}
    real = sb.evaluate(spec, units, env, interfaces=ctx["interfaces"], orbit_alt_km=ctx["alt_km"])
    real["notes"] = notes
    real["meta"] = {k: entry.get(k) for k in ("origin", "by", "seat", "at", "report", "approved_by",
                                              "approved_seat", "approved_at", "form_factor")}
    real["positions_m"] = sb.design_positions(real, units, env)
    return real


async def _may_approve(request: Request | None, study_id: str) -> tuple[bool, str | None]:
    """(allowed, owner seat) — the Structures seat, its fallback, or the instructor."""
    from ..seats import config as seat_cfg
    from ..seats.service import seat_ctx, used_seats
    ctx = await seat_ctx(request, study_id)
    if not ctx.enabled:
        return True, None
    owner = seat_cfg.resolve_in_study(STRUCTURES_SEAT, used_seats(ctx.state)) or STRUCTURES_SEAT
    return (ctx.instructor or ctx.holds(owner)), owner


async def _actor(request: Request | None, study_id: str) -> tuple[str, str, Any]:
    from ..seats.service import seat_ctx
    try:
        ctx = await seat_ctx(request, study_id)
    except Exception:  # noqa: BLE001
        return "", "", None
    seat = ctx.active or ("instructor" if ctx.instructor else "")
    return (ctx.person.name or ctx.person.id or ""), seat, ctx


async def _log(request: Request, study_id: str, action: str, detail: dict[str, Any]) -> None:
    from ..seats import store as seat_store
    _, seat, ctx = await _actor(request, study_id)
    if ctx is None or not ctx.enabled:
        return
    await seat_store.log_event(study_id, seat, ctx.person, action, "stack layout", detail)
    try:
        request.state.seat_logged = True
    except Exception:  # noqa: BLE001
        pass


async def _payload(study_id: str, request: Request | None, form_factor: str | None = None) -> dict[str, Any]:
    ctx = await _context(study_id, form_factor)
    lay = ctx["layout"]
    ff = ctx["ff"]
    may, owner = await _may_approve(request, study_id)
    from ..seats import config as seat_cfg
    owner_label = seat_cfg.label(owner or STRUCTURES_SEAT)
    base = {"study_id": study_id, "form_factor": ff, "version": lay.get("version", 0), "can_approve": may,
            "owner_seat": owner or STRUCTURES_SEAT, "owner_label": owner_label, "frame": dict(sb.FRAME_NOTE),
            "spacecraft": ctx.get("spacecraft")}
    if not _applicable(ff):
        return {**base, "applicable": False, "approved": None, "proposal": None, "units": [],
                "reason": {"en": "Not a CubeSat form factor: pick a CubeSat structure from the KB (or set structure.form_factor_u).",
                           "fr": "Pas un facteur de forme CubeSat : choisir une structure CubeSat dans la base (ou structure.form_factor_u)."}}
    env = sb.envelope(ff)
    units = sb.collect_units(ctx["elements"])
    return {**base, "applicable": True, "envelope": env,
            "units": [{"id": u["id"], "name": u["name"], "role": u["role"], "subsystem": u["subsystem"],
                       "mount_class": u["mech"]["mount_class"], "source": u["mech"]["source"],
                       "assumptions": u["mech"]["assumptions"], "mass_kg": u["mass_kg"], "power_w": u["power_w"],
                       "quantity": u["quantity"], "manufacturer": u.get("manufacturer")} for u in units],
            "approved": _evaluate(lay.get("approved"), units, env, ctx),
            "proposal": _evaluate(lay.get("proposal"), units, env, ctx)}


# ───────────────────────────────────────────────────────────── routes

class AutoPlaceBody(BaseModel):
    form_factor: str | None = None


class SpecBody(BaseModel):
    spec: dict[str, Any]
    base_version: int | None = None
    form_factor: str | None = None


@router.get("/studies/{study_id}/stack")
async def get_stack(study_id: str, request: Request, form_factor: str | None = Query(None)) -> dict:
    return await _payload(study_id, request, form_factor)


@router.post("/studies/{study_id}/stack/auto-place")
async def auto_place(study_id: str, request: Request, body: AutoPlaceBody | None = None) -> dict:
    ff_q = (body.form_factor if body else None)
    ctx = await _context(study_id, ff_q)
    if not _applicable(ctx["ff"]):
        raise HTTPException(409, {"code": "not_a_cubesat", "message": "Not a CubeSat form factor"})
    lay = dict(ctx["layout"])
    env = sb.envelope(ctx["ff"])
    units = sb.collect_units(ctx["elements"])
    if not units:
        raise HTTPException(409, {"code": "nothing_to_place", "message": "No space hardware to place yet"})
    prev = (lay.get("proposal") or lay.get("approved") or {}).get("spec")
    spec, report = sb.auto_place(units, env, prev, ctx["interfaces"])
    by, seat, _ = await _actor(request, study_id)
    lay["form_factor"] = ctx["ff"]
    lay["proposal"] = {"spec": spec, "origin": sb.AUTO_ORIGIN, "by": by, "seat": seat, "at": _now(),
                       "report": report, "form_factor": ctx["ff"]}
    await _save(study_id, lay)
    await _log(request, study_id, "propose", {"kind": "stack_layout", "origin": sb.AUTO_ORIGIN,
                                               "score": report["end"]["total"]})
    return await _payload(study_id, request, ff_q)


@router.put("/studies/{study_id}/stack/proposal")
async def put_proposal(study_id: str, body: SpecBody, request: Request) -> dict:
    ctx = await _context(study_id, body.form_factor)
    if not _applicable(ctx["ff"]):
        raise HTTPException(409, {"code": "not_a_cubesat", "message": "Not a CubeSat form factor"})
    lay = dict(ctx["layout"])
    if body.base_version is not None and body.base_version != lay.get("version", 0):
        raise HTTPException(409, {"code": "version_conflict", "current_version": lay.get("version", 0)})
    env = sb.envelope(ctx["ff"])
    units = sb.collect_units(ctx["elements"])
    spec, notes = sb.normalise_spec(body.spec, units, env)
    prev = (lay.get("proposal") or lay.get("approved") or {})
    origins = dict(((prev.get("spec") or {}).get("origins")) or {})
    old_where = _where_map((prev.get("spec") or {}))
    for pid, w in _where_map(spec).items():       # what the user moved is theirs now
        if old_where.get(pid) != w:
            origins[pid] = "user"
    spec["origins"] = origins
    by, seat, _ = await _actor(request, study_id)
    lay["form_factor"] = ctx["ff"]
    lay["proposal"] = {"spec": spec, "origin": "user", "by": by, "seat": seat, "at": _now(),
                       "report": (prev.get("report") if prev else None), "form_factor": ctx["ff"]}
    await _save(study_id, lay)
    await _log(request, study_id, "propose", {"kind": "stack_layout", "origin": "user", "notes": notes})
    return await _payload(study_id, request, body.form_factor)


def _where_map(spec: dict) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for ci, col in enumerate(spec.get("columns") or []):
        for si, p in enumerate(col):
            out[p] = ("c", ci, si)
    for a in ("nadir", "zenith"):
        for si, p in enumerate((spec.get("layers") or {}).get(a) or []):
            out[p] = ("l", a, si)
    for eid, groups in (spec.get("faces") or {}).items():
        for g in groups:
            out[f"{eid}@{g['face']}"] = ("f", g["face"], g.get("count"))
    for p, v in (spec.get("locks") or {}).items():
        if v and p in out:
            out[p] = (*out[p], "locked")
    return out


@router.post("/studies/{study_id}/stack/preview")
async def preview(study_id: str, body: SpecBody) -> dict:
    ctx = await _context(study_id, body.form_factor)
    if not _applicable(ctx["ff"]):
        raise HTTPException(409, {"code": "not_a_cubesat", "message": "Not a CubeSat form factor"})
    env = sb.envelope(ctx["ff"])
    units = sb.collect_units(ctx["elements"])
    return _evaluate({"spec": body.spec, "origin": "preview"}, units, env, ctx) or {}


@router.post("/studies/{study_id}/stack/approve")
async def approve(study_id: str, request: Request) -> dict:
    may, owner = await _may_approve(request, study_id)
    if not may:
        from ..seats import config as seat_cfg
        raise HTTPException(403, {"code": "structures_only",
                                  "message": f"Only {seat_cfg.label(owner)['en']} or the instructor approves the stack layout",
                                  "owner_seat": owner, "owner_label": seat_cfg.label(owner)})
    ctx = await _context(study_id, None)
    lay = dict(ctx["layout"])
    if not lay.get("proposal"):
        raise HTTPException(409, {"code": "no_proposal", "message": "No stack proposal to approve"})
    ff = lay["proposal"].get("form_factor") or ctx["ff"]
    env = sb.envelope(ff)
    units = sb.collect_units(ctx["elements"])
    real = _evaluate(lay["proposal"], units, env, ctx)
    positions = real["positions_m"]
    from .elements import _elements, apply_element_update
    written = 0
    for eid, pos in positions.items():
        el = _elements.get(eid)
        if el is None or el.get("deleted_at"):
            continue
        if el.get("position_json") != pos:
            await apply_element_update(el, {"position_json": pos})
            written += 1
    by, seat, _ = await _actor(request, study_id)
    prop = dict(lay["proposal"])
    prop["spec"] = {**real["spec"], "origins": (prop.get("spec") or {}).get("origins") or {}}
    prop.update({"approved_by": by, "approved_seat": seat, "approved_at": _now()})
    lay["approved"] = prop
    lay["proposal"] = None
    lay["form_factor"] = ff
    await _save(study_id, lay)
    await _log(request, study_id, "accept", {"kind": "stack_layout", "positions_written": written,
                                              "checks": real["summary"]})
    out = await _payload(study_id, request, None)
    out["positions_written"] = written
    return out


@router.post("/studies/{study_id}/stack/reject")
async def reject(study_id: str, request: Request) -> dict:
    ctx = await _context(study_id, None)
    lay = dict(ctx["layout"])
    if not lay.get("proposal"):
        raise HTTPException(409, {"code": "no_proposal", "message": "No stack proposal to discard"})
    may, _ = await _may_approve(request, study_id)
    by, seat, _c = await _actor(request, study_id)
    mine = (lay["proposal"].get("seat") or "") == seat and seat
    if not (may or mine):
        raise HTTPException(403, {"code": "structures_only", "message": "Only Structures or the proposer discards a proposal"})
    lay["proposal"] = None
    await _save(study_id, lay)
    await _log(request, study_id, "reject", {"kind": "stack_layout"})
    return await _payload(study_id, request, None)


async def study_geometry(study_id: str, which: str = "approved") -> dict | None:
    """The c2o.geometry/1 document of the study's stack layout, or None (not a CubeSat, or
    no layout of that kind). Shared by the route below and the simulator export."""
    ctx = await _context(study_id, None)
    if not _applicable(ctx["ff"]):
        return None
    lay = ctx["layout"]
    entry = lay.get("proposal") if which == "proposal" else lay.get("approved")
    if which == "current":
        entry = lay.get("proposal") or lay.get("approved")
    if not entry:
        return None
    env = sb.envelope(entry.get("form_factor") or ctx["ff"])
    units = sb.collect_units(ctx["elements"])
    real = _evaluate(entry, units, env, ctx)
    name = ""
    if ctx.get("study") is not None:
        name = getattr(ctx["study"], "name", "") or ""
    return sb.to_geometry(real, units, env, name)


@router.get("/studies/{study_id}/stack/geometry")
async def geometry(study_id: str, which: str = Query("approved", pattern="^(approved|proposal|current)$"),
                   format: str = Query("json", pattern="^(json|yaml)$")):
    ctx = await _context(study_id, None)
    if not _applicable(ctx["ff"]):
        raise HTTPException(409, {"code": "not_a_cubesat", "message": "Not a CubeSat form factor"})
    geo = await study_geometry(study_id, which)
    if geo is None:
        raise HTTPException(404, f"No {which} stack layout")
    if format == "yaml":
        import yaml
        head = ("# c2o.geometry/1 written by the SpaceCDF stack builder (design/docs/STACK_BUILDER.md).\n"
                f"# Frame: {sb.FRAME_NOTE['stack']}.\n"
                "# frame / internal / mass_properties are the additive stack-builder keys.\n")
        return PlainTextResponse(head + yaml.safe_dump(geo, sort_keys=False, allow_unicode=True),
                                 media_type="application/x-yaml",
                                 headers={"Content-Disposition": f'attachment; filename="geometry_{study_id}.yaml"'})
    return geo


# rule-engine hooks (CDS matrix, GC-STACK) live in services/stack_builder.py and read LAYOUT_CACHE
cds_stack_checks = sb.cds_stack_checks
stack_gate_check = sb.stack_gate_check
