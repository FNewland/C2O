"""CDR design model over HTTP (routers/cdr.py): the TM/TC database, FDIR, AOCS modes, TT&C
ladder, line states and operations proposed from an EOSAT-1-like design; the proposal life
cycle; ownership; the EOSAT-1 reference import and its round trip to the simulator shapes.
"""
from __future__ import annotations

import pytest

from tests.test_api.test_electrical_api import _accept_all, build_eosat


@pytest.fixture(autouse=True)
def _auto(monkeypatch):
    monkeypatch.setenv("SPACECDF_AUTO_IRD", "0")


async def _design(client, study) -> dict:
    """EOSAT-like parts, accepted links, electrical rows accepted, ConOps modes, rule-8 proposals."""
    parts = await build_eosat(client, study)
    await _accept_all(client, study)
    assert (await client.post(f"/api/studies/{study}/electrical/propose", json={})).status_code == 200
    assert (await client.post(f"/api/studies/{study}/modes/template", json={})).status_code == 200
    assert (await client.post(f"/api/studies/{study}/modes/propose", json={})).status_code == 200
    r = await client.post(f"/api/studies/{study}/design-rules/run?thermal=false")
    assert r.status_code == 200, r.text
    return parts


async def _view(client, study) -> dict:
    r = await client.get(f"/api/studies/{study}/cdr")
    assert r.status_code == 200, r.text
    return r.json()


def _data(view: dict, kind: str) -> list[dict]:
    return [r["data"] for r in view["rows"][kind] if r["status"] != "rejected"]


async def test_propose_default_database_from_the_design(client, study_obj, study):
    parts = await _design(client, study)
    r = await client.post(f"/api/studies/{study}/cdr/propose", json={})
    assert r.status_code == 200, r.text
    assert r.json()["created"] > 50
    v = await _view(client, study)
    assert v["dataset"] == "design"
    params = _data(v, "parameters")
    names = {p["name"] for p in params}
    assert {"eps.bus_voltage", "eps.bat_soc", "aocs.mode", "obdh.reboot_count", "ttc.rssi", "sys.sc_mode"} <= names
    # ids in the subsystem's EOSAT-1 block, unique
    ids = [p["param_id"] for p in params]
    assert len(ids) == len(set(ids))
    assert all(0x0100 <= p["param_id"] <= 0x01FF for p in params if p["subsystem"] == "eps")
    # one parameter per power line state, with the line id
    lines = v["lines"]
    assert lines and all(any(p.get("line_id") == ln["id"] and ".pl_" in p["name"] for p in params) for ln in lines)
    # the reaction wheel's monitored speed parameter exists and carries its element
    assert any(p["source_element_id"] == parts["Reaction wheel"]["id"] and p["name"].endswith("_speed") for p in params)
    # housekeeping: one SID per subsystem + beacon; every non-on-demand parameter is in a SID
    hk = _data(v, "hk")
    assert any(h["beacon"] and h["sid"] == 11 for h in hk)
    assert {h["subsystem"] for h in hk if not h["beacon"]} >= {"eps", "aocs", "obdh", "ttc"}
    in_hk = {i for h in hk for i in h["parameter_ids"]}
    assert all(p["param_id"] in in_hk for p in params if not p["on_demand"])
    # TC functions: S8 ids unique; every switchable line covered by EPS_POWER_ON / OFF
    cmds = {c["name"]: c for c in _data(v, "commands")}
    assert {"EPS_POWER_ON", "EPS_POWER_OFF", "AOCS_SET_MODE", "SYS_ENTER_SAFE", "TTC_SET_RATE"} <= set(cmds)
    fids = [c["func_id"] for c in cmds.values()]
    assert len(fids) == len(set(fids))
    assert cmds["OBC_REBOOT"]["criticality"] == "critical" and cmds["OBC_REBOOT"]["arm_execute"]
    sw = [ln["line_no"] for ln in lines if ln["switchable"]]
    assert set(sw) <= set(next(a for a in cmds["EPS_POWER_OFF"]["args"] if a["name"] == "line_index")["values"])
    assert "PROP_ARM" not in cmds            # no thruster in this design
    # events: standard + one per monitor; monitors promoted from rule 8 with validity on the unit's line
    mons = _data(v, "monitors")
    promoted = [m for m in mons if m.get("source_proposal_id")]
    assert promoted, "rule-8 monitor proposals are promoted into the FDIR model"
    assert any(m.get("validity") and m["validity"]["parameter"].startswith("eps.pl_") for m in promoted)
    evs = {e["name"] for e in _data(v, "events")}
    assert "SAFE_MODE_ENTERED" in evs and all(m["event_name"] in evs for m in mons if m.get("event_name"))
    # bus monitors sit on the named levels of the load-shed table (28.8 V BPX bus → levels)
    shed = _data(v, "load_shed")[0]
    levels = {k: x["value"] for k, x in shed["bus_protection"].items()}
    bus_mons = [m for m in mons if m["parameter"] == "eps.bus_voltage"]
    if levels["uv_v"] is not None:
        assert {m["low"] for m in bus_mons} == {levels["uv_v"], levels["eps_safe_v"]}
        assert levels["uv_v"] > levels["eps_safe_v"] > levels["aocs_safe_v"]
    # safe mode, AOCS modes, rate ladder, positions
    safe = _data(v, "safe_mode")[0]
    assert safe["aocs_mode"] == "COARSE_SUN" and safe["rate_tier"] == "LOW" and safe["exit"]["function"] == "SYS_EXIT_SAFE"
    aocs = {m["name"] for m in _data(v, "aocs_modes")}
    assert {"DETUMBLE", "NOMINAL", "FINE_POINT"} <= aocs or "NOMINAL" in aocs
    tiers = [t["name"] for t in _data(v, "rate_tiers")]
    assert tiers[0] == "SAFE" and "LOW" in tiers
    pos = {p["id"] for p in _data(v, "positions")}
    assert "flight_director" in pos and "eps_tcs" in pos
    # line states per mode: one row per mode; the OBC line is on in every mode
    ls = _data(v, "line_states")
    assert len(ls) == len(v["modes"]) == 8          # W1.03: the template has the disposal mode
    obc_line = next(ln for ln in lines if not ln["switchable"])
    assert all(s["states"][obc_line["id"]] == "on" for s in ls)
    # owners: parameters by subsystem seat, the rest of the DB by Comms & OBDH
    by_name = {r["data"]["name"]: r for r in v["rows"]["parameters"]}
    assert by_name["eps.bus_voltage"]["owner_seat"] == "power_engineer"
    assert by_name["aocs.mode"]["owner_seat"] == "aocs_engineer"
    assert v["rows"]["hk"][0]["owner_seat"] == "comms_engineer"
    # budget closes in every regime for this database
    assert all(r["ok"] for r in v["budget"]["regimes"] if r["ok"] is not None)
    assert len(v["budget"]["modes"]) == 8


