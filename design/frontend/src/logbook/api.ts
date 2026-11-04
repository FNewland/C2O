/**
 * Logbook API client (docs/plan_2026-11/LOGBOOK_SPEC.md §3). Same paths and
 * JSON shapes as the ops tools; SpaceCDF writes with tool "design".
 * The text lives on the server for 48 h; nothing is kept in the browser
 * except an unsent draft (sessionStorage).
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getLang } from '../i18n'
import type { WhereTarget } from '../where/where'
import type { ExternalLink } from '../where/links'

export const TOOL = 'design'
const BASE = '/api/logbook'

export type EntryKind = 'decision' | 'thought' | 'observation' | 'reflection' | 'worksheet'
export type Context = Record<string, string | number | boolean | null>

export interface Entry {
  id: string
  ts: string
  updated_ts: string
  edited: boolean
  tool: string
  kind: EntryKind
  text: string
  context: Context
  worksheet: { id: string; q: string; title?: string; q_text?: string; checked?: boolean; section?: string } | null
  sim_ts?: string | null
  lang?: string | null
  /** A structured decision record (kind "decision"; see decisions.ts). */
  record?: DecisionRecord | null
}

// ─── Decision records (logbook/decisions.py on the server) ───

export interface RecordOption {
  name: string
  summary?: string
  values?: Record<string, string | number | boolean>
  score?: number
  chosen?: boolean
}
export interface RecordCriterion { name: string; weight?: number; direction?: 'higher' | 'lower' }
export interface RecordEvidence {
  label: string
  value?: string | number | boolean
  unit?: string
  before?: string | number
  after?: string | number
}
export interface DecisionRecord {
  decision_id: string
  subject?: string
  question?: string
  part?: string
  part_title?: string
  gate?: string
  seat?: string
  options?: RecordOption[]
  criteria?: RecordCriterion[]
  choice?: string
  rationale?: string
  evidence?: RecordEvidence[]
  consequences?: string
  margin_impact?: string
  open_issues?: string
  capture?: string
}
export type RecordField = 'options' | 'criteria' | 'choice' | 'rationale' | 'evidence' | 'consequences' | 'margin_impact' | 'open_issues'

export interface CatalogueDecision {
  id: string
  part: string
  worksheet: string
  q: string
  worksheet_title: string | null
  part_title: string | null
  question: string
  hint: string | null
  seat: string
  seat_label: string
  gate: string
  fields: RecordField[]
  prefill: string[]
  capture: string[]
  /** Where in SpaceCDF it is decided, textbook sections, external reading (where_map.yaml). */
  where?: WhereTarget[]
  book?: string[]
  links?: ExternalLink[]
  entries: string[]
  status: 'open' | 'recorded'
}
export interface Catalogue {
  lang: string
  study_id: string | null
  /** The study's gate profile (WP6): ids and labels of ITS gates (cr in the ESA IOD profile, MCR in the NASA skin…) */
  gates: { id: string; short?: string; label: string; ui_gates: string[]; covers?: string[] }[]
  seats: { id: string; label: string }[]
  fields: Record<RecordField, string>
  sources: Record<string, { label: string; server: boolean }>
  decisions: CatalogueDecision[]
  counts: Record<string, { total: number; open: number }>
  due?: { gate: string; short?: string; total: number; open: string[]; recorded: string[] }
}
export interface Prefill extends Partial<DecisionRecord> { sources?: string[] }

export interface Summary {
  person: { id_label: string; local: boolean }
  retention_h: number
  max_age_h: number
  expires_at: string | null
  last_write: string | null
  last_download: string | null
  entries: Entry[]
  /** Every live entry, all tools (filters only narrow `entries`). */
  count: number
  unsaved: number
}

export interface Question {
  id: string; kind: string; text: string; prompt: string | null; points: string[]
  /** Where in SpaceCDF it is answered, textbook sections, external reading (where_map.yaml). */
  where?: WhereTarget[]; book?: string[]; links?: ExternalLink[]
}
export interface Worksheet {
  id: string
  number: string
  title: string
  phase: 'prep' | 'during' | 'debrief' | 'exercise'
  match: boolean
  questions: Question[]
  answered: Record<string, string[]>
}

export class LogbookHttpError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, { credentials: 'same-origin', ...init,
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined })
  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail || detail } catch { /* not JSON */ }
    throw new LogbookHttpError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export const LOGBOOK_KEY = ['logbook'] as const

export function useLogbook() {
  return useQuery<Summary>({
    queryKey: [...LOGBOOK_KEY, getLang()],
    queryFn: () => call<Summary>(`?lang=${getLang()}`),
    staleTime: 15_000,
    refetchOnWindowFocus: true,
    refetchInterval: 60_000,   // keeps the expiry banner and badge honest
    retry: 1,
  })
}

