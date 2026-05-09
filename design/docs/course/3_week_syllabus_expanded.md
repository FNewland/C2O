---
title: "Space Mission Design & Operations"
subtitle: "3-Week Intensive Programme — Syllabus"
course-codes: "SpaceCDF Course"
term: "Summer 2026"
version: "v2 — 2026-05-05"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
footer-en: "SpaceCDF · 3-Week Intensive Syllabus · 2026"
footer-fr: "SpaceCDF · Programme intensif de 3 semaines · 2026"
running: "SpaceCDF — 3-Week Intensive Syllabus"
---

# 3-Week Intensive Syllabus

## Audience and pre-requisites

This programme suits **industry professionals, graduate students, and
upper-year undergraduates** with an engineering background and the
appetite to make decisions quickly and in public. We assume basic
mechanics, electromagnetism, and programming literacy — but **no
prior spacecraft experience**. The cohort runs **20 to 30 participants**
in **interdisciplinary teams of 4 to 5**.

The course is delivered Monday to Friday, 09:00 – 16:00, in person at
the University of Ottawa. The tool spine is the **SpaceCDF AI-assisted
Concurrent Design Facility**.

> **Expected reading before Day 1.** *NASA CubeSat 101* (≈ 90 min) —
> [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf).
> *NASA Systems Engineering Handbook* §2 (≈ 60 min) —
> [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).

---

## How the three weeks fit together

![Mission lifecycle and review gates — Pre-Phase A through Phase F, NASA and ECSS gates](../assets/figures/fig_lifecycle.png)

*Figure 1.1 — The lifecycle the cohort lives. Week 1 grounds you in
Pre-Phase A; Week 2 walks the Phase A/B portion of the V; Week 3
puts you in operator seats during commissioning.*

The course follows the **System-V model** — decomposition on the
left, integration and verification on the right — and aligns each
day to a recognisable lifecycle phase.

