/**
 * DataTable: dense, tabular figures, sortable headers, a real empty state.
 *
 *   <DataTable rows={lines} rowKey={l => l.id} caption={t('Mass budget')}
 *     empty={t('No child elements yet.')}
 *     columns={[
 *       { key: 'name', header: t('Element'), render: l => l.name, sort: l => l.name },
 *       { key: 'mass', header: t('Mass (kg)'), num: true, render: l => fmt(l.mass), sort: l => l.mass },
 *     ]} />
 *
 * `num` right-aligns in IBM Plex Mono with tabular figures. Sorting is
 * client-side and announced through aria-sort.
 */
import { useMemo, useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { cx } from './util'

export interface Column<R> {
  key: string
  header: ReactNode
  render: (row: R, index: number) => ReactNode
  /** Sort key; omit for an unsortable column. */
  sort?: (row: R) => number | string | null | undefined
  num?: boolean
  center?: boolean
  width?: number | string
  /** Footer cell. */
  foot?: ReactNode
  className?: string
}

export interface DataTableProps<R> {
  columns: Column<R>[]
  rows: R[]
  rowKey: (row: R, index: number) => string
  /** Visually hidden caption (accessible name). */
  caption?: string
  empty?: ReactNode
  dense?: boolean
  onRowClick?: (row: R) => void
  isSelected?: (row: R) => boolean
  rowClassName?: (row: R) => string | undefined
  defaultSort?: { key: string; dir: 'asc' | 'desc' }
  className?: string
}

export function DataTable<R>({ columns, rows, rowKey, caption, empty, dense, onRowClick, isSelected, rowClassName, defaultSort, className }: DataTableProps<R>) {
  const { t } = useTranslation()
  const [sort, setSort] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(defaultSort ?? null)

  const sorted = useMemo(() => {
    if (!sort) return rows
    const col = columns.find(c => c.key === sort.key)
    if (!col?.sort) return rows
    const get = col.sort
    const out = [...rows].sort((a, b) => {
      const va = get(a), vb = get(b)
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      if (typeof va === 'number' && typeof vb === 'number') return va - vb
      return String(va).localeCompare(String(vb), undefined, { numeric: true })
    })
    return sort.dir === 'asc' ? out : out.reverse()
  }, [rows, columns, sort])

  const hasFoot = columns.some(c => c.foot != null)

  return (
    // Focusable region so a table wider than the screen can be scrolled from the keyboard.
    <div className="c2o-table-wrap" role="region" aria-label={caption} tabIndex={caption ? 0 : undefined}>
      <table className={cx('c2o-table', dense && 'c2o-table--dense', className)}>
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr>
            {columns.map(c => {
              const active = sort?.key === c.key
              const ariaSort = active ? (sort!.dir === 'asc' ? 'ascending' : 'descending') : c.sort ? 'none' : undefined
              return (
                <th key={c.key} scope="col" aria-sort={ariaSort} className={cx(c.num && 'num', c.center && 'ctr', c.className)} style={c.width != null ? { width: c.width } : undefined}>
                  {c.sort ? (
                    <button type="button" className="c2o-table__sort"
                      onClick={() => setSort(s => s?.key === c.key ? { key: c.key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: c.key, dir: c.num ? 'desc' : 'asc' })}>
                      {c.header}
                      <span className="c2o-table__sort-ind" aria-hidden="true">{active ? (sort!.dir === 'asc' ? '▲' : '▼') : ''}</span>
                    </button>
                  ) : c.header}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr className="c2o-table__empty"><td colSpan={columns.length}>{empty ?? t('Nothing to show yet.')}</td></tr>
          ) : sorted.map((r, i) => (
            <tr key={rowKey(r, i)}
              className={cx(onRowClick && 'is-clickable', rowClassName?.(r))}
              data-selected={isSelected?.(r) ? 'true' : undefined}
              onClick={onRowClick ? () => onRowClick(r) : undefined}>
              {columns.map(c => (
                <td key={c.key} className={cx(c.num && 'num', c.center && 'ctr', c.className)}>{c.render(r, i)}</td>
              ))}
            </tr>
          ))}
        </tbody>
        {hasFoot && sorted.length > 0 && (
          <tfoot>
            <tr>{columns.map(c => <td key={c.key} className={cx(c.num && 'num', c.center && 'ctr')}>{c.foot}</td>)}</tr>
          </tfoot>
        )}
      </table>
    </div>
  )
}
