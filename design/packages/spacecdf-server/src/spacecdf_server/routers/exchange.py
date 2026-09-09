"""Model-exchange router (SCDF-160 §3, Phase 2d) — mounted under ``/api``.

Exports (GET, download-ready)::

    /studies/{id}/export/capella.zip        Eclipse Capella project (exporters.capella)
    /studies/{id}/export/capella/summary    counts of a fresh Capella export (preview)
    /studies/{id}/export/ecss-10-25.zip     ECSS-E-TM-10-25 Annex C.3 exchange file
    /studies/{id}/export/requirements.reqif ReqIF 1.2
    /studies/{id}/export/model.sysml        textual SysML v2
    /studies/{id}/export/mbse-legacy.json   the pre-SCDF-160 "10-25-like" JSON

Imports (POST multipart ``file``)::

    /studies/{id}/import/capella            zip -> import_capella_model
    /studies/{id}/import/reqif              .reqif -> import_requirements_reqif

Push::

    /studies/{id}/push/comet                Annex C.2 POST; 501 unless COMET_URL is set

Imports broadcast ``model_imported`` on the study WebSocket.
"""
from __future__ import annotations

import io
import logging
import os
import re
from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response, StreamingResponse

from ._arcadia_events import broadcast_mutation

logger = logging.getLogger(__name__)

router = APIRouter()

MEDIA_ZIP = "application/zip"
MEDIA_REQIF = "application/xml"
MEDIA_SYSML = "text/plain; charset=utf-8"
MEDIA_JSON = "application/json"


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", name or "").strip("_")
    return s or "study"


def _study_name(study_id: str) -> str:
    try:
        from .studies import get_study_store
        s = get_study_store().get(study_id)
        return getattr(s, "name", None) or study_id
    except Exception:
        return study_id


def _require_study(study_id: str) -> None:
    """404 when the id is unknown to the study store *and* has no spine rows."""
    from .studies import get_study_store
    if study_id in get_study_store():
        return
    from .elements import _elements
    from .requirements import _requirements
    if any(e.get("study_id") == study_id for e in _elements.values()) or \
       any(r.get("study_id") == study_id for r in _requirements.values()):
        return
    raise HTTPException(status_code=404, detail=f"Study {study_id} not found")


def _download(data: bytes, filename: str, media_type: str) -> StreamingResponse:
    return StreamingResponse(io.BytesIO(data), media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(len(data)),
    })


def _plain(obj: Any) -> Any:
    return asdict(obj) if is_dataclass(obj) else obj


def _wrap(exc: Exception, what: str) -> HTTPException:
    logger.exception("%s failed", what)
    return HTTPException(status_code=500, detail=f"{what} failed: {exc}")


# ── exports ─────────────────────────────────────────────────────────────

@router.get("/studies/{study_id}/export/capella.zip")
async def export_capella(study_id: str, record_ids: bool = True):
    _require_study(study_id)
    from spacecdf_agents.exporters.capella import export_study_to_capella
    try:
        result = await export_study_to_capella(study_id, record_ids=record_ids)
    except Exception as exc:
        raise _wrap(exc, "Capella export") from exc
    return _download(result.zip_bytes, f"{_slug(_study_name(study_id))}.capella.zip", MEDIA_ZIP)


@router.get("/studies/{study_id}/export/capella/summary")
async def export_capella_summary(study_id: str) -> dict:
    _require_study(study_id)
    from spacecdf_agents.exporters.capella import export_study_to_capella, read_model_summary
    try:
        result = await export_study_to_capella(study_id, record_ids=False)
        summary = read_model_summary(result.zip_bytes)
    except Exception as exc:
        raise _wrap(exc, "Capella summary") from exc
    return {"study_id": study_id, **summary, "files": result.files, "warnings": result.warnings,
            "export_counts": result.counts}


@router.get("/studies/{study_id}/export/ecss-10-25.zip")
async def export_ecss_10_25(study_id: str):
    _require_study(study_id)
    from spacecdf_agents.exporters.ecss_10_25 import export_study_to_10_25
    try:
        data = await export_study_to_10_25(study_id)
    except Exception as exc:
        raise _wrap(exc, "ECSS-E-TM-10-25 export") from exc
    return _download(data, f"{_slug(_study_name(study_id))}.ecss-10-25.zip", MEDIA_ZIP)


@router.get("/studies/{study_id}/export/requirements.reqif")
async def export_reqif(study_id: str):
    _require_study(study_id)
    from spacecdf_agents.exporters.reqif import export_requirements_reqif
    try:
        data = await export_requirements_reqif(study_id)
    except Exception as exc:
        raise _wrap(exc, "ReqIF export") from exc
    return _download(data, f"{_slug(_study_name(study_id))}.reqif", MEDIA_REQIF)


