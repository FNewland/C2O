"""SpaceCDF — Export API Router.

Endpoints for generating SMO simulator configs, design review
documents, and flight software architecture from a design study.
"""
from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents import DesignLoopOrchestrator

from .studies import get_study_store

router = APIRouter()


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


@router.post("/smo/{study_id}")
async def export_smo_config(study_id: str) -> JSONResponse:
    """Generate SMO simulator configuration files from a design study."""
    state, requirements, _ = await _run_design_for_study(study_id)

    from spacecdf_agents.exporters.smo.exporter import SMOExporter
    exporter = SMOExporter()
    export = exporter.export(state, requirements)

    return JSONResponse(content={
        "files": {k: v for k, v in export.files.items()},
        "is_valid": export.is_valid,
        "validation_errors": export.validation_errors,
        "validation_warnings": export.validation_warnings,
        "param_count": len(export.param_id_map),
        "file_count": len(export.files),
    })


@router.get("/smo/{study_id}/validate")
async def validate_smo_export(study_id: str) -> dict:
    """Run SMO export validation only (no file generation)."""
    state, requirements, _ = await _run_design_for_study(study_id)

    from spacecdf_agents.exporters.smo.exporter import SMOExporter
    exporter = SMOExporter()
    export = exporter.export(state, requirements)

    return {
        "is_valid": export.is_valid,
        "errors": export.validation_errors,
        "warnings": export.validation_warnings,
    }


@router.post("/docs/{study_id}")
async def export_design_document(
    study_id: str,
    review: str = Query(default="srr", description="Review type: srr, pdr, cdr"),
    fmt: str = Query(default="zip", description="Output format: zip (default) or markdown"),
):
    """Generate a design review document from a design study.

    When ``fmt=zip`` (default) streams a zip archive containing Markdown,
    Word, and Excel artefacts. When ``fmt=markdown``, returns the Markdown
    body as JSON for backwards compatibility.
    """
    state, requirements, result = await _run_design_for_study(study_id)

    from spacecdf_agents.exporters.docs.generator import DocumentGenerator
    generator = DocumentGenerator()
    review_lower = (review or "srr").lower()
    if review_lower not in ("srr", "pdr", "cdr"):
        review_lower = "srr"

    if fmt.lower() == "markdown":
        doc = generator.generate(state, requirements, result, review_type=review_lower)
        return JSONResponse(content={
            "review_type": review_lower,
            "document_markdown": doc,
            "sections": doc.count("\n## "),
        })

    zip_bytes = generator.generate_bundle(
        state, requirements, result,
        review_type=review_lower,
        study_name=study_id,
    )
    filename = f"{review_lower}_export.zip"
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/fsw/{study_id}")
async def export_fsw_architecture(study_id: str) -> JSONResponse:
    """Generate flight software architecture scaffolding."""
    state, requirements, _ = await _run_design_for_study(study_id)

    from spacecdf_agents.exporters.fsw.generator import FSWGenerator
    generator = FSWGenerator()
    files = generator.generate(state, requirements)

    return JSONResponse(content={
        "files": files,
        "file_count": len(files),
    })


@router.post("/mbse/{study_id}")
async def export_mbse(study_id: str) -> JSONResponse:
    """Generate an ECSS-E-TM-10-25A-style MBSE JSON export.

    Research-credibility artefact: SysML-like model with blocks, parameters,
    requirements, traceability links, and applicable ECSS standards.
    Suitable for import into Cameo / Capella via a downstream converter and
    for archival in version control (diff-friendly JSON).
    """
    studies = get_study_store()
    study = studies.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")

    state, requirements, _ = await _run_design_for_study(study_id)

    # Auto-generate requirements from the mission baseline when the study
    # hasn't been augmented with explicit ones.
    from spacecdf_common.models.requirements import generate_requirements
    req_objects = generate_requirements(requirements.model_dump())

    # Pull applicable ECSS from the originating template when present
    applicable_ecss: list[str] = []
    notes = getattr(study, "notes", "") or ""
    if "Seeded from template:" in notes:
        tmpl_id = notes.split("Seeded from template:")[1].strip().split()[0]
        try:
            from ..services.template_library import get_template
            tmpl = get_template(tmpl_id)
            if tmpl:
                applicable_ecss = list(tmpl.applicable_ecss)
        except Exception:
            pass

    from spacecdf_agents.exporters.mbse import generate_mbse_export

    phase = study.phase.value if hasattr(study.phase, "value") else str(study.phase)
    export = generate_mbse_export(
        study_id=study.id,
        study_name=study.name,
        phase=phase,
        parameters=state.parameters,
        requirements=req_objects,
        applicable_standards=applicable_ecss,
        notes=notes,
    )
    return JSONResponse(content=export)


