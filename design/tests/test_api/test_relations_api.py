"""Requirement relations, traceability tree/trace and compliance affected ids (SCDF-160 §1.4)."""
from __future__ import annotations

import pytest

from tests.test_api.conftest import make_element, make_requirement


async def _rel(client, study, kind, sk, sid, tk, tid, **extra):
    r = await client.post(f"/api/relations/?study_id={study}", json={
        "kind": kind, "source_kind": sk, "source_id": sid, "target_kind": tk, "target_id": tid, **extra})
    assert r.status_code == 200, r.text
    return r.json()


async def test_relation_crud(client, study_obj, study):
    rel = await _rel(client, study, "satisfies", "element", "el-1", "requirement", "REQ-1", rationale="because")
    assert rel["kind"] == "satisfies" and rel["rationale"] == "because"
    again = await _rel(client, study, "satisfies", "element", "el-1", "requirement", "REQ-1")
    assert again["id"] == rel["id"]  # idempotent

    assert (await client.get(f"/api/relations/{rel['id']}")).json()["id"] == rel["id"]
    assert (await client.post(f"/api/relations/?study_id={study}", json={
        "kind": "loves", "source_kind": "element", "source_id": "a", "target_kind": "requirement", "target_id": "b"})).status_code == 400
    assert (await client.post(f"/api/relations/?study_id={study}", json={
        "kind": "traces", "source_kind": "widget", "source_id": "a", "target_kind": "requirement", "target_id": "b"})).status_code == 400
    assert (await client.post(f"/api/relations/?study_id={study}", json={
        "kind": "traces", "source_kind": "requirement", "source_id": "a", "target_kind": "requirement", "target_id": "a"})).status_code == 400

    await _rel(client, study, "verifies", "test", "T-1", "requirement", "REQ-1")
    assert len((await client.get(f"/api/studies/{study}/relations")).json()) == 2
    assert len((await client.get(f"/api/studies/{study}/relations?kind=verifies")).json()) == 1
    assert len((await client.get("/api/relations/for/requirement/REQ-1")).json()) == 2
    assert len((await client.get("/api/relations/for/requirement/REQ-1?direction=out")).json()) == 0
    assert len((await client.get("/api/relations/for/element/el-1?kind=satisfies")).json()) == 1

    assert (await client.delete(f"/api/relations/{rel['id']}")).json()["deleted"] is True
    assert (await client.get(f"/api/relations/{rel['id']}")).status_code == 404
    assert (await client.delete(f"/api/relations/{rel['id']}")).status_code == 404
    assert len((await client.get(f"/api/studies/{study}/relations")).json()) == 1


async def _seed_trace(client, study_obj, study):
    from spacecdf_common.models.mission_need import MissionNeed, Objective

    study_obj.mission_need = MissionNeed(objectives=[
        Objective(id="OBJ-1", text="Image crops at 10 m GSD", traced_to_requirements=["MR-1"]),
        Objective(id="OBJ-2", text="Orphan objective"),
    ])
    sc = await make_element(client, study, "Spacecraft", "system")
    eps = await make_element(client, study, "EPS", "subsystem", parent_id=sc["id"], subsystem_domain="eps")
    fn = (await client.post(f"/api/functions/?study_id={study}", json={"name": "Generate power"})).json()

    await make_requirement(client, study, "MR-1", level="mission", verification_method="analysis")
    await make_requirement(client, study, "SR-1", level="system", parent_id="MR-1", element_id=sc["id"],
                           verification_method="test", verification_phase="AIT", status="approved")
    await make_requirement(client, study, "SSR-1", level="subsystem", parent_id="SR-1",
                           threshold_param_path="power.eol_w", threshold_op=">=", threshold_value="100")
    await make_requirement(client, study, "SR-9", level="system")  # not traced to any objective

    await _rel(client, study, "satisfies", "element", eps["id"], "requirement", "SSR-1")
    await _rel(client, study, "allocates", "requirement", "SSR-1", "function", fn["id"])
    await _rel(client, study, "verifies", "test", "T-1", "requirement", "SSR-1")  # not a link kind
    return sc, eps, fn


