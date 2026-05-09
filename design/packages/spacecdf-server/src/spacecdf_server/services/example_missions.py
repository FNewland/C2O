"""SpaceCDF — Pre-loaded Example Missions.

Ready-to-load mission definitions that populate requirements, mission need,
and selected equipment.  Used by the /api/lifecycle/example-missions endpoint
and the frontend "Load Example" button.
"""
from __future__ import annotations

from typing import Any


EXAMPLE_MISSIONS: dict[str, dict[str, Any]] = {
    "unisat1_1u_techdemo": {
        "name": "UniSat-1 (1U Tech Demo)",
        "description": (
            "1U CubeSat technology demonstrator — MEMS magnetometer "
            "for space weather monitoring"
        ),
        "requirements": {
            "name": "UniSat-1",
            "mission_type": "technology_demo",
            "spacecraft_class": "nano",
            "orbit": {
                "orbit_type": "leo",
                "altitude_km": 400,
                "inclination_deg": 51.6,
                "mission_duration_years": 0.5,
                "deorbit_required": False,  # Natural decay in ~1 yr
            },
            "payloads": [
                {
                    "name": "MEMS Magnetometer",
                    "mass_kg": 0.05,
                    "power_w": 0.2,
                    "data_rate_mbps": 0.001,  # 1 kbps
                    "pointing_accuracy_deg": 30,  # No fine pointing needed
                    "duty_cycle_percent": 100,  # Always on
                },
            ],
            "design_lifetime_years": 0.5,
            "target_mass_kg": 1.33,
            "target_cost_meur": 0.2,
            "ground_stations": ["University Ground Station"],
        },
        "mission_need": {
            "problem_statement": (
                "Space weather monitoring requires in-situ magnetic field "
                "measurements at LEO altitudes. Current instruments are "
                "expensive and heavy. A MEMS-based magnetometer could enable "
                "distributed measurement networks using low-cost CubeSats."
            ),
            "operational_context": (
                "ISS orbit for rideshare deployment. UHF amateur band for "
                "TTC. University-operated ground station."
            ),
            "objectives": [
                {
                    "id": "OBJ-1",
                    "text": (
                        "Demonstrate MEMS magnetometer operation in LEO environment"
                    ),
                    "priority": "primary",
                    "type": "technology",
                    "measurable_criterion": (
                        "Magnetometer returns calibrated 3-axis data for >= 3 months"
                    ),
                },
                {
                    "id": "OBJ-2",
                    "text": (
                        "Validate MEMS sensor against reference magnetometer data "
                        "(INTERMAGNET)"
                    ),
                    "priority": "primary",
                    "type": "performance",
                    "measurable_criterion": (
                        "Correlation coefficient >= 0.9 with ground reference"
                    ),
                },
                {
                    "id": "OBJ-3",
                    "text": (
                        "Demonstrate end-to-end mission operations with student team"
                    ),
                    "priority": "secondary",
                    "type": "educational",
                    "measurable_criterion": (
                        "Team operates mission for full design lifetime"
                    ),
                },
            ],
            "stakeholders": [
                {
                    "name": "University Research Lab",
                    "role": "Mission owner and operator",
                    "needs": ["magnetometer data", "flight heritage for sensor"],
                    "constraints": ["budget < 200 kEUR", "12-month schedule"],
                },
                {
                    "name": "Student Team",
                    "role": "Design and operations team",
                    "needs": ["hands-on experience", "thesis material"],
                    "constraints": ["limited experience"],
                },
            ],
        },
        "selected_equipment": [
            {
                "category": "cubesat_structures",
                "componentId": "struct-isis-1u",
                "name": "1U CubeSat Structure",
                "mass_kg": 0.2,
                "power_w": 0,
                "cost_keur": 5,
                "quantity": 1,
            },
            {
                "category": "eps_boards",
                "componentId": "eps-gom-nanopow-p31us",
                "name": "NanoPower P31us",
                "mass_kg": 0.042,
                "power_w": 0,
                "cost_keur": 8,
                "quantity": 1,
            },
            {
                "category": "batteries",
                "componentId": "bat-gom-nanopow-p31u",
                "name": "NanoPower P31u Battery",
                "mass_kg": 0.06,
                "power_w": 0,
                "cost_keur": 5,
                "quantity": 1,
            },
            {
                "category": "solar_panels",
                "componentId": "sp-endurosat-1u-body",
                "name": "1U Body-Mounted Solar Panel",
                "mass_kg": 0.03,
                "power_w": 2.3,
                "cost_keur": 3,
                "quantity": 5,
            },
            {
                "category": "transponders",
                "componentId": "txr-isis-trxvu",
                "name": "TRXVU VHF/UHF Transceiver",
                "mass_kg": 0.08,
                "power_w": 4.8,
                "cost_keur": 10,
                "quantity": 1,
            },
            {
                "category": "antennas",
                "componentId": "ant-uhf-monopole",
                "name": "UHF Monopole Antenna",
                "mass_kg": 0.01,
                "power_w": 0,
                "cost_keur": 1,
                "quantity": 1,
            },
            {
                "category": "obcs",
                "componentId": "obc-endurosat-type-i",
                "name": "Endurosat OBC Type I",
                "mass_kg": 0.058,
                "power_w": 0.5,
                "cost_keur": 10,
                "quantity": 1,
            },
        ],
    },
    "superdove_3u_eo": {
        "name": "SuperDove-X (3U EO)",
        "description": (
            "3U Earth observation CubeSat — multispectral imagery at 3-5m GSD"
        ),
        "requirements": {
            "name": "SuperDove-X",
            "mission_type": "earth_observation",
            "spacecraft_class": "nano",
            "orbit": {
                "orbit_type": "sso",
                "altitude_km": 500,
                "inclination_deg": 97.4,
                "mission_duration_years": 3,
                "deorbit_required": True,
            },
            "payloads": [
                {
                    "name": "Multispectral Imager",
                    "mass_kg": 1.5,
                    "power_w": 10,
                    "data_rate_mbps": 100,
                    "pointing_accuracy_deg": 0.1,
                    "duty_cycle_percent": 25,
                },
            ],
            "design_lifetime_years": 3,
            "target_mass_kg": 5,
            "target_cost_meur": 3,
            "ground_stations": ["KSAT Svalbard"],
        },
        "mission_need": {
            "problem_statement": (
                "Frequent, high-resolution multispectral Earth imagery is "
                "needed for agricultural monitoring, environmental change "
                "detection, and disaster response. A 3U CubeSat with a "
                "compact imager can provide 3-5m GSD at low cost."
            ),
            "operational_context": (
                "Sun-synchronous orbit for consistent lighting. S-band "
                "downlink to KSAT Svalbard for high data volume. Autonomous "
                "imaging with tasking via ground command."
            ),
            "objectives": [
                {
                    "id": "OBJ-1",
                    "text": "Acquire multispectral imagery at 3-5m GSD",
                    "priority": "primary",
                    "type": "performance",
                    "measurable_criterion": (
                        "GSD <= 5m across all spectral bands"
                    ),
                },
                {
                    "id": "OBJ-2",
                    "text": "Achieve daily revisit for target areas",
                    "priority": "primary",
                    "type": "coverage",
                    "measurable_criterion": (
                        "Revisit time <= 24 hrs for latitudes 0-60 deg"
                    ),
                },
                {
                    "id": "OBJ-3",
                    "text": "Demonstrate 3-year operational lifetime",
                    "priority": "secondary",
                    "type": "reliability",
                    "measurable_criterion": (
                        "Satellite operational for >= 3 years"
                    ),
                },
            ],
            "stakeholders": [
                {
                    "name": "EO Data Provider",
                    "role": "Mission owner and data distributor",
                    "needs": ["high-quality imagery", "reliable data delivery"],
                    "constraints": ["cost < 3 MEUR per satellite"],
                },
            ],
        },
        "selected_equipment": [
            {
                "category": "cubesat_structures",
                "componentId": "struct-isis-3u",
                "name": "3U CubeSat Structure",
                "mass_kg": 0.35,
                "power_w": 0,
                "cost_keur": 8,
                "quantity": 1,
            },
            {
                "category": "eps_boards",
                "componentId": "eps-gom-nanopow-p31us",
                "name": "NanoPower P31us",
                "mass_kg": 0.042,
                "power_w": 0,
                "cost_keur": 8,
                "quantity": 1,
            },
            {
                "category": "batteries",
                "componentId": "bat-gom-nanopow-bp4",
                "name": "NanoPower BP4 Battery",
                "mass_kg": 0.22,
                "power_w": 0,
                "cost_keur": 10,
                "quantity": 1,
            },
            {
                "category": "solar_panels",
                "componentId": "sp-dhv-csa-3u-deploy",
                "name": "CSA 3U Deployable Array",
                "mass_kg": 0.28,
                "power_w": 7.0,
                "cost_keur": 15,
                "quantity": 2,
            },
            {
                "category": "transponders",
                "componentId": "txr-endurosat-sband",
                "name": "Endurosat S-Band Transceiver",
                "mass_kg": 0.246,
                "power_w": 12.0,
                "cost_keur": 20,
                "quantity": 1,
            },
            {
                "category": "antennas",
                "componentId": "ant-endurosat-sband-patch",
                "name": "S-Band Patch Antenna",
                "mass_kg": 0.045,
                "power_w": 0,
                "cost_keur": 3,
                "quantity": 1,
            },
            {
                "category": "obcs",
                "componentId": "obc-endurosat-type-i",
                "name": "Endurosat OBC Type I",
                "mass_kg": 0.058,
                "power_w": 0.5,
                "cost_keur": 10,
                "quantity": 1,
            },
        ],
    },
}


def get_example_mission(mission_id: str) -> dict | None:
    """Return a single example mission by ID, or None if not found."""
    return EXAMPLE_MISSIONS.get(mission_id)


def list_example_missions() -> list[dict]:
    """Return a summary list of all available example missions."""
    return [
        {
            "id": mid,
            "name": m["name"],
            "description": m["description"],
        }
        for mid, m in EXAMPLE_MISSIONS.items()
    ]
