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

Twenty procedures students will most likely use during Week 3, in
one-card format. The full procedure files are the authoritative
source — these cards are pointers, not substitutes.

Card format: **ID · Title · Owner positions · Trigger · Top 3 steps ·
Exit criterion · File**.

Source of truth for procedures:
`~/SpaceMissionSimulation/configs/eosat1/procedures/procedure_index.yaml`
plus the per-procedure files in subfolders.

---

## LEOP procedures

[Claude Code: produce a one-page card per procedure. Use this template:]

> **LEOP-001 · First Acquisition of Signal & OBC Boot**
> *Owner positions:* Flight Director · TT&C · FDIR/Systems
> *Trigger:* First pass over Iqaluit after separation timer expiry.
> *Top 3 steps:* (1) configure ground station, monitor RF acquisition;
> (2) verify bootloader beacon (SID 11); (3) issue OBC_BOOT_APP
> command (S8 func_id 42).
> *Exit:* App SW running, full HK reporting.
> *File:* `procedures/leop/first_acquisition.md`

Cards required for this section:
- LEOP-001 First Acquisition of Signal & OBC Boot
- LEOP-002 Initial Health Check
- LEOP-006 Time Synchronisation
- LEOP-007 Sequential Power-On

[Claude Code: also include LEOP-003 (Initial Orbit Determination)
and LEOP-005 (Sun Acquisition) for advanced students who reach
them in the simulation.]

---

## Commissioning procedures

[Claude Code: one card per procedure listed below, same format as
LEOP cards.]

- COM-001 EPS Checkout
- COM-002 TCS Verification
- COM-005 AOCS Mode Transitions
- COM-006 TTC Link Verification
- COM-007 OBDH Checkout
- COM-008 FDIR Configuration
- COM-009 Payload Power On
- COM-010 FPA Cooler Activation
- COM-011 Payload Calibration
- COM-012 First Light

---

## Nominal procedures

[Claude Code: one card per procedure.]

- NOM-001 Pass Startup
- NOM-002 Imaging Session
- NOM-003 Data Downlink
- NOM-009 Routine Health Check
- NOM-012 Shift Handover

---

## Contingency procedures (the most likely ones for Week 3)

[Claude Code: one card per procedure.]

- CTG-001 Under-Voltage Load Shed
- CTG-002 AOCS Anomaly Recovery
- CTG-003 TTC Link Loss Recovery
- CTG-007 Reaction Wheel Anomaly
- CTG-012 Overcurrent Response
- CTG-019 No Telemetry at Pass Start

---

## Emergency procedures (read once, never expected to invoke)

Brief mention only — students should know these exist:

- EMG Emergency Safe Mode (`procedures/emergency/emergency_safe_mode.md`)
- EMG Loss of Attitude
- EMG Loss of Communication
- EMG OBC Reboot
- EMG Thermal Runaway

If you find yourself reaching for any of these, **call the FD
first**. These procedures have safe-mode entry as a step and you
do not invoke safe-mode without FD authorisation.

---

## How to read a procedure file

[Claude Code: 200 words. The procedure files in the simulator follow a
consistent structure. Walk through it using
`procedures/leop/first_acquisition.md` as the example: front-matter,
preconditions, steps with ownership column, verifications, exit
criteria, troubleshooting.]

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
- CCSDS Mission Operations Procedures —
  https://public.ccsds.org/Pubs/520x0g4.pdf
- NASA *Mission Operations Handbook* (NPR 7120.5F)
