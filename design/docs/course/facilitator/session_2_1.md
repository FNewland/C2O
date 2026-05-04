# Session 2.1: Requirements Engineering

**Duration:** 2 hours
**Prerequisites:** Day 1 complete (mission need, trade, ConOps defined)
**References:** NASA SEH §4.2 (Process 2), Appendix C; ECSS-E-ST-10-06C §5; ECSS-E-ST-10C §5.2

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Write requirements that are SMART and express WHAT not HOW
2. Distinguish between mission, system, and subsystem level requirements
3. Apply NASA SEH Appendix C quality checklist to requirements
4. Generate and validate requirements using SpaceCDF
5. Trace requirements bidirectionally (up to objectives, down to verification)

---

## 1. What is a Requirement? (15 min)

### Teaching Notes

*[Source: NASA SEH §4.2; ECSS-E-ST-10-06C §5.2]*

A requirement is a **formal statement of what the system must do or how well it must perform**, expressed as a "shall" statement that is verifiable.

### The "Shall" Convention

Requirements use specific language:
- **"Shall"** = mandatory requirement (must be met)
- **"Should"** = desired but not mandatory (goal/guideline)
- **"Will"** = statement of fact or intent (not a requirement)

**Example:**
> "The system **shall** achieve a ground sample distance of 10 m or better at nadir."

This is testable: you can measure GSD from calibration imagery and verify it meets the threshold.

### Requirements vs Design Choices

| Requirement (WHAT) | Design Choice (HOW) |
|--------------------|--------------------|
| "The system shall achieve GSD ≤ 10 m" | "Use a 15 cm aperture telescope" |
| "The system shall survive launch loads" | "Use aluminium 7075-T6 structure" |
| "The system shall provide ≥ 3 dB link margin" | "Use S-band with 2W transmitter" |
| "The system shall deorbit within 5 years of EOL" | "Include cold gas propulsion system" |
| "The system shall operate for ≥ 3 years" | "Use rad-tolerant components" |

**Key principle:** Requirements constrain the solution space without specifying the solution. This preserves design freedom for trade studies.

*[Source: NASA SEH Appendix C — "Requirements should state WHAT is needed, not HOW to provide it"]*

---

## 2. The SMART Framework (20 min)

### Teaching Notes

While NASA's Appendix C uses a detailed checklist, the SMART acronym provides a useful mnemonic:

| Letter | Meaning | Test Question |
|--------|---------|--------------|
| **S** | Specific | Does it address one thing only? Is it unambiguous? |
| **M** | Measurable | Does it have a numeric threshold with units? Can it be tested? |
| **A** | Achievable | Is it technically feasible with current or near-term technology? |
| **R** | Relevant | Does it trace to a stakeholder need or objective? |
| **T** | Traceable | Can you identify where it came from (parent) and how it will be verified (child)? |

### NASA SEH Appendix C: Full Checklist

*[Source: NASA SEH Appendix C — How to Write a Good Requirement]*

The NASA checklist adds additional criteria:

1. **Single requirement per statement** — no compound "and" requirements
2. **Positive form** — state what the system shall DO, not what it shall NOT do
3. **Active voice** — "The system shall..." not "It is required that..."
4. **No implementation** — avoid naming specific hardware, software, or methods
5. **Verifiable** — must be provable by analysis, test, inspection, or demonstration
6. **No TBDs** — every threshold must have a value (even if it changes later)
7. **Consistent** — no contradictions with other requirements
8. **Bounded** — tolerance or range specified where appropriate

### Common Anti-Patterns (HOW not WHAT)

These fail the SMART test because they specify implementation:

| Anti-Pattern | Problem | Better Version |
|-------------|---------|----------------|
| "The spacecraft shall operate at 500 km altitude" | Prescribes orbit — that's a design choice | "The system shall provide global coverage with ≤ 5 day revisit at ±60° latitude" |
| "The spacecraft shall use triple-junction GaAs solar cells" | Prescribes technology | "The EPS shall generate ≥ 15 W EOL with ≤ 0.5 m² array area" |
| "The system shall use AX.25 protocol" | Prescribes implementation | "The TTC system shall provide reliable command reception with BER ≤ 10⁻⁵" |
| "The spacecraft shall be a 3U CubeSat" | Prescribes form factor | "The system shall have total mass ≤ 6 kg and fit within ISIPOD 3U envelope" |

**Exception:** Interface requirements ARE specific because they define boundaries between systems:
> "The EPS shall provide 28V ± 2V regulated bus voltage to all subsystems"

This is acceptable because bus voltage is an agreed interface, not a design choice.

**Exercise:** *Participants evaluate 5 sample requirements using the SMART checklist and Appendix C criteria. Mark which fail and rewrite them.*

---

## 3. Requirement Hierarchy (25 min)

### Teaching Notes

Requirements exist at multiple levels of the system hierarchy, each decomposing and deriving from the level above:

### Hierarchy Structure

