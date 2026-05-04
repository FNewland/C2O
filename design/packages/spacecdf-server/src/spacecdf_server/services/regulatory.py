"""SpaceCDF — Regulatory Paperwork Generator.

Generates filing templates for:
  - Canadian RSSSA (Remote Sensing Space Systems Act) licence application
  - Export control assessment (ITAR/EAR/CGP classification)
  - COPUOS/UN Registration Convention (Article IV)
  - End-of-life analysis report
  - Launch provider ICD template

References:
  - RSSSA (S.C. 2005, c. 45) and Regulations (SOR-2007-66)
  - ITAR 22 CFR 120-130, USML Category XV
  - EAR 15 CFR 730-774, ECCN 9A515
  - Canadian Controlled Goods List, Item 5504
  - UN Registration Convention (1975), Article IV
  - ECSS-U-AS-10C Rev.2 (debris mitigation)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def generate_rsssa_template(
    *,
    study_name: str = "",
    operator_name: str = "",
    satellite_description: str = "",
    orbit_altitude_km: float = 500,
    orbit_inclination_deg: float = 97.4,
    has_imaging: bool = True,
    gsd_m: float = 10.0,
    mission_lifetime_years: float = 3.0,
) -> dict[str, Any]:
    """Generate Canadian RSSSA licence application template.

    Required for any Canadian-operated remote sensing satellite.
    Administered by Global Affairs Canada.
    """
    return {
        "document": "RSSSA Operating Licence Application",
        "standard": "Remote Sensing Space Systems Act (S.C. 2005, c. 45)",
        "administering_body": "Global Affairs Canada",
        "contact": "RSSSA-LSTS@international.gc.ca",
        "generated": datetime.now(timezone.utc).isoformat(),
        "applicability": "Required" if has_imaging else "Likely not required (no remote sensing payload)",
        "sections": {
            "applicant_information": {
                "legal_name": operator_name or "TBD",
                "address": "TBD",
                "contact_person": "TBD",
                "canadian_entity": "TBD — must be Canadian or operating in Canada",
            },
            "system_description": {
                "satellite_name": study_name,
                "description": satellite_description or f"CubeSat remote sensing mission at {orbit_altitude_km} km {orbit_inclination_deg:.1f}°",
                "orbit_altitude_km": orbit_altitude_km,
                "orbit_inclination_deg": orbit_inclination_deg,
                "number_of_satellites": 1,
                "design_lifetime_years": mission_lifetime_years,
                "launch_date": "TBD",
                "launch_provider": "TBD",
            },
            "sensor_capabilities": {
                "sensor_type": "Optical imager" if has_imaging else "N/A",
                "ground_resolution_m": gsd_m if has_imaging else None,
                "spectral_bands": "TBD",
                "swath_width_km": "TBD",
                "imaging_modes": "TBD",
                "revisit_time_days": "TBD",
            },
            "data_handling": {
                "data_access_control": "TBD — describe access control measures",
                "cryptography": "TBD — describe encryption for data protection",
                "data_distribution_policy": "TBD — who receives data and under what terms",
                "shutter_control": "TBD — ability to restrict imaging of specific areas",
                "data_retention_policy": "TBD",
            },
            "disposal_plan": {
                "deorbit_method": "TBD — natural decay / propulsive / drag augmentation",
                "post_mission_lifetime_years": "TBD",
                "passivation_plan": "TBD — battery discharge, RF shutdown, momentum dump",
                "performance_guarantee": "TBD — financial or technical guarantee for disposal",
            },
            "national_security": {
                "assessment": "TBD — explain how system addresses national security considerations",
                "international_obligations": "TBD — treaty compliance (OST, Registration Convention)",
            },
        },
        "notes": [
            "RSSSA licence is SEPARATE from ISED spectrum licence — both are required",
            "Submit application to Global Affairs Canada: RSSSA-LSTS@international.gc.ca",
            "The Minister cannot grant a licence without a satisfactory disposal plan",
            "Processing time: variable, allow 6+ months",
        ],
    }


def generate_export_assessment(
    *,
    study_name: str = "",
    country_of_origin: str = "Canada",
    launch_country: str = "USA",
    components_origin: list[dict[str, str]] | None = None,
    has_encryption: bool = False,
    gsd_m: float = 10.0,
    has_propulsion: bool = False,
) -> dict[str, Any]:
    """Generate export control classification assessment.

    Helps determine which export regulations apply and what permits are needed.
    """
    comps = components_origin or []

    # Determine likely classification
    classifications = []
    if any(c.get("origin") == "USA" for c in comps):
        if gsd_m < 0.5:
            classifications.append({
                "regime": "ITAR",
                "category": "USML Category XV",
                "reason": f"Sub-metre GSD ({gsd_m}m) may fall under USML Category XV",
                "action": "Consult DDTC for classification. State Department licence likely required.",
            })
        else:
            classifications.append({
                "regime": "EAR",
                "eccn": "9A515.x",
                "reason": "Spacecraft with US-origin components",
                "action": "BIS classification request recommended. License Exception CSA may apply for Wassenaar countries.",
            })

    if country_of_origin == "Canada":
        classifications.append({
            "regime": "Canadian CGP",
            "category": "Item 5504",
            "reason": "Satellite systems are controlled goods under Canadian regulations",
            "action": "Register with Controlled Goods Directorate if handling US-origin controlled components.",
        })

    if launch_country == "USA":
        classifications.append({
            "regime": "EAR (launch)",
            "reason": "Any satellite launching from US soil must comply with EAR regardless of nationality",
            "action": "Ensure all satellite components are classified before integration at US launch site.",
        })

    return {
        "document": "Export Control Classification Assessment",
        "study_name": study_name,
        "generated": datetime.now(timezone.utc).isoformat(),
        "country_of_origin": country_of_origin,
        "launch_country": launch_country,
        "classifications": classifications,
        "components_assessed": comps,
        "encryption_note": "Encryption of data may trigger additional controls under Wassenaar Arrangement Category 5 Part 2" if has_encryption else "No encryption — no Category 5 concern",
        "recommendations": [
            "Classify all components BEFORE procurement (request vendor ECCN/USML classification)",
            "Apply for necessary export licences at least 6 months before hardware delivery",
            "Maintain records of all component classifications for audit purposes",
            "Consult with export control counsel if any component origin is uncertain",
        ],
    }


def generate_copuos_registration(
    *,
    study_name: str = "",
    launching_state: str = "Canada",
    launch_date: str = "TBD",
    launch_site: str = "TBD",
    orbit_altitude_km: float = 500,
    orbit_inclination_deg: float = 97.4,
    orbit_period_min: float = 94.6,
    general_function: str = "",
) -> dict[str, Any]:
    """Generate UN Registration Convention Article IV filing template."""
    import math
    if orbit_period_min == 0:
        a_m = (6371 + orbit_altitude_km) * 1000
        orbit_period_min = 2 * math.pi * math.sqrt(a_m**3 / 3.986004418e14) / 60

    return {
        "document": "UN Space Object Registration (Registration Convention Article IV)",
        "standard": "Convention on Registration of Objects Launched into Outer Space (1975)",
        "generated": datetime.now(timezone.utc).isoformat(),
        "filing_to": "UN Secretary-General, via national registrar",
        "fields": {
            "a_launching_states": [launching_state],
            "b_designator": f"{study_name} (registration number TBD)",
            "c_launch_date_utc": launch_date,
            "c_launch_territory": launch_site,
            "d_orbital_parameters": {
                "nodal_period_min": round(orbit_period_min, 1),
                "inclination_deg": orbit_inclination_deg,
                "apogee_km": orbit_altitude_km,
                "perigee_km": orbit_altitude_km,
            },
            "e_general_function": general_function or f"Earth observation / technology demonstration CubeSat mission",
        },
        "additional_recommended": {
            "web_link": "TBD — URL with additional mission information",
            "operator": "TBD",
            "expected_lifetime_years": "TBD",
        },
        "notes": [
            "Filing through national registrar (Canada: Global Affairs Canada)",
            "File 'as soon as practicable' after launch",
            "Update registration if orbital parameters change significantly",
        ],
    }


def generate_eol_report(
    *,
    study_name: str = "",
    orbit_altitude_km: float = 500,
    dry_mass_kg: float = 5.0,
    has_propulsion: bool = False,
    lifetime_years: float = 10.0,
    mission_duration_years: float = 3.0,
    passivation_items: list[str] | None = None,
    casualty_risk: float = 0.0,
    compliant_25yr: bool = True,
    compliant_5yr: bool = False,
) -> dict[str, Any]:
    """Generate end-of-life analysis report for regulatory filing."""
    return {
        "document": "End-of-Life Analysis Report",
        "standard": "ECSS-U-AS-10C Rev.2 / NASA-STD-8719.14 / IADC Guidelines",
        "study_name": study_name,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": {
            "orbital_lifetime": {
                "initial_altitude_km": orbit_altitude_km,
                "predicted_lifetime_years": lifetime_years,
                "post_mission_lifetime_years": max(0, lifetime_years - mission_duration_years),
                "compliant_25yr_rule": compliant_25yr,
                "compliant_5yr_rule": compliant_5yr,
                "fcc_5yr_applicable": "Yes — FCC rule effective September 2024",
            },
            "deorbit_plan": {
                "method": "propulsive" if has_propulsion else ("natural" if compliant_25yr else "drag augmentation required"),
                "propulsion_available": has_propulsion,
                "delta_v_for_deorbit_ms": "TBD" if has_propulsion else "N/A",
                "backup_plan": "Drag augmentation device" if not has_propulsion and not compliant_25yr else "N/A",
            },
            "passivation": {
                "items": passivation_items or [
                    "Battery discharge to safe level (<50% SoC)",
                    "RF transmitter shutdown",
                    "Reaction wheel spin-down",
                ],
                "passivation_command_capability": "Yes — via ground command",
            },
            "casualty_risk": {
                "estimated_surviving_mass_kg": dry_mass_kg * 0.2,
                "casualty_expectation": casualty_risk,
                "compliant_nasa_limit": casualty_risk < 0.0001,
                "nasa_limit": "1:10,000 (0.0001)",
            },
            "collision_avoidance": {
                "capability": "TBD — GPS-based orbit determination + ground-based conjunction screening",
                "delta_v_budget_per_year_ms": "TBD",
            },
        },
        "regulatory_compliance": {
            "IADC_guidelines": compliant_25yr,
            "FCC_5yr_rule": compliant_5yr,
            "ECSS_U_AS_10C": compliant_25yr,
            "NASA_STD_8719_14": casualty_risk < 0.0001,
        },
    }
