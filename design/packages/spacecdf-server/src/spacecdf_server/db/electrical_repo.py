"""Repository for the electrical and data-handling rows (db/electrical_models.py).

Dict in / dict out, rows are the truth (no cache), like the arcadia repositories. API keys
drop the ``_json`` suffix (``inhibits``, ``load_element_ids``, ``properties``,
``interface_ids``, ``rationale``, ``proposed``).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from .electrical_models import BusNodeRow, DataBusRow, ElementPortRow, PowerLineRow, PowerRailRow
from .engine import get_session_factory

logger = logging.getLogger(__name__)

#: API collection name → ORM class
KINDS: dict[str, type] = {
    "rails": PowerRailRow,
    "lines": PowerLineRow,
    "buses": DataBusRow,
    "nodes": BusNodeRow,
    "ports": ElementPortRow,
}
ID_PREFIX = {"rails": "rail", "lines": "pl", "buses": "bus", "nodes": "node", "ports": "port"}

_JSON = {
    "rationale": "rationale_json", "inhibits": "inhibits_json", "load_element_ids": "load_element_ids_json",
    "properties": "properties_json", "interface_ids": "interface_ids_json", "proposed": "proposed_json",
}
_COL_TO_KEY = {v: k for k, v in _JSON.items()}
_TS = ("created_at", "updated_at", "deleted_at")


def row_to_dict(row: Any) -> dict:
    d: dict[str, Any] = {}
    for c in row.__table__.columns:
        val = getattr(row, c.key)
        if isinstance(val, datetime):
            if val.tzinfo is None:
                val = val.replace(tzinfo=timezone.utc)
            val = val.isoformat()
        d[_COL_TO_KEY.get(c.key, c.key)] = val
    for k in ("inhibits", "load_element_ids", "interface_ids"):
        if k in d and d[k] is None:
            d[k] = []
    if "properties" in d and d["properties"] is None:
        d["properties"] = {}
    return d


def dict_to_kwargs(model: type, d: dict) -> dict:
    cols = {c.key for c in model.__table__.columns}
    kw: dict[str, Any] = {}
    for k, v in d.items():
        col = _JSON.get(k, k)
        if col not in cols or col in _TS:
            continue
        kw[col] = v
    return kw


async def list_rows(kind: str, study_id: str, *, include_deleted: bool = False) -> list[dict]:
    model = KINDS[kind]
    try:
        async with get_session_factory()() as session:
            stmt = select(model).where(model.study_id == study_id)
            if not include_deleted:
                stmt = stmt.where(model.deleted_at.is_(None))
            res = await session.execute(stmt)
            return [row_to_dict(r) for r in res.scalars()]
    except Exception:
        logger.exception("list %s failed for %s", kind, study_id)
        return []


async def load_all(study_id: str, *, include_deleted: bool = False) -> dict[str, list[dict]]:
    return {k: await list_rows(k, study_id, include_deleted=include_deleted) for k in KINDS}


async def get_row(kind: str, row_id: str) -> dict | None:
    model = KINDS[kind]
    async with get_session_factory()() as session:
        row = await session.get(model, row_id)
        return row_to_dict(row) if row is not None else None


async def create_row(kind: str, d: dict) -> dict:
    model = KINDS[kind]
    kw = dict_to_kwargs(model, d)
    if not kw.get("id"):
        from uuid import uuid4
        kw["id"] = f"{ID_PREFIX[kind]}-{uuid4().hex[:12]}"
    async with get_session_factory()() as session:
        existing = await session.get(model, kw["id"])
        if existing is not None:      # revive a soft-deleted deterministic id
            for k, v in kw.items():
                setattr(existing, k, v)
            existing.deleted_at = None
            existing.version = int(existing.version or 1) + 1
            row = existing
        else:
            row = model(**kw)
            session.add(row)
        await session.commit()
        return row_to_dict(row)


async def update_row(kind: str, row_id: str, changes: dict) -> dict:
    model = KINDS[kind]
    async with get_session_factory()() as session:
        row = await session.get(model, row_id)
        if row is None:
            raise KeyError(row_id)
        for k, v in dict_to_kwargs(model, changes).items():
            if k == "id":
                continue
            setattr(row, k, v)
        row.version = int(row.version or 1) + 1
        await session.commit()
        return row_to_dict(row)


async def soft_delete_row(kind: str, row_id: str) -> bool:
    model = KINDS[kind]
    async with get_session_factory()() as session:
        row = await session.get(model, row_id)
        if row is None or row.deleted_at is not None:
            return False
        row.deleted_at = datetime.now(timezone.utc)
        await session.commit()
        return True
