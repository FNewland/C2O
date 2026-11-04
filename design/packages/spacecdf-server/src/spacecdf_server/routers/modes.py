"""SpaceCDF — mode model, budgets per mode and the proposal rules (Nov 2026).

Mounted under ``/api``:

Mode machine (modes are ``mode`` design elements; ConOps attributes in their ``performance``)
* ``GET    /studies/{sid}/modes``                         modes, transitions, matrix, units, findings
* ``POST   /studies/{sid}/modes/template``                create the ConOps set (LEOP … survival) or
                                                          import the study ConOps modes once (``source=conops``)
* ``POST   /studies/{sid}/modes``                         add a mode
* ``PATCH  /studies/{sid}/modes/{mode_id}``               name, kind, phase, pointing, sunlit_only, orbit_fraction, initial
* ``DELETE /studies/{sid}/modes/{mode_id}``
* ``POST   /studies/{sid}/mode-transitions``              add a transition {from_mode_id, to_mode_id, trigger, guard}
* ``PATCH/DELETE /studies/{sid}/mode-transitions/{tid}``

Mode × element matrix (rules MO-01 / EB-02 / EB-03 / EB-05)
* ``POST   /studies/{sid}/modes/propose``                 propose power state, W, data rate per unit and mode
* ``PUT    /studies/{sid}/modes/{mode_id}/members/{eid}`` edit a cell, or {action: accept|reject}
* ``POST   /studies/{sid}/modes/members/accept-all``

Budgets
* ``GET /studies/{sid}/modes/energy``       per-mode power with margins, energy per orbit, DoD, ops orbit, duty
* ``GET /studies/{sid}/modes/data-chain``   generation → storage → downlink capacity (contact plan, link rate)
* ``GET /studies/{sid}/modes/dissipation``  heat per unit per mode, hot/cold case values used by the thermal analysis
* ``GET /studies/{sid}/budgets/equipment``  equipment selection → mass, power by mode, data, cost, heat, link

Rules → proposals (rules 7, 8, 9, 13)
* ``POST /studies/{sid}/design-rules/run``                FDIR monitor/action stubs, risks, heaters
* ``GET  /studies/{sid}/design-rules/proposals``          ?kind=monitor|action|risk|heater
* ``POST /studies/{sid}/design-rules/proposals/{pid}/{accept|reject}``
* ``GET  /studies/{sid}/heaters``
* ``GET  /studies/{sid}/kb-staleness``, ``POST /studies/{sid}/kb-staleness/mark``, ``POST /elements/{eid}/kb-refresh``
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..db import mode_repo
from ..services import mode_model as mm
from ..services import rule_config as rc

logger = logging.getLogger(__name__)
router = APIRouter()

MODE_ATTRS = ("mode_kind", "phase", "pointing", "sunlit_only", "orbit_fraction", "initial", "order", "template_key")


# ───────────────────────────────────────────────────────────── helpers

def _els(study_id: str) -> list[dict]:
    from .elements import _elements
    return [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]


def _study(study_id: str):
    from .studies import get_study_store
    return get_study_store().get(study_id)


def _modes(els: list[dict]) -> list[dict]:
    ms = [e for e in els if e.get("element_type") == "mode"]
    def order(m: dict) -> float:
        o = (m.get("performance") or {}).get("order")
        return float(o) if isinstance(o, (int, float)) else 999.0
    return sorted(ms, key=lambda m: (order(m), m.get("name") or ""))


def _mode_public(m: dict) -> dict:
    p = m.get("performance") or {}
    return {"id": m["id"], "name": m.get("name"), "description": m.get("description") or "", "version": m.get("version"),
            "kind": p.get("mode_kind") or "custom", "phase": p.get("phase") or "", "pointing": p.get("pointing") or "nadir",
            "sunlit_only": bool(p.get("sunlit_only")), "orbit_fraction": p.get("orbit_fraction"),
            "initial": bool(p.get("initial")), "order": p.get("order"), "template_key": p.get("template_key")}


def _parent_for_modes(els: list[dict]) -> str | None:
    for t in ("system", "mission"):
        cands = [e for e in els if e.get("element_type") == t and (e.get("segment") or "space") == "space"]
        if cands:
            return cands[0]["id"]
    return None


async def _broadcast(study_id: str, what: str) -> None:
    try:
        from .ws import _broadcast_study
        await _broadcast_study(study_id, {"type": "modes_changed", "study_id": study_id, "what": what})
    except Exception:  # noqa: BLE001
        logger.debug("broadcast failed", exc_info=True)


def _guard() -> None:
    errs = mm.validate_config()
    if errs:
        raise HTTPException(status_code=500, detail={"code": "mode_rules_invalid", "errors": errs})


def _wrap(fn):
    try:
        return fn()
    except rc.RuleConfigError as exc:
        raise HTTPException(status_code=500, detail={"code": "rule_config_invalid", "errors": str(exc)}) from exc


async def _create_mode(study_id: str, name: str, attrs: dict, description: str = "", parent_id: str | None = None) -> dict:
    from .elements import ElementCreate, create_element
    body = ElementCreate(name=name, element_type="mode", parent_id=parent_id, description=description,
                         performance={k: v for k, v in attrs.items() if k in MODE_ATTRS})
    return await create_element(body, study_id=study_id)


def _check_mode(study_id: str, mode_id: str) -> dict:
    from .elements import _elements
    m = _elements.get(mode_id)
    if not m or m.get("deleted_at") or m.get("study_id") != study_id or m.get("element_type") != "mode":
        raise HTTPException(404, f"Mode {mode_id} not found in study {study_id}")
    return m


# ───────────────────────────────────────────────────────────── overview

@router.get("/studies/{study_id}/modes")
async def get_modes(study_id: str, lang: str = Query("en")) -> dict:
    """The mode machine, the mode × element matrix and the findings on both."""
    _guard()
    els = _els(study_id)
    if _study(study_id) is None and not els:
        raise HTTPException(404, f"Study {study_id} not found")
    modes = _modes(els)
    trans = await mode_repo.list_transitions(study_id)
    members = await mode_repo.list_members([m["id"] for m in modes])
    units = mm.proposal_units(els)
    proposals = await mode_repo.list_proposals(study_id, "monitor")
    monitors = {p["id"] for p in proposals if p["status"] in ("accepted", "edited")}
    c = mm.cfg()
    return {
        "study_id": study_id,
        "modes": [_mode_public(m) for m in modes],
        "transitions": trans,
        "members": members,
        "units": [{"id": u["id"], "name": u.get("name"), "domain": u.get("subsystem_domain"),
                   "unit_class": mm.unit_class(u, c), "power_avg_w": u.get("power_avg_w"),
                   "power_peak_w": u.get("power_peak_w"), "quantity": u.get("quantity") or 1,
                   "kb_component_id": u.get("kb_component_id"), "stale": bool((u.get("kb_spec") or {}).get("stale"))}
                  for u in units],
        "findings": mm.validate_machine(modes, trans, monitors),
        "vocabulary": {"kinds": c["mode_kinds"], "triggers": c["trigger_kinds"], "pointing": c["pointing_kinds"],
                       "states": list(mm.STATES)},
        "template_ref": mm.ref(c["template"], c),
        "states_ref": mm.ref(c["states"], c),
    }


class TemplateBody(BaseModel):
    source: str = "template"     # template | conops
    replace: bool = False
    lang: str = "en"             # language of the mode names and descriptions created (data, not UI)


@router.post("/studies/{study_id}/modes/template")
async def create_template(study_id: str, body: TemplateBody | None = None) -> dict:
    """Create the seven ConOps modes and their transitions (or import the study ConOps modes once)."""
    _guard()
    body = body or TemplateBody()
    els = _els(study_id)
    existing = _modes(els)
    if existing and not body.replace:
        raise HTTPException(409, {"code": "modes_exist", "message": "The study already has modes; pass replace=true."})
    if existing and body.replace:
        from .elements import delete_element
        for m in existing:
            await mode_repo.delete_members(m["id"])
            await mode_repo.delete_transitions_of_mode(study_id, m["id"])
            await delete_element(m["id"])
    parent = _parent_for_modes(_els(study_id))
    c = mm.cfg()
    created: dict[str, dict] = {}
    if body.source == "conops":
        study = _study(study_id)
        ops = getattr(study, "conops", None)
        if ops is None or not getattr(ops, "modes", None):
            raise HTTPException(400, "The study has no ConOps modes to import.")
        kind_map = {"safe": "safe", "commissioning": "commissioning", "nominal_science": "imaging", "peak_science": "imaging",
                    "downlink": "downlink", "launch": "leop", "standby": "nominal", "calibration": "custom"}
        for i, om in enumerate(ops.modes):
            kind = kind_map.get(getattr(om.mode_type, "value", str(om.mode_type)), "custom")
            attrs = {"mode_kind": kind, "phase": "nominal", "pointing": "nadir" if om.nadir_pointing else "sun",
                     "sunlit_only": bool(om.sun_illuminated and om.payload_active),
                     "orbit_fraction": round(float(om.duty_cycle_percent or 0) / 100, 4), "order": i,
                     "initial": i == 0, "template_key": f"conops:{om.id or om.name}"}
            created[om.id or om.name] = await _create_mode(study_id, om.name or om.id, attrs, om.description, parent)
    else:
        for i, t in enumerate(c["template"]["modes"]):
            attrs = {"mode_kind": t["kind"], "phase": t["phase"], "pointing": t["pointing"],
                     "sunlit_only": bool(t.get("sunlit_only")), "orbit_fraction": t.get("orbit_fraction"),
                     "initial": bool(t.get("initial")), "order": i, "template_key": t["key"]}
            lang = "fr" if body.lang == "fr" else "en"
            created[t["key"]] = await _create_mode(study_id, t["name"][lang], attrs, t["description"][lang], parent)
        for t in c["template"]["transitions"]:
            await mode_repo.create_transition(study_id, {
                "from_mode_id": created[t["from"]]["id"], "to_mode_id": created[t["to"]]["id"], "trigger": t["trigger"],
                "guard": t.get("guard") or {}, "origin": "template"})
    await _broadcast(study_id, "template")
    return {"created": [_mode_public(m) for m in created.values()], "source": body.source}


class ModeBody(BaseModel):
    name: str | None = None
    description: str | None = None
    kind: str | None = None
    phase: str | None = None
    pointing: str | None = None
    sunlit_only: bool | None = None
    orbit_fraction: float | None = Field(None, ge=0, le=1)
    initial: bool | None = None
    order: float | None = None


def _attrs_from(body: ModeBody, c: dict) -> dict:
    a: dict[str, Any] = {}
    if body.kind is not None:
        if body.kind not in c["mode_kinds"]:
            raise HTTPException(400, f"Unknown mode kind {body.kind}")
        a["mode_kind"] = body.kind
    if body.pointing is not None:
        if body.pointing not in c["pointing_kinds"]:
            raise HTTPException(400, f"Unknown pointing {body.pointing}")
        a["pointing"] = body.pointing
    for k in ("phase", "sunlit_only", "orbit_fraction", "initial", "order"):
        v = getattr(body, k)
        if v is not None:
            a[k] = v
    return a


@router.post("/studies/{study_id}/modes")
async def add_mode(study_id: str, body: ModeBody) -> dict:
    _guard()
    c = mm.cfg()
    attrs = {"mode_kind": "custom", "pointing": "nadir", "phase": "nominal", "orbit_fraction": 0.0,
             "order": len(_modes(_els(study_id))), **_attrs_from(body, c)}
    m = await _create_mode(study_id, (body.name or "").strip() or "New mode", attrs, body.description or "",
                           _parent_for_modes(_els(study_id)))
    await _broadcast(study_id, "mode")
    return _mode_public(m)


@router.patch("/studies/{study_id}/modes/{mode_id}")
async def patch_mode(study_id: str, mode_id: str, body: ModeBody) -> dict:
    from .elements import apply_element_update
    _guard()
    m = _check_mode(study_id, mode_id)
    attrs = _attrs_from(body, mm.cfg())
    upd: dict[str, Any] = {}
    if attrs:
        upd["performance"] = {**(m.get("performance") or {}), **attrs}
    if body.name is not None and body.name.strip():
        upd["name"] = body.name.strip()
    if body.description is not None:
        upd["description"] = body.description
    if body.initial:
        for other in _modes(_els(study_id)):   # one initial mode
            if other["id"] != mode_id and (other.get("performance") or {}).get("initial"):
                await apply_element_update(other, {"performance": {**other["performance"], "initial": False}})
    if upd:
        m = await apply_element_update(m, upd)
    await _broadcast(study_id, "mode")
    return _mode_public(m)


@router.delete("/studies/{study_id}/modes/{mode_id}")
async def delete_mode(study_id: str, mode_id: str) -> dict:
    from .elements import delete_element
    _check_mode(study_id, mode_id)
    await mode_repo.delete_members(mode_id)
    await mode_repo.delete_transitions_of_mode(study_id, mode_id)
    await delete_element(mode_id)
    await _broadcast(study_id, "mode")
    return {"deleted": mode_id}


class TransitionBody(BaseModel):
    from_mode_id: str | None = None
    to_mode_id: str | None = None
    trigger: str | None = None
    guard: dict[str, Any] | None = None
    monitor_ref: str | None = None
    priority: int | None = None
    description: str | None = None


def _check_transition(study_id: str, body: TransitionBody, c: dict) -> None:
    for mid in (body.from_mode_id, body.to_mode_id):
        if mid is not None:
            _check_mode(study_id, mid)
    if body.trigger is not None and body.trigger not in c["trigger_kinds"]:
        raise HTTPException(400, f"Unknown trigger {body.trigger}")
    if body.from_mode_id and body.from_mode_id == body.to_mode_id:
        raise HTTPException(400, "A transition needs two different modes")


@router.post("/studies/{study_id}/mode-transitions")
async def add_transition(study_id: str, body: TransitionBody) -> dict:
    c = mm.cfg()
    if not body.from_mode_id or not body.to_mode_id:
        raise HTTPException(400, "from_mode_id and to_mode_id are required")
    _check_transition(study_id, body, c)
    t = await mode_repo.create_transition(study_id, body.model_dump(exclude_none=True))
    await _broadcast(study_id, "transition")
    return t


@router.patch("/studies/{study_id}/mode-transitions/{tid}")
async def patch_transition(study_id: str, tid: str, body: TransitionBody) -> dict:
    _check_transition(study_id, body, mm.cfg())
    t = await mode_repo.update_transition(tid, body.model_dump(exclude_none=True))
    if t is None or t["study_id"] != study_id:
        raise HTTPException(404, f"Transition {tid} not found")
    await _broadcast(study_id, "transition")
    return t


@router.delete("/studies/{study_id}/mode-transitions/{tid}")
async def remove_transition(study_id: str, tid: str) -> dict:
    if not await mode_repo.delete_transition(tid):
        raise HTTPException(404, f"Transition {tid} not found")
    await _broadcast(study_id, "transition")
    return {"deleted": tid}


# ───────────────────────────────────────────────────────────── mode × element matrix

@router.post("/studies/{study_id}/modes/propose")
async def propose_members(study_id: str) -> dict:
    """MO-01: propose (or refresh) every unit's state, power and data rate in every mode.

    Life cycle per cell: new → suggested; suggested → refreshed when its inputs changed;
    accepted/edited by a rule → stale when its inputs (KB part, power, quantity…) changed;
    rejected and user-made cells are left alone.
    """
    _guard()
    els = _els(study_id)
    modes = _modes(els)
    if not modes:
        raise HTTPException(400, {"code": "no_modes", "message": "Create the modes first (POST …/modes/template)."})
    units = mm.proposal_units(els)
    existing = {(r["mode_id"], r["element_id"]): r for r in await mode_repo.list_members([m["id"] for m in modes])}
    c = mm.cfg()
    counts = {"new": 0, "refreshed": 0, "stale": 0, "kept": 0}
    for m in modes:
        kind = (m.get("performance") or {}).get("mode_kind") or "custom"
        for u in units:
            p = mm.propose_member(u, kind, c)
            fields = {"power_state": p["power_state"], "power_w_in_mode": p["power_w_in_mode"],
                      "duty_cycle_percent": p["duty_cycle_percent"], "data_rate_bps": p["data_rate_bps"],
                      "source_ref": p["source_ref"], "inputs_hash": p["inputs_hash"], "is_active": True,
                      "notes": p["rationale"]["en"]}
            cur = existing.get((m["id"], u["id"]))
            if cur is None:
                await mode_repo.upsert_member(m["id"], u["id"], {**fields, "origin": "rule:MO-01", "status": "suggested"})
                counts["new"] += 1
            elif cur.get("origin") != "rule:MO-01" or cur.get("status") == "rejected" or cur.get("inputs_hash") == p["inputs_hash"]:
                counts["kept"] += 1
            elif cur.get("status") == "suggested":
                await mode_repo.upsert_member(m["id"], u["id"], fields)
                counts["refreshed"] += 1
            elif cur.get("status") != "stale":
                await mode_repo.upsert_member(m["id"], u["id"], {"status": "stale"})
                counts["stale"] += 1
            else:
                counts["kept"] += 1
    await _broadcast(study_id, "members")
    return {"counts": counts, "modes": len(modes), "units": len(units), **mm.ref(c["states"], c)}


class MemberBody(BaseModel):
    action: str | None = None              # accept | reject | edit (default when values are sent)
    power_w_in_mode: float | None = Field(None, ge=0)
    duty_cycle_percent: float | None = Field(None, ge=0, le=100)
    power_state: str | None = None
    data_rate_bps: float | None = Field(None, ge=0)
    dissipation_w: float | None = Field(None, ge=0)
    clear_dissipation: bool = False


@router.put("/studies/{study_id}/modes/{mode_id}/members/{element_id}")
async def put_member(study_id: str, mode_id: str, element_id: str, body: MemberBody) -> dict:
    from .elements import _elements
    _check_mode(study_id, mode_id)
    if element_id not in _elements:
        raise HTTPException(404, f"Element {element_id} not found")
    if body.power_state is not None and body.power_state not in mm.STATES:
        raise HTTPException(400, f"Unknown power state {body.power_state}")
    fields: dict[str, Any] = {k: v for k, v in body.model_dump(exclude={"action", "clear_dissipation"}).items()
                              if v is not None}
    if body.clear_dissipation:
        fields["dissipation_w"] = None
    if body.action == "accept":
        fields["status"] = "accepted"
    elif body.action == "reject":
        fields["status"] = "rejected"
    elif fields:
        fields["status"] = "edited"
        if body.power_state == "off" and body.power_w_in_mode is None:
            fields["power_w_in_mode"] = 0.0
    row = await mode_repo.upsert_member(mode_id, element_id, fields)
    await _broadcast(study_id, "members")
    return row


@router.post("/studies/{study_id}/modes/members/accept-all")
async def accept_all(study_id: str) -> dict:
    modes = _modes(_els(study_id))
    n = 0
    for r in await mode_repo.list_members([m["id"] for m in modes]):
        if r.get("status") in ("suggested", "stale"):
            await mode_repo.upsert_member(r["mode_id"], r["element_id"], {"status": "accepted"})
            n += 1
    await _broadcast(study_id, "members")
    return {"accepted": n}


# ───────────────────────────────────────────────────────────── budgets per mode

async def _ctx(study_id: str):
    from ..services.analysis_context import build_context
    if _study(study_id) is None and not _els(study_id):
        raise HTTPException(404, f"Study {study_id} not found")
    return await build_context(study_id)


def _element_modes(ctx) -> list:
    return [m for m in ctx.modes if m.source == "element"]


def _power_sources(ctx) -> tuple[float | None, str, float | None, str]:
    """(EOL array W, its source, battery Wh, its source) from the design parameters or the parts."""
    from ..services.rule_inputs import kb_component, perf, qty, space_hardware
    sa = ctx.power.get("sa_power_eol_w")
    sa_src = "power.sa_power_eol_w" if sa else ""
    bat = ctx.power.get("battery_capacity_wh")
    bat_src = "power.battery_capacity_wh" if bat else ""
    if not sa or not bat:
        sa_sum = bat_sum = 0.0
        for e in space_hardware(ctx.elements):
            kp = (kb_component(e) or {}).get("performance") or {}
            pe = perf(e)
            for src in (pe, kp):
                v = src.get("power_eol_w")
                if isinstance(v, (int, float)) and v > 0:
                    sa_sum += float(v) * qty(e)
                    break
            for src in (pe, kp):
                v = src.get("capacity_wh")
                if isinstance(v, (int, float)) and v > 0:
                    bat_sum += float(v) * qty(e)
                    break
        if not sa and sa_sum:
            sa, sa_src = sa_sum, "solar array parts (power_eol_w)"
        if not bat and bat_sum:
            bat, bat_src = bat_sum, "battery parts (capacity_wh)"
    return sa, sa_src, bat, bat_src


@router.get("/studies/{study_id}/modes/energy")
async def mode_energy(study_id: str, gate: str | None = Query(None)) -> dict:
    """MO-02: per-mode power with maturity and system margins, energy per orbit, DoD, operational orbit."""
    from ..services.margin_policy import convention, system_margin_percent
    from .gates import study_margin_gate
    _guard()
    ctx = await _ctx(study_id)
    g = gate or study_margin_gate(ctx.study)
    sys_p = system_margin_percent(g, "power")
    sa, sa_src, bat, bat_src = _power_sources(ctx)
    res = _wrap(lambda: mm.energy_balance(
        _element_modes(ctx), ctx.elements, period_s=ctx.orbit.get("period_s") or 5700.0,
        eclipse_fraction=ctx.orbit.get("eclipse_fraction"), sa_power_eol_w=sa, battery_wh=bat,
        system_margin_percent=sys_p, battery_efficiency=None,
        max_dod_percent=ctx.power.get("battery_dod_percent")))
    res["inputs"].update({"sa_power_source": sa_src, "battery_source": bat_src,
                          "altitude_km": ctx.orbit.get("altitude_km")})
    return {"study_id": study_id, "system_margin": {"gate": g, "percent": sys_p, **convention()}, **res}


def _station_rows(ctx, link, warnings: list[str]) -> list[dict]:
    from ..services import ground_closure as gc
    rows = []
    altitude = float(ctx.orbit.get("altitude_km") or 500.0)
    orbit = gc.OrbitParams(altitude_km=altitude, inclination_deg=float(ctx.orbit.get("inclination_deg") or 97.4),
                           period_s=float(ctx.orbit.get("period_s") or 0.0))
    rate_mbps = link.downlink_bps / 1e6
    for s in gc._pick_stations(ctx, warnings):
        gs = gc.station_to_ground_station(s, link.band)
        bands = [gc._band_key(str(b)) for b in (s.get("bands") or [gs.band])]
        minutes, n = gc._contact_minutes(orbit, gs, rate_mbps)
        row = {"name": gs.name, "contacts_per_day": n, "contact_min_per_day": round(minutes, 2), "margin_db": None,
               "bands": bands, "status": "ok"}
        if link.band not in bands:
            row.update(status="excluded", margin_db=None, contact_min_per_day=0.0)
        else:
            margin, _gt = gc._station_margin_db(link, gs, gc._num(s.get("g_over_t_db_k")), altitude, minutes * 60.0)
            row["margin_db"] = round(margin, 2)
        rows.append(row)
    if not rows and ctx.orbit.get("contact_time_per_day_s"):
        rows.append({"name": "orbit.contact_time_per_day_s", "contact_min_per_day": ctx.orbit["contact_time_per_day_s"] / 60,
                     "margin_db": None, "status": "ok"})
    return rows


@router.get("/studies/{study_id}/modes/data-chain")
async def mode_data_chain(study_id: str) -> dict:
    """EB-03 / MO-03: data generated per mode and per day, storage need vs capacity, downlink capacity."""
    from ..services import ground_closure as gc
    from ..services.margin_policy import CONFIG as MP
    _guard()
    ctx = await _ctx(study_id)
    warnings: list[str] = []
    link = gc._link_inputs(ctx, warnings)
    if link.source.get("downlink_rate") == "fallback":
        # no link rate in the parameters: use the selected transmitter's rate (KB part / element)
        from ..services.rule_inputs import kb_component, perf
        best = None
        for e in mm.proposal_units(ctx.elements):
            if mm.unit_class(e) != "transmitter":
                continue
            r = perf(e).get("data_rate_bps") or ((kb_component(e) or {}).get("performance") or {}).get("data_rate_bps")
            if isinstance(r, (int, float)) and r > 0 and (best is None or r > best[0]):
                best = (float(r), e.get("name"))
        if best:
            link.downlink_bps = best[0]
            link.source["downlink_rate"] = f"transmitter part ({best[1]})"
            warnings[:] = [w for w in warnings if "no downlink rate" not in w]
    stations = _station_rows(ctx, link, warnings)
    cap, used = mm.storage_capacity_gb(ctx.elements)
    smargin = float(rc.load(MP)["data_handling"]["storage_margin_percent"]["value"])
    res = _wrap(lambda: mm.data_chain(_element_modes(ctx), period_s=ctx.orbit.get("period_s") or 5700.0,
                                      link_rate_bps=link.downlink_bps, stations=stations, storage_gb=cap,
                                      storage_margin_percent=smargin))
    res["downlink"].update({"band": link.band, "rate_source": link.source.get("downlink_rate")})
    res["storage"]["elements"] = used
    return {"study_id": study_id, **res, "warnings": warnings}


@router.get("/studies/{study_id}/modes/dissipation")
async def mode_dissipation(study_id: str) -> dict:
    """EB-05: heat per unit per mode and the hot / cold case values the thermal analysis uses."""
    ctx = await _ctx(study_id)
    modes = _element_modes(ctx)
    cases = _wrap(lambda: mm.dissipation_cases(ctx.elements, modes))
    by_id = ctx.elements_by_id
    return {"study_id": study_id, "modes": [{"id": m.id, "name": m.name, "kind": m.kind} for m in modes],
            "units": [{"element_id": k, "name": (by_id.get(k) or {}).get("name"), **v} for k, v in cases.items()],
            "rf_out_ref": mm.ref(mm.cfg()["thermal"]["rf_out_fraction_default"])}


@router.get("/studies/{study_id}/budgets/equipment")
async def equipment_budgets(study_id: str, gate: str | None = Query(None)) -> dict:
    """Equipment selection → every budget, with maturity margins (margin_policy) and the gate's system margin."""
    from ..services.rule_inputs import kb_component, perf
    from .gates import study_margin_gate
    _guard()
    ctx = await _ctx(study_id)
    g = gate or study_margin_gate(ctx.study)
    link_rows: dict[str, dict] = {}
    for e in mm.proposal_units(ctx.elements):
        if mm.unit_class(e) == "transmitter":
            kb = kb_component(e) or {}
            kp = kb.get("performance") or {}
            link_rows[e["id"]] = {"tx_power_w": perf(e).get("tx_power_w") or kp.get("tx_power_w"),
                                  "data_rate_bps": perf(e).get("data_rate_bps") or kp.get("data_rate_bps"),
                                  "band": kb.get("frequency_band") or perf(e).get("band")}
    res = _wrap(lambda: mm.equipment_budgets(ctx.elements, _element_modes(ctx), gate=g, link_rows=link_rows))
    return {"study_id": study_id, **res}


