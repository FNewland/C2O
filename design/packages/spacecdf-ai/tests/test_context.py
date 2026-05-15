"""Tests for study context serialization."""
from spacecdf_ai.context import build_study_context, build_agent_context, build_review_context


def test_build_study_context_minimal():
    ctx = build_study_context({"name": "Test Mission"})
    assert "Test Mission" in ctx


def test_build_study_context_with_elements():
    elements = [
        {"name": "Spacecraft", "type": "system", "depth": 0, "properties": {"mass_kg": 12}},
        {"name": "EPS", "type": "subsystem", "depth": 1, "properties": {"mass_kg": 1.5, "power_w": 5}},
    ]
    ctx = build_study_context({"name": "Test"}, elements=elements)
    assert "Spacecraft" in ctx
    assert "EPS" in ctx
    assert "12 kg" in ctx


def test_build_study_context_truncates():
    elements = [{"name": f"El-{i}", "type": "component", "depth": 0, "properties": {}} for i in range(300)]
    ctx = build_study_context({"name": "Big"}, elements=elements, max_elements=10)
    assert "290 more elements truncated" in ctx


def test_build_agent_context():
    ctx = build_agent_context("power", {"sa_area_m2": 0.5, "battery_wh": 40})
    assert "power" in ctx
    assert "sa_area_m2" in ctx


def test_build_review_context_includes_interfaces():
    ctx = build_review_context(
        {"name": "Review"},
        interfaces=[{"source_name": "EPS", "target_name": "OBC", "type": "power"}],
    )
    assert "EPS -> OBC" in ctx
    assert "Interfaces" in ctx


def test_build_review_context_includes_conflicts():
    ctx = build_review_context(
        {"name": "Review"},
        conflicts=[{"severity": "critical", "description": "Mass budget exceeded"}],
    )
    assert "Mass budget exceeded" in ctx
