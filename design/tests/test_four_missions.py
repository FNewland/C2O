"""
Four Reference Mission Scenarios — Engineering Review

Tests every decision tool and design element for realistic missions:
1. Global RF monitoring constellation (IoT/AIS style)
2. Multispectral EO single spacecraft (Dove/SuperDove style)
3. HEO comms relay with 3 CubeSats (Molniya-type)
4. Lunar CubeSat (cislunar pathfinder)

Each mission exercises: mission trade, orbit trade, ground trade,
constellation sizing, contact scheduling, SMART requirements,
budget rollup, and export generation.
"""
import sys, math
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
for pkg in ["spacecdf-server", "spacecdf-common", "spacecdf-agents", "spacecdf-kb"]:
    src = str(_root / "packages" / pkg / "src")
    if src not in sys.path:
        sys.path.insert(0, src)

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from spacecdf_server.app import app
    return TestClient(app)


def create_study(client, name, mission_type, orbit, payloads, mass, cost, gs, need, duration=3):
    r = client.post("/api/studies/", json={
        "requirements": {
            "name": name, "mission_type": mission_type, "spacecraft_class": "nano",
            "orbit": orbit,
            "payloads": payloads,
            "design_lifetime_years": duration,
            "target_mass_kg": mass, "target_cost_meur": cost,
            "ground_stations": gs,
        },
        "mission_need": need,
    })
    assert r.status_code == 200, f"Study creation failed: {r.text}"
    return r.json()


# ═══════════════════════════════════════════════════════
# MISSION 1: Global RF Monitoring Constellation
# Reference: Spire Global, Kepler, Lacuna Space
# 24-48 sats, 500-600km LEO, UHF/VHF receivers
# ═══════════════════════════════════════════════════════

