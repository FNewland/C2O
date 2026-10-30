"""SCDF-173 — mission simulation closure: parameters on the mission root, a
shrunken battery raises a critical SoC conflict with a concrete fix, a study
without modes gets derived modes + a warning, series stay bounded."""
from __future__ import annotations

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


async def _seed(study_id: str, *, with_modes: bool = True, capacity_wh: float = 40.0) -> None:
    await _el(study_id, "mission", "Mission", "mission")
    await _el(study_id, "space", "Space Segment", "segment", "mission")
    await _el(study_id, "sc", "Spacecraft", "system", "space")
    await _el(study_id, "eps", "EPS", "subsystem", "sc", "power")
    await _el(study_id, "bat", "Battery", "component", "eps", "power", mass_kg=1.0, power_avg_w=0.2,
              performance_json={"capacity_wh": capacity_wh})
    await _el(study_id, "sa", "Solar array", "component", "eps", "power", mass_kg=0.8, power_avg_w=0.0,
              performance_json={"sa_power_eol_w": 16.0})
    await _el(study_id, "pcdu", "PCDU", "component", "eps", "power", mass_kg=0.5, power_avg_w=1.0)
    await _el(study_id, "aocs", "AOCS", "subsystem", "sc", "aocs", mass_kg=2.0, power_avg_w=3.0)
    await _el(study_id, "ttc", "TT&C", "subsystem", "sc", "ttc", mass_kg=0.5, power_avg_w=1.0, power_peak_w=6.0)
    await _el(study_id, "pl", "Camera", "subsystem", "sc", "payload", mass_kg=1.0, power_avg_w=4.0,
              performance_json={"data_rate_bps": 2e6})
    await _el(study_id, "ground", "Ground Segment", "segment", "mission", segment="ground")
    await _el(study_id, "gs", "Svalbard", "system", "ground", segment="ground", kb_component_id="svalbard")
    if with_modes:
        await _el(study_id, "ops", "Operations", "segment", "mission", segment="operations")
        await _el(study_id, "m-nom", "Nominal", "mode", "ops", segment="operations",
                  description="guard: soc < 25 -> Safe", performance_json={"data_rate_bps": 2e6})
        await _el(study_id, "m-safe", "Safe", "mode", "ops", segment="operations")
        await _el(study_id, "m-dl", "Downlink", "mode", "ops", segment="operations",
                  performance_json={"data_rate_bps": 20e6})
        from spacecdf_server.routers import elements as er
        for mid, members in {"m-nom": ["aocs", "pcdu", "bat", "pl"], "m-safe": ["pcdu", "bat"],
                             "m-dl": ["aocs", "pcdu", "bat", "ttc"]}.items():
            for eid in members:
                er._mode_elements.append({"mode_id": mid, "element_id": eid, "is_active": True,
                                          "power_w_in_mode": 6.0 if (mid == "m-dl" and eid == "ttc") else None,
                                          "duty_cycle_percent": 100.0})


async def _run(study_id, **kw):
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.mission_simulation import run_mission_simulation
    ctx = await build_context(study_id)
    return ctx, await run_mission_simulation(ctx, **kw)


