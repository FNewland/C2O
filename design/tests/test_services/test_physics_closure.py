"""SCDF-176 — physics closure: placement (auto stack + explicit positions),
mass properties of a symmetric 3U, CG-offset conflict when a heavy component
sits off-axis, wheel saturation with a tiny capacity override, thermal
out-of-range when a component dissipates 50 W."""
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


async def _seed(study_id: str, *, cam_power: float = 2.0, cam_pos=None, bat_pos=None) -> None:
    """A symmetric 3U: four 1U-ish boards of equal mass stacked in the 100x100x300 envelope."""
    await _el(study_id, "mission", "Mission", "mission")
    await _el(study_id, "space", "Space Segment", "segment", "mission")
    await _el(study_id, "sc", "Spacecraft", "system", "space", dimensions_mm=[100, 100, 300])
    await _el(study_id, "eps", "EPS", "subsystem", "sc", "power")
    await _el(study_id, "bat", "Battery", "component", "eps", "power", mass_kg=1.0, power_avg_w=0.2,
              dimensions_mm=[90, 90, 75], performance_json={"capacity_wh": 40.0}, position_json=bat_pos)
    await _el(study_id, "pcdu", "PCDU", "component", "eps", "power", mass_kg=1.0, power_avg_w=1.0, dimensions_mm=[90, 90, 75])
    await _el(study_id, "aocs", "AOCS", "subsystem", "sc", "aocs")
    await _el(study_id, "rw", "Reaction wheel", "component", "aocs", "aocs", mass_kg=1.0, power_avg_w=1.0,
              dimensions_mm=[90, 90, 75], performance_json={"momentum_nms": 0.011})
    await _el(study_id, "pl", "Payload", "subsystem", "sc", "payload")
    await _el(study_id, "cam", "Camera", "component", "pl", "payload", mass_kg=1.0, power_avg_w=cam_power,
              dimensions_mm=[90, 90, 75], position_json=cam_pos,
              performance_json={"op_temp_min_c": -25.0, "op_temp_max_c": 40.0})
    await _el(study_id, "ttc", "TT&C", "subsystem", "sc", "ttc", mass_kg=0.0, power_avg_w=0.3)


async def _ctx(study_id):
    from spacecdf_server.services.analysis_context import build_context
    return await build_context(study_id)


