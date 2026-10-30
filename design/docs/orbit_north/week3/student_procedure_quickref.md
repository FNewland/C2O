---
title: "Procedure Quick-Reference"
subtitle: "ORBIT NORTH · Week 3 operator pocket guide"
course-codes: "GNG 3100 · SYS 5186"
term: "Summer 2026"
version: "v1 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
audience: "students at console"
expected-reading: "Skim before each simulation day. Read in full any procedure your team is most likely to execute."
---

# Procedure Quick-Reference

Twenty-seven procedures students will most likely use during Week 3, in
one-card format. The full procedure files are the authoritative
source — these cards are pointers, not substitutes.

Card format: **ID · Title · Owner positions · Trigger · Top 3 steps ·
Exit criterion · File**.

Source of truth for procedures:
`~/SpaceMissionSimulation/configs/eosat1/procedures/procedure_index.yaml`
plus the per-procedure files in subfolders.

---

## LEOP procedures

Each card follows this template; LEOP-001 is shown in full.

> **LEOP-001 · First Acquisition of Signal & OBC Boot**
> *Owner positions:* Flight Director · TT&C · FDIR/Systems
> *Trigger:* First pass over Iqaluit after separation timer expiry.
> *Top 3 steps:* (1) configure ground station, monitor RF acquisition;
> (2) verify bootloader beacon (SID 11); (3) issue OBC_BOOT_APP
> command (S8 func_id 55).
> *Exit:* App SW running, full HK reporting.
> *File:* `procedures/leop/first_acquisition.md`

The other LEOP cards, one row each. The trigger is the card's entry condition. Top steps and the exit criterion are on the full card in textbook Part 2, §14.1;
the file is the authority. LEOP-003 and LEOP-005 are for advanced
students who reach them in the simulation.

| ID · Title | Owner positions | Trigger | File |
|---|---|---|---|
| LEOP-002 · Initial Health Check | Flight Director · Power & Thermal · FDIR / Systems | Immediately after LEOP-001; SIDs 1, 3, 4, 6 and 11 streaming | `procedures/leop/initial_health_check.md` |
| LEOP-007 · Sequential Power-On | Flight Director · Power & Thermal · Flight Dynamics · TT&C · FDIR / Systems | LEOP-004 done (wings deployed); `obdh.sw_image` = 1; SoC > 60 %. Powers only the AOCS suite and commands DETUMBLE | `procedures/leop/sequential_power_on.md` |
| LEOP-005 · Sun Acquisition | Flight Director · Flight Dynamics | After LEOP-007; AOCS in DETUMBLE (mode 2); SoC > 40 %. Observes the automatic handover to COARSE_SUN | `procedures/leop/sun_acquisition.md` |
| LEOP-006 · Time Synchronisation | Flight Director | After LEOP-005; application image running; `ttc.link_status` = 2 | `procedures/leop/time_sync.md` |
| LEOP-003 · Initial Orbit Determination | Flight Director · Flight Dynamics · TT&C | After LEOP-006; COARSE_SUN; GPS fix and SID 12. Last LEOP card: refined TLE to the ground tools, then declares phase 5 | `procedures/leop/initial_orbit_determination.md` |

Running order under the cold-boot initial state: LEOP-001 → LEOP-002 →
LEOP-004 → LEOP-007 → LEOP-005 → LEOP-006 → LEOP-003 (textbook Part 2,
§14.1).

---

## Commissioning procedures

The trigger is the card's entry condition. Top steps and the exit criterion are on the full card in textbook Part 2, §14.2. COM-003 (AOCS Sensor Calibration),
COM-004 (AOCS Actuator Checkout) and COM-013 are not on this list;
see §14.2.

