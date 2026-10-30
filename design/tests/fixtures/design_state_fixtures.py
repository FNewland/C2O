"""Reference design states for reactivity end-to-end tests (SCDF-104).

Each fixture returns a dict of parameter values representing a consistent
design state. These are used by test_reactivity_e2e.py to verify that
ChangeEvent dispatch correctly propagates through the dirty set and
triggers the right agents.
"""
from __future__ import annotations


def minimal_closed_design() -> dict:
    """A minimal valid design: orbit, mass, power, and link budgets closed.

    All margins positive. This is the baseline 'happy path' state.
    """
    return {
        # Orbit
        "orbit.altitude_km": 500,
        "orbit.inclination_deg": 97.4,
        "orbit.period_s": 5676,
        "orbit.eclipse_fraction": 0.35,
        # Mass
        "mass.dry_mass_kg": 4.0,
        "mass.wet_mass_kg": 4.2,
        "mass.margin_percent": 25.0,
        # Power
        "power.sa_power_eol_w": 12.0,
        "power.total_sunlight_w": 8.0,
        "power.battery_capacity_wh": 20.0,
        "power.margin_percent": 30.0,
        # Thermal
        "thermal.max_temp_c": 45.0,
        "thermal.min_temp_c": -10.0,
        "thermal.margin_c": 15.0,
        # Link
        "link.downlink_margin_db": 6.0,
        "link.downlink_rate_bps": 9600,
        # Data
        "data.generated_per_day_gb": 0.5,
        "data.downlinked_per_day_gb": 0.8,
        # AOCS
        "aocs.pointing_accuracy_deg": 1.0,
        # Cost
        "cost.total_meur": 0.8,
    }


def open_power_margin_design() -> dict:
    """A design with battery oversized — power margin is large.

    Useful for testing that power-domain edits propagate correctly.
    """
    state = minimal_closed_design()
    state.update({
        "power.battery_capacity_wh": 50.0,
        "power.margin_percent": 60.0,
        "mass.dry_mass_kg": 5.5,  # heavier due to bigger battery
        "mass.margin_percent": 12.0,
    })
    return state


def open_link_margin_design() -> dict:
    """A design with antenna undersized — link margin is tight.

    Useful for testing that link-domain edits propagate correctly.
    """
    state = minimal_closed_design()
    state.update({
        "link.downlink_margin_db": 1.5,
        "link.downlink_rate_bps": 4800,
    })
    return state


# ---------------------------------------------------------------------------
# Cascade expectations — which agents should run for each scenario
# ---------------------------------------------------------------------------

# Maps ChangeKind -> (expected_dirty_params, expected_domains_affected)
EXPECTED_CASCADES = {
    "parameter_override": {
        "trigger_param": "power.battery_capacity_wh",
        "expected_dirty": {"power.battery_capacity_wh"},
        "expected_domains": {"power", "thermal"},
        "should_not_dirty": {"link.downlink_margin_db", "aocs.pointing_accuracy_deg"},
    },
    "equipment_selection": {
        "trigger_param": "power.selected_battery",
        "expected_dirty": {"power.selected_battery"},
        "expected_domains": {"power"},
        "should_not_dirty": {"link.downlink_margin_db"},
    },
    "requirement_edit": {
        "trigger_param": "requirements.MR-001",
        "expected_dirty": set(),  # stub until SCDF-115
        "expected_domains": set(),
        "should_not_dirty": set(),
    },
    "requirement_delete": {
        "trigger_param": "requirements.MR-002",
        "expected_dirty": set(),  # stub until SCDF-116
        "expected_domains": set(),
        "should_not_dirty": set(),
    },
    "conops_edit": {
        "trigger_param": "conops.mode_0",
        "expected_dirty": set(),  # stub until SCDF-200
        "expected_domains": set(),
        "should_not_dirty": set(),
    },
    "qa_answer": {
        "trigger_param": "qa.question_1",
        "expected_dirty": set(),  # stub
        "expected_domains": set(),
        "should_not_dirty": set(),
    },
    "margin_phase_change": {
        "trigger_param": "mission.phase",
        "expected_dirty": set(),  # stub until SCDF-021
        "expected_domains": set(),
        "should_not_dirty": set(),
    },
    "parametric_fraction_edit": {
        "trigger_param": "parametric.mass_fraction_structure",
        "expected_dirty": set(),  # stub until SCDF-014
        "expected_domains": set(),
        "should_not_dirty": set(),
    },
    "launch_vehicle_selection": {
        "trigger_param": "launch.vehicle_id",
        "expected_dirty": set(),  # stub until SCDF-015
        "expected_domains": set(),
        "should_not_dirty": set(),
    },
    "spectrum_band_selection": {
        "trigger_param": "link.rf_band",
        "expected_dirty": set(),  # stub until SCDF-016
        "expected_domains": set(),
        "should_not_dirty": set(),
    },
    "gate_criterion_toggle": {
        "trigger_param": "gate.criterion_pdr_mass",
        "expected_dirty": set(),  # stub until SCDF-131
        "expected_domains": set(),
        "should_not_dirty": set(),
    },
}