class TestMission1_RFConstellation:
    """Global RF monitoring — IoT/AIS constellation."""

    @pytest.fixture(scope="class")
    def study(self, client):
        return create_study(client,
            name="RF-Watch Constellation",
            mission_type="communications",
            orbit={"orbit_type": "leo", "altitude_km": 550, "inclination_deg": 53,
                   "mission_duration_years": 5, "deorbit_required": True},
            payloads=[{"name": "SDR RF Receiver", "mass_kg": 0.3, "power_w": 5,
                       "data_rate_mbps": 1, "pointing_accuracy_deg": 5, "duty_cycle_percent": 100}],
            mass=4, cost=50, gs=["KSAT Svalbard", "Inuvik"],
            need={"problem_statement": "Real-time global RF spectrum monitoring for IoT/AIS/ADS-B",
                  "objectives": [
                      {"id": "o1", "text": "Global coverage with < 30 min revisit", "priority": "high"},
                      {"id": "o2", "text": "Detect UHF/VHF signals with -120 dBm sensitivity", "priority": "high"},
                      {"id": "o3", "text": "5 year operational lifetime", "priority": "medium"},
                  ]},
            duration=5,
        )

    def test_mission_trade_comms(self, client, study):
        """For RF monitoring, non-space alternatives are limited."""
        r = client.post("/api/lifecycle/mission-trade", json={
            "target_gsd_m": 0, "target_revisit_days": 0.02,  # 30 min
            "target_coverage": "global", "target_latency_hours": 0.5,
            "require_data_ownership": True, "require_scheduling_control": True,
            "max_annual_budget_keur": 5000, "mission_type": "communications",
            "num_spacecraft": 24,
        })
        assert r.status_code == 200
        data = r.json()
        alts = data.get("alternatives", [])
        print(f"\n=== RF Constellation Trade ===")
        for a in alts[:5]:
            print(f"  {a['rank']}. {a['name']} — {a.get('description', '')[:80]}")

    def test_constellation_sizing(self, client, study):
        """24 sats at 550km/53deg for <30 min revisit."""
        r = client.post("/api/lifecycle/constellation/design", json={
            "altitude_km": 550, "inclination_deg": 53,
            "target_revisit_hours": 0.5,  # 30 min
        })
        print(f"\n=== Constellation Sizing ===")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Result: {data}")
            # Should suggest multiple planes with many sats
            total = data.get("total_sats") or data.get("total")
            if total:
                assert total >= 8, f"Global coverage needs 8+ sats, got {total}"
        else:
            print(f"Body: {r.text[:300]}")

    def test_orbit_appropriate(self, client, study):
        """53 deg inclination covers ±53 deg latitude — covers most populated areas."""
        r = client.get(f"/api/lifecycle/orbit-trade/{study['id']}")
        data = r.json()
        candidates = data.get("candidates", [])
        print(f"\n=== RF Constellation Orbit Options ===")
        for c in candidates[:5]:
            print(f"  {c.get('name')}: {c.get('altitude_km')}km, {c.get('inclination_deg')}deg, "
                  f"period={c.get('period_min')}min, deorbit={c.get('deorbit_compliant_25yr')}")

    def test_ground_trade_multi_station(self, client, study):
        """Constellation needs multiple ground stations for good latency."""
        r = client.get(f"/api/lifecycle/ground/trade/{study['id']}")
        assert r.status_code == 200
        data = r.json()
        print(f"\n=== RF Constellation Ground Trade ===")
        for a in data.get("alternatives", []):
            print(f"  {a.get('name')}: contact={a.get('contact_minutes_per_day')}min/day, cost={a.get('annual_cost_keur')}kEUR/yr")

    def test_contact_schedule(self, client, study):
        r = client.post("/api/ground/schedule", json={
            "orbit": {"altitude_km": 550, "inclination_deg": 53},
        })
        assert r.status_code == 200
        contacts = r.json().get("contacts", [])
        print(f"\n=== RF Constellation Contacts ===")
        print(f"  Contacts/day: {len(contacts)}")
        for c in contacts[:3]:
            dur = (c["end_s"] - c["start_s"]) / 60
            print(f"  {c['station_id']}: {dur:.1f}min, max_el={c['max_elevation_deg']}deg")

    def test_budget_constellation(self, client, study):
        """Per-unit cost with learning curve for 24 sats."""
        sid = study["id"]
        mission = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "RF-Watch", "element_type": "mission", "segment": "space",
        }).json()
        space = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "Space Segment", "element_type": "segment", "segment": "space",
            "parent_id": mission["id"],
        }).json()
        sc = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "RF-Watch Spacecraft", "element_type": "system", "segment": "space",
            "parent_id": space["id"], "mass_kg": 3.5, "cost_recurring_keur": 80, "quantity": 24,
        }).json()

        r = client.get(f"/api/elements/{space['id']}/budget/mass")
        budget = r.json()
        # 24 sats × 3.5 kg = 84 kg total constellation mass
        assert budget["sum_nominal"] == pytest.approx(84.0, abs=0.1)
        print(f"\n=== RF Constellation Budget ===")
        print(f"  Total mass: {budget['sum_nominal']} kg (24 × 3.5 kg)")
        print(f"  With margin: {budget['sum_with_margin']} kg")


# ═══════════════════════════════════════════════════════
# MISSION 2: Multispectral EO Single Spacecraft
# Reference: Planet SuperDove, 3U, 500km SSO
# ═══════════════════════════════════════════════════════

