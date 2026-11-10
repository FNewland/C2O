"""SpaceCDF export family: rsssa.

RSSSA (Remote Sensing Space Systems Act) application export (json/docx).
Routes (prefix /api/exports): POST /rsssa/{study_id}

Moved from the single routers/exports.py in W0.1. W1.09e (agent L): the GSD comes from the payload
(``gsd_m``, else pixel pitch and focal length), not altitude x pointing accuracy (EG D7); stations
with ``lat``/``lon``; the lifetime from the disposal analysis with the drag sail (W5.02). The full
application (guide sections 1-32) is ``POST /api/exports/regulatory/rsssa/{study_id}``.
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
    from ...services import licensing as _lic
    gs_stations = _lic.stations(elements)
    gs_elements = [{"name": g["name"], "performance": {"latitude": g["lat"], "longitude": g["lon"],
                                                       "bands": g.get("bands") or []}} for g in gs_stations]
    ttc_elements = [e for e in elements if e.get("subsystem_domain") == "ttc"]
    spacecraft = [e for e in elements if e.get("segment") == "space" and e.get("element_type") == "system"]
    payload_elements = [e for e in elements if e.get("subsystem_domain") == "payload"]

    # Mass and form factor from the one roll-up (services/rollup.py, W0.3): leaf units x quantity,
    # subsystem estimates and product-tree nodes not double-counted (EG D6).
    from ...services.rollup import compute as _rollup
    ru = await _rollup(study_id)
    total_mass = ru.mass.cbe_kg
    form_factor = ru.form_factor or _form_factor_from_mass(total_mass)

    # Build ground station list for regulatory template
    gs_list = [
        {"name": e["name"], "latitude": e["performance"]["latitude"],
         "longitude": e["performance"]["longitude"],
         "bands": e["performance"].get("bands", [])}
        for e in gs_elements
    ]

    # Sensor performance from the payload (GSD from gsd_m / optics, EG D7)
    sensor = _lic._payload_info(study, elements, orbit_params["altitude_km"]) if study else {}
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
            gsd_m=sensor.get("gsd_m"),
            fov_deg=sensor.get("fov_deg"),
            ground_stations=gs_list if gs_list else None,
        )
    except Exception:
        pass

    # Orbital lifetime from the disposal analysis (drag sail, solar-cycle scenarios; W5.02)
    orbital_lifetime_years: float | None = None
    deorbit_compliant_25yr: bool | None = None
    disposal: dict = {}
    try:
        record, _ = await _lic.load_record(study_id)
        disposal = _lic.disposal_analysis(study, elements, ru.as_dict(), record) if study else {}
        ws, wo = disposal.get("lifetime_with_sail_y") or {}, disposal.get("lifetime_without_sail_y") or {}
        worst = max(ws.values()) if ws else (max(wo.values()) if wo else None)
        orbital_lifetime_years = worst
        deorbit_compliant_25yr = worst is not None and worst <= 25.0
    except Exception:
        pass

    # GSD: the payload's own figure (never altitude x pointing accuracy)
    gsd_estimate_m: float | None = sensor.get("gsd_m")

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
            "deorbit_compliant_5yr_ised": orbital_lifetime_years is not None and orbital_lifetime_years <= 5.0,
            "with_drag_sail": bool(disposal.get("sail")),
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
            doc.add_paragraph(f"Post-mission lifetime (worst solar scenario"
                              f"{', with the drag sail' if disposal.get('sail') else ''}): {orbital_lifetime_years} years")
            doc.add_paragraph(f"ISED 5-year disposal rule: {'met' if orbital_lifetime_years <= 5.0 else 'not met'}")
        else:
            doc.add_paragraph("Orbital lifetime analysis not available.")

        if gsd_estimate_m is not None:
            doc.add_heading("5. Imaging Capability", level=1)
            doc.add_paragraph(f"Ground sample distance (best, nadir): {gsd_estimate_m} m")
            if sensor.get("swath_km"):
                doc.add_paragraph(f"Swath: {sensor['swath_km']} km")
            if pointing_accuracy_deg is not None:
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
