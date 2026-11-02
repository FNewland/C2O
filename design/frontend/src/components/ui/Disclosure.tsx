/**
 * Disclosure: one click deeper (brief §1.2). Expanding never moves the
 * summary the user clicked; the body opens below it.
 *
 *   <Disclosure summary={t('Detail table')} meta={t('{{n}} rows', { n })}>…</Disclosure>
 */
import { useId, useState, type ReactNode } from 'react'
import { cx } from './util'

export interface DisclosureProps {
  summary: ReactNode
  meta?: ReactNode
  children: ReactNode
  defaultOpen?: boolean
  /** Controlled mode. */
  open?: boolean
  onToggle?: (open: boolean) => void
  /** Draw a hairline above (when it ends a section). */
  ruled?: boolean
  className?: string
}

export function Chevron() {
  return <svg className="c2o-disclosure__chev" viewBox="0 0 10 10" aria-hidden="true"><path d="M3 1.5 6.5 5 3 8.5" fill="none" stroke="currentColor" strokeWidth="1.6" /></svg>
}

export function Disclosure({ summary, meta, children, defaultOpen = false, open: openProp, onToggle, ruled, className }: DisclosureProps) {
  const [inner, setInner] = useState(defaultOpen)
  const open = openProp ?? inner
  const id = useId()
  return (
    <div className={cx('c2o-disclosure', ruled && 'c2o-disclosure--ruled', className)}>
      <button type="button" className="c2o-disclosure__btn" aria-expanded={open} aria-controls={id}
        onClick={() => { const v = !open; setInner(v); onToggle?.(v) }}>
        <Chevron />
        <span>{summary}</span>
        {meta != null && <span className="c2o-disclosure__meta">{meta}</span>}
      </button>
      {open && <div id={id} className="c2o-disclosure__body">{children}</div>}
    </div>
  )
}
