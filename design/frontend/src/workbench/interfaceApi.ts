/**
 * interfaceApi — client for the interface contract (SpaceCDF brief, API
 * contract section). Every panel that shows links reads through here, so the
 * Interfaces panel, the block diagram, the ICD, readiness and the Spacecraft
 * view agree on one normalised object.
 *
 *   GET    /api/studies/{sid}/interfaces
 *   GET    /api/studies/{sid}/interfaces/types
 *   POST   /api/studies/{sid}/interfaces/propose   {level?, element_id?, dry_run?}
 *   PATCH  /api/studies/{sid}/interfaces/{id}      {status, type, subtype, properties, endpoints}
 *   GET    /api/studies/{sid}/readiness?level=
 *
 * Older servers lack some of these routes; the client says so (a disabled
 * control with the reason) instead of failing silently, and PATCH falls back
 * to the legacy /api/interfaces/{id} route.
 */
import { useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  INTERFACE_TYPES, TYPE_META, normaliseInterface,
  type Bilingual, type DesignInterface, type InterfaceStatus, type InterfaceType, type TypeField,
} from '../types/interfaces'

const API = '/api'

// ─── Fetch helpers ───

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = res.statusText
    try { const j = await res.json(); msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail ?? j) } catch { /* not JSON */ }
    throw new ApiError(res.status, msg)
  }
  return res.json() as Promise<T>
}
const missing = (e: unknown) => e instanceof ApiError && (e.status === 404 || e.status === 405)

export async function fetchInterfaces(studyId: string): Promise<any[]> {
  return json<any[]>(await fetch(`${API}/studies/${studyId}/interfaces`))
}

/** All study interfaces, normalised. Shares the ['interfaces', sid] cache with the older panels. */
export function useInterfaces(studyId: string | null, opts: { poll?: boolean } = {}) {
  const q = useQuery({
    queryKey: ['interfaces', studyId],
    queryFn: () => fetchInterfaces(studyId!),
    enabled: !!studyId, structuralSharing: false,
    refetchInterval: opts.poll === false ? false : 5000,
  })
  const list = useMemo<DesignInterface[]>(() => (Array.isArray(q.data) ? q.data : []).map(normaliseInterface), [q.data])
  return { ...q, interfaces: list }
}

// ─── Types (server list, local fallback) ───

export interface TypeInfo {
  id: InterfaceType
  label: Bilingual | null
  /** Local fields (English i18n keys) */
  fields: TypeField[]
  /** Annex E reference-data fields from the server, when served (bilingual labels) */
  served: Array<{ key: string; label: Bilingual }>
  subtypes: Array<{ id: string; label: Bilingual }>
}

const bi = (l: any, fallback: string): Bilingual =>
  l && typeof l === 'object' ? { en: l.en ?? fallback, fr: l.fr ?? l.en ?? fallback } : { en: String(l ?? fallback), fr: String(l ?? fallback) }
function fieldsFrom(raw: any): Array<{ key: string; label: Bilingual }> {
  const f = raw?.fields ?? raw?.reference_data ?? raw?.reference_fields
  if (!Array.isArray(f)) return []
  return f.map((x: any) => (typeof x === 'string' ? { key: x, label: bi(null, x) } : { key: String(x?.key ?? ''), label: bi(x?.label, String(x?.key ?? '')) }))
    .filter(x => x.key)
}

export function useInterfaceTypes(studyId: string | null) {
  const q = useQuery({
    queryKey: ['interface-types', studyId],
    queryFn: async () => {
      try {
        const j = await json<any>(await fetch(`${API}/studies/${studyId}/interfaces/types`))
        return { served: true, list: Array.isArray(j) ? j : (j.types ?? []) }
      } catch (e) {
        if (missing(e)) return { served: false, list: [] as any[] }
        throw e
      }
    },
    enabled: !!studyId, staleTime: 5 * 60_000, retry: false,
  })
  const types = useMemo<TypeInfo[]>(() => {
    const served = new Map<string, any>((q.data?.list ?? []).map((t: any) => [t.id ?? t.type ?? t.value, t]))
    return INTERFACE_TYPES.map(id => {
      const s = served.get(id)
      const label = s?.label && typeof s.label === 'object' ? s.label as Bilingual : null
      const subtypes = Array.isArray(s?.subtypes)
        ? s.subtypes.map((x: any) => (typeof x === 'string' ? { id: x, label: bi(null, x) } : { id: String(x.id), label: bi(x.label, String(x.id)) }))
        : []
      return { id, label, fields: TYPE_META[id].fields, served: fieldsFrom(s), subtypes }
    })
  }, [q.data])
  return { types, served: !!q.data?.served }
}

// ─── Propose ───

