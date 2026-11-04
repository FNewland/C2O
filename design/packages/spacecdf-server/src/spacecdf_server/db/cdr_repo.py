"""Repository for the CDR design model rows (db/cdr_models.py).

Dict in / dict out, rows are the truth (no cache). API keys drop the ``_json`` suffix
(``data``, ``rationale``, ``proposed``).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from .cdr_models import CdrRow
from .engine import get_session_factory

logger = logging.getLogger(__name__)

_JSON = {"data": "data_json", "rationale": "rationale_json", "proposed": "proposed_json"}
_COL_TO_KEY = {v: k for k, v in _JSON.items()}
_TS = ("created_at", "updated_at", "deleted_at")
_COLS = {c.key for c in CdrRow.__table__.columns}


def row_to_dict(row: CdrRow) -> dict:
    d: dict[str, Any] = {}
    for c in row.__table__.columns:
        val = getattr(row, c.key)
        if isinstance(val, datetime):
            if val.tzinfo is None:
                val = val.replace(tzinfo=timezone.utc)
            val = val.isoformat()
        d[_COL_TO_KEY.get(c.key, c.key)] = val
    if d.get("data") is None:
        d["data"] = {}
    return d


def _kwargs(d: dict) -> dict:
    kw: dict[str, Any] = {}
    for k, v in d.items():
        col = _JSON.get(k, k)
        if col in _COLS and col not in _TS:
            kw[col] = v
    return kw


async def list_rows(study_id: str, kind: str | None = None, *, include_deleted: bool = False) -> list[dict]:
    try:
        async with get_session_factory()() as s:
            q = select(CdrRow).where(CdrRow.study_id == study_id)
            if kind:
                q = q.where(CdrRow.kind == kind)
            if not include_deleted:
                q = q.where(CdrRow.deleted_at.is_(None))
            res = await s.execute(q)
            return [row_to_dict(r) for r in res.scalars()]
    except Exception:
        logger.exception("cdr list failed for %s", study_id)
        return []


async def get_row(row_id: str) -> dict | None:
    async with get_session_factory()() as s:
        row = await s.get(CdrRow, row_id)
        return row_to_dict(row) if row is not None else None


async def create_rows(rows: list[dict]) -> int:
    """Insert (or revive soft-deleted rows with the same id) in one transaction."""
    if not rows:
        return 0
    async with get_session_factory()() as s:
        for d in rows:
            kw = _kwargs(d)
            kw.setdefault("id", f"cdr-{uuid4().hex[:12]}")
            existing = await s.get(CdrRow, kw["id"])
            if existing is not None:
                for k, v in kw.items():
                    setattr(existing, k, v)
                existing.deleted_at = None
                existing.version = int(existing.version or 1) + 1
            else:
                s.add(CdrRow(**kw))
        await s.commit()
    return len(rows)


async def create_row(d: dict) -> dict:
    d = dict(d)
    d.setdefault("id", f"cdr-{uuid4().hex[:12]}")
    await create_rows([d])
    out = await get_row(d["id"])
    assert out is not None
    return out


async def update_rows(changes: list[tuple[str, dict]]) -> int:
    if not changes:
        return 0
    async with get_session_factory()() as s:
        for row_id, ch in changes:
            row = await s.get(CdrRow, row_id)
            if row is None:
                continue
            for k, v in _kwargs(ch).items():
                if k != "id":
                    setattr(row, k, v)
            row.version = int(row.version or 1) + 1
        await s.commit()
    return len(changes)


async def update_row(row_id: str, changes: dict) -> dict:
    await update_rows([(row_id, changes)])
    out = await get_row(row_id)
    if out is None:
        raise KeyError(row_id)
    return out


async def soft_delete_rows(row_ids: list[str]) -> int:
    if not row_ids:
        return 0
    now = datetime.now(timezone.utc)
    n = 0
    async with get_session_factory()() as s:
        for rid in row_ids:
            row = await s.get(CdrRow, rid)
            if row is not None and row.deleted_at is None:
                row.deleted_at = now
                n += 1
        await s.commit()
    return n


async def purge_study(study_id: str, *, origin_prefix: str | None = None) -> int:
    """Hard-delete rows of a study (all, or those whose origin starts with ``origin_prefix``)."""
    async with get_session_factory()() as s:
        res = await s.execute(select(CdrRow).where(CdrRow.study_id == study_id))
        n = 0
        for r in res.scalars():
            if origin_prefix is None or str(r.origin or "").startswith(origin_prefix):
                await s.delete(r)
                n += 1
        await s.commit()
    return n