async def test_propose_is_idempotent_and_keeps_edits(client, study_obj, study):
    await _design(client, study)
    await client.post(f"/api/studies/{study}/cdr/propose", json={})
    again = (await client.post(f"/api/studies/{study}/cdr/propose", json={})).json()
    assert again["created"] == 0 and again["updated"] == 0 and again["removed"] == 0
    v = await _view(client, study)
    row = next(r for r in v["rows"]["hk"] if r["data"]["subsystem"] == "aocs")
    r = await client.patch(f"/api/studies/{study}/cdr/hk/{row['id']}", json={"data": {"period_s": 2}})
    assert r.status_code == 200 and r.json()["edited"] and r.json()["status"] == "accepted"
    await client.post(f"/api/studies/{study}/cdr/propose", json={})
    row2 = next(r for r in (await _view(client, study))["rows"]["hk"] if r["id"] == row["id"])
    assert row2["data"]["period_s"] == 2
    # reject a command: kept, never re-proposed
    cmd = next(r for r in v["rows"]["commands"] if r["data"]["name"] == "TTC_TX_ON")
    assert (await client.delete(f"/api/studies/{study}/cdr/commands/{cmd['id']}")).json()["rejected"]
    res = (await client.post(f"/api/studies/{study}/cdr/propose", json={})).json()
    assert res["skipped_rejected"] >= 1
    rows = (await _view(client, study))["rows"]["commands"]
    assert next(r for r in rows if r["id"] == cmd["id"])["status"] == "rejected"


