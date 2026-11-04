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
  return () => { for (const k of ['cdr', 'gates']) qc.invalidateQueries({ queryKey: [k, studyId] }) }
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
