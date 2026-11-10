"""SCDF-174 — ground segment closure: parameters on the mission root from two
selected stations, GS_NO_STATIONS when the study has none and the catalogue
is empty, GS_DATA_DEFICIT with a concrete fix when the payload rate is raised,
a station whose link does not close is excluded."""
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


async def _seed(study_id: str, *, stations: bool = True, payload_bps: float = 0.2e6) -> None:
    await _el(study_id, "mission", "Mission", "mission")
    await _el(study_id, "space", "Space Segment", "segment", "mission")
    await _el(study_id, "sc", "Spacecraft", "system", "space")
    await _el(study_id, "ttc", "TT&C", "subsystem", "sc", "ttc", mass_kg=0.5, power_avg_w=1.0,
              performance_json={"frequency_band": "X-band", "tx_power_w": 5.0, "gain_dbi": 10.0, "data_rate_bps": 20e6})
    await _el(study_id, "pl", "Camera", "subsystem", "sc", "payload", mass_kg=1.0, power_avg_w=4.0,
              performance_json={"data_rate_bps": payload_bps, "duty_cycle_percent": 50.0})
    await _el(study_id, "ground", "Ground Segment", "segment", "mission", segment="ground")
    if stations:
        await _el(study_id, "gs-sval", "SvalSat", "component", "ground", "ground", segment="ground", kb_component_id="svalbard")
        await _el(study_id, "gs-kir", "Kiruna", "component", "ground", "ground", segment="ground", kb_component_id="kiruna")


async def _run(study_id):
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.ground_closure import run_ground_segment
    ctx = await build_context(study_id)
    return ctx, await run_ground_segment(ctx)


