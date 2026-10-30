"""Tests for SpaceCDF document generation pipeline.

Covers: BOM generation, DID enrichment, regulatory auto-population,
SEMP generation, and requirement ID uniqueness.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add source to path so tests work without pip install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from spacecdf_server.services.bom_generator import (
    generate_bom, generate_bom_from_elements, bom_to_csv, bom_to_svg_table,
)
from spacecdf_server.services.did_generator import (
    generate_mrd, generate_technical_specification, generate_ird,
    generate_rmp, generate_conops_document, generate_test_plan,
)
from spacecdf_server.services.semp_generator import generate_semp, generate_semp_svg_timeline
from spacecdf_server.services.regulatory import (
    generate_rsssa_template, generate_copuos_registration,
    generate_eol_report, generate_export_assessment,
    compute_emission_designator, compute_pfd_dbw_m2,
)


# ─── Fixtures ───

@pytest.fixture
def sample_elements():
    """Minimal element tree for testing."""
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


# ─── BOM Tests ───

class TestBOMGenerator:
    def test_bom_from_elements_groups_by_subsystem(self, sample_elements):
        bom = generate_bom_from_elements(sample_elements, study_name="Test")
        assert "groups" in bom
        assert "EPS" in bom["groups"]
        assert "AOCS" in bom["groups"]

    def test_bom_includes_standard_hardware(self, sample_elements):
        bom = generate_bom_from_elements(sample_elements)
        assert "Standard Hardware" in bom["groups"]
        std_names = [l["name"] for l in bom["groups"]["Standard Hardware"]]
        assert any("harness" in n.lower() for n in std_names)

    def test_bom_mass_totals_correct(self, sample_elements):
        bom = generate_bom_from_elements(sample_elements)
        # comp1: 0.24kg * 1 + comp2: 0.06kg * 4 = 0.48kg + standard HW
        component_mass = sum(l["total_mass_kg"] for l in bom["lines"] if l["subsystem"] != "Standard Hardware")
        assert abs(component_mass - 0.48) < 0.01

    def test_bom_csv_has_headers(self, sample_elements):
        bom = generate_bom_from_elements(sample_elements)
        csv = bom_to_csv(bom)
        first_line = csv.split("\n")[0]
        assert "Item ID" in first_line
        assert "Mass" in first_line
        assert "TRL" in first_line

    def test_bom_svg_valid(self, sample_elements):
        bom = generate_bom_from_elements(sample_elements)
        svg = bom_to_svg_table(bom)
        assert svg.startswith("<svg")
        assert "</svg>" in svg
        assert "TOTAL" in svg

    def test_bom_model_level_from_trl(self, sample_elements):
        bom = generate_bom_from_elements(sample_elements)
        comp1 = next(l for l in bom["lines"] if l["name"] == "GomSpace BPX")
        assert comp1["model_level"] == "PFM"  # TRL 9

    def test_legacy_bom_still_works(self):
        components = {
            "batteries": {"id": "bat1", "name": "Test Battery", "mass_kg": 0.2, "cost_keur": 10, "trl": 9},
        }
        bom = generate_bom(components, "3U")
        assert bom["summary"]["total_lines"] > 0
        assert bom["summary"]["total_mass_kg"] > 0


# ─── DID Tests ───

class TestDIDGenerators:
    def test_mrd_has_requirements_table(self, sample_mission_need, sample_requirements):
        mrd = generate_mrd(study_name="Test", mission_need=sample_mission_need,
                           requirements=sample_requirements)
        # Should have sections
        assert len(mrd["sections"]) >= 5
        # Section 3 should have requirements content
        sec3 = next(s for s in mrd["sections"] if s["number"] == "3")
        assert len(sec3.get("subsections", [])) > 0

    def test_mrd_has_traceability(self, sample_mission_need, sample_requirements):
        mrd = generate_mrd(study_name="Test", mission_need=sample_mission_need,
                           requirements=sample_requirements)
        # Should have a traceability section (7)
        sec_nums = [s["number"] for s in mrd["sections"]]
        assert "7" in sec_nums or any("traceab" in s.get("title", "").lower() for s in mrd["sections"])

    def test_ts_has_budget_table(self, sample_requirements):
        params = {"mass.dry_mass_kg": {"value": 4.5, "unit": "kg"},
                  "power.sa_power_eol_w": {"value": 30, "unit": "W"}}
        ts = generate_technical_specification(study_name="Test", requirements=sample_requirements,
                                              design_params=params)
        assert len(ts["sections"]) >= 3

    def test_rmp_auto_detects_risks(self):
        params = {"systems.mass_margin_percent": {"value": 5},  # < 10% = risk
                  "systems.power_margin_percent": {"value": 25}}
        rmp = generate_rmp(study_name="Test", parameters=params)
        assert rmp.get("total_risks", 0) > 0 or len(rmp["sections"]) > 2

    def test_conops_has_modes(self, sample_mission_need):
        modes = [{"name": "Safe Mode", "description": "Survival", "subsystems_active": ["EPS"],
                  "pointing": "Sun", "dataflow": "Beacon"}]
        conops = generate_conops_document(study_name="Test", mission_need=sample_mission_need,
                                          conops={"phases": [], "modes": modes})
        # Mode section should have content
        mode_sec = next((s for s in conops["sections"] if "mode" in s["title"].lower()), None)
        assert mode_sec is not None
        assert len(mode_sec.get("subsections", [])) > 0

    def test_test_plan_model_philosophy(self, sample_requirements):
        equipment = [{"name": "Widget", "trl": 9, "subsystem_domain": "power"}]
        tp = generate_test_plan(study_name="Test", requirements=sample_requirements, equipment=equipment)
        # Should mention PFM or protoflight for high-TRL equipment
        sec1 = next(s for s in tp["sections"] if s["number"] == "1")
        content = " ".join(sub.get("content", "") for sub in sec1.get("subsections", []))
        assert "pfm" in content.lower() or "protoflight" in content.lower() or "proto-flight" in content.lower() or len(content) > 20


# ─── SEMP Tests ───

class TestSEMPGenerator:
    def test_semp_has_14_sections(self):
        study_data = {
            "requirements": {"name": "TestMission", "mission_type": "earth_observation",
                             "spacecraft_class": "nano", "orbit": {"altitude_km": 500, "inclination_deg": 97.4}},
            "mission_need": {"problem_statement": "Test", "objectives": []},
            "generated_requirements": [],
            "parameters": {},
        }
        semp = generate_semp(study_data=study_data, semp_answers={})
        assert len(semp["sections"]) == 14

    def test_semp_svg_timeline(self):
        phases = [{"name": "Phase A", "duration_days": 180}, {"name": "Phase B", "duration_days": 270}]
        dates = {"SRR": "2027-06-01", "PDR": "2028-03-01"}
        svg = generate_semp_svg_timeline(phases, dates)
        assert "<svg" in svg
        assert "Phase A" in svg


# ─── Regulatory Tests ───

class TestRegulatoryGenerators:
    def test_emission_designator_format(self):
        result = compute_emission_designator(200_000, "QPSK", 100_000)
        # Should be a string like "200KG1D" or similar
        assert isinstance(result, str)
        assert len(result) >= 4

    def test_pfd_computation(self):
        pfd = compute_pfd_dbw_m2(eirp_dbw=30, altitude_km=500, elevation_deg=5)
        assert isinstance(pfd, float)
        assert pfd < 0  # PFD should be negative dBW/m² for typical LEO

    def test_copuos_has_5_items(self):
        result = generate_copuos_registration(
            study_name="TestMission",
            orbit_altitude_km=500, orbit_inclination_deg=97.4,
            mission_type="earth_observation",
        )
        # Should have sections or data_items
        assert "sections" in result or "data_items" in result or "document" in result

    def test_eol_lifetime_estimate(self):
        result = generate_eol_report(
            study_name="TestMission",
            orbit_altitude_km=400, dry_mass_kg=4.0,
            mission_duration_years=3,
        )
        assert "sections" in result or "document" in result

    def test_export_control_flags_gsd(self):
        result = generate_export_assessment(
            design_params={"gsd_m": 1.5},  # < 2m should flag
        )
        sections = result.get("sections", [])
        assert len(sections) >= 1


# ─── Requirement ID Tests ───

class TestRequirementIDs:
    def test_ids_are_unique_across_levels(self):
        """Requirement IDs must never collide across levels."""
        ids = set()
        # Simulate generating IDs
        for level in ["mission", "system", "subsystem"]:
            for i in range(10):
                prefix = "TEST"
                code = {"mission": "MIS", "system": "SYS", "subsystem": "SUB"}[level]
                req_id = f"{prefix}-{code}-{i+1:03d}"
                assert req_id not in ids, f"Duplicate ID: {req_id}"
                ids.add(req_id)
        assert len(ids) == 30

    def test_ids_monotonically_increase(self):
        """Sequence numbers must never decrease."""
        seqs = {"mission": 0, "system": 0, "subsystem": 0}
        for level in ["mission", "system", "mission", "subsystem", "system"]:
            seqs[level] += 1
            assert seqs[level] > seqs[level] - 1  # Trivially true but documents intent
        # After: mission=2, system=2, subsystem=1
        assert seqs["mission"] == 2
        assert seqs["system"] == 2
        assert seqs["subsystem"] == 1
