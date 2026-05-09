"""Requirement repository — CRUD operations for RequirementRow.

Follows the same defensive pattern as db/repo.py: errors are logged,
never crash the hot path. Uses async SQLAlchemy sessions from the
shared engine.

Hierarchy enforcement (defense in depth):
- Subsystem requirements must have a system-level parent.
- System requirements must have a mission-level parent.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from spacecdf_common.models.requirement import (
    Requirement,
    RequirementLevel,
    RequirementStatus,
)

from ..db.engine import get_session_factory
from ..db.models import RequirementRow

logger = logging.getLogger(__name__)


def _row_to_model(row: RequirementRow) -> Requirement:
    """Convert a DB row to the Pydantic model."""
    return Requirement(
        id=row.id,
        study_id=row.study_id,
        parent_id=row.parent_id,
        level=RequirementLevel(row.level),
        code=row.code,
        text=row.text,
        rationale=row.rationale,
        threshold_param_path=row.threshold_param_path,
        threshold_op=row.threshold_op,
        threshold_value=row.threshold_value,
        verification_method=row.verification_method,
        verification_phase=row.verification_phase,
        responsible_position=row.responsible_position,
        status=RequirementStatus(row.status),
        derived_from_requirement_id=row.derived_from_requirement_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _model_to_row(req: Requirement) -> RequirementRow:
    """Convert the Pydantic model to a DB row."""
    return RequirementRow(
        id=req.id,
        study_id=req.study_id,
        parent_id=req.parent_id,
        level=req.level.value if isinstance(req.level, RequirementLevel) else req.level,
        code=req.code,
        text=req.text,
        rationale=req.rationale,
        threshold_param_path=req.threshold_param_path,
        threshold_op=req.threshold_op,
        threshold_value=req.threshold_value,
        verification_method=req.verification_method,
        verification_phase=req.verification_phase,
        responsible_position=req.responsible_position,
        status=req.status.value if isinstance(req.status, RequirementStatus) else req.status,
        derived_from_requirement_id=req.derived_from_requirement_id,
    )


class RequirementRepository:
    """Async CRUD repository for requirements."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    async def create(self, requirement: Requirement) -> Requirement:
        """Create a new requirement. Validates parent hierarchy."""
        factory = get_session_factory()
        async with factory() as db:
            # Validate parent hierarchy (defense in depth — model also checks)
            if requirement.parent_id:
                parent = await db.get(RequirementRow, requirement.parent_id)
                if parent is None:
                    raise ValueError(f"Parent requirement '{requirement.parent_id}' not found")
                self._validate_parent_level(requirement.level, parent.level)

            row = _model_to_row(requirement)
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return _row_to_model(row)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    async def get_by_id(self, requirement_id: str) -> Requirement | None:
        """Fetch a single requirement by ID."""
        try:
            factory = get_session_factory()
            async with factory() as db:
                row = await db.get(RequirementRow, requirement_id)
                return _row_to_model(row) if row else None
        except Exception as e:
            logger.warning("get_by_id failed: %s", e)
            return None

    async def get_tree(self, study_id: str) -> list[Requirement]:
        """Fetch all requirements for a study, ordered for tree rendering.

        Returns mission-level first, then system, then subsystem.
        Within each level, ordered by code.
        """
        try:
            factory = get_session_factory()
            async with factory() as db:
                stmt = (
                    select(RequirementRow)
                    .where(RequirementRow.study_id == study_id)
                    .order_by(RequirementRow.level, RequirementRow.code)
                )
                result = await db.execute(stmt)
                rows = result.scalars().all()
                return [_row_to_model(r) for r in rows]
        except Exception as e:
            logger.warning("get_tree failed: %s", e)
            return []

    async def get_children(self, parent_id: str) -> list[Requirement]:
        """Fetch all direct children of a requirement."""
        try:
            factory = get_session_factory()
            async with factory() as db:
                stmt = (
                    select(RequirementRow)
                    .where(RequirementRow.parent_id == parent_id)
                    .order_by(RequirementRow.code)
                )
                result = await db.execute(stmt)
                rows = result.scalars().all()
                return [_row_to_model(r) for r in rows]
        except Exception as e:
            logger.warning("get_children failed: %s", e)
            return []

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    async def update(self, requirement_id: str, updates: dict) -> Requirement:
        """Update specific fields of a requirement.

        Validates hierarchy if level or parent_id changes.
        """
        factory = get_session_factory()
        async with factory() as db:
            row = await db.get(RequirementRow, requirement_id)
            if row is None:
                raise ValueError(f"Requirement '{requirement_id}' not found")

            # If level or parent changes, validate hierarchy
            new_level = updates.get("level", row.level)
            new_parent_id = updates.get("parent_id", row.parent_id)
            if "level" in updates or "parent_id" in updates:
                if new_parent_id:
                    parent = await db.get(RequirementRow, new_parent_id)
                    if parent is None:
                        raise ValueError(f"Parent requirement '{new_parent_id}' not found")
                    level_enum = RequirementLevel(new_level) if isinstance(new_level, str) else new_level
                    self._validate_parent_level(level_enum, parent.level)

            # Apply updates
            allowed_fields = {
                "parent_id", "level", "code", "text", "rationale",
                "threshold_param_path", "threshold_op", "threshold_value",
                "verification_method", "verification_phase", "verification_evidence",
                "responsible_position", "status", "derived_from_requirement_id",
            }
            for key, value in updates.items():
                if key in allowed_fields:
                    # Convert enums to their string values for DB storage
                    if key == "level" and isinstance(value, RequirementLevel):
                        value = value.value
                    if key == "status" and isinstance(value, RequirementStatus):
                        value = value.value
                    setattr(row, key, value)

            row.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(row)
            return _row_to_model(row)

    # ------------------------------------------------------------------
    # Delete (hard delete — soft delete via status=retired is in SCDF-112)
    # ------------------------------------------------------------------
    async def delete(self, requirement_id: str) -> None:
        """Hard-delete a requirement. See SCDF-112 for soft-delete."""
        factory = get_session_factory()
        async with factory() as db:
            row = await db.get(RequirementRow, requirement_id)
            if row is None:
                raise ValueError(f"Requirement '{requirement_id}' not found")
            await db.delete(row)
            await db.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_parent_level(
        child_level: RequirementLevel | str,
        parent_level: str,
    ) -> None:
        """Enforce hierarchy: system->mission, subsystem->system."""
        child = child_level.value if isinstance(child_level, RequirementLevel) else child_level
        if child == "system" and parent_level != "mission":
            raise ValueError(
                f"System requirements must have a mission parent, got '{parent_level}'"
            )
        if child == "subsystem" and parent_level != "system":
            raise ValueError(
                f"Subsystem requirements must have a system parent, got '{parent_level}'"
            )
