/**
 * Panel: a titled section over a hairline rule (no box by default).
 *
 *   <Panel title={t('Mass budget')} meta={t('Spacecraft')} actions={<Button …/>}>…</Panel>
 *
 * `boxed` draws a 1 px outline for the rare case where sections sit side by
 * side. `level` sets the heading level so the document outline stays sane.
 */
import type { ReactNode } from 'react'
import { cx } from './util'

export interface PanelProps {
  title?: ReactNode
  meta?: ReactNode
  actions?: ReactNode
  children?: ReactNode
  boxed?: boolean
  level?: 2 | 3 | 4
  className?: string
  id?: string
  'aria-label'?: string
}

export function Panel({ title, meta, actions, children, boxed, level = 3, className, id, ...rest }: PanelProps) {
  const H = `h${level}` as 'h2' | 'h3' | 'h4'
  return (
    <section id={id} className={cx('c2o-panel', boxed && 'c2o-panel--boxed', className)} aria-label={rest['aria-label']}>
      {(title || actions || meta) && (
        <div className="c2o-panel__head">
          {title && <H className="c2o-panel__title">{title}</H>}
          {meta && <span className="c2o-panel__meta">{meta}</span>}
          {actions && <div className="c2o-panel__actions">{actions}</div>}
        </div>
      )}
      <div className="c2o-panel__body">{children}</div>
    </section>
  )
}

/** Inline notice: a left rule in the status colour plus text (not a card). */
export function Note({ tone = 'neutral', children, className, role }: { tone?: 'neutral' | 'info' | 'caution' | 'alarm' | 'ok'; children: ReactNode; className?: string; role?: 'status' | 'alert' }) {
  return <div role={role} className={cx('c2o-note', tone !== 'neutral' && `c2o-note--${tone}`, className)}>{children}</div>
}

/** Distinct "no data" label (brief §1.3): never an em-dash. */
export function NoData({ label }: { label: string }) {
  return <span className="c2o-nodata">{label}</span>
}
