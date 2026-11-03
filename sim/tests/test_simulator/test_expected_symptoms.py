"""Expected first symptom per failure (Franz's ruling, 2026-11-03).

configs/eosat1/instructor/expected_symptoms.yaml names, for every failure in
the catalogue, the events / S12 monitors / parameters it is expected to trip
first; the instructor recorder times "inject -> first symptom" to the first of
those instead of the first warning of any kind. tools/failure_symptoms.py
injects every failure headless and checks the list (slow test below).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from smo_simulator import failure_catalog as fc
from smo_simulator.engine import SimulationEngine

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "configs" / "eosat1"
KINDS = {"event", "s12", "param", "clock_offset_s"}


def _doc():
    return yaml.safe_load((CONFIG / "instructor" / "expected_symptoms.yaml")
                          .read_text(encoding="utf-8"))["expected_symptoms"]


def test_every_failure_has_expected_symptoms():
    doc = _doc()
    names = {f"{s}.{f}" for s, f in fc.all_failure_names()}
    missing = sorted(n for n in names if not (doc.get(n) or {}).get("symptoms"))
    stale = sorted(set(doc) - names)
    assert not missing, f"failures without expected symptoms: {missing}"
    assert not stale, f"expected symptoms for failures that do not exist: {stale}"


def test_every_symptom_names_something_real():
    events = {int(e["id"]) for e in yaml.safe_load(
        (CONFIG / "events" / "event_catalog.yaml").read_text())["events"]}
    params = {int(p["id"]) for p in yaml.safe_load(
        (CONFIG / "telemetry" / "parameters.yaml").read_text())["parameters"]}
    s12 = {int(str(d["param_id"]), 0) if isinstance(d["param_id"], str) else int(d["param_id"])
           for d in yaml.safe_load((CONFIG / "monitoring" / "s12_definitions.yaml")
                                   .read_text())["s12_definitions"]}
    limits = {int(r["param_id"]) for r in yaml.safe_load(
        (CONFIG / "mcs" / "limits.yaml").read_text())["limits"]}
    for name, entry in _doc().items():
        assert entry.get("context", "nominal") in ("nominal", "imaging", "contact"), name
        if entry.get("checkable") is False:
            assert entry.get("reason"), f"{name}: not checkable needs a reason"
        for sym in entry["symptoms"]:
            kind = KINDS & set(sym)
            assert len(kind) == 1, (name, sym)
            if "event" in sym:
                assert int(sym["event"]) in events, (name, sym)
            if "s12" in sym:
                assert int(sym["s12"]) in s12, (name, sym)
            if "param" in sym:
                assert int(sym["param"]) in params, (name, sym)
                assert {"limit", "below", "above", "change"} & set(sym), (name, sym)
                assert set(sym) <= {"param", "limit", "below", "above", "change",
                                    "when", "for_s"}, (name, sym)
                if sym.get("limit"):
                    assert int(sym["param"]) in limits, (name, sym)


def test_catalogue_api_carries_them():
    d = fc.to_dict(CONFIG)
    rows = [f for s in d["subsystems"] for f in s["failures"]]
    assert rows and all(f["expected_symptoms"] for f in rows)


def _engine():
    e = SimulationEngine(CONFIG, speed=1.0)
    ok, why = e.submit_instructor_cmd_sync({"type": "set_phase", "phase": 6})
    assert ok, why
    return e


def _lane(e, failure):
    return next(f for f in e.instructor_rec.fault_lanes() if f["failure"] == failure)


def test_first_symptom_is_the_expected_one_not_the_first_warning():
    """An unrelated warning after the inject must not count as its symptom."""
    e = _engine()
    for _ in range(3):
        e._tick_once(1.0)
    ok, why = e.submit_instructor_cmd_sync({
        "type": "failure_inject", "subsystem": "tcs", "failure": "sensor_drift",
        "magnitude": 10.0, "zone": "battery"})
    assert ok, why
    e._tick_once(1.0)
    # An unrelated TCS warning (battery undertemp warning event) right away.
    e._emit_event({"event_id": 0x0402, "severity": 2,
                   "description": "unrelated TCS warning"})
    e._tick_once(1.0)
    rec = _lane(e, "sensor_drift")
    assert rec["expected"], rec
    # The drift's expected symptom is the battery reading > +14 C; the
    # unrelated warning is not taken.
    if rec["symptom_ts"] is not None:
        assert rec["symptom_kind"] == "param" and rec["symptom_param"] == 0x0407


def test_param_symptom_is_detected_and_reaches_the_ground():
    e = _engine()
    e._handle_instructor_cmd({"type": "override_passes", "enabled": True})
    for sid in range(1, 8):
        e.set_hk_enabled(sid, True)
    for _ in range(3):
        e._tick_once(1.0)
    tcs = e.subsystems["tcs"]
    ok, why = e.submit_instructor_cmd_sync({
        "type": "failure_inject", "subsystem": "tcs", "failure": "sensor_drift",
        "magnitude": 10.0, "zone": "battery"})
    assert ok, why
    for _ in range(200):
        e._tick_once(1.0)
        rec = _lane(e, "sensor_drift")
        if rec["ground_ts"] is not None:
            break
    rec = _lane(e, "sensor_drift")
    assert rec["symptom_kind"] == "param" and rec["symptom_param"] == 0x0407
    assert rec["latency"]["to_symptom_s"] is not None
    assert rec["latency"]["to_symptom_s"] <= 2.0
    assert rec["ground_ts"] is not None
    assert "param_base" not in rec


def test_event_symptom_at_any_severity():
    e = _engine()
    for _ in range(3):
        e._tick_once(1.0)
    ok, why = e.submit_instructor_cmd_sync({
        "type": "failure_inject", "subsystem": "aocs", "failure": "gyro_bias",
        "axis": 0, "bias": 0.05})
    assert ok, why
    e._tick_once(1.0)
    e._emit_event({"event_id": 0x020B, "severity": 1,
                   "description": "GYRO_BIAS_HIGH"})   # INFO severity
    e._tick_once(1.0)
    rec = _lane(e, "gyro_bias")
    assert rec["symptom_ts"] is not None and rec["symptom_kind"] == "event"


@pytest.mark.slow
def test_failure_symptom_tool_check_passes():
    """Inject every failure headless; each one trips one of its expected
    symptoms (or is declared not checkable with a reason)."""
    proc = subprocess.run([sys.executable, "tools/failure_symptoms.py", "--check"],
                          cwd=REPO, capture_output=True, text=True, timeout=5400)
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-2000:]
