# SpaceCDF live files and translation packets

*Generated 2026-10-28 by packet C0. Do not hand-edit the file lists without re-running the reachability check.*

**Live** means reachable by static `import` from `src/main.tsx` (relative imports followed through `.ts`/`.tsx`/`index`).
Result: **144** source files under `src/` (excluding `src/i18n/`), **52 live**, **92 dead**. Only live files are translated.
The packet split follows UI_STRING_SURVEY §7.2; the 10 live files the survey table omitted (stores, hooks, types, `SVGBarChart`)
are assigned to the packet whose components use them. **No file is in two packets.** C0 owns `src/i18n/**`; each of C1–C4 writes
its French **only** to its own catalog `src/i18n/locales/fr.c1.json` … `fr.c4.json` (merged at load time over `fr.json`), so
parallel packets never edit the same file. The catalogs are folded into `fr.json` after wave 2.

"Candidates" = string literals / JSX text / template literals containing words (AST count with the TypeScript compiler,
excluding imports, property keys, comparisons, `case` labels and non-text JSX attributes). As in the survey, about 70 % are real
UI prose; the rest are IDs, units, CSS and persisted seed data that must **not** be translated.

| Packet | Scope | Files | Candidates | Est. translatable |
|---|---|---|---|---|
| C0 | App shell, header, navigation (done in C0) | 3 | 53 | done |
| C1 | Shell panels, mission wizard, decisions, options, AI | 20 | 532 | ~370 |
| C2 | Blocks, guidance, export, exchange, seed data | 9 | 675 | ~470 |
| C3 | Requirements, V&V, interfaces, functions, FMECA | 9 | 646 | ~450 |
| C4 | Analyses, budgets, physics, ground, simulation, charts | 11 | 476 | ~330 |
| **Total** | | **52** | **2382** | **~1630** (C1–C4) |

## C0 — App shell, header, navigation (done in C0)

- `src/main.tsx` — 0
- `src/App.tsx` — 53
- `src/stores/uiStore.ts` — 0

## C1 — Shell panels, mission wizard, decisions, options, AI

- `src/workbench/LevelWorkbench.tsx` — 14
- `src/workbench/MissionWizard.tsx` — 135
- `src/workbench/ReadinessChecklist.tsx` — 18
- `src/workbench/EscalationBanner.tsx` — 7
- `src/workbench/PresenceBar.tsx` — 4
- `src/workbench/DecisionPanel.tsx` — 225
- `src/workbench/DesignTools.tsx` — 49
- `src/components/MarginTower.tsx` — 15
- `src/components/OptionSwitcher.tsx` — 15
- `src/components/OptionCompare.tsx` — 31
- `src/components/ErrorBoundary.tsx` — 4
- `src/ai/AIContext.tsx` — 1
- `src/ai/AIGate.tsx` — 1
- `src/ai/AIStatusIndicator.tsx` — 5
- `src/ai/index.ts` — 0
- `src/stores/optionStore.ts` — 0
- `src/stores/sessionStore.ts` — 0
- `src/types/options.ts` — 0
- `src/workbench/useCollaboration.ts` — 1
- `src/hooks/useSessionSocket.ts` — 7

## C2 — Blocks, guidance, export, exchange, seed data

- `src/workbench/BlocksPanel.tsx` — 224
- `src/workbench/BlockDiagram.tsx` — 13
- `src/workbench/EquipmentBrowser.tsx` — 45
- `src/workbench/GuidancePanel.tsx` — 157
- `src/workbench/ExportPanel.tsx` — 133
- `src/components/ExchangePanel.tsx` — 39
- `src/stores/designStore.ts` — 49
- `src/stores/modelStore.ts` — 11
- `src/types/arcadia.ts` — 4

## C3 — Requirements, V&V, interfaces, functions, FMECA

- `src/workbench/VVPanel.tsx` — 222
- `src/workbench/RequirementsPanel.tsx` — 66
- `src/workbench/InterfacesPanel.tsx` — 70
- `src/workbench/suggestedReqs.ts` — 23
- `src/components/VVPlanPanel.tsx` — 80
- `src/components/ICDTable.tsx` — 37
- `src/components/TraceabilityTree.tsx` — 29
- `src/components/FMECAPanel.tsx` — 59
- `src/components/FunctionTree.tsx` — 60

## C4 — Analyses, budgets, physics, ground, simulation, charts

- `src/workbench/AnalysesPanel.tsx` — 58
- `src/workbench/BudgetPanel.tsx` — 99
- `src/components/PhysicsClosurePanel.tsx` — 85
- `src/components/GroundSegmentPanel.tsx` — 88
- `src/components/MissionSimulationPanel.tsx` — 51
- `src/components/ParameterPanel.tsx` — 53
- `src/components/ConflictsPanel.tsx` — 37
- `src/charts/SVGLineChart.tsx` — 5
- `src/charts/SVGBarChart.tsx` — 0
- `src/types/analyses.ts` — 0
- `src/hooks/useActiveParameters.ts` — 0

### Notes per packet

- **C0** translated the shell strings in `App.tsx` (level tabs, breadcrumb root, StatusBar buttons, name prompt, alerts).
  Left English on purpose: `'New Mission'` and `'Loaded Mission'` (default study names sent to the backend = stored data).
  `CreateStudyGate` in `App.tsx` is unused but was translated anyway.
- **C1** `MissionWizard` creates studies and elements: names it POSTs are stored data — translate only what is rendered.
  `toLocaleDateString` in `MissionWizard`/`DecisionPanel` → `fmtDate()`.
