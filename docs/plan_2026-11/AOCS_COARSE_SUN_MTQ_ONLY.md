# COARSE_SUN on magnetorquers alone did not hold the Sun (found 2026-11-05, fixed 2026-11-06)

Found while filming LEOP-005 and LEOP-003 for the course videos. **Fixed 2026-11-06**
(Franz: "fix the model now"): see the last section.

## What the cards expect

LEOP-005 Step 4 (`procedures/leop/sun_acquisition.md`): `aocs.att_error` (0x0217)
< 15° within 600 s, rates < 0.5°/s, and "a degree-class, slowly-hunting hold,
not a wheel-tight one. Rates of a few hundredths to ~0.2 deg/s while it hunts
are normal here." GO/NO-GO: "Sun-pointing achieved within 15 degrees and holding".
The wheels are still disabled (COM-004 enables them).

## What the model does

From breakpoint `card-LEOP-005`, run offline at 1 s ticks for an hour
(`SimulationEngine` + `_tick_once`, sun-pointing error and peak body rate):

| t (s) | mode | error (°) | peak rate (°/s) |
|---:|---|---:|---:|
| 0 | DETUMBLE | 0.1 | 0.014 |
| 120 | COARSE_SUN | 132.5 | 0.19 |
| 600 | COARSE_SUN | 42.7 | 0.31 |
| 720 | COARSE_SUN | 18.6 | 0.41 |
| 960 | COARSE_SUN | 92.3 | 0.31 |
| 1680 | COARSE_SUN | 2.7 | 0.27 |
| 1920 | COARSE_SUN | 47.4 (eclipse: frozen) | 0.21 |
| 3480 | COARSE_SUN | 47.4 (eclipse) | 0.52 |

* The error swings between ~3° and ~100° with a period of roughly 15–20 min:
  it hunts, but at tens of degrees, not "degree-class".
* In eclipse the rates grow (0.15 → 0.52°/s in ~25 min), past the card's 0.5°/s.
* The live console shows the same: at the `card-LEOP-003` entry, 0x0217 reads
  ~60° and rising, with an HH alarm on screen.

## The magnetic-only branch

`models/aocs_basic.py`, `_tick_coarse_sun`, no-wheels path:

```python
tau_des = self._pd_torque(s, q_ref, w_ref, 0.005, 1.0)
m = np.cross(B_b, tau_des) / (Bmag * Bmag) * 25.0
m += 800.0 * np.cross(self._omega_est, B_b / Bmag)
```

The docstring already says "With fewer wheels it degrades to the slow
magnetic-only crawl" — the cards were written for a hold.

## Gain experiment (reverted)

| Kp × | Kd | behaviour over 1 h |
|---:|---:|---|
| 25 | 800 | as above (baseline) |
| 10 | 2000 | slower, min ~48°, eclipse rates to 0.31 |
| 5 | 3000 | slower still, min ~48°, eclipse rates to 0.29 |
| 15 | 3000 | min ~48°, eclipse rate spike 0.45 |

No pair gives a hold, and every pair lets the rates grow in eclipse. That points at the
damping term's input: in eclipse there is no CSS, so `_omega_est` comes from an estimator
with no sun vector, and damping on a wrong rate pumps energy in. Candidates to look at:

1. damp with a magnetometer-derivative (B-dot) term in eclipse and whenever CSS is invalid,
   which needs no rate estimate (as DETUMBLE does);
2. check `_omega_est` against `omega_true` through an eclipse in COARSE_SUN without gyros;
3. then decide whether the cards' "degree-class hold" is achievable with a 1.6 A·m² rod set
   on this inertia, or whether the cards should say "converging, tens of degrees".

## Effect on the course videos

V-OPS-07 (LEOP-005) and V-OPS-09 (LEOP-003) are written and dry-run but not rendered: on
screen they would contradict their cards. They render as soon as the model holds the Sun
(or the cards are changed).

## The fix (2026-11-06)

`AOCSBasicModel._mag_sun_dipole` replaces the magnetic-only branch. It points ONE axis (+X,
the wing normal) at the Sun and leaves the rotation about the sun line free, and it uses
measured quantities only, never the MEKF:

1. B-dot on the magnetometer, sun and eclipse (damps ω ⊥ B with no rate estimate);
2. sunlit: damping of ω ⊥ sun line from the CSS sun vector's own rate, ω⊥ = ṡ × ŝ
   (`_update_sun_rate`, once per tick, low-passed);
3. sunlit: pointing τ = Kp·(x̂ × ŝ) (full unit demand past 90°), realised ⊥ B as
   m = (B × τ)/|B|², the dampers having first claim on the rod headroom.

Root causes found on the way: damping on the MEKF rate (its gyro-bias estimate wanders in
eclipse by 0.1–0.35 °/s, and the old law then drove the body to that wrong rate after eclipse
exit), the ×25 Kp scaling against a full three-axis sun-frame target, a constant torque about
the minor (Z) axis when the Sun was behind, and saturation scaling the sum so a large pointing
demand starved the damper.

Gains (`aocs.yaml` `magnetorquers.coarse_sun_mag`), swept over three orbits from
`card-LEOP-005`:

| Kp (N·m) | B-dot k | Kd (N·m·s) | first < 15° | sunlit time < 15° | peak rate |
|---:|---:|---:|---:|---:|---:|
| old law | | | 720 s, then lost | — | 0.52 °/s |
| 6e-5 | 5e5 | 5e-3 | 451 s | 73 % | 0.82 °/s |
| **6e-5** | **1e6** | **5e-3** | **482 s** | **62 %** | **0.50 °/s** |
| 6e-5 | 5e5 | 1e-2 | 844 s | 81 % | 0.76 °/s |
| 6e-5 | 2e6 | 5e-3 | 553 s | 53 % | 0.79 °/s |

"Sunlit time < 15°" counts the ~10 min reacquisition after every eclipse exit; once held, the
error stays 0–7° until eclipse, where it drifts (no sun sensor) as the card says.

Also found: the wheel-controlled NOMINAL hold was never the problem (it settles to 0.05° in
~2.5 min). `card-COM-007` had been saved mid-transient (33° error, 0.3 °/s) after COM-005's
mode tests, so every load of it raised attitude alarms. `tools/card_breakpoints.py` now lets
a wheel-controlled attitude settle before each save.

And: the ground limits on 0x0217 (yellow 1°, red 2°) and its S12 1° monitor describe a
wheel-controlled hold. They now carry a validity flag, `aocs.pointing_limits_valid` 0x02D3
(1 in NOMINAL, FINE_POINT, INERTIAL; in SID 2), as the FPA bands carry 0x0426, so a correct
COARSE_SUN hold is no longer a red alarm.
