# Part I — Foundations and Design

# Chapter 1 — Concurrent Design and the Systems Engineering Framework

> **Recommended background.** NASA Systems Engineering Handbook (SP-2016-6105 Rev 2) §1–§3 — [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/); NPR 7123.1D §3. An undergraduate engineering background is assumed; no prior spacecraft design experience is required.

## Learning objectives

By the end of this chapter, you will be able to:

1. Describe the purpose and structure of a Concurrent Design Facility (CDF) and contrast it with sequential design
2. Explain the System-V model and its two sides (decomposition and integration)
3. List the 17 common technical processes defined in NPR 7123.1D and explain their recursive application
4. Map NASA lifecycle phases (Pre-A through F) to ECSS phases and identify the key review gates
5. Identify the role of each CDF engineering position and the parameters it owns

---

## 1.1 What is a Concurrent Design Facility?

### 1.1.1 The problem with sequential design

Consider the question: how is spacecraft design traditionally done?

Traditional spacecraft design follows a **sequential (waterfall) approach**: one discipline completes its work, documents it, and passes the design to the next discipline. This method dominated the space industry from the 1960s through the 1990s. Its limitations are well documented:

- **Interface mismatches** discovered late in integration, requiring costly redesign
- **Budget overruns** in mass, power, and cost not caught until formal reviews
- **Long iteration cycles** — months between design reviews with limited inter-discipline feedback
- **Knowledge silos** — critical design rationale locked in individual engineers' notes
- **Rework costs** — the cost of correcting an error increases by roughly an order of magnitude per lifecycle phase (the "1-10-100 rule")

The aerospace industry's response was **concurrent engineering (CE)**, also called Integrated Product Development (IPD) or Integrated Concurrent Engineering (ICE). The core idea: bring all disciplines together to work simultaneously on a shared parametric model, resolving conflicts in real time rather than discovering them in review.

> **Industry practice.** Boeing's Phantom Works implemented concurrent engineering for the X-32 Joint Strike Fighter demonstrator in the late 1990s, reducing design iteration time from weeks to hours. JPL's Team X has been performing rapid mission assessments since 1995, completing Pre-Phase A studies in as little as one week. ESA's CDF, established in November 1998 at ESTEC (Noordwijk, Netherlands), became the most widely replicated model for space-specific concurrent design.

### 1.1.2 ESA's CDF — the reference model

ESA's Concurrent Design Facility pioneered the approach for space missions and has been widely replicated at space agencies worldwide (DLR, CNES, JAXA, CSA, and over 60 universities).

| Parameter | Value |
|-----------|-------|
| Established | November 1998, ESTEC, Noordwijk, NL |
| Team size | 15–25 domain specialists per study |
| Design-session format | 3–4 hour focused design sessions, typically 2 per week |
| Study duration | 3–6 weeks for a complete Phase 0/A mission assessment |
| Tooling | Originally Excel-based IDM; now Open Concurrent Design Tool (OCDT) |
| Output | Complete mission feasibility assessment: mass, power, cost, risk, schedule |
| Track record | 200+ studies completed by 20th anniversary (2018) |
| Cost savings | Studies completed in ~1/5 the time and ~1/3 the cost of the traditional approach |

[Source: ESA CDF official documentation; Bandecchi et al., "The ESA/ESTEC Concurrent Design Facility", ESA Bulletin No. 107, 2001]

### 1.1.3 Key principles of concurrent design

**Shared parametric model.** All disciplines read from and write to a common data model. When the power engineer changes the solar array area, the structures engineer immediately sees the mass impact, and the thermal engineer sees the changed radiator view factor. This eliminates the "frozen interface document" problem.

**Scoped parameter ownership.** Each engineering position "owns" a defined set of parameters. Only the power engineer can modify EPS parameters; only the AOCS engineer can modify attitude control parameters. This prevents conflicting edits while maintaining concurrent access.

**Real-time conflict detection.** When parameter changes create conflicts (e.g., mass budget exceeded, link margin negative), the system flags them immediately. The systems engineer arbitrates.

**Design convergence through iteration.** A CDF study typically converges through 3–5 major iterations, with each design session refining the design toward closure. The parametric model propagates changes automatically, so the team sees the system-level impact of every decision.

### 1.1.4 Concurrent design in software

The CDF concept does not require a physical room. A web-based concurrent-design tool can implement the same principles so that a distributed team shares one live model. The numerical examples in this book were produced with one such tool, SpaceCDF, which is described neutrally in Appendix A; the mapping between CDF principles and software features is summarised below.