| ID · Title | Owner positions | Trigger | File |
|---|---|---|---|
| COM-001 · EPS Checkout | Flight Director · Power & Thermal | Start of commissioning pass 1; COARSE_SUN; SoC > 70 % | `procedures/commissioning/eps_checkout.md` |
| COM-002 · TCS Verification | Flight Director · Power & Thermal | After COM-001 GO | `procedures/commissioning/tcs_verification.md` |
| COM-005 · AOCS Mode Transitions | Flight Director · Flight Dynamics | After COM-003 GO (wheels enabled in COM-004, gyros calibrated in COM-003) | `procedures/commissioning/aocs_mode_transitions.md` |
| COM-006 · TTC Link Verification | Flight Director · TT&C | After COM-005 GO | `procedures/commissioning/ttc_link_verification.md` |
| COM-007 · OBDH Checkout | Flight Director · FDIR / Systems | Commissioning pass 2, after the pass-startup health check | `procedures/commissioning/obdh_checkout.md` |
| COM-008 · FDIR Configuration & Protection Functions | Flight Director · FDIR / Systems | After COM-007 GO; FDIR moves from the LEOP set to the nominal set | `procedures/commissioning/fdir_configuration.md` |
| COM-009 · Payload Power On | Flight Director · Payload Operations · Power & Thermal | Nominal FDIR set armed; SoC > 75 %; generation > 40 W | `procedures/commissioning/payload_power_on.md` |
| COM-010 · FPA Cooler Activation | Flight Director · Payload Operations · Power & Thermal | Immediately after COM-009 GO; payload in STANDBY | `procedures/commissioning/fpa_cooler_activation.md` |
| COM-011 · Payload Calibration | Flight Director · Payload Operations | FPA in the −16.5…−14.5 °C band; `payload.fpa_ready` = 1 | `procedures/commissioning/payload_calibration.md` |
| COM-012 · First Light | Flight Director · Payload Operations · Flight Dynamics | After COM-011 GO | `procedures/commissioning/first_light.md` |

---

## Nominal procedures

The trigger is the card's entry condition. Top steps and the exit criterion are on the full card in textbook Part 2, §14.3.

| ID · Title | Owner positions | Trigger | File |
|---|---|---|---|
| NOM-001 · Pass Startup | Flight Director · TT&C | AOS at any of the five network stations | `procedures/nominal/startup.md` |
| NOM-002 · Imaging Session | Payload Operations · Flight Dynamics | Scheduled imaging window opens; AOCS in or entering FINE_POINT | `procedures/nominal/imaging_session.md` |
| NOM-003 · Data Downlink | TT&C · Payload Operations | AOS with products queued, usually right after NOM-001 | `procedures/nominal/data_downlink.md` |
| NOM-009 · Routine Health Check | Flight Director | Every pass startup, within NOM-001; or ad hoc by the FD | `procedures/nominal/routine_health_check.md` |
| NOM-012 · Shift Handover | Flight Director | End of shift | `procedures/nominal/shift_handover.md` |

---

## Contingency procedures (the most likely ones for Week 3)

The trigger is the card's entry condition. Top steps and the exit criterion are on the full card in textbook Part 2, §14.4.

| ID · Title | Owner positions | Trigger | File |
|---|---|---|---|
| CTG-001 · Under-Voltage Load Shed | Flight Director · Power & Thermal | `eps.uv_flag` (0x010E) = 1, rule ea 1001 fires, or bus below 27.0 V | `procedures/contingency/undervoltage_loadshed.md` |
| CTG-002 · AOCS Anomaly Recovery | Flight Director · Flight Dynamics | `aocs.att_error` (0x0217) > 5°, a wheel above 60 °C, or a star tracker BLIND | `procedures/contingency/aocs_anomaly.md` |
| CTG-003 · TTC Link Loss Recovery | Flight Director · TT&C | `ttc.link_status` (0x0501) = 0 for > 30 s after AOS, or the link lost mid-pass | `procedures/contingency/ttc_link_loss.md` |
| CTG-007 · Reaction Wheel Anomaly | Flight Director · Flight Dynamics | Speed jitter > ±500 rpm over 10 s, speed > 6500 rpm, or bearing above 60 °C | `procedures/contingency/reaction_wheel_anomaly.md` |
| CTG-012 · Overcurrent Response | Flight Director · Power & Thermal | A trip bit set in `eps.oc_trip_flags` (0x010D) | `procedures/contingency/overcurrent_response.md` |
| CTG-019 · No Telemetry at Pass Start | Flight Director · TT&C | No beacon and no HK at the expected AOS, or a beacon but no full HK after boot | `procedures/contingency/no_telemetry_at_pass.md` |

