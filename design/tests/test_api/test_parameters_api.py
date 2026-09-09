"""Parameters API tests (SCDF-160 §3): definitions seed, PUT formula -> effective
value, manual switch overrides computed (and writes back to the element column),
graph endpoint, recompute, delete, element PATCH re-evaluates dependents."""
from __future__ import annotations

from tests.test_api.conftest import make_element


async def _put(client, eid, name, **body):
    r = await client.put(f"/api/elements/{eid}/parameters/{name}", json=body)
    assert r.status_code == 200, r.text
    return r.json()


async def _get(client, eid, name):
    r = await client.get(f"/api/elements/{eid}/parameters")
    assert r.status_code == 200, r.text
    return next(p for p in r.json() if p["name"] == name)


async def _tree(client, study):
    await client.post("/api/parameters/definitions/seed")   # lifespan does this in production
    sc = await make_element(client, study, "Spacecraft", "system")
    r = await client.post(f"/api/elements/?study_id={study}", json={
        "name": "EPS", "element_type": "subsystem", "parent_id": sc["id"],
        "subsystem_domain": "eps", "mass_kg": 4.0, "power_avg_w": 10.0})
    eps = r.json()
    r = await client.post(f"/api/elements/?study_id={study}", json={
        "name": "AOCS", "element_type": "subsystem", "parent_id": sc["id"],
        "subsystem_domain": "aocs", "mass_kg": 6.0, "power_avg_w": 5.0})
    return sc, eps, r.json()


async def test_definitions_seed_and_list(client, study_obj, study):
    r = await client.post("/api/parameters/definitions/seed")
    assert r.status_code == 200 and r.json()["created"] > 0 and r.json()["total"] == r.json()["created"]
    r = await client.get("/api/parameters/definitions?well_known_only=true")
    names = {d["name"] for d in r.json()}
    assert {"mass_kg", "power_avg_w", "cost_recurring_keur"} <= names
    assert next(d for d in r.json() if d["name"] == "mass_kg")["unit"] == "kg"
    r = await client.get("/api/parameters/definitions")
    assert len(r.json()) > len(names)


async def test_put_formula_gives_effective_value(client, study_obj, study):
    sc, eps, aocs = await _tree(client, study)
    p = await _put(client, sc["id"], "mass_kg", formula='children("mass_kg")', formula_kind="ref")
    assert p["effective_value"] == 10.0 and p["formula"] == 'children("mass_kg")'
    assert p["formula_kind"] == "ref" and p["provenance"] == "formula" and p["errors"] == []
    assert p["unit"] == "kg" and p["value_switch"] == "computed"
    # ref + well-known: column written back so the elements cache sees it
    r = await client.get(f"/api/elements/{sc['id']}")
    assert r.json()["mass_kg"] == 10.0
    # calc formula with a new definition created on the fly
    p = await _put(client, sc["id"], "mass_margin_kg", formula='mass_kg * 0.2', formula_kind="calc",
                   unit="kg", quantity_kind="mass")
    assert p["effective_value"] == 2.0 and p["unit"] == "kg" and p["computed_value"] == 2.0
    r = await client.get("/api/parameters/definitions")
    assert any(d["name"] == "mass_margin_kg" and d["unit"] == "kg" for d in r.json())
    # flat study list + filters
    r = await client.get(f"/api/studies/{study}/parameters")
    assert {p["name"] for p in r.json()} >= {"mass_kg", "power_avg_w", "mass_margin_kg"}
    r = await client.get(f"/api/studies/{study}/parameters?element_id={sc['id']}&name=mass_kg")
    assert len(r.json()) == 1 and r.json()[0]["effective_value"] == 10.0
    # invalid formula -> 400, bad switch -> 400, unknown element -> 404
    r = await client.put(f"/api/elements/{sc['id']}/parameters/x", json={"formula": "open('f')"})
    assert r.status_code == 400
    r = await client.put(f"/api/elements/{sc['id']}/parameters/x", json={"value_switch": "bogus"})
    assert r.status_code == 400
    r = await client.put("/api/elements/ghost/parameters/x", json={"manual_value": 1})
    assert r.status_code == 404