| Principle | Software implementation |
|-----------|------------------------|
| Shared model | Real-time synchronisation; all participants see live updates |
| Parameter ownership | 16 engineering positions with scoped editing rights (§1.5) |
| Design convergence | Background design agents that propagate parametric relationships (sizing and analysis) |
| Conflict detection | Automated constraint engine over inter-parameter connections |
| Document generation | ECSS-style exports with full traceability |
| Review gates | Automated gate-criteria evaluation for MCR, SRR, SDR, PDR and CDR (§1.4) |

**Think about it.** Concurrent design accelerates convergence, but speed has a cost. Where might a tightly coupled team converge *too* quickly — on an architecture nobody questioned, or on a budget that only closed because everyone adjusted their numbers at once? Problem 1 asks you to weigh these risks against the advantages.

---

## 1.2 The System-V model

### 1.2.1 Origin and purpose

The "Vee" (V) model is the foundational framework for systems engineering. It appears in NASA SEH Section 2.3 (Figure 2.3-1), in ECSS-E-ST-10C, and in ISO/IEC 15288. It is not a project schedule — it is a **logical model** showing the relationship between decomposition (breaking the problem down) and integration (building and verifying the solution).

The V-model answers two fundamental questions:

1. **Left side (top-down):** How do we decompose the mission need into buildable components?
2. **Right side (bottom-up):** How do we verify that what we built satisfies the original need?

The key insight is **horizontal traceability**: every element on the left side has a corresponding verification or validation activity on the right side, connected at the same level of abstraction. Figure 1.1 shows the model; the left and right branches are tabulated in §1.2.2 and §1.2.3.

![System-V model: decomposition on the left, integration and verification on the right.](../assets/figures/fig_system_v.png)

**Figure 1.1** — The System-V model (after NASA SEH Figure 2.3-1). The left branch decomposes the mission need into components; the right branch integrates and verifies at matching levels; the horizontal links are the traceability between a requirement and the activity that verifies it.

### 1.2.2 Left side: top-down decomposition

The left side of the V answers "how do we break the problem down into solvable pieces?"

| Level | Activity | Key question | Output |
|-------|----------|-------------|--------|
| 1. Mission need | Define the problem and concept of operations | What problem are we solving? For whom? | ConOps, problem statement, MoEs |
| 2. Stakeholder requirements | Capture needs of all stakeholders | What must the system achieve? (WHAT, not HOW) | Stakeholder requirements baseline |
| 3. System architecture | Define segments, elements, interfaces | How is the system structured? | System architecture, ICDs |
| 4. Subsystem design | Design each subsystem to meet allocated requirements | How does each subsystem work? | Subsystem specifications |
| 5. Component selection | Choose or design lowest-level components | Which hardware/software fulfils each need? | Component specifications, BoM |

### 1.2.3 Right side: bottom-up integration

The right side answers "how do we verify that what we built satisfies the original need?"

| Level | Activity | Key question | Verification method |
|-------|----------|-------------|-------------------|
| 5. Component verification | Test each component against its spec | Does each part work? | Inspection, test |
| 4. Subsystem verification | Integrate and test each subsystem | Do subsystems meet allocated requirements? | Test, analysis |
| 3. Integration and test | Assemble the system and test interfaces | Do the subsystems work together? | Test, demonstration |
| 2. System verification | Verify system against requirements | Does the system meet all requirements? | Test, analysis, inspection, demonstration |
| 1. Mission validation | Validate against the original need | Does it solve the original problem? | Operations, user acceptance |

### 1.2.4 Horizontal traceability

The horizontal links in Figure 1.1 represent **horizontal traceability** — the principle that every element on the left must have a corresponding verification or validation activity on the right:

- Each **requirement** (left) has a **verification method** (right): analysis, test, inspection or review of design, plus demonstration where ECSS lists it — abbreviated ATIR(D) throughout this book (Chapter 14 treats the methods in detail)
- Each **design decision** (left) has a **test or analysis** (right) to confirm it works
- This traceability is captured in the **Requirements Verification Matrix (RVM)**

> **Key equation.** The traceability completeness metric is
>
> $$T_c = \frac{N_{\text{verified}}}{N_{\text{total requirements}}} \times 100\%$$
>
> A target of $T_c = 100\%$ is required at CDR. At PDR, $T_c \geq 90\%$ is typical.

**Key insight:** the V is not a timeline — it is a *correspondence map*. The left branch asks "what must be done?" at increasing levels of detail. The right branch asks "did we do it?" at corresponding levels. Each horizontal row is a matched pair.

