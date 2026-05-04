# SpaceCDF Ultraplan — Comprehensive Issue Resolution

## Status as of 2026-05-04

24 specific issues identified from detailed user review. Each is catalogued
below with severity, effort estimate, dependencies, and resolution approach.

---

## Issue Catalogue

### Category A: Decision Support Inputs (broken/missing user controls)

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| A1 | Orbit advisor has no inputs (region, lifetime, mission type) | HIGH | 2h | TODO |
| A2 | Class advisor has no inputs, values don't flow to payload params | HIGH | 2h | TODO |
| A3 | RF/comms missions not considered (wide FOV, limb) | MED | 3h | TODO |
| A4 | Ground sensor + space relay architecture not modelled | MED | 2h | TODO |
| A5 | "Run Design" result not obviously visible (need to click Design step) | HIGH | 30min | TODO |

### Category B: ConOps & Architecture (fundamental model gap)

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| B1 | ConOps is power modes, not mission architecture diagrams | HIGH | 8h | TODO |
| B2 | Should show phases/modes as architecture schematics with data interfaces | HIGH | 8h | TODO |
| B3 | Power budget in wrong place (under budgets, not ConOps) | LOW | 1h | TODO |

### Category C: Requirements & Functions (editability + quality)

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| C1 | Functions can't be edited | HIGH | 3h | TODO |
| C2 | Tool should suggest, user approves/edits (not auto-generate silently) | HIGH | 4h | TODO |
| C3 | Consistency checking on accepted items | MED | 4h | TODO |
| C4 | Requirements not SMART — "operate at 500km" is HOW not WHAT | HIGH | 3h | TODO |
| C5 | Requirements should be editable with sanity checks | HIGH | 3h | TODO |
| C6 | Requirement non-compliance resolution workflow | MED | 3h | TODO |

### Category D: Interfaces & Conflicts (resolution workflow)

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| D1 | Interface conflicts: no way to resolve them | HIGH | 3h | TODO |
| D2 | Position questions: no support to help answer them | MED | 4h | TODO |
| D3 | Gate review: unclear how to resolve unmet criteria | MED | 3h | TODO |

### Category E: Equipment & Budgets (selection + custom design)

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| E1 | Equipment browser doesn't cover all needed equipment | MED | 4h | TODO |
| E2 | Equipment doesn't show requirement violations | HIGH | 3h | TODO |
| E3 | Option to design custom equipment (not just catalogue) | MED | 6h | TODO |
| E4 | Budgets don't visibly update when equipment selected | HIGH | 2h | TODO |
| E5 | Trade study between equipment selections | MED | 4h | TODO |

### Category F: Trade Studies & Optimization (completeness)

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| F1 | Trade studies/optimizer may not consider all factors | MED | 4h | TODO |

### Category G: Document Generation (ECSS DID compliance)

| # | Issue | Severity | Effort | Status |
|---|-------|----------|--------|--------|
| G1 | Generate ALL ECSS document templates (DIDs) | HIGH | 12h | TODO |
| G2 | DID compliance checking | MED | 6h | TODO |
| G3 | Option to override DID structure or select compliance level | LOW | 3h | TODO |

---

## Prioritised Resolution Phases

### Phase 1: Quick Wins (make existing features work properly)
*Estimated: 1 day*

- **A1**: Orbit advisor gets input fields (same pattern as MissionTradeView fix)
- **A2**: Class advisor gets input fields, values flow to RequirementsPanel
- **A5**: Auto-switch to Design step after "Run Design" completes
- **B3**: Move power mode profiles to engineering budgets, ConOps gets architecture focus
- **E4**: Equipment selection triggers reconvergence → budgets update visibly

### Phase 2: Requirements Quality (SMART requirements + editing)
*Estimated: 2 days*

