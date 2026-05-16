---
title: "Student MCS & MPS Reference"
subtitle: "ORBIT NORTH · Week 3 operations tools quick reference"
course-codes: "GNG 3100 · SYS 5186"
term: "Summer 2026"
version: "v1 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
audience: "students"
expected-reading: "Sections 1 – 4 before Training Day 2; sections 5 – 7 before Wednesday LEOP day"
---

# Student MCS & MPS Reference

This document is the operator's reference for the two tools you will
use during Week 3 of ORBIT NORTH:

- **MCS** — the Mission Control System (telemetry, commanding,
  procedure panel, FDIR panel)
- **MPS** — the Mission Planning System (imaging targets, pass
  planning, conflict checking)

You do **not** need to know how the underlying simulator works.
You **do** need to be fluent in the MCS and MPS UIs.

---

## 1. The console at a glance

[Claude Code: include an annotated screenshot of the MCS — the
default Flight Director dashboard. Label: top header (callsign,
phase, time), left rail (subsystem tabs), centre (telemetry
mosaic), right rail (FDIR panel, voice loop, procedure panel).
~250 words walking through each region.]

### 1.1 Position-specific tabs

Each MCS position has a different visible-tab set defined in
`mcs/positions.yaml`. Quick reference:

| Position | Visible tabs |
|----------|-------------|
| Flight Director | system_dashboard, power_monitor, fdir_panel, contact_schedule, procedure_panel, overview, eps, aocs, tcs, obdh, ttc, payload, commanding, pus, procedures, manual |
| Power & Thermal | overview, eps, tcs, commanding, procedures, manual |
| Flight Dynamics (AOCS) | overview, aocs, commanding, procedures, manual |
| TT&C | overview, ttc, commanding, procedures, manual |
| Payload Operations | overview, payload, commanding, procedures, manual |
| FDIR / Systems | overview, obdh, commanding, pus, procedures, manual |

The overview tab is always present so every position has shared
situational awareness; the position-specific tabs are where you do
your work.

[Claude Code: convert the table above into a position-cheat-sheet
card.]

---

## 2. Reading telemetry

[Claude Code: 400 words. Cover:

- The HK structure (SIDs from `telemetry/hk_structures.yaml`,
  parameters from `telemetry/parameters.yaml`)
- Limit colouring: green / yellow / red bands defined in
  `mcs/limits.yaml`
- "Stale" telemetry indicator (no update for > 10 s)
- The "watch" widget — how to pin a parameter for the whole shift
- Reading a plot: trend line, limit lines, eclipse shading

Include an annotated screenshot of one telemetry mosaic.]

---

## 3. Sending a command

[Claude Code: 350 words. Cover:

- Command paths: procedure-driven (recommended) vs direct command
- The PUS service primer for the seven services students see most:
  S1 (verification), S3 (HK), S5 (events), S8 (function management),
  S9 (time), S11 (onboard scheduling), S17 (link test). Each in 30
  words. Source: `mcs/pus_services.yaml`.
- Dual-key authorisation: many destructive commands require the
  Flight Director to second-key
- Commanding from a procedure step — automatic field population
- Common errors: out-of-range parameter, wrong APID, no AOS

Include an annotated screenshot of the commanding panel.]

---

## 4. The procedure panel

[Claude Code: 300 words. Cover:

- How to load a procedure (procedure picker, search by ID)
- The step list: each step has owner / action / verification / pass
- "Skip" and "Hold" — when each is allowed
- Logging a procedure run: timestamp, executor, comments
- Where the run history goes (per-shift log)

Include an annotated screenshot of `procedures/nominal/startup.md`
loaded in the panel.]

---

## 5. The FDIR panel

[Claude Code: 350 words. Cover:

- Reading FDIR rules (loaded from `monitoring/s12_definitions.yaml`
  and `monitoring/s19_rules.yaml`)
- Active-anomaly list: severity colour coding, time of trigger,
  affected subsystem
- Acknowledging an anomaly vs clearing it
- The escalation ladder: level 0 (informational) → level 4 (safe-mode
  candidate)
- Manual override — when and why
- Anomaly-ticket creation: required fields, where the ticket lives

Include an annotated FDIR-panel screenshot.]

---

## 6. The Mission Planning System (MPS)

[Claude Code: 400 words. Cover:

- Imaging-target picker — geographic filter, science-band filter
  (configs in `planning/imaging_targets.yaml`)
- Activity types — `planning/activity_types.yaml` (slew, image,
  downlink, eclipse, momentum-management)
- Ground-station schedule: AOS, max elevation, duration, station
  (`planning/ground_stations.yaml`)
- Conflict checker — slew time, power budget, thermal envelope,
  pointing budget
- Plan export — produces the activity sequence loaded by the OBC
- Plan import to MCS procedure panel

Include screenshots of the MPS schedule view and the conflict
checker output.]

---

## 7. Voice loop & MCS chat

[Claude Code: 250 words. Cover:

- Voice loop: hardware (Cyberrange softphone), loop discipline (see
  Training Day 2 §1), addressing pattern, hot-mike rule
- Backup MCS chat: when to use it (low-priority comments), when
  not to (any commanding intention)
- Loop logging: every callout is recorded for the post-sim debrief]

---

## 8. Quick keyboard shortcuts

[Claude Code: produce a 12-row table of common MCS keyboard
shortcuts. Examples:

| Shortcut | Action |
|----------|--------|
| F2 | Focus telemetry mosaic |
| F3 | Focus commanding panel |
| F4 | Focus procedure panel |
| Ctrl-K | Quick command picker |
| Ctrl-, | Toggle overview |
| Esc | Cancel pending command |

Confirm exact shortcuts against the simulator UI.]

---

## 9. Where to read more

| Topic | Source file in simulator |
|-------|--------------------------|
| Subsystem manuals (background) | `configs/eosat1/manual/0*.md` |
| Position role analyses | `configs/eosat1/mcs/role_analysis/*.md` |
| Telemetry parameters | `configs/eosat1/telemetry/parameters.yaml` |
| Telemetry limits | `configs/eosat1/mcs/limits.yaml` |
| Procedure index | `configs/eosat1/procedures/procedure_index.yaml` |
| FDIR rules | `configs/eosat1/monitoring/s19_rules.yaml` |

External references:

- ECSS-E-ST-70-11C — Space segment operability —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- ECSS-E-ST-70-32C — Test and operations procedures —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-32c-test-and-operations-procedures/
- CCSDS Packet Utilization Standard (PUS) —
  https://public.ccsds.org/Pubs/660x0g3.pdf
- NASA *Mission Operations Handbook* — https://nodis3.gsfc.nasa.gov/
