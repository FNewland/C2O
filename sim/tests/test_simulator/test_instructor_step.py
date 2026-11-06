"""Instructor `step`: advance N sim-seconds while frozen, then stay frozen."""
import os
import threading
import time
from pathlib import Path

import pytest

from smo_simulator.engine import SimulationEngine

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


@pytest.fixture
def engine(tmp_path):
    os.environ.setdefault("SMO_DUMP_DIR", str(tmp_path / "dumps"))
    return SimulationEngine(CONFIG_DIR)


def test_step_is_validated():
    ok, _ = SimulationEngine.validate_instructor_cmd({"type": "step", "seconds": 30})
    assert ok
    ok, why = SimulationEngine.validate_instructor_cmd({"type": "step", "seconds": -1})
    assert not ok and "seconds" in why
    ok, _ = SimulationEngine.validate_instructor_cmd({"type": "step", "seconds": 99999})
    assert not ok


def test_step_refused_while_running(engine):
    engine.speed = 1.0
    engine._handle_instructor_cmd({"type": "step", "seconds": 30})
    assert engine._step_remaining_s == 0.0


def test_step_advances_sim_time_and_stays_frozen(engine):
    engine._handle_instructor_cmd({"type": "freeze"})
    engine._handle_instructor_cmd({"type": "step", "seconds": 25})
    assert engine._step_remaining_s == 25.0
    t0 = engine._sim_time
    engine.running = True
    th = threading.Thread(target=engine._run_loop, daemon=True)
    th.start()
    try:
        deadline = time.monotonic() + 20
        while engine._step_remaining_s > 0 and time.monotonic() < deadline:
            time.sleep(0.05)
        time.sleep(0.3)
    finally:
        engine.running = False
        th.join(timeout=5)
    assert engine.speed == 0.0
    assert engine._step_remaining_s == 0.0
    assert abs((engine._sim_time - t0).total_seconds() - 25.0) < 1e-6


def test_resume_cancels_a_pending_step(engine):
    engine._handle_instructor_cmd({"type": "freeze"})
    engine._handle_instructor_cmd({"type": "step", "seconds": 600})
    engine._handle_instructor_cmd({"type": "resume"})
    assert engine._step_remaining_s == 0.0
