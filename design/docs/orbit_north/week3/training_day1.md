---
title: "Week 3 — Training Day 1: Operations Concept Development"
subtitle: "ORBIT NORTH · Mon 17 August 2026 · uOttawa Cyberrange"
course-codes: "GNG 3100 · SYS 5186"
term: "Summer 2026"
version: "v1 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
audience: "students + instructor"
expected-reading: "EOSAT-1 mission summary (Section 2 of this document) before Day 1; the Student MCS & MPS Reference (separate doc) before Day 2"
---

# Training Day 1 — Operations Concept Development

**Day at a glance**

| When | What | Output |
|------|------|--------|
| 09:00 – 10:30 | Brief: ground-segment elements; ConOps recap; tools intro | Q&A captured |
| 10:30 – 12:00 | Mission Planning System (MPS) hands-on | First plan exported |
| 13:00 – 15:00 | MCS round-robin: each student rotates through six positions | Position tour completed |
| 15:00 – 16:30 | Pass-plan team exercise on the MPS | Team-written pass plan |
| 16:30 – 17:00 | Debrief & Day 2 brief; **expected reading flag** | Set up for Day 2 |

**Setting:** uOttawa Cyberrange, console room. Simulator runs the
**Nominal Post-Commissioning** breakpoint (BP-1 in the breakpoint
spec) — the spacecraft is healthy and doing routine ops, so the team
can focus on tools rather than recovery.

---

## 1. Brief — what we're flying

[Claude Code: expand to ~400 words. Cover EOSAT-1 mission: 6U
CubeSat, ocean-current monitoring with multispectral imager (443,
560, 665, 865 nm), 450 km Sun-synchronous orbit at 98° inclination.
Ground stations Iqaluit and Troll, both polar S-band. Reference
`~/SpaceMissionSimulation/configs/eosat1/mission.yaml` and
`orbit.yaml` for canonical values.]

### 1.1 The four ground-segment elements

[Claude Code: 200 words. Reference NASA Mission Operations
Handbook structure: ground stations · baseband · MCS · flight
dynamics. EOSAT-1 specifics: Iqaluit (63.7° N), Troll (-72° S),
S-band, 5° minimum elevation.]

### 1.2 Pass geometry — the polar S-band picture

[Claude Code: 200 words and a diagram. Show why polar SSO with
polar ground stations gives many short passes per day. Include a
Python-generated diagram (use `outputs/sample_figures/uottawa_brand.py`
style) showing one orbit with ground tracks, Iqaluit + Troll
visibility cones, and AOS/TCA/LOS markers.]

### 1.3 Procedure structure

