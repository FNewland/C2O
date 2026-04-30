# SpaceCDF Decision Support Framework — Architecture Document

## Purpose

This document defines how SpaceCDF supports the ~46 design decisions that
constitute a space mission lifecycle, from "what need does this serve?" through
"is it ready to fly?" It synthesizes NASA SEH (SP-2016-6105 Rev2), ECSS-M-ST-10C,
DoD 5000.02, and ESA CDF methodology into a unified decision framework.

## Core principle

**The tool presents decisions, not forms.** Each step in the design process
is a decision to be made, not a field to be filled. The tool shows:
1. What question is being answered
2. What drives the answer (objectives, constraints, higher-level decisions)
3. What alternatives exist (pre-populated where possible)
4. What each alternative costs downstream (mass, power, cost, schedule, risk)
5. Whether this is a) pick-and-go, b) trade study, or c) new design work
6. Who decides and how the rationale is captured

Gate review evidence accumulates naturally as decisions are made — not
assembled after the fact.

## Decision catalogue (46 decisions, 7 phases)

### Phase 0 / Pre-Phase A — Mission Definition (Gate: MCR/MDR)

| ID | Decision | Type | Question | Drives | Gate evidence |
|----|----------|------|----------|--------|---------------|
| 0.1 | Mission justification | a/b | Why does this mission need to exist? | Everything | Needs statement |
| 0.2 | Stakeholder identification | a/b | Who are the stakeholders and what do they need? | Objectives, ConOps | Stakeholder analysis |
| 0.3 | Objective prioritisation | b | Which objectives are primary/secondary/constraint? Needs vs wants? | Architecture, descope | Objectives hierarchy with MOEs |
| 0.4 | Solution modality | b | Is space the right answer? (AoA) | Everything below | AoA report with non-space alternatives |
| 0.5 | Mission concept(s) | b/c | What architecture concepts are feasible? | Orbit, size, cost | >=2 concept descriptions |
| 0.6 | Orbit/trajectory class | b | LEO/MEO/GEO/Lunar? SSO/polar? Altitude? | All subsystems | Trade study, trajectory analysis |
| 0.7 | Ground segment concept | b | Own stations vs commercial vs DSN? | Data latency, ops cost | Ground segment concept document |
| 0.8 | ConOps definition | b | What are the mission modes? How do we operate? | Power, thermal, AOCS, data sizing | ConOps (SEH Appendix S) |
| 0.9 | Technology assessment | b/c | What's heritage, what needs development? | Risk, cost, schedule | TRL assessment, AD² chart |
| 0.10 | Cost/schedule feasibility | b | Can we afford it in the required timeline? | Go/no-go (KDP-A) | ROM cost estimate |

### Phase A — Concept & Technology Development (Gate: SRR/PRR)

| ID | Decision | Type | Question | Drives | Gate evidence |
|----|----------|------|----------|--------|---------------|
| A.1 | Level 1 requirements | b/c | What are the system requirements? (shall statements with MOPs) | All flowdown | Requirements document |
| A.2 | System architecture | b | How do we decompose the system? (PBS/WBS) | Interfaces, make/buy | Architecture trade study |
| A.3 | Functional decomposition | c | How do functions flow? How complex? | Derived requirements | FFBD, N² diagrams |
| A.4 | Payload selection | b/c | Build, buy, or reuse? How well does it fit the need? | Mass, power, data, cost, TRL | Payload trade study, gap analysis |
| A.5 | Bus selection | a/b | Existing platform or new development? | Structure, EPS, AOCS, timeline | Make/buy/reuse analysis |
| A.6 | Preliminary budgets | b | Mass, power, data, ΔV allocations with margins? | Subsystem design envelopes | Budget tables (30%+ margin at SRR) |
| A.7 | Acquisition strategy | b | How do we procure? ITAR/export considerations? | Schedule, cost, partnerships | Preliminary acquisition plan |
| A.8 | Safety/hazard ID | b | What can go wrong? (MIL-STD-882E) | Safety requirements, SPF policy | Preliminary Hazard List |