async def test_checks_find_broken_database(client, study_obj, study):
    await _design(client, study)
    await client.post(f"/api/studies/{study}/cdr/propose", json={})
    v = await _view(client, study)
    p0, p1 = v["rows"]["parameters"][:2]
    # duplicate parameter id
    await client.patch(f"/api/studies/{study}/cdr/parameters/{p1['id']}", json={"data": {"param_id": p0["data"]["param_id"]}})
    # an event-action calling a function that does not exist
    ea = v["rows"]["event_actions"][0]
    await client.patch(f"/api/studies/{study}/cdr/event_actions/{ea['id']}", json={"data": {"action": "NO_SUCH_FN"}})
    # the safe mode switching off the OBC line
    safe = v["rows"]["safe_mode"][0]
    obc_line = next(ln for ln in v["lines"] if not ln["switchable"])
    await client.patch(f"/api/studies/{study}/cdr/safe_mode/{safe['id']}", json={"data": {"line_ids_off": [obc_line["id"]]}})
    # a very slow downlink: HK no longer fits
    for t in v["rows"]["rate_tiers"]:
        await client.patch(f"/api/studies/{study}/cdr/rate_tiers/{t['id']}", json={"data": {"bps": 100}})
    rules = {c["rule"] for c in (await client.get(f"/api/studies/{study}/cdr/checks")).json()}
    assert {"TMTC-PARAM", "FDIR-EA", "FDIR-SAFE", "TMTC-HK-BW"} <= rules


async def test_unknown_kind_and_power_line_without_tc(client, study_obj, study):
    await _design(client, study)
    await client.post(f"/api/studies/{study}/cdr/propose", json={})
    assert (await client.get(f"/api/studies/{study}/cdr/nope/x")).status_code in (404, 405)
    v = await _view(client, study)
    off = next(r for r in v["rows"]["commands"] if r["data"]["name"] == "EPS_POWER_OFF")
    args = [{**a, "values": []} if a["name"] == "line_index" else a for a in off["data"]["args"]]
    await client.patch(f"/api/studies/{study}/cdr/commands/{off['id']}", json={"data": {"args": args}})
    checks = (await client.get(f"/api/studies/{study}/cdr/checks")).json()
    assert any(c["rule"] == "TMTC-TC-LINE" for c in checks)


async def test_eosat1_reference_import_round_trips(client, study_obj, study):
    r = await client.post(f"/api/studies/{study}/cdr/import/eosat1", json={})
    assert r.status_code == 200, r.text
    counts = r.json()["counts"]
    assert counts["parameters"] == 458 and counts["hk"] == 11 and counts["commands"] == 220 and counts["events"] == 155
    assert counts["monitors"] == 41 and counts["event_actions"] == 30 + 17 and counts["rate_tiers"] == 3
    v = await _view(client, study)
    assert v["dataset"] == "reference"
    assert not [c for c in v["checks"] if c["severity"] == "alarm"], [c["message"]["en"] for c in v["checks"] if c["severity"] == "alarm"]
    # read-only
    row = v["rows"]["parameters"][0]
    r = await client.patch(f"/api/studies/{study}/cdr/parameters/{row['id']}", json={"data": {"unit": "x"}})
    assert r.status_code == 423
    assert (await client.post(f"/api/studies/{study}/cdr/propose", json={})).status_code == 409
    # export back to the simulator shapes
    files = (await client.get(f"/api/studies/{study}/cdr/export/sim")).json()["files"]
    import yaml
    from spacecdf_server.services.cdr_sim import sim_dir
    root = sim_dir()
    src_p = yaml.safe_load((root / "telemetry/parameters.yaml").read_text())["parameters"]
    assert [(p["id"], p["name"]) for p in files["telemetry/parameters.yaml"]["parameters"]] == \
        sorted((p["id"], p["name"]) for p in src_p)
    src_hk = yaml.safe_load((root / "telemetry/hk_structures.yaml").read_text())["structures"]
    out_hk = files["telemetry/hk_structures.yaml"]["structures"]
    assert [(s["sid"], [p["param_id"] for p in s["parameters"]]) for s in out_hk] == \
        [(s["sid"], [p["param_id"] for p in s["parameters"]]) for s in src_hk]
    src_tc = yaml.safe_load((root / "commands/tc_catalog.yaml").read_text())["commands"]
    assert [(t["name"], t.get("func_id")) for t in files["commands/tc_catalog.yaml"]["commands"]] == \
        [(t["name"], t.get("func_id")) for t in src_tc]
    assert len(files["events/event_catalog.yaml"]["events"]) == 155
    assert len(files["monitoring/s12_definitions.yaml"]["s12_definitions"]) == 41
    assert len(files["monitoring/s19_rules.yaml"]["s19_rules"]) == 30
    assert len(files["subsystems/fdir.yaml#rules"]["rules"]) == 17
    assert files["simulation.yaml#housekeeping"]["default_enabled_sids"] == [1, 11]
    # removing the import empties the study; importing over a design needs replace
    assert (await client.delete(f"/api/studies/{study}/cdr/import")).json()["removed"] == sum(counts.values())


