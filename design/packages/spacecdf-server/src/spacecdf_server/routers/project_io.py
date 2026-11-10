"""Project file Save / Load: the complete study as one JSON document.

    GET  /api/studies/{study_id}/export   → the project document (download)
    POST /api/studies/import              → a NEW study from a project document
                                            (?include_id_map=1 adds old → new ids)

The format, what is covered and how ids are remapped: ``services/project_file.py``.
The person's logbook entries for the study travel with the file (their own logbook only).
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query, Request, Response

from ..services import project_file as pf

router = APIRouter()


def _person(request: Request):
    from ..logbook.router import identify
    return identify(request)


@router.get("/studies/{study_id}/export")
async def export_project(study_id: str, request: Request) -> Response:
    ident = _person(request)
    try:
        doc = await pf.export_study(study_id, person_id=None if ident.new_cookie else ident.person_id)
    except pf.ProjectFileError as e:
        raise HTTPException(e.status, e.message) from e
    body = json.dumps(doc, ensure_ascii=False, separators=(",", ":"), default=str)
    name = pf.file_name(doc["study"].get("name"))
    return Response(body, media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.post("/studies/import")
async def import_project(request: Request, response: Response,
                         include_id_map: bool = Query(False)) -> dict:
    try:
        doc = json.loads(await request.body())
    except (ValueError, UnicodeDecodeError) as e:
        raise HTTPException(400, "The file is not valid JSON.") from e
    from ..logbook.router import _set_cookie
    ident = _person(request)
    try:
        result = await pf.import_study(doc, person_id=ident.person_id, include_id_map=include_id_map)
    except pf.ProjectFileError as e:
        raise HTTPException(e.status, e.message) from e
    if result.get("counts", {}).get("logbook"):
        _set_cookie(request, response, ident)
    return result