### Phase B — Preliminary Design (Gates: SDR, PDR)

| ID | Decision | Type | Question | Drives | Gate evidence |
|----|----------|------|----------|--------|---------------|
| B.1 | Physical architecture | c | Product tree — what are we building? | AIT plan, procurement | PBS, equipment list |
| B.2 | L2-L3 requirements | c | Subsystem requirements with flowdown | Subsystem design envelopes | Specs with traceability |
| B.3 | Component selection (per subsystem) | a/b | Which specific COTS component? Fit-gap analysis? | Interfaces, qualification | Per-subsystem trade studies |
| B.4 | Margin allocation | b | What margins at this phase? (ECSS margin philosophy) | Design freedom, risk | Budget tables (20% at PDR) |
| B.5 | Redundancy architecture | b | Where to add redundancy? (FMECA-driven) | Mass, cost, reliability | FMEA/FMECA, reliability block diagram |
| B.6 | Interface freeze | c | All ICDs baselined and controlled? | Integration sequence, change control | Signed ICDs |
| B.7 | AIT approach | b | Protoflight vs prototype vs digital twin? | Cost, schedule, risk | AIT plan, model philosophy |
| B.8 | Propulsion selection | b | Chemical, electric, none? Specific thruster? | Mass, ΔV, transfer time | Propulsion trade study |
| B.9 | Comms architecture | b | Band, antenna, relay vs direct, data protocol? | Link budget, mass, power, ground | Comms trade study |
| B.10 | AOCS mode design | c | Sensor/actuator suite, mode transitions? | Pointing budget, mass, power | AOCS mode table, error budget |
| B.11 | Thermal architecture | b/c | Passive, active, heat pipes, phase change? | Mass, power, complexity | Thermal model results |
| B.12 | Software architecture | c | Framework, onboard vs ground allocation? | Dev effort, V&V approach | SW architecture document |
| B.13 | Verification approach | b | Test/analysis/inspection/demo per requirement? | AIT plan, facility needs, cost | Verification plan |
| B.14 | Updated cost estimate | b | Parametric + vendor-based estimate | Budget confirmation (KDP-B) | Cost estimate at confidence level |

### Phase C — Final Design (Gate: CDR)

| ID | Decision | Type | Question | Drives | Gate evidence |
|----|----------|------|----------|--------|---------------|
| C.1 | Design complete to build? | c | All drawings, parts lists, tolerance analysis? | Manufacturing | Drawing package, DML |
| C.2 | Interfaces controlled? | a | All ICDs signed, EMC analysis done? | Integration | Interface verification matrix |
| C.3 | Parts qualified? | b | Radiation hardness, screening, ITAR? | Shielding mass, schedule | Approved parts list |
| C.4 | Requirements verifiable? | a | Complete verification matrix? | V&V completeness | VCD (ECSS) / VRM (NASA) |
| C.5 | SW detailed design? | c | Unit-level specs, coding standards? | Build, test | SW DD, test plan |
| C.6 | Safety mitigated? | b | All hazards addressed per MIL-STD-882E? | Safety-critical items | Updated hazard analysis |

### Phase D — AIT & Launch (Gates: SIR, TRR, ORR, FRR)

| ID | Decision | Type | Question | Drives | Gate evidence |
|----|----------|------|----------|--------|---------------|
| D.1 | System meets requirements? | a | Test results vs verification matrix? | Launch auth | Test reports, VCNs |
| D.2 | NCRs dispositioned? | b | All anomalies resolved or accepted? | Risk acceptance | NCR log, MRB minutes |
| D.3 | Ground segment ready? | a | Network compatible, procedures validated? | Ops capability | Ground test report |
| D.4 | Ops team ready? | a | Training complete, sims passed? | Mission success | Training records |
| D.5 | Launch commit? | a | FRR criteria met? | Mission execution | FRR certificate |

### Phase E — Operations (Gates: PLAR, CERR)

