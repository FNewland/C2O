/**
 * Review gates of a study's gate profile (WP6, Nov 2026).
 *
 *   useGateProfiles()            GET /api/gate-profiles
 *   useStudyGates(study)         GET /api/studies/{id}/gates          — profile + each gate's state
 *   useGateReview(study, gate)   GET /api/studies/{id}/rules/gates/{gate}
 *
 * The checklist is evaluated on the server from the stored study only: no mission
 * need or parameters are sent (WP0: the panel used to send the empty legacy store,
 * so the MDR always said "Problem statement is empty").
 */
import { useQuery } from '@tanstack/react-query'

const API = '/api'

export type Bilingual = { en: string; fr: string }

/** The label in the UI language (English when French is missing). */
export function pick(label: Bilingual | string | null | undefined, lang: string): string {
  if (!label) return ''
  if (typeof label === 'string') return label
  return (lang === 'fr' ? label.fr : label.en) || label.en || ''
}

export type GateState = 'not_ready' | 'ready' | 'under_review' | 'passed' | 'reopened'

export interface GateCriterion {
  id: string
  question: string
  category: string
  priority: 'must_pass' | 'should_pass' | string
  advisory: boolean
  status: 'pass' | 'fail' | 'manual' | 'not_evaluated'
  verdict: 'pass' | 'fail' | 'advisory' | 'manual' | 'not_evaluated'
  evidence_required?: string
  evidence_found: string
  evidence_key?: string
  evidence_params?: Record<string, string | number>
  owner_seat?: string | null
  owner_seat_label?: Bilingual | null
  step?: string | null
  step_label?: Bilingual | null
  fix?: string | null
  canonical_gate?: string
}

export interface RuleCheck {
  id: string
  label: Bilingual
  status: 'pass' | 'warn' | 'fail' | 'not_evaluated'
  detail: Bilingual | string
  standard_ref?: string
  c2o_default?: boolean
}

export interface ProfileGate { id: string; short: string; name: Bilingual; covers: string[]; margin_gate: string }

export interface GateProfile {
  id: string
  label: Bilingual
  description?: Bilingual
  source?: string
  skin: boolean
  default: boolean
  gates: ProfileGate[]
}

export interface GateHistory { action: string; from: string; to: string; at: string; by: string; note?: string }
export interface GateBaseline { id: string | null; at: string; by: string; products: string[]; error?: string }

export interface GateSummary {
  total: number; pass: number; fail: number; manual: number; not_evaluated: number
  advisory: number; must_pass: number; must_pass_met: number
}

export interface GateResult {
  study_id: string
  profile: GateProfile
  gate: ProfileGate
  state: GateState
  history: GateHistory[]
  baselines: GateBaseline[]
  products_baselined: Array<{ id: string; label: Bilingual; owner_seat: string }>
  criteria: GateCriterion[]
  checks: RuleCheck[]
  summary: GateSummary
  ready: boolean
  ready_pending_manual: boolean
  open_owner_seats: string[]
  system_margin: { gate: string; mass_percent: number; power_percent: number }
}

export interface StudyGates {
  study_id: string
  profile: GateProfile
  current_gate: string | null
  gates: Array<ProfileGate & { state: GateState; ready: boolean; summary: GateSummary; open_owner_seats: string[]; passed_at: string | null }>
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json() as Promise<T>
}

export function useGateProfiles() {
  return useQuery<{ default: string; profiles: GateProfile[] }>({
    queryKey: ['gate-profiles'],
    queryFn: () => getJson(`${API}/gate-profiles`),
    staleTime: 60_000,
  })
}

export function useStudyGates(studyId: string | null) {
  return useQuery<StudyGates>({
    queryKey: ['gates', studyId],
    queryFn: () => getJson(`${API}/studies/${encodeURIComponent(studyId || '')}/gates`),
    enabled: !!studyId,
    staleTime: 5_000,
  })
}

export function useGateReview(studyId: string | null, gate: string | null) {
  return useQuery<GateResult>({
    queryKey: ['gate-review', studyId, gate],
    queryFn: async () => {
      const data = await getJson<GateResult>(`${API}/studies/${encodeURIComponent(studyId || '')}/rules/gates/${encodeURIComponent(gate || '')}`)
      if (!data || !Array.isArray(data.criteria)) throw new Error('bad response')
      return data
    },
    enabled: !!studyId && !!gate,
    retry: 1,
    staleTime: 5_000,
    structuralSharing: false,
  })
}

export class GateActionError extends Error {
  code: string
  constructor(code: string, message: string) { super(message); this.code = code }
}

export async function gateAction(studyId: string, gate: string, action: 'start' | 'cancel' | 'pass' | 'reopen', by: string): Promise<GateResult> {
  const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/gates/${encodeURIComponent(gate)}/review`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action, by }),
  })
  if (!res.ok) {
    let code = String(res.status), message = ''
    try { const d = (await res.json())?.detail; code = d?.code ?? code; message = d?.message ?? '' } catch { /* not JSON */ }
    throw new GateActionError(code, message)
  }
  return res.json()
}

export async function setGateProfile(studyId: string, profile: string): Promise<void> {
  const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/gate-profile`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ profile }),
  })
  if (!res.ok) throw new Error(`${res.status}`)
}
