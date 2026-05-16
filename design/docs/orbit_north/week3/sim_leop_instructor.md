---
title: "Wednesday LEOP Simulation — Instructor Pack"
subtitle: "ORBIT NORTH · Wed 19 August 2026 · uOttawa Cyberrange"
course-codes: "GNG 3100 · SYS 5186"
term: "Summer 2026"
version: "v1 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
audience: "instructor + simulator operator"
---

# Wednesday LEOP Simulation — Instructor Pack

**Confidential — instructor and simulator operator only.**

This pack covers the Wednesday simulation day. Two student teams
swap operator/observer roles between two passes. Anomaly injection
choices are listed; the instructor picks per team strength after
Tuesday's training quiz.

---

## 1. Day at a glance

| When | What | Mode |
|------|------|------|
| 09:00 – 09:30 | Standup, scenario brief to both teams | Instructor-led |
| 09:30 – 11:30 | **Pass 1** — Team A operates; Team B observes | LEOP sim |
| 11:30 – 12:30 | Lunch + observer prep | — |
| 12:30 – 12:45 | Reset + brief for Pass 2 | Instructor-led |
| 12:45 – 14:45 | **Pass 2** — Team B operates; Team A observes | LEOP sim |
| 14:45 – 16:00 | Joint debrief, observer presentations | Plenary |
| 16:00 – 17:00 | Anomaly-ticket completion + shift logs | Individual |

Each pass is 90 min real time / 90 min sim time (1× speed).

---

## 2. Scenario configuration

- **Breakpoint:** BP-2 — LEOP Day Start (existing scenario
  `scenarios/first_contact.yaml`).
- **Phase at start:** 3 (BOOTLOADER_OPS).
- **Initial visibility:** Iqaluit, AOS at scenario T+0.
- **`override_passes`** flag set so contact remains for the
  pass duration.
- **Speed multiplier:** 1× (real time).

[Claude Code: confirm the scenario CLI invocation. Expected form:
`sim run scenarios/first_contact.yaml --duration 5400 --inject <anomaly_yaml>`]

---

## 3. Procedure expectations

Operator team is expected to drive the spacecraft from phase 3
(bootloader, no antennas) to phase 4 (LEOP, full HK, detumble
complete) in roughly that order:

1. **LEOP-001** First Acquisition of Signal & OBC Boot
2. **LEOP-006** Time Synchronisation
3. **(LEOP-002)** Initial Health Check
4. **LEOP-007** Sequential Power-On (this is the long one — battery
   heater, reaction wheels, AOCS detumble; see procedure for full
   ordering note)
5. (Optional, if time permits) **LEOP-005** Sun Acquisition

Pass 1 typical end-state: phase 4, antennas deployed, app SW running,
htr_bat ON, aocs_wheels ON, body rates < 0.05 °/s.

Pass 2 typical end-state: same, plus payload-bus on standby, FDIR
nominal table loaded, ready for commissioning Thursday.

---

## 4. Anomaly injection menu

Pick **one** primary injection per team and one optional secondary
("rolling injection") if the primary is resolved cleanly. Files
named are scenario YAML files in
`~/SpaceMissionSimulation/configs/eosat1/scenarios/`; trigger them
through the scenario operator UI mid-run.

| Severity | Scenario file | What students see | Recovery procedure |
|----------|--------------|-------------------|--------------------|
| Easy | `ttc_no_tm_at_aos.yaml` | Beacon present, full HK never reports despite OBC_BOOT_APP | CTG-019 No TM at Pass Start |
| Easy | `eps_overcurrent.yaml` | Sudden overcurrent on a power line during sequential power-on | CTG-012 Overcurrent Response |
| Medium | `aocs_actuator_stuck.yaml` | One reaction wheel locked at 0 RPM during detumble | CTG-007 Reaction Wheel Anomaly |
| Medium | `aocs_star_tracker_failure.yaml` | Primary star tracker degrades at end of detumble | CTG-008 Star Tracker Failure |
| Hard | `obc_watchdog.yaml` | OBC watchdog reset mid-deploy | CTG-010 OBDH Watchdog Recovery |
| Hard | `obc_bus_failure.yaml` | CAN bus A drops mid-sequential-power-on | CTG-017 Bus Failure Switchover |
| Very hard | `gs_antenna_failure.yaml` | Iqaluit antenna degraded mid-pass; team must defer rest of pass to Troll | CTG-020 Ground Station Antenna Failure |

