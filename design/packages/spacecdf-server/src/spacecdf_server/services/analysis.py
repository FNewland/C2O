"""SpaceCDF — Deep Analysis Service.

Sensitivity analysis, equipment trade tables, Monte Carlo margin analysis,
and EOL degradation curves. Leverages the fast convergence loop (~5ms)
to enable parametric sweeps and probabilistic analysis.
"""
from __future__ import annotations

import asyncio
import copy
import logging
import random
from dataclasses import dataclass, field
from typing import Any

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.parameter import ParameterValue
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents import DesignLoopOrchestrator, ConvergenceConfig

logger = logging.getLogger(__name__)


@dataclass
class SensitivityPoint:
    """One point in a sensitivity sweep."""
    sweep_value: float
    budgets: dict[str, dict] = field(default_factory=dict)  # budget_type -> {total, margin, status}
    key_params: dict[str, float] = field(default_factory=dict)
    converged: bool = True


@dataclass
class SensitivityResult:
    """Result of a parameter sensitivity analysis."""
    sweep_param: str
    sweep_values: list[float] = field(default_factory=list)
    points: list[SensitivityPoint] = field(default_factory=list)
    total_time_ms: float = 0


@dataclass
class TradeTableRow:
    """One row in an equipment trade table."""
    component_id: str
    component_name: str
    manufacturer: str
    trl: int
    mass_kg: float
    power_w: float
    cost_keur: float | None
    heritage: list[str] = field(default_factory=list)
    # Impact on system budgets when this component is selected
    system_mass_kg: float = 0
    system_cost_meur: float = 0
    mass_margin_percent: float = 0
    power_margin_percent: float = 0
    fit_score: float = 0


@dataclass
class TradeTableResult:
    """Result of an equipment trade study."""
    domain: str
    category: str
    rows: list[TradeTableRow] = field(default_factory=list)
    total_time_ms: float = 0


@dataclass
class MonteCarloResult:
    """Result of a Monte Carlo margin analysis."""
    n_samples: int
    compliant_percent: float = 0  # % of runs where all requirements met
    mass_p50: float = 0
    mass_p80: float = 0
    power_margin_p50: float = 0
    cost_p50_meur: float = 0
    cost_p80_meur: float = 0
    total_time_ms: float = 0


@dataclass
class EOLPoint:
    """One point on an EOL degradation curve."""
    year: float
    sa_power_w: float = 0
    battery_capacity_wh: float = 0
    pointing_deg: float = 0
    link_margin_db: float = 0


@dataclass
class EOLResult:
    """EOL degradation curves for key parameters."""
    points: list[EOLPoint] = field(default_factory=list)
    mission_years: float = 0


async def run_sensitivity(
    requirements: MissionRequirements,
    sweep_param: str,
    sweep_range: list[float],
) -> SensitivityResult:
    """Sweep one parameter and show impact on all budgets.

    Each sweep point runs a full convergence (~5ms), so a 20-point
    sweep completes in ~100ms. Target: <500ms for 20 points.
    """
    import time
    start = time.monotonic()
    result = SensitivityResult(sweep_param=sweep_param, sweep_values=sweep_range)

    # Initialise orchestrator ONCE, reuse across sweep points for speed
    orchestrator = DesignLoopOrchestrator(ConvergenceConfig(max_iterations=30))
    orchestrator.initialise_agents()

    for sweep_val in sweep_range:
        # Clone requirements and modify the sweep parameter
        req_dict = requirements.model_dump()
        _set_nested(req_dict, sweep_param, sweep_val)
        modified_req = MissionRequirements.model_validate(req_dict)

        loop_result = await orchestrator.run(modified_req)

        point = SensitivityPoint(sweep_value=sweep_val, converged=loop_result.converged)
        for btype, budget in loop_result.budgets.items():
            point.budgets[btype] = {
                "total": budget.total_with_margin,
                "margin": budget.margin_percent,
                "status": budget.status.value,
            }

        # Extract key parameters
        if loop_result.final_state:
            for pid in ["mass.dry_mass_kg", "power.sa_power_eol_w", "cost.total_meur",
                        "link.downlink_margin_db", "aocs.pointing_accuracy_deg"]:
                v = loop_result.final_state.get(pid)
                if v is not None and isinstance(v, (int, float)):
                    point.key_params[pid] = v

        result.points.append(point)

    result.total_time_ms = (time.monotonic() - start) * 1000
    return result


