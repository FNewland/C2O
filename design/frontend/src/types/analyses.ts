/**
 * Types for the SCDF-170 engineering analyses (runs, conflicts, closures).
 *
 * Each closure keeps its additions in its own delimited block so the parallel
 * build agents can append without conflicts.
 */

// ═══════════════════════════════════════════════════════════════════════
// Shared (analysis_runs / analysis_conflicts — services/analysis_results.py)
// ═══════════════════════════════════════════════════════════════════════

export type AnalysisRunStatus = 'running' | 'ok' | 'failed'
export type ConflictSeverity = 'critical' | 'major' | 'minor' | 'warning' | 'info'

export interface AnalysisRun {
  id: string
  study_id: string
  option_id: string | null
  analysis: string
  status: AnalysisRunStatus
  started_at: string
  finished_at: string | null
  inputs_hash: string | null
  current_hash?: string | null
  stale?: boolean
  summary: Record<string, any>
  series_ref: string | null
}

export interface AnalysisConflict {
  id: string
  study_id: string
  option_id: string | null
  analysis: string
  severity: ConflictSeverity
  code: string
  title: string
  detail: string
  element_ids: string[]
  requirement_ids: string[]
  suggested_fix: string | null
  created_at: string
  resolved_at: string | null
  resolved: boolean
  run_id?: string | null
}

// ═══════════════════════════════════════════════════════════════════════
// SCDF-173 — Mission simulation (services/mission_simulation.py) — BEGIN
// ═══════════════════════════════════════════════════════════════════════

export const MISSION_SIM_PARAMETERS = [
  'sim_min_soc_pct', 'sim_max_dod_pct', 'sim_energy_balance_wh_per_orbit', 'sim_data_buffer_max_gb',
  'sim_data_backlog_end_gb', 'sim_heater_energy_wh_per_orbit', 'sim_time_in_safe_pct', 'sim_orbits',
] as const
export type MissionSimParameter = typeof MISSION_SIM_PARAMETERS[number]

export type MissionSimConflictCode =
  | 'SIM_SOC_BELOW_MIN' | 'SIM_DOD_EXCEEDED' | 'SIM_ENERGY_NEGATIVE'
  | 'SIM_DATA_OVERFLOW' | 'SIM_DATA_BACKLOG' | 'SIM_SAFE_TIME'

export interface MissionSimSummary extends Partial<Record<MissionSimParameter, number>> {
  min_soc_pct?: number
  min_soc_at_s?: number
  min_soc_mode?: string
  energy_balance_wh_per_orbit?: number
  data_backlog_end_gb?: number
  time_in_safe_pct?: number
  min_temp_c?: number
  max_temp_c?: number
  guard_triggers?: number
  samples?: number
  duration_s?: number
  n_orbits?: number
  modes?: string[]
  conflict_codes?: string[]
  warnings?: string[]
  parameters_written?: number
  shadowed?: string[]
  conflicts?: number
  error?: string
}

export interface MissionSimRun extends AnalysisRun {
  summary: MissionSimSummary
  conflicts?: AnalysisConflict[]
}

export interface MissionSimRunResponse {
  run_id: string
  analysis: 'mission_simulation'
  option_id: string | null
  status: AnalysisRunStatus
  summary: MissionSimSummary
  parameters: { name: string; value: number; element_id: string }[]
  shadowed: { name: string; value: number; element_id: string }[]
  conflicts: AnalysisConflict[]
  warnings: string[]
  stale: false
}

export interface MissionSimSeries {
  analysis: 'mission_simulation'
  n_orbits: number
  period_s: number
  dt_s: number
  t_s: number[]
  mode: string[]
  soc_pct: number[]
  p_gen_w: number[]
  p_load_w: number[]
  data_buffer_gb: number[]
  temp_c: number[]
  events: { time_s: number; type: string; desc: string }[]
  modes: { name: string; power_w: number; data_rate_bps: number; payload_active: boolean }[]
  inputs: Record<string, any>
}

export interface RunSeriesResponse<S = MissionSimSeries> {
  run_id: string
  analysis: string
  series: S
}

// ═══════════════════════════════════════════════════════════════════════
// SCDF-173 — Mission simulation — END
// ═══════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════
// SCDF-174 — Ground segment closure (services/ground_closure.py) — BEGIN
// ═══════════════════════════════════════════════════════════════════════

export const GROUND_SEGMENT_PARAMETERS = [
  'gs_contact_min_per_day', 'gs_contacts_per_day', 'gs_data_return_gb_per_day', 'gs_data_generated_gb_per_day',
  'gs_backlog_end_gb', 'gs_min_link_margin_db', 'gs_station_count',
] as const
export type GroundSegmentParameter = typeof GROUND_SEGMENT_PARAMETERS[number]

