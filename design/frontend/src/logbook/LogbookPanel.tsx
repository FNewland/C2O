/**
 * Logbook side panel (LOGBOOK_SPEC.md §5): docked, non-modal, on the right.
 *
 *   head      Logbook · who it belongs to · close
 *   tabs      Entries (n) | Decisions (open n) | Worksheets (n for this step)
 *   entries   quick entry (kind chips, context chips, Ctrl/Cmd+Enter), list newest first
 *   decisions the decision record editor, or the open decisions by gate (decisions.tsx)
 *   sheets    worksheets that apply here, each question answerable inline, the part's
 *             decisions under it; download one worksheet or copy it as Markdown
 *   foot      private · deletion time · Download (Markdown / printable HTML) · End session · Delete now
 */
import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { ArmButton, Button } from '../components/ui/Button'
import { Disclosure } from '../components/ui/Disclosure'
import { Tabs } from '../components/ui/Tabs'
import { tabPanelProps } from '../components/ui/util'
import {
  download, downloadWorksheet, LogbookHttpError, useDecisions, useLogbook, useLogbookMutations, useWorksheets,
  worksheetMarkdown, type Context, type Entry, type EntryKind, type Question, type Worksheet,
} from './api'
import { useUIStore } from '../stores/uiStore'
import { DecisionsTab, PartDecisions, RecordSummary } from './decisions'
import { chipLabel, chipValue, HIDDEN_KEYS, matchContext, useAutoContext } from './context'
import { useLogbookUI, type PanelTab } from './store'
import { BookGlyph } from './parts'
import { deletionText, fmtWhen, KIND_LABEL } from './format'

const QUICK_KINDS: EntryKind[] = ['decision', 'thought', 'observation', 'reflection']
// English text is the i18n key: other tools that share the logbook.
const TOOL_LABEL: Record<string, string> = {
  mcs: 'MCS', delayed_tm: 'Delayed TM', orbit: 'Orbit', radio: 'Radio', docs: 'Docs',
  instructor: 'Instructor', portal: 'Portal', design: 'SpaceCDF',
}
const DRAFT_KEY = 'scdf.logbook.draft'

function readDraft(): string {
  try { return sessionStorage.getItem(DRAFT_KEY) || '' } catch { return '' }
}
function writeDraft(v: string) {
  try { if (v) sessionStorage.setItem(DRAFT_KEY, v); else sessionStorage.removeItem(DRAFT_KEY) } catch { /* private mode */ }
}

function errText(e: unknown, t: TFunction): string {
  if (e instanceof LogbookHttpError && e.status === 413) return e.message
  return t('The logbook did not save: {{message}}', { message: e instanceof Error ? e.message : String(e) })
}

export function LogbookPanel() {
  const { t } = useTranslation()
  const open = useLogbookUI(s => s.open)
  const tab = useLogbookUI(s => s.tab)
  const setTab = useLogbookUI(s => s.setTab)
  const setOpen = useLogbookUI(s => s.setOpen)
  const { data, isError } = useLogbook()
  const auto = useAutoContext()
  const sheetsQ = useWorksheets(matchContext(auto), false, open)
  const matched = sheetsQ.data?.worksheets.length ?? 0
  const studyId = useUIStore(s => s.studyId)
  const decQ = useDecisions(studyId, null, open)
  const openDecisions = decQ.data?.decisions.filter(d => d.status === 'open').length

  // The decision record needs room for its options table: the panel widens on that tab.
  useEffect(() => {
    document.body.classList.toggle('c2o-logbook-wide', open && tab === 'decisions')
    return () => document.body.classList.remove('c2o-logbook-wide')
  }, [open, tab])

  if (!open) return null
  return (
    <aside id="c2o-logbook" className={`c2o-logbook${tab === 'decisions' ? ' is-wide' : ''}`} aria-labelledby="c2o-logbook-title"
      onKeyDown={e => { if (e.key === 'Escape' && !(e.target as HTMLElement).closest('textarea')) setOpen(false) }}>
      <header className="c2o-logbook__head">
        <BookGlyph size={16} />
        <h2 id="c2o-logbook-title" className="c2o-logbook__title">{t('Logbook')}</h2>
        <span className="c2o-logbook__who t-12 c-3 ellipsis" title={data?.person.id_label}>
          {data ? (data.person.local ? t('Kept for this browser') : data.person.id_label) : ''}
        </span>
        <Button variant="icon" aria-label={t('Close the logbook')} onClick={() => setOpen(false)}>×</Button>
      </header>
      <Tabs<PanelTab> idBase="lb" label={t('Logbook')} value={tab} onChange={setTab} className="c2o-logbook__tabs"
        items={[
          { id: 'entries', label: t('Entries'), meta: <span className="mono">{data?.count ?? 0}</span> },
          { id: 'decisions', label: t('Decisions'),
            meta: <span className="mono" title={t('Decisions from the workbook not recorded yet')}>{openDecisions ?? '–'}</span> },
          { id: 'worksheets', label: t('Worksheets'), meta: <span className="mono">{matched}</span> },
        ]} />
      <div className="c2o-logbook__body" {...tabPanelProps('lb', tab)}>
        {isError && <p className="c2o-note c2o-note--alarm m-0 mb-2" role="alert">{t('The logbook service is unreachable. Nothing you type here is saved until it is back.')}</p>}
        {tab === 'entries' ? <EntriesTab auto={auto} entries={data?.entries ?? []} />
          : tab === 'decisions' ? <DecisionsTab /> : <WorksheetsTab auto={auto} />}
      </div>
      <LogbookFooter />
    </aside>
  )
}

