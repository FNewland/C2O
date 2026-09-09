# SCDF-170 — Closing the loop: engineering analyses driven by, and written back to, the model

**Status:** accepted for build (Sept 2026), follows SCDF-160 (branch `arcadia-spine` @ 4e2f432)
**Binding for:** agents building SCDF-170..178. Deviations → ADR in `docs/_review/adr/`.

## 0. The problem this range solves

After SCDF-160, SpaceCDF has an Arcadia/10-25-shaped model (elements, functions, interfaces, exchange items, requirements with relations, typed parameters with formulas) and five engineering services from the H3 backlog: `conops_executor.simulate_orbit`, `ground_scheduler.predict_contacts/schedule_downlinks`, `vv_planner.generate_vv_plan`, `thermal_network.analyze_thermal_network` / `thermal_transient`, `mass_properties.compute_mass_properties`, plus `fmeca.run_fmeca`. **Every one of them is a standalone calculator**: it takes hand-typed dataclass inputs with built-in defaults (`DEFAULT_MODES`, `OrbitParams()`), is exposed as a bare `POST /…/simulate|schedule|analyze`, and neither reads the study (elements, modes, parameters, requirements, KB stations) nor writes anything back. Likewise the design loop (`routers/design.py`) runs the agents from `study.requirements` only — a manual override or formula on an element parameter never reaches the power/mass/link agents.

This range makes the model the single input and output of every analysis:

```
study ──► AnalysisContext ──► {agents | simulation | ground | thermal | mass/AOCS | V&V | FMECA}
  ▲                                                     │
  └────────── ResultsSink (parameters + conflicts + compliance recheck + change events) ◄──┘
```

## 1. Shared primitives (built first, SCDF-170)

### 1.1 `services/analysis_context.py`
`async def build_context(study_id, *, option_id=None) -> AnalysisContext` assembling, read-only:
- `study` (mission need, `MissionRequirements`, conops), `latest_design` (last `DesignLoopResult` params if any — find where design results are cached; else empty).
- `elements` (tree, dicts as served by `routers/elements`), `interfaces`, `exchange_items`, `functions`, `allocations`.
- `params`: `{element_id: {name: EffectiveParam(value, unit, switch, provenance, formula)}}` from `parameter_repo` + `services/equations.evaluate_study` — **effective values** (manual/reference override, `ref` formula, else computed/column).
- `flat`: the flat `parameter_path → value` dict the agents consume, produced by `element_projection.project_elements_to_params` **but overlaid with effective parameter values** (so an override of `EPS.mass_kg` changes `power.eps_mass_kg`). This is the SCDF-171 coupling.
- `orbit`: altitude, inclination, period, eclipse fraction, RAAN/LTAN if SSO — from `flat` (`orbit.*`) falling back to `study.requirements`.
- `modes`: from elements of `element_type='mode'` + `ModeElementRow` (which elements active, power in mode, duty cycle) → list of `ConOpsMode` with per-mode power computed as the sum of active elements' `power_w_in_mode` (fallback `power_avg_w` × duty); guards from mode element notes if parseable, else `DEFAULT_GUARDS`.
- `power`: battery capacity/DoD/efficiency, SA power BOL/EOL — from `flat` (`power.*`) / KB component of the selected battery/solar array (`kb_component_id`).
- `thermal`: per-subsystem dissipation = `power_avg_w`, optical properties/area from KB or class defaults.
- `ground_stations`: KB `ground_stations/` entries selected for the study (elements with `segment='ground'` and `kb_component_id`, or all KB stations flagged default) + user-defined.
- `requirements`: rows (persisted) + relations.
- `options`: the active `Option` (SCDF-172) — parameter overrides are option-scoped.

