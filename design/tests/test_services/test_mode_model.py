"""Mode model, budgets per mode and the phase-1 design rules (Nov 2026).

Pins: F1 CDS envelope (6U/12U 366 mm, body frame), F2 one margin ladder, F3 one maturity
source, F4 KB copy + staleness (rule 13), F10 monitor-based detection, MO-01 per-mode unit
proposals, MO-02 energy per orbit, EB-03 data chain, EB-05 dissipation, MO-05 machine checks,
rules 7 (heater), 8 (FDIR stubs) and 9 (risks), and equipment → budgets.
"""
from __future__ import annotations

import pytest

from spacecdf_server.services import mode_model as mm
from spacecdf_server.services import rule_config as rc
from spacecdf_server.services.cds_checks import body_frame_cog_limits_cm, body_frame_envelope_mm
from spacecdf_server.services.consistency_engine import run_consistency_check
from spacecdf_server.services.fmeca_library import build_skeleton
from spacecdf_server.services.kb_copy import apply_to_element, find_kb_part, kb_element_fields, kb_hash, staleness
from spacecdf_server.services.margin_policy import maturity, system_margin_percent
from spacecdf_server.services.mode_rules import (fdir_proposals, heater_proposals, monitored_element_ids,
                                                 risk_proposals, validate_action)


def _el(eid, name, etype="component", parent="sys", **kw):
    return {"id": eid, "name": name, "element_type": etype, "parent_id": parent, **kw}


@pytest.fixture(autouse=True)
def _fresh_configs():
    rc.reload()
    yield
    rc.reload()


@pytest.fixture()
def sat():
    return [
        {"id": "m", "name": "Mission", "element_type": "mission"},
        _el("sys", "Spacecraft", "system", parent="m"),
        _el("obc", "OBC", kb_component_id="obc-isis-iobc", mass_kg=0.06, power_avg_w=0.8, trl=9),
        _el("tx", "S-band transmitter", kb_component_id="txrx-endurosat-s-band-tx", mass_kg=0.14, power_avg_w=8.0, trl=9),
        _el("cam", "Camera payload", mass_kg=1.0, power_avg_w=5.0, power_peak_w=6.0, subsystem_domain="payload",
            performance={"data_rate_bps": 50_000_000}),
        _el("bat", "Battery pack", mass_kg=0.3, subsystem_domain="power", trl=9, heritage_json=["x"]),
    ]


# ------------------------------------------------------------------ F1: CDS envelope

def test_cds_envelope_6u_12u_length_and_body_frame():
    cds = rc.load("cds_rules")
    assert cds["envelope_mm"]["values"]["6U"] == [226.3, 100.0, 366.0]
    assert cds["envelope_mm"]["values"]["12U"] == [226.3, 226.3, 366.0]
    assert cds["envelope_mm"]["values"]["3U"][2] == 340.5
    # body frame = simulator geometry.yaml (bus.size_m [0.100, 0.226, 0.366])
    assert body_frame_envelope_mm("6U") == [100.0, 226.3, 366.0]
    assert body_frame_cog_limits_cm("6U") == [2.0, 4.5, 7.0]
    assert body_frame_envelope_mm("12U") == [226.3, 226.3, 366.0]
    from spacecdf_common.models.cubesat_standards import CDS_SPECS
    assert CDS_SPECS["6U"]["dimensions_mm"][2] == 366.0 and CDS_SPECS["12U"]["rail_contact_length_mm"] == 366.0


# ------------------------------------------------------------------ F2 / F3: margins

def test_one_margin_ladder_in_consistency_engine():
    params = {"systems.mass_margin_percent": 17.0, "systems.power_margin_percent": 17.0}
    # MDR asks 20 % (textbook Table 8.3) -> both below; PDR asks 15 % -> both pass
    mdr = run_consistency_check(design_params=params, margin_gate="mdr")
    pdr = run_consistency_check(design_params=params, margin_gate="pdr")
    assert {i.id for i in mdr.issues if i.category == "budgets"} == {"CON-BDG-MASS", "CON-BDG-POWE"}
    assert not [i for i in pdr.issues if i.category == "budgets"]
    assert "20" in next(i.title for i in mdr.issues if i.category == "budgets")
    # without a gate the phase picks the ladder step (phase_0 -> MDR 20 %), not the old 30 %
    p0 = run_consistency_check(design_params={"systems.mass_margin_percent": 21.0}, phase_id="phase_0")
    assert not [i for i in p0.issues if i.id == "CON-BDG-MASS"]
    assert system_margin_percent("mdr") == 20 and system_margin_percent("cdr", "power") == 10


