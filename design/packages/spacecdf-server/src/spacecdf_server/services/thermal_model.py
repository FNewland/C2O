"""Thermal nodal model with hot and cold design cases (wave 3, 3.A6; PI addendum).

A teaching-grade lumped-parameter model built from the study's own product tree, solved over
whole orbits (transient, explicit Euler, until the orbit repeats):

* **Nodes** (6–12 for a CubeSat): the structure and body panels, the deployable wings, the
  radiator, the payload bench and optics, one node per powered payload unit, the battery, and one
  node per other powered space subsystem (EPS, AOCS, communications, on-board computer). Each node
  has a capacitance (mass × specific heat), optical properties for the external ones, the
  intersection of the operating limits of its units (KB ``operating_temp_c``; the element's own
  ``op_temp_min_c`` / ``op_temp_max_c`` win) and the dissipation of its units in each mode
  (the Modes tab power matrix).
* **Couplings**: conductive (W/K) along the mounting path and radiative (ε·A) to space for the
  external nodes, with C2O default values the Thermal seat edits.
* **Cases**: the hot case (smallest eclipse, highest β, the imaging and downlink passes in
  sunlight, hot environment, end-of-life optics) and the cold case (longest eclipse, lowest β,
  safe mode all orbit, cold environment). β and the eclipse come from ``orbit_season`` (agent H,
  3.H4) when it is there, else from the SSO geometry over the year (``source`` says which).
* **Margins** (ECSS-E-ST-31C logic, teaching form): the calculated range widened by the
  uncertainty margin (10 °C at PDR) must sit inside the operating limits (*design margin*); the
  acceptance range adds 5 °C (*acceptance margin*), the qualification range another 5 °C
  (*qualification margin*, judged against the unit's qualified range, the KB operating range when
  no qualification range is known).
* **Heater sizing**: for a node whose cold-case minimum with uncertainty is below its lower
  limit, the heater power that brings it back (bisection on the cold case), next to the heater the
  design already has.

Public API::

    await propose(study_id, replace=False) -> model     # nodes, couplings, cases from the study
    await run(study_id) -> model                         # solve every case, margins, heaters
    await get(study_id) -> {"nodes", "couplings", "cases", "counts", "summary"}
    await evidence(study_id) -> {"ok", "solved", "out_of_design", "heaters", ...}   # gates (R)
"""
from __future__ import annotations

import logging
import math
from typing import Any

from ..db.models_thermal import ThermalCaseRow, ThermalCouplingRow, ThermalNodeRow
from . import study_rows as sr

logger = logging.getLogger(__name__)

SIGMA = 5.670374419e-8
T_SPACE_K = 3.0
UNCERTAINTY_C = {"mdr": 15.0, "prr": 15.0, "srr": 12.0, "pdr": 10.0, "cdr": 5.0}   # ECSS: 10 °C at PDR
ACCEPTANCE_C = 5.0
QUALIFICATION_C = 5.0
CP = {"structure": 900.0, "battery": 1000.0, "default": 800.0}

#: environments of the two cases: solar flux W/m², albedo, Earth IR W/m², end-of-life optics
ENV = {"hot": {"solar": 1414.0, "albedo": 0.35, "earth_ir": 260.0, "alpha_factor": 1.1},
       "cold": {"solar": 1322.0, "albedo": 0.25, "earth_ir": 220.0, "alpha_factor": 1.0}}
#: external surface optical properties (C2O default; the Thermal seat edits them)
#: structure: body panels mostly covered with cells (α ≈ 0.9) and anodised rails; wings: cells
#: on the front, ε both faces; radiator: white paint
OPTICS = {"structure": (0.75, 0.80), "wings": (0.91, 0.85), "radiator": (0.20, 0.88)}
#: limits of the external and passive nodes when no unit gives one (C2O default, typical
#: qualification ranges of a CubeSat structure and of space solar panels)
DEFAULT_LIMITS = {"structure": (-40.0, 85.0), "radiator": (-40.0, 85.0), "bench": (-40.0, 85.0), "wings": (-80.0, 100.0)}


def _num(v: Any) -> float | None:
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _study(study_id: str):
    from ..routers.studies import get_study_store
    return get_study_store().get(study_id)


# ───────────────────────────────────────────────────────── orbit and cases

def _sso_beta_range(inc_deg: float, ltan_h: float) -> tuple[float, float]:
    """Min and max |β| over a year for a sun-synchronous orbit at a fixed local time."""
    ha = math.radians((ltan_h - 12.0) * 15.0)
    i = math.radians(inc_deg)
    vals = []
    for d in range(0, 365, 5):
        dec = math.radians(23.44) * math.sin(2 * math.pi * (d - 80) / 365.25)
        # sun direction in the orbit's node frame: the right ascension difference is the hour angle
        sb = math.cos(dec) * math.sin(i) * math.sin(ha) - math.sin(dec) * math.cos(i)
        vals.append(abs(math.degrees(math.asin(max(-1.0, min(1.0, sb))))))
    return min(vals), max(vals)


