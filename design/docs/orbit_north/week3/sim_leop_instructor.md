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

There is no `sim run` command. Start the simulator once
(`smo-simulator --config configs/eosat1/ --speed 1`, or `./start.sh`
for the whole suite), then start the scenario by the `name:` in its
YAML — **First Contact** — from the instructor console's Scenarios
panel, or over the instructor API on the simulator port:

```
curl -X POST http://localhost:8080/api/command \
     -H 'Content-Type: application/json' \
     -d '{"type": "start_scenario", "scenario": "First Contact"}'
```

Start an anomaly from §4 the same way, by its name, at its cue
moment. Only one scenario is active at a time: starting the anomaly
replaces *First Contact* as the active scenario but keeps the
spacecraft state, and the anomaly's events run from that moment.
`first_contact.yaml` declares `duration_s: 1800`; the pass runs for
as long as the instructor keeps the clock going.

---

## 3. Procedure expectations

Operator team is expected to drive the spacecraft from phase 3
(bootloader, no antennas) to phase 4 (LEOP, full HK, detumble
complete) in roughly that order:

1. **LEOP-001** First Acquisition of Signal & OBC Boot
2. **LEOP-002** Initial Health Check
3. **LEOP-004** Solar Array Verification (wing deployment)
4. **LEOP-007** Sequential Power-On (heaters if needed, the AOCS
   suite line, magnetometer, magnetorquers and GPS, then DETUMBLE;
   the wheels stay disabled until COM-004)
5. **LEOP-005** Sun Acquisition (observes the automatic handover to
   COARSE_SUN)
6. **LEOP-006** Time Synchronisation
7. (If time permits) **LEOP-003** Initial Orbit Determination, which
   ends LEOP by declaring phase 5

Pass 1 typical end-state: phase 4, antennas deployed, app SW running,
htr_bat ON, aocs_wheels ON, body rates < 0.05 °/s.

Pass 2 typical end-state: same, in the COARSE_SUN sun hold, clock
set; the payload stays off until COM-009; ready for commissioning
Thursday.

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

All seven files exist in `configs/eosat1/scenarios/` (checked against
the simulator tree on 2026-10-30). The console lists them by their
`name:` field: *No Telemetry at AOS*, *LCL Overcurrent Trip*,
*Reaction Wheel Stuck at Speed*, *Star Tracker Failure*, *OBC
Watchdog Reset*, *CAN Bus A Failure* and *Ground Station Antenna
Failure*. The instructor book's catalogue (§5.10.2) gives CTG-026
alongside CTG-007 for `aocs_actuator_stuck.yaml`.

### Injection cue card

For each injection, the instructor needs to know:

1. **Cue moment** — at what point in the LEOP procedure to inject.
2. **First indicator** — what the operators will see first
   (telemetry parameter, FDIR alarm, voice cue).
3. **Pass criterion** — what "successful recovery" looks like for
   the pass.
4. **Five debrief questions** to use after the pass.

The cue cards for all seven are in the instructor book, chapter 18:
§18.1 No TM at Pass Start, §18.2 Power-Line Overcurrent, §18.3
Reaction Wheel Stuck, §18.4 Star Tracker Failure, §18.5 OBC
Watchdog Reset, §18.6 OBC Bus Failure and §18.7 Ground Station
Antenna Failure. Each card gives the cue moment, first indicator,
recovery procedure, pass criterion and five debrief questions.
Print the cards you will use before the shift.

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
| FDIR rule sets enabled and verified | — | ✓ |

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