@router.get("/studies/{study_id}/export/model.sysml")
async def export_sysml(study_id: str):
    _require_study(study_id)
    from spacecdf_agents.exporters.sysmlv2 import export_study_sysml
    try:
        text = await export_study_sysml(study_id)
    except Exception as exc:
        raise _wrap(exc, "SysML v2 export") from exc
    return _download(text.encode("utf-8"), f"{_slug(_study_name(study_id))}.sysml", MEDIA_SYSML)


@router.get("/studies/{study_id}/export/mbse-legacy.json")
async def export_mbse_legacy(study_id: str) -> Response:
    """The pre-SCDF-160 ``exporters/mbse/generator.py`` JSON, built from the
    element tree (no design-loop run, unlike ``POST /api/exports/mbse/{id}``)."""
    from .studies import get_study_store
    study = get_study_store().get(study_id)
    if study is None:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    from spacecdf_agents.exporters.mbse import generate_mbse_export
    from ..services.element_projection import project_elements_to_params
    from .elements import _elements
    try:
        elements = [e for e in _elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
        if not elements:
            from ..db.element_repo import load_all_elements
            all_el, _ = await load_all_elements()
            elements = [e for e in all_el.values() if e.get("study_id") == study_id]
        params = project_elements_to_params(elements) if elements else {}
        from spacecdf_common.models.requirements import generate_requirements
        try:
            req_objects = generate_requirements(study.requirements.model_dump())
        except Exception:
            req_objects = []
        phase = study.phase.value if hasattr(study.phase, "value") else str(study.phase)
        export = generate_mbse_export(study_id=study.id, study_name=study.name, phase=phase, parameters=params,
                                      requirements=req_objects, applicable_standards=[],
                                      notes=getattr(study, "notes", "") or "")
    except Exception as exc:
        raise _wrap(exc, "legacy MBSE export") from exc
    return JSONResponse(content=export, headers={
        "Content-Disposition": f'attachment; filename="{_slug(study.name)}.mbse-legacy.json"'})


# ── imports ─────────────────────────────────────────────────────────────

async def _read_upload(file: UploadFile, max_bytes: int = 200 * 1024 * 1024) -> bytes:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file too large")
    return data


@router.post("/studies/{study_id}/import/capella")
async def import_capella(study_id: str, file: UploadFile = File(...)) -> dict:
    _require_study(study_id)
    data = await _read_upload(file)
    from spacecdf_agents.exporters.capella import import_capella_model
    try:
        result = await import_capella_model(study_id, data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Capella import failed: {exc}") from exc
    payload = _plain(result)
    await broadcast_mutation(study_id, "model_imported", "study", study_id,
                             {"format": "capella", "created": result.created, "updated": result.updated})
    return {"format": "capella", "filename": file.filename, **payload}


@router.post("/studies/{study_id}/import/reqif")
async def import_reqif(study_id: str, file: UploadFile = File(...)) -> dict:
    _require_study(study_id)
    data = await _read_upload(file)
    from spacecdf_agents.exporters.reqif import import_requirements_reqif
    try:
        result = await import_requirements_reqif(study_id, data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"ReqIF import failed: {exc}") from exc
    payload = _plain(result)
    await broadcast_mutation(study_id, "model_imported", "study", study_id,
                             {"format": "reqif", "created": result.created, "updated": result.updated,
                              "relations_created": result.relations_created})
    return {"format": "reqif", "filename": file.filename, **payload}


# ── push ────────────────────────────────────────────────────────────────

@router.post("/studies/{study_id}/push/comet")
async def push_comet(study_id: str) -> dict:
    """Push the study to an ECSS-E-TM-10-25 Annex C.2 server (COMET / CDP4).

    Configured by ``COMET_URL`` (+ optional ``COMET_USER``/``COMET_PASSWORD``).
    """
    base_url = os.environ.get("COMET_URL")
    if not base_url:
        raise HTTPException(status_code=501, detail="COMET push not configured (set COMET_URL)")
    _require_study(study_id)
    from spacecdf_agents.exporters.ecss_10_25 import AnnexCClient, push_study
    user, pwd = os.environ.get("COMET_USER"), os.environ.get("COMET_PASSWORD")
    client = AnnexCClient(base_url, (user, pwd) if user else None)
    try:
        return await push_study(study_id, client)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"COMET push failed: {exc}") from exc
    finally:
        await client.aclose()
