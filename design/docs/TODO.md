# SpaceCDF — Complete TODO List

## Tier 1: Critical Bugs (things that are broken)

- [x] Mission trade shows optical alternatives for comms missions → FIXED (mission_type threading)
- [x] Default spacecraft_class is "small" not "nano" → FIXED
- [x] Constellation not in mission trade options → FIXED
- [x] FunctionTreeView JSX parse error → FIXED
- [x] Functions show multispectral for comms → FIXED (mission-type-aware)
- [ ] Position Q&A answers not persisted to backend
- [ ] "operate at 500km" auto-generated requirement not user-approved
- [ ] Optimizer UI doesn't pass mission_type to config endpoint for relevance filtering

## Tier 2: Missing Wiring (backend exists, no interactive UI)

- [x] Tabular trade studies → WIRED (TradeStudyPanel with templates, criteria, options)
- [x] Conflict count on dashboard → WIRED (KPI badge)
- [x] Spectrum bands as interactive design constraint → SpectrumSelector on dashboard
- [x] Parametric data interactive editor → ParametricEditor tab (mass/cost/power/SA tables)
- [x] Duty cycle display → in ParametricEditor power tab
- [x] ECSS margin enforcement display → MarginEnforcement on dashboard
- [ ] Equipment needs analysis driving browser category filtering (backend exists, UI filtering not yet connected)
- [ ] Launch provider interactive selector (backend exists, UI not yet built as standalone selector)

## Tier 3: Architecture Gaps (need new code)

- [ ] System-V requirement hierarchy (mission → system → subsystem with parent/child links)
- [ ] Per-subsystem engineering budgets (mass/power/cost breakdown per subsystem)
- [ ] Interactive link budget calculator
- [ ] Pointing budget (RSS error tree)
- [ ] Data budget (generation → storage → downlink → processing pipeline)
- [ ] Timing budget (mode durations, transition times)
- [ ] Full V&V matrix with verification phases
- [ ] Spectrum selection as design constraint (band choice filters transponders)
- [ ] Launch selection as design constraint (sets mass allocation, vibration levels)
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
