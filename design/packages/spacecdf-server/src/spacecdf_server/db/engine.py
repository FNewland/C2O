"""Async SQLAlchemy engine for SpaceCDF persistence.

Defaults to SQLite with aiosqlite. Reads DATABASE_URL env var for
Postgres or other engines. Enables WAL mode on SQLite for better
concurrency.
"""
from __future__ import annotations

import os
import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./spacecdf.db")

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_pragma_listener_installed = False


def _install_sqlite_pragma_listener() -> None:
    """Install a sync-engine 'connect' listener that enables WAL + relaxed sync."""
    global _pragma_listener_installed
    if _pragma_listener_installed:
        return

    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # pragma: no cover
        # Best-effort: only runs for SQLite connections. Non-SQLite dialects
        # raise when executing PRAGMA; guard by checking the connection type.
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        except Exception:
            pass

    _pragma_listener_installed = True


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            future=True,
        )
        if DATABASE_URL.startswith("sqlite"):
            _install_sqlite_pragma_listener()
        logger.info("SQLAlchemy async engine created for %s", DATABASE_URL)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
