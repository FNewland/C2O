"""Tests for the Requirement Pydantic model (SCDF-111)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from spacecdf_common.models.requirement import (
    Requirement,
    RequirementLevel,
    RequirementStatus,
)


def _make_requirement(**overrides) -> Requirement:
    """Helper: create a valid mission requirement with overrides."""
    defaults = {
        "id": "MR-001",
        "study_id": "study-1",
        "parent_id": None,
        "level": RequirementLevel.MISSION,
        "code": "MR-001",
        "text": "The mission shall have a design lifetime of at least 3 years",
        "rationale": "Minimum science return",
        "status": RequirementStatus.DRAFT,
    }
    defaults.update(overrides)
    return Requirement(**defaults)


# -------------------------------------------------------------------
# Roundtrip serialization
# -------------------------------------------------------------------
class TestRequirementRoundtrip:
    def test_roundtrip_json(self):
        req = _make_requirement()
        payload = req.model_dump_json()
        restored = Requirement.model_validate_json(payload)
        assert restored.id == req.id
        assert restored.level == RequirementLevel.MISSION
        assert restored.status == RequirementStatus.DRAFT
        assert restored.code == "MR-001"

    def test_roundtrip_dict(self):
        req = _make_requirement()
        d = req.model_dump()
        restored = Requirement.model_validate(d)
        assert restored.text == req.text


# -------------------------------------------------------------------
# Hierarchy validation
# -------------------------------------------------------------------
class TestHierarchyValidation:
    def test_mission_no_parent_ok(self):
        req = _make_requirement(level=RequirementLevel.MISSION, parent_id=None)
        assert req.level == RequirementLevel.MISSION

    def test_subsystem_requires_parent(self):
        with pytest.raises(ValueError, match="Subsystem requirements must have a system parent"):
            _make_requirement(level=RequirementLevel.SUBSYSTEM, parent_id=None)

    def test_subsystem_with_parent_ok(self):
        req = _make_requirement(
            id="SSR-001",
            level=RequirementLevel.SUBSYSTEM,
            parent_id="SR-001",
            code="SSR-PWR-001",
        )
        assert req.parent_id == "SR-001"

    def test_system_requires_parent(self):
        with pytest.raises(ValueError, match="System requirements must have a mission parent"):
            _make_requirement(level=RequirementLevel.SYSTEM, parent_id=None)

    def test_system_with_parent_ok(self):
        req = _make_requirement(
            id="SR-001",
            level=RequirementLevel.SYSTEM,
            parent_id="MR-001",
            code="SR-PWR-001",
        )
        assert req.parent_id == "MR-001"


# -------------------------------------------------------------------
# is_evaluable
# -------------------------------------------------------------------
class TestIsEvaluable:
    def test_evaluable_when_threshold_set(self):
        req = _make_requirement(
            threshold_param_path="power.battery_capacity_wh",
            threshold_op=">=",
            threshold_value="100",
        )
        assert req.is_evaluable() is True

    def test_not_evaluable_when_threshold_missing(self):
        req = _make_requirement(threshold_param_path=None, threshold_op=None)
        assert req.is_evaluable() is False

    def test_not_evaluable_when_op_missing(self):
        req = _make_requirement(
            threshold_param_path="power.battery_capacity_wh",
            threshold_op=None,
        )
        assert req.is_evaluable() is False

    def test_not_evaluable_when_path_missing(self):
        req = _make_requirement(
            threshold_param_path=None,
            threshold_op=">=",
        )
        assert req.is_evaluable() is False


# -------------------------------------------------------------------
# Enum values
# -------------------------------------------------------------------
class TestEnums:
    def test_requirement_levels(self):
        assert RequirementLevel.MISSION.value == "mission"
        assert RequirementLevel.SYSTEM.value == "system"
        assert RequirementLevel.SUBSYSTEM.value == "subsystem"

    def test_requirement_statuses(self):
        assert RequirementStatus.DRAFT.value == "draft"
        assert RequirementStatus.APPROVED.value == "approved"
        assert RequirementStatus.VIOLATED.value == "violated"
        assert RequirementStatus.VERIFIED.value == "verified"
        assert RequirementStatus.RETIRED.value == "retired"


# -------------------------------------------------------------------
# Optional fields
# -------------------------------------------------------------------
class TestOptionalFields:
    def test_verification_fields(self):
        req = _make_requirement(
            verification_method="T",
            verification_phase="CDR",
            verification_evidence="Test report TR-001",
        )
        assert req.verification_method == "T"
        assert req.verification_phase == "CDR"
        assert req.verification_evidence == "Test report TR-001"

    def test_derived_from(self):
        req = _make_requirement(derived_from_requirement_id="MR-EXT-001")
        assert req.derived_from_requirement_id == "MR-EXT-001"

    def test_responsible_position(self):
        req = _make_requirement(responsible_position="power_engineer")
        assert req.responsible_position == "power_engineer"
