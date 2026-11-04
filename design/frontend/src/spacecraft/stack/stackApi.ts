/**
 * Stack builder client (routers/stack.py). One query per study; every edit returns the
 * whole evaluated layout, which replaces the cache.
 *
 *   GET  /api/studies/{sid}/stack
 *   POST /api/studies/{sid}/stack/auto-place
 *   PUT  /api/studies/{sid}/stack/proposal   {spec, base_version}
 *   POST /api/studies/{sid}/stack/approve | reject
 *   GET  /api/studies/{sid}/stack/geometry?which=approved|proposal&format=json|yaml
 *
 * Frames: everything here is in the stack frame = the simulator body frame (mm, origin at
 * the envelope centre, +Z zenith, -Z nadir). The element's position_json (metres, corner
 * origin, +Z nadir) is written by the server on approval.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'

const API = '/api'

export type Bi = { en: string; fr: string }
export type CheckStatus = 'pass' | 'warn' | 'fail' | 'not_evaluated'
export type Face = 'px' | 'mx' | 'py' | 'my' | 'pz' | 'mz'
export const FACES: Face[] = ['px', 'mx', 'py', 'my', 'pz', 'mz']

export interface Tile { center_mm: number[]; size_mm: number[]; uv_mm: [number, number, number, number] }
export interface Placement {
  id: string; element_id: string; name: string; subsystem: string; role: string; mount_class: string
  column: number | null; slot: number | null; layer: 'nadir' | 'zenith' | null; face: Face | null
  anchor: 'nadir' | 'zenith' | null; center_mm: number[]; size_mm: number[]; body_h_mm: number | null
  z_mm: [number, number] | null; fits: boolean; span: boolean; mass_kg: number; power_w: number; count: number
  locked: boolean; origin: string; tiles: Tile[] | null; protrusion_mm?: number; overflow?: number
  port_rect_mm?: [number, number, number, number]; distributed?: boolean; manufacturer?: string | null
  assumptions: string[]; deployable?: { kind: string } | null
}
export interface Check {
  id: string; label: Bi; status: CheckStatus; detail: Bi; standard_ref: string; c2o_default: boolean
  element_ids?: string[]
}
export interface Spec {
  columns: string[][]; layers: { nadir: string[]; zenith: string[] }
  faces: Record<string, { face: Face; count: number }[]>; locks: Record<string, boolean>; origins?: Record<string, string>
}
export interface Column { index: number; cx: number; cy: number; inner_mm: [number, number]; order: string[]; used_mm: number; length_mm: number; free_mm: number }
export interface Evaluated {
  placements: Placement[]; columns: Column[]; cog_mm: number[]; mass_kg: number; spec: Spec; checks: Check[]
  summary: Record<CheckStatus | 'total', number>; score: Record<string, number>; cog_design_m: number[]
  assumptions: string[]; notes: string[]; positions_m: Record<string, number[]>
  meta: { origin?: string; by?: string; seat?: string; at?: string; report?: any; approved_by?: string; approved_seat?: string; approved_at?: string }
}
export interface Envelope {
  form_factor: string; size_mm: [number, number, number]; cds_mm: number[]; swap: boolean
  cog_limits_mm: [number, number, number]; cog_limits_cds_cm: number[]; end_allowance_mm: number
  z0_mm: number; z1_mm: number; internal_length_mm: number; max_protrusion_mm: number
  columns: { index: number; cx: number; cy: number; inner_mm: [number, number] }[]
  sources: Record<string, string>
}
export interface Unit { id: string; name: string; role: string; subsystem: string; mount_class: string; source: string; assumptions: string[]; mass_kg: number; power_w: number; quantity: number; manufacturer?: string | null }
export interface StackPayload {
  study_id: string; applicable: boolean; form_factor: string | null; version: number; can_approve: boolean
  owner_seat: string; owner_label: Bi; frame: { stack: string; design: string }; reason?: Bi
  /** The spacecraft this layout is for (one CubeSat per layout: the first spacecraft of the space segment). */
  spacecraft?: { id: string; name: string; count: number } | null
  envelope?: Envelope; units: Unit[]; approved: Evaluated | null; proposal: Evaluated | null
}

export class StackError extends Error {
  status: number; code?: string
  constructor(status: number, message: string, code?: string) { super(message); this.status = status; this.code = code }
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init, headers: { ...(init.body ? { 'Content-Type': 'application/json' } : {}), ...(init.headers as Record<string, string> || {}) },
  })
  if (!res.ok) {
    let detail: any = null
    try { detail = (await res.json()).detail } catch { /* not JSON */ }
    throw new StackError(res.status, typeof detail === 'string' ? detail : (detail?.message ?? res.statusText), detail?.code)
  }
  return res.json() as Promise<T>
}

export function useStack(studyId: string | null) {
  return useQuery({
    queryKey: ['stack', studyId],
    queryFn: () => call<StackPayload>(`/studies/${studyId}/stack`),
    enabled: !!studyId, refetchInterval: 8000, structuralSharing: false,
  })
}

