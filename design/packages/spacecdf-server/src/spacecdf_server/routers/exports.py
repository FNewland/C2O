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
