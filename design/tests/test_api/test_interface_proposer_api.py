"""Expected interfaces (Nov 2026): canonical types, persistence, the rule-based
proposer, accept/edit/reject, readiness and the gate/consistency checks that use them."""
from __future__ import annotations

import pytest

from tests.test_api.conftest import make_element, make_interface

KB_EQUIPMENT = {
    "power": ["bat-gom-nanopow-bpx", "eps-gom-nanopow-p60", "sp-gom-nanopow-p110"],
    "aocs": ["rw-cubew-medium", "st-cubespace-cubestar", "ss-nss-css-01", "mtq-isis-imtq"],
    "ttc": ["txr-endurosat-uhf-ii", "ant-endurosat-uhf-dipole"],
    "obc": ["obc-gom-nanomind-a3200"],
}


@pytest.fixture()
def broadcasts(monkeypatch):
    """Capture every study-WebSocket message."""
    sent: list[dict] = []
    from spacecdf_server.routers import ws

    async def _capture(study_id, message, exclude=None):
        sent.append(message)

    monkeypatch.setattr(ws, "_broadcast_study", _capture)
    return sent


async def _populated(client, study, include_equipment=True):
    mission = await make_element(client, study, "Mission", "mission")
    space = await make_element(client, study, "Space Segment", "segment", mission["id"])
    r = await client.post(f"/api/studies/{study}/populate-subsystems?parent_element_id={space['id']}",
                          json={"spacecraft_class": "nano", "include_equipment": include_equipment})
    assert r.status_code == 200, r.text
    return mission, space, r.json()


async def _ifaces(client, study, **q):
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    return (await client.get(f"/api/studies/{study}/interfaces?{qs}")).json()


async def _propose(client, study, **body):
    r = await client.post(f"/api/studies/{study}/interfaces/propose", json=body)
    assert r.status_code == 200, r.text
    return r.json()


# ── canonical vocabulary ──────────────────────────────────────────────────

async def test_types_endpoint_lists_canonical_types(client, study_obj, study):
    from spacecdf_common.models.interface_types import INTERFACE_TYPE_VALUES
    types = (await client.get(f"/api/studies/{study}/interfaces/types")).json()
    assert [t["id"] for t in types] == list(INTERFACE_TYPE_VALUES)
    power = next(t for t in types if t["id"] == "power")
    assert power["label"] == {"en": "Power", "fr": "Alimentation"} and power["glyph"] == "bolt"
    assert "Electrical" in power["annex_e"] and any(f["key"] == "rail_voltage" for f in power["fields"])
    assert all(t["label"]["fr"] and t["fields"] and t["subtypes"] for t in types)


async def test_old_spellings_are_mapped_and_unknown_rejected(client, study_obj, study):
    a = await make_element(client, study, "EPS", "subsystem", subsystem_domain="power")
    b = await make_element(client, study, "OBC", "subsystem", subsystem_domain="obc")
    i = await make_interface(client, study, a["id"], b["id"], interface_type="electrical")
    assert i["type"] == i["interface_type"] == "power" and i["origin"] == "user" and i["status"] == "accepted"
    r = await client.post(f"/api/interfaces/?study_id={study}", json={
        "interface_type": "plasma", "from_element_id": a["id"], "to_element_id": b["id"]})
    assert r.status_code == 400
    r = await client.post(f"/api/interfaces/?study_id={study}", json={
        "type": "propulsion", "from_element_id": a["id"], "to_element_id": b["id"]})
    assert r.json()["type"] == "fluid"
    assert len(await _ifaces(client, study, type="electrical")) == 1   # filter takes old spellings too
    # exchange-item kinds share the vocabulary (the old frontend 'command'/'signal' now work)
    r = await client.post(f"/api/exchange-items/?study_id={study}", json={"name": "TC", "kind": "command"})
    assert r.status_code == 200 and r.json()["kind"] == "data"
    r = await client.post(f"/api/exchange-items/?study_id={study}", json={"name": "Sep", "kind": "signal"})
    assert r.json()["kind"] == "electrical_signal"


