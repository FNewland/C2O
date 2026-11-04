"""HTTP layer of the mode model (routers/modes.py) and the F3/F4 element fixes."""
from __future__ import annotations

import pytest

from tests.test_api.conftest import make_element, make_requirement


async def _sat(client, sid):
    sysel = await make_element(client, sid, "Spacecraft", "system")
    out = {"sys": sysel}
    subs = {d: (await make_element(client, sid, n, "subsystem", sysel["id"], d))["id"]
            for d, n in (("obc", "OBDH"), ("ttc", "TT&C"), ("payload", "Payload"), ("power", "EPS"))}
    parent_of = {"obc": "obc", "tx": "ttc", "cam": "payload", "bat": "power", "sa": "power"}
    for key, body in {
        "obc": {"name": "OBC", "kb_component_id": "obc-gom-nanomind-a3200"},
        "tx": {"name": "S-band transmitter", "kb_component_id": "txrx-endurosat-s-band-tx"},
        "cam": {"name": "Camera payload", "mass_kg": 1.0, "power_avg_w": 5.0, "subsystem_domain": "payload",
                "performance": {"data_rate_bps": 20_000_000}},
        "bat": {"name": "Battery pack", "mass_kg": 0.3, "subsystem_domain": "power", "trl": 9,
                "performance": {"capacity_wh": 40}},
        "sa": {"name": "Solar array wings", "mass_kg": 0.4, "subsystem_domain": "power", "performance": {"power_eol_w": 35}},
    }.items():
        r = await client.post(f"/api/elements/?study_id={sid}", json={"element_type": "component",
                                                                        "parent_id": subs[parent_of[key]], **body})
        assert r.status_code == 200, r.text
        out[key] = r.json()
    return out


async def test_kb_copy_and_maturity_on_create(client, study_obj):
    sid = study_obj.id
    els = await _sat(client, sid)
    obc = els["obc"]
    assert obc["dimensions_mm"] == [96.0, 90.0, 10.0]                          # F4
    assert obc["kb_spec"]["form_factor"] == "PC/104" and "I2C" in obc["kb_spec"]["interfaces"]
    assert obc["kb_spec"]["operating_temp_c"] == [-40, 85] and obc["kb_spec"]["kb_hash"]
    assert obc["margin_percent"] == 5.0                                        # F3: TRL 9 + heritage -> A
    assert els["cam"]["margin_percent"] == 20.0                                 # no part -> D
    # an explicit margin_percent is ignored (derived only)
    r = await client.patch(f"/api/elements/{els['cam']['id']}", json={"version": els["cam"]["version"],
                                                                        "margin_percent": 1.0, "trl": 7})
    assert r.json()["margin_percent"] == 10.0
    # persisted: reload from the DB
    from spacecdf_server.db.element_repo import load_all_elements
    loaded, _ = await load_all_elements()
    assert loaded[obc["id"]]["kb_spec"]["form_factor"] == "PC/104"
    # budgets show policy margins + the gate's system margin and the convention
    b = (await client.get(f"/api/elements/{obc['parent_id']}/budget/mass")).json()
    line = next(x for x in b["lines"] if x["element_id"] == obc["id"])
    assert line["margin_pct"] == 5.0 and line["maturity_category"] == "A"
    assert b["system_margin"]["convention"]["id"] == "percent_of_nominal" and b["system_margin"]["percent"] in (10, 20, 25)