export type GroundSegmentConflictCode =
  | 'GS_DATA_DEFICIT' | 'GS_LINK_MARGIN_LOW' | 'GS_STATION_EXCLUDED' | 'GS_NO_STATIONS'

export type GroundStationStatus = 'ok' | 'low_margin' | 'excluded' | 'no_contact'

/** One row of the per-station table (summary.stations / series.stations). */
export interface GroundStationRow {
  station_id: string
  name: string
  element_id: string | null
  lat: number
  lon: number
  bands: string[]
  antenna_m: number
  min_elevation_deg: number
  contacts_per_day: number
  contact_min_per_day: number
  margin_db: number | null
  g_t_db_k: number | null
  status: GroundStationStatus
  reason: string | null
  data_gb_per_day?: number
}

export interface GroundSegmentSummary extends Partial<Record<GroundSegmentParameter, number>> {
  stations?: GroundStationRow[]
  backlog_growth_gb_per_day?: number
  max_gap_hours?: number
  coverage_pct?: number
  downlink_rate_mbps?: number
  band?: string
  frequency_ghz?: number
  data_source?: string
  closure_pct?: number
  conflict_codes?: string[]
  warnings?: string[]
  parameters_written?: number
  shadowed?: string[]
  conflicts?: number
  error?: string
}

export interface GroundSegmentRun extends AnalysisRun {
  summary: GroundSegmentSummary
  conflicts?: AnalysisConflict[]
}

export interface GroundSegmentRunResponse {
  run_id: string
  analysis: 'ground_segment'
  option_id: string | null
  status: AnalysisRunStatus
  summary: GroundSegmentSummary
  parameters: { name: string; value: number; element_id: string }[]
  shadowed: { name: string; value: number; element_id: string }[]
  conflicts: AnalysisConflict[]
  warnings: string[]
  stale: false
}

export interface GroundContact {
  station_id: string
  station: string
  start_s: number
  end_s: number
  max_elevation_deg: number
  data_gb: number
}

export interface GroundSegmentSeries {
  analysis: 'ground_segment'
  duration_s: number
  contacts: GroundContact[]
  buffer: { t_s: number[]; gb: number[] }
  stations: GroundStationRow[]
  inputs: Record<string, any>
}

/** KB catalogue entry (packages/spacecdf-kb ground_stations/networks.yaml ``stations:``). */
export interface KbGroundStation {
  id: string
  name: string
  lat: number
  lon: number
  alt_m?: number
  bands: string[]
  antenna_m?: number
  operator?: string
  min_elevation_deg?: number
  g_over_t_db_k?: number
  eirp_dbw?: number
  notes?: string
  selected?: boolean
}

/** A station selected for the study (a ``segment='ground'`` component element). */
export interface SelectedGroundStation {
  element_id: string
  kb_station_id: string
  name: string
  parent_id: string | null
  version: number
  lat: number | null
  lon: number | null
  alt_m: number | null
  bands: string[] | null
  antenna_m: number | null
  g_over_t_db_k: number | null
  eirp_dbw: number | null
  min_elevation_deg: number | null
  operator: string | null
  in_catalogue: boolean
}

export interface GroundStationsResponse {
  study_id: string
  selected: SelectedGroundStation[]
  catalogue: KbGroundStation[]
}

// ═══════════════════════════════════════════════════════════════════════
// SCDF-174 — Ground segment closure — END
// ═══════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════
// SCDF-175 — V&V closure (services/vv_closure.py, routers/analyses_vv.py) — BEGIN
// ═══════════════════════════════════════════════════════════════════════

export type VVMethod = 'A' | 'T' | 'I' | 'R' | 'D'
export type VVLevel = 'unit' | 'subsystem' | 'system' | 'segment'
export type VVPhase = 'PDR' | 'CDR' | 'QR' | 'AR'
export type VVStatus = 'planned' | 'in_progress' | 'passed' | 'failed' | 'waived'

/** One ``verification_items`` row. */
export interface VerificationItem {
  id: string
  study_id: string
  requirement_id: string
  method: VVMethod | null
  level: VVLevel | null
  phase: VVPhase | null
  facility: string | null
  procedure_ref: string | null
  acceptance_criterion: string | null
  status: VVStatus
  evidence_ref: string | null
  edited_by_user: boolean
  notes: string
  created_at: string
  updated_at: string
}

/** Item joined with its requirement (GET /studies/{id}/verification-items, run response). */
export interface VerificationItemView extends VerificationItem {
  requirement_code: string
  requirement_text: string
  requirement_level: string | null
  threshold_param_path: string | null
  threshold_op: string | null
  threshold_value: string | null
  linked_elements: string[]
  linked_element_names: string[]
  linked_functions: string[]
  /** closed by an analysis run (evidence ``analysis:<run_id>``) and not hand-edited */
  auto_closed: boolean
}

