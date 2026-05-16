# ORBIT NORTH — Proposed Changes (Summer 2026)
**Owner:** Dr Franz Newland · uOttawa SEDTI
**Status:** v3 — agreed schedule, source files updated, bilingual EN/FR
**Last updated:** 2026-05-05

This proposal captures the agreed changes to the ORBIT NORTH course
materials and is the working document behind the four updated source
files in this folder:

| File | Purpose |
|------|---------|
| `CHANGES_PROPOSAL.md` | This document |
| `syllabus_en.md` | English syllabus source — Pandoc + uOttawa Horizon style |
| `syllabus_fr.md` | French syllabus source — same brand, bilingual page footer |
| `recruitment_en.md` | Recruitment poster source, English |
| `recruitment_fr.md` | Recruitment poster source, French |

---

## 1. Headline changes (v3)

1. **12-day intensive program** — replaces "3-week" framing throughout.
2. **Course window** — Thursday 6 August to Friday 21 August 2026,
   weekdays only, **09:00 – 17:00** every day.
3. **New ordering** — Canadian context first, mission concept developed
   in the CDF before MCR, regulatory landscape *after* MCR, subsystem
   CDF intensive, PDR Friday afternoon of Week 2, then operations week
   in the Cyberrange.
4. **MCR is now an early-Week-2 gate.** Concept work is done across
   Thursday afternoon, Friday, and the weekend; MCR is presented
   Monday morning. PRR/SRR are explicitly collapsed into CDF Day 1
   (Tuesday).
5. **No public-facing final presentation** is mentioned in any document.
   The Friday Aug 21 wrap is cohort-internal only.
6. **Stakeholder/user-needs analysis** is intentionally light-touch in
   this course. Other courses in the programme cover it more deeply.
7. **Bilingual delivery materials.** Syllabus and recruitment poster are
   produced in parallel English and French source files. Indigenous
   Affirmation, AIG/GIA attribution, and bilingual rights statements
   carry into both versions per uOttawa convention.
8. **Style alignment.** All four source files carry YAML front-matter
   (`brand: uottawa-horizon`) so the build script in
   `docs/PDF_BRANDING_PLAN.md` will render them with the Horizon palette,
   Work Sans / Spectral typography, the uOttawa lockup on the cover,
   and the SEDTI footer wordmark.

---

## 2. Final schedule

### Week 1 — Canadian Context, CDF Intro & Concept Development · Thu 6 – Fri 7 Aug · 2 days

| Day | AM | PM |
|-----|----|----|
| Thu 6 Aug | **Canadian space ecosystem** (compressed): history, present, emerging, course onboarding, team formation, discipline-role assignment, SpaceCDF tool tour. | **30-min regulatory teaser**, then **CDF and mission-design intro**. Teams open a SpaceCDF mission file and begin concept work. |
| Fri 7 Aug | **Mission architecture & alternatives** in the CDF; ConOps top-level v0; concept v0. | Concept refinement; **first touch on the CDF risk register** (preliminary identification only); end-of-week consolidation. Weekend pre-work briefed. |

### Week 2 — MCR, Regulatory & CDF Intensive · Mon 10 – Fri 14 Aug · 5 days

| Day | AM | PM |
|-----|----|----|
| Mon 10 Aug | **Mission Concept Review (MCR)** — gate. Risk register v0 captured. Programmatic envelope agreed. | **Canadian regulatory landscape**: RSSSA, ITU and Radiocommunication Act, ISED CPC-2-6-02 spectrum licensing, Export Control List, Controlled Goods Programme, ITAR overview, debris mitigation, UN Registration Convention. |
| Tue 11 Aug | **CDF Day 1** — System-V briefing, **PRR/SRR collapsed** into the CDF kickoff. Requirements baseline; functional decomposition; first parametric budgets. Power, AOCS, thermal commenced in the afternoon. | (continued) |
| Wed 12 Aug | **CDF Day 2** — Power, AOCS, thermal complete; orbit-selection trade. | (continued) |
| Thu 13 Aug | **CDF Day 3** — Comms, structure, propulsion. Two formal trades: link band and propulsion. | (continued) |
| Fri 14 Aug | **CDF Day 4 (AM)** — Integration, V&V matrix, cost CER, BOM, risk register closure, planning baseline review. | **Preliminary Design Review (PDR)** — gate. ECSS document export (MRD, TS, VP). |

