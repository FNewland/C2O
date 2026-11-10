"""ConOps Executor API — SCDF-201.

Provides REST endpoint to simulate spacecraft operations through orbit(s).
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..services.conops_executor import (
    ConOpsMode,
    ModeGuard,
    OrbitParams,
    PowerParams,
    ThermalParams,
    TimeSeriesResult,
    simulate_orbit,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ModeSchema(BaseModel):
    name: str
    power_draw_w: float
    pointing: str = "nadir"
    data_rate_bps: float = 0.0
    is_payload_active: bool = False


class GuardSchema(BaseModel):
    condition: str
    target_mode: str
    priority: int = 0


class OrbitParamsSchema(BaseModel):
    altitude_km: float = 550.0
    inclination_deg: float = 97.5
    eclipse_fraction: float = 0.35
    period_s: float = 5800.0
    contact_time_per_orbit_s: float = 600.0


class PowerParamsSchema(BaseModel):
    sa_power_eol_w: float = 60.0
    battery_capacity_wh: float = 40.0
    heater_power_w: float = 5.0


class ThermalParamsSchema(BaseModel):
    capacitance_j_per_k: float = 5000.0
    radiator_area_m2: float = 0.04
    emissivity: float = 0.85
    absorptivity: float = 0.3
    internal_dissipation_fraction: float = 0.6
    solar_flux_w_m2: float = 1361.0
    initial_temp_c: float = 20.0


class SimulateRequest(BaseModel):
    orbit_params: Optional[OrbitParamsSchema] = None
    power_params: Optional[PowerParamsSchema] = None
    thermal_params: Optional[ThermalParamsSchema] = None
    modes: Optional[List[ModeSchema]] = None
    guards: Optional[List[GuardSchema]] = None
    duration_hours: Optional[float] = None
    mode_schedule: Optional[List[Dict[str, Any]]] = None


class SimulateResponse(BaseModel):
    time_s: List[float]
    mode: List[str]
    soc_pct: List[float]
    temp_c: List[float]
    data_buffer_mbit: List[float]
    events: List[Dict[str, Any]]
    summary: Dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/simulate", response_model=SimulateResponse)
async def simulate_conops(req: SimulateRequest) -> SimulateResponse:
    """Simulate spacecraft ConOps through one or more orbits.

    All parameters are optional — sensible defaults are used for a typical
    LEO Earth-observation mission if not provided.
    """
    # Convert Pydantic models to dataclass instances
    orbit = OrbitParams(**req.orbit_params.model_dump()) if req.orbit_params else None
    power = PowerParams(**req.power_params.model_dump()) if req.power_params else None
    thermal = ThermalParams(**req.thermal_params.model_dump()) if req.thermal_params else None

    modes_dc = None
    if req.modes:
        modes_dc = [ConOpsMode(**m.model_dump()) for m in req.modes]

    guards_dc = None
    if req.guards:
        guards_dc = [ModeGuard(**g.model_dump()) for g in req.guards]

    duration_s = None
    if req.duration_hours is not None:
        duration_s = req.duration_hours * 3600.0

    result: TimeSeriesResult = simulate_orbit(
        modes=modes_dc,
        guards=guards_dc,
        orbit_params=orbit,
        power_params=power,
        thermal_params=thermal,
        duration_s=duration_s,
        mode_schedule=req.mode_schedule,
    )

    # Compute summary statistics
    summary = {
        "min_soc_pct": round(min(result.soc_pct), 2) if result.soc_pct else None,
        "max_soc_pct": round(max(result.soc_pct), 2) if result.soc_pct else None,
        "min_temp_c": round(min(result.temp_c), 2) if result.temp_c else None,
        "max_temp_c": round(max(result.temp_c), 2) if result.temp_c else None,
        "max_data_buffer_mbit": round(max(result.data_buffer_mbit), 3) if result.data_buffer_mbit else None,
        "num_events": len(result.events),
        "num_guard_triggers": sum(1 for e in result.events if e["type"] == "guard_trigger"),
        "duration_s": result.time_s[-1] if result.time_s else 0,
    }

    return SimulateResponse(
        time_s=result.time_s,
        mode=result.mode,
        soc_pct=result.soc_pct,
        temp_c=result.temp_c,
        data_buffer_mbit=result.data_buffer_mbit,
        events=result.events,
        summary=summary,
    )


# ═══════════════════════════════════════════════════════════════════════════
# W7 (Nov 2026): the study's ConOps — editable phases, the view built from the Modes tab and
# the ConOps document. Mounted under /api by routers/gates.py (``study_router``).
# ═══════════════════════════════════════════════════════════════════════════

study_router = APIRouter()

PHASE_TYPES = ("leop", "commissioning", "transfer", "nominal", "extended", "disposal")
#: Modes-tab ``phase`` values each mission-phase type shows (a mode of phase "any" shows in every phase)
_PHASE_MODES = {"leop": ("leop",), "commissioning": ("commissioning",), "transfer": ("nominal",),
                "nominal": ("nominal",), "extended": ("nominal",), "disposal": ("disposal",)}


class PhaseIn(BaseModel):
    id: str = Field("", max_length=40)
    name: str = Field(..., min_length=1, max_length=120)
    phase_type: str = "nominal"
    duration_days: float = Field(0.0, ge=0, le=36500)
    description: str = Field("", max_length=4000)
    entry_criteria: str = Field("", max_length=2000)
    exit_criteria: str = Field("", max_length=2000)
    modes: List[str] = Field(default_factory=list, max_length=50)
    primary_mode: str = Field("", max_length=64)


class PhasesBody(BaseModel):
    phases: List[PhaseIn] = Field(default_factory=list, max_length=20)


def _study(study_id: str):
    from .gates import _study_or_404
    return _study_or_404(study_id)


def _phase_dicts(study) -> List[Dict[str, Any]]:
    out = []
    for p in getattr(study.conops, "phases", None) or []:
        d = p.model_dump(mode="json")
        d["phase_type"] = str(d.get("phase_type") or "nominal")
        out.append(d)
    return out


def phase_template(study) -> List[Dict[str, Any]]:
    """Suggested phases for a LEO small satellite (EOSAT/NFI pattern: LEOP about a week, platform
    commissioning to day 30, payload commissioning to day 90, operations, disposal), sized
    from the study's mission duration. Not saved."""
    years = float(getattr(study.requirements.orbit, "mission_duration_years", 0) or study.requirements.design_lifetime_years or 2)
    ops_days = max(round(years * 365.25 - 90), 30)
    return [
        {"id": "leop", "name": "LEOP", "phase_type": "leop", "duration_days": 7,
         "entry_criteria": "Separation from the deployer", "exit_criteria": "Power-positive, two-way link, attitude stable",
         "description": "Separation, antenna deployment, beacon, detumble, first contacts, orbit identification"},
        {"id": "platform_commissioning", "name": "Platform commissioning", "phase_type": "commissioning",
         "duration_days": 23, "entry_criteria": "LEOP exit criteria met", "exit_criteria": "All subsystems nominal",
         "description": "Attitude control calibration, navigation, time synchronisation, link-rate tests, power and thermal trending"},
        {"id": "payload_commissioning", "name": "Payload commissioning", "phase_type": "commissioning",
         "duration_days": 60, "entry_criteria": "Platform commissioned", "exit_criteria": "Level-1 products meet the payload requirements",
         "description": "Dark frames, first light, calibration and validation"},
        {"id": "nominal", "name": "Nominal operations", "phase_type": "nominal", "duration_days": ops_days,
         "entry_criteria": "Payload commissioned", "exit_criteria": "Mission objectives met, decision to dispose",
         "description": "Routine acquisitions and data return"},
        {"id": "disposal", "name": "End of life / disposal", "phase_type": "disposal", "duration_days": 0,
         "entry_criteria": "Decision to dispose, or the disposal timer expires",
         "exit_criteria": "Transmitters off, batteries passivated, re-entry",
         "description": "Disposal device deployed, decay confirmed, passivation"},
    ]


