"""Shared lookup for the routers that work on one study: the study, or a 404."""
from __future__ import annotations

from fastapi import HTTPException


def study_or_404(study_id: str):
    """The cached study, or ``HTTPException(404)`` naming the id."""
    from .studies import get_study_store
    study = get_study_store().get(study_id)
    if study is None:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    return study
