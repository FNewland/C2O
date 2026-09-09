"""Async repository for parameter definitions and element parameters (SCDF-160 §1.5).

Public API:
    seed_parameter_definitions(path=None)              -> {"created": n, "updated": n}
    upsert_parameter_definition(d)                      keyed by name
    get_parameter_definition(id) / get_parameter_definition_by_name(name)
    list_parameter_definitions(well_known_only=False)
    load_all_parameter_definitions()                    -> dict[id, dict]

    load_all_element_parameters(study_id=None, option_id=ALL) -> dict[id, dict]
    upsert_element_parameter(d)                         keyed by (element_id, definition_id, iteration, option_id)
    get_element_parameter(id)
    update_element_parameter(id, updates, expected_version=None)
    soft_delete_element_parameter(id)
    list_element_parameters_by_study(study_id, option_id=None)
    list_element_parameters_by_element(element_id, iteration=None, option_id=None)
    overlay_option_rows(rows, option_id)                baseline ∪ option overrides (pure helper)

Option scoping (SCDF-172): the *baseline* is the set of rows with
``option_id IS NULL``. A row with ``option_id = X`` *shadows* the baseline
row for the same (element, definition, iteration) when reading option X.
Reads for option X therefore return baseline ∪ X-overrides (override wins);
writing with ``option_id = X`` creates/updates the X row and never touches
the baseline. ``option_id=None`` everywhere means "baseline" — so existing
callers see exactly what they saw before option rows existed. Well-known
column mirroring (``mirror_well_known_columns`` / ``effective_well_known_values``)
is baseline-only: element columns are not cloned per option.

    mirror_well_known_columns(element_dict)             element row -> parameter rows (non-fatal)
    effective_well_known_values(element_id)             parameter rows -> {column: value}
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select

from spacecdf_common.models.parameters import WELL_KNOWN_PARAMETERS

from ._arcadia_common import (
    apply_update, dict_to_kwargs, get_row, get_session_factory, list_rows,
    new_id, row_to_dict, soft_delete_row, utcnow,
)
from .models import ElementParameterRow, ParameterDefinitionRow

logger = logging.getLogger(__name__)

VALUE_SWITCHES = ("manual", "computed", "reference")
FORMULA_KINDS = ("ref", "calc")


def reference_data_library_path() -> Path:
    import spacecdf_kb
    return Path(spacecdf_kb.__file__).parent / "data" / "reference_data_library.json"


def load_reference_data_library(path: Path | None = None) -> dict:
    with open(path or reference_data_library_path(), encoding="utf-8") as fh:
        return json.load(fh)


# ── Definitions ─────────────────────────────────────────────────────────

def _definition_id_for(name: str) -> str:
    return f"pd-{name}"


async def _upsert_definition_in_session(session, d: dict) -> tuple[dict, bool]:
    """Returns (dict, created)."""
    kw = dict_to_kwargs(ParameterDefinitionRow, d)
    name = kw.get("name")
    if not name:
        raise ValueError("name is required")
    result = await session.execute(
        select(ParameterDefinitionRow).where(ParameterDefinitionRow.name == name)
    )
    row = result.scalar_one_or_none()
    if row is None:
        kw.setdefault("id", _definition_id_for(name))
        row = ParameterDefinitionRow(**kw)
        session.add(row)
        return row_to_dict(row), True
    for k, v in kw.items():
        if k in ("id", "created_at"):
            continue
        setattr(row, k, v)
    row.updated_at = utcnow()
    return row_to_dict(row), False


async def upsert_parameter_definition(d: dict) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        out, _ = await _upsert_definition_in_session(session, d)
        await session.commit()
        return out


async def seed_parameter_definitions(path: Path | None = None) -> dict:
    """Upsert every definition from the reference data library.

    The six well-known ones are forced ``is_well_known=True`` with names equal
    to the ``DesignElementRow`` columns. Non-fatal: logs and returns zeros on
    failure so start-up never breaks.
    """
    counts = {"created": 0, "updated": 0}
    try:
        lib = load_reference_data_library(path)
        units = {q["name"]: q.get("unit", "") for q in lib.get("quantity_kinds", [])}
        factory = get_session_factory()
        async with factory() as session:
            for d in lib.get("parameter_definitions", []):
                d = dict(d)
                d["is_well_known"] = d["name"] in WELL_KNOWN_PARAMETERS or bool(d.get("is_well_known"))
                d.setdefault("unit", units.get(d.get("quantity_kind", ""), ""))
                _, created = await _upsert_definition_in_session(session, d)
                counts["created" if created else "updated"] += 1
            await session.commit()
        logger.info("Seeded parameter definitions: %s", counts)
    except Exception:
        logger.exception("seed_parameter_definitions failed")
    return counts


async def get_parameter_definition(definition_id: str) -> dict | None:
    factory = get_session_factory()
    async with factory() as session:
        row = await session.get(ParameterDefinitionRow, definition_id)
        return row_to_dict(row) if row else None


async def get_parameter_definition_by_name(name: str) -> dict | None:
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(ParameterDefinitionRow).where(ParameterDefinitionRow.name == name)
        )
        row = result.scalar_one_or_none()
        return row_to_dict(row) if row else None


async def list_parameter_definitions(well_known_only: bool = False) -> list[dict]:
    filters = []
    if well_known_only:
        filters.append(ParameterDefinitionRow.is_well_known.is_(True))
    return await list_rows(ParameterDefinitionRow, *filters, order_by=ParameterDefinitionRow.name)


async def load_all_parameter_definitions() -> dict[str, dict]:
    return {d["id"]: d for d in await list_parameter_definitions()}


# ── Element parameters ──────────────────────────────────────────────────

def _validate_param_fields(d: dict) -> None:
    if "value_switch" in d and d["value_switch"] is not None and d["value_switch"] not in VALUE_SWITCHES:
        raise ValueError(f"value_switch must be one of {VALUE_SWITCHES}")
    if "formula_kind" in d and d["formula_kind"] is not None and d["formula_kind"] not in FORMULA_KINDS:
        raise ValueError(f"formula_kind must be one of {FORMULA_KINDS}")


#: Sentinel for ``load_all_element_parameters(option_id=ALL)`` — every row, all options.
ALL = "__all__"


def _option_filter(option_id: str | None):
    return ElementParameterRow.option_id.is_(None) if option_id is None else ElementParameterRow.option_id == option_id


def overlay_option_rows(rows: list[dict], option_id: str | None) -> list[dict]:
    """Pure helper: baseline rows (``option_id`` None) with option ``option_id``
    rows shadowing them per (element_id, definition_id, iteration).
    ``option_id=None`` returns the baseline rows only."""
    base = {(r["element_id"], r["definition_id"], r.get("iteration", 1)): r
            for r in rows if r.get("option_id") is None}
    if option_id:
        for r in rows:
            if r.get("option_id") == option_id:
                base[(r["element_id"], r["definition_id"], r.get("iteration", 1))] = r
    return list(base.values())


async def load_all_element_parameters(study_id: str | None = None,
                                      option_id: str | None = ALL) -> dict[str, dict]:
    """Rows by id. ``option_id=ALL`` (default) returns every row regardless of
    option; ``None`` returns the baseline only; ``X`` returns baseline ∪ X
    overrides with the override shadowing the baseline row."""
    out: dict[str, dict] = {}
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(ElementParameterRow).where(ElementParameterRow.deleted_at.is_(None))
            if study_id is not None:
                stmt = stmt.where(ElementParameterRow.study_id == study_id)
            if option_id is None:
                stmt = stmt.where(ElementParameterRow.option_id.is_(None))
            elif option_id != ALL:
                stmt = stmt.where((ElementParameterRow.option_id.is_(None))
                                  | (ElementParameterRow.option_id == option_id))
            result = await session.execute(stmt)
            rows = [row_to_dict(row) for row in result.scalars()]
        if option_id is not None and option_id != ALL:
            rows = overlay_option_rows(rows, option_id)
        for d in rows:
            out[d["id"]] = d
    except Exception:
        logger.exception("load_all_element_parameters failed")
    return out


async def _upsert_param_in_session(session, d: dict) -> ElementParameterRow:
    kw = dict_to_kwargs(ElementParameterRow, d)
    for key in ("study_id", "element_id", "definition_id"):
        if not kw.get(key):
            raise ValueError(f"{key} is required")
    _validate_param_fields(kw)
    iteration = kw.setdefault("iteration", 1)
    option_id = kw.get("option_id") or None
    kw["option_id"] = option_id
    result = await session.execute(
        select(ElementParameterRow).where(
            ElementParameterRow.element_id == kw["element_id"],
            ElementParameterRow.definition_id == kw["definition_id"],
            ElementParameterRow.iteration == iteration,
            _option_filter(option_id),
        )
    )
    row = result.scalars().first()
    if row is None:
        kw.setdefault("id", new_id("ep"))
        row = ElementParameterRow(**kw)
        session.add(row)
    else:
        row.deleted_at = None
        apply_update(row, kw, immutable=("id", "study_id", "element_id", "definition_id",
                                         "iteration", "option_id", "created_at"))
    return row


async def upsert_element_parameter(d: dict) -> dict:
    """Create or update the parameter keyed by (element_id, definition_id,
    iteration, option_id). ``option_id`` absent/None targets the baseline row;
    ``option_id=X`` targets (creates) the X override and leaves the baseline alone.

    Accepts ``definition_name`` instead of ``definition_id``; the definition is
    created on the fly (unit-less) if it does not exist yet.
    """
    d = dict(d)
    factory = get_session_factory()
    async with factory() as session:
        if not d.get("definition_id") and d.get("definition_name"):
            defn, _ = await _upsert_definition_in_session(
                session, {"name": d["definition_name"]}
            )
            d["definition_id"] = defn["id"]
        row = await _upsert_param_in_session(session, d)
        await session.commit()
        return row_to_dict(row)


async def get_element_parameter(param_id: str) -> dict | None:
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, ElementParameterRow, param_id)
        return row_to_dict(row) if row else None


async def update_element_parameter(param_id: str, updates: dict,
                                   expected_version: int | None = None) -> dict:
    _validate_param_fields(updates)
    factory = get_session_factory()
    async with factory() as session:
        row = await get_row(session, ElementParameterRow, param_id)
        if row is None:
            raise ValueError(f"Element parameter '{param_id}' not found")
        apply_update(row, updates, expected_version=expected_version,
                     immutable=("id", "study_id", "element_id", "definition_id", "created_at"))
        await session.commit()
        return row_to_dict(row)


async def soft_delete_element_parameter(param_id: str) -> bool:
    return await soft_delete_row(ElementParameterRow, param_id)


async def list_element_parameters_by_study(study_id: str, option_id: str | None = None) -> list[dict]:
    """Baseline rows of the study; with ``option_id`` the option's overrides
    shadow the baseline rows they duplicate (baseline ∪ overrides)."""
    rows = await list_rows(ElementParameterRow, ElementParameterRow.study_id == study_id,
                           (ElementParameterRow.option_id.is_(None)) if option_id is None else
                           ((ElementParameterRow.option_id.is_(None)) | (ElementParameterRow.option_id == option_id)))
    return overlay_option_rows(rows, option_id)


async def list_element_parameters_by_element(element_id: str, iteration: int | None = None,
                                             option_id: str | None = None) -> list[dict]:
    """Same shadowing rule as ``list_element_parameters_by_study`` for one element."""
    filters = [ElementParameterRow.element_id == element_id]
    if iteration is not None:
        filters.append(ElementParameterRow.iteration == iteration)
    filters.append((ElementParameterRow.option_id.is_(None)) if option_id is None else
                   ((ElementParameterRow.option_id.is_(None)) | (ElementParameterRow.option_id == option_id)))
    return overlay_option_rows(await list_rows(ElementParameterRow, *filters), option_id)


async def list_option_overrides(study_id: str, option_id: str) -> list[dict]:
    """Only the rows that belong to ``option_id`` (no baseline)."""
    return await list_rows(ElementParameterRow, ElementParameterRow.study_id == study_id,
                           ElementParameterRow.option_id == option_id)


# ── Well-known column mirroring ─────────────────────────────────────────

async def mirror_well_known_columns(element: dict) -> int:
    """Element dict -> ElementParameter rows for the six well-known columns.

    Called by ``element_repo`` after every element write. Cheap (one session),
    non-fatal (logs and returns 0 on failure). Only columns that are not
    ``None`` are mirrored; ``computed_value`` is set and, unless the row is
    already ``manual``/``reference``, ``value_switch`` stays ``computed``.
    Returns the number of parameter rows touched.
    """
    element_id = element.get("id")
    study_id = element.get("study_id")
    if not element_id or not study_id:
        return 0
    values = {name: element.get(name) for name in WELL_KNOWN_PARAMETERS if element.get(name) is not None}
    if not values:
        return 0
    touched = 0
    try:
        factory = get_session_factory()
        async with factory() as session:
            for name, value in values.items():
                defn, _ = await _upsert_definition_in_session(
                    session, {"name": name, "is_well_known": True}
                )
                result = await session.execute(
                    select(ElementParameterRow).where(
                        ElementParameterRow.element_id == element_id,
                        ElementParameterRow.definition_id == defn["id"],
                        ElementParameterRow.iteration == 1,
                        ElementParameterRow.option_id.is_(None),
                    )
                )
                row = result.scalars().first()
                if row is None:
                    session.add(ElementParameterRow(
                        id=new_id("ep"), study_id=study_id, element_id=element_id,
                        definition_id=defn["id"], owner_domain=element.get("subsystem_domain"),
                        computed_value=float(value), value_switch="computed",
                    ))
                    touched += 1
                elif row.computed_value != float(value) or row.deleted_at is not None:
                    row.computed_value = float(value)
                    row.deleted_at = None
                    row.version = (row.version or 0) + 1
                    row.updated_at = utcnow()
                    touched += 1
            await session.commit()
    except Exception:
        logger.exception("mirror_well_known_columns failed for %s", element_id)
        return 0
    return touched


async def effective_well_known_values(element_id: str) -> dict[str, float | None]:
    """Parameter rows -> {column_name: effective value} for the well-known set
    (the reverse mirror; callers decide whether to write it onto the element)."""
    out: dict[str, float | None] = {}
    try:
        factory = get_session_factory()
        async with factory() as session:
            stmt = (
                select(ElementParameterRow, ParameterDefinitionRow.name)
                .join(ParameterDefinitionRow, ParameterDefinitionRow.id == ElementParameterRow.definition_id)
                .where(
                    ElementParameterRow.element_id == element_id,
                    ElementParameterRow.deleted_at.is_(None),
                    ElementParameterRow.iteration == 1,
                    ElementParameterRow.option_id.is_(None),
                    ParameterDefinitionRow.name.in_(WELL_KNOWN_PARAMETERS),
                )
            )
            for row, name in (await session.execute(stmt)).all():
                if row.value_switch == "manual":
                    out[name] = row.manual_value
                elif row.value_switch == "reference":
                    out[name] = row.reference_value
                else:
                    out[name] = row.computed_value
    except Exception:
        logger.exception("effective_well_known_values failed for %s", element_id)
    return out
