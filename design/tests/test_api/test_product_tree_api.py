"""Product tree API (routers/product_tree.py): the wizard's default tree, adding spacecraft,
the level check on create/move, and the migration of studies whose subsystems hang off the
space segment (links, budgets, requirements and placements kept)."""
from __future__ import annotations

from tests.test_api.conftest import make_element, make_interface, make_requirement


async def _tree(client, study):
    return (await client.get(f"/api/studies/{study}/elements")).json()


async def test_default_tree_is_mission_segment_spacecraft_subsystems(client, study_obj, study):
    r = await client.post(f"/api/studies/{study}/product-tree/default",
                          json={"architecture": "single-leo", "mission_name": "TreeSat"})
    assert r.status_code == 200, r.text
    out = r.json()
    els = await _tree(client, study)
    by = {e["id"]: e for e in els}
    kids = lambda pid: [e for e in els if e.get("parent_id") == pid]
    root = by[out["mission_id"]]
    assert root["element_type"] == "mission" and root["name"] == "TreeSat" and root["parent_id"] is None
    segs = {e["name"]: e for e in kids(root["id"])}
    assert set(segs) == {"Space Segment", "Ground Segment", "Launch Segment", "User Segment", "Operations"}
    assert {e["element_type"] for e in segs.values()} == {"segment"}
    (sc,) = kids(segs["Space Segment"]["id"])
    assert sc["element_type"] == "system" and sc["name"] == "Spacecraft" and out["spacecraft_ids"] == [sc["id"]]
    subs = kids(sc["id"])
    assert len(subs) == 9 and {e["element_type"] for e in subs} == {"subsystem"}   # 8 + Harness (W2.09)
    assert "Harness" in {e["name"] for e in subs}
    assert {e["subsystem_domain"] for e in subs} >= {"payload", "power", "aocs", "ttc", "obc"}
    (gs,) = kids(segs["Ground Segment"]["id"])
    assert gs["element_type"] == "system" and gs["name"] == "Ground Station"
    chk = (await client.get(f"/api/studies/{study}/product-tree/check")).json()
    assert chk["ok"] and not chk["migration_pending"] and [s["id"] for s in chk["spacecraft"]] == [sc["id"]]
    # mass roll-up: the space segment's budget has one line, the spacecraft
    b = (await client.get(f"/api/elements/{segs['Space Segment']['id']}/budget/mass")).json()
    assert [ln["element_id"] for ln in b["lines"]] == [sc["id"]] and b["sum_nominal"] > 0


async def test_constellation_and_second_spacecraft(client, study_obj, study):
    out = (await client.post(f"/api/studies/{study}/product-tree/default", json={"architecture": "constellation"})).json()
    els = await _tree(client, study)
    sc = next(e for e in els if e["id"] == out["spacecraft_ids"][0])
    assert sc["quantity"] == 4 and sc["performance"]["constellation"] is True
    r = await client.post(f"/api/studies/{study}/spacecraft", json={})
    assert r.status_code == 200, r.text
    sc2 = r.json()
    assert sc2["name"] == "Spacecraft 2" and len(sc2["subsystem_ids"]) == 8
    els = await _tree(client, study)
    sc2_el = next(e for e in els if e["id"] == sc2["spacecraft_id"])
    assert sc2_el["parent_id"] == sc["parent_id"] and sc2_el["element_type"] == "system"
    chk = (await client.get(f"/api/studies/{study}/product-tree/check")).json()
    assert chk["ok"] and len(chk["spacecraft"]) == 2
    # the stack builder lays out one CubeSat: the first spacecraft
    st = (await client.get(f"/api/studies/{study}/stack")).json()
    assert st["spacecraft"] == {"id": sc["id"], "name": "Spacecraft", "count": 2}


async def test_components_never_go_directly_under_a_segment(client, study_obj, study):
    m = await make_element(client, study, "Mission", "mission")
    seg = await make_element(client, study, "Space Segment", "segment", m["id"])
    for t in ("subsystem", "component"):
        r = await client.post(f"/api/elements/?study_id={study}", json={"name": "EPS", "element_type": t, "parent_id": seg["id"]})
        assert r.status_code == 422 and r.json()["detail"]["error"] == "product_tree_level"
        assert r.json()["detail"]["allowed"] == ["system"]
    sc = await make_element(client, study, "Spacecraft", "system", seg["id"])
    eps = await make_element(client, study, "EPS", "subsystem", sc["id"], "power")
    # moving a subsystem up to the segment is refused too
    r = await client.patch(f"/api/elements/{eps['id']}", json={"version": eps["version"], "parent_id": seg["id"]})
    assert r.status_code == 422
    # populate a spacecraft directly (Quick Start on a system)
    r = await client.post(f"/api/studies/{study}/populate-subsystems?parent_element_id={sc['id']}",
                          json={"include_equipment": False})
    assert r.status_code == 200 and r.json()["system_id"] == sc["id"]
    assert set(r.json()["subsystem_ids"]) >= {"payload", "aocs"} and r.json()["subsystem_ids"]["power"] == eps["id"]