### 1.2.5 Phase mapping to the V

Although the V is not a schedule, each of its levels is worked predominantly in particular lifecycle phases (the phases themselves are defined in §1.4). The mapping is given in Table 1.1.

**Table 1.1** — Mapping of V-model levels to NASA lifecycle phases.

| V-level | Left branch (decomposition) | Right branch (verification) | NASA phase |
|---------|---------------------------|---------------------------|------------|
| Top | Stakeholder needs and objectives | Operational validation (does the mission deliver value?) | Pre-A / E |
| Mission | Mission-level requirements | Mission-level V&V (commissioning, in-orbit checkout) | A / E |
| System | System-level requirements | System integration and test (end-to-end) | B / D |
| Subsystem | Subsystem requirements | Subsystem qualification and acceptance test | C / D |
| Bottom | Implementation (detailed design, build) | Component acceptance | C–D |

### 1.2.6 Real mission example: Planet SuperDove

Planet's SuperDove constellation (2020–present) illustrates the V-model in commercial practice:

| Level | Requirement (left) | Verification (right) |
|-------|-------------------|---------------------|
| Stakeholder | "Daily global coverage at < 5 m for agricultural analytics" | In-orbit validation: coverage maps, user feedback |
| Mission | "Revisit ≤ 1 day at ±60° latitude" | Constellation coverage simulation confirmed |
| System | "GSD ≤ 3.7 m at 475 km SSO" | End-to-end imaging test from orbit |
| Subsystem | "Telescope aperture ≥ 90 mm, 8 spectral bands" | Instrument calibration on ground and in orbit |

*[Source: Planet Labs, "Planet Imagery Product Specifications," 2023]*

### 1.2.7 Iteration and the SE engine

The V is not a single pass. Real design iterates — requirements change as design constraints are discovered, and design parameters feed back to refine requirements. This iterative loop is captured in the concept of the **"SE engine"** (NASA SEH Section 2.1): the 17 common technical processes applied recursively at every level of the system hierarchy. These processes are the subject of §1.3.

[Source: NASA SEH Section 2.3, Figure 2.3-1; INCOSE Systems Engineering Handbook, 4th Edition, Section 3.2]

---

## 1.3 The 17 common technical processes

### 1.3.1 Overview

NASA's NPR 7123.1D defines 17 processes that apply recursively at every level of the system hierarchy. They are grouped into three categories, collectively called the **"SE engine"**. These processes are not sequential — they execute concurrently and iteratively, which is precisely what a CDF facilitates. Figure 1.2 shows the three groups as a pyramid; the following subsections tabulate each process.

![NASA SEH 17 common technical processes, grouped as system design, product realisation and technical management.](../assets/figures/fig_seh_processes.png)

**Figure 1.2** — The 17 common technical processes of NPR 7123.1D, grouped into system design (1–4), product realisation (5–9) and technical management (10–17).

[Source: NPR 7123.1D Chapter 3; NASA SEH Section 2.1, Figure 2.1-1]

### 1.3.2 System design processes (1–4)

These processes decompose the problem into a solution. They correspond to the left side of the V-model.

| # | Process | Key activity | Key output | NASA SEH reference |
|---|---------|-------------|------------|-------------------|
| 1 | **Stakeholder Expectations Definition** | Elicit needs, define ConOps, establish MoEs | Stakeholder requirements baseline | Section 4.1 |
| 2 | **Technical Requirements Definition** | Write "shall" statements, define MoPs and TPMs | Technical requirements baseline | Section 4.2 |
| 3 | **Logical Decomposition** | Functional analysis, behavioural modelling, derived requirements | Functional architecture | Section 4.3 |
| 4 | **Design Solution Definition** | Trade studies, select among alternatives, produce baseline design | Design solution baseline | Section 4.4 |

### 1.3.3 Product realisation processes (5–9)

These processes build, verify, and deliver the solution. They correspond to the right side of the V-model.

| # | Process | Key activity | Key output | NASA SEH reference |
|---|---------|-------------|------------|-------------------|
| 5 | **Product Implementation** | Make, buy, code, or reuse lowest-level products | Hardware/software products | Section 5.1 |
| 6 | **Product Integration** | Assemble per integration plan, verify interfaces | Integrated system | Section 5.2 |
| 7 | **Product Verification** | Confirm product meets technical requirements (ATIR(D)) | Verification evidence | Section 5.3 |
| 8 | **Product Validation** | Confirm product meets stakeholder expectations | Validation evidence | Section 5.4 |
| 9 | **Product Transition** | Deliver, deploy, hand over to operations | Operational system | Section 5.5 |

