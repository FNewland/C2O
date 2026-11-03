"""SMO Simulator — lumped-parameter thermal network (EOSAT-1 TCS physics).

Replaces the fixed-surroundings zone model of ``tcs_basic`` (where the OBC,
battery and FPA relaxed towards a configured +10/+12 C "internal sink" that
did not care what was powered) with a physical node network:

    C_i dT_i/dt = Q_ext,i                       absorbed sun / albedo / Earth IR
                - sum_s eps_s A_s sigma T_i^4   radiation to space (external faces)
                + sum_j G_ij (T_j - T_i)        conduction
                + sum_j R_ij sigma (T_j^4 - T_i^4)   internal radiation
                + P_i                           electrical dissipation + heaters

Everything below is pure (no engine, no RNG): the TCS model computes the
geometry and the dissipation, this module owns the node equations and the
integrator. Design note, values and sources: docs/plan_2026-11/THERMAL_MODEL.md.

Integrator: explicit Euler, internally sub-stepped so that every step is at
most ``stability_fraction`` x the smallest node time constant evaluated at the
current temperatures (radiation linearised as 4 sigma eps A T^3). It is
therefore unconditionally stable for any caller ``dt`` (the engine hands the
models <= 1.67 s even at 1000x, but standalone harnesses use 10-60 s).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

SIGMA = 5.670374419e-8      # Stefan-Boltzmann [W m^-2 K^-4] (CODATA 2018)
K0 = 273.15
AU_KM = 149597870.7         # IAU 2012

# ─────────────────────────────────────────────────────────────────────────
# Earth view factor of a flat plate
# ─────────────────────────────────────────────────────────────────────────

def plate_earth_view_factor(cos_theta: float, h_ratio: float) -> float:
    """View factor from one side of a flat plate to the Earth disc.

    ``cos_theta`` is the cosine of the angle between the plate normal and the
    nadir direction; ``h_ratio`` = (R_E + h) / R_E. Closed form for a
    differential plate (the standard result used by every orbital-heating
    short course, e.g. NASA TFAWS "Fundamentals of Orbital Heating", and
    Gilmore, Spacecraft Thermal Control Handbook Vol. I, ch. 2):

      * plate sees the full disc (theta <= pi/2 - rho):  F = cos(theta) / H^2
      * plate sees none of it   (theta >= pi/2 + rho):  F = 0
      * partial view in between:
        F = 1/2 - (1/pi) asin( sqrt(H^2-1) / (H sin theta) )
            + 1/(pi H^2) [ cos(theta) acos(-sqrt(H^2-1) cot(theta))
                           - sqrt(H^2-1) sqrt(1 - H^2 cos^2(theta)) ]

    with sin(rho) = 1/H the Earth's angular radius. Continuous at both
    boundaries (tests/test_simulator/test_thermal_network.py checks it).
    """
    H = max(h_ratio, 1.0 + 1e-9)
    c = max(-1.0, min(1.0, cos_theta))
    theta = math.acos(c)
    rho = math.asin(1.0 / H)
    if theta <= 0.5 * math.pi - rho:
        return c / (H * H)
    if theta >= 0.5 * math.pi + rho:
        return 0.0
    s = math.sin(theta)
    x = math.sqrt(H * H - 1.0)
    cot = c / s
    a1 = max(-1.0, min(1.0, x / (H * s)))
    a2 = max(-1.0, min(1.0, -x * cot))
    root = math.sqrt(max(0.0, 1.0 - H * H * c * c))
    f = (0.5 - math.asin(a1) / math.pi
         + (c * math.acos(a2) - x * root) / (math.pi * H * H))
    return max(0.0, f)


def tumbling_earth_view_factor(h_ratio: float) -> float:
    """Orientation-averaged plate view factor = (1 - cos rho)/2.

    For a randomly oriented plate (or per unit area of a sphere) the mean
    view factor to the Earth is (1 - sqrt(1 - 1/H^2)) / 2: 0.311 at 513 km.
    """
    H = max(h_ratio, 1.0 + 1e-9)
    return 0.5 * (1.0 - math.sqrt(max(0.0, 1.0 - 1.0 / (H * H))))


# ─────────────────────────────────────────────────────────────────────────
# Network definition
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class Surface:
    """An external, space-facing surface belonging to a node."""
    node: str
    area_m2: float
    alpha: float               # solar absorptance (area-weighted over coatings)
    epsilon: float             # IR emittance (= IR absorptance, grey body)
    normal: tuple[float, float, float] | None = None   # body frame; None = wing
    wing: str | None = None    # 'py' / 'my' for a deployable-wing surface
    side: str = "front"        # wing only: 'front' (cells) or 'back'
    array_face: str | None = None  # EPS face whose generated power leaves as electricity


@dataclass
class Network:
    names: list[str]
    index: dict[str, int]
    cap: list[float]                         # J/K
    conductors: list[tuple[int, int, float]]  # (i, j, G W/K)
    radiators: list[tuple[int, int, float]]   # (i, j, (eps A)_eff m^2)
    surfaces: list[Surface] = field(default_factory=list)


def _coating_average(sp: dict) -> tuple[float, float]:
    """Area-weighted alpha / epsilon from a ``coatings`` list or plain keys."""
    coats = sp.get("coatings")
    if not coats:
        return float(sp["alpha"]), float(sp["epsilon"])
    tot = sum(float(c["fraction"]) for c in coats)
    if abs(tot - 1.0) > 1e-6:
        raise ValueError(f"surface {sp.get('node')}: coating fractions sum "
                         f"to {tot:.3f}, not 1")
    a = sum(float(c["fraction"]) * float(c["alpha"]) for c in coats)
    e = sum(float(c["fraction"]) * float(c["epsilon"]) for c in coats)
    return a, e


_NODE_KEYS = {"name", "capacitance_j_per_k", "mass_kg", "cp_j_per_kg_k",
              "initial_c", "note"}
_SURF_KEYS = {"node", "area_m2", "alpha", "epsilon", "coatings", "normal",
              "wing", "side", "array_face", "note"}
_COND_KEYS = {"a", "b", "g_w_per_k", "note"}
_RAD_KEYS = {"a", "b", "ea_m2", "note"}


def _check_keys(d: dict, allowed: set, what: str) -> None:
    extra = set(d) - allowed
    if extra:
        raise ValueError(f"thermal network {what}: unknown key(s) {sorted(extra)}")


def build_network(spec: dict) -> tuple[Network, dict[str, float]]:
    """Build a :class:`Network` from the ``network:`` block of tcs.yaml.

    Returns the network and the initial temperatures (deg C) per node.
    Unknown keys and dangling node references are errors, not shrugs (the
    defect #51 lesson: config that the model silently ignores is worse
    than no config).
    """
    nodes = spec.get("nodes") or []
    if not nodes:
        raise ValueError("thermal network: no nodes")
    names, cap, init = [], [], {}
    for n in nodes:
        _check_keys(n, _NODE_KEYS, f"node {n.get('name')}")
        name = str(n["name"])
        if name in names:
            raise ValueError(f"thermal network: duplicate node {name}")
        if n.get("capacitance_j_per_k") is not None:
            c = float(n["capacitance_j_per_k"])
        else:
            c = float(n["mass_kg"]) * float(n["cp_j_per_kg_k"])
        if c <= 0:
            raise ValueError(f"thermal network: node {name} capacitance <= 0")
        names.append(name)
        cap.append(c)
        init[name] = float(n.get("initial_c", 15.0))
    index = {nm: i for i, nm in enumerate(names)}

    def idx(nm: str, what: str) -> int:
        if nm not in index:
            raise ValueError(f"thermal network {what}: unknown node {nm!r}")
        return index[nm]

    conds = []
    for c in spec.get("conductors") or []:
        _check_keys(c, _COND_KEYS, "conductor")
        conds.append((idx(c["a"], "conductor"), idx(c["b"], "conductor"),
                      float(c["g_w_per_k"])))
    rads = []
    for r in spec.get("radiative") or []:
        _check_keys(r, _RAD_KEYS, "radiative link")
        rads.append((idx(r["a"], "radiative link"), idx(r["b"], "radiative link"),
                     float(r["ea_m2"])))
    surfs = []
    for sp in spec.get("surfaces") or []:
        _check_keys(sp, _SURF_KEYS, f"surface on {sp.get('node')}")
        idx(sp["node"], "surface")
        a, e = _coating_average(sp)
        normal = sp.get("normal")
        surfs.append(Surface(
            node=str(sp["node"]), area_m2=float(sp["area_m2"]),
            alpha=a, epsilon=e,
            normal=tuple(float(v) for v in normal) if normal is not None else None,
            wing=sp.get("wing"), side=str(sp.get("side", "front")),
            array_face=sp.get("array_face")))
        if surfs[-1].normal is None and surfs[-1].wing is None:
            raise ValueError(f"surface on {sp['node']}: needs `normal` or `wing`")
    return Network(names, index, cap, conds, rads, surfs), init


# ─────────────────────────────────────────────────────────────────────────
# Integrator
# ─────────────────────────────────────────────────────────────────────────

class NetworkSolver:
    """Holds the node temperatures and integrates the network."""

    def __init__(self, net: Network, init_c: dict[str, float],
                 stability_fraction: float = 0.4, max_step_s: float = 20.0):
        self.net = net
        self.T = [init_c.get(n, 15.0) + K0 for n in net.names]   # kelvin
        self.stability_fraction = float(stability_fraction)
        self.max_step_s = float(max_step_s)
        n = len(net.names)
        # Per-node sums used by the stability bound.
        self._g_sum = [0.0] * n
        for i, j, g in net.conductors:
            self._g_sum[i] += g
            self._g_sum[j] += g
        self._r_sum = [0.0] * n
        for i, j, ea in net.radiators:
            self._r_sum[i] += ea
            self._r_sum[j] += ea
        self.last_substeps = 0

    # ── access ──────────────────────────────────────────────────────────
    def temp_c(self, name: str) -> float:
        return self.T[self.net.index[name]] - K0

    def set_temp_c(self, name: str, value_c: float) -> None:
        self.T[self.net.index[name]] = float(value_c) + K0

    def temps_c(self) -> dict[str, float]:
        return {n: self.T[i] - K0 for i, n in enumerate(self.net.names)}

    def energy_j(self) -> float:
        """Stored thermal energy relative to 0 K (sum C_i T_i)."""
        return sum(c * t for c, t in zip(self.net.cap, self.T))

    # ── physics ─────────────────────────────────────────────────────────
    def max_stable_step(self, emit_ea: list[float],
                        extra: list[tuple[int, int, float]] = ()) -> float:
        """Smallest node time constant x stability_fraction (seconds)."""
        tau_min = float("inf")
        g_extra = [0.0] * len(self.net.cap)
        for i, j, g in extra:
            g_extra[i] += g
            g_extra[j] += g
        for i, c in enumerate(self.net.cap):
            t3 = max(self.T[i], 200.0) ** 3
            k = (self._g_sum[i] + g_extra[i] + 4.0 * SIGMA * t3 * (self._r_sum[i] * 2.0
                                                      + emit_ea[i]))
            if k > 0:
                tau_min = min(tau_min, c / k)
        return self.stability_fraction * tau_min

    def derivatives(self, q_abs: list[float], emit_ea: list[float],
                    power: list[float],
                    extra: list[tuple[int, int, float]] = ()) -> list[float]:
        """Net heat flow into each node [W] at the current temperatures."""
        T = self.T
        q = [q_abs[i] + power[i] - emit_ea[i] * SIGMA * T[i] ** 4
             for i in range(len(T))]
        for i, j, g in self.net.conductors:
            f = g * (T[j] - T[i])
            q[i] += f
            q[j] -= f
        for i, j, g in extra:
            f = g * (T[j] - T[i])
            q[i] += f
            q[j] -= f
        for i, j, ea in self.net.radiators:
            f = ea * SIGMA * (T[j] ** 4 - T[i] ** 4)
            q[i] += f
            q[j] -= f
        return q

    def step(self, dt: float, q_abs: list[float], emit_ea: list[float],
             power: list[float],
             extra_conductors: list[tuple[int, int, float]] = ()) -> float:
        """Advance ``dt`` seconds with inputs held constant.

        ``q_abs`` absorbed environmental heat [W], ``emit_ea`` the radiating
        eps*A to space [m^2], ``power`` internal dissipation + heaters [W],
        all per node in network order; ``extra_conductors`` are
        state-dependent links (i, j, G) such as a stowed wing lying on its
        body face. Returns the energy radiated to space
        over the step [J] (for the conservation tests).
        """
        if dt <= 0:
            self.last_substeps = 0
            return 0.0
        h_max = min(self.max_step_s, self.max_stable_step(emit_ea, extra_conductors))
        n = max(1, int(math.ceil(dt / max(h_max, 1e-3))))
        h = dt / n
        cap = self.net.cap
        radiated = 0.0
        for _ in range(n):
            q = self.derivatives(q_abs, emit_ea, power, extra_conductors)
            radiated += sum(emit_ea[i] * SIGMA * self.T[i] ** 4
                            for i in range(len(self.T))) * h
            self.T = [t + qi * h / c for t, qi, c in zip(self.T, q, cap)]
        self.last_substeps = n
        return radiated


# ─────────────────────────────────────────────────────────────────────────
# Environment (absorbed flux per surface)
# ─────────────────────────────────────────────────────────────────────────

def _dot(a: Iterable[float], b: Iterable[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def wing_normal(angle_deg: float) -> tuple[float, float, float]:
    """Front (cell) normal of a deployed wing at SADA angle ``angle_deg``.

    Same convention as eps_basic.EPSBasicModel._wing_normal for the shipped
    drive axis 'y': n = cos(a) [1,0,0] + sin(a) [0,0,1].
    """
    a = math.radians(angle_deg)
    return (math.cos(a), 0.0, math.sin(a))


@dataclass
class Geometry:
    """Everything external heating needs for one step."""
    sun_body: tuple[float, float, float] | None   # unit vector, None = tumbling
    nadir_body: tuple[float, float, float] | None  # unit vector, None = tumbling
    sun_fraction: float          # 0 umbra .. 1 full sun
    albedo_cos: float            # max(0, r_hat . s_hat): sub-satellite sun elevation term
    h_ratio: float               # (R_E + h) / R_E
    sada_angle_deg: float = 0.0
    wings_deployed: tuple[bool, bool] = (True, True)   # (py, my)
    sun_dist_km: float | None = None    # for the 1/r^2 solar-flux scaling


def absorbed_flux(net: Network, geo: Geometry, env: dict[str, float],
                  array_power_w: dict[str, float] | None = None
                  ) -> tuple[list[float], list[float]]:
    """Absorbed environmental heat and radiating eps*A per node.

    Solar: alpha S A max(0, n.s) x sun_fraction. Albedo: alpha S a F(n) x
    max(0, r.s). Earth IR: eps q_IR F(n). F is the flat-plate Earth view
    factor; tumbling (no attitude) uses the orientation averages 1/4 for the
    sun and (1 - cos rho)/2 for the Earth. Electrical power the array
    delivers (``array_power_w``, from the EPS panel currents) is removed from
    the absorbed solar heat of the face that generated it - it leaves the
    face as electricity and reappears as dissipation in the loads.
    """
    S = env["solar_flux_w_m2"]
    alb = env["albedo"]
    olr = env["earth_ir_w_m2"]
    q = [0.0] * len(net.names)
    ea = [0.0] * len(net.names)
    F_tumble = tumbling_earth_view_factor(geo.h_ratio)
    dep = {"py": geo.wings_deployed[0], "my": geo.wings_deployed[1]}
    wn = wing_normal(geo.sada_angle_deg)
    array_power_w = array_power_w or {}
    for s in net.surfaces:
        i = net.index[s.node]
        if s.wing is not None:
            if not dep.get(s.wing, True):
                # Stowed: folded flat against its body face. The wing node is
                # then tied to that face by the stowed-contact conductance
                # (TCS adds it) and has no view of space of its own.
                continue
            n = wn if s.side == "front" else (-wn[0], -wn[1], -wn[2])
        else:
            n = s.normal
        ea[i] += s.epsilon * s.area_m2
        # Sun
        if geo.sun_body is None:
            sun_f = 0.25
        else:
            sun_f = max(0.0, _dot(n, geo.sun_body))
        q_sun = s.alpha * S * s.area_m2 * sun_f * geo.sun_fraction
        # Earth
        if geo.nadir_body is None:
            F = F_tumble
        else:
            F = plate_earth_view_factor(_dot(n, geo.nadir_body), geo.h_ratio)
        q_alb = s.alpha * S * alb * F * s.area_m2 * geo.albedo_cos
        q_ir = s.epsilon * olr * F * s.area_m2
        q[i] += q_sun + q_alb + q_ir
    # Electrical power out of the arrays.
    for s_name, p in array_power_w.items():
        node = None
        for s in net.surfaces:
            if s.array_face == s_name and s.side == "front":
                node = s.node
                break
        if node is not None and p > 0:
            q[net.index[node]] -= p
    return q, ea