// ─── Entries tab ───

function EntriesTab({ auto, entries }: { auto: Context; entries: Entry[] }) {
  const { t } = useTranslation()
  return (
    <>
      <QuickEntry auto={auto} />
      <h3 className="c2o-logbook__h">{t('Your entries')}<span className="c-3 w-400 mono">{entries.length}</span></h3>
      {entries.length === 0
        ? <p className="t-13 c-2 m-0">{t('Nothing logged yet. Write down decisions as you make them, and why: the reasons are what you will need at the review.')}</p>
        : <ol className="list-reset c2o-lb-list">{entries.map(e => <EntryRow key={e.id} entry={e} />)}</ol>}
    </>
  )
}

function QuickEntry({ auto }: { auto: Context }) {
  const { t } = useTranslation()
  const prefill = useLogbookUI(s => s.prefill)
  const { add } = useLogbookMutations()
  const [kind, setKind] = useState<EntryKind>('decision')
  const [text, setText] = useState(readDraft)
  const [extra, setExtra] = useState<Context>({})
  const [removed, setRemoved] = useState<Set<string>>(new Set())
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const ref = useRef<HTMLTextAreaElement>(null)
  const id = useId()

  // "Log this": take the kind and context, focus the box.
  useEffect(() => {
    if (!prefill) return
    setKind(prefill.kind === 'worksheet' ? 'decision' : prefill.kind)
    setExtra(prefill.context)
    setRemoved(new Set())
    window.setTimeout(() => ref.current?.focus(), 0)
  }, [prefill])

  useEffect(() => { writeDraft(text) }, [text])

  const context = useMemo(() => {
    const c: Context = { ...auto, ...extra }
    for (const k of removed) {
      delete c[k]
      if (k === 'study_name') delete c.study_id
    }
    return c
  }, [auto, extra, removed])

  const chips = Object.entries(context).filter(([k, v]) => !HIDDEN_KEYS.has(k) && v !== null && v !== '')
  const empty = !text.trim()

  const save = async () => {
    if (empty || busy) return
    setBusy(true); setErr(null)
    try {
      await add({ kind, text, context })
      setText(''); setExtra({}); setRemoved(new Set())
    } catch (e) { setErr(errText(e, t)) } finally { setBusy(false) }
  }

  return (
    <form className="c2o-lb-quick" onSubmit={e => { e.preventDefault(); void save() }}>
      <div role="group" aria-label={t('Kind of entry')} className="c2o-lb-kinds">
        {QUICK_KINDS.map(k => (
          <button key={k} type="button" className="c2o-choice-chip c2o-lb-kind" aria-pressed={kind === k} onClick={() => setKind(k)}>
            {t(KIND_LABEL[k])}
          </button>
        ))}
      </div>
      <label htmlFor={id} className="sr-only">{t('Entry text')}</label>
      <textarea id={id} ref={ref} className="c2o-textarea c2o-lb-text" rows={4} value={text} maxLength={8000}
        placeholder={kind === 'decision' ? t('What did you decide, and why? What did you reject?')
          : kind === 'observation' ? t('What did you see? Which value, where?')
          : kind === 'reflection' ? t('What would you do differently next time?')
          : t('A thought to come back to')}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); void save() } }} />
      {chips.length > 0 && (
        <ul className="list-reset c2o-lb-chips" aria-label={t('Context saved with this entry')}>
          {chips.map(([k, v]) => (
            <li key={k} className="c2o-lb-chip">
              <span className="c-3">{chipLabel(k, t)}</span>
              <span className="c2o-lb-chip__v">{chipValue(k, v, t)}</span>
              <button type="button" className="c2o-lb-chip__x" aria-label={t('Remove {{what}} from this entry', { what: chipLabel(k, t) })}
                onClick={() => setRemoved(s => new Set(s).add(k))}>×</button>
            </li>
          ))}
        </ul>
      )}
      {err && <p className="t-12 c-alarm m-0" role="alert">{err}</p>}
      <div className="row">
        <span className="t-12 c-3 grow">{t('Ctrl+Enter to save')}</span>
        <Button type="submit" variant="primary" size="sm" busy={busy} className="c2o-reason-end"
          disabledReason={empty ? t('Write something first') : undefined}>{t('Save entry')}</Button>
      </div>
    </form>
  )
}

