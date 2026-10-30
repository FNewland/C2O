"""SCDF-175 — V&V closure: one item per persisted requirement with method /
level / phase / facility / acceptance text derived from the requirement and
its allocation; user edits survive a re-run; auto-closure flips A-items when
a publish makes their threshold PASS or FAIL; VV_* conflicts; parameters."""
from __future__ import annotations

import pytest

from tests.test_repositories.conftest import db_factory, study  # noqa: F401
from tests.test_services.test_analysis_context import _el, clean_caches  # noqa: F401


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SPACECDF_DATA_DIR", str(tmp_path / "data"))
    from spacecdf_server.services import analysis_results
    from spacecdf_server.services.vv_closure import install_auto_closure
    analysis_results.reset_trackers()
    install_auto_closure()
    yield
    analysis_results.reset_trackers()


def _req(rr, study_id, rid, **kw):
    d = {"id": rid, "study_id": study_id, "parent_id": None, "element_id": None, "level": "system", "code": rid,
         "text": f"Requirement {rid}", "status": "approved", "threshold_param_path": None, "threshold_op": None,
         "threshold_value": None, "verification_method": None, "verification_phase": None, **kw}
    rr._requirements[rid] = d
    return d


async def _seed(study_id: str) -> None:
    from spacecdf_server.db.relation_repo import create_relation
    from spacecdf_server.routers import requirements as rr

    await _el(study_id, "mission", "Mission", "mission")
    await _el(study_id, "space", "Space Segment", "segment", "mission")
    await _el(study_id, "sc", "Spacecraft", "system", "space")
    await _el(study_id, "eps", "EPS", "subsystem", "sc", "power", mass_kg=1.5)
    await _el(study_id, "bat", "Battery", "component", "eps", "power", mass_kg=1.0, power_avg_w=0.5,
              performance_json={"capacity_wh": 40.0})
    await _el(study_id, "str", "Structure", "subsystem", "sc", "structure", mass_kg=1.5)
    await rr.ensure_requirements_loaded()
    # mission narrative, no method, no threshold -> R at segment level, VV_REQ_UNVERIFIABLE
    _req(rr, study_id, "MR-1", level="mission", text="The mission shall image the Arctic coast")
    # system requirement on an element parameter (analysis) — allocated to EPS via a relation
    _req(rr, study_id, "SR-PWR-1", text="EPS mass shall not exceed 5 kg",
         threshold_param_path="el:EPS.mass_kg", threshold_op="<=", threshold_value="5")
    await create_relation({"study_id": study_id, "kind": "satisfies", "source_kind": "element", "source_id": "eps",
                           "target_kind": "requirement", "target_id": "SR-PWR-1"})
    # subsystem requirement with an explicit test method on a component -> unit level, shaker
    _req(rr, study_id, "SR-STR-1", level="subsystem", element_id="str", verification_method="T",
         text="Structure shall survive qualification vibration", threshold_param_path="structure.first_mode_hz",
         threshold_op=">=", threshold_value="90")
    # flat-path requirement on a component (unit level) with DoD threshold
    _req(rr, study_id, "SR-BAT-1", level="subsystem", element_id="bat", verification_phase="CDR",
         text="Battery DoD", threshold_param_path="power.battery_dod_percent", threshold_op="<=", threshold_value="30")


async def _run(study_id, run_id=None):
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.vv_closure import run_vv
    ctx = await build_context(study_id)
    return ctx, await run_vv(ctx, run_id=run_id)