# ───────────────────────────────────────────────────────────── rules → proposals

@router.post("/studies/{study_id}/design-rules/run")
async def run_design_rules(study_id: str, thermal: bool = Query(True)) -> dict:
    """Rules 7, 8, 9: FDIR monitor/action stubs, risk entries, heater proposals (stored as proposals)."""
    from ..services.fmeca_library import build_skeleton
    from ..services.mode_rules import fdir_proposals, heater_proposals, monitored_element_ids, risk_proposals
    from .elements import active_interfaces
    from .requirements import _requirements, ensure_requirements_loaded
    _guard()
    els = _els(study_id)
    if _study(study_id) is None and not els:
        raise HTTPException(404, f"Study {study_id} not found")
    existing = await mode_repo.list_proposals(study_id)
    monitored = monitored_element_ids(existing)
    fmeca = _wrap(lambda: build_skeleton(els, active_interfaces(study_id), monitored=monitored))
    safe = next((m["id"] for m in _modes(els) if (m.get("performance") or {}).get("mode_kind") == "safe"), None)
    try:
        await ensure_requirements_loaded()
    except Exception:  # noqa: BLE001
        pass
    reqs = [r for r in _requirements.values() if r.get("study_id") == study_id]
    props = _wrap(lambda: fdir_proposals(fmeca["rows"], els, safe_mode_id=safe) + risk_proposals(fmeca["rows"], reqs))
    rule_ids = {"FD-01", "FD-02", "FD-03", "RV-04"}
    thermal_note = None
    if thermal:
        try:
            from ..services.physics_closure import run_thermal_closure
            ctx = await _ctx(study_id)
            th = run_thermal_closure(ctx)
            cases = mm.dissipation_cases(ctx.elements, _element_modes(ctx))
            off = {eid for eid, row in cases.items() if float(row.get("cold_w") or 0) <= 0}
            props += heater_proposals(th.nodes, th.conductances, ctx.elements,
                                      emissivity=float(th.inputs.get("emissivity") or 0.85), off_in_cold=off)
            rule_ids.add("EI-05")
            thermal_note = {"nodes": len(th.nodes), "worst_margin_c": th.worst_margin_c,
                            "dissipation_source": th.inputs.get("dissipation_source")}
        except Exception:  # noqa: BLE001 — no thermal network yet: the other rules still run
            logger.exception("thermal closure for heater proposals failed (%s)", study_id)
            thermal_note = {"error": "thermal analysis unavailable"}
    counts = await mode_repo.upsert_proposals(study_id, props, rule_ids=rule_ids)
    await _broadcast(study_id, "proposals")
    return {"counts": counts, "fmeca_summary": fmeca["summary"], "detection_basis": "monitor", "thermal": thermal_note,
            "proposals": await mode_repo.list_proposals(study_id)}


