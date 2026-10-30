"""SCDF-174 — ground segment over HTTP: station picker (catalogue + add /
duplicate / remove), run -> parameters on the mission root, GET last run with
conflicts, series, stale after removing a station, option scope."""
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
    pl = await make_element(client, study, "Payload", "subsystem", sc["id"], "payload")
    ttc = await make_element(client, study, "TT&C", "subsystem", sc["id"], "ttc")

    async def comp(name, parent, domain, **kw):
        r = await client.post(f"/api/elements/?study_id={study}", json={
            "name": name, "element_type": "component", "parent_id": parent, "subsystem_domain": domain, **kw})
        assert r.status_code == 200, r.text
        return r.json()

    cam = await comp("Camera", pl["id"], "payload", mass_kg=1.0, power_avg_w=4.0,
                     performance={"data_rate_bps": 0.2e6, "duty_cycle_percent": 50.0})
    await comp("X-band TX", ttc["id"], "ttc", mass_kg=0.3, power_avg_w=8.0,
               performance={"frequency_band": "X-band", "tx_power_w": 5.0, "gain_dbi": 10.0, "data_rate_bps": 20e6})
    return {"mission": mission, "cam": cam, "ttc": ttc}


async def test_station_picker_run_get_and_stale(client, study_obj, study):
    els = await _tree(client, study)
    GS = f"/api/studies/{study}/ground-stations"

    # catalogue served, nothing selected yet
    r = await client.get(GS)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["selected"] == [] and len(body["catalogue"]) > 10
    sval = next(s for s in body["catalogue"] if s["id"] == "svalbard")
    assert sval["selected"] is False and sval["lat"] == 78.23 and "X" in sval["bands"]

    # add two stations -> ground-segment element created, station elements persisted with KB props
    r = await client.post(GS, json={"kb_station_id": "svalbard"})
    assert r.status_code == 200, r.text
    st1 = r.json()
    assert st1["kb_station_id"] == "svalbard" and st1["g_over_t_db_k"] == 28.5 and st1["min_elevation_deg"] == 5
    r = await client.post(GS, json={"kb_station_id": "kiruna", "min_elevation_deg": 10})
    assert r.status_code == 200, r.text
    st2 = r.json()
    assert st2["min_elevation_deg"] == 10
    assert (await client.post(GS, json={"kb_station_id": "svalbard"})).status_code == 409
    assert (await client.post(GS, json={"kb_station_id": "atlantis"})).status_code == 404
    tree = (await client.get(f"/api/studies/{study}/elements")).json()
    ground = [e for e in tree if e.get("segment") == "ground"]
    seg = [e for e in ground if e["element_type"] == "segment"]
    assert len(seg) == 1 and seg[0]["parent_id"] == els["mission"]["id"]
    stations = [e for e in ground if e["element_type"] == "component"]
    assert {e["kb_component_id"] for e in stations} == {"svalbard", "kiruna"}
    assert all(e["parent_id"] == seg[0]["id"] and e["subsystem_domain"] == "ground" for e in stations)
    sel = (await client.get(GS)).json()
    assert [s["kb_station_id"] for s in sel["selected"]] == ["svalbard", "kiruna"]
    assert sum(1 for s in sel["catalogue"] if s["selected"]) == 2

    # run
    assert (await client.get(f"/api/studies/{study}/analyses/ground_segment")).status_code == 404
    r = await client.post(f"/api/studies/{study}/analyses/ground_segment/run")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["stale"] is False and body["status"] == "ok"
    names = [p["name"] for p in body["parameters"]]
    assert names == ["gs_contact_min_per_day", "gs_contacts_per_day", "gs_data_return_gb_per_day",
                     "gs_data_generated_gb_per_day", "gs_backlog_end_gb", "gs_min_link_margin_db", "gs_station_count"]
    assert all(p["element_id"] == els["mission"]["id"] for p in body["parameters"])
    s = body["summary"]
    assert s["gs_station_count"] == 2 and s["parameters_written"] == 7 and s["closure_pct"] > 95
    assert {row["station_id"] for row in s["stations"]} == {"svalbard", "kiruna"}
    assert all(row["status"] == "ok" for row in s["stations"])
    assert not any(c["code"] == "GS_DATA_DEFICIT" for c in body["conflicts"])
    assert not any("using catalogue defaults" in w for w in body["warnings"])

    r = await client.get(f"/api/elements/{els['mission']['id']}/parameters")
    rows = {p["name"]: p for p in r.json()}
    assert rows["gs_contact_min_per_day"]["owner_domain"] == "ground_segment"
    assert rows["gs_contact_min_per_day"]["effective_value"] == s["gs_contact_min_per_day"]

    # last run + series
    last = (await client.get(f"/api/studies/{study}/analyses/ground_segment")).json()
    assert last["id"] == body["run_id"] and last["stale"] is False and last["summary"]["gs_station_count"] == 2
    r = await client.get(f"/api/analyses/runs/{body['run_id']}/series")
    assert r.status_code == 200
    series = r.json()["series"]
    assert series["analysis"] == "ground_segment" and series["contacts"] and series["buffer"]["t_s"][-1] == 86400
    assert len(series["stations"]) == 2 and series["inputs"]["band"] == "X"
    assert {x["analysis"] for x in (await client.get(f"/api/studies/{study}/analyses")).json()} >= {"ground_segment"}

    # remove a station -> stale; the element is soft-deleted
    r = await client.delete(f"{GS}/{st2['element_id']}")
    assert r.status_code == 200, r.text
    assert r.json()["deleted"] is True and r.json()["kb_station_id"] == "kiruna"
    assert (await client.delete(f"{GS}/{st2['element_id']}")).status_code == 404
    assert [s["kb_station_id"] for s in (await client.get(GS)).json()["selected"]] == ["svalbard"]
    assert (await client.get(f"/api/studies/{study}/analyses/ground_segment")).json()["stale"] is True

    # re-run: fresh, one station, conflicts replaced
    r = await client.post(f"/api/studies/{study}/analyses/ground_segment/run")
    assert r.status_code == 200 and r.json()["summary"]["gs_station_count"] == 1
    assert (await client.get(f"/api/studies/{study}/analyses/ground_segment")).json()["stale"] is False
    served = (await client.get(f"/api/studies/{study}/conflicts")).json()["analysis"]
    assert len([c for c in served if c["analysis"] == "ground_segment"]) == len(r.json()["conflicts"])


