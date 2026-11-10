/**
 * GateReviewRecord (W4.08, Nov 2026) — the review record of one gate, under its checklist:
 *
 * - the RID / action log: number, kind, raised by seat, description, severity, owner seat, due
 *   date, status, closure evidence (GET /studies/{id}/rids, POST …/gates/{gate}/rids,
 *   PATCH/DELETE …/rids/{rid}); RIDs still open from earlier gates are listed too;
 * - the chair note and the go / no-go decision (PUT …/gates/{gate}/record; Team leader or
 *   instructor in a seat study);
 * - the review report (.docx, POST …/gates/{gate}/report) and the changes since the previous
 *   gate's baseline (GET …/gate-baselines/diff?gate=).
 */
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { useSeatStore } from '../seats/api'
import { useUIStore } from '../stores/uiStore'
import { Button, Disclosure, Input, Note, Select, Textarea } from '../components/ui'
import { pick } from '../components/useGateReview'

const API = '/api'

interface Rid {
  id: string; gate: string; number: string; kind: 'rid' | 'action'; criterion_id: string; raised_by_seat: string
  description: string; severity: 'major' | 'minor'; owner_seat: string; due_date: string
  status: 'open' | 'in_work' | 'closed' | 'rejected'; closure_evidence: string
}
interface ReviewRecord { chair_note?: string; decision?: 'go' | 'go_with_actions' | 'no_go' | null; board?: string; decided_at?: string | null; by?: string }
interface Diff {
  a: { gate: string; created_at: string }; b: { gate: string; created_at: string }
  changes: Record<'requirements' | 'elements' | 'risks', { added: string[]; removed: string[]; changed: string[] }> & { mission_need: string[]; criteria: string[] }
}

const STATUSES = ['open', 'in_work', 'closed', 'rejected'] as const
// English text is the i18n key
const STATUS_TEXT: Record<string, string> = { open: 'Open', in_work: 'In work', closed: 'Closed', rejected: 'Rejected' }
// English text is the i18n key
const DECISION_TEXT: Record<string, string> = { go: 'GO', go_with_actions: 'GO with actions', no_go: 'NO GO' }

