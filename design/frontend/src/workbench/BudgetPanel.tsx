/**
 * BudgetPanel — budget allocation and rollup for the elements at this level.
 *
 * Picture first (C2O brief §1.1): the parent's value against its allocation,
 * then one bar per child on a shared scale. The detail table (allocations,
 * nominal, maturity margin, quantities) is one click deeper.
 *
 * ECSS vocabulary (ECSS-E-ST-10C / ECSS-M-ST-10C): nominal = current best
 * estimate; maturity margin = the per-element margin for design maturity;
 * allocation = the value apportioned from the level above; margin to
 * allocation = (allocation − nominal with margin) / allocation.
 */
import { useState, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { displayElementName } from './BlocksPanel'
import { Button, DataTable, Disclosure, MarginBar, MarginBarKey, Note, NoData, Panel, Tabs, fmtNum, tabPanelProps, type Column } from '../components/ui'

const API = '/api'

/** System line: caution below the ECSS 20 % system margin. Element lines: caution when within 5 % of their allocation. */
const ELEMENT_CAUTION_PCT = 5

type BudgetKind = 'mass' | 'power' | 'data' | 'cost'

// English text is the i18n key
const BUDGET_TYPES: Array<{ id: BudgetKind; label: string; unit: string; digits: number }> = [
  { id: 'mass', label: 'Mass', unit: 'kg', digits: 2 },
  { id: 'power', label: 'Power', unit: 'W', digits: 1 },
  { id: 'data', label: 'Data', unit: 'Mbps', digits: 3 },
  { id: 'cost', label: 'Cost', unit: 'kEUR', digits: 0 },
]

interface BudgetLine {
  element_id: string; name: string; nominal: number; with_margin: number; margin_pct: number
  quantity: number; per_unit: number; allocation: number | null; allocation_per_unit: number | null
  power_avg_w?: number; power_peak_w?: number; duty_cycle?: number | null
  data_rate_mbps?: number; volume_per_orbit_mb?: number; data_volume_gb_per_day?: number
}

export function BudgetPanel() {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const [activeBudget, setActiveBudget] = useState<BudgetKind>('mass')
  const [autoBusy, setAutoBusy] = useState(false)
  const qc = useQueryClient()

  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false, refetchInterval: 3000,
  })
  const targetId = focusElementId || allElements.find((e: any) => !e.parent_id)?.id

  // Constellation context: an ancestor with quantity > 1 means per-spacecraft values.
  const constellationQty = useMemo(() => {
    if (!focusElementId) return 1
    let current = allElements.find((e: any) => e.id === focusElementId)
    while (current) {
      if ((current.quantity || 1) > 1) return current.quantity
      current = current.parent_id ? allElements.find((e: any) => e.id === current.parent_id) : null
    }
    return 1
  }, [focusElementId, allElements])

  const { data: budget } = useQuery({
    queryKey: ['budget', targetId, activeBudget],
    queryFn: () => fetch(`${API}/elements/${targetId}/budget/${activeBudget}`).then(r => r.json()),
    enabled: !!targetId,
    structuralSharing: false,
    refetchInterval: 3000,  // live multi-user updates
  })

  const bt = BUDGET_TYPES.find(b => b.id === activeBudget)!

  const setAllocation = useCallback(async (elementId: string, value: number) => {
    await fetch(`${API}/elements/${elementId}/allocations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ budget_type: activeBudget, allocation_value: value, unit: bt.unit, source: 'manual', rationale: '' }),
    })
    qc.invalidateQueries({ queryKey: ['budget'] })
  }, [activeBudget, bt.unit, qc])

  if (!targetId) {
    return <div className="c2o-pane c2o-pane--empty c-2">{t('Add a mission element first.')}</div>
  }

  const lines: BudgetLine[] = budget?.lines || []
  const totalChildAlloc = lines.reduce((s, l) => s + (l.allocation || 0), 0)
  const parentAlloc: number | null = budget?.allocation ?? null
  const unallocated = parentAlloc != null && totalChildAlloc > 0 ? parentAlloc - totalChildAlloc : null
  const unallocatedLines = lines.filter(l => l.nominal > 0 && l.allocation == null)
  const scaleMax = Math.max(0, ...lines.map(l => Math.max(l.allocation ?? 0, l.with_margin ?? 0)))
  const parentName = budget?.element_name ? displayElementName(budget.element_name, t) : t('Parent')
  const kindLabel = t(bt.label)

  const autoAllocate = async () => {
    setAutoBusy(true)
    try {
      for (const line of unallocatedLines) {
        // Allocation = nominal with margin + 10 %
        await setAllocation(line.element_id, Math.round(line.with_margin * 1.1 * 100) / 100)
      }
    } finally { setAutoBusy(false) }
  }

  return (
    <div className="c2o-pane stack gap-4">
      <div className="row wrap gap-3">
        <Tabs idBase="budget" variant="segmented" label={t('Budget type')} value={activeBudget} onChange={setActiveBudget}
          items={BUDGET_TYPES.map(b => ({ id: b.id, label: t(b.label) }))} />
        {constellationQty > 1 && (
          <span className="t-12 c-2">{t('Per spacecraft, ×{{qty}} in the constellation', { qty: constellationQty })}</span>
        )}
        <span className="grow" />
        {unallocatedLines.length > 0 && (
          <Button size="sm" onClick={autoAllocate} busy={autoBusy}
            title={t('Sets each missing allocation to its nominal with margin, plus 10 %')}>
            {autoBusy ? t('Allocating...') : t('Allocate the {{n}} unallocated (+10 %)', { n: unallocatedLines.length })}
          </Button>
        )}
      </div>

      <div {...tabPanelProps('budget', activeBudget)} className="stack gap-4">
        {/* Level 1: the parent against its allocation */}
        <section aria-label={t('{{name}}: {{kind}} budget', { name: parentName, kind: kindLabel })} className="stack gap-2">
          <MarginBar lead label={parentName} nominal={budget?.sum_nominal ?? null} withMargin={budget?.sum_with_margin ?? null}
            allocation={parentAlloc} unit={bt.unit} digits={bt.digits} />
          <div className="row wrap gap-4 t-12 c-3">
            <span className="row gap-1">
              {t('Allocation')}
              <AllocationInput currentValue={parentAlloc} onSet={v => setAllocation(targetId, v)} unit={bt.unit} label={t('Allocation for {{name}}', { name: parentName })} />
              {bt.unit}
            </span>
            {activeBudget === 'power' && budget?.total_avg_power != null && (
              <span>{t('Orbit average')} <span className="mono c-v t-13">{fmtNum(budget.total_avg_power, 1)}</span> W · {t('Peak')} <span className="mono c-v t-13">{fmtNum(budget.total_peak_power, 1)}</span> W</span>
            )}
            {activeBudget === 'data' && budget?.total_data_rate_mbps != null && (
              <span>{t('Volume per day')} <span className="mono c-v t-13">{fmtNum(budget.total_data_volume_gb_per_day, 3)}</span> GB</span>
            )}
          </div>
          {unallocated != null && Math.abs(unallocated) > 1e-9 && (
            unallocated < 0
              ? <Note tone="caution">{t('Child allocations total {{sum}} {{unit}}, {{over}} {{unit}} more than the {{alloc}} {{unit}} allocated to {{name}}.', { sum: fmtNum(totalChildAlloc, bt.digits), over: fmtNum(-unallocated, bt.digits), alloc: fmtNum(parentAlloc!, bt.digits), unit: bt.unit, name: parentName })}</Note>
              : <Note>{t('{{value}} {{unit}} unallocated to children', { value: fmtNum(unallocated, bt.digits), unit: bt.unit })}</Note>
          )}
        </section>

        {/* Level 2: each child against its own allocation, on one scale */}
        <Panel title={t('By element')} meta={t('{{count}} elements', { count: lines.length, defaultValue_one: '{{count}} element' })} actions={lines.length > 0 ? <MarginBarKey /> : undefined}>
          {lines.length === 0 ? (
            <p className="t-13 c-2 m-0">{t('No child elements. Add elements in the Blocks panel first.')}</p>
          ) : (
            <div className="c2o-mbar-list">
              {lines.map(l => (
                <MarginBar key={l.element_id}
                  label={l.quantity > 1 ? `${displayElementName(l.name, t)} ×${l.quantity}` : displayElementName(l.name, t)}
                  nominal={l.nominal} withMargin={l.with_margin} allocation={l.allocation}
                  unit={bt.unit} digits={bt.digits} scaleMax={scaleMax} cautionBelowPct={ELEMENT_CAUTION_PCT} />
              ))}
            </div>
          )}
        </Panel>

        {/* Level 3: the numbers */}
        {lines.length > 0 && (
          <Disclosure summary={t('Detail table')} meta={t('allocations, nominal, maturity margin')} ruled>
            <BudgetTable kind={activeBudget} unit={bt.unit} digits={bt.digits} lines={lines} budget={budget} totalChildAlloc={totalChildAlloc} onSet={setAllocation} />
          </Disclosure>
        )}
      </div>
    </div>
  )
}

function BudgetTable({ kind, unit, digits, lines, budget, totalChildAlloc, onSet }: {
  kind: BudgetKind; unit: string; digits: number; lines: BudgetLine[]; budget: any; totalChildAlloc: number
  onSet: (id: string, v: number) => void
}) {
  const { t } = useTranslation()
  const nd = <NoData label={t('no data')} />
  const num = (v: number | null | undefined, d = digits) => (v != null && v > 0 ? fmtNum(v, d) : nd)
  const name: Column<BudgetLine> = { key: 'name', header: t('Element'), render: l => <span className="w-500">{displayElementName(l.name, t)}</span>, sort: l => l.name }
  const qty: Column<BudgetLine> = { key: 'qty', header: t('Qty'), num: true, render: l => (l.quantity > 1 ? `×${l.quantity}` : ''), sort: l => l.quantity }
  const alloc: Column<BudgetLine> = {
    key: 'alloc', header: t('Allocation ({{unit}})', { unit }), num: true, sort: l => l.allocation,
    render: l => <AllocationInput currentValue={l.allocation} onSet={v => onSet(l.element_id, v)} unit={unit} label={t('Allocation for {{name}}', { name: displayElementName(l.name, t) })} />,
    foot: totalChildAlloc > 0 ? fmtNum(totalChildAlloc, digits) : '',
  }
  const mgn: Column<BudgetLine> = { key: 'mgn', header: t('Maturity margin'), num: true, render: l => `${l.margin_pct} %`, sort: l => l.margin_pct }

  let columns: Column<BudgetLine>[]
  if (kind === 'power') {
    columns = [name, alloc,
      { key: 'avg', header: t('Avg (W)'), num: true, render: l => num(l.power_avg_w, 2), sort: l => l.power_avg_w, foot: fmtNum(budget?.total_avg_power ?? 0, 2) },
      { key: 'peak', header: t('Peak (W)'), num: true, render: l => num(l.power_peak_w, 2), sort: l => l.power_peak_w, foot: fmtNum(budget?.total_peak_power ?? 0, 2) },
      { key: 'duty', header: t('Duty %'), num: true, render: l => (l.duty_cycle != null ? `${(l.duty_cycle * 100).toFixed(0)} %` : nd), sort: l => l.duty_cycle },
      mgn, qty]
  } else if (kind === 'data') {
    columns = [name,
      { key: 'rate', header: t('Data Rate (Mbps)'), num: true, render: l => num(l.data_rate_mbps, 3), sort: l => l.data_rate_mbps, foot: fmtNum(budget?.total_data_rate_mbps ?? 0, 3) },
      { key: 'duty', header: t('Duty %'), num: true, render: l => (l.duty_cycle != null ? `${(l.duty_cycle * 100).toFixed(0)} %` : nd), sort: l => l.duty_cycle },
      { key: 'orbit', header: t('Vol/Orbit (MB)'), num: true, render: l => num(l.volume_per_orbit_mb, 2), sort: l => l.volume_per_orbit_mb, foot: fmtNum(lines.reduce((s, l) => s + (l.volume_per_orbit_mb || 0), 0), 2) },
      { key: 'day', header: t('Vol/Day (GB)'), num: true, render: l => num(l.data_volume_gb_per_day, 3), sort: l => l.data_volume_gb_per_day, foot: fmtNum(budget?.total_data_volume_gb_per_day ?? 0, 3) },
      qty]
  } else {
    columns = [name, alloc,
      {
        key: 'nom', header: t('Nominal ({{unit}})', { unit }), num: true, sort: l => l.nominal, foot: fmtNum(budget?.sum_nominal ?? 0, digits),
        render: l => <>{num(l.nominal)}{l.quantity > 1 && l.per_unit > 0 && <div className="t-12 c-3">{t('{{value}} ea', { value: fmtNum(l.per_unit, digits) })}</div>}</>,
      },
      mgn,
      { key: 'wm', header: t('With margin ({{unit}})', { unit }), num: true, render: l => <span className="w-600">{num(l.with_margin)}</span>, sort: l => l.with_margin, foot: fmtNum(budget?.sum_with_margin ?? 0, digits) },
      qty]
  }
  return <DataTable dense caption={t('Budget detail')} columns={columns} rows={lines} rowKey={l => l.element_id} />
}

/** Inline allocation editor: shows the value, edits on click (Enter saves, Esc cancels). */
function AllocationInput({ currentValue, onSet, unit, label }: { currentValue: number | null | undefined; onSet: (v: number) => void; unit: string; label: string }) {
  const { t } = useTranslation()
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState('')

  if (editing) {
    return (
      <input
        type="number"
        autoFocus
        aria-label={label}
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={e => {
          if (e.key === 'Enter' && value) { onSet(parseFloat(value)); setEditing(false); setValue('') }
          if (e.key === 'Escape') { setEditing(false); setValue('') }
        }}
        onBlur={() => {
          if (value) onSet(parseFloat(value))
          setEditing(false); setValue('')
        }}
        placeholder={unit}
        className="c2o-input c2o-input--sm c2o-input--num c2o-alloc-input"
      />
    )
  }

  return (
    <button
      type="button"
      className={currentValue != null ? 'c2o-alloc mono' : 'c2o-alloc c2o-alloc--unset'}
      onClick={() => { setValue(currentValue != null ? String(currentValue) : ''); setEditing(true) }}
      aria-label={`${label}: ${currentValue != null ? `${currentValue} ${unit}` : t('not set')}`}
      title={t('Click to set allocation')}
    >
      {currentValue != null ? fmtNum(currentValue, currentValue < 10 ? 2 : 1) : t('set')}
    </button>
  )
}
