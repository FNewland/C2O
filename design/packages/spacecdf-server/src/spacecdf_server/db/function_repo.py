"""Async repository for functions, ports, allocations, functional exchanges and
realizations (SCDF-160 §1.1). Dict-in / dict-out; see ``_arcadia_common``.

Public API (what routers / services should call):

    load_all_functions(study_id=None)          -> dict[id, dict]
    load_all_function_ports(study_id=None)     -> dict[id, dict]
    load_all_function_allocations(study_id)    -> dict[id, dict]
    load_all_functional_exchanges(study_id)    -> dict[id, dict]
    load_all_realizations(study_id)            -> dict[id, dict]

    create_function(d) / get_function(id) / update_function(id, updates, expected_version)
    soft_delete_function(id) / list_functions_by_study(study_id, layer=None)
    list_function_children(parent_id)

    create_function_port(d) / update_function_port(id, updates) / soft_delete_function_port(id)
    list_ports_by_function(function_id)

    allocate_function(study_id, function_id, element_id, layer="SA")   (upsert per function+layer)
    unallocate_function(function_id, layer="SA")
    list_allocations_by_study(study_id) / list_allocations_by_function(function_id)
    list_allocations_by_element(element_id)

    create_functional_exchange(d) / update_functional_exchange(id, updates, expected_version)
    soft_delete_functional_exchange(id) / list_functional_exchanges_by_study(study_id)

    create_realization(d)  (idempotent on source/target)  / soft_delete_realization(id)
    list_realizations_by_study(study_id) / list_realizations_for(kind, entity_id)
"""
from __future__ import annotations

import logging

from sqlalchemy import select

from ._arcadia_common import (
    apply_update, dict_to_kwargs, get_row, get_session_factory, list_rows,
    new_id, row_to_dict, soft_delete_row, utcnow,
)
from .models import (
    FunctionAllocationRow, FunctionPortRow, FunctionRow, FunctionalExchangeRow,
    RealizationRow,
)

logger = logging.getLogger(__name__)


# ── Loaders ─────────────────────────────────────────────────────────────

async def _load_all(model, study_id: str | None, study_col=None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(model)
            if hasattr(model, "deleted_at"):
                stmt = stmt.where(model.deleted_at.is_(None))
            if study_id is not None and study_col is not None:
                stmt = stmt.where(study_col == study_id)
            result = await session.execute(stmt)
            for row in result.scalars():
                d = row_to_dict(row)
                out[d["id"]] = d
    except Exception:
        logger.exception("load_all failed for %s", model.__tablename__)
    return out


async def load_all_functions(study_id: str | None = None) -> dict[str, dict]:
    return await _load_all(FunctionRow, study_id, FunctionRow.study_id)


async def load_all_function_ports(study_id: str | None = None) -> dict[str, dict]:
    """Ports have no study_id column; filter through their function when asked."""
    out: dict[str, dict] = {}
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(FunctionPortRow).where(FunctionPortRow.deleted_at.is_(None))
            if study_id is not None:
                stmt = stmt.join(FunctionRow, FunctionRow.id == FunctionPortRow.function_id).where(
                    FunctionRow.study_id == study_id
                )
            result = await session.execute(stmt)
            for row in result.scalars():
                d = row_to_dict(row)
                out[d["id"]] = d
    except Exception:
        logger.exception("load_all_function_ports failed")
    return out


async def load_all_function_allocations(study_id: str | None = None) -> dict[str, dict]:
    return await _load_all(FunctionAllocationRow, study_id, FunctionAllocationRow.study_id)


async def load_all_functional_exchanges(study_id: str | None = None) -> dict[str, dict]:
    return await _load_all(FunctionalExchangeRow, study_id, FunctionalExchangeRow.study_id)


async def load_all_realizations(study_id: str | None = None) -> dict[str, dict]:
    return await _load_all(RealizationRow, study_id, RealizationRow.study_id)


# ── Functions ───────────────────────────────────────────────────────────

async def create_function(d: dict) -> dict:
    kw = dict_to_kwargs(FunctionRow, d)
    kw.setdefault("id", new_id("fn"))
    if not kw.get("study_id"):
        raise ValueError("study_id is required")
    if not kw.get("name"):
        raise ValueError("name is required")
    factory = get_session_factory()
    async with factory() as session:
        row = FunctionRow(**kw)
        session.add(row)
        await session.commit()
        return row_to_dict(row)


async def get_function(function_id: str, *, include_deleted: bool = False) -> dict | None:
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, FunctionRow, function_id, include_deleted=include_deleted)
        return row_to_dict(row) if row else None


