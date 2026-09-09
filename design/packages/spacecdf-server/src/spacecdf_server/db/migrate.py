"""Additive schema upgrades for databases created by ``Base.metadata.create_all``.

``create_all`` creates *missing tables* but never adds *missing columns* to
tables that already exist. Every time a column is added to an ORM model,
existing SQLite files would silently break. ``ensure_schema_upgrades`` walks
the ORM metadata, compares it with the live schema and issues
``ALTER TABLE ... ADD COLUMN`` for anything missing. It is idempotent and
safe to run on every start-up (SCDF-160).

Only additive column changes are handled — no renames, drops or type changes
(Alembic remains the tool for those) — with one deliberate exception:
``ensure_option_scoped_parameters`` (SCDF-172) rebuilds the
``element_parameters`` uniqueness so that it includes ``option_id``. The ORM
still declares the pre-172 constraint ``(element_id, definition_id,
iteration)``; option overrides need one row per option for the same
element/definition, so the live table is migrated to
``(element_parameter_element_definition_iteration_option)`` =
``(element_id, definition_id, iteration, option_id)``. Baseline rows keep
``option_id IS NULL`` (their uniqueness is guarded by the repository upsert,
since SQL treats NULLs as distinct).
"""
from __future__ import annotations

import logging

from sqlalchemy import MetaData, UniqueConstraint, inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.schema import CreateColumn, CreateIndex, CreateTable

from .models import Base

logger = logging.getLogger(__name__)


def _render_default(column, dialect) -> str:
    """Render a literal DEFAULT clause for simple scalar Python defaults."""
    default = column.default
    if default is None or not getattr(default, "is_scalar", False):
        return ""
    value = default.arg
    if isinstance(value, bool):
        return f" DEFAULT {1 if value else 0}"
    if isinstance(value, (int, float)):
        return f" DEFAULT {value}"
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f" DEFAULT '{escaped}'"
    return ""


def _upgrade_sync(conn: Connection) -> list[str]:
    """Synchronous worker — returns the list of 'table.column' additions made."""
    inspector = inspect(conn)
    existing_tables = set(inspector.get_table_names())
    dialect = conn.dialect
    added: list[str] = []

    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue  # create_all handles brand-new tables
        existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_cols:
                continue
            col_type = column.type.compile(dialect=dialect)
            ddl = f"ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type}"
            ddl += _render_default(column, dialect)
            conn.execute(text(ddl))
            added.append(f"{table.name}.{column.name}")
            logger.info("Schema upgrade: added column %s.%s", table.name, column.name)
    return added


# ── SCDF-172: option-scoped parameter rows ─────────────────────────────

PARAM_TABLE = "element_parameters"
OPTION_UNIQUE_NAME = "uq_element_parameter_element_definition_iteration_option"
OPTION_UNIQUE_COLUMNS = ("element_id", "definition_id", "iteration", "option_id")


def _legacy_param_unique(inspector) -> list[str]:
    """Names of unique constraints/indexes on element_parameters that do NOT include option_id."""
    names: list[str] = []
    try:
        for uc in inspector.get_unique_constraints(PARAM_TABLE):
            if "option_id" not in (uc.get("column_names") or []):
                names.append(uc.get("name") or "")
        for ix in inspector.get_indexes(PARAM_TABLE):
            if ix.get("unique") and "option_id" not in (ix.get("column_names") or []):
                names.append(ix.get("name") or "")
    except Exception:  # pragma: no cover - dialect quirks
        logger.exception("inspecting %s uniqueness failed", PARAM_TABLE)
    return names


def _has_option_unique(inspector) -> bool:
    try:
        for uc in inspector.get_unique_constraints(PARAM_TABLE):
            if list(uc.get("column_names") or []) == list(OPTION_UNIQUE_COLUMNS):
                return True
        for ix in inspector.get_indexes(PARAM_TABLE):
            if ix.get("unique") and list(ix.get("column_names") or []) == list(OPTION_UNIQUE_COLUMNS):
                return True
    except Exception:  # pragma: no cover
        pass
    return False