async def test_legacy_rows_migrated_in_db_and_on_read(db_factory, study):
    from sqlalchemy import text
    from spacecdf_server.db import engine as engine_mod
    from spacecdf_server.db.element_repo import load_all_elements
    from spacecdf_server.db.migrate import ensure_interface_vocabulary

    async with db_factory() as s:
        for eid in ("e1", "e2"):
            await s.execute(text("INSERT INTO design_elements (id, study_id, name, element_type, version, margin_percent,"
                                 " quantity, in_scope, frozen, diagram_collapsed, segment, layer, description, created_at,"
                                 " updated_at) "
                                 f"VALUES ('{eid}', '{study}', '{eid}', 'subsystem', 1, 20, 1, 1, 0, 0, 'space', 'PA', '',"
                                 " '2026-01-01', '2026-01-01')"))
        await s.execute(text("INSERT INTO element_interfaces (id, study_id, name, interface_type, direction, "
                             "from_element_id, to_element_id, status, criticality, diagram_label, version, origin, "
                             "created_at, updated_at) "
                             f"VALUES ('i1', '{study}', 'old', 'electrical', 'in', 'e1', 'e2', 'defined', 'standard', '', 1, '',"
                             " '2026-01-01', '2026-01-01')"))
        await s.commit()
    _, ifaces = await load_all_elements()
    assert ifaces["i1"]["type"] == "power" and ifaces["i1"]["status"] == "accepted" and ifaces["i1"]["origin"] == "user"
    assert await ensure_interface_vocabulary(engine_mod._engine) == 3
    assert await ensure_interface_vocabulary(engine_mod._engine) == 0      # idempotent
    async with db_factory() as s:
        row = (await s.execute(text("SELECT interface_type, status, origin FROM element_interfaces"))).one()
    assert tuple(row) == ("power", "accepted", "user")


# ── persistence + broadcast (the prerequisite bugs) ───────────────────────

async def test_patch_persists_and_broadcasts(client, study_obj, study, broadcasts):
    from spacecdf_server.db.element_repo import load_all_elements
    a = await make_element(client, study, "EPS", "subsystem", subsystem_domain="power")
    b = await make_element(client, study, "OBC", "subsystem", subsystem_domain="obc")
    i = await make_interface(client, study, a["id"], b["id"], interface_type="power")
    assert {"type": "interface_changed", "interface": i} in broadcasts or \
        any(m.get("type") == "interface_changed" and m["interface"]["id"] == i["id"] for m in broadcasts)

    r = await client.patch(f"/api/studies/{study}/interfaces/{i['id']}",
                           json={"properties": {"rail_voltage": 5.0, "connector": "Molex"}, "subtype": "switched"})
    assert r.status_code == 200 and r.json()["version"] == 2
    r = await client.patch(f"/api/interfaces/{i['id']}", json={"properties": {"connector": None}})
    assert r.json()["properties"] == {"rail_voltage": 5.0}
    assert (await client.patch(f"/api/interfaces/{i['id']}", json={"version": 1, "name": "x"})).status_code == 409
    assert (await client.patch(f"/api/interfaces/{i['id']}", json={"status": "maybe"})).status_code == 400

    _, stored = await load_all_elements()          # what a restart would load
    assert stored[i["id"]]["properties"] == {"rail_voltage": 5.0}
    assert stored[i["id"]]["subtype"] == "switched" and stored[i["id"]]["version"] == 3
    assert any(m["type"] == "interface_changed" and m["interface"]["properties"] == {"rail_voltage": 5.0}
               for m in broadcasts)

    assert (await client.delete(f"/api/studies/{study}/interfaces/{i['id']}")).status_code == 200
    assert {"type": "interface_deleted", "id": i["id"]} in broadcasts
    _, stored = await load_all_elements()
    assert i["id"] not in stored


