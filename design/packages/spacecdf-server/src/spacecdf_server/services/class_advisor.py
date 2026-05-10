"""SpaceCDF — Mission Class Advisor.

From mission objectives, computes which spacecraft class fits:
nano/micro/small with performance envelope, cost range, schedule range,
risk profile, and comparison against historical similar missions.

This is the answer to "what class of spacecraft should I build?"
which should be COMPUTED from objectives, not hand-selected from a dropdown.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClassProfile:
    """Performance/cost/schedule envelope for a spacecraft class."""
    name: str
    class_id: str
    mass_range_kg: tuple[float, float]
    cost_range_meur: tuple[float, float]
    schedule_range_months: tuple[int, int]
    gsd_range_m: tuple[float, float]  # Achievable GSD range
    max_data_rate_mbps: float
    max_pointing_deg: float  # Best achievable pointing
    max_lifetime_years: float
    max_delta_v_ms: float
    typical_applications: list[str]
    risk_profile: str
    heritage_examples: list[str]
    fit_score: float = 0.0
    fit_rationale: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


# Class performance envelopes (from heritage data + industry surveys)
CLASS_PROFILES: list[ClassProfile] = [
    ClassProfile(
        name="Nano (CubeSat 1U-6U)", class_id="nano",
        mass_range_kg=(1, 12), cost_range_meur=(1, 10),
        schedule_range_months=(6, 18),
        gsd_range_m=(5, 100), max_data_rate_mbps=200,
        max_pointing_deg=0.05, max_lifetime_years=5,
        max_delta_v_ms=100,
        typical_applications=["Tech demo", "IoT", "Low-res EO", "Education", "AIS/ADS-B", "Comms relay"],
        risk_profile="Medium: COTS components, limited redundancy, standard buses. Good heritage database.",
        heritage_examples=["OPS-SAT (7kg, ESA)", "Dove (Planet, 5kg)", "NORSAT (14kg)", "EOSAT-1 (12kg)"],
    ),
    ClassProfile(
        name="Nano (CubeSat 12U-16U)", class_id="nano_large",
        mass_range_kg=(12, 30), cost_range_meur=(5, 20),
        schedule_range_months=(12, 24),
        gsd_range_m=(2, 30), max_data_rate_mbps=500,
        max_pointing_deg=0.02, max_lifetime_years=7,
        max_delta_v_ms=500,
        typical_applications=["High-res EO", "SAR demo", "Constellation member", "Science"],
        risk_profile="Medium: larger COTS components available, some redundancy possible.",
        heritage_examples=["CAPSTONE (25kg, NASA)", "MarCO (13.5kg, NASA)", "HaloSat (12kg)"],
    ),
    ClassProfile(
        name="Micro (20-150 kg)", class_id="micro",
        mass_range_kg=(20, 150), cost_range_meur=(10, 50),
        schedule_range_months=(18, 36),
        gsd_range_m=(1, 10), max_data_rate_mbps=800,
        max_pointing_deg=0.01, max_lifetime_years=10,
        max_delta_v_ms=1000,
        typical_applications=["High-res EO", "Targeted science", "Constellation ops", "Technology pathfinder"],
        risk_profile="BEYOND CUBESAT SCOPE — consider custom microsatellite platform if CubeSat form factor cannot meet requirements",
        heritage_examples=["PROBA-V (138kg, ESA)", "SSTL-42", "NovaSAR (450kg)", "TechDemoSat-1"],
    ),
    ClassProfile(
        name="Small (150-500 kg)", class_id="small",
        mass_range_kg=(150, 500), cost_range_meur=(30, 150),
        schedule_range_months=(24, 48),
        gsd_range_m=(0.3, 5), max_data_rate_mbps=2000,
        max_pointing_deg=0.005, max_lifetime_years=15,
        max_delta_v_ms=2000,
        typical_applications=["Operational EO service", "Dedicated science", "Deep space precursor", "Defence/intel"],
        risk_profile="WELL BEYOND CUBESAT SCOPE — SpaceCDF is not designed for this class. Consider ESA CDF or dedicated mission design tools.",
        heritage_examples=["LADEE (248kg, NASA)", "Sentinel-2 (1100kg)", "PRISMA (145kg, ASI)"],
    ),
]


def advise_mission_class(
    target_gsd_m: float | None = None,
    target_revisit_days: float | None = None,
    target_lifetime_years: float | None = None,
    target_data_rate_mbps: float | None = None,
    target_pointing_deg: float | None = None,
    max_budget_meur: float | None = None,
    max_schedule_months: int | None = None,
    mission_type: str = "earth_observation",
    delta_v_needed_ms: float = 0,
) -> dict[str, Any]:
    """Advise which spacecraft class fits the mission objectives.

    Returns scored class options with rationale and gaps.
    """
    results: list[dict] = []

    for profile in CLASS_PROFILES:
        fit_score = 0.0
        max_score = 0.0
        rationale: list[str] = []
        gaps: list[str] = []

        # GSD check
        if target_gsd_m is not None:
            max_score += 1.0
            if target_gsd_m >= profile.gsd_range_m[0]:
                fit_score += 1.0
                rationale.append(f"GSD {target_gsd_m}m achievable (range: {profile.gsd_range_m[0]}-{profile.gsd_range_m[1]}m)")
            else:
                gaps.append(f"GSD {target_gsd_m}m below class minimum {profile.gsd_range_m[0]}m")

        # Lifetime check
        if target_lifetime_years is not None:
            max_score += 1.0
            if target_lifetime_years <= profile.max_lifetime_years:
                fit_score += 1.0
                rationale.append(f"Lifetime {target_lifetime_years}yr achievable (max: {profile.max_lifetime_years}yr)")
            else:
                gaps.append(f"Lifetime {target_lifetime_years}yr exceeds class max {profile.max_lifetime_years}yr")

        # Data rate check
        if target_data_rate_mbps is not None:
            max_score += 1.0
            if target_data_rate_mbps <= profile.max_data_rate_mbps:
                fit_score += 1.0
                rationale.append(f"Data rate {target_data_rate_mbps} Mbps achievable")
            else:
                gaps.append(f"Data rate {target_data_rate_mbps} Mbps exceeds class max {profile.max_data_rate_mbps}")

        # Pointing check
        if target_pointing_deg is not None:
            max_score += 1.0
            if target_pointing_deg >= profile.max_pointing_deg:
                fit_score += 1.0
                rationale.append(f"Pointing {target_pointing_deg}° achievable (best: {profile.max_pointing_deg}°)")
            else:
                gaps.append(f"Pointing {target_pointing_deg}° tighter than class best {profile.max_pointing_deg}°")

        # Budget check
        if max_budget_meur is not None:
            max_score += 1.5  # Higher weight for budget
            if max_budget_meur >= profile.cost_range_meur[0]:
                if max_budget_meur >= profile.cost_range_meur[1]:
                    fit_score += 1.5
                    rationale.append(f"Budget {max_budget_meur} MEUR covers full range ({profile.cost_range_meur[0]}-{profile.cost_range_meur[1]})")
                else:
                    fit_score += 1.0
                    rationale.append(f"Budget {max_budget_meur} MEUR covers low end only ({profile.cost_range_meur[0]}-{profile.cost_range_meur[1]})")
            else:
                gaps.append(f"Budget {max_budget_meur} MEUR below class minimum {profile.cost_range_meur[0]} MEUR")

        # Schedule check
        if max_schedule_months is not None:
            max_score += 1.0
            if max_schedule_months >= profile.schedule_range_months[0]:
                fit_score += 1.0
                rationale.append(f"Schedule {max_schedule_months} months feasible ({profile.schedule_range_months[0]}-{profile.schedule_range_months[1]})")
            else:
                gaps.append(f"Schedule {max_schedule_months} months shorter than class minimum {profile.schedule_range_months[0]}")

        # Delta-V check
        if delta_v_needed_ms > 0:
            max_score += 0.5
            if delta_v_needed_ms <= profile.max_delta_v_ms:
                fit_score += 0.5
            else:
                gaps.append(f"Delta-V {delta_v_needed_ms} m/s exceeds class max {profile.max_delta_v_ms}")

        # Normalise
        profile.fit_score = (fit_score / max_score * 100) if max_score > 0 else 50
        profile.fit_rationale = rationale
        profile.gaps = gaps

        results.append({
            "class": profile.class_id,
            "name": profile.name,
            "fit_percent": round(profile.fit_score, 0),
            "mass_range_kg": list(profile.mass_range_kg),
            "cost_range_meur": list(profile.cost_range_meur),
            "schedule_range_months": list(profile.schedule_range_months),
            "gsd_range_m": list(profile.gsd_range_m),
            "max_lifetime_years": profile.max_lifetime_years,
            "risk_profile": profile.risk_profile,
            "heritage_examples": profile.heritage_examples,
            "typical_applications": profile.typical_applications,
            "rationale": rationale,
            "gaps": gaps,
        })

    # Sort by fit
    results.sort(key=lambda r: r["fit_percent"], reverse=True)

    # Recommendation
    best = results[0] if results else None
    if best and best["fit_percent"] >= 80:
        recommendation = f"Your objectives best fit a {best['name']} ({best['fit_percent']:.0f}% match). Expected cost: {best['cost_range_meur'][0]}-{best['cost_range_meur'][1]} MEUR, schedule: {best['schedule_range_months'][0]}-{best['schedule_range_months'][1]} months."
    elif best and best["fit_percent"] >= 50:
        recommendation = f"Your objectives partially fit a {best['name']} ({best['fit_percent']:.0f}% match) but with gaps: {'; '.join(best['gaps'][:2])}. Consider relaxing requirements or moving to the next class up."
    else:
        recommendation = "No standard class fully meets your objectives. Consider relaxing requirements or a custom platform."

    return {
        "question": "What class of spacecraft should you build?",
        "inputs": {
            "target_gsd_m": target_gsd_m,
            "target_revisit_days": target_revisit_days,
            "target_lifetime_years": target_lifetime_years,
            "max_budget_meur": max_budget_meur,
            "max_schedule_months": max_schedule_months,
        },
        "classes": results,
        "recommendation": recommendation,
    }
