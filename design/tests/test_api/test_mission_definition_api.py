"""Mission definition editing (Nov 2026): PATCH /api/studies/{id}/mission, stale analyses,
the orbit every analysis reads, ground stations with their own coordinates, the link the
team chose, and the example-loader / duplicate-route fixes.

NFI is the worked case: 3U, SSO 590 km / 97.75°, LTAN 10:30, NIR + SWIR cameras,
UHF 401.5 MHz downlink at 38.4 kbit/s, four Canadian ground stations, drag sail.
"""
from __future__ import annotations

import pytest

NFI_STATIONS = [
    ("Ottawa", 45.42, -75.70), ("Waterloo", 43.47, -80.54),
    ("Timmins", 48.48, -81.33), ("Iqaluit", 63.75, -68.52),
]


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SPACECDF_DATA_DIR", str(tmp_path / "data"))
    from spacecdf_server.services import analysis_results
    analysis_results.reset_trackers()
    yield
    analysis_results.reset_trackers()


async def _study(client, **req) -> str:
    r = await client.post("/api/studies/", json={"requirements": {"name": "NFI", "spacecraft_class": "nano", **req}})
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    r = await client.post(f"/api/studies/{sid}/product-tree/default",
                          json={"architecture": "single-leo", "mission_name": "NFI", "spacecraft_class": "nano"})
    assert r.status_code == 200, r.text
    return sid


async def _stale(client, sid) -> dict[str, bool]:
    r = await client.get(f"/api/studies/{sid}/analyses")
    assert r.status_code == 200, r.text
    return {x["analysis"]: x["stale"] for x in r.json()}


# ── PATCH /api/studies/{id}/mission ─────────────────────────────────────

