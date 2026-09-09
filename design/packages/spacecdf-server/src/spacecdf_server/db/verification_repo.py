"""Async repository for verification items (SCDF-175, design SCDF-170 §2.3).

Dict-in / dict-out like the other arcadia repos (``_arcadia_common``):
``list_*`` / ``get_*`` never raise (log + empty), writers raise ``ValueError``
on not-found.

Public API:
    create_item(d)                                   -> dict
    get_item(item_id)                                -> dict | None
    get_by_requirement(study_id, requirement_id)     -> dict | None
    list_by_study(study_id)                          -> list[dict]
    list_by_requirement(requirement_id)              -> list[dict]
    update_item(item_id, updates, *, by_user=False)  -> dict   (by_user stamps edited_by_user)
    upsert_generated(item)                           -> dict   (never overwrites a user-edited row's
                                                                filled fields; fills empty ones only)
    set_status(item_id, status, evidence_ref=None)   -> dict
    soft_delete_item(item_id)                        -> bool

``upsert_generated`` is the generator's write path: for a row that the user
has touched (``edited_by_user=True``) only *empty* columns are filled; the
user's method / level / phase / facility / acceptance / status / evidence
are never displaced by a re-run.
"""
from __future__ import annotations

import logging

from sqlalchemy import select

from ._arcadia_common import (
    dict_to_kwargs, get_row, get_session_factory, list_rows, new_id, row_to_dict, soft_delete_row, utcnow,
)
from .models import VerificationItemRow

logger = logging.getLogger(__name__)

METHODS = ("A", "T", "I", "R", "D")
LEVELS = ("unit", "subsystem", "system", "segment")
PHASES = ("PDR", "CDR", "QR", "AR")
STATUSES = ("planned", "in_progress", "passed", "failed", "waived")

#: Columns the generator may fill; on user-edited rows they are only written when empty.
GENERATED_FIELDS = ("method", "level", "phase", "facility", "procedure_ref", "acceptance_criterion",
                    "status", "evidence_ref")


def _validate(kw: dict) -> None:
    if kw.get("method") is not None and kw["method"] not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    if kw.get("level") is not None and kw["level"] not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}")
    if kw.get("phase") is not None and kw["phase"] not in PHASES:
        raise ValueError(f"phase must be one of {PHASES}")
    if kw.get("status") is not None and kw["status"] not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")


async def create_item(d: dict) -> dict:
    kw = dict_to_kwargs(VerificationItemRow, d)
    for key in ("study_id", "requirement_id"):
        if not kw.get(key):
            raise ValueError(f"{key} is required")
    _validate(kw)
    kw.setdefault("id", new_id("vi"))
    kw.setdefault("status", "planned")
    kw.setdefault("notes", "")
    factory = get_session_factory()
    async with factory() as session:
        row = VerificationItemRow(**kw)
        session.add(row)
        await session.commit()
        return row_to_dict(row)


async def get_item(item_id: str) -> dict | None:
    try:
        factory = get_session_factory()
        async with factory() as session:
            row = await get_row(session, VerificationItemRow, item_id)
            return row_to_dict(row) if row else None
    except Exception:
        logger.exception("get_item failed for %s", item_id)
        return None


async def get_by_requirement(study_id: str, requirement_id: str) -> dict | None:
    rows = await list_rows(VerificationItemRow, VerificationItemRow.study_id == study_id,
                           VerificationItemRow.requirement_id == requirement_id,
                           order_by=VerificationItemRow.created_at)
    return rows[0] if rows else None


async def list_by_study(study_id: str) -> list[dict]:
    return await list_rows(VerificationItemRow, VerificationItemRow.study_id == study_id,
                           order_by=VerificationItemRow.created_at)


async def list_by_requirement(requirement_id: str) -> list[dict]:
    return await list_rows(VerificationItemRow, VerificationItemRow.requirement_id == requirement_id,
                           order_by=VerificationItemRow.created_at)


async def update_item(item_id: str, updates: dict, *, by_user: bool = False) -> dict:
    """Apply ``updates``; ``by_user=True`` stamps ``edited_by_user`` so later
    generator runs leave the row's filled fields alone."""
    kw = dict_to_kwargs(VerificationItemRow, updates)
    for key in ("id", "study_id", "requirement_id", "created_at", "deleted_at"):
        kw.pop(key, None)
    _validate(kw)
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, VerificationItemRow, item_id)
        if row is None:
            raise ValueError(f"Verification item {item_id} not found")
        for k, v in kw.items():
            setattr(row, k, v)
        if by_user:
            row.edited_by_user = True
        row.updated_at = utcnow()
        await session.commit()
        return row_to_dict(row)


async def set_status(item_id: str, status: str, evidence_ref: str | None = None) -> dict:
    updates: dict = {"status": status}
    if evidence_ref is not None:
        updates["evidence_ref"] = evidence_ref
    return await update_item(item_id, updates)


async def upsert_generated(item: dict) -> dict:
    """Create or refresh the (study, requirement) item from generator output.

    * no row yet → created with ``item`` as given;
    * row with ``edited_by_user=False`` → generated fields overwritten, except
      ``status`` / ``evidence_ref`` which are kept once the item has left
      ``planned`` (closure evidence is not planning data);
    * row with ``edited_by_user=True`` → only empty generated fields are filled.
    """
    study_id, requirement_id = item.get("study_id"), item.get("requirement_id")
    if not study_id or not requirement_id:
        raise ValueError("study_id and requirement_id are required")
    kw = dict_to_kwargs(VerificationItemRow, item)
    _validate(kw)
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(VerificationItemRow).where(
                VerificationItemRow.study_id == study_id,
                VerificationItemRow.requirement_id == requirement_id,
                VerificationItemRow.deleted_at.is_(None),
            ).order_by(VerificationItemRow.created_at)
        )
        row = result.scalars().first()
        if row is None:
            kw.setdefault("id", new_id("vi"))
            kw.setdefault("status", "planned")
            kw.setdefault("notes", "")
            row = VerificationItemRow(**kw)
            session.add(row)
        else:
            for f in GENERATED_FIELDS:
                if f not in kw:
                    continue
                current = getattr(row, f)
                if row.edited_by_user:
                    if current in (None, ""):
                        setattr(row, f, kw[f])
                elif f in ("status", "evidence_ref"):
                    if (row.status or "planned") == "planned" and current in (None, "", "planned"):
                        setattr(row, f, kw[f])
                else:
                    setattr(row, f, kw[f])
            row.updated_at = utcnow()
        await session.commit()
        return row_to_dict(row)


async def soft_delete_item(item_id: str) -> bool:
    return await soft_delete_row(VerificationItemRow, item_id)