export interface VVLevelRollup {
  total: number
  planned: number
  in_progress: number
  passed: number
  failed: number
  waived: number
}

export interface VerificationItemsResponse {
  study_id: string
  items: VerificationItemView[]
  by_level: Record<VVLevel, VVLevelRollup>
  total: number
}

export interface VVRunSummary {
  vv_items_total: number
  vv_items_passed: number
  vv_items_failed: number
  vv_items_planned: number
  vv_closure_pct: number
  vv_by_analysis_pct: number
  items_waived: number
  items_auto_closed: number
  by_level: Record<VVLevel, VVLevelRollup>
  by_method: Record<VVMethod, number>
  conflicts: number
  parameters_written?: number
  shadowed?: string[]
  run_id?: string | null
}

export interface VVRunResponse {
  run_id: string
  analysis: 'vv'
  option_id: string | null
  status: AnalysisRunStatus
  summary: VVRunSummary
  items: VerificationItemView[]
  parameters: { name: string; value: number; element_id: string }[]
  shadowed: { name: string; value: number; element_id: string }[]
  conflicts: AnalysisConflict[]
  warnings: string[]
  stale: boolean
}

export interface VVRun extends AnalysisRun {
  summary: VVRunSummary
  conflicts?: AnalysisConflict[]
  items?: VerificationItemView[]
}

export interface VerificationItemPatch {
  method?: VVMethod | null
  level?: VVLevel | null
  phase?: VVPhase | null
  facility?: string | null
  procedure_ref?: string | null
  acceptance_criterion?: string | null
  status?: VVStatus
  evidence_ref?: string | null
  notes?: string
}

export interface VerificationEvidencePost {
  evidence_ref?: string | null
  status: VVStatus
  notes?: string
}

// ═══════════════════════════════════════════════════════════════════════
// SCDF-175 — V&V closure — END
// ═══════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════
// SCDF-176 — Physics closure (services/physics_closure.py, routers/analyses_physics.py) — BEGIN
// ═══════════════════════════════════════════════════════════════════════

export const PHYSICS_PARAMETERS = [
  'mp_total_mass_kg', 'mp_com_x_m', 'mp_com_y_m', 'mp_com_z_m', 'mp_ixx_kgm2', 'mp_iyy_kgm2', 'mp_izz_kgm2',
  'mp_cp_cg_offset_m', 'mp_auto_placed_count',
  'aocs_disturbance_torque_nm', 'aocs_gg_torque_nm', 'aocs_aero_torque_nm', 'aocs_srp_torque_nm', 'aocs_mag_torque_nm',
  'aocs_momentum_per_orbit_nms', 'aocs_wheel_capacity_nms', 'aocs_wheel_margin_pct',
  'aocs_pointing_req_deg', 'aocs_pointing_est_deg', 'aocs_pointing_margin_deg',
  'thermal_worst_margin_c', 'thermal_nodes',
] as const
export type PhysicsParameter = typeof PHYSICS_PARAMETERS[number]
/** Element-scoped parameters written on every thermal node. */
export const PHYSICS_ELEMENT_PARAMETERS = ['thermal_t_hot_c', 'thermal_t_cold_c', 'thermal_margin_hot_c', 'thermal_margin_cold_c'] as const

export type PhysicsConflictCode = 'AOCS_WHEEL_SATURATION' | 'AOCS_POINTING_MARGIN' | 'AOCS_CG_OFFSET_HIGH' | 'THERMAL_OUT_OF_RANGE'

export interface PlacementItem {
  element_id: string
  name: string
  element_type: string
  domain: string | null
  mass_kg: number
  dims_m: [number, number, number]
  position_m: [number, number, number]
  source: string            // explicit | auto | "<source> (subsystem mass)"
  quantity: number
}

export interface PlacementResponse {
  study_id: string
  envelope_m: [number, number, number]
  envelope_source: string
  envelope_element_id: string | null
  auto_placed: string[]
  warnings: string[]
  items: PlacementItem[]
}

export interface PhysicsSummary extends Partial<Record<PhysicsParameter, number>> {
  auto_placed?: number
  placed?: number
  envelope_m?: [number, number, number]
  wheel_source?: string
  pointing_req_source?: string
  thermal_nodes?: number
  thermal_out_of_range?: string[]
  conflict_codes?: string[]
  warnings?: string[]
  parameters_written?: number
  shadowed?: string[]
  conflicts?: number
  error?: string
}

export interface PhysicsRun extends AnalysisRun {
  summary: PhysicsSummary
  conflicts?: AnalysisConflict[]
}

