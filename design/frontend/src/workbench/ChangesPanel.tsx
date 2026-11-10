/**
 * ChangesPanel (wave 3, 3.L4): the change proposals register (ECP / CR) of the Decide card.
 *
 * Server: GET/POST /api/studies/{id}/changes, PATCH …/changes/{id}, POST …/changes/{id}/preview,
 * POST …/changes/from-trade/{trade_id}. Each record shows its class, impact, the requirement
 * codes it affects (resolved to the study's rows; codes the study lacks are flagged), the source
 * trade, status and decision gate, and opens the "who is affected" preview of its impact specs.
 * The decision itself (affected seats agree, the board decides, a new baseline) is the
 * change-control flow of the Decide card (agent D), which reads these records.
 *
 * Mounted by the Decide panel (DecisionPanel, agent D). `RaiseChangeButton` is the "Raise change
 * from trade" action for a decided trade card.
 */
import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Button, Field, Input, Note, Select, StatusBadge, Tag, Textarea } from '../components/ui'
import { ImpactPreview } from '../components/ImpactPreview'

type Rec = Record<string, any>
const API = '/api'
const STATUSES = ['proposed', 'under_review', 'accepted', 'rejected', 'implemented', 'closed', 'withdrawn']
const GATES = ['', 'mdr', 'prr', 'srr', 'pdr', 'cdr', 'qr', 'ar', 'frr']

export function changeStatusLabel(t: TFunction, s: string): string {
  switch (s) {
    case 'proposed': return t('Proposed')
    case 'under_review': return t('Under review')
    case 'accepted': return t('Accepted')
    case 'rejected': return t('Rejected')
    case 'implemented': return t('Implemented')
    case 'closed': return t('Closed')
    case 'withdrawn': return t('Withdrawn')
    default: return s
  }
}

function tone(s: string): 'ok' | 'caution' | 'alarm' | 'neutral' | 'info' {
  return s === 'accepted' || s === 'implemented' || s === 'closed' ? 'ok'
    : s === 'rejected' ? 'alarm' : s === 'proposed' || s === 'under_review' ? 'caution' : 'neutral'
}

