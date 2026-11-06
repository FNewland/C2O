# COARSE_SUN on magnetorquers alone does not hold the Sun (found 2026-11-05)

Found while filming LEOP-005 and LEOP-003 for the course videos. **Not fixed**: the
gain experiment below shows it is not a tuning problem, and the change belongs
in an AOCS session, not a video one.

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
