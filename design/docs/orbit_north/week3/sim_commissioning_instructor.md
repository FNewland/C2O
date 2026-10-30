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
passes). The simulator operator switches the speed by hand (§2).

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

The only start-up flag is `--speed` (default 1.0). During the
shift, change the speed from the instructor console's speed buttons
(0.5×, 1×, 2×, 5×, 10×) or over the instructor API, e.g.
`{"type": "set_speed", "value": 3}` posted to `/api/command` for a
3× setting the buttons do not offer. `simulation.yaml` clamps any
request to 1000×, and the simulator holds ≤ 10× while a burn is
firing. The simulator does **not** change speed on its own around
passes: the simulator operator does it by hand, using the contact
schedule.

---

## 3. Procedure expectations

The team is expected to drive commissioning in approximately this
order across the four passes:

**Pass 1.** COM-001 EPS Checkout · COM-002 TCS Verification ·
COM-004 AOCS Actuator Checkout (wheels enabled, NOMINAL commanded) ·
COM-003 AOCS Sensor Calibration (gyro calibration in that NOMINAL,
ruling Q16) · COM-005 AOCS Mode Transitions · COM-006 TTC Link
Verification.

**Pass 2.** COM-007 OBDH Checkout · COM-008 FDIR Configuration
(enable S12 monitoring, verify the S12/S19 rule sets).

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
| Medium | `fpa_overtemp.yaml` | FPA cooler can't hold its −15 °C setpoint | CTG-004 Thermal Exceedance + payload safe |
| Medium | `payload_corrupt_image.yaml` | First image returns corrupt | CTG-015 Corrupted Image Recovery |
| Hard | `aocs_sensor_cascade.yaml` | Star tracker degrades; pointing budget broken | CTG-008 Star Tracker Failure → CTG-002 + defer First Light |
| Hard | `eps_progressive_load_shed.yaml` | Battery degradation forces progressive load-shed during cooler activation | CTG-001 Under-Voltage Load Shed |
| Very hard | `aocs_wheel_failure.yaml` followed by `transponder_failure.yaml` | Wheel locks late in pass 3, then transponder fails next pass — multi-anomaly response | CTG-007 → CTG-003 |

Cue cards for six of the seven are in the instructor book,
chapter 18: `eps_overcurrent.yaml` §18.2 (inject on `payload`,
`line_index=3`, during COM-009), `fpa_overtemp.yaml` §18.8,
`payload_corrupt_image.yaml` §18.9, `aocs_sensor_cascade.yaml`
§18.10, `eps_progressive_load_shed.yaml` §18.11 and the
`aocs_wheel_failure.yaml` + `transponder_failure.yaml` pair §18.12.
The seventh is below, in the same format.

**`gs_rf_degradation.yaml` — Ground Station RF Chain Degradation (Easy)**

- **Cue moment.** Start it after COM-006 has baselined the link
  margin, so the team has a reference. Its events fire at T+60 s
  (`high_ber` on the spacecraft side, magnitude 0.3, ramped over
  120 s), T+180 s (ground LNA, +3 dB noise figure) and T+360 s
  (ground antenna mispoint, 3 dB). The file's briefing asks for the
  RF bridge in FRAME mode (`SMO_RF_MODE=FRAME ./start.sh`).
- **First indicator.** Eb/N0 (`ttc.eb_n0`, 0x0519) falls and BER
  (`ttc.ber`, 0x050C) rises on the TT&C display while the link
  margin (`ttc.link_margin`, 0x0503) erodes.
- **Recovery procedure.** CTG-014 BER Anomaly; CTG-003 if the link
  is lost.
- **Pass criterion.** The team compares RSSI (`ttc.rssi`, 0x0502)
  with Eb/N0 to separate the spacecraft-side degradation from the
  two ground-side ones before commanding anything on board, and
  files one ticket per cause.
- **Debrief Qs.**
  1. Which reading told you part of the loss was on the ground?
  2. Did anyone command the spacecraft to fix a ground fault?
  3. When did TT&C first call the trend on the loop?
  4. Was the HIGH-tier dump deferred or moved to another pass?
  5. What would you check first next time?

---

## 5. Pass operator-side criteria

| Criterion | Pass-set 1 (Team A) | Pass-set 2 (Team B) |
|-----------|---------------------|---------------------|
| Phase advanced to COMMISSIONING (5) | ✓ | ✓ |
| EPS checkout complete with no faults | ✓ | ✓ |
| AOCS NOMINAL mode (4) achieved, pointing < 0.5° | ✓ | ✓ |
| FDIR rule sets enabled and verified (COM-008) | ✓ | ✓ |
| Payload powered ON | ✓ | ✓ |
| FPA cooler at its setpoint (−15 °C) | ✓ | ✓ |
| First Light image acquired (or formally deferred) | ✓ | ✓ |
| Anomaly tickets filed for all injections | ✓ | ✓ |

The "formally deferred" option is genuine: if the team correctly
diagnoses that pointing is insufficient and chooses to defer
imaging, they pass the criterion. If they image anyway and produce
garbage, they fail.

---

## 6. Coaching during the shift

As the LEOP pack, §6: voice-loop discipline, procedure compliance,
an FDIR-panel-level hint after five minutes stuck, and no pausing
during a pass. Two commissioning additions:

- **Speed changes only between passes.** Compression is the
  simulator operator's call, never the team's, and the clock runs at
  1× from AOS to LOS.
- **Handover quality between passes.** At each pass boundary the FD
  restates the open items, the procedure in progress and the next
  pass's goal; note anything dropped. Pass-to-pass continuity is
  harder than continuity within one pass, and First Light depends
  on it.

---

## 7. Debrief

Same structure and timings as the LEOP pack, §7: hot-wash (15 min),
anomaly walk-through (20 min), peer-review worksheet readout
(20 min), lessons-learned synthesis (15 min) and the brief for
Friday (5 min). The observer worksheets used today are *Team* and
*Space usage*; Wednesday used *Communications* and *Technical*.
The debrief prompts for each procedure are in textbook Part 2,
§11.8.

---

## 8. Safety, red lines, references

Safety and red lines are those of the LEOP pack, §8: no commanding
without FD authorisation, no pausing the simulator to win an
exercise (between-pass compression is set by the simulator
operator, not the team), and no silent FD.

References are those of the LEOP pack, §9, plus:

- `configs/eosat1/scenarios/commissioning_day_start.yaml` (NEW,
  written by the instructor from the BP-3 spec; not in the shipped
  set)
- `configs/eosat1/procedures/commissioning/*.md`
- `configs/eosat1/mcs/role_analysis/payload_ops_role.md` (today is
  heavy on payload operations)
- Textbook Part 2, chapter 11 (commissioning operations), and the
  instructor book, chapter 18 (cue cards)
