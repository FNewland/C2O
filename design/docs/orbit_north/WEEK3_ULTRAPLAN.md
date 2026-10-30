# ORBIT NORTH — Week 3 Ultraplan
**Operations & Mission Simulation, 17 – 21 August 2026 · uOttawa Cyberrange**

**Owner:** Dr Franz Newland · uOttawa SEDTI
**Status:** v1 — planning & skeleton drafts
**Last updated:** 2026-05-05
**Reference spacecraft:** EOSAT-1 (6U CubeSat, 450 km SSO, ocean-current monitoring,
multispectral imager 443/560/665/865 nm, S-band downlink to Iqaluit and Troll
ground stations) — config in `~/SpaceMissionSimulation/configs/eosat1/`

This is the master plan for Week 3 of ORBIT NORTH. It maps the four
deliverable docs (training Day 1, training Day 2, two simulation days,
plus the peer-review and instructor packs), names the breakpoints
needed in the simulator, and lists the concrete writing tasks that
remain. Skeleton drafts of every Week 3 document are in
`week3/` next to this file.

---

## 1. Aims for Week 3

By the end of Week 3, every student must have:

1. Operated each of the six MCS positions for at least one full
   ground-station pass. Positions: **Flight Director · Power &
   Thermal · Flight Dynamics (AOCS) · TT&C · Payload Operations ·
   FDIR / Systems.**
2. Run a planning cycle: imaging-target selection → activity sequence
   → conflict check → uplink schedule → execution.
3. Executed at least one nominal procedure and one off-nominal
   (contingency or emergency) procedure as the lead operator.
4. Critiqued a peer team's shift using the four-axis worksheet
   (team · communications · space usage · technical).
5. Produced a written shift log and an anomaly ticket.

Week 3 reinforces ECSS-E-ST-70-11C (space segment operability) and
the *NASA Mission Operations Handbook* style of pass-by-pass running.

---

## 2. Cohort and team structure

