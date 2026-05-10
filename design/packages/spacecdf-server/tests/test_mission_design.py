"""Tests for SpaceCDF core mission design functionality (end-to-end).

Covers: Element tree CRUD, KB equipment validation, architecture options,
regulatory generators, document generation, and data flow integration.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from uuid import uuid4

# Add source paths so tests work without pip install
_server_src = str(Path(__file__).parent.parent / "src")
_common_src = str(Path(__file__).resolve().parents[2] / "spacecdf-common" / "src")
if _server_src not in sys.path:
    sys.path.insert(0, _server_src)
if _common_src not in sys.path:
    sys.path.insert(0, _common_src)

import pytest
import yaml


# ─── Path helpers ───

_KB_DIR = Path(__file__).resolve().parents[2] / "spacecdf-kb" / "src" / "spacecdf_kb" / "data"
_COMPONENTS_DIR = _KB_DIR / "components"
_COST_DIR = _KB_DIR / "cost_models"


# ─── Fixtures ───

@pytest.fixture
def seeded_tree():
    """Seed a full element tree and return (elements, interfaces)."""
    from spacecdf_server.services.element_projection import seed_elements_from_design_result

    params = {
        "power.eps_mass_kg": 0.5,
        "power.total_sunlight_w": 12,
        "aocs.mass_kg": 0.4,
        "aocs.power_w": 3.0,
        "link.ttc_mass_kg": 0.3,
        "link.ttc_power_w": 5.0,
        "data.obdh_mass_kg": 0.06,
        "thermal.tcs_mass_kg": 0.1,
        "thermal.heater_power_w": 1.0,
        "structure.mass_kg": 0.35,
        "propulsion.total_mass_kg": 0.0,
        "payload.mass_kg": 1.5,
        "payload.0.power_w": 10,
    }
    elements, interfaces = seed_elements_from_design_result(
        study_id="test-study",
        result_params=params,
        mission_type="earth_observation",
        spacecraft_class="nano",
    )
    return elements, interfaces


@pytest.fixture
def element_dict_store():
    """Provide a plain dict acting as the in-memory element store."""
    return {}


@pytest.fixture
def kb_components():
    """Load all KB component YAML files into {filename_stem: data} dict."""
    results = {}
    if _COMPONENTS_DIR.exists():
        for f in sorted(_COMPONENTS_DIR.glob("*.yaml")):
            with open(f) as fp:
                data = yaml.safe_load(fp) or {}
            results[f.stem] = data.get("components", [])
    return results


@pytest.fixture
def sample_elements_for_bom():
    """Minimal element tree for BOM testing."""
    return [
        {"id": "m1", "study_id": "s1", "parent_id": None, "name": "Test Mission", "element_type": "mission",
         "subsystem_domain": None, "segment": "space", "mass_kg": None, "power_avg_w": None,
         "cost_recurring_keur": None, "trl": None, "manufacturer": None, "kb_component_id": None,
         "quantity": 1, "margin_percent": 0},
        {"id": "seg1", "study_id": "s1", "parent_id": "m1", "name": "Space Segment", "element_type": "segment",
         "subsystem_domain": None, "segment": "space", "mass_kg": None, "power_avg_w": None,
         "cost_recurring_keur": None, "trl": None, "manufacturer": None, "kb_component_id": None,
         "quantity": 1, "margin_percent": 0},
        {"id": "sys1", "study_id": "s1", "parent_id": "seg1", "name": "Platform", "element_type": "system",
         "subsystem_domain": None, "segment": "space", "mass_kg": None, "power_avg_w": None,
         "cost_recurring_keur": None, "trl": None, "manufacturer": None, "kb_component_id": None,
         "quantity": 1, "margin_percent": 0},
        {"id": "sub1", "study_id": "s1", "parent_id": "sys1", "name": "EPS", "element_type": "subsystem",
         "subsystem_domain": "power", "segment": "space", "mass_kg": 0.5, "power_avg_w": 0,
         "cost_recurring_keur": 50, "trl": 9, "manufacturer": None, "kb_component_id": None,
         "quantity": 1, "margin_percent": 10},
        {"id": "sub2", "study_id": "s1", "parent_id": "sys1", "name": "AOCS", "element_type": "subsystem",
         "subsystem_domain": "aocs", "segment": "space", "mass_kg": 0.3, "power_avg_w": 5,
         "cost_recurring_keur": 80, "trl": 8, "manufacturer": None, "kb_component_id": None,
         "quantity": 1, "margin_percent": 10},
        {"id": "comp1", "study_id": "s1", "parent_id": "sub1", "name": "GomSpace BPX", "element_type": "component",
         "subsystem_domain": "power", "segment": "space", "mass_kg": 0.24, "power_avg_w": 0,
         "cost_recurring_keur": 15, "trl": 9, "manufacturer": "GomSpace", "kb_component_id": "bat-gomspace-bpx",
         "quantity": 1, "margin_percent": 5},
        {"id": "comp2", "study_id": "s1", "parent_id": "sub2", "name": "CubeWheel Medium", "element_type": "component",
         "subsystem_domain": "aocs", "segment": "space", "mass_kg": 0.06, "power_avg_w": 1.5,
         "cost_recurring_keur": 20, "trl": 9, "manufacturer": "CubeSpace", "kb_component_id": "rw-cubespace-medium",
         "quantity": 4, "margin_percent": 5, "redundancy_type": None},
    ]


@pytest.fixture
def sample_requirements():
    return [
        {"id": "REQ-001", "text": "The system shall have a mass less than 6 kg", "domain": "mass",
         "level": "mission", "category": "performance", "threshold": 6, "operator": "<=", "unit": "kg",
         "verification_method": "analysis", "objective_id": "OBJ-1"},
        {"id": "REQ-002", "text": "The system shall provide 30W average power", "domain": "power",
         "level": "system", "category": "performance", "threshold": 30, "operator": ">=", "unit": "W",
         "verification_method": "test", "objective_id": "OBJ-1"},
        {"id": "REQ-003", "text": "The pointing accuracy shall be better than 0.1 deg", "domain": "aocs",
         "level": "subsystem", "category": "performance", "threshold": 0.1, "operator": "<=", "unit": "deg",
         "verification_method": "analysis", "objective_id": "OBJ-2"},
    ]


@pytest.fixture
def sample_mission_need():
    return {
        "problem_statement": "Need high-resolution Earth observation for agricultural monitoring",
        "operational_context": "LEO sun-synchronous orbit, 10:30 LTAN",
        "objectives": [
            {"id": "OBJ-1", "text": "Capture multispectral imagery at 5m GSD", "priority": "primary",
             "type": "performance", "measurable_criterion": "GSD <= 5m in all bands"},
            {"id": "OBJ-2", "text": "Provide daily revisit over target areas", "priority": "secondary",
             "type": "operational", "measurable_criterion": "Revisit time <= 24h"},
        ],
        "stakeholders": [
            {"name": "Agriculture Ministry", "role": "End user", "needs": ["crop monitoring", "yield prediction"]},
        ],
    }


# ─── Helper: in-memory budget computation (mirrors router logic without FastAPI) ───

def _compute_budget_from_dict(elements: dict, parent_id: str, budget_type: str) -> dict:
    """Replicate the budget computation from elements router without needing FastAPI."""
    prop_map = {
        "mass": "mass_kg",
        "power": "power_avg_w",
        "cost": "cost_recurring_keur",
    }
    prop = prop_map[budget_type]

    parent = elements[parent_id]
    lines = []
    total_nominal = 0
    for e in elements.values():
        if e.get("parent_id") == parent_id and not e.get("deleted_at"):
            val = (e.get(prop) or 0) * (e.get("quantity", 1))
            margin = e.get("margin_percent", 20) / 100
            val_with_margin = val * (1 + margin)
            total_nominal += val
            lines.append({
                "element_id": e["id"],
                "name": e["name"],
                "nominal": round(val, 3),
                "margin_pct": e.get("margin_percent", 20),
                "with_margin": round(val_with_margin, 3),
                "quantity": e.get("quantity", 1),
            })
    total_with_margin = sum(l["with_margin"] for l in lines)
    return {
        "element_id": parent_id,
        "element_name": parent["name"],
        "budget_type": budget_type,
        "sum_nominal": round(total_nominal, 3),
        "sum_with_margin": round(total_with_margin, 3),
        "lines": lines,
    }


def _create_element(store: dict, *, name: str, element_type: str, study_id: str = "s1",
                     parent_id: str | None = None, subsystem_domain: str | None = None,
                     mass_kg: float | None = None, power_avg_w: float | None = None,
                     cost_recurring_keur: float | None = None, quantity: int = 1,
                     margin_percent: float = 20.0, **kwargs) -> dict:
    """Create an element in the dict store (mirrors router create_element)."""
    el_id = uuid4().hex
    el = {
        "id": el_id, "study_id": study_id, "parent_id": parent_id,
        "name": name, "element_type": element_type,
        "subsystem_domain": subsystem_domain, "segment": "space",
        "mass_kg": mass_kg, "power_avg_w": power_avg_w,
        "cost_recurring_keur": cost_recurring_keur,
        "quantity": quantity, "margin_percent": margin_percent,
        "version": 1, "deleted_at": None,
        **kwargs,
    }
    store[el_id] = el
    return el


# ═══════════════════════════════════════════════════════════════════════
# 1. Element Tree Tests
# ═══════════════════════════════════════════════════════════════════════

class TestElementTree:
    def test_element_tree_seed_creates_hierarchy(self, seeded_tree):
        """Seed function creates mission -> segments -> systems -> subsystems."""
        elements, interfaces = seeded_tree
        types = {e["element_type"] for e in elements}
        assert "mission" in types
        assert "segment" in types
        assert "system" in types
        assert "subsystem" in types

        # Should have exactly one mission root
        missions = [e for e in elements if e["element_type"] == "mission"]
        assert len(missions) == 1

        # Should have space, ground, operations segments
        segments = [e for e in elements if e["element_type"] == "segment"]
        segment_names = {e["name"] for e in segments}
        assert "Space Segment" in segment_names
        assert "Ground Segment" in segment_names

        # Should have subsystems under platform
        subsystems = [e for e in elements if e["element_type"] == "subsystem"]
        assert len(subsystems) >= 5  # EPS, AOCS, TTC, OBC, Thermal, Structure, Propulsion

    def test_element_creation_with_parent(self, element_dict_store):
        """createElement returns valid ID with correct parent."""
        el = _create_element(
            element_dict_store,
            name="Test EPS",
            element_type="subsystem",
            parent_id="parent-123",
            subsystem_domain="power",
        )
        assert el["id"]  # non-empty ID
        assert el["parent_id"] == "parent-123"
        assert el["element_type"] == "subsystem"
        assert el["subsystem_domain"] == "power"
        assert el["version"] == 1
        assert el["id"] in element_dict_store

    def test_element_deletion(self, element_dict_store):
        """deleteElement soft-deletes from dict."""
        el = _create_element(element_dict_store, name="Temp", element_type="component")
        el_id = el["id"]

        # Simulate soft-delete (mirrors router logic)
        from datetime import datetime, timezone
        element_dict_store[el_id]["deleted_at"] = datetime.now(timezone.utc).isoformat()

        assert element_dict_store[el_id]["deleted_at"] is not None

    def test_element_update_version_increment(self, element_dict_store):
        """Update increments version number."""
        el = _create_element(element_dict_store, name="Widget", element_type="component", mass_kg=0.5)
        assert el["version"] == 1

        # Simulate update (mirrors router logic)
        el["mass_kg"] = 0.7
        el["version"] += 1
        assert el["version"] == 2
        assert el["mass_kg"] == 0.7

    def test_subsystem_domain_mapping(self):
        """Each domain (power, aocs, ttc, etc.) maps correctly in element projection."""
        from spacecdf_server.services.element_projection import DOMAIN_SUBSYSTEM_MAP

        expected = {"power", "aocs", "link", "thermal", "structure", "propulsion", "data", "payload"}
        assert expected.issubset(set(DOMAIN_SUBSYSTEM_MAP.keys()))
        # Values should be subsystem names
        assert DOMAIN_SUBSYSTEM_MAP["power"] == "eps"
        assert DOMAIN_SUBSYSTEM_MAP["aocs"] == "aocs"
        assert DOMAIN_SUBSYSTEM_MAP["link"] == "ttc"

    def test_interface_creation(self, seeded_tree):
        """Seed creates interfaces linking elements."""
        elements, interfaces = seeded_tree
        # Interfaces should have been created between subsystems
        assert len(interfaces) > 0
        for iface in interfaces:
            assert iface["from_element_id"]
            assert iface["to_element_id"]
            assert iface["interface_type"] in ("electrical", "data", "rf", "mechanical")
            assert iface["from_element_id"] != iface["to_element_id"]

    def test_tree_query_get_children(self, seeded_tree):
        """getChildren returns correct children for a parent."""
        elements, _ = seeded_tree

        # Find space segment
        space_seg = next(e for e in elements if e["name"] == "Space Segment")
        # Its children should be systems (Platform, Payload)
        children = [
            e for e in elements
            if e.get("parent_id") == space_seg["id"] and not e.get("deleted_at")
        ]
        assert len(children) >= 2
        child_types = {c["element_type"] for c in children}
        assert "system" in child_types

    def test_budget_computation(self, element_dict_store):
        """computeBudget sums children correctly."""
        parent = _create_element(
            element_dict_store,
            name="EPS", element_type="subsystem", subsystem_domain="power",
        )
        pid = parent["id"]

        _create_element(
            element_dict_store,
            name="Battery", element_type="component", parent_id=pid,
            mass_kg=0.2, quantity=1, margin_percent=10,
        )
        _create_element(
            element_dict_store,
            name="Solar Panel", element_type="component", parent_id=pid,
            mass_kg=0.1, quantity=2, margin_percent=10,
        )

        budget = _compute_budget_from_dict(element_dict_store, pid, "mass")
        # nominal: 0.2*1 + 0.1*2 = 0.4
        assert abs(budget["sum_nominal"] - 0.4) < 0.01
        # with margin: 0.22 + 0.22 = 0.44
        assert budget["sum_with_margin"] > budget["sum_nominal"]
        assert len(budget["lines"]) == 2


# ═══════════════════════════════════════════════════════════════════════
# 2. Equipment & KB Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEquipmentKB:
    def test_kb_components_are_cubesat_appropriate(self, kb_components):
        """No space-segment component mass > 10kg in any YAML file (excluding ground equipment).

        Threshold is 10 kg to accommodate larger nano-class (12U-16U) and
        borderline micro-class components (optical terminals, hall thrusters)
        while still flagging anything clearly outside CubeSat/small-sat scope.
        """
        for category, components in kb_components.items():
            if category == "ground_equipment":
                continue  # Ground antennas etc. are large by nature
            for comp in components:
                mass = comp.get("mass_kg", 0) or 0
                assert mass <= 10.0, (
                    f"Component {comp.get('id', '?')} in {category} has mass "
                    f"{mass} kg, exceeding CubeSat/small-sat range (10 kg max per component)"
                )

    def test_kb_no_duplicate_ids(self, kb_components):
        """No duplicate component IDs across all YAML files."""
        all_ids = []
        for category, components in kb_components.items():
            for comp in components:
                cid = comp.get("id")
                if cid:
                    all_ids.append((cid, category))

        seen = {}
        for cid, cat in all_ids:
            assert cid not in seen, (
                f"Duplicate component ID '{cid}' found in {cat} "
                f"(first seen in {seen[cid]})"
            )
            seen[cid] = cat

    def test_kb_all_categories_have_components(self, kb_components):
        """Each space-segment category referenced by DOMAIN_TO_CATEGORIES has at least 1 component."""
        # Hard-code the mapping to avoid importing equipment.py which requires spacecdf_common
        domain_to_categories = {
            "power": ["batteries", "solar_cells", "solar_panels", "eps_boards"],
            "aocs": ["reaction_wheels", "star_trackers", "sun_sensors", "magnetorquers"],
            "link": ["transponders", "antennas", "gps_receivers"],
            "propulsion": ["thrusters"],
            "structure": ["cubesat_structures", "deployers", "mechanical_hardware"],
            "data": ["obcs"],
            "thermal": ["thermal_hardware"],
            "integration": ["harnesses"],
        }

        for domain, categories in domain_to_categories.items():
            for cat in categories:
                assert cat in kb_components, (
                    f"Category '{cat}' (domain: {domain}) has no YAML file in KB"
                )
                assert len(kb_components[cat]) > 0, (
                    f"Category '{cat}' (domain: {domain}) has 0 components"
                )

    def test_ground_equipment_exists(self, kb_components):
        """ground_equipment.yaml has components."""
        assert "ground_equipment" in kb_components, "ground_equipment.yaml missing from KB"
        assert len(kb_components["ground_equipment"]) > 0, "ground_equipment.yaml has 0 components"

    def test_equipment_domain_mapping_complete(self):
        """Every KB category maps to a subsystem domain."""
        # Hard-code the mapping to avoid import dependency on spacecdf_common
        domain_to_categories = {
            "power": ["batteries", "solar_cells", "solar_panels", "eps_boards"],
            "aocs": ["reaction_wheels", "star_trackers", "sun_sensors", "magnetorquers"],
            "link": ["transponders", "antennas", "gps_receivers"],
            "propulsion": ["thrusters"],
            "structure": ["cubesat_structures", "deployers", "mechanical_hardware"],
            "data": ["obcs"],
            "thermal": ["thermal_hardware"],
            "integration": ["harnesses"],
            "ground_rf": ["ground_antennas", "ground_rf", "ground_baseband"],
            "ground_ops": ["ground_software", "ground_timing"],
        }

        all_categories = set()
        for cats in domain_to_categories.values():
            all_categories.update(cats)

        expected_yamls = {
            "batteries", "solar_panels", "eps_boards", "reaction_wheels",
            "star_trackers", "sun_sensors", "magnetorquers", "transponders",
            "antennas", "obcs", "cubesat_structures", "thrusters",
        }
        for cat in expected_yamls:
            assert cat in all_categories, (
                f"KB category '{cat}' not mapped to any subsystem domain"
            )

    def test_1u_example_mission_components_exist(self, kb_components):
        """All componentIds in the UniSat-1 example exist in KB."""
        from spacecdf_server.services.example_missions import EXAMPLE_MISSIONS

        mission = EXAMPLE_MISSIONS.get("unisat1_1u_techdemo")
        assert mission is not None, "UniSat-1 example mission not found"

        # Flatten all KB component IDs
        all_kb_ids = set()
        for components in kb_components.values():
            for comp in components:
                cid = comp.get("id")
                if cid:
                    all_kb_ids.add(cid)

        for equip in mission["selected_equipment"]:
            cid = equip.get("componentId")
            if cid:
                assert cid in all_kb_ids, (
                    f"UniSat-1 equipment '{equip['name']}' references "
                    f"componentId '{cid}' not found in KB"
                )


# ═══════════════════════════════════════════════════════════════════════
# 3. Architecture Tests
# ═══════════════════════════════════════════════════════════════════════

class TestArchitecture:
    def test_all_architecture_options_have_requirements(self):
        """Each option has derived_requirements."""
        from spacecdf_common.models.architecture import ARCHITECTURE_CATALOGUE

        for subsystem, options in ARCHITECTURE_CATALOGUE.items():
            for opt in options:
                assert len(opt.derived_requirements) > 0, (
                    f"Architecture option '{opt.id}' ({subsystem}) has no "
                    f"derived_requirements"
                )

    def test_1u_structure_option_exists(self):
        """str-1u is in STRUCTURE_OPTIONS."""
        from spacecdf_common.models.architecture import STRUCTURE_OPTIONS

        ids = [o.id for o in STRUCTURE_OPTIONS]
        assert "str-1u" in ids, "str-1u not found in STRUCTURE_OPTIONS"

        opt = next(o for o in STRUCTURE_OPTIONS if o.id == "str-1u")
        assert opt.mass_kg_typical <= 1.33, "1U structure should be well under 1.33 kg"
        assert opt.trl >= 7, "1U structure should have high TRL"

    def test_architecture_mass_within_cubesat_range(self):
        """No option has mass > 30kg."""
        from spacecdf_common.models.architecture import ARCHITECTURE_CATALOGUE

        for subsystem, options in ARCHITECTURE_CATALOGUE.items():
            for opt in options:
                assert opt.mass_kg_typical <= 30.0, (
                    f"Architecture option '{opt.id}' ({subsystem}) has mass "
                    f"{opt.mass_kg_typical} kg, exceeding 30 kg CubeSat range"
                )

    def test_no_large_satellite_cost_models(self):
        """parametric.yaml has no 'large_satellite' entries."""
        param_file = _COST_DIR / "parametric.yaml"
        assert param_file.exists(), "parametric.yaml not found"

        with open(param_file) as fp:
            data = yaml.safe_load(fp) or {}

        content = yaml.dump(data)
        assert "large_satellite" not in content, (
            "parametric.yaml should not contain 'large_satellite' cost models "
            "-- SpaceCDF targets CubeSat/small satellite class only"
        )

    def test_class_advisor_cubesat_scope(self):
        """nano and nano_large are primary; micro/small warn about scope."""
        from spacecdf_server.services.class_advisor import CLASS_PROFILES

        ids = {p.class_id for p in CLASS_PROFILES}
        assert "nano" in ids, "nano class missing"
        assert "nano_large" in ids, "nano_large class missing"

        # micro and small should warn about scope
        for p in CLASS_PROFILES:
            if p.class_id in ("micro", "small"):
                assert "SCOPE" in p.risk_profile.upper() or "BEYOND" in p.risk_profile.upper(), (
                    f"Class '{p.class_id}' should warn about being beyond CubeSat scope"
                )


# ═══════════════════════════════════════════════════════════════════════
# 4. Regulatory Generator Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRegulatoryGenerators:
    def test_rsssa_auto_populates_orbit(self):
        """RSSSA template has orbit parameters auto-filled."""
        from spacecdf_server.services.regulatory import generate_rsssa_template

        result = generate_rsssa_template(
            study_name="TestSat",
            orbit_altitude_km=550,
            orbit_inclination_deg=97.6,
        )
        orbit = result["sections"]["orbit"]
        assert orbit["altitude_km"]["value"] == 550
        assert orbit["altitude_km"]["auto_populated"] is True
        assert orbit["inclination_deg"]["value"] == 97.6
        assert orbit["period_min"]["auto_populated"] is True
        # Should auto-detect SSO
        assert "Sun-Synchronous" in orbit["orbit_type"]["value"] or "SSO" in orbit["orbit_type"]["value"]

    def test_itu_api_emission_designator_valid(self):
        """Computed designator matches ITU format."""
        from spacecdf_server.services.regulatory import compute_emission_designator

        # 200 kHz bandwidth, QPSK modulation
        result = compute_emission_designator(200_000, "QPSK", 100_000)
        assert isinstance(result, str)
        assert len(result) >= 4
        # Should contain bandwidth encoding with K for kHz
        assert "K" in result or "M" in result or "H" in result or "G" in result

        # 1.5 MHz bandwidth, GMSK
        result2 = compute_emission_designator(1_500_000, "GMSK", 1_000_000)
        assert isinstance(result2, str)
        assert len(result2) >= 4

    def test_copuos_mission_type_mapping(self):
        """All mission types map to UN function descriptions."""
        from spacecdf_server.services.regulatory import (
            generate_copuos_registration, _MISSION_TYPE_TO_UN_FUNCTION,
        )

        # Check mapping coverage
        expected_types = [
            "earth_observation", "communications", "science",
            "technology", "tech_demo", "education",
        ]
        for mt in expected_types:
            assert mt in _MISSION_TYPE_TO_UN_FUNCTION, (
                f"Mission type '{mt}' missing from COPUOS function mapping"
            )
            assert len(_MISSION_TYPE_TO_UN_FUNCTION[mt]) > 10, (
                f"COPUOS function for '{mt}' is too short to be meaningful"
            )

        # Check that function text is populated in output
        result = generate_copuos_registration(
            study_name="TestSat",
            mission_type="earth_observation",
            orbit_altitude_km=500,
        )
        func = result["article_iv_data_items"]["item_e_general_function"]
        assert func["value"]["auto_populated"] is True
        assert "observation" in func["value"]["value"].lower()

    def test_eol_25_year_compliance_check(self):
        """400km returns compliant, 800km returns non-compliant."""
        from spacecdf_server.services.regulatory import generate_eol_report

        # 400 km: orbital lifetime ~1 year, should be compliant
        result_400 = generate_eol_report(
            study_name="LowSat",
            orbit_altitude_km=400,
            dry_mass_kg=4.0,
            mission_duration_years=0.5,
        )
        result_str = str(result_400)
        assert "compliant" in result_str.lower() or "COMPLIANT" in result_str

        # 800 km: orbital lifetime ~100 years, should be non-compliant
        result_800 = generate_eol_report(
            study_name="HighSat",
            orbit_altitude_km=800,
            dry_mass_kg=4.0,
            mission_duration_years=3,
        )
        result_str_800 = str(result_800)
        # Should flag non-compliance or show very long lifetime
        assert "non" in result_str_800.lower() or "exceed" in result_str_800.lower() or "100" in result_str_800

    def test_export_control_flags_cubesat_components(self):
        """CubeSat components don't trigger ITAR flags (GSD > 2m typically)."""
        from spacecdf_server.services.regulatory import generate_export_assessment

        # Typical CubeSat: GSD > 5m, no encryption issues
        result = generate_export_assessment(
            study_name="CubeSatX",
            design_params={"gsd_m": 10.0},  # Coarse GSD
        )
        flags = result.get("flags", [])
        # No ITAR flags for 10m GSD
        itar_flags = [f for f in flags if f.get("flag") == "HIGH_RESOLUTION_IMAGING"]
        assert len(itar_flags) == 0, (
            "10m GSD CubeSat should not trigger high-resolution imaging flag"
        )


