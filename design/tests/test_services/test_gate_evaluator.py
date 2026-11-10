"""Gate exit-criteria evaluator (author ruling Q23; MDR/PRR Nov 2026).

The canonical gates are MDR / PRR / SRR / PDR (ECSS; "MCR" is the old name of the
MDR and still resolves to it). The criteria are evaluated by the backend from
``configs/gate_exit_criteria.yaml``. Should-pass items are advisory: they are
reported but never block the gate.
"""
from __future__ import annotations

import pytest
import yaml

from spacecdf_common.models.mission_need import MissionNeed
from spacecdf_server.services import gate_evaluator as ge


def _yaml_ids(gate: str) -> list[str]:
    data = yaml.safe_load(ge._criteria_file().read_text(encoding="utf-8"))
    for g in data["phases"].values():
        if g["gate"] == gate:
            return [c["id"] for c in g["exit_criteria"]]
    raise AssertionError(gate)


GOOD_NEED = {
    "problem_statement": "Wildfire smoke is detected too late in northern Ontario.",
    "stakeholders": [{"id": "S1", "name": "Ontario Forest Fire Service", "role": "user"}],
    "objectives": [{"id": "O1", "text": "Detect smoke plumes", "priority": "primary",
                    "measurable_criterion": "Detection within 30 min"}],
    # Frontend store key: ``alternatives`` (model: ``alternatives_considered``)
    "alternatives": [{"id": "A1", "name": "6U CubeSat", "type": "space_dedicated"},
                     {"id": "A2", "name": "Lookout drones", "type": "aerial_drone"}],
    "selected_alternative_id": "A1",
    "selection_rationale": "Coverage of remote areas",
    "conops_summary": "Two passes a day, downlink to Inuvik.",
}


@pytest.mark.parametrize("key,phase", [
    ("MDR", "phase_0"), ("mdr", "phase_0"), ("MCR", "phase_0"), ("mcr", "phase_0"),
    ("pre_phase_a", "phase_0"), ("prr", "phase_a"), ("srr", "phase_b1"),
    ("PDR", "phase_b"), ("phase_b1", "phase_b1"), ("cdr", "phase_c"), ("CDR", "phase_c"), ("qr", "phase_d_qr"), ("FRR", "phase_e_frr"),
    ("orr", None), ("", None),
])
def test_resolve_phase_accepts_gate_names(key, phase):
    """MCR (the old name, ruling 3) and pre_phase_a still resolve to the MDR."""
    assert ge.resolve_phase(key) == phase


def test_gate_options_list_mdr_prr_srr_pdr_cdr_qr_ar_frr():
    gates = [g["gate"] for g in ge.list_gate_options()]
    assert gates == ["MDR", "PRR", "SRR", "PDR", "CDR", "QR", "AR", "FRR"]


def test_legacy_criterion_ids_map_to_mdr():
    assert ge.canonical_criterion_id("MCR-EC-04") == "MDR-EC-04"
    assert ge.canonical_criterion_id("SRR-EC-04") == "SRR-EC-04"


def test_every_criterion_names_an_owner_seat_and_a_step():
    from spacecdf_server.logbook.decisions import catalogue
    from spacecdf_server.services import gate_profiles as gp
    seats = {s["id"] for s in catalogue().get("seats") or []}
    steps = set(gp.load()["steps"])
    panels = {"analyses", "budget", "blocks", "requirements", "functions", "interfaces", "decide", "vv:risks",
              "tmtc", "fdir", "aocs", "ops"}
    data = yaml.safe_load(ge._criteria_file().read_text(encoding="utf-8"))
    for g in data["phases"].values():
        for c in g["exit_criteria"]:
            assert c["owner_seat"] in seats, c["id"]
            assert c["step"] in steps, c["id"]
            assert c.get("fix") is None or c["fix"] in panels, c["id"]


@pytest.mark.parametrize("gate", ["MDR", "PRR", "SRR", "PDR", "CDR"])
def test_every_yaml_criterion_is_returned_in_order(gate):
    res = ge.evaluate_gate(gate.lower())
    assert res["found"] and res["gate"] == gate
    assert [c["id"] for c in res["criteria"]] == _yaml_ids(gate)
    for c in res["criteria"]:
        assert c["status"] in {"pass", "fail", "manual", "not_evaluated"}
        assert c["verdict"] in {"pass", "fail", "advisory", "manual", "not_evaluated"}
        assert c["evidence_found"]
        assert c["evidence_required"]
        # The English message is the rendered i18n key template
        if c["evidence_key"]:
            msg = c["evidence_key"]
            for k, v in c["evidence_params"].items():
                msg = msg.replace("{{" + k + "}}", str(v))
            assert msg == c["evidence_found"]


