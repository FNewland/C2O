/**
 * cdrApi — client for the CDR design model (routers/cdr.py): TM/TC database, FDIR, AOCS
 * modes, TT&C rate ladder, power-line states per mode, operations organisation.
 *
 *   GET    /api/studies/{sid}/cdr                       rows by kind, checks, HK budget, FMECA coverage
 *   POST   /api/studies/{sid}/cdr/propose
 *   POST   /api/studies/{sid}/cdr/{kind}                {data}
 *   PATCH  /api/studies/{sid}/cdr/{kind}/{id}           {data? | status | accept_update | dismiss_update}
 *   DELETE /api/studies/{sid}/cdr/{kind}/{id}
 *   POST   /api/studies/{sid}/cdr/accept-all            {group}
 *   POST   /api/studies/{sid}/cdr/import/eosat1         {replace?}
 *   DELETE /api/studies/{sid}/cdr/import
 *
 * Writes go through the seat-aware window.fetch (seats/api.ts): a change to another seat's
 * row asks first, then becomes a pending change for the owner.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import type { Bilingual } from '../types/interfaces'
import type { Finding, RowStatus } from '../workbench/electricalApi'

const API = '/api'

export type CdrKind =
  | 'settings' | 'apids' | 'services' | 'parameters' | 'hk' | 'commands' | 'events' | 'rate_tiers' | 'ttc'
  | 'monitors' | 'event_actions' | 'load_shed' | 'safe_mode' | 'fdir_levels' | 'limits'
  | 'aocs_modes' | 'aocs_transitions' | 'aocs_control' | 'line_states'
  | 'positions' | 'gonogo' | 'flight_rules'
  | 'link_framing' | 'stores' | 'rt_profiles' | 'service_allowances' | 'payload_products' | 'pass_classes' | 'pass_plan'

export type CdrGroup = 'tmtc' | 'fdir' | 'aocs' | 'ops'

/* eslint-disable @typescript-eslint/no-explicit-any */
export interface CdrRow<D = Record<string, any>> {
  id: string; study_id: string; kind: CdrKind; key: string; data: D; owner_seat: string
  status: RowStatus; origin: string; rationale: Bilingual | null; standard_ref: string | null
  edited: boolean; review: null | 'stale' | 'orphan'; proposed: Record<string, unknown> | null; version: number
}

export interface BudgetRegime {
  regime: 'bootloader' | 'safe' | 'nominal' | 'downlink'; tier: string | null; tier_bps: number | null
  hk_bps: number; budget_bps: number | null; use_percent: number | null; ok: boolean | null; sids: number[]
}
export interface CdrView {
  study_id: string
  dataset: 'empty' | 'design' | 'reference'
  rows: Record<CdrKind, CdrRow[]>
  checks: Finding[]
  summary: { alarm: number; caution: number; by_group: Record<string, { alarm: number; caution: number }> }
  budget: {
    sids: { sid: number; name: string; bytes: number; period_s: number; bps: number; enabled_at_boot: boolean; beacon: boolean }[]
    regimes: BudgetRegime[]
    modes: { mode_id: string; mode: string; regime: string; tier: string | null; hk_bps: number | null; budget_bps: number | null; ok: boolean | null }[]
    hk_share_percent: number; frame_efficiency: number; packet_overhead_bytes: number; standard_ref: string
    excluded_sids?: number[]
  }
  fmeca: {
    rows: { fmeca_row_id: string; element_id: string; component: string; mode: Bilingual | string; severity: number; critical: boolean
      monitors: string[]; monitors_counted: string[]; actions: string[]; detected: boolean; recovered: boolean }[]
    summary: { modes: number; critical: number; critical_detected: number; critical_recovered: number }
    severity_needing_recovery: number
  }
  owners: Record<CdrKind, string>
  modes: { id: string; name: string; kind: string }[]
  lines: { id: string; name: string; line_no: number; switchable: boolean; status: string }[]
  vocabulary: {
    check_types: string[]; monitor_severities: string[]; event_severities: string[]; types: string[]
    modulations: string[]; codings: string[]; criticalities: string[]; triggers: string[]; limits: string[]
    subsystems: { key: string; label: Bilingual; seat: string }[]
    pus_services: { service: number; name: Bilingual }[]
  }
  refs: Record<string, { standard_ref: string; c2o_default: boolean }>
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = res.statusText
    try { const j = await res.json(); msg = typeof j.detail === 'string' ? j.detail : (j.detail?.message ?? JSON.stringify(j.detail ?? j)) } catch { /* not JSON */ }
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export function useCdr(studyId: string | null) {
  return useQuery<CdrView>({
    queryKey: ['cdr', studyId],
    queryFn: async () => json<CdrView>(await fetch(`${API}/studies/${studyId}/cdr`)),
    enabled: !!studyId, refetchInterval: 8000, structuralSharing: false,
  })
}

export function useInvalidateCdr(studyId: string | null) {
  const qc = useQueryClient()
  return () => { for (const k of ['cdr', 'gates', 'data-budget']) qc.invalidateQueries({ queryKey: [k, studyId] }) }
}

export interface ProposeResult { created: number; updated: number; removed: number; unchanged: number; skipped_rejected: number }

export async function proposeCdr(studyId: string): Promise<ProposeResult> {
  return json(await fetch(`${API}/studies/${studyId}/cdr/propose`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
  }))
}