async def test_websocket_interface_create_is_persisted(client, study_obj, study, broadcasts):
    from spacecdf_server.db.element_repo import load_all_elements
    from spacecdf_server.routers.elements import store_interface
    a = await make_element(client, study, "A", "subsystem")
    b = await make_element(client, study, "B", "subsystem")
    iface = await store_interface({"study_id": study, "interface_type": "signal", "from_element_id": a["id"],
                                   "to_element_id": b["id"], "name": "ws"})
    _, stored = await load_all_elements()
    assert stored[iface["id"]]["type"] == "electrical_signal"
    assert any(m["type"] == "interface_changed" for m in broadcasts)


# ── the proposer ──────────────────────────────────────────────────────────

async def test_component_level_proposals_use_kb_data(client, study_obj, study):
    _, _, body = await _populated(client, study)
    ifaces = await _ifaces(client, study)
    els = {e["id"]: e for e in (await client.get(f"/api/studies/{study}/elements")).json()}

    def comp(kb_id):
        return next(e for e in els.values() if e.get("kb_component_id") == kb_id)

    def link(rule, to_id=None, from_id=None):
        return [i for i in ifaces if i["origin"] == f"rule:{rule}"
                and (to_id is None or i["to_element_id"] == to_id)
                and (from_id is None or i["from_element_id"] == from_id)]

    eps, obc, st = comp("eps-gom-nanopow-p60"), comp("obc-gom-nanomind-a3200"), comp("st-cubespace-cubestar")
    trx, ant = comp("txr-endurosat-uhf-ii"), comp("ant-endurosat-uhf-dipole")
    # power from the EPS on a rail it really offers (P60: 3.3/5/12 V)
    p = link("unit-power", obc["id"])
    assert len(p) == 1 and p[0]["from_element_id"] == eps["id"] and p[0]["properties"]["rail_voltage"] == 3.3
    # data protocol = common protocol of both ends, by priority (CAN first)
    d = link("unit-obc-tmtc", st["id"])
    assert d[0]["from_element_id"] == obc["id"] and d[0]["properties"]["protocol"] == "CAN"
    # RF coax between band-compatible transceiver and antenna
    rf = link("unit-rf-coax")
    assert len(rf) == 1 and (rf[0]["from_element_id"], rf[0]["to_element_id"]) == (trx["id"], ant["id"])
    assert rf[0]["properties"]["band"] == "UHF"
    # every unit mounted and thermally connected (fallback: the Structure subsystem)
    subs = body["subsystem_ids"]
    assert all(i["from_element_id"] == subs["structure"] for i in link("unit-mount"))
    assert {i["to_element_id"] for i in link("unit-mount")} >= {eps["id"], obc["id"], st["id"], trx["id"], ant["id"]}
    assert link("unit-mount", obc["id"])[0]["properties"]["mount_type"] == "PC/104 stack"
    # battery needs a heater (C2O default), the Thermal subsystem provides it
    bat = comp("bat-gom-nanopow-bpx")
    assert link("unit-heater", bat["id"])[0]["from_element_id"] == subs["thermal"]
    # CubeSat safety: deployment switch, RBF, RF inhibits, deployable release (CDS rev 14.1)
    assert link("unit-deployment-switch", eps["id"]) and link("unit-rbf", eps["id"])
    assert link("unit-rf-inhibits", trx["id"])[0]["properties"] == {"inhibit_count": 3, "delay_min": 45}
    assert link("unit-deploy-release", ant["id"])[0]["properties"]["delay_min"] == 30
    assert not any(i["type"] not in ("power", "data", "rf", "mechanical", "thermal", "timing", "optical", "fluid",
                                     "electrical_signal") for i in ifaces)