def test_unknown_gate_is_reported_not_raised():
    res = ge.evaluate_gate("orr")
    assert res["found"] is False and res["criteria"] == [] and res["ready"] is False


def test_mdr_complete_mission_need_and_design_is_ready():
    params = {"systems.mass_margin_percent": 12, "systems.power_margin_percent": {"value": 8},
              "risk.total_risks": 4, "debris.compliance_score": 70, "cost.total_meur": 1.0}
    res = ge.evaluate_gate("MDR", mission_need=GOOD_NEED, design_params=params)
    by = {c["id"]: c for c in res["criteria"]}
    assert all(c["status"] == "pass" for c in res["criteria"]), {k: c["evidence_found"] for k, c in by.items()}
    assert res["ready"] and res["ready_pending_manual"]
    assert by["MDR-EC-04"]["evidence_found"] == "2 alternative(s), including a non-space option"
    assert by["MDR-EC-07"]["evidence_params"] == {"mass": "12", "power": "8"}
    assert by["MDR-EC-01"]["owner_seat"] == "team_leader" and by["MDR-EC-01"]["step"] == "S1"


def test_mdr_accepts_the_pydantic_model():
    mn = MissionNeed(problem_statement="x", stakeholders=[{"name": "ESA"}])
    by = {c["id"]: c for c in ge.evaluate_gate("MCR", mission_need=mn)["criteria"]}   # old name still works
    assert by["MDR-EC-01"]["status"] == "pass"
    assert by["MDR-EC-02"]["status"] == "pass"
    assert by["MDR-EC-03"]["status"] == "fail"


def test_empty_study_fails_must_pass_and_skips_missing_parameters():
    res = ge.evaluate_gate("MDR")
    by = {c["id"]: c for c in res["criteria"]}
    assert by["MDR-EC-01"]["verdict"] == "fail"
    # No design run: parameters are not invented, the criterion is not evaluated
    assert by["MDR-EC-07"]["status"] == "not_evaluated"
    assert by["MDR-EC-07"]["evidence_key"] == ge.MSG_RUN_DESIGN
    assert "systems.mass_margin_percent" in by["MDR-EC-07"]["evidence_found"]
    assert res["ready"] is False


def test_mdr_ec07_names_the_missing_mass_limit_after_a_design_run():
    """The loop ran (power margin present) but there is no mass limit: say so, not 'run the loop'."""
    by = {c["id"]: c for c in ge.evaluate_gate(
        "MDR", design_params={"systems.power_margin_percent": 30})["criteria"]}
    assert by["MDR-EC-07"]["status"] == "not_evaluated"
    assert "mass limit" in by["MDR-EC-07"]["evidence_found"]
    with_target = {c["id"]: c for c in ge.evaluate_gate(
        "MDR", design_params={"systems.power_margin_percent": 30}, target_mass_kg=12)["criteria"]}
    assert with_target["MDR-EC-07"]["evidence_key"] == ge.MSG_RUN_DESIGN


def test_mdr_ec09_reads_the_risk_register():
    risks = [{"id": "RSK-001", "status": "open"}, {"id": "RSK-002", "status": "open"}]
    by = {c["id"]: c for c in ge.evaluate_gate("MDR", risks=risks)["criteria"]}
    assert by["MDR-EC-09"]["status"] == "pass" and by["MDR-EC-09"]["evidence_params"] == {"n": 2}
    none = {c["id"]: c for c in ge.evaluate_gate("MDR", design_params={"risk.total_risks": 0})["criteria"]}
    assert none["MDR-EC-09"]["status"] == "fail"


