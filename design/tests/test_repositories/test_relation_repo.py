"""Repo tests for typed requirement relations (SCDF-160 §1.4)."""
from __future__ import annotations

import pytest

from spacecdf_server.db import relation_repo as rr


def _rel(study, **kw):
    d = {"study_id": study, "kind": "satisfies", "source_kind": "element", "source_id": "el-1",
         "target_kind": "requirement", "target_id": "SR-001"}
    d.update(kw)
    return d


async def test_create_idempotent_and_revive(study):
    r1 = await rr.create_relation(_rel(study))
    r2 = await rr.create_relation(_rel(study, rationale="because"))
    assert r1["id"] == r2["id"] and r2["rationale"] == "because"
    assert len(await rr.list_relations_by_study(study)) == 1
    assert await rr.soft_delete_relation(r1["id"])
    assert await rr.get_relation(r1["id"]) is None
    assert await rr.list_relations_by_study(study) == []
    r3 = await rr.create_relation(_rel(study))
    assert r3["id"] == r1["id"] and r3["deleted_at"] is None


async def test_validation(study):
    with pytest.raises(ValueError, match="kind"):
        await rr.create_relation(_rel(study, kind="likes"))
    with pytest.raises(ValueError, match="source_kind"):
        await rr.create_relation(_rel(study, source_kind="planet"))
    with pytest.raises(ValueError, match="itself"):
        await rr.create_relation(_rel(study, source_kind="requirement", source_id="SR-001"))
    with pytest.raises(ValueError, match="required"):
        await rr.create_relation({"study_id": study, "kind": "satisfies"})


async def test_list_for_entity_and_direction(study):
    await rr.create_relation(_rel(study))                                   # el-1 -satisfies-> SR-001
    await rr.create_relation(_rel(study, kind="verifies", source_kind="test", source_id="T-1"))  # T-1 -verifies-> SR-001
    await rr.create_relation(_rel(study, kind="derives", source_kind="requirement", source_id="SR-001",
                                  target_kind="requirement", target_id="SSR-001"))  # SR-001 -derives-> SSR-001
    assert len(await rr.list_relations_for("requirement", "SR-001")) == 3
    assert len(await rr.list_relations_for("requirement", "SR-001", direction="in")) == 2
    assert len(await rr.list_relations_for("requirement", "SR-001", direction="out")) == 1
    assert len(await rr.list_relations_for("requirement", "SR-001", kind="verifies")) == 1
    assert len(await rr.list_relations_by_study(study, kind="satisfies")) == 1
    assert len(await rr.load_all_relations(study)) == 3
