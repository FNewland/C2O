# OER Conversion Inventory — `facilitator_book_expanded.md`

Source: `/Users/FNewland/SpaceCDF-arcadia/docs/course/facilitator_book_expanded.md` (11,5xx lines; Part 1 = 20 chapters, lines 269–9679; Part 2 = 9680–10462; Part 3/Appendix = 10463–10833; Part 4 = 10834–11330; HTML Index = 11331–end).
Figures: `/Users/FNewland/SpaceCDF-arcadia/docs/assets/figures/` (29 `fig_*.png`, 11 `_inline/svg_*.png`, hundreds of `_math/m_*.svg`).
Generators: one script per figure at `/Users/FNewland/SpaceCDF-arcadia/docs/assets/figures/fig_*.py` (29 scripts) + `uottawa_brand.py`.

Classification key: **DELETE** = pure course admin; **REWORD** = keep content, drop course framing; **RESTRUCTURE** = exercise/worksheet → problem set or self-study activity.

---

## A. Course / institution references

### Front matter (lines 1–268)

| Line | Snippet | Class |
|---|---|---|
| 2–12 | YAML: `title: "SpaceCDF — A Course Textbook…"`, `subtitle: "…40-hour Concurrent Design Facility programme"`, `brand: uottawa-horizon`, `publisher: "…SEDTI"`, `footer-en: "SpaceCDF Course Textbook · 2026"`, `footer-fr: "Manuel de l'animateur SpaceCDF"`, `running: "SpaceCDF — Course Textbook"` | REWORD (new title, CC-BY publisher line, drop brand/footers) |
| 16–33 | `## How to use this book` — "SpaceCDF course volume … 40-hour … Per-session course chapters (Sessions 1.1 – 5.4) … references they need from Day 1 … every formula students uses" | REWORD (describe the four parts without session/Day language) |
| 35–36 | "paired with the *Learner's Workbook*, which carries the worksheets students fills in." | DELETE (also typo "students fills") |
| 38–42 | "> **Expected reading before any session.** NASA SEH §1–§3 …" | REWORD → "Recommended background reading" |
| 44–46 | `![Lifecycle phases — what each Day touches]` / "*The lifecycle students lives.*" | REWORD caption (typo "students lives") |
| 48–50 | "*The 17 NASA SEH processes; each session names which process(es) it sits inside.*" | REWORD |
| 53–72 | `# Acknowledgement — Generative AI (AIG)` — "SpaceCDF teaching team", "Any course deliverable that incorporates content … must carry the AIG badge" | REWORD (keep AIG attribution; drop "course deliverable" rule or move to licence page) |
| 75–193 | `# How This Textbook Was Generated` — "students will exercise during the 40-hour intensive" (78), "`docs/course/facilitator/`" (91), "an instructor can lift any one…" (93), "Begin by asking the group…", "whiteboard" (101–102), "Teaching Notes" (105), "workbook kept in lock-step" (112), "uOttawa Horizon palette" (123), "*Course Workbook*" (150), "uOttawa-styled HTML scaffold" (159), "teaching team" (85, 174), "The first time a student in students generates an SRR" (185 — typo) | REWORD heavily or move to a short colophon; most of it is build-pipeline internals |
| 196–232 | `# Agents, Positions, and the SpaceCDF Architecture` — "a CDF session converges so quickly" (230) | REWORD (tool description; keep as "About the companion tool" appendix) |
| 234–265 | `# Design Reviews and the SpaceCDF Exports` — "uOttawa SpaceCDF course identity: garnet cover banner … u Ottawa · UNIVERSITÉ D'OTTAWA" (259–262), "supporting course material" (265) | REWORD (259–265 DELETE) |
| 267 | `# Part 1 — Course Lectures` | REWORD → "Part 1 — Foundations and Design" |

### Session 1.1 (269–834)

| Line | Snippet | Class |
|---|---|---|
| 269 | `# Session 1.1: Introduction to Space Mission Design` | REWORD |
| 281 | "> **Expected reading before this session.** NASA SEH §1–§3 (≈ 60 min)… NPR 7123.1D §3 (≈ 30 min)." | REWORD (drop timings) |
| 285–286 | "**Prerequisites:** None (engineering background assumed)" / inline "**References:**" list | REWORD (keep as chapter preamble; dedupe with §References at 825) |
| 296 | "By the end of this session, participants will be able to:" | REWORD → "By the end of this chapter, you will be able to:" |
| 330 | "\| Session format \| 3--4 hour focused design sessions, typically 2 per week \|" | KEEP (ESA CDF fact, not course admin) |
| 347 | "…with each session refining the design toward closure." | KEEP (CDF context) |
| 362 | "**Discussion point.** *What advantages does concurrent design offer…*" | RESTRUCTURE → review question |
| 507 | "**Exercise.** *Sketch the V-model from memory…*" | RESTRUCTURE |
| 575 | "**Exercise.** *Map each of the 17 processes to a feature in SpaceCDF… Complete Part A of Worksheet 1.1.*" | RESTRUCTURE (drop worksheet ref) |
| 730 | "**Exercise.** *In SpaceCDF, go to the Gate Review tab…*" | RESTRUCTURE (tool activity) |
| 759 | "The most productive CDF sessions are those where interface conflicts…" | KEEP (CDF context) |
| 769 | "**Discussion point.** *Which positions would interact most frequently in your mission?*" | RESTRUCTURE |
| 773 | `## 6. Session Summary` | REWORD → "Summary" |
| 788 | "Throughout this course, we use a second running example…" | REWORD → "Throughout this book" |
| 809 | "As the course progresses, each session will show…" | REWORD |
| 811 | "**Discussion point.** *How does the CDF process differ when the team has only 5 subsystems…*" | RESTRUCTURE |
| 815–821 | `## 7. Tool Exercise` … "**Complete Worksheet 1.1:**" | RESTRUCTURE (→ "Problems" / "Hands-on with SpaceCDF"); 821 DELETE |

### Session 1.2 (835–1232)

| Line | Snippet | Class |
|---|---|---|
| 835 | `# Session 1.2: The Canadian Space Ecosystem & Regulatory Environment` | REWORD |
| 842 | "> **Expected reading before this session.** NASA SEH §4.1 (≈ 30 min); SMAD4 Ch. 1" | REWORD (note: reading list does not match chapter topic — see F) |
| 846 | "**Prerequisites:** Session 1.1" | REWORD → "Chapter 1" |
| 860 | "By the end of this session, participants will be able to:" | REWORD |
| 958, 1069, 1203 | "**Discussion point.** *For your mission concept, which industry tier…*" / "*…RSSSA conditions…*" / "*…US-origin components…*" | RESTRUCTURE |
| 1207 | `## Session Summary` | REWORD |

### Session 1.3 (1233–1722)

| Line | Snippet | Class |
|---|---|---|
| 1233 | `# Session 1.3: International Standards for Space Systems` | REWORD |
| 1240 | "> **Expected reading before this session.** NASA SEH §6.5 — Decision Analysis (≈ 30 min); SMAD4 Ch. 6." | REWORD (mismatched topic — see F) |
| 1244 | "**Prerequisites:** Sessions 1.1--1.2" | REWORD |
| 1258 | "By the end of this session, participants will be able to:" | REWORD |
| 1690 | "**Exercise.** *In SpaceCDF, navigate to the Compliance panel…*" | RESTRUCTURE |
| 1694 | `## Session Summary` | REWORD |

### Session 1.4 (1723–2344)

| Line | Snippet | Class |
|---|---|---|
| 1723 | `# Session 1.4: Mission Needs, Stakeholder Analysis & Trade Studies` | REWORD |
| 1730 | "> **Expected reading before this session.** NASA SEH Appendix S — ConOps (≈ 45 min); SMAD4 Ch. 14." | REWORD |
| 1734 | "**Prerequisites:** Sessions 1.1--1.3" | REWORD |
| 1748 | "By the end of this session, participants will be able to:" | REWORD |
| 1811 | "**Discussion point.** *Why is it harmful to specify HOW at this stage?*" | RESTRUCTURE |
| 1848 | "**Exercise.** *Complete Part A of Worksheet 1.4 -- identify at least 4 stakeholders for your team's mission…*" | RESTRUCTURE (drop worksheet) |
| 1910 | "**Exercise.** *…trace the full hierarchy… Complete Part B of Worksheet 1.4.*" | RESTRUCTURE |
| 2063 | "**Exercise.** *Practice the pairwise comparison method… lunch restaurant choice…*" | RESTRUCTURE (good self-study problem) |
| 2172 | "**Exercise.** *In the ConOps tab, build your mission architecture diagram…*" | RESTRUCTURE |
| 2270 | "**SpaceCDF exercise:** *Check the Data Budget on the Dashboard…*" | RESTRUCTURE |
| 2274–2281 | `### 11. ConOps Tool Exercise` … "**Complete Worksheet 1.4, Parts E and F:**" | RESTRUCTURE; 2281 DELETE |
| 2320 | `## Session Summary` | REWORD |

### Session 2.1 (2345–2742)

| Line | Snippet | Class |
|---|---|---|
| 2345 | `# Session 2.1: The System-V and Requirements Engineering` | REWORD |
| 2347 | "> **Expected reading before this session.** NASA SEH Appendix C … (≈ 30 min); ECSS-E-ST-10C §5.5." | REWORD |
| 2351–2352 | "**Prerequisites:** Week 1 complete (mission need, stakeholder analysis, ConOps defined)" / "**SpaceCDF Tab:** Requirements" | REWORD ("Chapters 1–4") |
| 2368 | "By the end of this session, participants will be able to:" | REWORD |
| 2375 | LO 6: "Use SpaceCDF's Requirements tab to generate, validate, and manage requirements" | REWORD or DELETE (tool-specific LO) |
| 2696–2716 | `## 7. SpaceCDF Exercise` … `### Exercise Tasks` … "1. Generate requirements for your team's mission" … "6. Complete Worksheet 2.1" | RESTRUCTURE; 2716 DELETE |
| 2730 | `## Session Summary` | REWORD |

