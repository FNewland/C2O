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
| 13:00 – 15:00 | MCS round-robin: 15-min briefing, then each student rotates through the seven consoles (7 × 15 min) | Position tour completed |
| 15:00 – 16:30 | Pass-plan team exercise on the MPS | Team-written pass plan |
| 16:30 – 17:00 | Debrief & Day 2 brief; **expected reading flag** | Set up for Day 2 |

**Setting:** uOttawa Cyberrange, console room. Simulator runs the
**Nominal Post-Commissioning** breakpoint (BP-1 in the breakpoint
spec) — the spacecraft is healthy and doing routine ops, so the team
can focus on tools rather than recovery.

---

## 1. Brief — what we're flying

EOSAT-1 is a 6U CubeSat (12.0 kg dry, 12.40 kg wet) for
ocean-current monitoring along the Canadian coastlines. Its
four-band multispectral pushbroom imager (443, 560, 665 and 865 nm)
gives a 273 km swath at 33.4 m ground sample distance. It flies a
513 km sun-synchronous orbit at 97.39° inclination with the
ascending node at 10:00 local time, so each 94.5-minute orbit
includes about 34 minutes of eclipse. Power comes from body-mounted
cells and two deployable wings into a 100 Wh battery. Attitude is
controlled by four reaction wheels, with two star trackers, six
coarse sun sensors, one magnetometer and three gyros, and a 1U
green-monopropellant module (66.9 m/s) covers debris avoidance,
drag make-up and the end-of-life disposal burn.

The ground segment is five polar S-band stations — Iqaluit, Troll,
Svalbard, Inuvik and O'Higgins — on a 5° mask: about 51 passes a
day, 7.5 minutes long on average, with a median gap of 33 minutes.
Telemetry runs on a three-rung ladder: BEACON 1 kbps, LOW 16 kbps
for routine operations, HIGH 128 kbps for image dumps above 10°
elevation.

The full brief is textbook Part 2, §5.7. The canonical values are in
`configs/eosat1/mission.yaml` and `orbit.yaml`.

### 1.1 The four ground-segment elements

