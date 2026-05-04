# SpaceCDF Implementation Plan — Recorded for Future Sessions

## Priority Order

1. **Tier 2 completion** (this session)
2. **Tier 3 architecture** (next session)
3. **Tier 4 deepening** (following session)
4. **Course materials production** (parallel track)

---

## Tier 2 Remaining (6 items) — Complete Now

### T2.1: Spectrum Bands as Design Constraint
**What**: When user selects a license type (amateur/experimental/commercial) and mission type, the equipment browser should ONLY show transponders and antennas compatible with available bands. Spectrum choice should also set the ground station requirement.

**Implementation**:
- Add license_type selector to RequirementsPanel (amateur/experimental/commercial)
- On change, call `GET /api/lifecycle/spectrum/bands?mission_type=X&license_type=Y`
- Store available bands in designStore
- EquipmentBrowser filters transponders/antennas to only show matching bands
- Display available bands summary in a comms section card

**Files**: RequirementsPanel.tsx, EquipmentBrowser.tsx, designStore.ts

### T2.2: Parametric Data Interactive Editor
**What**: Users can view AND edit the mass fractions, cost fractions, power duty cycles used by the sizing agents. Changes should trigger redesign.

**Implementation**:
- New component `ParametricEditor.tsx` — tabular editor for each data set
- Loads from `GET /api/lifecycle/parametric-data`
- User edits values in table cells
- Edited values stored in designStore as overrides
- On "Apply", mark design as stale
- Show source citations alongside each value

**Files**: New ParametricEditor.tsx, designStore.ts (add parametricOverrides)

### T2.3: Duty Cycle Display
**What**: Show the power mode duty cycle breakdown in the dashboard/power section, with per-mode power draw and orbit-average calculation.

**Implementation**:
- Call `POST /api/lifecycle/duty-cycles` with mission config
- Display as table: Mode | Power (W) | Duty (%) | Orbit-Avg (W)
- Show total orbit-average and SA power needed
- Add to BudgetComparison or as separate card in dashboard

**Files**: BudgetComparison.tsx or new DutyCycleCard.tsx, MissionDashboard.tsx

### T2.4: ECSS Margin Enforcement Display
**What**: Show per-domain margin status vs ECSS policy for current phase. Red/amber/green indicators.

**Implementation**:
- Call `GET /api/ecss/margins/{study_id}` after design run
- Display as table: Domain | Required | Actual | Status | Standard
- Color-code: green (meets), amber (below policy but positive), red (negative)
- Add to dashboard or compliance tab

**Files**: New MarginEnforcementCard.tsx, MissionDashboard.tsx or ComplianceMatrix.tsx

### T2.5: Equipment Needs Filtering
**What**: EquipmentBrowser sidebar should highlight which categories are NEEDED (required vs optional) based on mission requirements.

**Implementation**:
- Call `GET /api/engineering/equipment/needs/{study_id}` on browser open
- Mark each sidebar category: green dot (required), grey dot (optional), hidden (not needed)
- Show reason text on hover ("Pointing < 0.1° requires star tracker")
- Optionally hide non-needed categories or show them greyed out

**Files**: EquipmentBrowser.tsx

### T2.6: Launch Provider Interactive Selector
**What**: Interactive panel showing available launch providers filtered by spacecraft mass/size, with pricing and deployer compatibility. Selection sets mass allocation.

**Implementation**:
- Load from `GET /api/lifecycle/parametric-data` (launch_providers section) or load YAML directly
- Filter by selected structure size and total mass estimate
- Show: provider, vehicle, price, capacity, lead time, deployer compatibility
- "Select" button sets the mass allocation in designStore (which updates margin)
- Show environmental test levels from selected vehicle

**Files**: New LaunchSelector.tsx or add to ExportsPanel, designStore.ts

---

## Tier 3 Architecture Plan (next session)

### T3.1: System-V Requirement Hierarchy
**Goal**: Requirements exist at mission, system, and subsystem levels with traceability.

**Data model change** (requirements.py):
```python
class Requirement:
    level: str  # "mission" | "system" | "subsystem"
    parent_id: str | None  # traces up to parent requirement
    children_ids: list[str]  # derived requirements below
    system_boundary: str  # which system/subsystem owns this
    verification_method: str  # A/T/R/I
    verification_phase: str  # phase_b / phase_c / phase_d
    verification_level: str  # unit / subsystem / system
```

**Frontend**: Requirements tree view (expandable hierarchy), filterable by level.

### T3.2: Per-Subsystem Engineering Budgets
**Goal**: Mass/power/cost allocated DOWN to subsystems, with per-subsystem margins.

**Implementation**:
- Backend: EngineeringBudget model already has `lines` (per-subsystem)
- Frontend: Budget breakdown card shows per-subsystem allocation AND roll-up
- Each subsystem has: allocated_mass, achieved_mass, margin_%
- System total = sum of subsystem allocations + system margin

### T3.3: Link Budget Tool
**Goal**: Interactive link budget calculator (not just agent output).

