/**
 * Mounted once for the whole app (workbench and wizard):
 *   - the docked panel (docks by narrowing the page; no overlay on wide screens)
 *   - the end-of-session prompt (End session button, a passed review gate,
 *     leaving the study)
 *   - the browser's own leave confirmation while entries are not downloaded
 *   - the slim expiry banner (see LogbookBanner)
 */
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../components/ui/Button'
import { Dialog } from '../components/ui/Dialog'
import { useUIStore } from '../stores/uiStore'
import { download, useLogbook, useLogbookMutations, useWorksheets, type Context, type Worksheet } from './api'
import { matchContext, useAutoContext } from './context'
import { DownloadButtons, LogbookPanel } from './LogbookPanel'
import { useLogbookUI } from './store'
import { BookGlyph } from './parts'
import { deletionText, fmtDeadline } from './format'

const BANNER_HOURS = 12

export function LogbookRoot() {
  const open = useLogbookUI(s => s.open)
  const { data } = useLogbook()
  const unsaved = data?.unsaved ?? 0

  // Dock: the page narrows by the panel width (CSS on the body class).
  useEffect(() => {
    document.body.classList.toggle('c2o-logbook-docked', open)
    return () => document.body.classList.remove('c2o-logbook-docked')
  }, [open])

  // Browser's generic confirm when entries were written since the last download.
  useEffect(() => {
    if (unsaved <= 0) return
    const onBeforeUnload = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = '' }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [unsaved])

  // Leaving a study (Close study, loading another one): offer the download.
  const studyId = useUIStore(s => s.studyId)
  const prev = useRef(studyId)
  const requestEnd = useLogbookUI(s => s.requestEndSession)
  useEffect(() => {
    if (prev.current && prev.current !== studyId && (data?.total ?? 0) > 0) requestEnd('leave')
    prev.current = studyId
  }, [studyId, data?.total, requestEnd])

  return (
    <>
      <LogbookPanel />
      <EndSessionDialog />
    </>
  )
}

/** Slim banner: entries not downloaded and the server deletes them in < 12 h. */
export function LogbookBanner() {
  const { t } = useTranslation()
  const { data } = useLogbook()
  const { refresh } = useLogbookMutations()
  const setOpen = useLogbookUI(s => s.setOpen)
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => { const id = window.setInterval(() => setNow(Date.now()), 60_000); return () => window.clearInterval(id) }, [])
  if (!data?.expires_at || data.unsaved <= 0) return null
  const left = new Date(data.expires_at).getTime() - now
  if (left > BANNER_HOURS * 3600_000) return null
  return (
    <div className="c2o-lb-banner" role="status">
      <BookGlyph />
      <span className="grow">
        {t('{{count}} logbook entries not downloaded · the server deletes your logbook on {{when}}',
          { count: data.unsaved, when: fmtDeadline(data.expires_at),
            defaultValue_one: '{{count}} logbook entry not downloaded · the server deletes your logbook on {{when}}' })}
      </span>
      <Button size="sm" variant="primary" onClick={() => download('md', refresh)}>{t('Download Markdown')}</Button>
      <Button size="sm" variant="quiet" onClick={() => setOpen(true)}>{t('Open logbook')}</Button>
    </div>
  )
}

// ─── End-of-session prompt ───

function pickDebrief(sheets: Worksheet[]): { ws: Worksheet; qid: string } | null {
  const unanswered = (ws: Worksheet, qid: string) => !(ws.answered[qid] || []).length
  const debrief = sheets.find(w => w.phase === 'debrief')
  if (debrief) {
    const q = debrief.questions.find(q => unanswered(debrief, q.id))
    if (q) return { ws: debrief, qid: q.id }
  }
  for (const ws of sheets) {
    if (ws.questions.some(q => q.id === 'notes') && unanswered(ws, 'notes')) return { ws, qid: 'notes' }
  }
  return null
}

function EndSessionDialog() {
  const { t } = useTranslation()
  const end = useLogbookUI(s => s.endSession)
  const close = useLogbookUI(s => s.closeEndSession)
  const setOpen = useLogbookUI(s => s.setOpen)
  const { data } = useLogbook()
  const auto = useAutoContext()
  const ctx: Context = { ...matchContext(auto), ...(end?.gate ? { gate: end.gate, tab: 'vv', level: 4 } : {}) }
  const sheets = useWorksheets(ctx, false, !!end)
  const debrief = pickDebrief(sheets.data?.worksheets ?? [])

  if (!end) return null
  const title = end.reason === 'gate' ? t('Review finished: download your logbook')
    : end.reason === 'leave' ? t('You left the study: download your logbook')
    : t('End session')
  const total = data?.total ?? 0
  const unsaved = data?.unsaved ?? 0
  return (
    <Dialog open title={title} onClose={close} width={520}
      actions={<>
        <Button onClick={() => { close(); setOpen(true) }}>{t('Open logbook')}</Button>
        <Button variant="primary" onClick={close}>{t('Done')}</Button>
      </>}>
      <dl className="c2o-stats m-0">
        <div><dt>{t('Entries')}</dt><dd>{total}</dd></div>
        <div><dt>{t('Not downloaded')}</dt><dd>{unsaved}</dd></div>
      </dl>
      {debrief && <DebriefQuestion ws={debrief.ws} qid={debrief.qid} context={{ ...auto, ...(end.gate ? { gate: end.gate } : {}) }} />}
      <DownloadButtons />
      <p className="t-12 c-2 m-0">{deletionText(data, t)}</p>
      {total > 0 && unsaved === 0 && <p className="c2o-note c2o-note--ok m-0">{t('Everything is downloaded. You can close the tab.')}</p>}
    </Dialog>
  )
}

function DebriefQuestion({ ws, qid, context }: { ws: Worksheet; qid: string; context: Context }) {
  const { t } = useTranslation()
  const { add } = useLogbookMutations()
  const q = ws.questions.find(q => q.id === qid)!
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  if (saved) return <p className="c2o-note c2o-note--ok m-0">{t('Answer saved in your logbook.')}</p>
  return (
    <div className="c2o-lb-debrief">
      <p className="t-12 c-2 m-0"><span className="mono">{ws.id}</span> · {ws.title}</p>
      <label className="c2o-field">
        <span className="c2o-field__label">{q.text}</span>
        {q.prompt && <span className="c2o-field__help">{q.prompt}</span>}
        <textarea className="c2o-textarea" rows={3} value={text} maxLength={8000} onChange={e => setText(e.target.value)} />
      </label>
      <div className="row">
        <span className="t-12 c-3 grow">{t('Optional. It goes into the download.')}</span>
        <Button size="sm" busy={busy} className="c2o-reason-end" disabledReason={!text.trim() ? t('Write an answer first') : undefined}
          onClick={async () => {
            setBusy(true)
            try {
              await add({ kind: 'worksheet', text, context, worksheet: { id: ws.id, q: q.id, title: ws.title, question: q.text } })
              setSaved(true)
            } finally { setBusy(false) }
          }}>{t('Save answer')}</Button>
      </div>
    </div>
  )
}
