"""Functions / ports / allocations / exchanges / realizations API (SCDF-160 §3)."""
from __future__ import annotations

from tests.test_api.conftest import make_element


async def _fn(client, study, name, **kw):
    r = await client.post(f"/api/functions/?study_id={study}", json={"name": name, **kw})
    assert r.status_code == 200, r.text
    return r.json()


async def test_function_crud_and_versioning(client, study_obj, study):
    fn = await _fn(client, study, "Acquire imagery", layer="SA", level=1)
    assert fn["study_id"] == study and fn["version"] == 1 and fn["layer"] == "SA"

    r = await client.get(f"/api/functions/{fn['id']}")
    assert r.status_code == 200 and r.json()["ports"] == [] and r.json()["allocations"] == []

    r = await client.patch(f"/api/functions/{fn['id']}", json={"version": 1, "name": "Acquire images"})
    assert r.status_code == 200 and r.json()["version"] == 2 and r.json()["name"] == "Acquire images"

    r = await client.patch(f"/api/functions/{fn['id']}", json={"version": 1, "name": "stale"})
    assert r.status_code == 409

    r = await client.post(f"/api/functions/?study_id={study}", json={"name": "x", "layer": "XX"})
    assert r.status_code == 400
    r = await client.post(f"/api/functions/?study_id={study}", json={"name": "x", "parent_id": "nope"})
    assert r.status_code == 400

    r = await client.delete(f"/api/functions/{fn['id']}")
    assert r.status_code == 200 and r.json()["deleted"] is True
    assert (await client.get(f"/api/functions/{fn['id']}")).status_code == 404
    assert (await client.get(f"/api/studies/{study}/functions")).json() == []


async def test_tree_with_ports_and_allocations(client, study_obj, study):
    sc = await make_element(client, study, "Spacecraft", "system")
    eps = await make_element(client, study, "EPS", "subsystem", parent_id=sc["id"], subsystem_domain="eps")

    root = await _fn(client, study, "Provide mission", level=0)
    child = await _fn(client, study, "Generate power", parent_id=root["id"], level=1, is_leaf=True)
    la = await _fn(client, study, "Logical power", layer="LA")

    r = await client.post(f"/api/functions/{child['id']}/ports", json={"name": "power_out", "direction": "out"})
    assert r.status_code == 200
    port = r.json()
    assert port["function_id"] == child["id"]

    r = await client.post(f"/api/functions/{child['id']}/allocate", json={"element_id": eps["id"], "layer": "SA"})
    assert r.status_code == 200
    assert r.json()["element"]["name"] == "EPS"
    # upsert: same layer re-allocates instead of duplicating
    r = await client.post(f"/api/functions/{child['id']}/allocate", json={"element_id": sc["id"], "layer": "SA"})
    assert r.status_code == 200 and r.json()["element_id"] == sc["id"]
    allocs = (await client.get(f"/api/functions/{child['id']}/allocations")).json()
    assert len(allocs) == 1
    r = await client.post(f"/api/functions/{child['id']}/allocate", json={"element_id": "missing", "layer": "SA"})
    assert r.status_code == 400

    tree = (await client.get(f"/api/studies/{study}/functions/tree")).json()
    assert [n["name"] for n in tree] == ["Provide mission", "Logical power"]
    node = tree[0]["children"][0]
    assert node["name"] == "Generate power"
    assert node["ports"][0]["name"] == "power_out"
    assert node["allocations"][0]["element"]["id"] == sc["id"]
    assert tree[0]["children"][0]["children"] == []

    sa_only = (await client.get(f"/api/studies/{study}/functions/tree?layer=SA")).json()
    assert [n["name"] for n in sa_only] == ["Provide mission"]
    flat = (await client.get(f"/api/studies/{study}/functions?layer=LA")).json()
    assert [f["id"] for f in flat] == [la["id"]]

    by_el = (await client.get(f"/api/elements/{sc['id']}/functions")).json()
    assert [f["id"] for f in by_el] == [child["id"]]

    r = await client.delete(f"/api/functions/{child['id']}/allocate/SA")
    assert r.status_code == 200 and r.json()["unallocated"] is True
    assert (await client.delete(f"/api/functions/{child['id']}/allocate/SA")).status_code == 404

    # parent move + cycle guard
    r = await client.patch(f"/api/functions/{root['id']}", json={"version": 1, "parent_id": child["id"]})
    assert r.status_code == 400
    # cascade delete: root removes child and its port
    r = await client.delete(f"/api/functions/{root['id']}")
    assert r.json()["children_deleted"] == 1 and r.json()["ports_deleted"] == 1
    assert [f["id"] for f in (await client.get(f"/api/studies/{study}/functions")).json()] == [la["id"]]


