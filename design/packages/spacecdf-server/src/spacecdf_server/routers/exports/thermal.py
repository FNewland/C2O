"""SpaceCDF export family: thermal.

Thermal analysis report (json/docx).
Routes (prefix /api/exports): POST /thermal-report/{study_id}

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

@router.post("/thermal-report/{study_id}")
async def export_thermal_report(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
) -> JSONResponse:
    """Generate thermal design report data."""
    from ...services.branding import get_branding
    from ..elements import _elements

    # Read study for orbit params
    studies = get_study_store()
    study = studies.get(study_id)
    orbit_params = _read_orbit_params(study) if study else {
        "altitude_km": 500.0, "inclination_deg": 97.4, "orbit_type": "SSO",
        "eccentricity": 0.0, "design_lifetime_years": 3.0,
    }

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    space_elements = [e for e in elements if e.get("segment") == "space"]
    power_elements = [e for e in elements if (e.get("power_avg_w") or 0) > 0]

    # Mass and form factor from the one roll-up (services/rollup.py, W0.3): leaf units x quantity,
    # subsystem estimates and product-tree nodes not double-counted (EG D6).
    from ...services.rollup import compute as _rollup
    ru = await _rollup(study_id)
    total_power = ru.power.sum_on_power_w
    total_mass = ru.mass.cbe_kg
    form_factor = ru.form_factor or _form_factor_from_mass(total_mass)

    # Compute eclipse fraction from orbit params
    eclipse_fraction = 0.35  # default
    orbit_computed: dict = {}
    try:
        from spacecdf_common.physics.orbit import compute_orbit_params
        op = compute_orbit_params(
            altitude_km=orbit_params["altitude_km"],
            inclination_deg=orbit_params["inclination_deg"],
            eccentricity=orbit_params["eccentricity"],
        )
        eclipse_fraction = op.eclipse_fraction
        orbit_computed = {
            "altitude_km": orbit_params["altitude_km"],
            "inclination_deg": orbit_params["inclination_deg"],
            "orbit_type": orbit_params["orbit_type"],
            "period_min": round(op.period_min, 2),
            "eclipse_fraction": round(op.eclipse_fraction, 3),
            "eclipse_duration_min": round(op.eclipse_duration_min, 2),
            "sunlight_duration_min": round(op.sunlight_duration_min, 2),
        }
    except Exception:
        orbit_computed = {
            "altitude_km": orbit_params["altitude_km"],
            "inclination_deg": orbit_params["inclination_deg"],
            "orbit_type": orbit_params["orbit_type"],
        }

    # Estimate spacecraft surface area
    spacecraft_area_m2 = 1.0
    try:
        from spacecdf_common.physics.thermal import spacecraft_surface_area
        spacecraft_area_m2 = spacecraft_surface_area(total_mass, form_factor="cubesat" if form_factor != "Custom" else "box")
    except Exception:
        pass

    # Run thermal balance computation
    thermal_result: dict = {}
    try:
        from spacecdf_common.physics.thermal import compute_thermal_balance
        # Read temperature limits from study requirements if available
        t_min_c = -20.0
        t_max_c = 50.0
        try:
            temp_range = study.requirements.payloads[0].temperature_range_c
            if temp_range and len(temp_range) >= 2:
                t_min_c = temp_range[0]
                t_max_c = temp_range[1]
        except Exception:
            pass

        tb = compute_thermal_balance(
            internal_power_w=total_power if total_power > 0 else 10.0,
            spacecraft_area_m2=spacecraft_area_m2,
            eclipse_fraction=eclipse_fraction,
            t_min_c=t_min_c,
            t_max_c=t_max_c,
        )
        thermal_result = {
            "hot_case_temp_c": round(tb.hot_case_temp_c, 1),
            "cold_case_temp_c": round(tb.cold_case_temp_c, 1),
            "cold_case_heater_w": round(tb.cold_case_heater_w, 2),
            "radiator_area_m2": round(tb.radiator_area_m2, 4),
            "radiator_mass_kg": round(tb.radiator_mass_kg, 3),
            "mli_area_m2": round(tb.mli_area_m2, 4),
            "mli_mass_kg": round(tb.mli_mass_kg, 3),
            "tcs_mass_kg": round(tb.tcs_mass_kg, 3),
            "tcs_heater_power_w": round(tb.tcs_heater_power_w, 2),
            "warnings": tb.warnings,
        }
    except Exception:
        thermal_result = {"note": "Thermal balance computation not available"}

    # Build component temperature range table
    component_thermal = []
    for e in space_elements:
        if e.get("element_type") == "component":
            comp_entry = {
                "name": e["name"],
                "subsystem": e.get("subsystem_domain", ""),
                "power_avg_w": e.get("power_avg_w", 0),
                "quantity": e.get("quantity", 1),
            }
            # Look for component-level temp limits in performance dict
            perf = e.get("performance") or {}
            if perf.get("temperature_range_c"):
                comp_entry["temp_range_c"] = perf["temperature_range_c"]
            elif perf.get("operating_temp_min_c") is not None:
                comp_entry["temp_range_c"] = [perf["operating_temp_min_c"], perf.get("operating_temp_max_c", 50)]
            else:
                # Use typical ranges by subsystem domain
                domain = e.get("subsystem_domain", "")
                typical_ranges = {
                    "eps": [-20, 50], "payload": [-10, 40], "obc": [-20, 60],
                    "ttc": [-20, 50], "aocs": [-20, 50], "propulsion": [5, 50],
                    "structure": [-40, 80], "thermal": [-40, 80],
                }
                comp_entry["temp_range_c"] = typical_ranges.get(domain, [-20, 50])
            component_thermal.append(comp_entry)

    b = get_branding()
    data = {
        "document": "Thermal Design Report",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "orbit": orbit_computed,
        "thermal_environment": {
            "orbit": f"{orbit_params['orbit_type']} ({orbit_params['altitude_km']} km)",
            "eclipse_fraction": round(eclipse_fraction, 3),
            "solar_flux_w_m2": 1361,
            "albedo_factor": 0.3,
            "earth_ir_w_m2": 237,
            "spacecraft_area_m2": round(spacecraft_area_m2, 4),
        },
        "power_dissipation": {
            "total_avg_w": round(total_power, 1),
            "elements": [
                {"name": e["name"], "power_avg_w": e.get("power_avg_w", 0), "quantity": e.get("quantity", 1),
                 "domain": e.get("subsystem_domain", "")}
                for e in power_elements
            ],
        },
        "thermal_balance": thermal_result,
        "component_thermal_ranges": component_thermal,
        "design_notes": [
            "Passive thermal control assumed (surface coatings + MLI)",
            "Heater power allocated for eclipse survival",
            "Radiator area sized from total power dissipation",
        ],
    }

    if fmt.lower() == "docx":
        from ...services.branding import create_branded_docx
        doc = create_branded_docx("Thermal Design Report", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Orbital Environment", level=1)
        doc.add_paragraph(f"Orbit: {orbit_params['orbit_type']} at {orbit_params['altitude_km']} km")
        doc.add_paragraph(f"Eclipse fraction: {round(eclipse_fraction, 3)}")
        if orbit_computed.get("period_min"):
            doc.add_paragraph(f"Period: {orbit_computed['period_min']} min")
            doc.add_paragraph(f"Eclipse duration: {orbit_computed.get('eclipse_duration_min', 'TBD')} min")
            doc.add_paragraph(f"Sunlight duration: {orbit_computed.get('sunlight_duration_min', 'TBD')} min")

        doc.add_heading("2. Thermal Environment", level=1)
        te = data["thermal_environment"]
        doc.add_paragraph(f"Solar flux: {te['solar_flux_w_m2']} W/m\u00b2")
        doc.add_paragraph(f"Albedo factor: {te['albedo_factor']}")
        doc.add_paragraph(f"Earth IR: {te['earth_ir_w_m2']} W/m\u00b2")
        doc.add_paragraph(f"Spacecraft surface area: {te['spacecraft_area_m2']} m\u00b2")

        doc.add_heading("3. Power Dissipation", level=1)
        doc.add_paragraph(f"Total average power: {round(total_power, 1)} W")
        if power_elements:
            t = doc.add_table(rows=1, cols=4, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Element"
            t.rows[0].cells[1].text = "Power (W)"
            t.rows[0].cells[2].text = "Qty"
            t.rows[0].cells[3].text = "Domain"
            for e in power_elements:
                row = t.add_row()
                row.cells[0].text = e["name"]
                row.cells[1].text = str(e.get("power_avg_w", 0))
                row.cells[2].text = str(e.get("quantity", 1))
                row.cells[3].text = e.get("subsystem_domain", "")

        doc.add_heading("4. Thermal Balance Analysis", level=1)
        if "note" in thermal_result:
            doc.add_paragraph(thermal_result["note"])
        else:
            t = doc.add_table(rows=1, cols=2, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Parameter"
            t.rows[0].cells[1].text = "Value"
            for label, key, unit in [
                ("Hot case temperature", "hot_case_temp_c", "C"),
                ("Cold case temperature", "cold_case_temp_c", "C"),
                ("Eclipse heater power", "cold_case_heater_w", "W"),
                ("Radiator area", "radiator_area_m2", "m\u00b2"),
                ("Radiator mass", "radiator_mass_kg", "kg"),
                ("MLI area", "mli_area_m2", "m\u00b2"),
                ("MLI mass", "mli_mass_kg", "kg"),
                ("TCS total mass", "tcs_mass_kg", "kg"),
                ("TCS heater power", "tcs_heater_power_w", "W"),
            ]:
                if key in thermal_result:
                    row = t.add_row()
                    row.cells[0].text = label
                    row.cells[1].text = f"{thermal_result[key]} {unit}"
            if thermal_result.get("warnings"):
                doc.add_paragraph("")
                for w in thermal_result["warnings"]:
                    doc.add_paragraph(f"WARNING: {w}", style="List Bullet")

        doc.add_heading("5. Component Temperature Ranges", level=1)
        if component_thermal:
            t = doc.add_table(rows=1, cols=5, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Component"
            t.rows[0].cells[1].text = "Subsystem"
            t.rows[0].cells[2].text = "Power (W)"
            t.rows[0].cells[3].text = "T_min (C)"
            t.rows[0].cells[4].text = "T_max (C)"
            for c in component_thermal:
                row = t.add_row()
                row.cells[0].text = c["name"]
                row.cells[1].text = c.get("subsystem", "")
                row.cells[2].text = str(c.get("power_avg_w", 0))
                tr = c.get("temp_range_c", [-20, 50])
                row.cells[3].text = str(tr[0])
                row.cells[4].text = str(tr[1])
        else:
            doc.add_paragraph("No space segment components defined.")

        doc.add_heading("6. Design Notes", level=1)
        for note in data["design_notes"]:
            doc.add_paragraph(note, style="List Bullet")

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="Thermal_Report_{study_id}.docx"'},
        )

    return JSONResponse(content=data)