def _eclipse_min(alt_km: float, beta_deg: float) -> tuple[float, float]:
    """(eclipse minutes, period minutes) for a circular orbit (cylindrical shadow)."""
    re, mu = 6378.137, 398600.4418
    a = re + alt_km
    period = 2 * math.pi * math.sqrt(a ** 3 / mu) / 60.0
    b = math.radians(beta_deg)
    x = math.sqrt(alt_km ** 2 + 2 * re * alt_km) / (a * math.cos(b)) if math.cos(b) > 0 else 2.0
    frac = math.acos(x) / math.pi if x < 1 else 0.0
    return frac * period, period


def _ltan_hours(v: Any) -> float | None:
    if isinstance(v, (int, float)):
        return float(v)
    try:
        h, m = str(v).split(":")[:2]
        return int(h) + int(m) / 60.0
    except (ValueError, AttributeError):
        return None


async def proposed_cases(study_id: str) -> list[dict]:
    """Hot and cold cases: from H's ``orbit_season.thermal_cases`` when available, else SSO geometry."""
    try:
        from . import orbit_season   # 3.H4 (agent H)
        cases = await orbit_season.thermal_cases(study_id)
        if isinstance(cases, dict):   # H's shape: {"hot": {beta_deg, eclipse_min, ...}, "cold": {...}, ...}
            cases = [{"kind": k, **cases[k]} for k in ("hot", "cold") if isinstance(cases.get(k), dict)]
        out = []
        for c in cases or []:
            kind = str(c.get("kind") or "").lower()
            if kind in ("hot", "cold"):
                out.append({"code": f"{kind.upper()}", "kind": kind, "beta_deg": _num(c.get("beta_deg")),
                            "eclipse_min": _num(c.get("eclipse_min")), "source": "orbit_season",
                            "data_json": {k: v for k, v in c.items() if k not in ("kind", "beta_deg", "eclipse_min")}})
        if out:
            return out
    except Exception:  # noqa: BLE001 — module absent or no orbit yet
        logger.debug("orbit_season unavailable", exc_info=True)
    study = _study(study_id)
    orbit = getattr(getattr(study, "requirements", None), "orbit", None)
    alt = _num(getattr(orbit, "altitude_km", None)) or 500.0
    inc = _num(getattr(orbit, "inclination_deg", None)) or 97.4
    ltan = _ltan_hours(getattr(orbit, "ltan", None))
    if ltan is None:
        bmin, bmax = 0.0, 30.0
    else:
        bmin, bmax = _sso_beta_range(inc, ltan)
    out = []
    for kind, beta in (("hot", bmax), ("cold", bmin)):
        ecl, period = _eclipse_min(alt, beta)
        out.append({"code": kind.upper(), "kind": kind, "beta_deg": round(beta, 1), "eclipse_min": round(ecl, 2),
                    "source": "sso_geometry", "data_json": {"period_min": round(period, 2), "altitude_km": alt}})
    return out


# ───────────────────────────────────────────────────────── nodes from the product tree

def _perf(e: dict) -> dict:
    p = e.get("performance") if e.get("performance") is not None else e.get("performance_json")
    return p if isinstance(p, dict) else {}


def _op_range(e: dict) -> tuple[list[float] | None, str]:
    from .rule_inputs import kb_component
    p = _perf(e)
    if _num(p.get("op_temp_min_c")) is not None and _num(p.get("op_temp_max_c")) is not None:
        return [float(p["op_temp_min_c"]), float(p["op_temp_max_c"])], "element"
    kb = kb_component(e) or {}
    for src in (p, kb, kb.get("performance") or {}):
        r = src.get("operating_temp_c") if isinstance(src, dict) else None
        if isinstance(r, (list, tuple)) and len(r) == 2 and all(_num(x) is not None for x in r):
            return [float(r[0]), float(r[1])], f"kb:{e.get('kb_component_id')}"
    return None, ""