function EntryRow({ entry }: { entry: Entry }) {
  const { t } = useTranslation()
  const { edit, remove } = useLogbookMutations()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(entry.text)
  const [err, setErr] = useState<string | null>(null)
  const ctx = Object.entries(entry.context || {}).filter(([k, v]) => !HIDDEN_KEYS.has(k) && k !== 'decision_id' && v !== null && v !== '')
  const own = entry.tool === 'design'
  const record = useLogbookUI(s => s.recordDecision)
  const isRecord = !!entry.record && entry.kind === 'decision'

  const save = async () => {
    if (!draft.trim()) return
    try { await edit(entry.id, draft); setEditing(false); setErr(null) } catch (e) { setErr(errText(e, t)) }
  }

  return (
    <li className={`c2o-lb-entry is-${entry.kind}`}>
      <div className="c2o-lb-entry__meta">
        <time className="mono c-2" dateTime={entry.ts}>{fmtWhen(entry.ts)}</time>
        <span className="c2o-lb-entry__kind">{t(KIND_LABEL[entry.kind] ?? entry.kind)}</span>
        {!own && <span className="c2o-tag">{t(TOOL_LABEL[entry.tool] ?? entry.tool)}</span>}
        {entry.edited && <span className="t-12 c-3">{t('edited')}</span>}
        <span className="grow" />
        {!editing && (
          <>
            <Button size="sm" variant="quiet"
              onClick={() => isRecord
                ? record({ decision: entry.record!.decision_id, ...entry.record, entryId: entry.id })
                : (setDraft(entry.text), setEditing(true))}
              aria-label={t('Edit entry from {{time}}', { time: fmtWhen(entry.ts) })}>{t('Edit')}</Button>
            <ArmButton label={t('Delete')} armedLabel={t('Confirm delete')} onConfirm={() => remove(entry.id)}
              aria-label={t('Delete entry from {{time}}', { time: fmtWhen(entry.ts) })} />
          </>
        )}
      </div>
      {entry.worksheet && !isRecord && (
        <p className="c2o-lb-entry__ws t-12 c-2">
          <span className="mono">{entry.worksheet.id}</span> · {entry.worksheet.q_text || entry.worksheet.q}
        </p>
      )}
      {editing ? (
        <div className="stack gap-1">
          <textarea className="c2o-textarea" value={draft} rows={4} maxLength={8000} autoFocus
            aria-label={t('Entry text')} onChange={e => setDraft(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); void save() }
              if (e.key === 'Escape') { e.stopPropagation(); setEditing(false) }
            }} />
          {err && <p className="t-12 c-alarm m-0" role="alert">{err}</p>}
          <div className="row">
            <span className="grow" />
            <Button size="sm" onClick={() => setEditing(false)}>{t('Cancel')}</Button>
            <Button size="sm" variant="primary" className="c2o-reason-end" onClick={save} disabledReason={!draft.trim() ? t('Write something first') : undefined}>{t('Save')}</Button>
          </div>
        </div>
      ) : isRecord ? <RecordSummary entry={entry} /> : <p className="c2o-lb-entry__text">{entry.text}</p>}
      {ctx.length > 0 && (
        <p className="c2o-lb-entry__ctx t-12 c-3">
          {ctx.map(([k, v]) => <span key={k}>{chipLabel(k, t)} <span className="c-2">{chipValue(k, v, t)}</span></span>)}
        </p>
      )}
    </li>
  )
}