async def test_mode_template_matrix_and_budgets(client, study_obj):
    sid = study_obj.id
    els = await _sat(client, sid)
    r = await client.post(f"/api/studies/{sid}/modes/template", json={})
    assert r.status_code == 200, r.text
    assert len(r.json()["created"]) == 7
    assert (await client.post(f"/api/studies/{sid}/modes/template", json={})).status_code == 409

    ov = (await client.get(f"/api/studies/{sid}/modes")).json()
    kinds = {m["kind"]: m for m in ov["modes"]}
    assert set(kinds) == {"leop", "commissioning", "nominal", "imaging", "downlink", "safe", "survival"}
    assert kinds["leop"]["initial"] and len(ov["transitions"]) == 13
    assert not [f for f in ov["findings"] if f["id"] in ("MM-UNREACHABLE", "MM-AUTO-NO-GUARD", "MM-NO-SAFE")]
    assert {u["unit_class"] for u in ov["units"]} >= {"obc", "transmitter", "payload"}

    p = (await client.post(f"/api/studies/{sid}/modes/propose")).json()
    assert p["counts"]["new"] == 7 * len(ov["units"])
    again = (await client.post(f"/api/studies/{sid}/modes/propose")).json()
    assert again["counts"]["new"] == 0 and again["counts"]["kept"] == p["counts"]["new"]

    ov = (await client.get(f"/api/studies/{sid}/modes")).json()
    cell = next(m for m in ov["members"] if m["mode_id"] == kinds["downlink"]["id"] and m["element_id"] == els["tx"]["id"])
    assert cell["status"] == "suggested" and cell["power_state"] == "peak" and cell["origin"] == "rule:MO-01"

    # edit a cell, reject another, accept the rest
    r = await client.put(f"/api/studies/{sid}/modes/{kinds['imaging']['id']}/members/{els['cam']['id']}",
                         json={"power_w_in_mode": 7.5})
    assert r.json()["status"] == "edited" and r.json()["power_w_in_mode"] == 7.5
    await client.put(f"/api/studies/{sid}/modes/{kinds['leop']['id']}/members/{els['cam']['id']}", json={"action": "reject"})
    acc = (await client.post(f"/api/studies/{sid}/modes/members/accept-all")).json()
    assert acc["accepted"] == p["counts"]["new"] - 2

    # staleness of an accepted rule cell when its unit changes (rule 13)
    tx = (await client.get(f"/api/elements/{els['tx']['id']}")).json()
    await client.patch(f"/api/elements/{tx['id']}", json={"version": tx["version"], "power_avg_w": 9.0})
    s = (await client.post(f"/api/studies/{sid}/modes/propose")).json()
    assert s["counts"]["stale"] == 7

    en = (await client.get(f"/api/studies/{sid}/modes/energy")).json()
    rows = {r["kind"]: r for r in en["modes"]}
    assert en["inputs"]["sa_power_eol_w"] == 35 and en["inputs"]["battery_capacity_wh"] == 40
    assert rows["imaging"]["power_cbe_w"] > rows["nominal"]["power_cbe_w"]
    assert rows["nominal"]["balance_wh"] is not None and en["operational_orbit"]["modes"]
    assert en["system_margin"]["convention"]["id"] == "percent_of_nominal"
    assert 0 < en["orbit"]["eclipse_fraction"] < 0.5

    dc = (await client.get(f"/api/studies/{sid}/modes/data-chain")).json()
    assert dc["generated_gb_per_day"] > 0 and dc["downlink"]["rate_bps"] > 0
    assert {c["id"] for c in dc["checks"]} >= {"DC-DOWNLINK", "DC-STORAGE"}

    ds = (await client.get(f"/api/studies/{sid}/modes/dissipation")).json()
    tx_d = next(u for u in ds["units"] if u["element_id"] == els["tx"]["id"])
    assert tx_d["hot_w"] > 0 and len(tx_d["by_mode"]) == 7

    eq = (await client.get(f"/api/studies/{sid}/budgets/equipment")).json()
    obc_row = next(r for r in eq["rows"] if r["element_id"] == els["obc"]["id"])
    assert obc_row["maturity_category"] == "A" and len(obc_row["power_by_mode_w"]) == 7
    assert next(r for r in eq["rows"] if r["element_id"] == els["tx"]["id"])["link"]["tx_power_w"] == 2.0

    # thermal analysis uses the mode dissipation
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.physics_closure import run_thermal_closure
    th = run_thermal_closure(await build_context(sid))
    assert th.inputs["dissipation_source"].startswith("mode matrix")


async def test_mode_crud_and_transitions(client, study_obj):
    sid = study_obj.id
    await _sat(client, sid)
    a = (await client.post(f"/api/studies/{sid}/modes", json={"name": "Detumble", "kind": "leop", "initial": True})).json()
    b = (await client.post(f"/api/studies/{sid}/modes", json={"name": "Safe", "kind": "safe", "pointing": "sun"})).json()
    assert (await client.post(f"/api/studies/{sid}/modes", json={"kind": "bogus"})).status_code == 400
    t = (await client.post(f"/api/studies/{sid}/mode-transitions", json={
        "from_mode_id": a["id"], "to_mode_id": b["id"], "trigger": "autonomous"})).json()
    ov = (await client.get(f"/api/studies/{sid}/modes")).json()
    assert any(f["id"] == "MM-AUTO-NO-GUARD" and f["transition_id"] == t["id"] for f in ov["findings"])
    await client.patch(f"/api/studies/{sid}/mode-transitions/{t['id']}",
                       json={"guard": {"param": "battery.soc_percent", "op": "<", "value": 20}})
    ov = (await client.get(f"/api/studies/{sid}/modes")).json()
    assert not any(f["id"] == "MM-AUTO-NO-GUARD" for f in ov["findings"])
    m = (await client.patch(f"/api/studies/{sid}/modes/{b['id']}", json={"orbit_fraction": 0.5, "name": "Sun safe"})).json()
    assert m["orbit_fraction"] == 0.5 and m["name"] == "Sun safe"
    assert (await client.delete(f"/api/studies/{sid}/modes/{b['id']}")).status_code == 200
    ov = (await client.get(f"/api/studies/{sid}/modes")).json()
    assert len(ov["modes"]) == 1 and ov["transitions"] == []