### 1.3.4 Technical management processes (10–17)

These processes manage the engineering work and apply throughout the lifecycle.

| # | Process | Key activity | Governing document |
|---|---------|-------------|-------------------|
| 10 | **Technical Planning** | SEMP, subsidiary plans, WBS | NPR 7123.1D Section 3.10 |
| 11 | **Requirements Management** | Baselining, traceability, change control | NPR 7123.1D Section 3.11 |
| 12 | **Interface Management** | ICDs, IRDs, internal and external interfaces | NPR 7123.1D Section 3.12 |
| 13 | **Technical Risk Management** | Identification, assessment, mitigation per NPR 8000.4 | NPR 8000.4B |
| 14 | **Configuration Management** | Baselines, CM plan, CCBs | NPR 7120.5F Chapter 4 |
| 15 | **Technical Data Management** | Data rights, retention, dissemination | NPR 7123.1D Section 3.15 |
| 16 | **Technical Assessment** | TPMs, reviews, EVM, health checks | NPR 7123.1D Section 3.16 |
| 17 | **Decision Analysis** | Structured alternative selection (trade studies) | NASA SEH Section 6.8 |

### 1.3.5 Recursion across the system hierarchy

A critical property of the 17 processes is that they apply **recursively** at every level of the system hierarchy, as Figure 1.3 illustrates.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 420" style="max-width:760px; font-family: sans-serif;">
  <defs>
    <marker id="recArrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6" fill="#1f4e79"/>
    </marker>
  </defs>
  <!-- Nested levels -->
  <rect x="20" y="20" width="720" height="380" rx="14" fill="none" stroke="#1f4e79" stroke-width="2"/>
  <text x="40" y="46" font-size="14" font-weight="bold" fill="#1f4e79">Mission level</text>
  <text x="40" y="64" font-size="11" fill="#444">mission requirements · ConOps · validation</text>

  <rect x="60" y="80" width="640" height="300" rx="12" fill="none" stroke="#2e6da4" stroke-width="2"/>
  <text x="80" y="106" font-size="14" font-weight="bold" fill="#2e6da4">System level</text>
  <text x="80" y="124" font-size="11" fill="#444">system requirements · architecture · verification</text>

  <rect x="100" y="140" width="560" height="220" rx="10" fill="none" stroke="#4a8fcf" stroke-width="2"/>
  <text x="120" y="166" font-size="14" font-weight="bold" fill="#4a8fcf">Subsystem level</text>
  <text x="120" y="184" font-size="11" fill="#444">subsystem requirements · design · testing</text>

  <rect x="140" y="200" width="480" height="140" rx="8" fill="none" stroke="#7fb3e6" stroke-width="2"/>
  <text x="160" y="226" font-size="14" font-weight="bold" fill="#4a8fcf">Component level</text>
  <text x="160" y="244" font-size="11" fill="#444">component specifications · procurement · acceptance</text>

  <!-- Central recursive cycle -->
  <path d="M 430 300 a 40 40 0 1 1 -0.1 -0.1" fill="none" stroke="#1f4e79" stroke-width="3" marker-end="url(#recArrow)"/>
  <text x="430" y="304" text-anchor="middle" font-size="11" font-weight="bold" fill="#1f4e79">17 SE</text>
  <text x="430" y="318" text-anchor="middle" font-size="11" font-weight="bold" fill="#1f4e79">processes</text>

  <!-- Side annotation -->
  <text x="520" y="280" font-size="11" fill="#444">same processes,</text>
  <text x="520" y="296" font-size="11" fill="#444">different scope, detail</text>
  <text x="520" y="312" font-size="11" fill="#444">and duration at each level</text>
</svg>

**Figure 1.3** — Recursion of the SE engine. The same 17 processes execute at the mission, system, subsystem and component levels, each with its own requirements baseline, design and verification evidence.

At each level, the same processes execute but with different scope, detail, and duration. In a CDF environment, multiple levels are often worked concurrently — the systems engineer manages the mission and system levels while subsystem engineers work their respective domains.

> **Industry practice.** On the James Webb Space Telescope (JWST), requirements management (Process 11) was applied at five levels of the system hierarchy simultaneously: Observatory, Optical Telescope Element, Integrated Science Instrument Module, individual instruments (NIRSpec, MIRI, NIRCam, FGS), and components (detectors, mechanisms). Each level had its own requirements baseline, traceability matrix, and verification plan. The total requirements count exceeded 10,000.

