"""
Level Workbench — Unit tests using FastAPI TestClient (no server required).

Tests the full System-V flow at each level independently.
Run with: pytest tests/test_level_workbench_unit.py -v
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


@pytest.fixture(scope="module")
def client():
    from spacecdf_server.app import app
    return TestClient(app)


@pytest.fixture(scope="module")
def study(client):
    r = client.post("/api/studies/", json={"requirements": {"name": "Test Mission"}, "mission_need": {}})
    assert r.status_code == 200
    return r.json()


# ═══════════════════════════════════════════════════════
# LEVEL 0: MISSION
# ═══════════════════════════════════════════════════════

class TestLevel0:
    """Create mission, add segments, scope, budget, requirements, interfaces, freeze."""

    def test_create_mission(self, client, study):
        r = client.post(f"/api/elements/?study_id={study['id']}", json={
            "name": "Test Mission", "element_type": "mission", "segment": "space",
        })
        assert r.status_code == 200
        study["mission_id"] = r.json()["id"]

    def test_add_segments(self, client, study):
        study["seg"] = {}
        for seg in ["space", "ground", "launch", "operations"]:
            r = client.post(f"/api/elements/?study_id={study['id']}", json={
                "name": f"{seg.title()} Segment", "element_type": "segment",
                "segment": seg, "parent_id": study["mission_id"],
            })
            assert r.status_code == 200
            study["seg"][seg] = r.json()["id"]

    def test_mark_out_of_scope(self, client, study):
        el = client.get(f"/api/elements/{study['seg']['launch']}").json()
        r = client.patch(f"/api/elements/{study['seg']['launch']}", json={"in_scope": False, "version": el["version"]})
        assert r.status_code == 200
        assert r.json()["in_scope"] is False

    def test_set_budget_allocation(self, client, study):
        r = client.post(f"/api/elements/{study['mission_id']}/allocations", json={
            "budget_type": "mass", "allocation_value": 6.0, "unit": "kg",
            "source": "requirement", "rationale": "6U CubeSat",
        })
        assert r.status_code == 200

    def test_read_budget(self, client, study):
        r = client.get(f"/api/elements/{study['mission_id']}/budget/mass")
        assert r.status_code == 200
        assert r.json()["allocation"] == 6.0

    def test_add_requirement_to_mission(self, client, study):
        r = client.post("/api/requirements/", json={
            "study_id": study["id"], "element_id": study["mission_id"],
            "level": "mission", "code": "MIS-001",
            "text": "Mission lifetime >= 3 years", "verification_method": "A",
        })
        assert r.status_code == 200
        study["req_mis_001"] = r.json()["id"]

    def test_add_requirement_to_segment(self, client, study):
        r = client.post("/api/requirements/", json={
            "study_id": study["id"], "element_id": study["seg"]["space"],
            "level": "mission", "code": "MIS-002",
            "text": "Space segment mass <= 5 kg", "verification_method": "I",
        })
        assert r.status_code == 200

    def test_filter_requirements_by_element(self, client, study):
        r = client.get(f"/api/requirements/tree?study_id={study['id']}&element_id={study['mission_id']}")
        assert r.status_code == 200
        assert any(req["code"] == "MIS-001" for req in r.json())

    def test_add_interface(self, client, study):
        r = client.post(f"/api/interfaces/?study_id={study['id']}", json={
            "name": "TM/TC Link", "interface_type": "rf", "direction": "bidirectional",
            "from_element_id": study["seg"]["space"], "to_element_id": study["seg"]["ground"],
        })
        assert r.status_code == 200

    def test_freeze_element(self, client, study):
        el = client.get(f"/api/elements/{study['seg']['space']}").json()
        r = client.patch(f"/api/elements/{study['seg']['space']}", json={"frozen": True, "version": el["version"]})
        assert r.status_code == 200
        assert r.json()["frozen"] is True

    def test_unfreeze_element(self, client, study):
        el = client.get(f"/api/elements/{study['seg']['space']}").json()
        r = client.patch(f"/api/elements/{study['seg']['space']}", json={"frozen": False, "version": el["version"]})
        assert r.status_code == 200
        assert r.json()["frozen"] is False


# ═══════════════════════════════════════════════════════
# LEVEL 1: SYSTEMS
# ═══════════════════════════════════════════════════════

class TestLevel1:
    """Add systems, allocate budgets, derive requirements, add interfaces."""

    def test_add_systems(self, client, study):
        study["sys"] = {}
        for name, domain in [("EPS", "power"), ("AOCS", "aocs"), ("TTC", "ttc"), ("OBC", "obc"), ("Payload", "payload")]:
            r = client.post(f"/api/elements/?study_id={study['id']}", json={
                "name": name, "element_type": "system", "subsystem_domain": domain,
                "segment": "space", "parent_id": study["seg"]["space"],
            })
            assert r.status_code == 200
            study["sys"][domain] = r.json()["id"]

    def test_system_budget_allocation(self, client, study):
        r = client.post(f"/api/elements/{study['sys']['power']}/allocations", json={
            "budget_type": "mass", "allocation_value": 0.8, "unit": "kg",
            "source": "manual", "rationale": "",
        })
        assert r.status_code == 200

    def test_space_segment_budget_shows_systems(self, client, study):
        r = client.get(f"/api/elements/{study['seg']['space']}/budget/mass")
        assert r.status_code == 200
        assert len(r.json()["lines"]) == 5

    def test_derive_requirement(self, client, study):
        r = client.post(f"/api/requirements/{study['req_mis_001']}/derive", json={
            "text": "EPS shall sustain 3 years in LEO",
            "element_id": study["sys"]["power"],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["level"] == "system"
        assert data["derived_from_requirement_id"] == study["req_mis_001"]

    def test_system_interface(self, client, study):
        r = client.post(f"/api/interfaces/?study_id={study['id']}", json={
            "name": "Power Bus", "interface_type": "electrical", "direction": "unidirectional",
            "from_element_id": study["sys"]["power"], "to_element_id": study["sys"]["obc"],
        })
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════
# LEVEL 2: EQUIPMENT
# ═══════════════════════════════════════════════════════

class TestLevel2:
    """Add components, verify actuals roll up, add component requirements."""

    def test_add_components(self, client, study):
        r1 = client.post(f"/api/elements/?study_id={study['id']}", json={
            "name": "GOMspace BPX", "element_type": "component", "subsystem_domain": "power",
            "segment": "space", "parent_id": study["sys"]["power"],
            "mass_kg": 0.32, "cost_recurring_keur": 8.5, "trl": 9, "manufacturer": "GOMspace", "quantity": 1,
        })
        assert r1.status_code == 200
        study["battery_id"] = r1.json()["id"]

        r2 = client.post(f"/api/elements/?study_id={study['id']}", json={
            "name": "NanoPower P110", "element_type": "component", "subsystem_domain": "power",
            "segment": "space", "parent_id": study["sys"]["power"],
            "mass_kg": 0.04, "power_avg_w": 2.3, "cost_recurring_keur": 3.0, "trl": 9,
            "manufacturer": "GOMspace", "quantity": 6,
        })
        assert r2.status_code == 200

    def test_eps_budget_rollup(self, client, study):
        r = client.get(f"/api/elements/{study['sys']['power']}/budget/mass")
        assert r.status_code == 200
        data = r.json()
        assert len(data["lines"]) == 2
        # Battery: 0.32*1 + Solar: 0.04*6 = 0.56
        assert data["sum_nominal"] == pytest.approx(0.56, abs=0.01)

    def test_component_requirement(self, client, study):
        r = client.post("/api/requirements/", json={
            "study_id": study["id"], "element_id": study["battery_id"],
            "level": "subsystem", "code": "SUB-PWR-001",
            "text": "Battery capacity >= 38 Wh", "verification_method": "T",
            "parent_id": study["req_mis_001"],
        })
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════
# LEVEL 3: VERIFICATION & INTEGRITY
# ═══════════════════════════════════════════════════════

class TestLevel3:
    """Full tree verification, delete cascade, no ghost recreation."""

    def test_full_tree_count(self, client, study):
        r = client.get(f"/api/studies/{study['id']}/elements")
        assert r.status_code == 200
        # mission(1) + segments(4) + systems(5) + components(2) = 12
        assert len(r.json()) == 12

    def test_all_requirements(self, client, study):
        r = client.get(f"/api/requirements/tree?study_id={study['id']}")
        assert r.status_code == 200
        assert len(r.json()) >= 4  # MIS-001, MIS-002, derived, SUB-PWR-001

    def test_all_interfaces(self, client, study):
        r = client.get(f"/api/studies/{study['id']}/interfaces")
        assert r.status_code == 200
        assert len(r.json()) >= 2

    def test_delete_cascade(self, client, study):
        """Deleting a system cascades to its components."""
        # Create temp system + child
        r1 = client.post(f"/api/elements/?study_id={study['id']}", json={
            "name": "TempSys", "element_type": "system", "segment": "space",
            "parent_id": study["seg"]["space"],
        })
        temp_id = r1.json()["id"]
        client.post(f"/api/elements/?study_id={study['id']}", json={
            "name": "TempComp", "element_type": "component", "segment": "space", "parent_id": temp_id,
        })

        before = len(client.get(f"/api/studies/{study['id']}/elements").json())
        r = client.delete(f"/api/elements/{temp_id}")
        assert r.status_code == 200
        after = len(client.get(f"/api/studies/{study['id']}/elements").json())
        assert after == before - 2

    def test_no_ghost_recreation(self, client, study):
        names = [e["name"] for e in client.get(f"/api/studies/{study['id']}/elements").json()]
        assert "TempSys" not in names
        assert "TempComp" not in names