export function GateReviewRecord({ studyId, gate, gateShort, gateOrder, review, canDecide, onChanged }: {
  studyId: string; gate: string; gateShort: string; gateOrder: string[]; review: ReviewRecord | undefined
  canDecide: boolean; onChanged: () => void
}) {
  const { t } = useTranslation()
  const lang = useUIStore(s => s.lang)
  const qc = useQueryClient()
  const catalogue = useSeatStore(st => st.catalogue)
  const seatTeam = useSeatStore(st => st.team)
  const mySeat = seatTeam?.enabled ? (seatTeam.me?.active ?? '') : ''
  const seats = (catalogue?.seats ?? []).filter(s => !['customer', 'observer', 'instructor'].includes(s.kind))
  const seatLabel = (id: string) => pick(seats.find(s => s.id === id)?.label, lang) || id

  const { data: ridData } = useQuery<{ items: Rid[]; open: number }>({
    queryKey: ['rids', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/rids`).then(r => (r.ok ? r.json() : { items: [], open: 0 })),
  })
  const { data: diff } = useQuery<Diff | null>({
    queryKey: ['gate-diff', studyId, gate],
    queryFn: () => fetch(`${API}/studies/${studyId}/gate-baselines/diff?gate=${encodeURIComponent(gate)}`).then(r => (r.ok ? r.json() : null)),
  })
  const idx = gateOrder.indexOf(gate)
  const earlier = new Set(idx > 0 ? gateOrder.slice(0, idx) : [])
  const here = (ridData?.items ?? []).filter(r => r.gate === gate)
  const carried = (ridData?.items ?? []).filter(r => earlier.has(r.gate) && (r.status === 'open' || r.status === 'in_work'))

  const [draft, setDraft] = useState({ kind: 'rid', severity: 'minor', description: '', owner_seat: '', due_date: '' })
  const [err, setErr] = useState<string | null>(null)
  const [rec, setRec] = useState<ReviewRecord>(review ?? {})
  useEffect(() => { setRec(review ?? {}) }, [review, gate])

  const refresh = () => { void qc.invalidateQueries({ queryKey: ['rids', studyId] }); onChanged() }
  const raise = async () => {
    setErr(null)
    const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/gates/${encodeURIComponent(gate)}/rids`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...draft, raised_by_seat: mySeat }),
    })
    if (!res.ok) { setErr(t('The RID could not be raised ({{code}}).', { code: res.status })); return }
    setDraft(d => ({ ...d, description: '' }))
    refresh()
  }
  const patch = async (rid: Rid, body: Partial<Rid>) => {
    const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/rids/${encodeURIComponent(rid.id)}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    })
    if (!res.ok) setErr(t('The RID could not be changed ({{code}}).', { code: res.status }))
    refresh()
  }
  const saveRecord = async () => {
    setErr(null)
    const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/gates/${encodeURIComponent(gate)}/record`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chair_note: rec.chair_note ?? '', decision: rec.decision || null, board: rec.board ?? '' }),
    })
    if (!res.ok) { setErr(t('The review record could not be saved ({{code}}).', { code: res.status })); return }
    onChanged()
  }
  const report = async () => {
    const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/gates/${encodeURIComponent(gate)}/report?lang=${i18n.language === 'fr' ? 'fr' : 'en'}`, { method: 'POST' })
    if (!res.ok) { setErr(t('The review report could not be generated ({{code}}).', { code: res.status })); return }
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = /filename="([^"]+)"/.exec(res.headers.get('content-disposition') || '')?.[1] || `SpaceCDF_${gateShort}_review_report.docx`
    a.click()
    setTimeout(() => URL.revokeObjectURL(a.href), 1000)
  }

  const ridRows = (items: Rid[], editable: boolean) => (
    <table className="c2o-table c2o-table--dense t-12">
      <thead>
        <tr className="bb"><th>{t('Number')}</th><th>{t('Description')}</th><th>{t('Raised by')}</th><th>{t('Owner')}</th>
          <th>{t('Due')}</th><th>{t('Status')}</th><th>{t('Closure evidence')}</th></tr>
      </thead>
      <tbody>
        {items.map(r => (
          <tr key={r.id} className="bb">
            <td className="mono">{r.number}{r.severity === 'major' ? ` · ${t('major')}` : ''}</td>
            <td>{r.description}</td>
            <td>{seatLabel(r.raised_by_seat)}</td>
            <td>{seatLabel(r.owner_seat)}</td>
            <td className="mono">{r.due_date}</td>
            <td>
              {editable ? (
                <Select dense aria-label={t('Status of {{n}}', { n: r.number })} value={r.status} onChange={e => void patch(r, { status: e.target.value as Rid['status'] })}>
                  {STATUSES.map(s => <option key={s} value={s}>{t(STATUS_TEXT[s])}</option>)}
                </Select>
              ) : t(STATUS_TEXT[r.status])}
            </td>
            <td>
              {editable ? (
                <Input dense aria-label={t('Closure evidence of {{n}}', { n: r.number })} defaultValue={r.closure_evidence}
                  onBlur={e => { if (e.target.value !== r.closure_evidence) void patch(r, { closure_evidence: e.target.value }) }} />
              ) : r.closure_evidence}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )

  const ch = diff?.changes
  return (
    <div className="mt-3 stack gap-2" data-testid="gate-review-record">
      <h4 className="c2o-reqs__group">{t('Review record')}</h4>
      <div className="stack gap-1">
        <div className="flex gap-1 wrap ai-c">
          <label className="t-12" htmlFor={`rec-dec-${gate}`}>{t('Board decision')}</label>
          <Select dense id={`rec-dec-${gate}`} value={rec.decision ?? ''} disabled={!canDecide}
            onChange={e => setRec(r => ({ ...r, decision: (e.target.value || null) as ReviewRecord['decision'] }))}>
            <option value="">{t('not recorded')}</option>
            {Object.keys(DECISION_TEXT).map(d => <option key={d} value={d}>{t(DECISION_TEXT[d])}</option>)}
          </Select>
          <Input dense style={{ flex: 1, minWidth: '12rem' }} aria-label={t('Review board')} placeholder={t('Review board (seats)')}
            value={rec.board ?? ''} disabled={!canDecide} onChange={e => setRec(r => ({ ...r, board: e.target.value }))} />
        </div>
        <Textarea rows={2} aria-label={t('Chair note')} placeholder={t('Chair note: what the board concluded and why')}
          value={rec.chair_note ?? ''} disabled={!canDecide} onChange={e => setRec(r => ({ ...r, chair_note: e.target.value }))} />
        <div className="flex gap-1 wrap">
          {canDecide && <Button size="sm" variant="primary" onClick={() => void saveRecord()}>{t('Save the review record')}</Button>}
          {!canDecide && <span className="t-12 c-3">{t('Gate decisions: Team leader or instructor')}</span>}
          <span className="grow" />
          <Button size="sm" onClick={() => void report()}>{t('Review report (.docx)')}</Button>
        </div>
      </div>

      <div>
        <h5 className="t-13 w-600 m-0 mb-1">{t('RIDs and actions ({{n}})', { n: here.length })}</h5>
        {here.length > 0 ? ridRows(here, true) : <p className="t-12 c-3 m-0">{t('No RID or action raised at this gate.')}</p>}
        <div className="flex gap-1 wrap ai-c mt-1">
          <Select dense aria-label={t('Kind')} value={draft.kind} onChange={e => setDraft(d => ({ ...d, kind: e.target.value }))}>
            <option value="rid">{t('RID')}</option><option value="action">{t('Action')}</option>
          </Select>
          <Select dense aria-label={t('Severity')} value={draft.severity} onChange={e => setDraft(d => ({ ...d, severity: e.target.value }))}>
            <option value="minor">{t('minor')}</option><option value="major">{t('major')}</option>
          </Select>
          <Input dense style={{ flex: 2, minWidth: '14rem' }} aria-label={t('Description')} placeholder={t('What is wrong or to be done')}
            value={draft.description} onChange={e => setDraft(d => ({ ...d, description: e.target.value }))} />
          <Select dense aria-label={t('Owner seat')} value={draft.owner_seat} onChange={e => setDraft(d => ({ ...d, owner_seat: e.target.value }))}>
            <option value="">{t('Owner seat')}</option>
            {seats.map(s => <option key={s.id} value={s.id}>{pick(s.label, lang)}</option>)}
          </Select>
          <Input dense type="date" aria-label={t('Due date')} value={draft.due_date} onChange={e => setDraft(d => ({ ...d, due_date: e.target.value }))} />
          <Button size="sm" disabledReason={!draft.description.trim() ? t('Describe the item first') : undefined} onClick={() => void raise()}>
            {t('Raise')}
          </Button>
        </div>
      </div>

      {carried.length > 0 && (
        <Disclosure ruled summary={t('Still open from earlier gates')} meta={String(carried.length)}>
          {ridRows(carried, true)}
        </Disclosure>
      )}

      <Disclosure ruled summary={t('Changes since the previous gate')} meta={ch ? `${diff!.a.gate.toUpperCase()} → ${diff!.b.gate.toUpperCase()}` : t('no baseline pair yet')}>
        {ch ? (
          <ul className="list-reset t-12 stack gap-1">
            {(['requirements', 'elements', 'risks'] as const).map(k => (
              <li key={k}>
                <span className="w-600">{t(k === 'requirements' ? 'Requirements' : k === 'elements' ? 'Elements' : 'Risks')}</span>
                {': '}{t('{{a}} added, {{r}} removed, {{c}} changed', { a: ch[k].added.length, r: ch[k].removed.length, c: ch[k].changed.length })}
                {ch[k].added.length + ch[k].changed.length > 0 && <span className="c-3"> ({[...ch[k].added, ...ch[k].changed].slice(0, 12).join(', ')})</span>}
              </li>
            ))}
            {ch.mission_need.length > 0 && <li>{t('Mission need changed: {{f}}', { f: ch.mission_need.join(', ') })}</li>}
          </ul>
        ) : <p className="t-12 c-3 m-0">{t('Pass this gate and the one before it to compare their baselines.')}</p>}
      </Disclosure>
      {err && <Note tone="alarm" role="alert">{err}</Note>}
    </div>
  )
}
