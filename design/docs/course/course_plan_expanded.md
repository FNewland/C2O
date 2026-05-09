---
title: "SpaceCDF Mission Design Course"
subtitle: "Collaborative Space Mission Design: From Problem to Flight-Ready CubeSat — 40-Hour Programme"
course-codes: "SpaceCDF · 40 hours"
term: "Summer 2026"
version: "v2 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
footer-en: "SpaceCDF · 40-Hour Course Plan · 2026"
footer-fr: "SpaceCDF · Plan du cours · 2026"
running: "SpaceCDF — 40-Hour Course Plan"
---

# Course Plan

## Course title

**Collaborative Space Mission Design: From Problem to Flight-Ready
CubeSat.** A 40-hour intensive in concurrent space-mission design,
delivered with the SpaceCDF AI-assisted Concurrent Design Facility.

## Audience

Engineers, scientists, and project managers participating in
concurrent design facility (CDF) studies. **No prior spacecraft
design experience is required**, but a working engineering
background is assumed (mechanics, electromagnetics, basic
programming).

## Structure

The 40-hour programme runs over **five days × eight hours** or
**ten half-days**. The cohort works in **interdisciplinary teams of
4–5**, with each student taking one CDF position (e.g. Power, AOCS,
Comms, Payload). Two reference texts accompany the course:

- **The Facilitator's Book** — complete teaching reference with
  every session expanded, solutions, and diagrams.
- **The Learner's Workbook** — condensed content plus worksheets
  for the SpaceCDF tool exercises.

> **Expected reading before Day 1.** *NASA CubeSat 101* (≈ 90 min)
> — [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf).
> NASA Systems Engineering Handbook §1 – §3 (≈ 90 min) —
> [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).

---

## What the cohort will build

Each team will, by the end of the week, deliver:

1. **A complete preliminary CubeSat mission design** — concept,
   requirements baseline, all major subsystem decisions, interface
   matrix, V&V plan, cost estimate, and risk register.
2. **An ECSS-aligned document set** auto-exported by SpaceCDF: MRD
   (mission-requirements document), TS (technical specification),
   VP (verification plan).
3. **A PDR-style design review presentation** showing budget
   closure, traded options, and the path to detailed design.

![Lifecycle phases and review gates — NASA and ECSS](../assets/figures/fig_lifecycle.png)

*Figure 2.1 — The lifecycle the course works inside. The 40-hour
programme spans Pre-Phase A through end of Phase B (PDR).*

![System-V — decomposition meets integration](../assets/figures/fig_system_v.png)

*Figure 2.2 — System-V model. Decomposition (left) drives the
build; integration and verification (right) closes the loop. The
horizontal dashed lines are the traceability that ECSS and NASA
both demand.*

![NASA SEH 17 common technical processes](../assets/figures/fig_seh_processes.png)

*Figure 2.3 — The 17 NASA SEH processes, organised into System
Design (top), Product Realisation (middle), and Technical
Management (bottom). Each course session names which process(es)
it sits inside.*

---

## Reference standards register

| Standard | Title | Where in this course |
|----------|-------|----------------------|
| NASA SP-2016-6105 Rev 2 | Systems Engineering Handbook | All sessions; primary text for SE process |
| NPR 7123.1D | NASA Systems Engineering Processes & Requirements | Sessions 1.1, 2.1, 4.1, 5.1 |
| NPR 7120.5F | NASA Space Flight Program & Project Management | Sessions 1.1, 4.4, 5.1 |
| ECSS-E-ST-10C Rev. 1 | Space engineering — general requirements | All sessions |
| ECSS-E-ST-10-02C Rev. 1 | Verification | Sessions 4.1, 4.2 |
| ECSS-E-ST-10-24C | Interface management | Session 2.3 |
| ECSS-M-ST-10C Rev. 1 | Project planning & management | Sessions 1.1, 4.4 |
| ECSS-M-ST-80C | Risk management | Session 4.3 |
| ECSS-Q-ST-30-02C | FMEA / FMECA | Session 4.3 |
| ECSS-E-ST-32C | Structures | Session 3.2 |
| ECSS-E-ST-31C | Thermal control | Session 3.3 |
| ECSS-E-ST-50-05C | Radio frequency & modulation | Session 3.4 |
| ECSS-U-AS-10C Rev. 2 | Space debris mitigation | Session 5.2 |
| Cal Poly CDS Rev 14 | CubeSat Design Specification | Sessions 3.2, 5.3 |
| CCSDS PUS | Packet Utilization Standard | Session 4.1, Week 3 |
| ITU Radio Regulations | RF allocation & licensing | Session 5.2 |
| ISED CPC-2-6-02 | Spectrum licensing of space stations (Canada) | Session 5.2 |
| RSSSA | Remote Sensing Space Systems Act (Canada) | Session 5.2 |