async def test_import_refused_over_a_design(client, study_obj, study):
    await _design(client, study)
    await client.post(f"/api/studies/{study}/cdr/propose", json={})
    r = await client.post(f"/api/studies/{study}/cdr/import/eosat1", json={})
    assert r.status_code == 409
    r = await client.post(f"/api/studies/{study}/cdr/import/eosat1", json={"replace": True})
    assert r.status_code == 200 and (await _view(client, study))["dataset"] == "reference"


async def test_fmeca_detection_credit_only_from_accepted_monitors(client, study_obj, study):
    await _design(client, study)
    await client.post(f"/api/studies/{study}/cdr/propose", json={})
    v = await _view(client, study)
    cov = v["fmeca"]
    assert cov["summary"]["critical_detected"] == 0          # suggestions do not count
    for m in v["rows"]["monitors"]:
        await client.patch(f"/api/studies/{study}/cdr/monitors/{m['id']}", json={"status": "accepted"})
    cov2 = (await _view(client, study))["fmeca"]
    assert cov2["summary"]["critical_detected"] >= 1 or cov2["summary"]["critical"] == 0
    det = [x for x in cov2["rows"] if x["detected"]]
    assert det and all(x["monitors_counted"] for x in det)


async def test_create_row_and_duplicates(client, study_obj, study):
    r = await client.post(f"/api/studies/{study}/cdr/flight_rules",
                          json={"data": {"rule_id": "FR-99", "text": {"en": "No imaging over the poles.", "fr": "Pas d’imagerie au-dessus des pôles."}}})
    assert r.status_code == 200, r.text
    assert r.json()["owner_seat"] == "mission_analyst" and r.json()["origin"] == "user"
    r = await client.post(f"/api/studies/{study}/cdr/flight_rules", json={"data": {"rule_id": "FR-99"}})
    assert r.status_code == 409
    r = await client.post(f"/api/studies/{study}/cdr/parameters", json={"data": {"name": "eps.x", "param_id": "0x01F0", "subsystem": "eps"}})
    assert r.status_code == 200 and r.json()["data"]["param_id"] == 0x01F0 and r.json()["owner_seat"] == "power_engineer"


# ── CDR gate ─────────────────────────────────────────────────────────────

async def test_cdr_gate_reads_the_cdr_model(client, study_obj, study):
    ov = (await client.get(f"/api/studies/{study}/gates")).json()
    assert [g["id"] for g in ov["gates"]] == ["mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr"]
    cdr_gate = next(g for g in ov["gates"] if g["id"] == "cdr")
    assert cdr_gate["margin_gate"] == "cdr"
    g = (await client.get(f"/api/studies/{study}/rules/gates/cdr")).json()
    by = {c["id"]: c for c in g["criteria"]}
    assert [c["id"] for c in g["criteria"]] == [f"CDR-EC-{i:02d}" for i in range(1, 12)]
    assert g["system_margin"]["mass_percent"] == 10
    assert by["CDR-EC-03"]["status"] == "fail" and "propose" in by["CDR-EC-03"]["evidence_found"]
    assert {p["id"] for p in g["products_baselined"]} >= {"tmtc_db", "fdir_spec", "aocs_design", "interfaces", "design_files"}

    await _design(client, study)
    await client.post(f"/api/studies/{study}/cdr/propose", json={})
    by = {c["id"]: c for c in (await client.get(f"/api/studies/{study}/rules/gates/cdr")).json()["criteria"]}
    assert by["CDR-EC-03"]["status"] == "fail" and by["CDR-EC-03"]["evidence_params"]["suggested"] > 0
    assert by["CDR-EC-04"]["status"] == "pass"
    assert by["CDR-EC-06"]["status"] == "pass", by["CDR-EC-06"]["evidence_found"]
    assert by["CDR-EC-08"]["status"] == "pass", by["CDR-EC-08"]["evidence_found"]
    assert by["CDR-EC-05"]["status"] == "fail"           # suggested monitors earn no detection credit

    r = (await client.post(f"/api/studies/{study}/cdr/accept-all", json={"group": "tmtc"})).json()
    assert r["accepted"] > 50 and r["left_for_owner"] == 0
    by = {c["id"]: c for c in (await client.get(f"/api/studies/{study}/rules/gates/cdr")).json()["criteria"]}
    assert by["CDR-EC-03"]["status"] == "pass", by["CDR-EC-03"]["evidence_found"]
    await client.post(f"/api/studies/{study}/cdr/accept-all", json={"group": "fdir"})
    cov = (await _view(client, study))["fmeca"]["summary"]
    assert cov["critical_detected"] > 0


