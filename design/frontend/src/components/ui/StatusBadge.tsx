/**
 * Status = colour + glyph + text (PRINCIPLES P6, brief §1.3).
 *
 *   <StatusBadge status="alarm">{t('Over allocation')}</StatusBadge>
 *   <StatusBadge status="ok" boxed>{t('GO')}</StatusBadge>
 *   <Tag>{t('test')}</Tag>          // neutral label: no status meaning
 *
 * Glyph shapes stay distinct in greyscale: ok = check, caution = triangle,
 * alarm = diamond, info = filled dot, neutral = ring, stale = clock,
 * nodata = dashed ring.
 */
import type { ReactNode } from 'react'
import { cx } from './util'

export type Status = 'ok' | 'caution' | 'alarm' | 'info' | 'neutral' | 'stale' | 'nodata'

export function Glyph({ kind, className }: { kind: Status; className?: string }) {
  const cls = cx('c2o-status__glyph', className)
  switch (kind) {
    case 'ok':
      return <svg className={cls} viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 5.2 4 7.6 8.6 2.4" fill="none" stroke="currentColor" strokeWidth="1.8" /></svg>
    case 'caution':
      return <svg className={cls} viewBox="0 0 10 10" aria-hidden="true"><path d="M5 .8 9.6 9.2H.4Z" fill="currentColor" /></svg>
    case 'alarm':
      return <svg className={cls} viewBox="0 0 10 10" aria-hidden="true"><path d="M5 .3 9.7 5 5 9.7.3 5Z" fill="currentColor" /></svg>
    case 'info':
      return <svg className={cls} viewBox="0 0 10 10" aria-hidden="true"><circle cx="5" cy="5" r="3.6" fill="currentColor" /></svg>
    case 'stale':
      return <svg className={cls} viewBox="0 0 10 10" aria-hidden="true"><circle cx="5" cy="5" r="4" fill="none" stroke="currentColor" strokeWidth="1.2" /><path d="M5 2.6V5l1.7 1.2" fill="none" stroke="currentColor" strokeWidth="1.2" /></svg>
    case 'nodata':
      return <svg className={cls} viewBox="0 0 10 10" aria-hidden="true"><circle cx="5" cy="5" r="3.8" fill="none" stroke="currentColor" strokeWidth="1.2" strokeDasharray="2 1.6" /></svg>
    default:
      return <svg className={cls} viewBox="0 0 10 10" aria-hidden="true"><circle cx="5" cy="5" r="3.6" fill="none" stroke="currentColor" strokeWidth="1.4" /></svg>
  }
}

export function StatusBadge({ status, children, boxed, title, className }: { status: Status; children: ReactNode; boxed?: boolean; title?: string; className?: string }) {
  return (
    <span className={cx('c2o-status', `c2o-status--${status}`, boxed && 'c2o-status--boxed', className)} title={title}>
      <Glyph kind={status} />
      <span>{children}</span>
    </span>
  )
}

export function Tag({ children, mono, accent, title, className }: { children: ReactNode; mono?: boolean; accent?: boolean; title?: string; className?: string }) {
  return <span className={cx('c2o-tag', mono && 'c2o-tag--mono', accent && 'c2o-tag--accent', className)} title={title}>{children}</span>
}