export async function acceptAllCdr(studyId: string, group: CdrGroup): Promise<{ accepted: number; left_for_owner: number }> {
  return json(await fetch(`${API}/studies/${studyId}/cdr/accept-all`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ group }),
  }))
}

export async function importEosat1(studyId: string, replace = false): Promise<{ imported: number; counts: Record<string, number> }> {
  return json(await fetch(`${API}/studies/${studyId}/cdr/import/eosat1`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ replace }),
  }))
}

export async function removeImport(studyId: string): Promise<{ removed: number }> {
  return json(await fetch(`${API}/studies/${studyId}/cdr/import`, { method: 'DELETE' }))
}

export async function patchCdr(studyId: string, kind: CdrKind, id: string, body: Record<string, unknown>): Promise<unknown> {
  return json(await fetch(`${API}/studies/${studyId}/cdr/${kind}/${id}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  }))
}

export async function createCdr(studyId: string, kind: CdrKind, data: Record<string, unknown>): Promise<unknown> {
  return json(await fetch(`${API}/studies/${studyId}/cdr/${kind}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ data }),
  }))
}

export async function deleteCdr(studyId: string, kind: CdrKind, id: string): Promise<unknown> {
  return json(await fetch(`${API}/studies/${studyId}/cdr/${kind}/${id}`, { method: 'DELETE' }))
}

export const hex4 = (n: unknown) => (typeof n === 'number' ? `0x${n.toString(16).toUpperCase().padStart(4, '0')}` : '')

/** Rows of a kind that count (not rejected). */
export const live = (rows: CdrRow[] | undefined) => (rows ?? []).filter(r => r.status !== 'rejected')

// ───────────────────────────────────────────────────────────── data budget (W3.02, services/data_budget.py)

export interface DbSid {
  row_id: string; sid: number; store_sid: number | null; name: string; subsystem: string; bytes: number; n_parameters: number
  diagnostic: boolean; beacon: boolean; enabled: { realtime: boolean; stored: boolean }; designed: boolean
  rt_period_by_mode: Record<string, number | null> | null; store_period_by_mode: Record<string, number | null> | null
  rt_interval_by_mode: Record<string, number | null>; store_interval_by_mode: Record<string, number | null>
  rt_bps_by_mode: Record<string, number>; store_bps_by_mode: Record<string, number>
}
export interface DbMode { id: string; name: string; kind: string; orbit_fraction: number | null; in_mix: boolean
  rt_bps: number; rt_beacon_bps: number; rt_diag_bps: number; store_bps: number; store_diag_bps: number; store_mb_per_day: number }
export interface DbCase { id: string; label: Bilingual; capacity_mb: number; rt_hk_mb: number; stored_hk_mb: number; science_mb: number
  other_mb: number; demand_mb: number; margin_pct: number | null; status: 'pass' | 'warn' | 'fail' | 'not_evaluated' }
