"""Options API (SCDF-172): create / branch / rename / delete, an override
written into an option shadows the baseline through the parameters routes,
compare reports the delta, a design run with ``?option_id=`` publishes an
option-scoped run and leaves the baseline alone."""
from __future__ import annotations

import pytest

from tests.test_api.conftest import make_element


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SPACECDF_DATA_DIR", str(tmp_path / "data"))
    from spacecdf_server.services import analysis_results
    analysis_results.reset_trackers()
    yield
    analysis_results.reset_trackers()


async def _tree(client, study):
    await client.post("/api/parameters/definitions/seed")
    mission = await make_element(client, study, "Mission", "mission")
    seg = await make_element(client, study, "Space Segment", "segment", mission["id"])
    sc = await make_element(client, study, "Spacecraft", "system", seg["id"])
    eps = await make_element(client, study, "EPS", "subsystem", sc["id"], "power")
    aocs = await make_element(client, study, "AOCS", "subsystem", sc["id"], "aocs")

    async def comp(name, parent, domain, **kw):
        r = await client.post(f"/api/elements/?study_id={study}", json={
            "name": name, "element_type": "component", "parent_id": parent, "subsystem_domain": domain, **kw})
        assert r.status_code == 200, r.text
        return r.json()

    bat = await comp("Battery", eps["id"], "power", mass_kg=1.0, power_avg_w=0.2, performance={"capacity_wh": 40.0})
    await comp("PCDU", eps["id"], "power", mass_kg=0.5, power_avg_w=1.0)
    rw = await comp("Wheel", aocs["id"], "aocs", mass_kg=0.4, power_avg_w=2.0)
    r = await client.put(f"/api/elements/{eps['id']}/parameters/mass_kg",
                         json={"formula": 'children("mass_kg")', "formula_kind": "ref"})
    assert r.status_code == 200, r.text
    return {"mission": mission, "sc": sc, "eps": eps, "aocs": aocs, "bat": bat, "rw": rw}


async def _param(client, eid, name, option_id=None):
    q = f"?option_id={option_id}" if option_id else ""
    r = await client.get(f"/api/elements/{eid}/parameters{q}")
    assert r.status_code == 200, r.text
    return next((p for p in r.json() if p["name"] == name), None)


async def _create(client, study, name, **extra):
    r = await client.post(f"/api/studies/{study}/options", json={"name": name, **extra})
    assert r.status_code == 200, r.text
    return r.json()


async def test_crud_and_baseline(client, study_obj, study):
    r = await client.get(f"/api/studies/{study}/options")
    assert r.status_code == 200 and len(r.json()) == 1 and r.json()[0]["is_baseline"]
    baseline = r.json()[0]
    a = await _create(client, study, "Option A", description="bigger battery")
    assert not a["is_baseline"] and a["description"] == "bigger battery"
    assert (await client.post(f"/api/studies/{study}/options", json={"name": " "})).status_code == 400
    r = await client.get(f"/api/studies/{study}/options")
    assert [o["id"] for o in r.json()] == [baseline["id"], a["id"]]
    r = await client.patch(f"/api/options/{a['id']}", json={"name": "A renamed"})
    assert r.status_code == 200 and r.json()["name"] == "A renamed"
    assert (await client.get(f"/api/options/{a['id']}")).json()["name"] == "A renamed"
    assert (await client.patch("/api/options/ghost", json={"name": "x"})).status_code == 404
    assert (await client.delete(f"/api/options/{baseline['id']}")).status_code == 409
    r = await client.delete(f"/api/options/{a['id']}")
    assert r.status_code == 200 and r.json()["deleted"] is True
    assert (await client.get(f"/api/options/{a['id']}")).status_code == 404
    assert len((await client.get(f"/api/studies/{study}/options")).json()) == 1