export function useGeometry(studyId: string | null, which: 'approved' | 'proposal' | null, version: number) {
  return useQuery({
    queryKey: ['stack-geometry', studyId, which, version],
    queryFn: () => call<any>(`/studies/${studyId}/stack/geometry?which=${which}`),
    enabled: !!studyId && !!which, structuralSharing: false,
  })
}

export function useStackActions(studyId: string | null) {
  const qc = useQueryClient()
  const set = (p: StackPayload) => { qc.setQueryData(['stack', studyId], p); return p }
  return {
    autoPlace: () => call<StackPayload>(`/studies/${studyId}/stack/auto-place`, { method: 'POST', body: '{}' }).then(set),
    propose: (spec: Spec, baseVersion: number) =>
      call<StackPayload>(`/studies/${studyId}/stack/proposal`, { method: 'PUT', body: JSON.stringify({ spec, base_version: baseVersion }) }).then(set),
    approve: () => call<StackPayload>(`/studies/${studyId}/stack/approve`, { method: 'POST', body: '{}' }).then(p => {
      void qc.invalidateQueries({ queryKey: ['elements'] }); void qc.invalidateQueries({ queryKey: ['study-elements'] }); return set(p)
    }),
    reject: () => call<StackPayload>(`/studies/${studyId}/stack/reject`, { method: 'POST', body: '{}' }).then(set),
    refresh: () => qc.invalidateQueries({ queryKey: ['stack', studyId] }),
  }
}

// ─── Pure spec edits (the server normalises: anchors return to their ends) ───

export function cloneSpec(s: Spec): Spec {
  return JSON.parse(JSON.stringify({ columns: s.columns, layers: s.layers, faces: s.faces, locks: s.locks ?? {}, origins: s.origins ?? {} }))
}

/** Where a column unit is: [column, index] or null. */
export function findInColumns(s: Spec, pid: string): [number, number] | null {
  for (let c = 0; c < s.columns.length; c++) {
    const i = s.columns[c].indexOf(pid)
    if (i >= 0) return [c, i]
  }
  return null
}

/** Move a column unit to column ``to`` at index ``index`` (nadir end = 0). */
export function moveColumnItem(s: Spec, pid: string, to: number, index: number): Spec {
  const out = cloneSpec(s)
  const at = findInColumns(out, pid)
  if (!at || to < 0 || to >= out.columns.length) return out
  out.columns[at[0]].splice(at[1], 1)
  const i = Math.max(0, Math.min(index, out.columns[to].length))
  out.columns[to].splice(i, 0, pid)
  return out
}

/** Move one face group (element on a face) to another face; merges with a group already there. */
export function moveFaceGroup(s: Spec, elementId: string, from: Face, to: Face): Spec {
  const out = cloneSpec(s)
  const groups = out.faces[elementId] ?? []
  const g = groups.find(x => x.face === from)
  if (!g || from === to) return out
  const there = groups.find(x => x.face === to)
  if (there) { there.count += g.count; groups.splice(groups.indexOf(g), 1) } else g.face = to
  const wasLocked = out.locks[`${elementId}@${from}`]
  delete out.locks[`${elementId}@${from}`]
  if (wasLocked) out.locks[`${elementId}@${to}`] = true
  return out
}

export function toggleLock(s: Spec, pid: string): Spec {
  const out = cloneSpec(s)
  if (out.locks[pid]) delete out.locks[pid]; else out.locks[pid] = true
  return out
}

export const STATUS_TONE: Record<CheckStatus, 'ok' | 'caution' | 'alarm' | 'info'> = {
  pass: 'ok', warn: 'caution', fail: 'alarm', not_evaluated: 'info',
}
const ORDER: Record<CheckStatus, number> = { fail: 0, warn: 1, not_evaluated: 2, pass: 3 }
export const sortChecks = (c: Check[]) => [...c].sort((a, b) => ORDER[a.status] - ORDER[b.status] || a.id.localeCompare(b.id))

/** Subsystem colour token (theme/tokens.ts SUBSYSTEM; shared/ui-viz/stack3d.js SUBSYSTEM_TOKEN). */
export const SUBSYSTEM_TOKEN: Record<string, string> = {
  payload: 'var(--cat-1)', obdh: 'var(--cat-2)', aocs: 'var(--cat-3)', power: 'var(--cat-4)', thermal: 'var(--cat-5)',
  ttc: 'var(--cat-6)', propulsion: 'var(--cat-7)', structure: 'var(--cat-8)', other: 'var(--cat-8)',
}
export const subColor = (s: string | null | undefined) => SUBSYSTEM_TOKEN[s ?? 'other'] ?? 'var(--cat-8)'

/** Number of units in a placement (a face group can hold several). */
export const unitsOf = (p: Placement) => p.count