// ─── Worksheets tab ───

function WorksheetsTab({ auto }: { auto: Context }) {
  const { t } = useTranslation()
  const ctx = matchContext(auto)
  const here = useWorksheets(ctx, false)
  const [showAll, setShowAll] = useState(false)
  const all = useWorksheets(ctx, true, showAll)
  const matched = here.data?.worksheets ?? []
  const others = (all.data?.worksheets ?? []).filter(w => !w.match)
  return (
    <>
      <p className="t-12 c-2 m-0 mb-2">{t('From the learner workbook. Your answers are logbook entries: they are in your download, not handed in automatically.')}</p>
      <h3 className="c2o-logbook__h">{t('For this step')}<span className="c-3 w-400 mono">{matched.length}</span></h3>
      {here.isLoading && <p className="t-13 c-2 m-0">{t('Loading...')}</p>}
      {!here.isLoading && matched.length === 0 && <p className="t-13 c-2 m-0">{t('No worksheet is tied to this step. All worksheets are listed below.')}</p>}
      {matched.map((w, i) => <WorksheetBlock key={w.id} ws={w} context={auto} defaultOpen={i === 0} />)}
      <Disclosure ruled summary={t('All worksheets')} meta={showAll ? String(others.length) : undefined}
        open={showAll} onToggle={setShowAll}>
        {all.isLoading && <p className="t-13 c-2 m-0">{t('Loading...')}</p>}
        {others.map(w => <WorksheetBlock key={w.id} ws={w} context={auto} />)}
      </Disclosure>
    </>
  )
}

function WorksheetBlock({ ws, context, defaultOpen = false }: { ws: Worksheet; context: Context; defaultOpen?: boolean }) {
  const { t } = useTranslation()
  const done = ws.questions.filter(q => (ws.answered[q.id] || []).length > 0).length
  return (
    <div className="c2o-lb-ws">
      <Disclosure defaultOpen={defaultOpen}
        summary={<span className="c2o-lb-ws__title"><span className="mono c-2">{ws.id}</span> {ws.title}</span>}
        meta={t('{{done}} of {{total}} answered', { done, total: ws.questions.length })}>
        <WorksheetExport ws={ws} />
        <ol className="list-reset stack gap-3">
          {ws.questions.map(q => <QuestionBlock key={q.id} ws={ws} q={q} context={context} />)}
        </ol>
      </Disclosure>
    </div>
  )
}

function QuestionBlock({ ws, q, context }: { ws: Worksheet; q: Question; context: Context }) {
  const { t } = useTranslation()
  const { data } = useLogbook()
  const { add } = useLogbookMutations()
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const id = useId()
  const answers = (data?.entries ?? []).filter(e => e.kind === 'worksheet' && e.worksheet?.id === ws.id && e.worksheet?.q === q.id)

  const save = async () => {
    if (!text.trim() || busy) return
    setBusy(true); setErr(null)
    try {
      await add({ kind: 'worksheet', text, context,
        worksheet: { id: ws.id, q: q.id, title: ws.title, q_text: q.text } })
      setText('')
    } catch (e) { setErr(errText(e, t)) } finally { setBusy(false) }
  }

  return (
    <li className="c2o-lb-q">
      <label htmlFor={id} className="c2o-lb-q__text">{q.text}</label>
      {q.prompt && <p className="c2o-lb-q__prompt">{q.prompt}</p>}
      {q.points.length > 0 && <ul className="c2o-lb-q__points">{q.points.map((p, i) => <li key={i}>{p}</li>)}</ul>}
      <PartDecisions worksheet={ws.id} q={q.id} />
      {answers.length > 0 && (
        <div className="c2o-lb-q__answers">
          {answers.map(a => (
            <p key={a.id} className="c2o-lb-q__answer">
              <span className="mono t-12 c-3">{fmtWhen(a.ts)}</span> {a.text}
            </p>
          ))}
        </div>
      )}
      <textarea id={id} className="c2o-textarea" rows={3} value={text} maxLength={8000}
        placeholder={answers.length ? t('Add to your answer') : t('Your answer')}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); void save() } }} />
      {err && <p className="t-12 c-alarm m-0" role="alert">{err}</p>}
      <div className="row">
        <span className="grow" />
        <Button size="sm" busy={busy} onClick={save} className="c2o-reason-end"
          disabledReason={!text.trim() ? t('Write an answer first') : undefined}>{t('Save answer')}</Button>
      </div>
    </li>
  )
}

