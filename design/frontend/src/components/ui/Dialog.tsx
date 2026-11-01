/**
 * Accessible modal dialog plus an imperative API that replaces the browser's
 * alert / confirm / prompt (R3 problem 14).
 *
 *   await showAlert(t('Save failed'))
 *   if (!(await askConfirm(t('Delete "{{name}}"?', { name }), { danger: true }))) return
 *   const name = await askText(t('Rename option:'), current)   // null when cancelled
 *   const kind = await askChoice(t('Interface type'), [{ value: 'data', label: t('Data') }], 'data')
 *
 * The dialog traps focus, closes on Esc (= cancel), is labelled by its title
 * and described by its message, and returns focus to the opener.
 * <DialogHost /> is mounted once in App.
 */
import { useEffect, useId, useRef, useState, useSyncExternalStore, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

// ─── Presentational dialog ───

export interface DialogProps {
  open: boolean
  title: string
  onClose: () => void
  children?: ReactNode
  /** Footer buttons. */
  actions?: ReactNode
  /** id of the element that describes the dialog (defaults to the body). */
  describedBy?: string
  width?: number | string
  /** role="alertdialog" for confirmations that interrupt work. */
  alert?: boolean
}

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function Dialog({ open, title, onClose, children, actions, describedBy, width = 440, alert = false }: DialogProps) {
  const ref = useRef<HTMLDivElement>(null)
  const titleId = useId()
  const bodyId = useId()
  const closeRef = useRef(onClose)
  closeRef.current = onClose

  useEffect(() => {
    if (!open) return
    const opener = document.activeElement as HTMLElement | null
    const node = ref.current
    // Focus the first field, else the default (last) action, else the dialog.
    const first = node?.querySelector<HTMLElement>('input, select, textarea, [data-autofocus]')
      ?? node?.querySelector<HTMLElement>('.c2o-dialog__actions button:last-child')
    ;(first ?? node)?.focus()

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { e.preventDefault(); closeRef.current(); return }
      if (e.key !== 'Tab' || !node) return
      const items = Array.from(node.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(el => el.offsetParent !== null)
      if (items.length === 0) { e.preventDefault(); return }
      const a = items[0], z = items[items.length - 1]
      if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus() }
      else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus() }
    }
    document.addEventListener('keydown', onKey, true)
    return () => {
      document.removeEventListener('keydown', onKey, true)
      opener?.focus?.()
    }
  }, [open])

  if (!open) return null
  return (
    <div className="c2o-dialog__scrim" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div
        ref={ref}
        className="c2o-dialog"
        role={alert ? 'alertdialog' : 'dialog'}
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={describedBy ?? bodyId}
        tabIndex={-1}
        style={{ width }}
      >
        <h2 id={titleId} className="c2o-dialog__title">{title}</h2>
        <div id={bodyId} className="c2o-dialog__body">{children}</div>
        {actions && <div className="c2o-dialog__actions">{actions}</div>}
      </div>
    </div>
  )
}

// ─── Imperative API ───

type Choice = { value: string; label: string; hint?: string }
type Request =
  | { kind: 'alert'; message: string; title?: string; resolve: (v: void) => void }
  | { kind: 'confirm'; message: string; title?: string; confirmLabel?: string; danger?: boolean; resolve: (v: boolean) => void }
  | { kind: 'text'; message: string; title?: string; initial: string; resolve: (v: string | null) => void }
  | { kind: 'choice'; message: string; title?: string; choices: Choice[]; initial: string; resolve: (v: string | null) => void }

let queue: Request[] = []
const listeners = new Set<() => void>()
const emit = () => listeners.forEach(l => l())
const push = (r: Request) => { queue = [...queue, r]; emit() }
const pop = () => { queue = queue.slice(1); emit() }

