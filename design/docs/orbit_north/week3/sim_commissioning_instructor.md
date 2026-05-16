---
title: "Thursday Commissioning Simulation — Instructor Pack"
subtitle: "ORBIT NORTH · Thu 20 August 2026 · uOttawa Cyberrange"
course-codes: "GNG 3100 · SYS 5186"
term: "Summer 2026"
version: "v1 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
audience: "instructor + simulator operator"
---

# Thursday Commissioning Simulation — Instructor Pack

**Confidential — instructor and simulator operator only.**

This pack covers the Thursday simulation day. Teams swap operator/
observer roles relative to Wednesday. Day target is **First Light**
on the multispectral imager.

---

## 1. Day at a glance

| When | What | Mode |
|------|------|------|
| 09:00 – 09:30 | Standup, scenario brief to both teams | Instructor-led |
| 09:30 – 12:00 | **Pass-set 1** — Team A operates two compressed passes; Team B observes | Commissioning sim |
| 12:00 – 13:00 | Lunch + observer prep | — |
| 13:00 – 13:15 | Reset + brief for Pass-set 2 | Instructor-led |
| 13:15 – 15:45 | **Pass-set 2** — Team B operates two compressed passes; Team A observes | Commissioning sim |
| 15:45 – 17:00 | Joint debrief, observer presentations, anomaly tickets | Plenary + individual |

Each pass-set covers ~4 simulated ground passes in 2.5 h real time
using a compressed-time multiplier (3×–5× between passes, 1× during
passes). The simulator handles the speed switching.

---

## 2. Scenario configuration

- **Breakpoint:** BP-3 — Commissioning Day Start (NEW; spec in
  `breakpoint_spec.md`).
- **Phase at start:** 4 (LEOP-complete).
- **Initial visibility:** Iqaluit, AOS at scenario T+0.
- **Planned passes during shift:** 4 (Iqaluit, Troll, Iqaluit,
  Troll — actual visibility depends on orbit).
- **Speed multiplier:** instructor-controlled; defaults to 3×
  between passes, 1× during passes.

[Claude Code: confirm the simulator's compressed-time CLI options.]

---

## 3. Procedure expectations

The team is expected to drive commissioning in approximately this
order across the four passes:

**Pass 1.** COM-001 EPS Checkout · COM-002 TCS Verification ·
COM-005 AOCS Mode Transitions (NADIR) · COM-006 TTC Link
Verification.

**Pass 2.** COM-007 OBDH Checkout · COM-008 FDIR Configuration
(load nominal table).

**Pass 3.** COM-009 Payload Power On · COM-010 FPA Cooler Activation
(this runs through the eclipse and into pass 4 — heat sink during
eclipse, cool-down on the day side).

**Pass 4.** COM-011 Payload Calibration · **COM-012 First Light** —
acquire one image of an ocean-current target listed in
`planning/imaging_targets.yaml`.

End-of-shift target state: phase 5+ (NOMINAL ready), payload
calibrated, one usable image acquired.

---

## 4. Anomaly injection menu

Pick one primary and one optional secondary per team. Injection
files live in `~/SpaceMissionSimulation/configs/eosat1/scenarios/`.

| Severity | Scenario file | What students see | Recovery |
|----------|--------------|-------------------|----------|
| Easy | `eps_overcurrent.yaml` (line=`payload`) | Overcurrent on payload power-on | CTG-012 Overcurrent Response |
| Easy | `gs_rf_degradation.yaml` | BER climbs mid-pass | CTG-014 BER Anomaly |
| Medium | `fpa_overtemp.yaml` | FPA cooler can't reach −60 °C | CTG-004 Thermal Exceedance + payload safe |
| Medium | `payload_corrupt_image.yaml` | First image returns corrupt | CTG-015 Corrupted Image Recovery |
| Hard | `aocs_sensor_cascade.yaml` | Star tracker degrades; pointing budget broken | CTG-008 Star Tracker Failure → CTG-002 + defer First Light |
| Hard | `eps_progressive_load_shed.yaml` | Battery degradation forces progressive load-shed during cooler activation | CTG-001 Under-Voltage Load Shed |
| Very hard | `aocs_wheel_failure.yaml` followed by `transponder_failure.yaml` | Wheel locks late in pass 3, then transponder fails next pass — multi-anomaly response | CTG-007 → CTG-003 |

[Claude Code: produce one cue card per scenario, same template as
LEOP day §4.]

---

## 5. Pass operator-side criteria

| Criterion | Pass-set 1 (Team A) | Pass-set 2 (Team B) |
|-----------|---------------------|---------------------|
| Phase advanced to COMMISSIONING (5) | ✓ | ✓ |
| EPS checkout complete with no faults | ✓ | ✓ |
| AOCS NADIR mode achieved, pointing < 0.5° | ✓ | ✓ |
| FDIR nominal table loaded | ✓ | ✓ |
| Payload powered ON | ✓ | ✓ |
| FPA cooler at temperature ( ≤ −55 °C) | ✓ | ✓ |
| First Light image acquired (or formally deferred) | ✓ | ✓ |
| Anomaly tickets filed for all injections | ✓ | ✓ |

The "formally deferred" option is genuine: if the team correctly
diagnoses that pointing is insufficient and chooses to defer
imaging, they pass the criterion. If they image anyway and produce
garbage, they fail.

---

## 6. Coaching during the shift

[Claude Code: copy §6 of `sim_leop_instructor.md` and adapt for
commissioning specifics. Add: watch the team's *handover quality*
between passes, since pass-to-pass continuity is harder than within
a single pass.]

---

## 7. Debrief

[Claude Code: same structure as `sim_leop_instructor.md` §7, with
the difference that observer worksheets used today are *Team*
and *Space usage* (the other two were used Wednesday).]

---

## 8. Safety, red lines, references

[Claude Code: copy from `sim_leop_instructor.md` §§8 – 9 and add the
Commissioning-day-specific files:

- `scenarios/commissioning_day_start.yaml` (NEW)
- `procedures/commissioning/*.md`
- The `mcs/role_analysis/payload_ops_role.md` (today is heavy on
  payload ops).]