[Claude Code: 150 words. Walk through one procedure from the
simulator (recommend `procedures/leop/first_acquisition.md` since
it's the simplest LEOP one). Highlight: preconditions block,
ownership column, verification, exit criteria. Tell students they
will read procedures, not write them.]

### 1.4 PUS service primer (light)

[Claude Code: 150 words. Introduce only services 1, 3, 5, 8, 9, 11,
17 by name and one-line meaning. Source: `mcs/pus_services.yaml`.
Emphasise that students use the MCS UI; PUS knowledge is for
context only.]

---

## 2. EOSAT-1 mission summary (expected reading before Day 1)

> **Read before Day 1.** Approximate reading time 25 minutes.

[Claude Code: produce a 600 – 900 word readable summary covering:
spacecraft platform (6U bus, multispectral imager, S-band), orbit
choice rationale (Sun-sync 450 km, why), payload science driver
(ocean-current monitoring, why those 4 bands), ground segment, ops
concept summary. Include diagrams: orbit + ground tracks + ground
station visibility (Python figure); spacecraft block diagram with
six MCS-position colour-coding; pass-cadence chart.]

### Key references

- EOSAT-1 mission config: `configs/eosat1/mission.yaml`
- ECSS-E-ST-70-11C — Space segment operability —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- NASA *Mission Operations Handbook* (NPR 7120.5F) —
  https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_
- CCSDS Mission Operations Reference Architecture (MOSE-IDP) —
  https://public.ccsds.org/Pubs/520x0g4.pdf

---

## 3. Mission Planning System hands-on

**Tool:** the MPS web UI (port 8080 by default — see
`configs/eosat1/mission.yaml`).

[Claude Code: produce a 1.5-page exercise. Use planning configs
(`planning/activity_types.yaml`, `planning/imaging_targets.yaml`,
`planning/ground_stations.yaml`) as reference. Steps:
  1. Open MPS, view ground-station schedule for next 24 h
  2. Pick three ocean-current imaging targets from the config
  3. Drop one imaging activity per target into the next available
     viable window
  4. Run conflict check (pointing slew time, power, thermal)
  5. Resolve conflicts, export plan
  6. Open the resulting plan in the MCS procedure panel.]

---

## 4. MCS round-robin

Six MCS positions, six 15-minute stations. Every student visits all
six during the afternoon. At each station, the seat-holder reads the
position's role analysis card aloud, then completes one position-
specific task while watching live telemetry.

| Position | Role analysis source | 15-min task |
|----------|---------------------|-------------|
| Flight Director | `mcs/role_analysis/flight_director_role.md` | Run a GO/NO-GO round on the live dashboard |
| Power & Thermal | `mcs/role_analysis/eps_tcs_role.md` | Identify the next eclipse and predict battery SoC at exit |
| Flight Dynamics (AOCS) | `mcs/role_analysis/aocs_role.md` | Compute AOS, TCA, LOS for the next Iqaluit pass |
| TT&C | `mcs/role_analysis/ttc_role.md` | Configure low-rate beacon → high-rate downlink at AOS |
| Payload Operations | `mcs/role_analysis/payload_ops_role.md` | Schedule a single imaging session via MPS |
| FDIR / Systems | `mcs/role_analysis/fdir_systems_role.md` | Walk through the FDIR panel and explain one rule |

[Claude Code: convert each row into a one-page station card and
include in the student bundle.]

---

## 5. Pass-plan team exercise

Team produces a written 60–90-min pass plan for an upcoming
Iqaluit pass. Plan must include:

- Pass timing (AOS – TCA – LOS, with margins)
- Procedures to run (using the curated procedure quick-reference)
- Imaging window, target ID, predicted ground swath
- Downlink config (data rate, encoding)
- Anomaly contingency: name **two** plausible failures and the
  procedure ID to run for each

Plans are read aloud at 16:30 and critiqued by another team using
the team-axis peer-review worksheet.

---

## 6. Debrief & expected reading for Day 2

> **Expected reading before Day 2.** Read the *Student MCS & MPS
> Reference* (`student_tool_reference.md`) — sections 1 to 4.
> Approximate reading time 45 minutes. Bring questions for Day 2 09:00.

Debrief questions:

1. Which MCS position felt most natural to you? Why?
2. What surprised you about a ground-station pass timing-wise?
3. What's one thing you'd want documented better before Day 2?

---

## 7. Tools, files & references

### Tools used

- Mission Control System (MCS) — webapp, port 8080
- Mission Planning System (MPS) — webapp, port 8080 (planning tab)
- Voice loop — Cyberrange softphone

### Simulator files referenced

- `configs/eosat1/mission.yaml`
- `configs/eosat1/orbit.yaml`
- `configs/eosat1/mcs/positions.yaml`
- `configs/eosat1/mcs/role_analysis/*.md`
- `configs/eosat1/planning/*.yaml`
- `configs/eosat1/procedures/procedure_index.yaml`

### Open references

- ECSS-E-ST-70C — Ground systems and operations —
  https://ecss.nl/standards/active-standards/ecss-e-st-70c-ground-systems-and-operations/
- ECSS-E-ST-70-11C — Space segment operability —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- CCSDS standards — https://public.ccsds.org/Publications/default.aspx
- NASA Mission Operations Handbook (NPR 7120.5F) —
  https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_
