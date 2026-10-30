"""SCDF-177 — FMECA from the element tree: a single-string EPS component
raises FMECA_SINGLE_POINT, ``redundancy_type='cold'`` suppresses it; modes
carry their allocated functions; parameters on the mission root."""
from __future__ import annotations

import pytest

from tests.test_repositories.conftest import db_factory, study  # noqa: F401
from tests.test_services.test_analysis_context import _el, clean_caches  # noqa: F401


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SPACECDF_DATA_DIR", str(tmp_path / "data"))
    from spacecdf_server.services import analysis_results
    analysis_results.reset_trackers()
    yield
    analysis_results.reset_trackers()


async def _seed(study_id: str, *, redundancy: str | None = None) -> None:
    await _el(study_id, "mission", "Mission", "mission")
    await _el(study_id, "space", "Space Segment", "segment", "mission")
    await _el(study_id, "sc", "Spacecraft", "system", "space")
    await _el(study_id, "eps", "EPS", "subsystem", "sc", "power")
    await _el(study_id, "bat", "Battery", "component", "eps", "power", mass_kg=1.0, power_avg_w=0.2, redundancy_type=redundancy)
    await _el(study_id, "pl", "Payload", "subsystem", "sc", "payload")
    await _el(study_id, "cam", "Camera", "component", "pl", "payload", mass_kg=1.0, power_avg_w=2.0, quantity=2)
    await _el(study_id, "aocs", "AOCS", "subsystem", "sc", "aocs", mass_kg=1.0, power_avg_w=1.0)


async def _run(study_id, **kw):
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.fmeca_closure import run_fmeca_closure
    ctx = await build_context(study_id)
    return ctx, run_fmeca_closure(ctx, **kw)


async def test_single_string_eps_component_is_a_single_point_conflict(db_factory, study, clean_caches):  # noqa: F811
    await _seed(study)
    ctx, out = await _run(study)
    modes = out.series["modes"]
    bat = [m for m in modes if m["element_id"] == "bat"]
    assert len(bat) == 1 and "Battery" in bat[0]["mode"] and bat[0]["single_point"] and bat[0]["critical"]
    assert bat[0]["severity"] == 5 and bat[0]["rpn"] == 5 * 2 * 3
    # AOCS subsystem without components: catalogue entries; the camera x2 is redundant
    assert any(m["element_id"] == "aocs" and m["source"] == "catalogue" for m in modes)
    cam = next(m for m in modes if m["element_id"] == "cam")
    assert cam["redundant"] and not cam["single_point"] and cam["severity"] == 3
    codes = [c for c in out.conflicts if c.code == "FMECA_SINGLE_POINT"]
    assert [c.element_ids for c in codes] == [["bat"]]
    assert codes[0].severity == "major" and "redundancy_type='cold'" in codes[0].suggested_fix and "power subsystem" in codes[0].detail
    p = {w.name: w.value for w in out.parameters}
    assert p["fmeca_modes"] == len(modes) and p["fmeca_single_point_failures"] >= 1 and p["fmeca_max_rpn"] == max(m["rpn"] for m in modes)
    assert p["fmeca_critical_modes"] == 1


async def test_cold_redundancy_suppresses_single_point(db_factory, study, clean_caches):  # noqa: F811
    await _seed(study, redundancy="cold")
    ctx, out = await _run(study)
    bat = next(m for m in out.series["modes"] if m["element_id"] == "bat")
    assert bat["redundant"] and not bat["single_point"] and bat["severity"] == 4
    assert not any(c.code == "FMECA_SINGLE_POINT" for c in out.conflicts)
    assert {w.name: w.value for w in out.parameters}["fmeca_critical_modes"] == 0


async def test_modes_link_allocated_functions_and_critical_list(db_factory, study, clean_caches):  # noqa: F811
    await _seed(study)
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.fmeca_closure import run_fmeca_closure
    ctx = await build_context(study)
    ctx.functions = [{"id": "F-IMG", "name": "Acquire image", "study_id": study}]
    ctx.allocations = [{"id": "A1", "function_id": "F-IMG", "element_id": "cam", "study_id": study}]
    ctx.elements_by_id["cam"]["quantity"] = 1
    out = run_fmeca_closure(ctx, critical=["Acquire image"])
    cam = next(m for m in out.series["modes"] if m["element_id"] == "cam")
    assert cam["function_ids"] == ["F-IMG"] and cam["functions"] == ["Acquire image"]
    assert cam["single_point"] and cam["critical"]
    ids = sorted(c.element_ids[0] for c in out.conflicts if c.code == "FMECA_SINGLE_POINT")
    assert ids == ["bat", "cam"]
    cam_c = next(c for c in out.conflicts if c.element_ids == ["cam"])
    assert "Acquire image" in cam_c.detail
    # the payload subsystem inherits the function of its child
    pl = [m for m in out.series["modes"] if m["element_id"] == "pl"]
    assert not pl                                       # payload has a component: no generic subsystem mode