> **Standard reference.** ECSS standards are freely available at
> [https://ecss.nl/](https://ecss.nl/). NASA standards: [https://standards.nasa.gov](https://standards.nasa.gov).

---

## Module map — sessions, NASA SEH §, ECSS §, SpaceCDF screens

| Day | Session | NASA SEH § | ECSS § | SpaceCDF tab | Deliverable |
|-----|---------|-----------|--------|--------------|-------------|
| 1 | 1.1 Introduction & lifecycle | §1 – §3 | E-ST-10C §4 | Step 1 | Tailoring matrix |
| 1 | 1.2 Mission need & stakeholders | §4 | E-ST-10C §5.2 | Step 1 | Stakeholder matrix, objectives |
| 1 | 1.3 Mission trade analysis | §6.5 (Process 17) | E-ST-10C §5.3 | Step 2 | Trade study matrix |
| 1 | 1.4 Concept of operations | App. S | E-ST-10C §5.4 | ConOps tab | ConOps outline |
| 2 | 2.1 Requirements engineering | §4.2 | E-ST-10C §5.5 | Requirements tab | Requirements baseline |
| 2 | 2.2 Functions & decomposition | §4.3 | E-ST-10C §5.6 | Functions tab | Functional baseline |
| 2 | 2.3 Interface management | §6.3 | E-ST-10-24C | Interfaces tab | N² matrix |
| 2 | 2.4 Architecture & block diagrams | §4.4 | E-ST-10C §5.7 | Dashboard | Block diagram |
| 3 | 3.1 Power & EPS | §4.4 | E-ST-20C | EPS tab | Solar/battery sizing |
| 3 | 3.2 Structure & mechanisms | §4.4 | E-ST-32C | Structure tab | Mass budget |
| 3 | 3.3 Thermal | §4.4 | E-ST-31C | Thermal tab | Thermal budget |
| 3 | 3.4 Comms | §4.4 | E-ST-50-05C | Link Budget tab | Link budget |
| 4 | 4.1 Equipment selection | §6.5 | E-ST-10C §5.8 | Equipment tab | BOM |
| 4 | 4.2 V&V planning | §6.4 | E-ST-10-02C | V&V Matrix | Verification matrix |
| 4 | 4.3 Risk management | §6.6 | M-ST-80C | Risk tab | Risk register |
| 4 | 4.4 Cost & schedule | §6.7 | M-ST-10C | Cost tab | Cost estimate |
| 5 | 5.1 Gate review preparation | §7 | M-ST-10C §6 | Gate Review | PDR pack |
| 5 | 5.2 Regulatory & licensing | — | (national) | Regulatory | Filings package |
| 5 | 5.3 Launch integration | §6.5 | E-ST-10C §5.10 | Launch ICD | ICD checklist |
| 5 | 5.4 Optimisation & final review | §6.5 | E-ST-10C §5.11 | Optimizer | Final design |

---

## Course Gantt — 40-hour and 3-week intensive variants

The same content can be delivered as either a 5-day 40-hour
intensive (one session per slot) or a 3-week version with
spreading (see the 3-week syllabus). The session sequence does
not change.

| | Mon | Tue | Wed | Thu | Fri |
|---|------|------|------|------|------|
| **AM** | 1.1 + 1.2 | 2.1 + 2.2 | 3.1 + 3.2 | 4.1 + 4.2 | 5.1 + 5.2 |
| **PM** | 1.3 + 1.4 | 2.3 + 2.4 | 3.3 + 3.4 | 4.3 + 4.4 | 5.3 + 5.4 |

---

## Day 1 — Mission Definition & Concept (8 h)

### Session 1.1 — Introduction to space mission design (2 h)

- What is a Concurrent Design Facility (CDF)? History (ESA Concurrent
  Design Facility, JPL Team-X, NASA Glenn COMPASS).
- The System-V model (NASA SEH Ch. 2 – 3) — see Figure 2.2.
- The 17 SE processes (NPR 7123.1) — see Figure 2.3.
- NASA / ECSS lifecycle phases and review gates — see Figure 2.1.
- Role of each CDF position and what "ownership" means in a CDF.
- **Exercise:** map the 17 processes to the SpaceCDF tool tabs.
- **Worksheet:** Worksheet 1.1 (process map).

### Session 1.2 — Mission need & stakeholder analysis (2 h)

- NASA SEH Process 1: Stakeholder Expectations Definition.
- Problem-statement writing (NASA SEH §4.1).
- Stakeholder identification and needs elicitation. Indigenous
  community engagement and UNDRIP considerations for Canadian
  context.
- Objective definition with measurable success criteria.
- MoE / MoP / TPM hierarchy.
- **Exercise:** define mission need for a sample problem (using
  SpaceCDF Step 1).
- **Worksheet:** stakeholder matrix, objective hierarchy.

### Session 1.3 — Mission trade analysis (2 h)

- NASA SEH Process 17: Decision Analysis.
- Space vs non-space alternatives — *when not to build a satellite*.
- Trade-study methodology: criteria, weightings, scoring; AHP and
  weighted-sum sensitivity.
- Existing data services (Copernicus / Sentinel, Planet, Spire,
  Radarsat).
- **Exercise:** run mission trade in SpaceCDF (Step 2).
- **Worksheet:** trade-study matrix with scoring.

### Session 1.4 — Concept of operations (2 h)

- NASA SEH Appendix S: ConOps structure.
- Mission architecture: space, ground, user segments.
- Mission phases (LEOP → commissioning → nominal → disposal) — see
  Figure 2.4.
- Operational modes and duty cycling.
- Data-flow pipeline design.
- Ground-segment architecture options.
- **Exercise:** build ConOps in SpaceCDF.
- **Worksheet:** ConOps outline per Appendix S.

![ConOps timeline — LEOP through disposal](../assets/figures/fig_conops_timeline.png)

*Figure 2.4 — Representative LEO mission timeline. The course
designs from Day 1 against this timeline.*

> **Expected reading before Day 2.** SMAD4 Ch. 4 – §6 (mission
> definition); NASA SEH Appendix C (How to write a good
> requirement) — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).

