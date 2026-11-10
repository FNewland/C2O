"""Shared helpers of the export routers (W0.1).

``_run_design_for_study`` runs the parametric design loop (packs, FSW and MBSE use it; patch
it HERE in tests: every family calls it through ``_common``). ``_read_orbit_params`` and
``_form_factor_from_mass`` are the legacy helpers kept for unchanged behaviour; new code takes
mass, power and form factor from ``services.rollup`` instead.
"""
from __future__ import annotations

from fastapi import HTTPException

from spacecdf_agents import DesignLoopOrchestrator

from ..studies import get_study_store


async def _run_design_for_study(study_id: str) -> tuple:
    """Run design loop for a study and return (state, requirements, result)."""
    studies = get_study_store()
    study = studies.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")

    orchestrator = DesignLoopOrchestrator()
    orchestrator.initialise_agents()
    result = await orchestrator.run(study.requirements)

    if not result.final_state:
        raise HTTPException(status_code=500, detail="Design loop produced no final state")

    return result.final_state, study.requirements, result


# ─── Helper: derive CubeSat form factor from total mass ───

def _form_factor_from_mass(mass_kg: float) -> str:
    """Return CubeSat form factor string from total spacecraft mass."""
    if mass_kg < 2:
        return "1U"
    elif mass_kg < 4:
        return "2U"
    elif mass_kg < 6:
        return "3U"
    elif mass_kg < 12:
        return "6U"
    elif mass_kg < 24:
        return "12U"
    else:
        return "Custom"


# ─── Helper: read study orbit parameters ───

def _read_orbit_params(study) -> dict:
    """Extract orbit parameters from a study object, with safe defaults."""
    altitude_km = 500.0
    inclination_deg = 97.4
    orbit_type = "SSO"
    eccentricity = 0.0
    design_lifetime_years = 3.0
    try:
        orb = study.requirements.orbit
        altitude_km = orb.altitude_km or 500.0
        inclination_deg = orb.inclination_deg or 97.4
        orbit_type = orb.orbit_type.value if hasattr(orb.orbit_type, "value") else str(orb.orbit_type)
        eccentricity = orb.eccentricity or 0.0
    except Exception:
        pass
    try:
        design_lifetime_years = study.requirements.design_lifetime_years or 3.0
    except Exception:
        pass
    return {
        "altitude_km": altitude_km,
        "inclination_deg": inclination_deg,
        "orbit_type": orbit_type,
        "eccentricity": eccentricity,
        "design_lifetime_years": design_lifetime_years,
    }
