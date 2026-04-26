"""SpaceCDF — Mission Template API.

Exposes the canonical MissionTemplate library plus a helper endpoint
to create a new Study seeded from a template.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from spacecdf_common.models.study import Study
from spacecdf_common.models.template import MissionTemplate

from ..services.template_library import get_template, list_templates
from .studies import get_study_store

router = APIRouter()


@router.get("/", response_model=list[MissionTemplate])
async def list_all_templates() -> list[MissionTemplate]:
    """Return all available mission templates."""
    return list_templates()


@router.get("/{template_id}", response_model=MissionTemplate)
async def get_template_by_id(template_id: str) -> MissionTemplate:
    """Return a single template by id."""
    tmpl = get_template(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return tmpl


@router.post("/{template_id}/instantiate", response_model=Study)
async def create_study_from_template(template_id: str) -> Study:
    """Create a new Study seeded from the given template.

    The returned Study is also stored in the in-memory study store so that
    subsequent /api/studies/{id} calls work against it.
    """
    tmpl = get_template(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    study = Study(
        id=str(uuid.uuid4())[:8],
        name=tmpl.requirements.name,
        phase=tmpl.target_phase,
        requirements=tmpl.requirements,
        created=datetime.now(timezone.utc),
        notes=f"Seeded from template: {tmpl.id} ({tmpl.name})",
    )
    get_study_store()[study.id] = study
    return study