@study_router.get("/studies/{study_id}/conops/phases")
async def get_phases(study_id: str) -> dict:
    study = _study(study_id)
    return {"study_id": study_id, "edited": bool(study.conops.phases_edited), "phases": _phase_dicts(study),
            "template": phase_template(study), "phase_types": list(PHASE_TYPES)}


@study_router.put("/studies/{study_id}/conops/phases")
async def put_phases(study_id: str, body: PhasesBody) -> dict:
    """Replace the mission phases (W7.01): durations, entry and exit criteria, modes. The ConOps
    regenerated from a mission-definition change never overwrites them again."""
    from fastapi import HTTPException
    from spacecdf_common.models.conops import MissionPhase
    study = _study(study_id)
    phases = []
    seen: set = set()
    for i, p in enumerate(body.phases):
        if p.phase_type not in PHASE_TYPES:
            raise HTTPException(422, f"phase_type must be one of {', '.join(PHASE_TYPES)}")
        pid = (p.id or "").strip() or f"phase-{i + 1}"
        if pid in seen:
            pid = f"{pid}-{i + 1}"
        seen.add(pid)
        phases.append(MissionPhase(**{**p.model_dump(), "id": pid}))
    study.conops = study.conops.model_copy(update={"phases": phases, "phases_edited": True})
    from .gates import _broadcast, _save
    await _save(study)
    await _broadcast(study_id, "study_records_changed", {"kind": "conops_phases"})
    return {"study_id": study_id, "edited": True, "phases": _phase_dicts(study)}


