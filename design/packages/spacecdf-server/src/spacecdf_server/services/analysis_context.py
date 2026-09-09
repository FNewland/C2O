"""AnalysisContext — the single, read-only input of every engineering analysis
(SCDF-170 §1.1).

``build_context(study_id, option_id=None)`` assembles, from the persisted
model, everything the design loop, the mission simulation, the ground /
thermal / physics closures and the V&V planner need:

* ``elements`` / ``interfaces`` / ``exchange_items`` / ``functions`` /
  ``allocations`` — dicts exactly as ``routers.elements`` serves them
  (cache first, DB when the cache does not hold the study);
* ``params`` — ``{element_id: {name: EffectiveParam}}`` with the *effective*
  value of every typed parameter (manual / reference override, ``ref`` or
  ``calc`` formula, else computed / column) from ``services.equations``;
* ``flat`` — the ``parameter_path -> value`` dict the agents consume:
  ``element_projection.project_elements_to_params`` over the element tree
  **with effective parameter values overlaid** on the six well-known columns
  (an overridden roll-up on a subsystem replaces the sum of its children).
  ``overridden_paths`` lists the flat paths that inherit at least one manual /
  reference / formula value; ``seed_design_state`` marks those
  ``POSITION_OVERRIDE`` (sticky) so the agents cannot overwrite them
  (SCDF-171 coupling). Computed mirrors never displace a value the last
  design loop produced — they only fill paths the agents have not set;
* ``orbit`` / ``modes`` / ``power`` / ``thermal`` / ``ground_stations`` /
  ``requirements`` — derived views, see the field docs on
  :class:`AnalysisContext`.

``context_hash(ctx, keys)`` is a stable SHA-256 over the named subsets and
is what ``analysis_results`` stores as ``inputs_hash`` for stale detection.

Option scoping (SCDF-172): ``option_id`` selects parameter rows whose
``option_id`` matches and falls back to the baseline rows (``NULL``) for
everything else (``equations.evaluate_study(study_id, option_id)``).
``EffectiveParam.option_id`` is set on the overrides. Elements are not cloned
per option; analysis runs/conflicts are option-scoped.

Public API:
    build_context(study_id, *, option_id=None) -> AnalysisContext
    context_hash(ctx, keys) -> str
    seed_design_state(ctx, *, requirements, conops, knowledge_base) -> DesignState
    HASH_KEYS — the valid names for ``context_hash``
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from spacecdf_common.models.parameters import WELL_KNOWN_PARAMETERS

from .element_projection import contributing_elements, project_elements_to_params

logger = logging.getLogger(__name__)

HASH_KEYS: tuple[str, ...] = (
    "elements", "params", "modes", "orbit", "power", "thermal", "stations", "requirements",
)

#: Provenances whose effective value is an *override* of the column / agent value.
OVERRIDE_PROVENANCES = ("manual", "formula", "reference")

_GUARD_RE = re.compile(r"^\s*guard\s*:\s*(?P<cond>[^-\n]+?)\s*->\s*(?P<target>[\w-]+)\s*$", re.I | re.M)


# ── Data classes ────────────────────────────────────────────────────────

@dataclass
class EffectiveParam:
    """One typed parameter on an element, as evaluated by ``services.equations``."""
    element_id: str
    name: str
    value: float | None
    unit: str = ""
    quantity_kind: str = ""
    switch: str = "computed"          # manual | computed | reference
    provenance: str = "column"        # manual | formula | column | agent | reference
    formula: str | None = None
    formula_kind: str | None = None   # ref | calc | None
    owner_domain: str | None = None
    option_id: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def is_override(self) -> bool:
        return self.provenance in OVERRIDE_PROVENANCES and self.value is not None


@dataclass
class ModeSpec:
    """An operational mode built from a ``mode`` element + its member rows."""
    id: str
    name: str
    power_w: float
    duty_cycle_percent: float = 100.0
    active_element_ids: list[str] = field(default_factory=list)
    payload_active: bool = False
    data_rate_bps: float = 0.0
    pointing: str = "nadir"
    guards: list[dict] = field(default_factory=list)   # [{condition, target_mode, priority}]
    source: str = "element"                             # element | conops | default


@dataclass
class AnalysisContext:
    study_id: str
    option_id: str | None = None
    study: Any = None                                  # spacecdf_common.models.study.Study | None
    latest_design: dict[str, dict] = field(default_factory=dict)  # last design_loop parameters {path: {value, unit, ...}}
    elements: list[dict] = field(default_factory=list)
    interfaces: list[dict] = field(default_factory=list)
    exchange_items: list[dict] = field(default_factory=list)
    functions: list[dict] = field(default_factory=list)
    allocations: list[dict] = field(default_factory=list)
    params: dict[str, dict[str, EffectiveParam]] = field(default_factory=dict)
    flat: dict[str, Any] = field(default_factory=dict)
    overridden_paths: set[str] = field(default_factory=set)
    orbit: dict[str, Any] = field(default_factory=dict)     # altitude_km, inclination_deg, period_s, eclipse_fraction, sunlight_fraction, raan_deg, ltan, orbit_type
    modes: list[ModeSpec] = field(default_factory=list)
    power: dict[str, Any] = field(default_factory=dict)     # battery_capacity_wh, battery_dod_percent, battery_efficiency, sa_power_bol_w, sa_power_eol_w, sa_area_m2
    thermal: dict[str, Any] = field(default_factory=dict)   # nodes: [{element_id, name, domain, dissipation_w, mass_kg}], emissivity, absorptivity
    ground_stations: list[dict] = field(default_factory=list)
    all_kb_stations: list[dict] = field(default_factory=list)
    requirements: list[dict] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # -- lookups ---------------------------------------------------------
    @property
    def elements_by_id(self) -> dict[str, dict]:
        return {e["id"]: e for e in self.elements}

    @property
    def mission_root(self) -> dict | None:
        """The ``mission`` element, else the first root element, else ``None``."""
        for e in self.elements:
            if e.get("element_type") == "mission":
                return e
        ids = {e["id"] for e in self.elements}
        for e in self.elements:
            if not e.get("parent_id") or e["parent_id"] not in ids:
                return e
        return None

    def element(self, ref: str) -> dict | None:
        """Element by id, else by unique name (``None`` when ambiguous / unknown)."""
        by_id = self.elements_by_id
        if ref in by_id:
            return by_id[ref]
        hits = [e for e in self.elements if e.get("name") == ref]
        return hits[0] if len(hits) == 1 else None

    def subsystem(self, domain: str) -> dict | None:
        for e in self.elements:
            if e.get("element_type") == "subsystem" and e.get("subsystem_domain") == domain:
                return e
        return None

    def param(self, element_ref: str, name: str) -> EffectiveParam | None:
        el = self.element(element_ref)
        if el is None:
            return None
        return self.params.get(el["id"], {}).get(name)

    def canonical_path(self, path: str) -> str:
        """``el:<name>.<param>`` -> ``el:<id>.<param>``; flat paths unchanged."""
        if not path.startswith("el:"):
            return path
        ref, _, name = path[3:].rpartition(".")
        el = self.element(ref) if ref else None
        return f"el:{el['id']}.{name}" if el else path

    def resolve(self, path: str) -> float | None:
        """Value behind a threshold / input path.

        ``el:<element id or name>.<param>`` reads the effective typed parameter
        (falling back to the element column for well-known names); anything
        else is looked up in ``flat``. ``None`` when unknown or non-numeric.
        """
        if path.startswith("el:"):
            ref, _, name = path[3:].rpartition(".")
            el = self.element(ref) if ref else None
            if el is None or not name:
                return None
            p = self.params.get(el["id"], {}).get(name)
            if p is not None and isinstance(p.value, (int, float)):
                return float(p.value)
            if name in WELL_KNOWN_PARAMETERS and isinstance(el.get(name), (int, float)):
                return float(el[name])
            return None
        v = self.flat.get(path)
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    def get(self, path: str, default: float | None = None) -> float | None:
        """``ComplianceTracker``-compatible accessor (``state.get(path)``)."""
        v = self.resolve(path)
        return default if v is None else v


# ── Loading helpers ─────────────────────────────────────────────────────

async def _load_elements(study_id: str) -> tuple[list[dict], list[dict]]:
    from ..routers import elements as elements_router
    els = [e for e in elements_router._elements.values()
           if e.get("study_id") == study_id and not e.get("deleted_at")]
    ifs = [i for i in elements_router._interfaces.values()
           if i.get("study_id") == study_id and not i.get("deleted_at")]
    if els:
        return els, ifs
    from ..db.element_repo import load_all_elements
    all_els, all_ifs = await load_all_elements()
    return ([e for e in all_els.values() if e.get("study_id") == study_id and not e.get("deleted_at")],
            [i for i in all_ifs.values() if i.get("study_id") == study_id and not i.get("deleted_at")])


async def _load_params(study_id: str, option_id: str | None) -> dict[str, dict[str, EffectiveParam]]:
    from ..db import parameter_repo
    from . import equations

    out: dict[str, dict[str, EffectiveParam]] = {}
    # SCDF-172: the equation engine evaluates baseline ∪ option overrides in one
    # pass (option rows shadow baseline rows; formulas see the option's values).
    res = await equations.evaluate_study(study_id, option_id=option_id)
    for p in res.get("parameters", []):
        ep = EffectiveParam(
            element_id=p["element_id"], name=p["name"], value=p.get("effective_value"),
            unit=p.get("unit") or "", quantity_kind=p.get("quantity_kind") or "",
            switch=p.get("value_switch") or "computed", provenance=p.get("provenance") or "column",
            formula=p.get("formula"), formula_kind=p.get("formula_kind"),
            owner_domain=p.get("owner_domain"), option_id=p.get("option_id"),
            errors=list(p.get("errors") or []),
        )
        if ep.switch == "reference" and ep.provenance == "agent":
            ep.provenance = "reference"
        out.setdefault(ep.element_id, {})[ep.name] = ep
    return out


def _effective_elements(elements: list[dict], params: dict[str, dict[str, EffectiveParam]]
                        ) -> tuple[list[dict], set[tuple[str, str]]]:
    """Copy of the elements with override values on the well-known columns,
    plus the set of ``(element_id, column)`` that were overridden."""
    overridden: set[tuple[str, str]] = set()
    out: list[dict] = []
    for e in elements:
        ee = dict(e)
        for name in WELL_KNOWN_PARAMETERS:
            p = params.get(e["id"], {}).get(name)
            if p is not None and p.is_override:
                ee[name] = p.value
                overridden.add((e["id"], name))
        out.append(ee)
    return out, overridden


def _enum_str(v: Any) -> str:
    return str(getattr(v, "value", v) or "")


def _build_orbit(flat: dict, latest: dict, study: Any) -> dict[str, Any]:
    def pick(path: str) -> float | None:
        v = flat.get(path)
        if v is None and path in latest:
            v = latest[path].get("value") if isinstance(latest[path], dict) else latest[path]
        return v if isinstance(v, (int, float)) else None

    req_orbit = getattr(getattr(study, "requirements", None), "orbit", None)
    alt = pick("orbit.altitude_km") or (req_orbit.altitude_km if req_orbit else 500.0)
    inc = pick("orbit.inclination_deg") or (req_orbit.inclination_deg if req_orbit else 97.4)
    period = pick("orbit.period_s")
    ecl = pick("orbit.eclipse_fraction")
    sun = pick("orbit.sunlight_fraction")
    if period is None or ecl is None:
        try:
            from spacecdf_common.physics.orbit import compute_orbit_params
            op = compute_orbit_params(alt, inc)
            period = period or op.period_s
            ecl = op.eclipse_fraction if ecl is None else ecl
        except Exception:  # pragma: no cover - defensive
            period, ecl = period or 5700.0, 0.35 if ecl is None else ecl
    if sun is None:
        sun = 1.0 - ecl
    return {
        "altitude_km": alt, "inclination_deg": inc, "period_s": period,
        "eclipse_fraction": ecl, "sunlight_fraction": sun,
        "eccentricity": getattr(req_orbit, "eccentricity", 0.0) if req_orbit else 0.0,
        "raan_deg": getattr(req_orbit, "raan_deg", None) if req_orbit else None,
        "ltan": getattr(req_orbit, "ltan", None) if req_orbit else None,
        "orbit_type": _enum_str(getattr(req_orbit, "orbit_type", "")) if req_orbit else "",
        "contact_time_per_day_s": pick("orbit.contact_time_per_day_s"),
    }


def _parse_guards(text: str | None) -> list[dict]:
    guards = []
    for i, m in enumerate(_GUARD_RE.finditer(text or "")):
        guards.append({"condition": m.group("cond").strip(), "target_mode": m.group("target"),
                       "priority": 10 - i})
    return guards


async def _load_mode_members(study_id: str, mode_ids: set[str]) -> dict[str, list[dict]]:
    """Members per mode from the in-memory ``_mode_elements`` list + ``mode_elements`` rows."""
    from ..routers import elements as elements_router
    members: dict[str, list[dict]] = {m: [] for m in mode_ids}
    seen: set[tuple[str, str]] = set()
    for m in elements_router._mode_elements:
        if m.get("mode_id") in mode_ids and m.get("is_active", True):
            members[m["mode_id"]].append(dict(m))
            seen.add((m["mode_id"], m["element_id"]))
    try:
        from sqlalchemy import select
        from ..db.engine import get_session_factory
        from ..db.models import ModeElementRow
        factory = get_session_factory()
        async with factory() as session:
            res = await session.execute(select(ModeElementRow).where(ModeElementRow.mode_id.in_(list(mode_ids))))
            for row in res.scalars():
                if not row.is_active or (row.mode_id, row.element_id) in seen:
                    continue
                members[row.mode_id].append({
                    "mode_id": row.mode_id, "element_id": row.element_id, "is_active": True,
                    "power_w_in_mode": row.power_w_in_mode, "duty_cycle_percent": row.duty_cycle_percent,
                    "notes": row.notes,
                })
    except Exception:
        logger.debug("mode_elements table unavailable", exc_info=True)
    return members


async def _build_modes(study_id: str, eff_elements: list[dict], study: Any) -> list[ModeSpec]:
    by_id = {e["id"]: e for e in eff_elements}
    mode_els = [e for e in eff_elements if e.get("element_type") == "mode"]
    if mode_els:
        members = await _load_mode_members(study_id, {m["id"] for m in mode_els})
        specs = []
        for m in mode_els:
            total = 0.0
            active: list[str] = []
            payload_active = False
            for mem in members.get(m["id"], []):
                el = by_id.get(mem["element_id"])
                if el is None:
                    continue
                pw = mem.get("power_w_in_mode")
                if pw is None:
                    pw = el.get("power_avg_w") or 0.0
                duty = (mem.get("duty_cycle_percent") if mem.get("duty_cycle_percent") is not None else 100.0) / 100.0
                total += float(pw) * duty
                active.append(el["id"])
                if el.get("subsystem_domain") == "payload":
                    payload_active = True
            perf = m.get("performance_json") or m.get("performance") or {}
            if not active and isinstance(perf.get("power_w"), (int, float)):
                total = float(perf["power_w"])
            if not active and isinstance(m.get("power_avg_w"), (int, float)):
                total = float(m["power_avg_w"])
            specs.append(ModeSpec(
                id=m["id"], name=m["name"], power_w=round(total, 3), active_element_ids=active,
                payload_active=payload_active or bool(perf.get("payload_active")),
                data_rate_bps=float(perf.get("data_rate_bps") or 0.0),
                pointing=str(perf.get("pointing") or "nadir"),
                guards=_parse_guards(m.get("description")), source="element",
            ))
        return specs
    conops = getattr(study, "conops", None)
    if conops is not None and getattr(conops, "modes", None):
        return [ModeSpec(id=om.id or om.name, name=om.name or om.id, power_w=float(om.power_w or 0.0),
                         payload_active=bool(om.payload_active), data_rate_bps=float(om.data_rate_mbps or 0) * 1e6,
                         source="conops") for om in conops.modes]
    from .conops_executor import DEFAULT_MODES
    return [ModeSpec(id=dm.name, name=dm.name, power_w=dm.power_draw_w, payload_active=dm.is_payload_active,
                     data_rate_bps=dm.data_rate_bps, pointing=dm.pointing, source="default") for dm in DEFAULT_MODES]


def _first_perf(eff_elements: list[dict], domain: str, key: str) -> float | None:
    for e in eff_elements:
        if e.get("subsystem_domain") != domain:
            continue
        perf = e.get("performance_json") or e.get("performance") or {}
        v = perf.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def _build_power(flat: dict, latest: dict, eff_elements: list[dict]) -> dict[str, Any]:
    def pick(path: str, default: float | None = None) -> float | None:
        v = flat.get(path)
        if v is None and path in latest:
            v = latest[path].get("value") if isinstance(latest[path], dict) else latest[path]
        return float(v) if isinstance(v, (int, float)) else default
    return {
        "battery_capacity_wh": pick("power.battery_capacity_wh"),
        "battery_dod_percent": _first_perf(eff_elements, "power", "dod_percent") or pick("power.battery_dod_percent", 30.0),
        "battery_efficiency": _first_perf(eff_elements, "power", "efficiency") or pick("power.battery_efficiency", 0.9),
        "min_soc_pct": _first_perf(eff_elements, "power", "min_soc_pct") or 20.0,
        "sa_power_bol_w": pick("power.sa_power_bol_w"),
        "sa_power_eol_w": pick("power.sa_power_eol_w"),
        "sa_area_m2": pick("power.sa_area_m2"),
        "heater_power_w": pick("thermal.heater_power_w"),
    }


def _build_thermal(eff_elements: list[dict]) -> dict[str, Any]:
    nodes = []
    for e in eff_elements:
        if e.get("element_type") not in ("subsystem", "component") or (e.get("segment") or "space") != "space":
            continue
        nodes.append({
            "element_id": e["id"], "name": e.get("name"), "domain": e.get("subsystem_domain"),
            "dissipation_w": float(e.get("power_avg_w") or 0.0), "mass_kg": float(e.get("mass_kg") or 0.0),
            "parent_id": e.get("parent_id"),
        })
    return {"nodes": nodes, "emissivity": 0.85, "absorptivity": 0.3}


def _kb_stations() -> list[dict]:
    try:
        from spacecdf_kb.loader import KnowledgeBase
        return KnowledgeBase().ground_stations
    except Exception:
        logger.warning("KB ground stations unavailable", exc_info=True)
        return []


def _select_stations(elements: list[dict], all_stations: list[dict]) -> list[dict]:
    by_id = {s.get("id"): s for s in all_stations}
    by_name = {s.get("name"): s for s in all_stations}
    out: list[dict] = []
    seen: set[str] = set()
    for e in elements:
        if e.get("segment") != "ground" or not e.get("kb_component_id"):
            continue
        s = by_id.get(e["kb_component_id"]) or by_name.get(e["kb_component_id"])
        if s and s.get("id") not in seen:
            seen.add(s.get("id"))
            out.append({**s, "element_id": e["id"]})
    return out


async def _load_requirements(study_id: str) -> tuple[list[dict], list[dict]]:
    from ..routers import requirements as req_router
    try:
        await req_router.ensure_requirements_loaded()
    except Exception:
        logger.debug("requirement cache hydration failed", exc_info=True)
    reqs = [dict(r) for r in req_router._requirements.values()
            if r.get("study_id") == study_id and r.get("status") != "retired"]
    try:
        from ..db.relation_repo import list_relations_by_study
        rels = await list_relations_by_study(study_id)
    except Exception:
        rels = []
    return reqs, rels


async def _load_latest_design(study_id: str, option_id: str | None) -> dict[str, dict]:
    try:
        from .analysis_results import load_series
        from ..db.analysis_repo import get_last_run
        run = await get_last_run(study_id, "design_loop", option_id)
        if not run or run.get("status") != "ok":
            return {}
        series = load_series(run.get("series_ref"))
        params = (series or {}).get("parameters") or {}
        return params if isinstance(params, dict) else {}
    except Exception:
        logger.debug("latest design unavailable", exc_info=True)
        return {}


# ── Public API ─────────────────────────────────────────────────────────

async def build_context(study_id: str, *, option_id: str | None = None) -> AnalysisContext:
    """Assemble the analysis context for a study (read-only, never raises for
    missing optional parts — they come back empty with a note in ``warnings``)."""
    from ..routers.studies import get_study_store

    if option_id:
        # SCDF-172: the baseline option's own id addresses the NULL rows.
        try:
            from ..db import option_repo
            option_id = await option_repo.resolve_option_id(option_id)
        except Exception:
            pass   # unknown id → treated as an option without overrides
    ctx = AnalysisContext(study_id=study_id, option_id=option_id)
    ctx.study = get_study_store().get(study_id)

    ctx.elements, ctx.interfaces = await _load_elements(study_id)
    try:
        from ..db.exchange_item_repo import list_exchange_items_by_study
        ctx.exchange_items = await list_exchange_items_by_study(study_id)
    except Exception:
        ctx.warnings.append("exchange items unavailable")
    try:
        from ..db.function_repo import load_all_function_allocations, load_all_functions
        ctx.functions = list((await load_all_functions(study_id)).values())
        ctx.allocations = list((await load_all_function_allocations(study_id)).values())
    except Exception:
        ctx.warnings.append("functions unavailable")

    ctx.params = await _load_params(study_id, option_id)
    ctx.latest_design = await _load_latest_design(study_id, option_id)

    eff_elements, overridden_cols = _effective_elements(ctx.elements, ctx.params)
    ctx.flat = project_elements_to_params(eff_elements, overridden_cols)
    ctx.overridden_paths = {
        path for path, contribs in contributing_elements(eff_elements, overridden_cols).items()
        if any((eid, prop) in overridden_cols for eid, prop in contribs) and path in ctx.flat
    }

    ctx.orbit = _build_orbit(ctx.flat, ctx.latest_design, ctx.study)
    ctx.modes = await _build_modes(study_id, eff_elements, ctx.study)
    ctx.power = _build_power(ctx.flat, ctx.latest_design, eff_elements)
    ctx.thermal = _build_thermal(eff_elements)
    ctx.all_kb_stations = _kb_stations()
    ctx.ground_stations = _select_stations(ctx.elements, ctx.all_kb_stations)
    ctx.requirements, ctx.relations = await _load_requirements(study_id)
    return ctx


def _hash_subset(ctx: AnalysisContext, key: str) -> Any:
    if key == "elements":
        return sorted(
            [e["id"], e.get("parent_id"), e.get("name"), e.get("element_type"), e.get("subsystem_domain"),
             e.get("segment"), e.get("quantity", 1), e.get("kb_component_id"),
             [e.get(c) for c in WELL_KNOWN_PARAMETERS],
             e.get("performance_json") or e.get("performance") or {}, e.get("in_scope", True)]
            for e in ctx.elements)
    if key == "params":
        return sorted(
            [eid, name, p.value, p.switch, p.formula, p.formula_kind]
            for eid, ps in ctx.params.items() for name, p in ps.items())
    if key == "modes":
        return [[m.id, m.name, m.power_w, m.duty_cycle_percent, sorted(m.active_element_ids),
                 m.payload_active, m.data_rate_bps, m.pointing, m.guards] for m in ctx.modes]
    if key == "orbit":
        return ctx.orbit
    if key == "power":
        return ctx.power
    if key == "thermal":
        return ctx.thermal
    if key == "stations":
        return sorted(s.get("id") or s.get("name") or "" for s in ctx.ground_stations)
    if key == "requirements":
        return sorted(
            [r.get("id"), r.get("parent_id"), r.get("threshold_param_path"), r.get("threshold_op"),
             r.get("threshold_value"), r.get("status"), r.get("element_id")]
            for r in ctx.requirements)
    raise KeyError(f"unknown context hash key {key!r}; valid: {HASH_KEYS}")


def context_hash(ctx: AnalysisContext, keys: list[str] | tuple[str, ...]) -> str:
    """Stable SHA-256 (hex) over the named context subsets (see ``HASH_KEYS``).

    The same model state always yields the same hash; a change in any named
    subset changes it. Unknown keys raise ``KeyError``.
    """
    payload = {k: _hash_subset(ctx, k) for k in sorted(set(keys))}
    blob = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def seed_design_state(ctx: AnalysisContext, *, requirements: Any = None, conops: Any = None,
                      knowledge_base: Any = None):
    """``DesignState`` for the orchestrator, seeded from the context (SCDF-171).

    Precedence: overridden flat paths (``POSITION_OVERRIDE``, sticky) >
    last design-loop values (``COMPUTED``) > non-overridden flat paths
    (``COMPUTED``, only where the last loop has no value).
    """
    from spacecdf_common.agents.base import DesignState
    from spacecdf_common.models.parameter import ParameterSource, ParameterValue

    params: dict[str, ParameterValue] = {}

    def _pv(path: str, value: Any, source: ParameterSource, unit: str = "") -> ParameterValue | None:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            return None
        return ParameterValue(id=path, name=path, value=value, unit=unit, domain=path.split(".")[0],
                              source=source, confidence=1.0 if source.is_sticky else 0.7,
                              margin_percent=0.0, updated_by="analysis_context")

    for path, entry in ctx.latest_design.items():
        value = entry.get("value") if isinstance(entry, dict) else entry
        pv = _pv(path, value, ParameterSource.COMPUTED, (entry.get("unit") or "") if isinstance(entry, dict) else "")
        if pv is not None:
            params[path] = pv
    for path, value in ctx.flat.items():
        if path in ctx.overridden_paths:
            pv = _pv(path, value, ParameterSource.POSITION_OVERRIDE)
        elif path in params:
            continue
        else:
            pv = _pv(path, value, ParameterSource.COMPUTED)
        if pv is not None:
            params[path] = pv

    req_dict = requirements.model_dump() if hasattr(requirements, "model_dump") else (requirements or {})
    return DesignState(parameters=params, requirements=req_dict, knowledge_base=knowledge_base, conops=conops)
