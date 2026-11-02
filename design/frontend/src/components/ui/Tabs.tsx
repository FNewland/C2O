/**
 * Tabs: an ARIA tablist with roving tabindex and arrow-key navigation.
 *
 *   <Tabs label={t('Budget')} value={kind} onChange={setKind} idBase="budget"
 *         items={[{ id: 'mass', label: t('Mass') }, …]} variant="segmented" />
 *   <div {...tabPanelProps('budget', kind)}>…</div>
 *
 * variant "line" (default) is the underlined bar used for views; "segmented"
 * is the compact switch used inside a panel. An item with `disabledReason`
 * stays focusable and shows the reason on hover and focus.
 */
import { useRef, type ReactNode } from 'react'
import { cx, panelId, tabId } from './util'

export interface TabItem<T extends string> {
  id: T
  label: ReactNode
  /** Small secondary text after the label (count, context). */
  meta?: ReactNode
  disabledReason?: string | false | null
}

export interface TabsProps<T extends string> {
  items: TabItem<T>[]
  value: T
  onChange: (id: T) => void
  /** Accessible name of the tablist. */
  label: string
  /** Prefix for tab / panel ids (see tabPanelProps). */
  idBase: string
  variant?: 'line' | 'segmented'
  className?: string
}

export function Tabs<T extends string>({ items, value, onChange, label, idBase, variant = 'line', className }: TabsProps<T>) {
  const ref = useRef<HTMLDivElement>(null)

  const onKeyDown = (e: React.KeyboardEvent) => {
    const i = items.findIndex(it => it.id === value)
    let j = i
    if (e.key === 'ArrowRight') j = (i + 1) % items.length
    else if (e.key === 'ArrowLeft') j = (i - 1 + items.length) % items.length
    else if (e.key === 'Home') j = 0
    else if (e.key === 'End') j = items.length - 1
    else return
    e.preventDefault()
    // Skip over disabled tabs, but still move focus so the reason can be read.
    const target = items[j]
    if (!target.disabledReason) onChange(target.id)
    ref.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[j]?.focus()
  }

  const seg = variant === 'segmented'
  return (
    <div ref={ref} role="tablist" aria-label={label} className={cx(seg ? 'c2o-seg' : 'c2o-tabs', className)} onKeyDown={onKeyDown}>
      {items.map(it => {
        const selected = it.id === value
        return (
          <button
            key={it.id}
            type="button"
            role="tab"
            id={tabId(idBase, it.id)}
            aria-selected={selected}
            aria-controls={selected ? panelId(idBase) : undefined}
            aria-disabled={it.disabledReason ? true : undefined}
            data-reason={it.disabledReason || undefined}
            tabIndex={selected ? 0 : -1}
            className={seg ? 'c2o-seg__item' : 'c2o-tab'}
            onClick={() => { if (!it.disabledReason) onChange(it.id) }}
          >
            <span>{it.label}</span>
            {it.meta != null && <span className="c2o-tab__ctx">{it.meta}</span>}
            {it.disabledReason && <span className="sr-only">{it.disabledReason}</span>}
          </button>
        )
      })}
    </div>
  )
}