# ─── wave 3 (3.D5): operational scenarios for requirements validation ──────────

SCENARIO_KINDS = ("nominal", "degraded", "contingency", "end_of_life")


class ScenarioIn(BaseModel):
    id: str = Field("", max_length=24)
    name: str = Field("", max_length=300)
    kind: str = "nominal"
    phase_id: str = Field("", max_length=64)
    description: str = Field("", max_length=4000)
    requirement_codes: List[str] = Field(default_factory=list, max_length=200)
    modes: List[str] = Field(default_factory=list, max_length=30)


class ScenariosBody(BaseModel):
    scenarios: List[ScenarioIn] = Field(default_factory=list, max_length=60)


def scenario_kind(name: str) -> str:
    """A kind from the scenario's words (import of ``vv_plan.yaml``, which has none)."""
    n = (name or "").lower()
    if any(w in n for w in ("end of life", "disposal", "end-of-life", "deorbit")):
        return "end_of_life"
    if any(w in n for w in ("safe", "failure", "out for", "anomal", "stop transmissions", "regulator", "embargo",
                            "data-governance request")):
        return "contingency" if any(w in n for w in ("regulator", "embargo", "governance")) else "degraded"
    return "nominal"


def _scenario_dicts(study) -> List[Dict[str, Any]]:
    return [x.model_dump(mode="json") for x in getattr(study.conops, "scenarios", None) or []]


async def _requirement_codes(study_id: str) -> Dict[str, Dict[str, Any]]:
    try:
        from .requirements import _ensure_loaded, _requirements
        await _ensure_loaded()
        return {r["code"]: r for r in _requirements.values() if r.get("study_id") == study_id and r.get("code")}
    except Exception:  # noqa: BLE001
        return {}


async def scenarios_view(study_id: str, study=None) -> Dict[str, Any]:
    """The scenarios with each requirement resolved (code, text, found) and the counts."""
    study = study or _study(study_id)
    reqs = await _requirement_codes(study_id)
    items = []
    for sc in _scenario_dicts(study):
        rows = [{"code": c, "found": c in reqs, "text": (reqs.get(c) or {}).get("text") or "",
                 "level": (reqs.get(c) or {}).get("level") or ""} for c in sc["requirement_codes"]]
        items.append({**sc, "requirements": rows, "missing": [r["code"] for r in rows if not r["found"]]})
    by_kind = {k: sum(1 for i in items if i["kind"] == k) for k in SCENARIO_KINDS}
    covered = sorted({r["code"] for i in items for r in i["requirements"] if r["found"]})
    return {"study_id": study_id, "items": items, "kinds": list(SCENARIO_KINDS),
            "counts": {"total": len(items), "with_requirements": sum(1 for i in items if i["requirements"]),
                       "requirements_covered": len(covered), "by_kind": by_kind}}


