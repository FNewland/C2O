"""Electrical & data design elements and the interface ↔ interface-requirement rules
(docs/plan_2026-11/design_sim/spacecdf_design_rules.md §1.2, §1.6 EI-01/EI-02, EB-08, §2.1, §2.4).

The study is an EOSAT-1-like 6U built from KB parts (8S battery, CAN OBC and units,
S-band transceiver): the rules must propose a 28 V bus, CAN with two segments and S-band —
not the nanosat defaults (7.4 V, I2C, UHF).
"""
from __future__ import annotations

import pytest

from tests.test_api.conftest import make_element

EOSAT_PARTS = {
    "power": [("Battery", "bat-gom-nanopow-bp8"), ("EPS", "eps-gom-nanopow-p60")],
    "obc": [("OBC", "obc-gom-nanomind-a3200")],
    "ttc": [("S-band transceiver", "txr-endurosat-sband")],
    "aocs": [("Reaction wheel", "rw-cubespace-cubewheel-medium"), ("Star tracker", "st-cubespace-cubestar")],
    "thermal": [("Battery heater", "th-heater-kapton-05")],
    "structure": [("Structure", "struct-isis-6u")],
}


@pytest.fixture(autouse=True)
def _auto(monkeypatch):
    monkeypatch.setenv("SPACECDF_AUTO_IRD", "1")


async def _component(client, study, name, parent, domain, kb):
    r = await client.post(f"/api/elements/?study_id={study}", json={
        "name": name, "element_type": "component", "parent_id": parent, "subsystem_domain": domain,
        "kb_component_id": kb})
    assert r.status_code == 200, r.text
    return r.json()


async def build_eosat(client, study) -> dict[str, dict]:
    mission = await make_element(client, study, "Mission", "mission")
    seg = await make_element(client, study, "Space Segment", "segment", mission["id"])
    sc = await make_element(client, study, "EOSAT-1", "system", seg["id"])
    out: dict[str, dict] = {}
    for dom, parts in EOSAT_PARTS.items():
        sub = await make_element(client, study, dom.upper(), "subsystem", sc["id"], subsystem_domain=dom)
        for name, kb in parts:
            out[name] = await _component(client, study, name, sub["id"], dom, kb)
    r = await client.post(f"/api/studies/{study}/interfaces/propose", json={})
    assert r.status_code == 200, r.text
    return out


async def _ifaces(client, study, **q):
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    return (await client.get(f"/api/studies/{study}/interfaces?{qs}")).json()


async def _accept_all(client, study):
    for i in await _ifaces(client, study, status="suggested"):
        r = await client.patch(f"/api/interfaces/{i['id']}", json={"status": "accepted"})
        assert r.status_code == 200, r.text


async def _elec(client, study) -> dict:
    r = await client.get(f"/api/studies/{study}/electrical")
    assert r.status_code == 200, r.text
    return r.json()


async def _irs(client, study) -> dict:
    r = await client.get(f"/api/studies/{study}/interface-requirements")
    assert r.status_code == 200, r.text
    return r.json()


# ── defaults derived from the KB parts ───────────────────────────────────

async def test_kb_parts_imply_eosat_defaults(client, study_obj, study):
    parts = await build_eosat(client, study)
    ifs = await _ifaces(client, study)
    power = [i for i in ifs if i["type"] == "power" and i["subtype"] == "regulated"]
    assert power and all(i["properties"]["rail_voltage"] == 28.8 for i in power), \
        [(i["name"], i["properties"]) for i in power]
    tmtc = [i for i in ifs if i["type"] == "data" and i["from_element_id"] == parts["OBC"]["id"]]
    assert tmtc and {i["properties"]["protocol"] for i in tmtc} == {"CAN"}
    prof = (await _elec(client, study))["profile"]
    assert prof["unregulated_bus_v"] == 28.8 and prof["data_protocol_by_class"] == "CAN"
    assert prof["ttc_band_by_class"] == "S"


# ── IF-01: accepted interface → interface requirements ───────────────────

