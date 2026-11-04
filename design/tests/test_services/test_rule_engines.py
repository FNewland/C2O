"""Deterministic rule engines that replace AI (docs/RULES_AND_AI.md).

Pins: the rule configs validate; margin policy numbers (ESA margin philosophy 1.3);
CDS rev 14.1 checks; EARS / INCOSE requirement checks (EN and FR); ECSS-E-ST-10-02C
verification defaults; FMECA skeleton; gate checks; AI output validation; and that
every result separates a cited standard from a C2O default.
"""
from __future__ import annotations

import pytest

from spacecdf_server.services import rule_config as rc
from spacecdf_server.services.ai_output_checks import check_ai_output, extract_statements
from spacecdf_server.services.cds_checks import evaluate_cds
from spacecdf_server.services.fmeca_library import build_skeleton
from spacecdf_server.services.gate_checks import computed_for_criterion, evaluate_gate_checks
from spacecdf_server.services.margin_policy import evaluate_margins
from spacecdf_server.services.requirement_quality import check_requirements, check_text
from spacecdf_server.services.rule_inputs import form_factor, leaves_with
from spacecdf_server.services.verification_defaults import suggest, suggest_all


def _el(eid, name, etype="component", parent="sys", **kw):
    return {"id": eid, "name": name, "element_type": etype, "parent_id": parent, **kw}


@pytest.fixture()
def cubesat():
    """A 3U CubeSat: structure (KB), EPS, battery, OBC, UHF radio, deployable antenna, camera."""
    return [
        {"id": "m", "name": "Mission", "element_type": "mission"},
        _el("sys", "Spacecraft", "system", parent="m"),
        _el("eps", "EPS", "subsystem", subsystem_domain="power"),
        _el("str", "Structure", kb_component_id="struct-isis-3u", mass_kg=0.6, position_json=[0.05, 0.05, 0.17]),
        _el("bat", "Battery pack", parent="eps", mass_kg=0.3, power_avg_w=0.1, position_json=[0.05, 0.05, 0.10],
            trl=9, heritage_json=["x"]),
        _el("obc", "OBC", mass_kg=0.1, power_avg_w=0.5, position_json=[0.05, 0.05, 0.15], trl=7),
        _el("radio", "UHF transceiver", mass_kg=0.1, power_avg_w=1.5, position_json=[0.05, 0.05, 0.20]),
        _el("ant", "Antenna", kb_component_id="ant-isis-uhf-deploy", mass_kg=0.1, position_json=[0.05, 0.05, 0.33]),
        _el("cam", "Camera payload", mass_kg=1.0, power_avg_w=3.0, position_json=[0.05, 0.05, 0.25]),
        {"id": "gs", "name": "Ground station", "element_type": "system", "segment": "ground", "mass_kg": 300.0},
    ]


# ------------------------------------------------------------------ configs

def test_rule_configs_validate():
    rc.reload()
    assert rc.validate_all() == {}