---

## 1.4 Lifecycle phases and review gates

### 1.4.1 NASA lifecycle phases

NASA defines seven lifecycle phases for space flight projects, governed by NPR 7120.5F. Each phase has specific objectives, activities, and exit criteria evaluated at formal review gates called Key Decision Points (KDPs). Figure 1.4 shows the phases and the review gates between them; Table 1.2 details each phase.

![Lifecycle phases Pre-A through F and the review gates between them.](../assets/figures/fig_lifecycle.png)

**Figure 1.4** — NASA space-flight project lifecycle (NPR 7120.5F): phases Pre-A through F and the review gates that separate them. Concurrent-design studies of the kind described in this book cover Pre-Phase A through Phase C.

[Source: NPR 7120.5F Chapter 2; NASA SEH Chapter 3]

### 1.4.2 Phase details

**Table 1.2** — NASA lifecycle phases, exit reviews and key outputs.

| Phase | Name | Primary activity | Exit review | Key outputs |
|-------|------|-----------------|-------------|-------------|
| **Pre-A** | Concept Studies | Identify need, explore feasibility, develop ConOps | MCR | Mission concept, preliminary ConOps, feasibility assessment |
| **A** | Concept and Technology Development | Develop requirements, mature technology to TRL 4+ | SRR/SDR | Requirements baseline, technology development plan |
| **B** | Preliminary Design and Technology Completion | Preliminary design, close preliminary budgets, TRL 6+ | PDR | Preliminary design, budget allocations, test plans |
| **C** | Final Design and Fabrication | Detailed design, build hardware, TRL 8 | CDR | Detailed drawings, as-built documentation, flight hardware |
| **D** | Assembly, Integration and Test, Launch | System AIT, environmental testing, launch | TRR, QR, ORR, FRR | Tested flight system, launch readiness |
| **E** | Operations and Sustainment | Operate the mission, produce data products | PLAR | Science data, operational lessons |
| **F** | Closeout | Decommission, passivate, dispose, lessons learned | DR | Disposal confirmation, final report |

**Key Decision Points (KDPs):** These are go/no-go authority decisions between phases, lettered A through F. They are distinct from technical reviews — KDPs are management decisions informed by technical review outcomes. For projects exceeding $250M (USD), KDP-C requires a Joint Confidence Level (JCL) analysis per NPR 7120.5F.

### 1.4.3 ECSS lifecycle phases

ECSS defines a similar but not identical lifecycle. The phase letters conveniently align, but the entry/exit criteria and review content differ.

[Source: ECSS-M-ST-10C Rev.1, Section 5.3]

| ECSS phase | Name | NASA equivalent | Key difference |
|-----------|------|----------------|----------------|
| 0 | Mission Analysis / Needs Identification | Pre-A | ECSS Phase 0 includes formal mission analysis |
| A | Feasibility | A | ECSS-A focuses on demonstrating feasibility |
| B | Preliminary Definition (B1/B2) | B | ECSS splits into B1 (system) and B2 (detailed) |
| C | Detailed Definition | C | Similar scope |
| D | Qualification and Production | D | ECSS-D emphasises qualification models |
| E | Utilisation | E | Similar scope |
| F | Disposal | F | ECSS-F explicitly addresses passivation |

### 1.4.4 Review gates — what each checks

Table 1.3 is the canonical list of review gates used throughout this book. Chapter 16 gives the detailed entry and exit criteria for each gate and discusses how to present a design at a review board.

**Table 1.3** — Review gates, the question each answers, and the evidence required.

| Review | Full name | Phase transition | Key question | Required evidence |
|--------|-----------|------------------|-------------|-------------------|
| **MCR** | Mission Concept Review | Pre-A → A | Is the mission need justified? Is space the right answer? | Problem statement, stakeholder analysis, alternatives analysis, ConOps draft |
| **SRR** | System Requirements Review | A | Are requirements complete, consistent, traceable, and verifiable? | Requirements baseline, traceability matrix, risk register, preliminary ConOps |
| **SDR** | System Design Review | A → B | Does the system architecture satisfy the requirements? | System architecture, functional decomposition, interface definitions |
| **PDR** | Preliminary Design Review | B → C | Does the preliminary design meet all requirements? | Design description, budget status (mass/power/cost), risk mitigation plans |
| **CDR** | Critical Design Review | C → D | Is the design complete and ready for fabrication? | Detailed drawings, analysis results, test plans, all budgets closed with positive margins |
| **TRR** | Test Readiness Review | D | Is the system ready for formal testing? | Test procedures, facility readiness, acceptance criteria |
| **QR** | Qualification Review | D | Has the qualification programme demonstrated that the design meets its requirements with margin? | Qualification test results, non-conformance closure, waivers, as-qualified baseline |
| **FRR** | Flight Readiness Review | D → E | Is everything ready for launch? | All tests passed, waivers documented, launch procedures verified |

