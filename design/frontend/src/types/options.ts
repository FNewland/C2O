/**
 * Types for design options (SCDF-172) — routers/options.py, services/options.py.
 *
 * Semantics: the baseline is the parameter rows without option; an option row
 * shadows the baseline row of the same (element, parameter). The frontend
 * addresses the baseline as `option_id = null` (no query parameter).
 */

export interface DesignOption {
  id: string
  study_id: string
  name: string
  description: string
  is_baseline: boolean
  branched_from_option_id: string | null
  deleted_at: string | null
  created_at: string
  updated_at: string
  /** Only on the response of a branch: rows copied into the new option. */
  copied?: number
}

export interface OptionCompareParameter {
  element_id: string
  element: string
  name: string
  unit: string
  a: number | null
  b: number | null
  delta: number | null
  a_override: boolean
  b_override: boolean
  a_provenance: string | null
  b_provenance: string | null
}

export interface OptionCompareDelta {
  key: string
  a: number | null
  b: number | null
  delta: number | null
}

export interface OptionCompareAnalysis {
  analysis: string
  a_run_id: string | null
  b_run_id: string | null
  a_finished_at: string | null
  b_finished_at: string | null
  a_status: string | null
  b_status: string | null
  a_summary: Record<string, any>
  b_summary: Record<string, any>
  deltas: OptionCompareDelta[]
}

export interface OptionCompareSide {
  id: string | null
  name: string | null
  /** null = baseline rows */
  option_id: string | null
}

export interface OptionCompareResult {
  study_id: string
  a: OptionCompareSide
  b: OptionCompareSide
  parameters: OptionCompareParameter[]
  analyses: OptionCompareAnalysis[]
  conflicts: { a: number; b: number }
  warnings: string[]
}
