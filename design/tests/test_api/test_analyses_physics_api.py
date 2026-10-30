"""SCDF-176/177 over HTTP: physics run -> parameters on the mission root and
per-element thermal parameters, GET last run (+ conflicts, series), placement
endpoint, position PATCH flips ``stale``; FMECA run -> get with modes."""
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
    r = await client.post(f"/api/elements/?study_id={study}", json={
        "name": "Spacecraft", "element_type": "system", "parent_id": seg["id"], "dimensions_mm": [100, 100, 300]})
    assert r.status_code == 200, r.text
    sc = r.json()
    eps = await make_element(client, study, "EPS", "subsystem", sc["id"], "power")
    aocs = await make_element(client, study, "AOCS", "subsystem", sc["id"], "aocs")
    pl = await make_element(client, study, "Payload", "subsystem", sc["id"], "payload")

    async def comp(name, parent, domain, **kw):
        r = await client.post(f"/api/elements/?study_id={study}", json={
            "name": name, "element_type": "component", "parent_id": parent, "subsystem_domain": domain,
            "dimensions_mm": [90, 90, 75], **kw})
        assert r.status_code == 200, r.text
        return r.json()

    bat = await comp("Battery", eps["id"], "power", mass_kg=1.0, power_avg_w=0.2, performance={"capacity_wh": 40.0})
    await comp("PCDU", eps["id"], "power", mass_kg=1.0, power_avg_w=1.0)
    rw = await comp("Wheel", aocs["id"], "aocs", mass_kg=1.0, power_avg_w=1.0, performance={"momentum_nms": 0.011})
    cam = await comp("Camera", pl["id"], "payload", mass_kg=1.0, power_avg_w=2.0,
                     performance={"op_temp_min_c": -25.0, "op_temp_max_c": 40.0})
    return {"mission": mission, "sc": sc, "eps": eps, "bat": bat, "rw": rw, "cam": cam}


async def test_physics_run_get_placement_and_position_stale(client, study_obj, study):
    els = await _tree(client, study)
    assert (await client.get(f"/api/studies/{study}/analyses/physics")).status_code == 404

    # placement before any run: everything auto-stacked in the 3U envelope
    r = await client.get(f"/api/studies/{study}/analyses/physics/placement")
    assert r.status_code == 200, r.text
    pl = r.json()
    assert pl["envelope_m"] == [0.1, 0.1, 0.3] and len(pl["auto_placed"]) == 4 and len(pl["items"]) == 4

    r = await client.post(f"/api/studies/{study}/analyses/physics/run")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok" and body["stale"] is False
    names = {p["name"] for p in body["parameters"]}
    assert {"mp_total_mass_kg", "mp_com_z_m", "mp_ixx_kgm2", "mp_cp_cg_offset_m", "aocs_disturbance_torque_nm",
            "aocs_momentum_per_orbit_nms", "aocs_wheel_margin_pct", "aocs_pointing_est_deg",
            "thermal_worst_margin_c", "thermal_nodes", "thermal_t_hot_c", "thermal_margin_cold_c"} <= names
    assert body["summary"]["mp_total_mass_kg"] == 4.0 and body["summary"]["auto_placed"] == 4
    root_params = {p["name"] for p in body["parameters"] if p["element_id"] == els["mission"]["id"]}
    assert "mp_com_z_m" in root_params and "thermal_t_hot_c" not in root_params
    cam_params = {p["name"]: p["value"] for p in body["parameters"] if p["element_id"] == els["cam"]["id"]}
    assert set(cam_params) == {"thermal_t_hot_c", "thermal_t_cold_c", "thermal_margin_hot_c", "thermal_margin_cold_c"}

    # parameters visible through the parameters API
    r = await client.get(f"/api/elements/{els['cam']['id']}/parameters")
    rows = {p["name"]: p for p in r.json()}
    assert rows["thermal_t_hot_c"]["owner_domain"] == "physics"

    # last run + series
    r = await client.get(f"/api/studies/{study}/analyses/physics")
    last = r.json()
    assert last["id"] == body["run_id"] and last["stale"] is False        # served by the generic analyses route
    r = await client.get(f"/api/studies/{study}/conflicts")
    assert all(c["analysis"] == "physics" for c in r.json()["analysis"])
    r = await client.get(f"/api/analyses/runs/{body['run_id']}/series")
    s = r.json()["series"]
    assert set(s) == {"analysis", "placement", "mass_properties", "aocs", "thermal"}
    assert len(s["thermal"]["transient"]["t_s"]) == len(s["thermal"]["transient"]["nodes"][0]["temps_c"])
    assert s["aocs"]["torques_nm"]["rss"] > 0 and s["mass_properties"]["principal_axes"]

    # move the camera: write-through position, run goes stale, placement reports it explicit
    r = await client.patch(f"/api/elements/{els['cam']['id']}/position", json={"x": 0.05, "y": 0.05, "z": 0.26})
    assert r.status_code == 200, r.text
    assert r.json()["position_json"] == [0.05, 0.05, 0.26] and r.json()["version"] == els["cam"]["version"] + 1
    r = await client.get(f"/api/elements/{els['cam']['id']}")
    assert r.json()["position_json"] == [0.05, 0.05, 0.26]
    r = await client.get(f"/api/studies/{study}/analyses/physics")
    assert r.json()["stale"] is True
    r = await client.get(f"/api/studies/{study}/analyses/physics/placement")
    item = next(i for i in r.json()["items"] if i["element_id"] == els["cam"]["id"])
    assert item["source"] == "explicit" and len(r.json()["auto_placed"]) == 3

    # clear it again
    r = await client.patch(f"/api/elements/{els['cam']['id']}/position", json={})
    assert r.json()["position_json"] is None
    assert (await client.patch("/api/elements/nope/position", json={"x": 0})).status_code == 404


async def test_fmeca_run_and_get(client, study_obj, study):
    els = await _tree(client, study)
    assert (await client.get(f"/api/studies/{study}/analyses/fmeca")).status_code == 404
    r = await client.post(f"/api/studies/{study}/analyses/fmeca/run", json={"critical": []})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok" and {p["name"] for p in body["parameters"]} == {
        "fmeca_max_rpn", "fmeca_single_point_failures", "fmeca_modes", "fmeca_critical_modes"}
    modes = body["modes"]
    assert modes and all("function_ids" in m for m in modes)
    bat = next(m for m in modes if m["element_id"] == els["bat"]["id"])
    assert bat["single_point"] and bat["critical"]
    assert any(c["code"] == "FMECA_SINGLE_POINT" and c["element_ids"] == [els["bat"]["id"]] for c in body["conflicts"])
    r = await client.get(f"/api/studies/{study}/analyses/fmeca")
    last = r.json()
    assert last["id"] == body["run_id"] and last["stale"] is False
    r = await client.get(f"/api/analyses/runs/{body['run_id']}/series")
    assert len(r.json()["series"]["modes"]) == len(modes)                 # the panel reads the modes from the series
    r = await client.get(f"/api/studies/{study}/conflicts")
    assert any(c["code"] == "FMECA_SINGLE_POINT" for c in r.json()["analysis"])
    r = await client.get(f"/api/studies/{study}/analyses")
    assert {x["analysis"] for x in r.json()} == {"fmeca"}
