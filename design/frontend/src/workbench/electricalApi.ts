/**
 * electricalApi — client for the electrical / data-handling rows and the interface
 * requirements (design rules EI-01, EI-02, EB-08, IF-01 … IF-05).
 *
 *   GET    /api/studies/{sid}/electrical                 rails, lines, buses, nodes, ports, checks, profile
 *   POST   /api/studies/{sid}/electrical/propose
 *   POST   /api/studies/{sid}/electrical/{kind}
 *   PATCH  /api/studies/{sid}/electrical/{kind}/{id}     fields | status | accept_update | dismiss_update
 *   DELETE /api/studies/{sid}/electrical/{kind}/{id}
 *   GET    /api/studies/{sid}/interface-requirements
 *   POST   /api/studies/{sid}/interface-requirements/{rid}/accept-update | dismiss-update
 *   POST   /api/studies/{sid}/interfaces/{iid}/agreement {side, agree}
 *
 * Writes go through the seat-aware window.fetch (seats/api.ts): a change to another seat's
 * row asks first, then becomes a pending change for the owner.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { pickLang, type Bilingual } from '../types/interfaces'

const API = '/api'

export type RowStatus = 'suggested' | 'accepted' | 'rejected'
export type Kind = 'rails' | 'lines' | 'buses' | 'nodes' | 'ports'

interface Proposal {
  id: string
  study_id: string
  status: RowStatus
  origin: string
  rationale: Bilingual | null
  standard_ref: string | null
  edited: boolean
  review: null | 'stale' | 'orphan'
  proposed: Record<string, unknown> | null
  version: number
}

export interface Rail extends Proposal {
  eps_element_id: string | null; name: string; voltage_v: number; regulated: boolean
  max_current_a: number | null; v_min: number | null; v_max: number | null
}
export interface PowerLine extends Proposal {
  eps_element_id: string | null; rail_id: string | null; line_no: number; name: string; switchable: boolean
  lcl_limit_a: number | null; default_on_separation: boolean; default_on_boot: boolean
  inhibits: string[]; load_element_ids: string[]
}
export interface DataBus extends Proposal {
  name: string; protocol: string; segment: string; bit_rate_bps: number | null; redundancy: string
  master_element_id: string | null; max_devices: number | null
}
export interface BusNode extends Proposal {
  bus_id: string; element_id: string; role: 'master' | 'node'; address: number | null
  data_rate_bps: number | null; interface_id: string | null
}
export interface Port extends Proposal {
  element_id: string; kind: string; name: string; connector: string | null
  properties: Record<string, unknown>; interface_ids: string[]; line_id: string | null; bus_id: string | null
}
export interface Finding {
  id: string; rule: string; severity: 'caution' | 'alarm'; target_kind: string; target_id: string
  element_ids: string[]; message: Bilingual; values: Record<string, unknown>
}
export interface ElectricalView {
  rails: Rail[]; lines: PowerLine[]; buses: DataBus[]; nodes: BusNode[]; ports: Port[]
  checks: Finding[]
  profile: { unregulated_bus_v?: number; battery_bus_by_class?: number; data_protocol_by_class?: string
    ttc_band_by_class?: string; sources?: Record<string, string[]> }
  spacecraft_class: string | null
  protocols: Record<string, { bit_rate_bps?: number; max_devices?: number; address_min?: number; address_max?: number; topology?: string }>
  inhibit_ids: string[]
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = res.statusText
    try { const j = await res.json(); msg = typeof j.detail === 'string' ? j.detail : (j.detail?.message ?? JSON.stringify(j.detail ?? j)) } catch { /* not JSON */ }
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export function useElectrical(studyId: string | null) {
  return useQuery<ElectricalView>({
    queryKey: ['electrical', studyId],
    queryFn: async () => json<ElectricalView>(await fetch(`${API}/studies/${studyId}/electrical`)),
    enabled: !!studyId, refetchInterval: 5000, structuralSharing: false,
  })
}

export async function proposeElectrical(studyId: string): Promise<{ created: number; updated: number; removed: number; unchanged: number }> {
  return json(await fetch(`${API}/studies/${studyId}/electrical/propose`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
  }))
}

