---
title: "Week 3 Simulator Breakpoint Specification"
subtitle: "ORBIT NORTH · Week 3 · simulator scenario states"
course-codes: "GNG 3100 · SYS 5186"
term: "Summer 2026"
version: "v1 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
audience: "instructor + simulator operator"
---

# Week 3 — Simulator Breakpoint Specification

This document specifies the four simulator states that ORBIT NORTH
Week 3 needs. Three of them already exist as scenario YAML files in
`~/SpaceMissionSimulation/configs/eosat1/scenarios/`. One needs to be
created.

For each breakpoint we list:
- **Purpose** — which Week 3 session it serves
- **Mission phase** — EOSAT-1 phase number (0=PRE_SEPARATION,
  3=BOOTLOADER_OPS, 4=LEOP, 5+=COMMISSIONING/NOMINAL)
- **Spacecraft state** — power lines, AOCS mode, antennas, payload, battery
- **Pass geometry** — which ground station, AOS minus how many minutes
- **Existing scenario** — YAML file path to use, or **NEW**

---

## BP-1 — Nominal Post-Commissioning *(existing)*

**Purpose.** Training Day 1 round-robin, Training Day 2 dry-runs, and
the *nominal-shift* example used for procedure familiarisation.

**Mission phase.** 5 (NOMINAL).

**Spacecraft state.**

- All antennas deployed; TT&C TX in low-rate beacon between passes,
  high-rate during a contact.
- AOCS mode: NADIR pointing, body rates < 0.01 °/s, reaction wheels
  spun up.
- EPS: battery 90% SoC, solar arrays nominal, all main power lines ON.
- TCS: heaters cycling on thermostat, all zones in green band.
- Payload: imager in STANDBY, FPA cooler at temperature.
- OBDH: bootloader phase 5, app SW running, FDIR enabled.

**Pass geometry.** The default in `nominal_ops.yaml` lets the orbit
propagator generate natural passes. For Training Day 1 the
instructor selects a starting epoch ~10 min before the next Iqaluit
AOS so students see a full pass start to LOS.

**Existing scenario.** `scenarios/nominal_ops.yaml`. No change required.

---

## BP-2 — LEOP Day Start *(existing)*

**Purpose.** Wednesday 19 August simulation day.

**Mission phase.** 3 (BOOTLOADER_OPS).

**Spacecraft state.**

- OBC running bootloader firmware, transmitting beacon TM (SID 11
  only) on the bootloader APID.
- All other power lines OFF: ttc_tx is in beacon-only mode,
  aocs_wheels OFF, payload OFF, fpa_cooler OFF, htr_bat OFF, htr_obc OFF.
- Antennas NOT yet deployed — only the patch antenna for beacon is
  available.
- AOCS in OFF mode with residual tumble rates ~1–2 °/s from the
  separation impulse (already partially decayed).
- EPS battery at ~85% SoC, solar arrays nominal but uncontrolled
  Sun-pointing.
- TCS: passive only, all zones at ~ambient.

**Pass geometry.** Iqaluit pass beginning at scenario time T+0; the
instructor sets the simulator clock such that AOS occurs at scenario
start.

**Existing scenario.** `scenarios/first_contact.yaml`. The
`override_passes: true` flag in that file ensures continuous
visibility for the duration the team needs.

**Operator pass criteria for the day.** By end of the second pass
(team swap), the spacecraft must be in phase 4 (LEOP), antennas
deployed, app SW booted, time set, and all power lines required for
detumble (htr_bat, aocs_wheels) ON.

---

## BP-3 — Commissioning Day Start *(NEW — must be created)*

**Purpose.** Thursday 20 August simulation day. The mission has just
exited LEOP — antennas are deployed, app SW is running, detumble has
completed, time is set, but no commissioning has begun.

**Mission phase.** 4 (LEOP-complete) → transitions to 5
(COMMISSIONING) once team commands the phase change.

**Spacecraft state required at scenario start.**

- All antennas DEPLOYED.
- App SW RUNNING, full HK active (all SIDs 1–N reporting at 4 s rate).
- AOCS mode: DETUMBLE-completed, body rates < 0.05 °/s, reaction
  wheels POWERED but at 0 RPM.