async def update_function(function_id: str, updates: dict, expected_version: int | None = None) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, FunctionRow, function_id)
        if row is None:
            raise ValueError(f"Function '{function_id}' not found")
        if updates.get("parent_id") == function_id:
            raise ValueError("A function cannot be its own parent")
        apply_update(row, updates, expected_version=expected_version)
        await session.commit()
        return row_to_dict(row)


async def soft_delete_function(function_id: str) -> bool:
    return await soft_delete_row(FunctionRow, function_id)


async def list_functions_by_study(study_id: str, layer: str | None = None,
                                  include_deleted: bool = False) -> list[dict]:
    filters = [FunctionRow.study_id == study_id]
    if layer:
        filters.append(FunctionRow.layer == layer)
    return await list_rows(FunctionRow, *filters, include_deleted=include_deleted,
                           order_by=FunctionRow.level)


async def list_function_children(parent_id: str) -> list[dict]:
    return await list_rows(FunctionRow, FunctionRow.parent_id == parent_id, order_by=FunctionRow.name)


# ── Ports ───────────────────────────────────────────────────────────────

async def create_function_port(d: dict) -> dict:
    kw = dict_to_kwargs(FunctionPortRow, d)
    kw.setdefault("id", new_id("fp"))
    if not kw.get("function_id"):
        raise ValueError("function_id is required")
    if kw.get("direction", "out") not in ("in", "out"):
        raise ValueError("direction must be 'in' or 'out'")
    factory = get_session_factory()
    async with factory() as session:
        if await get_row(session, FunctionRow, kw["function_id"]) is None:
            raise ValueError(f"Function '{kw['function_id']}' not found")
        row = FunctionPortRow(**kw)
        session.add(row)
        await session.commit()
        return row_to_dict(row)


async def update_function_port(port_id: str, updates: dict) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, FunctionPortRow, port_id)
        if row is None:
            raise ValueError(f"Function port '{port_id}' not found")
        apply_update(row, updates, immutable=("id", "function_id", "created_at"))
        await session.commit()
        return row_to_dict(row)


async def soft_delete_function_port(port_id: str) -> bool:
    return await soft_delete_row(FunctionPortRow, port_id)


async def list_ports_by_function(function_id: str) -> list[dict]:
    return await list_rows(FunctionPortRow, FunctionPortRow.function_id == function_id,
                           order_by=FunctionPortRow.name)


# ── Allocations ─────────────────────────────────────────────────────────