export function showAlert(message: string, opts: { title?: string } = {}): Promise<void> {
  return new Promise(resolve => push({ kind: 'alert', message, ...opts, resolve }))
}
export function askConfirm(message: string, opts: { title?: string; confirmLabel?: string; danger?: boolean } = {}): Promise<boolean> {
  return new Promise(resolve => push({ kind: 'confirm', message, ...opts, resolve }))
}
export function askText(message: string, initial = '', opts: { title?: string } = {}): Promise<string | null> {
  return new Promise(resolve => push({ kind: 'text', message, initial: initial ?? '', ...opts, resolve }))
}
export function askChoice(message: string, choices: Choice[], initial?: string, opts: { title?: string } = {}): Promise<string | null> {
  return new Promise(resolve => push({ kind: 'choice', message, choices, initial: initial ?? choices[0]?.value ?? '', ...opts, resolve }))
}

function useQueueHead(): Request | undefined {
  return useSyncExternalStore(
    cb => { listeners.add(cb); return () => { listeners.delete(cb) } },
    () => queue[0],
  )
}

export function DialogHost() {
  const req = useQueueHead()
  // key forces fresh field state per request
  return req ? <RequestDialog key={queueKey(req)} req={req} /> : null
}

const keys = new WeakMap<Request, number>()
let nextKey = 1
function queueKey(r: Request): number {
  if (!keys.has(r)) keys.set(r, nextKey++)
  return keys.get(r)!
}

function RequestDialog({ req }: { req: Request }) {
  const { t } = useTranslation()
  const [text, setText] = useState(req.kind === 'text' || req.kind === 'choice' ? req.initial : '')
  const fieldId = useId()

  const finish = (value: unknown) => {
    pop()
    ;(req.resolve as (v: unknown) => void)(value)
  }
  const cancelValue = req.kind === 'confirm' ? false : req.kind === 'alert' ? undefined : null
  const cancel = () => finish(cancelValue)
  const accept = () => finish(req.kind === 'confirm' ? true : req.kind === 'alert' ? undefined : text)

  const title = req.title ?? (req.kind === 'alert' ? t('Notice') : req.kind === 'confirm' ? t('Please confirm') : t('Enter a value'))
  const lines = req.message.split('\n')

  const message = (
    <p className="c2o-dialog__message">
      {lines.map((l, i) => <span key={i}>{l}{i < lines.length - 1 && <br />}</span>)}
    </p>
  )

  const actions = req.kind === 'alert'
    ? <button type="button" className="c2o-btn c2o-btn--primary" onClick={accept}>{t('OK')}</button>
    : <>
        <button type="button" className="c2o-btn" onClick={cancel} data-autofocus={req.kind === 'confirm' && req.danger ? true : undefined}>{t('Cancel')}</button>
        <button
          type={req.kind === 'confirm' ? 'button' : 'submit'}
          form={fieldId + '-form'}
          className={`c2o-btn ${req.kind === 'confirm' && req.danger ? 'c2o-btn--danger' : 'c2o-btn--primary'}`}
          onClick={req.kind === 'confirm' ? accept : undefined}
        >
          {req.kind === 'confirm' ? (req.confirmLabel ?? t('Confirm')) : t('OK')}
        </button>
      </>

  return (
    <Dialog open title={title} onClose={cancel} actions={actions} alert={req.kind !== 'text' && req.kind !== 'choice'}>
      <form id={fieldId + '-form'} onSubmit={e => { e.preventDefault(); accept() }}>
        {req.kind === 'text' ? (
          <>
            <label htmlFor={fieldId} className="c2o-dialog__message">{message}</label>
            <input id={fieldId} className="c2o-input" value={text} onChange={e => setText(e.target.value)} autoComplete="off" />
          </>
        ) : req.kind === 'choice' ? (
          <fieldset className="c2o-choice">
            <legend className="c2o-dialog__message">{req.message}</legend>
            {req.choices.map(ch => (
              <label key={ch.value} className="c2o-choice__item">
                <input type="radio" name={fieldId} value={ch.value} checked={text === ch.value} onChange={() => setText(ch.value)} />
                <span>{ch.label}</span>
                {ch.hint && <span className="c2o-choice__hint">{ch.hint}</span>}
              </label>
            ))}
          </fieldset>
        ) : message}
      </form>
    </Dialog>
  )
}
