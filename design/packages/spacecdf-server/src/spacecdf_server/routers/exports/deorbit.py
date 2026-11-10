"""SpaceCDF export family: deorbit.

Deorbit / end-of-life compliance report (json/docx).
Routes (prefix /api/exports): POST /deorbit/{study_id}

Moved verbatim from the single routers/exports.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from ..studies import get_study_store
from ._common import _form_factor_from_mass, _read_orbit_params

router = APIRouter()

@router.post("/deorbit/{study_id}")
async def export_deorbit(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
) -> JSONResponse:
    """Generate deorbit analysis and debris compliance report."""
    from ...services.branding import get_branding
    from ..elements import _elements

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    # Mass and form factor from the one roll-up (services/rollup.py, W0.3): leaf units x quantity,
    # subsystem estimates and product-tree nodes not double-counted (EG D6).
    from ...services.rollup import compute as _rollup
    ru = await _rollup(study_id)
    total_mass = ru.mass.cbe_kg

    # Read actual orbit altitude from study requirements, fall back to 500 km
    altitude_km = 500.0
    studies = get_study_store()
    study = studies.get(study_id)
    orbit_params = _read_orbit_params(study) if study else {
        "altitude_km": 500.0, "inclination_deg": 97.4, "orbit_type": "SSO",
        "eccentricity": 0.0, "design_lifetime_years": 3.0,
    }
    altitude_km = orbit_params["altitude_km"]

    # Derive form factor and cross-section
    form_factor = ru.form_factor or _form_factor_from_mass(total_mass)
    cross_section_m2 = 0.03  # default
    try:
        from spacecdf_common.physics.debris import estimate_cubesat_cross_section
        if form_factor != "Custom":
            cross_section_m2 = estimate_cubesat_cross_section(form_factor)
    except Exception:
        pass

    a_over_m = cross_section_m2 / max(total_mass, 0.1) if total_mass > 0 else 0.01

    # Run deorbit analysis using existing physics — 3 solar scenarios
    deorbit_data: dict = {}
    lifetime_scenarios: list[dict] = []
    try:
        from spacecdf_common.physics.debris import (
            estimate_orbital_lifetime, compute_casualty_risk, check_deorbit_compliance
        )
        # 3 solar scenarios
        for label, f107 in [("Solar Minimum (F10.7=70)", 70.0),
                            ("Solar Mean (F10.7=120)", 120.0),
                            ("Solar Maximum (F10.7=200)", 200.0)]:
            lt = estimate_orbital_lifetime(
                altitude_km=altitude_km,
                area_to_mass_ratio_m2_kg=a_over_m,
                f107=f107,
            )
            lt_rounded = round(lt, 2) if isinstance(lt, (int, float)) and lt < 1e5 else None
            lifetime_scenarios.append({
                "scenario": label,
                "f107": f107,
                "lifetime_years": lt_rounded,
                "compliant_25yr": lt_rounded <= 25.0 if lt_rounded is not None else None,
                "compliant_5yr": lt_rounded <= 5.0 if lt_rounded is not None else None,
            })

        # Use mean scenario for primary result
        mean_lifetime = lifetime_scenarios[1]["lifetime_years"]
        casualty = compute_casualty_risk(mass_kg=total_mass or 6)
        deorbit_data = {
            "orbital_lifetime_years": mean_lifetime,
            "casualty_risk": round(casualty, 6) if isinstance(casualty, (int, float)) else None,
            "compliant_25yr": mean_lifetime <= 25.0 if mean_lifetime is not None else None,
            "compliant_5yr": mean_lifetime <= 5.0 if mean_lifetime is not None else None,
        }
    except Exception:
        # Fallback: try the older API
        try:
            from spacecdf_common.physics.debris import (
                compute_orbital_lifetime, compute_casualty_risk, check_deorbit_compliance
            )
            lifetime = compute_orbital_lifetime(altitude_km=altitude_km, mass_kg=total_mass or 6, area_m2=cross_section_m2)
            casualty = compute_casualty_risk(mass_kg=total_mass or 6)
            compliance = check_deorbit_compliance(altitude_km=altitude_km, mass_kg=total_mass or 6, area_m2=cross_section_m2)
            deorbit_data = {
                "orbital_lifetime_years": round(lifetime, 1) if isinstance(lifetime, (int, float)) else None,
                "casualty_risk": round(casualty, 6) if isinstance(casualty, (int, float)) else None,
                "compliant_25yr": compliance if isinstance(compliance, bool) else None,
            }
        except Exception:
            deorbit_data = {"note": "Deorbit physics module not available — manual analysis required"}

    # Build passivation checklist from element types
    passivation_checklist = []
    has_battery = any(
        e.get("subsystem_domain") in ("eps", "power") or
        "battery" in (e.get("name") or "").lower()
        for e in elements if e.get("segment") == "space"
    )
    has_propulsion = any(
        e.get("subsystem_domain") == "propulsion" or
        "thruster" in (e.get("name") or "").lower() or
        "propulsion" in (e.get("name") or "").lower()
        for e in elements if e.get("segment") == "space"
    )
    has_ttc = any(
        e.get("subsystem_domain") == "ttc" or
        "transmitter" in (e.get("name") or "").lower() or
        "radio" in (e.get("name") or "").lower()
        for e in elements if e.get("segment") == "space"
    )
    has_momentum_wheels = any(
        e.get("subsystem_domain") == "aocs" or
        "wheel" in (e.get("name") or "").lower() or
        "magnetorquer" in (e.get("name") or "").lower()
        for e in elements if e.get("segment") == "space"
    )

    if has_battery:
        passivation_checklist.append({
            "item": "Discharge batteries",
            "description": "Discharge batteries to safe level (< 50% SoC) to prevent rupture",
            "standard": "ISO 24113 Cl. 6.2.3.1",
        })
    if has_propulsion:
        passivation_checklist.append({
            "item": "Vent propellant",
            "description": "Deplete or vent remaining propellant and pressurant",
            "standard": "ISO 24113 Cl. 6.2.3.2",
        })
    if has_ttc:
        passivation_checklist.append({
            "item": "Disable transmitter",
            "description": "Permanently disable RF transmitter to free frequency allocation",
            "standard": "ITU Radio Regulations Art. 22",
        })
    if has_momentum_wheels:
        passivation_checklist.append({
            "item": "Spin down momentum wheels",
            "description": "De-spin reaction/momentum wheels to prevent debris generation",
            "standard": "ISO 24113 Cl. 6.2.3.3",
        })
    # Always include solar array isolation
    passivation_checklist.append({
        "item": "Isolate solar arrays",
        "description": "Open solar array circuit to prevent battery charging",
        "standard": "ISO 24113 Cl. 6.2.3.1",
    })

    # Compliance summary
    compliance_summary = {
        "iadc_25yr": deorbit_data.get("compliant_25yr"),
        "fcc_5yr": deorbit_data.get("compliant_5yr"),
        "casualty_risk_compliant": (
            deorbit_data.get("casualty_risk", 1.0) < 0.0001
            if isinstance(deorbit_data.get("casualty_risk"), (int, float)) else None
        ),
        "passivation_items_count": len(passivation_checklist),
    }

    b = get_branding()
    data = {
        "document": "Deorbit Analysis & Debris Compliance Report",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "spacecraft": {
            "total_mass_kg": round(total_mass, 2),
            "altitude_km": altitude_km,
            "form_factor": form_factor,
            "cross_section_m2": round(cross_section_m2, 4),
        },
        "analysis": deorbit_data,
        "lifetime_scenarios": lifetime_scenarios,
        "passivation_checklist": passivation_checklist,
        "compliance_summary": compliance_summary,
        "standards": {
            "iso_24113": "ISO 24113:2023 — Space debris mitigation requirements",
            "ecss_u_as_10c": "ECSS-U-AS-10C Rev.2 — Space sustainability",
            "fcc_5yr": "FCC 2024+ 5-year deorbit rule",
            "iadc_25yr": "IADC 25-year guideline",
        },
        "mitigation_options": [
            {"method": "Natural decay", "description": "Rely on atmospheric drag at current altitude"},
            {"method": "Propulsive deorbit", "description": "Use onboard thruster for controlled reentry"},
            {"method": "Drag sail", "description": "Deploy drag augmentation device at end-of-life"},
            {"method": "Electrodynamic tether", "description": "Lorentz force deorbiting"},
        ],
    }

    if fmt.lower() == "docx":
        from ...services.branding import create_branded_docx
        doc = create_branded_docx("Deorbit Analysis & Debris Compliance Report", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Spacecraft Parameters", level=1)
        doc.add_paragraph(f"Total mass: {round(total_mass, 2)} kg")
        doc.add_paragraph(f"Orbit altitude: {altitude_km} km")
        doc.add_paragraph(f"Form factor: {form_factor}")
        doc.add_paragraph(f"Cross-sectional area: {round(cross_section_m2, 4)} m\u00b2")

        doc.add_heading("2. Lifetime Analysis — 3 Solar Scenarios", level=1)
        if lifetime_scenarios:
            t = doc.add_table(rows=1, cols=4, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Scenario"
            t.rows[0].cells[1].text = "F10.7"
            t.rows[0].cells[2].text = "Lifetime (yr)"
            t.rows[0].cells[3].text = "25-yr Compliant"
            for sc in lifetime_scenarios:
                row = t.add_row()
                row.cells[0].text = sc["scenario"]
                row.cells[1].text = str(sc["f107"])
                row.cells[2].text = str(sc["lifetime_years"]) if sc["lifetime_years"] is not None else "> 100,000"
                row.cells[3].text = "Yes" if sc.get("compliant_25yr") else "No" if sc.get("compliant_25yr") is False else "N/A"
        elif "note" in deorbit_data:
            doc.add_paragraph(deorbit_data["note"])
        else:
            t = doc.add_table(rows=1, cols=2, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Parameter"
            t.rows[0].cells[1].text = "Value"
            for key, val in deorbit_data.items():
                row = t.add_row()
                row.cells[0].text = key.replace("_", " ").title()
                row.cells[1].text = str(val)

        doc.add_heading("3. Passivation Checklist", level=1)
        if passivation_checklist:
            t = doc.add_table(rows=1, cols=3, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Action"
            t.rows[0].cells[1].text = "Description"
            t.rows[0].cells[2].text = "Standard"
            for item in passivation_checklist:
                row = t.add_row()
                row.cells[0].text = item["item"]
                row.cells[1].text = item["description"]
                row.cells[2].text = item["standard"]
        else:
            doc.add_paragraph("No passivation items identified.")

        doc.add_heading("4. Compliance Summary", level=1)
        t = doc.add_table(rows=1, cols=2, style="Light List Accent 1")
        t.rows[0].cells[0].text = "Requirement"
        t.rows[0].cells[1].text = "Status"
        for label, key in [("IADC 25-year guideline", "iadc_25yr"),
                           ("FCC 5-year rule", "fcc_5yr"),
                           ("Casualty risk < 1:10000", "casualty_risk_compliant")]:
            row = t.add_row()
            row.cells[0].text = label
            val = compliance_summary.get(key)
            row.cells[1].text = "PASS" if val else "FAIL" if val is False else "N/A"

        doc.add_heading("5. Applicable Standards", level=1)
        for key, std in data["standards"].items():
            doc.add_paragraph(std, style="List Bullet")

        doc.add_heading("6. Mitigation Options", level=1)
        t = doc.add_table(rows=1, cols=2, style="Light List Accent 1")
        t.rows[0].cells[0].text = "Method"
        t.rows[0].cells[1].text = "Description"
        for opt in data["mitigation_options"]:
            row = t.add_row()
            row.cells[0].text = opt["method"]
            row.cells[1].text = opt["description"]

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="Deorbit_Report_{study_id}.docx"'},
        )

    return JSONResponse(content=data)
