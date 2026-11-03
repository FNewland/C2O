/**
 * Decision records in the logbook: the design workbook part of it.
 *
 *   RecordDecision   one-click button at the point of decision (wizard step,
 *                    Decide widgets, Apply, Accept/Reject, equipment Add, gate
 *                    review). Opens the matching record prefilled with what the
 *                    tool showed; never blocks or replaces the action.
 *   DecisionsTab     the panel tab: the record editor, or the open decisions
 *                    by gate with their owner seat, and the recorded ones.
 *   GateDecisions    "which decisions still lack a record" for the gate review.
 *   PartDecisions    the decisions of one workbook part (Worksheets tab).
 *
 * Catalogue: configs/worksheets/decision_catalogue.yaml, served in the UI
 * language by GET /api/logbook/decisions. Records stay private to the person.
 */
import { useEffect, useId, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Button } from '../components/ui/Button'
import { Disclosure } from '../components/ui/Disclosure'
import { Glyph } from '../components/ui/StatusBadge'
import { useUIStore } from '../stores/uiStore'
import { fmtProse } from '../i18n'
import {
  fetchPrefill, LogbookHttpError, useDecisions, useLogbook, useLogbookMutations,
  type Catalogue, type CatalogueDecision, type Context, type DecisionRecord, type Entry, type Prefill,
  type RecordCriterion, type RecordEvidence, type RecordField, type RecordOption,
} from './api'
import { useAutoContext } from './context'
import { useLogbookUI, type DecisionDraft } from './store'

// ─── Glyph ───

/** A decision: a fork with one branch taken. */
export function DecisionGlyph({ size = 12 }: { size?: number }) {
  return (
    <svg className="c2o-lb-glyph" width={size} height={size} viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path d="M3 13.5V9.5a3 3 0 0 1 3-3h7" fill="none" stroke="currentColor" strokeWidth="1.4" />
      <path d="M10.5 4 13 6.5 10.5 9" fill="none" stroke="currentColor" strokeWidth="1.4" />
      <path d="M3 9.5V2.5" fill="none" stroke="currentColor" strokeWidth="1.4" strokeDasharray="1.6 1.6" />
    </svg>
  )
}

function fmtVal(v: unknown): string {
  if (typeof v === 'number') return fmtProse(v, { maximumFractionDigits: Math.abs(v) >= 100 ? 0 : 3 })
  if (typeof v === 'boolean') return v ? '✓' : '✗'
  return String(v ?? '')
}

function evidenceText(e: RecordEvidence): string {
  const u = e.unit ? `\u00a0${e.unit}` : ''
  if (e.before !== undefined || e.after !== undefined) {
    const b = e.before !== undefined ? fmtVal(e.before) + u : '—'
    const a = e.after !== undefined ? fmtVal(e.after) + u : e.value !== undefined ? fmtVal(e.value) + u : '—'
    return `${b} → ${a}`
  }
  return e.value !== undefined ? fmtVal(e.value) + u : ''
}

function scoreText(s: number | undefined): string {
  if (s === undefined) return ''
  return s >= 0 && s <= 1 && !Number.isInteger(s) ? `${Math.round(s * 100)}\u00a0%` : fmtVal(s)
}

// ─── The button at the point of decision ───

/**
 * "Record decision": opens the decision record prefilled with what the tool
 * shows here. `prefill` runs at click time so it reads the current numbers.
 * Sits beside the action; it never runs, blocks or replaces it.
 */
