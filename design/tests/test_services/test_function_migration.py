"""Legacy functional_decomposition JSON -> FunctionRow + allocations, idempotent (SCDF-160 §1.1)."""
from __future__ import annotations

import pytest

from spacecdf_common.models.functions import Function, FunctionType
from spacecdf_server.db import function_repo as fr
from spacecdf_server.services.function_migration import (
    get_functions, migrate_study_functions,
)


def _elements(study: str) -> dict[str, dict]:
    return {
        "el-sys": {"id": "el-sys", "study_id": study, "element_type": "system", "name": "SC"},
        "el-eps": {"id": "el-eps", "study_id": study, "element_type": "subsystem", "subsystem_domain": "eps"},
        "el-ttc": {"id": "el-ttc", "study_id": study, "element_type": "subsystem", "subsystem_domain": "ttc"},
        "el-pl": {"id": "el-pl", "study_id": study, "element_type": "subsystem", "subsystem_domain": "payload"},
        "el-old": {"id": "el-old", "study_id": study, "element_type": "subsystem", "subsystem_domain": "aocs",
                   "deleted_at": "2026-01-01T00:00:00"},
        "el-other": {"id": "el-other", "study_id": "other", "element_type": "subsystem", "subsystem_domain": "aocs"},
    }


def _legacy() -> list[dict]:
    fs = [
        Function(id="F-001", name="Achieve: observe crops", function_type=FunctionType.OBSERVE, level=0),
        Function(id="F-002", name="Acquire imagery", parent_function_id="F-001", allocated_to="payload",
                 level=1, is_leaf=True, position_responsible="payload_engineer"),
        Function(id="F-003", name="Downlink data", parent_function_id="F-001", allocated_to="link", level=1),
        Function(id="F-004", name="Generate electrical power", function_type=FunctionType.POWER,
                 allocated_to="power", level=0),
        Function(id="F-005", name="Point instrument", parent_function_id="F-001", allocated_to="aocs", level=1),
        Function(id="F-006", name="Direct to element", allocated_to="el-sys", level=0),
    ]
    return [f.model_dump() for f in fs]


async def test_migrates_functions_and_allocations(study):
    counts = await migrate_study_functions(study, _legacy(), _elements(study))
    assert counts["functions_created"] == 6 and counts["functions_updated"] == 0
    assert counts["parents_linked"] == 3
    assert counts["allocations"] == 4        # payload, link->ttc, power->eps, direct element id
    assert counts["unallocated"] == 2        # F-001 (none) and F-005 (aocs: deleted / other study only)

    rows = await fr.list_functions_by_study(study)
    assert len(rows) == 6
    by_legacy = {r["external_ids"]["legacy"]: r for r in rows}
    assert all(r["layer"] == "SA" for r in rows)
    assert by_legacy["F-002"]["parent_id"] == by_legacy["F-001"]["id"]
    assert by_legacy["F-002"]["is_leaf"] is True
    assert by_legacy["F-002"]["position_responsible"] == "payload_engineer"
    assert by_legacy["F-004"]["function_type"] == "power"
    assert by_legacy["F-001"]["parent_id"] is None

    allocs = {a["function_id"]: a["element_id"] for a in await fr.list_allocations_by_study(study)}
    assert allocs[by_legacy["F-002"]["id"]] == "el-pl"
    assert allocs[by_legacy["F-003"]["id"]] == "el-ttc"
    assert allocs[by_legacy["F-004"]["id"]] == "el-eps"
    assert allocs[by_legacy["F-006"]["id"]] == "el-sys"
    assert by_legacy["F-005"]["id"] not in allocs


async def test_rerun_is_idempotent_and_applies_changes(study):
    legacy = _legacy()
    await migrate_study_functions(study, legacy, _elements(study))
    first = {r["external_ids"]["legacy"]: r["id"] for r in await fr.list_functions_by_study(study)}

    # rename one, re-allocate one, re-parent one
    legacy[1]["name"] = "Acquire multispectral imagery"
    legacy[2]["allocated_to"] = "payload"
    legacy[4]["parent_function_id"] = None
    counts = await migrate_study_functions(study, legacy, _elements(study))
    assert counts["functions_created"] == 0 and counts["functions_updated"] == 6

    rows = await fr.list_functions_by_study(study)
    assert len(rows) == 6
    by_legacy = {r["external_ids"]["legacy"]: r for r in rows}
    assert {k: v["id"] for k, v in by_legacy.items()} == first  # same row ids
    assert by_legacy["F-002"]["name"] == "Acquire multispectral imagery"
    assert by_legacy["F-005"]["parent_id"] is None
    allocs = await fr.list_allocations_by_study(study)
    assert len(allocs) == 4
    assert {a["function_id"]: a["element_id"] for a in allocs}[by_legacy["F-003"]["id"]] == "el-pl"


async def test_empty_and_skipped(study):
    assert (await migrate_study_functions(study, [], {}))["functions_created"] == 0
    counts = await migrate_study_functions(study, [{"name": "no id"}], {})
    assert counts["functions_created"] == 0


async def test_get_functions_prefers_rows(study):
    legacy = _legacy()
    assert await get_functions(study, legacy) == legacy
    await migrate_study_functions(study, legacy, _elements(study))
    rows = await get_functions(study, legacy)
    assert len(rows) == 6 and rows[0]["id"].startswith("fn-")