@router.get("/studies/{study_id}/design-rules/proposals")
async def list_rule_proposals(study_id: str, kind: str | None = Query(None)) -> dict:
    from ..services.mode_rules import rules_ref
    return {"study_id": study_id, "proposals": await mode_repo.list_proposals(study_id, kind), "refs": rules_ref()}


async def _accept_risk(study_id: str, p: dict) -> str:
    from .gates import _clean_risk, _next_risk_id
    from .gates import _save as save_study
    study = _study(study_id)
    if study is None:
        raise HTTPException(404, f"Study {study_id} not found")
    risks = list(study.risk_register or [])
    src = p["payload"].get("source")
    hit = next((r for r in risks if r.get("source") == src), None)
    if hit:
        return hit["id"]
    r = _clean_risk(p["payload"], _next_risk_id(risks))
    study.risk_register = [*risks, r]
    await save_study(study)
    try:
        from .gates import _broadcast as gb
        await gb(study_id, "study_records_changed", {"kind": "risks"})
    except Exception:  # noqa: BLE001
        pass
    return r["id"]


async def _accept_heater(study_id: str, p: dict) -> str:
    from .elements import ElementCreate, _elements, create_element
    pl = p["payload"]
    target = _elements.get(pl["element_id"]) or {}
    els = _els(study_id)
    thermal = next((e for e in els if e.get("element_type") == "subsystem" and e.get("subsystem_domain") == "thermal"), None)
    parent = (thermal or {}).get("id") or target.get("parent_id") or target.get("id")
    el = await create_element(ElementCreate(
        name=pl["name"], element_type="component", parent_id=parent, subsystem_domain="thermal",
        power_avg_w=pl["power_w"], power_peak_w=pl["power_w"], mass_kg=0.01, trl=9,
        description=f"Thermostat on {pl['on_c']:g} / off {pl['off_c']:g} °C (rule EI-05)",
        performance={"heater_for": pl["element_id"], "on_c": pl["on_c"], "off_c": pl["off_c"], "control": pl.get("control", "auto"),
                     "maturity_category": "B"}), study_id=study_id)
    h = await mode_repo.create_heater(study_id, {**pl, "heater_element_id": el["id"], "proposal_id": p["id"]})
    return h["id"]