export interface ProposeResult {
  created: DesignInterface[]
  updated: DesignInterface[]
  unchanged: number
  unmet: Array<{ element_id: string; need: string; reason: Bilingual }>
  conflicts: Array<{ interface_id?: string; element_ids: string[]; reason: Bilingual; severity: 'caution' | 'alarm' }>
}

/** null when this server has no proposer yet. */
export async function proposeLinks(studyId: string, body: { level?: number; element_id?: string | null; dry_run?: boolean }): Promise<ProposeResult | null> {
  try {
    const r = await json<any>(await fetch(`${API}/studies/${studyId}/interfaces/propose`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    }))
    return {
      created: (r.created ?? []).map(normaliseInterface),
      updated: (r.updated ?? []).map(normaliseInterface),
      unchanged: Number(r.unchanged ?? 0),
      unmet: Array.isArray(r.unmet) ? r.unmet : [],
      conflicts: Array.isArray(r.conflicts) ? r.conflicts : [],
    }
  } catch (e) {
    if (missing(e)) return null
    throw e
  }
}

/** Dry-run proposal for the current level: unmet needs and conflicts, without writing. */
export function useProposalCheck(studyId: string | null, level: number, elementId: string | null, stamp: string) {
  return useQuery({
    queryKey: ['interface-proposal', studyId, level, elementId, stamp],
    queryFn: () => proposeLinks(studyId!, { level, element_id: elementId, dry_run: true }),
    enabled: !!studyId, staleTime: 30_000, retry: false,
  })
}

// ─── Mutations ───

export interface InterfacePatch {
  status?: InterfaceStatus
  type?: InterfaceType
  subtype?: string | null
  properties?: Record<string, unknown>
  from_element_id?: string
  to_element_id?: string
  name?: string
  diagram_label?: string
  version?: number
}

export async function patchInterface(studyId: string, id: string, patch: InterfacePatch): Promise<DesignInterface> {
  // The legacy route only knows interface_type; send both spellings.
  const body = { ...patch, ...(patch.type ? { interface_type: patch.type } : {}) }
  const init = { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
  try {
    return normaliseInterface(await json<any>(await fetch(`${API}/studies/${studyId}/interfaces/${id}`, init)))
  } catch (e) {
    if (!missing(e)) throw e
    return normaliseInterface(await json<any>(await fetch(`${API}/interfaces/${id}`, init)))
  }
}

export async function createInterface(studyId: string, body: {
  type: InterfaceType; from_element_id: string; to_element_id: string; name?: string; direction?: string
  diagram_label?: string; subtype?: string | null; properties?: Record<string, unknown>
}): Promise<DesignInterface> {
  const res = await fetch(`${API}/interfaces/?study_id=${studyId}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ direction: 'bidirectional', ...body, interface_type: body.type, origin: 'user', status: 'accepted' }),
  })
  return normaliseInterface(await json<any>(res))
}

export async function deleteInterface(id: string): Promise<void> {
  const res = await fetch(`${API}/interfaces/${id}`, { method: 'DELETE' })
  if (!res.ok && res.status !== 404) throw new ApiError(res.status, res.statusText)
}

/** Invalidate everything an interface change can move. */
export function useInvalidateLinks(studyId: string | null) {
  const qc = useQueryClient()
  return () => {
    for (const k of ['interfaces', 'interface-proposal', 'readiness', 'icd']) qc.invalidateQueries({ queryKey: [k, studyId] })
  }
}

// ─── Readiness ───

export interface ReadinessItem {
  id: string
  label: Bilingual
  ok: boolean
  detail: Bilingual
  counts?: Record<string, number>
}

/** Server readiness for a level; `served: false` on servers without the route. */
export function useServerReadiness(studyId: string | null, level: number, elementId: string | null) {
  return useQuery({
    queryKey: ['readiness', studyId, level, elementId],
    queryFn: async () => {
      const qs = new URLSearchParams({ level: String(level) })
      if (elementId) qs.set('element_id', elementId)
      try {
        const j = await json<any>(await fetch(`${API}/studies/${studyId}/readiness?${qs}`))
        const items: ReadinessItem[] = (Array.isArray(j) ? j : (j.items ?? [])).map((x: any) => ({
          id: String(x.id), ok: !!x.ok, counts: x.counts ?? undefined,
          label: typeof x.label === 'string' ? { en: x.label, fr: x.label } : x.label ?? { en: x.id, fr: x.id },
          detail: typeof x.detail === 'string' ? { en: x.detail, fr: x.detail } : x.detail ?? { en: '', fr: '' },
        }))
        return { served: true, items }
      } catch (e) {
        if (missing(e)) return { served: false, items: [] as ReadinessItem[] }
        throw e
      }
    },
    enabled: !!studyId, refetchInterval: 8000, retry: false, structuralSharing: false,
  })
}