async def test_propose_is_idempotent_and_respects_reject_accept_edit(client, study_obj, study, broadcasts):
    _, _, body = await _populated(client, study, include_equipment=False)
    subs = body["subsystem_ids"]
    again = await _propose(client, study)
    assert again["created"] == [] and again["updated"] == [] and again["removed"] == []
    assert again["unchanged"] == len(await _ifaces(client, study))

    ifaces = await _ifaces(client, study)
    pwr_obc = next(i for i in ifaces if i["origin"] == "rule:sub-power-distribution" and i["to_element_id"] == subs["obc"])
    mount = next(i for i in ifaces if i["origin"] == "rule:sub-structure-mount" and i["to_element_id"] == subs["obc"])
    data = next(i for i in ifaces if i["origin"] == "rule:sub-obc-tmtc" and i["to_element_id"] == subs["aocs"])

    # reject: kept as rejected, never re-proposed, excluded from analyses
    r = await client.patch(f"/api/studies/{study}/interfaces/{pwr_obc['id']}", json={"status": "rejected"})
    assert r.json()["status"] == "rejected" and r.json()["origin"] == "rule:sub-power-distribution"
    # accept: stays the rule's link
    r = await client.patch(f"/api/studies/{study}/interfaces/{mount['id']}", json={"status": "accepted"})
    assert r.json()["status"] == "accepted" and r.json()["origin"] == "rule:sub-structure-mount"
    # edit: becomes the user's, accepted
    r = await client.patch(f"/api/studies/{study}/interfaces/{data['id']}", json={"properties": {"protocol": "CAN"}})
    assert r.json()["origin"] == "user" and r.json()["status"] == "accepted"

    res = await _propose(client, study)
    assert res["created"] == [] and res["skipped_rejected"] == 1
    assert len(await _ifaces(client, study, status="rejected")) == 1
    from spacecdf_server.routers.elements import active_interfaces
    assert pwr_obc["id"] not in {i["id"] for i in active_interfaces(study)}

    # restore: the user brings the rejected suggestion back
    r = await client.patch(f"/api/studies/{study}/interfaces/{pwr_obc['id']}", json={"status": "suggested"})
    assert r.json()["status"] == "suggested"
    assert (await _propose(client, study))["created"] == []


async def test_suggestions_follow_rule_changes_accepted_links_do_not(client, study_obj, study):
    _, _, body = await _populated(client, study, include_equipment=False)
    subs = body["subsystem_ids"]
    ifaces = await _ifaces(client, study)
    heat = [i for i in ifaces if i["origin"] == "rule:sub-thermal-heaters"]
    assert len(heat) == 3
    acc = next(i for i in heat if i["to_element_id"] == subs["power"])
    await client.patch(f"/api/interfaces/{acc['id']}", json={"status": "accepted"})
    # The propulsion subsystem goes away: its suggested links are dropped by the cascade,
    # the payload subsystem goes out of the thermal rule's reach by changing domain.
    from spacecdf_server.routers.elements import _elements
    pl = _elements[subs["payload"]]
    r = await client.patch(f"/api/elements/{pl['id']}", json={"version": pl["version"], "subsystem_domain": "obc"})
    assert r.status_code == 200
    res = await _propose(client, study)
    removed = set(res["removed"])
    assert next(i["id"] for i in heat if i["to_element_id"] == subs["payload"]) in removed
    assert acc["id"] not in removed
    still = {i["id"] for i in await _ifaces(client, study)}
    assert acc["id"] in still