/** "Raise change from trade" on a decided trade (POST …/changes/from-trade/{trade}). */
export function RaiseChangeButton({ studyId, tradeId, decided, onRaised }: {
  studyId: string; tradeId: string; decided: boolean; onRaised?: (rec: Rec) => void
}) {
  const { t } = useTranslation()
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const raise = async () => {
    setBusy(true); setMsg(null)
    const r = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/changes/from-trade/${encodeURIComponent(tradeId)}`, { method: 'POST' })
    const j = await r.json().catch(() => ({}))
    setBusy(false)
    if (!r.ok) { setMsg(typeof j.detail === 'string' ? j.detail : `${r.status}`); return }
    setMsg(j.existing ? t('{{code}} already raised from this trade', { code: j.code }) : t('{{code}} raised', { code: j.code }))
    onRaised?.(j)
  }
  return (
    <span className="flex ai-c gap-1">
      <Button size="sm" onClick={raise} busy={busy} disabledReason={!decided ? t('Decide the trade first') : undefined}>{t('Raise change from trade')}</Button>
      {msg && <span className="t-12 c-2" role="status">{msg}</span>}
    </span>
  )
}

function ChangeRow({ studyId, c, onSaved }: { studyId: string; c: Rec; onSaved: () => void }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [preview, setPreview] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const patch = async (body: Rec) => {
    setErr(null)
    const r = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/changes/${encodeURIComponent(c.id)}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!r.ok) { const j = await r.json().catch(() => ({})); setErr(typeof j.detail === 'string' ? j.detail : `${r.status}`); return }
    onSaved()
  }
  const impact: Rec = c.impact ?? {}
  return (
    <li className="c2o-pcrow stack gap-1" data-testid={`change-${c.code}`}>
      <div className="flex ai-c gap-2 wrap">
        <span className="mono w-600">{c.code}</span>
        <Tag>{c.kind === 'cr' ? t('Change request') : t('Engineering change proposal')}</Tag>
        {c.change_class && <Tag title={c.class_text}>{t('Class {{cls}}', { cls: c.change_class })}</Tag>}
        <span className="grow min0">{c.title}</span>
        <StatusBadge status={tone(c.status)}>{changeStatusLabel(t, c.status)}</StatusBadge>
        {c.decision_gate && <Tag mono>{c.decision_gate.toUpperCase()}</Tag>}
        <Button size="sm" variant="quiet" onClick={() => setOpen(!open)} aria-expanded={open}>{open ? t('Less') : t('Details')}</Button>
      </div>
      {open && (<>
        {impact.summary && <p className="t-12 m-0"><strong>{t('Impact')}:</strong> {impact.summary}</p>}
        <div className="flex gap-1 wrap ai-c t-12">
          <span className="c-2">{t('Affected requirements')}:</span>
          {(c.affected_codes ?? []).map((code: string) => (
            <Tag key={code} mono title={(c.unresolved_codes ?? []).includes(code) ? t('Not in this study') : undefined}
              accent={(c.unresolved_codes ?? []).includes(code)}>{code}</Tag>
          ))}
          {(c.affected_codes ?? []).length === 0 && <span className="c-2">—</span>}
        </div>
        {(c.affected_other ?? []).length > 0 && <p className="t-12 c-2 m-0">{t('Also')}: {(c.affected_other ?? []).join('; ')}</p>}
        {c.source_trade && <p className="t-12 c-2 m-0">{t('Source trade')}: <span className="mono">{c.source_trade}</span></p>}
        <div className="flex gap-2 wrap ai-e">
          <Field label={t('Status')}>
            <Select dense value={c.status} onChange={e => patch({ status: e.target.value })}>
              {STATUSES.map(s => <option key={s} value={s}>{changeStatusLabel(t, s)}</option>)}
            </Select>
          </Field>
          <Field label={t('Decision gate')}>
            <Select dense value={c.decision_gate ?? ''} onChange={e => patch({ decision_gate: e.target.value })}>
              {GATES.map(g => <option key={g} value={g}>{g ? g.toUpperCase() : '—'}</option>)}
            </Select>
          </Field>
          <Button size="sm" onClick={() => setPreview(!preview)} disabledReason={(c.previews ?? []).length === 0 ? t('No impact specification on this record') : undefined}>
            {preview ? t('Hide who is affected') : t('Who is affected?')}
          </Button>
        </div>
        {err && <Note tone="alarm" role="alert">{err}</Note>}
        {preview && <ImpactPreview studyId={studyId} changeCode={c.code} title={t('Who is affected by {{code}}', { code: c.code })} />}
      </>)}
    </li>
  )
}

export function ChangesPanel({ studyId }: { studyId: string }) {
  const { t } = useTranslation()
  const [items, setItems] = useState<Rec[] | null>(null)
  const [counts, setCounts] = useState<Rec>({})
  const [err, setErr] = useState<string | null>(null)
  const [draft, setDraft] = useState<Rec | null>(null)
  const load = useCallback(async () => {
    const r = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/changes`)
    if (!r.ok) { setErr(t('Could not load the change proposals ({{status}})', { status: r.status })); return }
    const j = await r.json()
    setItems(j.items ?? []); setCounts(j.counts ?? {})
  }, [studyId, t])
  useEffect(() => { void load() }, [load])

  const create = async () => {
    if (!draft) return
    const body = { ...draft, affected: String(draft.affected ?? '').split(/[,;\s]+/).filter(Boolean) }
    const r = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/changes`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!r.ok) { const j = await r.json().catch(() => ({})); setErr(typeof j.detail === 'string' ? j.detail : `${r.status}`); return }
    setDraft(null); await load()
  }

  return (
    <section className="stack gap-2" aria-label={t('Change proposals')}>
      <div className="flex ai-c gap-2">
        <h4 className="c2o-panel__title m-0">{t('Change proposals')}</h4>
        {items && <span className="t-12 c-2">{t('{{total}} records, {{open}} open', { total: counts.total ?? items.length, open: counts.open ?? 0 })}</span>}
        <span className="grow" />
        <Button size="sm" onClick={() => setDraft(draft ? null : { kind: 'ecp', title: '', change_class: 'II', description: '', affected: '' })}>
          {draft ? t('Cancel') : t('New change')}
        </Button>
      </div>
      {err && <Note tone="alarm" role="alert">{err}</Note>}
      {draft && (
        <div className="stack gap-1">
          <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
            <Field label={t('Kind')}>
              <Select value={draft.kind} onChange={e => setDraft({ ...draft, kind: e.target.value })}>
                <option value="ecp">{t('Engineering change proposal')}</option><option value="cr">{t('Change request')}</option>
              </Select>
            </Field>
            <Field label={t('Class')} help={t('Class I changes form, fit or function, or an interface; class II does not')}>
              <Select value={draft.change_class} onChange={e => setDraft({ ...draft, change_class: e.target.value })}>
                <option value="I">I</option><option value="II">II</option>
              </Select>
            </Field>
            <Field label={t('Title')}><Input value={draft.title} onChange={e => setDraft({ ...draft, title: e.target.value })} /></Field>
            <Field label={t('Affected requirement codes')} help={t('Codes separated by commas')}>
              <Input value={draft.affected} onChange={e => setDraft({ ...draft, affected: e.target.value })} />
            </Field>
          </div>
          <Field label={t('Description and impact')}><Textarea rows={2} value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value, impact: e.target.value })} /></Field>
          <div><Button size="sm" variant="primary" onClick={create} disabledReason={!draft.title?.trim() ? t('Give the change a title') : undefined}>{t('Raise the change')}</Button></div>
        </div>
      )}
      {items === null ? <p className="t-12 c-2">{t('Loading…')}</p>
        : items.length === 0 ? <p className="t-12 c-2">{t('No change proposals yet.')}</p>
        : <ul className="stack gap-1 m-0" style={{ listStyle: 'none', padding: 0 }}>
            {items.map(c => <ChangeRow key={c.id} studyId={studyId} c={c} onSaved={load} />)}
          </ul>}
    </section>
  )
}