### Session 2.2 (2743–3065)

| Line | Snippet | Class |
|---|---|---|
| 2743 | `# Session 2.2: Functional Decomposition and Allocation` | REWORD |
| 2745–2747 | `![System-V model with course touchpoints.]` / caption "*System-V model with course touchpoints.*" | REWORD caption (figure also misplaced — belongs in 2.1; see D) |
| 2750 | "> **Expected reading before this session.** NASA SEH §4.3 (≈ 30 min); ECSS-E-ST-10C §5.6." | REWORD |
| 2754 | "**Prerequisites:** Session 2.1 (requirements defined and validated)" | REWORD |
| 2771 | "By the end of this session, participants will be able to:" | REWORD |
| 2943 | "**Discussion point.** *For each multi-allocated function in your design…*" | RESTRUCTURE |
| 2991–3014 | `## 5. SpaceCDF Function Tree Exercise` … "5. Complete Worksheet 2.2" | RESTRUCTURE; 3014 DELETE |
| 3054 | `## Session Summary` | REWORD |

### Session 2.3 (3066–3425)

| Line | Snippet | Class |
|---|---|---|
| 3066 | `# Session 2.3: Orbit Selection and Mission Architecture` | REWORD |
| 3073 | "> **Expected reading before this session.** ECSS-E-ST-10-24C — Interface management (≈ 60 min)" | REWORD (mismatched — interfaces are 2.4's topic) |
| 3077 | "**Prerequisites:** Sessions 2.1--2.2 (requirements and functions defined)" | REWORD |
| 3096 | "By the end of this session, participants will be able to:" | REWORD |
| 3309 | "This deorbit ΔV is a critical input to the propulsion sizing in Session 3.4." | REWORD → "Chapter 12" |
| 3382–3408 | `## 7. SpaceCDF Orbit Trade Exercise` … "- Complete Worksheet 2.3" | RESTRUCTURE; 3408 DELETE |
| 3412 | `## Session Summary` | REWORD |

### Session 2.4 (3426–3857)

| Line | Snippet | Class |
|---|---|---|
| 3426 | `# Session 2.4: Mission Architecture -- Segments, Interfaces, and Budgets` | REWORD |
| 3428 | "> **Expected reading before this session.** NASA SEH §4.4 (≈ 30 min)." | REWORD |
| 3432–3433 | "**Prerequisites:** Sessions 2.1--2.3…" / "**SpaceCDF Tabs:** Mission Architecture, System Architecture, Interfaces, Dashboard" | REWORD |
| 3449 | "By the end of this session, participants will be able to:" | REWORD |
| 3744–3746 | "These budgets will be developed in detail during Week 2 Day 3--4 sessions:" / table column header "\| Session \|" | REWORD → "in Chapters 9–12", rename column "Chapter" |
| 3815 | "…the sessions are shorter and the trade space is narrower." | REWORD ("the design loops are shorter") |
| 3819–3833 | `## 5. SpaceCDF Exercise` … "3. **Dashboard:** Examine all KPI cards" … "5. Complete Worksheet 2.4" | RESTRUCTURE; 3833 DELETE |
| 3844 | `## Session Summary` | REWORD |

### Session 3.1 (3858–4645)

| Line | Snippet | Class |
|---|---|---|
| 3858 | `# Session 3.1: Power System and Thermal Control Design` | REWORD |
| 3875 | "> **Expected reading before this session.** SMAD4 Ch. 11 (power); ECSS-E-ST-20C §5 (≈ 60 min). Patel…" | REWORD |
| 3879–3880 | "**Prerequisites:** Sessions 2.1--2.4…" / "**SpaceCDF Tabs:** Dashboard (Power KPI), Engineering Budgets, Timing Budget, Parametric" | REWORD |
| 3901 | "By the end of this session, participants will be able to:" | REWORD |
| 4509 | "> From Session 2.4: P_avg,demand = 0.68 W." | REWORD → "From Chapter 8" |
| 4594–4613 | `## 6. SpaceCDF Exercise` … "Is eclipse time consistent with your orbit calculation from Session 2.3?" (4604) … `### Worksheet 3.1 Tasks` (4613) | RESTRUCTURE |
| 4624 | `## Session Summary` | REWORD |

### Session 3.2 (4646–5394)

| Line | Snippet | Class |
|---|---|---|
| 4646 | `# Session 3.2: Attitude and Orbit Control System (AOCS)` | REWORD |
| 4653 | "> **Expected reading before this session.** Cal Poly CDS Rev 14 §3 (≈ 30 min); ECSS-E-ST-32C §4. Sarafin Ch. 3–5." | REWORD (mismatched — structures reading on AOCS chapter) |
| 4657–4658 | "**Prerequisites:** Sessions 2.1--2.4 and 3.1…" / "**SpaceCDF Tabs:** Dashboard (AOCS KPI), Pointing Budget, Architecture (AOCS)" | REWORD |
| 4678 | "By the end of this session, participants will be able to:" | REWORD |
| 5343–5362 | `## 6. SpaceCDF Exercise` … "2. **Pointing Budget** card on the Dashboard" … `### Worksheet 3.2 Tasks` | RESTRUCTURE |
| 5373 | `## Session Summary` | REWORD |

### Session 3.3 (5395–6055)

| Line | Snippet | Class |
|---|---|---|
| 5395 | `# Session 3.3: Communications and Link Budget Design` | REWORD |
| 5407 | "> **Expected reading before this session.** SMAD4 Ch. 12 (thermal); ECSS-E-ST-31C §5 (≈ 60 min). Gilmore Ch. 1." | REWORD (mismatched — thermal reading on comms chapter) |
| 5411–5412 | "**Prerequisites:** Sessions 2.1--3.2…" / "**SpaceCDF Tabs:** Link Budget, Spectrum Selector, Equipment Browser (Comms)" | REWORD |
| 5432 | "By the end of this session, participants will be able to:" | REWORD |
| 6011–6022 | `## 10. SpaceCDF Exercise` … "1. **Spectrum Selector** (Dashboard)…" … "5. Complete Worksheet 3.3" | RESTRUCTURE; 6022 DELETE |
| 6034 | `## Session Summary` | REWORD |

### Session 3.4 (6056–6777)

| Line | Snippet | Class |
|---|---|---|
| 6056 | `# Session 3.4: Structure, Propulsion, and Equipment Selection` | REWORD |
| 6083 | "> **Expected reading before this session.** SMAD4 Ch. 13 (comms); CCSDS PUS §1; Pratt et al. Ch. 4." | REWORD (mismatched — comms reading on structures chapter) |
| 6087–6088 | "**Prerequisites:** Sessions 2.1--3.3 (all subsystem sizing complete)" / "**SpaceCDF Tabs:** Equipment Browser, Dashboard, Trade Studies, Budget Breakdown" | REWORD |
| 6109 | "By the end of this session, participants will be able to:" | REWORD |
| 6552 | "> **Given:** Daily generation = 720 MB (from Session 3.3 data budget)…" | REWORD → "Chapter 11" |
| 6575–6578 | `## 4. Equipment Selection Exercise` — "This is the primary hands-on session for Day 4 of the design week. Teams select actual hardware components." | RESTRUCTURE; 6578 DELETE |
| 6627–6639 | `## 5. SpaceCDF Budget Closure Check` … "1. **Dashboard KPIs:** Record all margins" … "must be resolved before proceeding to integration (Week 3)" (6639) | RESTRUCTURE; 6639 REWORD |
| 6744 | "> **Parametric estimate from Session 2.4:** 3.68 kg CBE." | REWORD → "Chapter 8" |
| 6755 | `## Session Summary` | REWORD |

### Session 4.1 (6778–7213)

| Line | Snippet | Class |
|---|---|---|
| 6778 | `# Session 4.1: Equipment Selection & Bill of Materials` | REWORD |
| 6785 | "> **Expected reading before this session.** SMAD4 Ch. 14 (parts); NASA TRL definitions…" | REWORD |
| 6789 | "**Prerequisites:** Day 3 complete (subsystems sized, components identified via parametric agents)" | REWORD → "Chapters 9–12" |
| 6796 | "By the end of this session, participants will be able to:" | REWORD |
| 7156–7178 | `## 6. Equipment Selection Exercise` … "5. After all selections, review the **Budget Breakdown** on the Dashboard" (7168) … `### Worksheet 4.1 Tasks` (7178) | RESTRUCTURE |
| 7188 | `## Cited References` | REWORD → "References" (consistency) |
| 7202 | `## Session Summary` | REWORD |

### Session 4.2 (7214–7641)

| Line | Snippet | Class |
|---|---|---|
| 7214 | `# Session 4.2: Verification & Validation Matrix and Compliance` | REWORD |
| 7216 | "> **Expected reading before this session.** ECSS-E-ST-10-02C — Verification (≈ 60 min); NASA SEH §6.4." | REWORD |
| 7220 | "**Prerequisites:** Session 4.1 (equipment selected, BOM constructed)" | REWORD |
| 7227 | "By the end of this session, participants will be able to:" | REWORD |
| 7590–7606 | `## 5. SpaceCDF V&V Matrix Exercise` … "6. Discuss with your team: which tests are most critical?" (7604) … `### Worksheet 4.2 Tasks` | RESTRUCTURE |
| 7616 | `## Cited References` | REWORD |
| 7629 | `## Session Summary` | REWORD |

### Session 4.3 (7642–8018)

| Line | Snippet | Class |
|---|---|---|
| 7642 | `# Session 4.3: Risk, Interfaces & FMECA` | REWORD |
| 7649 | "> **Expected reading before this session.** ECSS-M-ST-80C — Risk management (≈ 60 min); ECSS-Q-ST-30-02C…" | REWORD |
| 7653 | "**Prerequisites:** Sessions 4.1-4.2 (equipment selected, V&V methods assigned)" | REWORD |
| 7660 | "By the end of this session, participants will be able to:" | REWORD |
| 7827 | "SpaceCDF detects many of these automatically … warning badges on the Dashboard." | KEEP/REWORD (tool note) |
| 7960–7983 | `## 5. Risk & Interface Exercise` … "2. **Risk Register Construction** (Worksheet 4.3):" (7964) … `### Worksheet 4.3 Tasks` | RESTRUCTURE |
| 7993 | `## Cited References` | REWORD |
| 8006 | `## Session Summary` | REWORD |

### Session 4.4 (8019–8464)

| Line | Snippet | Class |
|---|---|---|
| 8019 | `# Session 4.4: Cost Estimation & Design Review` | REWORD |
| 8021 | "> **Expected reading before this session.** NPR 7120.5F — WBS (≈ 30 min); SMAD4 Ch. 20 (cost)." | REWORD |
| 8025 | "**Prerequisites:** Sessions 4.1-4.3…" | REWORD |
| 8032 | "By the end of this session, participants will be able to:" | REWORD |
| 8307 | "\| 5.0 Bus Hardware \| 38 \| 36 \| See BOM from Session 4.1 \|" | REWORD → "Chapter 13" |
| 8408–8434 | `## 6. Cost & Review Exercise` … "4. On Worksheet 4.4:" (8416) … "4. Prepare a 3-minute summary of your design for peer review" (8426) … `### Worksheet 4.4 Tasks` (8428) | RESTRUCTURE; 8426 DELETE |
| 8438 | `## Cited References` | REWORD |
| 8452 | `## Session Summary` | REWORD |

### Session 5.1 (8465–8797)

| Line | Snippet | Class |
|---|---|---|
| 8465 | `# Session 5.1: Ground Segment & Operations Architecture` | REWORD |
| 8472 | "> **Expected reading before this session.** ECSS-M-ST-10C §6 — Review gates (≈ 60 min)." | REWORD (mismatched — review gates belong to 5.4) |
| 8476 | "**Prerequisites:** Week 2 complete (full design cycle through cost estimation)" | REWORD |
| 8483 | "By the end of this session, participants will be able to:" | REWORD |
| 8738–8762 | `## 5. Ground Segment Design Exercise` … "3. On Worksheet 5.1:" (8750) … `### Worksheet 5.1 Tasks` | RESTRUCTURE |
| 8772 | `## Cited References` | REWORD |
| 8786 | `## Session Summary` | REWORD |

### Session 5.2 (8798–9150)

| Line | Snippet | Class |
|---|---|---|
| 8798 | `# Session 5.2: Mission Operations Concepts` | REWORD |
| 8800 | "> **Expected reading before this session.** ITU Radio Regulations Article 21; ISED CPC-2-6-02; RSSSA…" | REWORD (mismatched — regulatory reading on ops chapter) |
| 8804 | "**Prerequisites:** Session 5.1 (ground segment architecture understood)" | REWORD |
| 8811 | "By the end of this session, participants will be able to:" | REWORD |
| 9091–9116 | `## 5. Operations Concepts Exercise` … "3. **Worksheet 5.2:**" (9104) … `### Worksheet 5.2 Tasks` | RESTRUCTURE |
| 9126 | `## Cited References` | REWORD |
| 9139 | `## Session Summary` | REWORD |

### Session 5.3 (9151–9418) — almost entirely facilitator-run

| Line | Snippet | Class |
|---|---|---|
| 9151 | `# Session 5.3: Mission Simulation Day` | REWORD → "A Mission Operations Simulation (Case Study)" |
| 9153 | "> **Expected reading before this session.** Cal Poly CDS Rev 14 §5 (Launch ICD); SMAD4 Ch. 18." | REWORD (mismatched) |
| 9157 | "**Prerequisites:** Sessions 5.1-5.2…" | REWORD |
| 9164 | "By the end of this session, participants will be able to:" | REWORD |
| 9174 | "This session is a **hands-on simulation**… The facilitator acts as the 'Universe'… procedures from Session 5.2." | REWORD (recast as a self-run tabletop exercise: "one participant acts as the Universe") |
| 9185 | "\| **Anomaly Logger** \| Documents all events… \| Worksheet 5.3 \|" | REWORD (drop worksheet) |
| 9187 | "*For smaller teams, combine roles…*" | KEEP |
| 9204 | "The facilitator narrates the simulation. Time is compressed. Each team executes their LEOP procedure." | REWORD |
| 9206 | `### Facilitator Script -- LEOP` | REWORD → "Simulation Script — LEOP" |
| 9252 | `### Facilitator Script -- Commissioning` | REWORD |
| 9262 | "Teams execute their science observation procedure from Worksheet 5.2." | REWORD |
| 9275–9277 | "The facilitator selects 2-3 anomalies…" / `### Anomaly Menu (Facilitator selects 2-3)` | REWORD |
| 9336 | "…teams complete the **Anomaly Response Form** on Worksheet 5.3:" | REWORD (inline the form) |
| 9380–9398 | `## Facilitator Notes` … "Review each team's ConOps, FDIR rules, and procedures from Session 5.2" (9384) … "Observe and note (for feedback, not formal grading):" (9398) | DELETE (or move to an instructor-guide companion) |
| 9407 | `## Session Summary` | REWORD |

### Session 5.4 (9419–9679) — mostly course admin

| Line | Snippet | Class |
|---|---|---|
| 9419 | `# Session 5.4: Final Review & Presentations` | REWORD → "Preparing and Conducting a Design Review" |
| 9421 | "> **Expected reading before this session.** SMAD4 Ch. 22 (optimization); Wertz et al. SME Ch. 9." | REWORD |
| 9425–9426 | "**Prerequisites:** All previous sessions…" / inline "**References:** …" | REWORD |
| 9432 | "By the end of this session, participants will be able to:" | REWORD |
| 9442 | "Before presenting, each team must verify…" | REWORD |
| 9453–9455 | Documentation checklist rows "Risk Register \| Worksheet 4.3", "Interface Matrix (N^2) \| Worksheet 4.3", "Cost Estimate \| Worksheet 4.4" | REWORD (→ "Chapter 15 / 16") |
| 9485 | "Each team presents a 12-minute design review followed by 5 minutes of Q&A from the peer review board." | REWORD (generic review-presentation guidance) |
| 9520–9521 | `## 3. Peer Review Process` — "Each team acts as a review board for another team." | REWORD (keep rubric and question bank as generic review-board material) |
| 9567–9588 | `## 4. Team Presentations` — "12 minutes presentation + 5 minutes Q&A per team. For 4 teams: allocate 17 min x 4 = 68 min…" / "Complete the gate criteria evaluation form on Worksheet 5.4" / "Brief applause and transition to next team" | DELETE |
| 9592–9603 | `## 5. Course Wrap-Up & Lessons Learned` — "self-assessment rubric on Worksheet 5.4, reflecting on their learning across all three weeks" (9594), "What would you do differently in Week 1?" (9603) | DELETE 9593–9594; REWORD 9596–9603 as reflective questions |
| 9605–9610 | `### Key Takeaways from the Course` — "Week 1 / Week 2 / Week 3" table | REWORD → "Key takeaways from the book" with Part names |
| 9614–9634 | ASCII V-model "Week 1-2 (left side) / Week 3 (right side)" / "*You have traversed the complete V-model…*" | REWORD |
| 9636–9642 | `### Next Steps for Participants` — "SpaceCDF access continues after the course", "Refer to the Course Textbook for session plans", "improve the course for future cohorts" | DELETE |
| 9644–9651 | `### Course Evaluation` — "Distribute the course evaluation form…" | DELETE |
| 9655 | `## Cited References` | REWORD |
| 9666–9676 | `## Session Summary` — row "Peer review \| Independent board evaluates…" (9673), "V-model \| Course traverses full V" (9675) | REWORD |

### Part 2 — Engineering-Position Reference (9680–10462)

| Line | Snippet | Class |
|---|---|---|
| 9683–9685 | "per-role background briefing for first-time CubeSat designers in a CDF. For each engineering position students might take" | REWORD |
| 9693–9695 | "read the one for your assigned role before Day 2 of Week 2 (CDF intensive Day 1)." | DELETE |
| 9697–9700 | "> **Expected reading.** Each role briefing is overnight reading the evening before students takes its CDF positions…" | DELETE (typo "students takes") |
| 9728 | "See *Course Plan* Figure 2.2." | DELETE / fix (dangling cross-ref to a document not in this book) |
| 10369 | "…this on Day 3 of Week 3 in the simulation." | REWORD → "in the simulation case study (Chapter 19)" |

### Part 3 / Appendix (10463–10833)

| Line | Snippet | Class |
|---|---|---|
| 10463 | `# Part 3 — Position Quick-Reference Cards (quick-reference cards)` — heading has no body; immediately followed by `# Appendix: Position-Specific Deep Dives` | REWORD (merge the two headings; drop redundant parenthetical) |

### Part 4 — Verification appendix (10834–11330)

Only 2 hits: 10838 "the formulas the **cohort** uses across the CDF **intensive**" and 10842 "give **students** a place to look up" → REWORD both. No "session" occurrences inside V.1–V.17; the "session" pattern does not recur here.

### Index (11331–end)

25 index entries link to `#part-1-per-session-teaching-notes` (lines 11350, 11357, 11377, 11378, 11381, 11391, 11413–11415, 11431, 11441, 11448, 11464, 11475, 11476, 11481, 11483, 11492, 11493, 11499, 11500, …). That anchor does not exist in the book (Part 1's heading is "Part 1 — Course Lectures"). The index never points into a Part 1 chapter — it only resolves to Part 2 roles, Part 4 V-sections and "how-to-use-this-book". **REWORD/regenerate** the index after re-titling.

### Repeated boilerplate (counts)

- "By the end of this session, participants will be able to:" — 20× (one per chapter).
- "> **Expected reading before this session.**" — 20× (+1 in front matter, +1 in Part 2).
- "**Prerequisites:**" — 20×.
- `## Session Summary` — 20×.
- "Complete Worksheet N.N" / `### Worksheet N.N Tasks` — 19 occurrences across 1.1, 1.4, 2.1–2.4, 3.1–3.4, 4.1–4.4, 5.1, 5.2, 5.3, 5.4.
- "SpaceCDF Exercise"/"Tool Exercise"/"… Exercise" `##` headings — 18 (every chapter except 1.2, 1.3).

---

## B. Chapter map

Equations column = lines containing inline `$…$` or `$$` blocks (approximate; currency `$` false positives excluded). Figures = `![…]` + inline `<svg>` inside the chapter's line range (chapter-top figure blocks counted where they sit, even if misplaced — see D).

| # | Current title | Lines | Proposed OER chapter | Exercise sections | LO | Summary | Refs | Figs | Eqns |
|---|---|---|---|---|---|---|---|---|---|
| 1.1 | Introduction to Space Mission Design | 269–834 | **1. Concurrent Design and the Systems Engineering Framework** | §7 Tool Exercise; inline Exercise ×3, Discussion ×3 | Y (294) | Y "6. Session Summary" (773) | Y "References" (825) + inline list (286) | 4 (2 png, 2 svg) | 3 |
| 1.2 | The Canadian Space Ecosystem & Regulatory Environment | 835–1232 | **2. The Canadian Space Ecosystem and Regulatory Environment** | none (Discussion ×3) | Y | Y | Y "References" | 1 | ~10 |
| 1.3 | International Standards for Space Systems | 1233–1722 | **3. International Standards for Space Systems** | inline Exercise (1690) | Y | Y | Y "References" | 2 | ~33 |
| 1.4 | Mission Needs, Stakeholder Analysis & Trade Studies | 1723–2344 | **4. Mission Needs, Stakeholders, Trade Studies and Concept of Operations** | §11 ConOps Tool Exercise; inline Exercise ×5 | Y | Y | Y "References" | 2 | ~62 |
| 2.1 | The System-V and Requirements Engineering | 2345–2742 | **5. Requirements Engineering** | §7 SpaceCDF Exercise | Y | Y | Y "References" (before LOs, 2356) | 1 (svg) | 2 |
| 2.2 | Functional Decomposition and Allocation | 2743–3065 | **6. Functional Decomposition and Allocation** | §5 Function Tree Exercise | Y | Y | Y (before LOs) | 2 | 0 |
| 2.3 | Orbit Selection and Mission Architecture | 3066–3425 | **7. Orbit Selection and the Space Environment** | §7 Orbit Trade Exercise | Y | Y | Y (before LOs) | 2 | ~74 (1 $$) |
| 2.4 | Mission Architecture -- Segments, Interfaces, and Budgets | 3426–3857 | **8. Mission Architecture: Segments, Interfaces and Engineering Budgets** | §5 SpaceCDF Exercise | Y | Y | Y (before LOs) | 2 (svg) | ~12 |
| 3.1 | Power System and Thermal Control Design | 3858–4645 | **9. Electrical Power and Thermal Control** | §6 SpaceCDF Exercise + Worksheet 3.1 Tasks | Y | Y | Y (before LOs) | 4 | ~290 (5 $$) |
| 3.2 | Attitude and Orbit Control System (AOCS) | 4646–5394 | **10. Attitude and Orbit Control** | §6 SpaceCDF Exercise + Worksheet 3.2 Tasks | Y | Y | Y (before LOs) | 1 | ~245 (15 $$) |
| 3.3 | Communications and Link Budget Design | 5395–6055 | **11. Communications and Link Budgets** | §10 SpaceCDF Exercise | Y | Y | Y (before LOs) | 3 | ~180 (3 $$) |
| 3.4 | Structure, Propulsion, and Equipment Selection | 6056–6777 | **12. Structures, Propulsion and On-Board Data Handling** | §4 Equipment Selection Exercise; §5 Budget Closure Check | Y | Y | Y (before LOs) | 5 | ~165 |
| 4.1 | Equipment Selection & Bill of Materials | 6778–7213 | **13. Equipment Selection and Bill of Materials** | §6 Equipment Selection Exercise + Worksheet 4.1 | Y | Y | Y "Cited References" | 1 | 0 |
| 4.2 | Verification & Validation Matrix and Compliance | 7214–7641 | **14. Verification and Validation** | §5 V&V Matrix Exercise + Worksheet 4.2 | Y | Y | Y "Cited References" | 0 | 0 |
| 4.3 | Risk, Interfaces & FMECA | 7642–8018 | **15. Risk Management, Interface Control and FMECA** | §5 Risk & Interface Exercise + Worksheet 4.3 | Y | Y | Y "Cited References" | 1 | 0 |
| 4.4 | Cost Estimation & Design Review | 8019–8464 | **16. Cost Estimation and Design Reviews** | §6 Cost & Review Exercise + Worksheet 4.4 | Y | Y | Y "Cited References" | 0 | 0 |
| 5.1 | Ground Segment & Operations Architecture | 8465–8797 | **17. Ground Segment Architecture** | §5 Ground Segment Design Exercise + Worksheet 5.1 | Y | Y | Y "Cited References" | 1 | 0 |
| 5.2 | Mission Operations Concepts | 8798–9150 | **18. Mission Operations and FDIR** | §5 Operations Concepts Exercise + Worksheet 5.2 | Y | Y | Y "Cited References" | 0 | 0 |
| 5.3 | Mission Simulation Day | 9151–9418 | **19. Case Study: A Mission Operations Simulation** (whole chapter is an exercise) | §1–§5 all; `## Facilitator Notes` | Y | Y | **N** (no references section) | 0 | 0 |
| 5.4 | Final Review & Presentations | 9419–9679 | **20. Preparing and Conducting a Design Review** (or fold into Ch. 16 and drop) | §4 Team Presentations; §5 Wrap-Up | Y | Y | Y "Cited References" + inline (9426) | 0 | 0 |

Notes:
- Chapters 2.1–3.4 put `## References` *before* `## Learning Objectives`; 1.1–1.4 put `## References` at the end; 4.1–5.4 use `## Cited References` at the end. 1.1 and 5.4 additionally carry an inline `**References:**` list in the preamble.
- Chapters 4.1–5.4 contain **no LaTeX at all**; their formulas (CER `Cost = a·M^b`, reliability `R = …`, learning-curve, P80) are plain text in tables — candidates for proper equation typesetting.
- 1.2–1.4 use `## Part 1/2/3` with continuously numbered `###` subsections (e.g. "### 8. Mission Architecture", "### 11. ConOps Tool Exercise"); all other chapters use numbered `##` sections. 2.2 and 3.4 have an unnumbered `## Worked Example` section; 2.1 has `## Key Equations Reference`; 1.1's `### 1U Worked Example: UniSat-1` (786) sits *after* the Session Summary.

---

## C. Duplication candidates

### C1. System-V model — 1.1 §2 (366–509) vs 2.1 §1 (2379–2437)
- 1.1 §2.1 (369): "The 'Vee' (V) model is the foundational framework for systems engineering. It appears in NASA SEH Section 2.3…"; full inline SVG (379–461, 'Segoe UI' style); left/right side tables (467–485); horizontal traceability + T_c equation (487–499).
- 2.1 §1 (2380): "The **System-V** (or 'Vee model') is the canonical systems engineering lifecycle. It connects the decomposition of requirements on the left branch to the integration and verification on the right…"; second inline SVG (2386–2411, different style); phase-mapping table (2417–2423); Planet SuperDove example (2425–2436).
- Also a *third* V: `fig_system_v.png` at 2745 (top of 2.2, "with course touchpoints") and a fourth ASCII V in 5.4 (9614–9632).
- **Recommendation:** Canonical = 1.1 §2 (introduces the model) but *move the SuperDove example and the phase-mapping table there*. In 2.1 §1 keep one paragraph: "Recall the V-model (Figure 1.x)… this chapter works the top of the left branch" and delete the second SVG. Use `fig_system_v.png` as the single V figure in Ch. 1; delete both inline SVGs. Drop the 5.4 ASCII V or keep as a one-line recap.

### C2. N² interface matrix — 2.4 §3 (3572–3655) vs 4.3 §3 (7772–7839)
- 2.4 §3 (3579): "The N² matrix is a standard systems engineering tool for mapping all subsystem interactions: diagonal cells… off-diagonal… upper triangle… lower triangle"; interface-type table M/E/T/D/R/O (3590–3597); 13-row concern table; severity classification; interface requirement examples.
- 4.3 §3 (7773): "The N^2 matrix is the standard systems engineering tool for identifying and managing interfaces between subsystems"; ASCII 6×6 example (7787–7804); colour-coded type table (7810–7817) that *conflicts* with 2.4's letter codes (Software/purple vs Optical/O); conflict detection bullets; I2C-vs-RS-422 worked example.
- `fig_n2_matrix.png` sits at 3068 (top of 2.3), used by neither section.
- **Recommendation:** Canonical = 2.4 §3 (architecture chapter; introduces the concept). Move the ASCII 6×6 matrix (or better, `fig_n2_matrix.png`) and the I2C/RS-422 worked example into 2.4. Reduce 4.3 §3 to "Interface conflicts as risks" (~15 lines): cross-ref "see Chapter 8 §3 for N² construction", keep only the conflict-detection bullets and the link to the risk register. Unify the interface-type coding to one table.

### C3. ConOps — 1.4 Part 3 (2136–2320) vs 5.2 §1 (8820–8889)
- 1.4 §9.1 (2179): LEOP/Commissioning/Nominal/Extended/Disposal phase table; §9.2 (2191): operational modes table "Safe … ~1--2 W; Science/Imaging … ~6 W (3U typical)"; §9.3 power budget equations; §10 data flow pipeline.
- 5.2 §1 (8827): ConOps document structure (8 items); operational modes table (8842–8850) "Safe … 5-10 W; Science … 25-40 W" — **numerically inconsistent** with 1.4 (different spacecraft class, unstated); mode-transition state machine (8854–8877); PROBA-2 example.
- Also overlaps: 1.4 §8 "Three Segments" (2140–2148) duplicates 2.4 §1 "Mission Segment Decomposition" (3460–3508); 1.4 §9.3 equations duplicate 3.1 §2–§3; 1.4 §10.2 data budget duplicates 3.3 §9 (5967–6009).
- **Recommendation:** Split responsibilities: Ch. 4 (1.4) keeps *what a ConOps is* — phases, segments at one-paragraph level, the mode concept with the 3U table; Ch. 18 (5.2) owns the *operational* detail — ConOps document structure, state machine, FDIR, and a single reconciled mode table (state the spacecraft class). Delete 1.4 §8.1–8.2 (point to Ch. 8 §1), delete 1.4 §9.3 equations (point to Ch. 9), delete 1.4 §10.2 (point to Ch. 11 §9). Use `fig_conops_timeline.png` once, in Ch. 4.

### C4. Lifecycle / review gates — 1.1 §4 (579–731) vs 4.4 §5 (8346–8405) vs 5.4 §1–§3 (9441–9563) (+ front matter 234–248)
- 1.1 §4.5 (718–726): "MCR | Mission Concept Review | Is the mission need justified?… SRR … SDR … PDR … CDR … TRR … FRR" with required evidence.
- 4.4 §5 (8354–8362): "MCR | Pre-A -> A | Is the mission need justified? … SRR … PDR … CDR … TRR … QR … FRR" — same questions, **omits SDR** (contradicting line 108 which claims the SDR gate is inserted everywhere), adds QR; then SRR/PDR gate-criteria tables (8364–8390) and "Presentation Skills" (8392–8404).
- 5.4 §2 (9499–9516) repeats the presentation do/don't list almost verbatim ("Lead with conclusions: 'Our mass budget closes with 22% margin'" vs 8395 "Lead with the conclusion ('Mass budget closes with 22% margin')"); 5.4 §3 gate-criteria rubric (9537–9548) overlaps the PDR criteria table at 8379–8390.
- Front matter 242–248 has a fourth gate table (MCR/SRR/SDR/PDR/CDR with exported bundle).
- **Recommendation:** Canonical for *what the gates are* = 1.1 §4 (add QR there). Canonical for *gate criteria + presenting at a review* = Ch. 16 (4.4 §5). Delete the 4.4 review-sequence table (cross-ref Ch. 1 §4). Collapse 5.4 into Ch. 16 as a final section "Running a review board" (roles table 9525–9531 and question bank 9552–9563 are the only unique content); delete the duplicated do/don't list. Front-matter table → move to the tool appendix.

### C5. Requirements / traceability — 2.1 (2440–2625) vs Part 2 "Systems Engineer" (9704–9770) vs Appendix A (10474–10497)
- 2.1 §4 (2529): "Requirements exist at multiple levels, each decomposed from the level above. Every requirement must trace bidirectionally." (hierarchy, RVM, coverage metric at 2724).
- Part 2 SE (9710–9721): "Decisions you own: Margin policy… Budget closure… Conflict resolution… Gate-review readiness"; ECSS margin-by-phase table (9739–9744) — this is really *budget/margin* content, duplicating 2.4 §4 (3658–3750, margin formula at 3668) rather than requirements.
- Appendix A (10485): "Own the requirements baseline and traceability matrix"; "Apply ECSS margin policy by project phase (44% Phase A -> 13% Phase C/D)" — a third statement of the margin schedule.
- **Recommendation:** Requirements content is only in 2.1 (fine). The *margin policy* is stated three times (2.4 §4, Part 2 SE, Appendix A) with slightly different numbers (Appendix A says "13% Phase C/D", Part 2 table says C +13 %, D +5 %). Make 2.4 §4 canonical with one ECSS-E-ST-10-02-style table; Part 2 SE keeps the "decisions you own / pitfalls" voice and cross-refs it; Appendix A becomes a 10-line card or is deleted (see C8).

### C6. Link budget — 3.3 §1–§2, §8 (5447–5590, 5854–5965) vs Part 2 "Communications Engineer" (10246–10319) vs Part 4 V.6–V.8 (11011–11102)
- 3.3 (5549): `C/N_0 = EIRP − FSPL − L_atm − L_point − L_pol + G/T − k (dBHz)`; FSPL (5530, 5668); margin (5557); worked examples (5854–5965).
- Part 2 CO (10280): `C/N_0 = EIRP − L_path − L_atm − L_point + G/T − k` (drops L_pol); FSPL (10271); figures CO.1–CO.4 (= the same four PNGs that also sit at the top of 3.4, lines 6058–6078).
- Part 4 V.6 (11020–11024) re-derives FSPL from the Friis equation; V.7 (11045–11057) full link algebra; V.8 BER formulas — plus the same three PNGs a third time (11028, 11063, 11090).
- Also 1.2 (1120–1132) has a mini link-budget aside (`P_r = P_t + G_t + G_r − L_fs − L_atm − L_misc`) in the regulatory chapter.
- **Recommendation:** Canonical teaching = Ch. 11 (3.3). Part 4 V.6–V.8 keep *derivations only* (Friis → FSPL, BER integrals) and cross-ref Ch. 11 for use; Part 2 CO keeps decisions/pitfalls and cross-refs "Ch. 11 §2, Eq. 11.x" rather than restating equations. Each PNG should appear once in Part 1 (move `fig_link_budget`, `fig_fspl`, `fig_antenna_pattern`, `fig_signal_noise` from the top of 3.4 into 3.3 §2/§4/§3/§6) and be referenced by figure number elsewhere. Delete the 1.2 link aside (point to Ch. 11).

### C7. Power sizing — 3.1 §2–§3 (4040–4225) vs Part 2 "Power Engineer" (9952–10025) vs Appendix D (10547–10568) vs Part 4 V.11–V.12 (11171–11228) vs 1.4 §9.3 (2211–2231)
- 3.1 §2 (4052): `P_SA,EOL = P_peak,sunlight + P_eclipse·t_eclipse/(t_sunlight·η_path,eclipse)`; BOL via `L_d·L_T`; `A_SA = P_BOL/(η_cell·S·cosθ·f_pack·f_cover)` (4070); battery `E_bat = P_ecl·t_ecl/(DOD·η_dis)` (4175).
- Part 2 PW (9977): `A_SA = P_avg·(1 + f_eclipse/(f_sun·η_dis)) / (S₀·η_cell·cosβ·(1−D_deg))` — different formulation and symbols (β vs θ, D_deg vs L_d·L_T); battery 9990.
- Appendix D (10562–10565): ASCII versions "P_SA = P_peak_sun + (P_eclipse × t_ecl)/(t_sun × eta_charge)", "A_SA = P_BOL/(eta_cell × S × cos(theta) × eta_pack)".
- Part 4 V.11 (11177–11184) derives the Part 2 form; V.12 battery.
- 1.4 §9.3 (2221, 2227): a fourth, simplified pair `P_SA = P_sunlight + P_eclipse·t_eclipse/(t_sunlight·η_charge)`, `E_battery = …`.
- **Recommendation:** Canonical = Ch. 9 (3.1) — but adopt ONE notation set across the book (suggest Ch. 9's with θ→β clarified). Part 4 V.11 should derive exactly Ch. 9's equation and note the equivalence to the f_eclipse/f_sun form. Delete the equations from 1.4 §9.3 and Appendix D; Part 2 PW cross-refs "Ch. 9 Eq. (9.x)". The three power PNGs are at the top of 3.1 (3860–3870) and again in Part 2 (9982–10002) and Part 4 (11188, 11221): keep in Ch. 9 §2/§3 with figure numbers.

### C8. Three layers of position material — Part 2 (9680–10462, 13 roles, ~780 lines) vs Part 3 heading (10463, **empty**) vs "Appendix: Position-Specific Deep Dives" (10466–10833, 16 cards A–P, ~370 lines) vs 1.1 §5.1 table (737–755, 15 positions)
- Part 2 "Systems Engineer" (9706): "You hold the budgets, the gate, and the authority to call a trade." / Appendix A (10476): "**Responsibility:** Overall system architecture, budget management, cross-domain conflict resolution." / 1.1 table (741): "Systems Engineer | Overall architecture, budgets, margins, conflict resolution | Mass margin, power margin…".
- Role lists disagree: 1.1 has 15 positions (incl. Compliance, User Rep, Mission Ops, Ground Segment, Software); Part 2 has 13 (adds "Cost & Schedule", "OBDH / Software", "Operations Engineer"; lacks Compliance, User Rep, Project Manager); Appendix has 16 (adds Project Manager, User Representative, Compliance). "Payload Engineer" (Part 2) vs "Payload Lead" (Appendix C, 1.1).
- The Appendix is titled "Deep Dives" but is the *short* form; Part 2 is the long form; front matter (29–30) calls Part 3 "short-form per-position cards". The Appendix cards contain mojibake (`?V`, `2pi?(`, `1.22lambdah/D`, `?(? theta?^2)` at 10481, 10514–10517, 10538, 10586, 10643–10656, 10679).
- **Recommendation:** Keep **one** layer: Part 2 (the briefings — real pedagogical content with figures). Delete the empty Part 3 heading. Delete the Appendix A–P cards entirely *after* harvesting the three roles Part 2 lacks (Project Manager, User Representative, Compliance/Regulatory) into short Part 2 entries. Reconcile the position list to the 15 used by 1.1 §5.1 and the tool, and cross-ref 1.1 §5 → Part 2 ("full briefing for each position in Part 2").

### C9. Front matter — "Acknowledgement — Generative AI (AIG)" (53–72) vs "How This Textbook Was Generated" (75–193)
- 53–62: "This textbook was produced with the assistance of generative AI… generated by the SpaceCDF backend (Python · matplotlib · python-docx · WeasyPrint) guided by ECSS, NASA SEH and SMAD-4… The chapter *How This Textbook Was Generated* describes the pipeline in detail."
- 75–86 repeats the same pipeline description ("Python toolchain — reorientation scripts, matplotlib figure generators, python-docx and WeasyPrint renderers"), and §"Validation and citation" (168–177) repeats the AIG-badge statement ("The AIG badge (see the *Acknowledgement* section) is attached to every exported document").
- **Recommendation:** Merge into a single ~40-line "About this book" page: licence (CC BY), AIG attribution (keep the Peters 2023 citation), one paragraph on procedural figures/reproducibility, one on numerical examples computed with SpaceCDF. Drop the build-script internals (`reorient_books.py`, `build_course_pdfs.sh`, "forty-odd Markdown chapter files", uOttawa HTML scaffold), the "Voice reorientation" section, and "What this means for learners".

### C10. Other duplications noticed (not requested but relevant)
- **Mission segments:** 1.4 §8.1 (2140–2148) vs 2.4 §1 (3460–3508, with SVG). Keep 2.4.
- **Data budget:** 1.4 §10.2 (2253–2268) vs 3.3 §9 (5967–6009) vs 3.4 §3 storage sizing (6536–6558) vs Part 4 V.15 (11264–11282). Keep 3.3 §9 + V.15 derivation.
- **Orbital lifetime rule-of-thumb** `τ ≈ (h−200)/30 · (m/A)/50`: 1.3 (1615) and Part 2 MA (9843). Keep 1.3 (or move to 2.3) and cross-ref.
- **Margin of safety** `MoS = σ_allow/(FoS·σ_applied) − 1`: 1.3 (1475), 3.4 (6240), Part 2 ST (10172), V.13 (11231). Keep 3.4 + V.13.
- **Eclipse fraction**: 2.3 (3159, β-free form `arccos(√(a²−R²)/a)`), Part 2 MA (9832, β form), V.5 (10991, β form), Appendix B (10515, ASCII). Keep 2.3 (upgrade to β form) + V.5.
- **Tsiolkovsky**: 3.4 (6334), Part 2 PR (10222), Appendix H (10655), V.3 (10915). Keep 3.4 + V.3.
- **TRL**: 4.1 §2 (6861–6909) vs 1.3 (~1400s TRL mentions in ECSS context) — minor.
- **UniSat-1 worked example** appears 11× (786, 2285, 2655, 3339, 3755, 4483, 5284, 5894, 6653, 6985, 8293): this is deliberate (running example) and should stay, but the intro paragraph "Throughout this course, we use a second running example…" (788) should appear once.

---

## D. Figure inventory

All 29 `fig_*.png` referenced files **exist** (verified by Glob). Two PNGs in the directory are referenced nowhere: **`fig_ground_track.png`** and **`fig_hohmann.png`** (both have generator scripts). The 11 inline `<svg>` blocks are mirrored by 11 rasterised files in `_inline/svg_*.png` (produced by the PDF builder, `docs/build_pdfs_fpdf.py`, which titles them "Figure: Diagram"/first `<text>`).

Path inconsistency: Part 1 and front matter use `../assets/figures/…`; Part 2 and Part 4 use `../../assets/figures/…`. Only one can be right relative to this file (`docs/course/`): `../assets/figures/` is correct; the 31 Part 2/Part 4 references are **broken relative links** unless the build rewrites them.

Flag column: **C** = caption references Day/session/students/course; **M** = figure is placed in the wrong chapter; **U** = unreferenced.

### D1. Raster figures (`![…]`)

| Line | Path | Caption (alt text / italic caption) | Chapter | Exists | Flag |
|---|---|---|---|---|---|
| 44 | fig_lifecycle.png | "Lifecycle phases — what each Day touches" / "*The lifecycle students lives.*" | Front matter | Y | **C** (typo too) |
| 48 | fig_seh_processes.png | "NASA SEH 17 common technical processes" / "*…each session names which process(es) it sits inside.*" | Front matter | Y | **C** |
| 271 | fig_lifecycle.png | "Lifecycle phases and review gates." | 1.1 | Y | dup of 44 |
| 276 | fig_seh_processes.png | "NASA SEH 17 processes pyramid." | 1.1 | Y | dup of 48 |
| 837 | fig_canadian_sector.png | "Representative stakeholder map for Canadian missions." | 1.2 | Y | |
| 1235 | fig_orbital_lifetime.png | "Orbital lifetime vs altitude with FCC/IADC limits." | 1.3 (top; relates to Part 2 §debris, 1600s) | Y | |
| 1725 | fig_conops_timeline.png | "Mission operations timeline (LEOP through disposal)." | 1.4 (top; relates to Part 3 §9, 2176) | Y | |
| 2745 | fig_system_v.png | "System-V model with course touchpoints." | 2.2 top | Y | **C, M** → belongs 1.1 §2 / 2.1 §1 |
| 3068 | fig_n2_matrix.png | "N² interface matrix for a 6U CubeSat." | 2.3 top | Y | **M** → belongs 2.4 §3 |
| 3860 | fig_power_modes.png | "Power generation and stacked load profile." | 3.1 top | Y | (→ 3.1 §1/§2) |
| 3865 | fig_solar_array.png | "Solar-array sizing nomograph." | 3.1 top | Y | (→ 3.1 §2) |
| 3870 | fig_battery_dod.png | "Battery cycle life vs DoD." | 3.1 top | Y | (→ 3.1 §3) |
| 4648 | fig_mass_budget.png | "Mass distribution and ECSS margin policy." | 3.2 top | Y | **M** → belongs 2.4 §4 |
| 5397 | fig_beta_eclipse.png | "β-angle envelope and eclipse fraction analytics." | 3.3 top | Y | **M** → belongs 2.3 §1 or 3.1 §4 |
| 5402 | fig_thermal_balance.png | "Radiative thermal equilibrium vs α/ε." | 3.3 top | Y | **M** → belongs 3.1 §4 |
| 6058 | fig_link_budget.png | "S-band downlink link-budget waterfall." | 3.4 top | Y | **M** → 3.3 §2/§8 |
| 6063 | fig_pass_geometry.png | "Iqaluit S-band pass geometry." | 3.4 top | Y | **M** → 3.3 §7 or 5.1 §2 |
| 6068 | fig_fspl.png | "Free-space path loss vs slant range across bands." | 3.4 top | Y | **M** → 3.3 §4 |
| 6073 | fig_antenna_pattern.png | "Antenna patterns: high-gain dish vs patch." | 3.4 top | Y | **M** → 3.3 §3 |
| 6078 | fig_signal_noise.png | "Eb/N0 vs BER for common modulations." | 3.4 top | Y | **M** → 3.3 §6 |
| 6780 | fig_trl.png | "Technology Readiness Level ladder." | 4.1 top | Y | (→ 4.1 §2) |
| 7644 | fig_risk_matrix.png | "5×5 risk matrix (ECSS-M-ST-80C)." | 4.3 top | Y | (→ 4.3 §2) |
| 8467 | fig_lifecycle.png | "Gate sequence at a glance." | 5.1 top | Y | **M** → 4.4 §5 (3rd use of this PNG) |
| 9746 | fig_mass_budget.png | "Figure SE.1 — Mass distribution and the ECSS margin schedule…" | Part 2 SE | Y | `../../` path |
| 9812 | fig_kepler_proof.png | "Kepler's Third Law verified against known orbits" | Part 2 MA | Y | `../../` |
| 9823 | fig_j2_nodal.png | "J2 nodal regression vs inclination at several altitudes" | Part 2 MA | Y | `../../` |
| 9836 | fig_beta_eclipse.png | "β-angle envelope and eclipse fraction analytics" | Part 2 MA | Y | `../../` |
| 9845 | fig_orbital_lifetime.png | "Orbital lifetime vs altitude — FCC 5-yr and IADC 25-yr lines" | Part 2 MA | Y | `../../` |
| 9912 | fig_gsd.png | "GSD vs aperture diameter — diffraction and pixel limits" | Part 2 PL | Y | `../../` (only Part 2/4 — never in Part 1) |
| 9936 | fig_data_volume.png | "Data volume vs band — capacity check" | Part 2 PL | Y | `../../` (never in Part 1) |
| 9982 | fig_solar_array.png | "Figure PW.1 — Solar-array nomograph…" | Part 2 PW | Y | `../../` |
| 9992 | fig_battery_dod.png | "Figure PW.2 — Battery cycle life vs DoD…" | Part 2 PW | Y | `../../` |
| 10002 | fig_power_modes.png | "Figure PW.3 — Generation (top) and stacked load profile (bottom)…" | Part 2 PW | Y | `../../` |
| 10058 | fig_pointing_tree.png | "Pointing-error budget waterfall" | Part 2 AO | Y | `../../` (never in Part 1 — should be in 3.2 §4) |
| 10068 | fig_rw_momentum.png | "Reaction-wheel momentum vs disturbance" | Part 2 AO | Y | `../../` (never in Part 1 — should be in 3.2 §5) |
| 10122 | fig_thermal_balance.png | "Radiative thermal equilibrium vs α/ε" | Part 2 TH | Y | `../../` |
| 10224 | fig_tsiolkovsky.png | "Tsiolkovsky — Δv vs mass ratio for selected Isp" | Part 2 PR | Y | `../../` (never in Part 1 — should be in 3.4 §2) |
| 10273 | fig_fspl.png | "Figure CO.1 — FSPL across bands…" | Part 2 CO | Y | `../../` |
| 10284 | fig_link_budget.png | "Figure CO.2 — A canonical S-band waterfall…" | Part 2 CO | Y | `../../` |
| 10292 | fig_signal_noise.png | "Figure CO.3 — Eb/N₀ vs BER…" | Part 2 CO | Y | `../../` |
| 10299 | fig_antenna_pattern.png | "Figure CO.4 — High-gain dish vs S-band patch…" | Part 2 CO | Y | `../../` |
| 10888 | fig_kepler_proof.png | "Figure V.1 — The analytical curve overplotted with known orbits…" | Part 4 V.2 | Y | `../../` |
| 10921 | fig_tsiolkovsky.png | "Tsiolkovsky — Δv vs mass ratio…" | Part 4 V.3 | Y | `../../` |
| 10964 | fig_j2_nodal.png | "J2 nodal regression…" | Part 4 V.4 | Y | `../../` |
| 10997 | fig_beta_eclipse.png | "β-angle envelope and eclipse fraction analytics" | Part 4 V.5 | Y | `../../` |
| 11028 | fig_fspl.png | "Figure V.5 — FSPL vs slant range for five frequency bands." | Part 4 V.6 | Y | `../../`; numbered V.5 inside section V.6 |
| 11063 | fig_link_budget.png | "Link-budget waterfall — S-band downlink" | Part 4 V.7 | Y | `../../` |
| 11090 | fig_signal_noise.png | "Eb/N0 vs BER curves" | Part 4 V.8 | Y | `../../` |
| 11128 | fig_gsd.png | "GSD vs aperture — diffraction and pixel limits" | Part 4 V.9 | Y | `../../` |
| 11155 | fig_thermal_balance.png | "Radiative thermal equilibrium vs α/ε" | Part 4 V.10 | Y | `../../` |
| 11188 | fig_solar_array.png | "Solar-array nomograph" | Part 4 V.11 | Y | `../../` |
| 11221 | fig_battery_dod.png | "Battery cycle life vs DoD" | Part 4 V.12 | Y | `../../` |
| 11256 | fig_rw_momentum.png | "Reaction-wheel momentum and disturbance torques" | Part 4 V.14 | Y | `../../` |
| 11274 | fig_data_volume.png | "Daily downlink capacity by band" | Part 4 V.15 | Y | `../../` |
| — | fig_ground_track.png | — | — | Y | **U** (candidate for 2.3 §4 Ground Coverage) |
| — | fig_hohmann.png | — | — | Y | **U** (candidate for 2.3 §5 Hohmann/Deorbit) |

Reuse summary: 54 `![…]` references to 27 distinct PNGs. Used 3×: fig_lifecycle (44/271/8467), fig_link_budget, fig_fspl, fig_signal_noise, fig_solar_array, fig_battery_dod, fig_beta_eclipse, fig_thermal_balance. Used 2×: seh_processes, mass_budget, power_modes, antenna_pattern, kepler_proof, j2_nodal, orbital_lifetime, gsd, data_volume, rw_momentum, tsiolkovsky. Used 1×: canadian_sector, conops_timeline, system_v, n2_matrix, pass_geometry, trl, risk_matrix, pointing_tree.

Caption style: Part 1 captions are unnumbered italics repeating the alt text; Part 2 uses "Figure SE.1/PW.1/CO.1"; Part 4 uses "Figure V.n" (and V.5 is mis-numbered inside §V.6). OER needs one numbering scheme (Figure 9.3 etc.).

### D2. Inline SVG blocks

| Line | Chapter / section | Content (first `<text>` title) | Style family | Notes |
|---|---|---|---|---|
| 379 | 1.1 §2.2 | V-model ("DECOMPOSITION / INTEGRATION") | A ('Segoe UI', #fafafa bg, border) | duplicates fig_system_v.png |
| 588 | 1.1 §4.2 | "NASA Space Flight Project Lifecycle (NPR 7120.5F)" with gate diamonds + "SpaceCDF Scope (Pre-A through C)" | A | duplicates fig_lifecycle.png |
| 1305 | 1.3 Part 1 | ECSS standards tree (800×450) | A | |
| 1919 | 1.4 Part 1 §MoE/MoP/TPM | Needs→MoE→MoP→TPM hierarchy (700×520) | A | |
| 2386 | 2.1 §1 | V-model, second rendering (800×500) | B (sans-serif, no bg) | duplicates 379 and fig_system_v.png |
| 2792 | 2.2 §1 | Function tree (800×360) | B | |
| 3123 | 2.3 §1 | Keplerian elements sketch (500×400) | B | |
| 3465 | 2.4 §1 | Three-segment architecture (800×300) | B | |
| 3513 | 2.4 §2 | System block diagram (800×500) | B | |
| 3921 | 3.1 §1 | EPS architecture block diagram (800×300) | B | |
| 5456 | 3.3 §1 | Link chain TX→RX (800×200) | B | |

Also 560–569 (1.1 §3.5): an HTML-comment placeholder `<!-- SVG DIAGRAM: SE Engine Recursion -->` followed by an ASCII block — a figure that was specified but never drawn. ASCII art stands in for figures at 2533–2560 (requirement hierarchy), 2238–2240 (data pipeline), 7787–7804 (N²), 8854–8877 (mode state machine), 9614–9632 (V-model).

### D3. Generator scripts

Location: `/Users/FNewland/SpaceCDF-arcadia/docs/assets/figures/`. One standalone script per figure (no functions — module-level code ending in `fig.savefig(...)`), all importing the palette from `uottawa_brand.py` (sets `savefig.dpi: 200`, `bbox: tight`, white facecolor). No orchestrator in `scripts/` regenerates them (`scripts/reorient_books.py` only mentions the directory in prose). **Every script hard-codes an output path from a dead sandbox** — `fig.savefig("/sessions/serene-eager-noether/mnt/docs/assets/figures/<name>.png")` — so none is reproducible as-is; they need a `Path(__file__).parent` output and a `make_all.py` driver.

| Script | Produces | savefig line |
|---|---|---|
| fig_antenna_pattern.py | fig_antenna_pattern.png | 55 |
| fig_battery_dod.py | fig_battery_dod.png | 50 |
| fig_beta_eclipse.py | fig_beta_eclipse.png | 82 |
| fig_canadian_sector.py | fig_canadian_sector.png | 77 |
| fig_conops_timeline.py | fig_conops_timeline.png | 55 |
| fig_data_volume.py | fig_data_volume.png | 58 |
| fig_fspl.py | fig_fspl.png | 41 |
| fig_ground_track.py | fig_ground_track.png (unused) | 93 |
| fig_gsd.py | fig_gsd.png | 47 |
| fig_hohmann.py | fig_hohmann.png (unused) | 75 |
| fig_j2_nodal.py | fig_j2_nodal.png | 51 |
| fig_kepler_proof.py | fig_kepler_proof.png | 43 |
| fig_lifecycle.py | fig_lifecycle.png | 60 |
| fig_link_budget.py | fig_link_budget.png | 66 |
| fig_mass_budget.py | fig_mass_budget.png | 59 |
| fig_n2_matrix.py | fig_n2_matrix.png | 101 |
| fig_orbital_lifetime.py | fig_orbital_lifetime.png | 39 |
| fig_pass_geometry.py | fig_pass_geometry.png | 52 |
| fig_pointing_tree.py | fig_pointing_tree.png | 64 |
| fig_power_modes.py | fig_power_modes.png | 58 |
| fig_risk_matrix.py | fig_risk_matrix.png | 65 |
| fig_rw_momentum.py | fig_rw_momentum.png | 61 |
| fig_seh_processes.py | fig_seh_processes.png | 82 |
| fig_signal_noise.py | fig_signal_noise.png | 48 |
| fig_solar_array.py | fig_solar_array.png | 47 |
| fig_system_v.py | fig_system_v.png | 82 |
| fig_thermal_balance.py | fig_thermal_balance.png | 52 |
| fig_trl.py | fig_trl.png | 46 |
| fig_tsiolkovsky.py | fig_tsiolkovsky.png | 38 |
| uottawa_brand.py | (palette/rcParams only; brand name needs neutralising for OER) | — |

Related: `docs/_render_math.py` renders `$…$` to `_math/m_*.svg` (hundreds of files; build artefacts, not content). `docs/build_pdfs_fpdf.py` rasterises inline SVGs to `_inline/`. `packages/spacecdf-agents/src/spacecdf_agents/exporters/docs/figures.py` is the tool's exporter styling (not a textbook generator).

---

## E. Under-illustrated sections (≥60 lines of prose, no figure in-section)

Ranked by how much a diagram would help. "Fig exists" = a PNG already exists but is placed elsewhere/unused.

| Rank | Section | Lines | Proposed figure (what it shows — type) |
|---|---|---|---|
| 1 | 3.1 §4 Thermal Control System | 4227–4562 (336) | Thermal energy balance on a CubeSat face: solar, albedo, Earth IR, internal dissipation in; radiated out; hot/cold case annotations — **schematic**. (Also drop `fig_thermal_balance.png` + `fig_beta_eclipse.png` in here; they exist.) |
| 2 | 3.2 §3 Attitude Actuators — Physics and Sizing | 4987–5181 (195) | Reaction-wheel momentum exchange + 4-wheel pyramid geometry with the D-matrix angle β — **schematic**; plus momentum saturation vs time — **plot**. (`fig_rw_momentum.png` exists, used only in Part 2/4.) |
| 3 | 3.4 §2 Propulsion System Design | 6305–6487 (183) | Isp vs thrust map of propulsion options (cold gas, mono-prop, electric) with CubeSat envelope — **plot**. (`fig_tsiolkovsky.png` exists; add it here too.) |
| 4 | 3.4 §1 CubeSat Structure and CDS Compliance | 6123–6304 (182) | 3U CubeSat envelope with rails, rail-end contact, deployer switches, dimensional limits per CDS Rev 14 — **schematic**. |
| 5 | 3.2 §1 AOCS Fundamentals | 4691–4860 (170) | AOCS control loop: sensors → estimator → controller → actuators → plant, with disturbance torque injection — **flow/block**. |
| 6 | 4.2 §3 Environmental Test Programme | 7367–7524 (158) | Test flow: functional → vibration (sine/random) → shock → TVAC → EMC → final functional, with qualification/acceptance levels — **flow**. |
| 7 | 3.3 §8 Worked Examples: Complete Link Budgets | 5854–5966 (113) | Waterfall of the 3U S-band worked example (EIRP → FSPL → G/T → C/N₀ → Eb/N₀ → margin) — **plot**. (`fig_link_budget.png` exists; move here.) |
| 8 | 4.3 §4 FMEA/FMECA | 7842–7959 (118) | Reliability block diagram for 3-of-4 reaction wheels vs 3 wheels, with R values — **schematic**. |
| 9 | 1.2 Part 2 Regulatory Environment | 1002–1206 (205) | Licensing timeline for a Canadian CubeSat: ITU API → ISED → RSSSA → export → launch, with lead times — **flow/Gantt**. |
| 10 | 1.3 Part 2 Launch Interfaces, Debris, Int'l Law | 1513–1693 (181) | Deployer/launch-interface stack (dispenser → rails → separation switches) alongside 25-yr/5-yr rule altitude bands — **schematic**; `fig_orbital_lifetime.png` already at chapter top. |
| 11 | 2.3 §6 Radiation Environment | 3313–3381 (69) | Trapped-proton/SAA dose vs altitude and shielding thickness — **plot**. |
| 12 | 4.1 §3 Bill of Materials Construction | 6911–7043 (133) | BOM hierarchy: system → subsystem → assembly → part, with columns mass/TRL/cost/lead time — **tree**. |
| 13 | 5.1 §2 Ground Station Contact Analysis | 8561–8642 (82) | Pass geometry: elevation mask, slant range, ground track over Iqaluit — **schematic/plot**. (`fig_pass_geometry.png` and unused `fig_ground_track.png` exist.) |
| 14 | 4.4 §1 Cost Estimation Methodologies | 8042–8137 (96) | Cost-estimate accuracy vs lifecycle phase (parametric → analogy → bottom-up funnel) — **plot**. |
| 15 | 5.2 §2 FDIR Architecture | 8892–8973 (82) | FDIR hierarchy: component → subsystem → system → safe mode, with detection/isolation/recovery layers — **tree/flow**. |

Also ≥60 lines and unillustrated (lower priority): 1.1 §1 (61), 1.1 §3 (68, has placeholder comment for an SE-engine recursion figure), 1.4 Part 2 Trade Studies (148 — pairwise/AHP matrix example would help), 2.1 §4 (63, ASCII), 2.1 §6 worked example (70), 2.3 §3 Orbit trade-offs (61 — altitude vs GSD/lifetime/coverage trade plot), 2.4 §3 N² (86 — `fig_n2_matrix.png` exists), 3.1 §2 (91) & §3 (96) (nomograph/DoD PNGs exist at chapter top), 3.3 §2 (70), §3 (68), §6 (64) (PNGs exist at top of 3.4), 3.2 §2 Disturbance torques (126 — torque vs altitude plot), 3.2 §5 Momentum management (104), 3.4 §3 OBDH (87 — data flow/bus diagram), 3.4 §5 (98), 4.1 §4 Export control (65), 4.2 §2 IADT methods (101), 4.2 §4 CVM (65), 4.3 §2 Risk matrix (78, PNG at chapter top), 4.4 §4 Cost risk (88 — S-curve P50/P80 plot), 5.1 §1 (69 — ground segment block diagram), 5.3 §4 (76), 5.4 §5 (63).

---

## F. Other OER issues noticed

**Structural / cross-reference**
1. **Chapter-top figure blocks and "Expected reading" blocks are attached to the wrong chapters** (apparently an injection-script mapping error). Figures: V-model at 2.2, N² at 2.3, mass budget at 3.2, β-eclipse+thermal at 3.3, five comms figures at 3.4, lifecycle at 5.1. Readings: 1.2 (mission objectives), 1.3 (decision analysis → 1.4), 2.3 (interfaces → 2.4), 3.2 (structures → 3.4), 3.3 (thermal → 3.1), 3.4 (comms → 3.3), 5.1 (review gates → 5.4), 5.2 (ITU/RSSSA → 1.2), 5.3 (launch ICD → 3.4). Both must be re-mapped before any figure QA.
2. 25 Index links to non-existent anchor `#part-1-per-session-teaching-notes`; the index never points into Part 1 chapters. Regenerate.
3. Dangling reference "See *Course Plan* Figure 2.2" (9728) — no such document in the book.
4. Part 2/Part 4 image paths `../../assets/figures/` vs Part 1 `../assets/figures/` (one set is broken relative to `docs/course/`).
5. `# Part 3 — Position Quick-Reference Cards (quick-reference cards)` (10463) is an empty heading with a redundant parenthetical; the content is under a separate `# Appendix: Position-Specific Deep Dives` (10466). Front matter (29–30) describes Part 3 as "short-form cards"; the Appendix title says "Deep Dives" but is the short form.
6. Front matter claims (108) "inserts the SDR gate into all review-gate tables" — but 4.4 §5 table (8354–8362) has no SDR, while 1.1 §4.5 and front matter 242–248 do.
7. 1.1 §3.5 has an unrendered figure placeholder (`<!-- SVG DIAGRAM: SE Engine Recursion -->`, 560–562).
8. In-chapter forward references by session number: 3309, 3744–3746, 4509, 4604, 6552, 6639, 6744, 8307, 9384, 9453–9455, 10369 — all need renumbering to chapter numbers.

**Headings / numbering**
9. `## References` (1.1–3.4) vs `## Cited References` (4.1–5.4); position varies (end in 1.x and 4.x–5.x; before Learning Objectives in 2.x–3.x); 1.1 and 5.4 have a second inline `**References:**` list. 5.3 has no references section at all. Reference formatting also varies: numbered markdown links (1.1), bullet links (2.1), 3-column tables (4.1–5.4), bare text (Part 2).
10. 1.2–1.4 use `## Part 1/2/3` + globally numbered `###` subsections (`### 8.`, `### 9.`, `### 11. ConOps Tool Exercise`) while every other chapter uses `## 1.`, `## 2.` …; 2.2/3.4 have unnumbered `## Worked Example`; 2.1 has `## Key Equations Reference`; 1.1's UniSat-1 example sits after the Summary. Section numbering restarts per chapter — fine — but an OER needs "9.4" style numbering for cross-refs.
11. Figure numbering: none in Part 1; "Figure SE.1/PW.1/CO.1" in Part 2; "Figure V.n" in Part 4 (V.5 appears inside §V.6).
12. Two inline-SVG style families (Segoe UI/boxed in 1.x; plain sans in 2.x–3.x) and matplotlib PNGs in a third (uOttawa palette) — visual inconsistency.

**Typos / language**
13. "students fills in" (36), "students uses" (32), "The lifecycle students lives." (46), "a student in students generates" (185), "students takes its CDF positions" (9698), "For each engineering position students might take" (9684) — all residue of a regex that replaced "the cohort/the class" with "students" without fixing verb agreement.
14. Mojibake in Appendix cards: `?V` for ΔV (10481, 10517, 10643–10656), `2pi?(` for 2π√( (10514), `?(1-(R_E/a)^2)` (10515), `1.22lambdah/D` (10538), `?(? theta?^2)` (10586), `(1/2pi)?(k/m)` (10679).
15. Mixed ASCII "--" / "<=" / ">=" / "+/-" / "deg" (1.1–2.4, 4.x–5.x) against Unicode "—", "≤", "±", "°" and LaTeX in 3.x and Parts 2/4.
16. Mixed spelling conventions: "Realisation"/"Decomposition" (UK) vs occasional "optimization" (9421).

**Technical consistency**
17. Earth radius: 2.3 uses R_E = 6371 km (3153); Part 4 V.1 uses 6378.137 km (10858). Worked numbers differ accordingly (e.g. 450 km SSO period 93.7 vs 94.5 min discussed at 10895–10900).
18. Operational-mode power tables disagree: 1.4 §9.2 Safe ~1–2 W / Science ~6 W "(3U typical)" vs 5.2 §1 Safe 5–10 W / Science 25–40 W (class unstated).
19. ECSS margin schedule stated three ways (2.4 §4, Part 2 SE 9739–9744, Appendix A 10482 "13% Phase C/D").
20. Verification-method acronym drifts: "TAID" (491), "ATID" (2591), "IADT" (7266), "A/T/R/I" (index 11500).
21. Part 2 Power pitfall (10014–10017) "β = 0° … means the array sees zero illumination at orbit noon" is physically dubious (β = 0 puts the Sun in the orbit plane; a nadir-pointed body panel still sees the Sun at orbit noon). Review before publication.
22. 3.3 link-budget equation includes L_pol (5549) while Part 2 (10280) omits it; Part 4 V.7 (11045) includes both L_pol and L_r.
23. Interface-type coding differs between 2.4 §3 (M/E/T/D/R/O letters, includes Optical) and 4.3 §3 (colour codes, includes Software, no Optical).

**Licensing / branding**
24. YAML `brand: uottawa-horizon`, bilingual uOttawa footers, "garnet cover banner … u Ottawa · UNIVERSITÉ D'OTTAWA" (259–262), `uottawa_brand.py` palette name, and the AIG attribution cited as **CC BY-NC-SA 4.0** (65) — the NC-SA framework citation needs checking against the intended CC BY licence for the OER (the Peters logo itself is NC-SA; the book's licence can still be CC BY, but say so explicitly).
25. Vendor-specific product names used as worked-example facts (Bradford SSOC-D60, Blue Canyon RWP100, GomSpace NanoPower) — acceptable for OER but should carry "example, not endorsement" wording and dated prices ("EUR 15K").
26. "ESA's PROBA-2 (launched 2009, still operational in 2026)" (8881) and "version: v4 — 2026-05-05" — time-stamped claims that will date.