async def test_accepted_interfaces_get_requirements_both_ways(client, study_obj, study):
    parts = await build_eosat(client, study)
    assert (await _irs(client, study))["requirements"] == []          # suggested links: no IR yet
    await _accept_all(client, study)
    body = await _irs(client, study)
    irs = body["requirements"]
    assert irs and all(r["level"] == "interface" and r["status"] == "draft" for r in irs)
    accepted = [i for i in await _ifaces(client, study) if i["status"] == "accepted"]
    linked = {r["ir_json"]["interface_id"] for r in irs}
    assert linked == {i["id"] for i in accepted}
    # power link EPS → reaction wheel: supply + draw requirements, EN and FR
    pw = next(i for i in accepted if i["type"] == "power" and i["to_element_id"] == parts["Reaction wheel"]["id"])
    mine = (await client.get(f"/api/studies/{study}/interfaces/{pw['id']}/requirements")).json()
    tids = {r["ir_json"]["template_id"] for r in mine["requirements"]}
    assert tids == {"IRT-PWR-SUPPLY", "IRT-PWR-DRAW"}
    draw = next(r for r in mine["requirements"] if r["ir_json"]["template_id"] == "IRT-PWR-DRAW")
    assert "28.8 V" in draw["text"] and "Reaction wheel" in draw["text"]
    assert draw["ir_json"]["text_i18n"]["fr"].startswith("L'élément Reaction wheel")
    assert draw["responsible_position"] == "aocs_engineer" and draw["verification_method"] == "T"
    assert mine["agreement"]["state"] == "defined"
    assert mine["agreement"]["provider_seat"] == "power_engineer"
    # relation both ways (requirement → interface, served from either end)
    rels = (await client.get(f"/api/relations/for/interface/{pw['id']}")).json() \
        if (await client.get(f"/api/relations/for/interface/{pw['id']}")).status_code == 200 else None
    from spacecdf_server.db.relation_repo import list_relations_for
    by_iface = await list_relations_for("interface", pw["id"])
    by_req = await list_relations_for("requirement", draw["id"])
    assert any(r["source_id"] == draw["id"] and r["kind"] == "allocates" for r in by_iface)
    assert any(r["target_id"] == pw["id"] for r in by_req)
    _ = rels


async def test_line_values_flow_into_requirements_and_go_stale(client, study_obj, study):
    parts = await build_eosat(client, study)
    await _accept_all(client, study)
    r = await client.post(f"/api/studies/{study}/electrical/propose", json={})
    assert r.status_code == 200 and r.json()["created"] > 0
    view = await _elec(client, study)
    line = next(ln for ln in view["lines"] if parts["Reaction wheel"]["id"] in ln["load_element_ids"])
    # P/V = 1.0 W / 28.8 V = 0.035 A → LCL = 1.5 × 0.035 → 0.1 A (minimum)
    assert line["lcl_limit_a"] == 0.1 and line["switchable"] and not line["default_on_boot"]
    obc_line = next(ln for ln in view["lines"] if parts["OBC"]["id"] in ln["load_element_ids"])
    assert obc_line["switchable"] is False and obc_line["default_on_boot"] is True
    assert obc_line["line_no"] == 0
    irs = (await _irs(client, study))["requirements"]
    sup = next(x for x in irs if x["ir_json"]["template_id"] == "IRT-PWR-SUPPLY"
               and x["ir_json"]["endpoints"]["to_element_id"] == parts["Reaction wheel"]["id"])
    assert f"power line {line['line_no']}" in sup["text"] and "0.1 A" in sup["text"]
    # approve it, then change the LCL: the approved requirement is flagged stale with the new text
    await client.patch(f"/api/requirements/{sup['id']}", json={"status": "approved"})
    r = await client.patch(f"/api/studies/{study}/electrical/lines/{line['id']}", json={"lcl_limit_a": 0.5})
    assert r.status_code == 200 and r.json()["edited"] and r.json()["status"] == "accepted"
    sup2 = next(x for x in (await _irs(client, study))["requirements"] if x["id"] == sup["id"])
    assert sup2["ir_json"]["review"] == "stale" and "0.5 A" in sup2["ir_json"]["proposed_text"]["en"]
    assert "0.1 A" in sup2["text"]
    r = await client.post(f"/api/studies/{study}/interface-requirements/{sup['id']}/accept-update")
    assert r.status_code == 200 and "0.5 A" in r.json()["text"] and r.json()["ir_json"]["review"] is None