- **C2** `designStore.ts`, `BlocksPanel.tsx` seed/catalog names ("CubeSat LEO Mission", "Ti-6Al-4V") are **persisted** as
  element names. Do not change the stored value; if a seed name must look French, translate at render time where it is displayed
  *and* only if the user has not renamed it (compare with the seed constant). Also owns the backend export TODO (ECSS templates,
  see GUIDE.md §Backend).
- **C3** `suggestedReqs.ts` texts become requirement text in the database when accepted: keep the stored text English, show
  `t(text)` only in the suggestion list. Requirement IDs/codes (`MIS-001`, `SYS-PWR-003`) never change.
- **C4** Charts draw SVG `<text>` — translate axis titles, never unit symbols. Backend analysis messages (`detail`,
  closure rationale) arrive in English and stay English in this wave (packet K4).

## Dead files (out of scope — 92)

Not reachable from `main.tsx`; do not translate. If one is wired back in later, re-run the reachability check and assign it.

- `src/charts/BudgetCascade.tsx`
- `src/charts/BudgetGauge.tsx`
- `src/charts/SVGWaterfall.tsx`
- `src/components/BOMView.tsx`
- `src/components/BudgetComparison.tsx`
- `src/components/ChangeAuditPanel.tsx`
- `src/components/ComplianceMatrix.tsx`
- `src/components/ConOpsEditor.tsx`
- `src/components/ConflictReviewModal.tsx`
- `src/components/ConstellationDesigner.tsx`
- `src/components/ConstraintViolationsPanel.tsx`
- `src/components/ConvergenceTrace.tsx`
- `src/components/CostBreakdown.tsx`
- `src/components/DataBudget.tsx`
- `src/components/DesignStateBar.tsx`
- `src/components/DesignWorkspace.tsx`
- `src/components/DirtySetBadge.tsx`
- `src/components/DisturbanceTorqueBudget.tsx`
- `src/components/DocumentPreview.tsx`
- `src/components/EcssCompliancePanel.tsx`
- `src/components/EngineeringBudgets.tsx`
- `src/components/EquipmentBrowser.tsx`
- `src/components/ExportsPanel.tsx`
- `src/components/FunctionTreeView.tsx`
- `src/components/GateReviewPanel.tsx`
- `src/components/GroundStationDesigner.tsx`
- `src/components/GroundSystemsArch.tsx`
- `src/components/HierarchicalDesigner.tsx`
- `src/components/HistoryDrawer.tsx`
- `src/components/ImpactPreview.tsx`
- `src/components/InsightsPanel.tsx`
- `src/components/InterfaceMatrixView.tsx`
- `src/components/LaunchSelector.tsx`
- `src/components/LinkBudgetTool.tsx`
- `src/components/LiveEditToast.tsx`
- `src/components/MarginEnforcement.tsx`
- `src/components/MassPropertiesPanel.tsx`
- `src/components/MaturityOverview.tsx`
- `src/components/MissionArchitectureEditor.tsx`
- `src/components/MissionBudgetSummary.tsx`
- `src/components/MissionDashboard.tsx`
- `src/components/MissionNeedPanel.tsx`
- `src/components/MissionTradeView.tsx`
- `src/components/ModelBlockDiagram.tsx`
- `src/components/OBCInterfaceDiagram.tsx`
- `src/components/OpsSystemsArch.tsx`
- `src/components/OptimizerPanel.tsx`
- `src/components/ParametricEditor.tsx`
- `src/components/PersistenceWarningBanner.tsx`
- `src/components/PhaseAndGateStrip.tsx`
- `src/components/PointingBudget.tsx`
- `src/components/PositionAnswersPanel.tsx`
- `src/components/PositionPanel.tsx`
- `src/components/PowerDistribution.tsx`
- `src/components/PowerRailEditor.tsx`
- `src/components/ProjectManagement.tsx`
- `src/components/PropulsionAnalysis.tsx`
- `src/components/RequirementsEditor.tsx`
- `src/components/RequirementsPanel.tsx`
- `src/components/RequirementsTree.tsx`
- `src/components/SEMPQuestionnaire.tsx`
- `src/components/SessionBar.tsx`
- `src/components/SnapshotsPanel.tsx`
- `src/components/SolarArrayDecayPlot.tsx`
- `src/components/SpectrumSelector.tsx`
- `src/components/StudyStepper.tsx`
- `src/components/SystemArchitectureEditor.tsx`
- `src/components/SystemBlockDiagram.tsx`
- `src/components/SystemBudgetEditor.tsx`
- `src/components/TemplateGallery.tsx`
- `src/components/ThermalAnalysis.tsx`
- `src/components/TimingBudget.tsx`
- `src/components/TradeStudyPanel.tsx`
- `src/components/UserManual.tsx`
- `src/components/VerificationMatrix.tsx`
- `src/constants.ts`
- `src/hooks/useApplyToDesign.ts`
- `src/hooks/useEquipmentView.ts`
- `src/hooks/useOptimizer.ts`
- `src/hooks/useSession.ts`
- `src/hooks/useSnapshots.ts`
- `src/hooks/useTemplates.ts`
- `src/phases/Phase0Need.tsx`
- `src/phases/Phase1MissionArch.tsx`
- `src/phases/Phase2SystemArch.tsx`
- `src/phases/Phase3SubsystemDesign.tsx`
- `src/phases/Phase4Integration.tsx`
- `src/phases/Phase5Verification.tsx`
- `src/types/changeEvent.ts`
- `src/types/mission.ts`
- `src/types/phases.ts`
- `src/views/LensView.tsx`