def test_one_maturity_source():
    # KB part TRL 9 with heritage -> A 5 %; TRL 7 -> C 10 %; no part, no TRL -> D 20 %
    assert maturity({"kb_component_id": "obc-isis-iobc"})["category"] == "A"
    assert maturity({"trl": 7})["percent"] == 10.0
    assert maturity({"name": "custom"})["category"] == "D"
    assert maturity({"trl": 4, "performance": {"maturity_category": "B"}})["category"] == "B"


def test_equipment_selection_uses_policy_margin():
    from spacecdf_common.agents.base import DesignState
    from spacecdf_server.services.equipment import apply_equipment_selection
    part = find_kb_part("obc-isis-iobc")
    st = DesignState()
    changed = apply_equipment_selection(part, "obc", "obcs", st, "obdh")
    mass = st.get_param("obc.obcs_mass_kg")
    assert mass.margin_percent == 5.0 and "obc.obcs_power_w" in changed
    assert st.get_param("obc.obcs_power_w").value == pytest.approx(0.8)


# ------------------------------------------------------------------ F4 / rule 13: KB copy and staleness

def test_kb_copy_carries_physical_facts():
    part = find_kb_part("obc-gom-nanomind-a3200")
    f = kb_element_fields(part)
    # A3200 values as corrected from the 2025 datasheet (C2O KB research, Nov 2026)
    assert f["dimensions_mm"] == [65.0, 40.0, 7.1]
    spec = f["kb_spec"]
    assert spec["form_factor"] == "GomSpace 65x40 module" and "CAN" in spec["interfaces"]
    assert spec["operating_temp_c"] == [-30, 85] and spec["kb_hash"] == kb_hash(part) and spec["category"] == "obc"
    assert f["heritage_json"] and f["mass_kg"] == 0.024
    el = {"id": "e1", "name": "My OBC", "kb_component_id": part["id"], "mass_kg": 0.05}
    apply_to_element(el, part)
    assert el["mass_kg"] == 0.05 and el["kb_spec"]["form_factor"] == "GomSpace 65x40 module"   # explicit value kept


def test_kb_staleness_detects_changed_part():
    part = dict(find_kb_part("obc-isis-iobc"))
    el = {"id": "e1", "name": "OBC", "kb_component_id": part["id"]}
    apply_to_element(el, part)
    assert staleness([el], lambda _k: part) == []
    changed = {**part, "mass_kg": 0.09}
    rows = staleness([el], lambda _k: changed)
    assert rows[0]["reason"] == "kb_changed" and "mass_kg" in rows[0]["changed"]
    assert staleness([el], lambda _k: None)[0]["reason"] == "kb_part_missing"
    assert staleness([{"id": "x", "kb_component_id": part["id"]}], lambda _k: part)[0]["reason"] == "never_copied"


# ------------------------------------------------------------------ MO-01: per-mode unit proposals

def test_propose_member_states_and_sources(sat):
    by = {e["id"]: e for e in sat}
    tx_dl = mm.propose_member(by["tx"], "downlink")
    tx_nom = mm.propose_member(by["tx"], "nominal")
    assert tx_dl["power_state"] == "peak" and tx_dl["power_w_in_mode"] == pytest.approx(8.0 * 1.6)
    assert tx_nom["power_state"] == "standby" and tx_nom["power_w_in_mode"] == pytest.approx(2.0)
    assert tx_dl["c2o_default"] and tx_dl["source_ref"].startswith("C2O default")
    cam_img = mm.propose_member(by["cam"], "imaging")
    assert cam_img["power_w_in_mode"] == 6.0 and cam_img["data_rate_bps"] == 50_000_000
    assert mm.propose_member(by["cam"], "safe")["power_state"] == "off"
    # KB per-mode power wins and is cited as such
    el = {**by["obc"], "kb_spec": {"power_modes_w": {"nominal": 0.7, "standby": 0.2}}}
    p = mm.propose_member(el, "nominal")
    assert p["power_w_in_mode"] == 0.7 and p["source_ref"] == "KB power_modes_w" and not p["c2o_default"]
    # the hash follows the inputs (staleness)
    assert mm.propose_member({**by["obc"], "power_avg_w": 1.0}, "nominal")["inputs_hash"] != \
        mm.propose_member(by["obc"], "nominal")["inputs_hash"]