async def test_dry_run_scope_unmet_and_conflicts(client, study_obj, study):
    mission = await make_element(client, study, "Mission", "mission")
    space = await make_element(client, study, "Space Segment", "segment", mission["id"])
    sc = await make_element(client, study, "Spacecraft", "system", space["id"])
    obc_sub = await make_element(client, study, "OBC", "subsystem", sc["id"], "obc")
    aocs = await make_element(client, study, "AOCS", "subsystem", sc["id"], "aocs")
    # two units with no common bus: the GPS speaks UART/SPI, the RW only I2C/SPI... make it disjoint
    r = await client.post(f"/api/elements/?study_id={study}", json={
        "name": "NanoMind A3200", "element_type": "component", "parent_id": obc_sub["id"],
        "kb_component_id": "obc-gom-nanomind-a3200"})
    obc = r.json()
    r = await client.post(f"/api/elements/?study_id={study}", json={
        "name": "Odd wheel", "element_type": "component", "parent_id": aocs["id"], "power_avg_w": 1.0,
        "performance": {"interfaces": ["RS485"]}})
    wheel = r.json()

    dry = await _propose(client, study, dry_run=True)
    assert dry["dry_run"] and dry["created"] and all(c["id"] is None for c in dry["created"])
    assert await _ifaces(client, study) == []
    # no EPS anywhere: every powered unit/subsystem is an unmet power need
    assert {(u["element_id"], u["need"]) for u in dry["unmet"]} >= {(wheel["id"], "power"), (obc["id"], "power"),
                                                                  (aocs["id"], "power")}
    assert all(u["reason"]["en"] and u["reason"]["fr"] for u in dry["unmet"])
    # protocol mismatch OBC (I2C/SPI/UART/CAN) vs wheel (RS485) → caution on the suggestion
    conf = [c for c in dry["conflicts"] if set(c["element_ids"]) == {obc["id"], wheel["id"]}]
    assert conf and conf[0]["severity"] == "caution" and "RS485" in conf[0]["reason"]["en"]

    scoped = await _propose(client, study, level=3, element_id=aocs["id"])
    assert scoped["created"] and all(wheel["id"] in (c["from_element_id"], c["to_element_id"])
                                     for c in scoped["created"])
    assert all(c["origin"].startswith("rule:unit-") for c in scoped["created"])
    # accepted with the mismatch → alarm
    link = next(c for c in scoped["created"] if c["type"] == "data")
    await client.patch(f"/api/interfaces/{link['id']}", json={"status": "accepted"})
    res = await _propose(client, study, dry_run=True)
    assert any(c["interface_id"] == link["id"] and c["severity"] == "alarm" for c in res["conflicts"])
    assert (await client.post(f"/api/studies/{study}/interfaces/propose", json={"element_id": "ghost"})).status_code == 404


async def test_element_create_triggers_proposal(client, study_obj, study, monkeypatch, broadcasts):
    monkeypatch.setenv("SPACECDF_AUTO_PROPOSE", "1")
    sc = await make_element(client, study, "Spacecraft", "system")
    eps = await make_element(client, study, "EPS", "subsystem", sc["id"], "power")
    assert await _ifaces(client, study) == []
    obc = await make_element(client, study, "OBC", "subsystem", sc["id"], "obc")
    ifaces = await _ifaces(client, study)
    assert any(i["from_element_id"] == eps["id"] and i["to_element_id"] == obc["id"] and i["type"] == "power"
               for i in ifaces)
    assert any(m["type"] == "interfaces_proposed" for m in broadcasts)
    await client.delete(f"/api/elements/{obc['id']}")
    assert await _ifaces(client, study) == []


async def test_invalid_rules_file_is_reported(client, study_obj, study, monkeypatch, tmp_path):
    from spacecdf_server.services.interface_proposer import rules_path, validate_rules
    import yaml
    doc = yaml.safe_load(rules_path().read_text(encoding="utf-8"))
    assert validate_rules(doc) == []
    doc["rules"][0]["type"] = "electrical"
    doc["rules"][1]["rationale"] = {"en": "only English"}
    doc["rules"][2]["from"] = {"roles": ["warp_drive"]}
    doc["rules"].append(dict(doc["rules"][3]))
    errs = validate_rules(doc)
    assert any("not a canonical interface type" in e for e in errs)
    assert any("rationale" in e for e in errs) and any("warp_drive" in e for e in errs)
    assert any("duplicate" in e for e in errs)
    bad = tmp_path / "rules.yaml"
    bad.write_text(yaml.safe_dump(doc), encoding="utf-8")
    monkeypatch.setenv("SPACECDF_INTERFACE_RULES", str(bad))
    r = await client.post(f"/api/studies/{study}/interfaces/propose", json={})
    assert r.status_code == 422 and r.json()["detail"]["errors"]
    info = (await client.get(f"/api/studies/{study}/interfaces/rules")).json()
    assert info["ok"] is False


