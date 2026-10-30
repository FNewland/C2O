# Chapter 5 — Requirements Engineering

> **Recommended background.** NASA Systems Engineering Handbook Appendix C — How to Write a Good Requirement; ECSS-E-ST-10C §5.5; ECSS-E-ST-10-06C §5. This chapter assumes that a mission need, stakeholder analysis and concept of operations exist (Chapter 4) and builds on the V-model of Chapter 1.

## Learning objectives

By the end of this chapter, you will be able to:

1. Explain how requirements flow down the left side of the System-V while verification flows up the right side
2. Write requirements that satisfy the SMART criteria and express WHAT, not HOW
3. Classify requirements by type: functional, performance, interface, constraint, and environmental
4. Construct a three-level requirement hierarchy (mission, system, subsystem) with bidirectional traceability
5. Assign verification methods (ATIR(D)) to requirements and justify each choice
6. Generate, validate and manage a requirement set for a small spacecraft, whether in a concurrent-design tool or a spreadsheet

---

## 5.1 Requirements on the System-V

Recall the System-V of Chapter 1 (Figure 1.1). The left branch decomposes stakeholder needs into mission, system and subsystem requirements at increasing levels of detail; the right branch integrates and verifies at the corresponding levels, so that every horizontal row of the V is a matched pair — a requirement and the test or analysis campaign that confirms it. The phase mapping (Table 1.1) and the SuperDove example (§1.2.6) showed how a commercial constellation works this correspondence in practice. This chapter works the *top of the left branch*: how to write the requirements that the rest of the design will be decomposed from, how to organise them into a traceable hierarchy, and how to assign to each the verification method that will later close its row of the V.

*[Source: NASA SEH Fig. 3-1; ECSS-E-ST-10C Rev.1 Fig. 5-1; INCOSE SEH 5th ed. Fig. 2.7]*

---

## 5.2 What is a requirement?

*[Source: NASA SEH Sec. 4.2; ECSS-E-ST-10-06C Sec. 5.2]*

A requirement is a **formal, verifiable statement of what the system must do or how well it must perform**. It is expressed as a "shall" statement with a measurable threshold.

### 5.2.1 The shall convention

Requirements use contractually precise language:

| Keyword | Meaning | Contractual force |
|---------|---------|-------------------|
| **"Shall"** | Mandatory requirement — must be met | Binding |
| **"Should"** | Goal or guideline — desired but not mandatory | Advisory |
| **"Will"** | Statement of fact or intent — not a requirement | Informational |

**Example:**
> "The system **shall** achieve a ground sample distance of 10 m or better at nadir from the operational orbit."

This is testable: GSD can be computed from optical geometry and verified from calibration imagery.

### 5.2.2 Requirement types

| Type | Definition | Example |
|------|-----------|---------|
| **Functional** | What the system must *do* (a capability) | "The system shall acquire multispectral imagery of the target area" |
| **Performance** | How *well* it must do it (quantified) | "The system shall achieve GSD ≤ 10 m at nadir" |
| **Interface** | Boundary agreements between elements | "The EPS shall provide a 5.0 V ± 0.25 V regulated bus to all subsystems" |
| **Constraint** | Non-negotiable external limits | "The system total mass shall not exceed 6.0 kg" |
| **Environmental** | Survival conditions | "The system shall survive launch loads of 9 g axial and 4 g lateral" |

*[Source: NASA SEH Appendix C, Table C-1; ECSS-E-ST-10-06C Sec. 5.2.2]*

### 5.2.3 Requirements versus design choices

| Requirement (WHAT) | Design choice (HOW) |
|--------------------|---------------------|
| "The system shall achieve GSD ≤ 10 m" | "Use a 150 mm aperture telescope" |
| "The system shall survive launch loads" | "Use aluminium 7075-T6 structure" |
| "The system shall provide ≥ 3 dB link margin" | "Use S-band with a 2 W transmitter" |
| "The system shall deorbit within 5 years of EOL" | "Include a cold-gas propulsion system" |
| "The system shall operate for ≥ 3 years" | "Use rad-tolerant components" |

**Key principle:** Requirements constrain the solution space without specifying the solution. This preserves design freedom for the trade studies of Chapter 4 and the architecture decisions of Chapter 8.

---

## 5.3 The SMART framework

While NASA Appendix C provides a detailed quality checklist, the SMART acronym serves as a rapid quality screen:

| Letter | Meaning | Test question |
|--------|---------|---------------|
| **S** | Specific | Does it address exactly one concern? Is it unambiguous? |
| **M** | Measurable | Does it have a numeric threshold with units? Can it be verified? |
| **A** | Achievable | Is it technically feasible with current or near-term technology? |
| **R** | Relevant | Does it trace to a stakeholder need or higher-level objective? |
| **T** | Traceable | Can you identify its parent (where it came from) and its children (how it will be verified)? |