export async function patchRow(studyId: string, kind: Kind, id: string, body: Record<string, unknown>): Promise<unknown> {
  return json(await fetch(`${API}/studies/${studyId}/electrical/${kind}/${id}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  }))
}

export async function createRow(studyId: string, kind: Kind, body: Record<string, unknown>): Promise<unknown> {
  return json(await fetch(`${API}/studies/${studyId}/electrical/${kind}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  }))
}

export async function deleteRow(studyId: string, kind: Kind, id: string): Promise<unknown> {
  return json(await fetch(`${API}/studies/${studyId}/electrical/${kind}/${id}`, { method: 'DELETE' }))
}

// ─── Interface requirements ───

export interface InterfaceRequirement {
  id: string; code: string; text: string; status: string; level: 'interface'
  verification_method: string | null; responsible_position: string | null; element_id: string | null
  ir_json: {
    origin?: string; template_id?: string; interface_id?: string; review?: null | 'stale' | 'retire'
    text_i18n?: Bilingual | null; proposed_text?: Bilingual | null; missing?: string[]; edited?: boolean
  } | null
  interface?: { id: string; name: string; type: string; status: string; from_element_id: string; to_element_id: string } | null
}
export interface Agreement {
  state: 'identified' | 'defined' | 'agreed' | 'verified'
  provider_seat: string | null; consumer_seat: string | null
  provider: { by: string; at: string; seat: string | null } | null
  consumer: { by: string; at: string; seat: string | null } | null
  reset_at?: string | null
}
export interface IrdView {
  requirements: InterfaceRequirement[]
  status: { accepted: number; with_requirements: number; approved: number; agreed: number; complete: number
    without_interface: string[]; stale: string[] }
  agreements: Record<string, Agreement>
}

export function useInterfaceRequirements(studyId: string | null) {
  return useQuery<IrdView>({
    queryKey: ['interface-requirements', studyId],
    queryFn: async () => json<IrdView>(await fetch(`${API}/studies/${studyId}/interface-requirements`)),
    enabled: !!studyId, refetchInterval: 5000, structuralSharing: false, retry: false,
  })
}

export async function irUpdate(studyId: string, rid: string, action: 'accept-update' | 'dismiss-update'): Promise<unknown> {
  return json(await fetch(`${API}/studies/${studyId}/interface-requirements/${rid}/${action}`, { method: 'POST' }))
}

export async function setAgreement(studyId: string, iid: string, side: 'provider' | 'consumer' | 'both', agree: boolean): Promise<unknown> {
  return json(await fetch(`${API}/studies/${studyId}/interfaces/${iid}/agreement`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ side, agree }),
  }))
}

/** Invalidate everything an electrical or IR change can move. */
export function useInvalidateElectrical(studyId: string | null) {
  const qc = useQueryClient()
  return () => {
    for (const k of ['electrical', 'interface-requirements', 'requirements', 'interfaces']) qc.invalidateQueries({ queryKey: [k, studyId] })
  }
}

export const hex = (n: number | null | undefined, width = 2) =>
  n == null ? '' : `0x${n.toString(16).toUpperCase().padStart(width, '0')}`

/** "0x1A", "26" → 26; "" → null; NaN → undefined (invalid). */
export function parseAddress(s: string): number | null | undefined {
  const v = s.trim()
  if (!v) return null
  const n = /^0x/i.test(v) ? parseInt(v.slice(2), 16) : Number(v)
  return Number.isInteger(n) && n >= 0 ? n : undefined
}

/** The element fields the Electrical and Data tabs read. */
export interface ElementLite {
  id: string; name: string; element_type?: string; deleted_at?: string | null; parent_id?: string | null
  power_avg_w?: number | null; power_peak_w?: number | null; quantity?: number | null
}

/** Interface requirement text in the current language (generated ones carry EN + FR). */
export function irText(r: Pick<InterfaceRequirement, 'text' | 'ir_json'>, lang: string): string {
  const i18n = r.ir_json?.text_i18n
  return (i18n && pickLang(i18n, lang)) || r.text
}
