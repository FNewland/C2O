"""ensure_schema_upgrades adds ORM columns missing from pre-existing tables (SCDF-160)."""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from spacecdf_server.db.migrate import ensure_schema_upgrades
from spacecdf_server.db.models import Base


# A design_elements / element_interfaces / requirements table as they looked
# BEFORE SCDF-160 (no layer / exchange_item_ids_json / external_id columns).
_OLD_ELEMENTS = """
CREATE TABLE studies (id VARCHAR(32) PRIMARY KEY, name VARCHAR(255), created_at DATETIME, meta_json JSON)
"""
_OLD_DESIGN_ELEMENTS = """
CREATE TABLE design_elements (
  id VARCHAR(64) PRIMARY KEY, study_id VARCHAR(32), session_id VARCHAR(32), parent_id VARCHAR(64),
  name VARCHAR(255), element_type VARCHAR(32), subsystem_domain VARCHAR(32), description TEXT,
  segment VARCHAR(16), mass_kg FLOAT, power_avg_w FLOAT, power_peak_w FLOAT, volume_cm3 FLOAT,
  dimensions_json JSON, cost_nre_keur FLOAT, cost_recurring_keur FLOAT, work_package_id VARCHAR(32),
  trl INTEGER, heritage_json JSON, manufacturer VARCHAR(128), part_number VARCHAR(128),
  kb_component_id VARCHAR(64), quantity INTEGER, redundancy_type VARCHAR(32), performance_json JSON,
  margin_percent FLOAT, verification_status VARCHAR(32), owner_position VARCHAR(64),
  in_scope BOOLEAN, frozen BOOLEAN, diagram_x FLOAT, diagram_y FLOAT, diagram_collapsed BOOLEAN,
  version INTEGER, deleted_at DATETIME, created_at DATETIME, updated_at DATETIME)
"""
_OLD_INTERFACES = """
CREATE TABLE element_interfaces (
  id VARCHAR(64) PRIMARY KEY, study_id VARCHAR(32), name VARCHAR(255), interface_type VARCHAR(32),
  direction VARCHAR(16), from_element_id VARCHAR(64), to_element_id VARCHAR(64), properties_json JSON,
  status VARCHAR(32), criticality VARCHAR(16), diagram_label VARCHAR(128), version INTEGER,
  deleted_at DATETIME, created_at DATETIME, updated_at DATETIME)
"""
_OLD_REQUIREMENTS = """
CREATE TABLE requirements (
  id VARCHAR(32) PRIMARY KEY, study_id VARCHAR(32), parent_id VARCHAR(32), level VARCHAR(16),
  code VARCHAR(32), text TEXT, rationale TEXT, threshold_param_path VARCHAR(255), threshold_op VARCHAR(16),
  threshold_value TEXT, verification_method VARCHAR(8), verification_phase VARCHAR(8),
  responsible_position VARCHAR(64), status VARCHAR(16), element_id VARCHAR(64),
  derived_from_requirement_id VARCHAR(32), created_at DATETIME, updated_at DATETIME)
"""


async def _columns(engine, table: str) -> set[str]:
    async with engine.connect() as conn:
        rows = (await conn.execute(text(f"PRAGMA table_info({table})"))).fetchall()
    return {r[1] for r in rows}


@pytest.fixture()
async def old_engine(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/old.db")
    async with engine.begin() as conn:
        for ddl in (_OLD_ELEMENTS, _OLD_DESIGN_ELEMENTS, _OLD_INTERFACES, _OLD_REQUIREMENTS):
            await conn.execute(text(ddl))
        await conn.execute(text(
            "INSERT INTO design_elements (id, study_id, name, element_type, version) "
            "VALUES ('el-1', 'study-1', 'Bus', 'system', 1)"
        ))
    yield engine
    await engine.dispose()


async def test_adds_missing_columns_to_old_tables(old_engine):
    assert "layer" not in await _columns(old_engine, "design_elements")
    assert "exchange_item_ids_json" not in await _columns(old_engine, "element_interfaces")
    assert "external_id" not in await _columns(old_engine, "requirements")

    added = await ensure_schema_upgrades(old_engine)

    assert "design_elements.layer" in added
    assert "element_interfaces.exchange_item_ids_json" in added
    assert "requirements.external_id" in added
    assert "requirements.external_ids_json" in added
    assert "layer" in await _columns(old_engine, "design_elements")
    assert "exchange_item_ids_json" in await _columns(old_engine, "element_interfaces")
    assert {"external_id", "external_ids_json"} <= await _columns(old_engine, "requirements")


async def test_scalar_default_applied_to_existing_rows(old_engine):
    await ensure_schema_upgrades(old_engine)
    async with old_engine.connect() as conn:
        layer = (await conn.execute(text("SELECT layer FROM design_elements WHERE id='el-1'"))).scalar()
    assert layer == "PA"


async def test_idempotent(old_engine):
    first = await ensure_schema_upgrades(old_engine)
    second = await ensure_schema_upgrades(old_engine)
    assert first
    assert second == []


async def test_noop_on_fresh_schema(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/fresh.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    assert await ensure_schema_upgrades(engine) == []
    await engine.dispose()


async def test_skips_tables_that_do_not_exist_yet(old_engine):
    """Brand-new tables are create_all's job — the upgrader must not touch them."""
    await ensure_schema_upgrades(old_engine)
    async with old_engine.connect() as conn:
        names = (await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )).scalars().all()
    assert "functions" not in names


async def test_old_db_gains_analysis_tables_via_create_all(old_engine):
    """SCDF-170: on an old DB the app path (create_all, then the upgrader) creates
    ``analysis_runs`` / ``analysis_conflicts`` and adds nothing else for them."""
    async with old_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    added = await ensure_schema_upgrades(old_engine)
    assert not any(a.startswith(("analysis_runs.", "analysis_conflicts.")) for a in added)
    async with old_engine.connect() as conn:
        names = set((await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )).scalars().all())
    assert {"analysis_runs", "analysis_conflicts"} <= names
    assert {"id", "study_id", "option_id", "analysis", "status", "inputs_hash", "summary_json", "series_ref"} \
        <= await _columns(old_engine, "analysis_runs")
    assert {"severity", "code", "element_ids_json", "requirement_ids_json", "resolved_at"} \
        <= await _columns(old_engine, "analysis_conflicts")