def _node_key(e: dict, idx: dict[str, dict]) -> str:
    """Which node an element's mass and dissipation belong to."""
    from .rule_inputs import kb_component
    name = str(e.get("name") or "").lower()
    kbid = str(e.get("kb_component_id") or "").lower()
    cat = str((kb_component(e) or {}).get("category") or "").lower()
    dom = str(e.get("subsystem_domain") or "").lower()
    if dom == "propulsion" or "sail" in name or "deorbit" in name:
        return "structure"
    if dom == "structure" or dom == "harness":
        return "structure"
    if "solar" in cat or kbid.startswith("sp-") or "panel" in name or "wing" in name:
        return "wings" if ("wing" in name or "deploy" in name or "dmsa" in kbid) else "structure"
    if "batter" in name or cat == "battery" or kbid.startswith("bat-"):
        return "battery"
    if dom == "thermal":
        if "heater" in name:
            return "bench" if ("payload" in name or "bench" in name) else "battery"
        if "paint" in name or "coating" in name or "radiator" in name:
            return "radiator"
        return "structure"
    if dom == "payload":
        if float(e.get("power_avg_w") or 0) > 0:
            return f"pay:{e['id']}"
        return "bench"
    return dom or "structure"


#: external area (m²) of a CubeSat by form factor: 1U 0.06, 3U 4 × 0.1 × 0.34 + 2 × 0.01, 6U, 12U
_FF_AREA = {1: 0.06, 2: 0.10, 3: 0.156, 6: 0.244, 12: 0.392}


def _external_area(els: list[dict]) -> float:
    import re as _re
    for e in els:
        if e.get("element_type") in ("system", "subsystem") and (e.get("segment") or "space") == "space":
            ff = str(_perf(e).get("form_factor") or "")
            m = _re.match(r"\s*(\d+)\s*U", ff, _re.I)
            if m and int(m.group(1)) in _FF_AREA:
                return _FF_AREA[int(m.group(1))]
    return _FF_AREA[3]


