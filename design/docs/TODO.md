# SpaceCDF — Complete TODO List

## Tier 1: Critical Bugs (things that are broken)

- [x] Mission trade shows optical alternatives for comms missions → FIXED (mission_type threading)
- [x] Default spacecraft_class is "small" not "nano" → FIXED
- [x] Constellation not in mission trade options → FIXED
- [x] FunctionTreeView JSX parse error → FIXED
- [x] Functions show multispectral for comms → FIXED (mission-type-aware)
- [x] Position Q&A answers persisted to backend (POST /api/positions/answers, loaded on mount)
- [x] "operate at 500km" auto-generated requirement → RequirementsEditor now has level filter and auto-generated reqs tagged; compliance panel already has explanatory note
- [x] Optimizer UI passes mission_type → auto-enables relevant variables, disables propulsion for non-prop missions

## Tier 2: Missing Wiring (backend exists, no interactive UI)

- [x] Tabular trade studies → WIRED (TradeStudyPanel with templates, criteria, options)
- [x] Conflict count on dashboard → WIRED (KPI badge)
- [x] Spectrum bands as interactive design constraint → SpectrumSelector on dashboard
- [x] Parametric data interactive editor → ParametricEditor tab (mass/cost/power/SA tables)
- [x] Duty cycle display → in ParametricEditor power tab
- [x] ECSS margin enforcement display → MarginEnforcement on dashboard
- [x] Equipment needs analysis → browser sidebar shows required (blue dot) / optional (circle) / not needed (dimmed) per category with quantity and reason tooltip
- [x] Launch provider interactive selector → LaunchSelector on dashboard with 8 providers, capacity filtering, pricing, deployer compatibility

## Tier 3: Architecture Gaps (need new code)

- [x] System-V requirement hierarchy → RequirementsEditor level filter (mission/system/subsystem) + parent_id in data model
- [ ] Per-subsystem engineering budgets (editable allocations per subsystem with margins)
- [x] Interactive link budget calculator → LinkBudgetTool tab with full cascade (TX, path, RX, margin)
- [x] Pointing budget → PointingBudget on dashboard (7 error sources, RSS, editable, margin vs requirement)
- [x] Data budget → DataBudget on dashboard (generation→storage→downlink→user flow, balance check)
- [x] Timing budget → TimingBudget on dashboard (orbit timeline with mode segments, transitions, energy per mode)
- [x] V&V matrix → VerificationMatrix tab (per-req ATRI method, phase, level, status, responsible)
- [x] Spectrum selection → EquipmentBrowser filters transponders/antennas by selectedRfBand from SpectrumSelector
- [ ] Launch selection as design constraint (selector exists, mass allocation not yet auto-set)
- [ ] Consolidate duplicate exports (right panel ExportPanel vs center ExportsPanel)
- [ ] Mission type auto-set from mission need objectives

## Tier 4: Deepening (improve existing features)

- [ ] Structure CER too high for CubeSats (need COTS-anchored mass)
- [ ] Deep-space AOCS model broken (MarCO validation fails 162%)
- [ ] Cost CERs too high for CubeSats (need COMPACT-like model)
- [ ] Navigation redesign (6 workflow phases instead of 20+ tabs)
- [ ] System/subsystem boundary definition tool
- [ ] Per-requirement V&V method and phase assignment
- [ ] Constellation integrated into design loop (not just mission trade)
- [ ] Beyond-LEO orbits in orbit form selector

## Course Materials

- [x] Course plan (40 hours, 5 days, 20 sessions) → docs/course/COURSE_PLAN.md
- [ ] Facilitator's Book (~400 pages) — full content, solutions, diagrams, formulae, index
- [ ] Learner's Workbook (~150 pages) — condensed content, 20 worksheets, tool guides
- [ ] PDF generation pipeline

## Documentation

- [x] README.md overhaul with install guide
- [x] REDESIGN.md with architecture vision
- [ ] User guide PDF (short, focused on tool usage)
- [ ] API documentation