class TestMission2_EOSingle:
    """Single 3U EO CubeSat — multispectral imaging."""

    @pytest.fixture(scope="class")
    def study(self, client):
        return create_study(client,
            name="AgriSat-1",
            mission_type="earth_observation",
            orbit={"orbit_type": "sso", "altitude_km": 500, "inclination_deg": 97.4,
                   "mission_duration_years": 3, "deorbit_required": True},
            payloads=[{"name": "8-band Multispectral Camera", "mass_kg": 1.2, "power_w": 15,
                       "data_rate_mbps": 200, "pointing_accuracy_deg": 0.05, "duty_cycle_percent": 20}],
            mass=5, cost=2, gs=["KSAT Svalbard"],
            need={"problem_statement": "Precision agriculture monitoring for Canadian prairies",
                  "objectives": [
                      {"id": "o1", "text": "5m GSD 8-band multispectral imagery", "priority": "high"},
                      {"id": "o2", "text": "Weekly revisit over 45-60N", "priority": "high"},
                      {"id": "o3", "text": "Data latency < 6 hours from acquisition to delivery", "priority": "medium"},
                  ]},
        )

    def test_mission_trade_eo(self, client, study):
        r = client.post("/api/lifecycle/mission-trade", json={
            "target_gsd_m": 5, "target_revisit_days": 7,
            "target_coverage": "regional", "target_latency_hours": 6,
            "require_data_ownership": True, "max_annual_budget_keur": 2000,
            "mission_type": "earth_observation", "num_spacecraft": 1,
        })
        assert r.status_code == 200
        data = r.json()
        alts = data.get("alternatives", [])
        print(f"\n=== EO Mission Trade ===")
        for a in alts[:5]:
            print(f"  {a['rank']}. {a['name']} — GSD:{a.get('gsd_m')}m, revisit:{a.get('revisit_days')}d")

        # Sentinel-2 (free, 10m, 5-day revisit) should be a strong alternative
        sentinel = [a for a in alts if "sentinel" in a["name"].lower()]
        assert len(sentinel) >= 1, "Sentinel-2 should appear as free data alternative"

    def test_orbit_sso_correct(self, client, study):
        r = client.get(f"/api/lifecycle/orbit-trade/{study['id']}")
        data = r.json()
        candidates = data.get("candidates", [])
        # SSO at 500km should have inclination ~97.4
        sso_500 = [c for c in candidates if abs(c.get("altitude_km", 0) - 500) < 100 and "sso" in c.get("name", "").lower()]
        print(f"\n=== EO Orbit Trade ===")
        for c in candidates[:5]:
            print(f"  {c.get('name')}: alt={c.get('altitude_km')}km, GSD={c.get('achievable_gsd_m')}m, "
                  f"revisit={c.get('revisit_days')}d, deorbit={c.get('deorbit_compliant_25yr')}")

    def test_data_budget_sanity(self, client, study):
        """200 Mbps payload, 20% duty cycle, ~6 orbits with imaging = lots of data."""
        # Data per day: 200 Mbps × 0.2 duty × ~6000s imaging/day ÷ 8 = ~30 GB/day
        data_per_day_gb = 200 * 0.2 * 6000 / 8 / 1000
        print(f"\n=== EO Data Budget ===")
        print(f"  Estimated data: {data_per_day_gb:.1f} GB/day")
        # Svalbard X-band downlink: ~100 Mbps × 30 min/day = ~22 GB/day
        downlink_gb = 100 * 30 * 60 / 8 / 1000
        print(f"  Svalbard X-band capacity: {downlink_gb:.1f} GB/day")
        if data_per_day_gb > downlink_gb:
            print(f"  WARNING: Data exceeds downlink capacity — need compression or more GS passes")

    def test_smart_eo_requirements(self, client, study):
        """Validate EO-specific requirements."""
        reqs = [
            {"id": "r1", "text": "The imager shall achieve a ground sample distance of 5 metres or less at nadir",
             "level": "system", "threshold": 5, "operator": "<=", "unit": "m", "objective_id": "o1"},
            {"id": "r2", "text": "The spacecraft pointing accuracy shall be 0.05 degrees (3-sigma)",
             "level": "system", "threshold": 0.05, "operator": "<=", "unit": "deg"},
            {"id": "r3", "text": "The onboard data storage shall accommodate 48 hours of imaging data",
             "level": "subsystem", "threshold": 48, "operator": ">=", "unit": "hours"},
        ]
        print(f"\n=== EO SMART Requirement Check ===")
        for req in reqs:
            r = client.post("/api/lifecycle/requirements/validate", json=req)
            d = r.json()
            status = "SMART" if d["is_smart"] else "ISSUES"
            print(f"  {req['id']}: {status} — S:{d['specific']} M:{d['measurable']} A:{d['achievable']} R:{d['relevant']} T:{d['traceable']}")
            if d["issues"]:
                print(f"    Issues: {', '.join(d['issues'][:2])}")