def _modes(sat):
    """Nominal (background), imaging (sunlit only), downlink, safe — with members."""
    by = {e["id"]: e for e in sat}

    def members(kind):
        rows = []
        for eid in ("obc", "tx", "cam"):
            p = mm.propose_member(by[eid], kind)
            rows.append({"element_id": eid, "power_w": p["power_w_in_mode"], "duty": 1.0,
                         "data_rate_bps": p["data_rate_bps"], "state": p["power_state"]})
        return rows
    return [
        {"id": "nom", "name": "Nominal", "kind": "nominal", "pointing": "nadir", "orbit_fraction": 0.75,
         "members": members("nominal"), "data_rate_bps": 0.0},
        {"id": "img", "name": "Imaging", "kind": "imaging", "pointing": "target", "sunlit_only": True,
         "orbit_fraction": 0.15, "members": members("imaging"), "data_rate_bps": 50_000_000},
        {"id": "dl", "name": "Downlink", "kind": "downlink", "pointing": "station", "orbit_fraction": 0.10,
         "members": members("downlink"), "data_rate_bps": 0.0},
        {"id": "safe", "name": "Safe", "kind": "safe", "pointing": "sun", "members": members("safe"), "data_rate_bps": 0.0},
    ]


# ------------------------------------------------------------------ MO-02: energy per orbit

def test_energy_balance_per_mode_and_orbit(sat):
    modes = _modes(sat)
    res = mm.energy_balance(modes, sat, period_s=5700, eclipse_fraction=0.35, sa_power_eol_w=40.0,
                            battery_wh=40.0, system_margin_percent=20)
    rows = {r["mode_id"]: r for r in res["modes"]}
    nom = rows["nom"]
    # nominal: OBC 0.8 (A 5 %) + TX standby 2.0 (A 5 %) + camera standby 1.25 (D 20 %)
    cbe = 0.8 + 2.0 + 1.25
    mat = (0.8 + 2.0) * 1.05 + 1.25 * 1.2
    assert nom["power_cbe_w"] == pytest.approx(cbe, abs=1e-3)
    assert nom["power_total_w"] == pytest.approx(mat * 1.2, abs=1e-3)
    t_sun, t_ecl = 0.65 * 5700, 0.35 * 5700
    gen = 40.0 * 0.65 * t_sun / 3600
    need = mat * 1.2 * (t_sun + t_ecl / 0.9) / 3600
    assert nom["balance_wh"] == pytest.approx(gen - need, abs=1e-2)
    assert nom["dod_percent"] == pytest.approx(100 * mat * 1.2 * t_ecl / 3600 / 40.0, abs=1e-2)
    assert nom["status"] == "pass" and rows["safe"]["array_factor"] == 1.0
    ops = res["operational_orbit"]
    assert ops and {m["mode_id"] for m in ops["modes"]} == {"nom", "img", "dl"}
    duty = {d["mode_id"]: d for d in res["sustainable_duty"]}
    assert 0 < duty["img"]["sustainable_fraction"] <= 0.65 + 1e-9    # imaging only in sunlight
    # no array power -> not evaluated, with a warning
    none = mm.energy_balance(modes, sat, period_s=5700, eclipse_fraction=0.35, sa_power_eol_w=None,
                             battery_wh=None, system_margin_percent=20)
    assert none["warnings"] and none["modes"][0]["status"] == "not_evaluated"


# ------------------------------------------------------------------ EB-03: data chain

def test_data_chain_generation_storage_downlink(sat):
    modes = _modes(sat)
    st = [{"name": "A", "contact_min_per_day": 40.0, "margin_db": 6.0},
          {"name": "B", "contact_min_per_day": 30.0, "margin_db": -1.0},
          {"name": "C", "contact_min_per_day": 20.0, "margin_db": 2.0}]
    res = mm.data_chain(modes, period_s=5700, link_rate_bps=2e6, stations=st, storage_gb=8.0, storage_margin_percent=50)
    hk = 2000.0
    bits_orbit = ((0 + hk) * 0.75 + (50e6 + hk) * 0.15 + (0 + hk) * 0.10) * 5700
    gen = bits_orbit * 86400 / 5700 / 8e9
    assert res["generated_gb_per_day"] == pytest.approx(gen, rel=1e-3)
    assert res["downlink"]["contact_min_per_day"] == 60.0              # station B does not close
    cap = 60 * 60 * 2e6 * 0.85 / 8e9
    assert res["downlink"]["capacity_gb_per_day"] == pytest.approx(cap, rel=1e-3)
    checks = {c["id"]: c for c in res["checks"]}
    assert checks["DC-DOWNLINK"]["status"] == "fail"                  # 50 Mbit/s imaging swamps 2 Mbit/s
    assert checks["DC-STORAGE"]["status"] == "fail" and checks["DC-LINK-MARGIN"]["status"] == "warn"
    assert res["days_to_full"] == pytest.approx(8.0 / (gen - cap), rel=1e-2)
    small = mm.data_chain(modes[:1], period_s=5700, link_rate_bps=2e6, stations=st, storage_gb=8.0,
                          storage_margin_percent=50)
    assert {c["id"]: c["status"] for c in small["checks"]}["DC-DOWNLINK"] == "pass"


