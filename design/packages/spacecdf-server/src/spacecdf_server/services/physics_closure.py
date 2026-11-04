"""Physics closure — mass properties -> AOCS, thermal network from elements
(SCDF-176, design SCDF-170 §2.4).

Everything is built from the :class:`AnalysisContext` (elements with their
effective ``mass_kg`` / ``power_avg_w``, ``dimensions_mm``, ``position_json``,
``thermal`` interfaces, KB components, orbit, requirements):

* ``place_elements`` — body-frame position of every mass-carrying element:
  ``position_json`` when set, else an automatic stack along +z inside the
  spacecraft envelope (``auto_placed`` warnings). The envelope is the
  ``system`` element's ``dimensions_mm``, else the class default (nano = 3U);
* ``run_mass_properties`` — CoM, inertia tensor (box inertia per component +
  parallel axis), principal axes, CP at the envelope's geometric centre
  -> ``mp_*`` parameters on the mission root;
* ``run_aocs_closure`` — disturbance torques with the real inertia and
  CP-CG offset (``spacecdf_common.physics.aocs.compute_disturbance_torques``),
  momentum per orbit vs the selected reaction wheel (KB ``momentum_nms``,
  ``performance.momentum_nms``, a manual ``aocs_wheel_capacity_nms`` on the
  mission root, else the class default), pointing estimate vs the tightest
  pointing requirement -> ``aocs_*`` parameters and conflicts;
* ``run_thermal_closure`` — a lumped network: one node per space subsystem
  (dropped when all its mass and power sit in its hot components), one per
  leaf component dissipating > 0.5 W, plus the bus structure (system
  element) as the backbone; bolted-joint conductances parent <-> child
  and along ``thermal`` interfaces (``properties.conductance_w_per_k``);
  hot case = sunlit steady state at peak power with the hot environment
  constants; cold case = periodic orbit transient (eclipse, safe-mode power,
  cold constants), its minimum per node; allowable ranges from ``performance.op_temp_min_c`` /
  ``op_temp_max_c``, the KB ``operating_temp_c`` range, else class defaults
  -> per-element ``thermal_*`` parameters and ``THERMAL_OUT_OF_RANGE``;
* ``run_physics`` — the three in sequence, one :class:`AnalysisOutput`.

Pure with respect to the model: nothing is written here — the router hands
the output to ``ResultsSink``.

Public API:
    Placement, place_elements(ctx) -> Placement
    run_mass_properties(ctx, placement=None) -> MassPropertiesOut
    run_aocs_closure(ctx, mp) -> AocsOut
    run_thermal_closure(ctx) -> ThermalOut
    run_physics(ctx) -> AnalysisOutput
    ANALYSIS, OUTPUT_PARAMETERS, CONFLICT_CODES
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from spacecdf_common.physics.aocs import MU_EARTH, R_EARTH, compute_disturbance_torques

from .analysis_context import AnalysisContext
from .analysis_results import ANALYSIS_INPUT_KEYS, Conflict, ParamWrite
from .mass_properties import MassComponent, MassPropertiesResult, compute_mass_properties
from .thermal_network import (
    SPACE_SINK_TEMP_K,
    STEFAN_BOLTZMANN,
    ThermalConductance,
    ThermalNode,
    solve_steady_state,
    solve_transient,
)

logger = logging.getLogger(__name__)

ANALYSIS = "physics"
ANALYSIS_INPUT_KEYS.setdefault(ANALYSIS, ("elements", "params", "orbit", "thermal"))

OUTPUT_PARAMETERS: tuple[str, ...] = (
    "mp_total_mass_kg", "mp_com_x_m", "mp_com_y_m", "mp_com_z_m",
    "mp_ixx_kgm2", "mp_iyy_kgm2", "mp_izz_kgm2", "mp_cp_cg_offset_m", "mp_auto_placed_count",
    "aocs_disturbance_torque_nm", "aocs_gg_torque_nm", "aocs_aero_torque_nm", "aocs_srp_torque_nm",
    "aocs_mag_torque_nm", "aocs_momentum_per_orbit_nms", "aocs_wheel_capacity_nms", "aocs_wheel_margin_pct",
    "aocs_pointing_req_deg", "aocs_pointing_est_deg", "aocs_pointing_margin_deg",
    "thermal_worst_margin_c", "thermal_nodes",
)
ELEMENT_PARAMETERS: tuple[str, ...] = ("thermal_t_hot_c", "thermal_t_cold_c", "thermal_margin_hot_c", "thermal_margin_cold_c")
CONFLICT_CODES: tuple[str, ...] = (
    "AOCS_WHEEL_SATURATION", "AOCS_POINTING_MARGIN", "AOCS_CG_OFFSET_HIGH", "THERMAL_OUT_OF_RANGE",
)

# ── class defaults ──────────────────────────────────────────────────────
#: Envelope (dx, dy, dz) m per spacecraft class when the system element has no dimensions.
CLASS_ENVELOPE_M: dict[str, tuple[float, float, float]] = {
    "nano": (0.1, 0.1, 0.3), "micro": (0.5, 0.5, 0.6), "small": (1.0, 1.0, 1.2),
    "medium": (2.0, 2.0, 2.5), "large": (3.0, 3.0, 4.0), "flagship": (4.0, 4.0, 6.0),
}
#: Residual magnetic dipole [A m2] per class (SMAD / ECSS-E-ST-10-04 typical).
CLASS_DIPOLE_AM2: dict[str, float] = {"nano": 0.01, "micro": 0.1, "small": 0.5, "medium": 1.0, "large": 2.0, "flagship": 5.0}
#: Reaction-wheel momentum capacity [N m s] per class when no wheel is selected.
CLASS_WHEEL_NMS: dict[str, float] = {"nano": 0.01, "micro": 0.1, "small": 1.0, "medium": 8.0, "large": 25.0, "flagship": 50.0}
#: Attitude knowledge [deg] per sensor class found in the element tree.
SENSOR_KNOWLEDGE_DEG: tuple[tuple[str, float], ...] = (
    ("star", 0.005), ("gyro", 0.05), ("horizon", 0.1), ("earth sensor", 0.1), ("sun", 0.5), ("magnetometer", 2.0),
)
DEFAULT_KNOWLEDGE_DEG = 1.0        # no attitude sensor found
CONTROL_BANDWIDTH_HZ = 0.05        # closed-loop bandwidth used for the disturbance-induced pointing error
CP_UNCERTAINTY_FRACTION = 0.01     # CP-CG offset floor: 1 % of the max dimension (ECSS practice)
CG_OFFSET_WARN_FRACTION = 0.02     # AOCS_CG_OFFSET_HIGH above 2 % of the max dimension
DESATURATIONS_PER_ORBIT = 1.0      # momentum budget assumes one magnetorquer dump per orbit

DEFAULT_COMPONENT_DIMS_M = (0.09, 0.09, 0.025)   # PC/104 board
DEFAULT_CP_J_PER_KG_K = 900.0                    # aluminium-dominated
DOMAIN_CP_J_PER_KG_K: dict[str, float] = {"power": 950.0, "structure": 900.0, "payload": 800.0}
BATTERY_CP_J_PER_KG_K = 1100.0
DEFAULT_OP_RANGE_C = (-20.0, 50.0)
BATTERY_OP_RANGE_C = (0.0, 40.0)
DOMAIN_OP_RANGE_C: dict[str, tuple[float, float]] = {
    "propulsion": (5.0, 50.0), "structure": (-40.0, 80.0), "thermal": (-40.0, 80.0), "payload": (-10.0, 40.0),
}
JOINT_CONDUCTANCE_W_K = 0.5        # bolted joint parent <-> child
INTERFACE_CONDUCTANCE_W_K = 0.5    # default of a `thermal` interface without properties
DEFAULT_EMISSIVITY = 0.85
DEFAULT_ABSORPTIVITY = 0.8         # solar-cell-covered faces (0.9) with anodised aluminium (0.5) elsewhere
SOLAR_FLUX_HOT = 1414.0            # perihelion
SOLAR_FLUX_COLD = 1322.0           # aphelion
EARTH_IR_HOT = 258.0
EARTH_IR_COLD = 218.0
ALBEDO_HOT = 0.35
ALBEDO_COLD = 0.25
TRANSIENT_ORBITS = 3               # orbits integrated before the periodic cold orbit is read
EARTH_VIEW_FACTOR = 0.3            # mean view factor of a tumbling LEO body to Earth
PROJECTED_AREA_FRACTION = 0.25     # projected / total area of a convex body (sphere)
NODE_POWER_THRESHOLD_W = 0.5
SAFE_POWER_FRACTION = 0.6          # cold case load when the model has no safe mode
MAX_SERIES_POINTS = 600


# ── output dataclasses ─────────────────────────────────────────────────

@dataclass
class AnalysisOutput:
    parameters: list[ParamWrite] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    series: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PlacedItem:
    element_id: str
    name: str
    element_type: str
    domain: str | None
    mass_kg: float
    dims_m: tuple[float, float, float]
    position_m: list[float]
    source: str          # explicit | auto | fallback (subsystem mass used because it has no children)
    quantity: int = 1


@dataclass
class Placement:
    positions: dict[str, list[float]] = field(default_factory=dict)
    items: list[PlacedItem] = field(default_factory=list)
    auto_placed: list[str] = field(default_factory=list)
    envelope_m: tuple[float, float, float] = (0.1, 0.1, 0.3)
    envelope_source: str = "class default"
    envelope_element_id: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class MassPropertiesOut:
    result: MassPropertiesResult
    placement: Placement
    cp_m: list[float]
    cp_cg_offset_m: float
    max_dimension_m: float
    parameters: list[ParamWrite] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class AocsOut:
    torques: dict[str, float]
    momentum_per_orbit_nms: float
    wheel_capacity_nms: float
    wheel_source: str
    wheel_element_id: str | None
    wheel_margin_pct: float
    pointing_req_deg: float | None
    pointing_req_source: str
    pointing_est_deg: float
    pointing_budget: dict[str, float]
    pointing_margin_deg: float | None
    inputs: dict[str, Any]
    parameters: list[ParamWrite] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ThermalNodeOut:
    element_id: str
    name: str
    domain: str | None
    kind: str                 # subsystem | component | structure
    mass_kg: float
    cp_j_per_kg_k: float
    area_m2: float
    dissipation_hot_w: float
    dissipation_cold_w: float
    allow_min_c: float
    allow_max_c: float
    allow_source: str
    t_hot_c: float = 0.0
    t_cold_c: float = 0.0
    margin_hot_c: float = 0.0
    margin_cold_c: float = 0.0
    t_transient_min_c: float = 0.0
    t_transient_max_c: float = 0.0


@dataclass
class ThermalOut:
    nodes: list[ThermalNodeOut]
    conductances: list[dict]
    worst_margin_c: float | None
    transient: dict[str, Any]
    inputs: dict[str, Any]
    parameters: list[ParamWrite] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ── helpers ─────────────────────────────────────────────────────────────

def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _perf(e: dict) -> dict:
    perf = e.get("performance_json") or e.get("performance") or {}
    return perf if isinstance(perf, dict) else {}


def _eff_col(ctx: AnalysisContext, e: dict, name: str) -> float:
    """Effective well-known column: manual / reference / formula override, else the column."""
    p = ctx.params.get(e["id"], {}).get(name)
    if p is not None and p.value is not None and p.is_override:
        return float(p.value)
    return _num(e.get(name)) or 0.0


def _override(ctx: AnalysisContext, e: dict | None, *names: str) -> float | None:
    if e is None:
        return None
    for name in names:
        p = ctx.params.get(e["id"], {}).get(name)
        if p is not None and p.is_override:
            v = _num(p.value)
            if v is not None:
                return v
    return None


def _sc_class(ctx: AnalysisContext) -> str:
    cls = str(getattr(getattr(ctx.study, "requirements", None), "spacecraft_class", "") or "").lower()
    if cls in CLASS_ENVELOPE_M:
        return cls
    mass = _num(ctx.flat.get("mass.dry_mass_kg")) or sum(_eff_col(ctx, e, "mass_kg") for e in _space_elements(ctx)
                                                           if e.get("element_type") == "component")
    if mass <= 0:
        return "nano"
    return "nano" if mass < 15 else "micro" if mass < 100 else "small" if mass < 500 else "medium" if mass < 1500 else "large"


def _space_elements(ctx: AnalysisContext) -> list[dict]:
    return [e for e in ctx.elements
            if e.get("element_type") in ("system", "subsystem", "component")
            and (e.get("segment") or "space") == "space" and e.get("in_scope", True) is not False]


_kb_cache: dict[str, dict | None] = {}


def _kb_component(kb_id: str | None) -> dict | None:
    """KB component by id or name (``None`` when unknown / KB unavailable)."""
    if not kb_id:
        return None
    if kb_id in _kb_cache:
        return _kb_cache[kb_id]
    found = None
    try:
        from spacecdf_kb.loader import KnowledgeBase
        for c in KnowledgeBase().search_components():
            if c.get("id") == kb_id or c.get("name") == kb_id:
                found = c
                break
    except Exception:
        logger.debug("KB lookup failed for %s", kb_id, exc_info=True)
    _kb_cache[kb_id] = found
    return found


def _dims_m(e: dict) -> tuple[float, float, float] | None:
    dims = e.get("dimensions_mm") or e.get("dimensions_json")
    if not dims:
        kb = _kb_component(e.get("kb_component_id"))
        dims = (kb or {}).get("dimensions_mm")
    if isinstance(dims, (list, tuple)) and len(dims) == 3 and all(_num(d) is not None and d > 0 for d in dims):
        return (float(dims[0]) / 1000.0, float(dims[1]) / 1000.0, float(dims[2]) / 1000.0)
    return None


def _position(e: dict) -> list[float] | None:
    pos = e.get("position_json")
    if isinstance(pos, dict):
        pos = [pos.get("x"), pos.get("y"), pos.get("z")]
    if isinstance(pos, (list, tuple)) and len(pos) == 3 and all(_num(p) is not None for p in pos):
        return [float(pos[0]), float(pos[1]), float(pos[2])]
    return None


def _children(ctx: AnalysisContext) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for e in ctx.elements:
        if e.get("parent_id"):
            out.setdefault(e["parent_id"], []).append(e)
    return out


def _envelope(ctx: AnalysisContext) -> tuple[tuple[float, float, float], str, str | None]:
    systems = [e for e in _space_elements(ctx) if e.get("element_type") == "system"]
    for s in systems:
        d = _dims_m(s)
        if d:
            return d, f"system element {s.get('name')}", s["id"]
    # A CubeSat structure (or any structure-domain unit with dimensions) fixes the envelope:
    # the class fallback alone took a 6U for a 1 m "small" spacecraft (Nov 2026: the study's
    # spacecraft_class defaults to "small"), 24 x the radiating area of the real bus.
    for e in _space_elements(ctx):
        if e.get("element_type") != "component":
            continue
        kb = _kb_component(e.get("kb_component_id")) or {}
        if e.get("subsystem_domain") == "structure" or "structure" in str(kb.get("category") or ""):
            d = _dims_m(e)
            if d:
                return d, f"structure element {e.get('name')}", systems[0]["id"] if systems else None
    cls = _sc_class(ctx)
    return CLASS_ENVELOPE_M.get(cls, CLASS_ENVELOPE_M["nano"]), f"class default ({cls})", systems[0]["id"] if systems else None


# ── placement ───────────────────────────────────────────────────────────

def _mass_items(ctx: AnalysisContext) -> list[tuple[dict, float, str]]:
    """``(element, mass, source)`` for every element that carries mass into the
    budget: components (x quantity), and subsystems without component children
    (their own ``mass_kg``)."""
    kids = _children(ctx)
    items: list[tuple[dict, float, str]] = []
    for e in _space_elements(ctx):
        et = e.get("element_type")
        if et == "component":
            m = _eff_col(ctx, e, "mass_kg") * max(int(e.get("quantity") or 1), 1)
            items.append((e, m, "component"))
        elif et == "subsystem":
            comp_kids = [k for k in kids.get(e["id"], []) if k.get("element_type") == "component"
                         and not k.get("deleted_at") and k.get("in_scope", True) is not False]
            if not comp_kids or sum(_eff_col(ctx, k, "mass_kg") for k in comp_kids) <= 0:
                m = _eff_col(ctx, e, "mass_kg")
                if m > 0:
                    items.append((e, m, "fallback"))
    return items


def place_elements(ctx: AnalysisContext) -> Placement:
    """Body-frame positions (m, origin at the envelope corner, +z = stack axis).

    ``position_json`` wins; elements without one are stacked along +z in
    subsystem-domain order, centred in x/y. Fallback subsystems are stacked
    like components with a default board size.
    """
    env, env_src, env_id = _envelope(ctx)
    pl = Placement(envelope_m=env, envelope_source=env_src, envelope_element_id=env_id)
    by_id = ctx.elements_by_id
    items = _mass_items(ctx)
    # deterministic order: subsystem domain -> subsystem name -> element name
    def key(it):
        e = it[0]
        parent = by_id.get(e.get("parent_id") or "", {})
        return (str(parent.get("subsystem_domain") or e.get("subsystem_domain") or ""), str(parent.get("name") or ""),
                str(e.get("name") or ""), e["id"])
    items.sort(key=key)

    z_cursor = 0.0
    for e, mass, source in items:
        dims = _dims_m(e) or DEFAULT_COMPONENT_DIMS_M
        pos = _position(e)
        src = "explicit"
        if pos is None:
            pos = [env[0] / 2.0, env[1] / 2.0, z_cursor + dims[2] / 2.0]
            z_cursor += dims[2]
            src = "auto"
            pl.auto_placed.append(e["id"])
        pl.positions[e["id"]] = pos
        pl.items.append(PlacedItem(e["id"], str(e.get("name")), str(e.get("element_type")), e.get("subsystem_domain"),
                                   round(mass, 4), dims, pos, src if source != "fallback" else f"{src} (subsystem mass)",
                                   max(int(e.get("quantity") or 1), 1)))
    if pl.auto_placed:
        pl.warnings.append(f"{len(pl.auto_placed)} element(s) auto-placed on a +z stack (no position_json): "
                           + ", ".join(by_id[i].get("name", i) for i in pl.auto_placed[:8])
                           + (" ..." if len(pl.auto_placed) > 8 else ""))
    if z_cursor > env[2] * 1.001:
        pl.warnings.append(f"auto-stack height {z_cursor:.3f} m exceeds the envelope {env[2]:.3f} m ({env_src}) — "
                           f"set dimensions on the system element or positions on the components")
    for it in pl.items:
        if it.source == "explicit" and not all(-0.01 <= it.position_m[k] <= env[k] + 0.01 for k in range(3)):
            pl.warnings.append(f"{it.name}: position {it.position_m} lies outside the envelope {list(env)}")
    return pl


# ── mass properties ────────────────────────────────────────────────────

def run_mass_properties(ctx: AnalysisContext, placement: Placement | None = None) -> MassPropertiesOut:
    pl = placement or place_elements(ctx)
    comps = [MassComponent(it.name, it.mass_kg, it.position_m[0], it.position_m[1], it.position_m[2], it.dims_m)
             for it in pl.items if it.mass_kg > 0]
    res = compute_mass_properties(comps, pl.envelope_m, body_inertia=False)
    env = pl.envelope_m
    cp = [env[0] / 2.0, env[1] / 2.0, env[2] / 2.0]
    max_dim = max(env)
    offset = math.sqrt(sum((c - p) ** 2 for c, p in zip((res.com_x_m, res.com_y_m, res.com_z_m), cp))) if comps else 0.0
    out = MassPropertiesOut(res, pl, cp, round(offset, 5), max_dim, warnings=list(pl.warnings) + list(res.warnings))
    if not comps:
        out.warnings.append("no element carries mass — mass properties are zero")
    P = out.parameters
    P.append(ParamWrite("mp_total_mass_kg", res.total_mass_kg, unit="kg", quantity_kind="mass", description="Sum of the placed element masses"))
    P.append(ParamWrite("mp_com_x_m", res.com_x_m, unit="m", description="Centre of mass x (body frame, origin at the envelope corner)"))
    P.append(ParamWrite("mp_com_y_m", res.com_y_m, unit="m", description="Centre of mass y"))
    P.append(ParamWrite("mp_com_z_m", res.com_z_m, unit="m", description="Centre of mass z (stack axis)"))
    P.append(ParamWrite("mp_ixx_kgm2", res.ixx, unit="kg m2", description="Moment of inertia about x through the CoM"))
    P.append(ParamWrite("mp_iyy_kgm2", res.iyy, unit="kg m2", description="Moment of inertia about y through the CoM"))
    P.append(ParamWrite("mp_izz_kgm2", res.izz, unit="kg m2", description="Moment of inertia about z through the CoM"))
    P.append(ParamWrite("mp_cp_cg_offset_m", out.cp_cg_offset_m, unit="m", description="Distance between the centre of pressure (envelope centre) and the CoM"))
    P.append(ParamWrite("mp_auto_placed_count", float(len(pl.auto_placed)), unit="", description="Elements placed automatically (no position_json)"))
    if comps and offset > CG_OFFSET_WARN_FRACTION * max_dim:
        heaviest = max(pl.items, key=lambda it: it.mass_kg * math.sqrt(sum((it.position_m[k] - cp[k]) ** 2 for k in range(3))))
        out.conflicts.append(Conflict(
            "warning", "AOCS_CG_OFFSET_HIGH",
            f"CP-CG offset {offset * 1000:.1f} mm exceeds {CG_OFFSET_WARN_FRACTION * 100:.0f} % of the max dimension ({max_dim * 1000:.0f} mm)",
            f"CoM at ({res.com_x_m:.3f}, {res.com_y_m:.3f}, {res.com_z_m:.3f}) m vs envelope centre ({cp[0]:.3f}, {cp[1]:.3f}, {cp[2]:.3f}) m; "
            f"largest lever: {heaviest.name} ({heaviest.mass_kg:.2f} kg at {heaviest.position_m}).",
            element_ids=[heaviest.element_id],
            suggested_fix=f"move {heaviest.name} towards the envelope centre or balance it with mass on the opposite side; "
                          f"set positions explicitly (PATCH /elements/{{id}}/position) instead of the auto stack"))
    return out


# ── AOCS ────────────────────────────────────────────────────────────────

def _body_for(ctx: AnalysisContext) -> str:
    ot = str(ctx.orbit.get("orbit_type") or "").lower()
    return "moon" if "lunar" in ot else "mars" if "mars" in ot else "sun" if "interplanetary" in ot else "earth"


def _wheel_capacity(ctx: AnalysisContext, cls: str) -> tuple[float, str, str | None]:
    root = ctx.mission_root
    v = _override(ctx, root, "aocs_wheel_capacity_nms")
    if v is not None:
        return v, "manual aocs_wheel_capacity_nms on the mission root", root["id"] if root else None
    for e in _space_elements(ctx):
        if e.get("subsystem_domain") != "aocs":
            continue
        v = _override(ctx, e, "momentum_nms", "wheel_momentum_nms")
        if v is not None:
            return v, f"manual momentum_nms on {e.get('name')}", e["id"]
        perf = _perf(e)
        v = _num(perf.get("momentum_nms"))
        if v is not None:
            return v, f"performance.momentum_nms of {e.get('name')}", e["id"]
        kb = _kb_component(e.get("kb_component_id"))
        if kb and (kb.get("category") == "reaction_wheel" or "momentum_nms" in (kb.get("performance") or {})):
            v = _num((kb.get("performance") or {}).get("momentum_nms"))
            if v is not None:
                return v, f"KB {kb.get('name')} ({e.get('name')})", e["id"]
    return CLASS_WHEEL_NMS.get(cls, 0.01), f"class default ({cls})", None


def _pointing_requirement(ctx: AnalysisContext) -> tuple[float | None, str, list[str]]:
    best: float | None = None
    src = "none"
    ids: list[str] = []
    for r in ctx.requirements:
        path = str(r.get("threshold_param_path") or "")
        if "pointing" not in path.lower():
            continue
        v = _num(r.get("threshold_value"))
        if v is None:
            try:
                v = float(str(r.get("threshold_value")).strip())
            except (TypeError, ValueError):
                continue
        if v <= 0:
            continue
        if best is None or v < best:
            best, src, ids = v, f"requirement {r.get('id')} ({path})", [str(r.get("id"))]
    if best is not None:
        return best, src, ids
    for path in ("payload.pointing_deg", "payload.0.pointing_deg", "aocs.pointing_accuracy_deg"):
        v = _num(ctx.flat.get(path))
        if v is not None and v > 0:
            return v, f"flat {path}", []
    payloads = getattr(getattr(ctx.study, "requirements", None), "payloads", None) or []
    vals = [_num(getattr(p, "pointing_accuracy_deg", None)) for p in payloads]
    vals = [v for v in vals if v is not None and v > 0]
    if vals:
        return min(vals), "study payload requirements", []
    return None, "none", []


def _knowledge_deg(ctx: AnalysisContext) -> tuple[float, str]:
    best = None
    src = "no attitude sensor in the tree"
    for e in _space_elements(ctx):
        if e.get("element_type") != "component":
            continue
        kb = _kb_component(e.get("kb_component_id")) or {}
        perf = _perf(e)
        v = _num(perf.get("accuracy_deg")) or _num((kb.get("performance") or {}).get("accuracy_deg"))
        if v is None:
            arcsec = _num(perf.get("accuracy_arcsec")) or _num((kb.get("performance") or {}).get("accuracy_arcsec"))
            v = arcsec / 3600.0 if arcsec else None
        if v is None:
            text = f"{e.get('name', '')} {kb.get('category', '')} {kb.get('name', '')}".lower()
            for word, k in SENSOR_KNOWLEDGE_DEG:
                if word in text:
                    v = k
                    break
        if v is not None and (best is None or v < best):
            best, src = v, str(e.get("name"))
    return (best if best is not None else DEFAULT_KNOWLEDGE_DEG), src


def run_aocs_closure(ctx: AnalysisContext, mp: MassPropertiesOut) -> AocsOut:
    cls = _sc_class(ctx)
    res = mp.result
    env = mp.placement.envelope_m
    max_dim = mp.max_dimension_m
    mass = res.total_mass_kg or (_num(ctx.flat.get("mass.dry_mass_kg")) or 0.0)
    alt = _num(ctx.orbit.get("altitude_km")) or 500.0
    period = _num(ctx.orbit.get("period_s")) or 5700.0
    body = _body_for(ctx)
    warnings: list[str] = []

    principal = sorted([res.principal_ixx, res.principal_iyy, res.principal_izz])
    delta_i = principal[2] - principal[0]
    # the shared torque model uses mass * L^2 * ratio / 12 for (Iz - Iy): invert it for the real inertia
    inertia_ratio = 12.0 * delta_i / (mass * max_dim ** 2) if mass > 0 and max_dim > 0 else 0.0
    area = max(env[0] * env[1], env[1] * env[2], env[0] * env[2])         # largest face (worst case)
    offset = mp.cp_cg_offset_m
    offset_floor = CP_UNCERTAINTY_FRACTION * max_dim
    if offset < offset_floor:
        warnings.append(f"CP-CG offset {offset * 1000:.1f} mm below the {CP_UNCERTAINTY_FRACTION * 100:.0f} % uncertainty floor "
                        f"({offset_floor * 1000:.1f} mm) — floor used for aero / SRP torques")
        offset = offset_floor
    dipole = _override(ctx, ctx.subsystem("aocs"), "residual_dipole_am2") or _num(ctx.flat.get("aocs.residual_dipole_am2")) \
        or CLASS_DIPOLE_AM2.get(cls, 0.01)
    t = compute_disturbance_torques(alt, mass, area, max_dim, dipole, offset, inertia_ratio, body=body) if mass > 0 else \
        {"gravity_gradient": 0.0, "solar_pressure": 0.0, "magnetic": 0.0, "aerodynamic": 0.0, "total": 0.0}
    rss = math.sqrt(t["gravity_gradient"] ** 2 + t["solar_pressure"] ** 2 + t["magnetic"] ** 2 + t["aerodynamic"] ** 2)
    torques = {"gravity_gradient": t["gravity_gradient"], "aerodynamic": t["aerodynamic"], "solar_pressure": t["solar_pressure"],
               "magnetic": t["magnetic"], "sum": t["total"], "rss": rss}

    momentum = rss * period / DESATURATIONS_PER_ORBIT
    cap, cap_src, wheel_el = _wheel_capacity(ctx, cls)
    margin_pct = (cap - momentum) / momentum * 100.0 if momentum > 0 else float("inf")
    if not math.isfinite(margin_pct):
        margin_pct = 999.0

    req, req_src, req_ids = _pointing_requirement(ctx)
    knowledge, k_src = _knowledge_deg(ctx)
    i_min = principal[0] if principal[0] > 0 else (mass * max_dim ** 2 / 12 or 1e-4)
    omega = 2.0 * math.pi * CONTROL_BANDWIDTH_HZ
    control = math.degrees(rss / (i_min * omega ** 2)) if i_min > 0 else 0.0
    wheel_ripple = 0.002 if cap > 0 else 0.0
    est = math.sqrt(knowledge ** 2 + control ** 2 + wheel_ripple ** 2)
    budget = {"knowledge_deg": knowledge, "control_deg": control, "actuator_deg": wheel_ripple, "rss_deg": est}
    p_margin = (req - est) if req is not None else None
    if req is None:
        warnings.append("no pointing requirement (threshold path containing 'pointing', payload.pointing_deg or study payloads) — "
                        "pointing margin not assessed")

    out = AocsOut(torques, momentum, cap, cap_src, wheel_el, margin_pct, req, req_src, est, budget, p_margin,
                  inputs={"altitude_km": alt, "period_s": period, "body": body, "mass_kg": mass, "area_m2": area,
                          "max_dimension_m": max_dim, "cp_cg_offset_used_m": offset, "residual_dipole_am2": dipole,
                          "principal_moments_kgm2": principal, "inertia_ratio": inertia_ratio,
                          "knowledge_source": k_src, "desaturations_per_orbit": DESATURATIONS_PER_ORBIT,
                          "control_bandwidth_hz": CONTROL_BANDWIDTH_HZ, "spacecraft_class": cls},
                  warnings=warnings)
    P = out.parameters
    P.append(ParamWrite("aocs_disturbance_torque_nm", rss, unit="N m", description="RSS of the worst-case disturbance torques"))
    P.append(ParamWrite("aocs_gg_torque_nm", t["gravity_gradient"], unit="N m", description="Gravity-gradient torque (real principal inertia)"))
    P.append(ParamWrite("aocs_aero_torque_nm", t["aerodynamic"], unit="N m", description="Aerodynamic torque (largest face x CP-CG offset)"))
    P.append(ParamWrite("aocs_srp_torque_nm", t["solar_pressure"], unit="N m", description="Solar radiation pressure torque"))
    P.append(ParamWrite("aocs_mag_torque_nm", t["magnetic"], unit="N m", description="Magnetic torque from the residual dipole"))
    P.append(ParamWrite("aocs_momentum_per_orbit_nms", momentum, unit="N m s", description="Momentum accumulated between desaturations (one per orbit)"))
    P.append(ParamWrite("aocs_wheel_capacity_nms", cap, unit="N m s", description=f"Reaction wheel momentum capacity ({cap_src})"))
    P.append(ParamWrite("aocs_wheel_margin_pct", round(margin_pct, 2), unit="%", description="(capacity - momentum per orbit) / momentum"))
    if req is not None:
        P.append(ParamWrite("aocs_pointing_req_deg", req, unit="deg", description=f"Tightest pointing requirement ({req_src})"))
    P.append(ParamWrite("aocs_pointing_est_deg", est, unit="deg", description="Pointing estimate: RSS of knowledge, disturbance-induced control error and actuator ripple"))
    if p_margin is not None:
        P.append(ParamWrite("aocs_pointing_margin_deg", p_margin, unit="deg", description="Requirement minus estimate"))

    C = out.conflicts
    ids = [wheel_el] if wheel_el else ([ctx.subsystem("aocs")["id"]] if ctx.subsystem("aocs") else [])
    if momentum > cap:
        need = momentum * 1.25
        larger = _kb_larger_wheel(need)
        fix = f"select a wheel with >= {need:.4f} N m s"
        if larger:
            fix += f" (KB: {larger.get('name')} {_num((larger.get('performance') or {}).get('momentum_nms')):.4f} N m s, {larger.get('mass_kg', 0):.2f} kg)"
        n_desat = math.ceil(momentum / cap) if cap > 0 else 0
        if n_desat > 1:
            fix += f" or desaturate {n_desat} x per orbit (every {period / n_desat / 60:.0f} min)"
        C.append(Conflict("major", "AOCS_WHEEL_SATURATION",
                          f"Reaction wheel saturates: {momentum:.4f} N m s per orbit vs {cap:.4f} N m s capacity",
                          f"Disturbance RSS {rss:.2e} N m (GG {t['gravity_gradient']:.1e}, aero {t['aerodynamic']:.1e}, SRP {t['solar_pressure']:.1e}, "
                          f"mag {t['magnetic']:.1e}) over a {period / 60:.0f} min orbit; capacity from {cap_src}.",
                          element_ids=ids, suggested_fix=fix))
    if p_margin is not None and p_margin < 0:
        C.append(Conflict("major", "AOCS_POINTING_MARGIN",
                          f"Pointing estimate {est:.3f} deg exceeds requirement {req:.3f} deg",
                          f"Knowledge {knowledge:.3f} deg ({k_src}), disturbance-induced control error {control:.3f} deg "
                          f"(RSS torque {rss:.2e} N m, I_min {i_min:.4f} kg m2, {CONTROL_BANDWIDTH_HZ} Hz bandwidth).",
                          element_ids=ids, requirement_ids=req_ids,
                          suggested_fix=("add a star tracker (knowledge ~0.005 deg)" if knowledge > 0.01 else "raise the control bandwidth")
                                        + (f"; reduce the CP-CG offset ({offset * 1000:.1f} mm)" if control > knowledge else "")))
    return out


def _kb_larger_wheel(need_nms: float) -> dict | None:
    try:
        from spacecdf_kb.loader import KnowledgeBase
        wheels = [w for w in KnowledgeBase().search_components("reaction_wheels")
                  if _num((w.get("performance") or {}).get("momentum_nms")) is not None]
        ok = [w for w in wheels if (w["performance"]["momentum_nms"]) >= need_nms]
        return min(ok, key=lambda w: w["performance"]["momentum_nms"]) if ok else None
    except Exception:
        return None


# ── thermal ─────────────────────────────────────────────────────────────

def _op_range(e: dict, ctx: AnalysisContext) -> tuple[float, float, str]:
    perf = _perf(e)
    lo = _override(ctx, e, "op_temp_min_c")
    hi = _override(ctx, e, "op_temp_max_c")
    if lo is None:
        lo = _num(perf.get("op_temp_min_c"))
    if hi is None:
        hi = _num(perf.get("op_temp_max_c"))
    if lo is not None and hi is not None:
        return lo, hi, "performance"
    rng = perf.get("operating_temp_c")
    kb = _kb_component(e.get("kb_component_id")) or {}
    if not (isinstance(rng, (list, tuple)) and len(rng) == 2):
        rng = (kb.get("performance") or {}).get("operating_temp_c")
    if isinstance(rng, (list, tuple)) and len(rng) == 2 and all(_num(x) is not None for x in rng):
        return (lo if lo is not None else float(rng[0])), (hi if hi is not None else float(rng[1])), "KB" if kb else "performance"
    text = f"{e.get('name', '')} {kb.get('category', '')}".lower()
    if "batt" in text:
        d = BATTERY_OP_RANGE_C
    else:
        d = DOMAIN_OP_RANGE_C.get(str(e.get("subsystem_domain") or ""), DEFAULT_OP_RANGE_C)
    return (lo if lo is not None else d[0]), (hi if hi is not None else d[1]), "class default"


def _cp(e: dict, ctx: AnalysisContext) -> float:
    v = _override(ctx, e, "specific_heat_j_kg_k") or _num(_perf(e).get("specific_heat_j_kg_k"))
    if v is None:
        kb = _kb_component(e.get("kb_component_id")) or {}
        v = _num((kb.get("performance") or {}).get("specific_heat_j_kg_k"))
        if v is None and ("batt" in str(e.get("name", "")).lower() or kb.get("category") == "battery"):
            v = BATTERY_CP_J_PER_KG_K
    return v if v is not None else DOMAIN_CP_J_PER_KG_K.get(str(e.get("subsystem_domain") or ""), DEFAULT_CP_J_PER_KG_K)


def _safe_fraction(ctx: AnalysisContext) -> float:
    powers = [m.power_w for m in ctx.modes if m.source != "default" and m.power_w > 0]
    if len(powers) >= 2:
        return max(0.05, min(1.0, min(powers) / max(powers)))
    return SAFE_POWER_FRACTION


def _mode_dissipation(ctx: AnalysisContext) -> dict[str, dict]:
    """``{element_id: {hot_w, cold_w}}`` from the mode members (services/mode_model); {} if none."""
    if not any(getattr(m, "members", None) for m in ctx.modes):
        return {}
    try:
        from .mode_model import dissipation_cases
        return dissipation_cases(ctx.elements, ctx.modes)
    except Exception:  # noqa: BLE001 — a broken mode config must not stop the thermal analysis
        return {}


def run_thermal_closure(ctx: AnalysisContext) -> ThermalOut:
    warnings: list[str] = []
    kids = _children(ctx)
    by_id = ctx.elements_by_id
    space = _space_elements(ctx)
    systems = [e for e in space if e.get("element_type") == "system"]
    subsystems = [e for e in space if e.get("element_type") == "subsystem"]
    env, env_src, _ = _envelope(ctx)
    a_ext = 2.0 * (env[0] * env[1] + env[1] * env[2] + env[0] * env[2])
    eps_ = _num(ctx.flat.get("thermal.emissivity")) or DEFAULT_EMISSIVITY
    alpha = _num(ctx.flat.get("thermal.absorptivity")) or DEFAULT_ABSORPTIVITY
    ecl = _num(ctx.orbit.get("eclipse_fraction"))
    ecl = 0.35 if ecl is None else min(max(ecl, 0.0), 0.95)
    period = _num(ctx.orbit.get("period_s")) or 5700.0
    safe_frac = _safe_fraction(ctx)

    nodes: list[ThermalNodeOut] = []
    total_sub_mass = 0.0
    comp_nodes: list[tuple[dict, dict]] = []   # (component, subsystem)
    mode_diss = _mode_dissipation(ctx)

    def _diss(k: dict, hot_case: bool) -> float:
        """Heat of unit ``k`` in the hot / cold case: per-mode value, else peak / avg × safe fraction."""
        q = max(int(k.get("quantity") or 1), 1)
        row = mode_diss.get(k["id"])
        if row is not None:
            return float(row["hot_w"] if hot_case else row["cold_w"])
        if hot_case:
            return (_eff_col(ctx, k, "power_peak_w") or _eff_col(ctx, k, "power_avg_w")) * q
        return _eff_col(ctx, k, "power_avg_w") * q * safe_frac
    structure_sub = next((s for s in subsystems if s.get("subsystem_domain") == "structure"), None)
    m_structure_sub = 0.0
    for s in subsystems:
        comps = [k for k in kids.get(s["id"], []) if k.get("element_type") == "component" and k.get("in_scope", True) is not False]
        qty = lambda k: max(int(k.get("quantity") or 1), 1)   # noqa: E731
        m_comps = sum(_eff_col(ctx, k, "mass_kg") * qty(k) for k in comps)
        m_sub = m_comps if m_comps > 0 else _eff_col(ctx, s, "mass_kg")
        p_comps = sum(_eff_col(ctx, k, "power_avg_w") * qty(k) for k in comps)
        p_sub = p_comps if p_comps > 0 else _eff_col(ctx, s, "power_avg_w")
        pk_comps = sum((_eff_col(ctx, k, "power_peak_w") or _eff_col(ctx, k, "power_avg_w")) * qty(k) for k in comps)
        pk_sub = pk_comps if pk_comps > 0 else (_eff_col(ctx, s, "power_peak_w") or p_sub)
        hot_comps = [k for k in comps if _eff_col(ctx, k, "power_avg_w") * qty(k) > NODE_POWER_THRESHOLD_W]
        # the subsystem node keeps what its hot components do not carry
        m_hot = sum(_eff_col(ctx, k, "mass_kg") * qty(k) for k in hot_comps)
        p_hot = sum(_eff_col(ctx, k, "power_avg_w") * qty(k) for k in hot_comps)
        pk_hot = sum((_eff_col(ctx, k, "power_peak_w") or _eff_col(ctx, k, "power_avg_w")) * qty(k) for k in hot_comps)
        lo, hi, src = _op_range(s, ctx)
        shell = hot_comps and m_sub - m_hot <= 1e-3 and p_sub - p_hot <= 1e-6
        # Nov 2026 (EB-05): dissipation per mode from the mode × element matrix when the units
        # have it — hot = largest over the operational modes, cold = smallest over safe/survival.
        md_hot, md_cold = pk_sub - pk_hot, (p_sub - p_hot) * safe_frac
        if any(x["id"] in mode_diss for x in [s, *comps]):
            rest = [k for k in comps if k not in hot_comps] if comps else [s]
            md_hot = sum(_diss(k, True) for k in rest)
            md_cold = sum(_diss(k, False) for k in rest)
        if s is structure_sub:
            # The structure subsystem IS the bus structure node (below): its mass is the
            # chassis' thermal capacity. As a separate node it left the chassis at 0.05 kg
            # carrying all the absorbed sunlight.
            m_structure_sub = max(m_sub - m_hot, 0.0)
        elif not shell:
            nodes.append(ThermalNodeOut(s["id"], str(s.get("name")), s.get("subsystem_domain"), "subsystem",
                                        max(m_sub - m_hot, 0.02), _cp(s, ctx), 0.0,
                                        max(md_hot, 0.0), max(md_cold, 0.0), lo, hi, src))
        total_sub_mass += m_sub
        for k in hot_comps:
            lo, hi, src = _op_range(k, ctx)
            nodes.append(ThermalNodeOut(k["id"], str(k.get("name")), k.get("subsystem_domain") or s.get("subsystem_domain"), "component",
                                        max(_eff_col(ctx, k, "mass_kg") * qty(k), 0.02), _cp(k, ctx), 0.0,
                                        _diss(k, True), _diss(k, False), lo, hi, src))
            comp_nodes.append((k, s if not (shell or s is structure_sub) else None))   # empty shell / structure: mount on the chassis
    if not nodes:
        warnings.append("no space subsystem in the model — thermal network empty")
        return ThermalOut([], [], None, {}, {"envelope_m": env}, warnings=warnings)

    # bus structure backbone (the system element; carries 10 % of the mass when there is no structure subsystem)
    sys_el = systems[0] if systems else None
    chassis_id = "chassis"
    chassis_name = f"{sys_el.get('name')} (bus structure)" if sys_el else "Bus structure"
    m_struct = m_structure_sub if structure_sub else max(0.1 * total_sub_mass, 0.05)
    nodes.insert(0, ThermalNodeOut(sys_el["id"] if sys_el else chassis_id, chassis_name, "structure", "structure",
                                   max(m_struct, 0.05), DEFAULT_CP_J_PER_KG_K, 0.0, 0.0, 0.0, *DOMAIN_OP_RANGE_C["structure"], "class default"))

    # external area shares: every subsystem / component node by its mass (CubeSat
    # equipment is mounted to the outer structure), the structure node keeps 20 %
    sub_nodes = [n for n in nodes if n.kind == "subsystem"]
    m_all = sum(n.mass_kg for n in nodes if n.kind != "structure") or 1.0
    nodes[0].area_m2 = 0.2 * a_ext
    for n in nodes[1:]:
        n.area_m2 = 0.8 * a_ext * n.mass_kg / m_all

    def nid(n: ThermalNodeOut) -> str:
        return chassis_id if n.kind == "structure" else n.element_id

    def q_earth(a: float, hot: bool) -> float:
        return eps_ * (EARTH_IR_HOT if hot else EARTH_IR_COLD) * EARTH_VIEW_FACTOR * a

    def q_sun(a: float, hot: bool) -> float:
        flux = SOLAR_FLUX_HOT if hot else SOLAR_FLUX_COLD
        albedo = ALBEDO_HOT if hot else ALBEDO_COLD
        return alpha * flux * PROJECTED_AREA_FRACTION * a * (1.0 + albedo * EARTH_VIEW_FACTOR)

    def build(case: str) -> tuple[list[ThermalNode], list[ThermalConductance]]:
        hot = case == "hot"
        tn: list[ThermalNode] = []
        for n in nodes:
            # hot: continuous sun on every external face share; cold: solar goes on the chassis in sunlight only
            ext = q_earth(n.area_m2, hot) + (q_sun(n.area_m2, True) if hot else 0.0)
            diss = n.dissipation_hot_w if hot else n.dissipation_cold_w
            tn.append(ThermalNode(id=nid(n), name=n.name, mass_kg=n.mass_kg, specific_heat_j_kg_k=n.cp_j_per_kg_k,
                                  temperature_c=20.0, power_dissipation_w=diss + ext,
                                  emissivity=eps_ if n.area_m2 > 0 else 0.0, area_m2=n.area_m2, is_radiator=n.area_m2 > 0))
        links: list[ThermalConductance] = []
        seen: set[tuple[str, str]] = set()

        def link(a: str, b: str, g: float) -> None:
            k = (min(a, b), max(a, b))
            if a == b or k in seen:
                return
            seen.add(k)
            links.append(ThermalConductance(a, b, g))

        for n in sub_nodes:
            link(chassis_id, n.element_id, JOINT_CONDUCTANCE_W_K)
        for k, s in comp_nodes:
            link(s["id"] if s is not None else chassis_id, k["id"], JOINT_CONDUCTANCE_W_K)
        node_ids = {t.id for t in tn}
        for itf in ctx.interfaces:
            if str(itf.get("interface_type") or "").lower() != "thermal":
                continue
            a, b = itf.get("from_element_id"), itf.get("to_element_id")
            on_chassis = {x["id"] for x in (sys_el, structure_sub) if x}
            a = chassis_id if a in on_chassis else a
            b = chassis_id if b in on_chassis else b
            if a in node_ids and b in node_ids:
                props = itf.get("properties") or itf.get("properties_json") or {}
                g = _num(props.get("conductance_w_per_k")) or _num(props.get("conductance_w_k")) or INTERFACE_CONDUCTANCE_W_K
                link(a, b, g)
        return tn, links

    hot_n, links = build("hot")
    hot = solve_steady_state(hot_n, links, max_iterations=500)
    warnings.extend(w for w in hot.warnings if "converge" in w)

    # cold case: periodic orbit with eclipse, safe-mode power, cold constants (start from the orbit-average steady state)
    cold_n, _ = build("cold")
    solar_cold = sum(q_sun(n.area_m2, False) for n in nodes)
    avg_n, _ = build("cold")
    for t in avg_n:
        if t.id == chassis_id:
            t.power_dissipation_w += solar_cold * (1.0 - ecl)
    avg = solve_steady_state(avg_n, links, max_iterations=500)
    for t in cold_n:
        t.temperature_c = avg.node_temps.get(t.id, 0.0)
    dt = max(5.0, period / 1000.0)
    tr = None
    for _ in range(TRANSIENT_ORBITS):
        tr = solve_transient(cold_n, links, duration_s=period, dt_s=dt, eclipse_fraction=ecl, solar_absorbed_w=solar_cold)
        for t in cold_n:
            t.temperature_c = tr.temperatures[t.id][-1]
    assert tr is not None

    worst: float | None = None
    for n in nodes:
        temps = tr.temperatures.get(nid(n)) or [avg.node_temps.get(nid(n), 0.0)]
        n.t_hot_c = hot.node_temps.get(nid(n), 0.0)
        n.t_transient_min_c, n.t_transient_max_c = min(temps), max(temps)
        n.t_cold_c = round(n.t_transient_min_c, 2)
        n.margin_hot_c = round(n.allow_max_c - n.t_hot_c, 2)
        n.margin_cold_c = round(n.t_cold_c - n.allow_min_c, 2)
        m = min(n.margin_hot_c, n.margin_cold_c)
        if worst is None or m < worst:
            worst = m

    # series (bounded)
    n_pts = len(tr.time_s)
    stride = max(1, math.ceil(n_pts / MAX_SERIES_POINTS))
    idx = list(range(0, n_pts, stride))
    if idx and idx[-1] != n_pts - 1:
        idx.append(n_pts - 1)
    transient = {
        "case": "cold (periodic orbit, safe-mode power, cold constants)",
        "t_s": [tr.time_s[i] for i in idx],
        "period_s": period, "eclipse_fraction": ecl, "eclipse_start_s": (1.0 - ecl) * period,
        "nodes": [{"id": n.element_id, "name": n.name, "kind": n.kind,
                   "temps_c": [tr.temperatures[nid(n)][i] for i in idx]} for n in nodes],
    }
    solar_total = sum(q_sun(n.area_m2, True) for n in nodes)
    out = ThermalOut(nodes, [{"a": l.node_a_id, "b": l.node_b_id, "w_per_k": l.conductance_w_k} for l in links], worst, transient,
                     inputs={"envelope_m": env, "envelope_source": env_src, "external_area_m2": round(a_ext, 4),
                             "emissivity": eps_, "absorptivity": alpha, "eclipse_fraction": ecl, "period_s": period,
                             "safe_power_fraction": safe_frac,
                             "dissipation_source": "mode matrix (hot: max over modes, cold: safe/survival)" if mode_diss else "unit power columns",
                             "solar_absorbed_hot_w": round(solar_total, 2),
                             "solar_absorbed_cold_w": round(solar_cold, 2),
                             "earth_ir_hot_w": round(sum(q_earth(n.area_m2, True) for n in nodes), 2),
                             "cold_orbit_avg_c": {nid(n): avg.node_temps.get(nid(n)) for n in nodes},
                             "joint_conductance_w_k": JOINT_CONDUCTANCE_W_K},
                     warnings=warnings)
    P = out.parameters
    for n in nodes:
        if n.kind == "structure" and not sys_el:
            continue
        P.append(ParamWrite("thermal_t_hot_c", n.t_hot_c, element_id=n.element_id, unit="degC", description="Hot-case steady-state temperature"))
        P.append(ParamWrite("thermal_t_cold_c", n.t_cold_c, element_id=n.element_id, unit="degC", description="Cold-case steady-state temperature"))
        P.append(ParamWrite("thermal_margin_hot_c", n.margin_hot_c, element_id=n.element_id, unit="K", description="Allowable max minus hot-case temperature"))
        P.append(ParamWrite("thermal_margin_cold_c", n.margin_cold_c, element_id=n.element_id, unit="K", description="Cold-case temperature minus allowable min"))
    P.append(ParamWrite("thermal_worst_margin_c", worst if worst is not None else 0.0, unit="K", description="Smallest hot/cold margin over all nodes"))
    P.append(ParamWrite("thermal_nodes", float(len(nodes)), unit="", description="Nodes in the thermal network"))

    for n in nodes:
        if n.kind == "structure":
            continue
        if n.margin_hot_c < 0 or n.margin_cold_c < 0:
            fixes = []
            if n.margin_hot_c < 0:
                t_allow_k = n.allow_max_c + 273.15
                q_in = n.dissipation_hot_w + q_earth(n.area_m2, True) + q_sun(n.area_m2, True)
                a_need = q_in / max(eps_ * STEFAN_BOLTZMANN * (t_allow_k ** 4 - SPACE_SINK_TEMP_K ** 4) - alpha * SOLAR_FLUX_HOT * PROJECTED_AREA_FRACTION, 1.0)
                fixes.append(f"add ~{max(a_need - n.area_m2, 0.001) * 1e4:.0f} cm2 of radiator (eps {eps_:.2f}) or a conductive path to the structure "
                             f"(hot case {n.t_hot_c:.1f} degC vs allowable {n.allow_max_c:.0f} degC)")
            if n.margin_cold_c < 0:
                g_tot = sum(l["w_per_k"] for l in out.conductances if nid(n) in (l["a"], l["b"]))
                g_rad = 4.0 * eps_ * STEFAN_BOLTZMANN * n.area_m2 * (n.t_cold_c + 273.15) ** 3
                heater = (n.allow_min_c - n.t_cold_c) * (g_tot + g_rad)
                fixes.append(f"add a ~{heater:.1f} W heater (cold case {n.t_cold_c:.1f} degC vs allowable {n.allow_min_c:.0f} degC)")
            out.conflicts.append(Conflict(
                "major", "THERMAL_OUT_OF_RANGE",
                f"{n.name}: {n.t_hot_c:.1f} / {n.t_cold_c:.1f} degC (hot / cold) outside {n.allow_min_c:.0f}..{n.allow_max_c:.0f} degC",
                f"Dissipation {n.dissipation_hot_w:.1f} W hot / {n.dissipation_cold_w:.1f} W cold, radiating area {n.area_m2 * 1e4:.0f} cm2, "
                f"allowable range from {n.allow_source}; margins hot {n.margin_hot_c:+.1f} K, cold {n.margin_cold_c:+.1f} K.",
                element_ids=[n.element_id], suggested_fix="; ".join(fixes)))
    return out


# ── orchestration ───────────────────────────────────────────────────────

async def run_physics(ctx: AnalysisContext) -> AnalysisOutput:
    """Mass properties -> AOCS -> thermal in one run; nothing is written."""
    out = AnalysisOutput()
    pl = place_elements(ctx)
    mp = run_mass_properties(ctx, pl)
    aocs = run_aocs_closure(ctx, mp)
    th = run_thermal_closure(ctx)
    out.parameters = mp.parameters + aocs.parameters + th.parameters
    out.conflicts = mp.conflicts + aocs.conflicts + th.conflicts
    out.warnings = mp.warnings + aocs.warnings + th.warnings
    r = mp.result
    out.series = {
        "analysis": ANALYSIS,
        "placement": {
            "envelope_m": list(pl.envelope_m), "envelope_source": pl.envelope_source,
            "envelope_element_id": pl.envelope_element_id, "auto_placed": pl.auto_placed,
            "items": [{"element_id": it.element_id, "name": it.name, "element_type": it.element_type, "domain": it.domain,
                       "mass_kg": it.mass_kg, "dims_m": list(it.dims_m), "position_m": it.position_m, "source": it.source,
                       "quantity": it.quantity} for it in pl.items],
        },
        "mass_properties": {
            "total_mass_kg": r.total_mass_kg, "com_m": [r.com_x_m, r.com_y_m, r.com_z_m], "cp_m": mp.cp_m,
            "cp_cg_offset_m": mp.cp_cg_offset_m, "inertia": {"ixx": r.ixx, "iyy": r.iyy, "izz": r.izz, "ixy": r.ixy, "ixz": r.ixz, "iyz": r.iyz},
            "principal": [r.principal_ixx, r.principal_iyy, r.principal_izz], "principal_axes": r.principal_axes,
        },
        "aocs": {
            "torques_nm": aocs.torques, "momentum_per_orbit_nms": aocs.momentum_per_orbit_nms,
            "wheel_capacity_nms": aocs.wheel_capacity_nms, "wheel_source": aocs.wheel_source, "wheel_element_id": aocs.wheel_element_id,
            "wheel_margin_pct": aocs.wheel_margin_pct, "pointing_req_deg": aocs.pointing_req_deg, "pointing_req_source": aocs.pointing_req_source,
            "pointing_est_deg": aocs.pointing_est_deg, "pointing_budget": aocs.pointing_budget, "pointing_margin_deg": aocs.pointing_margin_deg,
            "inputs": aocs.inputs,
        },
        "thermal": {
            "nodes": [{"element_id": n.element_id, "name": n.name, "domain": n.domain, "kind": n.kind, "mass_kg": round(n.mass_kg, 4),
                       "area_m2": round(n.area_m2, 5), "dissipation_hot_w": round(n.dissipation_hot_w, 3),
                       "dissipation_cold_w": round(n.dissipation_cold_w, 3), "allow_min_c": n.allow_min_c, "allow_max_c": n.allow_max_c,
                       "allow_source": n.allow_source, "t_hot_c": n.t_hot_c, "t_cold_c": n.t_cold_c,
                       "margin_hot_c": n.margin_hot_c, "margin_cold_c": n.margin_cold_c,
                       "t_transient_min_c": n.t_transient_min_c, "t_transient_max_c": n.t_transient_max_c} for n in th.nodes],
            "conductances": th.conductances, "worst_margin_c": th.worst_margin_c, "transient": th.transient, "inputs": th.inputs,
        },
    }
    out.summary = {
        **{p.name: p.value for p in out.parameters if p.element_id is None},
        "auto_placed": len(pl.auto_placed), "placed": len(pl.items), "envelope_m": list(pl.envelope_m),
        "wheel_source": aocs.wheel_source, "pointing_req_source": aocs.pointing_req_source,
        "thermal_nodes": len(th.nodes), "thermal_out_of_range": [c.element_ids[0] for c in th.conflicts if c.element_ids],
        "conflict_codes": [c.code for c in out.conflicts], "warnings": out.warnings,
    }
    return out
