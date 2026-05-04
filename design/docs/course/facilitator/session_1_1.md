# Session 1.1: Introduction to Space Mission Design

**Duration:** 2 hours
**Prerequisites:** None (engineering background assumed)
**References:** NASA SEH Rev 2 (§1-3), NPR 7123.1D, ECSS-M-ST-10C Rev.1

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Describe the purpose and structure of a Concurrent Design Facility
2. Explain the System-V model and its two sides (decomposition + integration)
3. List the 17 common technical processes and their groupings
4. Map NASA and ECSS lifecycle phases to review gates
5. Identify the role of each CDF engineering position

---

## 1. What is a Concurrent Design Facility? (20 min)

### Teaching Notes

Begin by asking the group: *"How is spacecraft design traditionally done?"*

Traditional approach: sequential design -- one discipline finishes, hands off to the next. Problems:
- Interface mismatches discovered late
- Mass/power budget overruns not caught until integration
- Long iteration cycles (months between design reviews)
- Knowledge locked in individual engineers' heads

**Concurrent design** changes this: all disciplines work simultaneously on a shared parametric model, in the same room, resolving conflicts in real-time.

### Key Facts (verified -- see Appendix N)

**ESA's CDF** was established in **November 1998** at ESTEC, Noordwijk, Netherlands. It pioneered the approach for space missions.

- **Team:** ~20-25 domain specialists working simultaneously
- **Sessions:** 4-hour focused design sessions, typically 2 per week
- **Study duration:** 4-8 weeks for a complete mission assessment
- **Tool:** Shared parametric model (originally Excel-based IDM, now OCDT -- Open Concurrent Design Tool)
- **Output:** Complete mission feasibility assessment including mass, power, cost, risk, and schedule
- **Track record:** Over 200 studies completed by the 20th anniversary (2018)

*[Source: ESA CDF official documentation; "20 years of ESA's CDF" publication]*

### SpaceCDF Context

SpaceCDF implements this approach as a web-based tool:
- Shared real-time design model via WebSocket
- 15 engineering positions with scoped parameter editing
- 20 automated design agents that converge the design in seconds
- Conflict detection and resolution workflow
- ECSS-compliant document generation

**Discussion prompt:** *What advantages does concurrent design offer over sequential? What are the risks?*

---

## 2. The System-V Model (30 min)

### Teaching Notes

The "Vee" (V) model is the fundamental framework for systems engineering. It appears in NASA SEH §2.3 (Figure 2.3-1) and underpins both NASA and ECSS processes.

### The Two Sides

```
                    Mission Need
                   /            \
          Requirements          Validation
             /                      \
      System Design            Verification
           /                        \
    Subsystem Design        Integration & Test
         /                          \
  Component Selection    Component Verification
```

**Left side (top-down decomposition):**
1. Mission need -> What problem are we solving?
2. Mission requirements -> What must the system achieve? (WHAT, not HOW)
3. System architecture -> How is the system structured? (segments, interfaces)
4. Subsystem design -> How does each subsystem work?
5. Component selection -> Which hardware fulfils each need?

**Right side (bottom-up integration):**
5. Component verification -> Does each component meet its spec?
4. Subsystem integration -> Do subsystems work together?
3. System verification -> Does the system meet requirements?
2. System validation -> Does the system satisfy the mission need?
1. Mission operations -> Does it solve the original problem?

### Key Principle: Traceability

Every element on the right traces horizontally to its counterpart on the left:
- Each **requirement** (left) has a **verification method** (right)
- Each **design decision** (left) has a **test or analysis** (right)
- This horizontal traceability is captured in the **Verification Matrix**

### Key Principle: Iteration

The V is not a single pass. Real design iterates:
- Requirements change as design constraints are discovered
- Design parameters feed back to refine requirements
- This is captured in the "SE Engine" -- the iterative loop of the 17 processes

*[Source: NASA SEH §2.3, Figure 2.3-1]*

**Diagram:** Draw the V on the whiteboard with the group. Have participants label each level.

---

## 3. The 17 Common Technical Processes (30 min)

### Teaching Notes