async def test_auto_placement_stacks_along_z(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.physics_closure import place_elements
    await _seed(study)
    pl = place_elements(await _ctx(study))
    assert pl.envelope_m == (0.1, 0.1, 0.3) and "Spacecraft" in pl.envelope_source
    assert sorted(pl.auto_placed) == ["bat", "cam", "pcdu", "rw"]
    zs = sorted(pl.positions[i][2] for i in ("bat", "pcdu", "rw", "cam"))
    assert zs == pytest.approx([0.0375, 0.1125, 0.1875, 0.2625])          # 4 x 75 mm boards, centred
    assert all(pl.positions[i][:2] == [0.05, 0.05] for i in pl.positions)
    assert any("auto-placed" in w for w in pl.warnings)
    assert not any("exceeds the envelope" in w for w in pl.warnings)


async def test_explicit_position_is_kept(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.physics_closure import place_elements
    await _seed(study, cam_pos=[0.05, 0.05, 0.26])
    pl = place_elements(await _ctx(study))
    assert pl.positions["cam"] == [0.05, 0.05, 0.26]
    assert "cam" not in pl.auto_placed and len(pl.auto_placed) == 3
    item = next(i for i in pl.items if i.element_id == "cam")
    assert item.source == "explicit" and item.dims_m == (0.09, 0.09, 0.075)


async def test_symmetric_3u_mass_properties(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.physics_closure import run_mass_properties
    await _seed(study)
    mp = run_mass_properties(await _ctx(study))
    r = mp.result
    assert r.total_mass_kg == 4.0
    assert (r.com_x_m, r.com_y_m, r.com_z_m) == pytest.approx((0.05, 0.05, 0.15), abs=1e-4)
    assert mp.cp_cg_offset_m == pytest.approx(0.0, abs=1e-4)
    # stacked boards: Izz small (about the stack axis), Ixx == Iyy, and a 4 kg x 0.3 m body gives ~0.03 kg m2
    assert r.ixx == pytest.approx(r.iyy, rel=1e-6)
    assert 0.02 < r.ixx < 0.05 and r.izz < r.ixx
    assert abs(r.ixy) < 1e-9 and abs(r.ixz) < 1e-9
    names = [p.name for p in mp.parameters]
    assert names[:4] == ["mp_total_mass_kg", "mp_com_x_m", "mp_com_y_m", "mp_com_z_m"]
    assert {p.name: p.value for p in mp.parameters}["mp_auto_placed_count"] == 4
    assert not mp.conflicts


async def test_off_axis_heavy_component_raises_cg_offset_warning(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.physics_closure import run_mass_properties
    await _seed(study, bat_pos=[0.05, 0.05, 0.02])
    # make the battery heavy and low in the stack while the other three boards are auto-stacked from z=0
    from spacecdf_server.routers import elements as er
    er._elements["bat"]["mass_kg"] = 6.0
    mp = run_mass_properties(await _ctx(study))
    assert mp.cp_cg_offset_m > 0.02 * 0.3
    codes = {c.code: c for c in mp.conflicts}
    assert "AOCS_CG_OFFSET_HIGH" in codes
    c = codes["AOCS_CG_OFFSET_HIGH"]
    assert c.severity == "warning" and c.element_ids == ["bat"] and "position" in c.suggested_fix


async def test_wheel_saturation_with_tiny_capacity(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.physics_closure import run_aocs_closure, run_mass_properties
    await _seed(study)
    ctx = await _ctx(study)
    mp = run_mass_properties(ctx)
    ok = run_aocs_closure(ctx, mp)
    assert ok.wheel_capacity_nms == 0.011 and "Reaction wheel" in ok.wheel_source
    assert ok.torques["rss"] > 0 and ok.torques["gravity_gradient"] > 0
    assert ok.momentum_per_orbit_nms < 0.011 and ok.wheel_margin_pct > 0
    assert not any(c.code == "AOCS_WHEEL_SATURATION" for c in ok.conflicts)
    # override the capacity on the mission root -> saturation
    from spacecdf_server.db.parameter_repo import upsert_element_parameter
    await upsert_element_parameter({"study_id": study, "element_id": "mission", "definition_name": "aocs_wheel_capacity_nms",
                                    "manual_value": 1e-6, "value_switch": "manual"})
    ctx = await _ctx(study)
    sat = run_aocs_closure(ctx, run_mass_properties(ctx))
    assert sat.wheel_capacity_nms == 1e-6 and sat.wheel_margin_pct < 0
    codes = {c.code: c for c in sat.conflicts}
    assert "AOCS_WHEEL_SATURATION" in codes
    c = codes["AOCS_WHEEL_SATURATION"]
    assert c.severity == "major" and "N m s" in c.suggested_fix and ("KB:" in c.suggested_fix or "desaturate" in c.suggested_fix)
    names = {p.name for p in sat.parameters}
    assert {"aocs_disturbance_torque_nm", "aocs_gg_torque_nm", "aocs_aero_torque_nm", "aocs_srp_torque_nm", "aocs_mag_torque_nm",
            "aocs_momentum_per_orbit_nms", "aocs_wheel_capacity_nms", "aocs_wheel_margin_pct", "aocs_pointing_est_deg"} <= names


async def test_pointing_requirement_from_threshold_path(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.physics_closure import run_aocs_closure, run_mass_properties
    from spacecdf_server.routers import requirements as rr
    await _seed(study)
    rr._requirements["R-PT"] = {"id": "R-PT", "study_id": study, "text": "pointing", "level": "system", "status": "approved",
                                "threshold_param_path": "aocs.pointing_accuracy_deg", "threshold_op": "<=", "threshold_value": "0.001"}
    ctx = await _ctx(study)
    out = run_aocs_closure(ctx, run_mass_properties(ctx))
    assert out.pointing_req_deg == 0.001 and "R-PT" in out.pointing_req_source
    assert out.pointing_margin_deg is not None and out.pointing_margin_deg < 0
    c = next(c for c in out.conflicts if c.code == "AOCS_POINTING_MARGIN")
    assert c.severity == "major" and c.requirement_ids == ["R-PT"]


async def test_thermal_out_of_range_for_50w_component(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.physics_closure import run_thermal_closure
    await _seed(study)
    th = run_thermal_closure(await _ctx(study))
    kinds = {n.element_id: n.kind for n in th.nodes}
    assert kinds["sc"] == "structure" and kinds["eps"] == "subsystem" and kinds["cam"] == "component"   # 2 W camera is its own node
    assert "bat" not in kinds                                              # 0.2 W stays inside the EPS node
    assert "pl" not in kinds and "aocs" not in kinds                       # empty shells: their only component mounts on the chassis
    assert {"a": "chassis", "b": "cam", "w_per_k": 0.5} in th.conductances
    assert th.worst_margin_c is not None and th.worst_margin_c > 0 and not th.conflicts
    assert len(th.transient["t_s"]) <= 601 and len(th.transient["nodes"]) == len(th.nodes)
    eps_node = next(n for n in th.nodes if n.element_id == "eps")
    assert (eps_node.allow_min_c, eps_node.allow_max_c, eps_node.allow_source) == (-20.0, 50.0, "class default")
    cam_node = next(n for n in th.nodes if n.element_id == "cam")
    assert (cam_node.allow_min_c, cam_node.allow_max_c, cam_node.allow_source) == (-25.0, 40.0, "performance")
    assert -40 < cam_node.t_cold_c < cam_node.t_hot_c < 45          # a 3U at 500 km: roughly -20..+35 degC

    from spacecdf_server.routers import elements as er
    er._elements["cam"]["power_avg_w"] = 50.0
    th = run_thermal_closure(await _ctx(study))
    cam = next(n for n in th.nodes if n.element_id == "cam")
    assert cam.dissipation_hot_w == 50.0 and cam.t_hot_c > cam.allow_max_c
    codes = [c for c in th.conflicts if c.code == "THERMAL_OUT_OF_RANGE"]
    assert any(c.element_ids == ["cam"] and c.severity == "major" and "radiator" in c.suggested_fix for c in codes)
    per_el = {(p.element_id, p.name): p.value for p in th.parameters if p.element_id}
    assert per_el[("cam", "thermal_margin_hot_c")] < 0
    assert th.worst_margin_c < 0


async def test_run_physics_publishes_everything(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.analysis_results import ResultsSink
    from spacecdf_server.services.physics_closure import run_physics
    await _seed(study)
    ctx = await _ctx(study)
    out = await run_physics(ctx)
    assert set(out.series) == {"analysis", "placement", "mass_properties", "aocs", "thermal"}
    assert out.summary["mp_total_mass_kg"] == 4.0 and out.summary["thermal_nodes"] == len(out.series["thermal"]["nodes"])
    res = await ResultsSink().publish(study, "physics", parameters=out.parameters, conflicts=out.conflicts, ctx=ctx)
    fresh = await build_context(study)
    assert fresh.params["mission"]["mp_total_mass_kg"].value == 4.0
    assert fresh.params["cam"]["thermal_t_hot_c"].value == out.series["thermal"]["nodes"][-1]["t_hot_c"] or \
        any(p.name == "thermal_t_hot_c" for p in fresh.params["cam"].values())
    assert not res.skipped
