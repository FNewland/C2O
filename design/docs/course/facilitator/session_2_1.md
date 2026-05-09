# Session 2.1: The System-V and Requirements Engineering

**Duration:** 2 hours
**Prerequisites:** Week 1 complete (mission need, stakeholder analysis, ConOps defined)
**SpaceCDF Tab:** Requirements

---

## References

- [NASA, *Systems Engineering Handbook* (NASA/SP-2016-6105 Rev 2), 2016, Ch. 4.2 & Appendix C](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [ECSS, *ECSS-E-ST-10-06C: Technical Requirements Specification*, 2009, Sec. 5](https://ecss.nl/standard/ecss-e-st-10-06c-technical-requirements-specification/)
- [ECSS, *ECSS-E-ST-10C Rev.1: Space Engineering -- System Engineering General Requirements*, 2017, Sec. 5.2](https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/)
- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 3--4](https://www.space.com/smad)
- [INCOSE, *Systems Engineering Handbook*, 5th ed., 2023, Ch. 2.3.5](https://www.incose.org/products-and-publications/se-handbook)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Explain the System-V lifecycle model and how requirements flow down the left side while verification flows up the right side
2. Write requirements that satisfy the SMART criteria and express WHAT, not HOW
3. Classify requirements by type: functional, performance, interface, constraint, and environmental
4. Construct a three-level requirement hierarchy (mission, system, subsystem) with bidirectional traceability
5. Assign verification methods (ATID) to requirements and justify each choice
6. Use SpaceCDF's Requirements tab to generate, validate, and manage requirements

---

## 1. The System-V Model (20 min)

### Teaching Notes

The **System-V** (or "Vee model") is the canonical systems engineering lifecycle. It connects the decomposition of requirements on the left branch to the integration and verification on the right branch. Every horizontal level on the V represents a matched pair: requirements at that level are verified by the corresponding test or analysis campaign at the same level on the right side.

*[Source: NASA SEH Fig. 3-1; ECSS-E-ST-10C Rev.1 Fig. 5-1; INCOSE SEH 5th ed. Fig. 2.7]*

### The V-Model Structure

<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 12px;">
  <!-- V shape -->
  <line x1="100" y1="60" x2="400" y2="400" stroke="#2563eb" stroke-width="3"/>
  <line x1="400" y1="400" x2="700" y2="60" stroke="#16a34a" stroke-width="3"/>
  <!-- Horizontal dashed lines -->
  <line x1="100" y1="60" x2="700" y2="60" stroke="#94a3b8" stroke-width="1" stroke-dasharray="6,4"/>
  <line x1="175" y1="130" x2="625" y2="130" stroke="#94a3b8" stroke-width="1" stroke-dasharray="6,4"/>
  <line x1="250" y1="210" x2="550" y2="210" stroke="#94a3b8" stroke-width="1" stroke-dasharray="6,4"/>
  <line x1="325" y1="290" x2="475" y2="290" stroke="#94a3b8" stroke-width="1" stroke-dasharray="6,4"/>
  <!-- Left labels (Requirements) -->
  <text x="40" y="55" fill="#2563eb" font-weight="bold">Stakeholder Needs</text>
  <text x="90" y="125" fill="#2563eb" font-weight="bold">Mission Requirements</text>
  <text x="155" y="205" fill="#2563eb" font-weight="bold">System Requirements</text>
  <text x="220" y="285" fill="#2563eb" font-weight="bold">Subsystem Requirements</text>
  <text x="340" y="420" fill="#7c3aed" font-weight="bold">Implementation</text>
  <!-- Right labels (Verification) -->
  <text x="605" y="55" fill="#16a34a" font-weight="bold">Validation</text>
  <text x="545" y="125" fill="#16a34a" font-weight="bold">Mission V&V</text>
  <text x="480" y="205" fill="#16a34a" font-weight="bold">System Integration</text>
  <text x="415" y="285" fill="#16a34a" font-weight="bold">Subsystem Test</text>
  <!-- Arrows -->
  <text x="370" y="45" fill="#94a3b8" font-size="11">Verification matches decomposition level</text>
  <!-- Branch labels -->
  <text x="150" y="370" fill="#2563eb" font-size="13" font-weight="bold">Decomposition</text>
  <text x="540" y="370" fill="#16a34a" font-size="13" font-weight="bold">Integration</text>
</svg>

**Key insight:** The V is not a timeline -- it is a *correspondence map*. The left branch asks "what must be done?" at increasing levels of detail. The right branch asks "did we do it?" at corresponding levels. Each horizontal row is a matched pair.

### Phase Mapping to the V

| V-Level | Left Branch (Decomposition) | Right Branch (Verification) | NASA Phase |
|---------|---------------------------|---------------------------|------------|
| Top | Stakeholder needs & objectives | Operational validation (does the mission deliver value?) | Pre-A / E |
| Mission | Mission-level requirements | Mission-level V&V (commissioning, in-orbit checkout) | A / E |
| System | System-level requirements | System integration & test (end-to-end) | B / D |
| Subsystem | Subsystem requirements | Subsystem qualification & acceptance test | C / D |
| Bottom | Implementation (detailed design, build) | Component acceptance | C-D |

### Real Mission Example: Planet SuperDove

Planet's SuperDove constellation (2020--present) illustrates the V-model in commercial practice:

| Level | Requirement (Left) | Verification (Right) |
|-------|-------------------|---------------------|
| Stakeholder | "Daily global coverage at <5 m for agricultural analytics" | In-orbit validation: coverage maps, user feedback |
| Mission | "Revisit <= 1 day at +-60deg latitude" | Constellation coverage simulation confirmed |
| System | "GSD <= 3.7 m at 475 km SSO" | End-to-end imaging test from orbit |
| Subsystem | "Telescope aperture >= 90 mm, 8 spectral bands" | Instrument calibration on ground + in-orbit |

*[Source: Planet Labs, "Planet Imagery Product Specifications," 2023]*

---

## 2. What is a Requirement? (15 min)

### Teaching Notes

*[Source: NASA SEH Sec. 4.2; ECSS-E-ST-10-06C Sec. 5.2]*

A requirement is a **formal, verifiable statement of what the system must do or how well it must perform**. It is expressed as a "shall" statement with a measurable threshold.

### The Shall Convention

Requirements use contractually precise language:

| Keyword | Meaning | Contractual Force |
|---------|---------|-------------------|
| **"Shall"** | Mandatory requirement -- must be met | Binding |
| **"Should"** | Goal or guideline -- desired but not mandatory | Advisory |
| **"Will"** | Statement of fact or intent -- not a requirement | Informational |

**Example:**
> "The system **shall** achieve a ground sample distance of 10 m or better at nadir from the operational orbit."

This is testable: GSD can be computed from optical geometry and verified from calibration imagery.

### Requirement Types

| Type | Definition | Example |
|------|-----------|---------|
| **Functional** | What the system must *do* (a capability) | "The system shall acquire multispectral imagery of the target area" |
| **Performance** | How *well* it must do it (quantified) | "The system shall achieve GSD <= 10 m at nadir" |
| **Interface** | Boundary agreements between elements | "The EPS shall provide 5.0 V +/- 0.25 V regulated bus to all subsystems" |
| **Constraint** | Non-negotiable external limits | "The system total mass shall not exceed 6.0 kg" |
| **Environmental** | Survival conditions | "The system shall survive launch loads of 9 g axial and 4 g lateral" |

*[Source: NASA SEH Appendix C, Table C-1; ECSS-E-ST-10-06C Sec. 5.2.2]*

### Requirements vs. Design Choices

| Requirement (WHAT) | Design Choice (HOW) |
|--------------------|---------------------|
| "The system shall achieve GSD <= 10 m" | "Use a 150 mm aperture telescope" |
| "The system shall survive launch loads" | "Use aluminium 7075-T6 structure" |
| "The system shall provide >= 3 dB link margin" | "Use S-band with 2 W transmitter" |
| "The system shall deorbit within 5 years of EOL" | "Include cold gas propulsion system" |
| "The system shall operate for >= 3 years" | "Use rad-tolerant components" |

**Key principle:** Requirements constrain the solution space without specifying the solution. This preserves design freedom for trade studies.

---

## 3. The SMART Framework (20 min)

### Teaching Notes

While NASA Appendix C provides a detailed quality checklist, the SMART acronym serves as a rapid quality screen:

| Letter | Meaning | Test Question |
|--------|---------|---------------|
| **S** | Specific | Does it address exactly one concern? Is it unambiguous? |
| **M** | Measurable | Does it have a numeric threshold with units? Can it be verified? |
| **A** | Achievable | Is it technically feasible with current or near-term technology? |
| **R** | Relevant | Does it trace to a stakeholder need or higher-level objective? |
| **T** | Traceable | Can you identify its parent (where it came from) and its children (how it will be verified)? |

### NASA SEH Appendix C: Full Quality Checklist

*[Source: NASA SEH Appendix C -- "How to Write a Good Requirement"]*

The full NASA checklist adds criteria beyond SMART:

1. **Single requirement per statement** -- no compound "and" requirements
2. **Positive form** -- state what the system SHALL DO, not what it shall NOT do
3. **Active voice** -- "The system shall..." not "It is required that..."
4. **No implementation** -- avoid naming specific hardware, software, or methods
5. **Verifiable** -- must be provable by analysis, test, inspection, or demonstration
6. **No TBDs** -- every threshold must have a value (even if it changes later)
7. **Consistent** -- no contradictions with other requirements in the set
8. **Bounded** -- tolerance or range specified where appropriate

### Common Anti-Patterns

| Anti-Pattern | Problem | Better Version |
|-------------|---------|----------------|
| "The spacecraft shall operate at 500 km altitude" | Prescribes orbit (design choice) | "The system shall provide global coverage with revisit <= 5 days at +/-60 deg latitude" |
| "The spacecraft shall use triple-junction GaAs solar cells" | Prescribes technology | "The EPS shall generate >= 15 W EOL with <= 0.5 m^2 array area" |
| "The system shall use AX.25 protocol" | Prescribes implementation | "The TTC system shall provide reliable command reception with BER <= $10^{-6}$" |
| "The spacecraft shall be a 3U CubeSat" | Prescribes form factor | "The system shall have total mass <= 6 kg and fit within a standard 3U deployer envelope" |

**Exception:** Interface requirements ARE specific because they define contractual boundaries:
> "The EPS shall provide 28 V +/- 2 V regulated bus voltage to all subsystems."

This is acceptable because bus voltage is a negotiated interface agreement, not a unilateral design choice.

---

## 4. Requirement Hierarchy and Traceability (25 min)

### Teaching Notes

Requirements exist at multiple levels, each decomposed from the level above. Every requirement must trace bidirectionally.

### Hierarchy Structure

```
Stakeholder Need: "Timely agricultural monitoring for food security"
  |
  v derives
Mission Requirement (MR):
  MR-001: "The system shall provide multispectral imagery with
           GSD <= 10 m and revisit <= 5 days over target region"
  |
  v decomposes into
System Requirements (SR):
  SR-PL-001:   "The payload shall achieve GSD <= 10 m at nadir
                from the operational orbit"
  SR-AOCS-001: "The AOCS shall provide pointing accuracy <= 0.1 deg
                (3-sigma) during imaging"
  SR-LINK-001: "The comms system shall downlink >= 5 GB/day"
  |
  v derives
Subsystem Requirements (SSR):
  SSR-PL-001a:   "The telescope aperture shall be >= 80 mm"
  SSR-AOCS-001a: "The star tracker shall provide <= 5 arcsec
                  attitude knowledge (3-sigma)"
  SSR-LINK-001a: "The X-band transmitter shall provide >= 2 W RF power"
```

### Level Definitions

| Level | Scope | Written By | Verified By |
|-------|-------|-----------|-------------|
| **Mission** | What the mission achieves (MoE-derived) | Systems engineer + stakeholders | Operational validation |
| **System** | What the system must do (MoP-derived) | Systems engineer | System-level integration & test |
| **Subsystem** | What each subsystem must provide | Subsystem engineers | Subsystem qualification & acceptance |
| **Component** | What each component must meet | Component engineers | Component acceptance testing |

### Traceability Rules

Every requirement must trace in three directions:

1. **Upward:** to its parent requirement or objective (WHY does this exist?)
2. **Downward:** to child requirements or design parameters (HOW is it decomposed?)
3. **Horizontally:** to a verification method (HOW will it be confirmed?)

This three-axis traceability is captured in the **Requirements Traceability Matrix (RTM)**.

*[Source: NASA SEH Sec. 6.2 (Process 11: Requirements Management); ECSS-E-ST-10C Sec. 5.2]*

### Splitting Compound Requirements

A compound requirement that addresses multiple concerns must be split for independent verification:

| Compound (Poor) | Split (Correct) |
|-----------------|-----------------|
| "The system shall provide 10 m GSD with 5-day revisit and 24 h latency" | MR-001: "GSD <= 10 m" **+** MR-002: "Revisit <= 5 days" **+** MR-003: "Latency <= 24 h" |
| "The EPS shall provide positive power margin in all modes including eclipse" | SR-PWR-001: "Positive margin in sunlit modes" **+** SR-PWR-002: "Positive margin in eclipse" **+** SR-PWR-003: "Battery DOD <= 30% in worst-case eclipse" |

**Rationale:** Each split requirement can be verified independently. If GSD passes but revisit fails, the team knows exactly what to fix without ambiguity.

---

## 5. Verification Methods -- ATID (20 min)

### Teaching Notes

*[Source: ECSS-E-ST-10-02C Rev.1 Sec. 5.3; NASA SEH Sec. 5.3]*

Every requirement must have an assigned verification method. The four standard methods (sometimes called ATRI or ATID) are:

| Method | Code | What It Proves | When Used |
|--------|------|---------------|-----------|
| **Analysis** | A | Requirement satisfied by mathematical model, simulation, or similarity | Phase B--C; when testing is impractical or cost-prohibitive |
| **Test** | T | Requirement satisfied by physical measurement | Phase C--D; when proof requires hardware in a controlled environment |
| **Inspection** | I | Requirement confirmed by visual or physical examination | Physical characteristics (dimensions, labels, markings, mass) |
| **Demonstration** | D | Requirement confirmed by operational exercise | Functional requirements proven by executing procedures |

### Verification Method Selection Guide

| Requirement Type | Typical Method | Rationale |
|-----------------|---------------|-----------|
| Mass <= X kg | **I** (weigh it) | Direct physical measurement |
| Pointing <= Y deg | **A** (simulation) + **T** (TVAC/HITL) | Analysis first, confirmed by test |
| Link margin >= 3 dB | **A** (link budget analysis) | Full test requires satellite in orbit |
| Survival at launch loads | **T** (vibration test) | Must physically prove structural integrity |
| Data latency <= 24 h | **D** (end-to-end ops exercise) | Pipeline is procedural -- demonstrate it works |
| Operating temperature range | **T** (thermal vacuum test) | Thermal environment must be simulated |
| Software FDIR logic | **D** (fault injection test) | Demonstrate correct autonomous response |

### Verification by Project Phase

| Phase | Verification Activities |
|-------|------------------------|
| **B** | Analysis verification (models, simulations, budgets, trade studies) |
| **C** | Design verification (detailed analysis, breadboard testing, qualification) |
| **D** | Acceptance testing (flight hardware), system integration, environmental test |
| **E** | In-orbit validation (commissioning, calibration, operational checkout) |

---

## 6. Worked Example: 3U Earth Observation CubeSat (10 min)

> **Worked Example -- Deriving Requirements for a 3U EO CubeSat**
>
> **Stakeholder need:** "Monitor crop health across the Canadian prairies with weekly updates."
>
> **Step 1 -- Mission requirement:**
> MR-001: "The system shall provide NDVI-capable imagery with GSD <= 10 m and revisit <= 7 days over 49--54 deg N, 100--115 deg W."
>
> **Step 2 -- System requirements (decomposed):**
> - SR-PL-001: "The payload shall acquire imagery in at least RED (630--690 nm) and NIR (760--900 nm) bands."
> - SR-AOCS-001: "The AOCS shall provide pointing accuracy <= 0.5 deg (3-sigma) during imaging."
> - SR-LINK-001: "The comms system shall downlink >= 2 GB per day to a Canadian ground station."
> - SR-PWR-001: "The EPS shall provide positive power margin in all operational modes."
>
> **Step 3 -- Subsystem requirements (derived):**
> - SSR-PL-001a: "The telescope aperture shall be >= 80 mm." [Derived from GSD + altitude]
> - SSR-AOCS-001a: "The star tracker shall provide <= 30 arcsec attitude knowledge." [Derived from pointing budget]
> - SSR-LINK-001a: "The X-band transmitter shall provide >= 2 W RF output power." [Derived from link budget]
>
> **Step 4 -- Verification assignment:**
>
> | Requirement | Method | Phase | Rationale |
> |-------------|--------|-------|-----------|
> | MR-001 (GSD + revisit) | A + D | B + E | Analysis during design; demonstrated from orbit |
> | SR-PL-001 (spectral bands) | T | D | Spectral calibration in lab |
> | SR-AOCS-001 (pointing) | A + T | B + D | Simulation then hardware-in-loop test |
> | SR-LINK-001 (downlink) | A | B | Link budget analysis |
> | SSR-PL-001a (aperture) | I | D | Physical measurement |

---

## 7. SpaceCDF Exercise (30 min)

### Instructions

1. Navigate to the **Requirements** tab in SpaceCDF
2. Click **"Generate from Objectives"** -- the AI agent generates SMART requirements from your mission objectives and ConOps
3. For each generated requirement:
   - Review the SMART validation badges (green = pass, amber = warning, red = fail)
   - Check: does it say WHAT not HOW? Is it a single concern?
   - **Accept**, **Edit**, or **Reject** each one
4. Use the **Level filter** (Mission / System / Subsystem) to view by hierarchy level
5. Use the **Type filter** (Functional / Performance / Interface / Constraint) to classify
6. Navigate to the **V&V Matrix** sub-panel to assign verification methods (A/T/I/D) to each accepted requirement

### Exercise Tasks

1. Generate requirements for your team's mission
2. Identify at least one requirement that specifies HOW (implementation) -- rewrite it as WHAT
3. Split any compound requirements into individual testable statements
4. Classify 5 requirements by type (functional, performance, interface, constraint, environmental)
5. For 5 key requirements, assign verification method (A/T/I/D) and target phase (B/C/D/E)
6. Complete Worksheet 2.1

---

## Key Equations Reference

> **There are no equations in requirements engineering per se**, but the following relationship governs traceability completeness:
>
> $$\text{Coverage} = \frac{N_{\text{verified requirements}}}{N_{\text{total requirements}}} \times 100\%$$
>
> Target: 100% coverage -- every requirement must have at least one assigned verification method and one parent traceability link.

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| System-V model | Left branch decomposes requirements; right branch integrates and verifies at matching levels |
| Shall statements | Formal, verifiable, single-concern statements |
| WHAT not HOW | Requirements preserve design freedom; design choices come later in trade studies |
| SMART | Specific, Measurable, Achievable, Relevant, Traceable |
| Requirement types | Functional, performance, interface, constraint, environmental |
| Hierarchy | Mission -> System -> Subsystem with bidirectional traceability (up, down, horizontal) |
| Splitting | One concern per requirement for independent verification |
| ATID | Analysis, Test, Inspection, Demonstration -- assigned per requirement per phase |