/** "Download this worksheet" and "Copy as Markdown" (for a team document). Neither counts as a download. */
function WorksheetExport({ ws }: { ws: Worksheet }) {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const [copied, setCopied] = useState<'ok' | 'fail' | null>(null)
  const copy = async () => {
    try {
      const md = await worksheetMarkdown(ws.id, studyId)
      try {
        await navigator.clipboard.writeText(md)
      } catch {
        // No clipboard permission (http, old browser): the classic way.
        const ta = document.createElement('textarea')
        ta.value = md; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0'
        document.body.appendChild(ta); ta.select()
        const ok = document.execCommand('copy'); ta.remove()
        if (!ok) throw new Error('copy')
      }
      setCopied('ok')
    } catch { setCopied('fail') }
    window.setTimeout(() => setCopied(null), 2500)
  }
  return (
    <div className="c2o-lb-wsx" role="group" aria-label={t('This worksheet')}>
      <Button size="sm" onClick={() => downloadWorksheet(ws.id, studyId, 'md')}
        title={t('This worksheet only, every part, with your decision records and answers')}>{t('Download this worksheet')}</Button>
      <Button size="sm" variant="quiet" onClick={copy} title={t('Paste it into your team document')}>{t('Copy as Markdown')}</Button>
      <span className="t-12 c-2" role="status" aria-live="polite">
        {copied === 'ok' ? t('Copied') : copied === 'fail' ? t('Could not copy: use Download') : ''}
      </span>
    </div>
  )
}

// ─── Footer ───

export function DownloadButtons({ compact = false }: { compact?: boolean }) {
  const { t } = useTranslation()
  const { refresh } = useLogbookMutations()
  const { data } = useLogbook()
  const studyId = useUIStore(s => s.studyId)
  const none = !data || data.count === 0
  const reason = none ? t('Nothing to download yet') : undefined
  return (
    <span className="c2o-lb-dl" role="group" aria-label={t('Download your logbook')}>
      {!compact && <span className="t-12 c-2">{t('Download')}</span>}
      <Button size="sm" onClick={() => download('md', refresh, studyId)} disabledReason={reason}
        title={t('Laid out as your workbook: decision records and answers by worksheet, then the log')}>{t('Markdown')}</Button>
      <Button size="sm" onClick={() => download('html', refresh, studyId)} disabledReason={reason}
        title={t('Open it and print, or Save as PDF')}>{t('Printable HTML')}</Button>
    </span>
  )
}

function LogbookFooter() {
  const { t } = useTranslation()
  const { data } = useLogbook()
  const { deleteAll } = useLogbookMutations()
  const requestEnd = useLogbookUI(s => s.requestEndSession)
  return (
    <footer className="c2o-logbook__foot">
      <p className="t-12 c-2 m-0">{deletionText(data, t)}</p>
      <div className="c2o-logbook__foot-row">
        <DownloadButtons />
      </div>
      <div className="c2o-logbook__foot-row">
        <Button size="sm" onClick={() => requestEnd('button')}>{t('End session')}</Button>
        <span className="grow" />
        <ArmButton label={t('Delete now')} armedLabel={t('Confirm: delete all entries')} variant="default"
          className="c2o-reason-up c2o-reason-end"
          title={t('Delete your whole logbook from the server now, in every C2O tool')}
          disabledReason={!data || data.count === 0 ? t('Nothing to delete') : undefined}
          onConfirm={deleteAll} />
      </div>
    </footer>
  )
}
