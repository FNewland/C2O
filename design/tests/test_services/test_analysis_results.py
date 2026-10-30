"""SCDF-170 §1.2 — ResultsSink: parameters written with provenance, manual
switch never overridden, conflicts persisted/resolved, run + stale lifecycle,
``el:`` compliance flips on publish."""
from __future__ import annotations

import json

import pytest

from tests.test_repositories.conftest import db_factory, study  # noqa: F401
from tests.test_services.test_analysis_context import _el, clean_caches  # noqa: F401


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SPACECDF_DATA_DIR", str(tmp_path / "data"))
    from spacecdf_server.services import analysis_results
    analysis_results.reset_trackers()
    yield tmp_path / "data"
    analysis_results.reset_trackers()


async def _seed(study_id: str) -> None:
    await _el(study_id, "mission", "Mission", "mission")
    await _el(study_id, "sc", "Spacecraft", "system", "mission")
    await _el(study_id, "eps", "EPS", "subsystem", "sc", "power")
    await _el(study_id, "bat", "Battery", "component", "eps", "power", mass_kg=1.0)
    await _el(study_id, "aocs", "AOCS", "subsystem", "sc", "aocs", mass_kg=2.0)


async def test_publish_writes_params_with_provenance(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db.parameter_repo import list_element_parameters_by_element
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.analysis_results import ParamWrite, ResultsSink

    await _seed(study)
    res = await ResultsSink().publish(study, "mission_simulation", parameters=[
        ParamWrite("sim_min_soc_pct", 42.5, unit="%"),                       # study-level -> mission root
        ParamWrite("mass_kg", 4.2, element_id="eps", unit="kg"),             # well-known, column empty
        ParamWrite("mass_kg", 9.9, element_id="ghost"),                      # unknown element
        ParamWrite("bogus", "x"),                                            # type: ignore[arg-type]
    ])
    assert [w["name"] for w in res.written] == ["sim_min_soc_pct", "mass_kg"]
    assert sorted(s["reason"] for s in res.skipped) == ["element 'ghost' not in study", "non-numeric value"]
    assert res.paths[:2] == ["el:mission.sim_min_soc_pct", "el:Mission.sim_min_soc_pct"]
    assert "power.eps_mass_kg" in res.paths and "el:EPS.mass_kg" in res.paths

    rows = {r["definition_id"]: r for r in await list_element_parameters_by_element("mission")}
    row = rows["pd-sim_min_soc_pct"]
    assert row["computed_value"] == 42.5 and row["owner_domain"] == "mission_simulation"
    assert row["value_switch"] == "computed"

    ctx = await build_context(study)
    assert ctx.params["mission"]["sim_min_soc_pct"].value == 42.5
    assert ctx.params["mission"]["sim_min_soc_pct"].unit == "%"
    assert ctx.params["eps"]["mass_kg"].value == 4.2
    assert ctx.elements_by_id["eps"]["mass_kg"] == 4.2                    # column written through (was None)
    assert ctx.resolve("el:mission.sim_min_soc_pct") == 42.5


async def test_publish_never_overrides_manual(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db.parameter_repo import upsert_element_parameter
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.analysis_results import ParamWrite, ResultsSink

    await _seed(study)
    await upsert_element_parameter({"study_id": study, "element_id": "aocs", "definition_name": "mass_kg",
                                    "manual_value": 5.0, "value_switch": "manual"})
    res = await ResultsSink().publish(study, "design_loop", parameters=[
        ParamWrite("mass_kg", 1.23, element_id="aocs")])
    assert res.written == [] and [s["name"] for s in res.shadowed] == ["mass_kg"]
    ctx = await build_context(study)
    p = ctx.params["aocs"]["mass_kg"]
    assert p.value == 5.0 and p.switch == "manual" and p.provenance == "manual"
    # column untouched by the sink (the API PUT path writes it back); flat uses the override
    assert ctx.elements_by_id["aocs"]["mass_kg"] == 2.0
    assert ctx.flat["aocs.mass_kg"] == 5.0 and "aocs.mass_kg" in ctx.overridden_paths


async def test_conflicts_persisted_and_resolved(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db.analysis_repo import list_conflicts
    from spacecdf_server.services.analysis_results import Conflict, ResultsSink, resolve_conflict

    await _seed(study)
    sink = ResultsSink()
    res = await sink.publish(study, "mission_simulation", conflicts=[
        Conflict("critical", "SOC_LOW", "SoC below 20 %", "min 12 % in Safe", element_ids=["bat"],
                 requirement_ids=["SR-1"], suggested_fix="bigger battery"),
        Conflict("major", "DATA_OVERFLOW", "Buffer full"),
    ])
    assert len(res.conflicts) == 2
    rows = await list_conflicts(study)
    assert [(r["severity"], r["code"], r["element_ids"], r["resolved"]) for r in rows] == [
        ("critical", "SOC_LOW", ["bat"], False), ("major", "DATA_OVERFLOW", [], False)]
    assert rows[0]["suggested_fix"] == "bigger battery" and rows[0]["requirement_ids"] == ["SR-1"]

    resolved = await resolve_conflict(rows[0]["id"])
    assert resolved["resolved"] and resolved["resolved_at"]
    assert await resolve_conflict("cf-missing") is None
    assert [r["code"] for r in await list_conflicts(study)] == ["DATA_OVERFLOW"]
    assert len(await list_conflicts(study, include_resolved=True)) == 2

    # re-publish replaces the unresolved set, keeps the resolved one, other analyses untouched
    await sink.publish(study, "ground", conflicts=[Conflict("warning", "MARGIN", "Low margin")])
    await sink.publish(study, "mission_simulation", conflicts=[Conflict("minor", "SAFE_TIME", "Safe 12 %")])
    codes = sorted((r["analysis"], r["code"]) for r in await list_conflicts(study, include_resolved=True))
    assert codes == [("ground", "MARGIN"), ("mission_simulation", "SAFE_TIME"), ("mission_simulation", "SOC_LOW")]
    # option-scoped conflicts are separate
    await sink.publish(study, "ground", option_id="opt-b", conflicts=[Conflict("info", "B", "b")])
    assert [r["code"] for r in await list_conflicts(study, option_id="opt-b")] == ["B"]
    assert [r["code"] for r in await list_conflicts(study, analysis="ground")] == ["MARGIN"]


async def test_run_lifecycle_and_stale(db_factory, study, clean_caches, data_dir):  # noqa: F811
    from spacecdf_server.db.parameter_repo import upsert_element_parameter
    from spacecdf_server.services.analysis_context import build_context, context_hash
    from spacecdf_server.services.analysis_results import (
        finish_run, get_last_run, input_keys_for, list_analyses, load_series, start_run,
    )

    await _seed(study)
    assert await get_last_run(study, "mission_simulation") is None
    ctx = await build_context(study)
    h = context_hash(ctx, input_keys_for("mission_simulation"))
    run_id = await start_run(study, "mission_simulation", h)
    assert run_id.startswith("run-")
    assert await get_last_run(study, "mission_simulation") is None      # still running -> not "last"

    run = await finish_run(run_id, "ok", summary={"min_soc": 33.0}, series={"t": [0, 1], "soc": [100, 90]})
    assert run["status"] == "ok" and run["finished_at"] and run["summary"] == {"min_soc": 33.0}
    assert run["series_ref"] == f"analysis/{run_id}.json"
    assert (data_dir / "analysis" / f"{run_id}.json").exists()
    assert json.loads((data_dir / "analysis" / f"{run_id}.json").read_text())["soc"] == [100, 90]
    assert load_series(run["series_ref"]) == {"t": [0, 1], "soc": [100, 90]}

    last = await get_last_run(study, "mission_simulation")
    assert last["id"] == run_id and last["stale"] is False and last["current_hash"] == h

    # an input the analysis reads changes -> stale; one it does not read -> still fresh
    await upsert_element_parameter({"study_id": study, "element_id": "bat", "definition_name": "mass_kg",
                                    "manual_value": 3.0, "value_switch": "manual"})
    assert (await get_last_run(study, "mission_simulation"))["stale"] is True
    run2 = await start_run(study, "vv", context_hash(await build_context(study), input_keys_for("vv")))
    await finish_run(run2, "ok")
    listing = await list_analyses(study)
    assert [(r["analysis"], r["stale"]) for r in listing] == [("mission_simulation", True), ("vv", False)]

    # a failed later run becomes the last one; option-scoped runs are separate
    run3 = await start_run(study, "mission_simulation", None)
    await finish_run(run3, "failed", summary={"error": "boom"})
    assert (await get_last_run(study, "mission_simulation"))["id"] == run3
    assert await get_last_run(study, "mission_simulation", option_id="opt-x") is None
    with pytest.raises(ValueError):
        await finish_run(run3, "weird")


async def test_el_path_compliance_flips(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.routers import requirements as rr
    from spacecdf_server.services.analysis_results import ParamWrite, ResultsSink, get_tracker

    await _seed(study)
    await rr.ensure_requirements_loaded()
    rr._requirements["SR-M"] = {"id": "SR-M", "study_id": study, "parent_id": None, "element_id": "eps",
                                "level": "system", "code": "SR-M", "text": "EPS mass <= 5 kg", "status": "approved",
                                "threshold_param_path": "el:EPS.mass_kg", "threshold_op": "<=", "threshold_value": "5"}
    rr._requirements["SR-F"] = {"id": "SR-F", "study_id": study, "parent_id": None, "element_id": None,
                                "level": "system", "code": "SR-F", "text": "flat path", "status": "approved",
                                "threshold_param_path": "power.eps_mass_kg", "threshold_op": "<=",
                                "threshold_value": "0.5"}
    rr._requirements["SR-X"] = {"id": "SR-X", "study_id": study, "parent_id": None, "element_id": None,
                                "level": "system", "code": "SR-X", "text": "untouched", "status": "approved",
                                "threshold_param_path": "el:AOCS.mass_kg", "threshold_op": "<=",
                                "threshold_value": "1"}
    sink = ResultsSink()
    res = await sink.publish(study, "design_loop", parameters=[ParamWrite("mass_kg", 4.0, element_id="eps")])
    assert res.compliance_results["SR-M"]["status"] == "pass"
    assert res.compliance_results["SR-M"]["achieved"] == 4.0
    assert "SR-X" not in res.compliance_results                       # not dirty, not evaluated
    assert res.compliance.newly_violated == []

    res = await sink.publish(study, "design_loop", parameters=[ParamWrite("mass_kg", 6.0, element_id="eps")])
    assert res.compliance_results["SR-M"]["status"] == "fail"
    assert res.compliance.newly_violated == ["SR-M"]
    assert res.compliance.affected_elements == ["eps"]

    # a component write dirties the flat registry path its subsystem aggregate feeds; the
    # column (1.0, KB truth) still drives the projection — computed values never displace it
    res = await sink.publish(study, "design_loop", parameters=[ParamWrite("mass_kg", 2.0, element_id="bat")])
    assert "power.eps_mass_kg" in res.paths
    assert res.compliance_results["SR-F"]["status"] == "fail" and res.compliance_results["SR-F"]["achieved"] == 1.0
    assert get_tracker(study).get_all_results()["SR-M"].status == "fail"

    res = await sink.publish(study, "design_loop", parameters=[ParamWrite("mass_kg", 4.5, element_id="eps")])
    assert res.compliance.newly_cleared == ["SR-M"]