### 1.2 `services/analysis_results.py`
`class ResultsSink` with `async def publish(study_id, analysis: str, *, parameters: list[ParamWrite], conflicts: list[Conflict], notes: list[str], option_id=None)`:
- `ParamWrite(element_id | None, name, value, unit, quantity_kind)` → `parameter_repo.upsert_element_parameter(... computed_value=value, owner_domain=analysis)`; study-level results attach to the mission root element. Never overrides a `manual`/`reference` switch.
- `Conflict(severity, code, title, detail, element_ids, requirement_ids, suggested_fix)` → new table `analysis_conflicts` (id, study_id, option_id, analysis, severity, code, title, detail, element_ids_json, requirement_ids_json, suggested_fix, created_at, resolved_at). `GET /studies/{id}/conflicts` merges these with the existing design-loop conflicts (find where `ConflictsPanel` reads from and add this source).
- After writing: `compliance_tracker.recheck` with the written parameter paths (map `element.name` → threshold paths like `power.battery_dod_percent` via the projection registry; also allow requirements whose `threshold_param_path` is `el:<element_id>.<name>` — add that resolution to `evaluate_single`), then `broadcast_mutation('analysis_completed', ...)`.
- New table `analysis_runs` (id, study_id, option_id, analysis, started_at, finished_at, status, inputs_hash, summary_json, series_ref) so results are reproducible and the UI can show "last run / stale" — `stale` when `inputs_hash` (hash of the context subset the analysis declares it reads) differs from the current context hash.

### 1.3 Agent coupling (SCDF-171)
- `routers/design.py::run_design_loop` seeds the orchestrator's initial `DesignState` from `context.flat` (with effective overrides marked `POSITION_OVERRIDE` so they stay sticky per SPINE §1.3), and after the run writes agent outputs back via `ResultsSink` (analysis=`agent:<domain>`) and `element_projection.merge_agent_params_to_elements` (already exists — reuse).
- Acceptance: set `manual_value` for a component's `mass_kg` → run design → subsystem mass parameter, `mass.dry_mass_kg` and the margin tower change accordingly; a `ref` formula on a subsystem parameter that feeds a `power.*` input changes the power agent output.

### 1.4 Options (SCDF-172)
- Table `options` (id, study_id, name, description, is_baseline, created_at). `ElementParameterRow.option_id` already exists: an override with `option_id` shadows the baseline row for that option. `analysis_runs`/`analysis_conflicts` are option-scoped.
- API: `GET/POST /studies/{id}/options`, `POST /options/{id}/branch` (copy current overrides into a new option), `GET /studies/{id}/options/compare?a=&b=` → table of parameters and analysis summaries that differ, with deltas. Design runs and analyses accept `?option_id=`.
- UI: option switcher in the workbench status bar; `OptionCompare.tsx` table.
- Elements/tree are NOT cloned per option in this range (documented limit); `in_scope` per option is deferred.

### 1.5 As built (SCDF-170 Phase A, 2026-09-09) — binding interfaces for the closures