NASA's NPR 7123.1 (currently Revision D) defines 17 processes that apply recursively at every level of the system hierarchy. They are grouped into three categories, collectively called the **"SE Engine"**.

*[Source: NPR 7123.1D Chapter 3; NASA SEH §2.1]*

### System Design Processes (1-4) -- NASA SEH Chapter 4

These processes decompose the problem into a solution:

| # | Process | Key Activity | Key Output |
|---|---------|-------------|------------|
| 1 | **Stakeholder Expectations Definition** | Elicit needs, define ConOps, establish MoEs | Stakeholder requirements baseline |
| 2 | **Technical Requirements Definition** | Write "shall" statements with MoPs/TPMs | Technical requirements baseline |
| 3 | **Logical Decomposition** | Functional/behavioural analysis, derived requirements | Functional architecture |
| 4 | **Design Solution Definition** | Select among alternatives; produce baseline design | Design solution baseline |

### Product Realization Processes (5-9) -- NASA SEH Chapter 5

These processes build and verify the solution:

| # | Process | Key Activity | Key Output |
|---|---------|-------------|------------|
| 5 | **Product Implementation** | Make/buy/reuse lowest-level products | Hardware/software products |
| 6 | **Product Integration** | Assemble per integration plan | Integrated system |
| 7 | **Product Verification** | Confirm product meets requirements | Verification evidence |
| 8 | **Product Validation** | Confirm product meets stakeholder expectations | Validation evidence |
| 9 | **Product Transition** | Deliver, hand over, deploy | Operational system |

### Technical Management Processes (10-17) -- NASA SEH Chapter 6

These processes manage the engineering work:

| # | Process | Key Activity |
|---|---------|-------------|
| 10 | **Technical Planning** | SEMP and subsidiary plans |
| 11 | **Requirements Management** | Baselining, traceability, change control |
| 12 | **Interface Management** | ICDs/IRDs, internal + external interfaces |
| 13 | **Technical Risk Management** | Per NPR 8000.4 |
| 14 | **Configuration Management** | Baselines, CM plan, change boards |
| 15 | **Technical Data Management** | Data rights, retention, dissemination |
| 16 | **Technical Assessment** | TPMs, reviews, EVM, health checks |
| 17 | **Decision Analysis** | Structured alternative selection (trade studies) |

### Recursion

These 17 processes apply at **every level** of the system hierarchy:
- Mission level -> system level -> subsystem level -> component level

At each level, the same processes execute but with different scope and detail.

**Exercise:** *Map each of the 17 processes to a feature in SpaceCDF. Which processes does the tool support directly? Which require human judgment?*

---

## 4. Lifecycle Phases and Review Gates (25 min)

### NASA Lifecycle Phases

*[Source: NPR 7120.5F Chapter 2; NASA SEH Chapter 3]*

| Phase | Name | Primary Activity | Exit Review |
|-------|------|-----------------|-------------|
| **Pre-A** | Concept Studies | Identify need, explore concepts | MCR |
| **A** | Concept & Technology Development | Develop requirements, mature technology | SRR/SDR |
| **B** | Preliminary Design & Tech Completion | Preliminary design, close budgets | PDR |
| **C** | Final Design & Fabrication | Detailed design, build hardware | CDR |
| **D** | Assembly, Integration & Test, Launch | Assemble, test, launch | TRR, ORR, FRR |
| **E** | Operations & Sustainment | Operate the mission | PLAR |
| **F** | Closeout | Decommission, lessons learned | DR |

**Key Decision Points (KDPs):** Go/no-go authority decisions between phases, lettered A through F. KDP-C for projects >$250M (USD) requires a Joint Confidence Level (JCL) analysis per NPR 7120.5.

### ECSS Lifecycle Phases

*[Source: ECSS-M-ST-10C Rev.1]*

| ECSS Phase | Name | Approximate NASA Equivalent |
|-----------|------|---------------------------|
| 0 | Mission Analysis / Needs Identification | Pre-A |
| A | Feasibility | A |
| B | Preliminary Definition (B1: system, B2: detailed) | B |
| C | Detailed Definition | C |
| D | Qualification & Production | D |
| E | Utilisation | E |
| F | Disposal | F |