@router.post("/studies/{study_id}/design-rules/proposals/{pid}/{action}")
async def decide_proposal(study_id: str, pid: str, action: str) -> dict:
    p = await mode_repo.get_proposal(pid)
    if p is None or p["study_id"] != study_id:
        raise HTTPException(404, f"Proposal {pid} not found")
    if action == "reject":
        out = await mode_repo.set_proposal_status(pid, "rejected")
    elif action == "accept":
        ref_id = p.get("result_ref") or None
        if p["kind"] == "risk" and not ref_id:
            ref_id = await _accept_risk(study_id, p)
        elif p["kind"] == "heater" and not ref_id:
            ref_id = await _accept_heater(study_id, p)
        out = await mode_repo.set_proposal_status(pid, "accepted", result_ref=ref_id)
    else:
        raise HTTPException(400, "action must be accept or reject")
    await _broadcast(study_id, "proposals")
    return out or {}


@router.get("/studies/{study_id}/heaters")
async def list_heaters(study_id: str) -> list[dict]:
    return await mode_repo.list_heaters(study_id)


# ───────────────────────────────────────────────────────────── rule 13: KB staleness

@router.get("/studies/{study_id}/kb-staleness")
async def kb_staleness(study_id: str) -> dict:
    from ..services.kb_copy import staleness
    rows = staleness(_els(study_id))
    return {"study_id": study_id, "stale": rows, "count": len(rows)}