# --- Word Document Generation ---

@router.post("/docx/{doc_type}")
async def generate_docx(doc_type: str, study_id: str | None = None):
    """Generate an editable Word (.docx) document.

    Available types: mrd, conops, vp
    Returns a downloadable .docx file.
    """
    from ..services.docx_generator import DOCX_GENERATORS
    from .studies import get_study_store

    if doc_type not in DOCX_GENERATORS:
        raise HTTPException(400, f"Unknown doc type: {doc_type}. Available: {list(DOCX_GENERATORS.keys())}")

    name, gen_fn = DOCX_GENERATORS[doc_type]

    # Get study data if available
    study_name = "Unnamed Mission"
    mission_need = {}
    requirements = []
    conops = {}

    if study_id:
        store = get_study_store()
        study = store.get(study_id)
        if study:
            study_name = study.name
            if hasattr(study, 'mission_need') and study.mission_need:
                mn = study.mission_need
                mission_need = {
                    "problem_statement": getattr(mn, "problem_statement", ""),
                    "objectives": [{"text": o.text, "priority": o.priority, "measurable_criterion": getattr(o, "measurable_criterion", "")} for o in getattr(mn, "objectives", [])],
                    "stakeholders": [{"name": s.name, "role": getattr(s, "role", ""), "needs": getattr(s, "needs", [])} for s in getattr(mn, "stakeholders", [])],
                }

    # Generate the document
    kwargs = {"study_name": study_name}
    if doc_type in ("mrd",):
        kwargs["mission_need"] = mission_need
        kwargs["requirements"] = requirements
    elif doc_type in ("conops",):
        kwargs["mission_need"] = mission_need
        kwargs["conops"] = conops
    elif doc_type in ("vp",):
        kwargs["requirements"] = requirements

    docx_bytes = gen_fn(**kwargs)

    filename = f"SpaceCDF_{name.replace(' ', '_')}_{study_name.replace(' ', '_')}.docx"
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── New branded export endpoints ───

