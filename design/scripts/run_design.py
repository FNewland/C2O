#!/usr/bin/env python3
"""SpaceCDF — Standalone design loop runner.

Runs the full concurrent design loop from a YAML mission requirements
file and prints the results. No server needed.

Usage:
    python scripts/run_design.py configs/examples/6u_eo_cubesat.yaml
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add package source directories to path for development
root = Path(__file__).resolve().parent.parent
for pkg in ["spacecdf-common", "spacecdf-agents", "spacecdf-kb"]:
    src = root / "packages" / pkg / "src"
    if src.exists():
        sys.path.insert(0, str(src))

from spacecdf_common.config.loader import load_yaml
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents import DesignLoopOrchestrator, ConvergenceConfig


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def main():
    # Load mission requirements
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
    else:
        config_path = root / "configs" / "examples" / "6u_eo_cubesat.yaml"

    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        sys.exit(1)

    print(f"Loading requirements from: {config_path}")
    data = load_yaml(config_path)
    requirements = MissionRequirements.model_validate(data)

    print_section(f"MISSION: {requirements.name}")
    print(f"  Type: {requirements.mission_type}")
    print(f"  Class: {requirements.spacecraft_class}")
    print(f"  Orbit: {requirements.orbit.orbit_type} @ {requirements.orbit.altitude_km} km")
    print(f"  Duration: {requirements.design_lifetime_years} years")
    print(f"  Payloads: {len(requirements.payloads)}")
    for pl in requirements.payloads:
        print(f"    - {pl.name}: {pl.mass_kg}kg, {pl.power_w}W, {pl.data_rate_mbps}Mbps")

    # Run design loop
    config = ConvergenceConfig(max_iterations=50, convergence_threshold=0.001)
    orchestrator = DesignLoopOrchestrator(config=config)
    orchestrator.initialise_agents()

    print_section("RUNNING DESIGN LOOP")
    result = await orchestrator.run(requirements)

    # Results
    print_section("CONVERGENCE")
    print(f"  Converged: {result.converged}")
    print(f"  Iterations: {len(result.iterations)}")
    print(f"  Time: {result.total_time_s:.3f}s")
    if result.iterations:
        last = result.iterations[-1]
        print(f"  Final max delta: {last.max_parameter_delta:.6f}")

    # Parameters by domain
    print_section("DESIGN PARAMETERS")
    if result.final_state:
        domains: dict[str, list] = {}
        for pid, p in sorted(result.final_state.parameters.items()):
            domain = p.domain
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(p)

        for domain in sorted(domains.keys()):
            print(f"\n  [{domain.upper()}]")
            for p in domains[domain]:
                val = p.value
                if isinstance(val, float):
                    val = f"{val:.2f}"
                margin_str = f" (±{p.margin_percent:.0f}%)" if p.margin_percent > 0 else ""
                conf_str = f" [{p.confidence:.0%}]" if p.confidence < 1.0 else ""
                print(f"    {p.name:.<40s} {val} {p.unit}{margin_str}{conf_str}")

    # Budgets
    print_section("SYSTEM BUDGETS")
    for btype, budget in result.budgets.items():
        status_emoji = {"green": "[OK]", "amber": "[!!]", "red": "[XX]", "exceeded": "[!!]"}
        status = status_emoji.get(budget.status.value, "  ")
        print(f"\n  {status} {btype.upper()} BUDGET")
        print(f"    Total (nominal): {budget.total_nominal:.1f} {budget.unit}")
        print(f"    Total (w/margin): {budget.total_with_margin:.1f} {budget.unit}")
        print(f"    Allocation: {budget.allocation:.1f} {budget.unit}")
        print(f"    Margin: {budget.margin_percent:.1f}%")
        print(f"    Status: {budget.status.value}")

    # Warnings
    if result.all_warnings:
        print_section("WARNINGS")
        for w in result.all_warnings:
            print(f"  - {w}")

    # Recommendations
    if result.all_recommendations:
        print_section("RECOMMENDATIONS")
        for r in result.all_recommendations:
            print(f"  - {r}")

    # Agent results summary
    print_section("AGENT EXECUTION SUMMARY")
    for name, ar in result.agent_results.items():
        print(f"  {name}: {len(ar.parameters)} params, {len(ar.warnings)} warnings, confidence={ar.confidence:.0%}")


if __name__ == "__main__":
    asyncio.run(main())