---

## Day 2 — Requirements, functions & interfaces (8 h)

### Session 2.1 — Requirements engineering (2 h)

- NASA SEH Process 2: Technical Requirements Definition.
- SMART requirements (Specific · Measurable · Achievable ·
  Relevant · Traceable).
- *WHAT not HOW* — requirements vs design choices. The classic
  failure mode: writing implementation in the requirements.
- Requirement hierarchy: mission → system → subsystem.
- NASA SEH Appendix C — *How to write a good requirement*.
- **Exercise:** generate requirements from objectives in SpaceCDF.
- **Worksheet:** requirements quality checklist.

### Session 2.2 — Functions & decomposition (2 h)

- NASA SEH Process 3: Logical Decomposition.
- Functional analysis vs physical decomposition.
- Function trees; function-allocation matrix; mode matrix.
- **Exercise:** decompose top-level mission function in SpaceCDF.
- **Worksheet:** function-allocation matrix.

### Session 2.3 — Interface management (2 h)

- NASA SEH §6.3 (Process 12) — interface management.
- ECSS-E-ST-10-24C — interface requirements documents.
- The N² matrix and interface-type classification (Mechanical,
  Electrical, Thermal, Data, RF, Optical).

![N² interface matrix for a 6U CubeSat](../assets/figures/fig_n2_matrix.png)

*Figure 2.5 — N² interface matrix for a 6U CubeSat. Cells are
coloured by interface type; "D" = data, "E" = electrical,
"M" = mechanical, "T" = thermal, "R" = RF, "O" = optical.*

- **Exercise:** complete N² matrix for the team's mission in
  SpaceCDF.
- **Worksheet:** interface-requirements draft for two pairs.

### Session 2.4 — Architecture & block diagrams (2 h)

- Architecture decision records.
- Block-diagram conventions; signal-flow vs power-flow.
- Power architecture; data architecture; thermal coupling.
- **Exercise:** build subsystem block diagrams in SpaceCDF.
- **Worksheet:** architecture decision log (3 entries).

