"""Async repository for typed requirement relations (SCDF-160 §1.4).

Public API:
    load_all_relations(study_id=None)                      -> dict[id, dict]
    create_relation(d)          idempotent on (kind, source, target); revives soft-deleted
    get_relation(id) / soft_delete_relation(id)
    list_relations_by_study(study_id, kind=None)
    list_relations_for(entity_kind, entity_id, kind=None, direction="both")
    sync_relations(study_id, wanted, owned)                 bulk: make a set of relations exact

Entity kinds (Nov 2026, W2.03/W2.07): ``objective`` (a MissionNeed objective id such as ``O1``;
``traces`` requirement -> objective) and ``exchange_item`` (an ICD row; ``allocates`` interface
requirement -> exchange item). Further parents are ``derives`` requirement -> parent requirement.
"""
from __future__ import annotations

import logging

from sqlalchemy import and_, or_, select

from ._arcadia_common import (
    dict_to_kwargs, get_row, get_session_factory, list_rows, new_id, row_to_dict,
    soft_delete_row,
)
from .models import RequirementRelationRow

logger = logging.getLogger(__name__)

RELATION_KINDS = ("satisfies", "verifies", "refines", "derives", "traces", "allocates")
ENTITY_KINDS = ("requirement", "element", "function", "interface", "parameter", "test", "objective",
                "exchange_item")


