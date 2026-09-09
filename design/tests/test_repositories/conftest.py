"""Shared fixtures for repository tests (SCDF-160).

``db_factory`` points the *global* engine/session-factory singletons in
``spacecdf_server.db.engine`` at a throw-away SQLite file, so every repo that
calls ``get_session_factory()`` — whatever module it imported it from — hits
the test database. Tables are created from the current ORM metadata.
"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest


@pytest.fixture()
def db_factory(tmp_path):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from spacecdf_server.db import engine as engine_mod
    from spacecdf_server.db.models import Base

    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    engine = create_async_engine(db_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_tables())

    with patch.object(engine_mod, "_engine", engine), \
            patch.object(engine_mod, "_session_factory", factory):
        yield factory

    asyncio.run(engine.dispose())


@pytest.fixture()
async def study(db_factory):
    """A minimal StudyRow so FK-bearing rows have a parent."""
    from spacecdf_server.db.models import StudyRow

    async with db_factory() as s:
        s.add(StudyRow(id="study-1", name="Test study", meta_json={}))
        await s.commit()
    return "study-1"
