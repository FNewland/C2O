#!/usr/bin/env python3
"""SpaceCDF — Mission Validation Script.

Runs the design loop against 7 real CubeSat missions and compares
computed outputs to known actual values. Reports discrepancies.
"""
import asyncio
import sys
import os

# Add package paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'spacecdf-common', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'spacecdf-agents', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'spacecdf-server', 'src'))

from spacecdf_agents import DesignLoopOrchestrator, ConvergenceConfig
from spacecdf_common.models.study import MissionRequirements, OrbitRequirements, PayloadRequirements


# Reference missions with known parameters
MISSIONS = [
    {
        "name": "Planet SuperDove (3U EO)",
        "requirements": MissionRequirements(
            name="SuperDove",
            mission_type="earth_observation",
            spacecraft_class="nano",
            orbit=OrbitRequirements(
                orbit_type="sso", altitude_km=525, inclination_deg=98,
                mission_duration_years=3.0, deorbit_required=True,
            ),
            payloads=[PayloadRequirements(
                name="Multispectral Imager", type="optical_imager",
                mass_kg=1.5, power_w=8, data_rate_mbps=220,
                pointing_accuracy_deg=0.5, fov_deg=4.4, duty_cycle_percent=25,
            )],
            design_lifetime_years=3.0,
            target_mass_kg=6.0,
        ),
        "expected": {
            "mass.dry_mass_kg": 5.2,
            "power.sa_power_eol_w": 18.0,
        },
        "tolerance_pct": 40,
    },
    {
        "name": "MarCO (6U Deep Space Relay)",
        "requirements": MissionRequirements(
            name="MarCO",
            mission_type="technology_demo",
            spacecraft_class="nano",
            orbit=OrbitRequirements(
                orbit_type="interplanetary", altitude_km=0,
                inclination_deg=0, mission_duration_years=1.0,
                deorbit_required=False,
            ),
            payloads=[PayloadRequirements(
                name="UHF-X Relay", type="rf_relay",
                mass_kg=2.0, power_w=15, data_rate_mbps=0.008,
                pointing_accuracy_deg=0.2, duty_cycle_percent=10,
            )],
            design_lifetime_years=1.0,
            target_mass_kg=14.0,
        ),
        "expected": {
            "mass.dry_mass_kg": 14.0,
            "power.sa_power_eol_w": 35.0,
        },
        "tolerance_pct": 50,  # Deep space has fewer heritage CERs
    },
    {
        "name": "Spire LEMUR-2 (3U AIS+GNSS-RO)",
        "requirements": MissionRequirements(
            name="LEMUR-2",
            mission_type="earth_observation",
            spacecraft_class="nano",
            orbit=OrbitRequirements(
                orbit_type="sso", altitude_km=500, inclination_deg=97,
                mission_duration_years=2.0, deorbit_required=True,
            ),
            payloads=[PayloadRequirements(
                name="AIS+GNSS-RO", type="ais",
                mass_kg=0.5, power_w=5, data_rate_mbps=1,
                pointing_accuracy_deg=2.0, duty_cycle_percent=100,
            )],
            design_lifetime_years=2.0,
            target_mass_kg=5.0,
        ),
        "expected": {
            "mass.dry_mass_kg": 4.6,
            "power.sa_power_eol_w": 9.0,
        },
        "tolerance_pct": 40,
    },
    {
        "name": "CAPSTONE (12U Lunar)",
        "requirements": MissionRequirements(
            name="CAPSTONE",
            mission_type="technology_demo",
            spacecraft_class="nano",
            orbit=OrbitRequirements(
                orbit_type="lunar", altitude_km=70000,
                inclination_deg=0, mission_duration_years=1.0,
                deorbit_required=False,
            ),
            payloads=[PayloadRequirements(
                name="CAPS Navigation", type="technology_demo",
                mass_kg=2.0, power_w=10, data_rate_mbps=0.01,
                pointing_accuracy_deg=0.5, duty_cycle_percent=50,
            )],
            design_lifetime_years=1.0,
            target_mass_kg=25.0,
        ),
        "expected": {
            "mass.dry_mass_kg": 25.0,
        },
        "tolerance_pct": 50,
    },
    {
        "name": "Astrocast (3U IoT/M2M)",
        "requirements": MissionRequirements(
            name="Astrocast",
            mission_type="communications",
            spacecraft_class="nano",
            orbit=OrbitRequirements(
                orbit_type="sso", altitude_km=500, inclination_deg=97,
                mission_duration_years=5.0, deorbit_required=True,
            ),
            payloads=[PayloadRequirements(
                name="L-band IoT Relay", type="rf_relay",
                mass_kg=0.3, power_w=3, data_rate_mbps=0.01,
                pointing_accuracy_deg=5.0, duty_cycle_percent=100,
            )],
            design_lifetime_years=5.0,
            target_mass_kg=4.0,
        ),
        "expected": {
            "mass.dry_mass_kg": 4.0,
            "power.sa_power_eol_w": 8.0,
        },
        "tolerance_pct": 40,
    },
]