### 5.3.1 NASA SEH Appendix C: full quality checklist

*[Source: NASA SEH Appendix C — "How to Write a Good Requirement"]*

The full NASA checklist adds criteria beyond SMART:

1. **Single requirement per statement** — no compound "and" requirements
2. **Positive form** — state what the system SHALL DO, not what it shall NOT do
3. **Active voice** — "The system shall…" not "It is required that…"
4. **No implementation** — avoid naming specific hardware, software, or methods
5. **Verifiable** — must be provable by analysis, test, inspection, review of design or demonstration
6. **No TBDs** — every threshold must have a value (even if it changes later)
7. **Consistent** — no contradictions with other requirements in the set
8. **Bounded** — tolerance or range specified where appropriate

### 5.3.2 Common anti-patterns

| Anti-pattern | Problem | Better version |
|-------------|---------|----------------|
| "The spacecraft shall operate at 500 km altitude" | Prescribes orbit (design choice) | "The system shall provide global coverage with revisit ≤ 5 days at ±60° latitude" |
| "The spacecraft shall use triple-junction GaAs solar cells" | Prescribes technology | "The EPS shall generate ≥ 15 W EOL with ≤ 0.5 m² array area" |
| "The system shall use AX.25 protocol" | Prescribes implementation | "The TTC system shall provide reliable command reception with BER ≤ $10^{-6}$" |
| "The spacecraft shall be a 3U CubeSat" | Prescribes form factor | "The system shall have total mass ≤ 6 kg and fit within a standard 3U deployer envelope" |

**Exception:** Interface requirements ARE specific because they define contractual boundaries:
> "The EPS shall provide 28 V ± 2 V regulated bus voltage to all subsystems."

This is acceptable because bus voltage is a negotiated interface agreement, not a unilateral design choice.

---

## 5.4 Requirement hierarchy and traceability

Requirements exist at multiple levels, each decomposed from the level above. Every requirement must trace bidirectionally. Figure 5.1 shows the hierarchy for an agricultural-monitoring mission.

### 5.4.1 Hierarchy structure

![Requirement hierarchy tree: stakeholder need, mission requirement MR-001, three system requirements, three subsystem requirements and the component level beneath them.](../assets/figures/fig_requirement_hierarchy.png)

**Figure 5.1** — Requirement hierarchy for an agricultural-monitoring EO mission: a stakeholder need derives a mission requirement (MR-001), which decomposes into system requirements for the payload, AOCS and link, each of which derives a subsystem requirement; the component level beneath (dashed) is where the subsystem requirements are allocated to individual parts. Every requirement traces upward to its parent and downward to its children (§5.4.3).

### 5.4.2 Level definitions

| Level | Scope | Written by | Verified by |
|-------|-------|-----------|-------------|
| **Mission** | What the mission achieves (MoE-derived) | Systems engineer and stakeholders | Operational validation |
| **System** | What the system must do (MoP-derived) | Systems engineer | System-level integration and test |
| **Subsystem** | What each subsystem must provide | Subsystem engineers | Subsystem qualification and acceptance |
| **Component** | What each component must meet | Component engineers | Component acceptance testing |

### 5.4.3 Traceability rules

Every requirement must trace in three directions:

1. **Upward:** to its parent requirement or objective (WHY does this exist?)
2. **Downward:** to child requirements or design parameters (HOW is it decomposed?)
3. **Horizontally:** to a verification method (HOW will it be confirmed?)

This three-axis traceability is captured in the **Requirements Traceability Matrix (RTM)**.

There are no equations in requirements engineering per se, but one relationship governs traceability completeness — the same metric introduced as $T_c$ in Chapter 1 §1.2.4:

$$\text{Coverage} = \frac{N_{\text{verified requirements}}}{N_{\text{total requirements}}} \times 100\%$$

Target: 100 % coverage — every requirement must have at least one assigned verification method and one parent traceability link.

*[Source: NASA SEH Sec. 6.2 (Process 11: Requirements Management); ECSS-E-ST-10C Sec. 5.2]*

### 5.4.4 Splitting compound requirements

A compound requirement that addresses multiple concerns must be split for independent verification:

