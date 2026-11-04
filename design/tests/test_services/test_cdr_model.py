"""CDR design model, pure parts (services/cdr_*): config, reconcile, checks, HK budget, the
EOSAT-1 import and export, the frame converter and the reference template orbit."""
from __future__ import annotations

import copy

import pytest
import yaml

from spacecdf_server.services import cdr_checks, cdr_model as cm, cdr_sim


@pytest.fixture(scope="module")
def eosat_rows():
    if cdr_sim.sim_dir() is None:
        pytest.skip("sim/configs/eosat1 not available")
    return cdr_sim.import_eosat1("s-ref")


def test_config_is_valid_and_kinds_have_rules():
    assert cm.validate_config() == []
    assert set(cm.RULE_OF) == set(cm.KINDS)
    c = cm.cfg()
    services = [s["service"] for s in c["pus_services"]["list"]]
    assert services == sorted(services) and 7 not in services and 10 not in services and 16 not in services
    assert {s["key"] for s in cm.subsystems()} >= {"eps", "aocs", "obdh", "tcs", "ttc", "payload", "prop", "sys"}


def test_owner_seats_follow_ruling_5():
    assert cm.owner_seat("parameters", {"subsystem": "eps"}) == "power_engineer"
    assert cm.owner_seat("parameters", {"subsystem": "aocs"}) == "aocs_engineer"
    assert cm.owner_seat("monitors", {"parameter": "tcs.structure_temp"}) == "thermal_engineer"
    assert cm.owner_seat("hk", {}) == "comms_engineer" and cm.owner_seat("commands", {}) == "comms_engineer"
    assert cm.owner_seat("event_actions", {}) == "systems_engineer"
    assert cm.owner_seat("load_shed", {}) == "power_engineer" and cm.owner_seat("line_states", {}) == "power_engineer"
    assert cm.owner_seat("aocs_modes", {}) == "aocs_engineer" and cm.owner_seat("gonogo", {}) == "mission_analyst"


def test_reconcile_contract():
    want = {"hk": {"r1": {"key": "1", "data": {"sid": 1, "period_s": 8}, "owner_seat": "comms_engineer"}}}
    ops = cm.reconcile(want, [])
    assert len(ops["create"]) == 1 and ops["create"][0]["status"] == "suggested"
    row = {**ops["create"][0], "study_id": "s"}
    # unchanged
    assert cm.reconcile(want, [row])["unchanged"] == 1
    # rule moves a suggested row: silently refreshed
    want2 = copy.deepcopy(want)
    want2["hk"]["r1"]["data"]["period_s"] = 4
    upd = cm.reconcile(want2, [row])["update"]
    assert upd and upd[0][1]["data"]["period_s"] == 4
    # accepted + edited: never overwritten, flagged stale with the proposal
    acc = {**row, "status": "accepted", "edited": True, "data": {"sid": 1, "period_s": 2}}
    upd = cm.reconcile(want2, [acc])["update"]
    assert upd == [("r1", {"review": "stale", "proposed": {"sid": 1, "period_s": 4}})]
    # rejected: skipped; no longer implied: suggested removed, accepted flagged orphan
    assert cm.reconcile(want2, [{**row, "status": "rejected"}])["skipped_rejected"] == 1
    assert cm.reconcile({"hk": {}}, [row])["remove"] == ["r1"]
    assert cm.reconcile({"hk": {}}, [{**row, "status": "accepted"}])["update"] == [("r1", {"review": "orphan", "proposed": None})]


def test_eosat1_import_counts(eosat_rows):
    by = {}
    for r in eosat_rows:
        by[r["kind"]] = by.get(r["kind"], 0) + 1
    assert by["parameters"] == 457 and by["hk"] == 11 and by["commands"] == 220 and by["events"] == 155
    assert by["monitors"] == 41 and by["event_actions"] == 47 and by["limits"] == 49
    assert by["positions"] == 7 and by["gonogo"] == 11 and by["aocs_modes"] == 10 and by["rate_tiers"] == 3
    assert all(r["origin"] == cm.IMPORT_ORIGIN and r["status"] == "accepted" for r in eosat_rows)
    shed = next(r["data"] for r in eosat_rows if r["kind"] == "load_shed")
    assert shed["bus_protection"]["uv_v"]["value"] == 28.4 and shed["order"][0] == "payload" and shed["order"][-1] == "prop"
    nominal = next(r["data"] for r in eosat_rows if r["kind"] == "aocs_modes" and r["data"]["name"] == "NOMINAL")
    assert nominal["gains"] in (None, {"omega_n": 0.04, "zeta": 0.7})
    ea = next(r["data"] for r in eosat_rows if r["kind"] == "event_actions" and r["data"].get("ea_id") == 1001)
    assert ea["action"] == "EPS_POWER_OFF" and ea["action_data"] == [3]     # ruling M1