Textbook Part 2, §8.2, walks the four elements as they appear in the
room: **ground stations** (five polar S-band sites on a 5° mask —
Iqaluit 63.7° N, Inuvik 68.3° N, Svalbard 78.2° N, Troll 72.0° S and
O'Higgins 63.3° S; `ttc.active_gs`, 0x0523, names the live one),
**baseband** (the RF and baseband health feed: Eb/N0 and frame
sync), the **MCS** (port 9090) and **flight dynamics** (the
planner's contact schedule on port 9091 and
`tools/pass_gap_analysis.py`). The station list and coordinates are
in `orbit.yaml`.

### 1.2 Pass geometry — the polar S-band picture

Textbook Part 2, §8.2.1, with Figure 8.1 (one orbit with the five
stations' visibility cones, lit and eclipsed segments shaded), is
the session text. The point to land: the stations sit at high
latitude, where the ground tracks of a polar sun-synchronous orbit
converge, so most orbits bring the spacecraft over at least one of
them. Over 48 h that gives 103 passes, a median gap of 33 minutes
and a worst gap of 79 minutes. Passes last 3 to 9.4 minutes; the
overhead maximum with the 5° mask is 9.3 minutes at 513 km.

### 1.3 Procedure structure

Walk through `procedures/leop/first_acquisition.md` using the
*Procedure Quick-Reference*, "How to read a procedure file", and
textbook Part 2, §7.4. Highlight the header with its entry state,
the Prerequisites checklist, steps built from **TC**, **Action**,
**Verify** and **Note** labels, Off-Nominal Handling, and the Exit
state and Post-Conditions that form the exit criterion. Ownership
is not a column in the file: it is `required_positions` in
`procedure_index.yaml`. Students read procedures; they do not write
them.

### 1.4 PUS service primer (light)

Use the seven-service list in the *Student MCS & MPS Reference*, §3
(S1, S3, S5, S8, S9, S11 and S17, one line each). The full primer is
textbook Part 2, §7.6, and the source is `mcs/pus_services.yaml`.
Students command through the MCS; PUS knowledge is context only.

---

## 2. EOSAT-1 mission summary (expected reading before Day 1)

> **Read before Day 1.** Approximate reading time 25 minutes.

The expected reading is textbook Part 2, §5.7 (*What we are flying —
EOSAT-1 in 600 words*), with §§5.2–5.5 for the operations concept:
the arc of the mission, what an operator must be able to do, the
control-room positions, and how passes and shifts work. On the
orbit: a sun-synchronous orbit keeps the local solar time of each
pass the same, so images of a target are taken under comparable
light; EOSAT-1's is at 513 km with the ascending node at 10:00, so
it has an eclipse on every orbit. Natural decay from 513 km takes
5.0 years at mean solar activity and 14.2 years at solar minimum,
which fails the 5-year disposal rule, so the mission ends with a
34.3 m/s perigee-lowering burn to 390 km (NOM-014), after which
re-entry takes 1.5 years (4.2 at solar minimum). The band choice (443, 560, 665 and 865 nm, for
dissolved organic carbon and surface chlorophyll) is explained in
§5.7. Figures: Figure 8.1 for the orbit and station visibility, and
§5.6 for the control-room layout.

### Key references

- EOSAT-1 mission config: `configs/eosat1/mission.yaml`
- ECSS-E-ST-70-11C — Space segment operability —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- NASA *Space Flight Program and Project Management Requirements* (NPR 7120.5F) —
  https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_
- CCSDS Mission Operations Services Concept (CCSDS 520.0-G) —
  https://public.ccsds.org/Pubs/520x0g4.pdf

---

## 3. Mission Planning System hands-on

**Tool:** the MPS web UI (port 9091 by default — the planner's own
`--port`; the simulator uses 8080 and the MCS 9090).

> **TODO (author):** Write the MPS exercise for this session
> (about one and a half pages) from `planning/activity_types.yaml`,
> `planning/imaging_targets.yaml` and `planning/ground_stations.yaml`:
> open the 24 h station schedule, pick three ocean-current targets,
> drop one imaging activity per target into a viable window, run the
> conflict check (slew time, power, thermal), resolve and export the
> plan, then open it in the MCS Procedures page. Textbook Part 2,
> §8.5, has a ten-step version that can serve as the base.

---

## 4. MCS round-robin

A 15-minute briefing, then seven 15-minute stations, one per console
configured in `mcs/positions.yaml`: the 13:00–15:00 block exactly.
Every student visits all seven during the afternoon. At each
station, the seat-holder reads the position's role analysis card
aloud, then completes one position-specific task while watching live
telemetry and records it on the matching workbook card (WB-5.1).
Mission Manager and Ground Segment are room roles, not consoles; the
ground-segment check is part of the TT&C station.

| Position | Role analysis source | 15-min task |
|----------|---------------------|-------------|
| Flight Director | `mcs/role_analysis/flight_director_role.md` | Run a GO/NO-GO round on the live dashboard (*go for* `CONNECTION_TEST`) |
| Power & Thermal | `mcs/role_analysis/eps_tcs_role.md` | Predict battery SoC at exit of the next eclipse; name the heater at the highest duty cycle |
| Flight Dynamics | `mcs/role_analysis/aocs_role.md` | Check `aocs.att_error` against the NOMINAL budget; compute AOS, TCA and LOS for the next Iqaluit pass |
| TT&C | `mcs/role_analysis/ttc_role.md` | Walk the rate ladder from LOW to HIGH at AOS; confirm which station carries the pass |
| Payload Operations | `mcs/role_analysis/payload_ops_role.md` | Schedule a single imaging session via MPS; confirm `payload.fpa_ready` = 1 |
| FDIR / Systems | `mcs/role_analysis/fdir_systems_role.md` | Walk through the FDIR panel and explain one rule |
| Propulsion | `mcs/role_analysis/propulsion_role.md` | Read the arm interlock mask (`prop.arm_inhibit_mask`, 0x0B15) and name the gate blocking an arm, without commanding |

The station cards are workbook WB-5.1, one per console, each with
its task and the readings to record. The role analysis named in the
table is the brief each seat-holder reads aloud.

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

- Mission Control System (MCS) — webapp, port 9090
- Mission Planning System (MPS) — webapp, port 9091 (its own server)
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
- NASA Space Flight Program and Project Management Requirements (NPR 7120.5F) —
  https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_
