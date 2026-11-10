"""SpaceCDF export family: rsssa.

RSSSA (Remote Sensing Space Systems Act) application export (json/docx).
Routes (prefix /api/exports): POST /rsssa/{study_id}

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

@router.post("/rsssa/{study_id}")
async def export_rsssa(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
) -> JSONResponse:
    """Generate RSSSA (Remote Sensing Space Systems Act) filing data."""
    from ...services.branding import get_branding
    from ..elements import _elements

    # Read study for orbit params and requirements
    studies = get_study_store()
    study = studies.get(study_id)
    orbit_params = _read_orbit_params(study) if study else {
        "altitude_km": 500.0, "inclination_deg": 97.4, "orbit_type": "SSO",
        "eccentricity": 0.0, "design_lifetime_years": 3.0,
    }

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    gs_elements = [e for e in elements if e.get("segment") == "ground" and (e.get("performance") or {}).get("latitude")]
    ttc_elements = [e for e in elements if e.get("subsystem_domain") == "ttc"]
    spacecraft = [e for e in elements if e.get("segment") == "space" and e.get("element_type") == "system"]
    payload_elements = [e for e in elements if e.get("subsystem_domain") == "payload"]

    total_mass = sum((e.get("mass_kg") or 0) * e.get("quantity", 1) for e in elements if e.get("segment") == "space")
    form_factor = _form_factor_from_mass(total_mass)

    # Build ground station list for regulatory template
    gs_list = [
        {"name": e["name"], "latitude": e["performance"]["latitude"],
         "longitude": e["performance"]["longitude"],
         "bands": e["performance"].get("bands", [])}
        for e in gs_elements
    ]

    # Extract payload pointing accuracy for GSD estimate
    pointing_accuracy_deg = None
    try:
        pointing_accuracy_deg = study.requirements.payloads[0].pointing_accuracy_deg if study else None
    except Exception:
        pass
    # Also check payload element performance
    if pointing_accuracy_deg is None:
        for p in payload_elements:
            perf = p.get("performance") or {}
            if perf.get("pointing_accuracy_deg"):
                pointing_accuracy_deg = perf["pointing_accuracy_deg"]
                break

    # Call generate_rsssa_template with actual study data
    filing_data: dict = {}
    try:
        from ...services.regulatory import generate_rsssa_template
        filing_data = generate_rsssa_template(
            study_name=study.name if study else "",
            operator_name=get_branding().university,
            orbit_altitude_km=orbit_params["altitude_km"],
            orbit_inclination_deg=orbit_params["inclination_deg"],
            orbit_type=orbit_params["orbit_type"],
            orbit_eccentricity=orbit_params["eccentricity"],
            mass_kg=total_mass or None,
            dimensions=form_factor,
            design_lifetime_years=orbit_params["design_lifetime_years"],
            pointing_accuracy_deg=pointing_accuracy_deg,
            ground_stations=gs_list if gs_list else None,
        )
    except Exception:
        pass

    # Run orbital lifetime estimate
    orbital_lifetime_years: float | None = None
    deorbit_compliant_25yr: bool | None = None
    try:
        from spacecdf_common.physics.debris import estimate_orbital_lifetime, estimate_cubesat_cross_section
        cross_section = estimate_cubesat_cross_section(form_factor) if form_factor != "Custom" else 0.03
        a_over_m = cross_section / max(total_mass, 0.1)
        orbital_lifetime_years = round(estimate_orbital_lifetime(
            altitude_km=orbit_params["altitude_km"],
            area_to_mass_ratio_m2_kg=a_over_m,
        ), 2)
        deorbit_compliant_25yr = orbital_lifetime_years <= 25.0
    except Exception:
        pass

    # Compute GSD estimate if pointing accuracy available
    gsd_estimate_m: float | None = None
    if pointing_accuracy_deg is not None:
        try:
            import math
            # Diffraction-limited GSD ≈ altitude * tan(pointing_accuracy)
            # Simplified: GSD ~ altitude_m * pointing_accuracy_rad
            alt_m = orbit_params["altitude_km"] * 1000
            gsd_estimate_m = round(alt_m * math.radians(pointing_accuracy_deg), 2)
        except Exception:
            pass

    # Compute orbit parameters
    orbit_computed: dict = {}
    try:
        from spacecdf_common.physics.orbit import compute_orbit_params
        op = compute_orbit_params(
            altitude_km=orbit_params["altitude_km"],
            inclination_deg=orbit_params["inclination_deg"],
            eccentricity=orbit_params["eccentricity"],
        )
        orbit_computed = {
            "period_min": round(op.period_min, 2),
            "eclipse_fraction": round(op.eclipse_fraction, 3),
            "orbits_per_day": round(op.orbits_per_day, 1),
        }
    except Exception:
        pass

    b = get_branding()
    data = {
        "document": "RSSSA Licence Application Data",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "applicant": {
            "name": b.university,
            "department": b.department,
            "country": "Canada",
        },
        "orbit": {
            "altitude_km": orbit_params["altitude_km"],
            "inclination_deg": orbit_params["inclination_deg"],
            "orbit_type": orbit_params["orbit_type"],
            "eccentricity": orbit_params["eccentricity"],
            "design_lifetime_years": orbit_params["design_lifetime_years"],
            **orbit_computed,
        },
        "system_description": {
            "spacecraft_count": sum(s.get("quantity", 1) for s in spacecraft),
            "spacecraft": [{"name": s["name"], "quantity": s.get("quantity", 1)} for s in spacecraft],
            "total_mass_kg": round(total_mass, 2),
            "form_factor": form_factor,
        },
        "orbital_lifetime": {
            "orbital_lifetime_years": orbital_lifetime_years,
            "deorbit_compliant_25yr": deorbit_compliant_25yr,
        },
        "gsd_estimate_m": gsd_estimate_m,
        "ground_stations": gs_list,
        "frequency_usage": [
            {"subsystem": e["name"], "bands": (e.get("performance") or {}).get("bands", []),
             "rf_band": (e.get("performance") or {}).get("rf_band")}
            for e in ttc_elements
        ],
        "template_fields": filing_data,
    }

    if fmt.lower() == "docx":
        from ...services.branding import create_branded_docx
        doc = create_branded_docx("RSSSA Licence Application Data", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Applicant Information", level=1)
        doc.add_paragraph(f"Name: {b.university}")
        doc.add_paragraph(f"Department: {b.department}")
        doc.add_paragraph("Country: Canada")

        doc.add_heading("2. Orbital Parameters", level=1)
        doc.add_paragraph(f"Altitude: {orbit_params['altitude_km']} km")
        doc.add_paragraph(f"Inclination: {orbit_params['inclination_deg']} deg")
        doc.add_paragraph(f"Orbit type: {orbit_params['orbit_type']}")
        doc.add_paragraph(f"Eccentricity: {orbit_params['eccentricity']}")
        doc.add_paragraph(f"Design lifetime: {orbit_params['design_lifetime_years']} years")
        if orbit_computed:
            doc.add_paragraph(f"Period: {orbit_computed.get('period_min', 'TBD')} min")
            doc.add_paragraph(f"Eclipse fraction: {orbit_computed.get('eclipse_fraction', 'TBD')}")
            doc.add_paragraph(f"Orbits per day: {orbit_computed.get('orbits_per_day', 'TBD')}")

        doc.add_heading("3. System Description", level=1)
        doc.add_paragraph(f"Spacecraft count: {data['system_description']['spacecraft_count']}")
        doc.add_paragraph(f"Total mass: {round(total_mass, 2)} kg")
        doc.add_paragraph(f"Form factor: {form_factor}")
        if spacecraft:
            t = doc.add_table(rows=1, cols=2, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Spacecraft"
            t.rows[0].cells[1].text = "Qty"
            for s in spacecraft:
                row = t.add_row()
                row.cells[0].text = s["name"]
                row.cells[1].text = str(s.get("quantity", 1))

        doc.add_heading("4. Orbital Lifetime Analysis", level=1)
        if orbital_lifetime_years is not None:
            doc.add_paragraph(f"Estimated orbital lifetime: {orbital_lifetime_years} years")
            doc.add_paragraph(f"25-year deorbit compliant: {'Yes' if deorbit_compliant_25yr else 'No'}")
        else:
            doc.add_paragraph("Orbital lifetime analysis not available (physics module missing).")

        if gsd_estimate_m is not None:
            doc.add_heading("5. Imaging Capability", level=1)
            doc.add_paragraph(f"Estimated GSD: {gsd_estimate_m} m")
            doc.add_paragraph(f"Pointing accuracy: {pointing_accuracy_deg} deg")

        next_section = 6 if gsd_estimate_m is not None else 5
        doc.add_heading(f"{next_section}. Ground Stations", level=1)
        if gs_elements:
            t = doc.add_table(rows=1, cols=4, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Station"
            t.rows[0].cells[1].text = "Latitude"
            t.rows[0].cells[2].text = "Longitude"
            t.rows[0].cells[3].text = "Bands"
            for e in gs_elements:
                row = t.add_row()
                row.cells[0].text = e["name"]
                row.cells[1].text = str(e["performance"]["latitude"])
                row.cells[2].text = str(e["performance"]["longitude"])
                row.cells[3].text = ", ".join(e["performance"].get("bands", []))
        else:
            doc.add_paragraph("No ground stations defined.")

        doc.add_heading(f"{next_section + 1}. Frequency Usage", level=1)
        if ttc_elements:
            t = doc.add_table(rows=1, cols=3, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Subsystem"
            t.rows[0].cells[1].text = "Bands"
            t.rows[0].cells[2].text = "RF Band"
            for e in ttc_elements:
                row = t.add_row()
                row.cells[0].text = e["name"]
                perf = e.get("performance") or {}
                row.cells[1].text = ", ".join(perf.get("bands", []))
                row.cells[2].text = str(perf.get("rf_band") or "TBD")
        else:
            doc.add_paragraph("No TT&C elements defined.")

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="RSSSA_{study_id}.docx"'},
        )

    return JSONResponse(content=data)