async def test_deficit_conflict_over_http_and_option_scope(client, study_obj, study):
    els = await _tree(client, study)
    await client.post(f"/api/studies/{study}/ground-stations", json={"kb_station_id": "svalbard"})
    r = await client.patch(f"/api/elements/{els['cam']['id']}",
                           json={"performance": {"data_rate_bps": 200e6, "duty_cycle_percent": 50.0}, "version": els["cam"]["version"]})
    assert r.status_code == 200, r.text
    r = await client.post(f"/api/studies/{study}/analyses/ground_segment/run")
    assert r.status_code == 200, r.text
    codes = {c["code"]: c for c in r.json()["conflicts"]}
    assert "GS_DATA_DEFICIT" in codes
    c = codes["GS_DATA_DEFICIT"]
    assert c["severity"] == "major" and c["element_ids"] == [els["mission"]["id"]]
    assert "from the catalogue" in c["suggested_fix"] and "min/day of contact" in c["suggested_fix"]
    assert "GS_DATA_DEFICIT" in {x["code"] for x in (await client.get(f"/api/studies/{study}/conflicts")).json()["analysis"]}

    # option-scoped run does not touch the baseline's last run
    r = await client.post(f"/api/studies/{study}/analyses/ground_segment/run?option_id=opt-b")
    assert r.status_code == 200 and r.json()["option_id"] == "opt-b"
    base = (await client.get(f"/api/studies/{study}/analyses/ground_segment")).json()
    assert base["option_id"] is None
    opt = (await client.get(f"/api/studies/{study}/analyses/ground_segment?option_id=opt-b")).json()
    assert opt["option_id"] == "opt-b"

    # no stations at all: catalogue defaults + warning, not a hard failure
    assert (await client.post("/api/studies/nope/analyses/ground_segment/run")).status_code == 400
