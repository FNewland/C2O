---
title: "Week 3 — Training Day 2: Mission Operations Training"
subtitle: "ORBIT NORTH · Tue 18 August 2026 · uOttawa Cyberrange"
course-codes: "GNG 3100 · SYS 5186"
term: "Summer 2026"
version: "v1 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
audience: "students + instructor"
expected-reading: "Curated procedure quick-reference (separate doc) and the MCS & MPS Reference §5 (anomaly response panel) before Day 2; one nominal procedure (NOM-001) and one contingency procedure (CTG-003) before the dry-run after lunch"
---

# Training Day 2 — Mission Operations Training

**Day at a glance**

| When | What | Output |
|------|------|--------|
| 09:00 – 10:00 | Voice-loop discipline + GO/NO-GO protocol | Voice card learnt |
| 10:00 – 11:30 | Procedure walk-through: NOM-001 and CTG-003 | Q&A captured |
| 11:30 – 12:00 | Shift handover practice (NOM-012) | Two handovers logged |
| 13:00 – 14:00 | Flight-dynamics workshop | Pass timing predicted |
| 14:00 – 15:30 | Dry-run 1 — nominal pass, no failures | Operator-shift logs |
| 15:30 – 16:30 | Dry-run 2 — nominal pass with one failure injected | Anomaly tickets, debrief |
| 16:30 – 17:00 | **Operations training quiz** | Quiz submitted |

**Setting:** uOttawa Cyberrange. Two consoles set up by 09:00. Both
dry-runs use the **Nominal Post-Commissioning** breakpoint (BP-1).

---

## 1. Voice-loop discipline