async def test_parameters_written_on_mission_root(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.analysis_results import ResultsSink
    from spacecdf_server.services.mission_simulation import OUTPUT_PARAMETERS

    await _seed(study)
    ctx, out = await _run(study, n_orbits=3)
    assert {m.name for m in ctx.modes} == {"Nominal", "Safe", "Downlink"}
    assert [p.name for p in out.parameters] == list(OUTPUT_PARAMETERS)
    assert out.summary["n_orbits"] == 3 and out.summary["modes"] == ["Nominal", "Safe", "Downlink"]
    # 16 W EOL against ~8 W nominal: healthy
    assert not any(c.code in ("SIM_SOC_BELOW_MIN", "SIM_ENERGY_NEGATIVE") for c in out.conflicts)
    assert out.summary["sim_min_soc_pct"] > 25 and out.summary["sim_energy_balance_wh_per_orbit"] > 0
    assert out.summary["sim_time_in_safe_pct"] == 0
    assert out.series["inputs"]["guards"] == ["soc < 25 -> Safe"]     # from the mode note
    assert out.series["inputs"]["battery_capacity_wh"] == 40.0 and out.series["inputs"]["sa_power_eol_w"] == 16.0
    assert "Downlink" in out.series["mode"] and out.series["mode"][0] == "Downlink"   # contact at orbit start
    assert max(out.series["p_gen_w"]) == 16.0 and min(out.series["p_gen_w"]) == 0.0

    res = await ResultsSink().publish(study, "mission_simulation", parameters=out.parameters,
                                      conflicts=out.conflicts, ctx=ctx)
    assert [w["name"] for w in res.written] == list(OUTPUT_PARAMETERS)
    assert all(w["element_id"] == "mission" for w in res.written)
    fresh = await build_context(study)
    assert fresh.params["mission"]["sim_min_soc_pct"].value == out.summary["sim_min_soc_pct"]
    assert fresh.params["mission"]["sim_orbits"].value == 3.0
    assert fresh.resolve("el:Mission.sim_time_in_safe_pct") is not None


async def test_shrunken_battery_raises_critical_soc_conflict(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.db.parameter_repo import upsert_element_parameter
    from spacecdf_server.services.analysis_context import build_context

    await _seed(study)
    # manual override on the battery capacity parameter feeds power.battery_capacity_wh via the KB/perf path
    await upsert_element_parameter({"study_id": study, "element_id": "bat", "definition_name": "capacity_wh",
                                    "manual_value": 1.0, "value_switch": "manual"})
    ctx = await build_context(study)
    assert ctx.power["battery_capacity_wh"] == 40.0        # the context projects the column, not the typed override
    from spacecdf_server.services.mission_simulation import run_mission_simulation
    out = await run_mission_simulation(ctx, n_orbits=3)
    assert out.series["inputs"]["battery_capacity_wh"] == 1.0   # ... the closure honours the override
    codes = {c.code: c for c in out.conflicts}
    assert "SIM_SOC_BELOW_MIN" in codes
    c = codes["SIM_SOC_BELOW_MIN"]
    assert c.severity == "critical" and c.element_ids == ["bat"]
    assert "raise battery capacity to" in c.suggested_fix and "Wh" in c.suggested_fix
    assert "orbit" in c.detail and "mode" in c.detail
    assert out.summary["sim_min_soc_pct"] < 20
    # the guard drops it into Safe -> time in safe reported (and warned when > 10 %)
    assert out.summary["sim_time_in_safe_pct"] > 0
    assert any(c.code == "SIM_SAFE_TIME" for c in out.conflicts) == (out.summary["sim_time_in_safe_pct"] > 10)


async def test_no_modes_derives_defaults_with_warning(db_factory, study, clean_caches):  # noqa: F811
    await _seed(study, with_modes=False)
    ctx, out = await _run(study, n_orbits=2)
    assert all(m.source == "default" for m in ctx.modes)           # context fell back to the executor defaults
    assert out.summary["modes"] == ["Nominal", "Safe", "Downlink"]  # ... which we replace by derived modes
    assert any("no operational modes" in w for w in out.warnings)
    by = {m["name"]: m for m in out.series["modes"]}
    platform = 0.2 + 0.0 + 1.0 + 3.0 + 1.0            # bat + sa + pcdu + aocs + ttc
    assert by["Safe"]["power_w"] == pytest.approx(platform * 0.6, abs=1e-6)
    assert by["Nominal"]["power_w"] == pytest.approx(platform + 4.0, abs=1e-6)
    assert by["Downlink"]["power_w"] == pytest.approx(platform + 4.0 + 6.0, abs=1e-6)
    assert by["Nominal"]["payload_active"] and by["Nominal"]["data_rate_bps"] == 2e6
    assert [p.name for p in out.parameters][:2] == ["sim_min_soc_pct", "sim_max_dod_pct"]


async def test_series_bounded_and_energy_conflict(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.routers import elements as er

    await _seed(study)
    er._elements["sa"]["performance_json"] = {"sa_power_eol_w": 2.0}     # starve the array
    ctx, out = await _run(study, n_orbits=60, dt_s=10)
    n = len(out.series["t_s"])
    assert n <= 2000
    for k in ("mode", "soc_pct", "p_gen_w", "p_load_w", "data_buffer_gb", "temp_c"):
        assert len(out.series[k]) == n
    assert out.series["t_s"][-1] >= 59 * ctx.orbit["period_s"]
    codes = [c.code for c in out.conflicts]
    assert "SIM_ENERGY_NEGATIVE" in codes and "SIM_SOC_BELOW_MIN" in codes
    e = next(c for c in out.conflicts if c.code == "SIM_ENERGY_NEGATIVE")
    assert e.severity == "major" and "raise SA EOL power to" in e.suggested_fix and e.element_ids == ["sa"]
    assert out.summary["sim_energy_balance_wh_per_orbit"] < 0