> **Expected reading before Day 3.** SMAD4 Ch. 9 (orbit selection),
> Ch. 11 (power), Ch. 12 (thermal), Ch. 13 (structures). All
> referenced sections cached on Brightspace.

---

## Day 3 — Subsystem design loop (8 h)

### Session 3.1 — Power & EPS (2 h)

- Power-budget structure: bus / housekeeping / payload / comms /
  thermal / margin.
- Solar array sizing (body-mounted vs deployable) at end-of-life.
- Battery sizing — DoD vs cycle life trade.
- EPS architecture: MPPT, PCDU, single-bus vs dual-bus.

![Power profile across one orbit — generation and stacked load](../assets/figures/fig_power_modes.png)

*Figure 2.6 — Generation (top) and stacked load (bottom) over one
orbit. Eclipse drives battery sizing; comms and payload pulses
drive PCDU peak rating.*

- **Exercise:** size SA + battery in SpaceCDF.
- **Worksheet:** EPS sizing sheet, end-of-life worst-case.

### Session 3.2 — Structure & mechanisms (2 h)

- Cal Poly CDS Rev 14 — CubeSat structural envelope.
- Launch loads: quasi-static, sine-vibration, random vibration,
  shock.
- Mass-budget convergence under ECSS margin policy.

![Mass budget — distribution and ECSS margin policy](../assets/figures/fig_mass_budget.png)

*Figure 2.7 — Mass distribution and the ECSS margin schedule.
Margin starts at +44 % at Phase A and tightens to +5 % at Phase D.*

- **Exercise:** size structure in SpaceCDF.
- **Worksheet:** mass budget with margin column.

### Session 3.3 — Thermal (2 h)

- Radiative equilibrium first-order analysis.
- Hot-case / cold-case envelope.
- β-angle and eclipse — see Figure 2.8.
- Passive vs active thermal control; MLI; heaters; heat pipes.

![β-angle envelope and eclipse fraction analysis](../assets/figures/fig_beta_eclipse.png)

*Figure 2.8 — β-angle range vs day of year (left) and eclipse
fraction analytical curves (right) for an ISS-like and a 600 km SSO.*

- **Exercise:** thermal envelope analysis in SpaceCDF.
- **Worksheet:** thermal budget with heater duty.

### Session 3.4 — Communications (2 h)

- Link-budget basics: EIRP, FSPL, G/T, C/N₀ vs Eb/N₀.
- Frequency band selection — UHF / S / X / Ka.
- Modulation and coding: QPSK + LDPC (DVB-S2 family) for ground.
- Doppler and Doppler-rate budget for a polar pass.
- Antenna patterns and pointing.

![S-band downlink link budget — waterfall](../assets/figures/fig_link_budget.png)

*Figure 2.9 — A canonical link-budget waterfall. Required C/N₀
and link margin always sit at the bottom-right.*

- **Exercise:** close link budget in SpaceCDF.
- **Worksheet:** link-budget calculator with margin.

> **Expected reading before Day 4.** SMAD4 Ch. 17 (V&V); ECSS-E-ST-10-02C; NASA NPR 8715.3 (system safety —
> primer only).

---

## Day 4 — Equipment, V&V, risk, cost (8 h)

### Session 4.1 — Equipment selection (2 h)

- Catalogue vs custom design.
- TRL gating decisions.

![Technology readiness level ladder](../assets/figures/fig_trl.png)

*Figure 2.10 — TRL ladder. Most CubeSat platform decisions land at
TRL 7 – 9; novel instruments at TRL 4 – 6 require explicit
risk-buy-down planning.*

- **Exercise:** complete equipment selection in SpaceCDF.
- **Worksheet:** equipment-compatibility checklist.

### Session 4.2 — Verification & validation planning (2 h)

- NASA SEH Processes 7 – 8.
- ECSS-E-ST-10-02C — verification methods (A · T · R · I).
- Verification-matrix structure.
- Test levels — unit → subsystem → system → acceptance → qualification.
- Environmental testing — vibration, thermal-vacuum, EMC.
- **Exercise:** review compliance matrix in SpaceCDF.
- **Worksheet:** V&V matrix for 10 key requirements.

### Session 4.3 — Risk management (2 h)

