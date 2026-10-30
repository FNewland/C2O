"""Shared helpers for the SCDF-160 arcadia repositories.

All repos are dict-in / dict-out like ``element_repo``. Rows are the truth
(no in-memory cache in this layer), so:

* ``load_all_*`` / ``list_*`` never raise — they log and return empty.
* ``create_*`` / ``update_*`` / ``soft_delete_*`` raise ``ValueError`` on
  not-found / version conflict and let DB errors propagate, so routers can
  turn them into 404 / 409 / 500.

Dict keys use the API-level spelling (``external_ids``, ``exchange_item_ids``,
``properties``) which map to the ``*_json`` ORM columns.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from .engine import get_session_factory  # re-exported for repos
from .models import Base

__all__ = [
    "get_session_factory", "new_id", "utcnow", "row_to_dict", "dict_to_kwargs",
    "apply_update", "get_row", "soft_delete_row", "JSON_KEY_MAP",
]

#: API key -> ORM column for JSON-bearing columns (applies to all arcadia rows).
JSON_KEY_MAP: dict[str, str] = {
    "external_ids": "external_ids_json",
    "exchange_item_ids": "exchange_item_ids_json",
    "properties": "properties_json",
}
_COL_TO_KEY = {v: k for k, v in JSON_KEY_MAP.items()}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def row_to_dict(row: Base) -> dict:
    """ORM row -> flat dict with API-level keys; datetimes as ISO strings."""
    d: dict[str, Any] = {}
    for c in row.__table__.columns:
        val = getattr(row, c.key)
        if isinstance(val, datetime):
            # SCDF-170 verification fix: SQLite drops tzinfo, and a naive ISO string is
            # parsed as *local* time by browsers (`new Date(...)`) — stamp it as UTC.
            if val.tzinfo is None:
                val = val.replace(tzinfo=timezone.utc)
            val = val.isoformat()
        d[_COL_TO_KEY.get(c.key, c.key)] = val
    return d


def dict_to_kwargs(model: type[Base], d: dict) -> dict:
    """API-level dict -> column kwargs, dropping unknown keys and enum-ising values."""
    kw: dict[str, Any] = {}
    cols = {c.key for c in model.__table__.columns}
    for k, v in d.items():
        col = JSON_KEY_MAP.get(k, k)
        if col not in cols:
            continue
        if hasattr(v, "value") and not isinstance(v, (int, float, str, bool)):
            v = v.value  # pydantic/str enums
        if isinstance(v, str) and col in ("deleted_at", "created_at", "updated_at"):
            v = datetime.fromisoformat(v)
        kw[col] = v
    return kw


async def get_row(session, model: type[Base], row_id: str, *, include_deleted: bool = False):
    row = await session.get(model, row_id)
    if row is None:
        return None
    if not include_deleted and getattr(row, "deleted_at", None) is not None:
        return None
    return row


def apply_update(row: Base, updates: dict, *, expected_version: int | None = None,
                 immutable: tuple[str, ...] = ("id", "study_id", "created_at")) -> None:
    """Apply an update dict to a row with optimistic locking.

    Raises ``ValueError`` on version mismatch. Bumps ``version`` and
    ``updated_at`` when the row has them.
    """
    if expected_version is not None and hasattr(row, "version") and row.version != expected_version:
        raise ValueError(
            f"Version conflict on {row.__tablename__}/{row.id}: "
            f"expected {expected_version}, have {row.version}"
        )
    kw = dict_to_kwargs(type(row), updates)
    for key in immutable + ("version", "deleted_at"):
        kw.pop(key, None)
    for k, v in kw.items():
        setattr(row, k, v)
    if hasattr(row, "version"):
        row.version = (row.version or 0) + 1
    if hasattr(row, "updated_at"):
        row.updated_at = utcnow()


async def soft_delete_row(model: type[Base], row_id: str) -> bool:
    """Set ``deleted_at`` (or hard-delete rows without that column). Returns True if a row changed."""
    factory = get_session_factory()
    async with factory() as session:
        row = await session.get(model, row_id)
        if row is None:
            return False
        if hasattr(row, "deleted_at"):
            if row.deleted_at is not None:
                return False
            row.deleted_at = utcnow()
        else:
            await session.delete(row)
        await session.commit()
        return True


async def list_rows(model: type[Base], *filters, include_deleted: bool = False, order_by=None) -> list[dict]:
    """Generic list helper; never raises."""
    import logging
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(model).where(*filters)
            if not include_deleted and hasattr(model, "deleted_at"):
                stmt = stmt.where(model.deleted_at.is_(None))
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            result = await session.execute(stmt)
            return [row_to_dict(r) for r in result.scalars()]
    except Exception:
        logging.getLogger(__name__).exception("list_rows failed for %s", model.__tablename__)
        return []