[Claude Code: cross-check filenames against simulator. The five
*medium* and *hard* scenarios are listed in
`scenarios/aocs_*.yaml`, `obc_*.yaml`, etc.]

### Injection cue card

For each injection, the instructor needs to know:

1. **Cue moment** — at what point in the LEOP procedure to inject.
2. **First indicator** — what the operators will see first
   (telemetry parameter, FDIR alarm, voice cue).
3. **Pass criterion** — what "successful recovery" looks like for
   the pass.
4. **Five debrief questions** to use after the pass.

[Claude Code: produce a one-page cue card per scenario.]

---

## 5. Pass operator-side criteria

End-of-pass GO/NO-GO criteria (instructor uses for assessment):

| Criterion | Pass 1 (Team A) | Pass 2 (Team B) |
|-----------|-----------------|-----------------|
| OBC application SW running | ✓ | ✓ |
| Onboard time set, drift < 0.5 s | ✓ | ✓ |
| Antennas deployed, high-rate link | ✓ | ✓ |
| Battery heater ON | ✓ | ✓ |
| Reaction wheels ON, AOCS in DETUMBLE | ✓ | ✓ |
| Body rates < 0.05 °/s | optional | ✓ |
| Anomaly ticket filed for any injection | ✓ | ✓ |
| FDIR nominal table loaded | — | ✓ |

Each criterion contributes to the team's **simulation performance**
mark (Week 3 assessment row).

---

## 6. Coaching during the shift

The instructor (acting as Mission Director) sits behind the FD seat
and coaches by exception only:

- **Voice-loop discipline.** If the team starts cross-talking,
  stop, name the rule, restart.
- **Procedure compliance.** If a position commands without FD
  GO, stop, log it, treat as a safety violation.
- **Anomaly response.** If the team is stuck > 5 minutes, drop a
  hint at the FDIR-panel level (don't name the procedure).
- **Time pressure.** Maintain the real-time clock — no pausing the
  sim for discussion. Pass closes when the orbit closes.

---

## 7. Debrief (joint)

Structure of the 75-minute debrief at end of day:

1. **Hot-wash (15 min).** Each team's FD reads their shift log
   highlights. No critique yet.
2. **Anomaly walk-through (20 min).** Operator team walks through
   the anomaly response; observer team challenges.
3. **Peer-review worksheet readout (20 min).** Each observer team
   reads its four-axis worksheet aloud (team / comms / space /
   technical). Operator team responds with one accept and one
   defend per axis.
4. **Lessons-learned synthesis (15 min).** Instructor consolidates
   into a single list. Logged in the cohort lessons-learned register.
5. **Brief Thursday (5 min).** Reading task: at minimum the COM-001
   through COM-008 procedure cards before tomorrow.

---

## 8. Safety and red lines

- **No commanding without FD authorisation.** Violation → instructor
  calls the shift, team logs the violation, no penalty if learnt-from.
- **No simulator-pause to win an exercise.** The clock runs.
- **No silent FD.** The Flight Director must be on the loop. If the
  FD is over-driven, the instructor calls a 30-second hold and
  resets the position.

---

## 9. References & files

- Simulator scenario: `configs/eosat1/scenarios/first_contact.yaml`
- Anomaly scenarios: see §4 table
- Procedure files: `configs/eosat1/procedures/leop/*.md`
- MCS positions: `configs/eosat1/mcs/positions.yaml`
- Telemetry limits: `configs/eosat1/mcs/limits.yaml`
- ECSS-E-ST-70-11C — Space segment operability
- NASA *Mission Operations Handbook* — https://nodis3.gsfc.nasa.gov/
- ESA *Mission Operations Concept* —
  https://www.esa.int/Enabling_Support/Operations
