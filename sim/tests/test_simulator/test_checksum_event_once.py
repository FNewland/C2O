"""IMAGE_CHECKSUM_ERROR (0x0607) fires once per new error, not forever (2026-11-08).

It used to re-fire at random (1 %/s) for as long as the counter was non-zero,
so a single bad frame raised the same alarm every ~100 s for the session.
"""
import queue
from pathlib import Path
from types import SimpleNamespace

from smo_simulator.engine import SimulationEngine

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


def test_one_bad_frame_one_event():
    eng = SimulationEngine(CONFIG_DIR, speed=1.0)
    pl = eng.subsystems["payload"]
    q = queue.Queue()
    pl._engine = SimpleNamespace(_model_event_queue=q)
    params = dict(eng.params)
    orbit = eng.orbit.propagate_to(eng._sim_time)

    def tick_and_count(n):
        for _ in range(n):
            pl.tick(1.0, orbit, params)
        out = []
        while not q.empty():
            out.append(q.get_nowait())
        return [e for e in out if e["event_id"] == 0x0607]

    tick_and_count(3)
    pl._state.checksum_errors += 1
    assert len(tick_and_count(1)) == 1
    assert tick_and_count(600) == [], "the same error must not raise the event again"