def test_eosat1_reference_has_no_alarm_and_closes_the_hk_budget(eosat_rows):
    findings = cdr_checks.run_checks(eosat_rows, {"reference": True})
    assert not [f for f in findings if f["severity"] == "alarm"], [f["message"]["en"] for f in findings if f["severity"] == "alarm"]
    bud = cdr_checks.hk_budget(eosat_rows)
    reg = {r["regime"]: r for r in bud["regimes"]}
    assert reg["bootloader"]["tier"] == "SAFE" and reg["bootloader"]["sids"] == [11]
    assert reg["safe"]["sids"] == [1, 11] and all(r["ok"] for r in bud["regimes"])


def test_export_round_trips_the_simulator_files(eosat_rows):
    root = cdr_sim.sim_dir()
    out = cdr_sim.export_sim(eosat_rows)
    src_p = yaml.safe_load((root / "telemetry/parameters.yaml").read_text(encoding="utf-8"))["parameters"]
    got = out["telemetry/parameters.yaml"]["parameters"]
    assert len(got) == 457
    assert {(p["id"], p["name"], p["subsystem"]) for p in got} == {(p["id"], p["name"], p["subsystem"]) for p in src_p}
    src_e = yaml.safe_load((root / "events/event_catalog.yaml").read_text(encoding="utf-8"))["events"]
    assert [(e["id"], e["name"], e["severity"]) for e in out["events/event_catalog.yaml"]["events"]] == \
        [(e["id"], e["name"], e["severity"]) for e in src_e]
    src_m = yaml.safe_load((root / "monitoring/s12_definitions.yaml").read_text(encoding="utf-8"))["s12_definitions"]
    got_m = out["monitoring/s12_definitions.yaml"]["s12_definitions"]
    assert [(m["param_id"], m["low_limit"], m["high_limit"], m.get("validity")) for m in got_m] == \
        [(m["param_id"], m["low_limit"], m["high_limit"], m.get("validity")) for m in src_m]
    src_r = yaml.safe_load((root / "monitoring/s19_rules.yaml").read_text(encoding="utf-8"))["s19_rules"]
    assert [(r["ea_id"], r["trigger"]["id"], r["action_func_id"]) for r in out["monitoring/s19_rules.yaml"]["s19_rules"]] == \
        [(r["ea_id"], r["trigger"]["id"], r["action_func_id"]) for r in src_r]
    assert out["simulation.yaml#eps"]["bus_protection"]["eps_safe_v"] == 27.7
    assert out["subsystems/ttc.yaml"]["default_tier"] == "LOW" and len(out["subsystems/ttc.yaml"]["tm_rate_tiers"]) == 3


def test_checks_catch_the_classic_mistakes(eosat_rows):
    rows = copy.deepcopy(eosat_rows)
    params = [r for r in rows if r["kind"] == "parameters"]
    params[1]["data"]["param_id"] = params[0]["data"]["param_id"]                 # duplicate id
    ea = next(r for r in rows if r["kind"] == "event_actions" and r["data"].get("source") == "s19")
    ea["data"]["action"], ea["data"]["action_func_id"] = None, 250                # no such function
    mon = next(r for r in rows if r["kind"] == "monitors")
    mon["data"]["low"], mon["data"]["high"] = 10, 5                               # empty band
    for t in (r for r in rows if r["kind"] == "rate_tiers"):
        t["data"]["bps"] = 10                                                     # HK cannot fit
    rules = {f["rule"] for f in cdr_checks.run_checks(rows, {"reference": True}) if f["severity"] == "alarm"}
    assert {"TMTC-PARAM", "FDIR-EA", "FDIR-MON", "TMTC-HK-BW"} <= rules


def test_frame_converter_flips_products_of_inertia():
    from spacecdf_server.services.stack_builder import design_to_stack_tensor, envelope
    env = envelope("6U")
    i_design = [[0.18, 0.002, -0.003], [0.002, 0.15, 0.001], [-0.003, 0.001, 0.06]]
    i_stack = design_to_stack_tensor(i_design, env)
    assert [i_stack[k][k] for k in range(3)] == [0.18, 0.15, 0.06]
    assert i_stack[0][1] == -0.002 and i_stack[0][2] == 0.003 and i_stack[1][2] == 0.001
    assert design_to_stack_tensor(i_stack, env) == i_design                       # an involution here


def test_reference_template_flies_the_eosat1_orbit():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    tpl = yaml.safe_load((root / "configs/templates/6u_eo_cubesat.yaml").read_text(encoding="utf-8"))
    orbit = tpl["requirements"]["orbit"]
    assert orbit["altitude_km"] == 513.0 and orbit["inclination_deg"] == 97.39 and orbit["ltan"] == "10:00"
    assert "zenith" in tpl["notes"] and "nadir" in tpl["notes"]
    ref = yaml.safe_load((root / "configs/validation/eosat_6u_reference.yaml").read_text(encoding="utf-8"))
    assert "513 km" in ref["description"] and "450" not in ref["description"]
    if cdr_sim.sim_dir() is not None:
        sim_orbit = yaml.safe_load((cdr_sim.sim_dir() / "orbit.yaml").read_text(encoding="utf-8"))
        assert sim_orbit["altitude_km"] == orbit["altitude_km"] and sim_orbit["inclination_deg"] == orbit["inclination_deg"]