async def test_traceability_tree(client, study_obj, study):
    sc, eps, fn = await _seed_trace(client, study_obj, study)

    r = await client.get(f"/api/studies/{study}/traceability/tree")
    assert r.status_code == 200, r.text
    tree = r.json()
    assert tree["summary"] == {
        "objectives": 2, "requirements": 4,
        "requirements_by_level": {"mission": 1, "system": 2, "subsystem": 1},
        "relations": 3, "requirements_traced_to_objectives": 1,
    }
    obj1, obj2 = tree["objectives"]
    assert obj1["id"] == "OBJ-1" and obj2["requirements"] == []
    mr = obj1["requirements"][0]
    assert mr["id"] == "MR-1" and mr["level"] == "mission" and mr["verification"]["method"] == "analysis"
    sr = mr["children"][0]
    assert sr["id"] == "SR-1"
    assert sr["elements"] == [{"id": sc["id"], "name": "Spacecraft", "element_type": "system",
                               "subsystem_domain": None, "relation": "element_id"}]
    assert sr["verification"] == {"method": "test", "phase": "AIT", "status": "approved"}
    ssr = sr["children"][0]
    assert ssr["id"] == "SSR-1" and ssr["children"] == []
    assert [(e["id"], e["relation"]) for e in ssr["elements"]] == [(eps["id"], "satisfies")]
    assert ssr["functions"] == [{"id": fn["id"], "name": "Generate power", "layer": "SA", "relation": "allocates"}]
    assert [n["id"] for n in tree["unlinked_requirements"]] == ["SR-9"]


async def test_requirement_trace_up_and_down(client, study_obj, study):
    sc, eps, fn = await _seed_trace(client, study_obj, study)

    r = await client.get("/api/requirements/SSR-1/trace")
    assert r.status_code == 200, r.text
    t = r.json()
    assert t["requirement"]["id"] == "SSR-1"
    assert [p["id"] for p in t["up"]["parents"]] == ["SR-1", "MR-1"]
    assert [o["id"] for o in t["up"]["objectives"]] == ["OBJ-1"]
    assert t["down"]["children"] == []
    assert [e["id"] for e in t["down"]["elements"]] == [eps["id"]]
    assert [f["id"] for f in t["down"]["functions"]] == [fn["id"]]
    assert len(t["relations"]) == 3

    t = (await client.get("/api/requirements/MR-1/trace")).json()
    assert t["up"]["parents"] == []
    assert [c["id"] for c in t["down"]["children"]] == ["SR-1"]
    assert [c["id"] for c in t["down"]["children"][0]["children"]] == ["SSR-1"]

    assert (await client.get("/api/requirements/NOPE/trace")).status_code == 404


async def test_compliance_delta_affected_ids(client, study_obj, study):
    from spacecdf_server.services.compliance_tracker import ComplianceTracker

    sc, eps, fn = await _seed_trace(client, study_obj, study)
    reqs = (await client.get(f"/api/requirements/tree?study_id={study}")).json()

    tracker = ComplianceTracker(reqs)
    await tracker.load_relations(study)
    assert tracker.linked_entities("SSR-1") == ([eps["id"]], [fn["id"]])
    assert tracker.linked_entities("SR-1") == ([sc["id"]], [])

    # baseline pass, then violation, then cleared
    d0 = await tracker.recheck({"power.eol_w": 120.0})
    assert d0.newly_violated == [] and d0.affected_elements == [] and d0.affected_functions == []
    d1 = await tracker.recheck({"power.eol_w": 80.0})
    assert d1.newly_violated == ["SSR-1"]
    assert d1.affected_elements == [eps["id"]] and d1.affected_functions == [fn["id"]]
    d2 = await tracker.recheck({"power.eol_w": 150.0})
    assert d2.newly_cleared == ["SSR-1"]
    assert d2.affected_elements == [eps["id"]] and d2.affected_functions == [fn["id"]]
    d3 = await tracker.recheck({"power.eol_w": 150.0})
    assert d3.newly_cleared == [] and d3.affected_elements == []


def test_compliance_tracker_without_relations_unchanged():
    """Backwards compatible: no relations → empty affected lists, same delta fields."""
    import asyncio
    from spacecdf_server.services.compliance_tracker import ComplianceTracker

    t = ComplianceTracker([{"id": "R", "threshold_param_path": "m", "threshold_op": "<=", "threshold_value": "10",
                            "element_id": "el-x"}])
    asyncio.run(t.recheck({"m": 5}))
    d = asyncio.run(t.recheck({"m": 15}))
    assert d.newly_violated == ["R"] and d.affected_elements == ["el-x"] and d.affected_functions == []