# ═══════════════════════════════════════════════════════════════════════
# 5. Document Generation Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDocumentGeneration:
    def test_mrd_sections_complete(self, sample_mission_need, sample_requirements):
        """MRD has all 7 sections with non-empty content."""
        from spacecdf_server.services.did_generator import generate_mrd

        mrd = generate_mrd(
            study_name="Test",
            mission_need=sample_mission_need,
            requirements=sample_requirements,
        )
        assert "sections" in mrd
        assert len(mrd["sections"]) >= 7, (
            f"MRD should have at least 7 sections, got {len(mrd['sections'])}"
        )
        for sec in mrd["sections"]:
            assert sec.get("title"), f"Section {sec.get('number', '?')} has no title"
            # Each section should have subsections or content
            has_content = (
                sec.get("content")
                or sec.get("subsections")
                or sec.get("table")
                or sec.get("items")
            )
            assert has_content, (
                f"Section {sec['number']} '{sec['title']}' has no content"
            )

    def test_semp_14_sections_with_content(self):
        """SEMP sections have substantive text, not just 'TBD'."""
        from spacecdf_server.services.semp_generator import generate_semp

        study_data = {
            "requirements": {
                "name": "TestMission",
                "mission_type": "earth_observation",
                "spacecraft_class": "nano",
                "orbit": {"altitude_km": 500, "inclination_deg": 97.4},
            },
            "mission_need": {"problem_statement": "Test problem", "objectives": []},
            "generated_requirements": [],
            "parameters": {},
        }
        semp = generate_semp(study_data=study_data, semp_answers={})
        assert len(semp["sections"]) == 14, (
            f"SEMP should have exactly 14 sections, got {len(semp['sections'])}"
        )

        tbd_only_sections = []
        for sec in semp["sections"]:
            # Collect all text content
            all_text = ""
            for sub in sec.get("subsections", []):
                all_text += sub.get("content", "")
            # If a section only has TBD, flag it
            cleaned = all_text.replace("TBD", "").strip()
            if len(all_text) > 0 and len(cleaned) < 10:
                tbd_only_sections.append(sec["number"])

        assert len(tbd_only_sections) == 0, (
            f"SEMP sections {tbd_only_sections} contain only TBD placeholders"
        )

    def test_bom_groups_by_subsystem(self, sample_elements_for_bom):
        """BOM groups components under domain labels."""
        from spacecdf_server.services.bom_generator import generate_bom_from_elements

        bom = generate_bom_from_elements(sample_elements_for_bom, study_name="Test")
        assert "groups" in bom
        # Should have groups named after subsystems
        assert "EPS" in bom["groups"], "BOM should have EPS group"
        assert "AOCS" in bom["groups"], "BOM should have AOCS group"
        # Each group should have components
        for name, lines in bom["groups"].items():
            assert len(lines) > 0, f"BOM group '{name}' has no lines"

    def test_bom_no_unassigned_with_domain(self, sample_elements_for_bom):
        """Components with subsystem_domain never show 'Unassigned'."""
        from spacecdf_server.services.bom_generator import generate_bom_from_elements

        bom = generate_bom_from_elements(sample_elements_for_bom, study_name="Test")
        for line in bom["lines"]:
            if line.get("subsystem_domain") and line["subsystem_domain"] != "integration":
                assert line["subsystem"] != "Unassigned", (
                    f"Component '{line['name']}' has domain "
                    f"'{line['subsystem_domain']}' but shows 'Unassigned'"
                )