async def test_override_in_option_shadows_baseline_via_parameters(client, study_obj, study):
    els = await _tree(client, study)
    bat, eps = els["bat"]["id"], els["eps"]["id"]
    a = await _create(client, study, "A")

    # write into the option
    r = await client.put(f"/api/elements/{bat}/parameters/mass_kg?option_id={a['id']}", json={"manual_value": 3.0})
    assert r.status_code == 200, r.text
    assert r.json()["effective_value"] == 3.0 and r.json()["option_id"] == a["id"]
    assert (await client.put(f"/api/elements/{bat}/parameters/mass_kg?option_id=ghost", json={"manual_value": 3.0})).status_code == 404

    # option read: override + baseline formula sees it; baseline read: untouched
    p = await _param(client, bat, "mass_kg", a["id"])
    assert p["effective_value"] == 3.0 and p["provenance"] == "manual" and p["option_id"] == a["id"]
    assert (await _param(client, eps, "mass_kg", a["id"]))["effective_value"] == pytest.approx(3.5)
    assert (await _param(client, eps, "mass_kg", a["id"]))["option_id"] is None
    assert (await _param(client, bat, "mass_kg"))["effective_value"] == 1.0
    assert (await _param(client, bat, "mass_kg"))["option_id"] is None
    assert (await _param(client, eps, "mass_kg"))["effective_value"] == pytest.approx(1.5)
    assert (await client.get(f"/api/elements/{bat}")).json()["mass_kg"] == 1.0    # column = baseline
    # the baseline option's id reads as the baseline
    baseline = next(o for o in (await client.get(f"/api/studies/{study}/options")).json() if o["is_baseline"])
    assert (await _param(client, bat, "mass_kg", baseline["id"]))["effective_value"] == 1.0
    # study-level list honours option_id
    r = await client.get(f"/api/studies/{study}/parameters?element_id={bat}&name=mass_kg&option_id={a['id']}")
    assert r.json()[0]["effective_value"] == 3.0
    r = await client.get(f"/api/studies/{study}/parameters?element_id={bat}&name=mass_kg")
    assert r.json()[0]["effective_value"] == 1.0

    # overrides listing
    r = await client.get(f"/api/studies/{study}/options/{a['id']}/overrides")
    assert r.status_code == 200 and [(o["element_id"], o["name"]) for o in r.json()] == [(bat, "mass_kg")]
    assert (await client.get(f"/api/studies/{study}/options/{baseline['id']}/overrides")).json() == []

    # branch A -> B copies the override; B diverges without touching A
    r = await client.post(f"/api/options/{a['id']}/branch", json={"name": "B"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["copied"] == 1 and b["branched_from_option_id"] == a["id"]
    assert (await _param(client, bat, "mass_kg", b["id"]))["effective_value"] == 3.0
    r = await client.put(f"/api/elements/{bat}/parameters/mass_kg?option_id={b['id']}", json={"manual_value": 4.0})
    assert r.status_code == 200
    assert (await _param(client, bat, "mass_kg", a["id"]))["effective_value"] == 3.0
    assert (await _param(client, bat, "mass_kg", b["id"]))["effective_value"] == 4.0
    # create with branch_from does the same
    c = await _create(client, study, "C", branch_from=b["id"])
    assert c["copied"] == 1 and (await _param(client, bat, "mass_kg", c["id"]))["effective_value"] == 4.0

    # deleting the override in the option lets the baseline show through
    r = await client.delete(f"/api/elements/{bat}/parameters/mass_kg?option_id={b['id']}")
    assert r.status_code == 200 and r.json()["deleted"] is True and r.json()["option_id"] == b["id"]
    assert (await _param(client, bat, "mass_kg", b["id"]))["effective_value"] == 1.0
    assert (await client.delete(f"/api/elements/{bat}/parameters/mass_kg?option_id={b['id']}")).status_code == 404
    assert (await _param(client, bat, "mass_kg"))["effective_value"] == 1.0

    # deleting an option removes its overrides
    assert (await client.delete(f"/api/options/{a['id']}")).status_code == 200
    r = await client.get(f"/api/studies/{study}/options/compare?a={a['id']}&b={c['id']}")
    assert r.status_code == 404


async def test_compare_shows_deltas(client, study_obj, study):
    els = await _tree(client, study)
    bat = els["bat"]["id"]
    a = await _create(client, study, "A")
    r = await client.put(f"/api/elements/{bat}/parameters/mass_kg?option_id={a['id']}", json={"manual_value": 3.0})
    assert r.status_code == 200

    r = await client.get(f"/api/studies/{study}/options/compare?b={a['id']}")   # a = baseline
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["a"]["option_id"] is None and body["a"]["name"] == "Baseline" and body["b"]["id"] == a["id"]
    rows = {(p["element"], p["name"]): p for p in body["parameters"]}
    assert rows[("Battery", "mass_kg")]["a"] == 1.0 and rows[("Battery", "mass_kg")]["b"] == 3.0
    assert rows[("Battery", "mass_kg")]["delta"] == pytest.approx(2.0)
    assert rows[("Battery", "mass_kg")]["unit"] == "kg" and rows[("Battery", "mass_kg")]["b_override"] is True
    assert rows[("EPS", "mass_kg")]["delta"] == pytest.approx(2.0) and rows[("EPS", "mass_kg")]["b_override"] is False
    assert ("Wheel", "mass_kg") not in rows
    assert body["analyses"] == [] and body["conflicts"] == {"a": 0, "b": 0}
    # same option on both sides -> nothing differs
    r = await client.get(f"/api/studies/{study}/options/compare?a={a['id']}&b={a['id']}")
    assert r.json()["parameters"] == []
    assert (await client.get(f"/api/studies/{study}/options/compare?a=ghost")).status_code == 404


async def test_design_run_with_option_is_scoped_and_baseline_unaffected(client, study_obj, study):
    els = await _tree(client, study)
    bat, eps, mission = els["bat"]["id"], els["eps"]["id"], els["mission"]["id"]
    a = await _create(client, study, "A")
    r = await client.put(f"/api/elements/{bat}/parameters/mass_kg?option_id={a['id']}", json={"manual_value": 6.0})
    assert r.status_code == 200

    # baseline run first
    r = await client.post(f"/api/design/{study}/run", json={"max_iterations": 12})
    assert r.status_code == 200, r.text
    base_dry = r.json()["parameters"]["mass.dry_mass_kg"]["value"]
    base_root = await _param(client, mission, "mass_dry_mass_kg")
    assert base_root is not None and base_root["option_id"] is None

    # option run: sticky override from the option, results published under the option
    r = await client.post(f"/api/design/{study}/run?option_id={a['id']}", json={"max_iterations": 12})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["parameters"]["power.eps_mass_kg"]["source"] == "position_override"
    assert body["parameters"]["power.eps_mass_kg"]["value"] == pytest.approx(6.5)
    opt_dry = body["parameters"]["mass.dry_mass_kg"]["value"]
    assert opt_dry > base_dry

    r = await client.get(f"/api/studies/{study}/analyses?option_id={a['id']}")
    runs = {x["analysis"]: x for x in r.json()}
    assert runs["design_loop"]["option_id"] == a["id"] and runs["design_loop"]["status"] == "ok"
    r = await client.get(f"/api/studies/{study}/analyses")
    assert {x["analysis"]: x for x in r.json()}["design_loop"]["option_id"] is None

    # option-scoped parameter rows, baseline rows and columns unchanged
    opt_root = await _param(client, mission, "mass_dry_mass_kg", a["id"])
    assert opt_root["option_id"] == a["id"] and opt_root["effective_value"] == pytest.approx(opt_dry, rel=1e-6)
    base_root_after = await _param(client, mission, "mass_dry_mass_kg")
    assert base_root_after["effective_value"] == pytest.approx(base_root["effective_value"], rel=1e-6)
    assert base_root_after["option_id"] is None
    assert (await _param(client, bat, "mass_kg"))["effective_value"] == 1.0
    assert (await client.get(f"/api/elements/{bat}")).json()["mass_kg"] == 1.0
    assert (await _param(client, eps, "mass_kg", a["id"]))["effective_value"] == pytest.approx(6.5)
    assert (await _param(client, eps, "mass_kg"))["effective_value"] == pytest.approx(1.5)

    # compare sees both the parameter and the analysis delta
    r = await client.get(f"/api/studies/{study}/options/compare?b={a['id']}")
    body = r.json()
    ana = {x["analysis"]: x for x in body["analyses"]}
    assert ana["design_loop"]["a_run_id"] and ana["design_loop"]["b_run_id"]
    assert any(d["key"].startswith("budgets.mass") for d in ana["design_loop"]["deltas"])
    assert any(p["name"] == "mass_dry_mass_kg" and p["delta"] > 0 for p in body["parameters"])