async def test_items_generated_for_all_requirements(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db import verification_repo as vr
    from spacecdf_server.services.vv_closure import OUTPUT_PARAMETERS

    await _seed(study)
    ctx, out = await _run(study, run_id="run-vv-1")
    items = {i["requirement_id"]: i for i in await vr.list_by_study(study)}
    assert set(items) == {"MR-1", "SR-PWR-1", "SR-STR-1", "SR-BAT-1"}

    mr = items["MR-1"]
    assert mr["method"] == "R" and mr["level"] == "segment" and mr["phase"] == "PDR"
    assert mr["acceptance_criterion"] == "The mission shall image the Arctic coast (review of design), PDR"

    pwr = items["SR-PWR-1"]
    assert pwr["method"] == "A" and pwr["level"] == "system" and pwr["phase"] == "PDR"
    assert pwr["acceptance_criterion"] == "EPS mass ≤ 5 kg (analysis: design loop), PDR"
    assert pwr["facility"] == "analysis desk"
    # EPS mass column 1.5 kg <= 5 -> closed by the run's own evaluation
    assert pwr["status"] == "passed" and pwr["evidence_ref"] == "analysis:run-vv-1"

    st = items["SR-STR-1"]
    assert st["method"] == "T" and st["level"] == "subsystem" and st["phase"] == "CDR"
    assert st["facility"] == "shaker_table"
    assert st["acceptance_criterion"] == "First mode ≥ 90 Hz (test), CDR"
    assert st["status"] == "planned"  # tests are never auto-closed

    bat = items["SR-BAT-1"]
    assert bat["method"] == "A" and bat["level"] == "unit" and bat["phase"] == "CDR"
    assert bat["acceptance_criterion"] == "Battery DoD ≤ 30 % (analysis: power budget), CDR"
    assert bat["status"] == "planned"  # no design value yet -> untestable, stays planned

    assert [p.name for p in out.parameters] == list(OUTPUT_PARAMETERS)
    s = out.summary
    assert s["vv_items_total"] == 4 and s["vv_items_passed"] == 1 and s["vv_items_failed"] == 0
    assert s["vv_items_planned"] == 3 and s["vv_closure_pct"] == 25.0 and s["vv_by_analysis_pct"] == 50.0
    assert s["by_level"]["unit"]["total"] == 1 and s["by_level"]["system"]["passed"] == 1
    codes = [(c.code, c.severity) for c in out.conflicts]
    assert codes == [("VV_REQ_UNVERIFIABLE", "warning")]
    assert out.conflicts[0].requirement_ids == ["MR-1"] and "MR-1" in out.conflicts[0].title
    row = next(i for i in s["items"] if i["requirement_id"] == "SR-PWR-1")
    assert row["linked_elements"] == ["eps"] and row["requirement_code"] == "SR-PWR-1"


async def test_user_edit_preserved_on_rerun(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db import verification_repo as vr

    await _seed(study)
    await _run(study)
    item = await vr.get_by_requirement(study, "SR-BAT-1")
    await vr.update_item(item["id"], {"method": "T", "facility": "battery lab", "acceptance_criterion": None,
                                      "status": "waived"}, by_user=True)
    await _run(study)
    again = await vr.get_by_requirement(study, "SR-BAT-1")
    assert again["id"] == item["id"] and again["method"] == "T" and again["facility"] == "battery lab"
    assert again["status"] == "waived" and again["edited_by_user"] is True
    assert again["acceptance_criterion"] == "Battery DoD ≤ 30 % (analysis: power budget), CDR"  # empty -> filled
    assert len(await vr.list_by_study(study)) == 4


async def test_auto_closure_after_publish(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db import verification_repo as vr
    from spacecdf_server.services.analysis_results import ParamWrite, ResultsSink

    await _seed(study)
    ctx, out = await _run(study, run_id="run-vv-1")
    pwr = await vr.get_by_requirement(study, "SR-PWR-1")
    assert pwr["status"] == "passed"

    # a design-loop publish that breaks the threshold -> item fails with the run's evidence
    res = await ResultsSink().publish(study, "design_loop", run_id="run-dl-1",
                                      parameters=[ParamWrite("mass_kg", 6.0, element_id="eps")])
    assert res.compliance_results["SR-PWR-1"]["status"] == "fail"
    pwr = await vr.get_by_requirement(study, "SR-PWR-1")
    assert pwr["status"] == "failed" and pwr["evidence_ref"] == "analysis:run-dl-1"
    assert pwr["edited_by_user"] is False

    # the next V&V run reports it as a major conflict with the requirement code in the title
    ctx, out = await _run(study, run_id="run-vv-2")
    failed = [c for c in out.conflicts if c.code == "VV_FAILED"]
    assert len(failed) == 1 and failed[0].severity == "major" and "SR-PWR-1" in failed[0].title
    assert failed[0].requirement_ids == ["SR-PWR-1"] and failed[0].element_ids == ["eps"]
    assert out.summary["vv_items_failed"] == 1

    # back under the threshold -> passed again
    await ResultsSink().publish(study, "design_loop", run_id="run-dl-2",
                                parameters=[ParamWrite("mass_kg", 4.0, element_id="eps")])
    pwr = await vr.get_by_requirement(study, "SR-PWR-1")
    assert pwr["status"] == "passed" and pwr["evidence_ref"] == "analysis:run-dl-2"

    # waived / user-edited items are never touched by the hook
    await vr.update_item(pwr["id"], {"status": "waived"}, by_user=True)
    await ResultsSink().publish(study, "design_loop", run_id="run-dl-3",
                                parameters=[ParamWrite("mass_kg", 9.0, element_id="eps")])
    pwr = await vr.get_by_requirement(study, "SR-PWR-1")
    assert pwr["status"] == "waived" and pwr["evidence_ref"] == "analysis:run-dl-2"

    # a T item never follows compliance even when its path is written
    st = await vr.get_by_requirement(study, "SR-STR-1")
    assert st["status"] == "planned"


async def test_acceptance_text_helpers():
    from spacecdf_server.services.vv_closure import acceptance_text, humanise_path

    assert humanise_path("power.battery_dod_percent") == ("Battery DoD", "%")
    assert humanise_path("el:EPS.mass_kg") == ("EPS mass", "kg")
    assert humanise_path("link.margin_db") == ("Margin", "dB")
    req = {"threshold_param_path": "power.battery_dod_percent", "threshold_op": "<=", "threshold_value": "30"}
    assert acceptance_text(req, "A", "PDR", "power budget") == "Battery DoD ≤ 30 % (analysis: power budget), PDR"
    rng = {"threshold_param_path": "thermal.battery_temp_c", "threshold_op": "in_range", "threshold_value": "[0, 40]"}
    assert acceptance_text(rng, "T", "QR") == "Battery temp within 0–40 °C (test), QR"
    assert acceptance_text({"code": "MR-9", "text": "Shall be nice."}, "R", "PDR") == "Shall be nice (review of design), PDR"