def test_pdr_should_pass_items_are_advisory_and_do_not_block():
    """Q23: PDR should-pass items stay advisory."""
    reqs = [{"id": "R1", "code": "SYS-001", "threshold_param_path": "systems.mass_margin_percent",
             "threshold_op": ">=", "threshold_value": "10", "verification_method": "A"}]
    params = {"systems.mass_margin_percent": 15, "systems.power_margin_percent": 20,
              "reliability.mission_reliability": 0.95,
              # PDR-EC-03 (margin ladder, PDR 20 %): 9 kg × 1.2 = 10.8 kg ≤ 12 kg; 20 W × 1.2 = 24 W ≤ 30 W
              "mass.dry_mass_kg": 9.0, "power.total_sunlight_w": 20.0, "power.sa_power_eol_w": 30.0}
    # PDR-EC-04 (should_pass): a subsystem with no component → not met
    elements = [{"id": "sc", "element_type": "system"},
                {"id": "eps", "element_type": "subsystem", "parent_id": "sc"}]
    res = ge.evaluate_gate("PDR", design_params=params, requirements=reqs, elements=elements,
                           target_mass_kg=12.0)
    by = {c["id"]: c for c in res["criteria"]}

    assert by["PDR-EC-04"]["priority"] == "should_pass"
    assert by["PDR-EC-04"]["status"] == "fail"
    assert by["PDR-EC-04"]["verdict"] == "advisory"
    assert by["PDR-EC-04"]["advisory"] is True

    assert by["PDR-EC-01"]["status"] == "pass"
    assert by["PDR-EC-03"]["status"] == "pass"
    assert by["PDR-EC-05"]["status"] == "pass"
    # Nov 2026: PDR-EC-02 is computed from the expected-interface coverage; the
    # lone EPS subsystem has no mount / thermal link → must_pass not met
    assert by["PDR-EC-02"]["status"] == "fail" and by["PDR-EC-02"]["verdict"] == "fail"
    assert by["PDR-EC-02"]["evidence_params"]["met"] == 0
    assert res["ready"] is False
    assert res["ready_pending_manual"] is False
    assert res["summary"]["advisory"] == 1
    assert res["summary"]["must_pass"] == 4 and res["summary"]["must_pass_met"] == 3


def test_pdr_margin_and_requirement_failures_block():
    reqs = [{"id": "R1", "code": "SYS-PWR-003", "threshold_param_path": "eps.power_w",
             "threshold_op": "<=", "threshold_value": 10}]
    # 10.5 kg × 1.15 (PDR, Phase B, textbook Table 8.3) = 12.075 kg > 12 kg
    params = {"mass.dry_mass_kg": 10.5, "power.total_sunlight_w": 10.0, "power.sa_power_eol_w": 30.0,
              "eps.power_w": 12}
    by = {c["id"]: c for c in ge.evaluate_gate("PDR", design_params=params, requirements=reqs,
                                               target_mass_kg=12.0)["criteria"]}
    assert by["PDR-EC-03"]["verdict"] == "fail"
    assert by["PDR-EC-03"]["evidence_params"]["margin"] == "15"
    assert by["PDR-EC-03"]["evidence_params"]["total"] == "12.07"
    assert by["PDR-EC-01"]["verdict"] == "fail"
    assert "SYS-PWR-003" in by["PDR-EC-01"]["evidence_found"]


def test_pdr_subsystems_with_components_pass():
    elements = [{"id": "eps", "element_type": "subsystem"},
                {"id": "bat", "element_type": "component", "parent_id": "eps"},
                {"id": "aocs", "element_type": "subsystem"},
                {"id": "grp", "element_type": "logical", "parent_id": "aocs"},
                {"id": "rw", "element_type": "component", "parent_id": "grp"}]
    by = {c["id"]: c for c in ge.evaluate_gate("PDR", elements=elements)["criteria"]}
    assert by["PDR-EC-04"]["status"] == "pass"
    assert by["PDR-EC-04"]["evidence_params"] == {"ok": 2, "total": 2}


def test_srr_sustainability_is_not_evaluated_as_reliability():
    params = {"sustainability.score": 60, "debris.casualty_compliant": 0,
              "reliability.mission_reliability": 0.99}
    by = {c["id"]: c for c in ge.evaluate_gate("SRR", design_params=params)["criteria"]}
    assert by["SRR-EC-10"]["status"] == "fail"
    assert by["SRR-EC-10"]["evidence_key"].endswith("casualty risk not compliant")


def test_srr_traceability_and_requirement_quality():
    need = {"objectives": [{"id": "O1", "priority": "primary"}, {"id": "O2", "priority": "secondary"}]}
    reqs = [{"id": "R1", "objective_id": "O1", "verification_method": "T",
             "threshold_param_path": "p", "threshold_op": ">=", "threshold_value": "1"},
            {"id": "R2", "verification_method": "I"}]
    by = {c["id"]: c for c in ge.evaluate_gate("SRR", mission_need=need, requirements=reqs)["criteria"]}
    assert by["SRR-EC-01"]["status"] == "fail"
    assert by["SRR-EC-01"]["evidence_params"] == {"traced": 1, "total": 2}
    assert by["SRR-EC-02"]["status"] == "fail"
    assert by["SRR-EC-02"]["evidence_params"] == {"ok": 1, "total": 2}
    assert by["SRR-EC-09"]["status"] == "manual"
    assert by["SRR-EC-09"]["verdict"] == "advisory"   # should_pass sign-off: never blocks