async def test_functional_exchanges_and_realizations(client, study_obj, study):
    a = await _fn(client, study, "Sense")
    b = await _fn(client, study, "Process")
    pa = (await client.post(f"/api/functions/{a['id']}/ports", json={"name": "out", "direction": "out"})).json()
    pb = (await client.post(f"/api/functions/{b['id']}/ports", json={"name": "in", "direction": "in"})).json()

    r = await client.post(f"/api/functional-exchanges/?study_id={study}", json={
        "name": "raw frames", "from_port_id": pa["id"], "to_port_id": pb["id"],
    })
    assert r.status_code == 200, r.text
    fx = r.json()
    assert (await client.get(f"/api/functional-exchanges/{fx['id']}")).json()["name"] == "raw frames"
    r = await client.patch(f"/api/functional-exchanges/{fx['id']}", json={"name": "frames", "version": fx["version"]})
    assert r.status_code == 200 and r.json()["name"] == "frames"
    assert len((await client.get(f"/api/studies/{study}/functional-exchanges")).json()) == 1
    r = await client.post(f"/api/functional-exchanges/?study_id={study}", json={
        "from_port_id": pa["id"], "to_port_id": "ghost"})
    assert r.status_code == 404

    pa_fn = await _fn(client, study, "Physical sense", layer="PA")
    r = await client.post(f"/api/realizations/?study_id={study}", json={
        "source_kind": "function", "source_id": a["id"], "target_kind": "function", "target_id": pa_fn["id"]})
    assert r.status_code == 200
    rz = r.json()
    again = (await client.post(f"/api/realizations/?study_id={study}", json={
        "source_kind": "function", "source_id": a["id"], "target_kind": "function", "target_id": pa_fn["id"]})).json()
    assert again["id"] == rz["id"]
    assert len((await client.get(f"/api/studies/{study}/realizations")).json()) == 1
    assert len((await client.get(f"/api/realizations/for/function/{pa_fn['id']}")).json()) == 1
    assert (await client.delete(f"/api/realizations/{rz['id']}")).json()["deleted"] is True
    assert (await client.get(f"/api/studies/{study}/realizations")).json() == []

    # deleting a function with ports removes the exchange too
    r = await client.delete(f"/api/functions/{a['id']}")
    assert r.json()["exchanges_deleted"] == 1
    assert (await client.get(f"/api/studies/{study}/functional-exchanges")).json() == []


async def test_migrate_legacy(client, study_obj, study):
    from spacecdf_common.models.functions import Function, FunctionalDecomposition, FunctionType

    sc = await make_element(client, study, "Spacecraft", "system")
    eps = await make_element(client, study, "EPS", "subsystem", parent_id=sc["id"], subsystem_domain="eps")
    study_obj.functional_decomposition = FunctionalDecomposition(functions=[
        Function(id="F-001", name="Observe", function_type=FunctionType.OBSERVE, level=0),
        Function(id="F-002", name="Generate power", parent_function_id="F-001", allocated_to="power",
                 level=1, is_leaf=True),
    ])

    r = await client.post(f"/api/studies/{study}/functions/migrate-legacy")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["legacy_functions"] == 2 and body["functions_created"] == 2 and body["allocations"] == 1

    tree = (await client.get(f"/api/studies/{study}/functions/tree")).json()
    assert len(tree) == 1 and tree[0]["external_ids"]["legacy"] == "F-001"
    child = tree[0]["children"][0]
    assert child["name"] == "Generate power"
    assert child["allocations"][0]["element_id"] == eps["id"]

    # idempotent
    body2 = (await client.post(f"/api/studies/{study}/functions/migrate-legacy")).json()
    assert body2["functions_created"] == 0 and body2["functions_updated"] == 2
    assert len((await client.get(f"/api/studies/{study}/functions")).json()) == 2

    assert (await client.post("/api/studies/nope/functions/migrate-legacy")).status_code == 404


async def test_lifecycle_prefers_rows(client, study_obj, study):
    """routers.lifecycle._study_functions: legacy passthrough, then rows win."""
    from spacecdf_common.models.functions import Function, FunctionalDecomposition
    from spacecdf_server.routers.lifecycle import _study_functions

    study_obj.functional_decomposition = FunctionalDecomposition(functions=[
        Function(id="F-001", name="Legacy", allocated_to="power", level=0),
    ])
    legacy = await _study_functions(study, study_obj)
    assert legacy == [f.model_dump() for f in study_obj.functional_decomposition.functions]

    eps = await make_element(client, study, "EPS", "subsystem", subsystem_domain="eps")
    fn = await _fn(client, study, "Row function")
    await client.post(f"/api/functions/{fn['id']}/allocate", json={"element_id": eps["id"], "layer": "SA"})
    rows = await _study_functions(study, study_obj)
    assert [r["name"] for r in rows] == ["Row function"]
    assert rows[0]["parent_function_id"] is None and rows[0]["allocated_to"] == "eps"
    assert rows[0]["derived_requirement_ids"] == []


async def test_lifecycle_consistency_reads_functions_from_rows_and_legacy(client):
    """SCDF-160 verification regression: /lifecycle/consistency/{id} 500'd on every study
    (it iterated ``study.requirements`` — the MissionRequirements input model — as if it
    were the requirement list). It must answer for a study with only legacy JSON functions
    and for one with FunctionRows."""
    r = await client.post("/api/studies/", json={
        "requirements": {"name": "Consistency"},
        "mission_need": {"problem_statement": "p", "objectives": [
            {"id": "O1", "text": "Image the UK", "priority": "primary", "type": "performance"}]},
    })
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    assert r.json()["functions"] > 0  # legacy JSON functions generated from the objective
    assert (await client.get(f"/api/studies/{sid}/functions")).json() == []

    await client.post("/api/requirements/", json={"id": "MR-C", "study_id": sid, "level": "mission",
                                                  "text": "The mission shall image the UK.", "objective_id": "O1"})
    legacy = await client.get(f"/api/lifecycle/consistency/{sid}")
    assert legacy.status_code == 200, legacy.text
    assert legacy.json()["total_checks"] > 0

    m = await client.post(f"/api/studies/{sid}/functions/migrate-legacy")
    assert m.status_code == 200 and m.json()["functions_created"] > 0
    rows = await client.get(f"/api/lifecycle/consistency/{sid}")
    assert rows.status_code == 200, rows.text
    assert rows.json()["total_checks"] == legacy.json()["total_checks"]