async def load_all_relations(study_id: str | None = None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(RequirementRelationRow).where(RequirementRelationRow.deleted_at.is_(None))
            if study_id is not None:
                stmt = stmt.where(RequirementRelationRow.study_id == study_id)
            result = await session.execute(stmt)
            for row in result.scalars():
                d = row_to_dict(row)
                out[d["id"]] = d
    except Exception:
        logger.exception("load_all_relations failed")
    return out


async def create_relation(d: dict) -> dict:
    kw = dict_to_kwargs(RequirementRelationRow, d)
    for key in ("study_id", "kind", "source_kind", "source_id", "target_kind", "target_id"):
        if not kw.get(key):
            raise ValueError(f"{key} is required")
    if kw["kind"] not in RELATION_KINDS:
        raise ValueError(f"kind must be one of {RELATION_KINDS}")
    for key in ("source_kind", "target_kind"):
        if kw[key] not in ENTITY_KINDS:
            raise ValueError(f"{key} must be one of {ENTITY_KINDS}")
    if (kw["source_kind"], kw["source_id"]) == (kw["target_kind"], kw["target_id"]):
        raise ValueError("A relation cannot link an entity to itself")
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(RequirementRelationRow).where(
                RequirementRelationRow.kind == kw["kind"],
                RequirementRelationRow.source_kind == kw["source_kind"],
                RequirementRelationRow.source_id == kw["source_id"],
                RequirementRelationRow.target_kind == kw["target_kind"],
                RequirementRelationRow.target_id == kw["target_id"],
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            kw.setdefault("id", new_id("rel"))
            row = RequirementRelationRow(**kw)
            session.add(row)
        else:
            row.deleted_at = None
            row.study_id = kw["study_id"]
            if kw.get("rationale"):
                row.rationale = kw["rationale"]
            if kw.get("external_id"):
                row.external_id = kw["external_id"]
        await session.commit()
        return row_to_dict(row)


async def get_relation(relation_id: str) -> dict | None:
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, RequirementRelationRow, relation_id)
        return row_to_dict(row) if row else None


async def soft_delete_relation(relation_id: str) -> bool:
    return await soft_delete_row(RequirementRelationRow, relation_id)


async def list_relations_by_study(study_id: str, kind: str | None = None) -> list[dict]:
    filters = [RequirementRelationRow.study_id == study_id]
    if kind:
        filters.append(RequirementRelationRow.kind == kind)
    return await list_rows(RequirementRelationRow, *filters)


async def list_relations_for(entity_kind: str, entity_id: str, kind: str | None = None,
                             direction: str = "both") -> list[dict]:
    """Relations touching an entity. ``direction``: 'out' (entity is source),
    'in' (entity is target) or 'both'."""
    as_source = and_(RequirementRelationRow.source_kind == entity_kind,
                     RequirementRelationRow.source_id == entity_id)
    as_target = and_(RequirementRelationRow.target_kind == entity_kind,
                     RequirementRelationRow.target_id == entity_id)
    if direction == "out":
        cond = as_source
    elif direction == "in":
        cond = as_target
    else:
        cond = or_(as_source, as_target)
    filters = [cond]
    if kind:
        filters.append(RequirementRelationRow.kind == kind)
    return await list_rows(RequirementRelationRow, *filters)


async def sync_relations(study_id: str, wanted: list[dict], owned: set[tuple[str, str, str]]) -> tuple[int, int]:
    """Bulk upsert in one transaction (requirement import).

    ``wanted``: relation dicts (kind, source_kind, source_id, target_kind, target_id, rationale?).
    ``owned``: (kind, source_id, target_kind) groups the caller manages: a live relation of the
    study in one of these groups that is not in ``wanted`` is soft-deleted. Returns
    (created or revived, removed)."""
    from datetime import datetime, timedelta, timezone
    factory = get_session_factory()
    created = removed = 0
    t0 = datetime.now(timezone.utc)
    async with factory() as session:
        rows = (await session.execute(select(RequirementRelationRow).where(
            RequirementRelationRow.study_id == study_id))).scalars().all()
        have = {(r.kind, r.source_kind, r.source_id, r.target_kind, r.target_id): r for r in rows}
        want_keys = set()
        for d in wanted:
            key = (d["kind"], d["source_kind"], d["source_id"], d["target_kind"], d["target_id"])
            if key in want_keys:
                continue
            want_keys.add(key)
            if d["kind"] not in RELATION_KINDS or d["source_kind"] not in ENTITY_KINDS \
                    or d["target_kind"] not in ENTITY_KINDS:
                raise ValueError(f"invalid relation {key}")
            row = have.get(key)
            if row is None:
                # explicit, increasing creation times keep the file order of further parents/objectives
                session.add(RequirementRelationRow(**dict_to_kwargs(RequirementRelationRow, {
                    "id": new_id("rel"), "study_id": study_id, **d,
                    "created_at": t0 + timedelta(microseconds=len(want_keys))})))
                created += 1
            elif row.deleted_at is not None:
                row.deleted_at = None
                created += 1
        now = datetime.now(timezone.utc)
        for key, row in have.items():
            if row.deleted_at is None and key not in want_keys and (key[0], key[2], key[3]) in owned:
                row.deleted_at = now
                removed += 1
        await session.commit()
    return created, removed


async def sync_incoming(study_id: str, kind: str, source_kind: str, target_kind: str,
                        wanted: set[tuple[str, str]], managed_targets: set[str],
                        rationale: str = "") -> tuple[int, int]:
    """Make the ``kind`` relations ``source_kind`` → ``target_kind`` exact for the targets in
    ``managed_targets`` (wave 3, 3.R1: the functions that satisfy a requirement). ``wanted``
    holds (source id, target id) pairs. Relations to other targets are untouched. Returns
    (created or revived, removed)."""
    from datetime import datetime, timezone
    factory = get_session_factory()
    created = removed = 0
    async with factory() as session:
        rows = (await session.execute(select(RequirementRelationRow).where(
            RequirementRelationRow.study_id == study_id, RequirementRelationRow.kind == kind,
            RequirementRelationRow.source_kind == source_kind,
            RequirementRelationRow.target_kind == target_kind))).scalars().all()
        have = {(r.source_id, r.target_id): r for r in rows}
        for key in sorted(wanted):
            row = have.get(key)
            if row is None:
                session.add(RequirementRelationRow(**dict_to_kwargs(RequirementRelationRow, {
                    "id": new_id("rel"), "study_id": study_id, "kind": kind, "source_kind": source_kind,
                    "source_id": key[0], "target_kind": target_kind, "target_id": key[1],
                    "rationale": rationale or ""})))
                created += 1
            elif row.deleted_at is not None:
                row.deleted_at = None
                created += 1
        now = datetime.now(timezone.utc)
        for key, row in have.items():
            if row.deleted_at is None and key[1] in managed_targets and key not in wanted:
                row.deleted_at = now
                removed += 1
        await session.commit()
    return created, removed