| Compound (poor) | Split (correct) |
|-----------------|-----------------|
| "The system shall provide 10 m GSD with 5-day revisit and 24 h latency" | MR-001: "GSD ≤ 10 m" **+** MR-002: "Revisit ≤ 5 days" **+** MR-003: "Latency ≤ 24 h" |
| "The EPS shall provide positive power margin in all modes including eclipse" | SR-PWR-001: "Positive margin in sunlit modes" **+** SR-PWR-002: "Positive margin in eclipse" **+** SR-PWR-003: "Battery DoD ≤ 30 % in worst-case eclipse" |

**Rationale:** Each split requirement can be verified independently. If GSD passes but revisit fails, the team knows exactly what to fix without ambiguity.

---

## 5.5 Verification methods — ATIR(D)

*[Source: ECSS-E-ST-10-02C Rev.1 Sec. 5.3; NASA SEH Sec. 5.3]*

Every requirement must have an assigned verification method. ECSS-E-ST-10-02C defines four methods — analysis, test, inspection and review of design — and NASA practice adds demonstration; this book abbreviates the set as ATIR(D). Chapter 14 describes how each method is planned and executed.

| Method | Code | What it proves | When used |
|--------|------|---------------|-----------|
| **Analysis** | A | Requirement satisfied by mathematical model, simulation, or similarity | Phase B–C; when testing is impractical or cost-prohibitive |
| **Test** | T | Requirement satisfied by physical measurement | Phase C–D; when proof requires hardware in a controlled environment |
| **Inspection** | I | Requirement confirmed by visual or physical examination | Physical characteristics (dimensions, labels, markings, mass) |
| **Review of design** | R | Requirement confirmed by examination of drawings, schematics or documentation | Design features that can be established from the records (e.g., use of approved parts, redundancy present) |
| **Demonstration** | D | Requirement confirmed by operational exercise | Functional requirements proven by executing procedures |

### 5.5.1 Verification method selection guide

| Requirement type | Typical method | Rationale |
|-----------------|---------------|-----------|
| Mass ≤ X kg | **I** (weigh it) | Direct physical measurement |
| Pointing ≤ Y° | **A** (simulation) + **T** (TVAC/HITL) | Analysis first, confirmed by test |
| Link margin ≥ 3 dB | **A** (link budget analysis) | Full test requires satellite in orbit |
| Survival at launch loads | **T** (vibration test) | Must physically prove structural integrity |
| Data latency ≤ 24 h | **D** (end-to-end ops exercise) | Pipeline is procedural — demonstrate it works |
| Operating temperature range | **T** (thermal vacuum test) | Thermal environment must be simulated |
| Software FDIR logic | **D** (fault injection test) | Demonstrate correct autonomous response |
| Redundant power path present | **R** (schematic review) | Established from the design record |

### 5.5.2 Verification by project phase

| Phase | Verification activities |
|-------|------------------------|
| **B** | Analysis verification (models, simulations, budgets, trade studies) |
| **C** | Design verification (detailed analysis, breadboard testing, qualification) |
| **D** | Acceptance testing (flight hardware), system integration, environmental test |
| **E** | In-orbit validation (commissioning, calibration, operational checkout) |

---

## 5.6 Worked examples

### 5.6.1 Deriving requirements for the 3U EO CubeSat

> **Worked example — Deriving requirements for a 3U EO CubeSat**
>
> **Stakeholder need:** "Monitor crop health across the Canadian prairies with weekly updates."
>
> **Step 1 — Mission requirement:**
> MR-001: "The system shall provide NDVI-capable imagery with GSD ≤ 10 m and revisit ≤ 7 days over 49–54° N, 100–115° W."
>
> **Step 2 — System requirements (decomposed):**
> - SR-PL-001: "The payload shall acquire imagery in at least RED (630–690 nm) and NIR (760–900 nm) bands."
> - SR-AOCS-001: "The AOCS shall provide pointing accuracy ≤ 0.5° (3σ) during imaging."
> - SR-LINK-001: "The comms system shall downlink ≥ 2 GB per day to a Canadian ground station."
> - SR-PWR-001: "The EPS shall provide positive power margin in all operational modes."
>
> **Step 3 — Subsystem requirements (derived):**
> - SSR-PL-001a: "The telescope aperture shall be ≥ 80 mm." [Derived from GSD + altitude]
> - SSR-AOCS-001a: "The star tracker shall provide ≤ 30 arcsec attitude knowledge." [Derived from pointing budget]
> - SSR-LINK-001a: "The X-band transmitter shall provide ≥ 2 W RF output power." [Derived from link budget]
>
> **Step 4 — Verification assignment:**
>
> | Requirement | Method | Phase | Rationale |
> |-------------|--------|-------|-----------|
> | MR-001 (GSD + revisit) | A + D | B + E | Analysis during design; demonstrated from orbit |
> | SR-PL-001 (spectral bands) | T | D | Spectral calibration in lab |
> | SR-AOCS-001 (pointing) | A + T | B + D | Simulation then hardware-in-loop test |
> | SR-LINK-001 (downlink) | A | B | Link budget analysis |
> | SSR-PL-001a (aperture) | I | D | Physical measurement |

