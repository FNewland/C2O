"""Async repository for DesignElement and ElementInterface persistence.

Write-through cache: the in-memory dicts in elements.py are the primary
read path; this module ensures durability by mirroring every mutation
to the database. On startup, existing rows are loaded back into memory.

All DB errors are logged and swallowed so the hot path never crashes.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select, update as sa_update

from .engine import get_engine, get_session_factory
from .models import Base, DesignElementRow, ElementInterfaceRow

logger = logging.getLogger(__name__)


# ── Column mapping helpers ──────────────────────────────────────────────
# The in-memory dicts use flat keys (e.g. "performance", "dimensions",
# "properties") while the ORM columns use _json suffixes.

_ELEMENT_JSON_FIELDS = {
    "performance": "performance_json",
    "dimensions_mm": "dimensions_json",
}

_INTERFACE_JSON_FIELDS = {
    "properties": "properties_json",
}


def _dict_to_element_row_kwargs(d: dict) -> dict:
    """Convert an in-memory element dict to DesignElementRow column kwargs."""
    skip = {"children"}
    kw = {}
    for k, v in d.items():
        if k in skip:
            continue
        col = _ELEMENT_JSON_FIELDS.get(k, k)
        # Only set columns that actually exist on the model
        if hasattr(DesignElementRow, col):
            kw[col] = v
    return kw


def _element_row_to_dict(row: DesignElementRow) -> dict:
    """Convert a DesignElementRow to the flat dict format used in-memory."""
    d: dict = {}
    for c in DesignElementRow.__table__.columns:
        val = getattr(row, c.key)
        d[c.key] = val
    # Re-map JSON columns to the API-level keys
    d["performance"] = d.pop("performance_json", None)
    d["dimensions_mm"] = d.pop("dimensions_json", None)
    # deleted_at: keep as ISO string or None for consistency with router
    if d.get("deleted_at") and isinstance(d["deleted_at"], datetime):
        d["deleted_at"] = d["deleted_at"].isoformat()
    return d


def _dict_to_interface_row_kwargs(d: dict) -> dict:
    skip = {"children"}
    kw = {}
    for k, v in d.items():
        if k in skip:
            continue
        col = _INTERFACE_JSON_FIELDS.get(k, k)
        if hasattr(ElementInterfaceRow, col):
            kw[col] = v
    return kw


def _interface_row_to_dict(row: ElementInterfaceRow) -> dict:
    d: dict = {}
    for c in ElementInterfaceRow.__table__.columns:
        val = getattr(row, c.key)
        d[c.key] = val
    d["properties"] = d.pop("properties_json", None)
    if d.get("deleted_at") and isinstance(d["deleted_at"], datetime):
        d["deleted_at"] = d["deleted_at"].isoformat()
    return d


# ── Public API ──────────────────────────────────────────────────────────

async def load_all_elements() -> tuple[dict[str, dict], dict[str, dict]]:
    """Load all non-deleted elements and interfaces from DB into dicts.

    Returns (elements_dict, interfaces_dict) keyed by id.
    """
    elements: dict[str, dict] = {}
    interfaces: dict[str, dict] = {}
    try:
        factory = get_session_factory()
        async with factory() as session:
            # Elements — exclude soft-deleted
            result = await session.execute(
                select(DesignElementRow).where(DesignElementRow.deleted_at.is_(None))
            )
            for row in result.scalars():
                d = _element_row_to_dict(row)
                elements[d["id"]] = d

            # Interfaces — exclude soft-deleted
            result = await session.execute(
                select(ElementInterfaceRow).where(ElementInterfaceRow.deleted_at.is_(None))
            )
            for row in result.scalars():
                d = _interface_row_to_dict(row)
                interfaces[d["id"]] = d

        logger.info(
            "Loaded %d elements and %d interfaces from DB",
            len(elements), len(interfaces),
        )
    except Exception:
        logger.exception("Failed to load elements from DB — starting with empty cache")
    return elements, interfaces


async def db_create_element(element_dict: dict) -> None:
    """Persist a new element to the database."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            row = DesignElementRow(**_dict_to_element_row_kwargs(element_dict))
            session.add(row)
            await session.commit()
    except Exception:
        logger.exception("db_create_element failed for %s", element_dict.get("id"))


