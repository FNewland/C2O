# SpaceCDF Ultraplan 6 — System-V Redesign

## Status: 2026-05-05

This plan addresses a comprehensive redesign following the System-V model rigorously, based on detailed user feedback. The tool must follow the decomposition hierarchy faithfully: Need → Mission Architecture → System Architecture → Subsystem Design → Component Selection, with engineering budgets, requirements, and interfaces defined and rolled up at each level.

---

## Fundamental Architecture Issues Identified

### Current State (what's wrong):
1. **Flat structure**: All tabs visible simultaneously regardless of design maturity
2. **Missing levels**: No mission-level block diagram editor; no system-level block diagrams per segment
3. **Requirements not persistent**: Generated requirements lost on tab navigation
4. **Budgets not layered**: Engineering budgets exist but don't roll up through levels
5. **Testing not structured**: V&V matrix exists but not mapped to test levels (unit/system/mission)
6. **No project management**: No risk matrix, Gantt chart, WBS, or PM role
7. **Interfaces at wrong level**: N² matrix exists but only at subsystem level, not mission/system
8. **Exports not in Word**: All exports are JSON, not editable Word documents
9. **Link budget incomplete**: Only downlink; needs full up/down with all terms
10. **Session state not saveable/loadable**: No persistence between browser sessions
11. **ConOps not interactive**: Static SVG, not an editable diagram with standard symbols

### Target State (what's needed):
The tool must follow this exact decomposition:

```
Level 0: Mission Need & Trade
  → Define problem, stakeholders, objectives
  → Space vs non-space trade
  → Output: Mission-level requirements (MR-)

Level 1: Mission Architecture
  → EDITABLE block diagram: Space segment, Ground segment, User segment, External systems
  → Standard symbols: antennas, sensors, ground vehicles, aircraft, GNSS, relay sats
  → Interfaces between segments defined
  → Mission phases: Pre-A through F, plus LEOP/commissioning/nominal/disposal
  → Output: Segment-level interface requirements (MIR-)

Level 2: System Architecture (per segment)
  → Block diagram per segment (space: platform+payload; ground: station+MCC+processing)
  → Architecture options with trade studies
  → System-level engineering budgets (estimated)
  → Output: System requirements (SR-) allocated to systems

Level 3: Subsystem Design
  → Architecture selection per subsystem (EPS, AOCS, TTC, etc.)
  → Equipment selection from KB
  → Subsystem-level engineering budgets (refined, measured)
  → Output: Subsystem requirements (SSR-) + component specs

Level 4: Integration & Verification
  → Budgets roll up: component → subsystem → system → mission
  → Testing: unit → subsystem → system → environmental → end-to-end
  → Risk tracking + schedule (Gantt)
  → Document generation (Word format)
```

---

## Issue Catalogue (from user feedback)

### Category A: Session & State Management
| # | Issue | Severity |
|---|-------|----------|
| A1 | Cannot save and reload a session (no persistence between browser visits) | CRITICAL |
| A2 | Requirements not stored when validated — lost on tab change | CRITICAL |
| A3 | Still generating "HOW" requirements like "operate at 500km" | HIGH |

### Category B: Mission Architecture (Level 1)
| # | Issue | Severity |
|---|-------|----------|
| B1 | ConOps diagram not editable — need drag/drop box/line editor | HIGH |
| B2 | No standard symbols (antennas, sensors, vehicles, GNSS, relay) | HIGH |
| B3 | Missing external systems (GNSS, aircraft, ground vehicles, ground sensors) | HIGH |
| B4 | Boxes and lines overlap — need layout checking | MED |
| B5 | Architecture diagram should drive what systems need defining | HIGH |
| B6 | Mission phases should include Phase A-F not just LEOP/ops/disposal | MED |
| B7 | Data pipeline should be editable | MED |

### Category C: System Architecture (Level 2)
| # | Issue | Severity |
|---|-------|----------|
| C1 | No system-level block diagram per segment | HIGH |
| C2 | Systems architecture should allow custom options beyond catalogue | HIGH |
| C3 | System requirements not clearly allocated to systems | HIGH |
| C4 | Need ground segment architecture block diagram | HIGH |
| C5 | Need sensor/vehicle segment if applicable | MED |

### Category D: Requirements
| # | Issue | Severity |
|---|-------|----------|
| D1 | Requirement types needed: Functional, Performance, Interface, Regulatory, Process/Constraint | HIGH |
| D2 | "Link" function type should be "Communications" | LOW |
| D3 | No way to connect a requirement to a function in the UI | HIGH |
| D4 | Long mission statements should auto-split into multiple requirements | MED |
| D5 | Requirements not persisted after generation | CRITICAL |
| D6 | Mission requirements should drive system requirements which drive subsystem requirements (traceability chain) | HIGH |

