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

[Claude Code: 350 words. Cover the canonical phrasing used at NASA
and ESA mission control. Include a one-page reference card with:
addressing pattern ("FD, AOCS — go for star-tracker enable"),
GO/NO-GO call-and-response, hot-mike rules, "loop discipline"
expectations, the rule that the FD does not command directly. Cite
ESA *Operations Manual for Mission Control* and the Mission
Operations Voice Procedure standard from NASA APPEL —
https://appel.nasa.gov/

Also provide a short EN/FR glossary of voice-loop callouts. uOttawa
is bilingual; the team may use either language but must use one
consistently per shift.]

### 1.1 Standard callouts

[Claude Code: produce a 12-row table — callout · meaning · response.
Examples: "Comm check 1-2-3", "Standby plus 30", "TTC report",
"AOS in 2", "Pass closed".]

### 1.2 GO/NO-GO protocol

[Claude Code: 150 words. The FD polls each position; each position
returns GO, NO-GO with reason, or HOLD with reason. The FD makes
the decision. No commanding without an explicit FD authorisation.]

---

## 2. Procedure walk-through

### 2.1 NOM-001 Pass Startup

[Claude Code: walk students through procedure
`procedures/nominal/startup.md` step by step. Show how each step
maps to MCS UI actions. ~350 words plus annotated MCS screenshots.]

### 2.2 CTG-003 TTC Link Loss Recovery

[Claude Code: walk students through
`procedures/contingency/ttc_link_loss.md`. Emphasise the
detection/assessment/recovery loop. ~350 words plus annotated MCS
screenshots showing the FDIR panel and link-status telemetry.]

---

## 3. Shift handover practice (NOM-012)

[Claude Code: 150 words. Use procedure `nominal/shift_handover.md`.
Each team performs two handovers — outgoing FD briefs incoming FD
using the NOM-012 template — and the instructor times them. Target:
under 6 minutes.]

---

## 4. Flight-dynamics workshop

[Claude Code: 400 words plus three Python figures. Workshop
exercises:

1. Read the orbit (TLE in `configs/eosat1/orbit.yaml`); compute
   period and rev/day; predict the next 24 h of Iqaluit AOS times.
2. Compute pass duration as a function of maximum elevation; show
   the typical 8–12 minute polar pass.
3. Explain eclipse: where it starts in the orbit, how long it lasts,
   what the power and thermal consequences are.

Figures (use the brand stylesheet from `outputs/sample_figures/`):

- Ground-track + Iqaluit and Troll visibility cones
- Pass-elevation profile vs time for a typical Iqaluit pass
- Eclipse fraction over a 24 h window]

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

[Claude Code: produce a 15-question MCQ + short-answer paper, 30
minutes. Topics:

- Voice-loop discipline (3 Qs)
- MCS UI navigation (3 Qs)
- Telemetry interpretation — limits and SIDs (3 Qs)
- Procedure structure — what's in a procedure file (2 Qs)
- Anomaly response steps (2 Qs)
- Pass timing — AOS / TCA / LOS arithmetic (2 Qs)

Solutions on a separate page for the instructor pack.]

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
- CCSDS Pus standards (background) —
  https://public.ccsds.org/Publications/AllPubs.aspx
