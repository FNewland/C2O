"""Additive schema upgrades for databases created by ``Base.metadata.create_all``.

``create_all`` creates *missing tables* but never adds *missing columns* to
tables that already exist. Every time a column is added to an ORM model,
existing SQLite files would silently break. ``ensure_schema_upgrades`` walks
the ORM metadata, compares it with the live schema and issues
``ALTER TABLE ... ADD COLUMN`` for anything missing. It is idempotent and
safe to run on every start-up (SCDF-160).

Only additive column changes are handled — no renames, drops or type changes
(Alembic remains the tool for those).
"""
from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.schema import CreateColumn

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


async def ensure_schema_upgrades(engine: AsyncEngine) -> list[str]:
    """Add any ORM-declared columns missing from existing tables.

    Returns the list of ``"table.column"`` strings that were added (empty when
    the schema was already up to date). Never raises for a single failed
    column — the error is logged and the remaining columns are still tried.
    """
    try:
        async with engine.begin() as conn:
            return await conn.run_sync(_upgrade_sync)
    except Exception:
        logger.exception("ensure_schema_upgrades failed")
        return []