# ── IF-03 / IF-04: interface change and rejection ─────────────────────────

async def test_interface_change_marks_stale_and_rejection_retires(client, study_obj, study):
    parts = await build_eosat(client, study)
    await _accept_all(client, study)
    ifs = await _ifaces(client, study)
    data = next(i for i in ifs if i["type"] == "data" and i["to_element_id"] == parts["Star tracker"]["id"])
    mine = (await client.get(f"/api/studies/{study}/interfaces/{data['id']}/requirements")).json()["requirements"]
    assert len(mine) == 1 and "CAN" in mine[0]["text"]
    draft_id = mine[0]["id"]
    # a draft follows the interface silently
    await client.patch(f"/api/interfaces/{data['id']}", json={"properties": {"protocol": "UART"}})
    now = (await client.get(f"/api/studies/{study}/interfaces/{data['id']}/requirements")).json()["requirements"]
    assert now[0]["id"] == draft_id and "UART" in now[0]["text"] and now[0]["ir_json"]["review"] is None
    # an approved one is flagged for review
    await client.patch(f"/api/requirements/{draft_id}", json={"status": "approved"})
    await client.patch(f"/api/interfaces/{data['id']}", json={"properties": {"protocol": "CAN"}})
    now = (await client.get(f"/api/studies/{study}/interfaces/{data['id']}/requirements")).json()["requirements"]
    assert now[0]["ir_json"]["review"] == "stale" and "UART" in now[0]["text"]
    # rejection: the approved IR is proposed for retirement; drafts of another link retire at once
    other = next(i for i in ifs if i["type"] == "power" and i["to_element_id"] == parts["Star tracker"]["id"])
    o_irs = (await client.get(f"/api/studies/{study}/interfaces/{other['id']}/requirements")).json()["requirements"]
    await client.patch(f"/api/interfaces/{other['id']}", json={"status": "rejected"})
    await client.patch(f"/api/interfaces/{data['id']}", json={"status": "rejected"})
    from spacecdf_server.routers.requirements import _requirements
    assert all(_requirements[r["id"]]["status"] == "retired" for r in o_irs)
    assert _requirements[draft_id]["ir_json"]["review"] == "retire"


# ── IF-02: requirement → interface ────────────────────────────────────────

async def test_requirement_without_interface_proposes_it(client, study_obj, study):
    parts = await build_eosat(client, study)
    a, b = parts["OBC"]["id"], parts["Battery heater"]["id"]
    r = await client.post(f"/api/studies/{study}/interface-requirements", json={
        "from_element_id": a, "to_element_id": b, "interface_type": "electrical_signal",
        "text": "The OBC shall command the battery heater through a discrete line."})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created_interface"] and body["interface"]["origin"] == "rule:IF-02"
    assert body["interface"]["status"] == "suggested"
    assert body["requirement"]["ir_json"]["interface_id"] == body["interface"]["id"]
    # a second IR on the same pair and type links the same interface
    r2 = await client.post(f"/api/studies/{study}/interface-requirements", json={
        "from_element_id": b, "to_element_id": a, "interface_type": "electrical_signal", "text": "x"})
    assert r2.json()["interface"]["id"] == body["interface"]["id"] and not r2.json()["created_interface"]
    # an IR created through the generic route with no endpoints is reported without interface
    r3 = await client.post("/api/requirements/", json={"study_id": study, "level": "interface", "text": "Loose IR"})
    assert r3.status_code == 200
    st = (await _irs(client, study))["status"]
    assert r3.json()["id"] in st["without_interface"]


# ── electrical proposals and checks ──────────────────────────────────────

