"""Continuous imaging drains the battery, and the planner says so (2026-11-03).

tools/power_budget.py derives the sustainable imaging duty cycle (77 % of an
orbit at the worst beta with the 10 % design margin); activity_types.yaml
carries it on imaging_pass and PowerConstraintChecker warns above it.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from smo_planner.activity_scheduler import ActivityScheduler
from smo_planner.constraint_checkers import (
    PowerConstraintChecker, SUSTAINABLE_IMAGING_DUTY_PCT, validate_plan,
)

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"
T0 = datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc)


def _types():
    return yaml.safe_load((CONFIG_DIR / "planning" / "activity_types.yaml")
                          .read_text())["activity_types"]


def _orbit_start():
    period = 95.0 * 60.0
    k = int(T0.timestamp() / period) + 1
    return datetime.fromtimestamp(k * period, tz=timezone.utc)


def test_imaging_pass_carries_the_sustainable_duty_cycle():
    imaging = next(a for a in _types() if a["name"] == "imaging_pass")
    assert imaging["power_constraints"]["sustainable_duty_pct"] == \
        SUSTAINABLE_IMAGING_DUTY_PCT == 77


def test_one_orbit_of_continuous_imaging_warns():
    t = _orbit_start()
    acts = [{"id": i, "name": "imaging_pass",
             "start_time": (t + timedelta(seconds=660 * i)).isoformat(),
             "duration_s": 660, "power_constraints": {"sustainable_duty_pct": 77}}
            for i in range(8)]                    # 88 min of a 95 min orbit
    (v,) = PowerConstraintChecker().check_imaging_duty_cycle(acts)
    assert v.severity == "warning"
    assert v.message_key == "imaging_power_duty"
    assert v.message_params["pct"] == 93 and v.message_params["limit"] == 77
    assert "77 %" in v.message


def test_a_normal_imaging_orbit_does_not_warn():
    t = _orbit_start()
    acts = [{"id": i, "name": "imaging_pass",
             "start_time": (t + timedelta(minutes=20 * i)).isoformat(),
             "duration_s": 660} for i in range(3)]
    assert PowerConstraintChecker().check_imaging_duty_cycle(acts) == []


def test_validate_plan_reports_it_through_the_scheduler():
    sched = ActivityScheduler(_types())
    t = _orbit_start()
    for i in range(8):
        sched.add_activity("imaging_pass", (t + timedelta(seconds=665 * i)).isoformat())
    result = validate_plan(sched.get_schedule())
    keys = [v.message_key for v in result.violations]
    assert "imaging_power_duty" in keys