# --------------------------------------------------------------------------- i18n contract
# The UI renders evidence via t(evidence_key, evidence_params) and questions via
# t(question); both need the English text listed in gateReviewText.ts (so the
# i18n tool extracts it) and a French entry in a frontend catalog.

import ast  # noqa: E402
import glob  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

_DESIGN = Path(__file__).resolve().parents[2]
_FRONT_TEXT = (_DESIGN / "frontend/src/components/gateReviewText.ts").read_text(encoding="utf-8")


def _fr_catalog() -> dict:
    out: dict = {}
    for p in sorted(glob.glob(str(_DESIGN / "frontend/src/i18n/locales/fr*.json"))):
        out.update({k: v for k, v in json.loads(Path(p).read_text(encoding="utf-8")).items() if v})
    return out


def _emitted_keys() -> set[str]:
    """String literals passed as the key of ``_set`` or assigned to ``key``."""
    tree = ast.parse(Path(ge.__file__).read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_set" and len(node.args) >= 3:
            arg = node.args[2]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                found.add(arg.value)
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "key" for t in node.targets):
            for c in ast.walk(node.value):
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    found.add(c.value)
    return found


def test_every_emitted_key_is_declared():
    assert _emitted_keys() - set(ge.EVIDENCE_KEYS) == set()


def test_evidence_keys_and_questions_are_translatable():
    fr = _fr_catalog()
    data = yaml.safe_load(ge._criteria_file().read_text(encoding="utf-8"))
    questions = [c["question"] for g in data["phases"].values() for c in g["exit_criteria"]]
    for text in [*ge.EVIDENCE_KEYS, *questions]:
        assert f"'{text}'" in _FRONT_TEXT, f"not listed in gateReviewText.ts: {text!r}"
        assert text in fr, f"no French translation: {text!r}"


# ─── wave 2 (W4.09): QR, AR and FRR criteria live in the YAML ─────────────────────────────


def test_post_cdr_review_record_items_come_from_the_yaml_with_the_interim_behaviour():
    """gate_reviews.POST_CDR_CRITERIA (agent D's interim table) is now read from the YAML: every
    interim item is there with the same question, category, owner, evidence and auto rule."""
    from spacecdf_server.services import gate_reviews
    table = ge.review_record_table()
    assert set(table) == {"qr", "ar", "frr"}
    for gate, specs in gate_reviews.POST_CDR_CRITERIA.items():
        by_id = {s["id"]: s for s in table[gate]}
        for spec in specs:
            got = by_id[spec["id"]]
            for k in ("question", "category", "owner_seat", "auto", "evidence"):
                assert got.get(k) == spec.get(k), (spec["id"], k)
    # FRR (agency CubeSat practice: before delivery): VCD, licences, operations, mass properties, delivery
    assert [s["id"] for s in table["frr"]] == [f"FRR-RR-0{i}" for i in range(1, 7)]


def test_evaluate_gate_leaves_review_record_items_to_the_review_record():
    res = ge.evaluate_gate("frr")
    assert res["found"] and res["gate"] == "FRR" and res["criteria"] == []
    qr = ge.evaluate_gate("qr", requirements=[
        {"id": "a", "code": "SYS-1", "level": "system", "verification_method": "T", "verification_phase": "CDR"},
        {"id": "b", "code": "OBJ-O1", "level": "mission", "verification_method": None},
        {"id": "c", "code": "SN-01", "level": "stakeholder"}])
    assert [c["id"] for c in qr["criteria"]] == ["QR-EC-01"]
    c = qr["criteria"][0]
    assert c["status"] == "fail" and c["evidence_params"]["codes"] == "OBJ-O1" and c["evidence_params"]["total"] == 2
    ok = ge.evaluate_gate("qr", requirements=[{"id": "a", "code": "SYS-1", "level": "system",
                                               "verification_methods": ["T"], "verification_phase": "QR"}])
    assert ok["criteria"][0]["status"] == "pass"