```
Stakeholder Need: "Timely agricultural monitoring for food security"
   ↓ derives
Mission Requirement (MR): "The system shall provide multispectral 
   imagery with GSD ≤ 10m and revisit ≤ 5 days over target region"
   ↓ decomposes into
System Requirements (SR):
   SR-PL-001: "The payload shall achieve GSD ≤ 10m at nadir from operational orbit"
   SR-AOCS-001: "The AOCS shall provide pointing accuracy ≤ 0.1°"
   SR-LINK-001: "The comms system shall downlink ≥ 5 GB/day"
   ↓ derives
Subsystem Requirements (SSR):
   SSR-PL-001a: "The telescope aperture shall be ≥ 8 cm"
   SSR-AOCS-001a: "The star tracker shall provide ≤ 5 arcsec accuracy"
   SSR-LINK-001a: "The X-band TX shall provide ≥ 2W RF power"
```

### Level Definitions

| Level | Scope | Written By | Verified By |
|-------|-------|-----------|-------------|
| **Mission** | What the mission achieves (MoE-derived) | Systems engineer + stakeholders | Validation against user needs |
| **System** | What the system must do (MoP-derived) | Systems engineer | System-level V&V |
| **Subsystem** | What each subsystem must provide | Subsystem engineers | Subsystem testing |
| **Component** | What each component must meet | Component engineers | Component acceptance |

### Traceability

Every requirement must trace:
- **Upward**: to its parent requirement or objective (WHY does this exist?)
- **Downward**: to derived requirements or design parameters (HOW is it decomposed?)
- **Horizontally**: to a verification method (HOW will it be confirmed?)

This is captured in the **Requirements Traceability Matrix (RTM)**.

*[Source: NASA SEH §6.2 (Process 11: Requirements Management); ECSS-E-ST-10C §5.2]*

### Splitting Compound Requirements

A requirement addressing multiple concerns must be split for independent management and testing:

| Compound (bad) | Split (good) |
|----------------|-------------|
| "The system shall provide 10m GSD with 5-day revisit and 24h latency" | MR-001: "GSD ≤ 10m" + MR-002: "Revisit ≤ 5 days" + MR-003: "Latency ≤ 24h" |
| "The EPS shall provide positive power margin in all modes including eclipse" | SR-PWR-001: "Positive margin in sunlight" + SR-PWR-002: "Positive margin in eclipse" + SR-PWR-003: "Battery DoD ≤ 30% in worst-case eclipse" |

**Rationale:** Each split requirement can be verified independently. If GSD passes but revisit fails, you know exactly what to fix.

---

## 4. Verification Methods (ATRI) (20 min)

### Teaching Notes

*[Source: ECSS-E-ST-10-02C Rev.1 §5.3; NASA SEH §5.3]*

Every requirement must have an assigned verification method. The four standard methods are:

| Method | Code | What It Proves | When Used |
|--------|------|---------------|-----------|
| **Analysis** | A | Requirement met by mathematical model or simulation | Early phases (B-C); for things difficult/expensive to test |
| **Test** | T | Requirement met by physical testing | Phase C-D; for things that must be proven in hardware |
| **Review of Design** | R | Requirement met by design inspection | Documents, processes, management requirements |
| **Inspection** | I | Requirement met by visual/physical examination | Physical characteristics (dimensions, labels, markings) |

### Choosing the Right Method

| Requirement Type | Typical Method | Rationale |
|-----------------|---------------|-----------|
| Mass ≤ X kg | I (weigh it) | Direct measurement |
| Pointing ≤ Y° | A (simulation) + T (TVAC pointing test) | Both: analysis first, confirmed by test |
| Link margin ≥ 3 dB | A (link budget) | Test would require satellite in orbit |
| Survival at launch loads | T (vibration test) | Must physically prove structural integrity |
| Data latency ≤ 24h | R (ops concept review) | End-to-end pipeline is procedural |
| Operating temp range | T (TVAC) | Thermal environment must be simulated |

### Verification Phase

| Phase | What's Verified |
|-------|----------------|
| Phase B | Analysis verification (models, simulations, trade studies) |
| Phase C | Qualification testing (environmental, functional) |
| Phase D | Acceptance testing (flight hardware), system-level integration |
| Phase E | In-orbit validation (confirm requirements met in actual operations) |

---

## 5. SpaceCDF Requirements Tool (40 min)

### Instructions

1. Navigate to the **Requirements** tab
2. Click **"Generate from Objectives"** — the tool generates SMART requirements from your mission objectives
3. For each generated requirement:
   - Review the SMART validation badges (green = pass, amber = warning, red = fail)
   - Check: does it say WHAT not HOW?
   - **Accept**, **Edit**, or **Reject** each one
4. Use the **Level filter** (Mission / System / Subsystem) to view by hierarchy
5. Navigate to the **V&V Matrix** tab to assign verification methods

### Exercise

1. Generate requirements for your team's mission
2. Identify at least one requirement that specifies HOW (implementation) — rewrite it as WHAT
3. Split any compound requirements into individual testable statements
4. For 5 key requirements, assign verification method (A/T/R/I) and phase (B/C/D)
5. Complete Worksheet 2.1

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Shall statements | Formal, verifiable, single-concern |
| WHAT not HOW | Requirements preserve design freedom; design choices come later |
| SMART | Specific, Measurable, Achievable, Relevant, Traceable |
| Hierarchy | Mission → System → Subsystem with bidirectional traceability |
| Splitting | One concern per requirement for independent verification |
| ATRI | Analysis, Test, Review, Inspection — assigned per requirement |
