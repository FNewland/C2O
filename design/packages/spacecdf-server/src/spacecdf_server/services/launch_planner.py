"""SpaceCDF — Launch Campaign Planner.

Launch vehicle compatibility check, rideshare matching, campaign
timeline, regulatory filing support, and export control assessment.
Stage 7 of CubeSat full lifecycle capability.
"""
from __future__ import annotations

from typing import Any


# Launch vehicle database (rideshare-compatible for CubeSats)
LAUNCH_VEHICLES: list[dict[str, Any]] = [
    {
        "name": "SpaceX Falcon 9 (Transporter rideshare)",
        "provider": "SpaceX / Spaceflight Inc / Exolaunch",
        "orbit": "SSO 500-550 km",
        "max_mass_kg": 200, "max_volume_U": 24,
        "deployer": "ISIPOD / EXApod",
        "frequency": "quarterly",
        "cost_keur_per_kg": 5,
        "min_cost_keur": 200,
        "lead_time_months": 6,
        "vibration_g_rms": 7.7,
        "notes": "Most frequent rideshare, SSO standard",
    },
    {
        "name": "Rocket Lab Electron (dedicated or rideshare)",
        "provider": "Rocket Lab",
        "orbit": "SSO 300-600 km (flexible)",
        "max_mass_kg": 300, "max_volume_U": 48,
        "deployer": "CubeSat deployer or custom adapter",
        "frequency": "monthly",
        "cost_keur_per_kg": 25,
        "min_cost_keur": 5000,
        "lead_time_months": 12,
        "vibration_g_rms": 8.0,
        "notes": "Dedicated launch option for custom orbit",
    },
    {
        "name": "Vega-C (SSMS rideshare)",
        "provider": "Arianespace",
        "orbit": "SSO 500-800 km",
        "max_mass_kg": 150, "max_volume_U": 24,
        "deployer": "QuadPack / ISIPOD",
        "frequency": "biannual",
        "cost_keur_per_kg": 8,
        "min_cost_keur": 300,
        "lead_time_months": 12,
        "vibration_g_rms": 8.5,
        "notes": "European launch, ITAR-free",
    },
    {
        "name": "PSLV (rideshare)",
        "provider": "ISRO / Antrix",
        "orbit": "SSO 500-700 km",
        "max_mass_kg": 100, "max_volume_U": 24,
        "deployer": "ISIPOD",
        "frequency": "quarterly",
        "cost_keur_per_kg": 4,
        "min_cost_keur": 150,
        "lead_time_months": 9,
        "vibration_g_rms": 6.5,
        "notes": "Cost-effective Indian launch",
    },
    {
        "name": "ISS deployment (NanoRacks / SpaceX CRS)",
        "provider": "NanoRacks",
        "orbit": "ISS orbit ~420 km, 51.6° incl",
        "max_mass_kg": 12, "max_volume_U": 6,
        "deployer": "NRCSD",
        "frequency": "with CRS missions",
        "cost_keur_per_kg": 10,
        "min_cost_keur": 80,
        "lead_time_months": 6,
        "vibration_g_rms": 6.0,
        "notes": "Fixed orbit (51.6°), rapid decay (~1 year from 420 km)",
    },
    {
        "name": "D-Orbit ION (last-mile delivery)",
        "provider": "D-Orbit",
        "orbit": "Custom (within ION capability)",
        "max_mass_kg": 150, "max_volume_U": 48,
        "deployer": "ION internal deployer",
        "frequency": "quarterly",
        "cost_keur_per_kg": 15,
        "min_cost_keur": 400,
        "lead_time_months": 9,
        "vibration_g_rms": 7.0,
        "notes": "Precise orbit delivery, multiple deployment opportunities",
    },
    {
        "name": "Firefly Alpha",
        "provider": "Firefly Aerospace",
        "orbit": "SSO/LEO 300-600 km",
        "max_mass_kg": 1000, "max_volume_U": 96,
        "deployer": "Custom adapter",
        "frequency": "quarterly",
        "cost_keur_per_kg": 15,
        "min_cost_keur": 12000,
        "lead_time_months": 12,
        "vibration_g_rms": 7.5,
        "notes": "US small launch vehicle",
    },
]

# Rideshare brokers
RIDESHARE_BROKERS = [
    {"name": "Spaceflight Inc", "website": "spaceflight.com", "services": "Rideshare booking, integration, regulatory"},
    {"name": "Exolaunch", "website": "exolaunch.com", "services": "Rideshare, deployment, mission management"},
    {"name": "D-Orbit", "website": "d-orbit.com", "services": "Last-mile delivery, custom orbit deployment"},
    {"name": "ISILaunch", "website": "isilaunch.com", "services": "CubeSat launch services, ISIPOD integration"},
    {"name": "Momentus", "website": "momentus.space", "services": "In-space transportation, orbit raising"},
]