def _clean_scenarios(raw: List[ScenarioIn]):
    from fastapi import HTTPException
    from spacecdf_common.models.conops import ConopsScenario
    out, seen = [], set()
    for i, sc in enumerate(raw):
        kind = sc.kind if sc.kind in SCENARIO_KINDS else None
        if kind is None:
            raise HTTPException(422, f"kind must be one of {', '.join(SCENARIO_KINDS)}")
        sid = (sc.id or "").strip() or f"S{i + 1}"
        if sid in seen:
            raise HTTPException(422, f"duplicate scenario id {sid}")
        seen.add(sid)
        codes = list(dict.fromkeys(c.strip() for c in sc.requirement_codes if c and c.strip()))
        out.append(ConopsScenario(**{**sc.model_dump(), "id": sid, "requirement_codes": codes}))
    return out


@study_router.get("/studies/{study_id}/conops/scenarios")
async def get_scenarios(study_id: str) -> dict:
    return await scenarios_view(study_id)


@study_router.put("/studies/{study_id}/conops/scenarios")
async def put_scenarios(study_id: str, body: ScenariosBody) -> dict:
    """Replace the operational scenarios (3.D5): id, name, kind, phase, requirement codes."""
    study = _study(study_id)
    study.conops = study.conops.model_copy(update={"scenarios": _clean_scenarios(body.scenarios)})
    from .gates import _broadcast, _save
    await _save(study)
    await _broadcast(study_id, "study_records_changed", {"kind": "conops_scenarios"})
    return await scenarios_view(study_id, study)


class ScenarioImport(BaseModel):
    scenarios: List[Dict[str, Any]] = Field(default_factory=list, max_length=60)
    replace: bool = False


@study_router.post("/studies/{study_id}/conops/scenarios/import")
async def import_scenarios(study_id: str, body: ScenarioImport) -> dict:
    """Scenarios in the ``vv_plan.yaml`` form (``id``, ``scenario``, ``requirements``) in one call;
    the kind is read from the name unless given. Existing ids are kept unless ``replace``."""
    study = _study(study_id)
    have = {s.id: s for s in getattr(study.conops, "scenarios", None) or []}
    raw = []
    for x in body.scenarios:
        if not isinstance(x, dict):
            continue
        name = str(x.get("name") or x.get("scenario") or "")
        raw.append(ScenarioIn(id=str(x.get("id") or ""), name=name, kind=x.get("kind") or scenario_kind(name),
                              phase_id=str(x.get("phase_id") or ""), description=str(x.get("description") or ""),
                              requirement_codes=list(x.get("requirement_codes") or x.get("requirements") or []),
                              modes=list(x.get("modes") or [])))
    new = _clean_scenarios(raw)
    merged = dict(have)
    added = []
    for sc in new:
        if sc.id in merged and not body.replace:
            continue
        merged[sc.id] = sc
        added.append(sc.id)
    study.conops = study.conops.model_copy(update={"scenarios": list(merged.values())})
    from .gates import _broadcast, _save
    await _save(study)
    await _broadcast(study_id, "study_records_changed", {"kind": "conops_scenarios"})
    return {"added": added, **await scenarios_view(study_id, study)}


def scenario_count(study) -> int:
    """MDR-EC-06 evidence (R wires it): the number of operational scenarios with ≥ 1 requirement."""
    return sum(1 for s in getattr(getattr(study, "conops", None), "scenarios", None) or [] if s.requirement_codes)


def _text(v: Any, lang: str) -> str:
    if isinstance(v, dict):
        return str(v.get(lang) or v.get("en") or "")
    return str(v or "")