@router.post("/launch-icd/{study_id}")
async def export_launch_icd(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
) -> JSONResponse:
    """Generate Launch Interface Control Document data."""
    from ..services.branding import get_branding
    from .elements import _elements

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    spacecraft = [e for e in elements if e.get("segment") == "space" and e.get("element_type") in ("system", "segment")]
    components = [e for e in elements if e.get("element_type") == "component"]

    total_mass = sum((e.get("mass_kg") or 0) * (e.get("quantity", 1)) for e in elements if e.get("segment") == "space")
    comp_mass = round(sum((c.get("mass_kg") or 0) * c.get("quantity", 1) for c in components), 2)

    b = get_branding()
    data = {
        "document": "Launch Interface Control Document",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "spacecraft": {
            "total_mass_kg": round(total_mass, 2),
            "form_factor": "CubeSat",
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
        "components_summary": {
            "total_components": len(components),
            "total_mass_kg": comp_mass,
        },
    }

    if fmt.lower() == "docx":
        from ..services.branding import create_branded_docx
        doc = create_branded_docx("Launch Interface Control Document", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Spacecraft Description", level=1)
        doc.add_paragraph(f"Total mass: {round(total_mass, 2)} kg")
        doc.add_paragraph(f"Form factor: CubeSat")
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

        doc.add_heading("2. Mechanical Interface", level=1)
        mi = data["mechanical_interface"]
        doc.add_paragraph(f"Deployer type: {mi['deployer_type']}")
        doc.add_paragraph(f"Rail spec: {mi['rail_spec']}")
        doc.add_paragraph(f"Protrusion limit: {mi['protrusion_limit_mm']} mm")
        doc.add_paragraph(f"CG offset limit: {mi['cg_offset_limit_mm']} mm")

        doc.add_heading("3. Electrical Interface", level=1)
        ei = data["electrical_interface"]
        doc.add_paragraph(f"Inhibit switches: {ei['inhibit_switches']}")
        doc.add_paragraph(f"Battery state: {ei['battery_state']}")
        doc.add_paragraph(f"Max voltage: {ei['max_voltage_v']} V")
        doc.add_paragraph(f"Umbilical: {ei['umbilical']}")

        doc.add_heading("4. Environmental Requirements", level=1)
        env = data["environmental"]
        doc.add_paragraph(f"Vibration: {env['vibration']}")
        doc.add_paragraph(f"Shock: {env['shock']}")
        doc.add_paragraph(f"Thermal range: {env['thermal_range_c'][0]} to {env['thermal_range_c'][1]} C")
        doc.add_paragraph(f"Depressurization rate: {env['depressurization_rate']}")

        doc.add_heading("5. Components Summary", level=1)
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


@router.post("/rsssa/{study_id}")
async def export_rsssa(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
) -> JSONResponse:
    """Generate RSSSA (Remote Sensing Space Systems Act) filing data."""
    from ..services.branding import get_branding
    from .elements import _elements

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    gs_elements = [e for e in elements if e.get("segment") == "ground" and (e.get("performance") or {}).get("latitude")]
    ttc_elements = [e for e in elements if e.get("subsystem_domain") == "ttc"]
    spacecraft = [e for e in elements if e.get("segment") == "space" and e.get("element_type") == "system"]

    # Try to get regulatory data from existing service
    filing_data: dict = {}
    try:
        from ..services.regulatory import generate_rsssa_template
        filing_data = generate_rsssa_template({})
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
        "system_description": {
            "spacecraft_count": sum(s.get("quantity", 1) for s in spacecraft),
            "spacecraft": [{"name": s["name"], "quantity": s.get("quantity", 1)} for s in spacecraft],
        },
        "ground_stations": [
            {"name": e["name"], "latitude": e["performance"]["latitude"], "longitude": e["performance"]["longitude"],
             "bands": e["performance"].get("bands", [])}
            for e in gs_elements
        ],
        "frequency_usage": [
            {"subsystem": e["name"], "bands": (e.get("performance") or {}).get("bands", []),
             "rf_band": (e.get("performance") or {}).get("rf_band")}
            for e in ttc_elements
        ],
        "template_fields": filing_data,
    }

    if fmt.lower() == "docx":
        from ..services.branding import create_branded_docx
        doc = create_branded_docx("RSSSA Licence Application Data", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Applicant Information", level=1)
        doc.add_paragraph(f"Name: {b.university}")
        doc.add_paragraph(f"Department: {b.department}")
        doc.add_paragraph(f"Country: Canada")

        doc.add_heading("2. System Description", level=1)
        doc.add_paragraph(f"Spacecraft count: {data['system_description']['spacecraft_count']}")
        if spacecraft:
            t = doc.add_table(rows=1, cols=2, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Spacecraft"
            t.rows[0].cells[1].text = "Qty"
            for s in spacecraft:
                row = t.add_row()
                row.cells[0].text = s["name"]
                row.cells[1].text = str(s.get("quantity", 1))

        doc.add_heading("3. Ground Stations", level=1)
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

        doc.add_heading("4. Frequency Usage", level=1)
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


@router.post("/deorbit/{study_id}")
async def export_deorbit(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
) -> JSONResponse:
    """Generate deorbit analysis and debris compliance report."""
    from ..services.branding import get_branding
    from .elements import _elements

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    total_mass = sum((e.get("mass_kg") or 0) * e.get("quantity", 1) for e in elements if e.get("segment") == "space")

    # Read actual orbit altitude from study requirements, fall back to 500 km
    altitude_km = 500.0
    studies = get_study_store()
    study = studies.get(study_id)
    if study:
        try:
            altitude_km = study.requirements.orbit.altitude_km or 500.0
        except Exception:
            pass

    # Run deorbit analysis using existing physics
    deorbit_data: dict = {}
    try:
        from spacecdf_common.physics.debris import (
            compute_orbital_lifetime, compute_casualty_risk, check_deorbit_compliance
        )
        lifetime = compute_orbital_lifetime(altitude_km=altitude_km, mass_kg=total_mass or 6, area_m2=0.03)
        casualty = compute_casualty_risk(mass_kg=total_mass or 6)
        compliance = check_deorbit_compliance(altitude_km=altitude_km, mass_kg=total_mass or 6, area_m2=0.03)
        deorbit_data = {
            "orbital_lifetime_years": round(lifetime, 1) if isinstance(lifetime, (int, float)) else None,
            "casualty_risk": round(casualty, 6) if isinstance(casualty, (int, float)) else None,
            "compliant_25yr": compliance if isinstance(compliance, bool) else None,
        }
    except Exception:
        deorbit_data = {"note": "Deorbit physics module not available — manual analysis required"}

    b = get_branding()
    data = {
        "document": "Deorbit Analysis & Debris Compliance Report",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "spacecraft": {
            "total_mass_kg": round(total_mass, 2),
            "altitude_km": altitude_km,
            "assumed_area_m2": 0.03,
        },
        "analysis": deorbit_data,
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
        from ..services.branding import create_branded_docx
        doc = create_branded_docx("Deorbit Analysis & Debris Compliance Report", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Spacecraft Parameters", level=1)
        doc.add_paragraph(f"Total mass: {round(total_mass, 2)} kg")
        doc.add_paragraph(f"Orbit altitude: {altitude_km} km")
        doc.add_paragraph(f"Assumed cross-sectional area: 0.03 m\u00b2")

        doc.add_heading("2. Deorbit Analysis", level=1)
        if "note" in deorbit_data:
            doc.add_paragraph(deorbit_data["note"])
        else:
            t = doc.add_table(rows=1, cols=2, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Parameter"
            t.rows[0].cells[1].text = "Value"
            for key, val in deorbit_data.items():
                row = t.add_row()
                row.cells[0].text = key.replace("_", " ").title()
                row.cells[1].text = str(val)

        doc.add_heading("3. Applicable Standards", level=1)
        for key, std in data["standards"].items():
            doc.add_paragraph(std, style="List Bullet")

        doc.add_heading("4. Mitigation Options", level=1)
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


@router.post("/thermal-report/{study_id}")
async def export_thermal_report(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx"),
) -> JSONResponse:
    """Generate thermal design report data."""
    from ..services.branding import get_branding
    from .elements import _elements

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    power_elements = [e for e in elements if (e.get("power_avg_w") or 0) > 0]

    total_power = sum((e.get("power_avg_w") or 0) * e.get("quantity", 1) for e in power_elements)

    b = get_branding()
    data = {
        "document": "Thermal Design Report",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "thermal_environment": {
            "orbit": "LEO SSO (assumed 500 km)",
            "eclipse_fraction": 0.35,
            "solar_flux_w_m2": 1361,
            "albedo_factor": 0.3,
            "earth_ir_w_m2": 237,
        },
        "power_dissipation": {
            "total_avg_w": round(total_power, 1),
            "elements": [
                {"name": e["name"], "power_avg_w": e.get("power_avg_w", 0), "quantity": e.get("quantity", 1),
                 "domain": e.get("subsystem_domain", "")}
                for e in power_elements
            ],
        },
        "design_notes": [
            "Passive thermal control assumed (surface coatings + MLI)",
            "Heater power allocated for eclipse survival",
            "Radiator area sized from total power dissipation",
        ],
    }

    if fmt.lower() == "docx":
        from ..services.branding import create_branded_docx
        doc = create_branded_docx("Thermal Design Report", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Thermal Environment", level=1)
        te = data["thermal_environment"]
        doc.add_paragraph(f"Orbit: {te['orbit']}")
        doc.add_paragraph(f"Eclipse fraction: {te['eclipse_fraction']}")
        doc.add_paragraph(f"Solar flux: {te['solar_flux_w_m2']} W/m\u00b2")
        doc.add_paragraph(f"Albedo factor: {te['albedo_factor']}")
        doc.add_paragraph(f"Earth IR: {te['earth_ir_w_m2']} W/m\u00b2")

        doc.add_heading("2. Power Dissipation", level=1)
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

        doc.add_heading("3. Design Notes", level=1)
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


@router.post("/test-plan/{study_id}")
async def export_test_plan(
    study_id: str,
    fmt: str = Query(default="json", description="Output format: json, docx, xlsx"),
) -> JSONResponse:
    """Generate AIT/AIV test plan from requirements."""
    from ..services.branding import get_branding
    from ..routers.requirements import _requirements

    reqs = [r for r in _requirements.values() if r.get("study_id") == study_id and r.get("status") != "retired"]
    test_reqs = [r for r in reqs if r.get("verification_method") == "T"]
    analysis_reqs = [r for r in reqs if r.get("verification_method") == "A"]
    inspection_reqs = [r for r in reqs if r.get("verification_method") == "I"]

    test_cases = []
    for i, r in enumerate(test_reqs):
        test_cases.append({
            "test_id": f"TC-{i+1:03d}",
            "requirement_code": r.get("code", r["id"]),
            "requirement_text": r.get("text", ""),
            "level": r.get("level", "system"),
            "test_description": f"Verify: {r.get('text', '')}",
            "pass_criteria": f"Requirement {r.get('code', '')} is satisfied",
            "test_type": "Functional",
            "status": "planned",
        })

    b = get_branding()
    data = {
        "document": "AIT/AIV Test Plan",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "summary": {
            "total_requirements": len(reqs),
            "test_requirements": len(test_reqs),
            "analysis_requirements": len(analysis_reqs),
            "inspection_requirements": len(inspection_reqs),
        },
        "test_cases": test_cases,
        "test_phases": [
            {"phase": "Unit Test", "description": "Individual component functional verification"},
            {"phase": "Integration Test", "description": "Subsystem-level interface and performance verification"},
            {"phase": "System Test", "description": "Full spacecraft functional and environmental testing"},
            {"phase": "Acceptance Test", "description": "Final verification before launch campaign"},
        ],
    }

    if fmt.lower() == "docx":
        from ..services.branding import create_branded_docx
        doc = create_branded_docx("AIT/AIV Test Plan", f"Study {study_id}")
        if doc is None:
            raise HTTPException(status_code=500, detail="python-docx not available")

        doc.add_heading("1. Summary", level=1)
        doc.add_paragraph(f"Total requirements: {len(reqs)}")
        doc.add_paragraph(f"Test (T): {len(test_reqs)}  |  Analysis (A): {len(analysis_reqs)}  |  Inspection (I): {len(inspection_reqs)}")

        doc.add_heading("2. Test Cases", level=1)
        if test_cases:
            t = doc.add_table(rows=1, cols=6, style="Light List Accent 1")
            t.rows[0].cells[0].text = "Test ID"
            t.rows[0].cells[1].text = "Req Code"
            t.rows[0].cells[2].text = "Level"
            t.rows[0].cells[3].text = "Description"
            t.rows[0].cells[4].text = "Pass Criteria"
            t.rows[0].cells[5].text = "Status"
            for tc in test_cases:
                row = t.add_row()
                row.cells[0].text = tc["test_id"]
                row.cells[1].text = tc["requirement_code"]
                row.cells[2].text = tc["level"]
                row.cells[3].text = tc["test_description"]
                row.cells[4].text = tc["pass_criteria"]
                row.cells[5].text = tc["status"]
        else:
            doc.add_paragraph("No test-verified requirements defined.")

        doc.add_heading("3. Test Phases", level=1)
        for phase in data["test_phases"]:
            doc.add_paragraph(f"{phase['phase']}: {phase['description']}", style="List Bullet")

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="Test_Plan_{study_id}.docx"'},
        )

    if fmt.lower() == "xlsx":
        from ..services.branding import create_branded_xlsx
        wb = create_branded_xlsx(f"AIT/AIV Test Plan — Study {study_id}")
        if wb is None:
            raise HTTPException(status_code=500, detail="openpyxl not available")

        ws = wb.create_sheet("Test Cases")
        headers = ["Test ID", "Req Code", "Req Text", "Level", "Description", "Pass Criteria", "Type", "Status"]
        ws.append(headers)
        from openpyxl.styles import Font as XlFont
        for cell in ws[1]:
            cell.font = XlFont(bold=True)
        for tc in test_cases:
            ws.append([
                tc["test_id"], tc["requirement_code"], tc["requirement_text"],
                tc["level"], tc["test_description"], tc["pass_criteria"],
                tc["test_type"], tc["status"],
            ])
        # Auto-size columns (approximate)
        for col in ws.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

        ws2 = wb.create_sheet("Summary")
        ws2.append(["Metric", "Count"])
        ws2.append(["Total requirements", len(reqs)])
        ws2.append(["Test (T)", len(test_reqs)])
        ws2.append(["Analysis (A)", len(analysis_reqs)])
        ws2.append(["Inspection (I)", len(inspection_reqs)])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="Test_Plan_{study_id}.xlsx"'},
        )

    return JSONResponse(content=data)