![System-V model with the cohort's daily touchpoints](../assets/figures/fig_system_v.png)

*Figure 1.2 — System-V with course touchpoints. Mission-needs work
happens Day 1; subsystem specs converge Days 2–3; integration and
V&V are Day 4; the gate review is Day 5.*

---

## Week 1 — Canadian Space Landscape & Regulatory Environment

This week grounds the cohort in the system the missions live in:
the **Canadian space ecosystem**, the **regulatory landscape**, and
the systems-engineering frameworks that professionals actually use.
Lectures are deliberately short — the aim is to set context for the
tool-led work that begins in Week 2.

![The Canadian space sector — actors and funding flows](../assets/figures/fig_canadian_sector.png)

*Figure 1.3 — A map of the Canadian space sector. Where students
see themselves in this picture is the central question of Day 1.*

### Daily schedule

| Day | Topic | Activities |
|-----|-------|-----------|
| **Mon** | **The Canadian Space Ecosystem** | Canadian Space Agency mandate & programmes. Industry map: MDA, Telesat, GHGSat, Kepler, NorthStar, university labs. CSA funding (STDP, FAST, CSEP). Canada's role in Artemis, Lunar Gateway, Radarsat. Guest speaker (CSA or industry). |
| **Tue** | **Regulatory Framework** | ISED spectrum licensing under CPC-2-6-02. RSSSA (Remote Sensing Space Systems Act). Canadian Controlled Goods Programme and export control. ITU filing through ISED. Practical: complete an ISED spectrum-licence application for a sample mission. |
| **Wed** | **International Standards & Compliance** | ECSS standard framework and tailoring. NASA SEH 17 processes overview (see Figure 2). Cal Poly CDS Rev 14. Space-debris mitigation (IADC 25 yr, FCC 5 yr). UN Registration Convention. Practical: complete a tailoring matrix. |
| **Thu** | **Mission Needs & Opportunities** | Identifying mission needs in the Canadian context (Arctic monitoring, maritime surveillance, agriculture, resource management, connectivity). Stakeholder analysis. Indigenous community engagement and UNDRIP. Problem-statement workshop. |
| **Fri** | **Space vs Non-Space Trade & Concept** | Trade-study methodology (criteria, weightings, scoring). Existing services (Radarsat, Sentinel, Planet) vs new missions. Constellation economics and business cases. Teams form, select a mission need, and run an initial trade analysis in SpaceCDF. |

### Canadian regulatory checklist (Tuesday deliverable)

| Regulator | Filing | Trigger | Approximate timeline |
|-----------|--------|---------|----------------------|
| ISED (Spectrum Management) | Radio licence — CPC-2-6-02 | Any RF emission to/from satellite | 6 – 12 months |
| ISED (RSSSA) | RSSSA licence | Earth-observation payload above resolution threshold | 12 – 18 months |
| ITU (via ISED) | API → coordination → notification | New frequency assignment | 2 – 5 years |
| Global Affairs Canada | Export permit (ECL / CGP) | Cross-border hardware, data, technology transfer | 4 – 12 weeks |
| UNOOSA (via Global Affairs) | Registration of Space Object | Launch into orbit | At launch |
| ISED (Space-Object) | Debris-mitigation plan | Launch — IADC 25 yr / FCC 5 yr | At launch |

> **Standard reference.** ECSS-E-ST-10C Rev. 1 — *System engineering
> general requirements* — [https://ecss.nl/standards/active-standards/ecss-e-st-10c-rev-1-system-engineering-general-requirements/](https://ecss.nl/standards/active-standards/ecss-e-st-10c-rev-1-system-engineering-general-requirements/).
> NASA SEH (SP-2016-6105 Rev 2) — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/).

### Mission archetypes used in Week 1 trade studies

| Archetype | Orbit | Payload | Comms | Typical use |
|-----------|-------|---------|-------|-------------|
| Ocean-colour EO | 450 – 700 km SSO, ≈ 98° | Multispectral imager | S-band | GHG, climate, fisheries |
| SAR EO | 500 – 700 km SSO | C/X/Ka SAR | X-band | Maritime, ice, defence |
| AIS | 400 – 600 km LEO | RF receiver | UHF/VHF | Maritime traffic |
| IoT / data relay | 500 – 1100 km LEO | Store-forward radio | UHF/Ka | Connectivity, IoT |
| Climate-GHG | 500 km SSO | Spectrometer (point) | S-band | Methane, CO₂ |
| LEO-PNT | 500 – 1200 km MEO/LEO | GNSS supplement | L-band | Backup PNT |
| Constellation comms | 500 – 1200 km LEO | Phased-array | Ka-band | Broadband/IoT |

### Weekend pre-work (overnight reading flag)

> **Expected reading before Tuesday.** ECSS-M-ST-10C Rev. 1
> §5 (project-management lifecycle), ≈ 30 min —
> [https://ecss.nl/](https://ecss.nl/). NASA CubeSat 101 §3
> (mission types).

> **Expected reading before Wednesday.** Cal Poly *CubeSat Design
> Specification* Rev 14, §1 – §3 (≈ 45 min) —
> [https://www.cubesat.org/cds-announcement](https://www.cubesat.org/cds-announcement).

> **Expected reading before Friday.** SpaceCDF user guide §1 – §3
> (≈ 30 min). Bring a one-page mission idea on Friday morning.

---

## Week 2 — Concurrent Design Facility — Designing a Mission

Week 2 is the **CDF intensive**. Each interdisciplinary team
converges on a complete preliminary mission design across five
working days, supported by SpaceCDF's embedded systems-engineering
process, risk register, and trade-study modules. The PDR sits at
end of week.

![ConOps timeline — LEOP through commissioning, nominal ops, and disposal](../assets/figures/fig_conops_timeline.png)

*Figure 1.4 — A representative LEO mission timeline. Week 2 builds
the design that will fly through this timeline.*

### Daily schedule

| Day | Topic | Activities |
|-----|-------|-----------|
| **Mon** | **System-V & Requirements** | System-V model deep dive. SMART requirements from objectives. Functional decomposition. Teams enter mission need, run orbit/class advisors, generate the requirements baseline in SpaceCDF. |
| **Tue** | **Subsystem Design: Power, AOCS, Thermal** | Orbit selection trade. Solar-array and battery sizing. Duty cycling. Attitude-control selection. Thermal environment analysis. Teams run the design loop and review parametric budgets. |
| **Wed** | **Subsystem Design: Comms, Structure, Propulsion** | Link-budget calculation. Frequency-band selection and licensing implications via the SpaceCDF regulatory check. CubeSat structure and deployer selection. Propulsion trade. Equipment selection in the SpaceCDF library. |
| **Thu** | **Integration, Verification, Cost** | Interface-matrix review. V&V matrix assignment. Environmental test planning. Cost estimation (parametric + COTS). Bill of materials. Trade studies on key decisions. |
| **Fri** | **Design Review & Optimisation** | Run optimiser. Sensitivity analysis. Gate review (PDR criteria). Resolve conflicts. Generate ECSS documents (MRD, TS, VP). Regulatory filings (ITU, RSSSA if applicable). Each team presents its preliminary design. |

### A first look at the budgets you will close

![Mass distribution and ECSS margin policy by phase](../assets/figures/fig_mass_budget.png)

*Figure 1.5 — Mass budget and the ECSS margin schedule. Phase A
margins start at +44 % above dry mass and tighten phase-by-phase to
+5 % at Phase D.*

![Power profile across one orbit — generation, eclipse, stacked load](../assets/figures/fig_power_modes.png)

*Figure 1.6 — Power generation and load profile across one orbit.
Eclipse is the disciplined consumer of design margin.*

![Link-budget waterfall — S-band downlink, 1500 km slant range](../assets/figures/fig_link_budget.png)

*Figure 1.7 — A link-budget waterfall is the standard way to
present a closed link. Required C/N₀ and link margin sit at the
bottom-right of every link-budget review.*

### Risk register template (Wednesday + Thursday)

| ID | Title | P (1–5) | I (1–5) | Score | Owner | Mitigation | Status |
|----|-------|--------:|--------:|------:|-------|------------|--------|
| R1 | RW failure mid-life | 4 | 3 | 12 | AOCS | Redundant 4-wheel pyramid; in-flight desat strategy | Open |
| R2 | Battery degradation > 20 % | 2 | 4 | 8 | EPS | Cycle-life model; DoD ≤ 30 % design point | Open |
| R3 | Star-tracker glare during equator pass | 3 | 2 | 6 | AOCS | Two-head ST; baffle design; pointing law | Open |
| R4 | Ground-link outage at LOS | 3 | 3 | 9 | TT&C | Redundant GS (Iqaluit + Troll); SSPA back-off | Open |
| R5 | Programme schedule slip | 4 | 4 | 16 | PM | Critical-path padding; pre-procure long-lead items | Open |
| R6 | Cosmic-ray SEU on OBC | 5 | 1 | 5 | OBDH | Watchdog + EDAC + N-version; daily TM check | Open |

![5×5 risk matrix with worked example](../assets/figures/fig_risk_matrix.png)

*Figure 1.8 — The ECSS-M-ST-80C 5×5 risk matrix. Tier colour
coding: 1–2 green, 3–4 light green, 5–9 yellow, 10–15 amber, 16–25
red. R5 (schedule) sits in the amber band; R6 (SEU) is yellow but
deserves attention because of the consequence dimension.*

> **Expected reading before Tuesday Wk 2.** SMAD4 Ch. 9 (orbit
> selection) and Ch. 10 (mission analysis) — locally cached on
> Brightspace. ECSS-E-ST-32C (structures) §4 — [https://ecss.nl/](https://ecss.nl/).

---

## Week 3 — Mission Operations & Simulation

Week 3 puts the cohort into mission-control seats. Two days of
operations training, followed by two days running a live simulation
on the SpaceCDF / EOSAT-1 simulator at the uOttawa Cyberrange. See
the dedicated Week 3 documents for the operations curriculum,
procedures, and simulation packs.

| Day | Topic | Activities |
|-----|-------|-----------|
| **Mon** | **Operations Concept Development** | Ground-segment architecture. MCS familiarisation (COSMOS / OpenMCT / Yamcs overview). Operations procedures: nominal, contingency, FDIR. Pass planning and scheduling. TC/TM definition from SpaceCDF FSW export. |
| **Tue** | **Mission Operations Training** | Console positions and responsibilities. Voice-loop discipline. Anomaly-response procedures. Dry-run walk-throughs of LEOP, nominal, and contingency scenarios. Practice commanding and telemetry monitoring. |
| **Wed** | **Mission Simulation Day 1** | Full-day simulated LEOP + commissioning. Teams operate their designed mission on console. Deployment, first contact, detumbling, initial checkout. Real-time anomaly injection. Post-sim debrief and lessons-learned. |
| **Thu** | **Mission Simulation Day 2** | Full-day simulated nominal + contingency operations. Science-data acquisition mode. Ground-pass downlink. Injected anomalies: safe-mode entry, power anomaly, comms degradation. Constellation ops (for teams with multi-satellite designs). Post-sim debrief. |
| **Fri** | **Wrap-Up & Presentations** | Final design documentation review. Each team presents complete mission: need, design, ops concept, lessons-learned. Peer review and Q&A. Certificate. Course evaluation. Discussion: next steps, collaboration opportunities, CSA / industry pathways. |

---

## Assessment

| Component | Weight | Description |
|-----------|-------:|-------------|
| Worksheets (daily) | 20 % | Completed during sessions, formative feedback |
| Design Review (Week 2 Fri) | 30 % | Team presentation of preliminary design |
| Simulation Performance (Week 3) | 20 % | Console operations, anomaly response |
| Final Presentation (Week 3 Fri) | 30 % | Complete mission design, ops concept, lessons |

### Competency self-assessment grid

Use this in **week 0** and again at end of **week 3**. Score each
row 1 (no exposure) – 5 (could lead a team in this area).

| Competency | Wk 0 | Wk 3 | Δ |
|------------|:----:|:----:|:-:|
| Articulate the Canadian space sector and one's place in it | | | |
| Identify and apply Canadian regulatory obligations | | | |
| Decompose mission objectives to SMART requirements | | | |
| Design a mission inside a CDF (any discipline role) | | | |
| Maintain a risk register and a planning baseline | | | |
| Read & write a procedure file (ECSS-E-ST-70-32C) | | | |
| Operate an MCS console under voice-loop discipline | | | |
| Lead a structured peer critique | | | |
| Synthesise lessons-learned into improvement actions | | | |

---

## Course outcomes

By the end of the programme, every participant will have:

- Worked a complete CubeSat mission design from problem statement
  to PDR, inside a Concurrent Design Facility.
- Operated each of the six MCS positions for at least one
  ground-station pass on a live simulator.
- Maintained a risk register and a planning baseline through
  the full design week.
- Written, run, and critiqued at least one operations procedure.
- Built a peer network across academia, industry, and the
  Canadian Space Agency.

---

## Reference list

A live, hyperlinked list of the standards, handbooks, and tools
referenced in the syllabus.

- **NASA SEH (SP-2016-6105 Rev 2)** — *Systems Engineering Handbook*. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
- **NPR 7123.1D** — *NASA Systems Engineering Processes and Requirements*. [https://nodis3.gsfc.nasa.gov/](https://nodis3.gsfc.nasa.gov/)
- **NPR 7120.5F** — *NASA Space Flight Program and Project Management Requirements*. [https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_)
- **NASA CubeSat 101** — *Basic Concepts and Processes for First-Time CubeSat Developers*. [https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf)
- **ECSS-E-ST-10C Rev. 1** — *System engineering general requirements*. [https://ecss.nl/standards/active-standards/ecss-e-st-10c-rev-1-system-engineering-general-requirements/](https://ecss.nl/standards/active-standards/ecss-e-st-10c-rev-1-system-engineering-general-requirements/)
- **ECSS-E-ST-10-02C Rev. 1** — *Verification*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-E-ST-10-24C** — *Interface management*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-M-ST-10C Rev. 1** — *Project planning*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-M-ST-80C** — *Risk management*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-Q-ST-30-02C** — *FMEA / FMECA*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-E-ST-70C** — *Ground systems and operations*. [https://ecss.nl/](https://ecss.nl/)
- **ECSS-E-ST-70-32C** — *Test and operations procedures*. [https://ecss.nl/](https://ecss.nl/)
- **Cal Poly CDS Rev 14** — *CubeSat Design Specification*. [https://www.cubesat.org/cds-announcement](https://www.cubesat.org/cds-announcement)
- **CCSDS PUS** — *Packet Utilization Standard*. [https://public.ccsds.org/Pubs/660x0g3.pdf](https://public.ccsds.org/Pubs/660x0g3.pdf)
- **ITU-R Radio Regulations** — [https://www.itu.int/pub/R-REG-RR](https://www.itu.int/pub/R-REG-RR)
- **ISED CPC-2-6-02** — *Licensing of space stations*. [https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en](https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en)
- **Remote Sensing Space Systems Act** — [https://laws-lois.justice.gc.ca/eng/acts/R-5.4/](https://laws-lois.justice.gc.ca/eng/acts/R-5.4/)
- **IADC 25-year debris mitigation guideline** — [https://www.iadc-home.org/](https://www.iadc-home.org/)
- **UN COPUOS Registration Convention** — [https://www.unoosa.org/](https://www.unoosa.org/)
- **Wertz, Everett & Puschell** — *Space Mission Engineering: The New SMAD* (2011).
- **Larson & Wertz** — *Space Mission Analysis and Design*, 4th ed.
- **Sutton & Biblarz** — *Rocket Propulsion Elements*, 9th ed.
- **Markley & Crassidis** — *Fundamentals of Spacecraft Attitude Determination and Control*.
- **Pratt, Bostian & Allnutt** — *Satellite Communications*, 3rd ed.
