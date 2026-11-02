"""Async repository for exchange items (SCDF-160 §1.2). Dict-in / dict-out.

Public API:
    load_all_exchange_items(study_id=None)      -> dict[id, dict]
    create_exchange_item(d) / get_exchange_item(id)
    update_exchange_item(id, updates, expected_version=None)
    soft_delete_exchange_item(id)
    list_exchange_items_by_study(study_id, kind=None)
    list_exchange_items_by_ids(ids)
"""
from __future__ import annotations

import logging

from sqlalchemy import select

from ._arcadia_common import (
    apply_update, dict_to_kwargs, get_row, get_session_factory, list_rows,
    new_id, row_to_dict, soft_delete_row,
)
from .models import ExchangeItemRow

logger = logging.getLogger(__name__)

from spacecdf_common.models.interface_types import INTERFACE_TYPE_VALUES, canonical_interface_type

# Exchange-item kinds = the canonical interface types (Nov 2026); the frontend's
# old "command"/"signal" kinds are mapped to data / electrical_signal.
EXCHANGE_ITEM_KINDS = INTERFACE_TYPE_VALUES


def canonical_kind(raw: object) -> str | None:
    """Canonical kind for any accepted spelling; ``None`` when unknown."""
    return canonical_interface_type(raw)


async def load_all_exchange_items(study_id: str | None = None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(ExchangeItemRow).where(ExchangeItemRow.deleted_at.is_(None))
            if study_id is not None:
                stmt = stmt.where(ExchangeItemRow.study_id == study_id)
            result = await session.execute(stmt)
            for row in result.scalars():
                d = row_to_dict(row)
                out[d["id"]] = d
    except Exception:
        logger.exception("load_all_exchange_items failed")
    return out


async def create_exchange_item(d: dict) -> dict:
    kw = dict_to_kwargs(ExchangeItemRow, d)
    kw.setdefault("id", new_id("xi"))
    if not kw.get("study_id"):
        raise ValueError("study_id is required")
    if not kw.get("name"):
        raise ValueError("name is required")
    kind = canonical_kind(kw.setdefault("kind", "data")) or kw["kind"]
    kw["kind"] = kind
    if kind not in EXCHANGE_ITEM_KINDS:
        raise ValueError(f"kind must be one of {EXCHANGE_ITEM_KINDS}")
    factory = get_session_factory()
    async with factory() as session:
        row = ExchangeItemRow(**kw)
        session.add(row)
        await session.commit()
        return row_to_dict(row)


async def get_exchange_item(item_id: str, *, include_deleted: bool = False) -> dict | None:
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, ExchangeItemRow, item_id, include_deleted=include_deleted)
        return row_to_dict(row) if row else None


async def update_exchange_item(item_id: str, updates: dict, expected_version: int | None = None) -> dict:
    if "kind" in updates:
        updates = {**updates, "kind": canonical_kind(updates["kind"]) or updates["kind"]}
    if "kind" in updates and updates["kind"] not in EXCHANGE_ITEM_KINDS:
        raise ValueError(f"kind must be one of {EXCHANGE_ITEM_KINDS}")
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, ExchangeItemRow, item_id)
        if row is None:
            raise ValueError(f"Exchange item '{item_id}' not found")
        apply_update(row, updates, expected_version=expected_version)
        await session.commit()
        return row_to_dict(row)


async def soft_delete_exchange_item(item_id: str) -> bool:
    return await soft_delete_row(ExchangeItemRow, item_id)


async def list_exchange_items_by_study(study_id: str, kind: str | None = None) -> list[dict]:
    filters = [ExchangeItemRow.study_id == study_id]
    if kind:
        filters.append(ExchangeItemRow.kind == kind)
    return await list_rows(ExchangeItemRow, *filters, order_by=ExchangeItemRow.name)


async def list_exchange_items_by_ids(ids: list[str]) -> list[dict]:
    if not ids:
        return []
    return await list_rows(ExchangeItemRow, ExchangeItemRow.id.in_(list(ids)))
