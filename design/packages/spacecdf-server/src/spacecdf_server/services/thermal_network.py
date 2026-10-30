"""SpaceCDF — Multi-Node Thermal Network Solver (SCDF-211/212/213).

Implements a lightweight lumped-parameter thermal model for spacecraft
thermal analysis. Supports both steady-state (iterative) and transient
(Euler integration) solvers with conductive and radiative heat transfer.

Physics:
  - Stefan-Boltzmann constant: sigma = 5.67e-8 W/m^2/K^4
  - Conduction: Q = G * (T_a - T_b) where G is conductance [W/K]
  - Radiation to space: Q_rad = epsilon * sigma * A * (T^4 - T_sink^4)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STEFAN_BOLTZMANN = 5.67e-8  # W/m^2/K^4
SPACE_SINK_TEMP_K = 3.0  # Deep space background
EARTH_FACING_SINK_K = 250.0  # Effective Earth IR sink


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ThermalNode:
    """A single thermal node in the network."""

    id: str
    name: str
    mass_kg: float
    specific_heat_j_kg_k: float  # J/(kg*K)
    temperature_c: float = 20.0  # Initial temperature [degC]
    power_dissipation_w: float = 0.0  # Internal heat generation
    emissivity: float = 0.0  # Surface emissivity (0 = no radiation)
    area_m2: float = 0.0  # Radiating area [m^2]
    is_radiator: bool = False  # True if this node radiates to space
    earth_facing: bool = False  # Use Earth IR sink instead of deep space


@dataclass
class ThermalConductance:
    """Thermal conduction link between two nodes."""

    node_a_id: str
    node_b_id: str
    conductance_w_k: float  # W/K


@dataclass
class ThermalNetworkResult:
    """Result of a thermal network analysis."""

    node_temps: dict[str, float]  # node_id -> temperature [degC]
    radiator_heat_rejection_w: float
    max_temp_c: float
    min_temp_c: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class TransientResult:
    """Time-series result from transient analysis."""

    time_s: list[float]
    temperatures: dict[str, list[float]]  # node_id -> list of temps [degC]
    radiator_heat_rejection_w: list[float]
    max_temp_c: float
    min_temp_c: float
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Default 6U CubeSat thermal network
# ---------------------------------------------------------------------------


def default_6u_cubesat_nodes() -> list[ThermalNode]:
    """Return a default 6U CubeSat thermal node set."""
    return [
        ThermalNode(
            id="chassis",
            name="Chassis (core structure)",
            mass_kg=0.5,
            specific_heat_j_kg_k=900.0,  # Aluminium
            temperature_c=20.0,
            power_dissipation_w=0.0,
            emissivity=0.1,
            area_m2=0.06,
            is_radiator=False,
        ),
        ThermalNode(
            id="payload",
            name="Payload bay",
            mass_kg=0.3,
            specific_heat_j_kg_k=800.0,
            temperature_c=20.0,
            power_dissipation_w=5.0,
            emissivity=0.05,
            area_m2=0.02,
            is_radiator=False,
        ),
        ThermalNode(
            id="battery",
            name="Battery pack",
            mass_kg=0.15,
            specific_heat_j_kg_k=1100.0,  # Li-ion effective
            temperature_c=20.0,
            power_dissipation_w=0.5,
            emissivity=0.05,
            area_m2=0.005,
            is_radiator=False,
        ),
        ThermalNode(
            id="eps",
            name="EPS board",
            mass_kg=0.1,
            specific_heat_j_kg_k=900.0,
            temperature_c=20.0,
            power_dissipation_w=2.0,
            emissivity=0.05,
            area_m2=0.01,
            is_radiator=False,
        ),
        ThermalNode(
            id="radiator",
            name="Radiator panel",
            mass_kg=0.05,
            specific_heat_j_kg_k=900.0,
            temperature_c=20.0,
            power_dissipation_w=0.0,
            emissivity=0.85,
            area_m2=0.04,
            is_radiator=True,
            earth_facing=False,
        ),
        ThermalNode(
            id="obc",
            name="OBC",
            mass_kg=0.05,
            specific_heat_j_kg_k=900.0,
            temperature_c=20.0,
            power_dissipation_w=1.5,
            emissivity=0.05,
            area_m2=0.005,
            is_radiator=False,
        ),
    ]


def default_6u_cubesat_conductances() -> list[ThermalConductance]:
    """Return default conductance links for a 6U CubeSat."""
    return [
        # Chassis is the thermal backbone
        ThermalConductance("chassis", "payload", 0.8),  # Standoff-isolated
        ThermalConductance("chassis", "battery", 3.0),  # Direct mount
        ThermalConductance("chassis", "eps", 2.5),  # PCB bolted to structure
        ThermalConductance("chassis", "radiator", 4.0),  # Good thermal path
        ThermalConductance("chassis", "obc", 2.0),  # PCB mount
        # Battery to EPS (short harness, some conduction)
        ThermalConductance("battery", "eps", 0.5),
        # OBC to EPS (stacked boards, standoffs)
        ThermalConductance("obc", "eps", 0.3),
        # Payload to radiator (MLI-limited)
        ThermalConductance("payload", "radiator", 0.03),
    ]


# ---------------------------------------------------------------------------
# Steady-state solver
# ---------------------------------------------------------------------------


def _c_to_k(t_c: float) -> float:
    """Convert Celsius to Kelvin."""
    return t_c + 273.15


def _k_to_c(t_k: float) -> float:
    """Convert Kelvin to Celsius."""
    return t_k - 273.15


def solve_steady_state(
    nodes: list[ThermalNode],
    conductances: list[ThermalConductance],
    max_iterations: int = 200,
    tolerance_k: float = 0.1,
) -> ThermalNetworkResult:
    """Solve for steady-state temperatures using fixed-point iteration.

    The radiative term (epsilon * sigma * A * T^4) makes the problem
    nonlinear, so we iterate: at each step, linearize radiation about
    the current temperature estimate, solve the linear system, and repeat.

    Uses Gauss-Seidel iteration for the linear solve (avoids numpy dependency).
    """
    warnings: list[str] = []
    n = len(nodes)
    node_map = {nd.id: i for i, nd in enumerate(nodes)}

    # Initial guess: current temperatures in Kelvin
    temps_k = [_c_to_k(nd.temperature_c) for nd in nodes]

    for iteration in range(max_iterations):
        temps_prev = temps_k[:]

        for i, node in enumerate(nodes):
            # Sum of conductive heat flows into node i
            q_cond = 0.0
            g_total = 0.0

            for link in conductances:
                if link.node_a_id == node.id:
                    j = node_map[link.node_b_id]
                    q_cond += link.conductance_w_k * (temps_k[j] - temps_k[i])
                    g_total += link.conductance_w_k
                elif link.node_b_id == node.id:
                    j = node_map[link.node_a_id]
                    q_cond += link.conductance_w_k * (temps_k[j] - temps_k[i])
                    g_total += link.conductance_w_k

            # Internal heat generation
            q_internal = node.power_dissipation_w

            # Radiative heat loss (only for nodes with radiating surfaces)
            q_rad = 0.0
            if node.is_radiator and node.emissivity > 0 and node.area_m2 > 0:
                t_sink = EARTH_FACING_SINK_K if node.earth_facing else SPACE_SINK_TEMP_K
                q_rad = (
                    node.emissivity
                    * STEFAN_BOLTZMANN
                    * node.area_m2
                    * (temps_k[i] ** 4 - t_sink**4)
                )

            # Energy balance: q_cond + q_internal - q_rad = 0 at steady state
            # Solve for T_i given neighbours are fixed (Gauss-Seidel style)
            if g_total > 0:
                # Linearized: G_total * T_i = sum(G_j * T_j) + Q_int - Q_rad
                sum_g_t = 0.0
                for link in conductances:
                    if link.node_a_id == node.id:
                        j = node_map[link.node_b_id]
                        sum_g_t += link.conductance_w_k * temps_k[j]
                    elif link.node_b_id == node.id:
                        j = node_map[link.node_a_id]
                        sum_g_t += link.conductance_w_k * temps_k[j]

                # Linearize radiation about current T:
                # Q_rad ~ eps*sig*A*T0^4 + 4*eps*sig*A*T0^3 * (T - T0)
                # = eps*sig*A*(4*T0^3*T - 3*T0^4) - sink term
                if node.is_radiator and node.emissivity > 0 and node.area_m2 > 0:
                    t_sink = EARTH_FACING_SINK_K if node.earth_facing else SPACE_SINK_TEMP_K
                    h_rad = 4 * node.emissivity * STEFAN_BOLTZMANN * node.area_m2 * temps_k[i] ** 3
                    q_rad_const = (
                        node.emissivity
                        * STEFAN_BOLTZMANN
                        * node.area_m2
                        * (3 * temps_k[i] ** 4 + t_sink**4)
                    )
                    temps_k[i] = (sum_g_t + q_internal + q_rad_const) / (g_total + h_rad)
                else:
                    temps_k[i] = (sum_g_t + q_internal) / g_total
            else:
                # Isolated node — only radiation balance
                if node.is_radiator and node.emissivity > 0 and node.area_m2 > 0:
                    t_sink = EARTH_FACING_SINK_K if node.earth_facing else SPACE_SINK_TEMP_K
                    # Q_int = eps*sig*A*(T^4 - T_sink^4)
                    t4 = q_internal / (node.emissivity * STEFAN_BOLTZMANN * node.area_m2) + t_sink**4
                    if t4 > 0:
                        temps_k[i] = t4**0.25
                    else:
                        temps_k[i] = t_sink
                # else: no heat path, temperature stays at initial

        # Convergence check
        max_delta = max(abs(temps_k[i] - temps_prev[i]) for i in range(n))
        if max_delta < tolerance_k:
            break
    else:
        warnings.append(
            f"Steady-state did not converge within {max_iterations} iterations "
            f"(residual: {max_delta:.3f} K)"
        )

    # Compute total radiator heat rejection
    total_rad_w = 0.0
    for i, node in enumerate(nodes):
        if node.is_radiator and node.emissivity > 0 and node.area_m2 > 0:
            t_sink = EARTH_FACING_SINK_K if node.earth_facing else SPACE_SINK_TEMP_K
            total_rad_w += (
                node.emissivity
                * STEFAN_BOLTZMANN
                * node.area_m2
                * (temps_k[i] ** 4 - t_sink**4)
            )

    node_temps_c = {nodes[i].id: round(_k_to_c(temps_k[i]), 2) for i in range(n)}
    temps_c_vals = list(node_temps_c.values())

    # Operational limit warnings
    for nd_id, t_c in node_temps_c.items():
        if t_c > 60.0:
            warnings.append(f"Node '{nd_id}' exceeds 60 degC ({t_c:.1f} degC)")
        if t_c < -20.0:
            warnings.append(f"Node '{nd_id}' below -20 degC ({t_c:.1f} degC)")

    return ThermalNetworkResult(
        node_temps=node_temps_c,
        radiator_heat_rejection_w=round(total_rad_w, 3),
        max_temp_c=max(temps_c_vals),
        min_temp_c=min(temps_c_vals),
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Transient solver
# ---------------------------------------------------------------------------


def solve_transient(
    nodes: list[ThermalNode],
    conductances: list[ThermalConductance],
    duration_s: float = 5400.0,
    dt_s: float = 10.0,
    eclipse_fraction: float = 0.35,
    solar_absorbed_w: float | None = None,
) -> TransientResult:
    """Solve the transient thermal problem via forward Euler integration.

    dT_i/dt = (Q_cond_i + Q_internal_i - Q_rad_i) / (m_i * c_i)

    Optionally models eclipse/sunlit cycling: during sunlit phase,
    solar_absorbed_w is added to the chassis node.

    Parameters
    ----------
    nodes : list of ThermalNode
    conductances : list of ThermalConductance
    duration_s : total simulation duration [s] (default: one LEO orbit ~5400s)
    dt_s : time step [s] (default: 10s)
    eclipse_fraction : fraction of orbit in eclipse (default: 0.35)
    solar_absorbed_w : solar heat absorbed during sunlit phase [W]
        If None, defaults to alpha*flux*area for the chassis node.
    """
    warnings: list[str] = []
    n = len(nodes)
    node_map = {nd.id: i for i, nd in enumerate(nodes)}

    # Initialise temperatures in Kelvin
    temps_k = [_c_to_k(nd.temperature_c) for nd in nodes]

    # Pre-compute thermal capacitances
    capacitances = [nd.mass_kg * nd.specific_heat_j_kg_k for nd in nodes]

    # Orbit timing
    orbit_period_s = duration_s  # assume one orbit if not specified
    eclipse_start = (1.0 - eclipse_fraction) * orbit_period_s
    # Sunlit: 0 -> eclipse_start, Eclipse: eclipse_start -> orbit_period_s

    # Default solar absorbed (chassis absorptivity * flux * projected area)
    if solar_absorbed_w is None:
        # Typical 6U: alpha=0.3, area~0.06 m^2 projected
        solar_absorbed_w = 0.3 * 1361.0 * 0.03  # ~12 W

    # Time series storage
    n_steps = int(duration_s / dt_s) + 1
    time_series: list[float] = []
    temp_series: dict[str, list[float]] = {nd.id: [] for nd in nodes}
    rad_series: list[float] = []

    global_max_c = -1e9
    global_min_c = 1e9

    for step in range(n_steps):
        t = step * dt_s
        time_series.append(t)

        # Record current temperatures
        for i, nd in enumerate(nodes):
            t_c = _k_to_c(temps_k[i])
            temp_series[nd.id].append(round(t_c, 2))
            if t_c > global_max_c:
                global_max_c = t_c
            if t_c < global_min_c:
                global_min_c = t_c

        # Compute radiator rejection at this step
        step_rad_w = 0.0
        for i, nd in enumerate(nodes):
            if nd.is_radiator and nd.emissivity > 0 and nd.area_m2 > 0:
                t_sink = EARTH_FACING_SINK_K if nd.earth_facing else SPACE_SINK_TEMP_K
                step_rad_w += (
                    nd.emissivity
                    * STEFAN_BOLTZMANN
                    * nd.area_m2
                    * (temps_k[i] ** 4 - t_sink**4)
                )
        rad_series.append(round(step_rad_w, 3))

        # Determine if in eclipse
        orbit_time = t % orbit_period_s
        in_eclipse = orbit_time >= eclipse_start

        # Compute temperature derivatives and update (Forward Euler)
        dt_arr = [0.0] * n
        for i, nd in enumerate(nodes):
            # Conductive heat flow
            q_cond = 0.0
            for link in conductances:
                if link.node_a_id == nd.id:
                    j = node_map[link.node_b_id]
                    q_cond += link.conductance_w_k * (temps_k[j] - temps_k[i])
                elif link.node_b_id == nd.id:
                    j = node_map[link.node_a_id]
                    q_cond += link.conductance_w_k * (temps_k[j] - temps_k[i])

            # Internal heat
            q_internal = nd.power_dissipation_w

            # Solar absorbed (only chassis, only in sunlit)
            q_solar = 0.0
            if nd.id == "chassis" and not in_eclipse:
                q_solar = solar_absorbed_w

            # Radiative loss
            q_rad = 0.0
            if nd.is_radiator and nd.emissivity > 0 and nd.area_m2 > 0:
                t_sink = EARTH_FACING_SINK_K if nd.earth_facing else SPACE_SINK_TEMP_K
                q_rad = (
                    nd.emissivity
                    * STEFAN_BOLTZMANN
                    * nd.area_m2
                    * (temps_k[i] ** 4 - t_sink**4)
                )

            # dT/dt
            if capacitances[i] > 0:
                dt_arr[i] = (q_cond + q_internal + q_solar - q_rad) / capacitances[i]

        # Update temperatures
        for i in range(n):
            temps_k[i] += dt_arr[i] * dt_s

    # Warnings
    for nd_id, t_list in temp_series.items():
        t_max = max(t_list)
        t_min = min(t_list)
        if t_max > 60.0:
            warnings.append(f"Node '{nd_id}' exceeds 60 degC (peak: {t_max:.1f} degC)")
        if t_min < -20.0:
            warnings.append(f"Node '{nd_id}' below -20 degC (min: {t_min:.1f} degC)")

    return TransientResult(
        time_s=time_series,
        temperatures=temp_series,
        radiator_heat_rejection_w=rad_series,
        max_temp_c=round(global_max_c, 2),
        min_temp_c=round(global_min_c, 2),
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Convenience: full analysis combining both solvers
# ---------------------------------------------------------------------------


def analyze_thermal_network(
    nodes: list[ThermalNode] | None = None,
    conductances: list[ThermalConductance] | None = None,
    duration_s: float = 5400.0,
    eclipse_fraction: float = 0.35,
    run_transient: bool = True,
) -> dict[str, Any]:
    """Run a complete thermal analysis (steady-state + optional transient).

    If nodes/conductances are not provided, uses the default 6U CubeSat model.
    """
    if nodes is None:
        nodes = default_6u_cubesat_nodes()
    if conductances is None:
        conductances = default_6u_cubesat_conductances()

    # Validate node references in conductances
    node_ids = {nd.id for nd in nodes}
    for link in conductances:
        if link.node_a_id not in node_ids:
            raise ValueError(f"Conductance references unknown node: '{link.node_a_id}'")
        if link.node_b_id not in node_ids:
            raise ValueError(f"Conductance references unknown node: '{link.node_b_id}'")

    steady = solve_steady_state(nodes, conductances)

    result: dict[str, Any] = {
        "steady_state": {
            "node_temps": steady.node_temps,
            "radiator_heat_rejection_w": steady.radiator_heat_rejection_w,
            "max_temp_c": steady.max_temp_c,
            "min_temp_c": steady.min_temp_c,
            "warnings": steady.warnings,
        }
    }

    if run_transient:
        transient = solve_transient(
            nodes, conductances, duration_s=duration_s, eclipse_fraction=eclipse_fraction
        )
        result["transient"] = {
            "time_s": transient.time_s,
            "temperatures": transient.temperatures,
            "radiator_heat_rejection_w": transient.radiator_heat_rejection_w,
            "max_temp_c": transient.max_temp_c,
            "min_temp_c": transient.min_temp_c,
            "warnings": transient.warnings,
        }

    return result