- **C4**: Rewrite requirement generator — requirements describe WHAT not HOW
  - BAD: "The spacecraft shall operate at 500km" (that's a design choice)
  - GOOD: "The system shall provide 10m GSD imagery of the target region"
  - Interface reqs ARE specific: "The EPS shall provide 28V ± 2V to all subsystems"
- **C5**: Requirements editor: view all requirements, edit text/threshold/method,
  run sanity checks (SMART criteria: Specific, Measurable, Achievable, Relevant, Traceable)
- **C6**: Non-compliance resolution: for each RED requirement, show options
  (relax requirement, change design, accept risk, escalate to stakeholder)
- **C1**: Functions editable: add/remove/edit functions, re-link to requirements
- **C2**: Suggest-then-approve pattern: tool generates, shows "Accept / Edit / Reject"
  for each requirement, function, and design parameter

### Phase 3: ConOps as Architecture (not just power modes)
*Estimated: 3 days*

- **B1 + B2**: ConOps redesign as mission architecture tool:
  - Mission architecture diagram: space segment → ground segment → user with
    labelled data interfaces (instrument data, TM/TC, command, products)
  - Phase timeline: LEOP → commissioning → nominal → extended → disposal
  - Mode diagrams: for each mode, show which subsystems are active, data flow,
    pointing mode, power state
  - Architecture options: single sat vs constellation vs hosted payload
  - NOT a power budget tool (power profiles move to engineering budgets)

### Phase 4: Equipment & Budget Integration
*Estimated: 2 days*

- **E1**: Expand equipment browser to cover all subsystem needs (harness, thermal
  hardware, mechanisms, separation systems)
- **E2**: When browsing equipment, show which requirements it violates (red flags)
  and which it meets (green checks) — per-requirement compliance view
- **E3**: "Design Custom" option: when no COTS component fits, create a custom
  equipment spec with mass/power/cost/interface fields → feeds into design
- **E5**: Side-by-side equipment trade: select 2-3 candidates, compare against
  all requirements, show which is best overall

### Phase 5: Conflict Resolution & Decision Support
*Estimated: 2 days*

- **D1**: Interface conflict resolution workflow: for each conflict, show
  options (relocate component, add shielding, change orientation, accept risk),
  let user select resolution, record rationale
- **D2**: Position question support: for each question, show relevant parameters,
  highlight if they're in/out of range, suggest answer based on design state
- **D3**: Gate review resolution: for each RED criterion, show what's needed to
  turn it GREEN, link to the relevant step/decision, "Go fix this" button
- **A3**: RF/comms mission support: mission trade includes comms payloads,
  link budget as primary performance metric instead of GSD
- **A4**: Ground sensor + space relay architecture option

### Phase 6: Trade Study Completeness + ECSS Documents
*Estimated: 3 days*

- **F1**: Trade study framework: ensure all relevant parameters are considered
  (mass, power, cost, risk, TRL, heritage, interfaces, schedule, reliability)
- **G1**: ECSS DID document generator:
  - MRD (Mission Requirements Document) — ECSS-E-ST-10C Annex A
  - TS (Technical Specification) — ECSS-E-ST-10-06C
  - VP (Verification Plan) — ECSS-E-ST-10-02C [exists]
  - VCD (Verification Control Document) — ECSS-E-ST-10-02C Annex B [exists]
  - IRD (Interface Requirements Document) — ECSS-E-ST-10-24C
  - SEMP (SE Management Plan) — per NASA SEH Appendix J
  - RMP (Risk Management Plan) — ECSS-M-ST-80C
  - Tailoring Matrix — ECSS-S-ST-00-02C [exists]
  - ConOps document — per NASA SEH Appendix S
  - Test Plan — per ECSS-E-ST-10-03C
  - AIT Plan — per ECSS-E-ST-10-03C Annex
- **G2**: DID compliance checker: verify generated documents contain required sections
- **G3**: Compliance level selector: full ECSS / tailored ECSS / NASA-only / minimal

### Phase 7: Consistency & Intelligence Layer
*Estimated: 2 days*

- **C3**: Consistency checking engine:
  - Requirements consistent with objectives (no orphans)
  - Functions cover all requirements (no uncovered functions)
  - Interface matrix complete (all subsystem pairs have defined interfaces)
  - Design parameters satisfy all requirements (compliance matrix green)
  - Budget margins within policy for current phase
  - Equipment selections compatible (interface check)
  - ConOps modes cover all mission phases
  - Run on demand or after each change, flag inconsistencies

---

## Total Estimated Effort

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| Phase 1: Quick wins | 1 day | None |
| Phase 2: Requirements quality | 2 days | None |
| Phase 3: ConOps architecture | 3 days | Phase 2 |
| Phase 4: Equipment integration | 2 days | Phase 2 |
| Phase 5: Conflict resolution | 2 days | Phase 3, 4 |
| Phase 6: Documents + trades | 3 days | Phase 2 |
| Phase 7: Consistency | 2 days | All above |
| **TOTAL** | **~15 working days** | |

---

## Implementation Order

Start with Phase 1 (quick wins) — immediate visible improvement.
Then Phase 2 (requirements) — foundational for everything else.
Phases 3-6 can be partially parallelised.
Phase 7 last — it validates everything above.