### Category E: Engineering Budgets
| # | Issue | Severity |
|---|-------|----------|
| E1 | Need complete link budget (up AND downlink, all terms, per ECSS-E-ST-50-05C) | HIGH |
| E2 | Power budget: generation + average + peak per mode | MED |
| E3 | Timing budget: timestamp accuracy for time-critical data | MED |
| E4 | Pointing budget: knowledge AND control based on sensor+actuator selection | HIGH |
| E5 | Delta-V budget: orbit + manoeuvre selection driven | MED |
| E6 | Volume budget: from selected equipment vs structure envelope | MED |
| E7 | Mass budget: with margins per design maturity stage (configurable via parametric) | HIGH |
| E8 | Budgets estimated at mission level, refined at system, set at subsystem, rolled up | HIGH |

### Category F: Interfaces
| # | Issue | Severity |
|---|-------|----------|
| F1 | Interfaces at mission segment level (between segments) | HIGH |
| F2 | Interfaces at system level (between subsystems) — exists but only visible after system design | MED |
| F3 | Interfaces only visible once the level of work is done | MED |

### Category G: Verification & Test
| # | Issue | Severity |
|---|-------|----------|
| G1 | Testing: unit, system, mission, environmental, end-to-end, commissioning | MED |
| G2 | May need to be repeated at different levels | LOW |
| G3 | V&V matrix should map to test levels | MED |

### Category H: Project Management (NEW)
| # | Issue | Severity |
|---|-------|----------|
| H1 | No risk matrix (5x5 with tracking) | HIGH |
| H2 | No project Gantt chart / schedule | HIGH |
| H3 | No Work Breakdown Structure (WBS) / work packages | HIGH |
| H4 | No project management role/position | HIGH |
| H5 | Need to track risks and schedule | HIGH |

### Category I: Equipment & Cost
| # | Issue | Severity |
|---|-------|----------|
| I1 | Equipment browser visible too early (before subsystem design) | MED |
| I2 | Cost estimation should be editable and use selected component costs | MED |
| I3 | Margins should be configurable by design maturity (off-the-shelf vs new) | MED |

### Category J: Exports & Documents
| # | Issue | Severity |
|---|-------|----------|
| J1 | Exports should be in Word format (editable) not just JSON | HIGH |
| J2 | Still 2 export buttons doing different things | MED |
| J3 | Exported documents should include ALL relevant tool information | MED |
| J4 | All info from ConOps, mission need, architecture should flow into documents | MED |

### Category K: UI/UX
| # | Issue | Severity |
|---|-------|----------|
| K1 | Position questions should be answerable from Positions tab (not just Q&A) | MED |
| K2 | Levels of work should be progressive (unlock next level when previous complete) | HIGH |
| K3 | Engineering budgets only visible when relevant level reached | MED |

---

## Redesigned Tool Structure

### Progressive Disclosure (unlock levels sequentially):

```
LEVEL 0: MISSION NEED (always visible)
├── Problem statement
├── Stakeholders  
├── Objectives (with measurable criteria)
├── Mission trade (space vs non-space)
└── GATE: MCR exit criteria met → unlock Level 1

LEVEL 1: MISSION ARCHITECTURE (unlocked after MCR)
├── Interactive architecture diagram (editable boxes, lines, symbols)
│   ├── Space segment (with subsystems)
│   ├── Ground segment (with elements)
│   ├── User segment
│   ├── External systems (GNSS, other sats, aircraft, vehicles, sensors)
│   └── Interfaces between segments (labelled, typed)
├── Mission phases (Pre-A through F + operational phases)
├── ConOps (editable data pipeline, modes)
├── Mission-level engineering budgets (estimated)
├── Mission-level requirements (MR-)
├── Mission-level interface requirements (MIR-)
└── GATE: SRR exit criteria met → unlock Level 2

LEVEL 2: SYSTEM ARCHITECTURE (unlocked after SRR, per segment)
├── System block diagram per segment
│   ├── Space: Platform subsystems + Payload
│   ├── Ground: Station + MCC + Processing
│   └── Other segments as needed
├── Architecture options + trade studies
├── System requirements (SR-) allocated per system
├── System interfaces (between subsystems within a segment)
├── System-level engineering budgets (refined)
└── GATE: PDR exit criteria met → unlock Level 3

LEVEL 3: SUBSYSTEM DESIGN (unlocked after PDR)
├── Subsystem architecture selection (per subsystem)
├── Equipment selection from KB
├── Subsystem requirements (SSR-)
├── Subsystem-level budgets (set, from actual equipment)
├── Interface specifications (detailed: pinouts, protocols, voltages)
└── Roll-up to system and mission levels

LEVEL 4: VERIFICATION & INTEGRATION
├── V&V matrix (unit/subsystem/system/mission/environmental/E2E)
├── Test specifications (from launch vehicle ICD)
├── Risk matrix (5x5, tracked, mitigated)
├── Schedule (Gantt chart with milestones)
├── WBS / work packages
├── Document generation (Word format)
└── Gate reviews (MCR/SRR/PDR/CDR/TRR/FRR)

CROSS-CUTTING (available at all levels):
├── Position Q&A (answerable from both tabs)
├── Change audit trail
├── Cost estimation (editable, component-aware)
├── Consistency checker
├── Optimizer (only at appropriate level)
└── Design state bar (stale detection)
```