export function useWorksheets(context: Context, all: boolean, enabled = true) {
  const lang = getLang()
  const ctx = JSON.stringify(context)
  return useQuery<{ worksheets: Worksheet[] }>({
    queryKey: ['logbook-worksheets', lang, ctx, all],
    queryFn: () => call(`/worksheets?tool=${TOOL}&lang=${lang}&all=${all ? 1 : 0}&context=${encodeURIComponent(ctx)}`),
    enabled,
    staleTime: 10_000,
  })
}

export const DECISIONS_KEY = ['logbook-decisions'] as const

/** The decision catalogue with this person's status for the study (and what is due by `gate`). */
export function useDecisions(studyId: string | null, gate?: string | null, enabled = true) {
  const lang = getLang()
  const q = new URLSearchParams({ lang })
  if (studyId) q.set('study_id', studyId)
  if (gate) q.set('gate', gate)
  return useQuery<Catalogue>({
    queryKey: [...DECISIONS_KEY, lang, studyId, gate ?? null],
    queryFn: () => call<Catalogue>(`/decisions?${q}`),
    enabled,
    staleTime: 15_000,
  })
}

/** What SpaceCDF can fill in for a decision from the study (open-decision list). */
export function fetchPrefill(decisionId: string, studyId: string | null): Promise<Prefill> {
  const q = new URLSearchParams({ lang: getLang() })
  if (studyId) q.set('study_id', studyId)
  return call<Prefill>(`/decisions/${encodeURIComponent(decisionId)}/prefill?${q}`)
}

export function useLogbookMutations() {
  const qc = useQueryClient()
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: LOGBOOK_KEY })
    void qc.invalidateQueries({ queryKey: ['logbook-worksheets'] })
    void qc.invalidateQueries({ queryKey: DECISIONS_KEY })
  }
  return {
    refresh,
    add: async (body: { kind: EntryKind; text: string; context?: Context; worksheet?: Entry['worksheet'] }) => {
      const e = await call<Entry>('/entries', { method: 'POST',
        body: JSON.stringify({ ...body, tool: TOOL, lang: getLang() }) })
      refresh()
      return e
    },
    /** A decision record: the server writes the text, workbook part and decision id. */
    addDecision: async (record: DecisionRecord, context: Context) => {
      const e = await call<Entry>('/entries', { method: 'POST',
        body: JSON.stringify({ kind: 'decision', text: '-', record, context, tool: TOOL, lang: getLang() }) })
      refresh()
      return e
    },
    editDecision: async (id: string, record: DecisionRecord) => {
      const e = await call<Entry>(`/entries/${encodeURIComponent(id)}`, { method: 'PATCH',
        body: JSON.stringify({ text: '-', record, lang: getLang() }) })
      refresh()
      return e
    },
    edit: async (id: string, text: string) => {
      const e = await call<Entry>(`/entries/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ text }) })
      refresh()
      return e
    },
    remove: async (id: string) => {
      await call(`/entries/${encodeURIComponent(id)}`, { method: 'DELETE' })
      refresh()
    },
    deleteAll: async () => {
      await call('', { method: 'DELETE' })
      refresh()
    },
  }
}

function localZone(): string {
  try { return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC' } catch { return 'UTC' /* old browser */ }
}

function exportQuery(format: string, opts: { studyId?: string | null; worksheet?: string; inline?: boolean } = {}): string {
  const q = new URLSearchParams({ format, lang: getLang(), tz: localZone() })
  if (opts.studyId) q.set('study_id', opts.studyId)
  if (opts.worksheet) q.set('worksheet', opts.worksheet)
  if (opts.inline) q.set('inline', '1')
  return q.toString()
}

/** One worksheet as Markdown text, for "Copy as Markdown" (not counted as a download). */
export async function worksheetMarkdown(worksheet: string, studyId: string | null): Promise<string> {
  const res = await fetch(`${BASE}/export?${exportQuery('md', { studyId, worksheet, inline: true })}`, { credentials: 'same-origin' })
  if (!res.ok) throw new LogbookHttpError(res.status, res.statusText)
  return res.text()
}

/** "Download this worksheet": one worksheet, every part, its open decisions. */
export function downloadWorksheet(worksheet: string, studyId: string | null, format: 'md' | 'html' = 'md') {
  const a = document.createElement('a')
  a.href = `${BASE}/export?${exportQuery(format, { studyId, worksheet })}`
  a.download = ''
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  a.remove()
}

/** Download the whole logbook (every tool), laid out as the workbook. The server records the download. */
export function download(format: 'md' | 'html', onDone?: () => void, studyId?: string | null) {
  const a = document.createElement('a')
  a.href = `${BASE}/export?${exportQuery(format, { studyId })}`
  a.download = ''
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  a.remove()
  // The marker is written while the file is served; refresh shortly after.
  if (onDone) window.setTimeout(onDone, 800)
}