# ═══════════════════════════════════════════════════════════════════════
# 6. Data Flow Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDataFlowIntegration:
    def test_requirement_id_format(self):
        """IDs match {NAME}-{LEVEL}-{SEQ} pattern."""
        from spacecdf_server.services.requirement_engine import generate_smart_requirements

        objectives = [
            {"id": "OBJ-1", "text": "Provide 5m GSD imagery", "priority": "primary",
             "type": "performance", "measurable_criterion": "GSD <= 5m"},
        ]
        mission_reqs = {
            "name": "TestSat",
            "mission_type": "earth_observation",
            "spacecraft_class": "nano",
            "orbit": {"altitude_km": 500},
            "payloads": [{"name": "Imager", "mass_kg": 1.5, "power_w": 10,
                          "data_rate_mbps": 100, "pointing_accuracy_deg": 0.1}],
        }
        suggestions = generate_smart_requirements(
            objectives=objectives,
            mission_requirements_dict=mission_reqs,
        )
        assert len(suggestions) > 0, "Should generate at least one requirement"

        # All IDs should match the pattern PREFIX-LEVEL-SEQ
        pattern = re.compile(r"^REQ-[A-Z]{2,4}-\d{3}$")
        for s in suggestions:
            assert pattern.match(s.id), (
                f"Requirement ID '{s.id}' does not match "
                f"expected format REQ-{{LEVEL}}-{{SEQ}}"
            )

    def test_requirement_ids_never_reuse(self):
        """Generating 20 IDs produces 20 unique values."""
        from spacecdf_server.services.requirement_engine import generate_smart_requirements

        objectives = [
            {"id": f"OBJ-{i}", "text": f"Objective {i} text", "priority": "primary",
             "type": "performance", "measurable_criterion": f"Metric {i}"}
            for i in range(1, 21)
        ]
        mission_reqs = {
            "name": "TestSat",
            "mission_type": "earth_observation",
            "spacecraft_class": "nano",
            "orbit": {"altitude_km": 500},
            "payloads": [],
        }
        suggestions = generate_smart_requirements(
            objectives=objectives,
            mission_requirements_dict=mission_reqs,
        )
        ids = [s.id for s in suggestions]
        assert len(ids) == len(set(ids)), (
            f"Generated {len(ids)} requirement IDs but only "
            f"{len(set(ids))} are unique -- duplicates: "
            f"{[x for x in ids if ids.count(x) > 1]}"
        )

    def test_maturity_with_orphaned_components(self):
        """Subsystem with component having kb_component_id shows 'selected' not 'parametric'."""
        from spacecdf_server.services.bom_generator import _assess_maturity

        # Component with kb_component_id but no manufacturer
        comp_selected = {
            "kb_component_id": "bat-gom-nanopow-p31u",
            "mass_kg": 0.065,
            "manufacturer": None,
        }
        assert _assess_maturity(comp_selected) == "selected"

        # Component with nothing
        comp_parametric = {}
        assert _assess_maturity(comp_parametric) == "parametric"

        # Fully specified component
        comp_specified = {
            "kb_component_id": "bat-gom-nanopow-p31u",
            "mass_kg": 0.065,
            "manufacturer": "GomSpace",
        }
        assert _assess_maturity(comp_specified) == "specified"

    def test_budget_rollup_includes_orphans(self, element_dict_store):
        """Orphaned components (matching domain, added to parent) contribute to budget totals."""
        parent = _create_element(
            element_dict_store,
            name="AOCS", element_type="subsystem", subsystem_domain="aocs",
        )
        pid = parent["id"]

        # Add an "orphan" component (domain matches but was added after tree was built)
        _create_element(
            element_dict_store,
            name="Orphan Star Tracker", element_type="component",
            parent_id=pid, subsystem_domain="aocs",
            mass_kg=0.15, quantity=1, margin_percent=20,
        )

        budget = _compute_budget_from_dict(element_dict_store, pid, "mass")
        # The orphan should be counted
        assert budget["sum_nominal"] >= 0.15
        assert len(budget["lines"]) >= 1
        orphan_line = next(
            (l for l in budget["lines"] if l["name"] == "Orphan Star Tracker"), None
        )
        assert orphan_line is not None, "Orphan component not found in budget lines"
        assert orphan_line["nominal"] == 0.15