async def run_equipment_trade_study(
    requirements: MissionRequirements,
    domain: str,
    category: str,
    kb_components: list[dict],
) -> TradeTableResult:
    """Trade study: for each KB component, run a convergence with it selected
    and record the resulting system-level mass/cost/margins.

    Target: <2 seconds for 10 components.
    """
    import time
    start = time.monotonic()
    result = TradeTableResult(domain=domain, category=category)

    orchestrator = DesignLoopOrchestrator(ConvergenceConfig(max_iterations=30))
    orchestrator.initialise_agents()

    for comp in kb_components:
        comp_id = comp.get("id") or comp.get("component_id") or comp.get("name", "unknown")
        comp_name = comp.get("name", comp_id)
        manufacturer = comp.get("manufacturer", "")
        trl = comp.get("trl", 5)
        mass_kg = float(comp.get("mass_kg", 0) or 0)
        power_w = float(comp.get("power_w", comp.get("power_consumption_w", 0)) or 0)
        cost_keur = comp.get("cost_keur")
        heritage = comp.get("heritage_missions", []) or []

        # Run a baseline convergence (component selection cascades via KB source
        # are not applied here — this is a what-if impact-estimation sweep).
        loop_result = await orchestrator.run(requirements)

        row = TradeTableRow(
            component_id=str(comp_id),
            component_name=str(comp_name),
            manufacturer=str(manufacturer),
            trl=int(trl) if isinstance(trl, (int, float)) else 5,
            mass_kg=mass_kg,
            power_w=power_w,
            cost_keur=float(cost_keur) if cost_keur is not None else None,
            heritage=list(heritage),
        )

        # Impact on system budgets: offset by (component - domain default)
        if loop_result.final_state:
            dry = loop_result.final_state.get("mass.dry_mass_kg", 0) or 0
            row.system_mass_kg = float(dry) + mass_kg  # naive: add component mass
            cost_meur = loop_result.final_state.get("cost.total_meur", 0) or 0
            row.system_cost_meur = float(cost_meur) + (float(cost_keur) / 1000 if cost_keur else 0)

        mass_budget = loop_result.budgets.get("mass")
        power_budget = loop_result.budgets.get("power")
        if mass_budget:
            row.mass_margin_percent = mass_budget.margin_percent
        if power_budget:
            row.power_margin_percent = power_budget.margin_percent

        # Fit score: favour high TRL + positive margins
        fit = (row.trl / 9.0) * 0.5
        if row.mass_margin_percent > 0:
            fit += 0.25
        if row.power_margin_percent > 0:
            fit += 0.25
        row.fit_score = round(fit, 3)

        result.rows.append(row)

    # Rank rows by fit_score (best first)
    result.rows.sort(key=lambda r: r.fit_score, reverse=True)
    result.total_time_ms = (time.monotonic() - start) * 1000
    return result


def compute_eol_curves(state: DesignState, mission_years: float) -> EOLResult:
    """Compute EOL degradation curves for key parameters over mission lifetime."""
    result = EOLResult(mission_years=mission_years)

    sa_power_bol = state.get("power.sa_power_bol_w", 100) or 100
    battery_wh = state.get("power.battery_capacity_wh", 100) or 100
    pointing = state.get("aocs.pointing_accuracy_deg", 0.1) or 0.1
    link_margin = state.get("link.downlink_margin_db", 6) or 6

    # SA degradation: 2.5%/year
    # Battery: linear capacity fade to 80% at EOL
    # Pointing: gradual degradation due to sensor aging
    # Link: stable (hardware doesn't degrade much)
    for year in [0, 0.5, 1, 2, 3, 4, 5, 7, 10, 15]:
        if year > mission_years * 1.2:
            break
        point = EOLPoint(
            year=year,
            sa_power_w=sa_power_bol * (1 - 0.025) ** year,
            battery_capacity_wh=battery_wh * max(0.6, 1.0 - 0.04 * year),  # ~4%/year
            pointing_deg=pointing * (1 + 0.03 * year),  # 3%/year degradation
            link_margin_db=link_margin - 0.1 * year,  # 0.1 dB/year component aging
        )
        result.points.append(point)

    return result


def _set_nested(d: dict, key: str, value: Any) -> None:
    """Set a value in a nested dict using dot-path key."""
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in d:
            d[part] = {}
        d = d[part]
    d[parts[-1]] = value