async def db_update_element(element_id: str, full_dict: dict) -> None:
    """Update an existing element row with the full current state."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            kw = _dict_to_element_row_kwargs(full_dict)
            kw.pop("id", None)  # Don't update PK
            kw["updated_at"] = datetime.now(timezone.utc)
            stmt = (
                sa_update(DesignElementRow)
                .where(DesignElementRow.id == element_id)
                .values(**kw)
            )
            await session.execute(stmt)
            await session.commit()
    except Exception:
        logger.exception("db_update_element failed for %s", element_id)


async def db_soft_delete_element(element_id: str, deleted_at_iso: str) -> None:
    """Set deleted_at on an element row."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = (
                sa_update(DesignElementRow)
                .where(DesignElementRow.id == element_id)
                .values(deleted_at=datetime.fromisoformat(deleted_at_iso))
            )
            await session.execute(stmt)
            await session.commit()
    except Exception:
        logger.exception("db_soft_delete_element failed for %s", element_id)


async def db_create_interface(interface_dict: dict) -> None:
    """Persist a new interface to the database."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            row = ElementInterfaceRow(**_dict_to_interface_row_kwargs(interface_dict))
            session.add(row)
            await session.commit()
    except Exception:
        logger.exception("db_create_interface failed for %s", interface_dict.get("id"))


async def db_soft_delete_interface(interface_id: str, deleted_at_iso: str) -> None:
    """Set deleted_at on an interface row."""
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = (
                sa_update(ElementInterfaceRow)
                .where(ElementInterfaceRow.id == interface_id)
                .values(deleted_at=datetime.fromisoformat(deleted_at_iso))
            )
            await session.execute(stmt)
            await session.commit()
    except Exception:
        logger.exception("db_soft_delete_interface failed for %s", interface_id)


async def db_bulk_create_elements(element_dicts: list[dict]) -> None:
    """Persist multiple elements in a single transaction (used by seed)."""
    if not element_dicts:
        return
    try:
        factory = get_session_factory()
        async with factory() as session:
            for d in element_dicts:
                session.add(DesignElementRow(**_dict_to_element_row_kwargs(d)))
            await session.commit()
        logger.info("Bulk-created %d elements in DB", len(element_dicts))
    except Exception:
        logger.exception("db_bulk_create_elements failed (%d items)", len(element_dicts))


async def db_bulk_create_interfaces(interface_dicts: list[dict]) -> None:
    """Persist multiple interfaces in a single transaction (used by seed)."""
    if not interface_dicts:
        return
    try:
        factory = get_session_factory()
        async with factory() as session:
            for d in interface_dicts:
                session.add(ElementInterfaceRow(**_dict_to_interface_row_kwargs(d)))
            await session.commit()
        logger.info("Bulk-created %d interfaces in DB", len(interface_dicts))
    except Exception:
        logger.exception("db_bulk_create_interfaces failed (%d items)", len(interface_dicts))


async def db_upsert_budget_allocation(alloc: dict) -> None:
    """Persist a budget allocation to DB (upsert by element_id + budget_type)."""
    from .models import BudgetAllocationRow
    try:
        factory = get_session_factory()
        async with factory() as session:
            # Delete existing for same element + type
            from sqlalchemy import delete
            await session.execute(
                delete(BudgetAllocationRow).where(
                    BudgetAllocationRow.element_id == alloc["element_id"],
                    BudgetAllocationRow.budget_type == alloc["budget_type"],
                )
            )
            session.add(BudgetAllocationRow(
                study_id=alloc["study_id"],
                element_id=alloc["element_id"],
                budget_type=alloc["budget_type"],
                allocation_value=alloc["allocation_value"],
                unit=alloc.get("unit", ""),
                source=alloc.get("source", "manual"),
                rationale=alloc.get("rationale", ""),
            ))
            await session.commit()
        logger.info("Persisted budget allocation %s/%s", alloc["element_id"], alloc["budget_type"])
    except Exception:
        logger.exception("db_upsert_budget_allocation failed")
