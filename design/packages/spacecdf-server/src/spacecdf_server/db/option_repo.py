"""Async repository for design options (SCDF-172, ECSS-E-TM-10-25 *Option*).

Semantics
---------
* The **baseline** of a study is *not* an ``OptionRow``: it is the set of
  ``ElementParameterRow`` rows whose ``option_id IS NULL``. ``ensure_baseline``
  lazily creates one ``OptionRow(is_baseline=True, name="Baseline")`` so the
  UI has something to select and compare against; reads/writes for it are
  routed to ``option_id=None``.
* An option row ``(element, definition, option_id=X)`` **shadows** the
  baseline row of the same (element, definition) when reading option X.
  Reads for X = baseline ∪ X-overrides; writing with ``option_id=X``
  creates/updates the X row and never the baseline (``parameter_repo``).
* ``branch_option(study_id, from_option_id, name)`` copies every override row
  of ``from`` into the new option. Branching from the baseline copies nothing
  (the baseline *is* the NULL rows, which every option already sees).
* Elements / interfaces / requirements are **not** cloned per option (design
  doc §1.4 limit). ``analysis_runs`` / ``analysis_conflicts`` are option-scoped.
* Delete is soft (``deleted_at``); the option's override rows are soft-deleted
  with it. The baseline option cannot be deleted.

Public API:
    ensure_baseline(study_id) -> dict
    create_option(study_id, name, description="", branched_from_option_id=None) -> dict
    list_options(study_id) -> list[dict]           baseline first, then by created_at
    get_option(option_id) -> dict | None
    update_option(option_id, updates) -> dict
    soft_delete_option(option_id) -> bool
    branch_option(study_id, from_option_id, name, description="") -> dict   (+ ``copied``)
    list_option_overrides(study_id, option_id) -> list[dict]
    resolve_option_id(option_id) -> str | None     baseline option id -> None
"""
from __future__ import annotations

import logging

from sqlalchemy import select

from ._arcadia_common import (
    apply_update, get_row, get_session_factory, list_rows, new_id, row_to_dict, utcnow,
)
from .models import ElementParameterRow, OptionRow

logger = logging.getLogger(__name__)

BASELINE_NAME = "Baseline"


def _validate_name(name: str | None) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("option name is required")
    return name[:128]


async def ensure_baseline(study_id: str) -> dict:
    """Return the study's baseline option, creating it on first use."""
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(OptionRow).where(OptionRow.study_id == study_id, OptionRow.is_baseline.is_(True),
                                    OptionRow.deleted_at.is_(None)).order_by(OptionRow.created_at)
        )
        row = result.scalars().first()
        if row is None:
            row = OptionRow(id=new_id("opt"), study_id=study_id, name=BASELINE_NAME,
                            description="Baseline (parameter rows without option)", is_baseline=True)
            session.add(row)
            await session.commit()
        return row_to_dict(row)


async def create_option(study_id: str, name: str, description: str = "",
                        branched_from_option_id: str | None = None) -> dict:
    if not study_id:
        raise ValueError("study_id is required")
    name = _validate_name(name)
    await ensure_baseline(study_id)
    factory = get_session_factory()
    async with factory() as session:
        row = OptionRow(id=new_id("opt"), study_id=study_id, name=name, description=description or "",
                        is_baseline=False, branched_from_option_id=branched_from_option_id)
        session.add(row)
        await session.commit()
        return row_to_dict(row)


async def list_options(study_id: str) -> list[dict]:
    await ensure_baseline(study_id)
    rows = await list_rows(OptionRow, OptionRow.study_id == study_id, order_by=OptionRow.created_at)
    rows.sort(key=lambda r: (0 if r.get("is_baseline") else 1, r.get("created_at") or ""))
    return rows


async def get_option(option_id: str) -> dict | None:
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, OptionRow, option_id)
        return row_to_dict(row) if row else None


async def update_option(option_id: str, updates: dict) -> dict:
    updates = {k: v for k, v in dict(updates).items() if k in ("name", "description")}
    if "name" in updates:
        updates["name"] = _validate_name(updates["name"])
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, OptionRow, option_id)
        if row is None:
            raise ValueError(f"Option '{option_id}' not found")
        if row.is_baseline and "name" in updates:
            updates.pop("name")        # the baseline keeps its name
        apply_update(row, updates, immutable=("id", "study_id", "is_baseline",
                                              "branched_from_option_id", "created_at"))
        await session.commit()
        return row_to_dict(row)


async def soft_delete_option(option_id: str) -> bool:
    """Soft-delete the option and its override rows. Baseline: refused (False)."""
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, OptionRow, option_id)
        if row is None or row.is_baseline:
            return False
        now = utcnow()
        row.deleted_at = now
        result = await session.execute(
            select(ElementParameterRow).where(ElementParameterRow.option_id == option_id,
                                              ElementParameterRow.deleted_at.is_(None))
        )
        for p in result.scalars():
            p.deleted_at = now
        await session.commit()
        return True


async def resolve_option_id(option_id: str | None) -> str | None:
    """Map the baseline option's id (or None/'') to ``None`` — the parameter
    layer addresses the baseline as ``option_id IS NULL``."""
    if not option_id:
        return None
    opt = await get_option(option_id)
    if opt is None:
        raise ValueError(f"Option '{option_id}' not found")
    return None if opt.get("is_baseline") else option_id


async def list_option_overrides(study_id: str, option_id: str) -> list[dict]:
    """The option's own rows (no baseline). Empty for the baseline option and
    for unknown / deleted options."""
    try:
        scoped = await resolve_option_id(option_id)
    except ValueError:
        return []
    if scoped is None:
        return []
    return await list_rows(ElementParameterRow, ElementParameterRow.study_id == study_id,
                           ElementParameterRow.option_id == scoped)


async def branch_option(study_id: str, from_option_id: str | None, name: str,
                        description: str = "") -> dict:
    """New option carrying a copy of ``from``'s override rows.

    ``from_option_id`` None / baseline → nothing to copy (baseline rows are
    shared). Returns the option dict plus ``copied`` (number of rows copied).
    """
    source = await resolve_option_id(from_option_id)
    new = await create_option(study_id, name, description, branched_from_option_id=from_option_id or None)
    copied = 0
    if source is not None:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(
                select(ElementParameterRow).where(ElementParameterRow.study_id == study_id,
                                                  ElementParameterRow.option_id == source,
                                                  ElementParameterRow.deleted_at.is_(None))
            )
            for src in result.scalars():
                session.add(ElementParameterRow(
                    id=new_id("ep"), study_id=src.study_id, element_id=src.element_id,
                    definition_id=src.definition_id, owner_domain=src.owner_domain,
                    manual_value=src.manual_value, computed_value=src.computed_value,
                    reference_value=src.reference_value, value_switch=src.value_switch,
                    formula=src.formula, formula_kind=src.formula_kind, option_id=new["id"],
                    iteration=src.iteration, version=1,
                ))
                copied += 1
            await session.commit()
    new["copied"] = copied
    return new
