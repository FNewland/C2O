"""SpaceCDF export family: smo.

Simulator configuration export (design-to-simulator).
Routes (prefix /api/exports): POST /smo/{study_id}, GET /smo/{study_id}/validate

Moved verbatim from the single routers/exports.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations


from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter()

# ─── Simulator configuration (design-to-simulator export) ───

@router.post("/smo/{study_id}")
async def export_smo_config(study_id: str) -> JSONResponse:
    """Simulator configuration files from the design (Nov 2026: the design-to-simulator export,
    routers/sim_export.py; the hard-coded placeholder exporter is gone). ``files`` maps each
    path of the configuration directory to its YAML text."""
    from ..sim_export import build_export
    ex, report = await build_export(study_id)
    v = report.get("validation") or {}
    return JSONResponse(content={
        "files": ex.render(),
        "readiness": report,
        "is_valid": bool(v.get("available")) and not v.get("errors"),
        "validation_errors": v.get("errors") or [],
        "validation_available": bool(v.get("available")),
        "file_count": len(report.get("files") or []),
    })


@router.get("/smo/{study_id}/validate")
async def validate_smo_export(study_id: str) -> dict:
    """Validate the exported simulator configuration with the simulator's strict loaders."""
    from ..sim_export import build_export
    _, report = await build_export(study_id)
    v = report.get("validation") or {}
    return {"is_valid": bool(v.get("available")) and not v.get("errors"), "errors": v.get("errors") or [],
            "warnings": [] if v.get("available") else ["simulator packages not available: not validated"]}
