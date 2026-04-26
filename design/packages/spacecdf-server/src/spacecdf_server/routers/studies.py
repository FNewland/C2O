"""SpaceCDF — Study Management API.

CRUD operations for design studies.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from spacecdf_common.models.study import Study, MissionRequirements

router = APIRouter()

# In-memory study store (PostgreSQL in production)
_studies: dict[str, Study] = {}


@router.get("/")
async def list_studies() -> list[dict]:
    """List all studies."""
    return [
        {"id": s.id, "name": s.name, "phase": s.phase, "created": s.created.isoformat()}
        for s in _studies.values()
    ]


@router.post("/")
async def create_study(requirements: MissionRequirements) -> Study:
    """Create a new design study from mission requirements."""
    study = Study(
        id=str(uuid.uuid4())[:8],
        name=requirements.name,
        requirements=requirements,
        created=datetime.now(timezone.utc),
    )
    _studies[study.id] = study
    return study


@router.get("/{study_id}")
async def get_study(study_id: str) -> Study:
    """Get a study by ID."""
    study = _studies.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    return study


@router.delete("/{study_id}")
async def delete_study(study_id: str) -> dict:
    """Delete a study."""
    if study_id not in _studies:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    del _studies[study_id]
    return {"deleted": study_id}


def get_study_store() -> dict[str, Study]:
    """Access the study store (for use by other routers)."""
    return _studies