- ECSS-M-ST-80C — risk-management process.
- Risk identification, assessment (5×5 matrix), mitigation.
- FMECA methodology (ECSS-Q-ST-30-02C).
- Single-point failure analysis.
- Technical Performance Measures (TPMs).

![5×5 risk matrix with worked examples](../assets/figures/fig_risk_matrix.png)

*Figure 2.11 — The risk matrix in use. Each plotted point is a
real risk on a representative mission; positions on the matrix
drive mitigation priority.*

- **Exercise:** review risk scores and reliability in SpaceCDF.
- **Worksheet:** risk register for top 5 risks.

### Session 4.4 — Cost & schedule (2 h)

- Cost estimation: parametric (SSCM, COMPACT), analogy, bottom-up.
- WBS structure (NPR 7120.5).
- CubeSat cost drivers and cost fractions.
- Schedule estimation and critical path; learning-curve effects
  for constellations.
- **Exercise:** review cost breakdown and run optimiser.
- **Worksheet:** cost estimate by WBS element.

> **Expected reading before Day 5.** ECSS-M-ST-10C §6 (review
> gates) — [https://ecss.nl/](https://ecss.nl/). ITU Radio
> Regulations Article 21 — [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR).

---

## Day 5 — Design review & regulatory (8 h)

### Session 5.1 — Gate review preparation (2 h)

- ECSS-M-ST-10C — review-gate structure.
- MCR / SRR / PDR / CDR exit criteria.
- Design-review presentation structure: 6-slide standard pack.
- Action-item management.
- **Exercise:** run gate review in SpaceCDF; resolve action items.
- **Worksheet:** PDR presentation outline.

### Session 5.2 — Regulatory & licensing (2 h)

- Frequency licensing — ITU, IARU, national authority.
- ITU filing process (API → coordination → notification).
- Canadian RSSSA for remote sensing.
- Export control: ITAR / EAR / Canadian CGP.
- UN Registration Convention (COPUOS).
- Space-debris regulations (25-yr / 5-yr rules).
- **Exercise:** generate regulatory filings in SpaceCDF.
- **Worksheet:** licensing decision tree.

### Session 5.3 — Launch integration (2 h)

- Launch providers and pricing landscape.
- Deployer standards (ISIPOD, EXOpod, CSD).
- Launch ICD requirements (mechanical, electrical, environmental).
- Separation switches and inhibits.
- Environmental-test specification derivation.
- **Exercise:** select launch provider, review ICD requirements.
- **Worksheet:** launch ICD compliance checklist.

### Session 5.4 — Design optimisation & final review (2 h)

- Multi-objective optimisation (Pareto concepts).
- Sensitivity analysis (Morris screening).
- Design iteration and convergence.
- Final design-review presentation.
- Lessons-learned capture.
- **Exercise:** run optimiser, review Pareto front, select final
  design.
- **Final Exercise:** each team presents its complete mission design.

---

## Assessment

- **Day 1 – 4:** worksheets completed in class (formative).
- **Day 5:** team presentation of complete mission design (summative).
- **Post-course:** continued access to the SpaceCDF tool and the
  Facilitator's Book for self-study.

### Bloom-level outcome matrix

| Outcome | Bloom level | Where earned |
|---------|-------------|--------------|
| Recall the 17 SEH processes and gate sequence | Remember | Sessions 1.1, 5.1 |
| Explain the System-V and where it fails | Understand | Sessions 1.1, 4.2 |
| Apply SMART criteria to derive requirements | Apply | Session 2.1 |
| Apply the N² matrix to a real CubeSat | Apply | Session 2.3 |
| Analyse a link budget and find the dominant loss | Analyse | Session 3.4 |
| Analyse a risk register and find single points of failure | Analyse | Session 4.3 |
| Evaluate trade-off options and defend a recommendation | Evaluate | Sessions 1.3, 5.4 |
| Create a complete preliminary CubeSat design | Create | Day 5 final review |

### Equipment & software register

| Tool | Purpose | Where in course |
|------|---------|-----------------|
| SpaceCDF (web) | Concurrent design and review | All days |
| Brightspace | Reading distribution, submissions | All days |
| Python 3.11+ (notebooks) | Optional analytical exercises | Days 3, 4 |
| Open-source plotting (matplotlib, plotly) | Visualisations | Days 3, 4 |
| Office suite | PDR slide pack | Days 1, 5 |

### Pre-requisite knowledge audit (self-check)

| Topic | Required level | Where to refresh |
|-------|----------------|------------------|
| Newtonian mechanics | Year 1 engineering | Hibbeler / Meriam |
| Vector and matrix algebra | Year 2 engineering | Strang |
| Basic electromagnetism | Year 1 physics | Griffiths Ch. 1 – 3 |
| Statistics & probability | Year 2 engineering | Montgomery & Runger |
| Programming basics | Comfortable in any language | — |

### RACI for delivery

| Activity | Instructor | Co-instructor | TA / facilitator | Cohort |
|----------|------------|---------------|------------------|--------|
| Lecture delivery | R | A | C | I |
| CDF session facilitation | A | R | R | C |
| Tool support | I | I | R | A |
| Worksheet review | C | R | A | I |
| Gate review | R | A | C | C |
| Final review judging | R | R | C | I |

R = Responsible, A = Accountable, C = Consulted, I = Informed.

---

## Per-position deep dives (appendices)

The Facilitator's Book carries full per-position appendices
(systems engineer, mission analyst, payload, power, AOCS,
thermal, structures, propulsion, comms, OBDH, software,
operations, ground segment). The summary list of positions and
their responsibilities is below; full appendices live in the
Facilitator's Book.

| Position | Owns (parameters) | Drives (sessions) |
|----------|-------------------|-------------------|
| Systems Engineer | Mass margin, power margin, system cost, TRL, health score | All |
| Mission Analyst | Orbit, ground track, contact time, eclipse, β | 1.4, 3.1 – 3.3 |
| Payload Engineer | Aperture, GSD, data rate, FOV | 1.2, 3.4 |
| Power Engineer | Solar-array area, battery capacity, EPS topology | 3.1 |
| AOCS Engineer | Pointing budget, RW capacity, sensor selection | 3.2, 4.3 |
| Thermal Engineer | Hot/cold case, radiator area, heater duty | 3.3 |
| Structures Engineer | Mass-budget closure, deployers, mechanisms | 3.2 |
| Propulsion Engineer | Δv budget, thruster sizing, propellant mass | (when needed) |
| Comms Engineer | Link budget, antenna pattern, modulation | 3.4 |
| OBDH / Software | OBC, FSW architecture, FDIR, telemetry list | 4.1 |
| Operations | Pass plan, ConOps, anomaly tree | 1.4, 5.1 |
| Ground Segment | Ground stations, MCS, MPS, archive | 1.4, 5.1 |
| Cost / Schedule | WBS, CER, critical path | 4.4 |

---

## Reference list (live links)

- **NASA SEH (SP-2016-6105 Rev 2)** — *Systems Engineering Handbook*. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
- **NPR 7123.1D** — [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- **NPR 7120.5F** — [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- **NASA CubeSat 101** — [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf)
- **ECSS standards (all)** — [https://ecss.nl/](https://ecss.nl/)
- **Cal Poly CDS Rev 14** — [https://www.cubesat.org/cds-announcement](https://www.cubesat.org/cds-announcement)
- **CCSDS PUS** — [https://public.ccsds.org/Pubs/660x0g3.pdf](https://public.ccsds.org/Pubs/660x0g3.pdf)
- **ITU Radio Regulations** — [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR)
- **ISED CPC-2-6-02** — [https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en](https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en)
- **Remote Sensing Space Systems Act** — [https://laws-lois.justice.gc.ca/eng/acts/R-5.4/](https://laws-lois.justice.gc.ca/eng/acts/R-5.4/)
- **IADC debris guidelines** — [https://www.iadc-home.org/](https://www.iadc-home.org/)
- **UN COPUOS Registration Convention** — [https://www.unoosa.org/](https://www.unoosa.org/)
- **Wertz, Everett & Puschell** — *Space Mission Engineering: The New SMAD* (2011).
- **Larson & Wertz** — *Space Mission Analysis and Design*, 4th ed.
- **Sutton & Biblarz** — *Rocket Propulsion Elements*, 9th ed.
- **Markley & Crassidis** — *Fundamentals of Spacecraft Attitude Determination and Control*.
- **Pratt, Bostian & Allnutt** — *Satellite Communications*, 3rd ed.
- **Fortescue, Stark & Swinerd** — *Spacecraft Systems Engineering*, 4th ed.