---

## New Positions Needed

| Position | Responsibility |
|----------|---------------|
| **Project Manager** | Schedule, WBS, risk, budget tracking, reviews |
| (existing 15 positions) | As defined |

---

## Implementation Phases

### Phase 1: State Persistence & Requirements Storage (CRITICAL)
- Save/load session state to browser localStorage + backend
- Requirements persist in designStore (not regenerated on tab change)
- Fix "HOW" requirement filtering (reject altitude as requirement)
- Fix requirement-function linking in UI

### Phase 2: Progressive Level Unlocking
- Restructure App.tsx: levels 0-4 replace flat tabs
- Each level unlocks when previous level's gate criteria met
- Equipment browser only visible at Level 3+
- Interfaces only visible at appropriate level

### Phase 3: Interactive Architecture Diagram Editor
- Drag/drop boxes with standard symbols
- Lines between boxes with labels and direction
- External systems (GNSS, aircraft, sensors)
- Layout collision detection
- Architecture drives what systems need defining

### Phase 4: System-Level Block Diagrams
- Per-segment block diagram (space, ground, sensors)
- Custom architecture options beyond catalogue
- System requirements allocated to systems
- System-level interfaces

### Phase 5: Complete Engineering Budgets
- Full link budget (up + down)
- Power (generation/average/peak per mode)
- Pointing (knowledge + control)
- Delta-V, volume, mass with configurable margins
- Roll-up through levels

### Phase 6: Project Management
- Risk matrix (5x5, interactive, tracked)
- Gantt chart with milestones and dependencies
- WBS with work packages
- Project Manager position

### Phase 7: Document Export (Word format)
- python-docx for Word generation
- All tool data flows into documents
- Consolidate to single export location
- Templates per document type (MRD, TS, VP, etc.)

---

## Estimated Effort

| Phase | Effort | Priority |
|-------|--------|----------|
| Phase 1: Persistence & Requirements | 8h | CRITICAL |
| Phase 2: Progressive Levels | 12h | HIGH |
| Phase 3: Architecture Diagram Editor | 16h | HIGH |
| Phase 4: System Block Diagrams | 8h | HIGH |
| Phase 5: Engineering Budgets | 12h | HIGH |
| Phase 6: Project Management | 12h | MEDIUM |
| Phase 7: Word Documents | 8h | MEDIUM |
| **TOTAL** | **~76h** | |

---

## Research Needed

1. **Link budget spreadsheets**: Research complete up/down link budget templates (CCSDS 401.0, ESA link budget handbook) for full implementation
2. **Interactive diagram editors**: Research React-based diagram libraries (React Flow, mxGraph, JointJS) for mission architecture editor
3. **Gantt chart libraries**: Research React Gantt components (frappe-gantt, dhtmlx-gantt, gantt-task-react)
4. **Word document generation**: python-docx templates for ECSS DIDs
5. **Risk matrix standards**: ISO 31000, NPR 8000.4 for risk register structure

---

## Key Design Principles

1. **Progressive disclosure**: Don't show Level 3 tools until Level 2 is done
2. **Requirements flow DOWN**: Mission → System → Subsystem (never skip levels)
3. **Budgets roll UP**: Component → Subsystem → System → Mission
4. **Interfaces at every boundary**: Mission/system/subsystem boundaries all have interface requirements
5. **Everything persists**: No data lost on tab change, page refresh, or session restart
6. **Everything traces**: Every requirement traces up (to need) and down (to verification)
7. **Everything is editable**: No read-only displays for things the user should control
8. **Documents capture everything**: Exports include all tool state relevant to that document