| ID | Decision | Type | Question | Drives | Gate evidence |
|----|----------|------|----------|--------|---------------|
| E.1 | Commissioning complete? | a | IOT results vs predictions? | Routine ops | Commissioning report |
| E.2 | Performance nominal? | a | Degradation trending within bounds? | Remaining life | Trend reports |
| E.3 | Mission extension? | b | Resources remaining vs science return vs cost? | Extended ops plan | Extension proposal |

### Phase F — Disposal (Gate: DR/ELR)

| ID | Decision | Type | Question | Drives | Gate evidence |
|----|----------|------|----------|--------|---------------|
| F.1 | Disposal method? | b | Deorbit, graveyard, re-entry? | Compliance | Disposal plan |
| F.2 | Passivation complete? | a | All stored energy discharged? | Debris risk | Passivation log |
| F.3 | Lessons learned? | a | What did we learn for next time? | Future missions | LL database |

## Decision support system design

### For each decision, the tool provides:

```
┌─────────────────────────────────────────────────┐
│ DECISION B.3: Component Selection — EPS Battery │
│ Phase B · PDR gate · Trade study needed (type b) │
├─────────────────────────────────────────────────┤
│                                                 │
│ QUESTION: Which battery meets the power storage │
│ requirement derived from the ConOps eclipse mode?│
│                                                 │
│ DRIVEN BY:                                      │
│ ├─ Objective: "3-year mission lifetime"         │
│ ├─ Requirement: REQ-PWR-002 "Battery capacity   │
│ │   >= 91 Wh at 30% DoD" (from function F-005)  │
│ ├─ ConOps: Eclipse mode = 30W × 35 min          │
│ └─ Constraint: mass allocation <= 0.8 kg        │
│                                                 │
│ ALTERNATIVES:        Fit    Mass   Capacity  TRL│
│ ┌────────────────────────────────────────────┐  │
│ │ GomSpace BP-X      92%    0.25   76 Wh    9  │ ← gap: 15 Wh below need
│ │ GomSpace BP4×2     100%   0.50   77 Wh    9  │ ← meets, but 2× mass
│ │ SAFT MP176065      100%   0.60   96 Wh    8  │ ← meets with margin
│ │ Custom Li-ion      100%   0.45   95 Wh    5  │ ← TRL risk
│ └────────────────────────────────────────────┘  │
│                                                 │
│ FIT-GAP ANALYSIS (selected: SAFT MP176065):     │
│ ├─ Capacity: 96 Wh vs 91 Wh need → 5% margin ✓│
│ ├─ Mass: 0.60 kg vs 0.80 allocation → fits ✓   │
│ ├─ Cycle life: 30k vs 16k needed → 87% margin ✓│
│ ├─ Voltage: 28.8V vs 28V bus → need regulator! │
│ ├─ Temperature: -20/+60°C vs -10/+50°C → ✓    │
│ └─ Heritage: Sentinel-2, PROBA-3 → strong      │
│                                                 │
│ DOWNSTREAM CONSEQUENCES:                        │
│ ├─ EPS mass: +0.15 kg (regulator for 28.8V)    │
│ ├─ Power margin: drops from 44% to 38%         │
│ ├─ Interface: new ICD needed for voltage reg    │
│ └─ Verification: requires charge/discharge test │
│                                                 │
│ DECISION: [Select] [More analysis] [Defer]      │
│ Authority: Power Engineer · Approved by: SE     │
│ Rationale: ________________________________     │
└─────────────────────────────────────────────────┘
```

### Decision maturity tracking

Each decision has a maturity level that progresses through the lifecycle:

| Maturity | Meaning | Typical phase |
|----------|---------|---------------|
| Open | Decision not yet addressed | Pre-Phase A |
| Explored | Alternatives identified, not evaluated | Phase A |
| Traded | Trade study complete, recommendation made | Phase A/B |
| Decided | Selected by decision authority, rationale recorded | Phase B |
| Baselined | Under configuration control, change requires CCB | Phase B/C |
| Verified | Implementation verified against the decision | Phase D |
| Validated | Stakeholder confirms the decision met their need | Phase E |

