"""Requirement persistence — write-through mirror for ``routers.requirements``.

Canonical requirement repository (SCDF-160 N0). Mirrors the pattern of
``db/element_repo.py``: the in-memory ``routers.requirements._requirements``
dict is the primary read path; every mutation is mirrored here so data
survives restarts, and ``load_all_requirements`` hydrates the cache at
start-up (or lazily on first use).

Dict <-> row mapping is column-driven (``hasattr(RequirementRow, key)``), so
new columns such as ``objective_id`` / ``external_id`` flow through without
edits here. ``external_ids`` (API key) <-> ``external_ids_json`` (column).

All DB errors are logged and swallowed so the hot path never crashes.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update as sa_update

from .engine import get_session_factory
from .models import RequirementRow

logger = logging.getLogger(__name__)

_JSON_FIELDS = {"external_ids": "external_ids_json"}
_TIMESTAMPS = ("created_at", "updated_at")


def _dict_to_row_kwargs(d: dict) -> dict:
    """Convert an in-memory requirement dict to RequirementRow column kwargs."""
    kw: dict[str, Any] = {}
    for k, v in d.items():
        col = _JSON_FIELDS.get(k, k)
        if col in _TIMESTAMPS or not hasattr(RequirementRow, col):
            continue
        if col == "threshold_value" and v is not None and not isinstance(v, str):
            v = json.dumps(v)  # column is Text (JSON-encoded)
        kw[col] = v
    return kw


def _row_to_dict(row: RequirementRow) -> dict:
    """Convert a RequirementRow to the flat dict served by the API."""
    d: dict[str, Any] = {}
    for c in RequirementRow.__table__.columns:
        if c.key in _TIMESTAMPS:
            continue
        d[c.key] = getattr(row, c.key)
    ext = d.pop("external_ids_json", None)
    if ext is not None:
        d["external_ids"] = ext
    # Before Nov 2026 the Requirements panel stored the type in ``rationale``; move it.
    if not d.get("req_type") and d.get("rationale") in REQ_TYPES:
        d["req_type"], d["rationale"] = d["rationale"], None
    return d


#: Requirement types (RequirementsPanel REQ_TYPES).
REQ_TYPES = frozenset({"functional", "performance", "interface", "regulatory", "process"})


# ── Public API (write-through) ─────────────────────────────────────────

async def load_all_requirements() -> dict[str, dict]:
    """Load every requirement row (including retired) keyed by id.

    Retired rows are kept so ``GET /requirements/{id}`` and parent lookups
    keep behaving exactly as they did in-process; ``/tree`` filters them.
    """
    out: dict[str, dict] = {}
    try:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(RequirementRow))
            for row in result.scalars():
                d = _row_to_dict(row)
                out[d["id"]] = d
        logger.info("Loaded %d requirements from DB", len(out))
    except Exception:
        logger.exception("Failed to load requirements from DB — starting with empty cache")
    return out


async def db_create_requirement(req: dict) -> None:
    """Persist a new requirement (write-through; non-fatal)."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            session.add(RequirementRow(**_dict_to_row_kwargs(req)))
            await session.commit()
    except Exception:
        logger.exception("db_create_requirement failed for %s", req.get("id"))


async def db_update_requirement(req_id: str, full_dict: dict) -> None:
    """Persist the full current state of a requirement (write-through; non-fatal)."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            kw = _dict_to_row_kwargs(full_dict)
            kw.pop("id", None)
            kw["updated_at"] = datetime.now(timezone.utc)
            await session.execute(
                sa_update(RequirementRow).where(RequirementRow.id == req_id).values(**kw)
            )
            await session.commit()
    except Exception:
        logger.exception("db_update_requirement failed for %s", req_id)


async def db_upsert_requirement(req: dict) -> None:
    """Create-or-update by id (used by importers that write straight into the cache)."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            exists = await session.get(RequirementRow, req["id"])
    except Exception:
        logger.exception("db_upsert_requirement lookup failed for %s", req.get("id"))
        return
    if exists is None:
        await db_create_requirement(req)
    else:
        await db_update_requirement(req["id"], req)


async def db_soft_delete_requirement(req_id: str) -> None:
    """Mark a requirement retired (write-through; non-fatal)."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(
                sa_update(RequirementRow)
                .where(RequirementRow.id == req_id)
                .values(status="retired", updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
    except Exception:
        logger.exception("db_soft_delete_requirement failed for %s", req_id)
