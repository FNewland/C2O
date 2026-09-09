"""Requirements survive a server restart (SCDF-160 verification finding N0).

``routers.requirements`` is a write-through cache over the ``requirements``
table. A restart is simulated by ``reset_requirement_cache()`` (drops the
in-memory dict and the loaded flag); the next request re-hydrates from the DB.
"""
from __future__ import annotations

from tests.test_api.conftest import make_element, make_requirement


def _restart():
    from spacecdf_server.routers import requirements
    requirements.reset_requirement_cache()
    assert requirements._requirements == {}


async def test_create_survives_restart(client, study_obj, study):
    created = await make_requirement(client, study, "MR-1", level="mission", objective_id="OBJ-1",
                                     verification_method="analysis", threshold_param_path="mass.total_kg",
                                     threshold_op="<=", threshold_value=12, external_id="CUST-7")
    assert created["objective_id"] == "OBJ-1"

    _restart()

    r = await client.get("/api/requirements/MR-1")
    assert r.status_code == 200, r.text
    got = r.json()
    for k in ("id", "study_id", "level", "code", "text", "objective_id", "verification_method",
              "threshold_param_path", "threshold_op", "status"):
        assert got[k] == created[k], k
    assert got["threshold_value"] == "12"  # JSON-encoded Text column
    assert got["external_id"] == "CUST-7"
    tree = (await client.get(f"/api/requirements/tree?study_id={study}")).json()
    assert [t["id"] for t in tree] == ["MR-1"]


async def test_patch_derive_and_delete_survive_restart(client, study_obj, study):
    sc = await make_element(client, study, "Spacecraft", "system")
    await make_requirement(client, study, "MR-1", level="mission")
    d = await client.post("/api/requirements/MR-1/derive", json={"id": "SR-1", "text": "derived"})
    assert d.status_code == 200, d.text
    assert d.json()["parent_id"] == "MR-1" and d.json()["level"] == "system"
    await make_requirement(client, study, "SR-2", level="system", parent_id="MR-1")

    p = await client.patch("/api/requirements/SR-1", json={"text": "patched", "element_id": sc["id"],
                                                          "status": "approved", "objective_id": "OBJ-9"})
    assert p.status_code == 200, p.text
    assert (await client.delete("/api/requirements/SR-2")).json()["status"] == "retired"

    _restart()

    sr1 = (await client.get("/api/requirements/SR-1")).json()
    assert sr1["text"] == "patched" and sr1["element_id"] == sc["id"]
    assert sr1["status"] == "approved" and sr1["objective_id"] == "OBJ-9"
    assert sr1["parent_id"] == "MR-1" and sr1["derived_from_requirement_id"] == "MR-1"

    # retired requirement is still addressable but hidden from the tree
    assert (await client.get("/api/requirements/SR-2")).json()["status"] == "retired"
    tree = (await client.get(f"/api/requirements/tree?study_id={study}")).json()
    assert sorted(t["id"] for t in tree) == ["MR-1", "SR-1"]

    # element filter and verify endpoints work on the re-hydrated cache
    by_el = (await client.get(f"/api/requirements/tree?study_id={study}&element_id={sc['id']}")).json()
    assert [t["id"] for t in by_el] == ["SR-1"]
    assert (await client.get(f"/api/requirements/verify?study_id={study}")).json()["total"] == 2

    # deriving from a re-hydrated parent works (parent lookup hits the cache)
    d2 = await client.post("/api/requirements/SR-1/derive", json={"id": "SSR-1", "text": "child"})
    assert d2.status_code == 200, d2.text
    _restart()
    assert (await client.get("/api/requirements/SSR-1")).json()["parent_id"] == "SR-1"


async def test_traceability_tree_after_restart(client, study_obj, study):
    from spacecdf_common.models.mission_need import MissionNeed, Objective

    study_obj.mission_need = MissionNeed(objectives=[
        Objective(id="OBJ-1", text="Image crops", traced_to_requirements=["MR-1"]),
    ])
    sc = await make_element(client, study, "Spacecraft", "system")
    await make_requirement(client, study, "MR-1", level="mission")
    await make_requirement(client, study, "SR-1", level="system", parent_id="MR-1", element_id=sc["id"])
    await make_requirement(client, study, "SR-9", level="system", objective_id="OBJ-1")

    _restart()

    r = await client.get(f"/api/studies/{study}/traceability/tree")
    assert r.status_code == 200, r.text
    tree = r.json()
    assert tree["summary"]["requirements"] == 3
    assert tree["summary"]["requirements_by_level"] == {"mission": 1, "system": 2}
    obj = tree["objectives"][0]
    assert sorted(q["id"] for q in obj["requirements"]) == ["MR-1", "SR-9"]
    mr = next(q for q in obj["requirements"] if q["id"] == "MR-1")
    assert [c["id"] for c in mr["children"]] == ["SR-1"]
    assert mr["children"][0]["elements"][0]["id"] == sc["id"]
    assert tree["unlinked_requirements"] == []

    t = (await client.get("/api/requirements/SR-1/trace")).json()
    assert [p["id"] for p in t["up"]["parents"]] == ["MR-1"]


async def test_in_memory_state_wins_over_db_on_hydration(client, study_obj, study):
    """Lazy hydration must not clobber entries written in-process since the last load."""
    from spacecdf_server.routers import requirements

    await make_requirement(client, study, "MR-1", level="mission", text="v1")
    requirements._cache_loaded = False  # force a re-load without dropping the dict
    requirements._requirements["MR-1"]["text"] = "in-memory edit"
    got = (await client.get("/api/requirements/MR-1")).json()
    assert got["text"] == "in-memory edit"