> **Industry practice.** RADARSAT-2 (MDA/CSA, launched 2007) went through all NASA-equivalent review gates over a 6-year development. The CDR alone involved over 400 review items and 50 reviewers across 3 weeks. The mission exceeded its 7-year design life, operating for over 15 years — a testament to thorough verification at each gate.

---

## 1.5 CDF engineering positions

### 1.5.1 Position overview

In a CDF study, each engineering position owns a set of parameters and is responsible for its domain's design decisions. Table 1.4 lists the 16 positions used throughout this book. Part IV gives a full briefing for each position — the decisions it owns, the equations it uses and the pitfalls it should watch for.

**Table 1.4** — The 16 CDF engineering positions, their responsibilities and the parameters they own.

| Position | Responsibility | Key owned parameters | Primary interfaces |
|----------|---------------|---------------------|-------------------|
| **Systems Engineer** | Overall architecture, budgets, margins, conflict resolution | Mass margin, power margin, system-level budgets | All positions |
| **Project Manager** | Schedule, budget authority, risk owner; chairs the design session | Schedule, cost cap, risk register, review-gate decisions | Systems Engineer, Cost, all positions |
| **Mission Analyst** | Orbit design, coverage analysis, ground station access | Altitude, inclination, RAAN, eclipse fraction, contact time | Comms, Payload, Ground |
| **Payload Lead** | Instrument performance, data generation rates | GSD, spectral bands, data rate, FOV, SNR | Mission Analyst, Power, AOCS, Comms |
| **Power Engineer** | Solar arrays, batteries, EPS architecture, duty cycling | SA area, battery capacity, bus voltage, DoD | All (power is a universal constraint) |
| **AOCS Engineer** | Attitude sensors, actuators, pointing modes | Pointing accuracy, slew rate, wheel momentum, sensor suite | Payload, Structures, Propulsion |
| **Thermal Engineer** | Temperature control, radiators, heaters, coatings | Max/min temperatures, radiator area, heater power, thermal margin | Structures, Power, Payload |
| **Comms Engineer** | Link budget, transponder, antenna, spectrum licensing | Link margin, data rate, frequency band, EIRP, G/T | Mission Analyst, Payload, Ground |
| **Propulsion Engineer** | Δv budget, thruster selection, propellant mass | Isp, propellant mass, total impulse, thrust vector | Mission Analyst, AOCS, Structures |
| **Structures Engineer** | Primary structure, mechanisms, launch loads | Structure mass, natural frequency, margin of safety | All (mass is a universal constraint) |
| **Cost Engineer** | WBS, cost estimating relationships, schedule | Total cost, per-subsystem cost, launch cost, risk-adjusted cost | Systems Engineer, all subsystems |
| **Compliance Engineer** | Standards, frequency licensing, export control | Standard applicability, ITAR/EAR status, filing status | All |
| **User Representative** | End-user needs, data product requirements | Data format, latency, accessibility, coverage | Payload, Comms, Ground |
| **Mission Operations** | Ground ops concept, staffing, automation | Contact schedule, automation level, anomaly procedures | Comms, Ground, Systems |
| **Ground Segment** | Ground stations, data processing pipeline | Station network, processing latency, archive capacity | Comms, Mission Ops, User Rep |
| **Software Engineer** | Flight software, FDIR, TC/TM interfaces | FSW architecture, command dictionary, FDIR rules | OBC, AOCS, Comms, Payload |

### 1.5.2 Interface conflicts

The most productive CDF design sessions are those where **interface conflicts** are identified and resolved. Common conflict patterns:

| Conflict | Positions involved | Resolution approach |
|----------|--------------------|-------------------|
| Mass budget exceeded | Systems, Structures, all subsystems | Re-allocate margins, descope payload, select lighter components |
| Power budget exceeded | Systems, Power, Payload, Comms | Adjust duty cycles, increase SA area, reduce payload power |
| Pointing requirement vs actuator capability | Payload, AOCS, Structures | Relax pointing requirement, add fine steering mirror, improve isolation |
| Downlink capacity vs data generation | Comms, Payload, Ground | Add ground stations, increase TX power, reduce data rate, add compression |
| Volume constraint vs thermal rejection | Structures, Thermal, Payload | Redesign radiator location, add deployable radiator, reduce heat dissipation |

