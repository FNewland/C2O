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
async def export_launch_icd(study_id: str) -> JSONResponse:
    """Generate Launch Interface Control Document data."""
    from ..services.branding import get_branding
    from .elements import _elements

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    spacecraft = [e for e in elements if e.get("segment") == "space" and e.get("element_type") in ("system", "segment")]
    components = [e for e in elements if e.get("element_type") == "component"]

    total_mass = sum((e.get("mass_kg") or 0) * (e.get("quantity", 1)) for e in elements if e.get("segment") == "space")

    b = get_branding()
    return JSONResponse(content={
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
            "total_mass_kg": round(sum((c.get("mass_kg") or 0) * c.get("quantity", 1) for c in components), 2),
        },
    })


@router.post("/rsssa/{study_id}")
async def export_rsssa(study_id: str) -> JSONResponse:
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
    return JSONResponse(content={
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
    })


@router.post("/deorbit/{study_id}")
async def export_deorbit(study_id: str) -> JSONResponse:
    """Generate deorbit analysis and debris compliance report."""
    from ..services.branding import get_branding
    from .elements import _elements

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    total_mass = sum((e.get("mass_kg") or 0) * e.get("quantity", 1) for e in elements if e.get("segment") == "space")

    # Run deorbit analysis using existing physics
    deorbit_data: dict = {}
    try:
        from spacecdf_common.physics.debris import (
            compute_orbital_lifetime, compute_casualty_risk, check_deorbit_compliance
        )
        lifetime = compute_orbital_lifetime(altitude_km=500, mass_kg=total_mass or 6, area_m2=0.03)
        casualty = compute_casualty_risk(mass_kg=total_mass or 6)
        compliance = check_deorbit_compliance(altitude_km=500, mass_kg=total_mass or 6, area_m2=0.03)
        deorbit_data = {
            "orbital_lifetime_years": round(lifetime, 1) if isinstance(lifetime, (int, float)) else None,
            "casualty_risk": round(casualty, 6) if isinstance(casualty, (int, float)) else None,
            "compliant_25yr": compliance if isinstance(compliance, bool) else None,
        }
    except Exception:
        deorbit_data = {"note": "Deorbit physics module not available — manual analysis required"}

    b = get_branding()
    return JSONResponse(content={
        "document": "Deorbit Analysis & Debris Compliance Report",
        "branding": {"university": b.university, "department": b.department, "classification": b.classification},
        "study_id": study_id,
        "spacecraft": {
            "total_mass_kg": round(total_mass, 2),
            "assumed_altitude_km": 500,
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
    })


@router.post("/thermal-report/{study_id}")
async def export_thermal_report(study_id: str) -> JSONResponse:
    """Generate thermal design report data."""
    from ..services.branding import get_branding
    from .elements import _elements

    elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    power_elements = [e for e in elements if (e.get("power_avg_w") or 0) > 0]

    total_power = sum((e.get("power_avg_w") or 0) * e.get("quantity", 1) for e in power_elements)

    b = get_branding()
    return JSONResponse(content={
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
    })


@router.post("/test-plan/{study_id}")
async def export_test_plan(study_id: str) -> JSONResponse:
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
    return JSONResponse(content={
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
    })
