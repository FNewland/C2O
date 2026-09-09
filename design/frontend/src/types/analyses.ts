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
