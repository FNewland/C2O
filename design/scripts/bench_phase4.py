#!/usr/bin/env python3
"""Phase 4 hot-path latency benchmark.

Measures:
  - Full convergence latency (should be 3-12ms typical, <100ms p95)
  - Selective re-convergence latency (should be <50ms typical)
  - Monte Carlo cost analysis (<50ms for n=1000)
  - Sensitivity sweep (<500ms for 20 points)
  - Compliance matrix build (<100ms)

Usage: python3 scripts/bench_phase4.py
"""
from __future__ import annotations

import asyncio
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for pkg in ("spacecdf-common", "spacecdf-agents", "spacecdf-kb", "spacecdf-server"):
    src = ROOT / "packages" / pkg / "src"
    if src.exists():
        sys.path.insert(0, str(src))

from spacecdf_common.models.study import MissionRequirements
from spacecdf_common.models.parameter import ParameterSource, ParameterValue
from spacecdf_agents import ConvergenceConfig, DesignLoopOrchestrator

REF_REQ = MissionRequirements.model_validate({
    "name": "EOSAT-1 bench",
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


def summary(name: str, times_ms: list[float], budget_ms: float) -> bool:
    p50 = statistics.median(times_ms)
    p95 = sorted(times_ms)[int(len(times_ms) * 0.95)] if len(times_ms) > 1 else times_ms[0]
    ok = p95 < budget_ms
    mark = "✓" if ok else "✗"
    print(f"  {mark} {name:40s}  p50={p50:7.2f}ms  p95={p95:7.2f}ms  budget={budget_ms}ms")
    return ok


async def bench_full_convergence(n: int = 20) -> list[float]:
    orchestrator = DesignLoopOrchestrator(ConvergenceConfig(max_iterations=50))
    orchestrator.initialise_agents()
    times = []
    # Warmup
    await orchestrator.run(REF_REQ)
    for _ in range(n):
        t0 = time.monotonic()
        await orchestrator.run(REF_REQ)
        times.append((time.monotonic() - t0) * 1000)
    return times


async def bench_selective_reconvergence(n: int = 20) -> list[float]:
    from spacecdf_server.services.reconvergence import SelectiveReconvergence

    orchestrator = DesignLoopOrchestrator()
    orchestrator.initialise_agents()
    result = await orchestrator.run(REF_REQ)
    state = result.final_state

    reconverger = SelectiveReconvergence()
    reconverger.initialise()

    times = []
    for i in range(n):
        # Apply a simulated KB_COMPONENT edit
        state._parameters["power.battery_capacity_wh"] = ParameterValue(
            id="power.battery_capacity_wh",
            name="Battery capacity",
            value=77.0 + i * 0.1,  # Tiny perturbations
            unit="Wh",
            domain="power",
            source=ParameterSource.KB_COMPONENT,
            equipment_id="bench-bat",
        )
        t0 = time.monotonic()
        await reconverger.reconverge(state, {"power.battery_capacity_wh"})
        times.append((time.monotonic() - t0) * 1000)
    return times


def bench_monte_carlo(n_runs: int = 10) -> list[float]:
    from spacecdf_server.services.cost_engine import WBSElement, monte_carlo

    wbs = [WBSElement(wbs_id=f"X.{i}", name=f"item{i}", total_keur=100 * (i + 1)) for i in range(40)]
    times = []
    # Warmup
    monte_carlo(wbs, n=1000)
    for _ in range(n_runs):
        t0 = time.monotonic()
        monte_carlo(wbs, n=1000)
        times.append((time.monotonic() - t0) * 1000)
    return times


async def bench_sensitivity_sweep(n: int = 5) -> list[float]:
    from spacecdf_server.services.analysis import run_sensitivity
    times = []
    for _ in range(n):
        t0 = time.monotonic()
        await run_sensitivity(REF_REQ, "orbit.altitude_km", [350, 400, 450, 500, 550, 600, 650])
        times.append((time.monotonic() - t0) * 1000)
    return times


async def bench_compliance(n: int = 10) -> list[float]:
    from spacecdf_server.services.verification import build_compliance_matrix
    orchestrator = DesignLoopOrchestrator()
    orchestrator.initialise_agents()
    result = await orchestrator.run(REF_REQ)
    state = result.final_state

    times = []
    for _ in range(n):
        t0 = time.monotonic()
        build_compliance_matrix(state, worst_case="nominal")
        times.append((time.monotonic() - t0) * 1000)
    return times


async def main():
    print("=" * 70)
    print("  SpaceCDF Phase 4 hot-path benchmark")
    print("=" * 70)
    print()

    all_ok = []

    print("Full convergence (n=20):")
    all_ok.append(summary("Full convergence", await bench_full_convergence(20), 100))

    print("\nSelective re-convergence (n=20):")
    all_ok.append(summary("Selective re-convergence", await bench_selective_reconvergence(20), 50))

    print("\nMonte Carlo cost (n=10, samples=1000):")
    all_ok.append(summary("Monte Carlo cost", bench_monte_carlo(10), 100))

    print("\nSensitivity sweep (n=5, 7 points each):")
    all_ok.append(summary("Sensitivity sweep 7pt", await bench_sensitivity_sweep(5), 500))

    print("\nCompliance matrix (n=10):")
    all_ok.append(summary("Compliance matrix", await bench_compliance(10), 100))

    print()
    print("=" * 70)
    if all(all_ok):
        print("  ✓ All latency budgets met")
    else:
        print("  ✗ Some budgets exceeded")
    print("=" * 70)
    return 0 if all(all_ok) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
