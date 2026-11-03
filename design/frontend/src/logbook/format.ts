/** Logbook formatting helpers (times in the UI language) and shared labels. */
import type { TFunction } from 'i18next'
import { fmtDate } from '../i18n'
import type { EntryKind } from './api'

// English text is the i18n key: entry kinds.
export const KIND_LABEL: Record<EntryKind, string> = {
  decision: 'Decision', thought: 'Thought', observation: 'Observation', reflection: 'Reflection', worksheet: 'Worksheet',
}

export function fmtTime(ts: string | null | undefined): string {
  if (!ts) return ''
  return fmtDate(ts, { hour: '2-digit', minute: '2-digit' })
}

export function fmtWhen(ts: string | null | undefined): string {
  if (!ts) return ''
  const d = new Date(ts)
  const sameDay = d.toDateString() === new Date().toDateString()
  return sameDay ? fmtTime(ts) : fmtDate(ts, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export function fmtDeadline(ts: string | null | undefined): string {
  if (!ts) return ''
  return fmtDate(ts, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

/** Footer line: private, and when the server deletes it. */
export function deletionText(data: { count: number; expires_at: string | null; retention_h: number } | undefined,
  t: TFunction): string {
  if (!data || !data.expires_at || data.count === 0) return t('Private to you · nothing is stored on the server yet')
  return t('Private to you · deleted from the server on {{when}} ({{hours}} h after your last entry)',
    { when: fmtDeadline(data.expires_at), hours: data.retention_h })
}