EOSAT-1 has **six MCS positions**. With student teams of 4–6, each
team occupies all positions (some positions can be covered by one
person, e.g. a quiet shift's TT&C can dual with the Flight Director).
We expect the cohort to split into **two teams of 5–6**, plus
**1–2 instructor controllers** running the simulator and injecting
anomalies. The third team, if any, observes during a given shift
and uses the peer-review worksheet.

| Role count | Notes |
|------------|-------|
| 6 | MCS positions (1 student each — see `positions.yaml`) |
| 1 | Mission Director / instructor coach — coaches the team mid-shift |
| 1 | Simulator operator / scenario controller — drives the scenario file, injects events |

The instructor is a coach during the shift and an examiner during
the debrief.

---

## 3. The two training days (Mon 17 + Tue 18 Aug)

### Training Day 1 — Operations Concept Development

**Tools introduced:** SpaceCDF (re-used briefly for the imported
mission), the **Mission Control System (MCS)**, the **Mission Planning
System (MPS)**.

**Spacecraft state:** *nominal post-commissioning* — i.e. the
simulator starts in the `nominal_ops` scenario state. Antennas
deployed, AOCS in NADIR mode, FPA cooler at temperature, payload in
STANDBY. **Breakpoint required:** "Nominal Post-Commissioning"
(see §6).

Topics:

- The four ground-segment elements: ground stations, baseband, MCS,
  flight-dynamics. EOSAT-1's Iqaluit + Troll stations and the
  geometry of polar S-band passes.
- Pass planning: AOS, TCA, LOS; how the planning system computes
  contact windows; how imaging targets are scheduled inside windows.
- Procedure structure: what a procedure file looks like
  (preconditions, steps with ownership, verification, pass criteria).
- Telecommand basics: PUS service primer (focus on services 1, 3, 5,
  8, 9, 11, 17). What students need to know is the *MCS UI* — they do
  not need to memorise PUS.
- Telemetry structure: SIDs, parameter limits, FDIR alarms.
- Position-specific orientation. Each student rotates through all
  six positions in a 90-min round-robin.

Deliverable: short pass-plan written by each team for a real
upcoming Iqaluit pass in the simulator (60–90 min plan, including
imaging window and downlink configuration).

### Training Day 2 — Mission Operations Training

Topics:

- Voice-loop discipline: callouts, GO/NO-GO protocol, FD rounds.
  Standard phrasing students must use is documented in the student
  reference card.
- Shift handover: how to do it without losing situational awareness
  (procedure NOM-012 in the simulator).
- Anomaly response: detection → assessment → recovery → debrief.
  Walk through a sample CTG procedure and one EMG procedure.
- Flight dynamics workshop: read the orbit, predict the next AOS,
  understand what eclipse does to the power profile and thermal
  profile.
- Dry-runs: the Mon-night and Tue-night dry-runs are 90-min
  scenarios with no failure injection (operator practice only) and
  one failure injection (recovery practice).

End of Day 2: **operations training quiz** — short MCQ + short-answer
covering the MCS UI, the telemetry primer, the procedure index, and
the voice-loop discipline.

Detailed lesson plans: `week3/training_day1.md`,
`week3/training_day2.md`.

---

## 4. The two simulation days (Wed 19 + Thu 20 Aug)

### Wed 19 Aug — LEOP Simulation Day

**Mission phase simulated.** From AOS at the first Iqaluit pass
through OBC application boot, antenna deployment, sequential
power-on, and detumble.

**Breakpoint required:** "LEOP Day Start" (see §6) — spacecraft is
in phase 3 (BOOTLOADER_OPS), already in view of Iqaluit, with the
RF link not yet established. Operators must establish the link
within the first three minutes of the scenario or the pass closes
on them.

**Procedures expected:** LEOP-001 → -002 → -006 → -007 (then
optional -003 if time permits).

**Anomaly injections** (instructor decides which based on team
strength):

- *Easy:* `ttc_no_tm_at_aos.yaml` — beacon present but no full TM
  until link parameters corrected.
- *Medium:* `aocs_actuator_stuck.yaml` — one reaction wheel stuck
  during detumble.
- *Hard:* `obc_watchdog.yaml` — OBC watchdog reset mid-deploy.
- *Very hard:* `gs_antenna_failure.yaml` injected during second pass —
  forces failover to Troll.

Two teams alternate operator/observer over two passes; each team
runs one full operator shift and one full observer shift.

Detailed plan: `week3/sim_leop_instructor.md`.

### Thu 20 Aug — Commissioning Simulation Day

**Mission phase simulated.** From start of commissioning (post-LEOP)
through subsystem checkouts, AOCS sensor calibration, payload
power-on, FPA cool-down, and first light. Realistic over a half-day
of simulated operations across 4–5 ground passes (compressed time).

**Breakpoint required:** "Commissioning Day Start" (see §6) —
spacecraft is in phase 4 (LEOP-complete), all antennas deployed,
AOCS in DETUMBLE-completed state with rates ~0.05 °/s, FPA cooler
not yet on, payload in OFF state, battery at 90% SoC, first
Iqaluit pass beginning.

**Procedures expected:** COM-001 → -002 → -005 → -006 → -007 → -008 →
-009 → -010 → -011 → -012 (First Light). Not all need to complete; the
pass-criterion is *FPA cool-down initiated and one image acquired*.

**Anomaly injections:**

- *Easy:* `eps_overcurrent.yaml` during payload power-on.
- *Medium:* `fpa_overtemp.yaml` during FPA cool-down (cooler under-spec).
- *Hard:* `payload_corrupt_image.yaml` during First Light — corrupted
  image must be retaken.
- *Very hard:* `aocs_sensor_cascade.yaml` — star tracker degrades,
  pointing budget broken just before First Light, team must defer
  imaging and re-baseline.

Detailed plan: `week3/sim_commissioning_instructor.md`.

### Friday wrap (21 Aug)

- Morning: structured debrief led by student Flight Directors
  (one per team). Observer presentations to operators. Lessons
  learned cross-team.
- Afternoon: course synthesis, Canadian space sector pathways,
  course evaluation, cohort-internal final mission review.

---

## 5. Procedure curation for student reference

Students do **not** need to memorise the simulator's 50+ procedure
files. They need a curated quick-reference that lists:

1. The **20 procedures** most likely to be invoked in Week 3
   (LEOP-001/-002/-006/-007, all 13 COM-* commissioning procedures,
   the most relevant nominal procedures NOM-001/-002/-003/-009,
   and the most likely contingencies CTG-001 through -010).
2. A one-page-per-procedure card: title, owner positions, trigger,
   preconditions, top-level steps, exit criteria, links to the full
   procedure file.

The curated quick-reference will be Cyberrange-printed. Source:
`week3/student_procedure_quickref.md`.

The full simulator procedure tree
(`~/SpaceMissionSimulation/configs/eosat1/procedures/`) remains the
authoritative source — students consult it for detail.

---

## 6. Simulator breakpoints

The user asked for breakpoints at the start of each simulation day.
Three simulator scenarios cover the three breakpoints needed; one is
new. Specs are in `week3/breakpoint_spec.md`.

| Breakpoint | Use | Existing scenario | New work |
|------------|-----|-------------------|----------|
| **Nominal Post-Commissioning** | Training Day 1 + 2 dry-runs | `nominal_ops.yaml` (already configured, phase 5+) | None — use as is |
| **LEOP Day Start** (first AOS at Iqaluit, phase 3) | Wed 19 Aug | `first_contact.yaml` | None — use as is |
| **Commissioning Day Start** (post-LEOP, all antennas deployed, detumble done, payload OFF, first AOS) | Thu 20 Aug | *No exact match* | **New scenario file required: `commissioning_day_start.yaml`** — see breakpoint_spec.md for the YAML to add to the simulator |
| **End-of-Sim "What if" Branch** *(optional)* | Friday debrief — replay a shift's decision point | n/a | Optional — could record state mid-Wed/Thu run for replay |

The Commissioning Day Start scenario is the only new simulator
artifact required for Week 3. Spec is short (≈ 30 lines of YAML).

Optional intermediate breakpoints the instructor may want for
training Day 2 dry-runs:

- *Eclipse-entry start* — drop into the scenario at +T-5 min before
  first eclipse, for thermal/power discussion.
- *Pre-pass T-10* — drop in 10 min before AOS for pass-startup
  practice without LEOP overhead.

These can be implemented as alternate `initial_conditions.start_at`
parameters in derivative scenario files.

---

## 7. Peer-review worksheet pack

Four worksheets, all single-page, A4. Student observers fill one per
operator-shift. Used at the post-sim debrief.

| Axis | What it measures |
|------|------------------|
| **Team** | Role clarity, FD authority, coverage, fatigue management |
| **Communications** | Voice-loop discipline, callouts, handover quality, MCS chat usage |
| **Space usage** | Console layout, line-of-sight, distraction management, physical comfort |
| **Technical** | Procedure adherence, anomaly response timing, telemetry interpretation, command discipline |

Each worksheet is a 4-block grid: *Observed*, *Worked well*, *Could
improve*, *Specific recommendation*. Source:
`week3/peer_review_worksheets.md`.

---

## 8. Instructor scenario plans

For each simulation day, the instructor needs:

- A scenario timeline (in real and simulated time) with anomaly
  injection cues.
- A pass-criteria list (operator-side), so the FD/coach knows when to
  step in.
- A failure-injection menu with parameters (which valve, which wheel,
  what severity).
- A debrief script (questions to ask, traps to watch for).

Two instructor scenario packs are skeleton-drafted:

- `week3/sim_leop_instructor.md` — Wed 19 Aug LEOP day, two-pass
  structure with team swap.
- `week3/sim_commissioning_instructor.md` — Thu 20 Aug
  commissioning day, four-pass compressed timeline.

---

## 9. Tool-specific student documentation

Students must **be fluent** in:

1. **Mission Control System (MCS)**: telemetry views, command panels,
   limits, FDIR panel, procedure panel, contact schedule, voice-loop
   chat, manual viewer. No coding required; the MCS is a webapp.
   Source for student doc: simulator's
   `configs/eosat1/mcs/role_analysis/*` files.
2. **Mission Planning System (MPS)**: imaging-target picker, activity
   types, ground-station schedule, conflict checker, plan exporter.
   Source: simulator's `configs/eosat1/planning/*.yaml` files.
3. **Procedure files** themselves — students need to know how to read
   them (preconditions, ownership, verification rows) but not write
   them.

Students do **not** need to know:

- The simulator internals — Python, YAML, scenario file format,
  network protocol, FDIR DSL.
- How to write procedures or planning configurations.
- The flight-dynamics maths under the orbit propagator.

A curated *MCS & MPS Student Reference* document is part of the
hand-off (skeleton: `week3/student_tool_reference.md`).

---

## 10. Document inventory & status

Every Week 3 document lives under `docs/orbit_north/week3/`.

| File | Type | Status |
|------|------|--------|
| `training_day1.md` | Lesson plan, instructor + student | Skeleton drafted |
| `training_day2.md` | Lesson plan, instructor + student | Skeleton drafted |
| `student_tool_reference.md` | Student MCS/MPS reference | Skeleton drafted |
| `student_procedure_quickref.md` | Curated procedure card pack | Skeleton drafted |
| `sim_leop_instructor.md` | Wed sim day instructor pack | Skeleton drafted |
| `sim_commissioning_instructor.md` | Thu sim day instructor pack | Skeleton drafted |
| `peer_review_worksheets.md` | Four observer worksheets | Skeleton drafted |
| `breakpoint_spec.md` | Simulator scenario specs incl. new YAML | Skeleton drafted |

Outstanding writing work, listed for Claude Code in the hand-off
file `SPACECDF_EXPANSION_TASKS.md`.

---

## 11. Hand-off action items

To finish Week 3 to publication quality, Claude Code needs to:

1. Implement the new `commissioning_day_start.yaml` scenario per
   `breakpoint_spec.md` and add it to the simulator repo.
2. Expand each skeleton draft to publication length (typically
   2 – 4× current). Each skeleton lists which simulator files to
   read for the substantive content.
3. Cross-check every procedure ID and scenario file referenced
   against the simulator (procedures and scenario names can drift).
4. Add diagrams: at minimum, a Cyberrange console layout diagram, a
   pass-geometry diagram per ground station, a voice-loop wiring
   diagram, and an anomaly-response flowchart.
5. Build the Week 3 PDFs with the same `build_pdf.py` pipeline used
   for the syllabus. Two output bundles:
   - **Student bundle**: training_day*.md + student_tool_reference.md
     + student_procedure_quickref.md + peer_review_worksheets.md.
   - **Instructor bundle**: sim_leop_instructor.md +
     sim_commissioning_instructor.md + breakpoint_spec.md +
     a copy of the procedure index for facilitator use.
