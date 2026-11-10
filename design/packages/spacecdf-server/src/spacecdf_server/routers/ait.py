"""AIT API (W8a): model philosophy, test matrix and the verification plan of a study.

    GET    /api/studies/{sid}/ait                      models, tests, environment levels
    POST   /api/studies/{sid}/ait/propose              default protoflight philosophy and test matrix
    POST   /api/studies/{sid}/ait/models               add a model;  PATCH/DELETE .../models/{id}
    POST   /api/studies/{sid}/ait/tests                add a test;   PATCH/DELETE .../tests/{id}
    GET    /api/studies/{sid}/ait/verification-plan    the VP as data (?fmt=docx for the Word document,
                                                       ?lang=fr for French headings)

Services: ``services/ait.py``; document: ``services/docx/vp.py`` ``generate_verification_plan_docx``.
"""
from __future__ import annotations

import io
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..services import ait as svc

router = APIRouter()


def _require_study(study_id: str) -> Any:
    from .elements import _elements
    from .studies import get_study_store
    st = get_study_store().get(study_id)
    if st is None and not any(e.get("study_id") == study_id for e in _elements.values()):
        raise HTTPException(404, f"Study {study_id} not found")
    return st


class ModelBody(BaseModel):
    code: str | None = None
    name: str | None = None
    name_fr: str | None = None
    philosophy: str | None = None
    level: str | None = None
    due_month: int | None = None
    purpose: str | None = None
    purpose_fr: str | None = None
    build_standard: str | None = None
    status: str | None = None
    order: int | None = None


class TestBody(BaseModel):
    code: str | None = None
    name: str | None = None
    name_fr: str | None = None
    category: str | None = None
    models: list[str] | None = None
    level: str | None = None
    level_source: str | None = None
    facility: str | None = None
    environment: dict[str, Any] | None = None
    requirement_codes: list[str] | None = None
    stage: str | None = None
    status: str | None = None
    notes: str | None = None
    order: int | None = None


class ProposeBody(BaseModel):
    replace: bool = False


@router.get("/studies/{study_id}/ait")
async def get_ait(study_id: str) -> dict:
    study = _require_study(study_id)
    _, els = svc._study_and_elements(study_id)
    return {"models": await svc.list_models(study_id), "tests": await svc.list_tests(study_id),
            "environment": svc.environment_levels(study, els, launch_provided=await svc._launch_provided(study_id)),
            "stages": list(svc.STAGES)}


@router.post("/studies/{study_id}/ait/propose")
async def propose_ait(study_id: str, body: ProposeBody | None = None) -> dict:
    _require_study(study_id)
    return await svc.propose(study_id, replace=bool(body and body.replace))


@router.post("/studies/{study_id}/ait/import")
async def import_plan(study_id: str, body: dict[str, Any]) -> dict:
    """Wave 3 (3.A4): a V&V plan's model philosophy and verification events (``vv_plan.yaml``
    shape) as the study's models and test-matrix events: ``{"plan": {...}, "replace_proposed": true}``."""
    _require_study(study_id)
    plan = body.get("plan") or body.get("document")
    if not isinstance(plan, dict):
        raise HTTPException(422, "plan must be the V&V plan document (an object)")
    return await svc.import_vv_plan(study_id, plan, replace_proposed=body.get("replace_proposed", True) is not False)


@router.post("/studies/{study_id}/ait/models")
async def add_model(study_id: str, body: ModelBody) -> dict:
    _require_study(study_id)
    if not body.code:
        raise HTTPException(422, "code is required")
    return await svc.upsert_model(study_id, body.model_dump(exclude_none=True))


@router.patch("/studies/{study_id}/ait/models/{model_id}")
async def patch_model(study_id: str, model_id: str, body: ModelBody) -> dict:
    out = await svc.upsert_model(study_id, body.model_dump(exclude_none=True), model_id)
    if out is None:
        raise HTTPException(404, "model not found")
    return out


@router.delete("/studies/{study_id}/ait/models/{model_id}")
async def delete_model(study_id: str, model_id: str) -> dict:
    if not await svc.delete_row(study_id, "models", model_id):
        raise HTTPException(404, "model not found")
    return {"deleted": model_id}


@router.post("/studies/{study_id}/ait/tests")
async def add_test(study_id: str, body: TestBody) -> dict:
    _require_study(study_id)
    if not body.code:
        raise HTTPException(422, "code is required")
    return await svc.upsert_test(study_id, body.model_dump(exclude_none=True))


@router.patch("/studies/{study_id}/ait/tests/{test_id}")
async def patch_test(study_id: str, test_id: str, body: TestBody) -> dict:
    out = await svc.upsert_test(study_id, body.model_dump(exclude_none=True), test_id)
    if out is None:
        raise HTTPException(404, "test not found")
    return out


@router.delete("/studies/{study_id}/ait/tests/{test_id}")
async def delete_test(study_id: str, test_id: str) -> dict:
    if not await svc.delete_row(study_id, "tests", test_id):
        raise HTTPException(404, "test not found")
    return {"deleted": test_id}


@router.get("/studies/{study_id}/ait/verification-plan")
async def verification_plan(study_id: str, fmt: str = Query("json", description="json or docx"),
                            lang: str = Query("en", description="en or fr")) -> Any:
    _require_study(study_id)
    if fmt == "docx":
        from ..services.docx.vp import generate_verification_plan_docx
        from ..services.export_context import collect
        sx = await collect(study_id, sections=["mission", "requirements", "ait", "schedule", "validation"], lang=lang)
        data = generate_verification_plan_docx(sx, lang=lang)
        return StreamingResponse(io.BytesIO(data),
                                 media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                 headers={"Content-Disposition": f"attachment; filename=VP_{study_id[:8]}.docx"})
    if fmt != "json":
        raise HTTPException(422, "fmt must be json or docx")
    return await svc.verification_plan(study_id)