def _rebuild_param_table_sqlite(conn: Connection) -> None:
    """SQLite cannot drop a table-level UNIQUE: copy into a rebuilt table."""
    md = MetaData()
    for tbl in Base.metadata.sorted_tables:
        if tbl.name == PARAM_TABLE:
            continue
        tbl.to_metadata(md)
    tmp_name = PARAM_TABLE + "__scdf172"
    new_tbl = Base.metadata.tables[PARAM_TABLE].to_metadata(md, name=tmp_name)
    for c in list(new_tbl.constraints):
        if isinstance(c, UniqueConstraint):
            new_tbl.constraints.discard(c)
    new_tbl.append_constraint(UniqueConstraint(*OPTION_UNIQUE_COLUMNS, name=OPTION_UNIQUE_NAME))
    # Indexes are recreated after the rename (they carry the original names).
    indexes = list(new_tbl.indexes)
    new_tbl.indexes.clear()
    dialect = conn.dialect
    conn.execute(text(f"DROP TABLE IF EXISTS {tmp_name}"))
    conn.execute(text(str(CreateTable(new_tbl).compile(dialect=dialect))))
    cols = ", ".join(c.name for c in new_tbl.columns)
    conn.execute(text(f"INSERT INTO {tmp_name} ({cols}) SELECT {cols} FROM {PARAM_TABLE}"))
    conn.execute(text(f"DROP TABLE {PARAM_TABLE}"))
    conn.execute(text(f"ALTER TABLE {tmp_name} RENAME TO {PARAM_TABLE}"))
    for ix in Base.metadata.tables[PARAM_TABLE].indexes:
        conn.execute(text(str(CreateIndex(ix).compile(dialect=dialect))))
    del indexes


def _option_scoped_sync(conn: Connection) -> bool:
    inspector = inspect(conn)
    if PARAM_TABLE not in set(inspector.get_table_names()):
        return False
    if "option_id" not in {c["name"] for c in inspector.get_columns(PARAM_TABLE)}:
        return False  # column upgrade runs first; next start-up will rebuild
    legacy = _legacy_param_unique(inspector)
    if not legacy and _has_option_unique(inspector):
        return False
    if conn.dialect.name == "sqlite":
        _rebuild_param_table_sqlite(conn)
    else:  # pragma: no cover - Postgres & friends
        for name in legacy:
            if name:
                try:
                    conn.execute(text(f"ALTER TABLE {PARAM_TABLE} DROP CONSTRAINT {name}"))
                except Exception:
                    conn.execute(text(f"DROP INDEX IF EXISTS {name}"))
        conn.execute(text(
            f"ALTER TABLE {PARAM_TABLE} ADD CONSTRAINT {OPTION_UNIQUE_NAME} "
            f"UNIQUE ({', '.join(OPTION_UNIQUE_COLUMNS)})"))
    logger.info("Schema upgrade: %s uniqueness now includes option_id (SCDF-172)", PARAM_TABLE)
    return True


async def ensure_option_scoped_parameters(engine: AsyncEngine) -> bool:
    """Make ``element_parameters`` unique per (element, definition, iteration, option).

    Idempotent; returns True when the table was migrated. Never raises.
    """
    try:
        async with engine.begin() as conn:
            return await conn.run_sync(_option_scoped_sync)
    except Exception:
        logger.exception("ensure_option_scoped_parameters failed")
        return False


async def ensure_schema_upgrades(engine: AsyncEngine) -> list[str]:
    """Add any ORM-declared columns missing from existing tables.

    Returns the list of ``"table.column"`` strings that were added (empty when
    the schema was already up to date). Never raises for a single failed
    column — the error is logged and the remaining columns are still tried.
    """
    added: list[str] = []
    try:
        async with engine.begin() as conn:
            added = await conn.run_sync(_upgrade_sync)
    except Exception:
        logger.exception("ensure_schema_upgrades failed")
    if await ensure_option_scoped_parameters(engine):
        added.append(f"{PARAM_TABLE}.{OPTION_UNIQUE_NAME}")
    return added