# ── readiness, consistency, gate ──────────────────────────────────────────

async def test_readiness_interfaces_and_suggestions(client, study_obj, study):
    _, space, body = await _populated(client, study, include_equipment=False)
    sc = body["system_id"]
    r = (await client.get(f"/api/studies/{study}/readiness?level=2&element_id={sc}")).json()
    items = {i["id"]: i for i in r["items"]}
    assert set(items) >= {"elements_defined", "interfaces_defined", "suggested_reviewed", "all_frozen"}
    assert all(i["label"]["en"] and i["label"]["fr"] and i["detail"]["fr"] for i in r["items"])
    assert items["interfaces_defined"]["ok"] is True
    assert items["interfaces_defined"]["counts"]["by_type"]["power"]["required"] == 6
    assert items["suggested_reviewed"]["ok"] is False and items["suggested_reviewed"]["counts"]["suggested"] > 0

    # reject the OBC's power link → coverage fails for that need
    subs = body["subsystem_ids"]
    pwr = next(i for i in await _ifaces(client, study)
               if i["origin"] == "rule:sub-power-distribution" and i["to_element_id"] == subs["obc"])
    await client.patch(f"/api/interfaces/{pwr['id']}", json={"status": "rejected"})
    items = {i["id"]: i for i in (await client.get(
        f"/api/studies/{study}/readiness?element_id={sc}")).json()["items"]}
    assert items["interfaces_defined"]["ok"] is False
    assert {"element_id": subs["obc"], "need": "power"}.items() <= items["interfaces_defined"]["counts"]["missing"][0].items()
    assert "power link" in items["interfaces_defined"]["detail"]["en"]
    assert "liaison d'alimentation" in items["interfaces_defined"]["detail"]["fr"]

    # accept everything else → suggestions reviewed
    for i in await _ifaces(client, study, status="suggested"):
        await client.patch(f"/api/interfaces/{i['id']}", json={"status": "accepted"})
    items = {i["id"]: i for i in (await client.get(
        f"/api/studies/{study}/readiness?element_id={sc}")).json()["items"]}
    assert items["suggested_reviewed"]["ok"] is True


async def test_pdr_gate_and_consistency_use_interfaces(client, study_obj, study):
    from spacecdf_server.routers.elements import _elements, _interfaces
    from spacecdf_server.services.consistency_engine import run_consistency_check
    from spacecdf_server.services.gate_evaluator import evaluate_gate
    from spacecdf_server.services.readiness import build_context, interface_coverage

    _, _, body = await _populated(client, study, include_equipment=False)
    els = [e for e in _elements.values() if e["study_id"] == study]

    def gate():
        ifs = [i for i in _interfaces.values() if i["study_id"] == study and not i.get("deleted_at")]
        res = evaluate_gate("PDR", elements=els, interfaces=ifs)
        return next(c for c in res["criteria"] if c["id"] == "PDR-EC-02")

    c = gate()
    assert c["status"] == "fail" and c["evidence_params"]["suggested"] > 0
    for i in await _ifaces(client, study, status="suggested"):
        await client.patch(f"/api/interfaces/{i['id']}", json={"status": "accepted"})
    c = gate()
    assert c["status"] == "pass" and c["evidence_key"].startswith("All {{required}}")

    obc = body["subsystem_ids"]["obc"]
    for i in list(_interfaces.values()):
        if i["to_element_id"] == obc and i["type"] == "mechanical":
            await client.patch(f"/api/interfaces/{i['id']}", json={"status": "rejected"})
    ifs = [i for i in _interfaces.values() if i["study_id"] == study]
    cov = interface_coverage(build_context(study, els), ifs)
    rep = run_consistency_check(interfaces=ifs, interface_coverage=cov)
    issue = next(i for i in rep.issues if i.id == "CON-IF-01")
    assert obc in issue.affected_items
    assert gate()["status"] == "fail"