export function RecordDecision({ decision, capture, prefill, context, label, className }: {
  decision: string
  capture: string
  prefill?: () => Partial<DecisionRecord>
  context?: Context
  label?: string
  className?: string
}) {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const record = useLogbookUI(s => s.recordDecision)
  const { data } = useDecisions(studyId)
  const d = data?.decisions.find(x => x.id === decision)
  const done = d?.status === 'recorded'
  return (
    <Button size="sm" variant="quiet" className={`c2o-lb-logthis c2o-lb-record${done ? ' is-done' : ''}${className ? ` ${className}` : ''}`}
      data-decision={decision}
      aria-label={d ? t('Record the decision in your logbook: {{question}}', { question: d.question }) : t('Record decision')}
      title={done ? t('Recorded in your logbook. Click to record it again (for example after a change).')
        : t('Write the decision record: the options here are filled in, you add why (does not change the design)')}
      onClick={e => {
        e.stopPropagation()
        let pre: Partial<DecisionRecord> = {}
        try { pre = prefill?.() ?? {} } catch { /* a prefill must never stop the record */ }
        record({ decision, capture, ...pre, context })
      }}>
      {done ? <Glyph kind="ok" /> : <DecisionGlyph />}
      <span>{label ?? (done ? t('Recorded') : t('Record decision'))}</span>
    </Button>
  )
}

// ─── Panel tab ───

export function DecisionsTab() {
  const draft = useLogbookUI(s => s.draft)
  return draft ? <DecisionEditor key={draft.nonce} draft={draft} /> : <DecisionList />
}

function gateOrder(cat: Catalogue | undefined): string[] {
  return (cat?.gates ?? []).map(g => g.id)
}