# ------------------------------------------------------------------ EB-05: dissipation

def test_dissipation_removes_rf_out_and_feeds_cases(sat):
    modes = _modes(sat)
    cases = mm.dissipation_cases(sat, modes)
    # transmitter at peak 12.8 W radiates its KB tx_power_w (2 W) as RF
    assert cases["tx"]["by_mode"]["dl"] == pytest.approx(12.8 - 2.0)
    assert cases["tx"]["hot_w"] == pytest.approx(10.8)
    assert cases["cam"]["cold_w"] == 0.0 and cases["cam"]["hot_w"] == 6.0   # cold from the safe mode
    assert mm.dissipation_w(sat[2], {"power_w": 1.0, "dissipation_w": 0.4}) == 0.4


# ------------------------------------------------------------------ MO-05: mode machine

def test_validate_machine_findings():
    modes = [{"id": "a", "name": "LEOP", "performance": {"mode_kind": "leop", "initial": True}},
             {"id": "b", "name": "Nominal", "performance": {"mode_kind": "nominal"}},
             {"id": "c", "name": "Orphan", "performance": {"mode_kind": "custom"}}]
    trans = [{"id": "t1", "from_mode_id": "a", "to_mode_id": "b", "trigger": "ground_tc"},
             {"id": "t2", "from_mode_id": "b", "to_mode_id": "a", "trigger": "autonomous", "guard": {"text": "low"}},
             {"id": "t3", "from_mode_id": "b", "to_mode_id": "zz", "trigger": "timer"}]
    ids = {(f["id"], f.get("mode_id") or f.get("transition_id")) for f in mm.validate_machine(modes, trans)}
    assert ("MM-UNREACHABLE", "c") in ids and ("MM-NO-EXIT", "c") in ids
    assert ("MM-AUTO-NO-GUARD", "t2") in ids and ("MM-DANGLING", "t3") in ids
    assert any(f[0] == "MM-NO-SAFE" for f in ids)


def test_template_config_is_complete():
    c = mm.cfg()
    kinds = {m["kind"] for m in c["template"]["modes"]}
    assert {"leop", "commissioning", "nominal", "imaging", "downlink", "safe", "survival", "disposal"} == kinds
    assert sum(m["orbit_fraction"] for m in c["template"]["modes"] if m["phase"] == "nominal") == pytest.approx(1.0)
    assert mm.validate_config() == []


# ------------------------------------------------------------------ rules 8 / 9 / 7 and F10

def _fmeca(sat):
    return build_skeleton(sat, [], monitored=set())["rows"]


def test_fdir_stubs_and_validation(sat):
    rows = _fmeca(sat)
    props = fdir_proposals(rows, sat, safe_mode_id="safe")
    mons = [p for p in props if p["kind"] == "monitor"]
    acts = [p for p in props if p["kind"] == "action"]
    assert mons and len(mons) == len(acts)
    assert all(int(next(r for r in rows if r["id"] == m["payload"]["fmeca_row_id"])["severity"]) >= 3 for m in mons)
    # the OBC library action is SWITCH_TO_REDUNDANT; a single OBC gets a valid fallback instead
    obc_act = next(a for a in acts if a["element_id"] == "obc")
    assert obc_act["payload"]["function_id"] != "SWITCH_TO_REDUNDANT"
    assert obc_act["payload"]["replaced"]["function_id"] == "SWITCH_TO_REDUNDANT"
    assert obc_act["payload"]["problems"] == []
    assert validate_action("POWER_OFF_UNIT", sat[2])[0]["code"] == "FD-02-SELF-OFF"
    assert validate_action("NOPE", sat[2])[0]["code"] == "FD-02-UNKNOWN-FUNCTION"
    assert not validate_action("SWITCH_TO_REDUNDANT", {**sat[2], "quantity": 2})
    obc_mon = next(m for m in mons if m["element_id"] == "obc")
    assert obc_mon["standard_ref"].startswith("ECSS-E-ST-70-41C")


