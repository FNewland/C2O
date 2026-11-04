/**
 * electricalParts — pieces shared by the Electrical and Data tabs: the proposal status
 * and its actions (accept / reject / take the rule's new values), an input that commits
 * on Enter or blur, the findings list and the "parts imply" note.
 */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ArmButton, Button, Input, Note, StatusBadge } from '../components/ui'
import { pickLang } from '../types/interfaces'
import { LinkStatusChip } from './linkParts'
import type { ElectricalView, Finding, RowStatus } from './electricalApi'
import './electrical.css'

interface ProposalLike {
  id: string; status: RowStatus; origin: string; review: null | 'stale' | 'orphan'
  proposed: Record<string, unknown> | null; edited: boolean; rationale: { en: string; fr: string } | null
  standard_ref: string | null
}

/** Status chip + accept / reject, and the stale-review actions. */
export function ProposalCell({ row, label, busy, onPatch, onDelete }: {
  row: ProposalLike; label: string; busy: boolean
  onPatch: (body: Record<string, unknown>) => void; onDelete: () => void
}) {
  const { t, i18n } = useTranslation()
  const fromRule = row.origin.startsWith('rule:')
  const why = pickLang(row.rationale, i18n.language)
  const title = [why, row.standard_ref, fromRule ? t('Rule {{id}}', { id: row.origin.slice(5) }) : t('Added by a designer')]
    .filter(Boolean).join(' · ')
  return (
    <span className="c2o-el__acts">
      <span title={title}><LinkStatusChip status={row.status} /></span>
      {row.edited && <span className="c2o-tag t-12" title={t('Edited by a designer: the rules never overwrite it')}>{t('edited')}</span>}
      {row.status === 'suggested' && (
        <Button size="sm" variant="primary" busy={busy} onClick={() => onPatch({ status: 'accepted' })}
          aria-label={t('Accept {{name}}', { name: label })}>{t('Accept')}</Button>
      )}
      {row.status === 'rejected'
        ? <Button size="sm" busy={busy} onClick={() => onPatch({ status: 'suggested' })}
            aria-label={t('Restore {{name}}', { name: label })}>{t('Restore')}</Button>
        : <ArmButton size="sm" label={fromRule ? t('Reject') : t('Delete')} armedLabel={fromRule ? t('Confirm reject') : t('Confirm delete')}
            aria-label={(fromRule ? t('Reject {{name}}', { name: label }) : t('Delete {{name}}', { name: label }))}
            onConfirm={() => (fromRule ? onPatch({ status: 'rejected' }) : onDelete())} />}
      {row.review === 'stale' && (
        <span className="c2o-el__stale">
          <StatusBadge status="stale" title={t('The rule inputs changed since this row was accepted or edited.')}>{t('Needs review')}</StatusBadge>
          <Button size="sm" busy={busy} onClick={() => onPatch({ accept_update: true })}
            title={proposedText(row.proposed)}>{t('Take rule values')}</Button>
          <Button size="sm" variant="quiet" busy={busy} onClick={() => onPatch({ dismiss_update: true })}>{t('Keep mine')}</Button>
        </span>
      )}
      {row.review === 'orphan' && (
        <span className="c2o-el__stale">
          <StatusBadge status="caution" title={t('The links that implied this row are gone.')}>{t('No longer implied')}</StatusBadge>
          <Button size="sm" busy={busy} onClick={() => onPatch({ accept_update: true })}>{t('Reject')}</Button>
        </span>
      )}
    </span>
  )
}

function proposedText(p: Record<string, unknown> | null): string {
  if (!p) return ''
  return Object.entries(p).filter(([, v]) => v != null && typeof v !== 'object').map(([k, v]) => `${k} = ${v}`).join(', ')
}

/** A text/number input that commits on Enter or blur (Escape reverts). */
export function CommitInput({ value, onCommit, label, width = 72, mono = true, invalid, placeholder }: {
  value: string; onCommit: (v: string) => void; label: string; width?: number; mono?: boolean
  invalid?: boolean; placeholder?: string
}) {
  const [v, setV] = useState(value)
  useEffect(() => { setV(value) }, [value])
  const commit = () => { if (v !== value) onCommit(v) }
  return (
    <Input dense aria-label={label} value={v} placeholder={placeholder}
      className={`${mono ? 'mono ' : ''}c2o-el__in${invalid ? ' is-invalid' : ''}`} style={{ width }}
      aria-invalid={invalid || undefined}
      onChange={e => setV(e.target.value)} onBlur={commit}
      onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); commit() } else if (e.key === 'Escape') setV(value) }} />
  )
}

/** Worst finding for a row: glyph + count, the messages on hover. */
export function FindingMark({ findings }: { findings: Finding[] }) {
  const { t, i18n } = useTranslation()
  if (!findings.length) return <StatusBadge status="ok"><span className="sr-only">{t('No finding')}</span></StatusBadge>
  const worst = findings.some(f => f.severity === 'alarm') ? 'alarm' : 'caution'
  const text = findings.map(f => pickLang(f.message, i18n.language)).join('\n')
  return <StatusBadge status={worst} title={text}>{findings.length}</StatusBadge>
}

export function FindingsList({ findings, empty }: { findings: Finding[]; empty: string }) {
  const { i18n } = useTranslation()
  if (!findings.length) return <p className="t-12 c-3 m-0 pb-2" role="status">{empty}</p>
  // one note per message (an address clash is reported on each node involved)
  const seen = new Set<string>()
  const order = [...findings].sort((a, b) => (a.severity === b.severity ? 0 : a.severity === 'alarm' ? -1 : 1))
    .filter(f => { const k = `${f.severity}|${f.message.en}`; if (seen.has(k)) return false; seen.add(k); return true })
  return (
    <div className="stack gap-1 mb-3" data-testid="electrical-findings">
      {order.map(f => (
        <Note key={f.id} tone={f.severity}>
          <StatusBadge status={f.severity}><span className="mono t-12">{f.rule}</span></StatusBadge>
          <span>{pickLang(f.message, i18n.language)}</span>
        </Note>
      ))}
    </div>
  )
}

/** "The selected parts imply: 28.8 V unregulated bus · CAN · S-band". */
export function ProfileNote({ view }: { view: ElectricalView }) {
  const { t } = useTranslation()
  const p = view.profile ?? {}
  const bits: string[] = []
  if (p.unregulated_bus_v) bits.push(t('{{v}} V unregulated battery bus', { v: p.unregulated_bus_v }))
  else if (p.battery_bus_by_class) bits.push(t('{{v}} V battery bus', { v: p.battery_bus_by_class }))
  if (p.data_protocol_by_class) bits.push(t('{{p}} TM/TC bus', { p: p.data_protocol_by_class }))
  if (p.ttc_band_by_class) bits.push(t('{{b}}-band TT&C', { b: p.ttc_band_by_class }))
  if (!bits.length) {
    return <p className="t-12 c-3 m-0 pb-2">{t('No KB part sets the bus voltage, bus protocol or band yet: the rules use the {{cls}} class defaults.', { cls: view.spacecraft_class ?? 'small' })}</p>
  }
  const src = Object.values(p.sources ?? {}).flat()
  return (
    <p className="t-12 c-2 m-0 pb-2" title={src.length ? t('From KB parts: {{ids}}', { ids: Array.from(new Set(src)).join(', ') }) : undefined}>
      <span className="w-500">{t('The selected parts imply:')}</span> {bits.join(' · ')}
    </p>
  )
}
