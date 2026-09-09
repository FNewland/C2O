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
