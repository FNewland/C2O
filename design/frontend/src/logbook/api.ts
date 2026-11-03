/**
 * Logbook API client (docs/plan_2026-11/LOGBOOK_SPEC.md §3). Same paths and
 * JSON shapes as the ops tools; SpaceCDF writes with tool "design".
 * The text lives on the server for 48 h; nothing is kept in the browser
 * except an unsent draft (sessionStorage).
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getLang } from '../i18n'

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
  worksheet: { id: string; q: string; title?: string; question?: string } | null
  sim_ts?: string | null
  lang?: string | null
}

export interface Summary {
  person: { id_label: string; local: boolean }
  retention_h: number
  max_age_h: number
  expires_at: string | null
  last_write: string | null
  last_download: string | null
  entries: Entry[]
  count: number
  total: number
  unsaved: number
}

export interface Question { id: string; kind: string; text: string; prompt: string | null; points: string[] }
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

export function useLogbookMutations() {
  const qc = useQueryClient()
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: LOGBOOK_KEY })
    void qc.invalidateQueries({ queryKey: ['logbook-worksheets'] })
  }
  return {
    refresh,
    add: async (body: { kind: EntryKind; text: string; context?: Context; worksheet?: Entry['worksheet'] }) => {
      const e = await call<Entry>('/entries', { method: 'POST',
        body: JSON.stringify({ ...body, tool: TOOL, lang: getLang() }) })
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

/** Download the whole logbook (every tool). The server records the download. */
export function download(format: 'md' | 'html', onDone?: () => void) {
  const a = document.createElement('a')
  let tz = 'UTC'
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC' } catch { /* old browser: UTC */ }
  a.href = `${BASE}/export?format=${format}&lang=${getLang()}&tz=${encodeURIComponent(tz)}`
  a.download = ''
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  a.remove()
  // The marker is written while the file is served; refresh shortly after.
  if (onDone) window.setTimeout(onDone, 800)
}
