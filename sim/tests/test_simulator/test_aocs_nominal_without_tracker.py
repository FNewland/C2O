"""NOMINAL before a star tracker keeps a bounded attitude estimate (2026-11-08).

COM-004 (ruling Q16) commands wheel-controlled NOMINAL from the LEOP sun hold
BEFORE COM-003 brings a star tracker up. The card says knowledge stays on the
coarse sun/magnetometer path until then, but the estimator ran that path only
in DETUMBLE/COARSE_SUN or with every gyro off: in NOMINAL it coasted on the
uncalibrated gyros. With a realistic bias the controller followed the drifting
estimate off nadir (the V-OPS-12 take stalled at 43 deg and diverged).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from smo_common import attitude as att
from smo_simulator.engine import SimulationEngine

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


def test_nominal_without_tracker_stays_on_nadir_with_a_gyro_bias():
    eng = SimulationEngine(CONFIG_DIR, speed=1.0)
    d = eng._dispatcher
    tc = lambda *b: d.dispatch(8, 1, bytes(b), None)   # noqa: E731
    run = lambda n: [eng._tick_once(1.0) for _ in range(int(n))]  # noqa: E731
    tc(55); run(20)                       # OBC_BOOT_APP
    tc(19, 7); run(5)                     # EPS_POWER_ON aocs_wheels
    for w in range(4):
        tc(3, w)                          # AOCS_ENABLE_WHEEL
    tc(0, 3); run(300)                    # COARSE_SUN (no tracker on)
    aocs = eng.subsystems["aocs"]
    s = aocs._state
    aocs._gyro_bias_inject = [0.1, -0.08, 0.05]   # uncalibrated gyros, deg/s
    tc(0, 4)                              # NOMINAL, still no tracker
    worst_late = 0.0
    for t in range(900):
        run(1)
        if s.st_valid:
            break
        if t > 600 and s.mode == 4:
            est_err = att.quat_angle_deg(np.asarray(s.q_true, float), aocs._est_quat())
            worst_late = max(worst_late, est_err, s.att_error)
    assert not s.st_valid, "a tracker came up: this test needs the coarse path"
    assert s.mode in (4, 8), s.mode
    assert worst_late < 10.0, f"estimate/pointing drifted to {worst_late:.1f} deg"