---

## 1.6 Working the lifecycle in a concurrent-design study

A concurrent-design study does not replace the lifecycle of §1.4; it compresses the early part of it. A typical Phase 0/A study takes the mission from a stated need to a converged concept with closed mass, power, link and cost budgets — the evidence required at MCR and SRR in Table 1.3 — and a well-run Phase B study carries the same model forward to the PDR evidence. The chapters that follow are organised in the order in which a concurrent-design team encounters the work:

- **Chapters 2–3** set the regulatory and standards context within which every design decision must sit.
- **Chapters 4–8** work the left side of the V from mission need (Chapter 4) through requirements (Chapter 5), functional decomposition (Chapter 6), orbit selection (Chapter 7) and mission architecture with its engineering budgets (Chapter 8).
- **Chapters 9–12** size the subsystems — power and thermal, attitude control, communications, and structures, propulsion and data handling.
- **Chapters 13–19** cover equipment selection, verification and validation, risk and interfaces, cost and reviews, and the ground and operations segments that complete the right side of the V.

Each chapter identifies which of the 17 processes it exercises and which review gate its outputs feed.

---

## 1.7 The running examples

Two spacecraft are used as running examples throughout this book. The primary example is a **3U Earth-observation (EO) CubeSat** — a multispectral imager for agricultural monitoring, sized in detail from Chapter 4 onwards. Alongside it, we use a second, deliberately simpler spacecraft: **UniSat-1**, a 1U CubeSat technology demonstrator designed by a university team. This is the simplest realistic spacecraft design.

**Mission:** Demonstrate a novel MEMS-based magnetometer for space weather monitoring from LEO.

**Why 1U?** The 1U form factor (100 × 100 × 113.5 mm, up to 1.33 kg) is the smallest standard CubeSat and the entry point for many university and educational missions. It forces extreme design discipline — every gram, every milliwatt, and every cubic centimetre matters.

| Parameter | Value |
|-----------|-------|
| Form factor | 1U (100 × 100 × 113.5 mm) |
| Mass limit | 1.33 kg (CDS Rev 14) |
| Target mass | 1.0 kg |
| Orbit | 400 km circular, 51.6° (ISS rideshare) |
| Design lifetime | 6 months |
| Payload | MEMS magnetometer (50 g, 0.2 W, < 1 kbps) |
| Comms | UHF 437 MHz, 9600 bps |
| Power | ~2 W orbit average (body-mounted solar cells) |
| AOCS | Passive magnetic (permanent magnet + hysteresis rods) |
| Propulsion | None (natural deorbit in ~1 year) |
| Estimated cost | 50–200 kEUR (indicative, 2026) |
| Development time | 6–12 months |

UniSat-1 illustrates that a meaningful space mission can be accomplished with just five subsystems (EPS, OBC, Comms, Structure, Payload), no active attitude control, no propulsion, and no thermal hardware beyond surface coatings. As the book progresses, each chapter will show how the same design processes apply to UniSat-1, but with radically simpler solutions at every step. Later chapters introduce it with the phrase "Returning to UniSat-1".

---

## Summary

| Topic | Key takeaway |
|-------|-------------|
| CDF | Concurrent multi-discipline design resolves conflicts in real time; a shared parametric model with scoped ownership is what makes this possible |
| System-V | Left side decomposes (need to components); right side integrates (build to validate); horizontal traceability links them |
| 17 processes | Recursive at every system level; grouped as Design (1–4), Realisation (5–9), Management (10–17) |
| Lifecycle phases | Pre-A through F with KDP gates; ECSS phases approximately align; concurrent-design studies cover Pre-A through C |
| Review gates | Each gate answers a specific question with required evidence (Table 1.3); gate criteria can be evaluated automatically where the evidence is numerical |
| Positions | Each owns a parameter domain; conflicts arise at interfaces; the systems engineer arbitrates |
| Running examples | A 3U EO CubeSat and UniSat-1, a 1U magnetometer demonstrator, are carried through every chapter |

---

## Problems

1. **Concurrent versus sequential design.** List three advantages that concurrent design offers over sequential (waterfall) design, and three risks that it introduces (consider, for example, groupthink and premature convergence). For each risk, propose one practice a systems engineer could adopt to mitigate it.