async def allocate_function(study_id: str, function_id: str, element_id: str, layer: str = "SA") -> dict:
    """Upsert the allocation of ``function_id`` for ``layer`` (unique per function+layer)."""
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(FunctionAllocationRow).where(
                FunctionAllocationRow.function_id == function_id,
                FunctionAllocationRow.layer == layer,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = FunctionAllocationRow(
                id=new_id("fa"), study_id=study_id, function_id=function_id,
                element_id=element_id, layer=layer,
            )
            session.add(row)
        else:
            row.element_id = element_id
            row.study_id = study_id
        await session.commit()
        return row_to_dict(row)


async def unallocate_function(function_id: str, layer: str = "SA") -> bool:
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(FunctionAllocationRow).where(
                FunctionAllocationRow.function_id == function_id,
                FunctionAllocationRow.layer == layer,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await session.delete(row)
        await session.commit()
        return True


async def list_allocations_by_study(study_id: str) -> list[dict]:
    return await list_rows(FunctionAllocationRow, FunctionAllocationRow.study_id == study_id)


async def list_allocations_by_function(function_id: str) -> list[dict]:
    return await list_rows(FunctionAllocationRow, FunctionAllocationRow.function_id == function_id)


async def list_allocations_by_element(element_id: str) -> list[dict]:
    return await list_rows(FunctionAllocationRow, FunctionAllocationRow.element_id == element_id)


# ── Functional exchanges ────────────────────────────────────────────────

async def create_functional_exchange(d: dict) -> dict:
    kw = dict_to_kwargs(FunctionalExchangeRow, d)
    kw.setdefault("id", new_id("fx"))
    for key in ("study_id", "from_port_id", "to_port_id"):
        if not kw.get(key):
            raise ValueError(f"{key} is required")
    if kw["from_port_id"] == kw["to_port_id"]:
        raise ValueError("from_port_id and to_port_id must differ")
    factory = get_session_factory()
    async with factory() as session:
        for key in ("from_port_id", "to_port_id"):
            if await get_row(session, FunctionPortRow, kw[key]) is None:
                raise ValueError(f"Function port '{kw[key]}' not found")
        row = FunctionalExchangeRow(**kw)
        session.add(row)
        await session.commit()
        return row_to_dict(row)


async def update_functional_exchange(exchange_id: str, updates: dict,
                                     expected_version: int | None = None) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, FunctionalExchangeRow, exchange_id)
        if row is None:
            raise ValueError(f"Functional exchange '{exchange_id}' not found")
        apply_update(row, updates, expected_version=expected_version)
        await session.commit()
        return row_to_dict(row)


async def soft_delete_functional_exchange(exchange_id: str) -> bool:
    return await soft_delete_row(FunctionalExchangeRow, exchange_id)


async def list_functional_exchanges_by_study(study_id: str) -> list[dict]:
    return await list_rows(FunctionalExchangeRow, FunctionalExchangeRow.study_id == study_id,
                           order_by=FunctionalExchangeRow.name)


# ── Realizations ────────────────────────────────────────────────────────

async def create_realization(d: dict) -> dict:
    """Create (or revive) the realization link; idempotent on (source, target)."""
    kw = dict_to_kwargs(RealizationRow, d)
    for key in ("study_id", "source_kind", "source_id", "target_kind", "target_id"):
        if not kw.get(key):
            raise ValueError(f"{key} is required")
    if kw["source_kind"] not in ("function", "element") or kw["target_kind"] not in ("function", "element"):
        raise ValueError("source_kind/target_kind must be 'function' or 'element'")
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(RealizationRow).where(
                RealizationRow.source_kind == kw["source_kind"],
                RealizationRow.source_id == kw["source_id"],
                RealizationRow.target_kind == kw["target_kind"],
                RealizationRow.target_id == kw["target_id"],
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            kw.setdefault("id", new_id("rz"))
            row = RealizationRow(**kw)
            session.add(row)
        else:
            row.deleted_at = None
            row.study_id = kw["study_id"]
        await session.commit()
        return row_to_dict(row)


async def soft_delete_realization(realization_id: str) -> bool:
    return await soft_delete_row(RealizationRow, realization_id)


async def list_realizations_by_study(study_id: str) -> list[dict]:
    return await list_rows(RealizationRow, RealizationRow.study_id == study_id)


async def list_realizations_for(kind: str, entity_id: str) -> list[dict]:
    """All active realizations where the entity is source *or* target."""
    from sqlalchemy import and_, or_
    return await list_rows(
        RealizationRow,
        or_(
            and_(RealizationRow.source_kind == kind, RealizationRow.source_id == entity_id),
            and_(RealizationRow.target_kind == kind, RealizationRow.target_id == entity_id),
        ),
    )
