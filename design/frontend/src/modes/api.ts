/**
 * Mode model API (routers/modes.py): modes, transitions, the mode × element matrix,
 * budgets per mode and the rule proposals. Plain fetch + TanStack Query keys.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import i18n from '../i18n'

const API = '/api'

export type Bi = { en: string; fr: string }
export const bi = (v: Bi | string | null | undefined): string =>
  !v ? '' : typeof v === 'string' ? v : (i18n.language === 'fr' ? v.fr || v.en : v.en || v.fr)

export interface Mode {
  id: string; name: string; description: string; version: number
  kind: string; phase: string; pointing: string; sunlit_only: boolean
  orbit_fraction: number | null; initial: boolean; order: number | null; template_key?: string | null
}
export interface Guard { param?: string; op?: string; value?: number; unit?: string; text?: string }
export interface Transition {
  id: string; from_mode_id: string; to_mode_id: string; trigger: string
  guard: Guard; monitor_ref: string; priority: number; description: string; origin: string
}
export interface Member {
  mode_id: string; element_id: string; is_active: boolean; power_w_in_mode: number | null
  duty_cycle_percent: number | null; power_state: string | null; data_rate_bps: number | null
  dissipation_w: number | null; origin: string; status: string; source_ref: string; notes: string
}
export interface Unit {
  id: string; name: string; domain: string | null; unit_class: string; power_avg_w: number | null
  power_peak_w: number | null; quantity: number; kb_component_id: string | null; stale: boolean
}
export interface Finding { id: string; severity: string; mode_id?: string; transition_id?: string; text: Bi }
export interface ModesOverview {
  study_id: string; modes: Mode[]; transitions: Transition[]; members: Member[]; units: Unit[]
  findings: Finding[]
  vocabulary: { kinds: string[]; triggers: string[]; pointing: string[]; states: string[] }
  template_ref: { standard_ref: string; c2o_default: boolean }
  states_ref: { standard_ref: string; c2o_default: boolean }
}
export interface SystemMargin {
  gate: string | null; percent?: number; mass_percent?: number; power_percent?: number
  label: Bi; convention: { id: string; text: Bi }; standard_ref: string
}
export interface EnergyRow {
  mode_id: string; name: string; kind: string; pointing: string; sunlit_only: boolean
  power_cbe_w: number; power_with_maturity_w: number; power_total_w: number; generation_sunlit_w: number
  array_factor: number; energy_generated_wh: number; energy_needed_wh: number; balance_wh: number | null
  dod_percent: number | null; held_full_orbit: boolean; status: string
}
export interface Energy {
  system_margin: SystemMargin
  orbit: { period_s: number; eclipse_fraction: number; sunlit_s: number; eclipse_s: number }
  inputs: { sa_power_eol_w: number | null; battery_capacity_wh: number | null; battery_efficiency: number
    max_dod_percent: number; sa_power_source: string; battery_source: string; altitude_km: number | null
    array_factor_ref: { standard_ref: string } }
  modes: EnergyRow[]
  operational_orbit: { modes: { mode_id: string; name: string; orbit_fraction: number }[]; generated_wh: number
    needed_wh: number; balance_wh: number | null; orbit_average_load_w: number; dod_percent: number | null; status: string
    orbit_average_cbe_w?: number; share_total?: number } | null
  /** wave 3 (3.H4): β and the eclipse range over the year, the operational orbit in the longest eclipse */
  season?: { year: number; beta: { min_deg: number; max_deg: number }; eclipse: { min_min: number; max_min: number }
    worst_eclipse_orbit: { dod_percent: number | null; orbit_average_load_w: number } | null } | null
  sustainable_duty: { mode_id: string; name: string; sustainable_fraction: number; planned_fraction: number; status: string }[]
  warnings: string[]
}
export interface Check { id: string; label: Bi; status: string; value: number | null; limit: number | null; unit: string; standard_ref: string; c2o_default: boolean }
export interface DataChain {
  /** wave 3 (3.H2): "products" = science files + stored HK; acquired = the payloads' interface rate over the mix */
  generation_basis?: 'products' | 'modes'; acquired_gb_per_day?: number
  per_mode: { mode_id: string; name: string; kind: string; generation_bps: number; orbit_fraction: number | null; per_orbit_mb: number
    payload_bps?: number; hk_stored_bps?: number; hk_realtime_bps?: number | null; in_mix?: boolean }[]
  housekeeping_bps: number; orbits_per_day: number; generated_gb_per_day: number
  housekeeping?: { designed: boolean; source: string; stored_mb_per_day: number; realtime_mb_per_day: number
    realtime_contact_bps: number | null; realtime_allocation_bps: number | null }
  storage: { capacity_gb: number | null; buffer_days: number; need_gb: number; need_with_margin_gb: number; margin_percent: number }
  downlink: { rate_bps: number; protocol_efficiency: number; contact_min_per_day: number; capacity_gb_per_day: number
    band?: string; rate_source?: string; sum_of_stations_min_per_day?: number; contact_basis?: string; usable_min_per_day?: number | null
    /** "after_realtime_hk": capacity_gb_per_day is what is left after the real-time HK of the passes */
    capacity_basis?: 'after_realtime_hk' | 'total'; total_capacity_mb_per_day?: number; realtime_hk_mb_per_day?: number
    remaining_after_realtime_hk_mb_per_day?: number; allocatable_mb_per_day?: number | null; allocatable_percent?: number | null
    acquisition_s?: number | null; availability?: number | null
    stations: { name: string; contact_min_per_day: number; margin_db: number | null; used: boolean; low_margin: boolean; status: string
      capacity_gb_per_day: number; usable_min_per_day?: number }[] }
  backlog_growth_gb_per_day: number; days_to_full: number | null; checks: Check[]; warnings: string[]
  /** W3.05: the daily closure of the data budget (the numbers of the Data budget page) */
  data_budget?: { status: string; closure: DailyCase | null } | null
}
export interface DailyCase {
  id: string; label: Bi; capacity_mb: number; rt_hk_mb: number; stored_hk_mb: number; science_mb: number; other_mb: number
  demand_mb: number; margin_pct: number | null; status: string
}
export interface EquipRow {
  element_id: string; name: string; quantity: number; unit_class: string; maturity_category: string
  maturity_percent: number; maturity_from: string; mass_kg: number; mass_with_maturity_kg: number
  power_avg_w: number | null; power_by_mode_w: Record<string, number>; data_by_mode_bps: Record<string, number>
  dissipation_by_mode_w: Record<string, number>; cost_keur: number | null
  link: { tx_power_w?: number; data_rate_bps?: number; band?: string } | null; stale: boolean
}
export interface EquipBudgets {
  rows: EquipRow[]; modes: { id: string; name: string; kind: string }[]
  totals: { mass_cbe_kg: number; mass_with_maturity_kg: number; mass_total_kg: number; cost_keur: number
    power_by_mode_w: Record<string, number>; power_by_mode_with_maturity_w: Record<string, number>
    power_by_mode_total_w: Record<string, number>; data_by_mode_bps: Record<string, number>; dissipation_by_mode_w: Record<string, number> }
  system_margin: SystemMargin; note: Bi
}
export interface Proposal {
  id: string; rule_id: string; kind: 'monitor' | 'action' | 'risk' | 'heater'; target_key: string; element_id: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- payload shape depends on the rule kind
  payload: Record<string, any>; standard_ref: string; c2o_default: boolean; rationale: Bi & { stale_since?: string }
  status: string; result_ref: string
}
export interface StaleRow { element_id: string; name: string; kb_component_id: string; reason: string; changed: string[] }