### 5.6.2 Returning to UniSat-1

> **Worked example — Deriving requirements for a 1U technology demonstrator**
>
> **Stakeholder need:** "Demonstrate the feasibility of a MEMS-based magnetometer for space weather monitoring in LEO."
>
> **Step 1 — Mission requirements:**
>
> | ID | Requirement | Type | Rationale |
> |----|------------|------|-----------|
> | MR-001 | "The system shall measure the local magnetic field vector with resolution ≤ 10 nT at 1 Hz sampling rate for a minimum of 6 months." | Performance | Minimum science return for technology validation |
> | MR-002 | "The system total mass shall not exceed 1.33 kg." | Constraint | CDS Rev 14, 1U mass limit |
> | MR-003 | "The system shall downlink at least 1 MB of magnetometer data per day." | Performance | Sufficient for statistical analysis of sensor performance |
> | MR-004 | "The system shall operate for a minimum of 6 months in LEO." | Performance | Minimum mission duration for seasonal variation coverage |
>
> **Step 2 — System requirements (decomposed):**
> - SR-PWR-001: "The EPS shall provide orbit-average power ≥ 2 W to all subsystems."
> - SR-PWR-002: "The battery shall provide ≥ 10 Wh capacity."
> - SR-LINK-001: "The comms system shall provide a downlink data rate ≥ 9600 bps."
> - SR-LINK-002: "The comms system shall achieve link margin ≥ 3 dB at 10° minimum elevation."
> - SR-OBC-001: "The OBC shall consume ≤ 0.5 W average power."
> - SR-STR-001: "The structure shall comply with CDS Rev 14, 1U envelope (100 × 100 × 113.5 mm)."
>
> **Step 3 — Subsystem requirements (derived):**
> - SSR-PWR-001a: "Body-mounted solar cells shall generate ≥ 2 W orbit-average power accounting for eclipse and geometry." [Derived from power budget]
> - SSR-LINK-001a: "The UHF transmitter shall provide ≥ 0.5 W RF output at 437 MHz." [Derived from link budget]
>
> **Step 4 — Verification assignment:**
>
> | Requirement | Method | Phase | Rationale |
> |-------------|--------|-------|-----------|
> | MR-001 (magnetometer performance) | T + D | D + E | Ground calibration then in-orbit demonstration |
> | MR-002 (mass ≤ 1.33 kg) | I | D | Weigh the flight unit |
> | SR-PWR-001 (orbit-average power) | A | B | Power budget analysis |
> | SR-LINK-001 (9600 bps downlink) | A + D | B + E | Link budget analysis; demonstrated from orbit |
> | SR-STR-001 (CDS compliance) | I | D | Physical measurement against CDS template |
>
> **Key difference from 3U:** The 1U requirement set is much smaller (~15–20 requirements vs ~40–60 for a 3U EO mission). There are no pointing requirements, no imaging requirements, and no propulsion requirements. This makes the verification campaign significantly simpler and cheaper.

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| System-V model | Left branch decomposes requirements; right branch integrates and verifies at matching levels (Figure 1.1) |
| Shall statements | Formal, verifiable, single-concern statements |
| WHAT not HOW | Requirements preserve design freedom; design choices come later in trade studies |
| SMART | Specific, Measurable, Achievable, Relevant, Traceable |
| Requirement types | Functional, performance, interface, constraint, environmental |
| Hierarchy | Mission → System → Subsystem with bidirectional traceability (up, down, horizontal) |
| Splitting | One concern per requirement for independent verification |
| ATIR(D) | Analysis, Test, Inspection, Review of design (+ Demonstration) — assigned per requirement per phase |

---

## Problems

1. **WHAT, not HOW.** Each of the following statements prescribes an implementation. Rewrite each as a requirement that preserves design freedom, and state what stakeholder need or higher-level requirement it should trace to. (a) "The spacecraft shall use a deployable UHF tape-measure antenna." (b) "The payload shall be mounted on the +Z face." (c) "The OBC shall run FreeRTOS." (d) "The spacecraft shall carry four reaction wheels."

2. **Splitting compound requirements.** Split each of the following into single-concern requirements with identifiers, and explain for one of them what ambiguity would arise if the compound form failed verification. (a) "The ground segment shall receive, process and distribute imagery within 6 h of acquisition with 99 % availability." (b) "The thermal control subsystem shall keep the battery between 0 °C and 40 °C and the payload detector below −10 °C during imaging."