**Implementation**:
- New LinkBudgetTool.tsx with inputs: TX power, antenna gain, frequency, range, modulation, coding, atmospheric loss, pointing loss, implementation losses
- Computes: EIRP, FSPL, received power, C/N0, Eb/N0, margin
- Shows each term as a waterfall/cascade
- References ECSS-E-ST-50-05C

### T3.4: Pointing Budget
**Goal**: RSS error tree for pointing accuracy.

**Implementation**:
- Inputs: sensor accuracy, actuator accuracy, alignment knowledge, thermal distortion, jitter
- RSS combination: total = sqrt(sum of squares)
- Show as tree/table with per-contributor value
- Compare to requirement

### T3.5: Data Budget
**Goal**: Data pipeline budget from generation to user delivery.

**Implementation**:
- Generation rate (from payload specs × duty cycle)
- Onboard storage capacity and fill rate
- Downlink capacity per pass (from link budget × contact time)
- Ground processing time
- End-to-end latency
- Show as flow diagram with rates at each stage

### T3.6: Verification Matrix
**Goal**: Per-requirement V&V assignment.

**Implementation**:
- Each requirement gets: verification method (Analysis/Test/Review/Inspection)
- Verification phase (B/C/D/E)
- Verification level (unit/subsystem/system/mission)
- Status (not started / in progress / complete / waived)
- Responsible position
- Display as matrix: requirement rows × verification columns

### T3.7: Spectrum as Design Constraint
**Goal**: Band selection constrains equipment choices throughout the tool.

**Implementation**:
- `requirements.comms.license_type` drives band availability
- Band availability filters transponder + antenna options in equipment browser
- Band selection sets ground station requirements
- Data rate achievable limited by band characteristics

### T3.8: Launch as Design Constraint
**Goal**: Launch vehicle selection constrains mass, volume, environment.

**Implementation**:
- `requirements.launch.provider` sets:
  - Mass allocation (updates system mass budget)
  - Volume envelope (checks structure fit)
  - Environmental qualification levels (vibration, shock, thermal)
  - Deployer type required
  - Schedule milestones

---

## Tier 4 Deepening Plan (following session)

### T4.1: CubeSat Structure CER Fix
- Replace mass-fraction CER with COTS lookup (structure mass = selected frame mass from KB)
- When no frame selected, use form-factor table (1U=0.2kg, 3U=0.35kg, 6U=0.7kg)

### T4.2: Deep-Space AOCS Model
- Add interplanetary orbit type detection
- Use solar radiation pressure as primary disturbance (not gravity gradient)
- Scale wheel momentum for deep-space (much less than LEO)
- Reference: MarCO used BCT XACT (2.19 kg total AOCS for 14 kg spacecraft = 15.6%)

### T4.3: CubeSat Cost Model
- Replace SSCM-style CERs with CubeSat-specific model
- Anchor to known COTS pricing from KB
- Cost = sum(selected_component_costs) + I&T(12%) + SW(8%) + Launch + Ground + Ops
- When no components selected, use class-based estimate from cost_fractions

### T4.4: Navigation Redesign
- Replace 20+ tabs with 6 workflow phases (collapsible sections)
- Each phase contains its relevant tools as cards
- Cross-cutting tools (Q&A, consistency, gate) accessible from any phase
- Breadcrumb navigation showing current V-model position

---

## Course Materials Production Plan

### Phase 1: Content Writing (est. 40 hours)
Each of 20 sessions needs:
- 2-3 pages of facilitator content (theory, references, teaching notes)
- Key diagrams (1-3 per session, created as SVG)
- Key formulae (LaTeX rendered)
- Exercise instructions (step-by-step with SpaceCDF screenshots)
- Worksheet template

### Phase 2: Diagrams & Formulae (est. 15 hours)
- System-V diagram
- ECSS/NASA phase mapping
- Orbit geometry diagrams
- Link budget waterfall
- Mass budget pie/waterfall
- Power mode timeline
- Pointing budget tree
- Interface N² matrix example
- Trade study scoring example
- Verification matrix example
- CubeSat exploded view
- Ground segment architecture
- Data flow pipeline

### Phase 3: Worksheets (est. 10 hours)
20 worksheets, each 2-4 pages:
- Structured templates with fill-in sections
- Guided questions that map to SpaceCDF tool inputs
- Space for team discussion notes
- Reference to facilitator's book section

### Phase 4: Assembly & Indexing (est. 8 hours)
- Compile into two PDF documents
- Generate comprehensive index
- Cross-reference between facilitator and learner editions
- Table of contents, list of figures, list of tables
- Appendix with formulae summary and reference tables

### Phase 5: Review & Refinement (est. 7 hours)
- Technical review of all content
- Consistency check across sessions
- Verify all SpaceCDF references match current UI
- Final formatting and pagination

**Total estimated production: ~80 hours**

---

## Tracking

All items tracked in this file and docs/TODO.md. Implementation
proceeds in priority order: Tier 2 → Tier 3 → Tier 4 → Course.
Course content writing can begin in parallel with Tier 3/4 code work.