- EPS battery 90% SoC; main bus nominal; payload OFF; fpa_cooler OFF;
  htr_bat ON; htr_obc ON; htr_payload OFF.
- TCS: payload zone at ~+5 °C (no active control yet); FPA at ambient.
- OBDH: phase 4, FDIR partially configured (LEOP-only set), nominal
  FDIR not yet enabled.
- Time: onboard clock synced.

**Pass geometry.** First Iqaluit pass beginning at scenario T+0.

**Suggested YAML to add to the simulator** —
`configs/eosat1/scenarios/commissioning_day_start.yaml`:

```yaml
name: "Commissioning Day Start"
difficulty: INTERMEDIATE
duration_s: 14400          # 4 hours of compressed time across multiple passes
briefing: |
  EOSAT-1 has just exited LEOP. Antennas are deployed, app SW is
  running, detumble has completed, time is set, and the spacecraft
  is in phase 4 with FDIR configured for the LEOP-only fault set.
  Your shift covers the first 4 hours of commissioning across
  ~4 ground passes (compressed).
  Goals for the shift:
    1. Transition the spacecraft to phase 5 (COMMISSIONING).
    2. Run COM-001 through COM-008 in order.
    3. Power on the payload, cool the FPA, and complete COM-012
       (First Light) before LOS at end of pass 4.

initial_conditions:
  spacecraft_phase: 4
  override_passes: true
  override_state:
    aocs.mode: NADIR_PREP
    aocs.body_rates_deg_s: 0.04
    eps.battery_soc_pct: 90
    eps.power_lines:
      htr_bat: ON
      htr_obc: ON
      aocs_wheels: ON
      ttc_tx: ON
      payload: OFF
      fpa_cooler: OFF
      htr_payload: OFF
    payload.mode: OFF
    obdh.fdir_table: leop_only
    tcs.payload_zone_c: 5.0

events:
  - time_s: 600
    type: instructor
    action: trigger_optional
    value: eps_overcurrent_payload
    description: "Optional: easy anomaly during COM-009 payload power-on"

  - time_s: 5400
    type: instructor
    action: trigger_optional
    value: fpa_overtemp
    description: "Optional: medium anomaly during FPA cool-down"

expected_responses:
  - { category: command, description: "Transition to COMMISSIONING phase (S8 func_id 80)" }
  - { category: command, description: "Run COM-001 EPS Checkout" }
  - { category: command, description: "Run COM-005 AOCS Mode Transitions" }
  - { category: command, description: "Run COM-006 TTC Link Verification" }
  - { category: command, description: "Run COM-008 FDIR Configuration (nominal table)" }
  - { category: command, description: "Run COM-009 Payload Power On" }
  - { category: command, description: "Run COM-010 FPA Cooler Activation" }
  - { category: command, description: "Run COM-012 First Light — capture and assess one image" }
```

**Operator pass criteria for the day.** Two of the four passes must
include FPA cooler ON; First Light must be acquired or formally
deferred-with-justification by end of pass 4.

---

## BP-4 — End-of-Sim "What If" Branch *(optional)*

**Purpose.** Friday wrap. Lets the instructor replay a Wednesday or
Thursday decision-point with a different team choice, to make the
debrief concrete.

**Implementation.** The simulator already supports state snapshots.
Instructor takes a snapshot at the moment of the decision (e.g. just
before the team commits to safe-mode entry); during Friday wrap, the
sim is restored from that snapshot and a different team commands
the alternative branch. No new scenario file required.

**Procedure.** Instructor uses the sim CLI:

```
sim snapshot save snap_<scenario>_<event>
sim snapshot restore snap_<scenario>_<event>
```

[Claude Code: confirm exact CLI when expanding this section.]

---

## Appendix — Scenario file conventions

EOSAT-1 scenario YAML structure (consistent across all files in
`scenarios/`):

| Key | Meaning |
|-----|---------|
| `name` | Display name |
| `difficulty` | BASIC / INTERMEDIATE / ADVANCED |
| `duration_s` | Sim seconds (compressed time multiplier defined separately) |
| `briefing` | Multiline operator briefing text |
| `initial_conditions` | Spacecraft phase, optional state overrides, optional speed multiplier |
| `events` | List of timed instructor or auto events |
| `expected_responses` | Operator action checklist used by the assessor |

The new `commissioning_day_start.yaml` follows this convention.