Textbook Part 2, §§9.1–9.2, is the session text and the reference
card: the addressing pattern ("FD, AOCS — go for star-tracker
enable": the station called, then the caller, then the message),
the GO/NO-GO call-and-response, the hot-mike rule (push-to-talk;
only the FD goes hot-mike, and announces it), loop discipline, and
the rule that the FD authorises while the owning position commands.
Run the three drills of §9.2: addressing, GO/NO-GO with a hold, and
an anomaly callout.

The callouts stay in English for every crew. The French edition of
the textbook gives the meaning of each callout in French in the
same table (§9.2, *Callout vocabulary*), which serves as the EN/FR
glossary.

### 1.1 Standard callouts

The callout table is textbook Part 2, §9.2, *Callout vocabulary*:
15 callouts with meaning and expected response, from "Comm check
1-2-3" to "Loop discipline", including "Standby plus 30", "AOS in
N" and "Pass closed". Print it as the voice card.

### 1.2 GO/NO-GO protocol

Before any command that changes the spacecraft's state, the FD
polls the positions concerned ("AOCS, EPS, FDIR — go for
ST1_POWER?"). Each answers in poll order: *Go*, *No-go, [reason]*
or *Hold, [reason]*. The FD decides and declares it on the loop:
"Go for ST1_POWER" or "Hold on ST1_POWER, [reason]". The owning
position commands only on that explicit GO. Staging the command
(first key) before the GO is fine; uplinking before it is a
violation. Source: textbook Part 2, §9.2, *GO / NO-GO protocol*.

---

## 2. Procedure walk-through

### 2.1 NOM-001 Pass Startup

Textbook Part 2, §9.3, walks NOM-001 step by step against the MCS:
the pre-checklist calculations, the checklist, the post-conditions,
the common deviations, and which cards the MCS can run by itself.
Use it as the session text, with `procedures/nominal/startup.md`
open on the PRC page so students see each step become a line in
the panel.

### 2.2 CTG-003 TTC Link Loss Recovery

Textbook Part 2, §9.4, is the walk-through: the escalation-ladder
figure (check the ground station is tracking, blind-command the
primary transponder, switch to the redundant one, retry the
primary, verify, escalate to EMG-004), the read-and-do checklist,
why it is structured that way, and what operators often miss. The
loop to emphasise is detect (`ttc.link_status`, 0x0501, leaves 2)
→ assess (ground or space?) → recover (least intrusive rung
first).

---

## 3. Shift handover practice (NOM-012)

Textbook Part 2, §9.5, gives the NOM-012 template and the drill.
Each team performs two handovers: the outgoing FD briefs the
incoming FD on spacecraft posture, open anomalies, work in progress
and the next pass plan; the incoming FD reads it back verbatim; then
authority is handed over on the loop. The instructor times each
one. Target: under 6 minutes.

---

## 4. Flight-dynamics workshop

> **TODO (author):** Write the 400-word flight-dynamics workshop
> and its three Python figures (ground track with the five
> stations' visibility cones; elevation against time for a typical
> Iqaluit pass; eclipse fraction over a 24 h window). Exercises:
> read the TLE in `configs/eosat1/orbit.yaml` and compute the period
> (94.5 min) and revolutions per day (15.24); predict the next 24 h
> of Iqaluit AOS times; pass duration against maximum elevation
> (9.3 min overhead at 513 km with the 5° mask, 7.5 min on average);
> where eclipse starts, how long it lasts (33.2–35.2 min over the
> year), and its power and thermal consequences. Textbook Part 2,
> §9.6 and §§13.2–13.3, already have the arithmetic.

---

## 5. Dry-runs

### Dry-run 1 — nominal pass

- **Scenario:** BP-1 (Nominal Post-Commissioning).
- **Duration:** 90 min real time, 90 min sim time (1× speed).
- **Procedures expected:** NOM-001 → NOM-002 (imaging) → NOM-003
  (data downlink) → NOM-009 (routine health check) → LOS.
- **Failure injection:** none.
- **Outputs:** operator shift log; observer team uses
  *Communications* peer-review worksheet only.

### Dry-run 2 — nominal pass with one failure

- **Scenario:** BP-1 with one easy failure injected ~T+30 min.
- **Recommended injection:** `eps_overcurrent.yaml` on the
  `payload` line (forces CTG-012 *Overcurrent Response*).
- **Operator pass criterion:** anomaly detected, isolated, and
  procedure CTG-012 executed; pass continues to LOS.
- **Outputs:** operator shift log + anomaly ticket; observer team
  uses *Technical* peer-review worksheet.

---

## 6. Operations training quiz

> **TODO (author):** Write the 15-question paper (multiple choice
> and short answer, 30 minutes), with solutions on a separate page
> for the instructor pack: voice-loop discipline (3 questions), MCS
> navigation (3), telemetry interpretation — limits and SIDs (3),
> procedure structure (2), anomaly response (2), and pass timing —
> AOS / TCA / LOS arithmetic (2).

---

## 7. Expected reading for Wednesday

> **Expected reading before Wednesday LEOP day.** Read sections
> 1 – 4 of the *LEOP Day Instructor Pack* student-facing extract
> (a redacted version of `sim_leop_instructor.md`). Approximate
> reading time 30 minutes. Read procedures **LEOP-001, LEOP-002,
> LEOP-006, LEOP-007** in full
> (`procedures/leop/*.md`). Approximate reading time 30 minutes.

---

## 8. Tools, files & references

### Simulator files referenced

- `configs/eosat1/procedures/nominal/startup.md`
- `configs/eosat1/procedures/contingency/ttc_link_loss.md`
- `configs/eosat1/procedures/nominal/shift_handover.md`
- `configs/eosat1/procedures/leop/*.md` (for evening reading)
- `configs/eosat1/scenarios/eps_overcurrent.yaml`

### Open references

- NASA APPEL — Voice loop and mission ops standards —
  https://appel.nasa.gov/
- ESA Operations *Mission Operations Concept* —
  https://www.esa.int/Enabling_Support/Operations
- ECSS-E-ST-70-11C — Space segment operability —
  https://ecss.nl/standards/active-standards/ecss-e-st-70-11c-space-segment-operability/
- *NASA Systems Engineering Handbook* (SP-2016-6105 Rev 2) §8 —
  https://www.nasa.gov/reference/systems-engineering-handbook/
- CCSDS space packet standards (background; PUS itself is ECSS-E-ST-70-41C) —
  https://public.ccsds.org/Publications/AllPubs.aspx