def _num(v: Any) -> Any:
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def data_flow_section(sx, lang: str = "en") -> Dict[str, Any]:
    """The ConOps data flow and downlink allocation (W7.02), read from the ``data_budget``
    section (agent H's ``services/data_budget.py``); nothing here computes a data number.

    ``status`` is ``open`` while the study has no data budget (no closure), else ``ready`` with:
    ``volume`` (payload products, compression, the science delivered and on the channel per
    day), ``capacity`` (union and usable contact minutes, MB per day), ``closure`` (the baseline
    case: demand by stream against capacity, margin and the required margin), ``cases`` (every
    closure case), ``allocation`` (the pass classes: passes per day, usable minutes, real-time HK
    profile, VC order), ``stores`` (size, days held in the nominal mix, check) and ``backlog``."""
    db = getattr(sx, "data_budget", None) or {}
    link = (getattr(sx, "links", None) or {}).get("design_case") or {}
    out: Dict[str, Any] = {"downlink_rate_bps": link.get("downlink_rate_bps"),
                           "uplink_rate_bps": link.get("uplink_rate_bps"),
                           "band": link.get("band") or (db.get("link") or {}).get("band")}
    daily = db.get("daily") or {}
    closure = daily.get("closure") or {}
    if not db or db.get("status") in ("not_implemented", "empty") or not closure:
        return {**out, "status": "open", "owner": db.get("owner", "H"),
                "work_package": db.get("work_package", "W3.02/W3.05")}
    # the section (H, wave 2) carries ``science``/``capacity``/``cases`` at its top level and the
    # flat closure figures in ``daily``; older payloads nested them in ``daily`` — read either
    sci = db.get("science") or daily.get("science") or {}
    cap = dict(db.get("capacity") or daily.get("capacity") or {})
    if cap.get("capacity_mb_per_day") is None:
        cap["capacity_mb_per_day"] = daily.get("capacity_mb_per_day")
    req_margin = _num(daily.get("margin_required_percent"))
    #: export case key (``sections/data_budget.CASE_KEYS``) -> the data-budget case key used here
    export_keys = {"capacity_mb": "capacity", "demand_mb": "demand", "science_mb": "science", "rt_hk_mb": "rt_hk",
                   "stored_hk_mb": "stored_hk", "other_mb": "other", "margin_pct": "margin_pct"}

    def case(c: dict) -> Dict[str, Any]:
        return {"id": c.get("id"), "label": _text(c.get("label"), lang), "baseline": c.get("id") == closure.get("id"),
                **{k: _num(c.get(k)) if c.get(k) is not None else _num(c.get(ek)) for k, ek in export_keys.items()},
                "status": c.get("status")}

    stores = []
    for st in db.get("stores") or []:
        chk = st.get("check") or {}
        stores.append({"id": st.get("id"), "name": st.get("name"),
                       "size_mb": _num(st.get("size_mb")) if st.get("size_mb") is not None
                       else (_num(st.get("size_gb")) or 0) * 1000 or None,
                       "days_held": _num((st.get("days_held") or {}).get("nominal_mix")),
                       "fill_mb_per_day": _num((st.get("fill_mb_per_day") or {}).get("nominal_mix")),
                       "ok": chk.get("ok") if chk else None})
    backlog = db.get("backlog") or {}
    return {**out, "status": "ready",
            "volume": {k: _num(sci.get(k)) for k in ("raw_mb_per_day", "compression_ratio", "compression_needed",
                                                     "target_mb_per_day", "delivered_mb_per_day",
                                                     "on_channel_mb_per_day", "cfdp_efficiency")}
            | {"compression_ok": sci.get("compression_ok"),
               "products": [{"name": p.get("name"), "per_day": _num(p.get("per_day")), "mb_raw": _num(p.get("mb_raw")),
                             "mb_per_day_raw": _num(p.get("mb_per_day_raw")), "priority": p.get("priority")}
                            for p in sci.get("products") or []]},
            "capacity": {k: _num(cap.get(k)) for k in ("union_min_per_day", "usable_min_per_day", "raw_mb_per_day",
                                                       "capacity_mb_per_day")},
            "closure": {**case(closure), "margin_required_pct": req_margin},
            "daily": {k: v for k, v in daily.items() if k != "closure"},
            "cases": [case(c) for c in (db.get("cases") or daily.get("cases") or []) if isinstance(c, dict)],
            "allocation": [{"name": pc.get("name"), "per_day": _num(pc.get("per_day")),
                            "usable_min_per_day": _num(pc.get("usable_min_per_day")), "rt_profile": pc.get("rt_profile"),
                            "rt_mb_per_day": _num(pc.get("rt_mb_per_day")), "order": list(pc.get("order") or []),
                            "delayed_hk": pc.get("delayed_hk")} for pc in db.get("pass_classes") or []],
            "stores": stores,
            "backlog": {"growing": backlog.get("growing"), "days": len(backlog.get("days") or []),
                        "last_vc1_mb": _num((backlog.get("vc1_mb") or [None])[-1]),
                        "last_vc2_mb": _num((backlog.get("vc2_mb") or [None])[-1])} if backlog else {},
            "warnings": [_text(w, lang) for w in db.get("warnings") or []]}