**Important caveat:** The phase letters align but entry/exit criteria and review content differ between NASA and ECSS. They are **approximately equivalent**, not identical.

### Review Gates -- What Each Checks

| Review | Key Question | Evidence Required |
|--------|-------------|-------------------|
| **MCR** | Is the mission need justified? Is space the right answer? | Problem statement, stakeholders, alternatives analysis, ConOps draft |
| **SRR** | Are requirements complete, consistent, and traceable? | Requirements baseline, traceability matrix, risk register |
| **PDR** | Does the preliminary design meet requirements? | Design description, budget status (mass/power/cost), risk mitigation |
| **CDR** | Is the design complete and ready for fabrication? | Detailed drawings, analysis results, test plans, all budgets closed |
| **TRR** | Is the system ready for formal testing? | Test procedures, test facilities ready, acceptance criteria defined |
| **FRR** | Is everything ready for launch? | All tests passed, waivers documented, launch procedures verified |

**Exercise:** *In SpaceCDF, go to the Gate Review tab and examine the MCR exit criteria. Which criteria are auto-evaluated? Which require manual review?*

---

## 5. CDF Engineering Positions (15 min)

### Teaching Notes

In a CDF study, each engineering position owns a set of parameters and is responsible for their domain's design decisions. SpaceCDF supports 15 positions:

| Position | Responsibility | Key Parameters |
|----------|---------------|----------------|
| **Systems Engineer** | Overall architecture, budgets, margins, conflicts | Mass margin, power margin, all system-level budgets |
| **Mission Analyst** | Orbit design, coverage, ground station access | Altitude, inclination, eclipse fraction, contact time |
| **Payload Lead** | Instrument performance, data generation | GSD, data rate, pointing requirement |
| **Power Engineer** | Solar arrays, batteries, EPS, duty cycling | SA area, battery capacity, bus voltage |
| **AOCS Engineer** | Attitude sensors, actuators, pointing accuracy | Pointing accuracy, wheel momentum, sensor selection |
| **Thermal Engineer** | Temperature control, radiators, heaters | Max/min temp, radiator area, heater power |
| **Comms Engineer** | Link budget, transponder, antenna, licensing | Link margin, data rate, frequency band |
| **Propulsion Engineer** | Delta-V budget, thruster selection, propellant | Isp, propellant mass, total impulse |
| **Structures Engineer** | Primary structure, mechanisms, launch loads | Structure mass, natural frequency, margin of safety |
| **Cost Engineer** | WBS, CERs, schedule, risk-adjusted cost | Total cost, per-subsystem cost, launch cost |
| **Compliance Engineer** | ECSS standards, frequency licensing, export control | Standard applicability, filing status |
| **User Representative** | End-user needs, data product requirements | Data format, latency, accessibility |
| **Mission Operations** | Ground segment, ops concept, staffing | Contact schedule, automation level |
| **Ground Segment** | Ground stations, data processing pipeline | Station network, processing latency |
| **Software Engineer** | Flight software, FDIR, TC/TM interfaces | FSW architecture, command dictionary |

**Discussion prompt:** *Which positions would interact most frequently? Where do you expect conflicts?*

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| CDF | Concurrent multi-discipline design resolves conflicts in real-time |
| System-V | Left side decomposes; right side integrates; horizontal traceability |
| 17 Processes | Recursive at every level; grouped as Design, Realization, Management |
| Phases | Pre-A through F with KDP gates; ECSS phases approximately equivalent |
| Positions | Each owns a domain; conflicts arise at interfaces |

---

## Exercise (Tool Interaction)

**Duration:** 15 minutes

1. Open SpaceCDF and navigate through the workflow steps (Need -> Concept -> Requirements -> Design)
2. In the Design Dashboard, identify which KPI cards correspond to which engineering positions
3. Go to the Positions tab and review the key questions for your assigned position
4. Go to the Gate Review tab and examine the MCR exit criteria

**Worksheet 1.1:** Map the 17 processes to SpaceCDF features (provided in Learner's Workbook)
