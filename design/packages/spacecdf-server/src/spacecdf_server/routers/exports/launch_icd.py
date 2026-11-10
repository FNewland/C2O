"""SpaceCDF export family: launch_icd.

Launch Interface Control Document (json/docx).
Routes (prefix /api/exports): POST /launch-icd/{study_id}

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

# ─── New branded export endpoints ───

@router.post("/launch-icd/{study_id}")
async def export_launch_icd(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
) -> JSONResponse:
    """Generate Launch Interface Control Document data."""
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
    spacecraft = [e for e in elements if e.get("segment") == "space" and e.get("element_type") in ("system", "segment")]
    components = [e for e in elements if e.get("element_type") == "component"]

    # Mass and form factor from the one roll-up (services/rollup.py, W0.3): leaf units x quantity,
    # subsystem estimates and product-tree nodes not double-counted (EG D6).
    from ...services.rollup import compute as _rollup
    ru = await _rollup(study_id)
    total_mass = ru.mass.cbe_kg
    comp_mass = round(sum((c.get("mass_kg") or 0) * c.get("quantity", 1) for c in components), 2)
    form_factor = ru.form_factor or _form_factor_from_mass(total_mass)

    # Build component BOM table
    component_bom = []
    for c in components:
        component_bom.append({
            "name": c["name"],
            "subsystem": c.get("subsystem_domain", ""),
            "mass_kg": c.get("mass_kg"),
            "power_avg_w": c.get("power_avg_w"),
            "quantity": c.get("quantity", 1),
        })

    # Compute orbit parameters using physics module
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
            "velocity_ms": round(op.velocity_ms, 1),
            "eclipse_fraction": round(op.eclipse_fraction, 3),
            "orbits_per_day": round(op.orbits_per_day, 1),
            "footprint_radius_km": round(op.footprint_radius_km, 1),
        }
    except Exception:
        pass

    b = get_branding()
    data = {
        "document": "Launch Interface Control Document",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "orbit": {
            "altitude_km": orbit_params["altitude_km"],
            "inclination_deg": orbit_params["inclination_deg"],
            "orbit_type": orbit_params["orbit_type"],
            "eccentricity": orbit_params["eccentricity"],
            **orbit_computed,
        },
        "spacecraft": {
            "total_mass_kg": round(total_mass, 2),
            "form_factor": form_factor,
            "systems": [{"name": s["name"], "mass_kg": s.get("mass_kg"), "quantity": s.get("quantity", 1)} for s in spacecraft],
        },
        "mechanical_interface": {
            "deployer_type": "Standard CubeSat deployer (ISIPOD / EXApod)",
            "rail_spec": "PC/104 compliant rails",
            "protrusion_limit_mm": 6.5,
            "cg_offset_limit_mm": 20,
        },
        "electrical_interface": {
            "inhibit_switches": 3,
            "battery_state": "Charged, RBF pin installed",
            "max_voltage_v": 8.4,
            "umbilical": "None (autonomous activation)",
        },
        "environmental": {
            "vibration": "Qualification: 14.1 grms (20-2000 Hz random)",
            "shock": "1500g SRS at 1000 Hz",
            "thermal_range_c": [-40, 60],
            "depressurization_rate": "< 5 kPa/s",
        },
        "component_bom": component_bom,
        "components_summary": {
            "total_components": len(components),
            "total_mass_kg": comp_mass,
        },
    }

    if fmt.lower() == "docx":
        from ...services.branding import create_branded_docx
        doc = create_branded_docx("Launch Interface Control Document", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Orbit Parameters", level=1)
        doc.add_paragraph(f"Altitude: {orbit_params['altitude_km']} km")
        doc.add_paragraph(f"Inclination: {orbit_params['inclination_deg']} deg")
        doc.add_paragraph(f"Orbit type: {orbit_params['orbit_type']}")
        doc.add_paragraph(f"Eccentricity: {orbit_params['eccentricity']}")
        if orbit_computed:
            doc.add_paragraph(f"Period: {orbit_computed.get('period_min', 'TBD')} min")
            doc.add_paragraph(f"Velocity: {orbit_computed.get('velocity_ms', 'TBD')} m/s")
            doc.add_paragraph(f"Orbits per day: {orbit_computed.get('orbits_per_day', 'TBD')}")

        doc.add_heading("2. Spacecraft Description", level=1)
        doc.add_paragraph(f"Total mass: {round(total_mass, 2)} kg")
        doc.add_paragraph(f"Form factor: {form_factor}")
        if spacecraft:
            t = doc.add_table(rows=1, cols=3, style="Light List Accent 1")
            t.rows[0].cells[0].text = "System"
            t.rows[0].cells[1].text = "Mass (kg)"
            t.rows[0].cells[2].text = "Qty"
            for s in spacecraft:
                row = t.add_row()
                row.cells[0].text = s["name"]
                row.cells[1].text = str(s.get("mass_kg") or "TBD")
                row.cells[2].text = str(s.get("quantity", 1))

        doc.add_heading("3. Component Bill of Materials", level=1)
        if component_bom:
            t = doc.add_table(rows=1, cols=5, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Component"
            t.rows[0].cells[1].text = "Subsystem"
            t.rows[0].cells[2].text = "Mass (kg)"
            t.rows[0].cells[3].text = "Power (W)"
            t.rows[0].cells[4].text = "Qty"
            for c in component_bom:
                row = t.add_row()
                row.cells[0].text = c["name"]
                row.cells[1].text = c.get("subsystem", "")
                row.cells[2].text = str(c.get("mass_kg") or "TBD")
                row.cells[3].text = str(c.get("power_avg_w") or "TBD")
                row.cells[4].text = str(c.get("quantity", 1))
        else:
            doc.add_paragraph("No components defined.")

        doc.add_heading("4. Mechanical Interface", level=1)
        mi = data["mechanical_interface"]
        doc.add_paragraph(f"Deployer type: {mi['deployer_type']}")
        doc.add_paragraph(f"Rail spec: {mi['rail_spec']}")
        doc.add_paragraph(f"Protrusion limit: {mi['protrusion_limit_mm']} mm")
        doc.add_paragraph(f"CG offset limit: {mi['cg_offset_limit_mm']} mm")

        doc.add_heading("5. Electrical Interface", level=1)
        ei = data["electrical_interface"]
        doc.add_paragraph(f"Inhibit switches: {ei['inhibit_switches']}")
        doc.add_paragraph(f"Battery state: {ei['battery_state']}")
        doc.add_paragraph(f"Max voltage: {ei['max_voltage_v']} V")
        doc.add_paragraph(f"Umbilical: {ei['umbilical']}")

        doc.add_heading("6. Environmental Requirements", level=1)
        env = data["environmental"]
        doc.add_paragraph(f"Vibration: {env['vibration']}")
        doc.add_paragraph(f"Shock: {env['shock']}")
        doc.add_paragraph(f"Thermal range: {env['thermal_range_c'][0]} to {env['thermal_range_c'][1]} C")
        doc.add_paragraph(f"Depressurization rate: {env['depressurization_rate']}")

        doc.add_heading("7. Components Summary", level=1)
        doc.add_paragraph(f"Total components: {len(components)}")
        doc.add_paragraph(f"Total component mass: {comp_mass} kg")

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="Launch_ICD_{study_id}.docx"'},
        )

    return JSONResponse(content=data)