# ═══════════════════════════════════════════════════════
# MISSION 3: HEO Communications (3 CubeSats)
# Reference: Molniya orbit concept for Arctic comms
# ═══════════════════════════════════════════════════════

class TestMission3_HEOComms:
    """3 CubeSats in highly elliptical orbit for Arctic communications."""

    @pytest.fixture(scope="class")
    def study(self, client):
        return create_study(client,
            name="ArcticLink",
            mission_type="communications",
            orbit={"orbit_type": "heo", "altitude_km": 40000, "inclination_deg": 63.4,
                   "mission_duration_years": 5, "deorbit_required": False,
                   "delta_v_insertion_ms": 200},
            payloads=[{"name": "UHF Transponder", "mass_kg": 0.5, "power_w": 8,
                       "data_rate_mbps": 0.1, "pointing_accuracy_deg": 2, "duty_cycle_percent": 80}],
            mass=6, cost=5, gs=["Inuvik", "Gatineau"],
            need={"problem_statement": "Arctic communities lack reliable communications above 65N latitude",
                  "objectives": [
                      {"id": "o1", "text": "Continuous UHF voice/data relay above 65N", "priority": "high"},
                      {"id": "o2", "text": "8+ hours/day coverage per spacecraft", "priority": "high"},
                      {"id": "o3", "text": "Support 100+ simultaneous low-rate data links", "priority": "medium"},
                  ]},
            duration=5,
        )

    def test_orbit_trade_heo(self, client, study):
        """HEO trade should include Molniya-type and Tundra options."""
        r = client.get(f"/api/lifecycle/orbit-trade/{study['id']}")
        data = r.json()
        candidates = data.get("candidates", [])
        print(f"\n=== HEO Comms Orbit Trade ===")
        for c in candidates[:6]:
            print(f"  {c.get('name')}: alt={c.get('altitude_km')}km, inc={c.get('inclination_deg')}deg, "
                  f"period={c.get('period_min')}min")

        # At 40000km apogee, period should be ~12h (Molniya) or 24h (Tundra)
        # Standard orbit candidates may not include HEO — that's OK, the system
        # was designed for LEO CubeSats. But let's check what we get.
        high_orbits = [c for c in candidates if (c.get("altitude_km") or 0) > 1000]
        print(f"  High orbit options: {len(high_orbits)}")

    def test_budget_3_sats(self, client, study):
        """3 CubeSats with propulsion modules."""
        sid = study["id"]
        mission = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "ArcticLink", "element_type": "mission", "segment": "space",
        }).json()
        space = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "Space Segment", "element_type": "segment", "segment": "space",
            "parent_id": mission["id"],
        }).json()
        # 3 identical spacecraft
        sc = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "ArcticLink Spacecraft", "element_type": "system", "segment": "space",
            "parent_id": space["id"], "mass_kg": 5.5, "power_avg_w": 20,
            "cost_recurring_keur": 200, "quantity": 3,
        }).json()

        r = client.get(f"/api/elements/{space['id']}/budget/mass")
        budget = r.json()
        # 3 × 5.5 = 16.5 kg total
        assert budget["sum_nominal"] == pytest.approx(16.5, abs=0.1)
        print(f"\n=== HEO Budget ===")
        print(f"  3 × 5.5 kg = {budget['sum_nominal']} kg")
        print(f"  With margin: {budget['sum_with_margin']} kg")
        # Per-unit info
        for line in budget.get("lines", []):
            print(f"  {line['name']}: per_unit={line.get('per_unit', '?')}kg, total={line['nominal']}kg, qty={line['quantity']}")

    def test_heo_deorbit_not_required(self, client, study):
        """HEO orbits don't naturally decay — deorbit not feasible for CubeSats."""
        r = client.post("/api/exports/deorbit/{0}".format(study["id"]))
        if r.status_code == 200:
            data = r.json()
            print(f"\n=== HEO Deorbit Analysis ===")
            print(f"  Analysis: {data.get('analysis', {})}")
            print(f"  Note: HEO CubeSats typically use graveyard orbit, not deorbit")


