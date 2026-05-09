"""Requirement repository — CRUD for the requirement hierarchy (SCDF-111).

Uses the RequirementRow ORM model. All operations return Pydantic Requirement
models for API consumption.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import RequirementRow

logger = logging.getLogger(__name__)


async def get_tree(session: AsyncSession, study_id: str) -> list[dict]:
    """Return full requirement tree for a study, ordered by level then code."""
    result = await session.execute(
        select(RequirementRow)
        .where(RequirementRow.study_id == study_id)
        .where(RequirementRow.status != "retired")
        .order_by(RequirementRow.level, RequirementRow.code)
    )
    rows = result.scalars().all()
    return [_row_to_dict(r) for r in rows]


async def get_by_id(session: AsyncSession, req_id: str) -> dict | None:
    """Get a single requirement by ID."""
    result = await session.execute(
        select(RequirementRow).where(RequirementRow.id == req_id)
    )
    row = result.scalar_one_or_none()
    return _row_to_dict(row) if row else None


async def create(session: AsyncSession, data: dict[str, Any]) -> dict:
    """Create a new requirement."""
    row = RequirementRow(
        id=data["id"],
        study_id=data["study_id"],
        parent_id=data.get("parent_id"),
        level=data["level"],
        code=data["code"],
        text=data["text"],
        rationale=data.get("rationale"),
        threshold_param_path=data.get("threshold_param_path"),
        threshold_op=data.get("threshold_op"),
        threshold_value=data.get("threshold_value"),
        verification_method=data.get("verification_method"),
        verification_phase=data.get("verification_phase"),
        responsible_position=data.get("responsible_position"),
        status=data.get("status", "draft"),
        derived_from_requirement_id=data.get("derived_from_requirement_id"),
    )
    session.add(row)
    await session.flush()
    return _row_to_dict(row)


async def update_requirement(session: AsyncSession, req_id: str, data: dict[str, Any]) -> dict | None:
    """Update a requirement's fields."""
    data["updated_at"] = datetime.now(timezone.utc)
    await session.execute(
        update(RequirementRow)
        .where(RequirementRow.id == req_id)
        .values(**{k: v for k, v in data.items() if hasattr(RequirementRow, k)})
    )
    return await get_by_id(session, req_id)


async def soft_delete(session: AsyncSession, req_id: str) -> bool:
    """Soft-delete by setting status to 'retired'."""
    result = await session.execute(
        update(RequirementRow)
        .where(RequirementRow.id == req_id)
        .values(status="retired", updated_at=datetime.now(timezone.utc))
    )
    return result.rowcount > 0


async def derive_child(session: AsyncSession, parent_id: str, child_data: dict[str, Any]) -> dict:
    """Create a child requirement derived from a parent."""
    parent = await get_by_id(session, parent_id)
    if not parent:
        raise ValueError(f"Parent requirement {parent_id} not found")

    child_data["parent_id"] = parent_id
    child_data["study_id"] = parent["study_id"]
    return await create(session, child_data)


def _row_to_dict(row: RequirementRow) -> dict:
    """Convert a RequirementRow to a plain dict."""
    return {
        "id": row.id,
        "study_id": row.study_id,
        "parent_id": row.parent_id,
        "level": row.level,
        "code": row.code,
        "text": row.text,
        "rationale": row.rationale,
        "threshold_param_path": row.threshold_param_path,
        "threshold_op": row.threshold_op,
        "threshold_value": row.threshold_value,
        "verification_method": row.verification_method,
        "verification_phase": row.verification_phase,
        "responsible_position": row.responsible_position,
        "status": row.status,
        "derived_from_requirement_id": row.derived_from_requirement_id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