export interface DbStore { id: number; name: string; size_mb: number | null; circular: boolean; location: string | null
  fill_mb_per_day: Record<string, number>; days_held: Record<string, number | null>; fill_mb_per_orbit?: number; orbits_held?: number | null
  check?: { min_days: number; worst_mb_per_day: number; need_mb: number; ok: boolean | null } }
export interface DbProfile { name: string; description: Bilingual | null; designed_bps: number; allocation_bps: number | null; pass_bps: number
  reserve_bps: number | null; tier_fit: { tier: string; bps: number; hk_budget_bps: number; ok: boolean }[] }
export interface DbPass { index: number; local: string; minutes: number; max_elevation_deg: number; stations: string[]; class: string
  first_vc: string; usable_min: number; channel_mb: number; rt_hk_mb: number; delayed_hk_mb: number; payload_mb: number }
export interface DataBudgetView {
  study_id: string; status: 'designed' | 'legacy' | 'not_designed'; hk_source: string
  packet: { overhead_bytes: number; breakdown: Record<string, number> }
  sids: DbSid[]; modes: DbMode[]; mix: { mode_id: string; name: string; share: number }[]
  profiles: DbProfile[]
  realtime: { full_designed_bps: number; full_allocation_bps: number | null; lean_bps: number; diag_bps: number; with_diag_bps: number }
  stored: { mix_bps: number; mb_per_day: number; events_mb_per_day: number; diag_mb_per_orbit: number }
  framing: { frame_efficiency: number; raw_rate_bps: number; information_rate_bps: number; acquisition_s: number; availability: number; designed: boolean }
  capacity: { union_min_per_day: number; usable_min_per_day: number; raw_mb_per_day: number; capacity_mb_per_day: number
    /** wave 3 (3.H2) */
    remaining_after_realtime_hk_mb_per_day?: number; allocatable_percent?: number; allocatable_mb_per_day?: number }
  contacts: { union: Record<string, number>; stations: { id: string; name: string; min_per_day: number; passes_per_day: number }[] }
  science: { target_mb_per_day: number | null; compression_ratio: number; cfdp_efficiency: number; raw_mb_per_day: number
    delivered_mb_per_day: number; on_channel_mb_per_day: number; compression_needed: number | null; compression_ok: boolean | null
    largest_with_margin_mb_per_day: number }
  pass_classes: { name: string; per_day: number; usable_min_per_day: number; rt_profile: string; rt_bps: number; order: string[]; rt_mb_per_day: number }[]
  cases: DbCase[]; closure: DbCase; margin_required_percent: number
  stores: DbStore[]
  day_in_the_life: { day_index: number | null; utc_offset_h: number; windows: DbPass[]; totals: Record<string, number>; after_availability: Record<string, number> }
  backlog: { days: number[]; vc1_mb: number[]; vc2_mb: number[]; growing?: boolean }
  link?: { band: string; rate_bps: number; rate_source: string }
  warnings: string[]
}

export function useDataBudget(studyId: string | null) {
  return useQuery<DataBudgetView>({
    queryKey: ['data-budget', studyId],
    queryFn: async () => json<DataBudgetView>(await fetch(`${API}/studies/${studyId}/data-budget`)),
    enabled: !!studyId, refetchInterval: 15000, structuralSharing: false,
  })
}

export function useInvalidateDataBudget(studyId: string | null) {
  const qc = useQueryClient()
  return () => { for (const k of ['data-budget', 'cdr']) qc.invalidateQueries({ queryKey: [k, studyId] }) }
}

export async function dataBudgetScenario(studyId: string, body: Record<string, unknown>): Promise<DataBudgetView> {
  return json(await fetch(`${API}/studies/${studyId}/data-budget/scenario`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  }))
}

export const tmtcExportUrl = (studyId: string, fmt: 'csv' | 'xlsx' | 'json') => `${API}/studies/${studyId}/cdr/export/tmtc.${fmt}`
export const contactsExportUrl = (studyId: string) => `${API}/studies/${studyId}/contacts?format=csv`
