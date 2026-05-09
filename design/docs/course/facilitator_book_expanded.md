---
title: "SpaceCDF Facilitator's Book"
subtitle: "Teaching reference for the 40-hour Concurrent Design Facility intensive"
course-codes: "SpaceCDF"
term: "2026"
version: "v3 — 2026-05-09"
language: en
brand: uottawa-horizon
publisher: "Faculty of Engineering · School of Engineering Design and Teaching Innovation (SEDTI)"
footer-en: "SpaceCDF Facilitator's Book · 2026"
running: "SpaceCDF — Facilitator's Book"
---

# Facilitator's Book

## How to use this book

The Facilitator's Book is the teaching reference for the SpaceCDF 40-hour intensive. Each session in the *Course Plan* has a chapter here, with deep technical content, equations, worked examples, cited references, and SVG diagrams. The book is written so an instructor can lift it page-by-page into a session, while still leaving room for cohort-specific judgement.

The book is paired with the *Learner's Workbook*, which carries the worksheets the cohort fills in.

> **Key references used throughout:**
> - [NASA Systems Engineering Handbook Rev 2](https://www.nasa.gov/reference/systems-engineering-handbook/)
> - [NPR 7123.1D — SE Processes and Requirements](https://nodis3.gsfc.nasa.gov/)
> - [ECSS-E-ST-10C Rev.1 — System Engineering General Requirements](https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements-15-february-2017/)
> - [SMAD 4th Edition (Wertz, Everett, Puschell)](https://www.amazon.com/Space-Mission-Engineering-Microcosm-Inc/dp/1881883159)
> - [NASA CubeSat 101](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf)

---


---

# Session 1.1: Introduction to Space Mission Design

**Duration:** 3 hours (Monday AM)
**Prerequisites:** None (engineering background assumed)
**References:**
- [NASA, Systems Engineering Handbook Rev 2 (SP-2016-6105), 2016](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [NASA, NPR 7123.1D -- Systems Engineering Processes and Requirements, 2020](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
- [ECSS, ECSS-M-ST-10C Rev.1 -- Space Project Management, 2009](https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/)
- [ESA, "20 Years of Concurrent Design at ESA", 2018](https://www.esa.int/Enabling_Support/Space_Engineering_Technology/CDF/What_is_the_CDF)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Describe the purpose and structure of a Concurrent Design Facility (CDF) and contrast it with sequential design
2. Explain the System-V model and its two sides (decomposition + integration)
3. List the 17 common technical processes defined in NPR 7123.1D and explain their recursive application
4. Map NASA lifecycle phases (Pre-A through F) to ECSS phases and identify key review gates
5. Identify the role of each CDF engineering position and their parameter ownership

---

## 1. What is a Concurrent Design Facility? (30 min)

### 1.1 The Problem with Sequential Design

Begin by asking the group: *"How is spacecraft design traditionally done?"*

Traditional spacecraft design follows a **sequential (waterfall) approach**: one discipline completes its work, documents it, and passes the design to the next discipline. This method dominated the space industry from the 1960s through the 1990s. Its limitations are well documented:

- **Interface mismatches** discovered late in integration, requiring costly redesign
- **Budget overruns** in mass, power, and cost not caught until formal reviews
- **Long iteration cycles** -- months between design reviews with limited inter-discipline feedback
- **Knowledge silos** -- critical design rationale locked in individual engineers' notes
- **Rework costs** -- the cost of correcting an error increases by roughly an order of magnitude per lifecycle phase (the "1-10-100 rule")

The aerospace industry's response was **concurrent engineering (CE)**, also called Integrated Product Development (IPD) or Integrated Concurrent Engineering (ICE). The core idea: bring all disciplines together to work simultaneously on a shared parametric model, resolving conflicts in real-time rather than discovering them in review.

> **Industry Practice:** Boeing's Phantom Works implemented concurrent engineering for the X-32 Joint Strike Fighter demonstrator in the late 1990s, reducing design iteration time from weeks to hours. JPL's Team X has been performing rapid mission assessments since 1995, completing Pre-Phase A studies in as little as one week. ESA's CDF, established in November 1998 at ESTEC (Noordwijk, Netherlands), became the most widely replicated model for space-specific concurrent design.

### 1.2 ESA's CDF -- The Reference Model

ESA's Concurrent Design Facility pioneered the approach for space missions and has been widely replicated at space agencies worldwide (DLR, CNES, JAXA, CSA, and over 60 universities).

| Parameter | Value |
|-----------|-------|
| Established | November 1998, ESTEC, Noordwijk, NL |
| Team size | 15--25 domain specialists per study |
| Session format | 3--4 hour focused design sessions, typically 2 per week |
| Study duration | 3--6 weeks for a complete Phase 0/A mission assessment |
| Tooling | Originally Excel-based IDM; now Open Concurrent Design Tool (OCDT) |
| Output | Complete mission feasibility assessment: mass, power, cost, risk, schedule |
| Track record | 200+ studies completed by 20th anniversary (2018) |
| Cost savings | Studies completed in ~1/5 the time and ~1/3 the cost of traditional approach |

[Source: ESA CDF official documentation; Bandecchi et al., "The ESA/ESTEC Concurrent Design Facility", ESA Bulletin No. 107, 2001]

### 1.3 Key Principles of Concurrent Design

**Shared parametric model.** All disciplines read from and write to a common data model. When the power engineer changes the solar array area, the structures engineer immediately sees the mass impact, and the thermal engineer sees the changed radiator view factor. This eliminates the "frozen interface document" problem.

**Scoped parameter ownership.** Each engineering position "owns" a defined set of parameters. Only the power engineer can modify EPS parameters; only the AOCS engineer can modify attitude control parameters. This prevents conflicting edits while maintaining concurrent access.

**Real-time conflict detection.** When parameter changes create conflicts (e.g., mass budget exceeded, link margin negative), the system flags them immediately. The systems engineer arbitrates.

**Design convergence through iteration.** A CDF study typically converges through 3--5 major iterations, with each session refining the design toward closure. The parametric model propagates changes automatically, so the team sees the system-level impact of every decision.

### 1.4 SpaceCDF -- A Web-Based CDF

SpaceCDF implements the CDF concept as a web-based tool accessible from any browser:

| Feature | Implementation |
|---------|---------------|
| Shared model | Real-time synchronisation via WebSocket; all participants see live updates |
| Parameter ownership | 15 engineering positions with scoped editing rights |
| Design convergence | 20 automated design agents that propagate parametric relationships |
| Conflict detection | Automated constraint engine with 187 inter-parameter connections |
| Document generation | ECSS-compliant exports (Word, PDF) with full traceability |
| Review gates | Automated gate criteria evaluation for MCR, SRR, PDR, CDR |

**Discussion prompt:** *What advantages does concurrent design offer over sequential? What risks does it introduce (e.g., groupthink, premature convergence)?*

---

## 2. The System-V Model (40 min)

### 2.1 Origin and Purpose

The "Vee" (V) model is the foundational framework for systems engineering. It appears in NASA SEH Section 2.3 (Figure 2.3-1), in ECSS-E-ST-10C, and in ISO/IEC 15288. It is not a project schedule -- it is a **logical model** showing the relationship between decomposition (breaking the problem down) and integration (building and verifying the solution).

The V-model answers two fundamental questions:
1. **Left side (top-down):** How do we decompose the mission need into buildable components?
2. **Right side (bottom-up):** How do we verify that what we built satisfies the original need?

The key insight is **horizontal traceability**: every element on the left side has a corresponding verification or validation activity on the right side, connected at the same level of abstraction.

### 2.2 V-Model Diagram

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" style="max-width:800px; font-family: 'Segoe UI', Arial, sans-serif; background: #fafafa; border: 1px solid #ddd; border-radius: 8px;">
  <!-- Title -->
  <text x="400" y="30" text-anchor="middle" font-size="16" font-weight="bold" fill="#1a1a2e">System-V Model (after NASA SEH Figure 2.3-1)</text>

  <!-- Left side boxes (decomposition) -->
  <rect x="40" y="55" width="180" height="40" rx="6" fill="#1a237e" stroke="#0d1552" stroke-width="1.5"/>
  <text x="130" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Mission Need / ConOps</text>

  <rect x="100" y="135" width="180" height="40" rx="6" fill="#283593" stroke="#1a237e" stroke-width="1.5"/>
  <text x="190" y="160" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Stakeholder Requirements</text>

  <rect x="160" y="215" width="180" height="40" rx="6" fill="#3949ab" stroke="#283593" stroke-width="1.5"/>
  <text x="250" y="240" text-anchor="middle" font-size="11" fill="white" font-weight="bold">System Architecture</text>

  <rect x="220" y="295" width="180" height="40" rx="6" fill="#5c6bc0" stroke="#3949ab" stroke-width="1.5"/>
  <text x="310" y="320" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Subsystem Design</text>

  <rect x="280" y="375" width="180" height="40" rx="6" fill="#7986cb" stroke="#5c6bc0" stroke-width="1.5"/>
  <text x="370" y="400" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Component Selection</text>

  <!-- Right side boxes (integration) -->
  <rect x="580" y="55" width="180" height="40" rx="6" fill="#1b5e20" stroke="#0d3311" stroke-width="1.5"/>
  <text x="670" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Mission Validation</text>

  <rect x="520" y="135" width="180" height="40" rx="6" fill="#2e7d32" stroke="#1b5e20" stroke-width="1.5"/>
  <text x="610" y="160" text-anchor="middle" font-size="11" fill="white" font-weight="bold">System Verification</text>

  <rect x="460" y="215" width="180" height="40" rx="6" fill="#43a047" stroke="#2e7d32" stroke-width="1.5"/>
  <text x="550" y="240" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Integration & Test</text>

  <rect x="400" y="295" width="180" height="40" rx="6" fill="#66bb6a" stroke="#43a047" stroke-width="1.5"/>
  <text x="490" y="320" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Subsystem Verification</text>

  <rect x="340" y="375" width="180" height="40" rx="6" fill="#81c784" stroke="#66bb6a" stroke-width="1.5"/>
  <text x="430" y="400" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Component Verification</text>

  <!-- Left-side arrows (decomposition) -->
  <line x1="130" y1="95" x2="190" y2="135" stroke="#1a237e" stroke-width="2" marker-end="url(#arrowBlue)"/>
  <line x1="190" y1="175" x2="250" y2="215" stroke="#283593" stroke-width="2" marker-end="url(#arrowBlue)"/>
  <line x1="250" y1="255" x2="310" y2="295" stroke="#3949ab" stroke-width="2" marker-end="url(#arrowBlue)"/>
  <line x1="310" y1="335" x2="370" y2="375" stroke="#5c6bc0" stroke-width="2" marker-end="url(#arrowBlue)"/>

  <!-- Right-side arrows (integration) -->
  <line x1="430" y1="375" x2="490" y2="335" stroke="#43a047" stroke-width="2" marker-end="url(#arrowGreen)"/>
  <line x1="490" y1="295" x2="550" y2="255" stroke="#2e7d32" stroke-width="2" marker-end="url(#arrowGreen)"/>
  <line x1="550" y1="215" x2="610" y2="175" stroke="#1b5e20" stroke-width="2" marker-end="url(#arrowGreen)"/>
  <line x1="610" y1="135" x2="670" y2="95" stroke="#0d3311" stroke-width="2" marker-end="url(#arrowGreen)"/>

  <!-- Bottom connection -->
  <line x1="460" y1="395" x2="340" y2="395" stroke="#9e9e9e" stroke-width="2" stroke-dasharray="6,3"/>

  <!-- Horizontal traceability arrows (dashed) -->
  <line x1="220" y1="75" x2="580" y2="75" stroke="#e65100" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arrowOrange)"/>
  <text x="400" y="68" text-anchor="middle" font-size="9" fill="#e65100" font-style="italic">validates against need</text>

  <line x1="280" y1="155" x2="520" y2="155" stroke="#e65100" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arrowOrange)"/>
  <text x="400" y="148" text-anchor="middle" font-size="9" fill="#e65100" font-style="italic">verifies requirements</text>

  <line x1="340" y1="235" x2="460" y2="235" stroke="#e65100" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arrowOrange)"/>
  <text x="400" y="228" text-anchor="middle" font-size="9" fill="#e65100" font-style="italic">integrates to architecture</text>

  <line x1="400" y1="315" x2="400" y2="315" stroke="#e65100" stroke-width="1.5" stroke-dasharray="5,3"/>

  <!-- Side labels -->
  <text x="50" y="460" font-size="12" fill="#1a237e" font-weight="bold">DECOMPOSITION</text>
  <text x="50" y="475" font-size="10" fill="#555">(top-down: WHAT to HOW)</text>

  <text x="580" y="460" font-size="12" fill="#1b5e20" font-weight="bold">INTEGRATION</text>
  <text x="580" y="475" font-size="10" fill="#555">(bottom-up: build to validate)</text>

  <!-- Arrow markers -->
  <defs>
    <marker id="arrowBlue" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6" fill="#283593"/>
    </marker>
    <marker id="arrowGreen" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6" fill="#2e7d32"/>
    </marker>
    <marker id="arrowOrange" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6" fill="#e65100"/>
    </marker>
  </defs>
</svg>

### 2.3 Left Side: Top-Down Decomposition

The left side of the V answers "how do we break the problem down into solvable pieces?"

| Level | Activity | Key Question | Output |
|-------|----------|-------------|--------|
| 1. Mission Need | Define the problem and concept of operations | What problem are we solving? For whom? | ConOps, problem statement, MoEs |
| 2. Stakeholder Requirements | Capture needs of all stakeholders | What must the system achieve? (WHAT, not HOW) | Stakeholder requirements baseline |
| 3. System Architecture | Define segments, elements, interfaces | How is the system structured? | System architecture, ICDs |
| 4. Subsystem Design | Design each subsystem to meet allocated requirements | How does each subsystem work? | Subsystem specifications |
| 5. Component Selection | Choose or design lowest-level components | Which hardware/software fulfils each need? | Component specifications, BoM |

### 2.4 Right Side: Bottom-Up Integration

The right side answers "how do we verify that what we built satisfies the original need?"

| Level | Activity | Key Question | Verification Method |
|-------|----------|-------------|-------------------|
| 5. Component Verification | Test each component against its spec | Does each part work? | Inspection, test |
| 4. Subsystem Verification | Integrate and test each subsystem | Do subsystems meet allocated requirements? | Test, analysis |
| 3. Integration & Test | Assemble the system and test interfaces | Do the subsystems work together? | Test, demonstration |
| 2. System Verification | Verify system against requirements | Does the system meet all requirements? | Test, analysis, inspection, demonstration |
| 1. Mission Validation | Validate against the original need | Does it solve the original problem? | Operations, user acceptance |

### 2.5 Horizontal Traceability

The orange dashed arrows in the diagram represent **horizontal traceability** -- the principle that every element on the left must have a corresponding verification/validation activity on the right:

- Each **requirement** (left) has a **verification method** (right): test, analysis, inspection, or demonstration (TAID)
- Each **design decision** (left) has a **test or analysis** (right) to confirm it works
- This traceability is captured in the **Requirements Verification Matrix (RVM)**

> **Key Equation:** The traceability completeness metric is:
>
> $T_c = \frac{N_{verified}}{N_{total\_requirements}} \times 100\%$
>
> A target of $T_c = 100\%$ is required at CDR. At PDR, $T_c \geq 90\%$ is typical.

### 2.6 Iteration and the SE Engine

The V is not a single pass. Real design iterates -- requirements change as design constraints are discovered, and design parameters feed back to refine requirements. This iterative loop is captured in the concept of the **"SE Engine"** (NASA SEH Section 2.1): the 17 common technical processes applied recursively at every level of the system hierarchy.

[Source: NASA SEH Section 2.3, Figure 2.3-1; INCOSE Systems Engineering Handbook, 4th Edition, Section 3.2]

**Exercise:** *On a whiteboard, draw the V-model from memory and label each level. Add the horizontal traceability arrows and name one verification method for each level.*

---

## 3. The 17 Common Technical Processes (30 min)

### 3.1 Overview

NASA's NPR 7123.1D defines 17 processes that apply recursively at every level of the system hierarchy. They are grouped into three categories, collectively called the **"SE Engine"**. These processes are not sequential -- they execute concurrently and iteratively, which is precisely what a CDF facilitates.

[Source: NPR 7123.1D Chapter 3; NASA SEH Section 2.1, Figure 2.1-1]

### 3.2 System Design Processes (1--4)

These processes decompose the problem into a solution. They correspond to the left side of the V-model.

| # | Process | Key Activity | Key Output | NASA SEH Reference |
|---|---------|-------------|------------|-------------------|
| 1 | **Stakeholder Expectations Definition** | Elicit needs, define ConOps, establish MoEs | Stakeholder requirements baseline | Section 4.1 |
| 2 | **Technical Requirements Definition** | Write "shall" statements, define MoPs and TPMs | Technical requirements baseline | Section 4.2 |
| 3 | **Logical Decomposition** | Functional analysis, behavioural modelling, derived requirements | Functional architecture | Section 4.3 |
| 4 | **Design Solution Definition** | Trade studies, select among alternatives, produce baseline design | Design solution baseline | Section 4.4 |

### 3.3 Product Realisation Processes (5--9)

These processes build, verify, and deliver the solution. They correspond to the right side of the V-model.

| # | Process | Key Activity | Key Output | NASA SEH Reference |
|---|---------|-------------|------------|-------------------|
| 5 | **Product Implementation** | Make, buy, code, or reuse lowest-level products | Hardware/software products | Section 5.1 |
| 6 | **Product Integration** | Assemble per integration plan, verify interfaces | Integrated system | Section 5.2 |
| 7 | **Product Verification** | Confirm product meets technical requirements (TAID) | Verification evidence | Section 5.3 |
| 8 | **Product Validation** | Confirm product meets stakeholder expectations | Validation evidence | Section 5.4 |
| 9 | **Product Transition** | Deliver, deploy, hand over to operations | Operational system | Section 5.5 |

### 3.4 Technical Management Processes (10--17)

These processes manage the engineering work and apply throughout the lifecycle.

| # | Process | Key Activity | Governing Document |
|---|---------|-------------|-------------------|
| 10 | **Technical Planning** | SEMP, subsidiary plans, WBS | NPR 7123.1D Section 3.10 |
| 11 | **Requirements Management** | Baselining, traceability, change control | NPR 7123.1D Section 3.11 |
| 12 | **Interface Management** | ICDs, IRDs, internal + external interfaces | NPR 7123.1D Section 3.12 |
| 13 | **Technical Risk Management** | Identification, assessment, mitigation per NPR 8000.4 | NPR 8000.4B |
| 14 | **Configuration Management** | Baselines, CM plan, CCBs | NPR 7120.5F Chapter 4 |
| 15 | **Technical Data Management** | Data rights, retention, dissemination | NPR 7123.1D Section 3.15 |
| 16 | **Technical Assessment** | TPMs, reviews, EVM, health checks | NPR 7123.1D Section 3.16 |
| 17 | **Decision Analysis** | Structured alternative selection (trade studies) | NASA SEH Section 6.8 |

### 3.5 Recursion Across the System Hierarchy

A critical property of the 17 processes is that they apply **recursively** at every level of the system hierarchy:

<!-- SVG DIAGRAM: SE Engine Recursion -->
<!-- Description: A nested hierarchy showing Mission Level -> System Level -> Subsystem Level -> Component Level, each containing the same "17 processes" cycle -->
<!-- Elements: Four concentric rounded rectangles labelled with the hierarchy levels; a circular arrow in the centre labelled "17 SE Processes (recursive)" -->

```
Mission Level:     17 processes applied (mission-level requirements, ConOps, validation)
  System Level:    17 processes applied (system requirements, architecture, verification)
    Subsystem Level: 17 processes applied (subsystem requirements, design, testing)
      Component Level: 17 processes applied (component specs, procurement, acceptance)
```

At each level, the same processes execute but with different scope, detail, and duration. In a CDF environment, multiple levels are often worked concurrently -- the systems engineer manages the mission and system levels while subsystem engineers work their respective domains.

> **Industry Practice:** On the James Webb Space Telescope (JWST), requirements management (Process 11) was applied at five levels of the system hierarchy simultaneously: Observatory, Optical Telescope Element, Integrated Science Instrument Module, individual instruments (NIRSpec, MIRI, NIRCam, FGS), and components (detectors, mechanisms). Each level had its own requirements baseline, traceability matrix, and verification plan. The total requirements count exceeded 10,000.

**Exercise:** *Map each of the 17 processes to a feature in SpaceCDF. Which processes does the tool support directly? Which require human judgment? Complete Part A of Worksheet 1.1.*

---

## 4. Lifecycle Phases and Review Gates (30 min)

### 4.1 NASA Lifecycle Phases

NASA defines seven lifecycle phases for space flight projects, governed by NPR 7120.5F. Each phase has specific objectives, activities, and exit criteria evaluated at formal review gates called Key Decision Points (KDPs).

[Source: NPR 7120.5F Chapter 2; NASA SEH Chapter 3]

### 4.2 Lifecycle Phase Diagram

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 280" style="max-width:850px; font-family: 'Segoe UI', Arial, sans-serif; background: #fafafa; border: 1px solid #ddd; border-radius: 8px;">
  <!-- Title -->
  <text x="425" y="25" text-anchor="middle" font-size="15" font-weight="bold" fill="#1a1a2e">NASA Space Flight Project Lifecycle (NPR 7120.5F)</text>

  <!-- Phase boxes -->
  <rect x="20" y="50" width="100" height="50" rx="5" fill="#e8eaf6" stroke="#3949ab" stroke-width="2"/>
  <text x="70" y="72" text-anchor="middle" font-size="10" font-weight="bold" fill="#1a237e">Pre-Phase A</text>
  <text x="70" y="88" text-anchor="middle" font-size="9" fill="#333">Concept</text>
  <text x="70" y="98" text-anchor="middle" font-size="9" fill="#333">Studies</text>

  <rect x="135" y="50" width="100" height="50" rx="5" fill="#c5cae9" stroke="#3949ab" stroke-width="2"/>
  <text x="185" y="72" text-anchor="middle" font-size="10" font-weight="bold" fill="#1a237e">Phase A</text>
  <text x="185" y="88" text-anchor="middle" font-size="9" fill="#333">Concept &amp; Tech</text>
  <text x="185" y="98" text-anchor="middle" font-size="9" fill="#333">Development</text>

  <rect x="250" y="50" width="100" height="50" rx="5" fill="#9fa8da" stroke="#283593" stroke-width="2"/>
  <text x="300" y="72" text-anchor="middle" font-size="10" font-weight="bold" fill="#1a237e">Phase B</text>
  <text x="300" y="88" text-anchor="middle" font-size="9" fill="white">Preliminary</text>
  <text x="300" y="98" text-anchor="middle" font-size="9" fill="white">Design</text>

  <rect x="365" y="50" width="100" height="50" rx="5" fill="#7986cb" stroke="#283593" stroke-width="2"/>
  <text x="415" y="72" text-anchor="middle" font-size="10" font-weight="bold" fill="white">Phase C</text>
  <text x="415" y="88" text-anchor="middle" font-size="9" fill="white">Final Design</text>
  <text x="415" y="98" text-anchor="middle" font-size="9" fill="white">&amp; Fabrication</text>

  <rect x="480" y="50" width="100" height="50" rx="5" fill="#5c6bc0" stroke="#1a237e" stroke-width="2"/>
  <text x="530" y="72" text-anchor="middle" font-size="10" font-weight="bold" fill="white">Phase D</text>
  <text x="530" y="88" text-anchor="middle" font-size="9" fill="white">AIT &amp;</text>
  <text x="530" y="98" text-anchor="middle" font-size="9" fill="white">Launch</text>

  <rect x="595" y="50" width="100" height="50" rx="5" fill="#3949ab" stroke="#1a237e" stroke-width="2"/>
  <text x="645" y="72" text-anchor="middle" font-size="10" font-weight="bold" fill="white">Phase E</text>
  <text x="645" y="88" text-anchor="middle" font-size="9" fill="white">Operations &amp;</text>
  <text x="645" y="98" text-anchor="middle" font-size="9" fill="white">Sustainment</text>

  <rect x="710" y="50" width="100" height="50" rx="5" fill="#1a237e" stroke="#0d1552" stroke-width="2"/>
  <text x="760" y="72" text-anchor="middle" font-size="10" font-weight="bold" fill="white">Phase F</text>
  <text x="760" y="88" text-anchor="middle" font-size="9" fill="white">Closeout /</text>
  <text x="760" y="98" text-anchor="middle" font-size="9" fill="white">Disposal</text>

  <!-- Arrows between phases -->
  <line x1="120" y1="75" x2="135" y2="75" stroke="#333" stroke-width="2" marker-end="url(#arrowDark)"/>
  <line x1="235" y1="75" x2="250" y2="75" stroke="#333" stroke-width="2" marker-end="url(#arrowDark)"/>
  <line x1="350" y1="75" x2="365" y2="75" stroke="#333" stroke-width="2" marker-end="url(#arrowDark)"/>
  <line x1="465" y1="75" x2="480" y2="75" stroke="#333" stroke-width="2" marker-end="url(#arrowDark)"/>
  <line x1="580" y1="75" x2="595" y2="75" stroke="#333" stroke-width="2" marker-end="url(#arrowDark)"/>
  <line x1="695" y1="75" x2="710" y2="75" stroke="#333" stroke-width="2" marker-end="url(#arrowDark)"/>

  <!-- Review gates (diamonds) -->
  <polygon points="127,130 137,120 147,130 137,140" fill="#e65100" stroke="#bf360c" stroke-width="1.5"/>
  <text x="137" y="158" text-anchor="middle" font-size="9" font-weight="bold" fill="#e65100">MCR</text>
  <text x="137" y="170" text-anchor="middle" font-size="8" fill="#666">KDP-A</text>
  <line x1="137" y1="100" x2="137" y2="120" stroke="#e65100" stroke-width="1" stroke-dasharray="3,2"/>

  <polygon points="242,130 252,120 262,130 252,140" fill="#e65100" stroke="#bf360c" stroke-width="1.5"/>
  <text x="252" y="158" text-anchor="middle" font-size="9" font-weight="bold" fill="#e65100">SRR/SDR</text>
  <text x="252" y="170" text-anchor="middle" font-size="8" fill="#666">KDP-B</text>
  <line x1="252" y1="100" x2="252" y2="120" stroke="#e65100" stroke-width="1" stroke-dasharray="3,2"/>

  <polygon points="357,130 367,120 377,130 367,140" fill="#e65100" stroke="#bf360c" stroke-width="1.5"/>
  <text x="367" y="158" text-anchor="middle" font-size="9" font-weight="bold" fill="#e65100">PDR</text>
  <text x="367" y="170" text-anchor="middle" font-size="8" fill="#666">KDP-C</text>
  <line x1="367" y1="100" x2="367" y2="120" stroke="#e65100" stroke-width="1" stroke-dasharray="3,2"/>

  <polygon points="472,130 482,120 492,130 482,140" fill="#e65100" stroke="#bf360c" stroke-width="1.5"/>
  <text x="482" y="158" text-anchor="middle" font-size="9" font-weight="bold" fill="#e65100">CDR</text>
  <text x="482" y="170" text-anchor="middle" font-size="8" fill="#666">KDP-D</text>
  <line x1="482" y1="100" x2="482" y2="120" stroke="#e65100" stroke-width="1" stroke-dasharray="3,2"/>

  <polygon points="545,130 555,120 565,130 555,140" fill="#e65100" stroke="#bf360c" stroke-width="1.5"/>
  <text x="555" y="158" text-anchor="middle" font-size="9" font-weight="bold" fill="#e65100">TRR/FRR</text>
  <text x="555" y="170" text-anchor="middle" font-size="8" fill="#666">KDP-E</text>
  <line x1="555" y1="100" x2="555" y2="120" stroke="#e65100" stroke-width="1" stroke-dasharray="3,2"/>

  <polygon points="700,130 710,120 720,130 710,140" fill="#e65100" stroke="#bf360c" stroke-width="1.5"/>
  <text x="710" y="158" text-anchor="middle" font-size="9" font-weight="bold" fill="#e65100">PLAR/DR</text>
  <text x="710" y="170" text-anchor="middle" font-size="8" fill="#666">KDP-F</text>
  <line x1="710" y1="100" x2="710" y2="120" stroke="#e65100" stroke-width="1" stroke-dasharray="3,2"/>

  <!-- Legend -->
  <rect x="25" y="200" width="15" height="15" rx="2" fill="#9fa8da" stroke="#283593" stroke-width="1"/>
  <text x="47" y="213" font-size="10" fill="#333">Lifecycle Phase</text>
  <polygon points="180,200 190,195 200,200 190,210" fill="#e65100" stroke="#bf360c" stroke-width="1"/>
  <text x="207" y="208" font-size="10" fill="#333">Review Gate / KDP</text>

  <!-- SpaceCDF scope bracket -->
  <line x1="20" y1="240" x2="470" y2="240" stroke="#2196f3" stroke-width="2"/>
  <line x1="20" y1="235" x2="20" y2="245" stroke="#2196f3" stroke-width="2"/>
  <line x1="470" y1="235" x2="470" y2="245" stroke="#2196f3" stroke-width="2"/>
  <text x="245" y="260" text-anchor="middle" font-size="11" font-weight="bold" fill="#2196f3">SpaceCDF Scope (Pre-A through C)</text>

  <defs>
    <marker id="arrowDark" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6" fill="#333"/>
    </marker>
  </defs>
</svg>

### 4.3 Phase Details

| Phase | Name | Primary Activity | Exit Review | Key Outputs |
|-------|------|-----------------|-------------|-------------|
| **Pre-A** | Concept Studies | Identify need, explore feasibility, develop ConOps | MCR | Mission concept, preliminary ConOps, feasibility assessment |
| **A** | Concept & Technology Development | Develop requirements, mature technology to TRL 4+ | SRR/SDR | Requirements baseline, technology development plan |
| **B** | Preliminary Design & Tech Completion | Preliminary design, close preliminary budgets, TRL 6+ | PDR | Preliminary design, budget allocations, test plans |
| **C** | Final Design & Fabrication | Detailed design, build hardware, TRL 8 | CDR | Detailed drawings, as-built documentation, flight hardware |
| **D** | Assembly, Integration & Test, Launch | System AIT, environmental testing, launch | TRR, ORR, FRR | Tested flight system, launch readiness |
| **E** | Operations & Sustainment | Operate the mission, produce data products | PLAR | Science data, operational lessons |
| **F** | Closeout | Decommission, passivate, dispose, lessons learned | DR | Disposal confirmation, final report |

**Key Decision Points (KDPs):** These are go/no-go authority decisions between phases, lettered A through F. They are distinct from technical reviews -- KDPs are management decisions informed by technical review outcomes. For projects exceeding $250M (USD), KDP-C requires a Joint Confidence Level (JCL) analysis per NPR 7120.5F.

### 4.4 ECSS Lifecycle Phases

ECSS defines a similar but not identical lifecycle. The phase letters conveniently align, but the entry/exit criteria and review content differ.

[Source: ECSS-M-ST-10C Rev.1, Section 5.3]

| ECSS Phase | Name | NASA Equivalent | Key Difference |
|-----------|------|----------------|----------------|
| 0 | Mission Analysis / Needs Identification | Pre-A | ECSS Phase 0 includes formal mission analysis |
| A | Feasibility | A | ECSS-A focuses on demonstrating feasibility |
| B | Preliminary Definition (B1/B2) | B | ECSS splits into B1 (system) and B2 (detailed) |
| C | Detailed Definition | C | Similar scope |
| D | Qualification & Production | D | ECSS-D emphasises qualification models |
| E | Utilisation | E | Similar scope |
| F | Disposal | F | ECSS-F explicitly addresses passivation |

### 4.5 Review Gates -- What Each Checks

| Review | Full Name | Key Question | Required Evidence |
|--------|-----------|-------------|-------------------|
| **MCR** | Mission Concept Review | Is the mission need justified? Is space the right answer? | Problem statement, stakeholder analysis, alternatives analysis, ConOps draft |
| **SRR** | System Requirements Review | Are requirements complete, consistent, traceable, and verifiable? | Requirements baseline, traceability matrix, risk register, preliminary ConOps |
| **SDR** | System Design Review | Does the system architecture satisfy requirements? | System architecture, functional decomposition, interface definitions |
| **PDR** | Preliminary Design Review | Does the preliminary design meet all requirements? | Design description, budget status (mass/power/cost), risk mitigation plans |
| **CDR** | Critical Design Review | Is the design complete and ready for fabrication? | Detailed drawings, analysis results, test plans, all budgets closed with positive margins |
| **TRR** | Test Readiness Review | Is the system ready for formal testing? | Test procedures, facility readiness, acceptance criteria |
| **FRR** | Flight Readiness Review | Is everything ready for launch? | All tests passed, waivers documented, launch procedures verified |

> **Industry Practice:** RADARSAT-2 (MDA/CSA, launched 2007) went through all NASA-equivalent review gates over a 6-year development. The CDR alone involved over 400 review items and 50 reviewers across 3 weeks. The mission exceeded its 7-year design life, operating for over 15 years -- a testament to thorough verification at each gate.

**Exercise:** *In SpaceCDF, go to the Gate Review tab and examine the MCR exit criteria. Which criteria are auto-evaluated by the tool? Which require manual review by the facilitator?*

---

## 5. CDF Engineering Positions (20 min)

### 5.1 Position Overview

In a CDF study, each engineering position owns a set of parameters and is responsible for their domain's design decisions. SpaceCDF supports 15 positions:

| Position | Responsibility | Key Owned Parameters | Primary Interfaces |
|----------|---------------|---------------------|-------------------|
| **Systems Engineer** | Overall architecture, budgets, margins, conflict resolution | Mass margin, power margin, system-level budgets | All positions |
| **Mission Analyst** | Orbit design, coverage analysis, ground station access | Altitude, inclination, RAAN, eclipse fraction, contact time | Comms, Payload, Ground |
| **Payload Lead** | Instrument performance, data generation rates | GSD, spectral bands, data rate, FOV, SNR | Mission Analyst, Power, AOCS, Comms |
| **Power Engineer** | Solar arrays, batteries, EPS architecture, duty cycling | SA area, battery capacity, bus voltage, DoD | All (power is a universal constraint) |
| **AOCS Engineer** | Attitude sensors, actuators, pointing modes | Pointing accuracy, slew rate, wheel momentum, sensor suite | Payload, Structures, Propulsion |
| **Thermal Engineer** | Temperature control, radiators, heaters, coatings | Max/min temps, radiator area, heater power, thermal margin | Structures, Power, Payload |
| **Comms Engineer** | Link budget, transponder, antenna, spectrum licensing | Link margin, data rate, frequency band, EIRP, G/T | Mission Analyst, Payload, Ground |
| **Propulsion Engineer** | Delta-V budget, thruster selection, propellant mass | Isp, propellant mass, total impulse, thrust vector | Mission Analyst, AOCS, Structures |
| **Structures Engineer** | Primary structure, mechanisms, launch loads | Structure mass, natural frequency, margin of safety | All (mass is a universal constraint) |
| **Cost Engineer** | WBS, cost estimating relationships, schedule | Total cost, per-subsystem cost, launch cost, risk-adjusted cost | Systems Engineer, all subsystems |
| **Compliance Engineer** | Standards, frequency licensing, export control | Standard applicability, ITAR/EAR status, filing status | All |
| **User Representative** | End-user needs, data product requirements | Data format, latency, accessibility, coverage | Payload, Comms, Ground |
| **Mission Operations** | Ground ops concept, staffing, automation | Contact schedule, automation level, anomaly procedures | Comms, Ground, Systems |
| **Ground Segment** | Ground stations, data processing pipeline | Station network, processing latency, archive capacity | Comms, Mission Ops, User Rep |
| **Software Engineer** | Flight software, FDIR, TC/TM interfaces | FSW architecture, command dictionary, FDIR rules | OBC, AOCS, Comms, Payload |

### 5.2 Interface Conflicts

The most productive CDF sessions are those where **interface conflicts** are identified and resolved. Common conflict patterns:

| Conflict | Positions Involved | Resolution Approach |
|----------|--------------------|-------------------|
| Mass budget exceeded | Systems, Structures, all subsystems | Re-allocate margins, descope payload, select lighter components |
| Power budget exceeded | Systems, Power, Payload, Comms | Adjust duty cycles, increase SA area, reduce payload power |
| Pointing requirement vs actuator capability | Payload, AOCS, Structures | Relax pointing requirement, add fine steering mirror, improve isolation |
| Downlink capacity vs data generation | Comms, Payload, Ground | Add ground stations, increase TX power, reduce data rate, add compression |
| Volume constraint vs thermal rejection | Structures, Thermal, Payload | Redesign radiator location, add deployable radiator, reduce heat dissipation |

**Discussion prompt:** *Which positions would interact most frequently in your mission? Where do you expect the most difficult trade-offs?*

---

## 6. Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| CDF | Concurrent multi-discipline design resolves conflicts in real-time; SpaceCDF implements this as a web-based tool |
| System-V | Left side decomposes (need to components); right side integrates (build to validate); horizontal traceability links them |
| 17 Processes | Recursive at every system level; grouped as Design (1--4), Realisation (5--9), Management (10--17) |
| Lifecycle Phases | Pre-A through F with KDP gates; ECSS phases approximately align; SpaceCDF covers Pre-A through C |
| Review Gates | Each gate answers a specific question with required evidence; auto-evaluated where possible in SpaceCDF |
| Positions | Each owns a parameter domain; conflicts arise at interfaces; the systems engineer arbitrates |

---

## 7. Tool Exercise (15 min)

1. Open SpaceCDF and navigate through the workflow steps (Need -> Concept -> Requirements -> Design)
2. On the Design Dashboard, identify which KPI cards correspond to which engineering positions
3. Go to the Positions tab and review the key questions for your assigned position
4. Go to the Gate Review tab and examine the MCR exit criteria

**Complete Worksheet 1.1:** Map the 17 processes to SpaceCDF features and identify lifecycle phases for given activities.

---

## References

1. [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016](https://www.nasa.gov/reference/systems-engineering-handbook/)
2. [NASA, NPR 7123.1D -- Systems Engineering Processes and Requirements, 2020](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
3. [NASA, NPR 7120.5F -- NASA Space Flight Program and Project Management Requirements, 2021](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_)
4. [ECSS, ECSS-M-ST-10C Rev.1 -- Space Project Management, 2009](https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/)
5. [INCOSE, Systems Engineering Handbook, 4th Edition, 2015](https://www.incose.org/products-and-publications/se-handbook)
6. [Bandecchi, M. et al., "The ESA/ESTEC Concurrent Design Facility", ESA Bulletin No. 107, 2001](https://www.esa.int/esapub/bulletin/bullet107/bul107_2.pdf)
7. [Wertz, J.R. et al., Space Mission Engineering: The New SMAD (SMAD4), Microcosm Press, 2011](https://www.microcosminc.com/)

---

# Session 1.2: The Canadian Space Ecosystem & Regulatory Environment

**Duration:** 4 hours (Monday PM + Tuesday AM)
**Prerequisites:** Session 1.1
**References:**
- [Government of Canada, Canadian Space Agency Act (S.C. 1990, c. 13)](https://laws-lois.justice.gc.ca/eng/acts/c-11.2/)
- [Government of Canada, Remote Sensing Space Systems Act (RSSSA, S.C. 2005, c. 45)](https://laws-lois.justice.gc.ca/eng/acts/r-5.4/)
- [Government of Canada, Radiocommunication Act (R.S.C., 1985, c. R-2)](https://laws-lois.justice.gc.ca/eng/acts/r-2/)
- [ISED Canada, Spectrum Management and Telecommunications](https://www.ic.gc.ca/eic/site/smt-gst.nsf/eng/home)
- [Government of Canada, Export and Import Permits Act (EIPA)](https://laws-lois.justice.gc.ca/eng/acts/e-19/)
- [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [ITU, Radio Regulations, Edition 2020](https://www.itu.int/pub/R-REG-RR)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Describe the Canadian Space Agency's mandate and organisational structure
2. Map the Canadian space industry ecosystem -- prime contractors, SMEs, universities, and funding programs
3. Identify the regulatory bodies that govern space activities in Canada (CSA, ISED, GAC, DND)
4. Explain the RSSSA licensing process for remote sensing satellites
5. Describe the spectrum licensing process through ISED and ITU coordination
6. Identify Canadian export control obligations under EIPA, ITAR, and EAR

---

## Part 1: The Canadian Space Ecosystem (Monday PM -- 2 hours)

---

### 1. The Canadian Space Agency (30 min)

#### 1.1 Mandate and History

The Canadian Space Agency (CSA) was established by the *Canadian Space Agency Act* (S.C. 1990, c. 13) with the mandate to "promote the peaceful use and development of space, to advance the knowledge of space through science and to ensure that space science and technology provide social and economic benefits for Canadians."

| Milestone | Year | Significance |
|-----------|------|-------------|
| Alouette 1 | 1962 | Canada becomes the 3rd nation to build and design a satellite |
| Hermes (CTS) | 1976 | World's first high-power direct broadcast satellite (CSA/NASA) |
| Canadarm | 1981 | Robotic arm for Space Shuttle; established Canada's space robotics dominance |
| RADARSAT-1 | 1995 | First Canadian Earth observation satellite; C-band SAR |
| CSA established | 1990 | Canadian Space Agency Act creates the agency |
| Canadarm2 | 2001 | ISS robotic arm; continues robotics legacy |
| RADARSAT-2 | 2007 | Commercial SAR satellite (MDA); RSSSA applies |
| RADARSAT Constellation Mission (RCM) | 2019 | Three C-band SAR satellites; maritime surveillance, disaster management |
| Canadarm3 | In dev. | For the Lunar Gateway; next-generation autonomous robotics |
| Lunar Gateway participation | 2019+ | Canada committed as partner; astronaut flights planned |

[Source: CSA, "Canada's Space Milestones", www.asc-csa.gc.ca]

#### 1.2 CSA Organisational Focus Areas

The CSA is headquartered in Saint-Hubert, Quebec, and organises its activities around three strategic priorities:

| Priority | Activities | Key Programs |
|----------|-----------|-------------|
| **Space Exploration** | ISS operations, Lunar Gateway, Canadarm3, astronaut program | Lunar Exploration Accelerator Program (LEAP) |
| **Space Utilisation** | Earth observation, satellite communications, GNSS augmentation | RADARSAT, SmartEarth, eHealth |
| **Space Science & Technology** | Astronomy, planetary science, technology development | CASTOR, JWST/NIRISS, space health |

#### 1.3 Canadian Space Strategy (2019)

The *Exploration, Imagination, Innovation: A New Space Strategy for Canada* (2019) committed $2.05B over 24 years and established five priorities:
1. Ensure astronaut health and well-being in deep space
2. Develop and use advanced AI and robotics in space
3. Connect rural and remote Canadians through next-generation satellite communications
4. Use space data and technology to manage natural resources sustainably
5. Position the Canadian space sector for the future

> **Industry Practice:** The $150M Lunar Exploration Accelerator Program (LEAP) specifically targets Canadian SMEs and universities to develop technologies for lunar surface science, health, AI, and robotics. This "pull-through" model -- where a strategic government investment creates opportunities for industry -- is a hallmark of the Canadian space ecosystem.

---

### 2. Canadian Space Industry Map (30 min)

#### 2.1 Industry Structure

The Canadian space industry generated approximately $2.7B in revenue (2022) and employs ~12,000 people. It is structured in tiers:

| Tier | Role | Key Players | Revenue Share |
|------|------|-------------|--------------|
| **Tier 1: Primes** | System integration, large platforms, constellation operations | MDA Space, Telesat, SFL (U of T) | ~60% |
| **Tier 2: Subsystem/Component** | Subsystem design, specialised components, ground systems | Honeywell Canada, ABB, Magellan Aerospace, NGC Aerospace | ~25% |
| **Tier 3: SMEs & Startups** | Niche technologies, applications, data analytics | GHGSat, NorthStar, Kepler Communications, Wyvern | ~10% |
| **Tier 4: Academia** | R&D, training, technology incubation | U of T (SFL), York U, UBC, U of Calgary, Western | ~5% |

#### 2.2 Key Canadian Space Capabilities

Canada has world-leading capabilities in several domains:

| Capability | Key Player(s) | Notable Missions | Global Standing |
|-----------|--------------|-----------------|----------------|
| **Space robotics** | MDA Space | Canadarm, Canadarm2, Dextre, Canadarm3 | World leader |
| **SAR Earth observation** | MDA Space, CSA | RADARSAT-1/2/RCM | Top 3 globally |
| **Satellite communications** | Telesat | Anik fleet, Telesat Lightspeed (LEO constellation) | Pioneer in GEO DBS |
| **Small satellite systems** | SFL (U of T) | MOST, NEOSSat, GHGSat-D, BRITE | Top university lab globally |
| **GHG monitoring** | GHGSat | GHGSat constellation (methane) | World's only commercial GHG monitoring constellation |
| **Optical instruments** | ABB, Honeywell | JWST/FGS-NIRISS, OSIRIS-REx laser altimeter | Tier 1 instrument builder |
| **Star trackers/AOCS** | NGC Aerospace/Honeywell | Numerous missions | Widely used sensors |

#### 2.3 Funding Programs

Canadian space activities are funded through several mechanisms:

| Program | Administered By | Scope | Typical Value |
|---------|----------------|-------|--------------|
| **Space Technology Development Program (STDP)** | CSA | TRL advancement for flight heritage | $100K--$3M per project |
| **Class Grants and Contributions** | CSA | Space science, awareness, STEM | Variable |
| **LEAP** | CSA | Lunar technology development | Up to $3M per project |
| **IRAP** | NRC | SME innovation support | $50K--$1M |
| **SIF** | ISED | Strategic innovation projects | $10M--$100M+ |
| **DRDC contracts** | DND | Dual-use technology | Classified--$10M |
| **NSERC / CFI** | Federal | Academic research infrastructure | $50K--$5M |

> **Industry Practice:** GHGSat (Montreal) progressed from a CSA-funded technology demonstrator (GHGSat-D "Claire", launched 2016) to a commercial constellation of 12+ satellites monitoring methane emissions from individual industrial facilities. This trajectory -- government seed funding enabling commercial scale-up -- is the canonical Canadian space industry growth model.

**Discussion prompt:** *For your mission concept, which industry tier would you engage? What CSA funding programs might apply? What capabilities would need to be sourced internationally?*

---

### 3. Comparison with Other National Models (20 min)

Understanding Canada's space ecosystem requires comparing it with partner agencies:

| Parameter | Canada (CSA) | USA (NASA) | Europe (ESA) | Japan (JAXA) |
|-----------|-------------|-----------|-------------|-------------|
| Annual budget (approx.) | ~$300M CAD | ~$25B USD | ~$7.5B EUR | ~$1.5B USD |
| Staff | ~670 | ~18,000 | ~2,300 | ~1,500 |
| Launch capability | None (uses partners) | SLS, commercial (SpaceX, ULA) | Ariane 6, Vega-C | H3, Epsilon |
| Key strength | Robotics, SAR, instruments | Full spectrum | Science, EO, navigation | Rockets, science, ISS (Kibo) |
| Industry model | Government seed + commercial scale | Government prime + commercial | Juste retour (geographic return) | Government-led + commercial |

Canada's lack of indigenous launch capability means all Canadian satellites launch on foreign vehicles, which has implications for export control (Section 5 below).

---

### 4. Canadian Space in the International Context (20 min)

#### 4.1 International Partnerships

Canada participates in space through multilateral and bilateral agreements:

| Partnership | Canadian Contribution | Canadian Benefit |
|------------|----------------------|-----------------|
| **ISS** | Canadarm2, Dextre, SPDM | Astronaut access, research time, technology demonstrations |
| **Lunar Gateway** | Canadarm3 | Astronaut flights, lunar science access |
| **Copernicus (ESA)** | Data access agreement | Free access to Sentinel data for Canadian users |
| **COSPAS-SARSAT** | Canadian ground stations, MEOSAR payloads | Search and rescue capability for Canadian territory |
| **Five Eyes** | Intelligence sharing, dual-use technology | Access to allied space intelligence capabilities |

#### 4.2 The Canadian Niche Strategy

Canada has historically pursued a "niche excellence" strategy: rather than attempting full-spectrum space capability, Canada develops world-class expertise in specific domains (robotics, SAR, instruments) and trades access to these capabilities for partnership in larger programs.

> **Key Equation:** The "partnership leverage ratio" -- informal but useful -- describes how Canada trades capability for access:
>
> $L = \frac{V_{access}}{C_{contribution}}$
>
> Where $V_{access}$ is the value of program access obtained and $C_{contribution}$ is the cost of Canada's contribution. For the ISS, Canada's Canadarm2/Dextre contribution (~$2B CAD over 30 years) provides access to a $150B+ program, yielding $L \approx 75$. This is the highest leverage ratio of any ISS partner.

---

## Part 2: Regulatory Environment (Tuesday AM -- 2 hours)

---

### 5. Regulatory Framework Overview (15 min)

Space activities in Canada are governed by multiple federal bodies. There is no single "Space Act" -- instead, regulation is distributed across several statutes:

<!-- SVG DIAGRAM: Canadian Space Regulatory Framework -->
<!-- Description: A hierarchical diagram showing the regulatory bodies and their statutes -->
<!-- Elements: Central "Space Activity" node connected to CSA (CSA Act), ISED (Radiocommunication Act, Telecommunications Act), GAC (EIPA, ITAR), DND (dual-use), Transport Canada (launch -- future), and international bodies (ITU, COPUOS, MTCR) -->

| Regulatory Body | Statute | What It Regulates | Relevance to Mission Design |
|----------------|---------|-------------------|---------------------------|
| **CSA** | Canadian Space Agency Act | Space program coordination, policy | Mission approval, funding |
| **ISED** | Radiocommunication Act | Radio spectrum allocation, licensing | Frequency licensing for all RF transmissions |
| **ISED** | Remote Sensing Space Systems Act (RSSSA) | Operation of remote sensing satellites | Licensing for any satellite that images Earth |
| **GAC** | Export and Import Permits Act (EIPA) | Export control of strategic goods | Export permits for satellite technology |
| **GAC** | Controlled Goods Program | Access to controlled (ITAR/CG) goods | Personnel security clearances |
| **DND/DRDC** | National Defence Act | Dual-use technology, military space | Classification, security requirements |
| **Transport Canada** | (No current statute) | Launch operations (future) | Canada has no domestic launch regulation yet |

---

### 6. Remote Sensing Space Systems Act (RSSSA) (30 min)

#### 6.1 Purpose and Scope

The RSSSA (S.C. 2005, c. 45) regulates the operation of remote sensing satellites from Canada. It was enacted primarily in response to the commercialisation of RADARSAT-2 (the first Canadian commercial EO satellite) and addresses national security and foreign policy concerns related to Earth imagery.

[Source: Government of Canada, RSSSA, https://laws-lois.justice.gc.ca/eng/acts/r-5.4/]

#### 6.2 Who Needs a Licence?

An RSSSA licence is required for any person or entity that:
- **Operates** a remote sensing space system from Canada, or
- **Controls** the collection or distribution of remote sensing data from a Canadian system

This applies regardless of where the satellite is manufactured or launched. If it is operated from Canadian soil, RSSSA applies.

#### 6.3 Licence Categories and Conditions

| Licence Type | Scope | Typical Conditions |
|-------------|-------|-------------------|
| **System Operating Licence** | Operate a remote sensing satellite system | Data handling plan, priority access for Canadian government, shutter control provisions |
| **Interoperability Arrangements** | Share data with foreign entities | Approval for each foreign government or commercial partner |

Key conditions typically imposed:

| Condition | Description | Rationale |
|-----------|-------------|-----------|
| **Priority access** | Government of Canada can request priority imaging of any area | National security |
| **Shutter control** | Government can restrict imaging of specified areas | National security, diplomatic relations |
| **Data disposition** | Approved plan for data storage, distribution, and destruction | Prevent unauthorised access |
| **System disposal** | Plan for end-of-life decommissioning | Space debris mitigation |
| **Raw data protection** | Restrictions on distribution of unprocessed data | Prevent circumvention of controls |

#### 6.4 Implications for CubeSat and University Missions

Even small CubeSat missions with cameras must comply with RSSSA if they produce images of Earth. Key considerations:

| Parameter | Threshold | Implication |
|-----------|-----------|------------|
| GSD | No formal threshold in the Act | All resolutions require licensing |
| Orbit type | Any orbit imaging Earth | LEO, MEO, GEO all in scope |
| Data distribution | Any distribution of imagery | Must have approved data handling plan |
| Foreign participation | Any foreign access to data | Requires interoperability arrangement |

> **Industry Practice:** MDA's RADARSAT-2 operates under an RSSSA licence that includes shutter control provisions. During the 2010 Haiti earthquake response, the Government of Canada exercised priority access to direct RADARSAT-2 to image the disaster zone within hours. This demonstrates both the operational utility and the regulatory mechanism of RSSSA.

**Discussion prompt:** *Does your mission concept involve any remote sensing of Earth? If so, what RSSSA conditions might apply?*

---

### 7. Spectrum Management and Licensing (40 min)

#### 7.1 Why Spectrum Licensing Matters

Every satellite that transmits or receives radio signals requires spectrum authorisation. This is not optional -- unauthorised RF transmission is illegal in all ITU member states and can result in harmful interference to other systems.

The process involves two levels:
1. **National:** ISED (Innovation, Science and Economic Development Canada) issues the radio licence
2. **International:** ITU (International Telecommunication Union) coordinates the frequency filing to prevent interference with other national administrations

#### 7.2 The ITU Framework

The International Telecommunication Union allocates spectrum globally through the Radio Regulations (RR), updated at World Radiocommunication Conferences (WRC) every 3--4 years.

| ITU Concept | Description | Relevance |
|-------------|-------------|-----------|
| **Frequency allocation** | Spectrum divided among radio services (Fixed Satellite, Mobile, Earth Exploration Satellite, etc.) | Determines which bands are available for your mission type |
| **ITU Regions** | Region 1 (Europe/Africa), Region 2 (Americas), Region 3 (Asia/Pacific) | Canada is in Region 2; allocations may differ by region |
| **Coordination** | Bilateral/multilateral agreements to avoid interference | Required before a new satellite system can operate |
| **Notification** | Formal filing with the ITU Radiocommunication Bureau (BR) | Records the satellite system in the Master International Frequency Register (MIFR) |

#### 7.3 Common Satellite Frequency Bands

| Band | Frequency Range | Typical Use | Key Characteristics |
|------|----------------|-------------|-------------------|
| **UHF** | 400--450 MHz | CubeSat TT&C, AIS, ADS-B | Simple antennas, low data rate (1--9.6 kbps), crowded |
| **S-band** | 2.0--2.3 GHz | TT&C (uplink + downlink) | Standard for housekeeping; moderate antenna gain required |
| **X-band** | 8.025--8.4 GHz | EO payload data downlink | Higher data rates (10--150 Mbps); requires tracking antenna on ground |
| **Ka-band** | 26.5--40 GHz | High-throughput data downlink, inter-satellite links | Very high data rates (100+ Mbps); rain attenuation significant |
| **L-band** | 1.5--1.6 GHz | GNSS, mobile satellite service | Navigation, SAR beacons |
| **C-band** | 3.7--4.2 / 5.9--6.4 GHz | Legacy GEO comms (DBS), SAR (RADARSAT) | Being repurposed for 5G in some countries |

#### 7.4 The Licensing Process (Canada)

The ISED spectrum licensing process for a satellite system follows these steps:

| Step | Activity | Duration | Documents |
|------|----------|----------|-----------|
| 1 | Pre-application consultation with ISED | 2--4 weeks | Preliminary technical description |
| 2 | Formal application submission | -- | ISED application form, technical annex |
| 3 | ISED technical review | 3--6 months | Interference analysis, coordination requirements |
| 4 | ITU filing (Advance Publication Information -- API) | -- | ITU API filing (submitted by ISED on Canada's behalf) |
| 5 | ITU coordination with affected administrations | 2--7 years | Coordination agreements |
| 6 | ITU notification and recording in MIFR | -- | MIFR entry |
| 7 | ISED licence issuance | -- | Radio licence |

> **Key Equation:** The link budget equation governs whether a given frequency allocation provides sufficient performance. The received signal power is:
>
> $P_r = P_t + G_t + G_r - L_{fs} - L_{atm} - L_{misc}$
>
> Where all values are in dB:
> - $P_t$ = transmit power (dBW)
> - $G_t$ = transmit antenna gain (dBi)
> - $G_r$ = receive antenna gain (dBi)
> - $L_{fs} = 20\log_{10}(4\pi d / \lambda)$ = free-space path loss (dB)
> - $L_{atm}$ = atmospheric loss (dB)
> - $L_{misc}$ = miscellaneous losses (pointing, polarisation, etc.)
>
> The link margin is then:
>
> $M = P_r - P_{r,min} = (E_b/N_0)_{received} - (E_b/N_0)_{required}$
>
> A positive margin of at least 3 dB is typically required; 6 dB for critical links.

#### 7.5 CubeSat-Specific Considerations

Many CubeSat operators use amateur radio frequencies (VHF/UHF) during development but must transition to commercial bands for operational missions, especially if there is any commercial data distribution.

| Approach | Licensing Path | Limitations |
|----------|---------------|-------------|
| **Amateur radio (VHF/UHF)** | IARU coordination; national amateur licence | No commercial use; data must be freely available; limited power/bandwidth |
| **Commercial UHF** | ISED commercial licence; ITU coordination | Low data rate; crowded band; longer licensing timeline |
| **S-band TT&C** | ISED licence; SFCG coordination | Standard path; moderate timeline (6--12 months) |
| **X-band payload** | ISED licence; ITU coordination | Higher data rate; requires tracking ground station |

> **Industry Practice:** Kepler Communications (Toronto) initially operated its first pathfinder satellites on Ku-band for store-and-forward IoT data relay. Obtaining Ku-band spectrum rights required coordination with incumbent GEO operators, a process that took over 2 years. The lesson: begin spectrum licensing as early as Phase A.

---

### 8. Export Control (30 min)

#### 8.1 The Export Control Landscape

Satellite technology is controlled goods in most countries due to dual-use (civil/military) applications. Canadian space companies and universities must navigate three overlapping regimes:

| Regime | Administered By | Scope | Key List |
|--------|----------------|-------|----------|
| **EIPA** (Canada) | Global Affairs Canada (GAC) | Canadian-origin goods and technology | Export Control List (ECL), Groups 1--7 |
| **ITAR** (USA) | US State Department (DDTC) | US-origin defence articles and services | US Munitions List (USML), Category XV (spacecraft) |
| **EAR** (USA) | US Commerce Department (BIS) | US-origin dual-use goods and technology | Commerce Control List (CCL), ECCN 9Axx |

#### 8.2 Canadian Export Controls (EIPA)

The Export and Import Permits Act requires an export permit for goods on Canada's Export Control List (ECL). Space-relevant ECL groups:

| ECL Group | Description | Examples |
|-----------|-------------|---------|
| Group 1 | Dual-use goods (Wassenaar Arrangement) | Radiation-hardened electronics, space-qualified components |
| Group 2 | Munitions (defence goods) | Military satellite systems, encrypted comms |
| Group 4 | Nuclear-related (NSG) | RTGs, nuclear propulsion components |
| Group 6 | Missile technology (MTCR) | Complete rocket systems, guidance systems, propulsion |
| Group 7 | Chemical/biological weapons | Not typically space-relevant |

#### 8.3 US Export Controls (ITAR and EAR)

Any mission using US-origin components (which includes nearly all commercial space electronics) must comply with US export controls:

**ITAR (International Traffic in Arms Regulations):**
- USML Category XV covers spacecraft and related articles
- Requires a Technical Assistance Agreement (TAA) or Manufacturing License Agreement (MLA)
- Applies to US-origin defence articles regardless of where they are located
- Violation penalties: up to $1M per violation and 20 years imprisonment

**EAR (Export Administration Regulations):**
- Controls dual-use items (commercial space components, software, technology)
- Uses Export Control Classification Numbers (ECCNs)
- Requires a licence for export to most countries (except Canada for many items under bilateral agreements)
- The US-Canada Defence Production Sharing Agreement provides some exemptions

#### 8.4 Practical Implications for Mission Design

| Design Decision | Export Control Implication |
|----------------|--------------------------|
| Using US-origin reaction wheels | EAR licence may be required; ITAR if military-grade |
| Collaborating with a non-Five Eyes university | TAA required for ITAR-controlled technical data |
| Launching on a non-US rocket | ITAR Technology Transfer Agreement for US components on foreign launcher |
| Open-sourcing satellite software | Must verify no controlled algorithms (e.g., encryption above EAR thresholds) |
| Hosting a foreign payload | May require export permit under EIPA and/or ITAR approval |
| Publishing detailed design in a paper | Technical data review required if ITAR-controlled components discussed |

> **Industry Practice:** MDA's export of RADARSAT-2 ground segment technology to international partners required extensive EIPA permitting and ITAR compliance review (since US-origin components were embedded in the system). The process took 18+ months and required dedicated compliance staff. Even university CubeSat projects using US-origin COTS components must track their ECCN classifications.

**Discussion prompt:** *Does your mission concept involve any US-origin components? Any international partners? What export control obligations might apply?*

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| CSA mandate | Promote peaceful use of space; niche excellence strategy (robotics, SAR, instruments) |
| Industry structure | 4-tier ecosystem; government seed funding enables commercial scale-up |
| RSSSA | Any remote sensing satellite operated from Canada requires a licence; includes shutter control |
| Spectrum licensing | Two-level process (ISED national + ITU international); start in Phase A; 2+ year timeline |
| Export control | Three overlapping regimes (EIPA, ITAR, EAR); nearly all missions encounter US controls |
| Key lesson | Regulatory compliance is not optional -- it shapes design decisions from the earliest phases |

---

## References

1. [Government of Canada, Canadian Space Agency Act (S.C. 1990, c. 13)](https://laws-lois.justice.gc.ca/eng/acts/c-11.2/)
2. [Government of Canada, Remote Sensing Space Systems Act (S.C. 2005, c. 45)](https://laws-lois.justice.gc.ca/eng/acts/r-5.4/)
3. [Government of Canada, Radiocommunication Act (R.S.C., 1985, c. R-2)](https://laws-lois.justice.gc.ca/eng/acts/r-2/)
4. [Government of Canada, Export and Import Permits Act (R.S.C., 1985, c. E-19)](https://laws-lois.justice.gc.ca/eng/acts/e-19/)
5. [ISED, Spectrum Management and Telecommunications](https://www.ic.gc.ca/eic/site/smt-gst.nsf/eng/home)
6. [ITU, Radio Regulations, Edition 2020](https://www.itu.int/pub/R-REG-RR)
7. [CSA, Exploration, Imagination, Innovation: A New Space Strategy for Canada, 2019](https://www.asc-csa.gc.ca/eng/publications/space-strategy-for-canada.asp)
8. [CSA, State of the Canadian Space Sector Report, 2022](https://www.asc-csa.gc.ca/eng/publications/state.asp)
9. [US Department of State, ITAR (22 CFR 120-130)](https://www.ecfr.gov/current/title-22/chapter-I/subchapter-M)
10. [US Department of Commerce, EAR (15 CFR 730-774)](https://www.ecfr.gov/current/title-15/subtitle-B/chapter-VII/subchapter-C)

---

# Session 1.3: International Standards for Space Systems

**Duration:** 4 hours (Tuesday PM + Wednesday)
**Prerequisites:** Sessions 1.1--1.2
**References:**
- [ECSS, ECSS System -- Description, Implementation and General Requirements (ECSS-S-ST-00C), 2020](https://ecss.nl/standard/ecss-s-st-00c-space-standardization-policy-and-organisation/)
- [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [CDS, Interface Definition Document for Launch Vehicle Adapters, Rev 14, 2023](https://www.spacex.com/rideshare/)
- [IADC, Space Debris Mitigation Guidelines (IADC-02-01 Rev 3), 2021](https://www.iadc-home.org/documents_public/)
- [ISO, ISO 24113:2023 -- Space Debris Mitigation Requirements, 2023](https://www.iso.org/standard/82450.html)
- [UNOOSA, COPUOS Guidelines for the Long-term Sustainability of Outer Space Activities, 2019](https://www.unoosa.org/oosa/en/ourwork/topics/long-term-sustainability-of-outer-space-activities.html)
- [ESA, Space Debris Mitigation Compliance Verification Guidelines (ESSB-HB-U-002), 2023](https://technology.esa.int/upload/media/47ypgb5qwq.pdf)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Describe the ECSS standard framework and its hierarchical structure (Management, Engineering, Product Assurance, Sustainability)
2. Compare ECSS and NASA standards and identify equivalences
3. Explain the CDS Rev 14 interface standard and its role in launch vehicle integration
4. Apply space debris mitigation guidelines (IADC, ISO 24113, FCC 5-year rule) to mission design
5. Describe the role of COPUOS and the Outer Space Treaty framework
6. Use SpaceCDF's compliance tracking features

---

## Part 1: The ECSS Framework (Tuesday PM -- 2 hours)

---

### 1. Why Standards Matter in Space Engineering (20 min)

#### 1.1 The Cost of Non-Compliance

Space missions operate in an environment where failures are catastrophic, repair is impossible, and the consequences of interference or debris affect all space users. Standards exist to:

1. **Ensure mission safety and reliability** -- by codifying lessons learned from decades of space operations
2. **Enable interoperability** -- by defining common interfaces, data formats, and protocols
3. **Reduce cost** -- by providing proven design approaches rather than re-inventing solutions
4. **Satisfy regulatory requirements** -- by demonstrating compliance with national and international obligations
5. **Facilitate technology transfer** -- by establishing a common engineering language

> **Industry Practice:** The loss of the Mars Climate Orbiter (1999) is the canonical example of what happens without rigorous interface standards. Lockheed Martin's ground software produced thruster force data in pound-force seconds, while NASA's navigation software expected Newton-seconds. The spacecraft entered the Martian atmosphere at 57 km altitude instead of the planned 226 km and was destroyed. Total loss: $327.6M. This failure directly led to NASA's strengthening of Process 12 (Interface Management) in NPR 7123.1D. The lesson: standards and interface control are not bureaucratic overhead -- they are mission-critical.

#### 1.2 The Major Standard Frameworks

Three major standard frameworks govern space activities globally:

| Framework | Scope | Typical Adopter | Document Count |
|-----------|-------|----------------|---------------|
| **ECSS** (European Cooperation for Space Standardization) | Full lifecycle, all disciplines | ESA, European industry, CSA (partial) | 144 standards + 56 handbooks |
| **NASA Technical Standards** | NASA programs and projects | NASA centres, US contractors | NPR/NPD/NASA-STD series |
| **ISO TC 20/SC 14** | Space systems and operations | International (reference standard) | ~40 standards |

These frameworks are not mutually exclusive. Many missions (including Canadian ones) adopt a tailored combination: ECSS for systems engineering and product assurance, NASA standards for specific technical domains, and ISO for debris mitigation.

---

### 2. ECSS Standard Hierarchy (40 min)

#### 2.1 Structure

The ECSS system organises standards into four branches, each with three levels:

<!-- SVG DIAGRAM: ECSS Standard Hierarchy -->

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" style="max-width:800px; font-family: 'Segoe UI', Arial, sans-serif; background: #fafafa; border: 1px solid #ddd; border-radius: 8px;">
  <!-- Title -->
  <text x="400" y="28" text-anchor="middle" font-size="15" font-weight="bold" fill="#1a1a2e">ECSS Standard Hierarchy</text>

  <!-- Top level: ECSS-S (System) -->
  <rect x="300" y="45" width="200" height="40" rx="6" fill="#37474f" stroke="#263238" stroke-width="2"/>
  <text x="400" y="70" text-anchor="middle" font-size="12" fill="white" font-weight="bold">ECSS-S: System Level</text>

  <!-- Branch boxes -->
  <rect x="30" y="130" width="160" height="40" rx="6" fill="#1565c0" stroke="#0d47a1" stroke-width="2"/>
  <text x="110" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">M: Management</text>

  <rect x="220" y="130" width="160" height="40" rx="6" fill="#2e7d32" stroke="#1b5e20" stroke-width="2"/>
  <text x="300" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">E: Engineering</text>

  <rect x="410" y="130" width="160" height="40" rx="6" fill="#e65100" stroke="#bf360c" stroke-width="2"/>
  <text x="490" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">Q: Product Assurance</text>

  <rect x="600" y="130" width="160" height="40" rx="6" fill="#6a1b9a" stroke="#4a148c" stroke-width="2"/>
  <text x="680" y="155" text-anchor="middle" font-size="11" fill="white" font-weight="bold">U: Sustainability</text>

  <!-- Connecting lines from S to branches -->
  <line x1="350" y1="85" x2="110" y2="130" stroke="#555" stroke-width="1.5"/>
  <line x1="380" y1="85" x2="300" y2="130" stroke="#555" stroke-width="1.5"/>
  <line x1="420" y1="85" x2="490" y2="130" stroke="#555" stroke-width="1.5"/>
  <line x1="450" y1="85" x2="680" y2="130" stroke="#555" stroke-width="1.5"/>

  <!-- Level descriptions for M branch -->
  <rect x="10" y="195" width="180" height="30" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="100" y="215" text-anchor="middle" font-size="9" fill="#0d47a1">ST: Standard (SHALL)</text>

  <rect x="10" y="235" width="180" height="30" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="100" y="255" text-anchor="middle" font-size="9" fill="#0d47a1">HB: Handbook (guidance)</text>

  <rect x="10" y="275" width="180" height="30" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="1"/>
  <text x="100" y="295" text-anchor="middle" font-size="9" fill="#0d47a1">TM: Technical Memo</text>

  <!-- Key M standards -->
  <text x="20" y="325" font-size="9" fill="#333" font-weight="bold">Key M standards:</text>
  <text x="20" y="340" font-size="8" fill="#555">ECSS-M-ST-10C: Project Management</text>
  <text x="20" y="353" font-size="8" fill="#555">ECSS-M-ST-40C: Configuration Mgmt</text>
  <text x="20" y="366" font-size="8" fill="#555">ECSS-M-ST-80C: Risk Management</text>

  <!-- Level descriptions for E branch -->
  <rect x="205" y="195" width="190" height="30" rx="4" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1"/>
  <text x="300" y="215" text-anchor="middle" font-size="9" fill="#1b5e20">ST: Standard (SHALL)</text>

  <rect x="205" y="235" width="190" height="30" rx="4" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1"/>
  <text x="300" y="255" text-anchor="middle" font-size="9" fill="#1b5e20">HB: Handbook (guidance)</text>

  <!-- Key E standards -->
  <text x="210" y="290" font-size="9" fill="#333" font-weight="bold">Key E standards:</text>
  <text x="210" y="305" font-size="8" fill="#555">ECSS-E-ST-10C: SE General</text>
  <text x="210" y="318" font-size="8" fill="#555">ECSS-E-ST-20C: Electrical &amp; Electronic</text>
  <text x="210" y="331" font-size="8" fill="#555">ECSS-E-ST-31C: Thermal Control</text>
  <text x="210" y="344" font-size="8" fill="#555">ECSS-E-ST-32C: Structures</text>
  <text x="210" y="357" font-size="8" fill="#555">ECSS-E-ST-33-01C: Mechanisms</text>
  <text x="210" y="370" font-size="8" fill="#555">ECSS-E-ST-35C: Propulsion</text>
  <text x="210" y="383" font-size="8" fill="#555">ECSS-E-ST-40C: Software</text>
  <text x="210" y="396" font-size="8" fill="#555">ECSS-E-ST-50C: Communications</text>
  <text x="210" y="409" font-size="8" fill="#555">ECSS-E-ST-60C: Control</text>
  <text x="210" y="422" font-size="8" fill="#555">ECSS-E-ST-70C: Ground Systems</text>

  <!-- Key Q standards -->
  <text x="415" y="195" font-size="9" fill="#333" font-weight="bold">Key Q standards:</text>
  <text x="415" y="210" font-size="8" fill="#555">ECSS-Q-ST-10C: PA Management</text>
  <text x="415" y="223" font-size="8" fill="#555">ECSS-Q-ST-20C: QA</text>
  <text x="415" y="236" font-size="8" fill="#555">ECSS-Q-ST-30C: Dependability</text>
  <text x="415" y="249" font-size="8" fill="#555">ECSS-Q-ST-40C: Safety</text>
  <text x="415" y="262" font-size="8" fill="#555">ECSS-Q-ST-60C: EEE Components</text>
  <text x="415" y="275" font-size="8" fill="#555">ECSS-Q-ST-70C: Materials &amp; Processes</text>

  <!-- Key U standards -->
  <text x="605" y="195" font-size="9" fill="#333" font-weight="bold">Key U standards:</text>
  <text x="605" y="210" font-size="8" fill="#555">ECSS-U-AS-10C: Adoption Notice</text>
  <text x="605" y="223" font-size="8" fill="#555">for ISO 24113 (debris mitigation)</text>
  <text x="605" y="248" font-size="8" fill="#555">ECSS-U-AS-10C Rev.2:</text>
  <text x="605" y="261" font-size="8" fill="#555">Space sustainability requirements</text>

  <!-- Legend -->
  <rect x="500" y="380" width="280" height="55" rx="4" fill="#fff9c4" stroke="#f9a825" stroke-width="1"/>
  <text x="510" y="397" font-size="9" fill="#333" font-weight="bold">Naming convention:</text>
  <text x="510" y="412" font-size="8" fill="#555">ECSS-[Branch]-[Type]-[Number][Level]</text>
  <text x="510" y="425" font-size="8" fill="#555">Example: ECSS-E-ST-10C = Engineering-Standard-10-Level C</text>
</svg>

#### 2.2 The Four Branches

| Branch | Code | Scope | Example Standard |
|--------|------|-------|-----------------|
| **Management** | M | Project management, planning, reviews, configuration management, risk management | ECSS-M-ST-10C Rev.1 (Space Project Management) |
| **Engineering** | E | Technical disciplines: systems, structures, thermal, EPS, comms, AOCS, software, ground | ECSS-E-ST-10C (Systems Engineering General Requirements) |
| **Product Assurance** | Q | Quality, reliability, safety, EEE components, materials, contamination | ECSS-Q-ST-10C (Product Assurance Management) |
| **Sustainability** | U | Space debris mitigation, end-of-life disposal, space environment protection | ECSS-U-AS-10C Rev.2 (adoption of ISO 24113) |

#### 2.3 Document Types

| Type | Code | Meaning | Obligation |
|------|------|---------|-----------|
| **Standard** | ST | Contains "shall" requirements -- mandatory when invoked | Must comply or formally request a waiver |
| **Handbook** | HB | Contains guidance, best practices, worked examples | Advisory -- not mandatory but strongly recommended |
| **Technical Memorandum** | TM | Contains background information, state of the art | Informative only |

#### 2.4 Tailoring

A critical concept in ECSS (and all standard frameworks) is **tailoring** -- the process of selecting which standards and which requirements within those standards apply to a given project.

ECSS-S-ST-00C defines three tailoring levels:

| Tailoring Level | Description | Typical Application |
|----------------|-------------|-------------------|
| **Full application** | All requirements of the invoked standard apply | Large ESA missions (Sentinel, JUICE) |
| **Partial application** | Selected clauses apply; others are waived with rationale | Medium missions, CSA projects |
| **Not applicable** | Standard is not invoked for this project | CubeSat missions, technology demonstrators |

The tailoring rationale is documented in the **Product Assurance and Safety Plan (PASP)** and the **Systems Engineering Management Plan (SEMP)**.

> **Key Equation:** The cost of standards compliance scales non-linearly with mission class. A rough relationship observed in ESA studies:
>
> $C_{compliance} \approx k \cdot M_{SC}^{0.7} \cdot N_{standards}^{0.3}$
>
> Where $M_{SC}$ is the spacecraft dry mass (kg), $N_{standards}$ is the number of invoked standards, and $k$ is a constant dependent on the organisation's maturity. For a 10 kg CubeSat invoking 5 standards, compliance costs are roughly 5--10% of mission cost. For a 1000 kg satellite invoking 40 standards, compliance costs can reach 15--20%.

---

### 3. Key ECSS Engineering Standards (30 min)

#### 3.1 Systems Engineering (ECSS-E-ST-10C)

This is the master engineering standard, equivalent to NASA's NPR 7123.1D. It defines:
- System engineering processes and activities
- Requirements engineering (writing, verification, traceability)
- Functional analysis and decomposition
- Interface management
- Configuration management (technical aspects)

| ECSS-E-ST-10C Concept | NASA Equivalent | Key Difference |
|----------------------|----------------|----------------|
| System requirements specification | Technical requirements baseline | ECSS requires a formal Requirements Specification Document (RSD) |
| Functional analysis | Logical decomposition (Process 3) | Similar scope |
| Verification matrix | Requirements verification matrix | ECSS uses a formal DRD (Document Requirements Definition) |
| Design justification file | Design solution baseline | ECSS requires a DJF that traces every design decision |

#### 3.2 Key Subsystem Standards

| Standard | Discipline | Key Requirements | NASA Equivalent |
|----------|-----------|-----------------|----------------|
| ECSS-E-ST-20C | Electrical & Electronic | EPS design, grounding, EMC, harness | NASA-STD-4003A (EEE), NASA-HDBK-4001 |
| ECSS-E-ST-31C | Thermal Control | Thermal design, analysis, testing | NASA-STD-5001B (Structural Design) |
| ECSS-E-ST-32C | Structures | Structural design, factors of safety, testing | NASA-STD-5001B, GEVS (GSFC-STD-7000A) |
| ECSS-E-ST-33-01C | Mechanisms | Mechanism design, testing, lubrication | NASA-STD-5017 |
| ECSS-E-ST-35C | Propulsion | Propulsion system design, testing | -- |
| ECSS-E-ST-40C | Software | SW development, verification, FDIR | NASA-STD-8739.8 |
| ECSS-E-ST-50C | Communications | Comms system design, link budget, protocols | CCSDS standards |
| ECSS-E-ST-60C | Control | AOCS design, pointing, navigation | -- |
| ECSS-E-ST-70C | Ground Systems | Ground segment design, operations | CCSDS standards |

#### 3.3 Structural Design Requirements (Example)

To illustrate the depth of ECSS standards, consider the structural design requirements from ECSS-E-ST-32C:

| Requirement | Value | Rationale |
|-------------|-------|-----------|
| Factor of Safety (FoS) -- Yield | $\geq 1.25$ | Prevent permanent deformation under limit loads |
| Factor of Safety -- Ultimate | $\geq 1.5$ | Prevent structural failure under ultimate loads |
| Qualification loads | $1.25 \times$ limit loads | Demonstrate margin beyond expected environment |
| First natural frequency (axial) | $> 25$ Hz typical (launcher-dependent) | Avoid coupling with launcher modes |
| First natural frequency (lateral) | $> 10$ Hz typical (launcher-dependent) | Avoid coupling with launcher modes |

> **Key Equation:** The margin of safety (MoS) is defined as:
>
> $MoS = \frac{\sigma_{allowable}}{FoS \times \sigma_{applied}} - 1$
>
> A positive MoS ($MoS > 0$) indicates the structure meets the requirement. A MoS of 0.0 means the structure exactly meets the requirement with no margin to spare.
>
> Example: If the allowable stress is 280 MPa, the applied stress is 150 MPa, and the FoS is 1.5:
>
> $MoS = \frac{280}{1.5 \times 150} - 1 = \frac{280}{225} - 1 = 0.244$

---

### 4. NASA Standards Comparison (20 min)

#### 4.1 NASA Technical Standards Architecture

NASA's standards are organised differently from ECSS. Key document types:

| Type | Code | Example | Obligation |
|------|------|---------|-----------|
| **NASA Policy Directive** | NPD | NPD 8700.1 (Safety and Mission Assurance) | Mandatory for all NASA programs |
| **NASA Procedural Requirement** | NPR | NPR 7123.1D (SE Processes) | Mandatory; defines processes and requirements |
| **NASA Technical Standard** | NASA-STD | NASA-STD-5001B (Structural Design) | Mandatory when invoked |
| **NASA Handbook** | NASA-HDBK | NASA-HDBK-4001 (EEE Parts) | Advisory guidance |
| **Special Publication** | SP | SP-2016-6105 (SEH) | Reference text |

#### 4.2 Cross-Reference Table

| Domain | ECSS Standard | NASA Standard | ISO Standard |
|--------|--------------|--------------|-------------|
| Systems Engineering | ECSS-E-ST-10C | NPR 7123.1D, SP-2016-6105 | ISO 15288 |
| Project Management | ECSS-M-ST-10C | NPR 7120.5F | ISO 21500 |
| Configuration Management | ECSS-M-ST-40C | NPR 7120.5F Ch. 4 | ISO 10007 |
| Risk Management | ECSS-M-ST-80C | NPR 8000.4B | ISO 31000 |
| Structural Design | ECSS-E-ST-32C | NASA-STD-5001B | -- |
| Debris Mitigation | ECSS-U-AS-10C | NASA-STD-8719.14A | ISO 24113 |
| Cleanliness | ECSS-Q-ST-70-01C | NASA-SN-C-0005 | ISO 14644 |
| Software | ECSS-E-ST-40C | NASA-STD-8739.8 | ISO 12207 |

---

## Part 2: Launch Interfaces, Debris Mitigation & International Law (Wednesday -- 2 hours)

---

### 5. CDS Rev 14 -- Launch Vehicle Interface Standard (30 min)

#### 5.1 What is the CDS?

The **Cubesat Design Specification (CDS)**, maintained by the California Polytechnic State University (Cal Poly) and updated by the CubeSat community, defines the mechanical, electrical, and operational interfaces between CubeSats and their deployment systems (P-PODs, ISIPOD, etc.).

[Source: CDS Rev 14, 2022, available via Cal Poly CubeSat Program]

#### 5.2 Key CDS Requirements

| Parameter | CDS Rev 14 Requirement | Rationale |
|-----------|----------------------|-----------|
| **Unit dimensions** | $100 \times 100 \times 113.5$ mm per U | Standard deployer rail spacing |
| **Mass per U** | $\leq 2.0$ kg (with waiver up to 2.66 kg for some deployers) | Deployer spring mechanism limits |
| **Rail material** | Hard-anodised aluminium (7075 or 6061-T6) | Deployer contact surface compatibility |
| **Centre of gravity** | Within 2 cm of geometric centre | Deployment dynamics, tumble rate control |
| **Deployables** | Must be constrained during launch; no protrusion beyond CubeSat envelope | Protect adjacent payloads in deployer |
| **Separation springs** | Prohibited on CubeSat (deployer provides) | Standardised deployment mechanism |
| **RF silence** | No RF transmission until 30 minutes after deployment | Avoid interference with launch vehicle |
| **Deployment switches** | Minimum 1 per deployable; 2 for redundancy | Prevent premature deployment |
| **Battery charge state** | Fully charged (recommended); charging from deployer not available | No power interface with deployer |
| **Propulsion** | If present: must be inhibited by 3 independent inhibits; no toxic propellants | Safety of primary payload and deployer |

#### 5.3 Form Factors

| Form Factor | Dimensions (mm) | Mass Limit | Typical Applications |
|------------|-----------------|------------|---------------------|
| 1U | 100 x 100 x 113.5 | 2.0 kg | Technology demonstrators, IoT nodes |
| 1.5U | 100 x 100 x 170.2 | 3.0 kg | Enhanced technology demonstrators |
| 2U | 100 x 100 x 227.0 | 4.0 kg | Simple instruments, store-and-forward |
| 3U | 100 x 100 x 340.5 | 6.0 kg | Standard EO/science missions |
| 6U | 100 x 226.3 x 340.5 | 12.0 kg | Advanced EO, communications |
| 12U | 226.3 x 226.3 x 340.5 | 24.0 kg | High-performance missions |
| 16U | 226.3 x 226.3 x 454.0 | 32.0 kg | Near-microsatellite capability |

#### 5.4 Rideshare Launch Interfaces

For non-CubeSat smallsats (microsatellites 10--200 kg), the interface standard depends on the launch provider:

| Launch Provider | Interface Standard | Adapter Type | Key Document |
|----------------|-------------------|-------------|-------------|
| SpaceX (Rideshare) | ESPA-class | 15" or 24" ESPA port | SpaceX Rideshare User's Guide |
| Rocket Lab (Electron) | Custom separation system | Rocket Lab-provided | Electron Payload User's Guide |
| Arianespace (Vega-C) | ASAP-S | Multi-payload adapter | Vega-C User Manual |
| ISRO (PSLV) | Custom adapter | ISRO-provided | PSLV User Manual |

> **Industry Practice:** Planet Labs' SuperDove constellation (150+ satellites) uses a standardised 3U-plus form factor that is CDS-compliant but extends the standard with a custom deployer arrangement for batch deployment. Each SuperDove satellite (mass ~5.8 kg) carries a multispectral imager with 8 bands and ~3m GSD. The standardisation of the bus design enabled a manufacturing rate of 2+ satellites per week -- only possible because the CDS provides a stable interface baseline.

---

### 6. Space Debris Mitigation (40 min)

#### 6.1 The Debris Problem

As of 2025, there are approximately:
- **36,500+** tracked objects larger than 10 cm in Earth orbit
- **1,000,000+** estimated objects 1--10 cm (untracked, lethal to spacecraft)
- **130,000,000+** estimated objects 1 mm -- 1 cm (can damage components)

The debris population is growing due to collisions (the Kessler Syndrome), anti-satellite tests (e.g., Chinese ASAT 2007: 3,500+ tracked fragments), and the rapid growth of mega-constellations.

[Source: ESA Space Debris Office, Annual Report 2024; NASA ODPO Orbital Debris Quarterly News]

#### 6.2 Debris Mitigation Guidelines Hierarchy

| Level | Document | Scope | Status |
|-------|----------|-------|--------|
| **International voluntary** | IADC Space Debris Mitigation Guidelines (Rev 3, 2021) | Global best practice | Advisory; adopted by COPUOS |
| **International standard** | ISO 24113:2023 | Requirements for debris mitigation | Standard; invoked by many agencies |
| **European standard** | ECSS-U-AS-10C Rev.2 | ECSS adoption notice for ISO 24113 | Mandatory for ESA missions |
| **US regulation** | FCC 47 CFR 25.114(d)(14) | Post-mission disposal for US-licensed satellites | Legally binding for FCC licensees |
| **NASA standard** | NASA-STD-8719.14A | NASA process for limiting orbital debris | Mandatory for NASA missions |
| **ESA requirement** | ESA/ADMIN/IPOL(2023)2 | Clean Space requirements | Mandatory for ESA missions (2023+) |

#### 6.3 Key Debris Mitigation Requirements

| Requirement | Source | Value | Notes |
|-------------|--------|-------|-------|
| **Post-mission disposal** | IADC, ISO 24113 | $\leq 25$ years | Voluntary guideline; being tightened |
| **Post-mission disposal** | FCC (2024+) | $\leq 5$ years | Legally binding for FCC-licensed sats |
| **Probability of successful disposal** | ISO 24113 | $\geq 0.9$ | Must demonstrate reliability of deorbit mechanism |
| **Casualty risk on re-entry** | NASA-STD-8719.14A | $\leq 1:10{,}000$ per event | Drives material selection and design-for-demise |
| **Collision avoidance probability** | IADC | $< 10^{-4}$ per year (cumulative) | Drives orbit selection and manoeuvre capability |
| **Passivation** | ISO 24113, ECSS-U-AS-10C | All stored energy sources depleted at EOL | Batteries, pressure vessels, wheels, RF |

#### 6.4 Post-Mission Disposal Options

| Method | Applicable Orbit | Mechanism | Time to Re-entry |
|--------|-----------------|-----------|------------------|
| **Atmospheric drag (natural)** | LEO < 600 km | Natural orbital decay | Months to years |
| **Atmospheric drag (augmented)** | LEO < 700 km | Drag sail, drag tether | Weeks to years |
| **Propulsive deorbit** | LEO | Thrusters lower perigee to ~200 km | Days |
| **Graveyard orbit** | GEO | Raise orbit ~300 km above GEO | Indefinite (not re-entry) |
| **Heliocentric disposal** | Beyond GEO | Escape Earth orbit | N/A |

> **Key Equation:** The orbital lifetime of a satellite in LEO due to atmospheric drag is approximately:
>
> $\tau \approx \frac{C_D \cdot A \cdot \rho \cdot a^2}{2m} \cdot \text{(complex integral)}$
>
> A simpler rule-of-thumb for circular orbits:
>
> $\tau_{years} \approx \frac{h - 200}{30} \cdot \frac{m / A}{50}$
>
> Where $h$ is altitude in km, $m$ is mass in kg, and $A$ is the cross-sectional area in m$^2$. This is very approximate; actual lifetime depends on solar activity (which modulates atmospheric density at high altitudes), drag coefficient, and orbit eccentricity. Use NASA's DAS (Debris Assessment Software) or ESA's DRAMA tool for accurate predictions.
>
> More precisely, the ballistic coefficient is:
>
> $B = \frac{m}{C_D \cdot A}$
>
> Lower $B$ (lighter, larger area) means faster re-entry. A 3U CubeSat ($m \approx 4$ kg, $A \approx 0.03$ m$^2$, $C_D \approx 2.2$) at 400 km has $B \approx 61$ kg/m$^2$ and will re-enter within ~1--3 years depending on solar cycle.

#### 6.5 Practical Implications for Mission Design

| Design Decision | Debris Mitigation Impact |
|----------------|--------------------------|
| Orbit altitude selection | Altitudes > 600 km require active deorbit; > 700 km strongly discouraged for non-manoeuvrable spacecraft |
| Propulsion system | Required for altitudes > 500--600 km to meet 25-year (or 5-year FCC) rule |
| Passivation design | Must design battery disconnect, pressure relief, wheel spin-down circuits |
| Material selection | Aluminium structures preferred for design-for-demise; titanium and carbon fibre survive re-entry |
| Collision avoidance | Manoeuvre capability or conjunction assessment service (e.g., 18th SDS, ESA SSA) needed |

> **Industry Practice:** OneWeb (648 satellites at 1200 km) carries propulsion on every satellite specifically for end-of-life deorbit, since natural decay from 1200 km would take centuries. Each satellite carries sufficient propellant for multiple collision avoidance manoeuvres plus a complete deorbit burn to lower perigee below 300 km. The deorbit operation takes approximately 3 months per satellite.

---

### 7. International Space Law and COPUOS (30 min)

#### 7.1 The UN Space Treaties

The legal framework for space activities is established by five UN treaties negotiated under the Committee on the Peaceful Uses of Outer Space (COPUOS):

| Treaty | Year | Key Provisions | Ratification |
|--------|------|----------------|-------------|
| **Outer Space Treaty (OST)** | 1967 | Space is free for exploration; no national appropriation; states responsible for national activities; liability for damage | 114 parties (incl. Canada) |
| **Rescue Agreement** | 1968 | Return astronauts and space objects | 99 parties |
| **Liability Convention** | 1972 | Launching state liable for damage on Earth (absolute) and in space (fault-based) | 98 parties |
| **Registration Convention** | 1976 | States must register space objects with UN | 72 parties |
| **Moon Agreement** | 1979 | Moon and celestial bodies are "common heritage of mankind" | 18 parties (NOT US, Russia, China) |

#### 7.2 Key Legal Principles for Mission Design

| Principle | Source | Implication |
|-----------|--------|------------|
| **State responsibility** | OST Art. VI | The Government of Canada is internationally responsible for all Canadian space activities, including private/university missions |
| **Authorisation and supervision** | OST Art. VI | Canada must authorise and continuously supervise all non-governmental space activities (this is why RSSSA exists) |
| **Liability** | Liability Convention | Canada (as launching state) is liable for damage caused by Canadian satellites; absolute liability on Earth, fault-based in space |
| **Registration** | Registration Convention | Canada must register all space objects with the UN; CSA maintains the Canadian registry |
| **Non-contamination** | OST Art. IX | Must avoid harmful contamination of space and celestial bodies (planetary protection) |
| **Due regard** | OST Art. IX | Must conduct activities with "due regard" for other states' interests (debris mitigation) |

#### 7.3 COPUOS Long-Term Sustainability Guidelines (2019)

In 2019, COPUOS adopted 21 guidelines for the long-term sustainability of outer space activities. These are voluntary but politically significant:

| Guideline Category | Count | Key Points |
|--------------------|----|------------|
| Policy and regulatory | 7 | Adopt national regulatory frameworks, register space objects, share SSA data |
| Safety of operations | 4 | Conjunction assessment, collision avoidance, re-entry risk assessment |
| International cooperation | 4 | Share debris mitigation best practices, coordinate spectrum use |
| Scientific and technical | 6 | Improve debris models, develop removal technology, research space weather effects |

[Source: A/74/20, Report of COPUOS, 2019, Annex II]

---

### 8. SpaceCDF Compliance Features (20 min)

SpaceCDF tracks compliance through the **Compliance Engineer** position:

| Feature | What It Tracks | Automation Level |
|---------|---------------|-----------------|
| **Standard applicability matrix** | Which ECSS/NASA/ISO standards apply to this mission | Semi-automated (suggests based on mission type) |
| **Debris mitigation compliance** | Post-mission lifetime, passivation plan, casualty risk | Automated (calculates from orbit and mass) |
| **RSSSA checklist** | Licence requirements for Canadian remote sensing missions | Manual (checklist with guidance) |
| **Spectrum filing status** | ISED/ITU filing progress | Manual (status tracking) |
| **Export control classification** | ECCN/USML classification of key components | Manual (per-component) |
| **CDS compliance** | Mechanical/electrical interface compliance with CDS Rev 14 | Semi-automated (checks mass, dimensions, CG) |

**Exercise:** *In SpaceCDF, navigate to the Compliance panel. Review the debris mitigation compliance status for your mission. What orbit altitude would be needed to comply with the FCC 5-year rule without propulsion? Use the tool's orbital lifetime calculator.*

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| ECSS framework | Four branches (M, E, Q, U); three document types (ST, HB, TM); tailoring is essential |
| NASA standards | Organised as NPD/NPR/NASA-STD/NASA-HDBK; broadly equivalent to ECSS |
| CDS Rev 14 | Defines CubeSat mechanical/electrical/operational interfaces; compliance is required for rideshare launch |
| Debris mitigation | IADC 25-year rule; FCC 5-year rule (2024+); passivation required; drives orbit and propulsion design |
| International law | OST establishes state responsibility; Canada liable for all Canadian space activities |
| COPUOS | 21 sustainability guidelines (2019); voluntary but increasingly influential |
| Compliance in SpaceCDF | Tracked through the Compliance Engineer position; automated where possible |

---

## References

1. [ECSS, ECSS-S-ST-00C -- Space Standardization, 2020](https://ecss.nl/standard/ecss-s-st-00c-space-standardization-policy-and-organisation/)
2. [ECSS, ECSS-E-ST-10C -- System Engineering General Requirements, 2009](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
3. [ECSS, ECSS-E-ST-32C Rev.1 -- Structural General Requirements, 2008](https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/)
4. [ECSS, ECSS-U-AS-10C Rev.2 -- Adoption Notice of ISO 24113, 2023](https://ecss.nl/standard/ecss-u-as-10c-rev-2/)
5. [ISO, ISO 24113:2023 -- Space Systems: Space Debris Mitigation Requirements, 2023](https://www.iso.org/standard/82450.html)
6. [IADC, IADC-02-01 Rev 3 -- Space Debris Mitigation Guidelines, 2021](https://www.iadc-home.org/documents_public/)
7. [Cal Poly, CubeSat Design Specification (CDS) Rev 14, 2022](https://www.cubesat.org/cubesatinfo)
8. [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016](https://www.nasa.gov/reference/systems-engineering-handbook/)
9. [NASA, NASA-STD-8719.14A -- Process for Limiting Orbital Debris, 2019](https://standards.nasa.gov/standard/oce/nasa-std-871914)
10. [UNOOSA, A/74/20 -- Report of COPUOS, 2019](https://www.unoosa.org/oosa/en/ourwork/copuos/2019/index.html)
11. [UNOOSA, Outer Space Treaty, 1967](https://www.unoosa.org/oosa/en/ourwork/spacelaw/treaties/outerspacetreaty.html)
12. [FCC, 47 CFR 25.114 -- Satellite Applications](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-25)

---

# Session 1.4: Mission Needs, Stakeholder Analysis & Trade Studies

**Duration:** 6 hours (Thursday + Friday)
**Prerequisites:** Sessions 1.1--1.3
**References:**
- [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016 -- Sections 4.1, 4.4, 6.8](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [NASA, NPR 7123.1D -- Sections 3.2.1 (Process 1), 3.2.4 (Process 4), 3.5.8 (Process 17)](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
- [ECSS, ECSS-E-ST-10C -- Section 5.1 (Requirements Engineering)](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
- [ECSS, ECSS-M-ST-10C Rev.1 -- Section 5.3 (Review Process)](https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/)
- [Wertz, J.R. et al., Space Mission Engineering: The New SMAD (SMAD4), Microcosm Press, 2011 -- Chapters 1--3](https://www.microcosminc.com/)
- [NASA SEH Appendix C -- How to Write a Good Requirement](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [NASA SEH Appendix S -- ConOps Outline](https://www.nasa.gov/reference/systems-engineering-handbook/)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Write a clear problem statement that defines the mission need without prescribing a solution
2. Identify and categorise mission stakeholders using a structured analysis matrix
3. Define mission objectives with measurable success criteria and trace them through the MoE/MoP/TPM hierarchy
4. Structure and execute a trade study using weighted scoring methods (Decision Analysis -- Process 17)
5. Evaluate space vs non-space alternatives objectively and document the decision rationale
6. Design a Concept of Operations (ConOps) including mission phases, operational modes, and data flow
7. Use SpaceCDF Steps 1--2 and the Trade Studies tab to capture and evaluate mission concepts

---

## Part 1: Mission Need & Stakeholder Analysis (Thursday AM -- 2 hours)

---

### 1. The Problem Statement (30 min)

#### 1.1 Why Start with the Problem?

NASA SEH Section 4.1.1 states: *"Clearly define the problem before solving it."*

The single most common failure mode in mission design is not technical -- it is **solving the wrong problem**. Teams jump to solutions ("we need a 6U CubeSat at 500 km") before articulating the actual need ("agricultural monitoring in sub-Saharan Africa requires 10 m resolution multispectral imagery every 5 days"). This premature commitment to a solution:

- Closes off potentially superior alternatives (commercial data purchase, aerial surveys, ground sensors)
- Introduces unnecessary constraints that drive up cost and risk
- Makes it impossible to evaluate mission success (success against what?)
- Violates the fundamental SE principle of **WHAT before HOW**

[Source: NASA SEH Section 4.1; NASA SEH Appendix C -- "How to Write a Good Requirement"]

#### 1.2 Structure of a Good Problem Statement

A rigorous problem statement answers four questions:

| Question | Content | Example |
|----------|---------|---------|
| **What is the problem?** | The capability gap -- what is missing or inadequate | "Lack of timely, affordable multispectral imagery at sufficient resolution and revisit" |
| **Who is affected?** | Stakeholders and end users who suffer from the gap | "Agricultural monitoring agencies in sub-Saharan Africa" |
| **What is the impact?** | Consequence of not solving it -- quantified if possible | "Delayed or inaccurate crop assessments affecting food aid allocation for 300M people" |
| **What constraints exist?** | Budget, schedule, political, regulatory, or technical limitations | "Budget: <$10M total mission cost; timeline: 3 years to first data" |

#### 1.3 Good vs Bad Problem Statements

**Example -- GOOD:**
> "Agricultural monitoring agencies in sub-Saharan Africa lack timely, affordable access to multispectral imagery at sufficient resolution ($\leq 10$ m) and revisit rate ($\leq 5$ days) to support crop yield prediction and food security planning. Current Sentinel-2 data provides 10 m resolution but only 5-day revisit at the equator, and cloud cover reduces usable observations to approximately 60%. The consequence is delayed or inaccurate crop assessments affecting food aid allocation for 300 million people. Budget constraint: total mission cost $< \$10$M; first data delivery within 3 years."

**Example -- BAD:**
> "We need a 6U CubeSat with a multispectral imager at 500 km SSO."

The bad example prescribes a solution (6U CubeSat, SSO), specifies a design parameter (500 km), and says nothing about the actual problem. It is a **solution statement**, not a problem statement.

#### 1.4 The WHAT vs HOW Principle

At the mission need level, everything should describe **WHAT** is needed, not **HOW** to achieve it:

| WHAT (correct at this stage) | HOW (premature at this stage) |
|------------------------------|-------------------------------|
| "10 m resolution imagery" | "Use a 15 cm aperture telescope" |
| "Daily revisit at equator" | "Deploy a Walker delta constellation of 12 satellites" |
| "Data within 6 hours of acquisition" | "Use X-band downlink at 150 Mbps to 3 ground stations" |
| "Total cost under $10M" | "Use COTS components exclusively" |
| "5-year operational lifetime" | "Select radiation-hardened components" |

The HOW column is not wrong -- these are all reasonable design decisions. But they belong in later phases (Phase A/B), not in the problem statement. Fixing the HOW prematurely eliminates design freedom and may lead to suboptimal solutions.

**Discussion prompt:** *Why is it harmful to specify HOW at this stage? What design options does it close off?*

---

### 2. Stakeholder Identification & Analysis (30 min)

#### 2.1 Who is a Stakeholder?

NASA SEH Section 4.1.2 defines stakeholders as "all parties who have a legitimate interest in the system throughout its lifecycle." This is broader than just the end user -- it includes everyone who affects or is affected by the mission.

#### 2.2 Stakeholder Categories for Space Missions

| Category | Examples | Typical Needs | Typical Constraints |
|----------|---------|---------------|-------------------|
| **End Users** | Scientists, farmers, shipping companies, emergency responders | Data quality, resolution, latency, format, accessibility | Data rights, training, infrastructure |
| **Operators** | Mission control centre, ground station operators | Operability, automation level, staffing, training | Budget for operations, personnel availability |
| **Sponsors / Funders** | Space agency (CSA), university, commercial investor, DND | Return on investment, schedule adherence, risk profile | Budget cap, political timelines, reporting requirements |
| **Regulatory** | ISED, ITU, FCC, export control (GAC) | Compliance with spectrum, debris, RSSSA, export regulations | Licensing timelines, filing requirements |
| **Launch Provider** | SpaceX, Rocket Lab, ISRO, Arianespace | CDS compliance, mass/volume limits, schedule, payment | Interface requirements, launch window, manifesting |
| **Ground Segment** | KSAT, SSC, SatNOGS, own stations | Frequency compatibility, data volume, contact time | Station availability, geographic coverage |
| **Data Consumers** | Archives (e.g., EODMS), APIs, partner agencies | Data format (NetCDF, GeoTIFF), metadata standards, timeliness | Format standards, distribution agreements |
| **General Public** | Taxpayers (for government-funded missions) | Value for money, transparency, societal benefit | Political expectations, public engagement |
| **Orbital Environment** | Other satellite operators, debris community | Debris mitigation, spectrum cleanliness, collision avoidance | IADC guidelines, ISO 24113, FCC 5-year rule |

#### 2.3 Stakeholder Analysis Matrix

For each stakeholder, capture five attributes:

| Attribute | Description | Scale |
|-----------|-------------|-------|
| **Name / Role** | Who are they? | Text |
| **Needs** | What do they require from the mission? | Text (specific, measurable where possible) |
| **Constraints** | What limitations do they impose? | Text (mandatory vs desirable) |
| **Priority** | How critical is satisfying this stakeholder? | Primary (must satisfy) / Secondary (should satisfy) / Tertiary (nice to have) |
| **Influence** | How much power do they have over the mission? | High / Medium / Low |

> **Industry Practice:** For the RADARSAT Constellation Mission (RCM), the stakeholder analysis identified over 20 distinct stakeholder groups, including DND (maritime surveillance), Environment Canada (sea ice monitoring), Agriculture and Agri-Food Canada (crop monitoring), Natural Resources Canada (forestry), Public Safety Canada (disaster response), and international partners. Each stakeholder had different priority imaging modes, coverage requirements, and data latency needs. The systems engineering challenge was to design a 3-satellite constellation that satisfied all these needs within a single system architecture -- a classic example of multi-stakeholder optimisation.

**Exercise:** *Complete Part A of Worksheet 1.4 -- identify at least 4 stakeholders for your team's mission and fill in the analysis matrix.*

---

### 3. Mission Objectives and the MoE/MoP/TPM Hierarchy (30 min)

#### 3.1 From Need to Objectives

Objectives translate the problem statement into specific, testable goals. Each objective must have:

| Attribute | Description | Example |
|-----------|-------------|---------|
| **Text** | Clear statement of what the mission will achieve | "Provide 10 m GSD multispectral imagery over the target region" |
| **Priority** | Primary (mission fails without) or secondary (desirable) | Primary |
| **Measurable criterion** | How you know the objective is met -- a number with a unit | "GSD $\leq$ 10 m at nadir, 4+ spectral bands, revisit $\leq$ 5 days" |
| **Type** | Category of objective | Observation, communication, navigation, science, technology demonstration |

#### 3.2 Writing Good Objectives

| Good Objective | Why It Is Good |
|---------------|---------------|
| "Provide 10 m GSD multispectral imagery with 4+ bands for the target region (30S--30N), with $\leq$ 5-day revisit and $\leq$ 24 h data latency" | Specific (10 m, 4 bands, geographic scope), measurable (all criteria have numbers + units), relevant to agriculture, achievable with CubeSat technology |
| "Achieve 99.5% AIS ship detection probability in the North Atlantic within 30 minutes of ship transmission" | Specific (AIS, North Atlantic), measurable (99.5%, 30 min), relevant to maritime safety |

| Bad Objective | Why It Is Bad |
|--------------|-------------|
| "Take pictures from space" | Not specific, not measurable, no criterion for success |
| "Build a 3U CubeSat" | This is a solution, not an objective -- it says nothing about what the mission should accomplish |
| "Demonstrate new technology" | What technology? What does "demonstrate" mean? How do you know it succeeded? |

#### 3.3 The MoE / MoP / TPM Hierarchy

These three measures form a chain from operational need to tracked design parameter:

[Source: NASA SEH Section 4.1.4, Section 4.2.4, Section 6.7.3]

| Measure | What It Measures | Who Sets It | Example | When Evaluated |
|---------|-----------------|-------------|---------|---------------|
| **MoE** (Measure of Effectiveness) | How well the system satisfies the operational need | Users / stakeholders | "% of crop assessments delivered within 5 days of acquisition" | Phase E (operations) |
| **MoP** (Measure of Performance) | Technical performance of the system | Systems engineer | "GSD $\leq$ 10 m at nadir" | Phase C/D (verification) |
| **TPM** (Technical Performance Measure) | Design parameter tracked over time | Design team | "Current best estimate of imager mass vs allocation (1.5 kg target)" | All phases (continuous) |

The hierarchy flows downward:

```
Stakeholder Need
  -> MoE (operational effectiveness)
    -> Mission Objective
      -> MoP (technical performance)
        -> Technical Requirement ("shall" statement)
          -> TPM (tracked design parameter)
```

> **Key Equation:** Measures of Effectiveness often involve probability and time, connecting to system-level performance:
>
> $MoE = P_{detection} \times P_{data\_delivery} \times f(T_{latency})$
>
> For an Earth observation mission:
>
> $MoE_{coverage} = \frac{A_{imaged\_per\_revisit}}{A_{total\_target}} \times (1 - P_{cloud})$
>
> Where $A_{imaged\_per\_revisit}$ depends on swath width and orbit ground track spacing, $A_{total\_target}$ is the target area, and $P_{cloud}$ is the cloud cover probability.

**Exercise:** *For one of your objectives, trace the full hierarchy from stakeholder need through MoE, MoP, and TPM. Complete Part B of Worksheet 1.4.*

---

### 4. From Need to Design: The Flow (20 min)

Show how the mission need flows through to design decisions without the need itself prescribing the design:

<!-- SVG DIAGRAM: Need to Design Flow -->

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 520" style="max-width:700px; font-family: 'Segoe UI', Arial, sans-serif; background: #fafafa; border: 1px solid #ddd; border-radius: 8px;">
  <text x="350" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">From Mission Need to Design Decision</text>

  <!-- Level 1: Problem -->
  <rect x="50" y="45" width="600" height="45" rx="6" fill="#e8eaf6" stroke="#3949ab" stroke-width="2"/>
  <text x="70" y="63" font-size="10" font-weight="bold" fill="#1a237e">PROBLEM</text>
  <text x="70" y="78" font-size="9" fill="#333">"Need 10m imagery, 5-day revisit, &lt;$10M" -- describes WHAT is needed</text>

  <!-- Arrow -->
  <line x1="350" y1="90" x2="350" y2="110" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="105" font-size="8" fill="#888" font-style="italic">objectives derived</text>

  <!-- Level 2: Objective -->
  <rect x="50" y="115" width="600" height="45" rx="6" fill="#c5cae9" stroke="#3949ab" stroke-width="2"/>
  <text x="70" y="133" font-size="10" font-weight="bold" fill="#1a237e">OBJECTIVE</text>
  <text x="70" y="148" font-size="9" fill="#333">"Provide 10m GSD multispectral imagery with &lt;=5 day revisit" -- measurable goal</text>

  <!-- Arrow -->
  <line x1="350" y1="160" x2="350" y2="180" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="175" font-size="8" fill="#888" font-style="italic">mission trade (Process 17)</text>

  <!-- Level 3: Trade Decision -->
  <rect x="50" y="185" width="600" height="45" rx="6" fill="#fff9c4" stroke="#f9a825" stroke-width="2"/>
  <text x="70" y="203" font-size="10" font-weight="bold" fill="#e65100">TRADE DECISION</text>
  <text x="70" y="218" font-size="9" fill="#333">"Dedicated CubeSat -- existing services don't meet revisit+resolution together" -- justified choice</text>

  <!-- Arrow -->
  <line x1="350" y1="230" x2="350" y2="250" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="245" font-size="8" fill="#888" font-style="italic">requirements derived</text>

  <!-- Level 4: Requirement -->
  <rect x="50" y="255" width="600" height="45" rx="6" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>
  <text x="70" y="273" font-size="10" font-weight="bold" fill="#1b5e20">REQUIREMENT</text>
  <text x="70" y="288" font-size="9" fill="#333">"The system shall achieve GSD &lt;= 10m at nadir" -- verifiable "shall" statement</text>

  <!-- Arrow -->
  <line x1="350" y1="300" x2="350" y2="320" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="315" font-size="8" fill="#888" font-style="italic">design analysis</text>

  <!-- Level 5: Design Choice -->
  <rect x="50" y="325" width="600" height="45" rx="6" fill="#e3f2fd" stroke="#1565c0" stroke-width="2"/>
  <text x="70" y="343" font-size="10" font-weight="bold" fill="#0d47a1">DESIGN CHOICE</text>
  <text x="70" y="358" font-size="9" fill="#333">"SSO 500 km gives 10m GSD with 15cm aperture" -- now we specify HOW</text>

  <!-- Arrow -->
  <line x1="350" y1="370" x2="350" y2="390" stroke="#555" stroke-width="2" marker-end="url(#arrowDown)"/>
  <text x="370" y="385" font-size="8" fill="#888" font-style="italic">equipment selection</text>

  <!-- Level 6: Equipment -->
  <rect x="50" y="395" width="600" height="45" rx="6" fill="#fce4ec" stroke="#c62828" stroke-width="2"/>
  <text x="70" y="413" font-size="10" font-weight="bold" fill="#b71c1c">EQUIPMENT</text>
  <text x="70" y="428" font-size="9" fill="#333">"Selected: XYZ Telescope, 15cm aperture, 1.5 kg, 8W" -- component-level HOW</text>

  <!-- Side annotation -->
  <rect x="50" y="460" width="200" height="40" rx="4" fill="#e0e0e0" stroke="#9e9e9e" stroke-width="1"/>
  <text x="150" y="477" text-anchor="middle" font-size="9" fill="#333" font-weight="bold">Each level: team decides.</text>
  <text x="150" y="490" text-anchor="middle" font-size="8" fill="#666">SpaceCDF supports, does not dictate.</text>

  <defs>
    <marker id="arrowDown" markerWidth="8" markerHeight="6" refX="4" refY="6" orient="auto">
      <path d="M0,0 L4,6 L8,0" fill="#555"/>
    </marker>
  </defs>
</svg>

At each level in this hierarchy, the design team makes decisions informed by analysis and trade studies. The tool supports this process with parametric calculations and automated constraint checking, but the team retains decision authority.

---

## Part 2: Trade Study Methodology (Thursday PM -- 2 hours)

---

### 5. Decision Analysis Framework (40 min)

#### 5.1 Process 17: Decision Analysis

NASA SEH Process 17 (Decision Analysis) provides the framework for structured alternative evaluation. Every major design decision should follow this process to ensure decisions are auditable, traceable, and defensible.

[Source: NASA SEH Section 6.8, Process 17: Decision Analysis]

#### 5.2 The Five Elements of a Rigorous Trade Study

| Element | Description | Pitfall to Avoid |
|---------|-------------|-----------------|
| **1. Decision statement** | What are we deciding? Framed as a question. | Too broad ("What should we build?") or too narrow ("Which reaction wheel?") for the current phase |
| **2. Alternatives** | What are the options? Minimum 3, including "do nothing" | Straw-man alternatives designed to lose; failure to include obvious options |
| **3. Criteria** | What matters? Performance, cost, schedule, risk, compliance | Missing a critical criterion; criteria that overlap (double-counting) |
| **4. Weightings** | How important is each criterion? Normalised to sum to 1.0 | All criteria weighted equally (means nothing matters more than anything else); weights set after seeing scores |
| **5. Scoring** | How well does each alternative perform? | Inconsistent scoring scale; anchoring bias; group conformity |

#### 5.3 Weighting Methods

| Method | Procedure | Best When | Limitations |
|--------|-----------|-----------|------------|
| **Pairwise comparison** | Compare criteria two at a time; count wins. Weight = wins / total comparisons | Small number of criteria ($< 8$) | Circular preferences possible; does not capture magnitude |
| **Swing weighting** | For each criterion, assess the value of moving from worst to best case. Normalise. | Criteria have different units and scales | Requires clear understanding of worst/best cases |
| **Direct assignment** | Team discusses and agrees on weights | Quick preliminary assessment | Subjective; dominated by vocal team members |
| **AHP (Analytic Hierarchy Process)** | Pairwise comparison on a 1--9 ratio scale; compute eigenvector | Complex decisions with many stakeholders | Mathematically complex; consistency check needed |

> **Key Equation (Pairwise Comparison):** For $n$ criteria, there are $\frac{n(n-1)}{2}$ pairwise comparisons. The raw weight of criterion $i$ is:
>
> $w_i^{raw} = \sum_{j \neq i} p_{ij}$
>
> Where $p_{ij} = 1$ if criterion $i$ is preferred over $j$, 0.5 for a tie, and 0 if $j$ is preferred. The normalised weight is:
>
> $w_i = \frac{w_i^{raw}}{\sum_{k=1}^{n} w_k^{raw}}$

#### 5.4 Scoring Methods

| Type | Description | Example | When to Use |
|------|-------------|---------|-------------|
| **Quantitative** | Numeric value normalised to 0--1 | Mass: 5 kg scores 0.8, 10 kg scores 0.4 | When hard numbers exist |
| **Qualitative** | Verbal rating mapped to number | "Excellent" = 1.0, "Good" = 0.75, "Fair" = 0.5, "Poor" = 0.25 | When only expert judgment is available |
| **Threshold (go/no-go)** | Pass/fail gate applied before scoring | "TRL $\geq 6$ required" -- below threshold is eliminated | Non-negotiable requirements |

#### 5.5 Weighted Score Calculation

For each alternative $a$ across $n$ criteria:

> **Key Equation:**
>
> $S(a) = \sum_{c=1}^{n} w_c \cdot s(a,c)$
>
> Where $w_c$ is the normalised weight of criterion $c$ and $s(a,c)$ is the normalised score (0--1) of alternative $a$ on criterion $c$.
>
> For "higher is better" criteria:
>
> $s(a,c) = \frac{v(a,c) - v_{min}(c)}{v_{max}(c) - v_{min}(c)}$
>
> For "lower is better" criteria:
>
> $s(a,c) = 1 - \frac{v(a,c) - v_{min}(c)}{v_{max}(c) - v_{min}(c)}$

#### 5.6 Sensitivity Analysis

A trade study result is only meaningful if it is **robust** -- i.e., the ranking does not change with small perturbations in weights or scores. Sensitivity analysis tests this:

| Method | Procedure | What It Reveals |
|--------|-----------|----------------|
| **Weight perturbation** | Vary each weight by $\pm 20\%$, re-normalise, re-score | Which criteria are "swing" criteria that could flip the outcome |
| **Score perturbation** | Vary each score by $\pm 1$ level, re-calculate | Which scores are the most uncertain and impactful |
| **Threshold analysis** | For each criterion, find the weight at which the 2nd-place alternative overtakes the 1st | How much the weights would need to change to reverse the decision |

> **Industry Practice:** For the Iridium NEXT constellation (66 operational + 6 on-orbit spares), the initial trade study for the constellation architecture compared Walker Delta, Walker Star, and hybrid configurations across 12 criteria including global coverage, revisit time, inter-satellite link geometry, launch cost, and orbital debris risk. Sensitivity analysis revealed that the ranking was robust for all weight perturbations up to $\pm 30\%$, giving high confidence in the selected Walker Star configuration at 780 km altitude.

**Exercise:** *Practice the pairwise comparison method by weighting 4 criteria for a lunch restaurant choice: taste, cost, healthiness, speed. Then score 3 options. This builds the skill on a low-stakes example before applying it to mission design.*

---

### 6. Space vs Non-Space Alternatives (30 min)

#### 6.1 The Most Important Trade Study

Before committing to building a satellite, teams must honestly evaluate whether existing solutions meet the need. This is the most important trade study in the mission lifecycle because it determines whether the entire project should proceed.

#### 6.2 Alternative Categories

| Category | Examples | Strengths | Weaknesses |
|----------|---------|-----------|-----------|
| **Existing free data** | Copernicus Sentinel-2, Landsat 8/9 | Zero acquisition cost, proven quality, long archive | Fixed resolution/revisit, no tasking control |
| **Commercial data purchase** | Planet (SuperDove), Maxar (WorldView), ICEYE (SAR) | High resolution, fast tasking, no development risk | Ongoing cost, data rights limitations, vendor dependency |
| **Aerial (drones/aircraft)** | Survey drones, P-3 Orion, Twin Otter | Very high resolution ($< 1$ m), flexible scheduling | Limited area coverage, weather dependent, regulatory constraints |
| **Ground sensors** | IoT networks, weather stations, tide gauges | Continuous monitoring, low per-unit cost | Point measurements only, no spatial coverage |
| **Dedicated satellite** | New CubeSat, SmallSat, or microsatellite | Full control, custom instrument, IP ownership | High cost ($2--50M), development risk, 2--5 year schedule |
| **Constellation** | Multiple dedicated satellites | Global coverage, short revisit ($< 1$ day) | Much higher cost, operational complexity |
| **Hosted payload** | Payload on another operator's bus | Lower cost, shared bus risk | Compromised orbit, limited control, schedule dependency |

#### 6.3 Decision Criteria: When is Space Justified?

**Space is likely NOT the right answer when:**
- Existing free data (Sentinel-2, Landsat) meets resolution and revisit needs
- Coverage requirement is local (drones or aircraft are cheaper and higher resolution)
- Data rate is very low (ground sensors with cellular/satellite IoT backhaul suffice)
- Budget does not support minimum viable satellite cost (~$2M for a basic 3U CubeSat)
- Technology readiness is too low for the available schedule

**Space is likely justified when:**
- Global or wide-area coverage is needed simultaneously
- Persistent monitoring is required (24/7 or very frequent revisit $< 5$ days)
- User needs data ownership and control over acquisition scheduling
- No existing service provides the required measurement type (e.g., specific wavelength, polarisation)
- Regulatory or sovereignty requirements demand national control over the sensor

#### 6.4 Constellation Sizing

For missions requiring short revisit, the number of satellites drives cost:

> **Key Equation:** For a Walker Delta constellation at altitude $h$ with half-swath angle $\eta$, the number of orbital planes $P$ and satellites per plane $S$ needed for revisit time $T_{rev}$ is approximately:
>
> $P \times S \geq \frac{2\pi R_E}{v_{ground} \times T_{rev} \times \tan(\eta)}$
>
> Where $v_{ground} \approx 7.1$ km/s (ground track velocity at 500 km) and $\eta$ is related to the instrument swath width $W$ by $\eta = W / (2 R_E)$ for small angles.
>
> More practically, constellation cost scales sub-linearly due to learning curves:
>
> $C_{total} = C_1 \times \sum_{i=1}^{N} i^{\log_2(L)}$
>
> Where $C_1$ is the first unit cost, $N$ is the number of satellites, and $L$ is the learning curve factor (typically 0.90--0.95 for small batches, 0.85 for large batches like Planet's SuperDove).

---

### 7. Documenting the Trade Decision (20 min)

Every trade study must produce an **auditable decision record**. NASA SEH Process 17 requires documentation of:

| Element | Content | Purpose |
|---------|---------|---------|
| **Decision statement** | What was decided | Clarity |
| **Alternatives considered** | All options evaluated, including rejected ones | Completeness |
| **Criteria and weights** | What mattered and how much | Transparency |
| **Scoring rationale** | Why each alternative received its score | Auditability |
| **Result and recommendation** | The selected alternative and its total score | Decision record |
| **Sensitivity analysis** | Robustness of the result | Confidence |
| **Risks of selected option** | What could go wrong with the chosen approach | Risk awareness |
| **Responsible person and date** | Who decided and when | Accountability |

> **Industry Practice:** The Canadian Hydrographic Service evaluated commercial SAR data (ICEYE, Capella) versus a dedicated satellite for Arctic maritime surveillance. The trade study documented 8 alternatives across 11 criteria, with weights set by a stakeholder panel including DND, Transport Canada, and CCG. The decision to use RCM data supplemented by commercial SAR tasking -- rather than building a new satellite -- saved an estimated $100M while meeting 90% of the maritime domain awareness requirements.

---

## Part 3: Concept of Operations (Friday -- 2 hours)

---

### 8. Mission Architecture (30 min)

#### 8.1 Three Segments of a Space Mission

Every space mission comprises three segments that must be designed together:

| Segment | Components | Key Design Drivers |
|---------|-----------|-------------------|
| **Space Segment** | Platform (bus): EPS, AOCS, OBC, thermal, structure, propulsion. Payload: instrument(s). Communications: TT&C + payload data link. | Mass, power, volume, orbit, lifetime |
| **Ground Segment** | Ground Operations: commanding, telemetry, orbit determination. Payload Data Centre: data reception, processing (L0-L1-L2-L3), archive. | Contact time, data volume, processing capacity |
| **User Segment** | Data products and services. APIs, portals, archives. Training and documentation. | Latency, format, accessibility, user capacity |

#### 8.2 Data Interfaces Between Segments

| Interface | Direction | Band/Protocol | Content |
|-----------|-----------|--------------|---------|
| TM/TC | Space <-> Ground Ops | S-band (typical) | Housekeeping telemetry, telecommands |
| Payload data | Space -> Data Centre | X-band or Ka-band | Science/imagery data (high volume) |
| Orbit/TLE | Ground Ops -> Data Centre | Network | Geolocation metadata for data products |
| Data products | Data Centre -> Users | Internet/API | Processed imagery (L2/L3), analytics |

#### 8.3 Interactive Architecture Diagram

SpaceCDF provides a **drag-and-drop architecture diagram editor** in the ConOps tab:

| Symbol | Type | Represents |
|--------|------|-----------|
| Satellite (blue) | `satellite` | Space segment (spacecraft + payload) |
| Ground Station (green) | `groundStation` | Ground receiving station with antenna |
| Processing (cyan) | `processing` | Data processing, MCC, archive |
| User (amber) | `user` | End user / data consumer |
| Sensor (orange) | `sensor` | Ground sensor, IoT device, in-situ instrument |
| GNSS/External (purple) | `gnss` | External system (GNSS, relay sat, other constellation) |

**Exercise:** *In the ConOps tab, build your mission architecture diagram. Add all segments, label all connections with data type and frequency band.*

---

### 9. Mission Phases and Operational Modes (30 min)

#### 9.1 Operational Mission Phases

| Phase | Duration (typical CubeSat) | Activities | Key Risks |
|-------|--------------------------|------------|-----------|
| **LEOP** | 1--3 days | Deployment, antenna deploy, first contact, initial health check | Deployment failure, tumbling, no contact |
| **Commissioning** | 2--4 weeks | Subsystem checkout, calibration, first light, orbit determination | Anomalies, calibration issues |
| **Nominal Ops** | Months to years | Routine acquisition, downlink, orbit maintenance | Component degradation, anomalies |
| **Extended Ops** | Beyond design life | Continued operations with degraded performance | Solar array degradation, propellant depletion |
| **Disposal** | Days to months | Passivation, deorbit manoeuvre or natural decay | Failure of deorbit system |

#### 9.2 Operational Modes and Power Budgets

Each mode defines which subsystems are active, the pointing configuration, power demand, and data flow:

| Mode | Subsystems Active | Pointing | Power (3U typical) | Data Flow |
|------|-------------------|----------|-------------------|-----------|
| **Safe** | EPS, OBC, TTC (beacon), AOCS (coarse) | Sun-pointing | ~1--2 W | Beacon only |
| **Idle** | EPS, OBC, AOCS (standby), TTC (beacon) | Inertial hold | ~2 W | Health TM periodic |
| **Science/Imaging** | + Payload, AOCS (fine pointing) | Nadir or target | ~6 W | Instrument -> OBC storage |
| **Downlink** | + TTC (full TX power) | Ground station track | ~8 W | OBC -> TX -> GS |
| **Eclipse** | EPS (battery), OBC, TCS (heaters), AOCS | Inertial hold | ~3 W (battery) | None |
| **Orbit Maintenance** | + Propulsion | Thrust direction | ~7 W | Manoeuvre TM |

#### 9.3 Duty Cycling and Power Analysis

CubeSats have limited power generation (7--25 W for a 3U with deployable panels). Not all modes can run simultaneously. The orbit timeline determines what can happen when:

**Typical 95-minute orbit at 500 km SSO:**
- 60 min sunlight, 35 min eclipse
- ~10 min imaging per orbit (~10% duty cycle)
- ~8 min downlink per pass (1--2 passes/day over a single ground station)
- ~42 min idle
- 35 min eclipse (battery-powered)

> **Key Equations -- Power Budget:**
>
> Orbit-average power:
>
> $P_{avg} = \sum_{i} P_{mode,i} \times DC_i$
>
> Where $DC_i$ is the duty cycle (fraction of orbit) for each mode.
>
> Solar array sizing:
>
> $P_{SA} = P_{sunlight} + \frac{P_{eclipse} \times t_{eclipse}}{t_{sunlight} \times \eta_{charge}}$
>
> Where $\eta_{charge} \approx 0.9$ (battery charge efficiency).
>
> Battery sizing:
>
> $E_{battery} = \frac{P_{eclipse} \times t_{eclipse}}{DoD \times \eta_{discharge}}$
>
> Where $DoD$ is the maximum depth of discharge (typically 0.2--0.3 for long life, up to 0.5 for short missions) and $\eta_{discharge} \approx 0.95$.

[Source: Wertz et al., SMAD4, Chapter 11; ECSS-E-ST-20C power budget methodology]

---

### 10. Data Flow Pipeline (20 min)

#### 10.1 End-to-End Data Flow

```
Instrument -> Onboard Storage -> Downlink -> Ground Reception
  -> Processing (L0 -> L1 -> L2) -> Archive -> User Delivery
```

| Stage | Key Parameter | Sized By |
|-------|--------------|---------|
| Data generation | GB/day | Payload data rate $\times$ imaging duty cycle |
| Onboard storage | GB | Must hold $\geq 1$ day of data ($2\times$ for margin) |
| Downlink per pass | GB/pass | Link data rate $\times$ contact time per pass |
| Processing | hours | Algorithm complexity, compute infrastructure |
| User delivery | hours | Archive API, network bandwidth |

#### 10.2 Data Budget Balance

> **Key Equation:** For the system to be sustainable, daily downlink capacity must equal or exceed daily data generation:
>
> $C_{downlink} = R_{data} \times N_{passes} \times t_{contact} \times \eta_{protocol} \geq G_{daily}$
>
> Where:
> - $R_{data}$ = data link rate (Mbps)
> - $N_{passes}$ = number of ground station passes per day
> - $t_{contact}$ = average contact time per pass (seconds)
> - $\eta_{protocol}$ = protocol overhead factor (~0.8 for CCSDS framing)
> - $G_{daily}$ = daily data generation (Mb)
>
> If $C_{downlink} < G_{daily}$, data accumulates on board and storage eventually fills. Solutions:
> - Increase $R_{data}$ (higher TX power, higher frequency band, better antenna)
> - Increase $N_{passes}$ (more ground stations, polar ground station for SSO)
> - Increase $t_{contact}$ (higher altitude increases contact time but worsens resolution)
> - Decrease $G_{daily}$ (lower duty cycle, on-board compression, selective downlink)

**SpaceCDF exercise:** *Check the Data Budget on the Dashboard. Does your design balance? If not, which parameter would you change first?*

---

### 11. ConOps Tool Exercise (20 min)

1. Navigate to the **ConOps** tab in SpaceCDF
2. Review and edit the **mission architecture diagram** -- add all segments and connections
3. Edit the **mission phases**: adjust durations for your mission type
4. Review the **operational modes**: are the right modes defined? Adjust power values.
5. Check the **data flow pipeline**: does downlink capacity balance data generation?

**Complete Worksheet 1.4, Parts E and F:** Document your ConOps outline and calculate the orbit-average power budget.

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Problem statement | Defines WHAT is needed, not HOW to solve it; answers what, who, impact, constraints |
| Stakeholder analysis | Identify all parties with legitimate interest; capture needs, constraints, priority, influence |
| Objectives | Must be specific, measurable, and traceable to stakeholder needs via MoE/MoP/TPM chain |
| Trade study structure | 5 elements: decision, alternatives, criteria, weights, scores; must include sensitivity analysis |
| Space vs non-space | Existing services may already meet the need -- evaluate honestly before committing to build |
| Decision documentation | Every trade decision must have auditable rationale per Process 17 |
| ConOps | Three segments (space, ground, user); operational modes drive power budget via duty cycling |
| Data pipeline | Daily downlink capacity must equal or exceed daily data generation |

---

## References

1. [NASA, Systems Engineering Handbook (SP-2016-6105 Rev 2), 2016](https://www.nasa.gov/reference/systems-engineering-handbook/)
2. [NASA, NPR 7123.1D -- Systems Engineering Processes and Requirements, 2020](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
3. [ECSS, ECSS-E-ST-10C -- System Engineering General Requirements, 2009](https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/)
4. [Wertz, J.R. et al., Space Mission Engineering: The New SMAD (SMAD4), Microcosm Press, 2011](https://www.microcosminc.com/)
5. [NASA SEH Appendix C -- How to Write a Good Requirement](https://www.nasa.gov/reference/systems-engineering-handbook/)
6. [NASA SEH Appendix S -- ConOps Outline](https://www.nasa.gov/reference/systems-engineering-handbook/)
7. [Saaty, T.L., "The Analytic Hierarchy Process", McGraw-Hill, 1980](https://doi.org/10.1016/0377-2217(90)90057-I)

---

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

---

# Session 2.2: Functional Decomposition and Allocation

**Duration:** 2 hours
**Prerequisites:** Session 2.1 (requirements defined and validated)
**SpaceCDF Tab:** Functions

---

## References

- [NASA, *Systems Engineering Handbook* (NASA/SP-2016-6105 Rev 2), 2016, Sec. 4.3 (Process 3: Logical Decomposition)](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [ECSS, *ECSS-E-ST-10C Rev.1: System Engineering General Requirements*, 2017, Sec. 5.3](https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/)
- [INCOSE, *Systems Engineering Handbook*, 5th ed., 2023, Ch. 2.3.5.3](https://www.incose.org/products-and-publications/se-handbook)
- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 2](https://www.space.com/smad)
- [Blanchard & Fabrycky, *Systems Engineering and Analysis*, 5th ed., 2010, Ch. 3](https://www.pearson.com/en-us/subject-catalog/p/systems-engineering-and-analysis/P200000003502)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Explain the purpose of functional decomposition in bridging requirements to design
2. Decompose mission objectives into a hierarchical function tree (3+ levels)
3. Categorise functions by type (observe, communicate, navigate, point, power, protect, store, process, support)
4. Allocate functions to subsystem domains, including multi-allocation for shared responsibilities
5. Derive requirements from functional analysis
6. Identify and resolve coverage gaps (leaf functions without linked requirements)
7. Use SpaceCDF's function tree editor to build and validate a function architecture

---

## 1. What is Functional Decomposition? (20 min)

### Teaching Notes

*[Source: NASA SEH Sec. 4.3 -- Process 3: Logical Decomposition]*

Functional decomposition answers: **"What must the system DO to satisfy the requirements?"**

It creates a bridge between requirements (WHAT the system must achieve) and physical design (HOW it will be built). Functions describe *actions* the system must perform, without specifying the physical hardware or software that will perform them.

### The Decomposition Flow

<svg viewBox="0 0 800 360" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 12px;">
  <!-- Boxes -->
  <rect x="250" y="10" width="300" height="40" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="400" y="35" text-anchor="middle" fill="#1e40af" font-weight="bold">Objectives & Requirements</text>
  <!-- Arrow -->
  <line x1="400" y1="50" x2="400" y2="80" stroke="#64748b" stroke-width="2" marker-end="url(#arrowhead)"/>
  <rect x="250" y="80" width="300" height="40" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="400" y="105" text-anchor="middle" fill="#92400e" font-weight="bold">Functional Analysis (WHAT)</text>
  <line x1="400" y1="120" x2="400" y2="150" stroke="#64748b" stroke-width="2" marker-end="url(#arrowhead)"/>
  <rect x="250" y="150" width="300" height="40" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="400" y="175" text-anchor="middle" fill="#166534" font-weight="bold">Physical Architecture (HOW)</text>
  <!-- Side annotations -->
  <text x="570" y="70" fill="#64748b" font-size="11">Bridges the gap</text>
  <!-- Function tree below -->
  <rect x="100" y="230" width="180" height="30" rx="4" fill="#fef3c7" stroke="#d97706"/>
  <text x="190" y="250" text-anchor="middle" fill="#92400e" font-size="11">F-001: Acquire Imagery</text>
  <!-- Children -->
  <line x1="190" y1="260" x2="100" y2="290" stroke="#d97706"/>
  <line x1="190" y1="260" x2="280" y2="290" stroke="#d97706"/>
  <line x1="190" y1="260" x2="460" y2="290" stroke="#d97706"/>
  <rect x="20" y="290" width="160" height="26" rx="4" fill="#fff7ed" stroke="#d97706"/>
  <text x="100" y="308" text-anchor="middle" fill="#92400e" font-size="10">F-002: Point at target</text>
  <rect x="200" y="290" width="160" height="26" rx="4" fill="#fff7ed" stroke="#d97706"/>
  <text x="280" y="308" text-anchor="middle" fill="#92400e" font-size="10">F-003: Capture image data</text>
  <rect x="380" y="290" width="160" height="26" rx="4" fill="#fff7ed" stroke="#d97706"/>
  <text x="460" y="308" text-anchor="middle" fill="#92400e" font-size="10">F-004: Store data onboard</text>
  <!-- Universal functions -->
  <rect x="580" y="230" width="180" height="30" rx="4" fill="#e0e7ff" stroke="#4f46e5"/>
  <text x="670" y="250" text-anchor="middle" fill="#3730a3" font-size="11">Universal Functions</text>
  <text x="670" y="280" text-anchor="middle" fill="#3730a3" font-size="10">F-010: Generate power</text>
  <text x="670" y="296" text-anchor="middle" fill="#3730a3" font-size="10">F-011: Maintain thermal env</text>
  <text x="670" y="312" text-anchor="middle" fill="#3730a3" font-size="10">F-012: Survive launch</text>
  <text x="670" y="328" text-anchor="middle" fill="#3730a3" font-size="10">F-013: TTC with ground</text>
  <text x="670" y="344" text-anchor="middle" fill="#3730a3" font-size="10">F-014: Dispose at EOL</text>
  <defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/></marker></defs>
</svg>

### Function Types

Every spacecraft function falls into one of these categories:

| Type | Verb | Description | Example |
|------|------|-------------|---------|
| **Observe** | Sense/measure | Acquire data from the environment | Capture multispectral imagery, receive AIS signals |
| **Communicate** | Transfer | Move information between elements | Downlink science data, uplink telecommands |
| **Navigate** | Determine/control position | Know or change the orbit | Perform orbit maintenance manoeuvre |
| **Point** | Orient | Control spacecraft attitude | Nadir pointing during imaging, target tracking |
| **Power** | Generate/store/distribute | Provide electrical energy | Solar power generation, battery charge management |
| **Protect** | Maintain environment | Keep components within limits | Thermal control, radiation shielding |
| **Store** | Record | Buffer data for later use | Onboard solid-state data recording |
| **Process** | Transform | Convert data between forms | On-board image compression, L0 framing |
| **Support** | Provide structure | Mechanical integrity | Survive launch loads, deploy mechanisms |

### Universal Functions

Regardless of mission type, **every spacecraft** must perform these five functions:

1. **Generate electrical power** (solar, RTG, battery)
2. **Maintain thermal environment** (passive/active thermal control)
3. **Survive the launch environment** (structural loads, vibration, shock)
4. **Communicate with ground for TTC** (telemetry, tracking, command)
5. **Dispose of the spacecraft at end of life** (deorbit, graveyard, passivation)

SpaceCDF auto-generates these universal functions for every mission.

---

## 2. Mission-Type-Specific Function Trees (20 min)

### Teaching Notes

Different mission types produce fundamentally different primary function trees. The universal functions remain the same; it is the mission-specific branch that differentiates.

### Earth Observation (Optical/SAR)

```
F-001: Acquire imagery of target area
  +-- F-002: Point instrument at target
  +-- F-003: Capture image data (expose detector / SAR pulse)
  +-- F-004: Store acquired data onboard
  +-- F-005: Downlink data to ground station
```

**Real example -- Planet SuperDove:** F-001 decomposes into 8-band pushbroom acquisition, on-board radiometric correction, lossless compression, and X-band downlink. Each sub-function traces to specific SuperDove requirements (3.7 m GSD, 8 spectral bands, 200 Mbps downlink).

### Communications Relay (Store-and-Forward or Bent-Pipe)

```
F-001: Relay communications between users
  +-- F-002: Receive uplink signal from user terminal
  +-- F-003: Process and route data (store-and-forward or bent-pipe)
  +-- F-004: Transmit downlink signal to destination terminal or gateway
```

**Real example -- Astrocast (IoT):** F-001 decomposes into L-band receive (from IoT devices), on-board message deduplication and store-and-forward, and UHF/S-band downlink to gateway stations. Each message is <= 160 bytes.

*[Source: Astrocast, "Astrocast Network Overview," astrocast.com]*

### AIS/IoT Receiver (Passive)

```
F-001: Receive and process signals of interest
  +-- F-002: Receive AIS/IoT signals (passive -- no uplink transmission)
  +-- F-003: Decode and validate messages
  +-- F-004: Store processed data onboard
  +-- F-005: Downlink to ground for distribution
```

### Ground Segment Functions

Missions that include ground-side processing need ground-domain functions:

```
F-G01: Receive satellite data at ground station
F-G02: Process data pipeline (L0 -> L1 -> L2 products)
F-G03: Archive and distribute data products to users
F-G04: Operate mission control centre (planning, commanding, monitoring)
```

SpaceCDF supports allocation to ground domains: `ground_station`, `ground_processing`, `ground_sensor`.

---

## 3. Allocation to Subsystems (25 min)

### Teaching Notes

Each function must be **allocated** to one or more responsible subsystem domains. This allocation defines system boundaries and, critically, identifies **interfaces** wherever a function is shared.

### Allocation Rules

| Function | Typical Allocation | Multi-allocation? |
|----------|-------------------|-------------------|
| Acquire imagery | Payload | No (single owner) |
| Point at target | AOCS | No |
| Store data | OBC/Data Handling | No |
| Downlink data | Comms + AOCS | **Yes** -- comms for RF chain, AOCS for antenna pointing |
| Generate power | EPS | No |
| Maintain thermal | Thermal | No |
| Relay communications | Payload + Comms | **Yes** -- boundary depends on architecture |
| Survive launch | Structure | No |
| Dispose at EOL | Propulsion (or Ops) | No (or multi if drag-sail) |

### Multi-Allocation and Interface Identification

When a function is allocated to more than one subsystem, it creates an **interface** that must be explicitly managed.

**Example -- "Downlink data to ground station":**

| Responsible Subsystem | Contribution | Interface Created |
|-----------------------|-------------|-------------------|
| Comms (Link) | Transponder, antenna, modulation, RF chain | Comms <-> AOCS (antenna pointing) |
| AOCS | Antenna pointing towards ground station during pass | Comms <-> Data Handling (packet routing) |
| Data Handling | Data packaging, prioritisation, CCSDS framing | Data Handling <-> AOCS (pass scheduling) |

SpaceCDF supports multi-allocation by entering comma-separated domains.

**Discussion prompt:** *For each multi-allocated function in your design, where should the system boundary be drawn? Who "owns" the function, and who is a "contributor"?*

### Derived Requirements from Functions

Each allocated function generates **derived requirements** -- requirements not explicitly stated by stakeholders but necessary for the function to work:

| Function | Derived Requirement | Derivation Logic |
|----------|-------------------|------------------|
| "Point instrument at target" | "AOCS shall provide <= 0.1 deg pointing accuracy during imaging" | From GSD requirement + optical geometry |
| "Store data onboard" | "OBDH shall provide >= 32 GB solid-state storage" | From data rate x orbit period x missed-pass margin |
| "Downlink within daily contact window" | "TX shall provide >= 50 Mbps effective data rate" | From daily data volume / total contact time |
| "Generate power in all modes" | "SA shall produce >= 15 W EOL" | From worst-case sunlit power demand + recharge |

*[Source: NASA SEH Sec. 4.3.3 -- derived requirements from functional allocation]*

---

## 4. Performance Criteria and Coverage Analysis (15 min)

### Teaching Notes

Each leaf function (a function with no sub-functions) must have **performance criteria** -- quantitative thresholds that define "how well" the function must be performed:

| Function | Performance Criteria |
|----------|---------------------|
| Acquire imagery | GSD <= 10 m; SNR >= 100:1; >= 4 spectral bands |
| Point at target | Accuracy <= 0.1 deg; stability <= 0.01 deg/s; slew rate >= 1 deg/s |
| Downlink data | Link margin >= 3 dB; daily throughput >= 5 GB |
| Generate power | Positive margin in all modes; battery DOD <= 30% |
| Maintain thermal env | All components within operating range with >= 5 degC margin |

Performance criteria form the quantitative basis for subsystem-level requirements.

### Coverage Analysis

**Every leaf function** must trace to at least one requirement. If it does not, there is a **coverage gap** -- the function is defined but has no verification path.

SpaceCDF shows coverage status with badges:

- **Green badge:** Function has linked requirements (covered)
- **Amber badge:** "No requirements" -- coverage gap detected
- **Red badge:** Function conflicts with existing requirements

### Real Mission Example: CAPSTONE Coverage Gap

NASA's CAPSTONE mission (2022, Advanced Space) experienced a coverage gap during development: the "maintain attitude during trajectory correction manoeuvre" function initially had no formal pointing requirement during burns. This gap was identified during functional review and led to the derivation of SSR-AOCS-007: "The AOCS shall maintain pointing accuracy <= 2 deg during all propulsive manoeuvres."

*[Source: Advanced Space, "CAPSTONE Mission Overview," 2022]*

---

## 5. SpaceCDF Function Tree Exercise (40 min)

### Instructions

1. Navigate to the **Functions** tab in SpaceCDF
2. The tool auto-generates functions based on your selected mission type
3. **Review the generated tree:** Are the functions appropriate for YOUR mission?
   - For comms missions: should show relay/receive/transmit (not multispectral imagery)
   - For EO missions: should show acquire/point/store/downlink
   - For technology demos: should show demonstrate/characterise/report
4. **Edit functions:**
   - Click **edit** to change name, domain allocation, or performance criteria
   - Click **+sub** to add sub-functions (decompose further)
   - Click **x** to remove inappropriate functions
5. **Add ground segment functions** if your mission includes ground processing
6. **Check multi-allocation:** For any function allocated to multiple domains, verify the interface is captured
7. **Coverage check:** Are there any leaf functions (amber badge) without linked requirements? Derive requirements for them.

### Exercise Tasks

1. Build a function tree with at least 3 levels of decomposition
2. For each leaf function, write one derived requirement with a measurable threshold
3. Create a function-to-requirement traceability table (minimum 8 entries)
4. Identify at least one multi-allocated function and define the interface boundary
5. Complete Worksheet 2.2

---

## Worked Example: 3U EO CubeSat Function Tree

> **Function Tree for Agricultural Monitoring CubeSat**
>
> ```
> F-001: Acquire multispectral imagery
>   +-- F-002: Point telescope at target area (AOCS)
>   +-- F-003: Expose detector and capture image frames (Payload)
>   +-- F-004: Compress and store image data (OBC)
>   +-- F-005: Downlink stored data to ground station (Comms + AOCS)
>
> F-010: Generate electrical power (EPS)
>   +-- F-011: Convert solar energy to electrical (SA)
>   +-- F-012: Store energy for eclipse (Battery)
>   +-- F-013: Regulate and distribute power (EPS board)
>
> F-020: Maintain thermal environment (Thermal)
>   +-- F-021: Reject waste heat from electronics (Radiator)
>   +-- F-022: Maintain battery temperature during eclipse (Heater)
>
> F-030: Survive launch environment (Structure)
> F-040: Communicate with ground for TTC (Comms)
> F-050: Dispose at end of life (Propulsion/Ops)
> ```
>
> **Derived requirements from F-002 (Point telescope at target):**
> - SSR-AOCS-001: "The AOCS shall achieve <= 0.5 deg pointing accuracy during imaging mode"
> - SSR-AOCS-002: "The AOCS shall achieve pointing stability <= 0.01 deg/s during imaging"
>
> **Multi-allocation for F-005 (Downlink data):**
> - Comms subsystem: owns RF chain (transponder, antenna, modulation)
> - AOCS subsystem: provides antenna pointing towards ground station
> - Interface: AOCS must receive pass-schedule triggers from OBC to initiate slew to ground station pointing

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Functional decomposition | Bridges requirements (WHAT) to design (HOW) by identifying system actions |
| Function types | Observe, Communicate, Navigate, Point, Power, Protect, Store, Process, Support |
| Universal functions | Power, thermal, launch survival, TTC, disposal -- every spacecraft needs all five |
| Mission-specific trees | EO: acquire/point/store/downlink; Comms: receive/route/transmit; AIS: receive/decode/store |
| Allocation | Each function assigned to subsystem domain(s); multi-allocation creates interfaces |
| Derived requirements | Functions generate new requirements not stated by stakeholders |
| Coverage analysis | Every leaf function must trace to at least one requirement -- no gaps allowed |

---

# Session 2.3: Orbit Selection and Mission Architecture

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--2.2 (requirements and functions defined)
**SpaceCDF Tabs:** Mission Architecture, Orbit Trade Advisor

---

## References

- [Vallado, *Fundamentals of Astrodynamics and Applications*, 4th ed., 2013, Ch. 2--6](https://www.amazon.com/Fundamentals-Astrodynamics-Applications-Technology-Library/dp/1881883183)
- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 5--7](https://www.space.com/smad)
- [Curtis, *Orbital Mechanics for Engineering Students*, 4th ed., 2020, Ch. 2--4](https://www.elsevier.com/books/orbital-mechanics-for-engineering-students/curtis/978-0-08-102133-0)
- [NASA, *Systems Engineering Handbook*, 2016, Sec. 4.4 (Process 4: Design Solution Definition)](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [ECSS, *ECSS-U-AS-10C Rev.2: Space Debris Mitigation Requirements*, 2023](https://ecss.nl/standard/ecss-u-as-10c-rev-2-space-debris-mitigation-requirements/)
- [IADC, *Space Debris Mitigation Guidelines*, IADC-02-01 Rev 3, 2021](https://www.iadc-home.org/documents_public/)
- [FCC, *Report and Order FCC 22-74: Space Innovation*, 2022](https://www.fcc.gov/document/fcc-adopts-new-5-year-rule-deorbiting-satellites)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Define and compute the six Keplerian orbital elements
2. Calculate orbital period, velocity, and eclipse fraction for circular orbits
3. Compute the Sun-synchronous inclination using J2 precession
4. Evaluate orbit trade-offs across altitude, coverage, lifetime, radiation, and debris compliance
5. Apply the Hohmann transfer $\Delta V$ equations for orbit raising and deorbit
6. Use SpaceCDF's orbit trade advisor with mission-appropriate scoring weights

---

## 1. Keplerian Orbital Elements (25 min)

### Teaching Notes

Six parameters (the *classical orbital elements*) fully describe the size, shape, and orientation of an orbit, plus the satellite's position on it.

*[Source: Vallado, Ch. 2; Curtis, Ch. 2]*

| Element | Symbol | Physical Meaning | Typical Range |
|---------|--------|-----------------|---------------|
| Semi-major axis | $a$ | Size of the orbit | 6571--42164 km (LEO to GEO) |
| Eccentricity | $e$ | Shape (0 = circle, 0 < e < 1 = ellipse) | 0--0.001 for LEO circular |
| Inclination | $i$ | Tilt of orbit plane from equatorial plane | 0--180 deg |
| RAAN | $\Omega$ | Orientation of ascending node in equatorial plane | 0--360 deg |
| Argument of perigee | $\omega$ | Orientation of perigee within orbit plane | 0--360 deg |
| True anomaly | $\nu$ | Satellite position along the orbit | 0--360 deg |

For **circular LEO** missions (the most common CubeSat orbit type), the key design parameters reduce to three: **altitude** ($h$), **inclination** ($i$), and **LTAN** (local time of ascending node, for Sun-synchronous orbits).

<svg viewBox="0 0 500 400" xmlns="http://www.w3.org/2000/svg" style="max-width:450px; font-family: sans-serif; font-size: 11px;">
  <!-- Earth -->
  <circle cx="250" cy="200" r="80" fill="#bfdbfe" stroke="#2563eb" stroke-width="2"/>
  <text x="250" y="205" text-anchor="middle" fill="#1e3a5f" font-size="12">Earth</text>
  <!-- Equatorial plane -->
  <ellipse cx="250" cy="200" rx="160" ry="30" fill="none" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="420" y="195" fill="#94a3b8" font-size="10">Equatorial plane</text>
  <!-- Orbit ellipse (tilted) -->
  <ellipse cx="250" cy="185" rx="160" ry="120" fill="none" stroke="#dc2626" stroke-width="2" transform="rotate(-15, 250, 185)"/>
  <!-- Ascending node -->
  <circle cx="405" cy="195" r="5" fill="#dc2626"/>
  <text x="415" y="200" fill="#dc2626" font-weight="bold">AN</text>
  <!-- Labels -->
  <text x="250" y="50" text-anchor="middle" fill="#dc2626" font-weight="bold">Orbit plane (inclined)</text>
  <line x1="250" y1="200" x2="250" y2="100" stroke="#16a34a" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="260" y="145" fill="#16a34a" font-size="10">i (inclination)</text>
  <!-- RAAN arrow -->
  <path d="M 330 200 A 80 15 0 0 1 370 195" fill="none" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="345" y="220" fill="#7c3aed" font-size="10">$\Omega$ (RAAN)</text>
  <!-- Satellite -->
  <rect x="310" y="88" width="12" height="8" fill="#f59e0b" stroke="#92400e"/>
  <text x="330" y="95" fill="#92400e" font-size="10">Satellite</text>
</svg>

### Key Equations

> **Key Equations -- Orbital Mechanics Fundamentals**
>
> **Orbital period** (circular orbit):
> $$T = 2\pi \sqrt{\frac{a^3}{\mu}}$$
> where $a = R_E + h$ is the semi-major axis (m), $\mu = 3.986 \times 10^{14}$ m$^3$/s$^2$ is Earth's gravitational parameter, and $R_E = 6371$ km.
>
> **Orbital velocity** (circular):
> $$v = \sqrt{\frac{\mu}{a}}$$
>
> **Eclipse fraction** (maximum, circular orbit, cylindrical shadow):
> $$f_{\text{eclipse}} = \frac{1}{\pi} \arccos\left(\frac{\sqrt{a^2 - R_E^2}}{a}\right)$$
>
> **Sun-synchronous inclination** (J2-driven RAAN precession = 360 deg/year):
> $$\cos(i) = -\frac{2 \dot{\Omega}_{\text{req}} \, a^{7/2}}{3 R_E^2 \, J_2 \, \sqrt{\mu}}$$
> where $J_2 = 1.0826 \times 10^{-3}$, $\dot{\Omega}_{\text{req}} = \frac{2\pi}{365.25 \times 86400}$ rad/s.

---

## 2. Worked Examples: Orbital Computations (15 min)

> **Worked Example -- 500 km Circular LEO**
>
> **Given:** $h = 500$ km, circular orbit.
>
> **Step 1 -- Semi-major axis:**
> $a = 6371 + 500 = 6871$ km $= 6.871 \times 10^6$ m
>
> **Step 2 -- Orbital period:**
> $T = 2\pi \sqrt{\frac{(6.871 \times 10^6)^3}{3.986 \times 10^{14}}} = 2\pi \sqrt{8.137 \times 10^{5}} = 2\pi \times 5668 = 5669$ s $\approx$ **94.5 min**
>
> **Step 3 -- Orbital velocity:**
> $v = \sqrt{\frac{3.986 \times 10^{14}}{6.871 \times 10^6}} = \sqrt{5.802 \times 10^7} =$ **7617 m/s** $\approx$ 7.62 km/s
>
> **Step 4 -- Eclipse fraction (maximum):**
> $f = \frac{1}{\pi} \arccos\left(\frac{\sqrt{6871^2 - 6371^2}}{6871}\right) = \frac{1}{\pi} \arccos\left(\frac{2594}{6871}\right) = \frac{1}{\pi} \arccos(0.3774) = \frac{1}{\pi} \times 67.8\degree = $ **0.376** (37.6%)
>
> **Step 5 -- Eclipse and sunlight duration:**
> $t_{\text{eclipse}} = 94.5 \times 0.376 =$ **35.5 min**; $\quad t_{\text{sun}} = 94.5 - 35.5 =$ **59.0 min**
>
> **Step 6 -- Sun-synchronous inclination:**
> $\cos(i) = -\frac{2 \times 1.991 \times 10^{-7} \times (6.871 \times 10^6)^{3.5}}{3 \times (6.371 \times 10^6)^2 \times 1.0826 \times 10^{-3} \times \sqrt{3.986 \times 10^{14}}}$
>
> Numerator: $\approx -1.301 \times 10^{17}$; Denominator: $\approx 1.006 \times 10^{18}$
>
> $\cos(i) \approx -0.1293 \Rightarrow i \approx$ **97.4 deg**

---

## 3. Orbit Selection Trade-Offs (25 min)

### Teaching Notes

The orbit is the single most impactful early design decision. It cascades to every subsystem.

*[Source: SMAD, Ch. 7; Wertz et al., "Reducing Space Mission Cost," Ch. 3]*

| Parameter | Lower Altitude (300--400 km) | Higher Altitude (600--800 km) |
|-----------|------------------------------|-------------------------------|
| **GSD** | Better (shorter range to target) | Worse (longer range) |
| **Orbital lifetime** | Short (1--5 years, natural decay) | Long (25--100+ years) |
| **Debris compliance** | Easy (FCC 5-year rule met naturally) | May require active deorbit propulsion |
| **Radiation (TID)** | Lower (2--5 krad/yr) | Higher (10--20 krad/yr above 700 km) |
| **Launch cost** | Lower $\Delta V$ to orbit | Slightly higher |
| **Link budget** | Better (shorter slant range) | Worse (longer path loss) |
| **Coverage/swath** | Narrower per pass | Wider per pass |
| **Atmospheric drag** | Significant (limits lifetime) | Negligible above ~700 km |
| **Eclipse fraction** | ~35--38% | ~33--35% |

### Orbit Types and Applications

| Orbit | Altitude | Inclination | Best For | Real Example |
|-------|----------|-------------|----------|-------------|
| **LEO (non-SSO)** | 300--600 km | Any | Technology demos, ISS deployment | Many CubeSats |
| **SSO** | 400--800 km | 97--99 deg | EO (consistent solar illumination) | Planet SuperDove (475 km) |
| **ISS orbit** | ~410 km | 51.6 deg | ISS-deployed CubeSats | NanoRacks deployments |
| **MEO** | 2000--20200 km | Various | Navigation | GPS (20200 km) |
| **GEO** | 35786 km | 0 deg | Comms, weather | Anik F2 (Telesat) |
| **HEO (Molniya)** | 500--40000 km | 63.4 deg | High-latitude coverage | Meridian (Russia) |
| **Lunar NRHO** | 1500--70000 km | Lunar | Cislunar operations | CAPSTONE (NASA/Advanced Space) |

### Debris Compliance Rules

| Rule | Requirement | Applies To |
|------|------------|-----------|
| **IADC guideline** (2021) | Post-mission disposal within 25 years | International (voluntary but expected) |
| **FCC rule** (2024+) | Post-mission disposal within **5 years** | All FCC-licensed LEO satellites |
| **ECSS-U-AS-10C Rev.2** | Compliance with IADC + ESA Zero Debris Charter | ESA missions |
| **ISED (Canada)** | Currently 25-year rule; tightening under review | Canadian-licensed satellites |

**Critical altitude boundaries for FCC 5-year compliance:**

| Altitude | Natural Lifetime | FCC Compliant? | Action Needed |
|----------|-----------------|---------------|---------------|
| < 450 km | < 5 years | Yes | None (natural decay) |
| 450--550 km | 5--20 years | Marginal | Drag augmentation may suffice |
| 550--650 km | 20--50 years | **No** | Active deorbit (propulsion or drag sail) |
| > 700 km | > 100 years | **No** | Propulsion mandatory; ESA Zero Debris zone |

*[Source: IADC-02-01 Rev 3, Sec. 5.3.2; FCC 22-74; ECSS-U-AS-10C Rev.2]*

### Perturbation Effects

| Perturbation | Cause | Effect on Orbit | Design Impact |
|-------------|-------|----------------|---------------|
| **$J_2$ (Earth oblateness)** | Equatorial bulge | RAAN precession, argument of perigee drift | Enables Sun-synchronous; frozen orbits at $\omega = 90\degree$ |
| **Atmospheric drag** | Residual atmosphere | Semi-major axis decay, eventual re-entry | Limits lifetime below ~600 km; drives propulsion need |
| **Solar radiation pressure** | Photon momentum | Eccentricity oscillations, orbit perturbation | Significant for large A/m ratio (drag sails, large SA) |
| **Third-body (Moon/Sun)** | Gravitational pull | Long-period oscillations in $e$, $i$ | Significant for GEO and HEO; negligible for LEO |
| **Magnetic field** | Lorentz force on charged S/C | Very small drag-like effect | Negligible for most missions |

---

## 4. Ground Coverage and Revisit (15 min)

### Teaching Notes

> **Key Equations -- Ground Coverage**
>
> **Swath width** (nadir-pointing sensor with half-cone angle $\theta$):
> $$W_{\text{swath}} = 2h \tan(\theta)$$
>
> **Ground track spacing** (for a single satellite in LEO):
> The Earth rotates ~22.9 deg per orbit (for $T \approx 95$ min). At the equator, this corresponds to:
> $$\Delta_{\text{lon}} = \frac{360\degree}{T_{\text{sidereal}}} \times T_{\text{orbit}} \approx 22.9\degree \approx 2550 \text{ km (at equator)}$$
>
> **Revisit time** (approximate, single satellite):
> $$t_{\text{revisit}} \approx \frac{\Delta_{\text{lon}}}{W_{\text{swath}}} \times T_{\text{orbit}}$$
>
> **Constellation revisit** (N identical satellites in same plane):
> $$t_{\text{revisit,constellation}} \approx \frac{t_{\text{revisit,single}}}{N}$$

**Example -- SuperDove constellation:**
Planet operates ~200 SuperDove satellites. With a ~24 km swath at 475 km and multiple orbital planes, the constellation achieves daily global revisit -- a dramatic improvement over a single satellite's ~7-day revisit.

### Ground Station Contact Geometry

**Contact time per pass** depends on the minimum elevation angle $\epsilon_{\min}$ (typically 5--10 deg):

$$t_{\text{contact}} \approx \frac{T}{\pi} \arccos\left(\frac{\cos(\rho)}{\cos(\epsilon_{\min})}\right) - \text{geometric correction}$$

**Simplified rule of thumb** for LEO at 500 km, $\epsilon_{\min} = 10\degree$:
- Maximum pass duration: ~10 min (overhead pass)
- Average pass duration: ~6--7 min
- Passes per day (mid-latitude station): ~4--6

---

## 5. Hohmann Transfer and Deorbit (10 min)

### Teaching Notes

> **Key Equations -- Hohmann Transfer**
>
> The minimum-energy transfer between two circular orbits of radii $r_1$ and $r_2$:
>
> $$\Delta V_1 = \sqrt{\frac{\mu}{r_1}} \left(\sqrt{\frac{2r_2}{r_1 + r_2}} - 1\right)$$
>
> $$\Delta V_2 = \sqrt{\frac{\mu}{r_2}} \left(1 - \sqrt{\frac{2r_1}{r_1 + r_2}}\right)$$
>
> $$\Delta V_{\text{total}} = |\Delta V_1| + |\Delta V_2|$$

> **Worked Example -- Deorbit from 600 km to 200 km (re-entry perigee)**
>
> $r_1 = 6971$ km, $r_2 = 6571$ km
>
> $\Delta V_1 = \sqrt{\frac{3.986 \times 10^5}{6971}} \left(\sqrt{\frac{2 \times 6571}{6971 + 6571}} - 1\right)$
> $= 7.561 \times (\sqrt{0.9705} - 1) = 7.561 \times (-0.01498) = -0.1133$ km/s
>
> $\Delta V_{\text{total}} \approx$ **113 m/s** (only the first burn needed to lower perigee)

This deorbit $\Delta V$ is a critical input to the propulsion sizing in Session 3.4.

---

## 6. Radiation Environment (10 min)

### Teaching Notes

*[Source: ECSS-E-ST-10-04C Rev.1; SMAD, Ch. 8.1]*

### Total Ionising Dose (TID) by Orbit

| Orbit | TID (krad/year behind 2mm Al) | Electronics Class |
|-------|-------------------------------|-------------------|
| ISS (410 km, 51.6 deg) | 2--5 | Commercial COTS OK |
| SSO 500 km | 5--10 | Commercial / rad-tolerant |
| SSO 800 km | 10--20 | Rad-tolerant recommended |
| MEO 2000 km | 50--100 | Rad-hard required |
| GEO 35786 km | 10--20 | Rad-hard required |

**Rule of thumb:** Below 600 km in LEO, commercial COTS electronics can survive 3-year missions with modest shielding (2--3 mm Al equivalent). Above 600 km, radiation becomes a significant design driver and component cost escalates.

### South Atlantic Anomaly (SAA)

At 200--600 km altitude over South America, trapped protons from the inner Van Allen belt dip to lower altitudes. The SAA causes:
- Single-event upsets (SEU) in memory
- Single-event latch-ups (SEL) in CMOS
- Increased background noise in optical detectors

Mitigation: error-correcting memory (EDAC), watchdog timers, latch-up protection circuits.

---

## 7. SpaceCDF Orbit Trade Exercise (20 min)

### Instructions

1. Navigate to the **Mission Architecture** tab in SpaceCDF
2. Open the **Orbit Trade Advisor** panel
3. Enter your mission parameters:
   - GSD target (optical missions) or "N/A" for non-optical
   - Revisit target (days)
   - Mission lifetime (years)
   - Latitude band of interest
   - Cost ceiling (MEUR)
   - Aperture diameter (if known from optical sizing)
4. Click **"Compute Orbit Trade"**
5. Review the scored candidates:
   - Which orbit scores highest overall?
   - Is it debris-compliant (FCC 5-year rule)?
   - What is the natural orbital lifetime?
6. Click **"Use"** on your preferred orbit to populate the design parameters
7. Verify orbit fields updated in the dashboard (look for "Set from advisor" badge)

### Discussion Points

- Does the best-scoring orbit match your engineering intuition?
- What happens when you change scoring weights (prioritise GSD over cost, or vice versa)?
- For non-optical missions (comms, AIS), does the orbit scoring still make physical sense?
- If your selected orbit is above 600 km, what deorbit strategy will you use?
- Complete Worksheet 2.3

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Keplerian elements | Six parameters define the orbit; for LEO: altitude + inclination + LTAN |
| Key formulae | $T = 2\pi\sqrt{a^3/\mu}$; $v = \sqrt{\mu/a}$; eclipse fraction from geometry |
| Sun-synchronous | Requires specific inclination (~97 deg at 500 km) using $J_2$ precession |
| Perturbations | $J_2$ enables SSO; drag limits lifetime; SRP affects high-A/m satellites |
| Trade-offs | Lower altitude = better GSD and link but shorter lifetime and more drag |
| Debris rules | FCC 5-year, IADC 25-year; above ~550 km requires active deorbit |
| Hohmann transfer | $\Delta V_{\text{deorbit}} \approx 100$ m/s from 600 km; critical propulsion input |
| Radiation | Below 600 km: COTS OK; above: rad-tolerant/hard needed; SAA causes SEU |
| Cascade | Orbit choice affects every subsystem -- highest-leverage design decision |

---

# Session 2.4: Mission Architecture -- Segments, Interfaces, and Budgets

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--2.3 (requirements, functions, orbit selected)
**SpaceCDF Tabs:** Mission Architecture, System Architecture, Interfaces, Dashboard

---

## References

- [NASA, *Systems Engineering Handbook*, 2016, Sec. 4.4 (Process 4) & Sec. 6.3 (Process 12: Interface Management)](https://www.nasa.gov/reference/systems-engineering-handbook/)
- [ECSS, *ECSS-E-ST-10-24C: Interface Management*, 2015](https://ecss.nl/standard/ecss-e-st-10-24c-interface-management/)
- [ECSS, *ECSS-E-HB-10-02A: Verification Guidelines*, 2010, Sec. 5.2 (Mass Margins)](https://ecss.nl/hbstms/ecss-e-hb-10-02a-verification-guidelines/)
- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 10--11](https://www.space.com/smad)
- [ECSS, *ECSS-E-ST-20C: Electrical and Electronic*, 2021 (Power Budgets)](https://ecss.nl/standard/ecss-e-st-20c-electrical-and-electronic/)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Decompose a space mission into its constituent segments (space, ground, launch, user)
2. Construct a system architecture block diagram with subsystem boundaries
3. Identify and classify all subsystem-to-subsystem interfaces using an N-squared matrix
4. Write formal interface requirements for critical subsystem pairs
5. Construct a mass budget with ECSS margin policy and a mode-based power budget
6. Interpret SpaceCDF's dashboard KPIs and budget displays

---

## 1. Mission Segment Decomposition (15 min)

### Teaching Notes

*[Source: NASA SEH Sec. 4.4; ECSS-E-ST-10C Sec. 5.4; SMAD, Ch. 1]*

Every space mission decomposes into segments, each with distinct functions and interfaces:

<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 12px;">
  <!-- Space Segment -->
  <rect x="50" y="20" width="200" height="110" rx="8" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="150" y="45" text-anchor="middle" fill="#1e40af" font-weight="bold" font-size="14">Space Segment</text>
  <text x="150" y="65" text-anchor="middle" fill="#1e40af" font-size="10">Spacecraft bus</text>
  <text x="150" y="80" text-anchor="middle" fill="#1e40af" font-size="10">Payload instrument(s)</text>
  <text x="150" y="95" text-anchor="middle" fill="#1e40af" font-size="10">Subsystems (EPS, AOCS, TTC...)</text>
  <text x="150" y="110" text-anchor="middle" fill="#1e40af" font-size="10">Flight software</text>
  <!-- Ground Segment -->
  <rect x="300" y="170" width="200" height="110" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="400" y="195" text-anchor="middle" fill="#166534" font-weight="bold" font-size="14">Ground Segment</text>
  <text x="400" y="215" text-anchor="middle" fill="#166534" font-size="10">Ground station(s)</text>
  <text x="400" y="230" text-anchor="middle" fill="#166534" font-size="10">Mission control centre</text>
  <text x="400" y="245" text-anchor="middle" fill="#166534" font-size="10">Data processing pipeline</text>
  <text x="400" y="260" text-anchor="middle" fill="#166534" font-size="10">Operations team</text>
  <!-- Launch Segment -->
  <rect x="550" y="20" width="200" height="80" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="650" y="45" text-anchor="middle" fill="#92400e" font-weight="bold" font-size="14">Launch Segment</text>
  <text x="650" y="65" text-anchor="middle" fill="#92400e" font-size="10">Launch vehicle</text>
  <text x="650" y="80" text-anchor="middle" fill="#92400e" font-size="10">Deployer (e.g., ISIPOD)</text>
  <!-- User Segment -->
  <rect x="550" y="170" width="200" height="80" rx="8" fill="#fce7f3" stroke="#db2777" stroke-width="2"/>
  <text x="650" y="195" text-anchor="middle" fill="#9d174d" font-weight="bold" font-size="14">User Segment</text>
  <text x="650" y="215" text-anchor="middle" fill="#9d174d" font-size="10">End users</text>
  <text x="650" y="235" text-anchor="middle" fill="#9d174d" font-size="10">Data products / applications</text>
  <!-- RF link between space and ground -->
  <line x1="250" y1="100" x2="300" y2="200" stroke="#64748b" stroke-width="2" stroke-dasharray="6,3"/>
  <text x="260" y="155" fill="#64748b" font-size="10" transform="rotate(-35, 260, 155)">RF Link (TTC + Data)</text>
  <!-- Launch to space -->
  <line x1="550" y1="60" x2="250" y2="60" stroke="#d97706" stroke-width="2"/>
  <text x="400" y="52" text-anchor="middle" fill="#d97706" font-size="10">Deploy</text>
  <!-- Ground to user -->
  <line x1="500" y1="230" x2="550" y2="210" stroke="#64748b" stroke-width="1.5"/>
  <text x="530" y="215" fill="#64748b" font-size="10">Data</text>
</svg>

| Segment | Elements | Key Interfaces |
|---------|----------|---------------|
| **Space** | Spacecraft bus, payload, flight software | To ground (RF), to launch (mechanical/electrical) |
| **Ground** | Ground station, MCC, data processing | To space (RF), to user (network) |
| **Launch** | Launch vehicle, deployer, adapter | To space (mechanical, electrical inhibits) |
| **User** | End users, applications, data consumers | To ground (data products) |

---

## 2. System Architecture Block Diagram (20 min)

### Teaching Notes

The system block diagram shows the internal architecture of the space segment -- all subsystems and their data/power/mechanical connections.

<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" style="max-width:750px; font-family: sans-serif; font-size: 11px;">
  <!-- Central bus -->
  <rect x="300" y="200" width="200" height="60" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="400" y="225" text-anchor="middle" fill="#92400e" font-weight="bold">OBC / Data Handling</text>
  <text x="400" y="245" text-anchor="middle" fill="#92400e" font-size="10">I2C / SPI / CAN bus</text>
  <!-- EPS -->
  <rect x="50" y="30" width="160" height="55" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="130" y="52" text-anchor="middle" fill="#1e40af" font-weight="bold">EPS</text>
  <text x="130" y="70" text-anchor="middle" fill="#1e40af" font-size="10">SA + Battery + Regulator</text>
  <!-- Power bus lines -->
  <line x1="130" y1="85" x2="130" y2="160" stroke="#dc2626" stroke-width="2"/>
  <line x1="50" y1="160" x2="750" y2="160" stroke="#dc2626" stroke-width="2"/>
  <text x="400" y="153" text-anchor="middle" fill="#dc2626" font-size="10" font-weight="bold">Power Bus (3.3V / 5V / Battery)</text>
  <!-- AOCS -->
  <rect x="50" y="310" width="160" height="55" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="130" y="332" text-anchor="middle" fill="#166534" font-weight="bold">AOCS</text>
  <text x="130" y="350" text-anchor="middle" fill="#166534" font-size="10">RW + MTQ + ST + SS</text>
  <line x1="210" y1="335" x2="300" y2="230" stroke="#64748b" stroke-width="1.5"/>
  <!-- Comms -->
  <rect x="590" y="310" width="160" height="55" rx="6" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="670" y="332" text-anchor="middle" fill="#3730a3" font-weight="bold">Comms (TTC)</text>
  <text x="670" y="350" text-anchor="middle" fill="#3730a3" font-size="10">TX + RX + Antenna</text>
  <line x1="590" y1="335" x2="500" y2="230" stroke="#64748b" stroke-width="1.5"/>
  <!-- Payload -->
  <rect x="590" y="30" width="160" height="55" rx="6" fill="#fce7f3" stroke="#db2777" stroke-width="2"/>
  <text x="670" y="52" text-anchor="middle" fill="#9d174d" font-weight="bold">Payload</text>
  <text x="670" y="70" text-anchor="middle" fill="#9d174d" font-size="10">Telescope / Sensor</text>
  <line x1="590" y1="60" x2="500" y2="220" stroke="#64748b" stroke-width="1.5"/>
  <!-- Thermal -->
  <rect x="300" y="400" width="200" height="45" rx="6" fill="#fef9c3" stroke="#ca8a04" stroke-width="2"/>
  <text x="400" y="420" text-anchor="middle" fill="#854d0e" font-weight="bold">Thermal</text>
  <text x="400" y="437" text-anchor="middle" fill="#854d0e" font-size="10">Heaters + MLI + Radiators</text>
  <line x1="400" y1="400" x2="400" y2="260" stroke="#64748b" stroke-width="1" stroke-dasharray="4,3"/>
  <!-- Structure (background) -->
  <rect x="30" y="10" width="740" height="470" rx="10" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="8,4"/>
  <text x="400" y="490" text-anchor="middle" fill="#94a3b8" font-size="12">Structure (primary + secondary)</text>
  <!-- Power taps -->
  <line x1="130" y1="160" x2="130" y2="310" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="670" y1="160" x2="670" y2="310" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="670" y1="85" x2="670" y2="160" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="400" y1="160" x2="400" y2="200" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,2"/>
</svg>

### Subsystem Roles (CubeSat Reference)

| Subsystem | Abbreviation | Primary Function | Typical Mass Fraction |
|-----------|-------------|-----------------|----------------------|
| **Payload** | PL | Mission-specific sensing or communication | 25--40% |
| **Electrical Power System** | EPS | Generate, store, distribute electrical power | 15--25% |
| **Attitude & Orbit Control** | AOCS | Determine and control attitude; orbit knowledge | 8--15% |
| **Communications (TTC)** | LINK / TTC | Telemetry downlink, telecommand uplink, data downlink | 5--10% |
| **On-Board Computer** | OBC / C&DH | Command execution, data handling, flight software | 2--5% |
| **Thermal Control** | TCS | Maintain all components within temperature limits | 1--5% |
| **Structure** | STR | Mechanical support, launch load path, CDS compliance | 15--25% |
| **Propulsion** | PROP | Orbit manoeuvres, deorbit (if required) | 0--15% |
| **Harness** | HAR | Electrical interconnections | 3--7% |

---

## 3. The N-Squared Interface Matrix (25 min)

### Teaching Notes

*[Source: NASA SEH Sec. 6.3 -- Process 12: Interface Management; ECSS-E-ST-10-24C]*

Interface problems are the leading cause of integration failures. NASA SEH states: "Most system failures can be traced back to interface problems."

### N-Squared Matrix Structure

The N$^2$ matrix is a standard systems engineering tool for mapping all subsystem interactions:

- **Diagonal cells:** Subsystems (EPS, AOCS, Comms, Thermal, Structure, Propulsion, OBC, Payload)
- **Off-diagonal cells:** Interface between the row subsystem and the column subsystem
- **Upper triangle:** Outputs from row to column (data, power, commands)
- **Lower triangle:** Outputs from column to row

For 8 subsystems: $8 \times 7 / 2 = 28$ potential interface pairs. A typical CubeSat has 18--22 active interfaces.

### Interface Types

| Type | Symbol | Description | Example |
|------|--------|-------------|---------|
| **Mechanical** | M | Physical attachment, loads, alignment tolerances | Payload mounting to structure face |
| **Electrical** | E | Power connections, bus voltage, switched lines | EPS 5V bus to all subsystems |
| **Thermal** | T | Heat transfer paths, thermal coupling, conduction | Transponder waste heat to radiator panel |
| **Data** | D | Digital bus (I$^2$C, SPI, UART, CAN, RS-422) | OBC commands to AOCS controller |
| **RF** | R | Electromagnetic coupling or intentional RF paths | TX emissions coupling into payload receiver |
| **Optical** | O | Light paths, field-of-view clearance, stray light | Star tracker FOV clearance from solar array |

### Common CubeSat Interface Concerns

| Interface Pair | Types | Key Concern |
|----------------|-------|-------------|
| EPS <-> AOCS | E | Bus voltage compatibility; reaction wheel peak power draw |
| EPS <-> Comms | E | TX peak power demand (~6--10 W); switched line allocation |
| EPS <-> Thermal | E, T | SA thermal coupling; radiator vs SA area competition on external faces |
| EPS <-> Payload | E | Peak power switching; duty cycle coordination |
| Structure <-> AOCS | M | Reaction wheel and star tracker mounting alignment; vibration isolation |
| Structure <-> Payload | M, O | Payload alignment stability; optical FOV clearance |
| OBC <-> AOCS | D | Attitude data for payload pointing; mode transition commands |
| OBC <-> Comms | D | Telemetry packet routing; telecommand distribution |
| OBC <-> Payload | D | Science data acquisition trigger; instrument commanding |
| Comms <-> Payload | R | **EMC:** TX conducted/radiated emissions vs payload receiver sensitivity |
| Comms <-> AOCS | R, O | Antenna pattern vs star tracker FOV; antenna pointing coordination |
| Thermal <-> Payload | T | Detector cooling requirement; operating temperature limits |
| AOCS <-> Payload | M | Reaction wheel micro-vibration vs payload pointing stability (jitter) |

### Conflict Detection and Resolution

Interface conflicts arise when two subsystems have incompatible requirements at their shared boundary.

**Severity Classification:**

| Severity | Description | Example | Required Action |
|----------|-------------|---------|----------------|
| **Critical** | Design cannot close without resolution | EMC: TX radiation prevents payload operation | Must resolve before PDR |
| **Major** | Significant impact on design margin | Radiator area competes with SA area | Mitigation plan required by PDR |
| **Minor** | Manageable with minor adjustment | Star tracker FOV partially blocked by antenna stow | Accommodation analysis |

**Resolution Options:**

1. **Relocate:** Move a component to avoid the conflict (e.g., star tracker to different face)
2. **Shield/Isolate:** Add EMC shielding, vibration isolators, thermal insulation
3. **Time-Division:** Schedule conflicting activities to avoid simultaneity (e.g., no TX during imaging)
4. **Accept Risk:** Document residual risk and margin impact in the risk register

### Writing Interface Requirements

For each significant interface, write formal requirements:

**Example -- EPS <-> All Subsystems:**
```
IR-PWR-001: "The EPS shall provide regulated bus voltages of
             3.3 V +/- 0.1 V and 5.0 V +/- 0.25 V to all subsystems."
IR-PWR-002: "Each subsystem shall not exceed its allocated power
             draw without EPS coordination."
```

**Example -- Comms <-> Payload (EMC):**
```
IR-EMC-001: "TX conducted emissions shall be below -60 dBm in the
             payload receiver band (1.5-1.6 GHz) during imaging mode."
IR-EMC-002: "TX and payload acquisition shall not operate simultaneously
             unless IR-EMC-001 is verified by test."
```

---

## 4. Engineering Budgets: Mass and Power (30 min)

### Teaching Notes

*[Source: ECSS-E-HB-10-02A Sec. 5.2; SMAD, Ch. 10--11]*

Engineering budgets are the quantitative backbone of the design. They answer: **"Will this design close?"**

### Mass Budget

> **Key Equations -- Mass Budget**
>
> **Mass margin:**
> $$\text{Margin}_{\%} = \frac{M_{\text{allocation}} - M_{\text{MEV}}}{M_{\text{allocation}}} \times 100\%$$
>
> where MEV = Maximum Expected Value = CBE + maturity margins.
>
> **Status thresholds:** Green: > 20% | Amber: 10--20% | Red: < 10% | Exceeded: < 0%

| Term | Definition |
|------|-----------|
| **CBE** (Current Best Estimate) | Best estimate of actual mass based on current knowledge |
| **MEV** (Maximum Expected Value) | CBE + equipment maturity margin = worst-case expected mass |
| **Equipment maturity margin** | Applied per component based on design maturity (TRL) |
| **System margin** | Applied at system level as management reserve |

### ECSS Margin Policy by Phase

*[Source: ECSS-E-HB-10-02A Sec. 5.2]*

| Phase | Equipment Margin | System Margin | Compound |
|-------|-----------------|---------------|----------|
| **0/A** (concept) | 20% | 20% | ~44% |
| **B1** (preliminary) | 10% | 20% | ~32% |
| **B2** (detailed) | 5% | 15% | ~21% |
| **C/D** (build/test) | 3% | 10% | ~13% |
| **E** (as-built) | 0% | 5% | ~5% |

> **Worked Example -- 3U CubeSat Mass Budget (Phase A)**
>
> | Subsystem | CBE (kg) | Equip. Margin (20%) | MEV (kg) |
> |-----------|---------|---------------------|---------|
> | Payload | 1.50 | 0.30 | 1.80 |
> | EPS | 0.75 | 0.15 | 0.90 |
> | AOCS | 0.55 | 0.11 | 0.66 |
> | Comms (TTC) | 0.25 | 0.05 | 0.30 |
> | OBC | 0.08 | 0.02 | 0.10 |
> | Thermal | 0.05 | 0.01 | 0.06 |
> | Structure | 0.35 | 0.07 | 0.42 |
> | Harness | 0.15 | 0.03 | 0.18 |
> | **Dry Total** | **3.68** | | **4.42** |
> | System Margin (20%) | | | **0.88** |
> | **Dry MEV** | | | **5.30** |
> | Propellant | | | 0.00 |
> | **Wet Mass** | | | **5.30** |
> | **Launcher Allocation** | | | **6.00** (3U limit) |
> | **Mass Margin** | | | **0.70 kg (11.7%)** -- Amber |

### Mode-Based Power Budget

The power budget is computed **per operational mode** because not all subsystems draw power simultaneously:

| Subsystem | Safe (W) | Idle (W) | Imaging (W) | Downlink (W) | Eclipse (W) |
|-----------|---------|---------|-------------|-------------|-------------|
| OBC | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| AOCS | 0.5 | 1.0 | 3.0 | 2.0 | 0.5 |
| Payload | 0 | 0 | 5.0 | 0 | 0 |
| Comms (TX) | 0.5 | 0.5 | 0.5 | 6.0 | 0 |
| Thermal | 0.5 | 0.5 | 0.5 | 0.5 | 2.0 |
| **Total** | **2.5** | **3.0** | **10.0** | **9.5** | **3.5** |

### Orbit-Average Power

> **Key Equations -- Orbit-Average Power**
>
> $$P_{\text{avg}} = \sum_{\text{modes}} \left(P_{\text{mode}} \times \text{duty}_{\text{mode}}\right)$$
>
> **Example for 95-min orbit (60 min sunlight, 35 min eclipse):**
>
> | Mode | Power (W) | Duty (%) | Contribution (W) |
> |------|----------|----------|-------------------|
> | Idle | 3.0 | 45% | 1.35 |
> | Imaging | 10.0 | 10% | 1.00 |
> | Downlink | 9.5 | 8% | 0.76 |
> | Eclipse | 3.5 | 37% | 1.30 |
> | **Total** | | **100%** | **4.41 W** |

### Other Budget Types (Preview)

These budgets will be developed in detail during Week 2 Day 3--4 sessions:

| Budget | Key Equation | Session |
|--------|-------------|---------|
| **Link** | $\text{Margin} = \text{EIRP} - \text{FSPL} + G/T - k - 10\log_{10}(R_b) - E_b/N_0$ | 3.3 |
| **Pointing** | $\theta_{\text{total}} = \sqrt{\sum \theta_i^2}$ (RSS) | 3.2 |
| **$\Delta V$** | $\Delta V = I_{sp} \cdot g_0 \cdot \ln(m_0/m_f)$ (Tsiolkovsky) | 3.4 |
| **Data** | $\text{Daily Downlink} \geq \text{Daily Generation}$ | 3.3 |

---

## 5. SpaceCDF Exercise (30 min)

### Instructions

1. **System Architecture tab:** Review or edit the subsystem block diagram for your mission
2. **Interfaces tab:** Review the N$^2$ matrix
   - Click on 3 interface cells to examine types and concerns
   - For any red-bordered cell (conflict), use the "Resolve Conflict" workflow
   - Write interface requirements for your most critical pair
3. **Dashboard:** Examine all KPI cards:
   - Mass margin: green/amber/red?
   - Power margin per mode
   - Link margin (if computed)
   - Cost vs ceiling
4. **Budget Breakdown:** Open per-subsystem mass and power charts
5. Complete Worksheet 2.4

### Discussion Questions

- Which budget is tightest (closest to zero or negative margin)?
- What single design change would most improve the tightest budget?
- How does the ECSS margin policy affect your design freedom at Phase A vs Phase C?
- Which interface pair is most likely to cause integration problems?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Mission segments | Space, Ground, Launch, User -- each with defined interfaces |
| System architecture | Block diagram shows subsystems, data buses, power distribution |
| N$^2$ matrix | Maps all 28 potential interface pairs; 6 types (M, E, T, D, R, O) |
| Interface conflicts | Severity classification (critical/major/minor); 4 resolution options |
| Interface requirements | Formal boundary agreements; must be verifiable |
| Mass budget | CBE + equipment margin + system margin = MEV; compare to allocation |
| Power budget | Mode-based; duty cycling gives orbit-average; SA must cover peak + recharge |
| ECSS margins | Decrease with maturity: ~44% at Phase A to ~13% at Phase C/D |
| Budget closure | Negative margin = design does not close; reduce demand or increase allocation |

---

# Session 3.1: Power System and Thermal Control Design

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--2.4 (requirements, functions, orbit, architecture defined)
**SpaceCDF Tabs:** Dashboard (Power KPI), Engineering Budgets, Timing Budget, Parametric

---

## References

- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 11.4 (EPS), Ch. 11.5 (Thermal)](https://www.space.com/smad)
- [ECSS, *ECSS-E-ST-20C: Electrical and Electronic*, 2021](https://ecss.nl/standard/ecss-e-st-20c-electrical-and-electronic/)
- [ECSS, *ECSS-E-ST-31C: Thermal Control*, 2020](https://ecss.nl/standard/ecss-e-st-31c-thermal-control/)
- [Patel, *Spacecraft Power Systems*, 2005, Ch. 3--8](https://www.taylorfrancis.com/books/mono/10.1201/9781420038217/spacecraft-power-systems-mukund-patel)
- [Gilmore, *Spacecraft Thermal Control Handbook, Vol. 1*, 2002](https://arc.aiaa.org/doi/book/10.2514/4.104503)
- [GomSpace, *P31u EPS Datasheet*, 2023](https://www.gomspace.com)
- [MMA Design, *HaWK Solar Array Datasheet*, 2023](https://mmadesignllc.com)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Size a solar array from mission power demand, eclipse profile, and degradation
2. Size a battery from eclipse energy demand, depth-of-discharge, and cycle-life requirements
3. Compute orbit-average power using duty cycle analysis
4. Explain EPS architecture (DET vs PPT, MPPT, bus regulation)
5. Perform first-order thermal balance analysis (hot case and cold case)
6. Select thermal control methods and apply ECSS thermal margins
7. Verify power and thermal budgets in SpaceCDF

---

## 1. Electrical Power System Architecture (20 min)

### Teaching Notes

*[Source: SMAD, Ch. 11.4; ECSS-E-ST-20C; Patel, Ch. 3]*

The EPS is the "utility company" of the spacecraft. It must continuously supply regulated power to all subsystems through every operational mode, including eclipse.

### EPS Block Diagram

<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg" style="max-width:700px; font-family: sans-serif; font-size: 11px;">
  <!-- Solar Array -->
  <rect x="30" y="100" width="120" height="60" rx="4" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="90" y="125" text-anchor="middle" fill="#92400e" font-weight="bold">Solar Array</text>
  <text x="90" y="142" text-anchor="middle" fill="#92400e" font-size="10">GaAs 29.5%</text>
  <text x="90" y="155" text-anchor="middle" fill="#92400e" font-size="9">1361 W/m^2</text>
  <!-- MPPT -->
  <rect x="200" y="100" width="100" height="60" rx="4" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="250" y="125" text-anchor="middle" fill="#3730a3" font-weight="bold">MPPT</text>
  <text x="250" y="142" text-anchor="middle" fill="#3730a3" font-size="10">Regulator</text>
  <line x1="150" y1="130" x2="200" y2="130" stroke="#64748b" stroke-width="2" marker-end="url(#arr)"/>
  <!-- Bus -->
  <line x1="300" y1="130" x2="480" y2="130" stroke="#dc2626" stroke-width="3"/>
  <text x="390" y="120" text-anchor="middle" fill="#dc2626" font-weight="bold">Regulated Bus (3.3V / 5V / Batt)</text>
  <!-- Battery -->
  <rect x="330" y="200" width="120" height="55" rx="4" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="390" y="222" text-anchor="middle" fill="#166534" font-weight="bold">Battery</text>
  <text x="390" y="239" text-anchor="middle" fill="#166534" font-size="10">Li-ion, DOD 30%</text>
  <line x1="390" y1="200" x2="390" y2="133" stroke="#16a34a" stroke-width="2"/>
  <text x="408" y="175" fill="#16a34a" font-size="9">charge/discharge</text>
  <!-- Loads -->
  <rect x="520" y="40" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="62" text-anchor="middle" fill="#1e40af" font-size="10">Payload (SW)</text>
  <rect x="520" y="85" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="107" text-anchor="middle" fill="#1e40af" font-size="10">AOCS (SW)</text>
  <rect x="520" y="130" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="152" text-anchor="middle" fill="#1e40af" font-size="10">Comms TX (SW)</text>
  <rect x="520" y="175" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="197" text-anchor="middle" fill="#1e40af" font-size="10">OBC (always on)</text>
  <rect x="520" y="220" width="110" height="35" rx="4" fill="#dbeafe" stroke="#2563eb"/>
  <text x="575" y="242" text-anchor="middle" fill="#1e40af" font-size="10">Heaters (thermo)</text>
  <!-- Switch lines -->
  <line x1="480" y1="57" x2="520" y2="57" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="102" x2="520" y2="102" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="147" x2="520" y2="147" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="192" x2="520" y2="192" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="237" x2="520" y2="237" stroke="#64748b" stroke-width="1.5"/>
  <line x1="480" y1="57" x2="480" y2="237" stroke="#64748b" stroke-width="1.5"/>
  <text x="490" y="30" fill="#64748b" font-size="10">Switched lines</text>
  <text x="490" y="42" fill="#64748b" font-size="9">(SW = switchable)</text>
  <defs><marker id="arr" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/></marker></defs>
</svg>

### Architecture Types

| Architecture | Description | Efficiency | Complexity | Typical Use |
|-------------|-------------|-----------|-----------|------------|
| **DET** (Direct Energy Transfer) | SA connects directly to bus through shunt regulator | 80--85% | Low | Small satellites, CubeSats |
| **PPT** (Peak Power Tracking / MPPT) | DC-DC converter maximises SA power extraction | 90--95% | Medium | Most modern CubeSats |
| **Unregulated bus** | Battery voltage varies (3.0--4.2 V per cell) | Highest | Lowest | Very simple CubeSats |
| **Regulated bus** | Fixed voltage rails (3.3 V, 5 V, 12 V) | Good | Medium | Most CubeSat COTS EPS |

**CubeSat standard:** Most commercial EPS boards (GomSpace P31u, Endurosat, AAC Clyde) use MPPT + regulated bus with 3.3 V and 5 V rails.

---

## 2. Solar Array Sizing (25 min)

### Teaching Notes

> **Key Equations -- Solar Array Sizing**
>
> **Step 1: Orbit-average power demand:**
> $$P_{\text{avg}} = \sum_{\text{modes}} P_{\text{mode}} \times f_{\text{duty,mode}}$$
>
> **Step 2: SA end-of-life power requirement:**
> $$P_{\text{SA,EOL}} = P_{\text{peak,sunlight}} + \frac{P_{\text{eclipse}} \times t_{\text{eclipse}}}{t_{\text{sunlight}} \times \eta_{\text{charge}}}$$
> where $\eta_{\text{charge}} \approx 0.9$ (battery charge efficiency for Li-ion).
>
> **Step 3: Account for degradation:**
> $$P_{\text{SA,BOL}} = \frac{P_{\text{SA,EOL}}}{(1 - \delta)^n}$$
> where $\delta = 0.025$ (2.5% per year degradation for triple-junction GaAs in LEO), $n$ = mission lifetime in years.
>
> **Step 4: Compute SA area:**
> $$A_{\text{SA}} = \frac{P_{\text{SA,BOL}}}{\eta_{\text{cell}} \times S \times \cos(\theta) \times f_{\text{pack}}}$$
> where:
> - $\eta_{\text{cell}} = 0.295$ (triple-junction GaAs efficiency, AM0)
> - $S = 1361$ W/m$^2$ (solar constant at 1 AU)
> - $\theta$ = sun incidence angle (0 deg for ideal tracking)
> - $f_{\text{pack}} = 0.85$ (cell packing factor)
>
> **Step 5: SA mass:**
> $$m_{\text{SA}} = A_{\text{SA}} \times \sigma_{\text{SA}}$$
> where $\sigma_{\text{SA}}$ = 2.5 kg/m$^2$ (body-mounted) or 1.5 kg/m$^2$ (deployable).

> **Worked Example -- 3U EO CubeSat Solar Array**
>
> **Given:** $P_{\text{peak,sunlight}} = 10.0$ W (imaging mode), $P_{\text{eclipse}} = 3.5$ W, $t_{\text{eclipse}} = 35$ min, $t_{\text{sunlight}} = 60$ min, $\eta_{\text{charge}} = 0.9$, mission lifetime = 3 years.
>
> **Step 2:** Recharge power:
> $P_{\text{recharge}} = \frac{3.5 \times 35}{60 \times 0.9} = \frac{122.5}{54.0} = 2.27$ W
>
> $P_{\text{SA,EOL}} = 10.0 + 2.27 = 12.27$ W
>
> **Step 3:** BOL accounting for 3-year degradation:
> $P_{\text{SA,BOL}} = \frac{12.27}{(1 - 0.025)^3} = \frac{12.27}{0.9269} = 13.24$ W
>
> **Step 4:** SA area:
> $A_{\text{SA}} = \frac{13.24}{0.295 \times 1361 \times 1.0 \times 0.85} = \frac{13.24}{341.2} = 0.0388$ m$^2$
>
> This is approximately 20 cm x 20 cm -- achievable with a single deployable panel on a 3U CubeSat.
>
> **Step 5:** SA mass (deployable):
> $m_{\text{SA}} = 0.0388 \times 1.5 = 0.058$ kg (panel only; mechanism adds ~0.1--0.2 kg)

### CubeSat SA Power Reference

| Configuration | 1U | 3U | 6U |
|--------------|-----|-----|-----|
| Body-mounted only | ~2 W | ~7 W | ~12 W |
| Single deployable | ~4 W | ~15 W | ~30 W |
| Dual deployable | -- | ~25 W | ~48 W |

*[Source: GomSpace, ISIS, MMA Design vendor datasheets; ASTERIA 6U confirmed 48 W BOL]*

---

## 3. Battery Sizing (15 min)

### Teaching Notes

> **Key Equations -- Battery Sizing**
>
> **Required battery capacity:**
> $$C_{\text{bat}} = \frac{P_{\text{eclipse}} \times t_{\text{eclipse}}}{DOD \times \eta_{\text{discharge}}}$$
> where:
> - $DOD$ = maximum depth of discharge (0.30 for > 10,000 cycle life with Li-ion)
> - $\eta_{\text{discharge}} = 0.95$ (discharge efficiency)
> - $t_{\text{eclipse}}$ in hours
>
> **Battery mass:**
> $$m_{\text{bat}} = \frac{C_{\text{bat}}}{E_{\text{specific}}}$$
> where $E_{\text{specific}} = 150$--$200$ Wh/kg for Li-ion 18650 cells.
>
> **Cycle life relationship** (Li-ion 18650):
>
> | DOD | Typical Cycle Life | Suitable For |
> |-----|-------------------|-------------|
> | 80% | ~500 cycles | Short missions (< 1 month) |
> | 50% | ~2,000 cycles | Medium missions (< 6 months) |
> | 30% | ~10,000 cycles | Multi-year LEO missions |
> | 20% | ~30,000 cycles | Long-life LEO (> 5 years) |

> **Worked Example -- Battery for 3U EO CubeSat**
>
> **Given:** $P_{\text{eclipse}} = 3.5$ W, $t_{\text{eclipse}} = 35$ min $= 0.583$ h, $DOD = 0.30$, $\eta = 0.95$.
>
> $C_{\text{bat}} = \frac{3.5 \times 0.583}{0.30 \times 0.95} = \frac{2.04}{0.285} = 7.16$ Wh
>
> With 20% margin: $C_{\text{bat,spec}} \geq 8.6$ Wh. Specify **10 Wh** minimum.
>
> Battery mass: $m_{\text{bat}} = \frac{10}{150} = 0.067$ kg
>
> **Verification:** 3-year mission at 15 orbits/day = 16,425 eclipses. At 30% DOD, Li-ion 18650 cells provide > 10,000 cycles. **Marginal** -- consider 20% DOD for extra life margin ($C_{\text{bat}} = 10.7$ Wh, specify 13 Wh).

---

## 4. Thermal Control System (30 min)

### Teaching Notes

*[Source: ECSS-E-ST-31C; Gilmore, Ch. 1--4; SMAD, Ch. 11.5]*

### Thermal Environment in LEO

A spacecraft in LEO experiences four thermal inputs and one thermal sink:

| Source | Flux | Direction |
|--------|------|-----------|
| **Direct solar** | $S = 1361$ W/m$^2$ | Sun-facing surfaces only |
| **Earth albedo** | $\alpha_E \times S \approx 0.30 \times 1361 \approx 408$ W/m$^2$ | Earth-facing surfaces (nadir) |
| **Earth infrared** | $q_{\text{IR}} \approx 240$ W/m$^2$ | Earth-facing surfaces (nadir) |
| **Internal dissipation** | $Q_{\text{int}} = P_{\text{dissipated}}$ | From electronics waste heat |
| **Deep space** (sink) | $T_{\text{space}} \approx 3$ K | Zenith-facing radiator surfaces |

### Thermal Balance Equation

> **Key Equations -- Thermal Equilibrium**
>
> At steady state, the absorbed heat equals the radiated heat:
>
> $$Q_{\text{in}} = Q_{\text{out}}$$
>
> $$\alpha_s A_{\text{sun}} S + \alpha_s A_{\text{alb}} \alpha_E S + \varepsilon A_{\text{IR}} q_{\text{IR}} + Q_{\text{int}} = \varepsilon \sigma A_{\text{rad}} T^4$$
>
> where:
> - $\alpha_s$ = solar absorptance of surface coating
> - $\varepsilon$ = infrared emittance of surface coating
> - $\sigma = 5.67 \times 10^{-8}$ W/m$^2$/K$^4$ (Stefan-Boltzmann constant)
> - $A_{\text{sun}}$, $A_{\text{alb}}$, $A_{\text{IR}}$, $A_{\text{rad}}$ = projected areas for each flux
> - $T$ = equilibrium temperature (K)
>
> **Solving for equilibrium temperature:**
> $$T = \left(\frac{Q_{\text{absorbed}} + Q_{\text{internal}}}{\varepsilon \sigma A_{\text{rad}}}\right)^{1/4}$$

### Hot Case and Cold Case

| Case | Conditions | Design Concern |
|------|-----------|----------------|
| **Hot case** | Maximum solar exposure, all subsystems active, worst sun angle, BOL coatings | Components exceed maximum operating temperature |
| **Cold case** | Eclipse, minimum power dissipation, degraded coatings (EOL), deep space view | Components fall below minimum operating temperature |

### Surface Coatings

| Coating | $\alpha_s$ | $\varepsilon$ | $\alpha_s / \varepsilon$ | Use |
|---------|-----------|--------------|------------------------|-----|
| White paint (S13G) | 0.20 | 0.85 | 0.24 | Radiators (stay cool) |
| Black paint (Aeroglaze Z306) | 0.95 | 0.85 | 1.12 | Internal surfaces (maximize exchange) |
| Gold tape | 0.25 | 0.04 | 6.25 | MLI outer layer (minimize radiation) |
| Alodine (bare Al) | 0.38 | 0.15 | 2.53 | Moderate thermal control |
| MLI blanket (effective) | 0.05--0.15 | 0.02--0.05 | ~3 | Thermal isolation |
| Solar cells | 0.75--0.92 | 0.80--0.85 | ~1.0 | SA surfaces (high absorption) |

### Thermal Control Methods

| Method | Type | Mass Impact | Typical Use |
|--------|------|-------------|------------|
| **Surface coatings** | Passive | Negligible | Always -- select $\alpha_s/\varepsilon$ ratio per face |
| **MLI blankets** | Passive | 0.05--0.2 kg | Insulate sensitive components from environment |
| **Radiators** | Passive | Part of structure | Reject internal waste heat to deep space |
| **Heaters** | Active | 0.005--0.02 kg each | Maintain minimum temp during eclipse/safe mode |
| **Heat pipes** | Active/passive | 0.05--0.1 kg | Transport heat from source to radiator |
| **Louvers** | Active | 0.1--0.5 kg | Variable-conductance radiators (rare on CubeSats) |

### ECSS Thermal Margins

*[Source: ECSS-E-ST-31C, Table 5-1]*

| Test Level | Hot Margin | Cold Margin |
|-----------|-----------|-------------|
| **Qualification** | Predicted + 15 degC | Predicted - 15 degC |
| **Acceptance** | Predicted + 10 degC | Predicted - 10 degC |
| **Operating** | Predicted + 5 degC | Predicted - 5 degC |

> **Worked Example -- 3U CubeSat Thermal Check**
>
> **Hot case:** Predicted maximum temperature of payload CCD = 42 degC.
> - Operating limit = 50 degC. Margin = 50 - 42 = 8 degC > 5 degC. **Pass.**
> - Qualification test: must test at 42 + 15 = 57 degC. If qualification limit is 60 degC: **Pass.**
>
> **Cold case:** Predicted minimum temperature of battery = -8 degC during worst eclipse.
> - Operating limit = -10 degC. Margin = -8 - (-10) = 2 degC < 5 degC. **Fail.**
> - **Action:** Add heater (0.5 W survival heater with thermostat set to -5 degC).

---

## 5. Real Mission Examples (10 min)

### Planet SuperDove EPS

| Parameter | Value |
|-----------|-------|
| Form factor | 3U+, ~5 kg |
| SA configuration | Body-mounted + deployable wings |
| SA power (BOL) | ~25 W |
| Battery | Li-ion, ~20 Wh |
| Bus voltage | Unregulated 7.2--8.4 V (2S) |
| Peak demand | ~18 W (imaging mode) |
| Orbit | 475 km SSO, ~94 min period |
| Eclipse | ~35 min max, ~3 W demand |

*[Source: Planet Labs conference presentations; Salas et al., "SuperDove Constellation," SSC 2021]*

### CAPSTONE Thermal Design

NASA's CAPSTONE (12U, 25 kg) operates in a near-rectilinear halo orbit (NRHO) around the Moon with extreme thermal cycling:

- Perilune: strong Earth/Moon IR + solar
- Apolune: deep space cold, long shadow periods
- Thermal control: MLI wrapping, heaters on propulsion lines, passive radiator panels

*[Source: Advanced Space, "CAPSTONE Design Overview," SmallSat Conference 2022]*

---

## 6. SpaceCDF Exercise (30 min)

### Instructions

1. **Run the design** in SpaceCDF if not already converged
2. **Dashboard** -- review power KPIs:
   - Is power margin positive in **all** modes (sunlight, eclipse, safe)?
   - What is the orbit-average power demand?
   - What SA configuration was selected (body/deployable)?
3. **Timing Budget** card -- review mode durations:
   - Does the duty cycle match your ConOps modes?
   - Is eclipse time consistent with your orbit calculation from Session 2.3?
4. **Engineering Budgets** -- review the power waterfall:
   - Which subsystem is the largest power consumer in each mode?
   - Where could power be reduced if the budget is tight?
5. **Parametric** tab -- review thermal predictions:
   - Hot case temperature prediction
   - Cold case temperature prediction
   - Any exceedances?

### Worksheet 3.1 Tasks

1. Size the solar array for your mission (show all 5 calculation steps)
2. Size the battery (show calculation with DOD justification)
3. Compute orbit-average power using duty cycle table
4. Identify hot case and cold case conditions for your orbit
5. Check thermal margins against ECSS requirements

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| EPS architecture | MPPT + regulated bus is CubeSat standard; 3.3 V / 5 V / battery rails |
| SA sizing | $P_{\text{SA}} = P_{\text{peak}} + P_{\text{recharge}}$; account for degradation $(1-\delta)^n$ |
| SA area | $A = P_{\text{BOL}} / (\eta \cdot S \cdot \cos\theta \cdot f_{\text{pack}})$ |
| Battery | $C = P_{\text{ecl}} \cdot t_{\text{ecl}} / (DOD \cdot \eta)$; DOD 30% for multi-year LEO |
| SA power reference | Body-mounted: 2--12 W; single deploy: 4--30 W; dual deploy: 25--48 W |
| Thermal balance | $Q_{\text{in}} = Q_{\text{out}}$; solve for $T = (Q/\varepsilon\sigma A)^{1/4}$ |
| Hot/cold cases | Hot: max solar + all systems on; Cold: eclipse + min power |
| Thermal margins | ECSS: +/-5 degC operating, +/-10 degC acceptance, +/-15 degC qualification |
| Coatings | $\alpha_s/\varepsilon$ ratio controls equilibrium temperature; white paint for radiators |

---

# Session 3.2: Attitude and Orbit Control System (AOCS)

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--2.4 and 3.1 (requirements, orbit, power defined)
**SpaceCDF Tabs:** Dashboard (AOCS KPI), Pointing Budget, Architecture (AOCS)

---

## References

- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 11.1 (ADCS)](https://www.space.com/smad)
- [Sidi, *Spacecraft Dynamics and Control*, 1997, Ch. 4--9](https://www.cambridge.org/core/books/spacecraft-dynamics-and-control/82B47C7B6E2AA53BFAADAF26C2A79F14)
- [Markley & Crassidis, *Fundamentals of Spacecraft Attitude Determination and Control*, 2014](https://link.springer.com/book/10.1007/978-1-4939-0802-8)
- [ECSS, *ECSS-E-ST-60-10C: Control Performance*, 2008](https://ecss.nl/standard/ecss-e-st-60-10c-control-performance/)
- [ECSS, *ECSS-E-ST-60-20C: Star Tracker Performance Testing*, 2019](https://ecss.nl/standard/ecss-e-st-60-20c-star-tracker-performance-testing/)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Explain the distinction between attitude determination and attitude control
2. Select AOCS hardware architecture based on pointing requirements
3. Compute a pointing error budget using root-sum-square (RSS) combination
4. Calculate disturbance torques from gravity gradient, aerodynamic drag, solar radiation pressure, and residual magnetic dipole
5. Size actuators (reaction wheels, magnetorquers) for the computed disturbance environment
6. Verify AOCS design against requirements using SpaceCDF's pointing budget tool

---

## 1. AOCS Fundamentals (20 min)

### Teaching Notes

*[Source: SMAD, Ch. 11.1; Markley & Crassidis, Ch. 1--3]*

The AOCS performs two distinct functions:

| Function | Purpose | Hardware |
|----------|---------|---------|
| **Attitude Determination** (AD) | Know the spacecraft's orientation relative to a reference frame | Sensors: star tracker, sun sensors, magnetometer, gyroscope, Earth sensor |
| **Attitude Control** (AC) | Change or maintain the spacecraft's orientation | Actuators: reaction wheels, magnetorquers, thrusters, control moment gyros |

### AOCS Architecture Selection by Pointing Requirement

| Pointing Requirement | Architecture | Typical Hardware | Mass | Power | Cost |
|---------------------|-------------|-----------------|------|-------|------|
| > 5 deg | Passive magnetic | Permanent magnet + hysteresis rods | ~0.05 kg | 0 W | ~2 kEUR |
| 2--5 deg | Magnetorquers + sun sensors | 3-axis MTQ + coarse sun sensors | ~0.10 kg | 0.2 W | ~8 kEUR |
| 0.1--2 deg | Reaction wheels + MTQ | 3--4 RW + 3 MTQ + fine sun sensors | ~0.50 kg | 2--4 W | ~35 kEUR |
| < 0.1 deg | Fine pointing (RW + star tracker) | 4 RW + ST + 3 MTQ + sun sensors | ~0.80 kg | 3--5 W | ~55 kEUR |
| < 0.01 deg | Very fine pointing | 4 RW + ST + MEMS gyro + 3 MTQ | ~1.20 kg | 4--6 W | ~80 kEUR |

**Real mission examples:**

| Mission | Pointing Req | Architecture | Mass |
|---------|-------------|-------------|------|
| **Astrocast** (IoT) | ~5 deg | MTQ + sun sensors | 0.1 kg |
| **Planet SuperDove** (EO) | ~0.1 deg | 4 RW + ST + MTQ | 0.8 kg |
| **CAPSTONE** (cislunar) | ~0.05 deg | RW + ST + sun sensors | ~1.0 kg |

---

## 2. Disturbance Torques (25 min)

### Teaching Notes

In LEO, four external torques disturb the spacecraft attitude. The AOCS must counteract them continuously.

*[Source: SMAD, Ch. 11.1; Sidi, Ch. 5]*

> **Key Equations -- Disturbance Torques**
>
> **Gravity gradient torque** (worst case, 45 deg off nadir):
> $$T_{gg} = \frac{3\mu}{2a^3} |I_z - I_x| \sin(2\theta) \approx \frac{3\mu}{2a^3} |I_z - I_x|$$
> where $I_z$, $I_x$ are principal moments of inertia (kg m$^2$) and $\theta = 45\degree$ for worst case.
>
> **Aerodynamic torque:**
> $$T_{\text{aero}} = \frac{1}{2} \rho v^2 C_D A_{\text{ref}} \, d_{cp-cm}$$
> where $\rho$ = atmospheric density (kg/m$^3$), $v$ = orbital velocity (m/s), $C_D \approx 2.2$, $A_{\text{ref}}$ = cross-sectional area (m$^2$), $d_{cp-cm}$ = offset between centre of pressure and centre of mass (m).
>
> **Solar radiation pressure torque:**
> $$T_{\text{SRP}} = \frac{S}{c} A_s (1 + q) \, d_{sp-cm}$$
> where $S = 1361$ W/m$^2$, $c = 3 \times 10^8$ m/s, $A_s$ = illuminated area (m$^2$), $q$ = reflectance (0--1), $d_{sp-cm}$ = offset between solar pressure centre and centre of mass (m).
>
> **Residual magnetic dipole torque:**
> $$T_{\text{mag}} = M \times B$$
> where $M$ = spacecraft residual magnetic dipole moment (A m$^2$), $B$ = local geomagnetic field strength (T). For LEO: $B \approx 3 \times 10^{-5}$ T; typical CubeSat $M \approx 0.01$--$0.1$ A m$^2$.

> **Worked Example -- Disturbance Torques for a 3U CubeSat at 500 km**
>
> **Spacecraft properties:** 3U (100 x 100 x 340 mm), mass = 5 kg, $I_z = 0.035$ kg m$^2$, $I_x = 0.007$ kg m$^2$, $A_{\text{ref}} = 0.034$ m$^2$ (3U face), $d_{cp-cm} = 0.02$ m.
>
> **Gravity gradient:**
> $T_{gg} = \frac{3 \times 3.986 \times 10^{14}}{2 \times (6.871 \times 10^6)^3} \times |0.035 - 0.007|$
> $= \frac{1.196 \times 10^{15}}{6.494 \times 10^{20}} \times 0.028 = 1.84 \times 10^{-6} \times 0.028 = 5.2 \times 10^{-8}$ N m
>
> **Aerodynamic** (at 500 km, $\rho \approx 6 \times 10^{-13}$ kg/m$^3$):
> $T_{\text{aero}} = 0.5 \times 6 \times 10^{-13} \times 7617^2 \times 2.2 \times 0.034 \times 0.02$
> $= 0.5 \times 6 \times 10^{-13} \times 5.80 \times 10^7 \times 2.2 \times 0.034 \times 0.02 = 1.6 \times 10^{-8}$ N m
>
> **Solar radiation pressure:**
> $T_{\text{SRP}} = \frac{1361}{3 \times 10^8} \times 0.034 \times 1.5 \times 0.02 = 4.6 \times 10^{-9}$ N m
>
> **Magnetic** ($M = 0.05$ A m$^2$, $B = 3 \times 10^{-5}$ T):
> $T_{\text{mag}} = 0.05 \times 3 \times 10^{-5} = 1.5 \times 10^{-6}$ N m
>
> **Summary:**
>
> | Source | Torque (N m) | Dominant? |
> |--------|-------------|-----------|
> | Gravity gradient | $5.2 \times 10^{-8}$ | No |
> | Aerodynamic | $1.6 \times 10^{-8}$ | No |
> | Solar radiation pressure | $4.6 \times 10^{-9}$ | No |
> | Residual magnetic dipole | $1.5 \times 10^{-6}$ | **Yes** |
> | **Total (RSS)** | $\approx 1.5 \times 10^{-6}$ | |
>
> The residual magnetic dipole dominates for CubeSats due to COTS electronics and short wiring runs. This is a key finding -- magnetic cleanliness matters.

---

## 3. Actuator Sizing (20 min)

### Teaching Notes

### Reaction Wheel Sizing

> **Key Equations -- Reaction Wheel Sizing**
>
> **Torque requirement** (to counteract disturbances + provide control authority):
> $$T_{\text{RW}} \geq k \times T_{\text{disturbance,total}}$$
> where $k \geq 2$ is the control margin factor (typically 2--5).
>
> **Momentum storage requirement** (accumulation between desaturation cycles):
> $$H_{\text{required}} = T_{\text{disturbance}} \times \frac{t_{\text{desat}}}{2}$$
> where $t_{\text{desat}}$ is the time between magnetorquer desaturation events (typically one orbit).
>
> **Slew rate** (for agile missions):
> $$\dot{\theta}_{\text{max}} = \frac{H_{\text{RW,max}}}{I_{\text{axis}}}$$

> **Worked Example -- Reaction Wheel for 3U CubeSat**
>
> **Given:** $T_{\text{disturbance}} = 1.5 \times 10^{-6}$ N m, desaturation interval = 1 orbit (5670 s).
>
> **Momentum storage:**
> $H_{\text{required}} = 1.5 \times 10^{-6} \times \frac{5670}{2} = 4.25 \times 10^{-3}$ N m s $= 4.25$ mN m s
>
> **Typical CubeSat reaction wheels:**
>
> | Product | Torque (mN m) | Momentum (mN m s) | Mass (g) | Manufacturer |
> |---------|--------------|-------------------|----------|-------------|
> | RW-0.01 | 0.23 | 1.0 | 30 | Hyperion |
> | RW210 | 1.0 | 10 | 55 | Blue Canyon |
> | RW400 | 4.0 | 40 | 120 | Blue Canyon |
> | RW3-1.0 | 1.0 | 15 | 50 | CubeSpace |
>
> The RW210 (10 mN m s) exceeds the 4.25 mN m s requirement with 135% margin. **Selected.**

### Magnetorquer Sizing

Magnetorquers (MTQs) provide torque by interacting with Earth's magnetic field. They are essential for momentum dumping from reaction wheels.

> **Key Equations -- Magnetorquer Torque**
>
> $$T_{\text{MTQ}} = m_{\text{dipole}} \times B \times \sin(\alpha)$$
>
> where $m_{\text{dipole}}$ = magnetic dipole moment (A m$^2$), $B$ = local field (T), $\alpha$ = angle between dipole and field.
>
> **Desaturation time** (to dump one wheel from full momentum):
> $$t_{\text{dump}} = \frac{H_{\text{wheel}}}{T_{\text{MTQ,avg}}}$$

For a CubeSat MTQ with $m = 0.2$ A m$^2$ and $B = 3 \times 10^{-5}$ T:
$T_{\text{MTQ}} = 0.2 \times 3 \times 10^{-5} = 6 \times 10^{-6}$ N m

This is 4x the total disturbance torque -- sufficient for desaturation within a fraction of an orbit.

---

## 4. Pointing Error Budget (25 min)

### Teaching Notes

*[Source: ECSS-E-ST-60-10C; SMAD, Ch. 11.1]*

The pointing error budget combines all independent error sources using root-sum-square (RSS) to determine the total pointing uncertainty.

> **Key Equations -- Pointing Error Budget (RSS)**
>
> $$\theta_{\text{total}} = \sqrt{\theta_{\text{sensor}}^2 + \theta_{\text{actuator}}^2 + \theta_{\text{alignment}}^2 + \theta_{\text{thermal}}^2 + \theta_{\text{jitter}}^2 + \theta_{\text{orbit}}^2 + \theta_{\text{timing}}^2}$$
>
> The result must satisfy:
> $$\theta_{\text{total}} \leq \theta_{\text{requirement}}$$

### Error Source Definitions

| Source | Description | Typical Values (Star Tracker) | Typical Values (Sun Sensor) |
|--------|------------|------------------------------|----------------------------|
| **Sensor accuracy** | Intrinsic measurement noise of attitude sensor | 3--10 arcsec (0.001--0.003 deg) | 0.5--2 deg |
| **Actuator resolution** | Minimum controllable torque/step of actuators | 2--5 arcsec (0.001 deg) | N/A (MTQ: 1--5 deg) |
| **Alignment knowledge** | Misalignment between sensor boresight and payload boresight | 30--60 arcsec (0.01--0.02 deg) | 0.5 deg |
| **Thermal distortion** | Structural deformation with temperature | 10--30 arcsec (0.003--0.01 deg) | 0.1 deg |
| **Jitter** | High-frequency vibration from reaction wheels | 5--20 arcsec (0.001--0.006 deg) | N/A |
| **Orbit knowledge** | Uncertainty in satellite position (affects nadir pointing) | 1--5 arcsec (< 0.001 deg) | 0.05 deg |
| **Timing** | Time-stamping error between sensor read and actuator command | 1--3 arcsec (< 0.001 deg) | 0.01 deg |

> **Worked Example -- Pointing Budget for 3U EO CubeSat (Star Tracker + RW)**
>
> | Error Source | Value (deg) | Value$^2$ |
> |-------------|------------|-----------|
> | Star tracker accuracy | 0.003 | $9.0 \times 10^{-6}$ |
> | Reaction wheel resolution | 0.001 | $1.0 \times 10^{-6}$ |
> | Alignment knowledge | 0.020 | $4.0 \times 10^{-4}$ |
> | Thermal distortion | 0.010 | $1.0 \times 10^{-4}$ |
> | RW jitter | 0.005 | $2.5 \times 10^{-5}$ |
> | Orbit knowledge | 0.001 | $1.0 \times 10^{-6}$ |
> | Timing error | 0.001 | $1.0 \times 10^{-6}$ |
> | **RSS Total** | $\sqrt{5.37 \times 10^{-4}}$ = **0.023 deg** | |
>
> **Requirement:** 0.1 deg (3-sigma)
> **Margin:** 0.1 - 0.023 = 0.077 deg (77% margin) -- **comfortable**.
>
> **Key insight:** Alignment knowledge (0.020 deg) dominates the budget. Improving the star tracker accuracy from 0.003 to 0.001 deg would have negligible impact. **Budget-driven design** means investing effort in the dominant term.

---

## 5. Momentum Management and Desaturation (10 min)

### Teaching Notes

Disturbance torques cause angular momentum to accumulate in reaction wheels over time. Without management, wheels saturate and lose control authority.

**Desaturation cycle:**
1. Wheels accumulate momentum from disturbance torques (~$10^{-6}$ N m continuous)
2. At scheduled intervals (typically once per orbit), MTQs are activated
3. MTQs generate torque against Earth's magnetic field, slowing the wheels
4. Process takes 5--15 minutes per desaturation cycle

**Limitation:** MTQs can only generate torque **perpendicular** to the local magnetic field vector. They cannot dump momentum in all three axes simultaneously. This requires a multi-axis dumping strategy timed with the magnetic field rotation along the orbit.

### 3+1 Redundancy

The standard 4-wheel configuration provides full 3-axis control with one spare:
- **3 wheels** in the body X, Y, Z axes provide minimum control
- **4th wheel** on a skew axis provides redundancy and enhanced torque distribution
- If one wheel fails, the remaining three (including the skew wheel) maintain 3-axis control

---

## 6. SpaceCDF Exercise (30 min)

### Instructions

1. **Architecture tab (AOCS):** Select the AOCS architecture appropriate for your pointing requirement
   - Review the derived requirements that appear
   - Check that the selected hardware fits within your power and mass budgets
2. **Pointing Budget** card on the Dashboard:
   - Review the RSS error tree
   - Identify the largest contributor
   - Verify the total is within your pointing requirement
3. **Dashboard AOCS KPI:**
   - Pointing accuracy achieved
   - Margin to requirement
   - AOCS power demand by mode
4. **Equipment Browser (if time permits):**
   - Browse reaction wheels: compare mass, torque, momentum, cost
   - Browse star trackers: compare accuracy, mass, FOV

### Worksheet 3.2 Tasks

1. Select AOCS architecture and justify based on pointing requirement
2. Calculate at least 2 disturbance torques for your orbit and spacecraft
3. Size the reaction wheel (torque and momentum storage)
4. Complete the pointing error budget table (RSS)
5. Verify margin to pointing requirement

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| AD vs AC | Determination = know orientation (sensors); Control = change orientation (actuators) |
| Architecture selection | Driven by pointing requirement: MTQ for > 2 deg; RW+ST for < 0.1 deg |
| Disturbance torques | Gravity gradient, aero, SRP, magnetic dipole; magnetic dominates for CubeSats |
| RW sizing | Torque >= 2x disturbance; momentum storage >= half-orbit accumulation |
| MTQ sizing | Desaturation torque must exceed disturbance accumulation rate |
| Pointing budget | RSS of 5--7 independent sources; alignment knowledge typically dominates |
| Budget-driven design | Improve the dominant error source, not the smallest one |
| Redundancy | 4-wheel (3+1 skew) provides single-fault tolerance for 3-axis control |
| Momentum management | MTQs dump momentum against Earth's B-field; ~once per orbit |

---

# Session 3.3: Communications and Link Budget Design

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--3.2 (requirements, orbit, power, AOCS defined)
**SpaceCDF Tabs:** Link Budget, Spectrum Selector, Equipment Browser (Comms)

---

## References

- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 13 (Communications)](https://www.space.com/smad)
- [ECSS, *ECSS-E-ST-50-05C: Radio Frequency and Modulation*, 2011](https://ecss.nl/standard/ecss-e-st-50-05c-radio-frequency-and-modulation/)
- [CCSDS, *131.0-B-4: TM Synchronization and Channel Coding*, 2023](https://public.ccsds.org/Pubs/131x0b4.pdf)
- [ITU, *Radio Regulations*, 2020 (Articles 5 and 22)](https://www.itu.int/en/publications/ITU-R/pages/default.aspx)
- [Maral & Bousquet, *Satellite Communications Systems*, 6th ed., 2020, Ch. 5](https://www.wiley.com/en-us/Satellite+Communications+Systems)
- [Roddy, *Satellite Communications*, 4th ed., 2006, Ch. 4--6](https://www.mhprofessional.com)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Construct a complete link budget from first principles (in decibels)
2. Compute free space path loss for any frequency and slant range
3. Select an appropriate frequency band based on data rate, licensing, and equipment availability
4. Choose modulation and coding scheme based on required $E_b/N_0$
5. Size an antenna (gain, beamwidth, mass) for the selected frequency
6. Determine data throughput and verify the data budget closes
7. Use SpaceCDF's link budget tool and spectrum selector

---

## 1. The Link Budget Concept (15 min)

### Teaching Notes

*[Source: SMAD, Ch. 13; ECSS-E-ST-50-05C; Roddy, Ch. 4]*

The link budget is the accounting statement for the communication link. Every gain and every loss from transmitter to receiver is tallied in **decibels (dB)** to determine whether the link "closes" -- meaning the received signal is strong enough to decode with acceptable error rate.

### Link Budget Flow

<svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg" style="max-width:750px; font-family: sans-serif; font-size: 11px;">
  <!-- TX -->
  <rect x="20" y="60" width="100" height="80" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="70" y="85" text-anchor="middle" fill="#1e40af" font-weight="bold">Transmitter</text>
  <text x="70" y="100" text-anchor="middle" fill="#1e40af" font-size="9">P_TX (dBW)</text>
  <text x="70" y="115" text-anchor="middle" fill="#1e40af" font-size="9">G_TX (dBi)</text>
  <text x="70" y="130" text-anchor="middle" fill="#1e40af" font-size="9">L_TX (dB)</text>
  <!-- EIRP label -->
  <rect x="145" y="80" width="70" height="30" rx="4" fill="#fef3c7" stroke="#d97706"/>
  <text x="180" y="100" text-anchor="middle" fill="#92400e" font-weight="bold" font-size="10">EIRP</text>
  <line x1="120" y1="100" x2="145" y2="95" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Path -->
  <rect x="240" y="60" width="120" height="80" rx="6" fill="#fee2e2" stroke="#dc2626" stroke-width="2"/>
  <text x="300" y="85" text-anchor="middle" fill="#991b1b" font-weight="bold">Channel Losses</text>
  <text x="300" y="100" text-anchor="middle" fill="#991b1b" font-size="9">FSPL (dB)</text>
  <text x="300" y="115" text-anchor="middle" fill="#991b1b" font-size="9">Atmospheric (dB)</text>
  <text x="300" y="130" text-anchor="middle" fill="#991b1b" font-size="9">Pointing loss (dB)</text>
  <line x1="215" y1="100" x2="240" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- RX -->
  <rect x="390" y="60" width="110" height="80" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="445" y="85" text-anchor="middle" fill="#166534" font-weight="bold">Receiver</text>
  <text x="445" y="100" text-anchor="middle" fill="#166534" font-size="9">G_RX (dBi)</text>
  <text x="445" y="115" text-anchor="middle" fill="#166534" font-size="9">T_sys (K)</text>
  <text x="445" y="130" text-anchor="middle" fill="#166534" font-size="9">G/T (dB/K)</text>
  <line x1="360" y1="100" x2="390" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Result -->
  <rect x="530" y="60" width="120" height="80" rx="6" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
  <text x="590" y="85" text-anchor="middle" fill="#3730a3" font-weight="bold">Demodulator</text>
  <text x="590" y="100" text-anchor="middle" fill="#3730a3" font-size="9">Eb/N0 avail (dB)</text>
  <text x="590" y="115" text-anchor="middle" fill="#3730a3" font-size="9">Eb/N0 req (dB)</text>
  <text x="590" y="130" text-anchor="middle" fill="#3730a3" font-size="9">Impl. loss (dB)</text>
  <line x1="500" y1="100" x2="530" y2="100" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <!-- Margin -->
  <rect x="680" y="70" width="90" height="55" rx="6" fill="#d1fae5" stroke="#059669" stroke-width="3"/>
  <text x="725" y="93" text-anchor="middle" fill="#065f46" font-weight="bold" font-size="13">MARGIN</text>
  <text x="725" y="112" text-anchor="middle" fill="#065f46" font-size="11">>= 3 dB</text>
  <line x1="650" y1="100" x2="680" y2="97" stroke="#64748b" stroke-width="1.5" marker-end="url(#a3)"/>
  <defs><marker id="a3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#64748b"/></marker></defs>
</svg>

### Decibel Refresher

All link budget terms are in decibels to convert multiplication/division into addition/subtraction:

| Conversion | Formula |
|-----------|---------|
| Watts to dBW | $P_{\text{dBW}} = 10 \log_{10}(P_W)$ |
| dBW to Watts | $P_W = 10^{P_{\text{dBW}}/10}$ |
| Ratio to dB | $G_{\text{dB}} = 10 \log_{10}(G)$ |
| Common values | 2 W = +3.0 dBW; 1 W = 0 dBW; 0.5 W = -3.0 dBW |

---

## 2. Complete Link Budget Equation (30 min)

### Teaching Notes

> **Key Equations -- Link Budget (dB form)**
>
> **EIRP** (Effective Isotropic Radiated Power):
> $$\text{EIRP} = P_{TX} + G_{TX} - L_{TX} \quad \text{(dBW)}$$
>
> **Free Space Path Loss:**
> $$\text{FSPL} = 20\log_{10}\left(\frac{4\pi d}{\lambda}\right) = 20\log_{10}\left(\frac{4\pi d f}{c}\right) \quad \text{(dB)}$$
> where $d$ = slant range (m), $f$ = frequency (Hz), $c = 3 \times 10^8$ m/s.
>
> **Receiver figure of merit:**
> $$G/T = G_{RX} - 10\log_{10}(T_{sys}) \quad \text{(dB/K)}$$
>
> **Carrier-to-noise density ratio:**
> $$C/N_0 = \text{EIRP} - \text{FSPL} - L_{\text{atm}} - L_{\text{point}} - L_{\text{pol}} + G/T - k \quad \text{(dBHz)}$$
> where $k = -228.6$ dBW/K/Hz (Boltzmann constant).
>
> **Energy per bit to noise density:**
> $$E_b/N_0 = C/N_0 - 10\log_{10}(R_b) \quad \text{(dB)}$$
> where $R_b$ = data rate (bps).
>
> **Link margin:**
> $$\text{Margin} = E_b/N_{0,\text{available}} - E_b/N_{0,\text{required}} - L_{\text{implementation}} \quad \text{(dB)}$$
>
> **Requirement:** Margin $\geq$ 3 dB for Phase B+ (per ECSS-E-ST-50-05C).

### Complete Link Budget Table

| Line | Parameter | Formula / Typical Value | Unit |
|------|-----------|------------------------|------|
| 1 | TX Power | $P_{TX}$ (e.g., 2 W = +3.0) | dBW |
| 2 | TX Antenna Gain | $G_{TX}$ (e.g., +6.0 for patch) | dBi |
| 3 | TX Line Losses | $L_{TX}$ (cables, filters: -1.5) | dB |
| 4 | **EIRP** | $= P_{TX} + G_{TX} - L_{TX}$ | dBW |
| 5 | Free Space Path Loss | $\text{FSPL} = 20\log_{10}(4\pi d f/c)$ | dB |
| 6 | Atmospheric Loss | $L_{\text{atm}}$ (-0.5 typical for S-band) | dB |
| 7 | Pointing Loss | $L_{\text{point}}$ (-1.0 typical) | dB |
| 8 | Polarisation Loss | $L_{\text{pol}}$ (-0.3 typical for circular) | dB |
| 9 | RX Antenna Gain | $G_{RX}$ (e.g., +35 for 3 m dish) | dBi |
| 10 | System Noise Temp | $T_{sys}$ (e.g., 150 K = 21.8 dBK) | dBK |
| 11 | **G/T** | $= G_{RX} - 10\log_{10}(T_{sys})$ | dB/K |
| 12 | Boltzmann Constant | $k = -228.6$ | dBW/K/Hz |
| 13 | **C/N$_0$** | $= \text{EIRP} - \text{FSPL} + G/T - k - L_{\text{losses}}$ | dBHz |
| 14 | Data Rate | $10\log_{10}(R_b)$ | dBbps |
| 15 | **$E_b/N_0$ available** | $= C/N_0 - 10\log_{10}(R_b)$ | dB |
| 16 | $E_b/N_0$ required | From modulation/coding selection | dB |
| 17 | Implementation Loss | Typically 2.0 dB | dB |
| 18 | **LINK MARGIN** | $= E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}}$ | dB |

---

## 3. Free Space Path Loss by Band (10 min)

### Teaching Notes

FSPL increases with both frequency and distance. At a fixed slant range, higher-frequency bands lose more signal.

> **Key Equations -- FSPL (expanded form)**
>
> $$\text{FSPL (dB)} = 20\log_{10}(4\pi) + 20\log_{10}(d) + 20\log_{10}(f) - 20\log_{10}(c)$$
> $$= 21.98 + 20\log_{10}(d_m) + 20\log_{10}(f_{Hz}) - 169.54$$

| Band | Centre Frequency | FSPL at 500 km (nadir) | FSPL at 1300 km (10 deg elev) |
|------|-----------------|----------------------|-------------------------------|
| **UHF** | 437 MHz | 148.3 dB | 157.6 dB |
| **S-band** | 2250 MHz | 162.5 dB | 170.8 dB |
| **X-band** | 8200 MHz | 173.8 dB | 182.1 dB |
| **Ka-band** | 26 GHz | 183.8 dB | 192.1 dB |

**Note:** The 10 deg minimum elevation corresponds to a slant range of approximately 1300 km for a 500 km orbit. All link budgets should be computed at the worst-case (minimum elevation) geometry.

---

## 4. Modulation, Coding, and Eb/N0 (15 min)

### Teaching Notes

*[Source: CCSDS 131.0-B-4; DVB-S2 standard; Maral & Bousquet, Ch. 5]*

The choice of modulation scheme and forward error correction (FEC) code determines the required $E_b/N_0$ for a target bit error rate (BER).

| Modulation + Coding | $E_b/N_0$ Required (BER $10^{-6}$) | Spectral Efficiency | Typical Use |
|--------------------|------------------------------------|---------------------|------------|
| BPSK uncoded | 10.5 dB | 1.0 bps/Hz | Legacy telecommand |
| QPSK uncoded | 10.5 dB | 2.0 bps/Hz | Simple telemetry |
| QPSK + convolutional (r=1/2) | 5.0 dB | 1.0 bps/Hz | Standard CCSDS TM |
| QPSK + LDPC (r=1/2) | 2.0 dB | 1.0 bps/Hz | High-efficiency downlink |
| QPSK + LDPC (r=3/4) | 4.0 dB | 1.5 bps/Hz | Balanced performance |
| 8PSK + LDPC (r=3/4) | 6.5 dB | 2.25 bps/Hz | High-rate downlink |
| 16APSK + LDPC (r=3/4) | 8.5 dB | 3.0 bps/Hz | Maximum throughput |

**Design guidance:** For CubeSat missions, QPSK + LDPC (r=1/2 or r=3/4) is the most common choice, offering a good balance of coding gain and implementation simplicity.

---

## 5. Frequency Band Selection and Licensing (15 min)

### Teaching Notes

*[Source: ITU Radio Regulations, Articles 5 and 22; ISED RSS-SAT; FCC Part 25]*

Band selection is a **design constraint** that affects data rate, antenna size, atmospheric losses, equipment availability, licensing cost, and data policy.

| Band | Frequency | Max BW | Data Rate | Antenna Size | License | Equipment |
|------|-----------|--------|-----------|-------------|---------|-----------|
| **UHF (amateur)** | 435--438 MHz | 20 kHz | < 20 kbps | Dipole/monopole | IARU coord (free) | Many COTS |
| **S-band** | 2200--2290 MHz | 5 MHz | 0.1--10 Mbps | Patch antenna | ISED/FCC ($30--45K) | Many COTS |
| **X-band** | 8025--8400 MHz | 375 MHz | 10--400 Mbps | Horn/patch array | ISED/FCC + ITU | Growing COTS |
| **Ka-band** | 25.5--27.0 GHz | 1.5 GHz | 100--2000 Mbps | Small dish/array | Complex ITU | Emerging |

### Antenna Gain and Beamwidth

> **Key Equations -- Antenna**
>
> **Gain of a parabolic antenna:**
> $$G = \eta_a \left(\frac{\pi D}{\lambda}\right)^2$$
>
> In dBi: $G_{\text{dBi}} = 10\log_{10}\left[\eta_a \left(\frac{\pi D}{\lambda}\right)^2\right]$
>
> where $\eta_a \approx 0.55$--$0.65$ (aperture efficiency), $D$ = antenna diameter (m), $\lambda = c/f$.
>
> **Half-power beamwidth (HPBW):**
> $$\theta_{3\text{dB}} \approx \frac{70\lambda}{D} \quad \text{(degrees)}$$
>
> **Patch antenna gain** (single element): typically 5--8 dBi
> **Patch array gain** (N elements): $G_{\text{array}} = G_{\text{element}} + 10\log_{10}(N)$

### Band Selection Decision Tree

```
Required data rate?
  <= 20 kbps AND non-commercial data -> UHF amateur (IARU, free, 6 mo)
  <= 10 Mbps                         -> S-band commercial (ISED/FCC, $30-45K, 6-12 mo)
  <= 400 Mbps                        -> X-band (ISED/FCC + ITU, higher cost, 12+ mo)
  > 400 Mbps                         -> Ka-band (complex ITU, rain fade, emerging)
```

---

## 6. Worked Example: Complete Link Budget (15 min)

> **Worked Example -- S-band Downlink for 3U EO CubeSat**
>
> **Scenario:** 500 km SSO, S-band (2250 MHz), 1 Mbps downlink, 10 deg minimum elevation, 3 m ground station dish.
>
> | Line | Parameter | Value | Unit |
> |------|-----------|-------|------|
> | 1 | TX Power (2 W) | +3.0 | dBW |
> | 2 | TX Antenna Gain (patch) | +6.0 | dBi |
> | 3 | TX Line Losses | -1.5 | dB |
> | 4 | **EIRP** | **+7.5** | dBW |
> | 5 | FSPL (2250 MHz, 1300 km slant) | -170.8 | dB |
> | 6 | Atmospheric Loss | -0.5 | dB |
> | 7 | Pointing Loss | -1.0 | dB |
> | 8 | Polarisation Loss | -0.3 | dB |
> | 9 | RX Antenna Gain (3 m dish) | +35.0 | dBi |
> | 10 | System Noise Temp (150 K) | 21.8 | dBK |
> | 11 | **G/T** | **+13.2** | dB/K |
> | 12 | Boltzmann Constant | +228.6 | dBW/K/Hz |
> | 13 | **C/N$_0$** = 7.5 - 170.8 - 0.5 - 1.0 - 0.3 + 13.2 + 228.6 | **+76.7** | dBHz |
> | 14 | Data Rate (1 Mbps = $10\log_{10}(10^6)$) | 60.0 | dBbps |
> | 15 | **$E_b/N_0$ available** = 76.7 - 60.0 | **+16.7** | dB |
> | 16 | $E_b/N_0$ required (QPSK + LDPC r=3/4) | 4.0 | dB |
> | 17 | Implementation Loss | 2.0 | dB |
> | 18 | **LINK MARGIN** = 16.7 - 4.0 - 2.0 | **+10.7** | dB |
>
> **Result:** Link closes with 10.7 dB margin (requirement: >= 3 dB). **Pass.**
>
> **Design insight:** The generous 10.7 dB margin suggests the link is over-designed for 1 Mbps. The team could increase the data rate:
> $R_{b,\text{max}} = 10^{(16.7 - 4.0 - 2.0 - 3.0)/10} \times 10^6 = 10^{0.77} \times 10^6 \approx$ **5.9 Mbps** at minimum 3 dB margin.

---

## 7. Data Budget (10 min)

### Teaching Notes

> **Key Equations -- Data Budget**
>
> **Daily data generation:**
> $$V_{\text{gen}} = R_{\text{payload}} \times t_{\text{imaging}} \times N_{\text{orbits}} \times f_{\text{compression}}$$
>
> **Daily downlink capacity:**
> $$V_{\text{DL}} = R_{\text{downlink}} \times t_{\text{contact}} \times N_{\text{passes}} \times \eta_{\text{protocol}}$$
>
> **Data budget closure:**
> $$V_{\text{DL}} \geq V_{\text{gen}} \quad \text{(data budget closes)}$$

> **Worked Example -- Data Budget for 3U EO CubeSat**
>
> **Generation:** 240 Mbps raw x 5 min/orbit x 15 orbits/day x 0.25 (4:1 compression) = **4.5 GB/day**
>
> **Downlink:** 5 Mbps effective x 7 min/pass x 5 passes/day x 0.85 (protocol overhead) = **1.49 GB/day**
>
> **Result:** 1.49 GB/day < 4.5 GB/day. **Data budget does NOT close.**
>
> **Options:** (a) reduce imaging duty cycle, (b) increase data rate (X-band), (c) add ground stations, (d) increase compression ratio.

---

## 8. SpaceCDF Exercise (30 min)

### Instructions

1. **Spectrum Selector** (Dashboard): Select your license type and frequency band
2. **Link Budget** tab:
   - Enter TX power, antenna type, frequency, ground station parameters
   - Review the computed link margin
   - Verify it meets >= 3 dB requirement
3. **Compare** to your hand calculation from the worked example
4. **Equipment Browser:** Select a transponder and antenna that match your band choice
   - Note RF compatibility warnings
5. Complete Worksheet 3.3

### Discussion Questions

- What is the most impactful parameter in your link budget? (Usually FSPL or G/T)
- How does doubling the data rate affect link margin? (Reduces by 3 dB)
- Could you use a lower-power transmitter and still close the link?
- Does your data budget close? If not, what is the cheapest fix?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Link budget | $\text{Margin} = E_b/N_{0,\text{avail}} - E_b/N_{0,\text{req}} - L_{\text{impl}} \geq 3$ dB |
| EIRP | $\text{EIRP} = P_{TX} + G_{TX} - L_{TX}$ -- transmitter's effective power |
| FSPL | $20\log_{10}(4\pi df/c)$; increases 6 dB per doubling of frequency or distance |
| G/T | Receiver figure of merit: antenna gain minus noise temperature |
| Modulation | QPSK + LDPC (r=3/4): $E_b/N_0 = 4.0$ dB -- standard CubeSat choice |
| Band selection | UHF for < 20 kbps; S-band for < 10 Mbps; X-band for < 400 Mbps |
| Antenna gain | $G = \eta_a (\pi D/\lambda)^2$; patch ~6 dBi; 3 m dish ~35 dBi at S-band |
| Data budget | Daily downlink capacity must exceed daily data generation |
| Licensing | Amateur (free, IARU); Commercial (ISED/FCC, $30--45K, 6--12 months) |

---

# Session 3.4: Structure, Propulsion, and Equipment Selection

**Duration:** 2 hours
**Prerequisites:** Sessions 2.1--3.3 (all subsystem sizing complete)
**SpaceCDF Tabs:** Equipment Browser, Dashboard, Trade Studies, Budget Breakdown

---

## References

- [Cal Poly, *CubeSat Design Specification (CDS) Rev 14.1*, February 2022](https://www.cubesat.org/cubesatinfo)
- [Wertz, Everett & Puschell, *Space Mission Engineering: The New SMAD*, 2011, Ch. 11.3 (Structure), Ch. 17 (Propulsion)](https://www.space.com/smad)
- [ECSS, *ECSS-E-ST-32C Rev.1: Structural General Requirements*, 2008](https://ecss.nl/standard/ecss-e-st-32c-rev-1-structural-general-requirements/)
- [ECSS, *ECSS-E-ST-35C: Propulsion General Requirements*, 2008](https://ecss.nl/standard/ecss-e-st-35c-propulsion-general-requirements/)
- [Sarafin, *Spacecraft Structures and Mechanisms*, 1995](https://www.springer.com/gp/book/9780792334767)
- [Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed., 2017, Ch. 2--4](https://www.wiley.com/en-us/Rocket+Propulsion+Elements)
- [Enpulsion, *NANO R3 Thruster Datasheet*, 2023](https://www.enpulsion.com/nano)
- [VACCO, *MiPS Propulsion System Datasheet*, 2023](https://www.cubesat-propulsion.com)

---

## Learning Objectives

By the end of this session, participants will be able to:

1. Verify CubeSat Design Specification (CDS) compliance for 1U--12U form factors
2. Compute structural margin of safety for quasi-static launch loads
3. Estimate the fundamental frequency requirement and verify it against deployer specifications
4. Apply the Tsiolkovsky rocket equation to compute propellant mass for a given $\Delta V$
5. Select appropriate propulsion technology based on mission $\Delta V$, thrust level, and form factor
6. Size onboard data storage from the data budget
7. Select flight hardware using SpaceCDF's equipment browser with budget tracking

---

## 1. CubeSat Structure and CDS Compliance (25 min)

### Teaching Notes

*[Source: Cal Poly CDS Rev 14.1, February 2022]*

### CDS Dimensional Specifications

| Form Factor | Dimensions (mm) | Max Mass (kg) | Internal Volume (cm$^3$) |
|------------|-----------------|---------------|------------------------|
| 1U | 100 x 100 x 113.5 | 2.0 | ~1000 |
| 1.5U | 100 x 100 x 170.2 | 3.0 | ~1500 |
| 2U | 100 x 100 x 227.0 | 4.0 | ~2000 |
| 3U | 100 x 100 x 340.5 | 6.0 | ~3000 |
| 6U | 100 x 226.3 x 340.5 | 12.0 | ~6000 |
| 12U | 226.3 x 226.3 x 340.5 | 24.0 | ~12000 |

### Key CDS Requirements

| Requirement | Specification |
|------------|---------------|
| Rail material | Hard anodised aluminium (7075-T6 or 6061-T6) |
| Rail cross-section | 8.5 x 8.5 mm minimum contact area |
| Surface finish | All external surfaces anodised or non-outgassing coating |
| Deployment switches | Minimum 1 on each accessible rail face (+X, -X) |
| Remove Before Flight (RBF) pin | Required; physically disables all power systems |
| Protrusions | None beyond rail envelope in stowed configuration |
| Centre of gravity | Within 2 cm of geometric centre (per deployer ICD) |
| Fundamental frequency | > 40 Hz first mode (typical deployer requirement) |

### Launch Load Environment

| Load Type | Typical Level | Verification Method |
|-----------|--------------|---------------------|
| Quasi-static acceleration | 6--9 g axial, 2--4 g lateral | Analysis + sine vibration test |
| Random vibration | Per launch vehicle PUG (20--2000 Hz spectrum) | Random vibration test (3 axes) |
| Shock | 500--2000 g at separation (high frequency) | Shock response spectrum test |
| Acoustic | Per vehicle specification | Usually covered by random vibration for CubeSats |

### Structural Margin of Safety

> **Key Equations -- Structural Margin of Safety**
>
> $$\text{MoS} = \frac{\sigma_{\text{allowable}}}{\sigma_{\text{design}} \times \text{FoS}} - 1$$
>
> where:
> - $\sigma_{\text{allowable}}$ = material yield or ultimate strength (MPa)
> - $\sigma_{\text{design}}$ = computed stress under design loads (MPa)
> - FoS = factor of safety
>
> **Requirement:** MoS $\geq$ 0 for all load cases.
>
> **Factors of safety (ECSS-E-ST-32C):**
>
> | Material | Yield FoS | Ultimate FoS |
> |----------|----------|-------------|
> | Metallic (Al 7075-T6) | 1.25 | 1.5 |
> | Composite (CFRP) | 1.5 | 2.0 |
> | Bonded joints | 1.5 | 2.0 |

> **Worked Example -- Axial Load on 3U CubeSat Rail**
>
> **Given:** 3U CubeSat, mass = 5 kg, axial launch load = 9 g, 4 rails (load shared equally), rail cross-section = 8.5 x 8.5 mm, material = Al 7075-T6 ($\sigma_y = 503$ MPa, $\sigma_u = 572$ MPa).
>
> **Step 1 -- Design load per rail:**
> $F = \frac{m \times a}{4} = \frac{5 \times 9 \times 9.81}{4} = \frac{441.5}{4} = 110.4$ N
>
> **Step 2 -- Stress:**
> $\sigma = \frac{F}{A} = \frac{110.4}{8.5 \times 10^{-3} \times 8.5 \times 10^{-3}} = \frac{110.4}{7.225 \times 10^{-5}} = 1.53$ MPa
>
> **Step 3 -- Margin of safety (yield):**
> $\text{MoS}_y = \frac{503}{1.53 \times 1.25} - 1 = \frac{503}{1.91} - 1 = 262 \gg 0$ **Pass** (by a very large margin)
>
> **Key insight:** For CubeSats, quasi-static axial stress on the rails is never the critical load case. The critical structural design drivers are usually: **(a)** stiffness (fundamental frequency > 40 Hz), **(b)** random vibration fatigue on PCB solder joints, and **(c)** deployment mechanism reliability.

### Fundamental Frequency

> **Key Equations -- Fundamental Frequency (simplified beam model)**
>
> For a cantilevered beam (simplified CubeSat model):
> $$f_1 = \frac{1.875^2}{2\pi L^2} \sqrt{\frac{EI}{\rho A}}$$
>
> where $E$ = Young's modulus (Pa), $I$ = second moment of area (m$^4$), $\rho$ = density (kg/m$^3$), $A$ = cross-section area (m$^2$), $L$ = length (m).
>
> **Requirement:** $f_1 > 40$ Hz (from deployer ICD).
>
> In practice, CubeSat structures meet this easily with Al frames. The concern is PCB stack assemblies and deployable mechanisms, which may have lower-frequency modes if not properly constrained.

---

## 2. Propulsion System Design (30 min)

### Teaching Notes

*[Source: SMAD, Ch. 17; Sutton & Biblarz, Ch. 2--4]*

### When Propulsion is Required

| Need | Typical $\Delta V$ | Example Scenario |
|------|-------------------|------------------|
| **Orbit maintenance** (drag compensation) | 5--15 m/s per year | LEO below 400 km |
| **Deorbit** | 50--150 m/s | Active disposal from > 600 km |
| **Collision avoidance** | 1--5 m/s per event | Conjunction avoidance manoeuvre |
| **Constellation phasing** | 10--50 m/s | Spreading satellites into operational slots |
| **Orbit raising** | 50--200 m/s | Transfer from deployment orbit to operational orbit |

### When NO Propulsion is Needed

- Orbit < 500 km: natural atmospheric decay provides FCC 5-year deorbit compliance
- Low-cost technology demonstration: limited lifetime acceptable, no orbit maintenance needed
- Constellation using differential drag for phasing (e.g., Planet SuperDove)
- Budget-constrained missions where propulsion cost/risk exceeds benefit

### The Tsiolkovsky Rocket Equation

> **Key Equations -- Tsiolkovsky Rocket Equation**
>
> $$\Delta V = I_{sp} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)$$
>
> Rearranged for propellant mass:
> $$m_{\text{propellant}} = m_{\text{dry}} \times \left(e^{\Delta V / (I_{sp} \cdot g_0)} - 1\right)$$
>
> where:
> - $I_{sp}$ = specific impulse (s) -- thruster efficiency metric
> - $g_0 = 9.80665$ m/s$^2$ -- standard gravitational acceleration
> - $m_0$ = initial (wet) mass (kg)
> - $m_f$ = final (dry) mass (kg)
> - $m_{\text{propellant}} = m_0 - m_f$

### CubeSat Propulsion Options

| Type | $I_{sp}$ (s) | Thrust | Dry Mass | $\Delta V$ (5 kg S/C) | TRL | Example Product |
|------|-------------|--------|----------|----------------------|-----|----------------|
| **Cold gas** (N$_2$, R-236fa) | 40--80 | 10--100 mN | 0.3--1.0 kg | 10--30 m/s | 9 | VACCO MiPS |
| **Resistojet** | 80--150 | 10--50 mN | 0.3--0.8 kg | 20--50 m/s | 7--8 | Busek AMAC |
| **Electrospray** (FEEP) | 500--1500 | 0.01--1 mN | 0.5--1.5 kg | 50--200 m/s | 7--8 | Enpulsion NANO R3 |
| **Hall effect** | 800--1500 | 1--10 mN | 1.0--3.0 kg | 100--500 m/s | 6--8 | Exotrail ExoMG-nano |
| **Hydrazine mono** | 200--230 | 0.1--1 N | 1.0--4.0 kg | 50--200 m/s | 9 | Aerojet MPS-130 |
| **Green monopropellant** | 200--250 | 0.1--1 N | 1.0--3.0 kg | 50--200 m/s | 7--8 | Bradford HPGP |

> **Worked Example -- Propellant Mass for Deorbit**
>
> **Scenario:** 3U CubeSat, $m_{\text{dry}} = 5.0$ kg, deorbit from 600 km ($\Delta V = 113$ m/s), cold gas thruster ($I_{sp} = 60$ s).
>
> $m_{\text{prop}} = 5.0 \times \left(e^{113/(60 \times 9.81)} - 1\right) = 5.0 \times \left(e^{0.192} - 1\right) = 5.0 \times 0.212 = $ **1.06 kg**
>
> **Problem:** 1.06 kg of propellant is 21% of the 3U mass limit (6 kg). This is a significant fraction.
>
> **Alternative with electrospray** ($I_{sp} = 1200$ s):
> $m_{\text{prop}} = 5.0 \times \left(e^{113/(1200 \times 9.81)} - 1\right) = 5.0 \times \left(e^{0.00960} - 1\right) = 5.0 \times 0.00965 = $ **0.048 kg**
>
> But the Enpulsion NANO R3 dry mass is 0.9 kg and thrust is 0.35 mN -- deorbit burn takes months.
>
> **Trade-off:** High-$I_{sp}$ systems use far less propellant but are heavier, lower-thrust, and require longer burn times. Low-$I_{sp}$ systems are lighter and provide immediate thrust but consume much more propellant.

### Propulsion Trade Summary

| Parameter | Cold Gas | Electrospray | Hall Effect |
|-----------|---------|-------------|------------|
| Propellant for 100 m/s | 0.87 kg | 0.042 kg | 0.052 kg |
| System dry mass | 0.3 kg | 0.9 kg | 1.5 kg |
| **Total system mass** | **1.17 kg** | **0.94 kg** | **1.55 kg** |
| Burn time | Minutes | Months | Weeks |
| Complexity | Low | Medium | High |
| Cost | ~15 kEUR | ~50 kEUR | ~80 kEUR |

---

## 3. On-Board Data Handling (15 min)

### Teaching Notes

### OBC Architecture

CubeSat OBCs provide computing, data storage, and bus management:

| Component | Typical Specification |
|-----------|----------------------|
| Processor | ARM Cortex-M4/M7 or Cortex-A (Linux-capable) |
| RAM | 64 MB -- 1 GB |
| Flash storage | 4--128 GB (NOR for code, NAND for data) |
| Interfaces | I$^2$C, SPI, UART, CAN, RS-422, USB |
| Operating system | FreeRTOS (real-time) or Linux (data-intensive) |
| Power | 0.5--3 W depending on processor |

### Data Storage Sizing

> **Key Equations -- Data Storage**
>
> $$S_{\text{required}} = V_{\text{daily}} \times N_{\text{days}} \times f_{\text{safety}}$$
>
> where $V_{\text{daily}}$ = daily data generation, $N_{\text{days}}$ = days between full downlinks (typically 1--2 for LEO), $f_{\text{safety}} = 2$ (to handle missed passes).

> **Worked Example -- Storage for 3U EO CubeSat**
>
> **Given:** Daily generation = 4.5 GB (from Session 3.3 data budget), daily downlink = 1.5 GB, days to clear backlog = $4.5/1.5 = 3$ days.
>
> $S_{\text{required}} = 4.5 \times 3 \times 2 = 27$ GB
>
> **Specify:** >= 32 GB flash storage.

### PC/104 Bus Standard

Most CubeSat avionics use the PC/104 stack architecture:

- **Board size:** 96 x 90 mm
- **Connector:** 104-pin stack-through header (2 x 52 pins, 2.54 mm pitch)
- **Signals:** 3.3 V, 5 V, 12 V, GND + I$^2$C, SPI, UART, CAN, GPIO
- **Stack capacity:** 1U ~ 4 boards; 3U ~ 12 boards; 6U ~ 24 boards

### Flight Software Functions

| Function | Description |
|----------|------------|
| **Mode management** | Transition between Safe, Idle, Imaging, Downlink, Eclipse modes |
| **ADCS control loop** | Attitude determination + control (PD/PID controller, Kalman filter) |
| **TM/TC handling** | Generate telemetry packets, execute telecommands |
| **Data handling** | Payload data acquisition, compression, buffering, downlink queue |
| **FDIR** | Fault Detection, Isolation, and Recovery (watchdog, safe mode triggers) |
| **Housekeeping** | Monitor temperatures, voltages, currents, wheel speeds |
| **Scheduling** | Time-tagged command execution (autonomous imaging, pass prep) |

---

## 4. Equipment Selection Exercise (45 min)

### Instructions

This is the primary hands-on session for Day 4 of the design week. Teams select actual hardware components.

1. **Open the Equipment Browser** (button in header bar)
2. The sidebar shows categories **annotated by need**:
   - Blue dot = Required for your mission
   - Circle = Optional
   - Dimmed = Not applicable
3. **For each required category, select a component:**
   - Check the quantity needed (e.g., 4 reaction wheels, 3 magnetorquers)
   - Note any RF compatibility warnings (transponder band must match antenna band)
   - Watch the **live budget bar** showing running mass / power / cost totals
4. **For each selection, verify:**
   - Does it fit within the subsystem mass allocation?
   - Is power draw within the power budget for its operational mode?
   - Is the interface compatible (PC/104? I$^2$C? SPI? CAN?)
5. **Review the Budget Breakdown** on the Dashboard:
   - Has per-subsystem mass changed from the parametric estimate?
   - Is the overall mass margin still positive?
   - Is the power budget still positive in all modes?

### Component Trade Study

For at least one subsystem, select 2--3 candidate components and run a formal tabular trade:

1. Navigate to the **Trade Studies** tab
2. Load or create a "Component Selection Trade" study
3. Define criteria: mass, power, cost, TRL, heritage, performance
4. Score each candidate (1--5 scale)
5. Apply weights and compute weighted scores
6. Document the winner and rationale

### Real Mission Example: Iridium NEXT Equipment Selection

Iridium NEXT (Thales Alenia Space, 2017--2019) serves as a large-scale example of rigorous equipment selection. For the phased-array antenna:

| Criterion | Weight | Candidate A (Thales) | Candidate B (Raytheon) |
|-----------|--------|---------------------|----------------------|
| Performance | 0.30 | 4.5 | 4.0 |
| Mass | 0.20 | 3.5 | 4.0 |
| Cost | 0.20 | 3.0 | 4.5 |
| TRL | 0.15 | 5.0 | 4.0 |
| Schedule | 0.15 | 4.0 | 3.5 |
| **Weighted** | | **3.95** | **4.00** |

The selection was ultimately Candidate A (Thales) due to contractual considerations beyond the numerical trade -- illustrating that trade studies inform but do not dictate decisions.

---

## 5. SpaceCDF Budget Closure Check (15 min)

### Instructions

After equipment selection, perform a final budget health check:

1. **Dashboard KPIs:** Record all margins
   - Mass margin (%) -- green/amber/red?
   - Power margin per mode (W)
   - Link margin (dB)
   - Cost vs ceiling (MEUR)
   - Pointing accuracy vs requirement (deg)
2. **Budget Comparison:** Compare parametric estimates to equipment-based totals
3. **Identify any negative margins** -- these must be resolved before proceeding to integration (Week 3)

### If a Budget Does Not Close

| Budget | Common Fix | Impact |
|--------|-----------|--------|
| **Mass** (negative) | Remove propulsion; select lighter components; reduce redundancy | Risk / performance trade |
| **Power** (negative) | Add deployable SA; reduce payload duty cycle; select lower-power AOCS | Cost / schedule trade |
| **Link** (negative) | Increase TX power; use higher-gain antenna; reduce data rate; upgrade coding | Mass / power trade |
| **Cost** (over ceiling) | Use COTS instead of rad-hard; remove propulsion; reduce ground segment | Risk / capability trade |

---

## Worked Example: Complete 3U EO CubeSat Equipment List

> | Category | Component | Mass (kg) | Power (W) | Cost (kEUR) | Qty |
> |----------|-----------|----------|----------|-------------|-----|
> | EPS Board | GomSpace P31u | 0.10 | 0.5 | 8 | 1 |
> | Battery | GomSpace BP4 (20 Wh) | 0.20 | -- | 5 | 1 |
> | Solar Panels | MMA HaWK (deploy) | 0.45 | -- | 25 | 2 |
> | OBC | GomSpace A3200 | 0.08 | 1.0 | 12 | 1 |
> | Reaction Wheel | Blue Canyon RW210 | 0.055 | 0.6 | 8 | 4 |
> | Magnetorquer | CubeSpace CubeMAG | 0.03 | 0.1 | 3 | 3 |
> | Star Tracker | Blue Canyon NST | 0.35 | 1.5 | 35 | 1 |
> | Sun Sensor | NewSpace NFSS-411 | 0.005 | 0.01 | 1 | 6 |
> | Transponder | Endurosat S-band TX/RX | 0.10 | 6.0 (TX) | 15 | 1 |
> | Antenna | Endurosat S-band patch | 0.02 | -- | 3 | 1 |
> | Payload | Custom telescope | 1.50 | 5.0 | 150 | 1 |
> | Structure | ISIS 3U frame | 0.30 | -- | 8 | 1 |
> | Harness | Custom | 0.15 | -- | 5 | 1 |
> | **TOTAL** | | **3.57** | **~10 (imaging)** | **~290** | |
>
> **Parametric estimate from Session 2.4:** 3.68 kg CBE. **Equipment total:** 3.57 kg. Difference: -3% (within expected range).

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| CDS compliance | Standard dimensions, rail specs, deployment switches, RBF pin, CG limits |
| Launch loads | 6--9 g axial, random vibe 20--2000 Hz; MoS $\geq$ 0 with FoS 1.25 (yield) / 1.5 (ultimate) |
| Frequency req | First mode > 40 Hz; CubeSat structures easily meet this; PCBs and deployables are the risk |
| Tsiolkovsky | $m_{\text{prop}} = m_{\text{dry}} \times (e^{\Delta V/(I_{sp} g_0)} - 1)$ |
| Propulsion trades | High-$I_{sp}$: less propellant, more dry mass, long burns; Low-$I_{sp}$: more propellant, light system, fast burns |
| When to skip propulsion | Below 500 km (natural deorbit); tech demo; differential drag constellation |
| Data handling | Storage $\geq 2\times$ daily generation; PC/104 stack architecture; FreeRTOS or Linux |
| Equipment selection | Live budget tracking; RF compatibility check; trade study for contested selections |
| Budget closure | All margins must be positive before proceeding to integration week |

---

# Session 4.1: Equipment Selection & Bill of Materials

**Duration:** 2 hours
**Prerequisites:** Day 3 complete (subsystems sized, components identified via parametric agents)
**References:** ECSS-Q-ST-20C (Quality Assurance), ECSS-E-ST-10-24C (Interfaces), ITAR/EAR (22 CFR 120-130 / 15 CFR 730-774), CDS Rev 14.1, NASA SEH Rev 2 section 6.8

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Apply a structured make/buy/reuse decision framework to component selection
2. Evaluate COTS components against requirements using TRL and heritage criteria
3. Construct a Bill of Materials (BOM) with full traceability to requirements
4. Identify export control constraints (ITAR, EAR, Canadian Controlled Goods) for selected equipment
5. Verify interface compatibility (RF, electrical, mechanical) during component selection
6. Track cumulative mass, power, and cost budgets as selections are made

---

## 1. The Make/Buy/Reuse Decision (20 min)

### Teaching Notes

Before selecting any hardware, the team must decide the procurement strategy for each subsystem. This is a fundamental systems engineering decision that affects cost, schedule, risk, and performance.

*[Source: NASA SEH Rev 2 section 6.8 "Decision Analysis"; ECSS-M-ST-10C Rev.1 section 5.4]*

### Decision Framework

```
For each subsystem or component:
  1. Does a COTS product exist that meets requirements?
     -> Yes: BUY (lowest risk, fastest schedule)
     -> No: Continue
  2. Does flight-proven hardware from a previous mission exist?
     -> Yes: REUSE (low risk, may need delta-qualification)
     -> No: Continue
  3. Can the requirement be met by modifying existing hardware?
     -> Yes: MODIFY (moderate risk, moderate schedule)
     -> No: MAKE (highest risk, longest schedule, most expensive)
```

### Make/Buy/Reuse Trade Matrix

| Factor | Buy (COTS) | Reuse (Heritage) | Modify | Make (Custom) |
|--------|-----------|-------------------|--------|---------------|
| **Cost (NRE)** | None | None-Low | Moderate | High |
| **Cost (Recurring)** | Vendor price | Reproduction cost | Vendor + delta | Full development |
| **Schedule** | 4-16 weeks lead | 8-24 weeks | 12-36 weeks | 12-48 months |
| **Risk** | Low (if TRL >= 7) | Low (flight-proven) | Medium | High |
| **Performance** | Fixed by vendor | Fixed by heritage | Tuneable | Fully customisable |
| **IP ownership** | Vendor retains | May be shared | Negotiated | Full ownership |
| **Qualification** | Vendor-provided data | Delta-qual only | Partial re-qual | Full qualification |

### Key Equations

> **Non-Recurring Engineering (NRE) Cost Estimate:**
>
> NRE = Labour_hours x Hourly_rate + Material_cost + Facility_cost + Testing_cost
>
> For COTS: NRE is near zero (vendor absorbs development cost).
> For custom: NRE can be 3-10x the unit recurring cost.

### Worked Example

*Problem:* A 6U CubeSat mission needs a fine sun sensor with 0.1 degree accuracy. Three options:

| Option | Type | Accuracy | Mass | Cost | TRL | Lead Time |
|--------|------|----------|------|------|-----|-----------|
| Bradford SSOC-D60 | COTS | 0.1 deg | 35 g | EUR 15K | 9 | 8 weeks |
| In-house photodiode array | Custom | 0.05 deg | 20 g | EUR 8K + 400 hr NRE | 4 | 12 months |
| Modified heritage sensor | Reuse | 0.08 deg | 40 g | EUR 6K + 80 hr delta-qual | 7 | 16 weeks |

*Decision:* The COTS option (Bradford SSOC-D60) meets the requirement, has TRL 9, lowest schedule risk, and total cost of EUR 15K vs EUR 8K + ~EUR 40K NRE for custom. **Buy.**

---

## 2. Technology Readiness Level (TRL) Assessment (20 min)

### Teaching Notes

TRL is the standard metric for technology maturity. It was developed by NASA in the 1970s and is now used universally in space programmes.

*[Source: NASA NPR 7123.1D Appendix E; ECSS-E-HB-11A "Technology Readiness Level (TRL) Guidelines"]*
*[URL: https://www.nasa.gov/directorates/somd/space-communications-navigation-program/technology-readiness-levels/]*

### TRL Scale with Decision Criteria

| TRL | Definition | Evidence Required | CubeSat Decision |
|-----|-----------|-------------------|-----------------|
| 1 | Basic principles observed | Published research | Do not select |
| 2 | Technology concept formulated | Analytical studies | Do not select |
| 3 | Experimental proof of concept | Lab measurements | Do not select |
| 4 | Component validated in lab | Breadboard tested | High risk -- avoid unless no alternative |
| 5 | Component validated in relevant environment | Engineering model tested | Acceptable for technology demonstrator missions |
| 6 | System/subsystem model demonstrated in relevant environment | Prototype in relevant environment | Acceptable with risk mitigation |
| 7 | System prototype demonstrated in operational environment | Prototype tested in space | Preferred minimum for CubeSats |
| 8 | Actual system completed and qualified | Flight-qualified hardware | Strong preference |
| 9 | Actual system flight-proven | Successful on-orbit operation | Lowest risk |

### TRL and Risk Relationship

> **Risk Reduction Factor (empirical):**
>
> Risk_factor = 10^(-(TRL - 1) / 3)
>
> | TRL | Risk Factor | Interpretation |
> |-----|------------|----------------|
> | 3 | 0.22 | High probability of failure/redesign |
> | 5 | 0.046 | Moderate risk |
> | 7 | 0.010 | Low risk |
> | 9 | 0.002 | Very low risk |
>
> *This empirical relationship (from SMAD4 Table 20-12) illustrates why TRL >= 6 is the typical threshold for mission-critical components.*

### Real Mission Example: MarCO (Mars Cube One)

NASA's MarCO A and B (launched May 2018) were the first interplanetary CubeSats. They used:
- Iris transponder (JPL, TRL 6 at selection -- first deep-space CubeSat radio)
- COTS reaction wheels (Blue Canyon Technologies, TRL 9)
- Custom deployable reflectarray antenna (JPL, TRL 5 at selection)

The custom antenna was the highest-risk item. It required extensive development testing and was the last component to reach TRL 6 for CDR. This delayed the schedule by 4 months but ultimately succeeded.

*Lesson: If you must fly a low-TRL component, it will dominate your schedule and risk register.*

*[Source: "Mars Cube One (MarCO) -- Lessons Learned", A. Klesh et al., 33rd Annual Small Satellite Conference, 2019]*

---

## 3. Bill of Materials (BOM) Construction (20 min)

### Teaching Notes

The BOM is the definitive list of all hardware, software, and consumables required to build the satellite. It is the bridge between design and procurement.

### BOM Structure

A properly structured BOM follows the WBS hierarchy:

```
BOM Level 0: Spacecraft (S/C-001)
  BOM Level 1: Subsystem (e.g., EPS-000)
    BOM Level 2: Assembly (e.g., EPS-SA-000 Solar Array Assembly)
      BOM Level 3: Component (e.g., EPS-SA-001 Solar Cell String)
        BOM Level 4: Part (e.g., EPS-SA-001-01 Azur 3G30C cell)
```

### BOM Fields

| Field | Description | Example |
|-------|------------|---------|
| **Item ID** | Unique hierarchical identifier | EPS-BAT-001 |
| **Description** | Component name and model | GomSpace NanoPower P31u |
| **Manufacturer** | Vendor name | GomSpace A/S |
| **Part Number** | Manufacturer part number | P31U-9-30 |
| **Quantity** | Number required | 1 |
| **Unit Mass (g)** | Per-item mass | 94 |
| **Unit Power (W)** | Peak / average power draw | 0.5 / 0.2 |
| **Unit Cost (EUR)** | Procurement cost | 8,500 |
| **TRL** | Technology readiness level | 9 |
| **Heritage** | Previous mission(s) flown | GOMX-3, GOMX-4 |
| **Lead Time** | Procurement lead time | 12 weeks |
| **ECCN/USML** | Export classification | EAR99 |
| **Status** | Selected / Ordered / Received / Tested | Selected |

### SpaceCDF BOM Generation

In SpaceCDF, the BOM is built automatically from the Equipment Browser selections:
1. Each component selected in the Equipment Browser creates a BOM entry
2. Quantities are set using the quantity selector (e.g., x4 for reaction wheels)
3. The **Exports** tab generates a formatted BOM spreadsheet
4. The BOM includes both parametric estimates and actual COTS data for comparison

### Key Equations

> **BOM Mass Total:**
>
> M_BOM = Sum_i (m_i x q_i) + M_harness + M_fasteners + M_margin
>
> Where:
> - m_i = unit mass of component i
> - q_i = quantity of component i
> - M_harness = harness mass (typically 5-8% of dry mass for CubeSats)
> - M_fasteners = mechanical fasteners, standoffs, thermal hardware (~3-5%)
> - M_margin = system margin (typically 20% at Phase A)

### Worked Example

*3U CubeSat BOM Summary:*

| Subsystem | Components | Total Mass (g) | Total Power (W) | Total Cost (kEUR) |
|-----------|-----------|----------------|-----------------|-------------------|
| Structure | Rails, panels, fasteners | 350 | 0 | 8.0 |
| EPS | SA + battery + board | 420 | 0.5 | 18.0 |
| OBC | Flight computer + storage | 80 | 1.2 | 10.0 |
| AOCS | Star tracker + magnetorquers + RWs | 550 | 4.5 | 45.0 |
| TTC | S-band transceiver + patch antenna | 180 | 8.0 (TX) | 22.0 |
| Thermal | MLI + heaters | 60 | 2.0 (peak) | 3.0 |
| Payload | Multispectral imager | 800 | 12.0 | 65.0 |
| Harness | Cables, connectors | 180 | 0 | 2.5 |
| **Total** | | **2620** | **28.2 (peak)** | **173.5** |
| Allocation (6U) | | 12000 | 40.0 (SA EOL) | 250.0 |
| Margin | | 9380 (78%) | 11.8 (30%) | 76.5 (31%) |

---

## 4. Export Control and Procurement (25 min)

### Teaching Notes

Export control is one of the most commonly overlooked aspects of CubeSat missions, especially for international teams. Violations carry severe penalties (criminal prosecution, programme cancellation).

*[Source: ITAR -- 22 CFR Parts 120-130; EAR -- 15 CFR Parts 730-774; Canadian Controlled Goods Program -- Defence Production Act]*
*[URL: https://www.pmddtc.state.gov/ddtc_public (US ITAR); https://www.bis.doc.gov (US EAR)]*

### Export Control Regimes

| Regime | Governing Law | Applies To | Key Concern for CubeSats |
|--------|-------------|-----------|-------------------------|
| **ITAR** | US Arms Export Control Act | Defence articles (USML Categories IV, XI, XV) | Star trackers, rad-hard processors, some GPS receivers |
| **EAR** | Export Administration Act | Dual-use items (CCL) | Most COTS space components (ECCN 9A515) |
| **Canadian CGP** | Defence Production Act | Controlled goods in Canada | Handling US-origin ITAR items in Canadian facilities |
| **Wassenaar** | Wassenaar Arrangement | Multilateral export controls | Encryption, high-accuracy GNSS, imaging sensors |

### Component Classification Decision

```
Is the component on the US Munitions List (USML)?
  -> Yes: ITAR-controlled. Need DSP-5 license for export.
     Categories: IV (launch vehicles), XI (military electronics),
                 XV (spacecraft systems)
  -> No: Check Commerce Control List (CCL)
     Is it classified under ECCN 9A515 (spacecraft)?
       -> Yes: EAR-controlled. May need BIS license.
       -> No: Likely EAR99 (no license required for most destinations)
```

### Common ITAR-Controlled CubeSat Components

| Component Type | Why Controlled | Alternative |
|---------------|---------------|------------|
| Radiation-hardened processors | Military-grade rad tolerance | COTS processors with software mitigation |
| High-accuracy star trackers (< 1 arcsec) | Missile guidance applicability | Lower-accuracy models (> 5 arcsec) |
| Certain GPS/GNSS receivers | Above COCOM limits (>60,000 ft, >1000 kt) | Space-rated receivers with COCOM compliance |
| Propulsion systems (some) | Missile technology | Cold-gas or water-based systems |
| Encryption modules | Signals intelligence | Open-source encryption (may still need EAR review) |

### Procurement Workflow

```
1. Requirements -> Derive component specification
2. Market survey -> Identify candidate COTS products
3. Export classification -> Request ECCN from vendor
4. Trade study -> Score and rank candidates
5. Request for Quote (RFQ) -> Obtain pricing and lead times
6. Purchase Order (PO) -> Commit to procurement
7. Incoming inspection -> Verify against PO and datasheet
8. Integration -> Install and functionally test
```

### Real Mission Example: Export Control Impact

The BRITE-Constellation (Austria/Canada/Poland) was a series of nanosatellites for stellar photometry. The Canadian BRITE satellites (UniBRITE and BRITE-Austria, built by UTIAS/SFL) required careful export control management:
- US-origin ITAR components required Technical Assistance Agreements (TAAs)
- Controlled Goods registration required for the Canadian team
- Export permits needed for shipping between Canada, Austria, and the US launch site
- Total regulatory compliance effort: ~6 person-months and 12+ months lead time

*Lesson: Start export classification immediately when components are identified. A single ITAR component can add 6-12 months to the schedule.*

*[Source: Sarda, K. et al., "BRITE-Constellation Mission and Spacecraft", AIAA/USU Small Satellite Conference, 2014]*

---

## 5. Interface Compatibility Verification (20 min)

### Teaching Notes

As components are selected, every interface must be verified for compatibility. The three interface categories are RF, electrical, and mechanical.

### RF Chain Compatibility

The RF chain (transponder, cable, antenna) must be frequency-matched. This is the most common equipment incompatibility for CubeSat newcomers.

| Rule | Correct Example | Incorrect Example |
|------|----------------|-------------------|
| **Band match** | S-band transponder + S-band patch antenna | S-band transponder + X-band horn |
| **Impedance match** | 50 ohm transponder + 50 ohm cable + 50 ohm antenna | Mixed impedances cause reflections |
| **Connector match** | SMA on transponder + SMA-SMA cable + SMA on antenna | SMA to N-type needs adapter (loss) |
| **Polarisation** | RHCP antenna + RHCP ground station | RHCP to LHCP causes > 20 dB cross-pol loss |

> **Impedance Mismatch Loss:**
>
> Return_Loss (dB) = -20 * log10(|Gamma|)
>
> Where Gamma = (Z_load - Z_source) / (Z_load + Z_source)
>
> For a 50 ohm source into a 75 ohm load:
> Gamma = (75 - 50) / (75 + 50) = 0.2
> Return_Loss = -20 * log10(0.2) = 14 dB
> Mismatch_Loss = -10 * log10(1 - |Gamma|^2) = -10 * log10(1 - 0.04) = 0.18 dB

SpaceCDF checks RF compatibility automatically: if you select a transponder in one band and an antenna in another, a warning dialog appears.

### Electrical Interface Verification

| Parameter | Typical CubeSat | What to Verify |
|-----------|----------------|----------------|
| Bus voltage | 3.3V, 5V, or unregulated (6-8.4V Li-ion) | Component input voltage range covers bus voltage |
| Peak current | Per switched line limit (typically 1-3A) | Component inrush current does not exceed limit |
| Data protocol | I2C, SPI, UART, CAN, RS-422 | All devices on same bus use compatible protocol |
| Connector | PC/104, Hirose, Harwin | Physical connector type matches or adapter planned |

### Mechanical Interface Verification

| Parameter | CDS 3U Requirement | Verification |
|-----------|--------------------|----|
| Dimensions | 100.0 +/- 0.1 mm x 100.0 +/- 0.1 mm x 340.5 +/- 0.5 mm | Caliper measurement |
| Rail profile | 8.5 x 8.5 mm +/- 0.1 mm | Profile gauge |
| Component stack height | <= 83 mm internal width per U | 3D model check |
| CG location | Within 2 cm of geometric centre | Mass properties measurement |

---

## 6. Equipment Selection Exercise (35 min)

### Instructions

**Part A: Equipment Selection (20 min)**

1. Open the **Equipment Browser** in SpaceCDF
2. For each **required** category (blue dot), select at least one component:
   - Start with EPS (batteries + solar panels + EPS board)
   - Then OBC, AOCS sensors/actuators, TTC, structure
   - Use quantity selectors (e.g., x4 for reaction wheels, x3 for magnetorquers)
3. Watch the **live budget bar** as you select -- keep mass under allocation
4. When selecting TTC: verify the spectrum band matches your earlier selection
5. After all selections, review the **Budget Breakdown** on the Dashboard

**Part B: BOM Review and Export Check (15 min)**

1. Navigate to the **Exports** tab
2. Generate the **BOM** -- review all entries
3. For each component, check: Is the ECCN listed? Is it EAR99, ECCN 9A515, or ITAR?
4. Flag any components that may require export licences
5. Compute: BOM total mass vs parametric estimate vs launcher allocation

### Worksheet 4.1 Tasks

1. Complete the full BOM table (component, manufacturer, part number, mass, power, cost, TRL, ECCN)
2. Document the make/buy/reuse decision for each subsystem with rationale
3. Compute total BOM mass vs parametric estimate vs allocation -- state margin
4. Identify any export-controlled components and note the required licensing action
5. Describe one interface incompatibility found during selection and how it was resolved

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | NASA Technology Readiness Levels | https://www.nasa.gov/directorates/somd/space-communications-navigation-program/technology-readiness-levels/ |
| 2 | ECSS-Q-ST-20C Quality Assurance | https://ecss.nl/standard/ecss-q-st-20c-rev-2-quality-assurance-1-march-2023/ |
| 3 | US DDTC (ITAR) | https://www.pmddtc.state.gov/ |
| 4 | US BIS (EAR) | https://www.bis.doc.gov/ |
| 5 | CubeSat Design Specification Rev 14.1 | https://www.cubesat.org/s/CDS-REV14_1-2022-02-09.pdf |
| 6 | SMAD4 Chapter 20 (Cost Modelling) | Wertz, Everett, Puschell (eds.), Space Mission Engineering, Microcosm 2011 |
| 7 | MarCO Lessons Learned (Klesh et al.) | SSC19-WKII-07, 33rd Small Sat Conference, 2019 |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Make/Buy/Reuse | Buy COTS first; Reuse heritage second; Make custom only when necessary |
| TRL | Minimum TRL 6 for mission-critical components; TRL 7+ preferred for CubeSats |
| BOM | Hierarchical list: Subsystem -> Assembly -> Component -> Part, with full traceability |
| Export control | Classify every component (EAR99 / ECCN / ITAR); start early -- delays programme |
| RF compatibility | Band, impedance, connector, polarisation must all match across RF chain |
| Electrical | Bus voltage, data protocol, connector type verified per component |
| Budget tracking | Live totals during selection; stop if allocation exceeded |

---

# Session 4.2: Verification & Validation Matrix and Compliance

**Duration:** 2 hours
**Prerequisites:** Session 4.1 (equipment selected, BOM constructed)
**References:** ECSS-E-ST-10-02C Rev.1 (Verification), ECSS-E-ST-10-03C (Testing), NASA SEH Rev 2 sections 5.3-5.4, MIL-STD-1540E, MIL-STD-461G

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Distinguish between verification and validation using the ECSS/NASA definitions
2. Assign appropriate verification methods (IADT) to each requirement using a decision logic
3. Define environmental test levels derived from launch vehicle ICD specifications
4. Construct a compliance verification matrix mapping every requirement to its method, level, and phase
5. Identify when waivers are appropriate and document the waiver rationale

---

## 1. Verification vs Validation: Precise Definitions (15 min)

### Teaching Notes

*[Source: ECSS-E-ST-10-02C Rev.1 section 4; NASA SEH Rev 2 section 5.3 (Process 7: Product Verification) and section 5.4 (Process 8: Product Validation)]*

| | **Verification** | **Validation** |
|--|-----------------|----------------|
| **Question** | "Did we build the system right?" | "Did we build the right system?" |
| **Checks against** | Requirements (shall statements) | Stakeholder needs and operational expectations |
| **Standard** | ECSS-E-ST-10-02C | ECSS-E-ST-10-06C |
| **Performed by** | Engineering team | Users, operators, stakeholders |
| **When** | Throughout development (Phases B-D) | End of development + early operations (Phase D-E) |
| **Methods** | IADT (Inspection, Analysis, Demonstration, Test) | Operational demonstration, user acceptance testing |
| **Output** | Verification Control Document (VCD) | Validation report |

### The Critical Distinction

A system can be **verified** (every requirement marked "pass") but still **fail validation** if the requirements were written incorrectly. This happens when:
- Requirements were derived from misunderstood stakeholder needs
- The operational environment differs from assumptions
- Edge cases were not captured in requirements

### Example

- **Requirement:** "The system shall achieve GSD <= 10 m from 500 km altitude"
- **Verification (Test):** Calibration target imagery at 500 km -> measured GSD = 9.2 m -> **verified**
- **Validation:** Users attempt crop assessment with 9.2 m imagery -> "We can see field boundaries but cannot distinguish crop types; we needed GSD <= 5 m" -> **not validated**

*The requirement was met, but the stakeholder need was not satisfied because the requirement was insufficiently stringent.*

---

## 2. IADT Verification Methods in Detail (30 min)

### Teaching Notes

ECSS-E-ST-10-02C Rev.1 section 5.3 defines four verification methods. Note: ECSS uses "IADT" ordering; some NASA documents use "ATRI" -- the methods are identical.

*[Source: ECSS-E-ST-10-02C Rev.1 section 5.3; freely available from https://ecss.nl]*

### Inspection (I)

**Definition:** Visual or physical examination of the product, without operation or stimulation, to verify conformance to requirements.

**When to use:**
- Physical characteristics (dimensions, mass, surface finish, labelling)
- Manufacturing workmanship (solder joints, cable routing, MLI installation)
- Markings, identification, and safety labels
- Mechanical fit (deployer rail compliance)

**Evidence produced:** Inspection report with photographs, measurements, pass/fail checklist.

**Examples for CubeSats:**
- Mass measurement on calibrated scale -> verifies "M_dry <= 4.0 kg"
- Caliper measurement of rail profile -> verifies CDS dimensional compliance
- Visual inspection of antenna stowage -> verifies no protrusions beyond deployer envelope
- Workmanship inspection of PCB solder joints -> verifies IPC-A-610 Class 3

### Analysis (A)

**Definition:** Mathematical models, simulations, statistical analysis, or heritage comparison demonstrate compliance with acceptable confidence.

**When to use:**
- Physical testing is impossible or impractical (orbital lifetime, radiation total ionising dose)
- Early in development (Phase B) before hardware exists
- To demonstrate margin (link budget, thermal model, structural FEA)
- Statistical parameters (reliability prediction, debris casualty risk)
- Requirements involving orbital mechanics or mission-level performance

**Evidence produced:** Analysis report with model description, assumptions, inputs, results, uncertainty assessment, and sensitivity analysis.

**Examples for CubeSats:**
- Orbital mechanics analysis -> verifies revisit time requirement
- Thermal model (finite difference/finite element) -> verifies temperature within limits
- Link budget calculation -> verifies margin >= 3 dB at worst case
- Structural FEA -> verifies positive Margin of Safety under launch loads

> **Margin of Safety (structural):**
>
> MoS = (Allowable_stress / (Factor_of_Safety x Applied_stress)) - 1
>
> MoS must be >= 0 for all load cases.
> Factor_of_Safety: 1.25 (yield), 1.5 (ultimate) per ECSS-E-ST-32-10C.

### Demonstration (D)

**Definition:** The system is operated under controlled conditions to show that it performs as required, without requiring precise measurement of performance parameters.

**When to use:**
- Functional requirements ("the system shall deploy the antenna within 30 minutes of separation")
- Operational procedures ("the system shall respond to a mode change command within 5 seconds")
- Software functional requirements ("FDIR shall autonomously switch to safe mode on loss of attitude")

**Evidence produced:** Demonstration report with procedure, observations, photographs/video, pass/fail.

**Examples for CubeSats:**
- Antenna deployment test -> demonstrates deployment within time limit
- Safe mode entry test -> demonstrates autonomous FDIR response
- Ground station commanding test -> demonstrates full command chain

### Test (T)

**Definition:** Physical hardware subjected to controlled conditions; measured performance compared quantitatively to requirement thresholds.

**When to use:**
- Physical properties must be proven with quantitative measurement
- Environmental survivability must be demonstrated (vibration, thermal-vacuum, EMC)
- End-to-end functional chains must be proven under representative conditions
- Performance must be measured, not just observed

**Test types by purpose:**

| Test Type | Purpose | Level | Phase | Loads/Conditions |
|-----------|---------|-------|-------|-----------------|
| **Development** | Explore design space, find problems early | Unit/BB | B | As needed |
| **Qualification** | Prove design withstands worst-case + margin | Unit/System | C | Qual levels (MPE + margin) |
| **Acceptance** | Prove flight hardware is defect-free | System | D | Acceptance levels (MPE) |
| **Proto-flight** | Combined qual + acceptance (single unit) | System | C/D | Qual levels, acceptance duration |

### Proto-Flight Approach

For CubeSats, the **proto-flight** approach is standard because building a separate qualification unit is prohibitively expensive. The flight unit is tested to **qualification levels** but for **acceptance duration**.

*[Source: ECSS-E-ST-10-03C section 5.4.2.3; MIL-STD-1540E section 6.2.4]*

**Rationale:** Qualification duration is longer and more stressful -- this is acceptable for a dedicated qualification model that will not fly. For proto-flight, the shorter duration reduces fatigue life consumption while still screening for workmanship defects.

| Parameter | Qualification | Acceptance | Proto-flight |
|-----------|-------------|-----------|-------------|
| Vibration level | MPE + 3 dB | MPE | MPE + 3 dB |
| Vibration duration | 2 min/axis | 1 min/axis | 1 min/axis |
| TVAC temperature range | Predicted +/- 15 C | Predicted +/- 10 C | Predicted +/- 10 C |
| TVAC cycles | 8 | 4 | 4-8 |

---

## 3. Environmental Test Programme (30 min)

### Teaching Notes

*[Source: ECSS-E-ST-10-03C (Testing); Launch vehicle Payload User's Guides; MIL-STD-1540E]*

### Standard Environmental Test Sequence

The test sequence is designed so that each test stresses the hardware in a specific way, and functional tests between environmental tests detect any damage.

<!--
SVG Description: Environmental Test Sequence Flow Diagram

A vertical flowchart with boxes connected by downward arrows:
1. [Receive Flight Hardware] -> 
2. [Initial Functional Test (baseline)] ->
3. [Sine Vibration (3 axes)] ->
4. [Random Vibration (3 axes)] ->
5. [Post-Vibration Functional Test] ->
6. [Thermal Vacuum (4-8 cycles)] ->
7. [Post-TVAC Functional Test] ->
8. [EMC Test (if required)] ->
9. [Mass Properties Measurement] ->
10. [Deployer Fit Check] ->
11. [Final Functional Test] ->
12. [Pack and Ship to Launch Site]

Decision diamond after step 5: "Any anomaly?" 
  Yes -> "Investigate and resolve before proceeding"
  No -> Continue to step 6
-->

```
 +--------------------------+
 | Receive Flight Hardware  |
 +-----------+--------------+
             |
 +-----------v--------------+
 | Initial Functional Test  |  <- Reference baseline
 +-----------+--------------+
             |
 +-----------v--------------+
 | Sine Vibration (3 axes)  |  <- Low-frequency loads
 +-----------+--------------+
             |
 +-----------v--------------+
 | Random Vibration (3 axes)|  <- Broadband acoustic loads
 +-----------+--------------+
             |
 +-----------v--------------+        +-------------------+
 | Post-Vibe Functional Test| ------>| Anomaly?          |
 +-----------+--------------+  Fail  | Investigate &     |
             | Pass                  | resolve           |
 +-----------v--------------+        +-------------------+
 | Thermal Vacuum Testing   |  <- 4-8 cycles, func at extremes
 +-----------+--------------+
             |
 +-----------v--------------+
 | Post-TVAC Functional Test|
 +-----------+--------------+
             |
 +-----------v--------------+
 | EMC Test (if required)   |
 +-----------+--------------+
             |
 +-----------v--------------+
 | Mass + CG Measurement    |
 +-----------+--------------+
             |
 +-----------v--------------+
 | Deployer Fit Check       |
 +-----------+--------------+
             |
 +-----------v--------------+
 | Pack & Ship to Launch    |
 +--------------------------+
```

### Sine Vibration Test Levels

*[Source: Typical Falcon 9 Transporter Rideshare PUG]*

Sine vibration simulates the low-frequency launch vehicle structural modes (typically 5-100 Hz). These are quasi-static loads.

| Frequency Range (Hz) | Level | Notes |
|----------------------|-------|-------|
| 5 - 8 | 12.5 mm displacement (0-peak) | Displacement-controlled |
| 8 - 100 | 1.25 g (0-peak) | Acceleration-controlled |
| Sweep rate | 2 octaves/minute | Standard sweep rate |
| Axes | 3 (X, Y, Z) | Sequential, one axis at a time |

> **Sine Vibration Acceleration at Crossover Frequency:**
>
> a = (2 * pi * f)^2 * d
>
> At f = 8 Hz, d = 12.5 mm = 0.0125 m:
> a = (2 * pi * 8)^2 * 0.0125 = (50.27)^2 * 0.0125 = 2526.6 * 0.0125 = 31.6 m/s^2 = 3.22 g
>
> *Note: The transition from displacement to acceleration control occurs where the displacement limit would exceed the acceleration limit. The actual crossover depends on the specific profile.*

### Random Vibration Test Levels

Random vibration simulates the broadband acoustic and mechanical environment during launch. Levels are specified as Power Spectral Density (PSD) in g^2/Hz.

| Frequency (Hz) | PSD Level (g^2/Hz) | Notes |
|----------------|---------------------|-------|
| 20 | 0.01 | Start of profile |
| 20 - 50 | +3 dB/octave ramp | Rising |
| 50 - 800 | 0.04 (flat) | Maximum level plateau |
| 800 - 2000 | -6 dB/octave ramp | Falling |
| 2000 | 0.004 | End of profile |
| **Overall gRMS** | **~7.0 gRMS** | Qualification level |

> **Computing Overall gRMS from PSD Profile:**
>
> gRMS = sqrt( integral from f1 to f2 of PSD(f) df )
>
> For a flat PSD region: gRMS_flat = sqrt(PSD_flat x (f2 - f1))
>
> Example: PSD = 0.04 g^2/Hz from 50-800 Hz:
> gRMS_flat = sqrt(0.04 x 750) = sqrt(30) = 5.48 gRMS
>
> The ramp sections and flat section are summed in quadrature:
> gRMS_total = sqrt(gRMS_ramp1^2 + gRMS_flat^2 + gRMS_ramp2^2)

### Thermal Vacuum Test Profile

| Parameter | Proto-flight Level | Notes |
|-----------|-------------------|-------|
| Hot case temperature | Predicted max + 10 C | e.g., if thermal model predicts +55 C -> test to +65 C |
| Cold case temperature | Predicted min - 10 C | e.g., if thermal model predicts -20 C -> test to -30 C |
| Number of cycles | 4 minimum (proto-flight) | Start and end at hot; functional test at each extreme |
| Vacuum level | < 10^-5 mbar | Space-representative vacuum |
| Dwell time at extreme | >= 1 hour | Allow thermal stabilisation (< 1 C/hr gradient) |
| Temperature transition rate | 1-3 C/min | Limited by chamber capability |
| Functional test | Full performance at hot and cold extremes | Subset functional at intermediate transitions |

> **TVAC Cycle Duration Estimate:**
>
> t_cycle = 2 x (Delta_T / ramp_rate) + 2 x t_dwell + 2 x t_functional
>
> Example: Delta_T = 95 C (from -30 to +65 C), ramp = 2 C/min, dwell = 1 hr, functional = 2 hr:
> t_cycle = 2 x (95/2 min) + 2 x 60 min + 2 x 120 min = 95 + 120 + 240 = 455 min = 7.6 hr
>
> Total TVAC campaign (4 cycles + setup): ~4 x 7.6 + 8 = 38.4 hr ~ 5 working days

### EMC Testing

*[Source: MIL-STD-461G; ECSS-E-ST-20-07C]*

| Test | Standard | Purpose |
|------|----------|---------|
| CE102 Conducted Emissions | MIL-STD-461G | Measure spurious conducted emissions on power lines |
| RE102 Radiated Emissions | MIL-STD-461G | Measure unintentional RF radiation from satellite |
| CS101 Conducted Susceptibility | MIL-STD-461G | Verify immunity to power line transients |
| RS103 Radiated Susceptibility | MIL-STD-461G | Verify immunity to external RF fields |

*Note: EMC testing is not always required for CubeSats. It depends on the launch provider and co-manifested payloads. Check the rideshare ICD.*

---

## 4. Compliance Verification Matrix Construction (20 min)

### Teaching Notes

The Verification Matrix (also called Compliance Matrix or Verification Cross-Reference Matrix, VCRM) is the central document linking every requirement to its verification evidence.

*[Source: ECSS-E-ST-10-02C Rev.1 section 6; DRD in Annex A]*

### Matrix Structure

| Req ID | Requirement Text | Method | Phase | Level | Responsible | Facility | Status | Evidence |
|--------|-----------------|--------|-------|-------|-------------|----------|--------|----------|
| SYS-001 | M_dry <= 4.0 kg | I | D | System | Structures | Clean room | Planned | Mass measurement report |
| SYS-002 | Survive 7 gRMS random | T | C/D | System | Structures | Vibe lab | Planned | Vibration test report |
| SYS-003 | GSD <= 10 m at 500 km | A | B | System | Payload | N/A | Planned | Optical analysis report |
| SYS-004 | Link margin >= 3 dB | A | B | System | Comms | N/A | Planned | Link budget analysis |
| SYS-005 | Antenna deploys < 30 min | D | D | System | Mechanisms | Clean room | Planned | Deployment demonstration |

### IADT Assignment Decision Logic

```
Is it a physical property (mass, dimensions, surface finish)?
  -> Inspection (I), Phase D, System level

Can it only be proven by quantitative measurement under controlled conditions?
  -> Test (T), Phase C/D, Unit or System level

Can it be demonstrated by operating the system (functional, not precision)?
  -> Demonstration (D), Phase D, System level

Can it be shown with acceptable confidence through modelling?
  -> Analysis (A), Phase B/C, System level

Is it a document, process, or plan?
  -> Review of Design (R*), Phase B
  (* Note: ECSS uses IADT; "Review" is sometimes used informally but is not
     a formal ECSS method. Reviews are part of the verification process but
     requirements verified by examining design documentation fall under
     "Analysis" in strict ECSS usage.)
```

### Multiple Methods

Some requirements need **both** analysis (early confidence) and test (final proof):

| Requirement | Analysis (Phase B) | Test (Phase C/D) |
|------------|-------------------|------------------|
| Structural survival under launch loads | FEA with positive MoS | Vibration test -- no damage |
| Pointing accuracy <= 0.1 deg | Error budget analysis | On-orbit calibration measurement |
| Thermal within limits (-20 to +55 C) | Thermal model simulation | TVAC functional test at extremes |
| RF link margin >= 3 dB | Link budget calculation | RF compatibility test (if feasible) |

In the matrix, list the **primary** method and note "confirmed by [secondary method] in Phase [X]".

### Waiver Process

When a requirement cannot be verified by the prescribed method, a **waiver** is needed:

| Waiver Type | When Used | Approval Level |
|-------------|-----------|---------------|
| **Non-compliance** | Requirement cannot be met; accept deviation | Project manager + customer |
| **Method deviation** | Different verification method used (e.g., analysis instead of test) | Systems engineer + quality |
| **Tailoring** | Standard requirement not applicable to this mission | Systems engineer |

**Waiver documentation must include:** Requirement ID, deviation description, technical justification, risk assessment, and compensating measures.

---

## 5. SpaceCDF V&V Matrix Exercise (25 min)

### Instructions

1. Navigate to the **V&V Matrix** tab in SpaceCDF
2. Requirements are auto-populated from the design
3. For each requirement, assign:
   - **Method:** I, A, D, or T (use the decision logic above)
   - **Phase:** When will verification occur (B, C, D)?
   - **Level:** Unit, subsystem, or system level?
   - **Status:** All should be "Planned" at this stage
4. Use the **filter buttons** to view by method type:
   - Count: How many are Analysis? Test? Demonstration? Inspection?
   - Are there any requirements with no method assigned?
5. Identify requirements that need **two methods** (analysis in Phase B + test in Phase D)
6. Discuss with your team: which tests are most critical? Which drive the test campaign schedule?

### Worksheet 4.2 Tasks

1. Assign IADT method to 10 key requirements (justify each choice)
2. Identify 3 requirements that need both analysis AND test
3. Specify the complete environmental test sequence for your mission
4. Determine which test levels apply from your selected launch vehicle PUG
5. Identify any requirements that may need waivers -- document the rationale

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-E-ST-10-02C Rev.1 (Verification) | https://ecss.nl/standard/ecss-e-st-10-02c-rev-1-verification/ |
| 2 | ECSS-E-ST-10-03C (Testing) | https://ecss.nl/standard/ecss-e-st-10-03c-testing/ |
| 3 | NASA SEH Rev 2 sections 5.3-5.4 | https://www.nasa.gov/reference/systems-engineering-handbook/ |
| 4 | MIL-STD-1540E (Test Requirements for Launch/Upper Stage/Space Vehicles) | https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=36197 |
| 5 | MIL-STD-461G (EMI/EMC) | https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=35789 |
| 6 | CubeSat Design Specification Rev 14.1 | https://www.cubesat.org/s/CDS-REV14_1-2022-02-09.pdf |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| V vs V | Verification = meets requirements (IADT); Validation = meets stakeholder needs |
| IADT | Inspection (physical), Analysis (models), Demonstration (functional), Test (quantitative) |
| Proto-flight | CubeSats: single flight unit tested to qualification levels, acceptance duration |
| Sine vibration | 5-100 Hz, 1.25 g, quasi-static launch loads |
| Random vibration | 20-2000 Hz, ~7 gRMS overall, broadband acoustic environment |
| TVAC | Predicted extremes +/- 10 C, 4+ cycles, functional at each extreme |
| Compliance matrix | Per requirement: method + phase + level + responsible + status + evidence |
| Waivers | Document deviation, justification, risk, and compensating measures |

---

# Session 4.3: Risk, Interfaces & FMECA

**Duration:** 2 hours
**Prerequisites:** Sessions 4.1-4.2 (equipment selected, V&V methods assigned)
**References:** ECSS-M-ST-80C (Risk Management), ECSS-Q-ST-30-02C (FMEA/FMECA), ECSS-E-ST-10-24C (Interface Management), NASA SEH Rev 2 section 6.4, NPR 8000.4B

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Construct and populate a risk register using a 5x5 likelihood-consequence matrix
2. Build an N-squared (N^2) interface matrix and identify interface conflicts
3. Perform a simplified FMEA/FMECA for critical subsystems
4. Identify single-point failures and compute series/parallel reliability
5. Classify risks and select appropriate mitigation strategies (accept, mitigate, transfer, avoid)

---

## 1. Risk Management Process (20 min)

### Teaching Notes

*[Source: ECSS-M-ST-80C (Risk Management); NASA SEH Rev 2 section 6.4 (Process 13: Technical Risk Management)]*
*[URL: https://ecss.nl/standard/ecss-m-st-80c-risk-management-31-july-2008/]*

### The Four-Step Process

Risk management is continuous throughout the project lifecycle. The four steps are:

1. **Identify** -- What can go wrong? (Brainstorming, checklists, historical data, expert judgment)
2. **Assess** -- How likely is it? How severe would the consequence be? (Scoring)
3. **Mitigate** -- What can we do to reduce likelihood or consequence? (Strategy selection)
4. **Monitor** -- Is the risk increasing, decreasing, or stable? (Tracking, triggers, escalation)

### Risk Sources

| Source | Example Risks |
|--------|--------------|
| **Technical** | Component failure, interface mismatch, performance shortfall, software defect |
| **Schedule** | Component delivery delay, test facility unavailable, regulatory delay |
| **Cost** | Component price increase, scope creep, test campaign overrun |
| **Programmatic** | Funding cut, personnel turnover, partner withdrawal |
| **External** | Launch delay/failure, spectrum interference, export control denial |

---

## 2. The 5x5 Risk Matrix (25 min)

### Teaching Notes

The 5x5 matrix is the standard risk scoring tool used across ESA, NASA, and commercial space programmes.

### Likelihood Scale

| Level | Likelihood | Description | Probability Range |
|-------|-----------|-------------|-------------------|
| 1 | Remote | Very unlikely; no precedent in similar missions | < 5% |
| 2 | Unlikely | Could happen but improbable; has occurred rarely | 5 - 20% |
| 3 | Possible | Has happened on similar missions; credible scenario | 20 - 50% |
| 4 | Likely | Expected to occur at least once during the mission | 50 - 80% |
| 5 | Almost certain | Will almost certainly occur; multiple precedents | > 80% |

### Consequence Scale

| Level | Consequence | Technical Impact | Cost Impact | Schedule Impact |
|-------|-----------|-----------------|-------------|----------------|
| 1 | Negligible | No performance impact | < 1% overrun | < 1 week slip |
| 2 | Minor | Minor performance degradation; workaround exists | 1 - 5% overrun | 1 - 4 week slip |
| 3 | Moderate | Significant performance loss; mission degraded | 5 - 15% overrun | 1 - 3 month slip |
| 4 | Major | Mission capability severely degraded; partial loss | 15 - 30% overrun | 3 - 6 month slip |
| 5 | Catastrophic | Mission failure; total loss | > 30% overrun | > 6 month slip or cancellation |

### Risk Score and Classification

> **Risk Score:**
>
> R = L x C
>
> Where L = Likelihood (1-5), C = Consequence (1-5)

### 5x5 Risk Matrix (Colour-Coded)

```
             Consequence ->
             1       2       3       4       5
  L   5 |   5(M) | 10(H) | 15(H) | 20(C) | 25(C) |
  i   4 |   4(L) |  8(M) | 12(H) | 16(C) | 20(C) |
  k   3 |   3(L) |  6(M) |  9(M) | 12(H) | 15(H) |
  e   2 |   2(L) |  4(L) |  6(M) |  8(M) | 10(H) |
  l   1 |   1(L) |  2(L) |  3(L) |  4(L) |  5(M) |
  i
  h
  o
  o
  d

  L = Low (1-4):    Accept and monitor
  M = Medium (5-9): Mitigate if cost-effective
  H = High (10-15): Active mitigation required
  C = Critical (16-25): Redesign or descope required
```

### CubeSat-Specific Risk Examples

| Risk | L | C | Score | Category | Typical Mitigation |
|------|---|---|-------|----------|-------------------|
| Deployment mechanism failure (antenna, SA) | 3 | 4 | 12 | High | Redundant mechanisms; 100+ ground test cycles |
| Communication loss after separation | 2 | 5 | 10 | High | Beacon mode; timer-based antenna deploy; multiple GS |
| ADCS does not achieve pointing specification | 3 | 3 | 9 | Medium | Margin in pointing budget; on-orbit calibration plan |
| Power budget negative during eclipse | 2 | 4 | 8 | Medium | Conservative duty cycling; 20% battery margin |
| COTS component radiation failure (SEU/SEL) | 2 | 4 | 8 | Medium | Watchdog resets; latchup protection circuits; EDAC |
| Software bug causing spurious safe mode entry | 4 | 2 | 8 | Medium | Extensive software testing; staged upload; safe mode must work independently |
| Thermal exceedance (hot case) | 2 | 3 | 6 | Medium | Additional radiator area; duty cycle limit |
| Launch delay (vehicle failure) | 3 | 2 | 6 | Medium | Manifest on multiple vehicles; schedule buffer |
| Spectrum licensing delay | 3 | 2 | 6 | Medium | Start filing 12+ months before planned launch |

### Mitigation Strategies

| Strategy | Description | When to Use | Cost Impact |
|----------|-------------|-------------|-------------|
| **Accept** | Risk is within tolerance; monitor only | Score 1-4 (Low) | None |
| **Mitigate** | Reduce L or C through design changes, testing, or procedures | Score 5-15 | Moderate -- cost of mitigation |
| **Transfer** | Pass risk to another party (insurance, supplier warranty) | Financial risk; operational risk | Premium or contract cost |
| **Avoid** | Change design to eliminate the risk entirely | Score 16-25 (Critical) | May affect performance or cost |

---

## 3. N-Squared (N^2) Interface Matrix (25 min)

### Teaching Notes

The N^2 matrix is the standard systems engineering tool for identifying and managing interfaces between subsystems. It was popularised by NASA and ESA CDF practice.

*[Source: ECSS-E-ST-10-24C (Interface Management); NASA SEH Rev 2 section 6.3 (Process 12: Interface Management)]*

### What is an N^2 Matrix?

For a system with N subsystems, the N^2 matrix is an N x N grid where:
- **Diagonal cells** contain the subsystem names
- **Off-diagonal cells** contain the interfaces between subsystems
- **Cell (i, j)** = outputs FROM subsystem i TO subsystem j (read across the row)
- **Cell (j, i)** = outputs FROM subsystem j TO subsystem i (read down the column)

### N^2 Matrix Example (6 Subsystems)

```
         TO ->
         EPS      OBC      AOCS     TTC      Payload  Structure
FROM
EPS      [EPS]    28V bus  28V bus  28V bus  28V bus   Mounting
         ------   5V reg   5V reg   5V reg   5V reg   bolts
                  I2C HK   I2C HK   I2C HK   
OBC      Pwr cmd  [OBC]    Cmd      TC data  Cmd      ---
         Telem    ------   I2C/SPI  UART     SPI/UART
AOCS     Pwr req  Att data [AOCS]   Att for  Att data Mount
         ---      AOCS HK  ------   antenna  pointing vibration
TTC      Pwr req  Rx data  ---      [TTC]    ---      Antenna
         ---      Cmd fwd           ------            mount
Payload  Pwr req  Sci data Pointing ---      [PYLD]   FOV
         ---      PL HK    request           ------   clearance
Struct   ---      ---      Sensor   Antenna  Payload  [STRUCT]
                           mounting mounting mounting  ------
```

### Interface Types

Colour-code the N^2 matrix by interface type:

| Type | Colour | Examples |
|------|--------|---------|
| **Electrical power** | Red | 28V bus, 5V regulated, switched lines |
| **Data** | Blue | I2C, SPI, UART, CAN, RS-422 |
| **RF** | Green | Coaxial cable, waveguide |
| **Mechanical** | Orange | Mounting bolts, thermal straps, alignment pins |
| **Thermal** | Yellow | Conductive paths, radiative coupling |
| **Software** | Purple | Command interfaces, telemetry packets, mode transitions |

### Interface Conflict Detection

An **interface conflict** exists when:
- Subsystem A expects to send 28V but Subsystem B only accepts 5V
- Subsystem A uses I2C but Subsystem B only has SPI
- Subsystem A is in S-band but Subsystem B antenna is X-band
- Subsystem A mounts on the +Z face but Structure has no mounting provision on +Z

SpaceCDF detects many of these automatically through the **constraint engine** and displays conflicts as warning badges on the Dashboard.

### Worked Example: Detecting a Conflict

*Problem:* The OBC sends commands to the reaction wheels via I2C. The selected reaction wheel unit (RWP100 from Blue Canyon) uses RS-422. This is a data protocol mismatch.

*Resolution options:*
1. Select a different reaction wheel that supports I2C
2. Add an I2C-to-RS-422 bridge (additional component, mass, cost, failure point)
3. Select a different OBC that supports RS-422

*In SpaceCDF:* This conflict would appear as a warning in the Equipment Browser when the reaction wheel is selected, because the system checks data protocol compatibility.

---

## 4. FMEA/FMECA (25 min)

### Teaching Notes

*[Source: ECSS-Q-ST-30-02C (Failure Mode, Effects, and Criticality Analysis); ECSS-Q-ST-30C (Dependability)]*
*[URL: https://ecss.nl/standard/ecss-q-st-30-02c-failure-mode-effects-and-criticality-analysis-fmeca-6-march-2009/]*

### Definitions

- **FMEA** (Failure Mode and Effects Analysis): Identifies failure modes, their causes, and effects on the system
- **FMECA** (Failure Mode, Effects, and Criticality Analysis): FMEA + criticality ranking

### FMEA/FMECA Table Structure

| Item | Function | Failure Mode | Cause | Local Effect | System Effect | Severity | Detection | Compensating Provision | Criticality |
|------|----------|-------------|-------|-------------|---------------|----------|-----------|----------------------|------------|
| OBC | Process commands, run FSW | Processor lockup | SEU, firmware bug | No command processing | Loss of mission control | 5 | HK timeout | Watchdog reset; redundant OBC (if fitted) | 1 (SPF) |
| Battery | Store energy | Cell short | Manufacturing defect | Reduced capacity | Shortened eclipse survival | 3 | Voltage monitoring | Cell balancing; margin in capacity | 2 |
| Reaction Wheel | Provide torque | Bearing seizure | Lubrication failure | Loss of one axis control | Degraded pointing | 4 | Current anomaly | 4-wheel config (3+1 redundancy) | 3 (with redundancy) |
| Antenna | Radiate RF | Deployment failure | Mechanism jam | No antenna deployed | No communication | 5 | Beacon absence | Redundant deployment; burn wire + spring | 1 (SPF) |

### Criticality Categories

| Category | Definition | Action Required |
|----------|-----------|----------------|
| **1 (Catastrophic)** | Single failure causes mission loss; no compensation | Redesign to add redundancy or accept with justification |
| **2 (Critical)** | Single failure causes significant degradation | Mitigate (redundancy, operational workaround) |
| **3 (Major)** | Single failure causes moderate degradation | Monitor; plan operational workaround |
| **4 (Minor)** | Single failure has negligible mission impact | Accept |

### Single-Point Failure (SPF) Analysis

A **single-point failure** is any single component whose failure alone causes loss of mission. Identifying SPFs is a critical output of the FMECA.

**Typical CubeSat Single-Point Failures:**

| Component | Why it is an SPF | Common Mitigation |
|-----------|-----------------|-------------------|
| OBC (single processor) | No command processing -> no mission | Watchdog timer + autonomous safe mode + EDAC memory |
| Battery (single pack) | No stored energy -> no eclipse survival | Cell-level monitoring; conservative DoD limit (< 20%) |
| Antenna (non-redundant deploy) | No RF link -> no commanding/telemetry | Redundant deployment mechanisms (burn wire + spring) |
| Solar array (deployment) | No power generation -> mission loss within hours | Redundant deployment; hinge spring + motor backup |
| EPS main board | No power distribution | Typically no mitigation (accepted SPF in CubeSats) |

### Key Equations: Reliability

> **Series Reliability (all components must work):**
>
> R_series = Product of R_i for i = 1 to n
>
> For n components each with reliability R_i:
> R_series = R_1 x R_2 x ... x R_n
>
> Example: 5 components each with R = 0.99:
> R_series = 0.99^5 = 0.951

> **Parallel Reliability (at least one must work -- redundancy):**
>
> R_parallel = 1 - Product of (1 - R_i) for i = 1 to n
>
> For n identical redundant units each with R:
> R_parallel = 1 - (1 - R)^n
>
> Example: 2 redundant deployment mechanisms each with R = 0.95:
> R_parallel = 1 - (1 - 0.95)^2 = 1 - (0.05)^2 = 1 - 0.0025 = 0.9975

> **Mean Time Between Failures (MTBF):**
>
> MTBF = Total_operating_hours / Number_of_failures
>
> For a component with failure rate lambda (failures/hour):
> MTBF = 1 / lambda
>
> **Reliability over time (exponential model):**
> R(t) = e^(-t / MTBF) = e^(-lambda * t)
>
> Example: MTBF = 50,000 hours, mission duration = 8,760 hours (1 year):
> R = e^(-8760/50000) = e^(-0.1752) = 0.839

> **System Availability:**
>
> A = MTBF / (MTBF + MTTR)
>
> Where MTTR = Mean Time To Repair (or recover, for spacecraft)
>
> For a spacecraft with MTBF = 50,000 hr and MTTR = 2 hr (safe mode recovery):
> A = 50000 / (50000 + 2) = 0.99996

### Worked Example: Reaction Wheel Redundancy

*Problem:* A fine-pointing mission requires 3-axis attitude control. Each reaction wheel has R = 0.98 over the 2-year mission.

*Configuration A -- 3 wheels (no redundancy):*
R_system = R^3 = 0.98^3 = 0.941

*Configuration B -- 4 wheels in 3-of-4 redundancy (1 spare):*
R_system = 4 x R^4 - 3 x R^3 ... Using the binomial:
P(>= 3 working) = C(4,4) x R^4 + C(4,3) x R^3 x (1-R)^1
= 0.98^4 + 4 x 0.98^3 x 0.02
= 0.9224 + 4 x 0.9412 x 0.02
= 0.9224 + 0.0753
= 0.9977

*Adding one spare wheel improves reliability from 0.941 to 0.998 -- a significant improvement for modest mass and cost increase.*

### Real Mission Example: Hitomi (ASTRO-H)

JAXA's Hitomi X-ray observatory was lost on 26 March 2016, just 37 days after launch, due to a cascading failure in the AOCS subsystem:
1. An incorrect parameter in the star tracker caused an erroneous attitude estimate
2. The reaction wheels applied incorrect torques based on the bad estimate
3. Thrusters fired to "correct" the (phantom) attitude error, causing rapid spin
4. The satellite spun up beyond structural limits, and the extensible optical bench broke off

**Root cause:** Software parameter error (unit conversion) + inadequate FDIR logic + no cross-check between attitude sensors.

*Lesson: FMECA must consider cascading failures and common-cause failures, not just single-component failures. Software errors are failure modes too.*

*[Source: JAXA Hitomi Investigation Report, 2016, available at https://global.jaxa.jp/press/2016/05/20160531_hitomi.html]*

---

## 5. Risk & Interface Exercise (25 min)

### Instructions

1. **Dashboard** -- Check the reliability score and conflict count
2. **Risk Register Construction** (Worksheet 4.3):
   - Identify **5 technical risks** for your mission design
   - Score each on the 5x5 matrix (L x C)
   - Define mitigation strategy for any scoring >= 10
   - Assign an owner (which CDF position is responsible)
3. **N^2 Matrix** -- Build a simplified N^2 matrix for your mission:
   - List 6 subsystems on the diagonal
   - Fill in the interfaces (power, data, RF, mechanical)
   - Identify at least 2 interface conflicts
4. **SPF Analysis** -- Identify all single-point failures in your design:
   - For each SPF: Is it acceptable? If not, what redundancy is needed?
   - Compute the reliability improvement from adding redundancy to one SPF

### Discussion Prompts

- "What is the highest-risk item in your design? What would it cost to mitigate?"
- "Do you have any interface conflicts that cannot be resolved without changing a component selection?"
- "Which single-point failure are you most concerned about? Would the customer accept it?"

### Worksheet 4.3 Tasks

1. Complete the risk register (5 risks minimum, scored)
2. Build a 6x6 N^2 interface matrix with colour-coded interface types
3. Complete the FMECA table for 4 critical components
4. List all single-point failures with accept/mitigate decision
5. Calculate series reliability for your mission's critical chain

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-M-ST-80C (Risk Management) | https://ecss.nl/standard/ecss-m-st-80c-risk-management-31-july-2008/ |
| 2 | ECSS-Q-ST-30-02C (FMEA/FMECA) | https://ecss.nl/standard/ecss-q-st-30-02c-failure-mode-effects-and-criticality-analysis-fmeca-6-march-2009/ |
| 3 | ECSS-E-ST-10-24C (Interface Management) | https://ecss.nl/standard/ecss-e-st-10-24c-interface-management/ |
| 4 | NASA SEH Rev 2, section 6.4 | https://www.nasa.gov/reference/systems-engineering-handbook/ |
| 5 | JAXA Hitomi Investigation Report | https://global.jaxa.jp/press/2016/05/20160531_hitomi.html |
| 6 | ECSS-Q-ST-30C (Dependability) | https://ecss.nl/standard/ecss-q-st-30c-dependability/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Risk process | Identify -> Assess -> Mitigate -> Monitor (continuous throughout lifecycle) |
| 5x5 matrix | L x C = Risk Score; Low (1-4), Medium (5-9), High (10-15), Critical (16-25) |
| Strategies | Accept (low), Mitigate (medium-high), Transfer (financial), Avoid (critical) |
| N^2 matrix | N x N grid mapping all subsystem interfaces; colour-code by type |
| Interface conflicts | Protocol mismatch, voltage mismatch, band mismatch -- detect early |
| FMECA | Failure mode -> cause -> local effect -> system effect -> severity -> detection -> mitigation |
| SPF | Single-point failures must be identified, assessed, and accepted or mitigated |
| Reliability | R_series = Product(R_i); R_parallel = 1 - Product(1-R_i); R(t) = e^(-lambda*t) |

---

# Session 4.4: Cost Estimation & Design Review

**Duration:** 2 hours
**Prerequisites:** Sessions 4.1-4.3 (equipment selected, V&V planned, risks assessed)
**References:** SMAD4 Ch.20, NASA Cost Estimating Handbook (CEH) v4.0, Aerospace Corp SSCM, NPR 7120.5F (WBS), ECSS-M-ST-60C (Cost Management), NPR 7123.1D Appendix G (Reviews)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Estimate mission cost using parametric (CER), analogy, and bottom-up methods
2. Structure a Work Breakdown Structure (WBS) for a CubeSat project
3. Apply learning curve effects for constellation cost estimation
4. Assess cost risk using confidence levels (P50/P70/P80)
5. Prepare for and conduct a design review (SRR/PDR/CDR) with gate criteria
6. Present design evidence clearly and respond to review board questions

---

## 1. Cost Estimation Methodologies (25 min)

### Teaching Notes

*[Source: NASA CEH v4.0 Appendix C; SMAD4 Chapter 20; Aerospace Corp SSCM]*
*[URL: https://www.nasa.gov/offices/ocfo/references-and-tools/ (NASA CEH)]*

### Three Primary Methods

| Method | Description | Accuracy (1-sigma) | When to Use | Data Required |
|--------|-------------|-------------------|-------------|---------------|
| **Parametric** | Cost Estimating Relationships (CERs) from historical database | +/- 30-50% | Phase 0/A (few details known) | Mass, power, mission type |
| **Analogy** | Compare to similar past mission, adjust for differences | +/- 20-40% | Phase A/B (reference mission available) | Detailed knowledge of reference |
| **Bottom-up** | Sum actual vendor quotes + labour estimates + facilities | +/- 10-20% | Phase B/C (detailed design) | BOM, vendor quotes, labour rates |

### Parametric Cost Estimating Relationships (CERs)

CERs express cost as a function of technical parameters, derived from regression analysis of historical data.

> **General CER Form:**
>
> Cost = a x (Parameter)^b x Complexity_factor
>
> Where:
> - a = coefficient (from regression)
> - Parameter = usually dry mass (kg), power (W), or data rate
> - b = exponent (typically 0.5-1.0)
> - Complexity_factor = adjustment for mission difficulty

### USCM (Unmanned Space Vehicle Cost Model) CERs

*[Source: SMAD4 Table 20-8; US Air Force USCM database]*

| Subsystem | CER (FY2010 $K) | Parameter | Typical b |
|-----------|-----------------|-----------|-----------|
| Structure | 157 x M_struct^0.83 | Dry mass (kg) | 0.83 |
| Thermal | 394 x M_therm^0.635 | Dry mass (kg) | 0.635 |
| EPS | 62.7 x M_EPS^1.00 | Dry mass (kg) | 1.00 |
| TTC | 545 x M_TTC^0.761 | Dry mass (kg) | 0.761 |
| AOCS | 464 x M_AOCS^0.867 | Dry mass (kg) | 0.867 |
| Propulsion | 17.8 x M_prop^0.75 | Dry mass (kg) | 0.75 |
| Integration & Test | 10.4 x M_dry^0.907 | Total dry mass (kg) | 0.907 |
| Program Management | 12.3% of hardware cost | N/A | N/A |
| Systems Engineering | 14.2% of hardware cost | N/A | N/A |

### SSCM (Small Satellite Cost Model)

The Aerospace Corporation SSCM was specifically calibrated for satellites < 500 kg. It provides more accurate estimates for CubeSats than USCM.

*[Source: Aerospace Corp, "Small Satellite Cost Model (SSCM)", available through Aerospace TOR]*

**Key SSCM adjustments for CubeSats:**
- COTS hardware costs are catalogue prices, not mass-based CERs
- Labour costs dominate for university/small-team projects
- NRE is heavily dependent on mission uniqueness
- Standard CERs (designed for > 100 kg) over-predict by 2-6x for nano/micro class

### CubeSat-Calibrated Pricing (SpaceCDF)

SpaceCDF uses a hybrid approach: COTS flat pricing for nano/micro class, CERs for larger spacecraft.

| Subsystem | CubeSat COTS Cost (kEUR) | USCM CER (kEUR, for CubeSat mass) | Ratio |
|-----------|--------------------------|-----------------------------------|-------|
| EPS | 15 | 60 | CER 4x higher |
| AOCS (fine) | 40 | 66 | CER 1.6x higher |
| TTC (S-band) | 20 | 25 | Similar |
| OBC | 10 | 12 | Similar |
| Structure | 8 | 3 | CER lower (min order effect) |
| Payload | 50 (variable) | 300 | CER 6x higher for COTS payloads |

*This confirms that for CubeSats, COTS pricing is more reliable than parametric CERs for hardware cost.*

### Worked Example: Parametric vs Bottom-Up

*3U Earth observation mission:*

| WBS Element | Parametric (kEUR) | Bottom-Up (kEUR) | Notes |
|-------------|-------------------|-------------------|-------|
| Structure | 8 | 8.5 | ISIS 3U structure |
| EPS | 18 | 16.2 | GomSpace P31u + SA |
| OBC | 12 | 10.0 | NanoAvionics SatBus |
| AOCS | 45 | 42.0 | BCT XACT-15 |
| TTC | 22 | 20.5 | Endurosat S-band |
| Thermal | 5 | 3.0 | Passive only |
| Payload | 65 | 58.0 | Simera Sense xScape |
| Harness | 3 | 2.5 | Custom cables |
| **Hardware subtotal** | **178** | **160.7** | |
| I&T (12%) | 21 | 19.3 | |
| Software (8%) | 14 | 12.9 | |
| PM/SE/MA (13%) | 23 | 20.9 | |
| Launch | 200 | 195.0 | SpaceX Transporter |
| Ground (5%) | 9 | 8.0 | SatNOGS + dedicated |
| Operations (3 yr) | 45 | 40.0 | 0.5 FTE |
| **TOTAL** | **490** | **456.8** | |

*The parametric estimate is ~7% higher than bottom-up. This is expected: parametric includes inherent uncertainty and contingency.*

---

## 2. Cost Breakdown Structure (WBS) (20 min)

### Teaching Notes

The Work Breakdown Structure (WBS) is the hierarchical decomposition of all work required to complete the mission. It is the foundation for cost estimation, scheduling, and management.

*[Source: NPR 7120.5F Appendix G; ECSS-M-ST-60C; NASA CEH v4.0 Appendix B]*

### Standard CubeSat WBS

```
WBS Level 1: Mission Total
  1.0  Programme Management                5%    (oversight, reviews, reporting)
  2.0  Systems Engineering                 5%    (budgets, interfaces, trade studies)
  3.0  Mission Assurance                   3%    (quality, reliability, parts)
  4.0  Payload                            20%    (instrument + calibration)
    4.1  Payload instrument hardware
    4.2  Payload software
    4.3  Payload calibration & characterisation
  5.0  Spacecraft Bus Hardware            30%    (all subsystems)
    5.1  Structure & mechanisms
    5.2  EPS (solar array + battery + board)
    5.3  AOCS (sensors + actuators)
    5.4  TTC (transponder + antenna)
    5.5  OBC & data handling
    5.6  Thermal control
    5.7  Propulsion (if applicable)
    5.8  Harness & cabling
  6.0  Integration & Test                 12%    (assembly, env. testing)
    6.1  Assembly & integration
    6.2  Environmental test campaign
    6.3  Test facilities rental
  7.0  Software (Flight + Ground)          8%    (FSW, GSW, mission planning)
    7.1  Flight software
    7.2  Ground segment software
    7.3  Mission planning tools
  8.0  Launch Services                    10%    (vehicle, deployer, integration)
  9.0  Ground Segment                      5%    (antennas, MCS, networks)
  10.0 Operations (mission lifetime)       5%    (staff, consumables, maintenance)
```

<!--
SVG Description: Cost Breakdown Structure (WBS) Tree Diagram

A hierarchical tree with "Mission Total" at the top, branching to 10 WBS Level 1 
elements (1.0 PM through 10.0 Operations). WBS 5.0 (Bus Hardware) further branches 
into 5.1-5.8 subsystems. Each box shows the WBS number, name, and percentage of total.
Colour coding: Blue for management (1-3), Green for space segment (4-6), 
Orange for software (7), Red for launch (8), Grey for ground/ops (9-10).
-->

### Cost by Phase

The distribution of cost across lifecycle phases is important for budgeting:

| Phase | % of Total | Activities | Peak Staffing |
|-------|-----------|-----------|---------------|
| 0/A (Concept) | 5-10% | Studies, trade-offs, requirements | Low |
| B (Preliminary Design) | 15-20% | PDR, detailed analysis, long-lead procurement | Growing |
| C (Detailed Design) | 30-40% | CDR, manufacturing, software development | Peak |
| D (Integration & Test) | 20-25% | Assembly, environmental testing, commissioning | High |
| E (Operations) | 10-20% | Routine operations, anomaly management | Low-steady |
| F (Disposal) | 1-3% | Decommissioning, deorbit | Minimal |

---

## 3. Learning Curve for Constellations (15 min)

### Teaching Notes

*[Source: SMAD4 section 20.3; Wright's Learning Curve Theory (1936)]*

When building multiple identical units, the cost per unit decreases due to manufacturing efficiency, reduced test time, bulk purchasing, and labour learning.

### Wright's Learning Curve

> **Nth Unit Cost:**
>
> C_N = C_1 x N^b
>
> Where b = ln(learning_rate) / ln(2)
>
> | Learning Rate | b | Cost of 10th Unit (% of 1st) |
> |--------------|-----|-----|
> | 95% | -0.074 | 77% |
> | 90% | -0.152 | 60% |
> | 85% | -0.234 | 47% |

> **Total Cost for N Units (cumulative):**
>
> C_total = C_1 x Sum from i=1 to N of (i^b)
>
> Or approximately: C_total ~ C_1 x N^(1+b) / (1+b)  (continuous approximation)

### Simplified Rule of Thumb

> At a **90% learning rate**, every time you **double** the number of units, the unit cost drops by **10%**.
>
> Unit 1: EUR 800K
> Unit 2: EUR 720K (800 x 0.90)
> Unit 4: EUR 648K (720 x 0.90)
> Unit 8: EUR 583K (648 x 0.90)
> Unit 16: EUR 525K (583 x 0.90)

### Worked Example: 20-Satellite Constellation

*First unit cost (bus + payload + I&T): EUR 800K. Learning rate: 90%.*

| Units | b | Avg Unit Cost | Total Hardware | Calc |
|-------|---|--------------|----------------|------|
| 1 | -0.152 | EUR 800K | EUR 800K | First unit |
| 5 | -0.152 | EUR 659K | EUR 3,295K | 5 x 800 x 5^(-0.152) |
| 10 | -0.152 | EUR 577K | EUR 5,770K | Cumulative sum |
| 20 | -0.152 | EUR 505K | EUR 10,100K | Cumulative sum |

Total constellation estimate:
- 20 satellites hardware: EUR 10.1M
- 2 spare units (10%): EUR 1.0M
- Launch (20 sats x EUR 200K rideshare): EUR 4.0M
- Ground segment: EUR 1.0M
- Operations (3 years): EUR 0.9M
- PM/SE/MA (10%): EUR 1.7M
- **Total: ~EUR 18.7M**

---

## 4. Cost Risk and Confidence Levels (10 min)

### Teaching Notes

Point estimates are misleading. Every cost estimate has uncertainty. The standard practice is to express cost as a probability distribution.

*[Source: NASA CEH v4.0 section 2.3; JPL parametric estimation practice]*

### Uncertainty by Cost Element

| Cost Element | Distribution | Uncertainty (1-sigma) | Rationale |
|-------------|-------------|----------------------|-----------|
| COTS hardware | Normal | +/- 10% | Known pricing from vendor quotes |
| Custom hardware | Lognormal | +/- 30% | Development uncertainty skews high |
| Software | Triangular | +/- 40% | Hardest to estimate; frequent overruns |
| Launch | Normal | +/- 15% | Published pricing; contract negotiation |
| Operations | Uniform | +/- 25% | Staffing level uncertainty |
| I&T | Lognormal | +/- 25% | Test anomalies cause schedule/cost growth |

### Confidence Levels

| Percentile | Meaning | Use |
|-----------|---------|-----|
| **P50** | 50% probability of being at or below this cost | Project baseline; "expected" cost |
| **P70** | 70% probability | NASA standard commitment level (NPR 7120.5F) |
| **P80** | 80% probability | Conservative planning; typical for proposals |

> **Rule of Thumb for CubeSat Missions:**
>
> P70 ~ P50 x 1.2
> P80 ~ P50 x 1.3
>
> Example: If P50 = EUR 500K, then P80 ~ EUR 650K.
>
> *This approximation assumes moderate complexity and well-understood COTS hardware. For missions with custom payloads or new technology, use P80 ~ P50 x 1.5.*

---

## 5. Design Review Process (25 min)

### Teaching Notes

Design reviews are formal decision gates where the project demonstrates readiness to proceed to the next lifecycle phase.

*[Source: NPR 7123.1D Appendix G; ECSS-M-ST-10C Rev.1 section 6; NASA SEH Rev 2 section 3.7]*
*[URL: https://www.nasa.gov/reference/systems-engineering-handbook/]*

### Review Sequence

| Review | Phase Transition | Key Question | Entry Criteria |
|--------|-----------------|-------------|----------------|
| **MCR** | Pre-A -> A | Is the mission need justified? | Problem statement, stakeholders, objectives defined |
| **SRR** | A -> B | Are requirements complete, consistent, traceable? | Requirements baselined, ConOps defined, feasibility shown |
| **PDR** | B -> C | Does preliminary design meet requirements with margin? | All budgets close, interfaces defined, risks identified |
| **CDR** | C -> D | Is detailed design complete and ready to build? | All drawings released, test plan approved, suppliers under contract |
| **TRR** | Pre-test | Is the system ready for environmental testing? | Assembly complete, procedures approved, facility booked |
| **QR** | Post-test | Has the system passed all tests? | All test reports approved, NCRs closed, V&V matrix complete |
| **FRR** | Pre-launch | Is everything ready for launch? | Shipping approved, launch manifest confirmed, operations ready |

### Gate Criteria for SRR (Phase A -> B)

| # | Criterion | Priority | Evidence |
|---|-----------|----------|----------|
| 1 | All Level 0/1 requirements baselined | Must pass | Requirements document signed |
| 2 | ConOps defined (all mission phases) | Must pass | ConOps document |
| 3 | Mission architecture trades completed | Must pass | Trade study reports with rationale |
| 4 | Feasibility confirmed (all budgets positive) | Must pass | Mass, power, link budgets with margin |
| 5 | Risk register established with mitigations | Must pass | Risk register with scores and plans |
| 6 | Preliminary V&V approach defined | Should pass | V&V matrix with methods assigned |
| 7 | Schedule and cost estimate (P50/P80) | Must pass | Cost estimate with WBS |
| 8 | Interface requirements identified | Should pass | N^2 matrix or ICD outline |

### Gate Criteria for PDR (Phase B -> C)

| # | Criterion | Priority | Evidence |
|---|-----------|----------|----------|
| 1 | All requirements allocated to subsystems | Must pass | Requirements allocation matrix |
| 2 | Preliminary design complete for all subsystems | Must pass | Design documents, block diagrams |
| 3 | All budgets close with >= 20% margin | Must pass | Mass, power, link, data, pointing budgets |
| 4 | Equipment selected (BOM) | Must pass | BOM with TRL, heritage, cost, lead time |
| 5 | All interfaces defined (N^2 matrix) | Must pass | Interface control documents |
| 6 | V&V matrix complete with methods assigned | Must pass | V&V matrix |
| 7 | Risk register updated; no Critical risks unmitigated | Must pass | Risk register |
| 8 | Test plan outline approved | Should pass | Environmental test plan |
| 9 | Software architecture defined | Should pass | Software design document |
| 10 | Cost estimate updated (bottom-up) | Must pass | Cost estimate with vendor quotes |

### Presentation Skills for Reviews

**Do:**
- Lead with the conclusion ("Mass budget closes with 22% margin")
- Show evidence, not just assertions ("Link budget analysis shows 4.2 dB margin at worst case")
- Acknowledge risks honestly ("Antenna deployment is our highest risk at L3 x C4 = 12")
- Answer questions directly; say "I don't know, we'll take an action" if needed

**Do not:**
- Read slides aloud
- Hide problems (review boards always find them)
- Present analysis without assumptions stated
- Skip backup slides -- have detailed data ready

---

## 6. Cost & Review Exercise (25 min)

### Instructions

**Part A: Cost Estimation (15 min)**

1. **Dashboard** -- Check the Cost KPI card (total cost in MEUR)
2. **Cost Breakdown** tab -- Review the breakdown by subsystem
3. **Exports** tab -- Generate BOM and sum COTS component costs
4. On Worksheet 4.4:
   - Fill in the WBS cost table using both parametric and bottom-up methods
   - Compute P50 and P80 estimates
   - If constellation: apply 90% learning curve

**Part B: Design Review Preparation (10 min)**

1. Open the **Gate Review** tab in SpaceCDF
2. Check all criteria: which are Pass/Fail/Manual?
3. For any failing criteria, click **"Go fix"** and resolve
4. Prepare a 3-minute summary of your design for peer review

### Worksheet 4.4 Tasks

1. Build a complete WBS cost table (parametric and bottom-up columns)
2. Compute P50 and P80 total cost estimates
3. If constellation: compute total cost with learning curve applied
4. Identify top 3 cost drivers and propose 20% cost reduction
5. List the gate criteria for SRR/PDR and assess your readiness

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | NASA Cost Estimating Handbook v4.0 | https://www.nasa.gov/offices/ocfo/references-and-tools/ |
| 2 | SMAD4 Chapter 20 (Cost) | Wertz, Everett, Puschell (eds.), Space Mission Engineering, Microcosm 2011 |
| 3 | Aerospace Corp SSCM | https://www.aerospace.org/capabilities/small-satellite-cost-model |
| 4 | NPR 7120.5F (WBS) | https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7120&s=5F |
| 5 | ECSS-M-ST-60C (Cost Management) | https://ecss.nl/standard/ecss-m-st-60c-cost-and-schedule-management/ |
| 6 | NPR 7123.1D (SE Processes) Appendix G | https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7123&s=1D |
| 7 | NASA SEH Rev 2, section 3.7 | https://www.nasa.gov/reference/systems-engineering-handbook/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Cost methods | Parametric (early, CERs), Analogy (reference mission), Bottom-up (vendor quotes) |
| CubeSat costs | COTS pricing often lower than CER predictions; use hybrid approach |
| WBS | Standard 10-element structure: PM, SE, MA, Payload, Bus, I&T, SW, Launch, Ground, Ops |
| CERs | Cost = a x M^b; USCM/SSCM databases; CubeSats need calibrated CERs |
| Learning curve | 90% rate: each doubling of quantity reduces unit cost by 10% |
| Cost risk | P50 (baseline), P70 (NASA commitment), P80 (conservative); P80 ~ P50 x 1.3 |
| Reviews | SRR, PDR, CDR: formal gates with exit criteria; must pass before proceeding |
| Presentation | Lead with conclusions, show evidence, acknowledge risks, answer directly |

---

# Session 5.1: Ground Segment & Operations Architecture

**Duration:** 2 hours
**Prerequisites:** Week 2 complete (full design cycle through cost estimation)
**References:** ECSS-E-ST-70C (Ground Systems), ECSS-E-ST-70-01C (Ground Segment), CCSDS 131.0-B-4 (TM Coding), CCSDS 231.0-B-4 (TC Coding), CCSDS 133.0-B-2 (Space Packet Protocol), NASA DSN Handbook (810-005)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Describe the components of a ground segment architecture (antennas, MCS, FDS, networks)
2. Calculate ground station contact time and data volume per pass
3. Explain the CCSDS protocol stack for space communication
4. Design a ground station network for a given orbit and data downlink requirement
5. Construct a mission operations timeline with key milestones

---

## 1. Ground Segment Architecture (25 min)

### Teaching Notes

The ground segment is everything on the ground that supports the space mission. It is frequently underestimated in early mission design but accounts for 5-15% of total mission cost and is critical to mission success.

*[Source: ECSS-E-ST-70C (Ground Systems and Operations); ECSS-E-ST-70-01C (Ground Segment)]*
*[URL: https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/]*

### Ground Segment Components

```
+------------------------------------------------------------------+
|                        GROUND SEGMENT                            |
|                                                                  |
|  +------------------+    +------------------+    +-----------+   |
|  | Ground Station   |    | Mission Control  |    | Flight    |   |
|  | Network          |    | System (MCS)     |    | Dynamics  |   |
|  |                  |    |                  |    | System    |   |
|  | - Antenna(s)     |    | - TM processing |    | (FDS)     |   |
|  | - RF front-end   |    | - TC generation  |    |           |   |
|  | - Modem/baseband |    | - Scheduling     |    | - Orbit   |   |
|  | - Tracking       |    | - Monitoring     |    |   determ. |   |
|  | - Data capture   |    | - Anomaly mgmt  |    | - Maneuver|   |
|  +--------+---------+    +--------+---------+    |   planning|   |
|           |                       |               +-+---+-----+   |
|           |    Data Network       |                 |   |         |
|           +----------+------------+-----------------+   |         |
|                      |                                  |         |
|  +------------------+v--+    +--------------------+     |         |
|  | Mission Planning     |    | Data Processing &  |     |         |
|  | System               |    | Archiving          |     |         |
|  | - Pass scheduling    |    | - Level 0-2 data   |     |         |
|  | - Resource planning  |    | - Archive/catalog  |     |         |
|  | - Conflict resoln.   |    | - Distribution     |     |         |
|  +----------------------+    +--------------------+     |         |
+------------------------------------------------------------------+
```

### Ground Station Components

| Component | Function | Typical Specification |
|-----------|----------|---------------------|
| **Antenna** | Transmit uplink commands, receive downlink telemetry | 3-13 m dish (S/X-band); Yagi/turnstile (UHF) |
| **RF front-end** | Low-noise amplifier (LNA), power amplifier, filters | LNA NF < 1 dB; PA 50-500 W |
| **Modem/baseband** | Modulation/demodulation, coding/decoding | CCSDS-compliant; BPSK/QPSK/8PSK |
| **Tracking system** | Antenna pointing, Doppler tracking, ranging | Autotrack or program-track |
| **Data capture** | Record raw baseband data for post-processing | High-speed disk array |
| **Timing** | GPS-disciplined oscillator for time synchronisation | < 1 microsecond accuracy |

### Mission Control System (MCS)

| Function | Description | Tools |
|----------|------------|-------|
| **Telemetry processing** | Decode, decommutate, display, and archive TM packets | COSMOS, YAMCS, EGOS (ESA) |
| **Telecommand generation** | Create, validate, encode, and uplink TC packets | Same MCS tools |
| **Pass scheduling** | Schedule antenna time, plan contact windows | STK, GMAT, custom schedulers |
| **Monitoring & control** | Real-time health monitoring, limit checking, alarming | MCS dashboards |
| **Anomaly management** | Detect, diagnose, and resolve anomalies | Procedures + expert judgment |

### Flight Dynamics System (FDS)

| Function | Description | Inputs |
|----------|------------|--------|
| **Orbit determination** | Compute current orbit from tracking data | Range, Doppler, GPS (if onboard) |
| **Orbit prediction** | Propagate orbit forward for pass planning | Current state vector, perturbation models |
| **Manoeuvre planning** | Compute delta-V for orbit maintenance | Target orbit, propulsion model |
| **Conjunction assessment** | Predict close approaches with debris/other objects | TLE catalogue, own orbit |
| **End-of-life planning** | Compute deorbit manoeuvre or passivation plan | Remaining propellant, target orbit |

---

## 2. Ground Station Contact Analysis (25 min)

### Teaching Notes

Understanding how much data can be transferred per pass is fundamental to mission design. The data budget depends on the contact geometry, data rate, and pass duration.

### Contact Geometry

For a circular LEO orbit, the visibility of a ground station is determined by the minimum elevation angle constraint.

> **Maximum Slant Range at Minimum Elevation:**
>
> rho = R_E x (sqrt((h/R_E + 1)^2 - cos^2(epsilon)) - sin(epsilon))
>
> Where:
> - R_E = Earth radius (6371 km)
> - h = orbital altitude
> - epsilon = minimum elevation angle (typically 5-10 degrees)
>
> For h = 500 km, epsilon = 5 degrees:
> rho = 6371 x (sqrt((500/6371 + 1)^2 - cos^2(5)) - sin(5))
> rho = 6371 x (sqrt(1.0785^2 - 0.9962^2) - 0.0872)
> rho = 6371 x (sqrt(1.1632 - 0.9924) - 0.0872)
> rho = 6371 x (sqrt(0.1708) - 0.0872)
> rho = 6371 x (0.4133 - 0.0872)
> rho = 6371 x 0.3261
> rho = 2077 km

> **Maximum Pass Duration (overhead pass):**
>
> T_max = 2 x R_E x arccos(R_E x cos(epsilon) / (R_E + h)) / V_ground_track
>
> Simplified approximation for LEO:
> T_max ~ (2 x rho_max) / V_orbital x (R_E / (R_E + h))
>
> For 500 km SSO:
> V_orbital = sqrt(mu / (R_E + h)) = sqrt(3.986e14 / 6.871e6) = 7613 m/s
> T_max ~ 2 x 2077e3 / 7613 x (6371/6871) ~ 505 s ~ 8.4 minutes
>
> *Typical average pass duration (not all passes are overhead): ~6 minutes*

> **Data Volume per Pass:**
>
> V_data = R_data x T_contact x eta_protocol
>
> Where:
> - R_data = downlink data rate (bps)
> - T_contact = contact duration (seconds)
> - eta_protocol = protocol efficiency (typically 0.85-0.95 for CCSDS)
>
> Example: R = 2 Mbps, T = 360 s (6 min average), eta = 0.9:
> V_data = 2e6 x 360 x 0.9 = 648 Mbit = 81 MB per pass

### Contact Frequency

| Orbit | GS Latitude | Passes per Day | Avg Duration | Daily Data Volume (2 Mbps) |
|-------|-------------|----------------|-------------|---------------------------|
| 500 km SSO | 52 N (e.g., Waterloo) | 3-5 | 6 min | 243-405 MB |
| 500 km SSO | 69 N (e.g., Kiruna) | 6-8 | 7 min | 544-726 MB |
| 500 km, 51.6 (ISS) | 52 N | 2-4 | 5 min | 130-260 MB |
| 500 km SSO | SatNOGS network (global) | 10-15 | 5 min | 648-972 MB |

*[Source: STK simulations; validated against SatNOGS observation logs]*

### Worked Example: Data Budget Closure

*Problem:* An Earth observation mission generates 500 MB/day of imagery. Is a single ground station at 52 N latitude sufficient with 2 Mbps S-band downlink?

*Calculation:*
- Passes per day: ~4 (500 km SSO from 52 N)
- Avg pass duration: 6 min = 360 s
- Data per pass: 2e6 bps x 360 s x 0.9 / 8 = 81 MB
- Daily capacity: 4 x 81 = 324 MB
- Required: 500 MB/day
- **Shortfall: 176 MB/day -- budget does not close!**

*Solutions:*
1. Add a second ground station at high latitude (e.g., Kiruna -> +6 passes -> +486 MB)
2. Increase data rate to X-band (10 Mbps -> 405 MB/pass -> easily sufficient)
3. Reduce data generation (lower duty cycle or reduce image resolution)
4. Add onboard data compression (2:1 lossless -> 250 MB/day required)
5. Use SatNOGS network for additional UHF passes (housekeeping only)

---

## 3. CCSDS Protocol Stack (20 min)

### Teaching Notes

The Consultative Committee for Space Data Systems (CCSDS) defines the standard protocols for space communication, analogous to TCP/IP for ground networks.

*[Source: CCSDS 131.0-B-4 (TM Synchronization and Channel Coding); CCSDS 231.0-B-4 (TC Synchronization and Channel Coding); CCSDS 133.0-B-2 (Space Packet Protocol)]*
*[URL: https://public.ccsds.org/Pubs/131x0b4.pdf (freely available)]*

### Protocol Layers

| Layer | CCSDS Standard | Function | Ground Analogy |
|-------|---------------|----------|----------------|
| **Application** | CCSDS 133.0 (Space Packet) | Mission data and housekeeping packets | HTTP/application data |
| **Network** | CCSDS 732.0 (AOS) or 132.0 (TM) | Virtual channels, multiplexing | IP routing |
| **Data Link** | CCSDS 131.0 (TM coding) / 231.0 (TC coding) | FEC, frame sync, CRC | Ethernet |
| **Physical** | CCSDS 401.0 (RF & Modulation) | Modulation, frequency, power | Physical layer |

### Telemetry (TM) Frame Structure

```
+--------+------------------+----+
| Header | Data Field       | EC |
| 6 bytes| 1-1019 bytes     | 2B |
+--------+------------------+----+
  |
  +-- Spacecraft ID (10 bits)
  +-- Virtual Channel ID (3 bits)
  +-- Frame Counter (8 bits)
  +-- Frame Length
```

### Forward Error Correction (FEC) Options

| Code | Rate | Coding Gain (dB) | Use Case |
|------|------|------------------|----------|
| Convolutional (7, 1/2) | 1/2 | 5.5 | Legacy CubeSats |
| Reed-Solomon (255, 223) | 0.87 | 3.5 | Combined with convolutional |
| Turbo (rate 1/2) | 1/2 | 7.5 | High-performance CubeSats |
| LDPC (rate 7/8) | 7/8 | 6.0 | High data rate, bandwidth efficient |

*Modern CubeSats typically use LDPC coding for downlink (high data rate) and convolutional + RS for uplink (robustness priority).*

---

## 4. Operations Timeline Construction (25 min)

### Teaching Notes

The operations timeline (or operations concept timeline) defines all major activities from launch to end of life. It is part of the ConOps and drives ground segment design.

### Mission Phases (Operations Perspective)

| Phase | Duration | Key Activities | Staffing |
|-------|----------|---------------|---------|
| **LEOP** | 0-72 hours | Separation, beacon acquisition, SA/antenna deploy, initial health check | 24/7 (3 shifts) |
| **Commissioning** | 1-4 weeks | Subsystem checkout, ADCS calibration, payload first light | 16/7 (2 shifts) |
| **Early Operations** | 1-3 months | Performance characterisation, procedure refinement | 8/5 (1 shift) |
| **Nominal Operations** | Mission lifetime | Routine science/service, orbit maintenance | 8/5 or automated |
| **Extended Operations** | If approved | Degraded mode operations, reduced data | Part-time |
| **End of Life** | 1-4 weeks | Passivation, deorbit manoeuvre, final telemetry | 8/5 |

### Operations Timeline (Gantt-Style)

```
Week:  1    2    3    4    5    6    7    8   ...  52
       |LEOP|
       |    |Commissioning         |
       |    |    |    |    |Early Operations    |
       |    |    |    |    |    |    |    |Nominal Operations ------>
       |    |    |    |    |    |    |    |    |    |    |    |    |
24/7:  XXXX
16/7:       XXXXXXXXXXXXXXX
8/5:                        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...
```

### LEOP Timeline Detail

| Time (after separation) | Activity | Success Criterion |
|------------------------|----------|-------------------|
| T+0 s | Separation from deployer | Deployment switches released |
| T+0 to T+30 min | Deployment timer countdown (no RF) | Timer runs; all inhibits clear |
| T+30 min | Antenna deployment | Beacon detected by ground station |
| T+30 to T+60 min | Beacon acquisition | Carrier lock; beacon decoded |
| T+1 hr | First telemetry downlink | Housekeeping data received and validated |
| T+1 to T+6 hr | Initial health assessment | All subsystems reporting nominal HK |
| T+6 to T+12 hr | Solar array deployment (if separate) | Power generation confirmed |
| T+12 to T+24 hr | ADCS initialisation | Attitude determination active |
| T+24 to T+48 hr | ADCS calibration (magnetometer, sun sensor) | Pointing within coarse spec |
| T+48 to T+72 hr | Communication chain validation (full duplex) | Uplink and downlink at operational rate |

### SpaceCDF Operations Planning

SpaceCDF's **ConOps Editor** allows you to:
- Define mission phases with start/end conditions
- Specify operational modes per phase (safe, nominal, science, downlink)
- Set ground contact requirements per phase (frequency, duration)
- The system validates that the ground segment design supports the operations concept

---

## 5. Ground Segment Design Exercise (25 min)

### Instructions

1. **Data Budget** tab -- Review the daily data generation vs downlink capacity
   - Is the data budget closing? If not, identify the bottleneck
   - How many ground station passes per day does your orbit provide?

2. **ConOps Editor** -- Define mission phases:
   - LEOP (duration, staffing, contact requirements)
   - Commissioning (activities, success criteria)
   - Nominal operations (duty cycle, data volume, contact frequency)

3. On Worksheet 5.1:
   - Calculate data volume per pass for your mission
   - Determine number of ground stations needed to close the data budget
   - Construct a LEOP timeline
   - Draft a simplified operations timeline (Gantt chart)

### Discussion Prompts

- "What happens if your first pass after deployment has no signal?"
- "How would you handle a safe mode entry at 3 AM on a Saturday?"
- "What is the minimum ground segment that could support your mission?"

### Worksheet 5.1 Tasks

1. Calculate ground station contact time and data volume per pass
2. Design a ground station network (locations, antenna sizes, data rates)
3. Construct a LEOP timeline (first 72 hours, hourly resolution)
4. Draft a mission operations timeline (Gantt chart, weekly resolution)
5. Estimate ground segment cost (antennas + MCS + FDS + operations staff)

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-E-ST-70C (Ground Systems and Operations) | https://ecss.nl/standard/ecss-e-st-70c-ground-systems-and-operations/ |
| 2 | CCSDS 131.0-B-4 (TM Synchronization and Channel Coding) | https://public.ccsds.org/Pubs/131x0b4.pdf |
| 3 | CCSDS 133.0-B-2 (Space Packet Protocol) | https://public.ccsds.org/Pubs/133x0b2.pdf |
| 4 | CCSDS 231.0-B-4 (TC Synchronization and Channel Coding) | https://public.ccsds.org/Pubs/231x0b4.pdf |
| 5 | SatNOGS Network | https://network.satnogs.org/ |
| 6 | NASA DSN Handbook (810-005) | https://deepspace.jpl.nasa.gov/dsndocs/810-005/ |
| 7 | YAMCS Mission Control Software | https://yamcs.org/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Ground segment | Antenna network + MCS + FDS + mission planning + data processing |
| Contact analysis | Pass duration ~6 min (LEO/SSO); data volume = rate x time x efficiency |
| Data budget | Must close: daily generation <= daily downlink capacity; add GS or increase rate |
| CCSDS | Standard protocol stack: Space Packet, AOS/TM frames, FEC coding, RF modulation |
| Operations timeline | LEOP (24/7) -> Commissioning (16/7) -> Nominal (8/5 or automated) |
| LEOP | First 72 hours critical: antenna deploy, beacon acquisition, health check |
| SpaceCDF | ConOps Editor defines phases; Data Budget validates ground segment sizing |

---

# Session 5.2: Mission Operations Concepts

**Duration:** 2 hours
**Prerequisites:** Session 5.1 (ground segment architecture understood)
**References:** ECSS-E-ST-70-11C (Space Segment Operability), ECSS-E-ST-70-32C (Procedures), ECSS-E-ST-70-41C (Packet Utilisation Standard), NPR 7120.5F, NASA Fault Management Handbook (NASA-HDBK-1002)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Define a Concept of Operations (ConOps) with operational modes and transitions
2. Design an FDIR (Fault Detection, Isolation, Recovery) architecture
3. Write operational procedures for routine and contingency operations
4. Describe anomaly response process with escalation levels
5. Plan spacecraft operational modes and their entry/exit criteria

---

## 1. Concept of Operations (ConOps) (25 min)

### Teaching Notes

The ConOps is the bridge between engineering design and operational reality. It describes HOW the system will be used, not just WHAT it can do.

*[Source: ECSS-E-ST-70-11C (Space Segment Operability); IEEE 1362 (Concept of Operations Document)]*

### ConOps Structure

A complete ConOps document covers:

1. **Mission overview** -- Objectives, stakeholders, success criteria
2. **System description** -- Space segment, ground segment, user segment
3. **Operational scenarios** -- Nominal operations, contingency operations
4. **Operational modes** -- Definition, transitions, constraints
5. **Resource management** -- Power, data, propellant budgets over time
6. **Communication plan** -- Contact schedule, data flow, latency requirements
7. **Staffing plan** -- Personnel, shifts, training requirements
8. **Maintenance and logistics** -- Software updates, ground equipment maintenance

### Operational Modes

Every spacecraft has a defined set of operational modes. Each mode specifies which subsystems are active, power consumption, and data rates.

| Mode | Description | Power (W) | Data Rate | Typical Duration | Entry Condition |
|------|------------|-----------|-----------|-----------------|----------------|
| **Safe** | Minimum functionality; survival only | 5-10 | Beacon only (1 bps) | Until ground intervenes | Autonomous fault detection |
| **Detumble** | Stop rotation after deployment | 8-12 | HK only (100 bps) | Minutes to hours | Post-separation; high angular rate |
| **Standby** | Sun-pointing; all subsystems ready | 12-18 | HK telemetry (1 kbps) | Between activities | After detumble; idle periods |
| **Science** | Payload operating; attitude controlled | 25-40 | Science data (variable) | Target-dependent | Scheduled; attitude achieved |
| **Downlink** | High-rate data transfer to ground | 20-30 | Full rate (2-10 Mbps) | During GS contact | GS in view; link established |
| **Manoeuvre** | Orbit adjustment or desaturation | 15-25 | HK only | Minutes | Scheduled; constraints met |
| **Eclipse** | Reduced operations during eclipse | 8-15 | HK only (100 bps) | ~35 min (LEO) | Sun not in view |

### Mode Transition State Machine

```
                    +----------+
      Separation    |          |    Fault
   +--------------->| DETUMBLE |<-----------+
   |                |          |            |
   |                +----+-----+            |
   |                     | Angular rate     |
   |                     | < threshold      |
   |                +----v-----+            |
   |                |          |    Fault   |
   |     +--------->| STANDBY  |----------->+--------+
   |     |          |          |<-----+     |        |
   |     |          +--+----+--+      |     |  +-----v----+
   |     |             |    |         |     |  |          |
   |     |    Schedule |    | GS      |     +--+  SAFE    |
   |     |             |    | contact |        |  MODE    |
   |     |       +-----v-+  +---v----++        |          |
   |     |       |       |  |        |         +-----+----+
   |     +-------+SCIENCE|  |DOWNLINK|               |
   |    Complete |       |  |        |      Ground    |
   |             +-------+  +--------+      command   |
   |                                        recovery  |
   +--------------------------------------------------+
```

### Real Mission Example: PROBA-2 Operations

ESA's PROBA-2 (launched 2009, still operational in 2026) demonstrates mature CubeSat-class operations:
- **5 operational modes:** Standby, Science, Manoeuvre, Safe, Off
- **Autonomous operations:** 95% of routine activities automated via onboard timeline
- **Ground contacts:** 4-6 passes/day via ESA Redu station (S-band)
- **Anomaly rate:** ~2-3 per year requiring ground intervention (after initial commissioning)
- **Key lesson:** Investing in onboard autonomy dramatically reduces operations cost

*[Source: ESA PROBA-2 Operations Team, "PROBA-2: Over a Decade of Operations", SpaceOps 2020]*

---

## 2. FDIR Architecture (30 min)

### Teaching Notes

FDIR (Fault Detection, Isolation, Recovery) is the spacecraft's autonomous ability to detect failures, determine which component failed, and take corrective action -- all without ground intervention.

*[Source: NASA Fault Management Handbook (NASA-HDBK-1002); ECSS-E-ST-70-11C section 5.3]*
*[URL: https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002]*

### Why FDIR is Critical for CubeSats

- **Limited ground contact:** LEO CubeSats are out of view ~85% of the time
- **No crewed intervention:** Unlike ISS, there is no astronaut to "fix" problems
- **Thermal constraints:** A safe mode must maintain thermal limits within minutes
- **Power constraints:** Battery can discharge completely in one eclipse without load shedding

### FDIR Hierarchy (Levels)

| Level | Detection | Response | Latency | Example |
|-------|-----------|----------|---------|---------|
| **0 -- Hardware** | Built-in watchdog | Component reset | Milliseconds | Processor watchdog timer |
| **1 -- Unit** | Unit-level monitoring | Unit reconfiguration | Seconds | EPS over-current trip |
| **2 -- Subsystem** | Subsystem health check | Subsystem fallback mode | Seconds-minutes | Switch to backup star tracker |
| **3 -- System** | System-level anomaly detection | Mode change (e.g., enter Safe) | Minutes | Transition to Safe Mode |
| **4 -- Ground** | Human-in-the-loop diagnosis | Ground command recovery | Hours-days | Anomaly investigation + patch |

### FDIR State Machine

```
                    NOMINAL OPERATIONS
                           |
              Fault detected (Level 2-3)
                           |
                    +------v------+
                    |  FAULT      |
                    |  DETECTED   |
                    +------+------+
                           |
              +------------+------------+
              |                         |
        Fault isolated            Cannot isolate
              |                         |
        +-----v-----+           +-------v------+
        | ISOLATION  |           | SAFE MODE    |
        | SUCCESS    |           | (Level 3)    |
        +-----+------+           +-------+------+
              |                          |
        Recovery action            Wait for ground
              |                    (Level 4)
        +-----v-----+                   |
        | RECOVERY   |           +------v-------+
        | ATTEMPT    |           | GROUND       |
        +-----+------+           | RECOVERY     |
              |                  +------+-------+
         Success / Fail                 |
              |                    Command sequence
        +-----v-----+                   |
        | RETURN TO  |<----------------+
        | NOMINAL    |
        +------------+
```

### Common CubeSat FDIR Rules

| Fault | Detection Method | Threshold | Response |
|-------|-----------------|-----------|----------|
| Processor lockup | Watchdog timer | No heartbeat for 60 s | Hardware reset (Level 0) |
| Battery under-voltage | EPS voltage monitor | V_bat < 6.0V | Load shedding; enter Safe Mode |
| Battery over-temperature | Temperature sensor | T_bat > 45 C | Disable charging; reduce loads |
| Attitude loss | No attitude solution for 5 min | ADCS health flag timeout | Enter Detumble Mode |
| Communication loss | No uplink for 48 hr | Timer-based | Reset TTC; revert to beacon mode |
| Memory corruption | EDAC error count | > 10 uncorrectable errors/hr | Memory scrub; reboot from backup |
| Solar array current anomaly | Current sensor | I_SA < expected - 30% | Check attitude; enter Standby |
| Reaction wheel over-speed | Wheel speed monitor | Omega > 6000 RPM | Reduce momentum; desaturation |

### Key Design Principles

1. **Safe Mode must always work** -- It is the last resort; it must be tested exhaustively
2. **Fail operational, then fail safe** -- Try to continue the mission before giving up
3. **No single fault should cause mission loss** -- Cross-reference with FMECA
4. **Ground override capability** -- Every autonomous action must be commandable from ground
5. **Logging** -- Record all fault events in non-volatile memory for post-analysis

---

## 3. Operational Procedures (20 min)

### Teaching Notes

*[Source: ECSS-E-ST-70-32C (Procedure Definition Language); ECSS-E-ST-70-01C section 5.6]*

### Procedure Types

| Type | Purpose | Execution | Example |
|------|---------|-----------|---------|
| **Nominal** | Routine scheduled operations | Automated (timeline) or manual | Science observation sequence |
| **Contingency** | Response to known anomaly types | Semi-automated; operator decision | Safe mode recovery |
| **Emergency** | Response to critical unexpected events | Manual; real-time decision | Communication loss recovery |
| **Maintenance** | Periodic calibration or updates | Scheduled manual | Magnetometer calibration |

### Procedure Structure (ECSS-E-ST-70-32C)

Each procedure has:
1. **Identifier** -- Unique procedure number (e.g., NOM-001)
2. **Purpose** -- What the procedure accomplishes
3. **Preconditions** -- System state required before starting
4. **Steps** -- Ordered list of actions, verifications, decisions
5. **Expected results** -- What should happen at each step
6. **Recovery actions** -- What to do if expected results are not observed
7. **Post-conditions** -- System state after successful completion

### Example: Science Observation Procedure

```
Procedure: NOM-SCI-001 "Earth Observation Target Acquisition"
Preconditions: Mode = Standby, Battery SoC > 60%, Target in FOV within 10 min

Step 1: Verify ADCS mode = Fine Pointing
  Expected: ADCS status = FINE, pointing error < 0.1 deg
  If not: Wait 60 s, retry. If still not achieved -> ABORT, remain in Standby

Step 2: Command payload power ON
  Expected: Payload HK reports power = ON within 5 s
  If not: Retry power command. If 3 fails -> ABORT, log anomaly

Step 3: Wait for payload thermal stabilisation (90 s)
  Expected: Payload temperature within operational range

Step 4: Command payload to imaging mode
  Expected: Payload status = IMAGING, frame counter incrementing

Step 5: Wait for target acquisition (ground-predicted start time)
  Expected: Imaging starts at predicted time +/- 5 s

Step 6: Collect imagery for scheduled duration

Step 7: Command payload to standby
  Expected: Payload status = STANDBY

Step 8: Command payload power OFF (if no more targets this orbit)
  Expected: Payload HK reports power = OFF

Post-conditions: Mode = Standby, imagery stored in mass memory
```

---

## 4. Anomaly Response Process (20 min)

### Teaching Notes

*[Source: NASA-HDBK-1002 (Fault Management Handbook); ESA Anomaly Review Board procedures]*

### Anomaly Escalation Levels

| Level | Severity | Response Time | Authority | Example |
|-------|----------|--------------|-----------|---------|
| **Green** | Informational | Next business day | Operations engineer | Minor parameter out of expected range |
| **Yellow** | Warning | Within 4 hours | Lead operator | Subsystem performance degraded |
| **Orange** | Serious | Within 1 hour | Flight director | Mode change required; mission impact |
| **Red** | Critical | Immediate | Project manager + FD | Mission-threatening; safe mode entered |

### Anomaly Response Workflow

```
1. DETECT: Telemetry alarm or operator observation
2. ASSESS: Is this a known anomaly type? Check procedures library
   -> Known: Execute contingency procedure
   -> Unknown: Continue to step 3
3. DIAGNOSE: Gather additional telemetry, correlate events, form hypothesis
4. PLAN: Develop response plan (may require Anomaly Review Board)
5. EXECUTE: Implement recovery commands (verify each step)
6. VERIFY: Confirm system returned to expected state
7. DOCUMENT: Record anomaly, root cause, response, and lessons learned
```

### Anomaly Report Form Fields

| Field | Description |
|-------|------------|
| **Anomaly ID** | Unique identifier (e.g., ANO-2026-042) |
| **Date/Time (UTC)** | When the anomaly was detected |
| **Severity** | Green / Yellow / Orange / Red |
| **Affected subsystem** | EPS, AOCS, TTC, Payload, etc. |
| **Observation** | What was observed (TM values, trends) |
| **Diagnosis** | Root cause analysis |
| **Action taken** | Commands sent, procedures executed |
| **Result** | System state after response |
| **Status** | Open / Resolved / Under investigation |
| **Lessons learned** | Preventive measures for future |

### Real Mission Example: Kepler Reaction Wheel Failure

NASA's Kepler space telescope lost reaction wheel #2 in July 2012, followed by wheel #4 in May 2013. The anomaly response:

1. **Detection:** Elevated friction torque in wheel #2 HK telemetry
2. **Assessment:** Known degradation signature; monitoring intensified
3. **Failure:** Wheel #2 ceased operation. Mission continued on 3 wheels.
4. **Second failure:** Wheel #4 failed 10 months later. Only 2 wheels remaining -- insufficient for fine pointing.
5. **Recovery:** Engineering team developed the "K2" mission concept using solar radiation pressure as a "virtual third wheel"
6. **Result:** K2 operated for 4+ additional years, discovering 2,700+ exoplanet candidates

*Lesson: Creative operational workarounds can save missions. FDIR should be designed with graceful degradation, not just "safe mode or nothing."*

*[Source: Howell et al., "The K2 Mission: Characterization and Early Results", PASP, 2014]*

---

## 5. Operations Concepts Exercise (25 min)

### Instructions

1. **ConOps Editor** in SpaceCDF:
   - Define all operational modes for your mission (at least 5)
   - Set entry/exit conditions for each mode
   - Verify power budget closes in each mode (especially Safe and Eclipse)

2. **FDIR Design:**
   - Define 5 FDIR rules for your mission (fault, detection, threshold, response)
   - Verify that Safe Mode power budget is sustainable indefinitely
   - Check: Can every FDIR response be overridden from ground?

3. **Worksheet 5.2:**
   - Complete the operational modes table
   - Write one nominal procedure (science observation or downlink)
   - Write one contingency procedure (safe mode recovery)
   - Fill in the FDIR rules table

### Discussion Prompts

- "What is the worst anomaly that could happen to your satellite? How would you respond?"
- "If the satellite enters safe mode on Friday evening and the next ground contact is Monday, will it survive?"
- "How much autonomy should the spacecraft have? Where is the line between onboard and ground decision-making?"

### Worksheet 5.2 Tasks

1. Complete the operational modes table (5+ modes with power, data rate, entry/exit)
2. Design the FDIR state machine (at least 5 rules)
3. Write one nominal and one contingency procedure
4. Complete the anomaly response form for a hypothetical scenario
5. Estimate operations staffing requirements by mission phase

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-E-ST-70-11C (Space Segment Operability) | https://ecss.nl/standard/ecss-e-st-70-11c-space-segment-operability/ |
| 2 | ECSS-E-ST-70-32C (Procedures) | https://ecss.nl/standard/ecss-e-st-70-32c-test-and-operations-procedure-language/ |
| 3 | NASA Fault Management Handbook (NASA-HDBK-1002) | https://standards.nasa.gov/standard/NASA/NASA-HDBK-1002 |
| 4 | ESA PROBA-2 Operations, SpaceOps 2020 | https://www.spaceops.org/ |
| 5 | Howell et al., K2 Mission, PASP 2014 | https://doi.org/10.1086/676406 |
| 6 | ECSS-E-ST-70-41C (Packet Utilisation Standard) | https://ecss.nl/standard/ecss-e-st-70-41c-telemetry-and-telecommand-packet-utilization/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| ConOps | Defines HOW the system is operated: modes, transitions, schedules, staffing |
| Operational modes | Safe, Detumble, Standby, Science, Downlink, Manoeuvre, Eclipse (minimum set) |
| Mode transitions | Defined by entry/exit conditions; Safe Mode always reachable from any mode |
| FDIR | 5 levels: Hardware -> Unit -> Subsystem -> System -> Ground; Safe Mode is last resort |
| Procedures | Nominal (routine), Contingency (known faults), Emergency (unknown), Maintenance |
| Anomaly response | Detect -> Assess -> Diagnose -> Plan -> Execute -> Verify -> Document |
| Design principles | Safe Mode must always work; fail operational before fail safe; ground override always |

---

# Session 5.3: Mission Simulation Day

**Duration:** 2 hours
**Prerequisites:** Sessions 5.1-5.2 (ground segment designed, operations concepts defined)
**References:** ECSS-E-ST-70-11C (Operability), ECSS-E-ST-70-32C (Procedures), ESA OPS-G Training Manual, NASA Mission Operations Directorate Training Handbook

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Execute a simulated LEOP sequence from separation through first telemetry
2. Perform commissioning activities using operational procedures
3. Respond to injected anomalies using the FDIR architecture and contingency procedures
4. Document anomaly response in real-time using structured forms
5. Conduct nominal science operations with live data budget tracking

---

## 1. Simulation Overview & Roles (10 min)

### Teaching Notes

This session is a **hands-on simulation** of mission operations. The facilitator acts as the "Universe" -- injecting events, anomalies, and time jumps. The team operates the mission using SpaceCDF and their procedures from Session 5.2.

### Role Assignments

| Role | Responsibility | SpaceCDF Feature Used |
|------|---------------|---------------------|
| **Flight Director (FD)** | Overall decision authority; coordinates team | Dashboard, all tabs |
| **Spacecraft Controller (SC)** | Sends commands; monitors housekeeping telemetry | ConOps Editor, mode control |
| **Ground Station Operator (GSO)** | Manages antenna scheduling; link acquisition | Data Budget, Link Budget |
| **Payload Operator (PO)** | Plans and executes science observations | Payload parameters, data budget |
| **Flight Dynamics (FD-nav)** | Monitors orbit; plans manoeuvres (if propulsion) | Orbit parameters, sustainability |
| **Anomaly Logger** | Documents all events, anomalies, and decisions | Worksheet 5.3 |

*For smaller teams, combine roles: SC+GSO and PO+FD-nav are natural pairings.*

### Simulation Timeline

| Sim Time | Real Time | Phase | Events |
|----------|----------|-------|--------|
| T+0 to T+1 hr | 0-20 min | LEOP | Separation, beacon acquisition, deploy, health check |
| T+1 hr to T+24 hr | 20-35 min | Early LEOP | SA deploy, ADCS init, comms chain validation |
| T+1 day to T+7 days | 35-50 min | Commissioning | Subsystem checkout, first payload activation |
| T+7 days to T+30 days | 50-65 min | Early Operations | Nominal science, orbit maintenance |
| *Anomaly injection* | 65-85 min | Contingency | Anomaly response exercise |
| T+30 days to T+1 year | 85-100 min | Nominal Operations | Routine operations, data review |
| Debrief | 100-120 min | Wrap-up | Lessons learned, documentation review |

---

## 2. LEOP Simulation (20 min)

### Teaching Notes

The facilitator narrates the simulation. Time is compressed. Each team executes their LEOP procedure.

### Facilitator Script -- LEOP

**[T+0 -- Separation]**
*"Your satellite has separated from the deployer. Deployment switches have released. The 30-minute timer has started. You are in radio silence -- no RF emissions allowed until the timer expires. What is your spacecraft doing right now?"*

Expected answers: Timer counting down. Battery providing power. No subsystems active except OBC running timer.

**[T+30 min -- Timer Expires]**
*"The 30-minute timer has expired. Your OBC has commanded antenna deployment. What do you expect to see?"*

Expected: Antenna deployment command sent. Beacon should begin transmitting.

**[T+35 min -- First Pass Over Ground Station]**
*"Your ground station at [location] has line of sight. The antenna operator reports: carrier detected at [frequency] with Doppler of -25 kHz. Signal strength is -110 dBm. Is this what you expected?"*

Teams should verify:
- Carrier frequency matches expected (accounting for Doppler)
- Signal strength is consistent with link budget at current range
- Beacon data rate is as designed

**[T+40 min -- First Telemetry]**
*"Beacon lock achieved. You are receiving housekeeping telemetry. I am going to read you the first HK frame:"*

| Parameter | Value | Expected Range | Status |
|-----------|-------|---------------|--------|
| Bus voltage | 7.8 V | 7.0 - 8.4 V | Nominal |
| Battery SoC | 72% | > 50% | Nominal |
| Solar array current | 0.45 A | 0.3 - 0.6 A | Nominal |
| OBC temperature | 22 C | -10 to +50 C | Nominal |
| Battery temperature | 19 C | 0 to 45 C | Nominal |
| ADCS mode | Detumble | Expected | Nominal |
| Angular rate | 3.2 deg/s | Decreasing | Nominal |
| Antenna status | Deployed | Expected | Nominal |
| Beacon mode | Active | Expected | Nominal |
| Uplink status | Not yet attempted | -- | -- |

*"All parameters nominal. Proceed with LEOP sequence."*

**[T+1 hr -- Uplink Validation]**
*"You now attempt your first uplink command. Send a 'NOP' (no operation) command to verify the uplink chain."*

Teams should: compose command, verify encoding, transmit, wait for acknowledgement in telemetry.

---

## 3. Commissioning Simulation (15 min)

### Facilitator Script -- Commissioning

**[Time Jump: T+24 hr]**
*"Your satellite has completed detumbling. ADCS is in sun-pointing mode. All HK parameters are nominal after 8 ground passes. You are ready to begin commissioning. What is your first activity?"*

Expected: ADCS calibration (magnetometer bias estimation, sun sensor alignment verification).

**[T+3 days -- Payload First Light]**
*"ADCS is calibrated and achieving 0.3 degree pointing. You are ready for payload first light. Walk me through your procedure."*

Teams execute their science observation procedure from Worksheet 5.2.

**[T+5 days -- First Data Download]**
*"Payload has captured 150 MB of imagery. Your next pass is 12 minutes long over [station]. Can you download all the data in one pass?"*

Teams should calculate:
- Data rate x pass duration x protocol efficiency = available capacity
- Compare to 150 MB -- determine if multiple passes needed
- Plan the download sequence

---

## 4. Anomaly Injection Scenarios (30 min)

### Teaching Notes

The facilitator selects 2-3 anomalies from the list below, appropriate to the mission design. Teams respond using their FDIR rules and contingency procedures.

### Anomaly Menu (Facilitator selects 2-3)

#### Anomaly A: Battery Under-Voltage

*"During eclipse, you receive an alert: battery voltage has dropped to 6.2V, below your 6.5V warning threshold. Battery temperature is 5 C. SoC is estimated at 18%."*

Expected response:
1. Verify FDIR has triggered load shedding (payload off, non-essential heaters off)
2. Check power budget: is consumption > generation?
3. Possible causes: SA degradation, unexpected load, battery degradation, long eclipse
4. Immediate action: Verify safe mode; disable non-essential loads manually
5. Investigation: Review power trends over last 24 hours; compare to power budget

#### Anomaly B: Communication Loss

*"You have not received telemetry for the last 3 scheduled passes (18 hours). The ground station reports pointing and frequency are correct but no carrier detected."*

Expected response:
1. Verify ground station equipment (antenna, LNA, modem) -- rule out ground fault
2. Check with other ground stations (SatNOGS) for any signal detection
3. Consider causes: TX failure, antenna deployment failure, attitude loss (antenna not pointing)
4. If 48-hour timer exists: satellite may reset TTC and revert to beacon mode
5. Plan: Wait for timer-based reset; use wide-beam ground antenna for beacon search

#### Anomaly C: ADCS Anomaly -- Loss of Fine Pointing

*"Pointing error has increased from 0.1 deg to 5 deg. Star tracker reports 'no solution'. Reaction wheels are at 80% capacity (near saturation)."*

Expected response:
1. Diagnose: Star tracker failure? Optical contamination? Sun in FOV?
2. Check magnetometer attitude -- is coarse attitude correct?
3. Immediate: Command desaturation using magnetorquers
4. If star tracker failed: switch to coarse pointing mode (sun sensors + magnetometer)
5. Impact assessment: Can mission science continue in coarse pointing mode?

#### Anomaly D: Unexpected Safe Mode Entry

*"Your satellite has autonomously entered Safe Mode. Last telemetry before entry showed: OBC reboot counter incremented by 3 in 10 minutes. All other parameters were nominal."*

Expected response:
1. Investigate: Multiple reboots suggest SEU (Single Event Upset) or firmware bug
2. Check radiation environment: Was the satellite in SAA (South Atlantic Anomaly)?
3. Review FDIR logs (stored in non-volatile memory) for fault triggers
4. Recovery plan: Command exit from Safe Mode; monitor for recurrence
5. If recurring: Upload software patch to increase SEU robustness

#### Anomaly E: Thermal Exceedance

*"Payload temperature has reached 58 C during a science observation, exceeding the 55 C operational limit. Battery temperature is 38 C (approaching 45 C limit)."*

Expected response:
1. Immediate: Disable payload to stop heat generation
2. Check attitude: Is the hot radiator face pointing toward the sun?
3. Review thermal model: Was this orbit geometry (high beta angle) predicted?
4. Mitigation: Adjust duty cycle; plan observations for cooler orbit phases
5. If structural: May need to update thermal model and operational constraints

### Anomaly Documentation

For each injected anomaly, teams complete the **Anomaly Response Form** on Worksheet 5.3:

| Field | What to Record |
|-------|---------------|
| Time (sim) | When the anomaly was detected |
| Observation | Exact telemetry values and symptoms |
| Initial assessment | Severity level (Green/Yellow/Orange/Red) |
| Diagnosis | Suspected root cause |
| Action taken | Commands sent, procedures executed |
| Result | System state after response |
| Follow-up required | Additional investigation, procedure updates |

---

## 5. Nominal Operations & Debrief (25 min)

### Nominal Operations (10 min)

**[Time Jump: T+30 days to T+1 year]**
*"Your mission has been operational for one month. All commissioning activities are complete. You are now in nominal operations. Let's review your operational metrics."*

Teams report:
- Total data downlinked in 30 days vs plan
- Number of science observations completed vs plan
- Any anomalies encountered (from injection exercise)
- Current budget status: power margin, data margin, propellant remaining (if applicable)
- Orbit status: any conjunction alerts? Debris compliance on track?

### Debrief (15 min)

1. **What went well?**
   - Which procedures worked as written?
   - Which FDIR rules triggered correctly?
   - Where did the team communicate effectively?

2. **What could be improved?**
   - Which procedures needed real-time modification?
   - Were there gaps in the FDIR design?
   - Where did decision-making slow down?

3. **Lessons for the design:**
   - Did the simulation reveal any design weaknesses?
   - Should any requirements be changed based on operational experience?
   - What additional autonomy would help?

---

## Facilitator Notes

### Preparation

- Review each team's ConOps, FDIR rules, and procedures from Session 5.2
- Select anomalies appropriate to each team's mission (e.g., don't inject propulsion anomaly for a mission without propulsion)
- Prepare HK data tables for each phase (modify the values in Section 2 to match the team's mission parameters)
- Have backup anomalies ready if teams resolve injections quickly

### Pacing

- LEOP simulation should feel time-pressured (short passes, decisions needed quickly)
- Commissioning can be more relaxed
- Anomaly injection should be challenging but solvable with the team's procedures
- Allow extra time for debrief -- this is where the deepest learning occurs

### Assessment Criteria

Observe and note (for feedback, not formal grading):
- Did the team follow their procedures or improvise?
- Did the Flight Director coordinate effectively?
- Was the anomaly response systematic (detect-diagnose-plan-execute-verify)?
- Did the team document events in real-time?
- Did anyone identify a design flaw during operations?

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| LEOP | First 72 hours are critical; every step is time-constrained |
| Commissioning | Systematic subsystem checkout before payload operations |
| Anomaly response | Follow the process: detect, assess, diagnose, plan, execute, verify, document |
| Documentation | Real-time logging is essential -- memory is unreliable under stress |
| FDIR validation | Simulation reveals gaps in FDIR design that analysis alone cannot find |
| Team coordination | Clear roles, communication protocols, and decision authority are essential |
| Design feedback | Operational experience should feed back into design (requirements, FDIR, procedures) |

---

# Session 5.4: Final Review & Presentations

**Duration:** 2 hours
**Prerequisites:** All previous sessions (complete design through simulation)
**References:** ECSS-M-ST-10C Rev.1 section 6 (Reviews), NPR 7123.1D Appendix G, NASA SEH Rev 2 section 3.7, ECSS-E-ST-10C section 4 (Technical Dossier)

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Prepare a complete design documentation package for review
2. Conduct a design review presentation with evidence-based arguments
3. Evaluate a peer team's design against gate criteria
4. Provide constructive technical feedback using a structured rubric
5. Identify lessons learned and articulate next steps for Phase B

---

## 1. Design Documentation Review (20 min)

### Teaching Notes

Before presenting, each team must verify that their design documentation is complete and internally consistent.

### Documentation Checklist

| Document | Source in SpaceCDF | Status Check |
|----------|-------------------|-------------|
| Mission Requirements Document (MRD) | Exports -> ECSS Documents | All requirements baselined? |
| Technical Specification (TS) | Exports -> ECSS Documents | All budgets captured? |
| Concept of Operations (ConOps) | Exports -> ECSS Documents | All phases defined? |
| Verification Plan (VP) | V&V Matrix tab | All requirements have methods? |
| Bill of Materials (BOM) | Exports -> Design Data | All equipment listed with TRL? |
| Risk Register | Worksheet 4.3 | All risks scored and mitigated? |
| Interface Matrix (N^2) | Worksheet 4.3 | Interfaces identified? Conflicts resolved? |
| Cost Estimate | Worksheet 4.4 | WBS complete? P80 computed? |
| Operations Concept | ConOps Editor | Modes, FDIR, procedures defined? |
| Sustainability Assessment | Sustainability Card | Debris compliance score? |

### Internal Consistency Checks

Before presenting, verify:

| Check | How to Verify | Common Error |
|-------|-------------|-------------|
| Mass budget closes | Dashboard mass KPI: margin > 0% | Equipment added without updating budget |
| Power budget closes | Dashboard power KPI: SA > loads in all modes | Eclipse mode power not checked |
| Link budget closes | Link Budget tool: margin >= 3 dB | Rain attenuation not included |
| Data budget closes | Data Budget: daily downlink >= daily generation | Assumed too many passes per day |
| Cost is within ceiling | Cost tab: total <= allocated budget | Forgot launch cost or operations |
| Requirements traceable | Every requirement maps to an objective | Orphan requirements (no parent objective) |
| V&V complete | Every requirement has a method assigned | "TBD" entries remaining |
| No unresolved conflicts | Dashboard: conflict count = 0 | Interface mismatches not addressed |

### SpaceCDF Document Generation

Navigate to **Exports** tab and generate all documents:
1. ECSS Documents: MRD, TS, VP, ConOps, SEMP, IRD
2. Design Data: BOM, Parametric Model Data
3. Regulatory Filings: ITU API, RSSSA, Export Assessment, COPUOS, EOL Report
4. Presentation: Summary slide data (auto-populated)

---

## 2. Presentation Structure (15 min)

### Teaching Notes

Each team presents a 12-minute design review followed by 5 minutes of Q&A from the peer review board.

*[Source: ECSS-M-ST-10C Rev.1 section 6; NPR 7123.1D Appendix G (Review Process)]*

### Presentation Outline (12 minutes)

| Section | Duration | Content | Evidence |
|---------|----------|---------|----------|
| **1. Mission Need** | 2 min | Problem statement; stakeholders; objectives with MoPs | Mission Need step |
| **2. Why Space?** | 2 min | Trade study results; why space beats alternatives | Mission Trade results |
| **3. System Design** | 3 min | Architecture; orbit; key parameters; budget status | Dashboard, budgets |
| **4. Equipment & Verification** | 2 min | Key equipment; BOM summary; V&V approach; test plan | BOM, V&V Matrix |
| **5. Risk & Cost** | 2 min | Top 5 risks; cost estimate (P50/P80); schedule | Risk register, cost tab |
| **6. Operations & Lessons** | 1 min | ConOps summary; FDIR; what would you change | ConOps, simulation debrief |

### Presentation Best Practices

**Slide design:**
- One key message per slide
- Data, not prose (budgets, trade tables, not paragraphs)
- Include backup slides with detailed analyses for Q&A

**Delivery:**
- Lead with conclusions: "Our mass budget closes with 22% margin"
- Show evidence for every claim: "Link budget analysis shows 4.2 dB margin at worst case"
- Acknowledge risks honestly: "Antenna deployment is our highest risk at 12 (L3 x C4)"
- For questions you cannot answer: "Good question -- we will take that as an action item"

**Common pitfalls to avoid:**
- Reading slides verbatim
- Hiding known problems (review boards always find them)
- Presenting analysis without stating assumptions
- Spending too long on the mission description and rushing through technical results

---

## 3. Peer Review Process (10 min)

### Teaching Notes

Each team acts as a review board for another team. This mirrors the real design review process where an independent board evaluates the project.

### Review Board Roles

| Role | Responsibility | Key Questions to Ask |
|------|---------------|---------------------|
| **Chair** | Manages review; ensures all criteria covered | "Let's systematically check each gate criterion" |
| **Systems reviewer** | Evaluates overall architecture and budgets | "Do all budgets close? What is the minimum margin?" |
| **Technical reviewer** | Evaluates subsystem design decisions | "Why did you choose this component over alternatives?" |
| **Risk reviewer** | Evaluates risk management and V&V | "What is your highest risk? Is the mitigation adequate?" |
| **Operations reviewer** | Evaluates ConOps, ground segment, regulatory | "What happens if you lose contact for 48 hours?" |

### Gate Criteria Evaluation

The review board evaluates the presenting team against PDR-level gate criteria:

| # | Criterion | Score (0-2) | Notes |
|---|-----------|------------|-------|
| 1 | Mission need clearly justified | 0 = missing, 1 = partial, 2 = strong | Is the problem real? Is space the right answer? |
| 2 | Requirements complete and traceable | 0/1/2 | All requirements linked to objectives? Verifiable? |
| 3 | All budgets close with adequate margin | 0/1/2 | Mass, power, link, data, pointing -- all positive? |
| 4 | Equipment selected with justified trades | 0/1/2 | BOM complete? TRL adequate? Trade studies documented? |
| 5 | Interfaces defined and conflicts resolved | 0/1/2 | N^2 matrix? No unresolved conflicts? |
| 6 | V&V approach defined for all requirements | 0/1/2 | Methods assigned? Test plan outlined? |
| 7 | Risks identified with mitigations | 0/1/2 | Risk register with scores? Top risks mitigated? |
| 8 | Cost estimate with WBS and P80 | 0/1/2 | Both parametric and bottom-up? Learning curve applied? |
| 9 | ConOps and ground segment designed | 0/1/2 | Modes defined? FDIR architecture? Ground stations? |
| 10 | Sustainability compliance | 0/1/2 | Debris compliance? 25-year rule? Passivation plan? |

### Review Board Questions Bank

Standard questions for the review board to ask:

- "Why is space the right answer? What alternatives were considered?"
- "What is your mass margin? What drives it? What if the payload is 20% heavier than estimated?"
- "Walk me through your link budget at worst case. What is the minimum margin?"
- "What are your top 3 risks? What is the residual risk after mitigation?"
- "Show me your data budget. Does it close with a single ground station?"
- "What happens during a safe mode entry in eclipse? Does the thermal budget survive?"
- "Which component has the lowest TRL? What is your qualification plan?"
- "Have you started spectrum licensing? What is on the critical path?"
- "What is your single-point failure list? Which ones have you accepted?"
- "If you had 6 more months and 20% more budget, what would you change?"

---

## 4. Team Presentations (45 min)

### Instructions

**Presentation Schedule:** 12 minutes presentation + 5 minutes Q&A per team.

For 4 teams: allocate 17 min x 4 = 68 min. Adjust timing based on actual number of teams. If fewer than 4 teams, allow 15 min presentation + 8 min Q&A.

**For the presenting team:**
1. Present the 6-section outline above
2. Use SpaceCDF live for demonstrations where helpful (show Dashboard, budgets)
3. Respond to board questions with evidence

**For the review board:**
1. Complete the gate criteria evaluation form on Worksheet 5.4
2. Ask at least 3 substantive questions
3. Provide a GO / NO GO / GO WITH ACTIONS recommendation
4. Document action items with responsible person and deadline

**After each presentation:**
- Chair announces the board's recommendation
- Action items are recorded
- Brief applause and transition to next team

---

## 5. Course Wrap-Up & Lessons Learned (30 min)

### Teaching Notes

### Individual Reflection (5 min)

Each participant completes the self-assessment rubric on Worksheet 5.4, reflecting on their learning across all three weeks.

### Team Lessons Learned (10 min)

Each team discusses and reports:

1. **Most challenging design decision:** What trade-off was hardest to resolve? Why?
2. **Biggest surprise:** What aspect of mission design was most different from expectations?
3. **Tool feedback:** What SpaceCDF feature was most valuable? What was missing?
4. **Process insight:** How did concurrent design change your approach to engineering?
5. **If starting over:** What would you do differently in Week 1?

### Key Takeaways from the Course (10 min)

| Week | Theme | Core Lesson |
|------|-------|------------|
| **Week 1** | Requirements & Architecture | Start with the problem, not the solution. Requirements define WHAT, not HOW. |
| **Week 2** | Subsystem Design & Budgets | Engineering budgets are the language of systems engineering. Everything trades against everything. |
| **Week 3** | Integration, Verification & Operations | Building the right thing (V&V) is as important as designing it. Operations reveal what analysis cannot. |

### The Systems Engineering V-Model -- Completed

```
You started here:                          You finished here:
                                           
  Mission Need                               Mission Validated
     |                                              ^
     v                                              |
  Requirements                              Requirements Verified
     |                                              ^
     v                                              |
  System Design                             System Integrated (sim)
     |                                              ^
     v                                              |
  Subsystem Design                          Subsystem V&V Planned
     |                                              ^
     v                                              |
  Equipment Selected  ------>  Equipment Verified (BOM + compliance)
  
  Week 1-2 (left side)         Week 3 (right side)
```

*You have traversed the complete V-model: from mission need to verified, validated design.*

### Next Steps for Participants

- **SpaceCDF access** continues after the course
- **Apply the methodology** to your own missions or projects
- **Use the tool** for CDF-style studies with your team
- **Refer to the Facilitator's Book** for session plans and appendices
- **Share feedback** to improve the course for future cohorts

### Course Evaluation

Distribute the course evaluation form. Key questions:
- Which session was most valuable? Least valuable?
- What content should be added? Removed?
- How effective was the simulation day?
- Would you recommend this course to colleagues?
- What is one thing you will do differently in your engineering practice as a result?

---

## Cited References

| # | Reference | URL |
|---|-----------|-----|
| 1 | ECSS-M-ST-10C Rev.1 (Project Planning and Implementation) | https://ecss.nl/standard/ecss-m-st-10c-rev-1-project-planning-and-implementation/ |
| 2 | NPR 7123.1D Appendix G (Review Process) | https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7123&s=1D |
| 3 | NASA SEH Rev 2, section 3.7 (Technical Reviews) | https://www.nasa.gov/reference/systems-engineering-handbook/ |
| 4 | ECSS-E-ST-10C (System Engineering) | https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements/ |

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Documentation | Complete package: MRD, TS, ConOps, VP, BOM, Risk Register, Cost, Regulatory |
| Consistency | All budgets must close; no unresolved conflicts; requirements fully traceable |
| Presentation | 6 sections: need, justification, design, V&V, risk+cost, operations+lessons |
| Peer review | Independent board evaluates against gate criteria; GO/NO GO/GO with actions |
| Best practices | Lead with conclusions, show evidence, acknowledge risks, answer directly |
| V-model | Course traverses full V: needs -> requirements -> design -> V&V -> validation |
| Lessons learned | Document what worked, what failed, and what to change -- this is the real output |

---

# Appendix: Position-Specific Deep Dives

This appendix provides detailed guidance for each CDF engineering position,
including responsibilities, key parameters owned, decision authority,
common pitfalls, and references.

---

## Appendix A: Systems Engineer

**Responsibility:** Overall system architecture, budget management, cross-domain conflict resolution.

**Key Parameters Owned:** Mass margin, power margin, system-level cost, composite TRL, health score.

**Key Activities:**
- Maintain all engineering budgets (mass, power, cost, ?V, data, pointing)
- Apply ECSS margin policy by project phase (44% Phase A -> 13% Phase C/D)
- Resolve cross-domain conflicts (convene affected positions, facilitate trade)
- Prepare gate review evidence packages
- Own the requirements baseline and traceability matrix
- Conduct design reviews and track action items

**Decision Authority:** System-level trade-offs, margin allocation, requirement waivers.

**Common Pitfalls:**
- Allowing individual subsystems to consume their margin allocation (no system reserve)
- Not challenging HOW requirements that should be WHAT
- Accepting conflicts without resolution timelines
- Not tracking parametric estimate vs selected equipment delta

**References:** NASA SEH §2, §6; ECSS-E-ST-10C Rev.1 §5; SMAD4 Ch.3

---

## Appendix B: Mission Analyst

**Responsibility:** Orbit design, coverage analysis, ground station access, constellation architecture.

**Key Parameters Owned:** Altitude, inclination, orbit type, eclipse fraction, revisit time, contact time, LTAN.

**Key Activities:**
- Run orbit trade studies (altitude/inclination/lifetime/coverage/cost)
- Compute coverage and revisit for target latitude bands
- Analyse ground station access (elevation angle, contact duration, pass scheduling)
- Assess debris compliance (lifetime vs 25yr/5yr rules)
- For constellations: Walker delta design, phasing, coverage optimisation

**Key Formulae:**
- Period: T = 2pi?(a^3/mu)
- Eclipse fraction: f = (1/pi)arccos(?(1-(R_E/a)^2))
- SSO inclination: cos(i) = f(a, J2)
- Hohmann ?V: from vis-viva equation
- Coverage radius: from ground station elevation geometry

**References:** SMAD4 Ch.5-7; Vallado §2-9; ECSS-U-AS-10C Rev.2

---

## Appendix C: Payload Lead

**Responsibility:** Instrument performance, data generation, payload accommodation.

**Key Parameters Owned:** GSD (or equivalent MoP), data rate, pointing requirement, payload mass, power, duty cycle, FOV.

**Key Activities:**
- Size the payload from performance requirements (GSD -> aperture for optical; data rate -> antenna for comms; resolution -> antenna area for SAR)
- Define payload data volume and duty cycle
- Specify thermal environment needs (detector cooling, operational temperature)
- Coordinate with AOCS for pointing and stability requirements
- Coordinate with comms for downlink capacity matching data generation

**Key Formulae:**
- Optical: GSD = max(1.22lambdah/D, ph/f)
- Payload mass: M ~ 20D^1.5 + 2 (heritage CER)
- Data rate: R = N_pixels × N_bands × bit_depth × line_rate
- SAR: antenna_length >= 2 × resolution

**References:** SMAD4 Ch.9; ECSS-E-ST-10-06C; specific instrument handbooks

---

## Appendix D: Power Engineer

**Responsibility:** Solar array, battery, EPS architecture, power distribution, duty cycling.

**Key Parameters Owned:** SA area, SA power (BOL/EOL), battery capacity, bus voltage, power margin per mode.

**Key Activities:**
- Construct power budget per operational mode (safe/idle/imaging/downlink/eclipse)
- Size solar array from peak sunlight demand + battery recharge
- Size battery from eclipse energy / maximum DoD
- Define switched power line allocation per subsystem
- Assess SA degradation over mission lifetime
- Coordinate with thermal on SA/radiator area competition

**Key Formulae:**
- P_SA = P_peak_sun + (P_eclipse × t_ecl)/(t_sun × eta_charge)
- P_SA_BOL = P_SA_EOL / (1 - degradation)^years
- A_SA = P_BOL / (eta_cell × S × cos(theta) × eta_pack)
- C_bat = (P_ecl × t_ecl) / (DoD × eta_discharge)

**References:** SMAD4 Ch.11.4; ECSS-E-ST-20C; vendor datasheets (GomSpace NanoPower)

---

## Appendix E: AOCS Engineer

**Responsibility:** Attitude determination and control, pointing accuracy, momentum management.

**Key Parameters Owned:** Pointing accuracy, stability, slew rate, wheel momentum, actuator mass/power.

**Key Activities:**
- Select AOCS architecture (passive magnetic -> MTQ -> RW -> RW+ST) based on pointing requirement
- Construct pointing error budget (RSS of all sources)
- Size reaction wheels for momentum storage and torque
- Size magnetorquers for momentum dumping
- Define safe mode attitude (sun-pointing) for power survival
- Assess disturbance torques (gravity gradient, magnetic, SRP, aero drag)

**Key Formulae:**
- RSS pointing: theta = ?(? theta?^2)
- Gravity gradient torque: T = (3mu/2R^3) × (I_z - I_x) × sin(2theta)
- Magnetic torque: T = m × B (dipole moment × field)
- Wheel momentum: H = T × t_accumulation

**References:** SMAD4 Ch.11.1; ECSS-E-ST-60-10C; Wertz §11.1

---

## Appendix F: Thermal Engineer

**Responsibility:** Temperature control (hot/cold case), radiators, heaters, MLI.

**Key Parameters Owned:** Max/min predicted temperatures, radiator area, heater power, thermal margin.

**Key Activities:**
- Define hot case (max solar + internal dissipation) and cold case (eclipse, min power)
- Select thermal control approach (passive coatings -> MLI -> heaters -> heat pipes)
- Size radiators to reject waste heat in hot case
- Size heaters to maintain minimum temperature in cold case (eclipse)
- Verify ECSS thermal margins (±5°C operating, ±10°C acceptance, ±15°C qualification)
- Coordinate with power on heater power budget and with structure on radiator mounting

**Key Formulae:**
- Stefan-Boltzmann: Q = ?sigmaAT? (radiative heat transfer)
- Equilibrium: Q_absorbed + Q_internal = Q_radiated
- Solar absorptance/emittance ratio (?/?) determines equilibrium temperature

**References:** SMAD4 Ch.11.5; ECSS-E-ST-31C; Gilmore, Spacecraft Thermal Control Handbook

---

## Appendix G: Communications Engineer

**Responsibility:** Link budget, transponder/antenna selection, frequency licensing, ground station network.

**Key Parameters Owned:** Link margin, data rate, frequency band, EIRP, antenna gain, modulation/coding.

**Key Activities:**
- Construct complete link budget (EIRP, FSPL, G/T, C/N0, Eb/N0, margin)
- Select frequency band based on data rate need and licensing constraints
- Select transponder and antenna (RF chain compatibility: band, impedance, polarisation)
- Coordinate with AOCS on antenna pointing accuracy
- Define ground station requirements (antenna size, G/T, location, contact schedule)
- Manage frequency licensing process (IARU/ISED/ITU as appropriate)

**Key Formulae:**
- FSPL = 20log10(4pid/lambda) dB
- EIRP = P_TX + G_TX - L_TX dBW
- Link margin = Eb/N0_avail - Eb/N0_req - L_impl dB

**References:** SMAD4 Ch.13; ECSS-E-ST-50-05C; ITU Radio Regulations; CCSDS 131.0-B

---

## Appendix H: Propulsion Engineer

**Responsibility:** ?V budget, propulsion system selection, propellant management.

**Key Parameters Owned:** Total ?V, Isp, propellant mass, thrust level, total impulse.

**Key Activities:**
- Construct ?V budget (orbit insertion, maintenance, collision avoidance, deorbit)
- Select propulsion technology (cold gas, electric, chemical) based on ?V and power
- Size propellant mass using Tsiolkovsky equation
- Coordinate with structure on tank mounting and plume impingement
- Assess debris compliance (deorbit capability vs natural lifetime)

**Key Formulae:**
- Tsiolkovsky: ?V = Isp × g0 × ln(m_initial/m_final)
- Propellant mass: m_p = m_dry × (e^(?V/(Isp·g0)) - 1)
- Total impulse: I_total = m_p × Isp × g0

**References:** SMAD4 Ch.17; Sutton & Biblarz, Rocket Propulsion Elements; vendor data

---

## Appendix I: Structures Engineer

**Responsibility:** Primary structure, mechanisms, CDS compliance, launch loads, integration.

**Key Parameters Owned:** Structure mass, natural frequency, margin of safety, deployer compatibility.

**Key Activities:**
- Select CubeSat structure (form factor, material, vendor)
- Verify CDS compliance (dimensions, rails, switches, RBF, CG)
- Analyse launch loads (quasi-static, random vibration, shock)
- Compute structural margin of safety (MoS)
- Design deployment mechanisms (antenna, solar panels, payload)
- Plan integration sequence (component -> board -> stack -> structure -> deployer)

**Key Formulae:**
- MoS = (Allowable / (Design × FoS)) - 1
- Natural frequency: f = (1/2pi)?(k/m)

**References:** CDS Rev 14.1; SMAD4 Ch.11.3; ECSS-E-ST-32C Rev.1; NASA GEVS

---

## Appendix J: Cost Engineer

**Responsibility:** Cost estimation, WBS, learning curves, risk-adjusted cost.

**Key Parameters Owned:** Total cost (MEUR), per-WBS element cost, launch cost, operations cost.

**Key Activities:**
- Construct WBS-level cost estimate (parametric early, bottom-up later)
- Apply CubeSat-specific COTS pricing where applicable
- Estimate learning curve effects for constellations
- Perform Monte Carlo cost risk analysis (P50/P70/P80)
- Track cost against programmatic ceiling
- Identify cost drivers and propose de-scope options

**References:** SMAD4 Ch.20; Aerospace Corp SSCM; NASA CEH; ECSS-M-ST-60C

---

## Appendix K: Compliance / Regulatory Engineer

**Responsibility:** ECSS standard compliance, frequency licensing, export control, debris mitigation.

**Key Parameters Owned:** Standard applicability matrix, filing status, export classification, debris compliance score.

**Key Activities:**
- Determine applicable ECSS/NASA standards and prepare tailoring matrix
- Manage frequency licensing process (IARU/ISED/ITU filings)
- Assess export control classification for all components (ITAR/EAR/CGP)
- Verify debris compliance (25yr IADC, 5yr FCC, casualty risk)
- Prepare RSSSA filing if mission has remote sensing capability
- File COPUOS registration post-launch

**References:** ECSS-S-ST-00-02C (tailoring); CPC-2-6-02 (ISED); RSSSA; ITU RR Article 9

---

## Appendix L: Ground Segment Engineer

**Responsibility:** Ground station network, MCS, data processing pipeline, ops concept.

**Key Parameters Owned:** Contact time per day, ground station locations, processing latency, data throughput.

**Key Activities:**
- Select ground station network (own station, KSAT, SatNOGS, DSN)
- Define MCS architecture (COSMOS, OpenMCT, Yamcs)
- Design data processing pipeline (L0 -> L1 -> L2 -> archive -> distribution)
- Plan operations concept (staffing, automation level, anomaly response)
- Coordinate with comms engineer on frequency bands and antenna requirements

**References:** SMAD4 Ch.14-15; ECSS-E-ST-70C; CCSDS standards

---

## Appendix M: Software Engineer

**Responsibility:** Flight software architecture, FDIR, TC/TM definition, ground software.

**Key Parameters Owned:** FSW architecture, mode definitions, command dictionary, telemetry list.

**Key Activities:**
- Define FSW architecture (mode manager, ADCS control, TM/TC handler, FDIR)
- Implement FDIR (Fault Detection, Isolation, Recovery) rules
- Define telecommand dictionary (all commands with parameters)
- Define telemetry dictionary (all HK and science packets)
- Define autonomous operations (time-tagged commands, on-board scheduling)
- Develop ground control software and procedures

**References:** ECSS-E-ST-70-01C; ECSS-E-ST-70-41C (PUS); CCSDS 133.0-B (Space Packet Protocol)

---

## Appendix N: Mission Operations Engineer

**Responsibility:** Operations concept, ground procedures, LEOP planning, anomaly response, scheduling.

**Key Parameters Owned:** Pass schedule, contact time, command load timing, housekeeping budget, anomaly recovery time.

**Key Activities:**
- Define operations concept (number of operators, shifts, automation level)
- Plan LEOP sequence (first contact, deployment, commissioning timeline)
- Define ground station network requirements (contact minutes per orbit, latency)
- Write nominal operations procedures (imaging, downlink, orbit maintenance)
- Define anomaly response procedures (safe mode recovery, contingencies)
- Plan scheduling and resource allocation (data volume vs contact time)

**Decision Authority:** Operations approach, automation vs manual, pass scheduling priority.

**Common Pitfalls:**
- Underestimating LEOP complexity (first hours are most critical)
- Not planning for degraded operations (single ground station, partial hardware)
- Assuming 24/7 staffing when budget supports only office hours
- Not accounting for seasonal ground station visibility

**References:** ECSS-E-ST-70C; ECSS-M-ST-10C Annex B (Operations); NASA SEH Appendix T (Phase E)

---

## Appendix O: Project Manager

**Responsibility:** Schedule, budget, team coordination, review preparation, stakeholder management.

**Key Parameters Owned:** Project schedule, cost breakdown, FTE allocation, risk register, milestone status.

**Key Activities:**
- Maintain project schedule with milestones and dependencies
- Track cost against budget (EAC, ETC, cost-to-complete)
- Coordinate between positions (ensure interface agreements are met)
- Prepare review data packages (SRR, PDR, CDR, FRR)
- Manage risk register (convene risk review boards)
- Interface with customer/stakeholder on requirements changes

**Decision Authority:** Schedule priorities, resource allocation, risk acceptance (with engineering concurrence).

**Common Pitfalls:**
- Not protecting schedule margin (consumed by early phases)
- Accepting scope creep without schedule/cost impact assessment
- Not tracking earned value (work done vs time spent)
- Holding reviews before engineering products are mature

**References:** ECSS-M-ST-10C (Project Management); NPR 7120.5 (NASA PM Requirements); PMI PMBOK

---

## Appendix P: User Representative

**Responsibility:** End-user needs, data product requirements, service level agreements, utilisation planning.

**Key Parameters Owned:** Data product specifications, latency requirements, coverage needs, user interface requirements.

**Key Activities:**
- Define data product requirements (format, resolution, accuracy, timeliness)
- Specify user access methods (API, web portal, direct download)
- Define service level agreements (availability, response time, data freshness)
- Validate that system design meets stakeholder expectations
- Represent user community in trade study decisions
- Plan user training and documentation

**Decision Authority:** Data product format, delivery mechanism, user interface design.

**Common Pitfalls:**
- Not distinguishing between "nice to have" and actual requirements
- Specifying implementation details instead of user needs
- Not considering different user types (research, commercial, public)
- Assuming unlimited bandwidth for data delivery

**References:** NASA SEH §4.1 (Stakeholder Expectations); ECSS-E-ST-10C §5.2 (Requirements); ISO 9241 (Usability)