---

## Emergency procedures (read once, never expected to invoke)

Brief mention only — students should know these exist:

- EMG-001 Emergency Safe Mode (`procedures/emergency/emergency_safe_mode.md`)
- EMG-002 Total Power Failure (`total_power_failure.md`)
- EMG-003 OBC Reboot (`obc_reboot.md`)
- EMG-004 Loss of Communication (`loss_of_communication.md`)
- EMG-005 Loss of Attitude (`loss_of_attitude.md`)
- EMG-006 Thermal Runaway (`thermal_runaway.md`)

If you find yourself reaching for any of these, **call the FD
first**. These procedures have safe-mode entry as a step and you
do not invoke safe-mode without FD authorisation.

---

## How to read a procedure file

Every procedure file has the same shape; textbook Part 2, §7.4,
gives the template. Open `procedures/leop/first_acquisition.md`
alongside this:

1. **Header** — `# LEOP-001: First Acquisition of Signal & OBC Boot`,
   then **Subsystem**, **Phase**, **Revision** and **Approved**. LEOP
   cards also state an **Entry state** (here: cold boot, OBC in the
   bootloader).
2. **Purpose** — what the card achieves.
3. **Prerequisites** — a checklist (`- [ ]`) that must all be true
   before step 1.
4. **Procedure Steps** — `### Step N — name`, built from bold labels
   rather than a table: **TC** (the command with its arguments inside
   the backticks, service and subtype beside it), **Action**,
   **Verify** (mnemonic, hex id, threshold and timeout) and **Note**;
   some cards add **GO/NO-GO** or **BRANCH**.
5. **Off-Nominal Handling** — what to do when a verification fails,
   usually naming a CTG or EMG card by ID.
6. **Exit state** and **Post-Conditions** — the exit criterion.

Ownership is not in the file. The positions that run a card are its
`required_positions` in `procedure_index.yaml`, which the MCS
Procedures tab shows.

---

## How procedures map to MCS commands

Each procedure step that involves commanding lists the PUS service
to use (from `mcs/pus_services.yaml`):

| Service | Use |
|---------|-----|
| S1 | Telecommand verification (success / failure of last command) |
| S3 | Housekeeping configuration (which SIDs report when) |
| S5 | Event reports (anomaly events from the spacecraft) |
| S8 | Function management (calling spacecraft functions, e.g. OBC_BOOT_APP) |
| S9 | Time management (set time, time correlation) |
| S11 | Onboard schedule (time-tagged commands) |
| S15 | On-board storage and retrieval (downlink mass memory) |
| S17 | Connection test (uplink-downlink link check) |
| S19 | Event-action service (trigger an OBC action when an event fires) |
| S20 | Parameter management (read / write OBC parameters) |

You command via the MCS UI; you do not need to write PUS frames
yourself.

---

## When you are stuck

1. Pause. Use a callout: "[Position], standby."
2. Do not command. Re-read the procedure exit criterion.
3. Ask the FD for a 60-second hold.
4. If the FD agrees, log the hold and consult the manual section
   for the affected subsystem
   (`configs/eosat1/manual/0*.md`).
5. If you cannot resolve, the FD calls *no-go* and the team rolls
   back to the last verified state.

---

## References

- Simulator procedure index:
  `~/SpaceMissionSimulation/configs/eosat1/procedures/procedure_index.yaml`
- ECSS-E-ST-70-32C — Test and operations procedures
- CCSDS Mission Operations Services Concept (CCSDS 520.0-G) —
  https://public.ccsds.org/Pubs/520x0g4.pdf
- NASA *Space Flight Program and Project Management Requirements* (NPR 7120.5F)