async def test_design_rules_proposals(client, study_obj):
    sid = study_obj.id
    els = await _sat(client, sid)
    await client.post(f"/api/studies/{sid}/modes/template", json={})
    await make_requirement(client, sid, "R-A", text="The dry mass shall not exceed 10 kg.", verification_method="A")
    run = (await client.post(f"/api/studies/{sid}/design-rules/run")).json()
    props = run["proposals"]
    kinds = {p["kind"] for p in props}
    assert {"monitor", "action", "risk"} <= kinds
    risk = next(p for p in props if p["kind"] == "risk" and p["rule_id"] == "RV-04")
    acc = (await client.post(f"/api/studies/{sid}/design-rules/proposals/{risk['id']}/accept")).json()
    assert acc["status"] == "accepted" and acc["result_ref"].startswith("RSK-")
    reg = (await client.get(f"/api/studies/{sid}/risks")).json()
    assert reg[0]["source"] == "rule:RV-04:R-A"
    # rejection memory: a rejected monitor stays rejected on the next run
    mon = next(p for p in props if p["kind"] == "monitor")
    await client.post(f"/api/studies/{sid}/design-rules/proposals/{mon['id']}/reject")
    run2 = (await client.post(f"/api/studies/{sid}/design-rules/run")).json()
    assert run2["counts"]["new"] == 0
    assert next(p for p in run2["proposals"] if p["id"] == mon["id"])["status"] == "rejected"
    # accepting a monitor gives FMECA detection credit (F10)
    other = next(p for p in run2["proposals"] if p["kind"] == "monitor" and p["status"] == "suggested")
    await client.post(f"/api/studies/{sid}/design-rules/proposals/{other['id']}/accept")
    run3 = (await client.post(f"/api/studies/{sid}/design-rules/run")).json()
    assert run3["detection_basis"] == "monitor"
    lst = (await client.get(f"/api/studies/{sid}/design-rules/proposals?kind=action")).json()
    assert lst["proposals"] and lst["refs"]["function_catalogue"]
    _ = els


async def test_heater_accept_creates_element(client, study_obj, monkeypatch):
    sid = study_obj.id
    await _sat(client, sid)
    from spacecdf_server.db import mode_repo
    prop = {"rule_id": "EI-05", "kind": "heater", "target_key": "heater:x", "element_id": "x",
            "payload": {"element_id": "x", "name": "Heater – Battery", "power_w": 4.0, "on_c": 5.0, "off_c": 10.0,
                        "control": "auto", "line": {"name": "htr_battery", "switchable": True}},
            "standard_ref": "C2O default", "c2o_default": True, "rationale": {"en": "e", "fr": "f"}, "inputs_hash": "h"}
    await mode_repo.upsert_proposals(sid, [prop])
    p = (await client.get(f"/api/studies/{sid}/design-rules/proposals?kind=heater")).json()["proposals"][0]
    out = (await client.post(f"/api/studies/{sid}/design-rules/proposals/{p['id']}/accept")).json()
    heaters = (await client.get(f"/api/studies/{sid}/heaters")).json()
    assert out["result_ref"] == heaters[0]["id"] and heaters[0]["on_c"] == 5.0
    el = (await client.get(f"/api/elements/{heaters[0]['heater_element_id']}")).json()
    assert el["power_avg_w"] == 4.0 and el["subsystem_domain"] == "thermal"


async def test_kb_staleness_mark_and_refresh(client, study_obj, monkeypatch):
    sid = study_obj.id
    els = await _sat(client, sid)
    assert (await client.get(f"/api/studies/{sid}/kb-staleness")).json()["count"] == 0
    from spacecdf_server.services import kb_copy
    real = kb_copy.find_kb_part

    def changed(kid):
        p = real(kid)
        return {**p, "mass_kg": 0.5} if p and kid == "obc-gom-nanomind-a3200" else p
    monkeypatch.setattr(kb_copy, "find_kb_part", changed)
    st = (await client.get(f"/api/studies/{sid}/kb-staleness")).json()
    assert st["count"] == 1 and st["stale"][0]["element_id"] == els["obc"]["id"]
    assert "mass_kg" in st["stale"][0]["changed"]
    mk = (await client.post(f"/api/studies/{sid}/kb-staleness/mark")).json()
    assert mk["marked"] == [els["obc"]["id"]]
    assert (await client.get(f"/api/elements/{els['obc']['id']}")).json()["kb_spec"]["stale"]
    ref = (await client.post(f"/api/elements/{els['obc']['id']}/kb-refresh")).json()
    assert ref["mass_kg"] == 0.5 and not ref["kb_spec"]["stale"] and ref["name"] == "OBC"


@pytest.mark.parametrize("path", ["modes", "modes/energy", "modes/data-chain", "budgets/equipment"])
async def test_unknown_study_404(client, path):
    assert (await client.get(f"/api/studies/nope/{path}")).status_code == 404