@router.post("/studies/{study_id}/kb-staleness/mark")
async def mark_stale(study_id: str) -> dict:
    """Mark every element whose KB part changed as stale (``kb_spec.stale``) for its owner to review."""
    from ..db.element_repo import db_update_element
    from ..services.kb_copy import staleness
    from .elements import _elements
    marked = []
    for row in staleness(_els(study_id)):
        if row["reason"] not in ("kb_changed", "kb_part_missing"):
            continue
        e = _elements[row["element_id"]]
        spec = dict(e.get("kb_spec") or {})
        if not spec.get("stale"):
            spec.update(stale=True, stale_reason=row["reason"], stale_fields=row.get("changed") or [])
            e["kb_spec"] = spec
            await db_update_element(e["id"], e)
            marked.append(e["id"])
    await _broadcast(study_id, "staleness")
    return {"marked": marked}


@router.post("/elements/{element_id}/kb-refresh")
async def kb_refresh(element_id: str) -> dict:
    """Re-apply the element's KB part (F4 copy) and clear the stale flag."""
    from ..services.kb_copy import apply_to_element, find_kb_part
    from .elements import _elements, apply_element_update
    e = _elements.get(element_id)
    if not e or e.get("deleted_at"):
        raise HTTPException(404, f"Element {element_id} not found")
    part = find_kb_part(e.get("kb_component_id") or "")
    if part is None:
        raise HTTPException(400, "The element has no KB part (or it is gone from the KB).")
    name = e.get("name")
    apply_to_element(e, part, overwrite=True)
    e["name"] = name           # keep the designer's name
    e = await apply_element_update(e, {"trl": e.get("trl")})
    return e
