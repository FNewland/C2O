/**
 * Diagram models from the server (routers/diagrams.py): one model per SEMP / ECSS diagram,
 * geometry included, so this view and the docx / SVG / PNG exports draw the same picture.
 *
 *   useDiagramCatalogue(study, gate?)   GET /api/studies/{id}/diagrams[?gate=]
 *   useDiagram(study, kind, opts)       GET /api/studies/{id}/diagrams/{kind}
 *   diagramUrl(study, kind, 'svg'|'png', opts, lang)
 */
import { useQuery } from '@tanstack/react-query'
import { create } from 'zustand'

const API = '/api'

/** Translatable text: {t: English key, p: params}; {en, fr}; or plain data. */
export type DText = string | { t: string; p?: Record<string, string | number> } | { en: string; fr?: string } | null | undefined

export interface Prov { source: string; ref?: string; origin?: string; status?: string; note?: string }
export interface DNode {
  id: string; label: DText; sub?: DText; x: number; y: number; w: number; h: number
  shape: string; style: string; badges: DText[]; group?: string; ref?: { kind: string; id: string }; prov: Prov; title?: DText
}
export interface DEdge {
  id: string; from: string; to: string; points: [number, number][]; type?: string; dash?: string; width?: number
  color?: string; arrow?: 'end' | 'start' | 'both' | 'none'; curve?: boolean; faded?: boolean; label?: DText; prov: Prov
}
export interface DGroup { id: string; label: DText; x: number; y: number; w: number; h: number; style: string; ref?: { kind: string; id: string }; prov: Prov }
export interface DLabel { x: number; y: number; text: DText; anchor: 'start' | 'middle' | 'end'; size: number; weight: number; style: string; rotate?: number }
export interface DCell {
  x: number; y: number; w: number; h: number; style: string; text?: DText; sub?: DText; title?: DText
  codes?: { type: string; c: string }[]
}
export interface DLegend { kind: 'line' | 'box' | 'dot'; label: DText; type?: string; style?: string; dash?: string; width?: number; color?: string; faded?: boolean; code?: string }
export interface DGap { code: string; message: DText; count: number; severity: 'info' | 'warn' | 'alarm'; fix?: string }
export interface DiagramModel {
  kind: string; title: DText; subtitle?: DText; view: string; width: number; height: number
  nodes: DNode[]; edges: DEdge[]; groups: DGroup[]; labels: DLabel[]; cells: DCell[]; legend: DLegend[]
  gaps: DGap[]; completeness: { expected: number; filled: number; score: number }
  table: { columns: DText[]; rows: DText[][] }; sources: string[]; notes: DText[]; empty: DText | null
  gates: { gate: string; maturity: string }[]; product: string; ref: string; group: string
  options?: { level?: string; focus?: string | null; subsystems?: { id: string; name: string }[]; which?: string; geometry?: boolean; hidden_types?: string[]; view?: string; trades?: { id: string; title: string }[] }
}
export interface CatalogueEntry {
  kind: string; title: DText; group: string; group_label: DText; gates: { gate: string; maturity: string }[]
  product: string; ref: string; link?: string | null; gaps: number; gap_alarm: number
  completeness: { expected: number; filled: number; score: number } | null; empty: boolean; top_gaps: DText[]
  instances?: string[]; views?: string[]
}
export interface Catalogue { study_id: string; gate: string | null; covers: string[] | null; diagrams: CatalogueEntry[] }

export interface DiagramOpts { level?: string; focus?: string; types?: string; view?: string }

function qs(o: Record<string, string | undefined>): string {
  const p = Object.entries(o).filter(([, v]) => v).map(([k, v]) => `${k}=${encodeURIComponent(v!)}`)
  return p.length ? `?${p.join('&')}` : ''
}

async function getJson<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${r.status}`)
  return r.json() as Promise<T>
}

export function useDiagramCatalogue(studyId: string | null, gate?: string | null) {
  return useQuery<Catalogue>({
    queryKey: ['diagram-catalogue', studyId, gate ?? null],
    queryFn: () => getJson(`${API}/studies/${encodeURIComponent(studyId || '')}/diagrams${qs({ gate: gate || undefined })}`),
    enabled: !!studyId, staleTime: 10_000,
  })
}

export function useDiagram(studyId: string | null, kind: string | null, opts: DiagramOpts = {}) {
  return useQuery<DiagramModel>({
    queryKey: ['diagram', studyId, kind, opts.level ?? '', opts.focus ?? '', opts.types ?? '', opts.view ?? ''],
    queryFn: () => getJson(`${API}/studies/${encodeURIComponent(studyId || '')}/diagrams/${kind}${qs({ ...opts })}`),
    enabled: !!studyId && !!kind, staleTime: 5_000, refetchInterval: 15_000,
  })
}

export function diagramUrl(studyId: string, kind: string, fmt: 'svg' | 'png', opts: DiagramOpts, lang: string): string {
  return `${API}/studies/${encodeURIComponent(studyId)}/diagrams/${kind}/${fmt}${qs({ ...opts, lang, download: '1' })}`
}

export function diagramDocUrl(studyId: string, set: 'semp' | 'ird' | 'se' | 'all', lang: string): string {
  return `${API}/studies/${encodeURIComponent(studyId)}/diagrams-document.docx${qs({ set, lang })}`
}

/** Which diagram the Diagrams tab shows (other views — the gate checklist — open one). */
export const useDiagramNav = create<{ kind: string; open: (kind: string) => void }>(set => ({
  kind: 'block',
  open: kind => set({ kind }),
}))