### Week 3 — Operations & Mission Simulation · Mon 17 – Fri 21 Aug · 5 days · uOttawa Cyberrange

| Day | Theme |
|-----|-------|
| Mon 17 Aug | Operations Concept Development |
| Tue 18 Aug | Operations Training |
| Wed 19 Aug | Mission Simulation Day 1 — LEOP & Commissioning |
| Thu 20 Aug | Mission Simulation Day 2 — Nominal Ops & Contingency |
| Fri 21 Aug | Wrap-up & cohort-internal final mission review |

---

## 3. Notes on the v3 design

- **Tuesday Wk 2 is the heaviest day** — System-V briefing, full
  requirements baseline (PRR/SRR collapsed), and the start of
  Power/AOCS/Thermal all in one day. The syllabus explicitly briefs
  **weekend pre-work** between Friday and Monday and again between
  Monday and Tuesday so students arrive primed.
- **Regulatory back-check** is handled inside the CDF tool itself
  (the platform now includes a regulatory-check module), so a
  separate workshop is no longer required.
- **PDR slack** — Friday afternoon Wk 2 is tight. If we hit a design
  issue, the operational fallback is to defer PDR closure to **Monday
  morning Wk 3** in the Cyberrange meeting room, before the operations
  block begins. We do not announce this in the syllabus; we simply use
  it if needed.
- **ECSS / NASA terminology note.** The course uses NASA's *Mission
  Concept Review* meaning (end of Pre-Phase A). ECSS reuses "MCR"
  for the Mission Close-out Review at the end of Phase E. The syllabus
  flags this once so cross-readers don't get confused.
- **Stakeholder analysis.** Down-weighted; remains as a brief learning
  outcome and a touchpoint in the Day 1 ecosystem session and the
  Day 2 (Friday) concept development. No standalone session.
- **Bilingual rights statement** and **Indigenous Affirmation** are
  carried into both EN and FR syllabi unchanged.
- **No public-facing presentation** is mentioned anywhere in the
  student-facing materials.

---

## 4. Translation note

The French source files are written in standard uOttawa-conventional
French. Two terms warrant verification with the SEDTI office before
the PDFs go to print:

1. **SEDTI's official French name.** The syllabus uses *"École
   d'innovation en conception et en enseignement du génie (SEDTI)"*
   as the working translation. uOttawa convention is to register an
   official bilingual school name; please confirm and adjust the
   French source if a different official form exists.
2. **GNG 3100 / SYS 5186 official French course titles.** I have
   used *"Sujets en génie I"* and *"Sujets avancés en ingénierie
   système"*; please confirm against the uOttawa course calendar.

Everything else (course content, dates, ECSS/NASA terminology,
proper nouns such as *SpaceCDF*, *Cyberrange*, *Brightspace*,
*ORBIT NORTH*) is consistent with Canadian bilingual technical usage.

---

## 5. What's still optional / could be added later

- **Hero image on each cover.** Currently using the SSO ground-track
  sample from `assets/figures/orbits/`. The Course Plan and Facilitator
  Book brief in `PDF_BRANDING_PLAN.md` carries a longer figure
  catalogue if you want a different hero image per document.
- **Author / credits page.** The PDF branding plan includes a
  copyright/document-control page as a default template. The syllabus
  uses a minimal version; we can expand it once the cohort
  facilitator team is confirmed.
- **Supplementary reading list.** The course no longer follows
  spacese.spacegrant.org module-by-module; it remains in the
  references list as optional self-study. If you want to add or
  remove items, edit the *Required Materials* section of both
  syllabi.

---

## 6. Status

- ✅ v3 schedule agreed
- ✅ Source files updated (EN + FR for both syllabus and recruitment)
- ✅ Bilingual rights, Indigenous Affirmation, AIG attribution preserved
- ⏭ Verify SEDTI French name, GNG/SYS official French course titles
- ⏭ Build to PDF using the `docs/PDF_BRANDING_PLAN.md` toolchain once
     the uOttawa Horizon SVG and SEDTI mark are dropped into
     `docs/assets/brand/uottawa/`
