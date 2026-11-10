"""Requirement persistence — write-through mirror for ``routers.requirements``.

Canonical requirement repository (SCDF-160 N0). Mirrors the pattern of
``db/element_repo.py``: the in-memory ``routers.requirements._requirements``
dict is the primary read path; every mutation is mirrored here so data
survives restarts, and ``load_all_requirements`` hydrates the cache at
start-up (or lazily on first use).

Dict <-> row mapping is column-driven (``hasattr(RequirementRow, key)``), so
new columns such as ``objective_id`` / ``external_id`` flow through without
edits here. ``external_ids`` (API key) <-> ``external_ids_json`` (column).

``threshold_value`` is JSON text in the column. It is decoded on load and normalised on write
(``normalise_threshold_value``), so the API serves the same value before and after a restart:
``15``, ``15.0`` and ``"15"`` all become ``15``; ``{"min": .., "max": ..}`` stays a dict; a date or
any other text stays a string (W1.01).

Write errors are no longer swallowed (W2.04): a duplicate live code in a study raises
``DuplicateCodeError`` (the API answers 409); any other integrity or data error (duplicate id,
unknown parent) raises ``RequirementStoreError``, so a caller never believes a row was saved
when it was not. Only an unavailable database (no table, locked, read-only) is still logged
and tolerated, so the in-memory store keeps working.
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


class RequirementStoreError(RuntimeError):
    """A requirement write failed in the database."""


class DuplicateCodeError(RequirementStoreError):
    """Another live requirement of the study already has this code."""


def normalise_threshold_value(v: Any) -> Any:
    """One canonical in-memory form for a threshold value (see the module doc).

    JSON text is decoded; numeric text becomes a number; an integral float becomes an int;
    a dict with numeric text (``{"min": "449.75"}``) gets numbers; anything else is kept."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        t = v.strip()
        if t == "":
            return None
        try:
            v = json.loads(t)
        except (ValueError, TypeError):
            try:
                v = float(t.replace(",", "."))
            except ValueError:
                return t
        if isinstance(v, str):
            return normalise_threshold_value(v) if v.strip() != t else v
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return v
        return int(v) if v.is_integer() else v
    if isinstance(v, dict):
        return {k: normalise_threshold_value(x) for k, x in v.items()}
    if isinstance(v, list):
        return [normalise_threshold_value(x) for x in v]
    return v


def _encode_threshold(v: Any) -> str | None:
    v = normalise_threshold_value(v)
    if v is None:
        return None
    return json.dumps(v)


_JSON_FIELDS = {"external_ids": "external_ids_json", "verification_methods": "verification_methods_json"}
_TIMESTAMPS = ("created_at", "updated_at")


def _dict_to_row_kwargs(d: dict) -> dict:
    """Convert an in-memory requirement dict to RequirementRow column kwargs."""
    kw: dict[str, Any] = {}
    for k, v in d.items():
        col = _JSON_FIELDS.get(k, k)
        if col in _TIMESTAMPS or not hasattr(RequirementRow, col):
            continue
        if col == "threshold_value":
            v = _encode_threshold(v)  # column is Text (JSON-encoded)
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
    d["verification_methods"] = d.pop("verification_methods_json", None)
    d["threshold_value"] = normalise_threshold_value(d.get("threshold_value"))
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


def _raise(op: str, req_id: Any, exc: Exception) -> None:
    """Integrity and data errors (duplicate code or id, missing parent, bad value) are raised;
    an environment error (no table yet, database locked or read-only) is logged and the
    in-memory write stands, as before (the next start-up reloads from the database)."""
    from sqlalchemy.exc import DataError, IntegrityError, OperationalError
    msg = str(getattr(exc, "orig", exc))
    if isinstance(exc, IntegrityError) and ("code" in msg or "uq_requirements_study_code_live" in msg):
        raise DuplicateCodeError(f"{op} {req_id}: duplicate requirement code ({msg})") from exc
    if isinstance(exc, OperationalError) and not isinstance(exc, (IntegrityError, DataError)):
        logger.exception("%s failed for %s (database unavailable; kept in memory)", op, req_id)
        return
    logger.exception("%s failed for %s", op, req_id)
    raise RequirementStoreError(f"{op} {req_id}: {msg}") from exc


async def db_create_requirement(req: dict) -> None:
    """Persist a new requirement (write-through). Raises on a database error."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            session.add(RequirementRow(**_dict_to_row_kwargs(req)))
            await session.commit()
    except Exception as exc:
        _raise("db_create_requirement", req.get("id"), exc)


async def db_create_requirements(reqs: list[dict]) -> None:
    """Persist many new requirements in one transaction (bulk import). All or nothing."""
    if not reqs:
        return
    try:
        factory = get_session_factory()
        async with factory() as session:
            session.add_all([RequirementRow(**_dict_to_row_kwargs(r)) for r in reqs])
            await session.commit()
    except Exception as exc:
        _raise("db_create_requirements", f"{len(reqs)} rows", exc)


async def db_update_requirement(req_id: str, full_dict: dict) -> None:
    """Persist the full current state of a requirement (write-through). Raises on a database error."""
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
    except Exception as exc:
        _raise("db_update_requirement", req_id, exc)


async def db_update_requirements(reqs: list[dict]) -> None:
    """Persist the full state of many requirements in one transaction (bulk import)."""
    if not reqs:
        return
    try:
        factory = get_session_factory()
        async with factory() as session:
            now = datetime.now(timezone.utc)
            for r in reqs:
                kw = _dict_to_row_kwargs(r)
                kw.pop("id", None)
                kw["updated_at"] = now
                await session.execute(sa_update(RequirementRow).where(RequirementRow.id == r["id"]).values(**kw))
            await session.commit()
    except Exception as exc:
        _raise("db_update_requirements", f"{len(reqs)} rows", exc)


async def db_upsert_requirement(req: dict) -> None:
    """Create-or-update by id (used by importers that write straight into the cache)."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            exists = await session.get(RequirementRow, req["id"])
    except Exception as exc:
        _raise("db_upsert_requirement", req.get("id"), exc)
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
    except Exception as exc:
        _raise("db_soft_delete_requirement", req_id, exc)
