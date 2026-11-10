"""Small helpers shared by the section collectors."""
from __future__ import annotations

from typing import Any


def stub(owner: str, work_package: str, **shape: Any) -> dict:
    """The shape of a section whose model does not exist yet."""
    return {"status": "not_implemented", "owner": owner, "work_package": work_package, **shape}


def dump(obj: Any) -> Any:
    """Pydantic model / list of models -> plain JSON data (anything else unchanged)."""
    if obj is None:
        return None
    if isinstance(obj, list):
        return [dump(o) for o in obj]
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return obj
