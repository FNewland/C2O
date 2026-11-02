"""Gate exit-criteria evaluator (author ruling Q23).

The Gate Review tab picks MCR / SRR / PDR and shows the criteria evaluated
by the backend from ``configs/gate_exit_criteria.yaml``. Should-pass items
are advisory: they are reported but never block the gate.
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
    ("MCR", "pre_phase_a"), ("mcr", "pre_phase_a"), ("srr", "phase_a"),
    ("PDR", "phase_b1"), ("phase_b1", "phase_b1"), ("cdr", None), ("", None),
])
def test_resolve_phase_accepts_gate_names(key, phase):
    assert ge.resolve_phase(key) == phase


def test_gate_options_list_mcr_srr_pdr():
    gates = [g["gate"] for g in ge.list_gate_options()]
    assert gates[:3] == ["MCR", "SRR", "PDR"]


@pytest.mark.parametrize("gate", ["MCR", "SRR", "PDR"])
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
    res = ge.evaluate_gate("cdr")
    assert res["found"] is False and res["criteria"] == [] and res["ready"] is False


def test_mcr_complete_mission_need_and_design_is_ready():
    params = {"systems.mass_margin_percent": 12, "systems.power_margin_percent": {"value": 8},
              "risk.total_risks": 4, "debris.compliance_score": 70, "cost.total_meur": 1.0}
    res = ge.evaluate_gate("MCR", mission_need=GOOD_NEED, design_params=params)
    by = {c["id"]: c for c in res["criteria"]}
    assert all(c["status"] == "pass" for c in res["criteria"]), {k: c["evidence_found"] for k, c in by.items()}
    assert res["ready"] and res["ready_pending_manual"]
    assert by["MCR-EC-04"]["evidence_found"] == "2 alternative(s), including a non-space option"
    assert by["MCR-EC-07"]["evidence_params"] == {"mass": "12", "power": "8"}


def test_mcr_accepts_the_pydantic_model():
    mn = MissionNeed(problem_statement="x", stakeholders=[{"name": "ESA"}])
    by = {c["id"]: c for c in ge.evaluate_gate("MCR", mission_need=mn)["criteria"]}
    assert by["MCR-EC-01"]["status"] == "pass"
    assert by["MCR-EC-02"]["status"] == "pass"
    assert by["MCR-EC-03"]["status"] == "fail"


def test_empty_study_fails_must_pass_and_skips_missing_parameters():
    res = ge.evaluate_gate("MCR")
    by = {c["id"]: c for c in res["criteria"]}
    assert by["MCR-EC-01"]["verdict"] == "fail"
    # No design run: parameters are not invented, the criterion is not evaluated
    assert by["MCR-EC-07"]["status"] == "not_evaluated"
    assert by["MCR-EC-07"]["evidence_key"] == ge.MSG_RUN_DESIGN
    assert "systems.mass_margin_percent" in by["MCR-EC-07"]["evidence_found"]
    assert res["ready"] is False


def test_pdr_should_pass_items_are_advisory_and_do_not_block():
    """Q23: PDR should-pass items stay advisory."""
    reqs = [{"id": "R1", "code": "SYS-001", "threshold_param_path": "systems.mass_margin_percent",
             "threshold_op": ">=", "threshold_value": "10", "verification_method": "A"}]
    params = {"systems.mass_margin_percent": 15, "systems.power_margin_percent": 20,
              "reliability.mission_reliability": 0.95}
    # PDR-EC-04 (should_pass): a subsystem with no component → not met
    elements = [{"id": "sc", "element_type": "system"},
                {"id": "eps", "element_type": "subsystem", "parent_id": "sc"}]
    res = ge.evaluate_gate("PDR", design_params=params, requirements=reqs, elements=elements)
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
    params = {"systems.mass_margin_percent": 5, "systems.power_margin_percent": 20, "eps.power_w": 12}
    by = {c["id"]: c for c in ge.evaluate_gate("PDR", design_params=params, requirements=reqs)["criteria"]}
    assert by["PDR-EC-03"]["verdict"] == "fail"
    assert by["PDR-EC-03"]["evidence_params"]["min"] == 10
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