const json = async (r: Response) => {
  if (!r.ok) {
    let msg = `${r.status}`
    try { const b = await r.json(); msg = typeof b.detail === 'string' ? b.detail : (b.detail?.message ?? JSON.stringify(b.detail)) } catch { /* keep status */ }
    throw new Error(msg)
  }
  return r.json()
}
export const get = <T,>(path: string): Promise<T> => fetch(`${API}${path}`).then(json)
export const send = <T,>(path: string, method: string, body?: unknown): Promise<T> =>
  fetch(`${API}${path}`, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) }).then(json)

export const modeKeys = (sid: string | null) => ({
  all: ['modes', sid] as const,
  overview: ['modes', sid, 'overview'] as const,
  energy: ['modes', sid, 'energy'] as const,
  data: ['modes', sid, 'data'] as const,
  equip: ['modes', sid, 'equip'] as const,
  proposals: ['modes', sid, 'proposals'] as const,
  stale: ['modes', sid, 'stale'] as const,
})

export function useModes(sid: string | null) {
  return useQuery<ModesOverview>({ queryKey: modeKeys(sid).overview, queryFn: () => get(`/studies/${sid}/modes`),
    enabled: !!sid, refetchInterval: 5000 })
}

export function useInvalidateModes(sid: string | null) {
  const qc = useQueryClient()
  return () => qc.invalidateQueries({ queryKey: modeKeys(sid).all })
}