export interface PhysicsRunResponse {
  run_id: string
  analysis: 'physics'
  option_id: string | null
  status: AnalysisRunStatus
  summary: PhysicsSummary
  parameters: { name: string; value: number; element_id: string }[]
  shadowed: { name: string; value: number; element_id: string }[]
  conflicts: AnalysisConflict[]
  warnings: string[]
  stale: false
}

export interface ThermalNodeView {
  element_id: string
  name: string
  domain: string | null
  kind: 'structure' | 'subsystem' | 'component'
  mass_kg: number
  area_m2: number
  dissipation_hot_w: number
  dissipation_cold_w: number
  allow_min_c: number
  allow_max_c: number
  allow_source: string
  t_hot_c: number
  t_cold_c: number
  margin_hot_c: number
  margin_cold_c: number
  t_transient_min_c: number
  t_transient_max_c: number
}

export interface PhysicsSeries {
  analysis: 'physics'
  placement: Omit<PlacementResponse, 'study_id' | 'warnings'>
  mass_properties: {
    total_mass_kg: number
    com_m: [number, number, number]
    cp_m: [number, number, number]
    cp_cg_offset_m: number
    inertia: { ixx: number; iyy: number; izz: number; ixy: number; ixz: number; iyz: number }
    principal: [number, number, number]
    principal_axes: number[][] | null
  }
  aocs: {
    torques_nm: { gravity_gradient: number; aerodynamic: number; solar_pressure: number; magnetic: number; sum: number; rss: number }
    momentum_per_orbit_nms: number
    wheel_capacity_nms: number
    wheel_source: string
    wheel_element_id: string | null
    wheel_margin_pct: number
    pointing_req_deg: number | null
    pointing_req_source: string
    pointing_est_deg: number
    pointing_budget: { knowledge_deg: number; control_deg: number; actuator_deg: number; rss_deg: number }
    pointing_margin_deg: number | null
    inputs: Record<string, any>
  }
  thermal: {
    nodes: ThermalNodeView[]
    conductances: { a: string; b: string; w_per_k: number }[]
    worst_margin_c: number | null
    transient: {
      case?: string
      t_s: number[]
      period_s: number
      eclipse_fraction: number
      eclipse_start_s: number
      nodes: { id: string; name: string; kind: string; temps_c: number[] }[]
    }
    inputs: Record<string, any>
  }
}

export interface ElementPositionPatch { x?: number | null; y?: number | null; z?: number | null }

// ═══════════════════════════════════════════════════════════════════════
// SCDF-176 — Physics closure — END
// ═══════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════
// SCDF-177 — FMECA closure (services/fmeca_closure.py, routers/fmeca.py study_router) — BEGIN
// ═══════════════════════════════════════════════════════════════════════

export const FMECA_PARAMETERS = ['fmeca_max_rpn', 'fmeca_single_point_failures', 'fmeca_modes', 'fmeca_critical_modes'] as const
export type FMECAConflictCode = 'FMECA_SINGLE_POINT'

export interface StudyFailureMode {
  id: string
  element_id: string
  element_name: string
  element_type: string
  subsystem_id: string | null
  subsystem: string | null
  domain: string
  mode: string
  cause: string
  local_effect: string
  system_effect: string
  severity: number
  occurrence: number
  detection: number
  rpn: number
  mitigation: string
  redundancy_type: string | null
  quantity: number
  redundant: boolean
  single_point: boolean
  critical: boolean
  function_ids: string[]
  functions: string[]
  affected: string[]
  source: string
}

export interface FMECASummary extends Partial<Record<typeof FMECA_PARAMETERS[number], number>> {
  modes?: number
  single_points?: string[]
  critical_single_points?: string[]
  top?: { id: string; element: string; mode: string; rpn: number }[]
  conflict_codes?: string[]
  warnings?: string[]
  parameters_written?: number
  conflicts?: number
  error?: string
}

export interface FMECARun extends AnalysisRun {
  summary: FMECASummary
  conflicts?: AnalysisConflict[]
  modes?: StudyFailureMode[]
}

export interface FMECARunResponse {
  run_id: string
  analysis: 'fmeca'
  option_id: string | null
  status: AnalysisRunStatus
  summary: FMECASummary
  modes: StudyFailureMode[]
  parameters: { name: string; value: number; element_id: string }[]
  shadowed: { name: string; value: number; element_id: string }[]
  conflicts: AnalysisConflict[]
  warnings: string[]
  stale: false
}

export interface FMECASeries {
  analysis: 'fmeca'
  modes: StudyFailureMode[]
  graph: Record<string, string[]>
  critical_function_ids: string[]
}

// ═══════════════════════════════════════════════════════════════════════
// SCDF-177 — FMECA closure — END
// ═══════════════════════════════════════════════════════════════════════