async def test_two_stations_close_the_data_loop(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.analysis_results import ResultsSink
    from spacecdf_server.services.ground_closure import OUTPUT_PARAMETERS

    await _seed(study)
    ctx, out = await _run(study)
    assert [s["id"] for s in ctx.ground_stations] == ["svalbard", "kiruna"]
    assert [p.name for p in out.parameters] == list(OUTPUT_PARAMETERS)
    s = out.summary
    assert s["gs_station_count"] == 2 and s["gs_contacts_per_day"] > 0 and s["gs_contact_min_per_day"] > 30
    # 0.2 Mbps x 50 % duty = 1.08 GB/day; two polar stations at 20 Mbps return it all
    assert abs(s["gs_data_generated_gb_per_day"] - 1.08) < 1e-3
    assert s["gs_data_return_gb_per_day"] >= s["gs_data_generated_gb_per_day"] - 0.02
    assert s["gs_backlog_end_gb"] < 0.1 and s["closure_pct"] > 95 and abs(s["backlog_growth_gb_per_day"]) < 0.02  # real (J2) passes: day-to-day jitter
    assert s["gs_min_link_margin_db"] > 3 and s["band"] == "X" and s["frequency_ghz"] == 8.2
    assert not any(c.code in ("GS_DATA_DEFICIT", "GS_NO_STATIONS", "GS_STATION_EXCLUDED") for c in out.conflicts)
    rows = {r["station_id"]: r for r in s["stations"]}
    assert rows["svalbard"]["status"] == "ok" and rows["svalbard"]["element_id"] == "gs-sval"
    assert rows["kiruna"]["contacts_per_day"] > 0 and rows["kiruna"]["margin_db"] > 3
    # series: contact windows + a 24 h buffer trace
    assert out.series["contacts"] and {c["station_id"] for c in out.series["contacts"]} == {"svalbard", "kiruna"}
    assert all(0 <= c["start_s"] < c["end_s"] <= 86400 for c in out.series["contacts"])
    assert out.series["buffer"]["t_s"][0] == 0 and out.series["buffer"]["t_s"][-1] == 86400
    assert len(out.series["buffer"]["gb"]) == len(out.series["buffer"]["t_s"])
    assert out.series["inputs"]["sources"]["tx_power"] == "ttc element"

    res = await ResultsSink().publish(study, "ground_segment", parameters=out.parameters, conflicts=out.conflicts, ctx=ctx)
    assert [w["name"] for w in res.written] == list(OUTPUT_PARAMETERS)
    assert all(w["element_id"] == "mission" for w in res.written)
    fresh = await build_context(study)
    assert fresh.params["mission"]["gs_contact_min_per_day"].value == s["gs_contact_min_per_day"]
    assert fresh.resolve("el:Mission.gs_station_count") == 2.0


async def test_no_stations_falls_back_to_catalogue_then_conflicts(db_factory, study, clean_caches):  # noqa: F811
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.ground_closure import run_ground_segment

    await _seed(study, stations=False)
    ctx = await build_context(study)
    assert ctx.ground_stations == []
    out = await run_ground_segment(ctx)
    # nothing selected -> the first two catalogue stations with a warning
    assert any("using catalogue defaults" in w for w in out.warnings)
    assert out.summary["gs_station_count"] == 2
    assert not any(c.code == "GS_NO_STATIONS" for c in out.conflicts)
    # ... and with an empty catalogue the closure raises GS_NO_STATIONS
    ctx.all_kb_stations = []
    out = await run_ground_segment(ctx)
    codes = {c.code: c for c in out.conflicts}
    assert "GS_NO_STATIONS" in codes and codes["GS_NO_STATIONS"].severity == "major"
    assert codes["GS_NO_STATIONS"].element_ids == ["mission"]
    assert out.summary["gs_station_count"] == 0 and out.summary["gs_data_return_gb_per_day"] == 0


async def test_raised_payload_rate_gives_deficit_with_fix(db_factory, study, clean_caches):  # noqa: F811
    await _seed(study, payload_bps=200e6)          # 100 MB/s x 50 % -> 1080 GB/day
    _ctx, out = await _run(study)
    codes = {c.code: c for c in out.conflicts}
    assert "GS_DATA_DEFICIT" in codes
    c = codes["GS_DATA_DEFICIT"]
    assert c.severity == "major" and c.element_ids == ["mission"]
    assert "min/day of contact" in c.suggested_fix and "raise the downlink rate to" in c.suggested_fix
    assert "from the catalogue" in c.suggested_fix and "svalbard" not in c.suggested_fix.lower()
    assert out.summary["gs_data_return_gb_per_day"] < out.summary["gs_data_generated_gb_per_day"]
    assert out.summary["gs_backlog_end_gb"] > 100 and out.summary["closure_pct"] < 10


async def test_negative_margin_station_is_excluded(db_factory, study, clean_caches):  # noqa: F811
    await _seed(study)
    # a third station whose element overrides the KB G/T so the X-band link cannot close
    await _el(study, "gs-bad", "Deaf dish", "component", "ground", "ground", segment="ground",
              kb_component_id="weilheim", performance_json={"g_over_t_db_k": -40.0})
    ctx, out = await _run(study)
    assert len(ctx.ground_stations) == 3
    rows = {r["station_id"]: r for r in out.summary["stations"]}
    assert rows["weilheim"]["status"] == "excluded" and rows["weilheim"]["margin_db"] < 0
    assert "link margin" in rows["weilheim"]["reason"]
    assert rows["svalbard"]["status"] == "ok"
    assert out.summary["gs_station_count"] == 2
    assert "weilheim" not in {c["station_id"] for c in out.series["contacts"]}
    codes = {c.code: c for c in out.conflicts}
    assert "GS_STATION_EXCLUDED" in codes and codes["GS_STATION_EXCLUDED"].element_ids == ["gs-bad"]
    assert codes["GS_STATION_EXCLUDED"].severity == "warning"
    # the excluded station does not drag the minimum margin down
    assert out.summary["gs_min_link_margin_db"] > 0


async def test_band_mismatch_and_low_margin(db_factory, study, clean_caches):  # noqa: F811
    await _seed(study)
    # UHF-only station cannot receive an X-band link
    await _el(study, "gs-uhf", "UHF yagi", "component", "ground", "ground", segment="ground",
              kb_component_id="delft", performance_json={"bands": ["UHF", "VHF"]})
    _ctx, out = await _run(study)
    rows = {r["station_id"]: r for r in out.summary["stations"]}
    assert rows["delft"]["status"] == "excluded" and "no X-band" in rows["delft"]["reason"]
    # push the rate so the margin at the good stations drops under 3 dB but stays positive
    from spacecdf_server.routers import elements as er
    er._elements["ttc"]["performance_json"]["data_rate_bps"] = 35e6      # ~2.5 dB at SvalSat
    _ctx, out = await _run(study)
    rows = {r["station_id"]: r for r in out.summary["stations"]}
    low = [r for r in rows.values() if r["status"] == "low_margin"]
    assert low, rows
    assert any(c.code == "GS_LINK_MARGIN_LOW" and c.severity == "warning" for c in out.conflicts)
    assert 0 <= out.summary["gs_min_link_margin_db"] < 3