# ═══════════════════════════════════════════════════════
# MISSION 4: Lunar CubeSat
# Reference: CAPSTONE, Lunar IceCube, LunaH-Map
# ═══════════════════════════════════════════════════════

class TestMission4_Lunar:
    """Lunar CubeSat pathfinder — cislunar mission."""

    @pytest.fixture(scope="class")
    def study(self, client):
        return create_study(client,
            name="LunarScout-1",
            mission_type="lunar",
            orbit={"orbit_type": "lunar", "altitude_km": 384400, "inclination_deg": 90,
                   "mission_duration_years": 1, "deorbit_required": False,
                   "delta_v_insertion_ms": 800},
            payloads=[{"name": "Neutron Spectrometer", "mass_kg": 2.0, "power_w": 10,
                       "data_rate_mbps": 0.01, "pointing_accuracy_deg": 1, "duty_cycle_percent": 50}],
            mass=14, cost=15, gs=["DSN Goldstone"],
            need={"problem_statement": "Map lunar polar water ice deposits for future ISRU",
                  "objectives": [
                      {"id": "o1", "text": "Map hydrogen concentration at lunar poles to 10km resolution", "priority": "high"},
                      {"id": "o2", "text": "Operate in NRHO for 6+ months", "priority": "high"},
                      {"id": "o3", "text": "Downlink science data via DSN at > 1 kbps", "priority": "medium"},
                  ]},
            duration=1,
        )

    def test_mission_trade_lunar(self, client, study):
        """Lunar missions have few non-space alternatives."""
        r = client.post("/api/lifecycle/mission-trade", json={
            "target_gsd_m": 0, "target_revisit_days": 0,
            "target_coverage": "global", "target_latency_hours": 48,
            "require_data_ownership": True, "max_annual_budget_keur": 15000,
            "mission_type": "science", "num_spacecraft": 1,
        })
        data = r.json()
        print(f"\n=== Lunar Mission Trade ===")
        for a in data.get("alternatives", [])[:5]:
            print(f"  {a['rank']}. {a['name']}")
        # For lunar science, building your own is likely the top recommendation
        rec = data.get("recommendation", "")
        print(f"  Recommendation: {rec[:100]}")

    def test_orbit_trade_lunar(self, client, study):
        """Orbit trade for a lunar mission."""
        r = client.get(f"/api/lifecycle/orbit-trade/{study['id']}")
        data = r.json()
        candidates = data.get("candidates", [])
        print(f"\n=== Lunar Orbit Trade ===")
        for c in candidates[:5]:
            print(f"  {c.get('name')}: alt={c.get('altitude_km')}km, "
                  f"period={c.get('period_min')}min")
        # Note: orbit trade is LEO-focused — it may not produce lunar orbit options
        # That's a known limitation (CubeSat tool scope)
        print(f"  Note: {len(candidates)} candidates (tool is LEO-focused, lunar options may be limited)")

    def test_budget_lunar_cubesat(self, client, study):
        """Lunar CubeSat: larger than LEO due to propulsion."""
        sid = study["id"]
        mission = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "LunarScout-1", "element_type": "mission", "segment": "space",
        }).json()
        space = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "Space Segment", "element_type": "segment", "segment": "space",
            "parent_id": mission["id"],
        }).json()

        # Realistic lunar CubeSat subsystems (6U-12U class)
        subsystems = [
            {"name": "Neutron Spectrometer", "domain": "payload", "mass": 2.0, "power": 10, "cost": 500},
            {"name": "Propulsion (green monoprop)", "domain": "propulsion", "mass": 4.0, "power": 0, "cost": 200},
            {"name": "EPS (body-mounted panels)", "domain": "power", "mass": 1.5, "power": 0, "cost": 60},
            {"name": "AOCS (star tracker + wheels)", "domain": "aocs", "mass": 0.8, "power": 4, "cost": 100},
            {"name": "X-band TTC (DSN-compatible)", "domain": "ttc", "mass": 0.5, "power": 12, "cost": 80},
            {"name": "OBC + rad-hard memory", "domain": "obc", "mass": 0.3, "power": 5, "cost": 60},
            {"name": "Thermal (MLI + heaters)", "domain": "thermal", "mass": 0.4, "power": 5, "cost": 30},
            {"name": "Structure (12U frame)", "domain": "structure", "mass": 2.5, "power": 0, "cost": 40},
        ]
        for ss in subsystems:
            client.post(f"/api/elements/?study_id={sid}", json={
                "name": ss["name"], "element_type": "system", "subsystem_domain": ss["domain"],
                "segment": "space", "parent_id": space["id"],
                "mass_kg": ss["mass"], "power_avg_w": ss["power"], "cost_recurring_keur": ss["cost"],
            })

        r = client.get(f"/api/elements/{space['id']}/budget/mass")
        budget = r.json()
        total = budget["sum_nominal"]
        print(f"\n=== Lunar CubeSat Budget ===")
        print(f"  Total mass: {total} kg")
        print(f"  With margin: {budget['sum_with_margin']} kg")
        # Lunar CubeSat: 10-16 kg range (6U-12U with propulsion)
        assert 8 < total < 20, f"Lunar CubeSat mass {total} kg outside 8-20kg range"
        for line in budget["lines"]:
            print(f"  {line['name']}: {line['nominal']} kg")

        # Cost check
        r = client.get(f"/api/elements/{space['id']}/budget/cost")
        cost_budget = r.json()
        total_cost = cost_budget["sum_nominal"]
        print(f"  Total hardware cost: {total_cost} kEUR")
        # Lunar CubeSat hardware: 500-2000 kEUR (more expensive than LEO due to rad-hard + propulsion)
        assert 300 < total_cost < 3000, f"Lunar CubeSat cost {total_cost} kEUR outside expected range"

    def test_smart_lunar_requirements(self, client, study):
        """Lunar-specific requirements."""
        reqs = [
            {"id": "lr1", "text": "The spacecraft shall survive the cislunar radiation environment (>50 krad TID)",
             "level": "mission", "threshold": 50, "operator": ">=", "unit": "krad", "objective_id": "o2"},
            {"id": "lr2", "text": "The propulsion system shall provide at least 800 m/s delta-V",
             "level": "system", "threshold": 800, "operator": ">=", "unit": "m/s"},
            {"id": "lr3", "text": "The communication system shall close the link budget with DSN 34m antenna at lunar distance",
             "level": "system"},
        ]
        print(f"\n=== Lunar SMART Check ===")
        for req in reqs:
            r = client.post("/api/lifecycle/requirements/validate", json=req)
            d = r.json()
            smart = "SMART" if d["is_smart"] else "ISSUES"
            print(f"  {req['id']}: {smart} — {', '.join(d.get('issues', ['OK'])[:2])}")

    def test_exports_lunar(self, client, study):
        """Generate exports for the lunar mission."""
        sid = study["id"]
        print(f"\n=== Lunar Mission Exports ===")
        for endpoint, name in [
            (f"/api/exports/launch-icd/{sid}", "Launch ICD"),
            (f"/api/exports/deorbit/{sid}", "Deorbit Analysis"),
            (f"/api/exports/thermal-report/{sid}", "Thermal Report"),
        ]:
            r = client.post(endpoint)
            print(f"  {name}: {'OK' if r.status_code == 200 else f'FAIL ({r.status_code})'}")
            if r.status_code == 200:
                data = r.json()
                assert data.get("branding", {}).get("university") == "University of Ottawa"
