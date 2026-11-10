"""Small CRUD helpers for the study-owned wave-3 tables of agent A (allocation ledger,
reliability blocks, FMEA rows, thermal nodes / couplings / cases, cost items).

Every table has ``id``, ``study_id``, ``order``, ``origin``, ``data_json`` and timestamps; these
helpers turn rows into plain dicts (the JSON the routes return and the export sections read) and
write them back. One short session per call, the same rule as the other repositories.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy import delete, select


def new_id(prefix: str = "") -> str:
    return (prefix + uuid.uuid4().hex)[:32]


def _columns(model) -> list[str]:
    return [c.key for c in model.__table__.columns]


def to_dict(row) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for c in row.__table__.columns:
        v = getattr(row, c.key)
        if isinstance(v, datetime):
            v = v.isoformat()
        out[c.key] = v
    return out


def clean(model, data: dict[str, Any]) -> dict[str, Any]:
    """Only the model's own columns, never the primary key or the timestamps."""
    cols = set(_columns(model)) - {"id", "created_at", "updated_at"}
    return {k: v for k, v in data.items() if k in cols}


async def list_rows(model, study_id: str, **where: Any) -> list[dict[str, Any]]:
    from ..db.engine import get_session_factory
    async with get_session_factory()() as s:
        q = select(model).where(model.study_id == study_id)
        for k, v in where.items():
            q = q.where(getattr(model, k) == v)
        rows = (await s.execute(q)).scalars().all()
    out = [to_dict(r) for r in rows]
    out.sort(key=lambda r: (r.get("order") or 0, str(r.get("code") or r.get("name") or ""), r["id"]))
    return out


async def get_row(model, row_id: str) -> dict[str, Any] | None:
    from ..db.engine import get_session_factory
    async with get_session_factory()() as s:
        r = await s.get(model, row_id)
        return to_dict(r) if r is not None else None


async def insert_rows(model, study_id: str, rows: Iterable[dict[str, Any]], prefix: str = "") -> list[dict[str, Any]]:
    from ..db.engine import get_session_factory
    out = []
    async with get_session_factory()() as s:
        for data in rows:
            obj = model(id=data.get("id") or new_id(prefix), study_id=study_id, **clean(model, data))
            s.add(obj)
            out.append(obj)
        await s.commit()
        return [to_dict(o) for o in out]


async def update_row(model, row_id: str, fields: dict[str, Any]) -> dict[str, Any] | None:
    from ..db.engine import get_session_factory
    async with get_session_factory()() as s:
        r = await s.get(model, row_id)
        if r is None:
            return None
        for k, v in clean(model, fields).items():
            setattr(r, k, v)
        await s.commit()
        await s.refresh(r)
        return to_dict(r)


async def delete_rows(model, study_id: str, ids: Iterable[str] | None = None, **where: Any) -> int:
    from ..db.engine import get_session_factory
    async with get_session_factory()() as s:
        q = delete(model).where(model.study_id == study_id)
        if ids is not None:
            q = q.where(model.id.in_(list(ids)))
        for k, v in where.items():
            q = q.where(getattr(model, k) == v)
        res = await s.execute(q)
        await s.commit()
        return int(res.rowcount or 0)
