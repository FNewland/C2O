"""SCDF-170 verification — regression tests for the fixes made during the
independent verification (public API only)."""
from __future__ import annotations

import pytest

from tests.test_api.conftest import make_element, make_requirement


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
    r = await client.post(f"/api/elements/?study_id={study}", json={
        "name": "Battery", "element_type": "component", "parent_id": eps["id"], "subsystem_domain": "power",
        "mass_kg": 1.0, "power_avg_w": 0.2, "performance": {"capacity_wh": 40.0}})
    bat = r.json()
    r = await client.post(f"/api/elements/?study_id={study}", json={
        "name": "PCDU", "element_type": "component", "parent_id": eps["id"], "subsystem_domain": "power",
        "mass_kg": 0.5, "power_avg_w": 1.0, "performance": {"sa_power_eol_w": 16.0}})
    pcdu = r.json()
    return {"mission": mission, "sc": sc, "eps": eps, "bat": bat, "pcdu": pcdu}


async def test_patch_dimensions_and_redundancy_persist(client, study_obj, study):
    """ElementUpdate silently dropped dimensions_mm / redundancy_type (unknown fields)."""
    els = await _tree(client, study)
    sc, pcdu = els["sc"], els["pcdu"]
    r = await client.patch(f"/api/elements/{sc['id']}", json={"version": sc["version"], "dimensions_mm": [100, 226, 366]})
    assert r.status_code == 200 and r.json()["dimensions_mm"] == [100, 226, 366]
    r = await client.patch(f"/api/elements/{pcdu['id']}", json={"version": pcdu["version"], "redundancy_type": "cold"})
    assert r.status_code == 200 and r.json()["redundancy_type"] == "cold"
    r = await client.get(f"/api/studies/{study}/analyses/physics/placement")
    assert r.json()["envelope_m"] == [0.1, 0.226, 0.366]
    r = await client.post(f"/api/studies/{study}/analyses/fmeca/run", json={"critical": []})
    assert pcdu["id"] not in {e for c in r.json()["conflicts"] for e in c["element_ids"]}


async def test_mode_membership_persists_across_cache_reset(client, study_obj, study):
    """activate wrote only an in-memory list; the analysis context reads mode_elements rows."""
    from spacecdf_server.routers import elements as elements_router

    els = await _tree(client, study)
    mode = await make_element(client, study, "Nominal", "mode", els["sc"]["id"])
    r = await client.post(f"/api/elements/{mode['id']}/activate?element_id={els['pcdu']['id']}&power_w=3.0")
    assert r.status_code == 200
    elements_router._mode_elements.clear()          # what a restart does
    r = await client.get(f"/api/elements/{mode['id']}/mode-profile")
    assert r.json()["total_power_w"] == 3.0
    r = await client.post(f"/api/studies/{study}/analyses/mission_simulation/run?n_orbits=2")
    assert r.status_code == 200, r.text
    assert not any("no operational modes" in w for w in r.json()["warnings"])


async def test_closure_outputs_do_not_stale_other_analyses(client, study_obj, study):
    """Every analysis went stale as soon as any other closure wrote its outputs."""
    await _tree(client, study)
    assert (await client.post(f"/api/studies/{study}/analyses/mission_simulation/run?n_orbits=2")).status_code == 200
    assert (await client.post(f"/api/studies/{study}/analyses/physics/run")).status_code == 200
    assert (await client.post(f"/api/studies/{study}/analyses/vv/run")).status_code == 200
    stale = {a["analysis"]: a["stale"] for a in (await client.get(f"/api/studies/{study}/analyses")).json()}
    assert stale == {"mission_simulation": False, "physics": False, "vv": False}


async def test_physics_stale_on_pointing_requirement_change(client, study_obj, study):
    els = await _tree(client, study)
    await make_requirement(client, study, "SR-AOCS-1", "system",
                           threshold_param_path=f"el:{els['mission']['id']}.aocs_pointing_est_deg",
                           threshold_op="<=", threshold_value="0.5")
    assert (await client.post(f"/api/studies/{study}/analyses/physics/run")).status_code == 200
    assert (await client.get(f"/api/studies/{study}/analyses/physics")).json()["stale"] is False
    assert (await client.patch("/api/requirements/SR-AOCS-1", json={"threshold_value": "0.05"})).status_code == 200
    assert (await client.get(f"/api/studies/{study}/analyses/physics")).json()["stale"] is True


async def test_sim_min_soc_excludes_start_transient_and_scales_with_capacity(client, study_obj, study):
    """Executor starts at 80 % SoC: the raw minimum was 80 % whatever the battery."""
    els = await _tree(client, study)
    r = await client.post(f"/api/studies/{study}/analyses/mission_simulation/run?n_orbits=6")
    s1 = r.json()["summary"]
    assert s1["min_soc_at_s"] > 0 and s1["sim_min_soc_pct"] > 80.0
    await client.put(f"/api/elements/{els['bat']['id']}/parameters/capacity_wh", json={"manual_value": 160.0})
    s2 = (await client.post(f"/api/studies/{study}/analyses/mission_simulation/run?n_orbits=6")).json()["summary"]
    assert s2["sim_max_dod_pct"] < s1["sim_max_dod_pct"]


async def test_template_instantiate_is_persisted(client):
    from spacecdf_server.db.study_repo import db_load_all_studies
    r = await client.post("/api/templates/6u_eo_cubesat/instantiate")
    assert r.status_code == 200, r.text
    assert r.json()["id"] in await db_load_all_studies()


async def test_run_timestamps_are_utc_tagged(client, study_obj, study):
    await _tree(client, study)
    r = await client.post(f"/api/studies/{study}/analyses/vv/run")
    run = (await client.get(f"/api/studies/{study}/analyses/vv")).json()
    assert run["finished_at"].endswith("+00:00")