async def test_migration_keeps_links_budgets_requirements_and_positions(client, study_obj, study):
    from spacecdf_server.db.element_repo import db_create_element
    from spacecdf_server.routers import elements as er

    m = await make_element(client, study, "Mission", "mission")
    seg = await make_element(client, study, "Space Segment", "segment", m["id"])
    # a pre-Nov-2026 tree: subsystems straight under the space segment (written past the API check)
    legacy = {}
    for name, typ, dom in (("EPS", "subsystem", "power"), ("OBC", "subsystem", "obc"), ("AOCS", "system", "aocs")):
        el = {"id": f"{name.lower()}{study[:6]}", "study_id": study, "name": name, "element_type": typ,
              "parent_id": seg["id"], "subsystem_domain": dom, "segment": "space", "version": 1, "deleted_at": None,
              "quantity": 1, "mass_kg": 0.5, "position_json": [0.05, 0.05, 0.1]}
        await db_create_element(el)
        er._elements[el["id"]] = el
        legacy[name] = el
    bat = await make_element(client, study, "Battery", "component", legacy["EPS"]["id"], "power")
    link = await make_interface(client, study, legacy["EPS"]["id"], legacy["OBC"]["id"], "Power to OBC", "electrical")
    r = await client.post(f"/api/elements/{legacy['EPS']['id']}/allocations",
                          json={"budget_type": "mass", "allocation_value": 0.8, "unit": "kg", "source": "manual", "rationale": ""})
    assert r.status_code == 200, r.text
    await make_requirement(client, study, "REQ-EPS-1", level="subsystem", element_id=legacy["EPS"]["id"])

    chk = (await client.get(f"/api/studies/{study}/product-tree/check")).json()
    assert not chk["ok"] and chk["migration_pending"] and len(chk["misplaced"]) == 3

    r = await client.post(f"/api/studies/{study}/product-tree/migrate")
    assert r.status_code == 200, r.text
    res = r.json()
    assert len(res["inserted"]) == 1 and sorted(res["moved"]) == sorted(e["id"] for e in legacy.values())
    assert res["retyped"] == [legacy["AOCS"]["id"]]
    els = {e["id"]: e for e in await _tree(client, study)}
    sc = els[res["inserted"][0]]
    assert sc["parent_id"] == seg["id"] and sc["element_type"] == "system" and sc["name"] == "Spacecraft"
    for e in legacy.values():
        assert els[e["id"]]["parent_id"] == sc["id"] and els[e["id"]]["element_type"] == "subsystem"
        assert els[e["id"]]["position_json"] == [0.05, 0.05, 0.1]
    assert els[bat["id"]]["parent_id"] == legacy["EPS"]["id"]
    ifcs = (await client.get(f"/api/studies/{study}/interfaces")).json()
    ifcs = ifcs if isinstance(ifcs, list) else ifcs.get("interfaces", [])
    ifc = next(i for i in ifcs if i["id"] == link["id"])
    assert (ifc["from_element_id"], ifc["to_element_id"]) == (legacy["EPS"]["id"], legacy["OBC"]["id"])
    allocs = (await client.get(f"/api/studies/{study}/allocations")).json()
    assert any(a["element_id"] == legacy["EPS"]["id"] and a["allocation_value"] == 0.8 for a in allocs)
    req = (await client.get("/api/requirements/REQ-EPS-1")).json()
    assert req["element_id"] == legacy["EPS"]["id"]
    # mass rolls up through the inserted spacecraft
    b = (await client.get(f"/api/elements/{sc['id']}/budget/mass")).json()
    assert len(b["lines"]) == 3
    # idempotent
    again = (await client.post(f"/api/studies/{study}/product-tree/migrate")).json()
    assert again["inserted"] == [] and again["moved"] == []
    assert (await client.get(f"/api/studies/{study}/product-tree/check")).json()["ok"]


async def test_ground_station_picker_takes_over_the_default_station(client, study_obj, study):
    await client.post(f"/api/studies/{study}/product-tree/default", json={"architecture": "single-leo"})
    r = await client.post(f"/api/studies/{study}/ground-stations", json={"kb_station_id": "svalbard"})
    assert r.status_code == 200, r.text
    els = await _tree(client, study)
    gseg = next(e for e in els if e["element_type"] == "segment" and e["segment"] == "ground")
    stations = [e for e in els if e.get("parent_id") == gseg["id"]]
    assert len(stations) == 1 and stations[0]["kb_component_id"] == "svalbard"
    assert stations[0]["element_type"] == "system"
    r = await client.post(f"/api/studies/{study}/ground-stations", json={"kb_station_id": "kiruna"})
    assert r.status_code == 200
    assert len([e for e in await _tree(client, study) if e.get("parent_id") == gseg["id"]]) == 2