async def test_cdr_decisions_are_due_at_the_cdr(client, study_obj, study):
    body = (await client.get(f"/api/logbook/decisions?study_id={study}&gate=cdr")).json()
    cdr_ids = {d["id"] for d in body["decisions"] if d["ecss_gate"] == "cdr"}
    assert {"D-CDR-TMTCDB", "D-CDR-LOADSHED", "D-CDR-AOCSMODES", "D-5.2-SAFEMODE", "D-3.3-LADDER", "D-5.2-FLIGHTRULES"} <= cdr_ids
    assert cdr_ids <= set(body["due"]["open"])
    tm = next(d for d in body["decisions"] if d["id"] == "D-CDR-TMTCDB")
    assert tm["part"] is None and tm["no_workbook_part"] is True
    pdr = (await client.get(f"/api/logbook/decisions?study_id={study}&gate=pdr")).json()
    assert not cdr_ids & set(pdr["due"]["open"])


async def test_pending_change_for_another_seat(client, study_obj, study, monkeypatch):
    """Ruling 5 on a CDR row: Comms & OBDH editing a Power parameter → 409, then a pending change
    the Power seat accepts; the owner's value stands until then."""
    from spacecdf_server.seats import store
    from spacecdf_server.seats.instructor import invalidate_gate_cache
    from tests.test_api.test_seats_api import INSTRUCTOR, claim, iap, seat_study
    monkeypatch.setenv("SPACECDF_INSTRUCTORS", INSTRUCTOR)
    store.reset_memory()
    invalidate_gate_cache()
    await _design(client, study)
    await client.post(f"/api/studies/{study}/cdr/propose", json={})
    v = await _view(client, study)
    row = next(r for r in v["rows"]["parameters"] if r["data"]["name"] == "eps.bus_voltage")
    await seat_study(client, study)
    comms, power = iap("comms@c2o.live", "Carol"), iap("power@c2o.live", "Pat")
    await claim(client, study, comms, "comms_engineer")
    await claim(client, study, power, "power_engineer")
    url = f"/api/studies/{study}/cdr/parameters/{row['id']}"
    r = await client.patch(url, json={"data": {"unit": "mV"}}, headers=comms)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "owned_by_other_seat"
    r = await client.patch(url, json={"data": {"unit": "mV"}}, headers={**comms, "X-C2O-Confirm-Review": "1"})
    assert r.status_code == 202, r.text
    pc = r.json()["pending_change"]
    assert pc["owner_seat"] == "power_engineer" and pc["kind"] == "cdr"
    unit = lambda vv: next(x for x in vv["rows"]["parameters"] if x["id"] == row["id"])["data"]["unit"]  # noqa: E731
    assert unit(await _view(client, study)) == "V"
    # the owner edits its own rows directly; accept-all leaves other seats' suggestions
    hk = next(r for r in v["rows"]["hk"])
    assert (await client.patch(f"/api/studies/{study}/cdr/hk/{hk['id']}", json={"status": "accepted"}, headers=comms)).status_code == 200
    left = (await client.post(f"/api/studies/{study}/cdr/accept-all", json={"group": "tmtc"}, headers=comms)).json()
    assert left["left_for_owner"] > 0
    r = await client.post(f"/api/studies/{study}/team/pending/{pc['id']}/accept", json={"comment": "ok"}, headers=power)
    assert r.status_code == 200, r.text
    assert unit(await _view(client, study)) == "mV"
    store.reset_memory()
