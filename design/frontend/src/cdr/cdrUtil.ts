/**
 * cdrUtil — non-component helpers of the CDR tabs: number formatting / parsing, the panel hook
 * (load, propose, import, patch), findings per tab, row classes.
 */
import { useState } from 'react'
import i18n from '../i18n'
import { useUIStore } from '../stores/uiStore'
import { pickLang } from '../types/interfaces'
import type { Finding } from '../workbench/electricalApi'
import { deleteCdr, patchCdr, useCdr, useInvalidateCdr, type CdrGroup, type CdrKind, type CdrRow, type CdrView } from './cdrApi'

/** Locale number (decimal comma in French), no grouping. */
export const fmt = (n: unknown, d = 3) => (typeof n !== 'number' || !Number.isFinite(n) ? '' : n.toLocaleString(
  i18n.language?.startsWith('fr') ? 'fr-FR' : 'en-GB', { maximumFractionDigits: d, useGrouping: false }))

export const num = (s: string): number | null | undefined => {
  const v = s.trim().replace(',', '.')
  if (!v) return null
  const n = /^0x/i.test(v) ? parseInt(v.slice(2), 16) : Number(v)
  return Number.isFinite(n) ? n : undefined
}

export function useCdrPanel() {
  const studyId = useUIStore(s => s.studyId)
  const q = useCdr(studyId)
  const invalidate = useInvalidateCdr(studyId)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastRun, setLastRun] = useState<string | null>(null)
  const run = async (key: string, fn: () => Promise<unknown>) => {
    setBusy(key); setError(null)
    try { await fn(); invalidate() } catch (e) { setError(String((e as Error).message || e)) } finally { setBusy(null) }
  }
  return {
    studyId, view: q.data, isLoading: q.isLoading, loadError: q.error as Error | null,
    busy, error, lastRun, setLastRun, run,
    patch: (kind: CdrKind, id: string, body: Record<string, unknown>) => run(id, () => patchCdr(studyId!, kind, id, body)),
    patchData: (kind: CdrKind, id: string, data: Record<string, unknown>) => run(id, () => patchCdr(studyId!, kind, id, { data })),
    remove: (kind: CdrKind, id: string) => run(id, () => deleteCdr(studyId!, kind, id)),
  }
}
export type CdrPanelCtx = ReturnType<typeof useCdrPanel>

const RULE_GROUP: [string, CdrGroup][] = [['TMTC', 'tmtc'], ['TTC', 'tmtc'], ['FDIR', 'fdir'], ['AOCS', 'aocs'], ['EL-STATE', 'aocs'], ['OPS', 'ops']]
export function findingsOf(view: CdrView, group: CdrGroup): Finding[] {
  return view.checks.filter(c => (RULE_GROUP.find(([p]) => c.rule.startsWith(p))?.[1] ?? 'tmtc') === group)
}

export const rowClass = (r: CdrRow) => (r.status === 'rejected' ? 'is-rejected' : r.status === 'suggested' ? 'is-suggested' : undefined)

export const bil = (b: unknown, lang: string): string =>
  (b && typeof b === 'object' ? pickLang(b as { en: string; fr: string }, lang) : String(b ?? ''))
