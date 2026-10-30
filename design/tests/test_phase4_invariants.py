"""Phase 4 invariant regression tests.

Verifies that Phase 1–3 guarantees still hold after Phase 4 additions:
- Convergence stays fast (<100ms p95 on EOSAT-1 reference)
- Sticky parameter invariant: KB_COMPONENT and POSITION_OVERRIDE
  sources are never overwritten by agents during re-convergence
- Monte Carlo percentile ordering is correct and stable
- Sensitivity sweep does not mutate the baseline design state
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for pkg in ("spacecdf-common", "spacecdf-agents", "spacecdf-kb", "spacecdf-server"):
    src = ROOT / "packages" / pkg / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))

import pytest

from spacecdf_common.agents.base import AgentResult, DesignState
from spacecdf_common.models.parameter import ParameterSource, ParameterValue
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents import ConvergenceConfig, DesignLoopOrchestrator


REF_REQ = MissionRequirements.model_validate({
    "name": "EOSAT-1",
    "mission_type": "earth_observation",
    "spacecraft_class": "nano",
    "orbit": {
        "orbit_type": "sso", "altitude_km": 450, "inclination_deg": 97.4,
        "mission_duration_years": 3, "deorbit_required": True,
    },
    "payloads": [{
        "name": "Imager", "type": "optical_imager",
        "mass_kg": 1.5, "power_w": 20, "data_rate_mbps": 100,
        "pointing_accuracy_deg": 0.1, "duty_cycle_percent": 25,
    }],
    "design_lifetime_years": 3, "target_mass_kg": 12, "target_cost_meur": 5,
    "ground_stations": ["KSAT Svalbard"],
})


@pytest.mark.asyncio
async def test_convergence_latency_budget():
    """Full convergence of EOSAT-1 must complete in <100ms (10x buffer over typical 3-12ms)."""
    orchestrator = DesignLoopOrchestrator(ConvergenceConfig(max_iterations=50))
    orchestrator.initialise_agents()

    durations = []
    for _ in range(5):
        t0 = time.monotonic()
        result = await orchestrator.run(REF_REQ)
        durations.append(time.monotonic() - t0)
        assert result.converged, "Reference design must converge"

    p95 = sorted(durations)[int(len(durations) * 0.95)]
    assert p95 < 0.100, f"Convergence p95 = {p95*1000:.1f}ms exceeds 100ms budget"


@pytest.mark.asyncio
async def test_sticky_kb_component_never_overwritten():
    """KB_COMPONENT source parameters must persist through re-convergence."""
    orchestrator = DesignLoopOrchestrator(ConvergenceConfig(max_iterations=30))
    orchestrator.initialise_agents()
    result = await orchestrator.run(REF_REQ)
    state = result.final_state
    assert state is not None

    # Inject a KB_COMPONENT parameter that power agent would normally write
    state._parameters["power.battery_capacity_wh"] = ParameterValue(
        id="power.battery_capacity_wh",
        name="Battery capacity",
        value=77.0,
        unit="Wh",
        domain="power",
        source=ParameterSource.KB_COMPONENT,
        equipment_id="bat-gom-nanopow-bpx",
    )

    # Re-run power agent — it should NOT overwrite our sticky value
    from spacecdf_agents.tier1.power import PowerAgent
    power = PowerAgent()
    agent_result = await power.execute(state)
    state.update(agent_result)

    final_battery = state.get_param("power.battery_capacity_wh")
    assert final_battery.source == ParameterSource.KB_COMPONENT, "Source should remain KB_COMPONENT"
    assert final_battery.value == 77.0, f"Value should remain 77.0, got {final_battery.value}"
    assert final_battery.equipment_id == "bat-gom-nanopow-bpx"


@pytest.mark.asyncio
async def test_sticky_position_override_never_overwritten():
    """POSITION_OVERRIDE source parameters must persist through re-convergence."""
    orchestrator = DesignLoopOrchestrator()
    orchestrator.initialise_agents()
    result = await orchestrator.run(REF_REQ)
    state = result.final_state
    assert state is not None

    state._parameters["aocs.mass_kg"] = ParameterValue(
        id="aocs.mass_kg",
        name="AOCS mass",
        value=0.5,  # Deliberately unrealistic to make overwrites detectable
        unit="kg",
        domain="aocs",
        source=ParameterSource.POSITION_OVERRIDE,
        override_by="aocs_engineer",
    )

    from spacecdf_agents.tier1.aocs import AOCSAgent
    aocs = AOCSAgent()
    agent_result = await aocs.execute(state)
    state.update(agent_result)

    final = state.get_param("aocs.mass_kg")
    assert final.source == ParameterSource.POSITION_OVERRIDE
    assert final.value == 0.5


def test_parameter_source_is_sticky_enum():
    """Verify the sticky property definitions are correct."""
    assert ParameterSource.KB_COMPONENT.is_sticky
    assert ParameterSource.POSITION_OVERRIDE.is_sticky
    assert ParameterSource.REQUIREMENT.is_sticky
    assert not ParameterSource.COMPUTED.is_sticky
    assert not ParameterSource.ASSUMED.is_sticky
    assert not ParameterSource.SELECTED.is_sticky


def test_monte_carlo_percentile_ordering():
    """P50 < P70 < P80 < P90 always."""
    from spacecdf_server.services.cost_engine import WBSElement, monte_carlo

    wbs = [
        WBSElement(wbs_id="X.01", name="PM", total_keur=500),
        WBSElement(wbs_id="X.02", name="SE", total_keur=400),
        WBSElement(wbs_id="X.06.01", name="Structures", total_keur=200),
        WBSElement(wbs_id="X.06.02", name="Power", total_keur=300),
        WBSElement(wbs_id="X.08", name="Launch", total_keur=1000),
    ]
    r = monte_carlo(wbs, n=1000, seed=42)
    assert r["p50"] < r["p70"] < r["p80"] < r["p90"], (
        f"Percentile ordering broken: {r['p50']} < {r['p70']} < {r['p80']} < {r['p90']}"
    )
    # Histogram must exist
    assert len(r.get("hist", [])) > 0


def test_monte_carlo_deterministic_with_seed():
    """Same seed produces same percentiles."""
    from spacecdf_server.services.cost_engine import WBSElement, monte_carlo
    wbs = [WBSElement(wbs_id=f"X.{i}", name=f"item{i}", total_keur=100 * (i + 1)) for i in range(10)]
    r1 = monte_carlo(wbs, n=500, seed=123)
    r2 = monte_carlo(wbs, n=500, seed=123)
    assert r1["p50"] == r2["p50"]
    assert r1["p90"] == r2["p90"]


@pytest.mark.asyncio
async def test_sensitivity_sweep_does_not_mutate_baseline():
    """Running a sensitivity sweep must not modify the original requirements object."""
    from spacecdf_server.services.analysis import run_sensitivity

    baseline_dump = REF_REQ.model_dump_json()
    baseline_hash = hashlib.md5(baseline_dump.encode()).hexdigest()

    result = await run_sensitivity(REF_REQ, "orbit.altitude_km", [400, 500, 600])
    assert len(result.points) == 3

    post_dump = REF_REQ.model_dump_json()
    post_hash = hashlib.md5(post_dump.encode()).hexdigest()
    assert baseline_hash == post_hash, "Sensitivity sweep mutated the baseline requirements"