async def test_manual_switch_overrides_computed_and_writes_back(client, study_obj, study):
    sc, eps, aocs = await _tree(client, study)
    await _put(client, sc["id"], "mass_kg", formula='children("mass_kg")', formula_kind="ref")
    p = await _put(client, eps["id"], "mass_kg", manual_value=1.5)   # switch inferred
    assert p["value_switch"] == "manual" and p["effective_value"] == 1.5 and p["provenance"] == "manual"
    r = await client.get(f"/api/elements/{eps['id']}")
    assert r.json()["mass_kg"] == 1.5
    # the column write-back is mirrored into computed_value (column <-> computed stay one number)
    assert (await _get(client, eps["id"], "mass_kg"))["computed_value"] == 1.5
    assert (await _get(client, sc["id"], "mass_kg"))["effective_value"] == 7.5
    # flip back to computed: the formula value / column mirror wins again
    p = await _put(client, eps["id"], "mass_kg", value_switch="computed")
    assert p["effective_value"] == 1.5 and p["provenance"] == "column"  # column is now 1.5
    assert (await _get(client, sc["id"], "mass_kg"))["effective_value"] == 7.5


async def test_element_patch_reevaluates_dependents(client, study_obj, study):
    sc, eps, aocs = await _tree(client, study)
    await _put(client, sc["id"], "mass_kg", formula='children("mass_kg")', formula_kind="ref")
    r = await client.patch(f"/api/elements/{aocs['id']}", json={"version": aocs["version"], "mass_kg": 9.0})
    assert r.status_code == 200
    assert (await _get(client, sc["id"], "mass_kg"))["effective_value"] == 13.0
    assert (await client.get(f"/api/elements/{sc['id']}")).json()["mass_kg"] == 13.0


async def test_graph_and_cycles(client, study_obj, study):
    sc, eps, aocs = await _tree(client, study)
    await _put(client, eps["id"], "x", formula='el("AOCS").x + 1', formula_kind="ref")
    await _put(client, aocs["id"], "x", formula='el("EPS").x + 1', formula_kind="ref")
    await _put(client, sc["id"], "mass_kg", formula='children("mass_kg")', formula_kind="ref")
    r = await client.get(f"/api/studies/{study}/parameters/graph")
    assert r.status_code == 200
    g = r.json()
    assert len(g["cycles"]) == 1 and set(g["cycles"][0][:2]) == {f"{eps['id']}:x", f"{aocs['id']}:x"}
    ids = {n["id"] for n in g["nodes"]}
    assert {f"{sc['id']}:mass_kg", f"{eps['id']}:mass_kg", f"{aocs['id']}:mass_kg"} <= ids
    assert {"from": f"{eps['id']}:mass_kg", "to": f"{sc['id']}:mass_kg"} in g["edges"]
    p = await _get(client, eps["id"], "x")
    assert p["effective_value"] is None and any("circular" in e for e in p["errors"])


async def test_recompute_and_delete(client, study_obj, study):
    sc, eps, aocs = await _tree(client, study)
    await _put(client, sc["id"], "mass_kg", formula='children("mass_kg")', formula_kind="ref")
    await _put(client, sc["id"], "note_w", formula='el("EPS").power_avg_w + el("AOCS").power_avg_w',
               formula_kind="calc")
    r = await client.post(f"/api/studies/{study}/parameters/recompute")
    assert r.status_code == 200
    body = r.json()
    assert body["persisted"] == 0 and body["errors"] == [] and body["cycles"] == []
    assert next(p for p in body["parameters"] if p["name"] == "note_w")["effective_value"] == 15.0
    # delete: custom parameter goes away, well-known one is reset (formula cleared) not deleted
    r = await client.delete(f"/api/elements/{sc['id']}/parameters/note_w")
    assert r.status_code == 200 and r.json()["deleted"] is True
    assert all(p["name"] != "note_w" for p in (await client.get(f"/api/elements/{sc['id']}/parameters")).json())
    r = await client.delete(f"/api/elements/{sc['id']}/parameters/mass_kg")
    assert r.status_code == 200 and r.json()["reset"] is True
    p = await _get(client, sc["id"], "mass_kg")
    assert p["formula"] is None and p["provenance"] == "column" and p["effective_value"] == 10.0
    r = await client.delete(f"/api/elements/{sc['id']}/parameters/never_set")
    assert r.status_code == 404