def test_invalid_config_is_reported(tmp_path, monkeypatch):
    src = rc.configs_dir()
    for name in rc.RULE_FILES:
        (tmp_path / f"{name}.yaml").write_text((src / f"{name}.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    bad = (tmp_path / "margin_policy.yaml").read_text(encoding="utf-8").replace(
        "system_margin_percent: {value: 20, source: esa_margin_1_3", "system_margin_percent: {value: 20, source: nowhere")
    (tmp_path / "margin_policy.yaml").write_text(bad, encoding="utf-8")
    monkeypatch.setenv("SPACECDF_RULES_DIR", str(tmp_path))
    rc.reload()
    try:
        errs = rc.validate_all()
        assert "margin_policy" in errs and any("unknown source 'nowhere'" in e for e in errs["margin_policy"])
        with pytest.raises(rc.RuleConfigError):
            rc.load("margin_policy")
    finally:
        monkeypatch.delenv("SPACECDF_RULES_DIR")
        rc.reload()


def test_standard_ref_distinguishes_default_from_citation():
    cfg = rc.load("margin_policy")
    cited = rc.ref_of(cfg, cfg["mass"]["harness_percent"])
    assert cited["standard_ref"] == "ESA margin philosophy (SCI) 1.3 R-M1-7" and not cited["c2o_default"]
    default = rc.ref_of(cfg, cfg["category_from_trl"])
    assert default["standard_ref"].startswith("C2O default") and default["c2o_default"]


# ------------------------------------------------------------------ margins

def test_leaves_avoid_double_counting(cubesat):
    cubesat.append(_el("eps-est", "EPS estimate", "subsystem", parent="sys", mass_kg=5.0))
    cubesat[2]["mass_kg"] = 2.0          # EPS subsystem estimate, overridden by its battery
    names = {e["id"] for e in leaves_with(cubesat, "mass_kg")}
    assert "eps" not in names and "bat" in names and "eps-est" in names and "gs" not in names


def test_margin_policy_numbers(cubesat):
    r = evaluate_margins(cubesat, {"power.sa_power_eol_w": 8.0}, mass_limit_kg=6.0)
    m = r["mass"]
    cats = {u["element_id"]: u["category"] for u in m["units"]}
    assert cats["bat"] == "A"           # TRL 9 with heritage
    assert cats["obc"] == "C"           # TRL 7, no heritage
    assert cats["cam"] == "D"           # no KB part, no TRL -> new design
    assert m["cbe_kg"] == pytest.approx(2.2)
    maturity = sum(u["with_margin"] for u in m["units"])
    assert m["harness_kg"] == pytest.approx(maturity * 0.05, rel=1e-3)
    assert m["total_dry_kg"] == pytest.approx(maturity * 1.05 * 1.20, rel=1e-3)
    ids = {c["id"]: c for c in r["checks"]}
    assert ids["MP-MASS-01"]["status"] == "pass"
    assert ids["MP-MASS-02"]["status"] == "warn"        # camera and radio have no KB part
    assert ids["MP-PWR-01"]["status"] == "pass"
    assert r["power"]["total_w"] == pytest.approx(sum(u["with_margin"] for u in r["power"]["units"]) * 1.2, rel=1e-3)


def test_delta_v_margins():
    els = [_el("t", "Thruster", mass_kg=0.5)]
    r = evaluate_margins(els, {"orbit.delta_v_insertion_ms": 100, "orbit.delta_v_sk_ms": 10,
                               "propulsion.delta_v_total_ms": 120})
    assert r["delta_v"]["total_with_margin_ms"] == pytest.approx(105 + 20)
    dv = next(c for c in r["checks"] if c["id"] == "MP-DV-01")
    assert dv["status"] == "fail" and "R-DV-11" in dv["standard_ref"]


def test_ram_rule_from_kb_obc():
    els = [_el("o", "OBC", kb_component_id="obc-isis-iobc", mass_kg=0.1, performance={"ram_used_mb": 40})]
    r = evaluate_margins(els, {})            # capacity 64 MB comes from the KB part
    ram = next(c for c in r["checks"] if c["id"] == "MP-DH-01")
    assert ram["status"] == "fail" and ram["limit"] == 50


# ------------------------------------------------------------------ CDS

def test_form_factor_from_kb_structure(cubesat):
    assert form_factor(cubesat, {}) == "3U"
    assert form_factor([], {"structure.form_factor_u": 6}) == "6U"
    assert form_factor([], {}) is None


def test_cds_checks(cubesat):
    r = evaluate_cds(cubesat, [], {}, "3U")
    ids = {c["id"]: c for c in r["checks"]}
    assert ids["CDS-MASS"]["status"] == "pass" and ids["CDS-MASS"]["limit"] == 6.0
    assert "CDS rev 14.1 2.2.10" in ids["CDS-MASS"]["standard_ref"]
    assert ids["CDS-COG"]["status"] in ("pass", "fail")
    assert ids["CDS-RF-INH"]["status"] == "warn"          # transmitter, nothing declared
    assert ids["CDS-DEP-INH"]["status"] == "warn"         # KB antenna is burn-wire deployable
    assert ids["CDS-PROP-INH"]["status"] == "pass" and ids["CDS-PROP-INH"]["applicable"] is False
    assert r["evidence"]["transmitters"] == ["radio"] and r["evidence"]["deployables"] == ["ant"]


def test_cds_inhibits_counted_from_links_and_declarations(cubesat):
    links = [{"id": f"i{k}", "type": "electrical_signal", "subtype": "rf_inhibit",
              "from_element_id": "eps", "to_element_id": "radio"} for k in range(2)]
    links.append({"id": "rej", "type": "electrical_signal", "subtype": "rf_inhibit", "status": "rejected"})
    cubesat[3]["performance"] = {"cds": {"rbf": True, "deployment_switches": 2, "rf_delay_min": 30,
                                         "tml_percent": 1.4}}
    r = evaluate_cds(cubesat, links, {}, "3U")
    ids = {c["id"]: c for c in r["checks"]}
    assert ids["CDS-RF-INH"]["status"] == "fail" and ids["CDS-RF-INH"]["value"] == 2   # rejected one ignored
    assert ids["CDS-RBF"]["status"] == "pass" and ids["CDS-SW"]["status"] == "pass"
    assert ids["CDS-RF-T"]["status"] == "fail"           # 30 < 45 min (2.4.5)
    assert ids["CDS-TML"]["status"] == "fail"


def test_cds_reads_the_link_proposer_shape(cubesat):
    """interface_rules.yaml proposes ONE 'inhibit' link carrying inhibit_count and delay_min,
    at subsystem level (power -> TT&C subsystem) or unit level (EPS -> transceiver)."""
    cubesat.append(_el("ttc", "TT&C", "subsystem", subsystem_domain="ttc"))
    cubesat[6]["parent_id"] = "ttc"                       # the transceiver sits in the TT&C subsystem
    links = [{"id": "l1", "type": "electrical_signal", "subtype": "inhibit", "status": "suggested",
              "from_element_id": "eps", "to_element_id": "ttc", "properties": {"inhibit_count": 3, "delay_min": 45}},
             {"id": "l2", "type": "electrical_signal", "subtype": "release", "status": "accepted",
              "from_element_id": "obc", "to_element_id": "ant", "properties": {"inhibit_count": 3, "delay_min": 30}},
             {"id": "l3", "type": "electrical_signal", "subtype": "rbf", "from_element_id": "str", "to_element_id": "eps"}]
    ids = {c["id"]: c for c in evaluate_cds(cubesat, links, {}, "3U")["checks"]}
    assert ids["CDS-RF-INH"]["status"] == "pass" and ids["CDS-RF-INH"]["value"] == 3
    assert ids["CDS-RF-T"]["status"] == "pass" and ids["CDS-DEP-T"]["status"] == "pass"
    assert ids["CDS-DEP-INH"]["status"] == "pass" and ids["CDS-RBF"]["status"] == "pass"
    assert ids["CDS-PROP-INH"]["applicable"] is False       # an inhibit to TT&C is not a propulsion inhibit


def test_cds_cog_out_of_box():
    els = [_el("a", "Box A", mass_kg=1.0, position_json=[0.05, 0.05, 0.02]),
           _el("b", "Box B", mass_kg=1.0, position_json=[0.05, 0.05, 0.05])]
    r = evaluate_cds(els, [], {}, "3U")
    cog = next(c for c in r["checks"] if c["id"] == "CDS-COG")
    assert cog["status"] == "fail"        # z offset ~13.5 cm > 7 cm


def test_cds_not_applicable_without_form_factor(cubesat):
    r = evaluate_cds(cubesat, [], {}, None)
    assert r["applicable"] is False and r["checks"] == []


# ------------------------------------------------------------------ requirement quality

@pytest.mark.parametrize("text, pattern, status", [
    ("The EPS shall provide at least 12 W orbit-average power at EOL.", "ubiquitous", "pass"),
    ("When the spacecraft separates, the OBC shall wait at least 45 min before transmitting.", "event", "pass"),
    ("While in safe mode, the ADCS shall keep the sun angle below 30 deg.", "state", "pass"),
    ("If the battery voltage drops below 6.2 V, then the EPS shall shed the payload load.", "unwanted", "pass"),
    ("Where a propulsion module is fitted, the OBC shall provide 3 independent inhibits.", "optional", "pass"),
    ("Le satellite doit fournir au moins 10 W en moyenne orbitale.", "ubiquitous", "pass"),
    ("Si la tension descend sous 6,2 V, alors l'EPS doit délester la charge utile.", "unwanted", "pass"),
])
def test_ears_patterns(text, pattern, status):
    r = check_text(text)
    assert r["ears"]["id"] == pattern
    assert r["status"] == status, r["findings"]


def test_incose_subset_findings():
    r = check_text("The system shall be fast and reliable where possible, and it shall store TBD data.")
    ids = {f["id"] for f in r["findings"]}
    assert {"R18-SINGLE", "R7-VAGUE", "R8-ESCAPE", "R24-PRONOUN", "C2O-TBD"} <= ids
    assert r["status"] == "fail"
    tbd = next(f for f in r["findings"] if f["id"] == "C2O-TBD")
    assert tbd["c2o_default"] and tbd["standard_ref"].startswith("C2O default")
    assert next(f for f in r["findings"] if f["id"] == "R7-VAGUE")["standard_ref"] == "INCOSE GtWR"
    assert check_text("Downlink 2 GB per day")["findings"][0]["id"] == "R-MODAL"
    units = check_text("The camera shall have a resolution of at least 5.")
    assert any(f["id"] == "R6-UNITS" for f in units["findings"])
    fr = check_text("Le système doit être rapide et/ou fiable si possible.")
    assert {"R7-VAGUE", "R19-COMBINATOR", "R8-ESCAPE"} <= {f["id"] for f in fr["findings"]}
    assert fr["findings"][0]["message"]["fr"]


def test_check_requirements_summary():
    out = check_requirements([{"id": "r1", "text": "The OBC shall boot within 10 s."},
                              {"id": "r2", "text": "The OBC shall be robust."}])
    assert out["summary"]["total"] == 2 and out["summary"]["fail"] == 1
    assert out["summary"]["by_rule"]["R7-VAGUE"] == 1


# ------------------------------------------------------------------ verification defaults

def test_verification_defaults():
    budget = suggest({"text": "The dry mass shall not exceed 4 kg.", "threshold_param_path": "mass.dry_mass_kg"})
    assert budget["default_method"] == "A" and budget["needs_risk_assessment"]
    assert budget["mapping_c2o_default"] and "ECSS-E-ST-10-02C" in budget["method_standard_ref"]
    assert suggest({"text": "The spacecraft shall comply with ITU Radio Regulations."})["default_method"] == "R"
    assert suggest({"text": "No part shall protrude more than 6.5 mm from the rail plane."})["default_method"] == "I"
    perf = suggest({"text": "The spacecraft shall downlink 2 GB per day.", "verification_method": "D"})
    assert perf["default_method"] == "T" and not perf["differs"]        # D counts as Test
    # "attitude" must not match the ITU keyword
    assert suggest({"text": "The attitude shall be known within 0.1 deg."})["type"] != "documentation"
    s = suggest_all([{"id": "a", "text": "The OBC shall boot within 10 s."}, {"id": "b", "text": "x", "status": "retired"}])
    assert s["summary"]["total"] == 1 and s["summary"]["missing_method"] == 1


# ------------------------------------------------------------------ FMECA

def test_fmeca_skeleton(cubesat):
    links = [{"type": "data", "from_element_id": "obc", "to_element_id": "radio"}]
    cubesat[6]["quantity"] = 2   # two radios -> redundant
    r = build_skeleton(cubesat, links)
    by_el: dict[str, list] = {}
    for row in r["rows"]:
        by_el.setdefault(row["element_id"], []).append(row)
    assert {"bat", "obc", "radio", "ant", "cam", "str"} <= set(by_el)
    assert "gs" not in by_el and "eps" not in by_el          # ground; subsystem with components
    radio = next(x for x in by_el["radio"] if x["library_id"] == "TTC-01")
    assert radio["severity"] == 4 and radio["detection"] == 3 and not radio["single_point"]
    assert radio["mode"]["fr"] and radio["rpn"] == radio["severity"] * radio["occurrence"] * radio["detection"]
    bat = next(x for x in by_el["bat"] if x["library_id"] == "BAT-01")
    assert bat["single_point"]
    assert r["library_c2o_default"] and r["method_standard_ref"].startswith("ECSS-Q-ST-30-02C")


# ------------------------------------------------------------------ gates

def test_gate_checks_pdr(cubesat):
    ctx = {"elements": cubesat, "interfaces": [], "params": {}, "form_factor": "3U", "mass_limit_kg": 6.0,
           "requirements": [
               {"id": "s1", "level": "system", "text": "The spacecraft shall downlink at least 1 GB per day.",
                "verification_method": "T"},
               {"id": "u1", "level": "subsystem", "text": "The EPS shall be efficient.", "parent_id": "s1"},
           ]}
    r = evaluate_gate_checks("PDR", ctx, [{"id": "SRR-EC-08", "status": "manual"}])
    ids = {c["id"]: c for c in r["checks"]}
    assert set(ids) == {"GC-PRODUCT-TREE", "GC-SPEC-TREE", "GC-REQ-QUALITY", "GC-VER-METHODS", "GC-VER-RISK",
                        "GC-MARGINS", "GC-CDS", "GC-STACK", "GC-FMECA"}
    assert ids["GC-REQ-QUALITY"]["status"] == "fail"           # "efficient" is vague, PDR needs 100 %
    assert ids["GC-VER-METHODS"]["status"] == "fail"
    assert ids["GC-SPEC-TREE"]["status"] == "pass"
    assert ids["GC-CDS"]["status"] == "warn"
    assert "4.4.3.4.4" in ids["GC-SPEC-TREE"]["standard_ref"]
    assert r["computed_criteria"][0]["id"] == "SRR-EC-08"


def test_srr_trl_criterion(cubesat):
    cubesat[5]["trl"] = 3
    out = computed_for_criterion("SRR-EC-08", {"elements": cubesat})
    assert out["status"] == "fail" and "OBC" in out["detail"]["en"]


# ------------------------------------------------------------------ AI output validation

def test_ai_output_is_rule_checked():
    res = check_ai_output("write_requirements", {"content": "", "requirements": [
        {"text": "The EPS shall provide at least 12 W at EOL."},
        {"text": "The system shall be user-friendly."}]})
    assert res["validated"] is True
    summ = res["rule_checks"]["summary"]
    assert summ["statements"] == 2 and summ["needs_revision"] == 1
    assert res["requirements"][1]["quality"]["status"] == "fail"

    prose = "Overall fine.\n- The OBC shall boot within 10 s.\n- The radio shall be robust. Some TBD remain."
    assert extract_statements(prose) == ["The OBC shall boot within 10 s.", "The radio shall be robust."]
    res = check_ai_output("critique_need", {"content": prose})
    assert res["rule_checks"]["summary"]["needs_revision"] == 1 and res["rule_checks"]["summary"]["open_items"] == 1