def test_detection_credit_comes_from_monitors(sat):
    links = [{"type": "data", "from_element_id": "obc", "to_element_id": "tx"}]
    legacy = build_skeleton(sat, links)
    assert legacy["rows"][0]["detection_basis"] == "data_link_heuristic"
    no_mon = {r["id"]: r for r in build_skeleton(sat, links, monitored=set())["rows"]}
    with_mon = {r["id"]: r for r in build_skeleton(sat, links, monitored={"tx"})["rows"]}
    tx_row = next(k for k in no_mon if k.endswith(":tx"))
    assert with_mon[tx_row]["detection"] == no_mon[tx_row]["detection"] - 1
    assert with_mon[tx_row]["adjustments"]["monitored"]
    accepted = [{"kind": "monitor", "status": "accepted", "element_id": "tx"},
                {"kind": "monitor", "status": "suggested", "element_id": "obc"}]
    assert monitored_element_ids(accepted) == {"tx"}


def test_risk_proposals(sat):
    rows = _fmeca(sat)
    reqs = [{"id": "R1", "text": "The mass shall be below 5 kg.", "verification_method": "A"},
            {"id": "R2", "text": "x", "verification_method": "T"},
            {"id": "R3", "text": "y", "verification_method": "R", "status": "retired"}]
    props = risk_proposals(rows, reqs)
    sp = [p for p in props if p["rule_id"] == "FD-03"]
    ao = [p for p in props if p["rule_id"] == "RV-04"]
    assert sp and all(p["payload"]["source"].startswith("rule:FD-03:") for p in sp)
    assert [p["target_key"] for p in ao] == ["risk:req:R1"]
    assert ao[0]["standard_ref"].startswith("ECSS-E-ST-10-02C")
    assert 1 <= sp[0]["payload"]["likelihood"] <= 5


def test_heater_proposal_from_cold_case(sat):
    nodes = [{"element_id": "bat", "name": "Battery pack", "kind": "component", "t_cold_c": -8.0, "allow_min_c": 0.0,
              "area_m2": 0.01},
             {"element_id": "obc", "name": "OBC", "kind": "component", "t_cold_c": 5.0, "allow_min_c": -20.0, "area_m2": 0.01}]
    cond = [{"a": "chassis", "b": "bat", "w_per_k": 0.5}]
    props = heater_proposals(nodes, cond, sat, emissivity=0.85)
    assert len(props) == 1 and props[0]["element_id"] == "bat"
    p = props[0]["payload"]
    assert p["on_c"] == 5.0 and p["off_c"] == 10.0
    assert p["power_w"] >= p["raw_w"] * 1.25 and p["power_w"] % 0.5 == 0
    assert p["line"]["switchable"] and p["line"]["lcl_limit_a"] == pytest.approx(p["line"]["current_a"] * 1.5, rel=1e-2)
    # switched off in the cold case: only the survival limit (op min − 15 K) applies -> -8 °C is fine
    assert heater_proposals(nodes, cond, sat, emissivity=0.85, off_in_cold={"bat"}) == []
    nodes[0]["t_cold_c"] = -20.0
    off = heater_proposals(nodes, cond, sat, emissivity=0.85, off_in_cold={"bat"})
    assert off and off[0]["payload"]["t_min_c"] == -15.0 and off[0]["payload"]["limit"].startswith("C2O default")


# ------------------------------------------------------------------ equipment → budgets

def test_equipment_budgets(sat):
    modes = _modes(sat)
    res = mm.equipment_budgets(sat, modes, gate="pdr")
    rows = {r["element_id"]: r for r in res["rows"]}
    assert rows["obc"]["maturity_category"] == "A" and rows["cam"]["maturity_category"] == "D"
    assert rows["cam"]["power_by_mode_w"]["img"] == 6.0 and rows["cam"]["data_by_mode_bps"]["img"] == 50_000_000
    assert rows["tx"]["dissipation_by_mode_w"]["dl"] == pytest.approx(10.8)
    t = res["totals"]
    assert t["mass_total_kg"] == pytest.approx(t["mass_with_maturity_kg"] * 1.15, abs=1e-3)
    assert res["system_margin"]["gate"] == "pdr" and res["system_margin"]["power_percent"] == 15
    assert res["system_margin"]["convention"]["id"] == "percent_of_nominal"
    assert t["cost_keur"] == pytest.approx(15 + 28)