async def conops_view(study_id: str, lang: str = "en", sx=None) -> Dict[str, Any]:
    """The ConOps built from the study (W7.02): the Modes tab (modes, transitions, power by
    mode), the edited phases, the mission need's ConOps summary, the contact statistics, the
    data flow (hook above), a typical day, the flight rules and FDIR of the CDR model, and the
    end-of-life operations from the disposal phase, modes and requirements."""
    from ..services.export_context import collect
    study = _study(study_id)
    if sx is None:
        sx = await collect(study_id, lang=lang, sections=["need", "mission", "requirements", "modes", "links",
                                                         "contacts", "data_budget"])
    modes_sec = sx.modes or {}
    modes = modes_sec.get("modes") or []
    energy = modes_sec.get("energy") or {}
    by_id = {m["id"]: m for m in modes}
    epw = {e.get("mode_id"): e for e in (energy.get("modes") or [])}
    mode_rows = []
    for m in modes:
        e = epw.get(m["id"]) or {}
        mode_rows.append({"id": m["id"], "name": m.get("name"), "kind": m.get("kind"), "phase": m.get("phase"),
                          "pointing": m.get("pointing"), "sunlit_only": bool(m.get("sunlit_only")),
                          "initial": bool(m.get("initial")), "orbit_fraction": m.get("orbit_fraction"),
                          "description": m.get("description") or "",
                          "power_cbe_w": e.get("power_cbe_w"), "power_total_w": e.get("power_total_w"),
                          "dod_percent": e.get("dod_percent"), "energy_status": e.get("status")})
    transitions = []
    for t in modes_sec.get("transitions") or []:
        g = t.get("guard") or {}
        transitions.append({"from": (by_id.get(t.get("from_mode_id")) or {}).get("name", t.get("from_mode_id")),
                            "to": (by_id.get(t.get("to_mode_id")) or {}).get("name", t.get("to_mode_id")),
                            "trigger": t.get("trigger"), "guard": g.get("text") if isinstance(g, dict) else str(g or ""),
                            "description": t.get("description") or ""})
    phases = _phase_dicts(study)
    for p in phases:
        if not p.get("modes"):
            kinds = _PHASE_MODES.get(p["phase_type"], ())
            p["modes"] = [m["name"] for m in modes if m.get("phase") in kinds or m.get("phase") == "any"]
        else:
            p["modes"] = [(by_id.get(x) or {}).get("name", x) for x in p["modes"]]
    orbit = energy.get("orbit") or {}
    period_s = float(orbit.get("period_s") or 0) or None
    mix = [m for m in mode_rows if m["phase"] == "nominal" and (m["orbit_fraction"] or 0) < 1]
    typical = {"period_min": round(period_s / 60, 2) if period_s else None,
               "orbits_per_day": round(86400 / period_s, 2) if period_s else None,
               "eclipse_min": round(float(orbit.get("eclipse_s") or 0) / 60, 1) if orbit.get("eclipse_s") else None,
               "mode_minutes": [{"mode": m["name"], "share_pct": round(100 * float(m["orbit_fraction"] or 0), 1),
                                 "min_per_day": round(1440 * float(m["orbit_fraction"] or 0), 1)} for m in mix],
               "contacts": sx.contacts if (sx.contacts or {}).get("status") != "not_implemented" else None}
    rows: Dict[str, list] = {}
    try:
        from ..db import cdr_repo
        from ..services import cdr_model as cm
        all_rows = await cdr_repo.list_rows(study_id)
        for kind in ("flight_rules", "event_actions", "safe_mode", "load_shed", "monitors"):
            rows[kind] = cm.live_data(all_rows, kind)
    except Exception:  # noqa: BLE001 — no CDR model yet
        rows = {}
    flight_rules = sorted(({"id": r.get("rule_id") or r.get("_id"), "text": _text(r.get("text"), lang),
                            "ref": r.get("ref") or ""} for r in rows.get("flight_rules") or []),
                          key=lambda r: str(r["id"]))
    contingencies = []
    for ea in rows.get("event_actions") or []:
        trig = ea.get("trigger") or {}
        contingencies.append({"name": ea.get("name"), "trigger": trig.get("monitor") or trig.get("parameter") or "",
                              "action": ea.get("action") or "", "level": ea.get("level")})
    safe = (rows.get("safe_mode") or [{}])[0] if rows.get("safe_mode") else {}
    reqs = (sx.requirements or {}).get("items") or []
    disposal_reqs = [{"code": r.get("code"), "text": r.get("text")} for r in reqs
                     if str(r.get("code") or "").startswith(("DIS-", "MIS-DIS", "REG-DEB"))]
    req_def = (sx.mission or {}).get("definition") or {}
    eol = {"phase": next((p for p in phases if p["phase_type"] == "disposal"), None),
           "modes": [m for m in mode_rows if m["phase"] == "disposal"],
           "disposal_method": req_def.get("disposal_method"),
           "constraints": {k: v for k, v in (req_def.get("constraints") or {}).items()
                           if k.startswith(("disposal", "collision", "apogee"))},
           "requirements": disposal_reqs}
    need = sx.need or {}
    scen = await scenarios_view(study_id, study)
    return {"study_id": study_id, "study_name": study.name, "lang": lang, "scenarios": scen["items"],
            "scenario_counts": scen["counts"],
            "summary": need.get("conops_summary") or "",
            "success_criteria": need.get("success_criteria") or [],
            "orbit": (sx.mission or {}).get("orbit") or {}, "phases": phases, "phases_edited": bool(study.conops.phases_edited),
            "modes": mode_rows, "transitions": transitions,
            "operational_orbit": energy.get("operational_orbit"), "energy_warnings": energy.get("warnings") or [],
            "typical_day": typical, "data_flow": data_flow_section(sx, lang),
            "link": (sx.links or {}).get("design_case") or {},
            "ground_stations": list(req_def.get("ground_stations") or []),
            "flight_rules": flight_rules, "contingencies": contingencies,
            "safe_mode": {"entry": safe.get("entry") or [], "exit": _text((safe.get("exit") or {}).get("condition"), lang),
                          "payload_off": safe.get("payload_off")} if safe else None,
            "eol": eol}


@study_router.get("/studies/{study_id}/conops")
async def get_conops(study_id: str, lang: str = "en") -> dict:
    return await conops_view(study_id, lang=lang)


@study_router.post("/studies/{study_id}/conops/document")
async def conops_document(study_id: str, lang: str = "en"):
    """The ConOps (.docx) built from the study: Modes tab, phases, ConOps summary, contacts, data
    flow, typical day, flight rules, contingencies, end-of-life operations."""
    import io

    from fastapi.responses import StreamingResponse

    from ..services.docx.conops import generate_conops_from_view
    view = await conops_view(study_id, lang=lang)
    blob = generate_conops_from_view(view, lang=lang)
    name = (view["study_name"] or "study").replace(" ", "_")
    return StreamingResponse(io.BytesIO(blob),
                             media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             headers={"Content-Disposition": f'attachment; filename="SpaceCDF_ConOps_{name}.docx"'})