/** Open decisions by gate, with the owner seat; recorded ones below each gate. */
function DecisionList() {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const { data: cat, isLoading, isError } = useDecisions(studyId)
  const seat = useLogbookUI(s => s.seat)
  const setSeat = useLogbookUI(s => s.setSeat)
  const seatId = useId()
  if (isLoading) return <p className="t-13 c-2 m-0">{t('Loading...')}</p>
  if (isError || !cat) return <p className="c2o-note c2o-note--alarm m-0">{t('The decision list did not load.')}</p>
  const items = cat.decisions.filter(d => !seat || d.seat === seat)
  const firstOpenGate = gateOrder(cat).find(g => items.some(d => d.gate === g && d.status === 'open'))
  const recorded = cat.decisions.filter(d => d.status === 'recorded').length
  return (
    <>
      <p className="t-12 c-2 m-0 mb-2">
        {t('The design decisions the workbook asks for. Record each one where you make it (look for Record decision), or from here. Before a review, the open ones are what still lacks a record.')}
      </p>
      <GateStrip cat={cat} seat={seat} />
      <div className="c2o-lb-dfilter">
        <label htmlFor={seatId} className="t-12 c-2">{t('Owner seat')}</label>
        <select id={seatId} className="c2o-select c2o-select--sm" value={seat} onChange={e => setSeat(e.target.value)}>
          <option value="">{t('All seats')}</option>
          {cat.seats.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
        </select>
        <span className="grow" />
        <span className="t-12 c-3 mono">{t('{{n}} of {{total}} recorded', { n: recorded, total: cat.decisions.length })}</span>
      </div>
      {cat.gates.map(g => {
        const mine = items.filter(d => d.gate === g.id)
        if (!mine.length) return null
        const open = mine.filter(d => d.status === 'open')
        return (
          <div key={g.id} className="c2o-lb-gate">
            <Disclosure defaultOpen={g.id === firstOpenGate}
              summary={<span className="c2o-lb-gate__title">{g.label}</span>}
              meta={open.length ? t('{{n}} open', { n: open.length }) : t('all recorded')}>
              <ol className="list-reset c2o-lb-dlist">
                {[...open, ...mine.filter(d => d.status === 'recorded')].map(d => <DecisionRow key={d.id} d={d} />)}
              </ol>
            </Disclosure>
          </div>
        )
      })}
    </>
  )
}

/** Picture first: one bar per gate, recorded against total. */
function GateStrip({ cat, seat }: { cat: Catalogue; seat: string }) {
  const { t } = useTranslation()
  return (
    <ul className="list-reset c2o-lb-gstrip" aria-label={t('Decision records by review')}>
      {cat.gates.map(g => {
        const mine = cat.decisions.filter(d => d.gate === g.id && (!seat || d.seat === seat))
        const done = mine.filter(d => d.status === 'recorded').length
        const pct = mine.length ? Math.round((done / mine.length) * 100) : 0
        return (
          <li key={g.id} className="c2o-lb-gstrip__item" title={t('{{gate}}: {{n}} of {{total}} decisions recorded', { gate: g.id.toUpperCase(), n: done, total: mine.length })}>
            <span className="mono w-600">{g.id.toUpperCase()}</span>
            <span className="c2o-lb-gstrip__bar" aria-hidden="true"><span style={{ width: `${pct}%` }} /></span>
            <span className="mono t-12 c-2">{done}/{mine.length}</span>
          </li>
        )
      })}
    </ul>
  )
}

function DecisionRow({ d, compact = false }: { d: CatalogueDecision; compact?: boolean }) {
  const { t } = useTranslation()
  const record = useLogbookUI(s => s.recordDecision)
  const setTab = useLogbookUI(s => s.setTab)
  const { data } = useLogbook()
  const done = d.status === 'recorded'
  const latest = done ? data?.entries.find(e => e.id === d.entries[0]) : undefined
  return (
    <li className={`c2o-lb-drow${done ? ' is-done' : ''}`}>
      <span className="c2o-lb-drow__state" aria-hidden="true">{done ? <Glyph kind="ok" /> : <span className="c2o-lb-open-dot" />}</span>
      <span className="c2o-lb-drow__main">
        <span className="c2o-lb-drow__q">{d.question}</span>
        <span className="c2o-lb-drow__meta t-12 c-3">
          <span className="c2o-tag">{d.seat_label}</span>
          {!compact && <span className="mono">{d.id}</span>}
          <span>{t('Worksheet {{n}}', { n: d.worksheet.replace('LW-', '') })}{d.part_title ? ` · ${d.part_title.replace(/^(Part|Partie) ([A-G])\s*:.*/, (_m, p, l) => `${p} ${l}`)}` : ''}</span>
          {latest?.record?.choice && <span className="c-2 ellipsis">→ {latest.record.choice}</span>}
        </span>
      </span>
      <span className="c2o-lb-drow__act">
        {done && latest ? (
          <Button size="sm" variant="quiet" onClick={() => { record({ decision: d.id, ...latest.record, entryId: latest.id }); setTab('decisions') }}
            aria-label={t('Edit the record: {{question}}', { question: d.question })}>{t('Edit')}</Button>
        ) : (
          <Button size="sm" onClick={() => record({ decision: d.id, fromStudy: true })}
            aria-label={t('Record the decision: {{question}}', { question: d.question })}>{t('Record')}</Button>
        )}
      </span>
    </li>
  )
}

// ─── Editor ───

function errText(e: unknown, t: TFunction): string {
  if (e instanceof LogbookHttpError && (e.status === 413 || e.status === 400)) return e.message
  return t('The logbook did not save: {{message}}', { message: e instanceof Error ? e.message : String(e) })
}

type Rec = Omit<DecisionRecord, 'decision_id'>

function fromDraft(d: DecisionDraft): Rec {
  const rec: Rec & Partial<DecisionDraft> = { ...d }
  for (const k of ['decision', 'context', 'entryId', 'fromStudy', 'nonce'] as const) delete rec[k]
  return rec
}

/** Fill the empty parts of `rec` from a server prefill (the student's own text always wins). */
function merge(rec: Rec, p: Prefill): Rec {
  const out: Rec = { ...rec }
  if (!out.options?.length && p.options?.length) out.options = p.options
  if (!out.criteria?.length && p.criteria?.length) out.criteria = p.criteria
  if (!out.evidence?.length && p.evidence?.length) out.evidence = p.evidence
  for (const k of ['choice', 'rationale', 'consequences', 'margin_impact', 'open_issues'] as const) {
    if (!out[k] && p[k]) out[k] = p[k]
  }
  return out
}

function DecisionEditor({ draft }: { draft: DecisionDraft }) {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const close = useLogbookUI(s => s.closeDraft)
  const { data: cat } = useDecisions(studyId)
  const auto = useAutoContext()
  const { addDecision, editDecision } = useLogbookMutations()
  const [decisionId, setDecisionId] = useState(draft.decision)
  const [rec, setRec] = useState<Rec>(() => fromDraft(draft))
  const [fromTool, setFromTool] = useState<Set<string>>(() => new Set(Object.keys(fromDraft(draft)).filter(k => k !== 'capture')))
  const [loadingPrefill, setLoadingPrefill] = useState(!!draft.fromStudy)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!draft.fromStudy) return
    let live = true
    fetchPrefill(draft.decision, studyId).then(p => {
      if (!live) return
      setRec(r => merge(r, p))
      setFromTool(new Set(Object.keys(p).filter(k => k !== 'sources' && k !== 'decision_id' && k !== 'study_id')))
    }).catch(() => { /* the record can be written by hand */ }).finally(() => { if (live) setLoadingPrefill(false) })
    return () => { live = false }
  }, [draft.fromStudy, draft.decision, studyId])

  const d = cat?.decisions.find(x => x.id === decisionId)
  const fields: RecordField[] = d?.fields ?? ['options', 'choice', 'rationale', 'evidence', 'consequences', 'open_issues']
  const has = (f: RecordField) => fields.includes(f)
  const label = (f: RecordField) => cat?.fields[f] ?? f
  const set = <K extends keyof Rec>(k: K, v: Rec[K]) => setRec(r => ({ ...r, [k]: v }))
  const canSave = !!(rec.choice?.trim() || rec.rationale?.trim())

  const save = async () => {
    if (!canSave || busy) return
    setBusy(true); setErr(null)
    const record: DecisionRecord = { decision_id: decisionId, ...rec }
    try {
      if (draft.entryId) await editDecision(draft.entryId, record)
      else await addDecision(record, { ...auto, ...(draft.context ?? {}) })
      setSaved(true)
      window.setTimeout(close, 700)
    } catch (e) { setErr(errText(e, t)) } finally { setBusy(false) }
  }

  const fromToolTag = (k: string) => fromTool.has(k)
    ? <span className="c2o-lb-src" title={t('Filled in by SpaceCDF from what the tool showed')}>{t('from SpaceCDF')}</span> : null

  return (
    <form className="c2o-lb-dr" onSubmit={e => { e.preventDefault(); void save() }}
      onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); void save() } }}>
      <div className="row">
        <Button size="sm" variant="quiet" onClick={close}>{t('← All decisions')}</Button>
        <span className="grow" />
        {draft.entryId && <span className="t-12 c-3">{t('Editing your record')}</span>}
      </div>
      <header className="c2o-lb-dr__head">
        <p className="c2o-lb-dr__meta t-12">
          <span className="mono c-2">{decisionId}</span>
          {d && <span className="c2o-tag mono">{d.gate.toUpperCase()}</span>}
          {d && <span className="c2o-tag">{d.seat_label}</span>}
        </p>
        <h3 className="c2o-lb-dr__q">{d?.question ?? decisionId}</h3>
        {d && <p className="t-12 c-3 m-0">{t('Worksheet {{n}}', { n: d.worksheet.replace('LW-', '') })}{d.worksheet_title ? ` · ${d.worksheet_title}` : ''}{d.part_title ? ` — ${d.part_title}` : ''}</p>}
        {d?.hint && <p className="t-12 c-2 m-0 lh-text">{d.hint}</p>}
        {cat && (
          <Disclosure summary={<span className="t-12">{t('Not this decision?')}</span>}>
            <select className="c2o-select c2o-select--sm" value={decisionId} aria-label={t('Which decision this record is for')}
              onChange={e => setDecisionId(e.target.value)}>
              {cat.gates.map(g => (
                <optgroup key={g.id} label={g.label}>
                  {cat.decisions.filter(x => x.gate === g.id).map(x => <option key={x.id} value={x.id}>{x.id} · {x.question}</option>)}
                </optgroup>
              ))}
            </select>
          </Disclosure>
        )}
      </header>
      {loadingPrefill && <p className="t-12 c-2 m-0" role="status">{t('Reading the study...')}</p>}

      {has('options') && (
        <section className="c2o-lb-dr__sec">
          <h4 className="c2o-lb-dr__h">{label('options')}{fromToolTag('options')}</h4>
          <OptionsEditor options={rec.options ?? []} onChange={o => {
            const before = (rec.options ?? []).find(x => x.chosen)?.name
            const now = o.find(x => x.chosen)?.name
            setRec(r => ({ ...r, options: o, choice: now && (!r.choice || r.choice === before) ? now : r.choice }))
          }} />
        </section>
      )}
      {has('criteria') && (
        <section className="c2o-lb-dr__sec">
          <h4 className="c2o-lb-dr__h">{label('criteria')}{fromToolTag('criteria')}</h4>
          <CriteriaEditor criteria={rec.criteria ?? []} onChange={c => set('criteria', c)} />
        </section>
      )}
      <section className="c2o-lb-dr__sec">
        <TextField label={label('choice')} value={rec.choice ?? ''} onChange={v => set('choice', v)} rows={1}
          tag={fromToolTag('choice')} placeholder={t('What did the team decide? (an option above, or in your words)')} />
      </section>
      <section className="c2o-lb-dr__sec is-yours">
        <TextField label={label('rationale')} value={rec.rationale ?? ''} onChange={v => set('rationale', v)} rows={4}
          help={t('Only you can write this: why this option and not the runner-up, which criterion decided it.')}
          placeholder={t('Why this option? What made the runner-up lose? What would change your mind?')} />
      </section>
      {has('evidence') && (
        <section className="c2o-lb-dr__sec">
          <h4 className="c2o-lb-dr__h">{label('evidence')}{fromToolTag('evidence')}</h4>
          <EvidenceEditor evidence={rec.evidence ?? []} onChange={v => set('evidence', v)} />
        </section>
      )}
      {has('consequences') && (
        <section className="c2o-lb-dr__sec is-yours">
          <TextField label={label('consequences')} value={rec.consequences ?? ''} onChange={v => set('consequences', v)} rows={2}
            placeholder={t('What does this commit other seats to? What could go wrong?')} />
        </section>
      )}
      {has('margin_impact') && (
        <section className="c2o-lb-dr__sec">
          <TextField label={label('margin_impact')} value={rec.margin_impact ?? ''} onChange={v => set('margin_impact', v)} rows={2}
            tag={fromToolTag('margin_impact')} placeholder={t('Which margin moves, from what to what?')} />
        </section>
      )}
      {has('open_issues') && (
        <section className="c2o-lb-dr__sec is-yours">
          <TextField label={label('open_issues')} value={rec.open_issues ?? ''} onChange={v => set('open_issues', v)} rows={2}
            placeholder={t('What is still TBD, and who closes it by when?')} />
        </section>
      )}
      {err && <p className="t-12 c-alarm m-0" role="alert">{err}</p>}
      {saved && <p className="c2o-note c2o-note--ok m-0" role="status">{t('Decision recorded in your logbook.')}</p>}
      <div className="c2o-lb-dr__foot">
        <span className="t-12 c-3 grow">{t('Private to you · Ctrl+Enter to save')}</span>
        <Button size="sm" onClick={close}>{t('Cancel')}</Button>
        <Button type="submit" size="sm" variant="primary" busy={busy} className="c2o-reason-end c2o-reason-up"
          disabledReason={!canSave ? t('Write the choice or the rationale first') : undefined}>
          {draft.entryId ? t('Save changes') : t('Save decision record')}
        </Button>
      </div>
    </form>
  )
}