* `services/analysis_context.py`: `AnalysisContext` (fields as in §1.1 plus `overridden_paths`,
  `latest_design`, `all_kb_stations`, `relations`, `warnings`; helpers `element()`, `subsystem()`,
  `param()`, `resolve(path)`, `canonical_path(path)`, `get(path)`, `mission_root`),
  `async build_context(study_id, *, option_id=None)`, `context_hash(ctx, keys)` over
  `HASH_KEYS = elements|params|modes|orbit|power|thermal|stations|requirements`,
  `seed_design_state(ctx, *, requirements, conops, knowledge_base)`. Overrides (manual /
  reference / formula) on the well-known columns overlay the projection; an overridden roll-up on a
  non-leaf element **replaces** its subtree in `sum` aggregates (`element_projection` now sums
  leaves only, so N1's rolled-up subsystem columns are not double counted).
* `services/analysis_results.py`: `ParamWrite`, `Conflict`, `PublishResult`,
  `ResultsSink().publish(study_id, analysis, *, parameters, conflicts, notes, option_id, run_id, ctx)`,
  `start_run` / `finish_run(run_id, status, summary, series, inputs_hash)` /
  `refresh_inputs_hash(run_id)` (write-back analyses call it after `finish_run`, else their own
  outputs flag them stale) / `get_last_run` / `list_analyses` / `resolve_conflict`,
  `ANALYSIS_INPUT_KEYS` (declare yours), series under `$SPACECDF_DATA_DIR/analysis/<run_id>.json`.
  Parameter rows are not yet option-scoped (unique per element/definition) — SCDF-172.
* Compliance: `threshold_param_path = "el:<element id|name>.<param>"` resolved via
  `ctx.resolve`; `ResultsSink` re-checks through a per-study `ComplianceTracker` (`get_tracker`).
* Routes: `GET /api/studies/{id}/conflicts` → `{design, analysis}` (design = `analysis='design_loop'`
  rows), `POST /api/conflicts/{id}/resolve`, `GET /api/studies/{id}/analyses[/{analysis}]`.
* Design loop (`routers/design.py`) is coupled per §1.3; `?option_id=` accepted.
* N4 ruling: the Capella Requirements VP has **no** containment on `Requirement` (capellambse 0.8:
  only `Folder.requirements` / `Folder.folders`), so parent requirements stay `Requirements:Folder`
  with the full payload plus `long_name = "<code>: <text>"`. Do not "fix" the
  `search("Requirement")` count — use `oa.all_requirements` or `search("Requirement", "Requirements:Folder")`.
* N1–N3: `populate-subsystems` rolls up `mass_kg`/`power_avg_w` (children, else class heritage
  table) and creates the default power/data/RF interfaces with exchange items; ReqIF carries the
  three threshold attributes.

## 2. Engineering closures (parallel, each owns its service + router + component)

Each closure implements `async def run_<name>(ctx: AnalysisContext) -> AnalysisOutput(parameters, conflicts, series, summary)` and a thin router `POST /studies/{id}/analyses/<name>/run?option_id=` + `GET /studies/{id}/analyses/<name>` (last run + stale flag) that goes through `ResultsSink`. No calculator keeps its own defaults path as the primary entry; the old bare endpoints stay for ad-hoc use.

### 2.1 Mission simulation (SCDF-173) — `services/mission_simulation.py`, `routers/analyses_simulation.py`, `components/MissionSimulationPanel.tsx`
Wraps `conops_executor.simulate_orbit` with context-built modes/orbit/power/thermal/contacts (contacts from the ground closure's predictor when available, else `orbit.contact_time_per_day_s` spread uniformly). Runs N orbits (default 15 ≈ one day). Writes parameters on the mission root: `sim_min_soc_pct`, `sim_max_dod_pct`, `sim_energy_balance_wh_per_orbit`, `sim_data_buffer_max_gb`, `sim_data_backlog_end_gb`, `sim_heater_energy_wh_per_orbit`, `sim_time_in_safe_pct`. Conflicts: SoC below battery `min_soc_pct` (from KB/params, default 20 %) → critical with the mode and time; negative energy balance → major; data buffer overflow → major; >10 % time in safe → warning. Series stored as compact JSON (downsampled to ≤2000 points) in `analysis_runs.series_ref` (file under `data/analysis/<run_id>.json`). UI: SVG line chart (add `charts/SVGLineChart.tsx`, shared) for SoC / power in-out / data buffer / mode band; summary cards; "what limited me" list from conflicts; run + stale indicator.

### 2.2 Ground segment closure (SCDF-174) — `services/ground_closure.py`, `routers/analyses_ground.py`, `components/GroundSegmentPanel.tsx`
Stations from context (KB catalogue selection persisted as ground elements with `kb_component_id`; endpoint to add/remove stations to the study). `predict_contacts` + `schedule_downlinks` from context orbit + data generation (`data.generated_per_day_gb` from flat or sim). Per-station link margin via `spacecdf_common.physics.link_budget` using the study's TT&C parameters (frequency, EIRP/G/T from selected transponder/antenna KB components or `link.*` flat params) — a station with negative margin is excluded and flagged. Parameters on mission root: `gs_contact_min_per_day`, `gs_data_return_gb_per_day`, `gs_backlog_end_gb`, `gs_min_link_margin_db`, `gs_station_count`. Conflicts: data return < generation → major (suggest station or rate); min margin < 3 dB → warning. UI: station picker (KB list with lat/lon, band), contact table, closure gauge (return vs generated), per-station margin.

### 2.3 V&V closure (SCDF-175) — `services/vv_closure.py`, `routers/analyses_vv.py`, `components/VVPlanPanel.tsx`
New table `verification_items` (id, study_id, requirement_id, method A/T/I/R/D, level unit/subsystem/system/segment, phase, facility, procedure_ref, acceptance_criterion, status planned/in_progress/passed/failed/waived, evidence_ref, updated_at). `run_vv` = `generate_vv_plan` over persisted requirements + relations, producing/refreshing items (never overwrite human-edited fields: track `edited_by_user` flag). Acceptance criterion auto-derived from `threshold_param_path/op/value` (e.g. "battery DoD ≤ 30 % by analysis (power budget), phase PDR"). **Verification by analysis auto-closure**: when a requirement's compliance is PASS from a completed analysis run (design loop or a closure) and the item's method is A, set status `passed` with `evidence_ref = analysis_runs.id`; FAIL → `failed`. RTM/VCD export: `GET /studies/{id}/export/rtm.csv` and `vcd.docx` (reuse `docx_generator`). UI: editable table per requirement (method/level/phase/facility/status/evidence), roll-up bars per level, filter by status.

### 2.4 Physics closure: mass properties → AOCS, thermal network from elements (SCDF-176) — `services/physics_closure.py`, `routers/analyses_physics.py`, `components/PhysicsClosurePanel.tsx`
- Add column `DesignElementRow.position_json` (list [x,y,z] m in body frame, nullable; additive upgrader). Auto-place components without a position on a simple stack from `dimensions_json`/class (U-stack for CubeSats) with a warning.
- Mass properties from the element tree (masses = effective `mass_kg`) → CoM, inertia tensor (box approximation from dimensions), principal axes; parameters `mp_com_x/y/z_m`, `mp_ixx/iyy/izz_kgm2`, `mp_cp_cg_offset_m` (CP at geometric centre of the external envelope).
- AOCS: `spacecdf_common.physics.aocs` disturbance torques with real inertia + offset → momentum per orbit vs selected reaction wheel capacity (KB) and pointing budget vs the tightest pointing requirement (threshold path or `payload.pointing_deg`); parameters `aocs_disturbance_torque_nm`, `aocs_momentum_per_orbit_nms`, `aocs_wheel_margin_pct`, `aocs_pointing_margin_deg`; conflicts on negative margins.
- Thermal: build `ThermalNode`s per subsystem/component (dissipation = effective `power_avg_w`, capacitance from mass × class Cp, area from dimensions) + conductances between parent/child and along `thermal`-type interfaces; `solve_steady_state` hot/cold + `solve_transient` one orbit; compare to allowable ranges (`performance_json.op_temp_min/max_c` from KB or class defaults); parameters per element `thermal_t_hot_c`, `thermal_t_cold_c`, `thermal_margin_c`; conflicts when out of range. Feed the existing `DisturbanceTorqueBudget`, `MassPropertiesPanel`, `ThermalAnalysis` components from these results (extend, don't duplicate).

### 2.5 FMECA closure (SCDF-177, small) — extend `routers/fmeca.py` so `run_fmeca` takes the element tree + `redundancy_type` + relations and writes `fmeca_max_rpn`, `fmeca_single_point_failures` and a conflict per single-point failure on a `critical` element; link failure modes to functions via allocations (`function_id` on the failure mode).

## 3. Cross-cutting UI (SCDF-178)
- **Analyses tab** in the Level Workbench (`ActivityPanel` 'analyses'): cards for Design loop, Mission simulation, Ground segment, Physics (mass/AOCS/thermal), V&V, FMECA — each with last-run time, stale badge, run button, summary metrics, and its panel below.
- `ConflictsPanel` shows analysis conflicts (source badge, element chips, "go to" links).
- Margin tower gets `sim_min_soc_pct` and `gs_data_return` as two extra bars when available.
- WS invalidation on `analysis_completed`, `analysis_started`, `option_*`, `verification_item_*`.

## 4. Non-goals
Multi-body/attitude dynamics integration; radiation transport; full station scheduling optimisation (greedy is fine); options cloning the element tree; cost model 2.0; SysML v2 import.

## 5. Tests (binding)
- Context: effective override reaches `flat`; modes built from ModeElementRow; stations from KB.
- Sink: parameters written with provenance; manual switch not overridden; conflicts persisted; compliance rechecked (a requirement with `el:` path flips to violated).
- Coupling: override mass → design → subsystem/dry mass and margin change; formula feeding power input changes SA area.
- Options: branch, override in option shadows baseline, compare shows delta, analyses are option-scoped.
- Each closure: runs on a populated template study end-to-end via HTTP; parameters exist; at least one conflict scenario (e.g. shrink battery to force SoC conflict; remove stations to force data deficit; tighten pointing requirement; set component allowable range narrow); stale flag flips after an input change.
- V&V: items generated, human edit preserved on re-run, auto-closure by analysis, RTM CSV.
- Existing 231 stay green; `vite build` green; `tsc -b` ≤ 105.

## 6. Dependencies
No new runtime deps (scipy already used by thermal_transient — verify it is in a pyproject; add if missing). All code MIT-compatible.