async def test_electrical_proposals_rails_buses_addresses(client, study_obj, study):
    parts = await build_eosat(client, study)
    r1 = (await client.post(f"/api/studies/{study}/electrical/propose", json={})).json()
    r2 = (await client.post(f"/api/studies/{study}/electrical/propose", json={})).json()
    assert r1["created"] > 0 and r2["created"] == 0 and r2["updated"] == 0      # idempotent
    v = await _elec(client, study)
    rails = {r["voltage_v"]: r for r in v["rails"]}
    assert rails[28.8]["regulated"] is False and rails[28.8]["v_min"] == 24.0 and rails[3.3]["regulated"]
    assert all(r["status"] == "suggested" and r["origin"] == "rule:EL-RAIL" for r in v["rails"])
    can = sorted((b for b in v["buses"] if b["protocol"] == "CAN"), key=lambda b: b["segment"])
    assert [b["segment"] for b in can] == ["A", "B"] and all(b["bit_rate_bps"] == 1e6 for b in can)
    nodes = {(n["bus_id"], n["element_id"]): n for n in v["nodes"]}
    seg_a = can[0]["id"]
    assert nodes[(seg_a, parts["OBC"]["id"])]["address"] == 1 and nodes[(seg_a, parts["OBC"]["id"])]["role"] == "master"
    assert nodes[(seg_a, parts["EPS"]["id"])]["address"] == 0x10
    assert (can[1]["id"], parts["S-band transceiver"]["id"]) in nodes
    addrs = [n["address"] for n in v["nodes"] if n["bus_id"] == seg_a]
    assert len(addrs) == len(set(addrs))
    kinds = {p["kind"] for p in v["ports"] if p["element_id"] == parts["EPS"]["id"]}
    assert {"power_out", "power_in", "data"} <= kinds
    assert not [c for c in v["checks"] if c["severity"] == "alarm"]


async def test_address_conflict_and_power_checks(client, study_obj, study):
    parts = await build_eosat(client, study)
    await client.post(f"/api/studies/{study}/electrical/propose", json={})
    v = await _elec(client, study)
    seg_a = next(b for b in v["buses"] if b["protocol"] == "CAN" and b["segment"] == "A")
    eps_node = next(n for n in v["nodes"] if n["bus_id"] == seg_a["id"] and n["element_id"] == parts["EPS"]["id"])
    rw_node = next(n for n in v["nodes"] if n["bus_id"] == seg_a["id"] and n["element_id"] == parts["Reaction wheel"]["id"])
    r = await client.patch(f"/api/studies/{study}/electrical/nodes/{rw_node['id']}", json={"address": "0x10"})
    assert r.status_code == 200 and r.json()["address"] == 16 and r.json()["edited"]
    checks = (await client.get(f"/api/studies/{study}/electrical/checks")).json()
    dup = [c for c in checks if c["id"].startswith("DATA-ADDR-DUP")]
    assert {c["target_id"] for c in dup} == {eps_node["id"], rw_node["id"]}
    assert dup[0]["message"]["fr"].startswith("L'adresse 0x10")
    # accepted on both sides → alarm; still a caution while the EPS node is only suggested
    assert {c["severity"] for c in dup} == {"caution"}
    await client.patch(f"/api/studies/{study}/electrical/nodes/{eps_node['id']}", json={"status": "accepted"})
    checks = (await client.get(f"/api/studies/{study}/electrical/checks")).json()
    assert {c["severity"] for c in checks if c["id"].startswith("DATA-ADDR-DUP")} == {"alarm"}
    # LCL below the peak current → alarm; rail capacity; EPS channel count
    line = next(ln for ln in v["lines"] if parts["S-band transceiver"]["id"] in ln["load_element_ids"])
    await client.patch(f"/api/studies/{study}/electrical/lines/{line['id']}", json={"lcl_limit_a": 0.01})
    rail = next(r for r in v["rails"] if r["id"] == line["rail_id"])
    await client.patch(f"/api/studies/{study}/electrical/rails/{rail['id']}", json={"max_current_a": 0.05})
    checks = (await client.get(f"/api/studies/{study}/electrical/checks")).json()
    ids = {c["id"].split(":")[0] for c in checks}
    assert {"PWR-LCL-OVER", "PWR-RAIL-CAP"} <= ids
    over = next(c for c in checks if c["id"].startswith("PWR-LCL-OVER"))
    assert over["severity"] == "alarm" and "28.8 V" in over["message"]["en"]


