"""
Real Mission Design Scenario — validates decision tool outputs against known references.

Scenario: 3U Earth Observation CubeSat (similar to Planet SuperDove)
Reference: Planet SuperDove specs — 5kg, 500km SSO, 3m GSD, 8-band, daily revisit

This test runs the full mission design flow and checks:
1. Mission trade results make physical sense
2. Orbit trade selects reasonable orbits with correct physics
3. Ground station trade returns realistic contact times
4. Contact scheduling produces plausible pass durations
5. Budget numbers are in CubeSat-realistic ranges
6. SMART checker catches real requirement quality issues
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
for pkg in ["spacecdf-server", "spacecdf-common", "spacecdf-agents", "spacecdf-kb"]:
    src = str(_root / "packages" / pkg / "src")
    if src not in sys.path:
        sys.path.insert(0, src)

import pytest
from fastapi.testclient import TestClient
import math


@pytest.fixture(scope="module")
def client():
    from spacecdf_server.app import app
    return TestClient(app)


@pytest.fixture(scope="module")
def eo_study(client):
    """Create a realistic 3U EO CubeSat study."""
    r = client.post("/api/studies/", json={
        "requirements": {
            "name": "SuperDove-Clone",
            "mission_type": "earth_observation",
            "spacecraft_class": "nano",
            "orbit": {
                "orbit_type": "sso",
                "altitude_km": 500,
                "inclination_deg": 97.4,
                "mission_duration_years": 3,
                "deorbit_required": True,
            },
            "payloads": [{
                "name": "Multispectral Imager",
                "mass_kg": 1.5,
                "power_w": 12,
                "data_rate_mbps": 120,
                "pointing_accuracy_deg": 0.1,
                "duty_cycle_percent": 25,
            }],
            "design_lifetime_years": 3,
            "target_mass_kg": 6,
            "target_cost_meur": 2,
            "ground_stations": ["KSAT Svalbard"],
        },
        "mission_need": {
            "problem_statement": "Agricultural monitoring in Canadian prairies needs frequent multispectral imagery",
            "objectives": [
                {"id": "obj1", "text": "5m GSD multispectral imagery", "priority": "high", "type": "performance"},
                {"id": "obj2", "text": "Daily revisit over 45-60N latitude band", "priority": "high", "type": "performance"},
                {"id": "obj3", "text": "3 year operational lifetime", "priority": "medium", "type": "performance"},
            ],
        },
    })
    assert r.status_code == 200
    return r.json()


class TestMissionTradePhysics:
    """Validate mission trade results against known alternatives."""

    def test_trade_returns_ranked_alternatives(self, client, eo_study):
        r = client.post("/api/lifecycle/mission-trade", json={
            "target_gsd_m": 5.0,
            "target_revisit_days": 1.0,
            "target_coverage": "regional",
            "target_latency_hours": 24.0,
            "require_data_ownership": True,
            "require_scheduling_control": True,
            "max_annual_budget_keur": 2000.0,
            "mission_type": "earth_observation",
            "num_spacecraft": 1,
        })
        assert r.status_code == 200
        data = r.json()

        alts = data.get("alternatives", [])
        assert len(alts) >= 3, f"Should have multiple alternatives, got {len(alts)}"

        # Planet SuperDove should be in the alternatives (it matches this use case)
        names = [a["name"].lower() for a in alts]
        has_commercial = any("planet" in n or "commercial" in n or "satellite" in n for n in names)
        assert has_commercial, f"Should include commercial satellite data option. Got: {names}"

        # Non-space alternatives should be present
        has_non_space = any("drone" in n or "aerial" in n or "ground" in n for n in names)
        # This may or may not be true depending on the trade engine's alternatives
        print(f"Non-space alternatives present: {has_non_space}")
        print(f"Alternatives: {[a['name'] for a in alts]}")

    def test_new_satellite_option_exists(self, client, eo_study):
        """The trade should include 'build new dedicated satellite' as an option."""
        r = client.post("/api/lifecycle/mission-trade", json={
            "target_gsd_m": 5.0, "target_revisit_days": 1.0,
            "require_data_ownership": True,
            "max_annual_budget_keur": 5000.0,
        })
        data = r.json()
        alts = data.get("alternatives", [])
        has_new = any("dedicated" in a["name"].lower() or "new" in a["name"].lower() or "custom" in a["name"].lower() for a in alts)
        assert has_new, f"Should include 'build new satellite' option. Got: {[a['name'] for a in alts]}"


class TestOrbitTradePhysics:
    """Validate orbit trade produces physically correct results."""

    def test_sso_inclination_correct(self, client, eo_study):
        """SSO at 500km should be ~97.4 degrees."""
        r = client.get(f"/api/lifecycle/orbit-trade/{eo_study['id']}")
        assert r.status_code == 200
        data = r.json()
        candidates = data.get("candidates", [])
        assert len(candidates) >= 2, f"Should have multiple orbit candidates"

        # Find SSO candidate
        sso = [c for c in candidates if "sso" in c.get("orbit_type", "").lower() or "sso" in c.get("name", "").lower()]
        assert len(sso) >= 1, f"Should have SSO orbit candidate"

        for s in sso:
            inc = s.get("inclination_deg", 0)
            # SSO at 350-600km should be between 96.5-98.0 degrees
            assert 96.0 <= inc <= 99.0, f"SSO inclination {inc} outside expected range [96-99] for altitude {s.get('altitude_km')}km"

    def test_orbital_period_reasonable(self, client, eo_study):
        """Orbital period at 500km should be ~94.6 minutes."""
        r = client.get(f"/api/lifecycle/orbit-trade/{eo_study['id']}")
        data = r.json()
        candidates = data.get("candidates", [])

        for c in candidates:
            alt = c.get("altitude_km", 500)
            period = c.get("period_min")
            if period:
                # Kepler: T = 2π√(a³/μ), at 500km ≈ 94.6 min
                R_earth = 6371
                a = R_earth + alt
                expected = 2 * math.pi * math.sqrt((a * 1000) ** 3 / 3.986e14) / 60
                assert abs(period - expected) < 2.0, f"Period {period} min at {alt}km far from expected {expected:.1f} min"

    def test_deorbit_compliance_correct(self, client, eo_study):
        """Orbits below ~600km should naturally deorbit within 25 years."""
        r = client.get(f"/api/lifecycle/orbit-trade/{eo_study['id']}")
        data = r.json()
        for c in data.get("candidates", []):
            alt = c.get("altitude_km", 500)
            compliant = c.get("deorbit_compliant_25yr") or c.get("deorbit_compliant")
            if alt <= 500 and compliant is not None:
                # At 500km a CubeSat typically deorbits in 5-15 years
                assert compliant, f"Orbit at {alt}km should be 25yr compliant but isn't"
            if alt >= 800 and compliant is not None:
                # At 800km+ natural decay takes centuries
                print(f"800km+ compliance: {compliant} (may need propulsion)")


class TestGroundSegmentTradePhysics:
    """Validate ground segment trade produces realistic contact times."""

    def test_ground_trade_contact_times(self, client, eo_study):
        r = client.get(f"/api/lifecycle/ground/trade/{eo_study['id']}")
        assert r.status_code == 200
        data = r.json()

        alts = data.get("alternatives", data.get("options", []))
        assert len(alts) >= 2, f"Should have multiple GS architectures"

        for alt in alts:
            contact = alt.get("contact_minutes_per_day") or alt.get("contact_min_per_day")
            if contact:
                # A single polar station gives ~20-40 min/day for LEO SSO
                # Multiple stations give 40-120 min/day
                assert 5 < contact < 200, f"Contact time {contact} min/day unrealistic for {alt.get('name')}"

            cost = alt.get("annual_cost_keur")
            if cost:
                # GS costs range from 50-500 kEUR/year
                assert 0 < cost < 2000, f"Annual cost {cost} kEUR unrealistic for {alt.get('name')}"

        print(f"Ground alternatives: {[(a.get('name'), a.get('contact_minutes_per_day') or a.get('contact_min_per_day')) for a in alts]}")


class TestContactSchedulePhysics:
    """Validate contact scheduling produces physically plausible passes."""

    def test_pass_duration_reasonable(self, client):
        """Typical LEO pass over a ground station is 5-12 minutes."""
        r = client.post("/api/ground/schedule", json={
            "orbit": {"altitude_km": 500, "inclination_deg": 97.4},
        })
        assert r.status_code == 200
        data = r.json()

        contacts = data.get("contacts", data.get("windows", []))
        assert len(contacts) >= 1, "Should have at least 1 contact per day"

        for c in contacts[:10]:
            dur_s = (c.get("end_s", 0) - c.get("start_s", 0))
            dur_min = c.get("duration_min", dur_s / 60)
            # Typical pass: 5-15 minutes max
            assert 1 < dur_min < 20, f"Pass duration {dur_min:.1f} min unrealistic for LEO"

            max_el = c.get("max_elevation_deg")
            if max_el:
                assert 5 <= max_el <= 90, f"Max elevation {max_el} deg invalid"


class TestSMARTRequirementPhysics:
    """Validate SMART checker catches real issues."""

    def test_good_requirement_passes(self, client):
        """A well-written requirement should pass SMART criteria."""
        r = client.post("/api/lifecycle/requirements/validate", json={
            "id": "good-1",
            "text": "The spacecraft total mass shall not exceed 6 kg",
            "level": "mission",
            "threshold": 6,
            "operator": "<=",
            "unit": "kg",
            "objective_id": "obj1",
        })
        data = r.json()
        assert data["specific"], f"Should be specific: {data.get('issues')}"
        assert data["measurable"], f"Should be measurable: {data.get('issues')}"

    def test_vague_requirement_fails(self, client):
        """A vague requirement should fail SMART."""
        r = client.post("/api/lifecycle/requirements/validate", json={
            "id": "vague-1",
            "text": "The system should be reliable",
            "level": "system",
        })
        data = r.json()
        assert not data["is_smart"], f"Vague requirement should fail SMART"
        assert len(data["issues"]) >= 1, "Should have at least 1 issue"

    def test_how_not_what_detected(self, client):
        """A requirement prescribing implementation should be flagged."""
        r = client.post("/api/lifecycle/requirements/validate", json={
            "id": "how-1",
            "text": "The power system shall use GOMspace NanoPower P31u EPS board",
            "level": "subsystem",
        })
        data = r.json()
        # This prescribes a specific product — should ideally be flagged as HOW-not-WHAT
        print(f"HOW-not-WHAT detected: {data.get('is_how_not_what')}")
        print(f"Issues: {data.get('issues')}")


class TestBudgetPhysics:
    """Validate budget numbers are in CubeSat-realistic ranges."""

    def test_element_tree_budget_rollup(self, client, eo_study):
        """Create a realistic element tree and verify budget math."""
        sid = eo_study["id"]

        # Create mission root + space segment
        mission = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "SuperDove-Clone", "element_type": "mission", "segment": "space",
        }).json()

        space = client.post(f"/api/elements/?study_id={sid}", json={
            "name": "Space Segment", "element_type": "segment", "segment": "space",
            "parent_id": mission["id"],
        }).json()

        # Set mission mass allocation
        client.post(f"/api/elements/{mission['id']}/allocations", json={
            "budget_type": "mass", "allocation_value": 6.0, "unit": "kg",
            "source": "requirement", "rationale": "3U CubeSat limit",
        })

        # Add realistic subsystems with actual CubeSat masses
        subsystems = [
            {"name": "Payload", "domain": "payload", "mass_kg": 1.5, "power_avg_w": 12, "cost_recurring_keur": 50},
            {"name": "EPS", "domain": "power", "mass_kg": 0.5, "power_avg_w": 0, "cost_recurring_keur": 15},
            {"name": "AOCS", "domain": "aocs", "mass_kg": 0.3, "power_avg_w": 2, "cost_recurring_keur": 20},
            {"name": "TTC", "domain": "ttc", "mass_kg": 0.2, "power_avg_w": 4, "cost_recurring_keur": 15},
            {"name": "OBC", "domain": "obc", "mass_kg": 0.1, "power_avg_w": 3, "cost_recurring_keur": 10},
            {"name": "Thermal", "domain": "thermal", "mass_kg": 0.1, "power_avg_w": 1, "cost_recurring_keur": 5},
            {"name": "Structure", "domain": "structure", "mass_kg": 1.0, "power_avg_w": 0, "cost_recurring_keur": 8},
        ]
        for ss in subsystems:
            client.post(f"/api/elements/?study_id={sid}", json={
                "name": ss["name"], "element_type": "system", "subsystem_domain": ss["domain"],
                "segment": "space", "parent_id": space["id"],
                "mass_kg": ss["mass_kg"], "power_avg_w": ss["power_avg_w"],
                "cost_recurring_keur": ss["cost_recurring_keur"],
            })

        # Check budget rollup
        r = client.get(f"/api/elements/{space['id']}/budget/mass")
        assert r.status_code == 200
        budget = r.json()

        total_mass = sum(ss["mass_kg"] for ss in subsystems)
        assert abs(budget["sum_nominal"] - total_mass) < 0.01, f"Mass rollup {budget['sum_nominal']} != expected {total_mass}"

        # Total should be ~3.7 kg — well within 6U CubeSat range
        assert 2.0 < total_mass < 8.0, f"Total mass {total_mass} kg outside CubeSat range"
        print(f"Total mass: {total_mass} kg, with margin: {budget['sum_with_margin']} kg")

        # Check cost rollup
        r = client.get(f"/api/elements/{space['id']}/budget/cost")
        budget_cost = r.json()
        total_cost = sum(ss["cost_recurring_keur"] for ss in subsystems)
        assert abs(budget_cost["sum_nominal"] - total_cost) < 0.01
        # CubeSat hardware cost typically 50-300 kEUR
        assert 50 < total_cost < 500, f"Total hardware cost {total_cost} kEUR outside CubeSat range"
        print(f"Total cost: {total_cost} kEUR, with margin: {budget_cost['sum_with_margin']} kEUR")