def check_launch_compatibility(
    spacecraft_mass_kg: float,
    spacecraft_volume_U: int,
    target_orbit_type: str = "sso",
    target_altitude_km: float = 500,
    target_inclination_deg: float = 97.4,
) -> dict[str, Any]:
    """Check compatibility with available launch vehicles."""
    compatible = []
    incompatible = []

    for lv in LAUNCH_VEHICLES:
        issues = []
        if spacecraft_mass_kg > lv["max_mass_kg"]:
            issues.append(f"Mass {spacecraft_mass_kg:.1f} kg exceeds max {lv['max_mass_kg']} kg")
        if spacecraft_volume_U > lv["max_volume_U"]:
            issues.append(f"Volume {spacecraft_volume_U}U exceeds max {lv['max_volume_U']}U")

        # Check orbit compatibility
        lv_orbit = lv["orbit"].lower()
        if target_orbit_type == "sso" and "sso" not in lv_orbit and "flexible" not in lv_orbit and "custom" not in lv_orbit:
            if "iss" in lv_orbit:
                issues.append(f"ISS orbit (51.6°) — cannot reach SSO ({target_inclination_deg}°)")

        cost_keur = max(spacecraft_mass_kg * lv["cost_keur_per_kg"], lv["min_cost_keur"])

        entry = {
            "launch_vehicle": lv["name"],
            "provider": lv["provider"],
            "compatible": len(issues) == 0,
            "issues": issues,
            "cost_estimate_keur": round(cost_keur, 0),
            "lead_time_months": lv["lead_time_months"],
            "deployer": lv["deployer"],
            "frequency": lv["frequency"],
            "vibration_g_rms": lv["vibration_g_rms"],
            "notes": lv["notes"],
        }

        if len(issues) == 0:
            compatible.append(entry)
        else:
            incompatible.append(entry)

    # Sort compatible by cost
    compatible.sort(key=lambda x: x["cost_estimate_keur"])

    return {
        "spacecraft": {
            "mass_kg": spacecraft_mass_kg,
            "volume_U": spacecraft_volume_U,
            "target_orbit": f"{target_orbit_type} {target_altitude_km} km, {target_inclination_deg}°",
        },
        "compatible": compatible,
        "incompatible": incompatible,
        "recommendation": compatible[0]["launch_vehicle"] if compatible else "No compatible launcher found",
        "rideshare_brokers": RIDESHARE_BROKERS,
    }


def generate_campaign_timeline(
    launch_vehicle: str = "SpaceX Falcon 9 (Transporter rideshare)",
    spacecraft_name: str = "SC1",
) -> list[dict[str, Any]]:
    """Generate a launch campaign timeline."""
    return [
        {"week": -24, "milestone": "Launch contract signed", "activities": ["Contract execution", "Schedule confirmation", "ICD exchange"]},
        {"week": -20, "milestone": "Fit check (if required)", "activities": ["Mechanical fit check with deployer", "Interface verification"]},
        {"week": -16, "milestone": "Environmental testing complete", "activities": ["Vibration test report delivered", "TVAC test report delivered", "EMC test report delivered"]},
        {"week": -12, "milestone": "Flight readiness review", "activities": ["All test reports reviewed", "Non-conformances dispositioned", "Flight software final version loaded"]},
        {"week": -8, "milestone": "Spacecraft delivery to integration site", "activities": [f"Ship {spacecraft_name} to launch site", "Receive and inspect", "Pre-integration functional test"]},
        {"week": -6, "milestone": "Integration with deployer", "activities": ["Install in deployer", "Deployment switch verification", "Umbilical connection test", "RF compatibility test"]},
        {"week": -4, "milestone": "Combined operations test", "activities": ["End-to-end communication test via launch vehicle", "Charge batteries to flight level", "Verify deployment sequence"]},
        {"week": -2, "milestone": "Encapsulation", "activities": ["Final visual inspection", "Remove Before Flight items removed", "Deployer closed and sealed"]},
        {"week": -1, "milestone": "Launch rehearsal", "activities": ["Countdown rehearsal", "Ground station readiness verification", "Operations team in position"]},
        {"week": 0, "milestone": "LAUNCH", "activities": ["Launch!", "Separation confirmation", "First beacon acquisition"]},
    ]


def generate_regulatory_checklist(
    orbit_altitude_km: float,
    frequency_mhz: float,
    spacecraft_mass_kg: float,
    country: str = "UK",
) -> list[dict[str, Any]]:
    """Generate regulatory filing checklist."""
    items = [
        {
            "item": "Frequency coordination (ITU)",
            "authority": "ITU via national administration",
            "description": f"File for {frequency_mhz} MHz allocation. Coordinate with neighbouring satellite operators.",
            "lead_time_months": 6,
            "status": "not_started",
        },
        {
            "item": f"National spectrum licence ({country})",
            "authority": "Ofcom (UK) / FCC (US) / ANFR (FR)",
            "description": f"Apply for spectrum licence to operate at {frequency_mhz} MHz from {country}",
            "lead_time_months": 3,
            "status": "not_started",
        },
        {
            "item": "Space debris mitigation compliance",
            "authority": "National space agency / UN COPUOS",
            "description": f"Demonstrate compliance with 25-year (or 5-year) deorbit rule at {orbit_altitude_km} km",
            "lead_time_months": 2,
            "status": "not_started",
        },
        {
            "item": "Third-party liability insurance",
            "authority": "Insurance broker",
            "description": f"Obtain space insurance for {spacecraft_mass_kg} kg spacecraft. Typical: 500k-2M EUR for CubeSat.",
            "lead_time_months": 2,
            "status": "not_started",
        },
        {
            "item": "Export control clearance",
            "authority": "National export control authority",
            "description": "Verify all components clear for export to launch site country. Check ITAR/EAR for US-origin parts.",
            "lead_time_months": 3,
            "status": "not_started",
        },
        {
            "item": "Space object registration",
            "authority": "UN Office for Outer Space Affairs (UNOOSA)",
            "description": "Register space object per UN Registration Convention (via national registry)",
            "lead_time_months": 1,
            "status": "not_started",
        },
    ]

    # UK-specific: Outer Space Act licence
    if country.upper() in ("UK", "GB"):
        items.insert(2, {
            "item": "UK Space Agency Outer Space Act licence",
            "authority": "UK Space Agency (via CAA)",
            "description": "Mandatory licence for UK entities operating spacecraft. Application includes orbital debris assessment.",
            "lead_time_months": 6,
            "status": "not_started",
        })

    return items