async def test_rejected_proposals_are_not_proposed_again(client, study_obj, study):
    await build_eosat(client, study)
    await client.post(f"/api/studies/{study}/electrical/propose", json={})
    v = await _elec(client, study)
    ln = v["lines"][0]
    r = await client.delete(f"/api/studies/{study}/electrical/lines/{ln['id']}")
    assert r.json() == {"id": ln["id"], "rejected": True}
    again = (await client.post(f"/api/studies/{study}/electrical/propose", json={})).json()
    assert again["created"] == 0 and again["skipped_rejected"] >= 1
    v2 = await _elec(client, study)
    assert next(x for x in v2["lines"] if x["id"] == ln["id"])["status"] == "rejected"
    # a user line
    r = await client.post(f"/api/studies/{study}/electrical/lines", json={
        "name": "Spare", "rail_id": v["rails"][0]["id"], "line_no": 20, "switchable": True})
    assert r.status_code == 200 and r.json()["origin"] == "user"


# ── IF-05 agreement and the PDR gate ─────────────────────────────────────

async def test_pdr_ec_02_counts_approved_and_agreed_interface_requirements(client, study_obj, study):
    from spacecdf_server.routers.elements import _elements, _interfaces
    from spacecdf_server.routers.requirements import _requirements
    from spacecdf_server.services.gate_evaluator import evaluate_gate
    await build_eosat(client, study)
    await _accept_all(client, study)

    def gate():
        els = [e for e in _elements.values() if e["study_id"] == study]
        ifs = [i for i in _interfaces.values() if i["study_id"] == study]
        reqs = [r for r in _requirements.values() if r["study_id"] == study]
        res = evaluate_gate("PDR", elements=els, interfaces=ifs, requirements=reqs)
        return next(c for c in res["criteria"] if c["id"] == "PDR-EC-02")

    c = gate()
    assert c["status"] == "fail" and c["evidence_params"].get("complete") == 0, (c["evidence_key"], c["evidence_params"])
    assert c["evidence_key"].startswith("{{complete}}/{{total}} accepted links")
    for r in (await _irs(client, study))["requirements"]:
        await client.patch(f"/api/requirements/{r['id']}", json={"status": "approved"})
    assert gate()["status"] == "fail"           # approved, not yet agreed by both seats
    for i in await _ifaces(client, study, status="accepted"):
        r = await client.post(f"/api/studies/{study}/interfaces/{i['id']}/agreement", json={"side": "both"})
        assert r.status_code == 200 and r.json()["agreement"]["state"] == "agreed"
    c = gate()
    assert c["status"] == "pass", c
    # an interface change resets the agreement and flags its approved requirements
    i = next(x for x in await _ifaces(client, study, status="accepted") if x["type"] == "data")
    await client.patch(f"/api/interfaces/{i['id']}", json={"properties": {"data_rate_bps": 9600}})
    ag = (await client.get(f"/api/studies/{study}/interfaces/{i['id']}/requirements")).json()["agreement"]
    assert ag["state"] == "defined" and ag["provider"] is None
    assert gate()["status"] == "fail"


# ── F6: SEMP and IRD use the model ───────────────────────────────────────

async def test_semp_and_ird_count_model_interface_requirements(client, study_obj, study):
    await build_eosat(client, study)
    await _accept_all(client, study)
    n_if = len(await _ifaces(client, study, status="accepted"))
    irs = (await _irs(client, study))["requirements"]
    r = await client.post(f"/api/ecss/dids/semp/generate?study_id={study}")
    assert r.status_code == 200, r.text
    sec9 = next(s for s in r.json()["sections"] if s["number"] == "9")
    assert f"{n_if} accepted interfaces" in sec9["content"] and f"{len(irs)} interface requirements" in sec9["content"]
    r = await client.post(f"/api/ecss/dids/ird/generate?study_id={study}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_interface_requirements"] == len([x for x in irs if x["ir_json"]["interface_id"]])
    text = "\n".join(s2["content"] for s in body["sections"] for s2 in s.get("subsections", []))
    assert irs[0]["code"] in text