3. **Classification.** Classify each of the following as functional, performance, interface, constraint or environmental, and justify the classification: (a) "The spacecraft shall survive a total ionising dose of 10 krad(Si)." (b) "The spacecraft shall transmit housekeeping telemetry." (c) "The payload shall deliver image data to the OBC over SpaceWire at 100 Mbps." (d) "The spacecraft shall be delivered for launch no later than 24 months after contract signature." (e) "The AOCS shall settle to within 0.1° of the commanded attitude within 60 s of a 30° slew." (f) "The spacecraft total mass shall not exceed 4.0 kg."

4. **Verification assignment.** For a 3U EO CubeSat with a 90 mm aperture multispectral imager and an S-band downlink, write five requirements — one at mission level, two at system level and two at subsystem level — and assign to each a verification method (A, T, I, R or D) and a target phase (B, C, D or E). Justify every choice in one sentence, following the format of §5.6.1 Step 4.

5. **A hierarchy from a new need.** A coastal authority states the need: "Know, within one hour, the position of every vessel over 300 tonnes within 200 nautical miles of the coast." Derive one mission requirement, at least three system requirements (covering payload, communications and power) and at least two subsystem requirements, with identifiers and explicit parent links. Which of your requirements are performance and which are functional?

6. **SMART audit.** Each of the following requirements fails at least one SMART criterion or one item of the NASA checklist of §5.3.1. Identify the failure and rewrite the requirement. (a) "The spacecraft shall have good pointing performance." (b) "The link margin shall be TBD dB." (c) "The spacecraft shall not fail." (d) "It is required that the imaging mode be entered." (e) "The system shall provide 5 m GSD and 10 bands and daily revisit."

7. **Coverage metric.** A requirement set contains 52 requirements. 44 have an assigned verification method; 49 have a parent traceability link; 41 have both. Compute the coverage as defined in §5.4.3 and state whether the set meets the target. Which requirements should the systems engineer examine first, and why?

8. **Deriving a subsystem requirement from a mission requirement.** Returning to UniSat-1, mission requirement MR-003 demands at least 1 MB of magnetometer data per day and SR-LINK-001 provides 9600 bps. (a) Compute the minimum total daily contact time required, assuming the link is used at 100 % efficiency. (b) Repeat assuming 60 % protocol efficiency and that only half of each pass is usable at ≥ 10° elevation. (c) Write the resulting derived requirement on the ground segment (minimum contact minutes per day), with its parent link and verification method.

9. **Interface requirements.** Explain why "The EPS shall provide 28 V ± 2 V regulated bus voltage to all subsystems" is an acceptable requirement even though it specifies a number that looks like a design choice. Write two further interface requirements for the 3U EO CubeSat — one data interface between payload and OBC and one mechanical interface between the spacecraft and its deployer — and identify which positions in Table 1.4 must agree each one.

10. **Right-sizing the requirement set.** The worked examples suggest ~15–20 requirements for a 1U demonstrator and ~40–60 for a 3U EO mission. For each of the following changes to UniSat-1, state which new requirements (type and level) would be needed and estimate how many: (a) adding a 1-axis magnetorquer for passive-to-active detumbling; (b) adding a second, redundant magnetometer; (c) extending the design lifetime from 6 months to 2 years.

---

## References

1. NASA, *Systems Engineering Handbook* (NASA/SP-2016-6105 Rev 2), 2016, Ch. 4.2 and Appendix C. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
2. ECSS, *ECSS-E-ST-10-06C: Technical Requirements Specification*, 2009, Sec. 5. [https://ecss.nl/standard/ecss-e-st-10-06c-technical-requirements-specification/](https://ecss.nl/standard/ecss-e-st-10-06c-technical-requirements-specification/)
3. ECSS, *ECSS-E-ST-10C Rev.1: Space Engineering — System Engineering General Requirements*, 2017, Sec. 5.2. [https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/](https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/)
4. ECSS, *ECSS-E-ST-10-02C Rev.1: Space Engineering — Verification*, 2018, Sec. 5.3. [https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification-1-february-2018/](https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification-1-february-2018/)
5. Wertz, J.R., Everett, D.F. and Puschell, J.J., *Space Mission Engineering: The New SMAD*, Microcosm Press, 2011, Ch. 3–4. [https://www.microcosminc.com/](https://www.microcosminc.com/)
6. INCOSE, *Systems Engineering Handbook*, 5th ed., 2023, Ch. 2.3.5. [https://www.incose.org/products-and-publications/se-handbook](https://www.incose.org/products-and-publications/se-handbook)