async def test_patch_mission_updates_and_persists(client, db_factory):
    sid = await _study(client)
    body = {
        "spacecraft_class": "nano", "design_lifetime_years": 3, "target_mass_kg": 4.5,
        "orbit": {"orbit_type": "sso", "altitude_km": 590, "inclination_deg": 97.75, "ltan": "10:30"},
        "payloads": [{"name": "NIR + SWIR cameras", "mass_kg": 0.9, "power_w": 8, "power_peak_w": 12,
                      "data_rate_mbps": 5, "gsd_m": 60, "swath_km": 150, "wavelengths_nm": [865, 1610],
                      "data_per_image_mb": 32}],
        "link": {"band": "UHF", "downlink_frequency_mhz": 401.5, "uplink_frequency_mhz": 450.0,
                 "downlink_rate_bps": 38400},
        "launch_vehicle": "SSO rideshare, 3U deployer", "disposal_method": "drag_sail",
        "mission_need": {"problem_statement": "Detect active wildfire fronts in northern Ontario",
                         "objectives": [{"id": "O1", "text": "image fire fronts at 60 m GSD", "priority": "primary"}]},
    }
    r = await client.patch(f"/api/studies/{sid}/mission", json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["warnings"] == []
    assert "requirements.orbit.altitude_km" in out["changed"] and "mission_need.problem_statement" in out["changed"]
    o = out["requirements"]["orbit"]
    assert (o["altitude_km"], o["inclination_deg"], o["ltan"]) == (590.0, 97.75, "10:30")
    assert o["deorbit_required"] is True and o["mission_duration_years"] == 3
    p = out["requirements"]["payloads"][0]
    assert (p["gsd_m"], p["swath_km"], p["wavelengths_nm"], p["power_peak_w"]) == (60, 150, [865, 1610], 12)
    assert out["requirements"]["link"]["downlink_rate_bps"] == 38400
    assert out["requirements"]["disposal_method"] == "drag_sail"

    study = (await client.get(f"/api/studies/{sid}")).json()
    assert study["requirements"]["orbit"]["altitude_km"] == 590
    assert study["mission_need"]["objectives"][0]["text"] == "image fire fronts at 60 m GSD"
    # persisted, not only in the cache
    from spacecdf_server.db.study_repo import db_load_all_studies
    stored = (await db_load_all_studies())[sid]
    assert stored.requirements.orbit.altitude_km == 590 and stored.requirements.payloads[0].gsd_m == 60


async def test_patch_mission_sso_inclination_auto_and_warnings(client, db_factory):
    from spacecdf_common.physics.orbit import sso_inclination
    sid = await _study(client)
    r = await client.patch(f"/api/studies/{sid}/mission", json={"orbit": {"altitude_km": 590}})
    assert r.status_code == 200, r.text
    assert r.json()["requirements"]["orbit"]["inclination_deg"] == pytest.approx(sso_inclination(590), abs=0.01)
    # an explicit, non-SSO inclination is kept but flagged
    r = await client.patch(f"/api/studies/{sid}/mission", json={"orbit": {"inclination_deg": 51.6}})
    assert r.status_code == 200
    assert r.json()["requirements"]["orbit"]["inclination_deg"] == 51.6
    assert any("not sun-synchronous" in w for w in r.json()["warnings"])


@pytest.mark.parametrize("body", [
    {"orbit": {"altitude_km": 50000}},                 # not an SSO altitude
    {"orbit": {"ltan": "25:00"}},
    {"orbit": {"inclination_deg": 200}},
    {"spacecraft_class": "jumbo"},
    {"design_lifetime_years": 0},
    {"payloads": [{"name": "x", "mass_kg": -1}]},
    {"link": {"downlink_rate_bps": -5}},
    {"link": {"nonsense": 1}},
    {"mission_need": {"objectives": [{"text": "x", "priority": "urgent"}]}},
])
async def test_patch_mission_rejects_invalid_and_changes_nothing(client, db_factory, body):
    sid = await _study(client)
    before = (await client.get(f"/api/studies/{sid}")).json()
    r = await client.patch(f"/api/studies/{sid}/mission", json=body)
    assert r.status_code == 422, r.text
    assert (await client.get(f"/api/studies/{sid}")).json()["requirements"] == before["requirements"]


async def test_patch_mission_unknown_study(client, db_factory):
    assert (await client.patch("/api/studies/nope/mission", json={"name": "x"})).status_code == 404


# ── stale marking + analyses read the edited orbit ──────────────────────

async def test_edit_marks_runs_stale_and_orbit_feeds_the_analyses(client, db_factory):
    from spacecdf_server.services.analysis_context import build_context
    sid = await _study(client)
    r = await client.post(f"/api/design/{sid}/run")
    assert r.status_code == 200, r.text
    p500 = r.json()["parameters"]
    assert p500["orbit.altitude_km"]["value"] == 500
    assert await _stale(client, sid) == {"design_loop": False}

    # a label-only change is not an input
    r = await client.patch(f"/api/studies/{sid}/mission", json={"name": "NFI-1"})
    assert r.status_code == 200 and r.json()["stale_analyses"] == []

    r = await client.patch(f"/api/studies/{sid}/mission", json={"orbit": {"altitude_km": 590}})
    assert r.status_code == 200
    assert r.json()["stale_analyses"] == ["design_loop"]
    assert await _stale(client, sid) == {"design_loop": True}

    # the analysis context uses the new orbit at once (the old run's period is not reused)
    ctx = await build_context(sid)
    assert ctx.orbit["altitude_km"] == 590
    assert ctx.orbit["period_s"] > p500["orbit.period_s"]["value"] + 60

    r = await client.post(f"/api/design/{sid}/run")
    p590 = r.json()["parameters"]
    assert p590["orbit.altitude_km"]["value"] == 590
    assert p590["orbit.period_s"]["value"] > p500["orbit.period_s"]["value"] + 60       # ~94.5 -> ~96.3 min
    assert p590["orbit.eclipse_fraction"]["value"] != pytest.approx(p500["orbit.eclipse_fraction"]["value"], abs=1e-4)
    assert await _stale(client, sid) == {"design_loop": False}

    # payload / lifetime edits are inputs too
    r = await client.patch(f"/api/studies/{sid}/mission", json={"design_lifetime_years": 5})
    assert r.json()["stale_analyses"] == ["design_loop"]


async def test_mission_simulation_goes_stale_on_orbit_edit(client, db_factory):
    sid = await _study(client)
    r = await client.post(f"/api/studies/{sid}/analyses/mission_simulation/run?n_orbits=2")
    assert r.status_code == 200, r.text
    assert (await _stale(client, sid))["mission_simulation"] is False
    await client.patch(f"/api/studies/{sid}/mission", json={"orbit": {"ltan": "10:30"}})
    assert (await _stale(client, sid))["mission_simulation"] is True


# ── ground stations with real coordinates ───────────────────────────────

async def _add_nfi_stations(client, sid):
    for name, lat, lon in NFI_STATIONS:
        r = await client.post(f"/api/studies/{sid}/ground-stations",
                              json={"name": name, "lat": lat, "lon": lon, "bands": ["UHF"], "antenna_m": 2.0})
        assert r.status_code == 200, r.text
        assert r.json()["custom"] is True and r.json()["lat"] == lat


async def test_own_ground_stations_use_their_coordinates(client, db_factory):
    sid = await _study(client)
    await client.patch(f"/api/studies/{sid}/mission", json={"orbit": {"altitude_km": 590, "inclination_deg": 97.75}})
    await _add_nfi_stations(client, sid)
    sel = (await client.get(f"/api/studies/{sid}/ground-stations")).json()["selected"]
    assert sorted((s["name"], s["lat"], s["lon"]) for s in sel) == sorted(NFI_STATIONS)

    # bad input
    assert (await client.post(f"/api/studies/{sid}/ground-stations", json={"name": "No coords"})).status_code == 422
    assert (await client.post(f"/api/studies/{sid}/ground-stations",
                              json={"name": "Ottawa", "lat": 45.4, "lon": -75.7})).status_code == 409
    assert (await client.post(f"/api/studies/{sid}/ground-stations",
                              json={"name": "Pole+", "lat": 95, "lon": 0})).status_code == 422

    # pass predictions: each station at its own latitude (was 78° for all)
    passes = (await client.get(f"/api/lifecycle/ground/passes/{sid}")).json()
    by = {s["station"]: s for s in passes["stations"]}
    assert {n: by[n]["latitude_deg"] for n, *_ in NFI_STATIONS} == {n: lat for n, lat, _ in NFI_STATIONS}
    assert by["Iqaluit"]["passes_per_day"] > by["Waterloo"]["passes_per_day"]
    assert by["Iqaluit"]["total_contact_min_per_day"] > by["Ottawa"]["total_contact_min_per_day"]

    # the ground-segment closure sees the four stations at their coordinates
    r = await client.post(f"/api/studies/{sid}/analyses/ground_segment/run")
    assert r.status_code == 200, r.text
    rows = {s["name"]: s for s in r.json()["summary"]["stations"]}
    assert set(rows) == {n for n, *_ in NFI_STATIONS}
    assert rows["Iqaluit"]["lat"] == 63.75 and rows["Timmins"]["lon"] == -81.33

    # moving a station makes the closure stale
    ott = next(s for s in sel if s["name"] == "Ottawa")
    r = await client.patch(f"/api/elements/{ott['element_id']}",
                           json={"performance": {"lat": 45.5, "lon": -75.7, "bands": ["UHF"]}, "version": ott["version"]})
    assert r.status_code == 200, r.text
    assert (await _stale(client, sid))["ground_segment"] is True


async def test_passes_report_unknown_station_names(client, db_factory):
    sid = await _study(client, ground_stations=["Nowhere-ville"])
    out = (await client.get(f"/api/lifecycle/ground/passes/{sid}")).json()
    assert out["stations"] == [] and out["unresolved_stations"] == ["Nowhere-ville"]


# ── link chosen by the team (mission editor / link-budget "Apply to Design") ─

async def test_link_definition_feeds_ground_closure_and_design_loop(client, db_factory):
    sid = await _study(client)
    await _add_nfi_stations(client, sid)
    r = await client.patch(f"/api/studies/{sid}/mission", json={"link": {
        "downlink_frequency_mhz": 401.5, "downlink_rate_bps": 38400, "tx_power_w": 1.0,
        "tx_antenna_gain_dbi": 0.0, "source": "link_budget_tool"}})
    assert r.status_code == 200, r.text
    r = await client.post(f"/api/studies/{sid}/analyses/ground_segment/run")
    s = r.json()["summary"]
    assert s["band"] == "UHF" and s["downlink_rate_mbps"] == pytest.approx(0.0384)
    assert s["gs_station_count"] == 4

    r = await client.post(f"/api/design/{sid}/run")
    assert r.json()["parameters"]["link.downlink_rate_bps"]["value"] == pytest.approx(38400, rel=0.25)


# ── orbit trade carries the study's orbit; example loader; duplicate route ──

async def test_orbit_trade_lists_the_current_orbit(client, db_factory):
    sid = await _study(client)
    await client.patch(f"/api/studies/{sid}/mission", json={"orbit": {"altitude_km": 590}})
    cands = (await client.get(f"/api/lifecycle/orbit-trade/{sid}")).json()["candidates"]
    cur = [c for c in cands if c["is_current"]]
    assert len(cur) == 1 and cur[0]["altitude_km"] == 590


async def test_example_unknown_category_is_kept_with_a_warning(client, db_factory, monkeypatch):
    from spacecdf_server.routers import lifecycle
    mission = {
        "name": "Sail demo", "requirements": {"name": "Sail demo"}, "mission_need": {},
        "selected_equipment": [
            {"category": "drag_sails", "componentId": "x-sail", "name": "Drag sail", "mass_kg": 0.3, "power_w": 0.1},
            {"category": "cameras", "componentId": "x-cam", "name": "SWIR camera", "mass_kg": 0.4, "power_w": 4},
        ],
    }
    monkeypatch.setattr(lifecycle, "get_example_mission", lambda mid: mission if mid == "sail" else None)
    r = await client.post("/api/lifecycle/example-missions/sail/load")
    assert r.status_code == 200, r.text
    out = r.json()
    assert len(out["warnings"]) == 1 and "drag_sails" in out["warnings"][0]
    els = (await client.get(f"/api/studies/{out['id']}/elements")).json()
    by_name = {e["name"]: e for e in els}
    sail = by_name["Drag sail"]
    assert by_name[next(e["name"] for e in els if e["id"] == sail["parent_id"])]["name"] == "Other equipment"
    assert by_name["SWIR camera"]["subsystem_domain"] == "payload"


def test_equipment_needs_route_registered_once():
    from spacecdf_server.routers import engineering
    hits = [r for r in engineering.router.routes if getattr(r, "path", "") == "/equipment/needs/{study_id}"]
    assert len(hits) == 1


async def test_equipment_needs_reads_the_mission_definition(client, db_factory):
    sid = await _study(client)
    r = await client.get(f"/api/engineering/equipment/needs/{sid}")
    assert r.status_code == 200, r.text
    assert r.json()["study_id"] == sid and r.json()["needs"]
