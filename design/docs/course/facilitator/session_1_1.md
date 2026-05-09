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
