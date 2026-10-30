"""SCDF-171 — the design loop is coupled to the model.

* a manual override on a component's ``mass_kg`` reaches the power/mass agents
  (sticky ``power.eps_mass_kg``): the EPS subsystem parameter and
  ``mass.dry_mass_kg`` follow it;
* a ``ref`` formula on the AOCS subsystem ``power_avg_w`` (a power-agent input
  through ``aocs.power_w``) changes the solar-array area;
* the run is recorded in ``analysis_runs`` (stale after an input change) and
  its conflicts are served by ``GET /api/studies/{id}/conflicts``.
"""
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

    bat = await comp("Battery", eps["id"], "power", mass_kg=1.0, power_avg_w=0.2,
                     performance={"capacity_wh": 40.0})
    await comp("PCDU", eps["id"], "power", mass_kg=0.5, power_avg_w=1.0)
    rw = await comp("Wheel", aocs["id"], "aocs", mass_kg=0.4, power_avg_w=2.0)
    return {"mission": mission, "eps": eps, "aocs": aocs, "bat": bat, "rw": rw}


async def _run(client, study):
    r = await client.post(f"/api/design/{study}/run", json={"max_iterations": 12})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) >= {"converged", "iterations", "parameters", "budgets", "warnings", "recommendations", "conflicts"}
    return body


async def _param(client, eid, name):
    r = await client.get(f"/api/elements/{eid}/parameters")
    assert r.status_code == 200
    return next((p for p in r.json() if p["name"] == name), None)


async def test_component_mass_override_drives_subsystem_and_dry_mass(client, study_obj, study):
    els = await _tree(client, study)
    base = await _run(client, study)
    base_eps = base["parameters"]["power.eps_mass_kg"]
    base_dry = base["parameters"]["mass.dry_mass_kg"]["value"]
    assert base_eps["source"] == "computed"                 # agents own it when nothing is overridden

    # EPS subsystem parameter written back by the loop (agent provenance)
    eps_param = await _param(client, els["eps"]["id"], "mass_kg")
    assert eps_param is not None and eps_param["owner_domain"] == "design_loop"
    assert eps_param["effective_value"] == pytest.approx(base_eps["value"], rel=1e-6)
    root = await _param(client, els["mission"]["id"], "mass_dry_mass_kg")
    assert root is not None and root["effective_value"] == pytest.approx(base_dry, rel=1e-6)

    # override the battery mass -> EPS aggregate becomes sticky
    r = await client.put(f"/api/elements/{els['bat']['id']}/parameters/mass_kg", json={"manual_value": 6.0})
    assert r.status_code == 200, r.text
    after = await _run(client, study)
    eps_after = after["parameters"]["power.eps_mass_kg"]
    assert eps_after["source"] == "position_override"
    assert eps_after["value"] == pytest.approx(6.5)                       # 6.0 battery + 0.5 PCDU
    dry_after = after["parameters"]["mass.dry_mass_kg"]["value"]
    assert dry_after != pytest.approx(base_dry) and dry_after > base_dry - 1e-9 + (6.5 - base_eps["value"]) * 0.5

    eps_param = await _param(client, els["eps"]["id"], "mass_kg")
    assert eps_param["effective_value"] == pytest.approx(6.5)
    assert after["budgets"]["mass"]["total_with_margin"] != pytest.approx(base["budgets"]["mass"]["total_with_margin"])


async def test_ref_formula_on_power_input_changes_sa_area(client, study_obj, study):
    els = await _tree(client, study)
    base = await _run(client, study)
    base_area = base["parameters"]["power.sa_area_m2"]["value"]
    assert base["parameters"]["aocs.power_w"]["source"] == "computed"

    # AOCS power = 10x the wheel power (formula on the subsystem feeds aocs.power_w -> power agent input)
    r = await client.put(f"/api/elements/{els['aocs']['id']}/parameters/power_avg_w",
                         json={"formula": 'el("Wheel").power_avg_w * 25', "formula_kind": "ref"})
    assert r.status_code == 200, r.text
    assert r.json()["effective_value"] == pytest.approx(50.0)

    after = await _run(client, study)
    assert after["parameters"]["aocs.power_w"]["source"] == "position_override"
    assert after["parameters"]["aocs.power_w"]["value"] == pytest.approx(50.0)
    assert after["parameters"]["power.sa_area_m2"]["value"] > base_area * 1.5


async def test_run_recorded_and_conflicts_served(client, study_obj, study):
    els = await _tree(client, study)
    r = await client.get(f"/api/studies/{study}/analyses")
    assert r.status_code == 200 and r.json() == []

    await _run(client, study)
    r = await client.get(f"/api/studies/{study}/analyses")
    runs = {x["analysis"]: x for x in r.json()}
    assert runs["design_loop"]["status"] == "ok" and runs["design_loop"]["stale"] is False
    assert runs["design_loop"]["summary"]["parameters_written"] > 0
    r = await client.get(f"/api/studies/{study}/analyses/design_loop")
    assert r.status_code == 200 and r.json()["id"] == runs["design_loop"]["id"]
    assert (await client.get(f"/api/studies/{study}/analyses/nope")).status_code == 404

    r = await client.get(f"/api/studies/{study}/conflicts")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"study_id", "option_id", "design", "analysis"} and body["analysis"] == []
    assert all(c["analysis"] == "design_loop" for c in body["design"])

    # an input change flags the run stale
    r = await client.put(f"/api/elements/{els['bat']['id']}/parameters/mass_kg", json={"manual_value": 2.0})
    assert r.status_code == 200
    r = await client.get(f"/api/studies/{study}/analyses/design_loop")
    assert r.json()["stale"] is True

    # conflicts can be resolved through the API
    from spacecdf_server.services.analysis_results import Conflict, ResultsSink
    res = await ResultsSink().publish(study, "ground", conflicts=[Conflict("warning", "MARGIN", "Low margin")])
    r = await client.get(f"/api/studies/{study}/conflicts")
    assert [c["code"] for c in r.json()["analysis"]] == ["MARGIN"]
    r = await client.post(f"/api/conflicts/{res.conflicts[0]['id']}/resolve")
    assert r.status_code == 200 and r.json()["resolved"] is True
    assert (await client.get(f"/api/studies/{study}/conflicts")).json()["analysis"] == []
    assert (await client.post("/api/conflicts/cf-nope/resolve")).status_code == 404
