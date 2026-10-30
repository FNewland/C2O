"""Async repository functions for SpaceCDF persistence.

All functions are defensive: DB errors are logged and swallowed so the
hot path never crashes because of persistence problems.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .engine import get_session_factory
from .models import (
    DesignStateSnapshotRow,
    ExportRow,
    ParameterEditRow,
    SessionRow,
    StudyRow,
)

logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)


# ---------------------------------------------------------------------------
# Study
# ---------------------------------------------------------------------------
async def save_study(study_dict: dict) -> None:
    """Upsert a study row."""
    try:
        factory = get_session_factory()
        async with factory() as db:
            existing = await db.get(StudyRow, study_dict["id"])
            if existing:
                existing.name = study_dict.get("name", existing.name)
                existing.meta_json = study_dict.get("meta", existing.meta_json or {})
            else:
                row = StudyRow(
                    id=study_dict["id"],
                    name=study_dict.get("name", ""),
                    meta_json=study_dict.get("meta", {}),
                )
                db.add(row)
            await db.commit()
    except Exception as e:
        logger.warning("save_study failed: %s", e)


async def list_studies() -> list[dict]:
    try:
        factory = get_session_factory()
        async with factory() as db:
            result = await db.execute(select(StudyRow))
            rows = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "meta": r.meta_json or {},
                }
                for r in rows
            ]
    except Exception as e:
        logger.warning("list_studies failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------
async def save_session(session_dict: dict) -> None:
    try:
        factory = get_session_factory()
        async with factory() as db:
            existing = await db.get(SessionRow, session_dict["id"])
            if existing:
                existing.study_id = session_dict.get("study_id", existing.study_id)
                existing.name = session_dict.get("name", existing.name)
                existing.state = session_dict.get("state", existing.state)
                existing.owner_label = session_dict.get(
                    "owner_label", existing.owner_label
                )
                closed_at = session_dict.get("closed_at")
                if closed_at:
                    existing.closed_at = _coerce_dt(closed_at)
            else:
                row = SessionRow(
                    id=session_dict["id"],
                    study_id=session_dict.get("study_id", ""),
                    name=session_dict.get("name", ""),
                    state=session_dict.get("state", "active"),
                    owner_label=session_dict.get("owner_label", ""),
                )
                db.add(row)
            await db.commit()
    except Exception as e:
        logger.warning("save_session failed: %s", e)


async def load_session(session_id: str) -> SessionRow | None:
    try:
        factory = get_session_factory()
        async with factory() as db:
            return await db.get(SessionRow, session_id)
    except Exception as e:
        logger.warning("load_session failed: %s", e)
        return None


async def list_sessions() -> list[dict]:
    try:
        factory = get_session_factory()
        async with factory() as db:
            result = await db.execute(select(SessionRow))
            rows = result.scalars().all()
            out: list[dict] = []
            for r in rows:
                out.append(
                    {
                        "id": r.id,
                        "study_id": r.study_id,
                        "name": r.name,
                        "state": r.state,
                        "owner_label": r.owner_label,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                        "closed_at": r.closed_at.isoformat() if r.closed_at else None,
                    }
                )
            return out
    except Exception as e:
        logger.warning("list_sessions failed: %s", e)
        return []


async def close_session(session_id: str) -> None:
    try:
        factory = get_session_factory()
        async with factory() as db:
            existing = await db.get(SessionRow, session_id)
            if existing:
                existing.state = "closed"
                existing.closed_at = datetime.now(timezone.utc)
                await db.commit()
    except Exception as e:
        logger.warning("close_session failed: %s", e)


# ---------------------------------------------------------------------------
# Parameter edits
# ---------------------------------------------------------------------------
async def save_edit(edit_dict: dict) -> None:
    try:
        factory = get_session_factory()
        async with factory() as db:
            row = ParameterEditRow(
                id=edit_dict["id"],
                session_id=edit_dict["session_id"],
                position_id=edit_dict.get("position_id", ""),
                param_path=edit_dict.get("param_path", ""),
                old_value=_json_safe(edit_dict.get("old_value")),
                new_value=_json_safe(edit_dict.get("new_value")) or "",
                source=edit_dict.get("source", ""),
                actor_label=edit_dict.get("actor_label", ""),
                edit_type=edit_dict.get("edit_type", "override"),
                equipment_id=edit_dict.get("equipment_id"),
                rationale=edit_dict.get("rationale", "") or "",
            )
            db.add(row)
            await db.commit()
    except Exception as e:
        logger.warning("save_edit failed: %s", e)


async def list_edits(
    session_id: str, since: datetime | None = None
) -> list[dict]:
    try:
        factory = get_session_factory()
        async with factory() as db:
            stmt = select(ParameterEditRow).where(
                ParameterEditRow.session_id == session_id
            )
            if since is not None:
                stmt = stmt.where(ParameterEditRow.created_at >= since)
            stmt = stmt.order_by(ParameterEditRow.created_at.asc())
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "session_id": r.session_id,
                    "position_id": r.position_id,
                    "param_path": r.param_path,
                    "old_value": _try_json_load(r.old_value),
                    "new_value": _try_json_load(r.new_value),
                    "source": r.source,
                    "actor_label": r.actor_label,
                    "edit_type": r.edit_type,
                    "equipment_id": r.equipment_id,
                    "rationale": r.rationale,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
    except Exception as e:
        logger.warning("list_edits failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------
async def save_snapshot(session_id: str, state_dict: dict) -> None:
    try:
        factory = get_session_factory()
        async with factory() as db:
            version = state_dict.get("_version", 0)
            payload = json.dumps(state_dict, default=str)
            row = DesignStateSnapshotRow(
                session_id=session_id,
                version=version,
                state_json=payload,
            )
            db.add(row)
            await db.commit()
    except Exception as e:
        logger.warning("save_snapshot failed: %s", e)


async def load_latest_snapshot(session_id: str) -> dict | None:
    try:
        factory = get_session_factory()
        async with factory() as db:
            stmt = (
                select(DesignStateSnapshotRow)
                .where(DesignStateSnapshotRow.session_id == session_id)
                .order_by(DesignStateSnapshotRow.created_at.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                return None
            try:
                return json.loads(row.state_json)
            except Exception:
                return None
    except Exception as e:
        logger.warning("load_latest_snapshot failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _try_json_load(value: str | None):
    if value is None:
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


def _coerce_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
    return None
