"""ConOps Executor — SCDF-201.

Simulates a spacecraft through one orbit (or arbitrary duration) using
mode-based operations with power, thermal, and data-budget tracking.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ConOpsMode:
    """Defines a spacecraft operational mode."""
    name: str
    power_draw_w: float
    pointing: str = "nadir"  # nadir | sun | inertial
    data_rate_bps: float = 0.0
    is_payload_active: bool = False


@dataclass
class ModeGuard:
    """Conditional mode transition rule.

    condition is a simple expression evaluated against state, e.g.:
      "soc < 30"   — switch when SoC drops below 30%
      "temp > 60"  — switch when temperature exceeds 60 C
    """
    condition: str
    target_mode: str
    priority: int = 0


@dataclass
class OrbitParams:
    altitude_km: float = 550.0
    inclination_deg: float = 97.5
    eclipse_fraction: float = 0.35
    period_s: float = 5800.0
    contact_time_per_orbit_s: float = 600.0


@dataclass
class PowerParams:
    sa_power_eol_w: float = 60.0
    battery_capacity_wh: float = 40.0
    heater_power_w: float = 5.0


@dataclass
class ThermalParams:
    """Single-node thermal model parameters."""
    capacitance_j_per_k: float = 5000.0  # thermal mass
    radiator_area_m2: float = 0.04
    emissivity: float = 0.85
    absorptivity: float = 0.3
    internal_dissipation_fraction: float = 0.6  # fraction of elec power -> heat
    solar_flux_w_m2: float = 1361.0
    initial_temp_c: float = 20.0


@dataclass
class TimeSeriesResult:
    """Output of a ConOps simulation run."""
    time_s: List[float] = field(default_factory=list)
    mode: List[str] = field(default_factory=list)
    soc_pct: List[float] = field(default_factory=list)
    temp_c: List[float] = field(default_factory=list)
    data_buffer_mbit: List[float] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Default modes
# ---------------------------------------------------------------------------

DEFAULT_MODES: List[ConOpsMode] = [
    ConOpsMode(name="safe", power_draw_w=10.0, pointing="sun", data_rate_bps=0, is_payload_active=False),
    ConOpsMode(name="imaging", power_draw_w=45.0, pointing="nadir", data_rate_bps=50e6, is_payload_active=True),
    ConOpsMode(name="downlink", power_draw_w=30.0, pointing="nadir", data_rate_bps=-2e6, is_payload_active=False),
    ConOpsMode(name="eclipse_survival", power_draw_w=12.0, pointing="inertial", data_rate_bps=0, is_payload_active=False),
]

DEFAULT_GUARDS: List[ModeGuard] = [
    ModeGuard(condition="soc < 20", target_mode="safe", priority=10),
    ModeGuard(condition="temp > 65", target_mode="safe", priority=9),
]

# Stefan-Boltzmann constant
SIGMA = 5.670374419e-8  # W m^-2 K^-4


# ---------------------------------------------------------------------------
# Guard evaluator
# ---------------------------------------------------------------------------

def _evaluate_guard(condition: str, state: Dict[str, float]) -> bool:
    """Evaluate a simple guard condition against current state.

    Supports: soc, temp, data_buffer with <, >, <=, >= operators.
    """
    import operator
    ops = {"<": operator.lt, ">": operator.gt, "<=": operator.le, ">=": operator.ge}
    tokens = condition.strip().split()
    if len(tokens) != 3:
        return False
    var, op_str, val_str = tokens
    if var not in state or op_str not in ops:
        return False
    try:
        return ops[op_str](state[var], float(val_str))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Orbit geometry helpers
# ---------------------------------------------------------------------------

def _in_sunlight(t: float, orbit_params: OrbitParams) -> bool:
    """Determine if spacecraft is in sunlight at time t.

    Eclipse is centred around the middle of each orbit period.
    """
    phase = (t % orbit_params.period_s) / orbit_params.period_s
    eclipse_start = 0.5 - orbit_params.eclipse_fraction / 2
    eclipse_end = 0.5 + orbit_params.eclipse_fraction / 2
    return not (eclipse_start <= phase <= eclipse_end)


def _in_contact(t: float, orbit_params: OrbitParams) -> bool:
    """Determine if spacecraft is in ground contact at time t.

    Contact window is placed at the start of each orbit.
    """
    phase_s = t % orbit_params.period_s
    return phase_s < orbit_params.contact_time_per_orbit_s


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def simulate_orbit(
    modes: Optional[List[ConOpsMode]] = None,
    guards: Optional[List[ModeGuard]] = None,
    orbit_params: Optional[OrbitParams] = None,
    power_params: Optional[PowerParams] = None,
    thermal_params: Optional[ThermalParams] = None,
    duration_s: Optional[float] = None,
    mode_schedule: Optional[List[Dict[str, Any]]] = None,
) -> TimeSeriesResult:
    """Run a mode-based ConOps simulation.

    Parameters
    ----------
    modes : list of ConOpsMode
        Available operational modes.
    guards : list of ModeGuard
        Autonomous mode-switch rules evaluated each timestep.
    orbit_params : OrbitParams
        Orbital geometry parameters.
    power_params : PowerParams
        Power subsystem parameters.
    thermal_params : ThermalParams
        Thermal model parameters.
    duration_s : float
        Total simulation duration in seconds. Defaults to one orbit period.
    mode_schedule : list of dict
        Optional time-based mode schedule: [{"time_s": 0, "mode": "imaging"}, ...]
        If not provided, starts in first mode and relies on guards.

    Returns
    -------
    TimeSeriesResult
    """
    # Apply defaults
    if modes is None:
        modes = DEFAULT_MODES
    if guards is None:
        guards = DEFAULT_GUARDS
    if orbit_params is None:
        orbit_params = OrbitParams()
    if power_params is None:
        power_params = PowerParams()
    if thermal_params is None:
        thermal_params = ThermalParams()

    period = orbit_params.period_s
    if duration_s is None:
        duration_s = period

    # Sort guards by priority (highest first)
    sorted_guards = sorted(guards, key=lambda g: g.priority, reverse=True)

    # Build mode lookup
    mode_map: Dict[str, ConOpsMode] = {m.name: m for m in modes}

    # Build schedule lookup (sorted by time)
    schedule: List[Dict[str, Any]] = []
    if mode_schedule:
        schedule = sorted(mode_schedule, key=lambda s: s["time_s"])

    # Simulation state
    dt = 30.0  # timestep seconds
    t = 0.0
    soc_wh = power_params.battery_capacity_wh * 0.8  # start at 80%
    temp_k = thermal_params.initial_temp_c + 273.15
    data_buffer_mbit = 0.0

    # Initial mode
    if schedule:
        current_mode_name = schedule[0]["mode"]
    else:
        current_mode_name = modes[0].name
    current_mode = mode_map[current_mode_name]

    result = TimeSeriesResult()
    schedule_idx = 0

    while t <= duration_s:
        sunlit = _in_sunlight(t, orbit_params)
        contact = _in_contact(t, orbit_params)

        # --- Scheduled mode transitions ---
        if schedule and schedule_idx < len(schedule):
            while schedule_idx < len(schedule) and schedule[schedule_idx]["time_s"] <= t:
                new_name = schedule[schedule_idx]["mode"]
                if new_name in mode_map and new_name != current_mode_name:
                    current_mode_name = new_name
                    current_mode = mode_map[current_mode_name]
                    result.events.append({
                        "time_s": t,
                        "type": "mode_change",
                        "desc": f"Scheduled transition to {current_mode_name}",
                    })
                schedule_idx += 1

        # --- Guard evaluation ---
        soc_pct = (soc_wh / power_params.battery_capacity_wh) * 100.0
        state_vars = {
            "soc": soc_pct,
            "temp": temp_k - 273.15,
            "data_buffer": data_buffer_mbit,
        }
        for guard in sorted_guards:
            if _evaluate_guard(guard.condition, state_vars):
                if guard.target_mode in mode_map and guard.target_mode != current_mode_name:
                    old_mode = current_mode_name
                    current_mode_name = guard.target_mode
                    current_mode = mode_map[current_mode_name]
                    result.events.append({
                        "time_s": t,
                        "type": "guard_trigger",
                        "desc": f"Guard '{guard.condition}' fired: {old_mode} -> {current_mode_name}",
                    })
                break  # only highest-priority guard fires

        # --- Power balance ---
        p_gen = power_params.sa_power_eol_w if sunlit else 0.0
        p_consume = current_mode.power_draw_w
        # Add heater power if cold
        if (temp_k - 273.15) < 0.0:
            p_consume += power_params.heater_power_w

        p_net = p_gen - p_consume  # watts
        soc_wh += p_net * (dt / 3600.0)
        soc_wh = max(0.0, min(soc_wh, power_params.battery_capacity_wh))

        # --- Thermal (single-node radiative balance) ---
        q_internal = current_mode.power_draw_w * thermal_params.internal_dissipation_fraction
        # Solar absorbed (only in sunlight, only if pointing allows it)
        q_solar = 0.0
        if sunlit:
            q_solar = (thermal_params.absorptivity * thermal_params.solar_flux_w_m2
                       * thermal_params.radiator_area_m2 * 0.25)  # projected area factor
        q_radiated = (thermal_params.emissivity * SIGMA
                      * thermal_params.radiator_area_m2 * temp_k**4)
        dT = (q_internal + q_solar - q_radiated) / thermal_params.capacitance_j_per_k * dt
        temp_k += dT

        # --- Data budget ---
        if current_mode.is_payload_active and current_mode.data_rate_bps > 0:
            data_buffer_mbit += current_mode.data_rate_bps * dt / 1e6
        if current_mode.name == "downlink" and contact:
            # Downlink rate magnitude (data_rate_bps is negative for downlink mode)
            downlink_rate = abs(current_mode.data_rate_bps)
            data_buffer_mbit -= downlink_rate * dt / 1e6
        data_buffer_mbit = max(0.0, data_buffer_mbit)

        # --- Record state ---
        soc_pct = (soc_wh / power_params.battery_capacity_wh) * 100.0
        result.time_s.append(round(t, 1))
        result.mode.append(current_mode_name)
        result.soc_pct.append(round(soc_pct, 2))
        result.temp_c.append(round(temp_k - 273.15, 2))
        result.data_buffer_mbit.append(round(data_buffer_mbit, 3))

        # --- Eclipse/sunlight transition events ---
        if t > 0:
            prev_sunlit = _in_sunlight(t - dt, orbit_params)
            if sunlit and not prev_sunlit:
                result.events.append({"time_s": t, "type": "eclipse_exit", "desc": "Entering sunlight"})
            elif not sunlit and prev_sunlit:
                result.events.append({"time_s": t, "type": "eclipse_entry", "desc": "Entering eclipse"})

        t += dt

    return result