2. **Sketching the V.** Sketch the V-model from memory and label each of its five levels on both branches. Add the horizontal traceability links and name one verification method (from ATIR(D)) appropriate to each level.

3. **Cost of late change.** Using the "1-10-100 rule" of §1.1.1, an interface mismatch that would cost 2 kEUR to correct in Phase A is discovered during environmental testing in Phase D. Estimate the cost of correcting it, stating your assumptions about how many phase boundaries the error has crossed. What does this imply about the value of a Phase A concurrent-design study whose cost is roughly 1/3 of a conventional study?

4. **The SE engine and software.** For each of the 17 common technical processes in §1.3, state whether a concurrent-design tool or spreadsheet can support it *directly* (by computing or checking something), *indirectly* (by recording the result of human judgement), or *not at all*. Which processes require the most human judgement, and why?

5. **Automating a gate.** The MCR requires the evidence listed in Table 1.3. Classify each item of evidence as (a) something that can be auto-evaluated from a parametric model (e.g., a budget closing with positive margin) or (b) something that requires review by an engineer. For one item in category (b), write the question a reviewer would have to answer.

6. **Traceability completeness.** A 3U EO CubeSat project has 48 requirements, of which 41 have an assigned and completed verification method. Compute the traceability completeness $T_c$. Is the project ready for PDR by the rule of thumb in §1.2.4? How many further requirements must be verified before CDR?

7. **Phase identification.** For each of the following activities, identify the NASA lifecycle phase in which it principally occurs and the review gate whose evidence it feeds: (a) a thermal-vacuum test of the flight model; (b) a trade study between a 500 km and a 600 km sun-synchronous orbit; (c) passivation of the battery at end of life; (d) closing the mass budget with 15 % system margin; (e) writing the first draft of the ConOps; (f) release of detailed manufacturing drawings.

8. **Position interactions.** For a 3U EO CubeSat with a multispectral imager, an S-band downlink and three-axis attitude control, identify the three pairs of positions in Table 1.4 that you expect to interact most frequently, and explain the parameter each pair contends over. Where do you expect the most difficult trade-off, and why?

9. **Positions for a small team.** Returning to UniSat-1, which has only five subsystems and no active attitude control or propulsion: which of the 16 positions are still needed, which can be combined, and which are not needed at all? Propose a team of five people and allocate the positions between them. How does the CDF process change when the team is this small?

10. **A V-model table for UniSat-1.** Following the SuperDove example of §1.2.6, write a four-row table (stakeholder, mission, system, subsystem) giving one requirement on the left branch and its matching verification activity on the right branch for UniSat-1. Use the parameters in §1.7.

---

## References

1. NASA, *Systems Engineering Handbook* (SP-2016-6105 Rev 2), 2016. [https://www.nasa.gov/reference/systems-engineering-handbook/](https://www.nasa.gov/reference/systems-engineering-handbook/)
2. NASA, *NPR 7123.1D — Systems Engineering Processes and Requirements*, 2020. [https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_)
3. NASA, *NPR 7120.5F — NASA Space Flight Program and Project Management Requirements*, 2021. [https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7120_005F_)
4. ECSS, *ECSS-M-ST-10C Rev.1 — Space Project Management*, 2009. [https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/](https://ecss.nl/standard/ecss-m-st-10c-rev-1-space-project-management-6-march-2009/)
5. INCOSE, *Systems Engineering Handbook*, 4th Edition, 2015. [https://www.incose.org/products-and-publications/se-handbook](https://www.incose.org/products-and-publications/se-handbook)
6. Bandecchi, M. et al., "The ESA/ESTEC Concurrent Design Facility", *ESA Bulletin* No. 107, 2001. [https://www.esa.int/esapub/bulletin/bullet107/bul107_2.pdf](https://www.esa.int/esapub/bulletin/bullet107/bul107_2.pdf)
7. ESA, "20 Years of Concurrent Design at ESA", 2018. [https://www.esa.int/Enabling_Support/Space_Engineering_Technology/CDF/What_is_the_CDF](https://www.esa.int/Enabling_Support/Space_Engineering_Technology/CDF/What_is_the_CDF)
8. Wertz, J.R. et al., *Space Mission Engineering: The New SMAD* (SMAD4), Microcosm Press, 2011. [https://www.microcosminc.com/](https://www.microcosminc.com/)
9. Planet Labs, *Planet Imagery Product Specifications*, 2023.
