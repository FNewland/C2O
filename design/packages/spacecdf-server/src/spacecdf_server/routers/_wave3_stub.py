"""Helpers for the wave-3 stub routes (step 0). Each owner replaces its stubs with real code and
stops importing this module; the file goes once no router uses it (owner A)."""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def study_or_404(study_id: str):
    from .studies import get_study_store
    study = get_study_store().get(study_id)
    if study is None:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    return study


def stub_list(study_id: str, owner: str, work_package: str, **shape: Any) -> dict[str, Any]:
    """A list route that has no model yet: 200 with the empty shape, marked as a stub."""
    study_or_404(study_id)
    return {"study_id": study_id, "items": [], "status": "not_implemented", "owner": owner,
            "work_package": work_package, **shape}


def not_implemented(owner: str, work_package: str) -> HTTPException:
    """A write route that has no model yet: 501, naming the owner and work package."""
    return HTTPException(status_code=501, detail={"status": "not_implemented", "owner": owner,
                                                  "work_package": work_package})