### How verification traces back to design decisions

```
Stakeholder Need: "Farmers need crop health data"
  └─ Objective: "Weekly 10m multispectral imagery"
      └─ Function: "Acquire multispectral imagery" (F-001)
          └─ Requirement: "GSD <= 10m at nadir" (REQ-PL-001)
              └─ Design Decision: "15cm aperture Ritchey-Chrétien" (B.3/PL)
                  └─ Verification: "Analysis — raytrace model + MTF measurement"
                      └─ Verification Status: PASS (MTF > 0.3 at Nyquist)
                          └─ Validation: "Test image resolves 10m field boundaries" ✓
```

The right side of the V is not separate — it's the mirror image. Each
requirement written on the way down creates a verification obligation.
Each verification closure feeds back to confirm the objective is met.
Each objective confirmation feeds back to validate the stakeholder need.

### Conflict taxonomy (5 levels)

| Level | Example conflict | How tool detects it |
|-------|-----------------|-------------------|
| Stakeholder | Funder wants <5M, PI wants 6 instruments | Budget vs instrument count |
| Objective | "Daily global" vs "10m GSD" vs "<5 MEUR" | Coverage-resolution-cost triangle |
| Requirement | "Pointing ≤0.1°" vs "mass ≤12 kg" | AOCS mass exceeds allocation |
| Design | SA panel blocks star tracker FOV | Interface matrix spatial conflict |
| Verification | "Test" requires facility that doesn't exist | V&V plan vs facility availability |

### Technical Performance Measures (TPMs)

The tool should track TPMs — the key technical metrics that indicate whether
the design is converging or diverging. TPMs are monitored continuously:

| TPM | Threshold | Current | Margin | Trend |
|-----|-----------|---------|--------|-------|
| Dry mass | ≤ 12 kg | 9.6 kg | +20% | Stable |
| Power margin | ≥ 20% | 38% | OK | Improving |
| Link margin | ≥ 3 dB | 7.7 dB | OK | Stable |
| Pointing accuracy | ≤ 0.1° | 0.1° | 0% | At limit |
| Mission reliability | ≥ 0.9 | 0.65 | -28% | **Concern** |

The trend column is critical — a TPM that's within threshold but degrading
each iteration signals a problem before it becomes a margin violation.

### FMECA integration

Design decisions should be informed by failure analysis:
- Each function has failure modes (from FMECA)
- Each failure mode has severity and likelihood
- Redundancy decisions (B.5) are driven by which single-point failures
  are unacceptable
- The tool should show: "If this component fails, what functions are lost?
  What is the mission impact? Is there a backup?"

### How the ESA CDF session structure maps to this framework

| CDF Session | SpaceCDF Decision Support |
|-------------|--------------------------|
| Sessions 1-2: Mission definition | Decisions 0.1-0.3 + stakeholder panel |
| Sessions 3-5: Architecture | Decisions 0.4-0.6 + A.2 + trade studies |
| Sessions 6-10: Subsystem sizing | Decisions A.4-A.6 + B.3-B.11 (prelim) |
| Sessions 11-14: Convergence | All agents converge + conflict resolution |
| Sessions 15-16: Costing & wrap-up | Decisions 0.10 + B.14 + gate review |

Each CDF session maps to a cluster of decisions. The tool should know
which decisions are active for the current session/phase and present
them in the right order.

## Implementation priority

1. **Decision Engine** — the core data model and service that manages the
   46 decisions, their maturity, dependencies, and evidence accumulation

2. **Decision cards in UI** — replacing parameter forms with structured
   decision presentations (question, alternatives, fit-gap, consequences)

3. **Ground segment trade** — first concrete decision support module
   (downlink architecture, station network, data latency vs cost)

4. **Component fit-gap analysis** — second module (requirement vs
   component capability, gap identification, downstream consequence)

5. **TPM tracking with trends** — continuous monitoring of key metrics

6. **Verification traceability** — right-side-of-V wiring from requirement
   through test to objective confirmation
