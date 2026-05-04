# SpaceCDF Tool Redesign — Architecture Document

## Problem Statement

The tool has 37 components, 105 API endpoints, and 20+ tabs that grew
organically. Key issues:

1. **Navigation overload**: 20 tabs with no clear workflow path
2. **Disconnected data**: edits don't propagate; backends not wired to UI
3. **Missing System-V structure**: no system/subsystem requirement hierarchy
4. **No engineering budgets per level**: link, mass, cost, pointing, timing,
   data budgets exist but aren't structured per system/subsystem
5. **Mission type not threaded through**: comms missions see optical defaults
6. **Position Q&A not connected**: answers don't feed back into design

## Redesign Principles

### 1. Follow the System-V

The tool should follow the left side of the V-model:
```
Mission Need → Mission Requirements → System Architecture
  → System Requirements → Subsystem Design → Subsystem Requirements
    → Component Selection → Verification Planning
```

Each level articulates:
- **Boundaries** (what's in scope, what interfaces exist)
- **Requirements** (what must be achieved, SMART, traceable)
- **Budgets** (mass, power, cost, data, pointing, timing — allocated down)
- **Verification** (how each requirement will be verified, at what level)

### 2. Workflow-Driven Navigation (not tab soup)

Replace 20 tabs with **6 workflow phases**, each containing relevant tools:

```
Phase 0: Mission Definition
  - Mission Need (problem, stakeholders, objectives)
  - Mission Trade (space vs non-space, including constellation options)
  - Concept of Operations (architecture, phases, modes, data flow)

Phase A: Requirements & Architecture
  - Mission-Level Requirements (from objectives, SMART, editable)
  - Functional Decomposition (with ground segment functions)
  - System Architecture (system boundaries, interfaces)
  - Engineering Budgets: mission-level (mass, power, cost, ΔV)

Phase B: System Design
  - Orbit Selection (with spectrum/licensing constraints)
  - Subsystem Design (per-subsystem requirements + parametric sizing)
  - Equipment Selection (compatibility-checked, budget-tracked)
  - Engineering Budgets: system-level (per-subsystem breakdown)
  - Trade Studies (tabular, weighted, multi-criteria)

Phase C: Detailed Design
  - Component Selection (from KB, with interface verification)
  - Harness & Integration (PC/104, power bus, data bus)
  - Subsystem Budgets (per-component within each subsystem)
  - Verification Plan (per-requirement V&V matrix)

Cross-Cutting (available in all phases):
  - Position Q&A (answer questions, flag tensions)
  - Consistency Check (health score, margin enforcement)
  - Gate Review (phase exit criteria)
  - Change History (audit trail with undo)

Outputs (generated from current state):
  - ECSS Documents (MRD, TS, IRD, VP, SEMP, RMP, ConOps, Test Plan)
  - Regulatory Filings (ITU, IARU, RSSSA, Export, COPUOS, EOL)
  - Design Data (BOM, parametric data, spectrum analysis)
  - Simulator Config (SMO, FSW, MBSE)
```

### 3. Engineering Budgets at Every Level

```
Mission Level:
  Total mass allocation (from launcher) → System margin
  Total power generation → System power margin
  Total cost ceiling → Cost margin
  Total ΔV → Propulsion margin

System Level:
  Mass: payload + EPS + AOCS + TTC + OBC + thermal + structure + propulsion + harness
  Power: per-mode (safe, science, downlink, eclipse) with duty cycles
  Cost: bus HW + payload + I&T + software + launch + ground + ops + PM
  Data: generation rate → storage → downlink capacity → ground processing
  Pointing: per-axis RSS (sensor + actuator + alignment + thermal distortion)
  Link: EIRP - FSPL + G/T - noise = margin (per band: TTC + payload DL)

Subsystem Level (per subsystem):
  Mass: sum of components + margin
  Power: peak + average + duty-cycled
  Cost: COTS + custom + integration
  Interface: connector count, data bus bandwidth, power draw from EPS
```

### 4. Requirements Hierarchy

```
Mission Requirement (MR): "The system shall provide 10m GSD imagery"
  ↓ derives
System Requirement (SR): "The payload shall achieve 10m GSD at 500 km"
  ↓ derives
Subsystem Requirement (SSR): "The telescope aperture shall be ≥ 8 cm"
  ↓ derives
Component Specification: "Selected: XYZ Telescope, aperture 10 cm"
  ↓ verified by
Verification: "Analysis (Phase B), Test (Phase C)"
```

Each requirement has:
- Level (mission / system / subsystem)
- Parent requirement (traceability up)
- Child requirements (decomposition down)
- Verification method (A/T/R/I)
- Verification phase
- Current compliance status
- Responsible position

### 5. Frequency & Licensing Integration

Spectrum choice affects:
- Transponder selection (filtered by licensed band)
- Antenna selection (must match transponder band)
- Data rate achievable (band determines max throughput)
- Ground station selection (must support the band)
- Cost (commercial licensing fees vs free amateur)
- Data policy (amateur = open, commercial = proprietary)

This should be a **design constraint**, not just an export document.

### 6. Launch Integration

Launch choice affects:
- Mass allocation (launcher capacity → system mass budget)
- Volume constraint (deployer envelope → structure selection)
- Environmental loads (vibration, shock → structural design)
- Schedule (manifest date → development timeline)
- Cost (launch cost → cost budget)

This should feed back into the mass budget and structure sizing.

## Implementation Priority

### Immediate (fix what's broken):
1. Thread mission_type through mission trade analysis
2. Make position Q&A actually persist and work
3. Fix FunctionTreeView crash
4. Show tabular trade studies in trade panel
5. Show spectrum/licensing as design constraint, not just export
6. Remove duplicate exports (right panel vs center tab)
7. Default mission_type from requirements, not hardcoded

### Short-term (restructure navigation):
1. Replace 20 tabs with 6 workflow phases
2. Add system/subsystem requirement hierarchy
3. Add per-subsystem engineering budgets
4. Add link budget, pointing budget, data budget, timing budget
5. Connect launch selection to mass/volume budgets
6. Connect spectrum selection to equipment filtering

### Medium-term (deepen analysis):
1. Full V&V matrix with verification phases
2. Per-requirement compliance roll-up
3. Constellation design integrated into mission trade
4. Beyond-LEO integrated into orbit selection
5. Parametric data editor (user can tweak mass/cost fractions)