async def proposed_nodes(study_id: str) -> tuple[list[dict], list[dict]]:
    """(nodes, couplings) from the product tree (pure apart from the element cache)."""
    from ..routers.elements import _elements as cache
    from .rule_inputs import qty, space_hardware
    els = [e for e in cache.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    hw = [e for e in space_hardware(els) if e.get("element_type") == "component"]
    idx = {e["id"]: e for e in els}
    groups: dict[str, dict[str, Any]] = {}
    labels = {"structure": "Structure and body panels", "wings": "Deployable solar wings", "radiator": "Radiator (payload end)",
              "bench": "Payload bench and optics", "battery": "Battery", "power": "EPS electronics",
              "aocs": "AOCS unit and sensors", "ttc": "Radio", "obc": "On-board computer"}
    labels_fr = {"structure": "Structure et panneaux de caisse", "wings": "Ailes solaires déployables",
                 "radiator": "Radiateur (côté charge utile)", "bench": "Banc optique de la charge utile",
                 "battery": "Batterie", "power": "Électronique d’alimentation", "aocs": "SCAO et senseurs",
                 "ttc": "Radio", "obc": "Ordinateur de bord"}
    for e in hw:
        key = _node_key(e, idx)
        g = groups.setdefault(key, {"mass": 0.0, "elements": [], "ranges": [], "heater_w": 0.0, "power": 0.0})
        g["mass"] += float(e.get("mass_kg") or 0.0) * qty(e)
        g["elements"].append(e["id"])
        g["power"] += float(e.get("power_avg_w") or 0.0) * qty(e)
        if "heater" in str(e.get("name") or "").lower():
            g["heater_w"] += float(e.get("power_avg_w") or 0.0)
        r, src = _op_range(e)
        if r and float(e.get("power_avg_w") or 0) > 0 or (r and key in ("battery",)):
            g["ranges"].append((r, src, e.get("name")))
        g.setdefault("first", e)
    # the structure carries the mass of every space subsystem without its own node
    if "structure" not in groups:
        groups["structure"] = {"mass": 0.3, "elements": [], "ranges": [], "heater_w": 0.0, "power": 0.0}
    has_strap = any("strap" in str(idx[x].get("name") or "").lower() for g in groups.values() for x in g["elements"])
    nodes, order = [], 0
    ff_area = _external_area(els)
    for key in sorted(groups, key=lambda k: (0 if k == "structure" else 1 if k in ("wings", "radiator") else 2, k)):
        g = groups[key]
        if key not in ("structure", "wings", "radiator") and g["mass"] <= 0 and g["power"] <= 0:
            continue
        external = key in ("structure", "wings", "radiator")
        if key.startswith("pay:"):
            name = str(idx[key[4:]].get("name") or "Payload unit")
            name_fr = name
            kind_cp = "default"
        else:
            name, name_fr = labels.get(key, key.title()), labels_fr.get(key, key.title())
            kind_cp = "structure" if key in ("structure", "wings", "radiator", "bench") else (
                "battery" if key == "battery" else "default")
        ranges = g["ranges"]
        op_min = max((r[0][0] for r in ranges), default=None)
        op_max = min((r[0][1] for r in ranges), default=None)
        if key == "battery" and op_min is not None:
            op_min = max(op_min, 0.0)                     # charging at or above 0 °C (Li-ion)
        if op_min is None and key in DEFAULT_LIMITS:
            op_min, op_max = DEFAULT_LIMITS[key]
        src = "; ".join(sorted({r[1] for r in ranges if r[1]})) or ("structure default" if external or key == "bench"
                                                                        else "assumption")
        area = None
        alpha = eps = None
        if key == "structure":
            area, (alpha, eps) = ff_area, OPTICS["structure"]
        elif key == "wings":
            area, (alpha, eps) = 0.03 * max(1, sum(qty(idx[x]) for x in g["elements"])), OPTICS["wings"]
        elif key == "radiator":
            area, (alpha, eps) = 0.01, OPTICS["radiator"]
        mass = max(g["mass"], 0.02)
        nodes.append({
            "code": f"N{order + 1:02d}", "name": name, "element_id": g["elements"][0] if g["elements"] else None,
            "kind": "diffusion", "capacitance_j_k": round(mass * CP[kind_cp], 2), "area_m2": area,
            "absorptivity": alpha, "emissivity": eps, "op_min_c": op_min, "op_max_c": op_max,
            "survival_min_c": (op_min - 10.0) if op_min is not None else None,
            "survival_max_c": (op_max + 10.0) if op_max is not None else None,
            "limits_source": src, "heater_w": round(g["heater_w"], 3) or None, "origin": "proposed", "order": order,
            "data_json": {"key": key, "name_fr": name_fr, "elements": g["elements"], "external": external,
                          "mass_kg": round(mass, 4)},
        })
        order += 1
    by_key = {n["data_json"]["key"]: n for n in nodes}
    couplings = []

    def link(a: str, b: str, kind: str, value: float, why: str) -> None:
        if a in by_key and (b == "space" or b in by_key):
            couplings.append({"node_a": a, "node_b": b, "kind": kind, "value": value, "source": why,
                              "origin": "proposed", "order": len(couplings)})

    for key, n in by_key.items():
        if key == "structure":
            continue
        if key in ("wings",):
            link(key, "structure", "conductive", 0.02, "hinge, C2O default")
        elif key == "radiator":
            link(key, "structure", "conductive", 0.05, "isolated mount, C2O default")
        elif key == "battery":
            link(key, "structure", "conductive", 0.15, "stack mount, C2O default")
        elif key == "bench":
            link(key, "structure", "conductive", 0.1, "bench isolators, C2O default")
            if "radiator" in by_key:
                link(key, "radiator", "conductive", 0.6 if has_strap else 0.2,
                     "copper strap to the radiator" if has_strap else "bench to radiator, C2O default")
        elif key.startswith("pay:"):
            link(key, "bench" if "bench" in by_key else "structure", "conductive", 0.5, "unit on the bench, C2O default")
        else:
            link(key, "structure", "conductive", 0.3, "stack mount, C2O default")
        if not n["data_json"]["external"]:
            link(key, "structure", "radiative", round(0.8 * 0.01, 4), "internal radiation ε·A, C2O default")
    for key in ("structure", "wings", "radiator"):
        if key in by_key:
            n = by_key[key]
            sides = 2.0 if key == "wings" else 1.0
            link(key, "space", "radiative", round(float(n["emissivity"]) * float(n["area_m2"]) * sides, 5),
                 "radiation to space ε·A" + (" (both faces)" if sides > 1 else ""))
    return nodes, couplings


# ───────────────────────────────────────────────────────── dissipation per mode

async def _mode_dissipation(study_id: str, nodes: list[dict]) -> dict[str, dict[str, float]]:
    """{mode kind or name: {node code: W}} from the Modes tab power matrix."""
    from .analysis_context import build_context
    ctx = await build_context(study_id)
    el_node: dict[str, str] = {}
    for n in nodes:
        for eid in (n.get("data_json") or {}).get("elements") or []:
            el_node[eid] = n["code"]
    out: dict[str, dict[str, float]] = {}
    for m in ctx.modes:
        if m.source != "element":
            continue
        d: dict[str, float] = {}
        for mem in m.members:
            code = el_node.get(mem["element_id"])
            if code is None:
                continue
            w = float(mem.get("dissipation_w") if mem.get("dissipation_w") is not None else mem.get("power_w") or 0.0)
            d[code] = d.get(code, 0.0) + w * float(mem.get("duty") or 1.0)
        key = (m.kind or m.name or m.id).lower()
        out.setdefault(key, d)
        out.setdefault((m.name or "").lower(), d)
        if m.orbit_fraction is not None:
            out.setdefault(f"__share__{key}", {"share": float(m.orbit_fraction)})
    return out


# ───────────────────────────────────────────────────────── solver

def _schedule(kind: str, period_s: float, eclipse_s: float, diss: dict[str, dict[str, float]]) -> list[tuple[float, bool, dict]]:
    """[(t_end, sunlit, dissipation)] over one orbit. Hot: imaging then downlink in sunlight,
    nominal elsewhere; cold: safe (or survival) all orbit."""
    nominal = diss.get("nominal") or diss.get("custom") or {}
    sun_s = period_s - eclipse_s
    if kind == "hot":
        img_share = (diss.get("__share__imaging") or {}).get("share", 0.05)
        dl_share = (diss.get("__share__downlink") or {}).get("share", 0.09)
        img, dl = img_share * period_s, dl_share * period_s
        segs = []
        t = 0.0
        for dur, d in ((min(img, sun_s), diss.get("imaging") or nominal),
                       (min(dl, max(0.0, sun_s - img)), diss.get("downlink") or nominal),
                       (max(0.0, sun_s - img - dl), nominal)):
            if dur > 0:
                t += dur
                segs.append((t, True, d))
        segs.append((period_s, False, nominal))
        return segs
    safe = diss.get("safe") or diss.get("survival") or nominal
    return [(sun_s, True, safe), (period_s, False, safe)]


def _external_loads(nodes: list[dict], env: dict, alt_km: float, sunlit: bool) -> dict[str, float]:
    re = 6378.137
    f_earth = (re / (re + alt_km)) ** 2
    out = {}
    for n in nodes:
        key = (n.get("data_json") or {}).get("key")
        if not (n.get("data_json") or {}).get("external"):
            continue
        a, e = float(n.get("absorptivity") or 0.5) * env["alpha_factor"], float(n.get("emissivity") or 0.8)
        area = float(n.get("area_m2") or 0.0)
        sun_frac, earth_frac = {"structure": (0.25, 0.25), "wings": (0.7, 0.5), "radiator": (0.1, 1.0)}.get(key, (0.25, 0.25))
        q = e * env["earth_ir"] * f_earth * area * earth_frac
        if sunlit:
            q += a * env["solar"] * area * sun_frac
            q += a * env["solar"] * env["albedo"] * f_earth * area * earth_frac * 0.5
        out[n["code"]] = q
    return out


def solve_case(nodes: list[dict], couplings: list[dict], case: dict, diss: dict[str, dict[str, float]],
               alt_km: float, extra_heat: dict[str, float] | None = None, dt: float = 10.0, orbits: int = 12
               ) -> dict[str, dict[str, float]]:
    """Transient over whole orbits until periodic; returns {node code: {t_min_c, t_max_c, t_mean_c}}."""
    period_min = (case.get("data_json") or {}).get("period_min") or _eclipse_min(alt_km, float(case.get("beta_deg") or 0))[1]
    period = float(period_min) * 60.0
    ecl = float(case.get("eclipse_min") or 0.0) * 60.0
    env = ENV.get(case.get("kind") or "hot", ENV["hot"])
    sched = _schedule(case.get("kind") or "hot", period, ecl, diss)
    codes = [n["code"] for n in nodes]
    ix = {c: i for i, c in enumerate(codes)}
    n_ = len(codes)
    # explicit Euler: keep the step under half the smallest node time constant C / ΣG
    gsum = [0.0] * n_
    for c in couplings:
        if c["kind"] == "conductive" and c["node_a"] in ix and c["node_b"] in ix:
            gsum[ix[c["node_a"]]] += float(c["value"] or 0.0)
            gsum[ix[c["node_b"]]] += float(c["value"] or 0.0)
        elif c["kind"] == "radiative" and c["node_a"] in ix:
            gsum[ix[c["node_a"]]] += 4 * SIGMA * float(c["value"] or 0.0) * 350.0 ** 3
    for i, n in enumerate(nodes):
        if gsum[i] > 0:
            dt = min(dt, 0.5 * max(float(n.get("capacitance_j_k") or 1.0), 1.0) / gsum[i])
    dt = max(dt, 0.5)
    inv_c = [dt / max(float(n.get("capacitance_j_k") or 1.0), 1.0) for n in nodes]
    cond = [(ix[c["node_a"]], ix[c["node_b"]], float(c["value"] or 0.0)) for c in couplings
            if c["kind"] == "conductive" and c["node_a"] in ix and c["node_b"] in ix]
    rad = [(ix[c["node_a"]], -1 if c["node_b"] == "space" else ix.get(c["node_b"], -1), SIGMA * float(c["value"] or 0.0))
           for c in couplings if c["kind"] == "radiative" and c["node_a"] in ix]
    load = {True: _external_loads(nodes, env, alt_km, True), False: _external_loads(nodes, env, alt_km, False)}
    extra = extra_heat or {}
    seg_q = []
    for t_end, sunlit, d in sched:
        seg_q.append((t_end, [float(d.get(c, 0.0)) + load[sunlit].get(c, 0.0) + float(extra.get(c, 0.0)) for c in codes]))
    space4 = T_SPACE_K ** 4
    T = [293.15] * n_
    stats: dict[str, dict[str, float]] = {}
    steps_per_orbit = max(1, int(round(period / dt)))
    for _orbit in range(orbits):
        tmin = [1e9] * n_
        tmax = [-1e9] * n_
        tsum = [0.0] * n_
        seg = 0
        for step in range(steps_per_orbit):
            t = step * dt
            while seg < len(seg_q) - 1 and t >= seg_q[seg][0]:
                seg += 1
            q = list(seg_q[seg][1])
            for a, b, g in cond:
                f = g * (T[a] - T[b])
                q[a] -= f
                q[b] += f
            for a, b, gr in rad:
                ta4 = T[a] ** 4
                if b < 0:
                    q[a] -= gr * (ta4 - space4)
                else:
                    f = gr * (ta4 - T[b] ** 4)
                    q[a] -= f
                    q[b] += f
            for i in range(n_):
                T[i] += q[i] * inv_c[i]
                if T[i] < tmin[i]:
                    tmin[i] = T[i]
                if T[i] > tmax[i]:
                    tmax[i] = T[i]
                tsum[i] += T[i]
        new = {c: {"t_min_c": round(tmin[i] - 273.15, 2), "t_max_c": round(tmax[i] - 273.15, 2),
                   "t_mean_c": round(tsum[i] / steps_per_orbit - 273.15, 2)} for i, c in enumerate(codes)}
        if stats and all(abs(new[c]["t_mean_c"] - stats[c]["t_mean_c"]) < 0.05 for c in codes):
            stats = new
            break
        stats = new
    return stats


def margins(node: dict, res_hot: dict | None, res_cold: dict | None, uncertainty: float) -> dict[str, Any]:
    """Design, acceptance and qualification margins of one node (°C; negative = violated)."""
    lo, hi = _num(node.get("op_min_c")), _num(node.get("op_max_c"))
    tmax = max([r["t_max_c"] for r in (res_hot, res_cold) if r] or [None]) if (res_hot or res_cold) else None
    tmin = min([r["t_min_c"] for r in (res_hot, res_cold) if r] or [None]) if (res_hot or res_cold) else None
    out: dict[str, Any] = {"t_min_c": tmin, "t_max_c": tmax, "uncertainty_c": uncertainty,
                           "op_min_c": lo, "op_max_c": hi}
    if lo is None or hi is None or tmin is None or tmax is None:
        out.update(design=None, acceptance=None, qualification=None, status="no_limits")
        return out
    pred_lo, pred_hi = tmin - uncertainty, tmax + uncertainty
    design = min(pred_lo - lo, hi - pred_hi)
    out.update(predicted_min_c=round(pred_lo, 2), predicted_max_c=round(pred_hi, 2),
               design=round(design, 2), acceptance=round(design - ACCEPTANCE_C, 2),
               qualification=round(design - ACCEPTANCE_C - QUALIFICATION_C, 2),
               cold_margin=round(pred_lo - lo, 2), hot_margin=round(hi - pred_hi, 2))
    out["status"] = "ok" if design >= 0 else ("cold" if pred_lo - lo < hi - pred_hi else "hot")
    return out


# ───────────────────────────────────────────────────────── persistence and runs

async def propose(study_id: str, *, replace: bool = False) -> dict[str, Any]:
    nodes_now = await sr.list_rows(ThermalNodeRow, study_id)
    if nodes_now and not replace:
        cases_now = await sr.list_rows(ThermalCaseRow, study_id)
        if not cases_now:
            await sr.insert_rows(ThermalCaseRow, study_id, [{**c, "status": "proposed", "origin": "proposed",
                                                             "order": i} for i, c in enumerate(await proposed_cases(study_id))],
                                 prefix="th")
        return await get(study_id)
    if replace:
        for model in (ThermalNodeRow, ThermalCouplingRow, ThermalCaseRow):
            await sr.delete_rows(model, study_id)
    nodes, couplings = await proposed_nodes(study_id)
    rows = await sr.insert_rows(ThermalNodeRow, study_id, nodes, prefix="tn")
    key_id = {r["data_json"]["key"]: r["id"] for r in rows}
    cps = [{**c, "node_a": key_id[c["node_a"]], "node_b": key_id.get(c["node_b"], c["node_b"])} for c in couplings]
    await sr.insert_rows(ThermalCouplingRow, study_id, cps, prefix="tc")
    cases = await proposed_cases(study_id)
    await sr.insert_rows(ThermalCaseRow, study_id, [{**c, "status": "proposed", "origin": "proposed", "order": i,
                                                      "mode_key": "imaging+downlink" if c["kind"] == "hot" else "safe",
                                                      "environment_json": ENV[c["kind"]]}
                                                     for i, c in enumerate(cases)], prefix="th")
    return await get(study_id)


def _gate(study: Any) -> str:
    try:
        from ..routers.gates import study_margin_gate
        return str(study_margin_gate(study) or "pdr").lower()
    except Exception:  # noqa: BLE001
        return "pdr"


#: thermostat set point above the node's design minimum (operational minimum + uncertainty), °C
THERMOSTAT_OFFSET_C = 1.0


async def run(study_id: str) -> dict[str, Any]:
    """Solve every case; store per-node temperatures, margins and the heater sizing."""
    if not await sr.list_rows(ThermalNodeRow, study_id):
        await propose(study_id)
    nodes = await sr.list_rows(ThermalNodeRow, study_id)
    couplings = await sr.list_rows(ThermalCouplingRow, study_id)
    cases = await sr.list_rows(ThermalCaseRow, study_id)
    by_id = {n["id"]: n["code"] for n in nodes}
    cps = [{**c, "node_a": by_id.get(c["node_a"], c["node_a"]), "node_b": by_id.get(c["node_b"], c["node_b"])}
           for c in couplings]
    study = _study(study_id)
    alt = _num(getattr(getattr(getattr(study, "requirements", None), "orbit", None), "altitude_km", None)) or 500.0
    diss = await _mode_dissipation(study_id, nodes)
    gate = _gate(study)
    unc = UNCERTAINTY_C.get(gate, 10.0)
    # thermostatic heaters (the node's ``heater_w``): on in the cold case. In the hot case the
    # thermostat only works when a node would fall below its design minimum (operational minimum +
    # uncertainty) with the heater off: it then delivers the orbit-average power that keeps the
    # node there (at most the installed power; its duty cycle). Integration fix: the battery's
    # coldest point is in the hot case with the heater off, which no cold-case heater fixed, and a
    # heater left full on in the hot case overheats it.
    heaters = {n["code"]: float(n.get("heater_w") or 0.0) for n in nodes
               if (n.get("heater_w") or 0) > 0 and not (n.get("data_json") or {}).get("external")}
    op_min = {n["code"]: float(n["op_min_c"]) for n in nodes if n.get("op_min_c") is not None}
    setpoint = unc + THERMOSTAT_OFFSET_C          # the thermostat holds the node 1 °C above its design minimum

    def solve(c: dict, extra: dict[str, float]) -> dict:
        if c["kind"] != "hot":
            return solve_case(nodes, cps, c, diss, alt, extra_heat=extra or None)
        r = solve_case(nodes, cps, c, diss, alt, extra_heat=None)
        on: dict[str, float] = {}
        for k, w in extra.items():
            if w <= 0 or k not in r or k not in op_min or r[k]["t_min_c"] - setpoint >= op_min[k]:
                continue
            lo, hi = 0.0, w
            for _ in range(7):
                mid = (lo + hi) / 2
                t = solve_case(nodes, cps, c, diss, alt, extra_heat={**on, k: mid}, dt=20.0, orbits=8)[k]["t_min_c"]
                lo, hi = (lo, mid) if t - setpoint >= op_min[k] else (mid, hi)
            on[k] = round(hi, 3)
        return solve_case(nodes, cps, c, diss, alt, extra_heat=on) if on else r

    sol: dict[str, dict] = {}
    for c in cases:
        res = solve(c, heaters)
        sol[c["kind"]] = res
        await sr.update_row(ThermalCaseRow, c["id"], {"results_json": res, "status": "solved"})
    # heater sizing on the cold case: smallest extra power keeping the node's minimum (with the
    # uncertainty) at or above its lower limit (the hot case then needs at most that power)
    cold_case = next((c for c in cases if c["kind"] == "cold"), None)
    for n in nodes:
        m = margins(n, (sol.get("hot") or {}).get(n["code"]), (sol.get("cold") or {}).get(n["code"]), unc)
        heater = None
        if cold_case is not None and m.get("cold_margin") is not None and m["cold_margin"] < 0 \
                and not (n.get("data_json") or {}).get("external"):
            lo, hi = 0.0, 10.0
            for _ in range(10):
                mid = (lo + hi) / 2
                r = solve_case(nodes, cps, cold_case, diss, alt,
                               extra_heat={**heaters, n["code"]: heaters.get(n["code"], 0.0) + mid}, dt=20.0, orbits=8)
                if r[n["code"]]["t_min_c"] - unc >= float(n["op_min_c"]):
                    hi = mid
                else:
                    lo = mid
            heater = round(heaters.get(n["code"], 0.0) + hi, 2) if hi < 10.0 else None
        data = dict(n.get("data_json") or {})
        data["margins"] = m
        data["heater_needed_w"] = heater
        data["gate"] = gate
        await sr.update_row(ThermalNodeRow, n["id"], {"data_json": data})
    return await get(study_id)


#: extra heater power over the sized figure when the Thermal seat takes it (see ``accept_heaters``)
HEATER_SIZING_MARGIN = 0.10


async def accept_heaters(study_id: str) -> dict[str, Any]:
    """The Thermal seat takes the sized heaters: each node's ``heater_w`` becomes the power the last
    run asked for plus ``HEATER_SIZING_MARGIN`` (rounded up to 0.1 W), then the model is solved again.
    The margin covers the sizing search, which runs the coarse transient (20 s step, 8 orbits): taken
    bare, a heater could come out a few hundredths of a watt short on the full solve (the 3.F1 dry run
    found the battery 0.08 °C below its design range after taking 2.7 W for 2.69 W asked). The heater
    power is an eclipse/cold-case load the Power seat must carry (a pending power change, wave 4)."""
    for n in await sr.list_rows(ThermalNodeRow, study_id):
        need = (n.get("data_json") or {}).get("heater_needed_w")
        if need:
            sized = float(need) * (1 + HEATER_SIZING_MARGIN)
            await sr.update_row(ThermalNodeRow, n["id"], {"heater_w": math.ceil(sized * 10 - 1e-9) / 10,
                                                          "origin": "user"})
    return await run(study_id)


async def get(study_id: str) -> dict[str, Any]:
    nodes = await sr.list_rows(ThermalNodeRow, study_id)
    couplings = await sr.list_rows(ThermalCouplingRow, study_id)
    cases = await sr.list_rows(ThermalCaseRow, study_id)
    solved = bool(cases) and all(c.get("status") == "solved" for c in cases)
    ms = [(n, (n.get("data_json") or {}).get("margins") or {}) for n in nodes]
    out_of_design = [n["code"] for n, m in ms if m.get("design") is not None and m["design"] < 0]
    heaters = [{"node": n["code"], "name": n["name"], "needed_w": (n.get("data_json") or {}).get("heater_needed_w"),
                "installed_w": n.get("heater_w")} for n in nodes
               if (n.get("data_json") or {}).get("heater_needed_w") or (n.get("heater_w") or 0) > 0]
    worst = min((m["design"] for _, m in ms if m.get("design") is not None), default=None)
    summary = {"solved": solved, "nodes": len(nodes), "couplings": len(couplings), "cases": len(cases),
               "out_of_design_range": out_of_design, "heaters": heaters, "worst_design_margin_c": worst,
               "uncertainty_c": next((m.get("uncertainty_c") for _, m in ms if m.get("uncertainty_c") is not None), None)}
    return {"study_id": study_id, "nodes": nodes, "couplings": couplings, "cases": cases,
            "counts": {"nodes": len(nodes), "couplings": len(couplings), "cases": len(cases)}, "summary": summary}


async def evidence(study_id: str) -> dict[str, Any]:
    """The thermal gate evidence (wired by R): a solved model with ≥ 6 nodes, hot and cold cases,
    every node inside its design range or a sized heater for it."""
    d = await get(study_id)
    s = d["summary"]
    kinds = {c.get("kind") for c in d["cases"]}
    uncovered = list(s["out_of_design_range"])     # the solution already includes the installed heaters
    reasons = []
    if s["nodes"] < 6:
        reasons.append(f"{s['nodes']} nodes (at least 6 expected)")
    if not {"hot", "cold"} <= kinds:
        reasons.append("hot and cold cases missing")
    if not s["solved"]:
        reasons.append("model not solved")
    if uncovered:
        reasons.append("outside the design range: " + ", ".join(uncovered))
    return {"study_id": study_id, "ok": not reasons, "solved": s["solved"], "nodes": s["nodes"],
            "cases": sorted(k for k in kinds if k), "out_of_design": s["out_of_design_range"],
            "uncovered": uncovered, "heaters": s["heaters"], "worst_design_margin_c": s["worst_design_margin_c"],
            "reasons": reasons}


NODE_FIELDS = ("code", "name", "element_id", "kind", "capacitance_j_k", "area_m2", "absorptivity", "emissivity",
               "dissipation_json", "op_min_c", "op_max_c", "survival_min_c", "survival_max_c", "limits_source",
               "heater_w")