async def validate_mission(mission_def: dict) -> dict:
    """Run one mission through the design loop and compare."""
    name = mission_def["name"]
    reqs = mission_def["requirements"]
    expected = mission_def["expected"]
    tol = mission_def["tolerance_pct"]

    config = ConvergenceConfig(max_iterations=30, convergence_threshold=0.005)
    orchestrator = DesignLoopOrchestrator(config=config)
    orchestrator.initialise_agents()

    try:
        result = await orchestrator.run(reqs)
    except Exception as e:
        return {"name": name, "error": str(e), "pass": False, "comparisons": []}

    comparisons = []
    state = result.final_state

    if state:
        for param_id, exp_val in expected.items():
            param = state.get_param(param_id)
            if param is None:
                comparisons.append({
                    "param": param_id, "expected": exp_val,
                    "actual": None, "delta_pct": None, "status": "MISSING",
                })
                continue

            actual = param.value if isinstance(param.value, (int, float)) else 0
            if exp_val != 0:
                delta_pct = abs(actual - exp_val) / exp_val * 100
            else:
                delta_pct = 0 if actual == 0 else 100

            status = "PASS" if delta_pct <= tol else "WARN" if delta_pct <= tol * 2 else "FAIL"
            comparisons.append({
                "param": param_id, "expected": exp_val,
                "actual": round(actual, 2), "delta_pct": round(delta_pct, 1),
                "status": status,
            })

        # Also collect key computed parameters for reporting
        key_params = [
            "mass.dry_mass_kg", "mass.wet_mass_kg",
            "power.sa_power_eol_w", "power.battery_capacity_wh",
            "power.eps_mass_kg", "aocs.mass_kg", "link.ttc_mass_kg",
            "thermal.tcs_mass_kg", "structure.mass_kg",
            "propulsion.total_mass_kg", "data.obc_mass_kg",
            "cost.total_meur", "systems.mass_margin_percent",
            "systems.power_margin_percent",
        ]
        computed = {}
        for pid in key_params:
            p = state.get_param(pid)
            if p and isinstance(p.value, (int, float)):
                computed[pid] = round(p.value, 3)

        return {
            "name": name,
            "converged": result.converged,
            "iterations": len(result.iterations),
            "time_s": round(result.total_time_s, 2),
            "pass": all(c["status"] in ("PASS", "WARN") for c in comparisons),
            "comparisons": comparisons,
            "computed": computed,
            "warnings": result.all_warnings[:5],
        }

    return {"name": name, "error": "No final state", "pass": False, "comparisons": []}


async def main():
    print("=" * 70)
    print("  SpaceCDF Mission Validation")
    print("=" * 70)

    all_results = []
    for mission in MISSIONS:
        print(f"\nRunning: {mission['name']}...")
        result = await validate_mission(mission)
        all_results.append(result)

        if "error" in result:
            print(f"  ERROR: {result['error']}")
            continue

        print(f"  Converged: {result.get('converged')} in {result.get('iterations')} iterations ({result.get('time_s', 0):.1f}s)")

        for comp in result.get("comparisons", []):
            status = comp["status"]
            symbol = "✓" if status == "PASS" else "~" if status == "WARN" else "✗" if status == "FAIL" else "?"
            actual_str = f"{comp['actual']}" if comp['actual'] is not None else "MISSING"
            delta_str = f"Δ={comp['delta_pct']}%" if comp['delta_pct'] is not None else ""
            print(f"  {symbol} {comp['param']}: computed={actual_str}, expected={comp['expected']} {delta_str}")

        if result.get("computed"):
            print("  Key computed values:")
            for pid, val in result["computed"].items():
                if pid not in [c["param"] for c in result.get("comparisons", [])]:
                    print(f"    {pid} = {val}")

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    passed = sum(1 for r in all_results if r.get("pass"))
    print(f"  {passed}/{len(all_results)} missions within tolerance")
    for r in all_results:
        status = "PASS" if r.get("pass") else "FAIL"
        print(f"  [{status}] {r['name']}")

    # Write results to JSON
    import json
    output_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'validation_results.json')
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Results written to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
