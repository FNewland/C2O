"""SCDF-173 — mission simulation over HTTP: run -> parameters on the mission
root, GET last run (+ conflicts), series bounded, stale flips after a PATCH of
a component's power, option-scoped runs are separate."""
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
    pl = await make_element(client, study, "Payload", "subsystem", sc["id"], "payload")

    async def comp(name, parent, domain, **kw):
        r = await client.post(f"/api/elements/?study_id={study}", json={
            "name": name, "element_type": "component", "parent_id": parent, "subsystem_domain": domain, **kw})
        assert r.status_code == 200, r.text
        return r.json()

    bat = await comp("Battery", eps["id"], "power", mass_kg=1.0, power_avg_w=0.2, performance={"capacity_wh": 40.0})
    await comp("Solar array", eps["id"], "power", mass_kg=0.8, power_avg_w=0.0, performance={"sa_power_eol_w": 16.0})
    await comp("PCDU", eps["id"], "power", mass_kg=0.5, power_avg_w=1.0)
    rw = await comp("Wheel", aocs["id"], "aocs", mass_kg=0.4, power_avg_w=2.0)
    cam = await comp("Camera", pl["id"], "payload", mass_kg=1.0, power_avg_w=4.0, performance={"data_rate_bps": 1e6})
    return {"mission": mission, "eps": eps, "bat": bat, "rw": rw, "cam": cam}


async def test_run_get_series_and_stale(client, study_obj, study):
    els = await _tree(client, study)
    assert (await client.get(f"/api/studies/{study}/analyses/mission_simulation")).status_code == 404

    r = await client.post(f"/api/studies/{study}/analyses/mission_simulation/run?n_orbits=3")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) >= {"run_id", "summary", "parameters", "conflicts", "warnings", "stale"}
    assert body["stale"] is False and body["status"] == "ok"
    names = [p["name"] for p in body["parameters"]]
    assert names == ["sim_min_soc_pct", "sim_max_dod_pct", "sim_energy_balance_wh_per_orbit", "sim_data_buffer_max_gb",
                     "sim_data_backlog_end_gb", "sim_heater_energy_wh_per_orbit", "sim_time_in_safe_pct", "sim_orbits"]
    assert all(p["element_id"] == els["mission"]["id"] for p in body["parameters"])
    assert body["summary"]["sim_orbits"] == 3 and body["summary"]["parameters_written"] == 8
    assert any("no operational modes" in w for w in body["warnings"])     # derived modes

    # parameters are visible on the mission root through the parameters API
    r = await client.get(f"/api/elements/{els['mission']['id']}/parameters")
    rows = {p["name"]: p for p in r.json()}
    assert rows["sim_min_soc_pct"]["owner_domain"] == "mission_simulation"
    assert rows["sim_min_soc_pct"]["effective_value"] == body["summary"]["sim_min_soc_pct"]

    # last run: fresh, with summary and conflicts
    r = await client.get(f"/api/studies/{study}/analyses/mission_simulation")
    assert r.status_code == 200, r.text
    last = r.json()
    assert last["id"] == body["run_id"] and last["stale"] is False and last["status"] == "ok"
    assert last["summary"]["sim_min_soc_pct"] == body["summary"]["sim_min_soc_pct"]
    r = await client.get(f"/api/studies/{study}/analyses")
    assert {x["analysis"] for x in r.json()} == {"mission_simulation"}

    # series
    r = await client.get(f"/api/analyses/runs/{body['run_id']}/series")
    assert r.status_code == 200
    s = r.json()["series"]
    n = len(s["t_s"])
    assert 0 < n <= 2000
    assert all(len(s[k]) == n for k in ("mode", "soc_pct", "p_gen_w", "p_load_w", "data_buffer_gb", "temp_c"))
    assert set(s["mode"]) <= {"Nominal", "Safe", "Downlink"}
    assert (await client.get("/api/analyses/runs/run-nope/series")).status_code == 404

    # PATCH a component's power -> the run is stale
    r = await client.patch(f"/api/elements/{els['rw']['id']}", json={"power_avg_w": 9.0, "version": els["rw"]["version"]})
    assert r.status_code == 200, r.text
    r = await client.get(f"/api/studies/{study}/analyses/mission_simulation")
    assert r.json()["stale"] is True

    # re-run: fresh again, conflicts replaced (not accumulated)
    r = await client.post(f"/api/studies/{study}/analyses/mission_simulation/run?n_orbits=2")
    assert r.status_code == 200
    assert (await client.get(f"/api/studies/{study}/analyses/mission_simulation")).json()["stale"] is False
    conflicts = (await client.get(f"/api/studies/{study}/conflicts")).json()["analysis"]
    assert all(c["analysis"] == "mission_simulation" for c in conflicts)
    assert len(conflicts) == len(r.json()["conflicts"])


async def test_shrunk_battery_conflict_over_http_and_option_scope(client, study_obj, study):
    els = await _tree(client, study)
    r = await client.put(f"/api/elements/{els['bat']['id']}/parameters/capacity_wh", json={"manual_value": 1.0})
    assert r.status_code == 200, r.text
    r = await client.post(f"/api/studies/{study}/analyses/mission_simulation/run?n_orbits=3")
    assert r.status_code == 200, r.text
    codes = {c["code"]: c for c in r.json()["conflicts"]}
    assert "SIM_SOC_BELOW_MIN" in codes
    c = codes["SIM_SOC_BELOW_MIN"]
    assert c["severity"] == "critical" and c["element_ids"] == [els["bat"]["id"]]
    assert "raise battery capacity to" in c["suggested_fix"]
    served = (await client.get(f"/api/studies/{study}/conflicts")).json()["analysis"]
    assert "SIM_SOC_BELOW_MIN" in {x["code"] for x in served}

    # option-scoped run does not touch the baseline's last run
    r = await client.post(f"/api/studies/{study}/analyses/mission_simulation/run?n_orbits=1&option_id=opt-b")
    assert r.status_code == 200 and r.json()["option_id"] == "opt-b"
    base = (await client.get(f"/api/studies/{study}/analyses/mission_simulation")).json()
    assert base["option_id"] is None and base["summary"]["sim_orbits"] == 3
    opt = (await client.get(f"/api/studies/{study}/analyses/mission_simulation?option_id=opt-b")).json()
    assert opt["option_id"] == "opt-b" and opt["summary"]["sim_orbits"] == 1

    # an empty study cannot be simulated
    assert (await client.post("/api/studies/nope/analyses/mission_simulation/run")).status_code == 400