function TextField({ label, value, onChange, rows, placeholder, help, tag }: {
  label: string; value: string; onChange: (v: string) => void; rows: number; placeholder?: string; help?: string; tag?: React.ReactNode
}) {
  const id = useId()
  return (
    <div className="c2o-field">
      <label htmlFor={id} className="c2o-lb-dr__h">{label}{tag}</label>
      {help && <span className="c2o-field__help">{help}</span>}
      {rows === 1
        ? <input id={id} className="c2o-input" value={value} maxLength={1000} placeholder={placeholder} onChange={e => onChange(e.target.value)} />
        : <textarea id={id} className="c2o-textarea" rows={rows} value={value} maxLength={4000} placeholder={placeholder} onChange={e => onChange(e.target.value)} />}
    </div>
  )
}

function OptionsEditor({ options, onChange }: { options: RecordOption[]; onChange: (o: RecordOption[]) => void }) {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const group = useId()
  const add = () => { if (name.trim()) { onChange([...options, { name: name.trim() }]); setName('') } }
  return (
    <>
      {options.length === 0 && <p className="t-12 c-3 m-0">{t('No options yet. Add the ones the team considered, including the ones you rejected.')}</p>}
      {options.length > 0 && (
        <ul className="list-reset c2o-lb-opts" role="radiogroup" aria-label={t('Options considered')}>
          {options.map((o, i) => (
            <li key={i} className={`c2o-lb-opt${o.chosen ? ' is-chosen' : ''}`}>
              <label className="c2o-lb-opt__pick">
                <input type="radio" name={group} checked={!!o.chosen}
                  onChange={() => onChange(options.map((x, j) => ({ ...x, chosen: j === i || undefined })))} />
                <span className="c2o-lb-opt__name">{o.name}</span>
              </label>
              {o.score !== undefined && <span className="mono t-12 c-2 c2o-lb-opt__score">{scoreText(o.score)}</span>}
              <button type="button" className="c2o-lb-chip__x" aria-label={t('Remove option {{name}}', { name: o.name })}
                onClick={() => onChange(options.filter((_, j) => j !== i))}>×</button>
              {(o.values || o.summary) && (
                <span className="c2o-lb-opt__vals t-12 c-2">
                  {o.values && (
                    <span className="c2o-lb-opt__pairs">
                      {Object.entries(o.values).map(([k, v]) => <span key={k}><span className="c-3">{k}</span> <span className="mono">{fmtVal(v)}</span></span>)}
                    </span>
                  )}
                  {o.summary && <span>{o.summary}</span>}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
      <div className="row gap-1">
        <input className="c2o-input c2o-input--sm" value={name} placeholder={t('Another option the team considered')} maxLength={200}
          aria-label={t('New option')} onChange={e => setName(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }} />
        <Button size="sm" onClick={add} disabledReason={!name.trim() ? t('Name the option first') : undefined}>{t('Add')}</Button>
      </div>
    </>
  )
}

function CriteriaEditor({ criteria, onChange }: { criteria: RecordCriterion[]; onChange: (c: RecordCriterion[]) => void }) {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const sum = criteria.reduce((s, c) => s + (c.weight ?? 0), 0)
  const weighted = criteria.some(c => c.weight !== undefined)
  const ok = Math.abs(sum - 1) < 0.011
  const add = () => { if (name.trim()) { onChange([...criteria, { name: name.trim() }]); setName('') } }
  const upd = (i: number, p: Partial<RecordCriterion>) => onChange(criteria.map((c, j) => (j === i ? { ...c, ...p } : c)))
  return (
    <>
      {criteria.length > 0 && (
        <table className="c2o-table c2o-table--dense c2o-lb-crit">
          <thead><tr><th>{t('Criterion')}</th><th className="num">{t('Weight')}</th><th>{t('Better when')}</th><th /></tr></thead>
          <tbody>
            {criteria.map((c, i) => (
              <tr key={i}>
                <td>{c.name}</td>
                <td className="num">
                  <input className="c2o-input c2o-input--sm c2o-input--num" type="number" min={0} max={1} step={0.05}
                    value={c.weight ?? ''} aria-label={t('Weight of {{name}}', { name: c.name })}
                    onChange={e => upd(i, { weight: e.target.value === '' ? undefined : Number(e.target.value) })} />
                </td>
                <td>
                  <select className="c2o-select c2o-select--sm" value={c.direction ?? ''} aria-label={t('Better when, for {{name}}', { name: c.name })}
                    onChange={e => upd(i, { direction: (e.target.value || undefined) as RecordCriterion['direction'] })}>
                    <option value="">—</option>
                    <option value="higher">{t('higher')}</option>
                    <option value="lower">{t('lower')}</option>
                  </select>
                </td>
                <td><button type="button" className="c2o-lb-chip__x" aria-label={t('Remove criterion {{name}}', { name: c.name })}
                  onClick={() => onChange(criteria.filter((_, j) => j !== i))}>×</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {weighted && (
        <p className={`t-12 m-0 ${ok ? 'c-2' : 'c-caution'}`} role="status">
          <Glyph kind={ok ? 'ok' : 'caution'} /> {ok ? t('Weights sum to 1.00') : t('Weights sum to {{sum}}, not 1.00', { sum: sum.toFixed(2) })}
        </p>
      )}
      <div className="row gap-1">
        <input className="c2o-input c2o-input--sm" value={name} placeholder={t('A criterion (mass, cost, TRL, revisit…)')} maxLength={100}
          aria-label={t('New criterion')} onChange={e => setName(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }} />
        <Button size="sm" onClick={add} disabledReason={!name.trim() ? t('Name the criterion first') : undefined}>{t('Add')}</Button>
      </div>
    </>
  )
}

function EvidenceEditor({ evidence, onChange }: { evidence: RecordEvidence[]; onChange: (e: RecordEvidence[]) => void }) {
  const { t } = useTranslation()
  const [label, setLabel] = useState('')
  const [value, setValue] = useState('')
  const add = () => {
    if (!label.trim()) return
    onChange([...evidence, { label: label.trim(), ...(value.trim() ? { value: value.trim() } : {}) }])
    setLabel(''); setValue('')
  }
  return (
    <>
      {evidence.length === 0 && <p className="t-12 c-3 m-0">{t('No numbers yet. Add the values that back the choice (budget, margin, analysis result).')}</p>}
      {evidence.length > 0 && (
        <dl className="c2o-lb-ev">
          {evidence.map((e, i) => (
            <div key={i} className="c2o-lb-ev__row">
              <dt>{e.label}</dt>
              <dd className={typeof e.value === 'string' && e.unit === undefined && e.before === undefined && /[a-z]{3}/i.test(e.value) ? 'is-text' : 'mono'}>{evidenceText(e)}</dd>
              <button type="button" className="c2o-lb-chip__x" aria-label={t('Remove {{what}}', { what: e.label })}
                onClick={() => onChange(evidence.filter((_, j) => j !== i))}>×</button>
            </div>
          ))}
        </dl>
      )}
      <div className="row gap-1">
        <input className="c2o-input c2o-input--sm" value={label} placeholder={t('What (e.g. Link margin)')} maxLength={120}
          aria-label={t('Evidence: what')} onChange={e => setLabel(e.target.value)} />
        <input className="c2o-input c2o-input--sm c2o-lb-ev__val" value={value} placeholder={t('Value and unit')} maxLength={60}
          aria-label={t('Evidence: value')} onChange={e => setValue(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }} />
        <Button size="sm" onClick={add} disabledReason={!label.trim() ? t('Say what the value is first') : undefined}>{t('Add')}</Button>
      </div>
    </>
  )
}

// ─── Entry list: a decision record as a structured summary ───

export function RecordSummary({ entry }: { entry: Entry }) {
  const { t } = useTranslation()
  const rec = entry.record!
  const chosen = rec.options?.find(o => o.chosen)
  return (
    <div className="c2o-lb-rsum">
      <p className="c2o-lb-rsum__q"><span className="mono c-3">{rec.decision_id}</span> {rec.question}</p>
      {rec.choice && <p className="m-0"><span className="c-3 t-12">{t('Choice')}</span> <b>{rec.choice}</b></p>}
      {rec.options && rec.options.length > 1 && (
        <p className="t-12 c-2 m-0">{t('{{n}} options considered', { n: rec.options.length })}{chosen && rec.choice !== chosen.name ? ` · ${chosen.name}` : ''}</p>
      )}
      {rec.rationale && <p className="c2o-lb-rsum__why">{rec.rationale}</p>}
      {!rec.rationale && <p className="t-12 c-caution m-0"><Glyph kind="caution" /> {t('No rationale yet')}</p>}
    </div>
  )
}

// ─── Gate review: which decisions still lack a record ───

export function GateDecisions({ gate }: { gate: string }) {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const setOpen = useLogbookUI(s => s.setOpen)
  const setTab = useLogbookUI(s => s.setTab)
  const { data: cat, isLoading } = useDecisions(studyId, gate)
  const due = cat?.due
  const items = useMemo(() => (cat && due ? cat.decisions.filter(d => due.open.includes(d.id)) : []), [cat, due])
  if (isLoading || !cat || !due) return null
  const done = due.recorded.length
  const pct = due.total ? Math.round((done / due.total) * 100) : 0
  const label = cat.gates.find(g => g.id === due.gate)?.label ?? due.gate.toUpperCase()
  return (
    <section className="c2o-lb-gatedec" aria-labelledby="gatedec-h">
      <div className="c2o-lb-gatedec__head">
        <h4 id="gatedec-h" className="m-0 t-13 w-600">{t('Decision records due by {{gate}}', { gate: due.gate.toUpperCase() })}</h4>
        <span className="c2o-lb-gstrip__bar c2o-lb-gatedec__bar" aria-hidden="true"><span style={{ width: `${pct}%` }} /></span>
        <span className="mono t-12">{t('{{n}} of {{total}} recorded', { n: done, total: due.total })}</span>
        <span className="grow" />
        <Button size="sm" variant="quiet" onClick={() => { setTab('decisions'); setOpen(true) }}>{t('Open in logbook')}</Button>
      </div>
      <p className="t-12 c-2 m-0">
        {items.length
          ? t('{{label}}: these decisions have no record in your logbook yet. Each owner seat records its own; the logbook is private to each person.', { label })
          : t('Every decision due by this review has a record in your logbook.')}
      </p>
      {items.length > 0 && (
        <ol className="list-reset c2o-lb-dlist">
          {items.map(d => <DecisionRow key={d.id} d={d} compact />)}
        </ol>
      )}
    </section>
  )
}

// ─── Worksheets tab: the decisions of one workbook part ───

export function PartDecisions({ worksheet, q }: { worksheet: string; q: string }) {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const { data: cat } = useDecisions(studyId)
  const items = (cat?.decisions ?? []).filter(d => d.worksheet === worksheet && d.q === q)
  if (!items.length) return null
  return (
    <div className="c2o-lb-partdec">
      <span className="c2o-lb-partdec__h t-12 c-2"><DecisionGlyph /> {t('Decisions in this part')}</span>
      <ol className="list-reset c2o-lb-dlist">
        {items.map(d => <DecisionRow key={d.id} d={d} compact />)}
      </ol>
    </div>
  )
}
