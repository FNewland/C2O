/**
 * BudgetPanel — Budget allocation and rollup for elements at the current level.
 *
 * Shows a table of child elements with:
 * - Allocation: what budget is assigned to this element (set by user)
 * - Actual: current value (from element properties or child rollup)
 * - Margin: allocation - actual
 * - Status: green/amber/red
 *
 * The top-level allocation on the parent constrains the total.
 * Per-child allocations break the parent allocation down.
 */
import { useState, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'

const API = '/api'

const BUDGET_TYPES = [
  { id: 'mass', label: 'Mass', unit: 'kg' },
  { id: 'power', label: 'Power', unit: 'W' },
  { id: 'data', label: 'Data', unit: 'Mbps' },
  { id: 'cost', label: 'Cost', unit: 'kEUR' },
]

const STATUS_COLORS: Record<string, string> = {
  green: 'var(--success)', amber: 'var(--warning)', red: 'var(--danger)', undefined: 'var(--text-secondary)',
}

export function BudgetPanel() {
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const [activeBudget, setActiveBudget] = useState('mass')
  const qc = useQueryClient()

  // Find root element if no focus
  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false, refetchInterval: 3000,
  })
  const targetId = focusElementId || allElements.find((e: any) => !e.parent_id)?.id

  // Detect constellation context: if an ancestor has quantity > 1, show per-unit values
  const constellationQty = useMemo(() => {
    if (!focusElementId) return 1
    let current = allElements.find((e: any) => e.id === focusElementId)
    while (current) {
      if ((current.quantity || 1) > 1) return current.quantity
      current = current.parent_id ? allElements.find((e: any) => e.id === current.parent_id) : null
    }
    return 1
  }, [focusElementId, allElements])
  const isConstellation = constellationQty > 1

  // Fetch budget
  const { data: budget, refetch: refetchBudget } = useQuery({
    queryKey: ['budget', targetId, activeBudget],
    queryFn: () => fetch(`${API}/elements/${targetId}/budget/${activeBudget}`).then(r => r.json()),
    enabled: !!targetId,
    structuralSharing: false,
    refetchInterval: 3000,  // Poll every 3s for live multi-user updates
  })

  const bt = BUDGET_TYPES.find(b => b.id === activeBudget)!

  // Set allocation on any element
  const setAllocation = useCallback(async (elementId: string, value: number) => {
    await fetch(`${API}/elements/${elementId}/allocations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ budget_type: activeBudget, allocation_value: value, unit: bt.unit, source: 'manual', rationale: '' }),
    })
    qc.invalidateQueries({ queryKey: ['budget'] })
  }, [activeBudget, bt.unit, qc])

  if (!targetId) {
    return <div style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Add a mission element first.</div>
  }

  // Compute total allocated to children
  const totalChildAlloc = (budget?.lines || []).reduce((s: number, l: any) => s + (l.allocation || 0), 0)
  const parentAlloc = budget?.allocation
  const unallocated = parentAlloc != null ? parentAlloc - totalChildAlloc : null

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: '0.75rem' }}>
      {/* Budget type selector */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.5rem', alignItems: 'center' }}>
        {BUDGET_TYPES.map(b => (
          <button key={b.id} onClick={() => setActiveBudget(b.id)} style={{
            padding: '0.25rem 0.6rem', fontSize: '0.72rem', borderRadius: '3px',
            background: activeBudget === b.id ? 'var(--accent)' : 'var(--bg-card)',
            color: activeBudget === b.id ? 'white' : 'var(--text-secondary)',
            border: 'none', cursor: 'pointer',
          }}>
            {b.label}
          </button>
        ))}
        <span style={{ flex: 1 }} />
        {budget && (
          <span style={{
            padding: '0.2rem 0.5rem', borderRadius: '3px', fontWeight: 600, fontSize: '0.68rem',
            background: `${STATUS_COLORS[budget.status]}20`, color: STATUS_COLORS[budget.status],
          }}>
            {budget.margin_pct != null ? `${budget.margin_pct.toFixed(0)}% margin` : 'No allocation set'}
          </span>
        )}
      </div>

      {/* Auto-allocate from current values */}
      {budget?.lines?.some((l: any) => l.nominal > 0 && l.allocation == null) && (
        <button onClick={async () => {
          for (const line of budget.lines) {
            if (line.nominal > 0 && line.allocation == null) {
              // Set allocation to actual + 20% margin
              const alloc = Math.round(line.with_margin * 1.1 * 100) / 100
              await setAllocation(line.element_id, alloc)
            }
          }
        }} style={{
          marginBottom: '0.4rem', padding: '0.2rem 0.5rem', fontSize: '0.65rem', fontWeight: 600,
          borderRadius: '3px', background: 'rgba(59,130,246,0.15)', color: 'var(--accent)',
          border: '1px solid var(--accent)', cursor: 'pointer',
        }}>
          Auto-allocate from current values (+10% margin)
        </button>
      )}

      {/* Parent allocation row */}
      <div style={{
        display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '0.5rem',
        padding: '0.4rem 0.5rem', background: 'var(--bg-card)', borderRadius: '4px', border: '1px solid var(--border)',
      }}>
        <span style={{ fontWeight: 600, fontSize: '0.72rem' }}>
          {budget?.element_name || 'Parent'} {isConstellation ? `(per spacecraft, ×${constellationQty} in constellation)` : 'Total'}:
        </span>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.68rem' }}>Allocation:</span>
        <AllocationInput currentValue={parentAlloc} onSet={v => setAllocation(targetId, v)} unit={bt.unit} />
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.68rem' }}>
          Actual: <b style={{ color: 'var(--text-primary)' }}>{budget?.sum_with_margin?.toFixed(2) || '0'} {bt.unit}</b>
        </span>
        {budget?.remaining != null && (
          <span style={{ fontSize: '0.68rem', color: STATUS_COLORS[budget.status] }}>
            Remaining: <b>{budget.remaining.toFixed(2)} {bt.unit}</b>
          </span>
        )}
      </div>

      {/* Unallocated warning */}
      {unallocated != null && unallocated > 0 && totalChildAlloc > 0 && (
        <div style={{
          fontSize: '0.68rem', color: 'var(--warning)', marginBottom: '0.4rem', padding: '0.2rem 0.5rem',
          background: 'rgba(245,158,11,0.1)', borderRadius: '3px',
        }}>
          {unallocated.toFixed(2)} {bt.unit} unallocated to children
        </div>
      )}

      {/* Power budget summary bar */}
      {activeBudget === 'power' && budget?.total_avg_power != null && (
        <div style={{
          display: 'flex', gap: '1rem', marginBottom: '0.5rem', padding: '0.3rem 0.5rem',
          background: 'rgba(168,85,247,0.08)', borderRadius: '4px', fontSize: '0.68rem',
        }}>
          <span>Avg Power: <b>{budget.total_avg_power.toFixed(2)} W</b></span>
          <span>Peak Power: <b>{budget.total_peak_power.toFixed(2)} W</b></span>
        </div>
      )}

      {/* Data budget summary bar */}
      {activeBudget === 'data' && budget?.total_data_rate_mbps != null && (
        <div style={{
          display: 'flex', gap: '1rem', marginBottom: '0.5rem', padding: '0.3rem 0.5rem',
          background: 'rgba(6,182,212,0.08)', borderRadius: '4px', fontSize: '0.68rem',
        }}>
          <span>Total Data Rate: <b>{budget.total_data_rate_mbps.toFixed(3)} Mbps</b></span>
          <span>Volume/Day: <b>{budget.total_data_volume_gb_per_day.toFixed(3)} GB</b></span>
        </div>
      )}

      {/* Per-element table */}
      {budget?.lines?.length > 0 ? (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={thL}>Element</th>
              {activeBudget === 'power' ? (
                <>
                  <th style={thR}>Allocation (W)</th>
                  <th style={thR}>Avg (W)</th>
                  <th style={thR}>Peak (W)</th>
                  <th style={thR}>Duty %</th>
                  <th style={thR}>Margin</th>
                  <th style={thR}>Qty</th>
                  <th style={thC}>Status</th>
                </>
              ) : activeBudget === 'data' ? (
                <>
                  <th style={thR}>Data Rate (Mbps)</th>
                  <th style={thR}>Duty %</th>
                  <th style={thR}>Vol/Orbit (MB)</th>
                  <th style={thR}>Vol/Day (GB)</th>
                  <th style={thR}>Qty</th>
                </>
              ) : (
                <>
                  <th style={thR}>Allocation ({bt.unit})</th>
                  <th style={thR}>Actual ({bt.unit})</th>
                  <th style={thR}>Margin</th>
                  <th style={thR}>With Margin</th>
                  <th style={thR}>Qty</th>
                  <th style={thC}>Status</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {budget.lines.map((line: any) => {
              const childMargin = line.allocation != null && line.allocation > 0
                ? ((line.allocation - line.with_margin) / line.allocation * 100)
                : null
              const childStatus = childMargin == null ? 'undefined'
                : childMargin > 20 ? 'green' : childMargin > 0 ? 'amber' : 'red'

              if (activeBudget === 'power') {
                return (
                  <tr key={line.element_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '0.3rem 0.4rem', fontWeight: 500 }}>{line.name}</td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right' }}>
                      <AllocationInput currentValue={line.allocation} onSet={v => setAllocation(line.element_id, v)} unit="W" />
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontFamily: 'monospace' }}>
                      {(line.power_avg_w || 0) > 0 ? line.power_avg_w.toFixed(2) : '—'}
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontFamily: 'monospace' }}>
                      {(line.power_peak_w || 0) > 0 ? line.power_peak_w.toFixed(2) : '—'}
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', color: 'var(--text-secondary)' }}>
                      {line.duty_cycle != null ? `${(line.duty_cycle * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', color: 'var(--text-secondary)' }}>
                      {line.margin_pct}%
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', color: 'var(--text-secondary)' }}>
                      {line.quantity > 1 ? `×${line.quantity}` : ''}
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'center' }}>
                      {childMargin != null ? (
                        <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: STATUS_COLORS[childStatus] }} title={`${childMargin.toFixed(0)}% margin`} />
                      ) : <span style={{ color: 'var(--text-secondary)', fontSize: '0.6rem' }}>—</span>}
                    </td>
                  </tr>
                )
              }

              if (activeBudget === 'data') {
                return (
                  <tr key={line.element_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '0.3rem 0.4rem', fontWeight: 500 }}>{line.name}</td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontFamily: 'monospace' }}>
                      {(line.data_rate_mbps || 0) > 0 ? line.data_rate_mbps.toFixed(3) : '—'}
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', color: 'var(--text-secondary)' }}>
                      {line.duty_cycle != null ? `${(line.duty_cycle * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontFamily: 'monospace' }}>
                      {(line.volume_per_orbit_mb || 0) > 0 ? line.volume_per_orbit_mb.toFixed(2) : '—'}
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontFamily: 'monospace' }}>
                      {(line.data_volume_gb_per_day || 0) > 0 ? line.data_volume_gb_per_day.toFixed(3) : '—'}
                    </td>
                    <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', color: 'var(--text-secondary)' }}>
                      {line.quantity > 1 ? `×${line.quantity}` : ''}
                    </td>
                  </tr>
                )
              }

              // Default: mass, cost, volume
              return (
                <tr key={line.element_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '0.3rem 0.4rem', fontWeight: 500 }}>{line.name}</td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right' }}>
                    <AllocationInput
                      currentValue={line.allocation}
                      onSet={v => setAllocation(line.element_id, v)}
                      unit={bt.unit}
                    />
                  </td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {line.nominal > 0 ? line.nominal.toFixed(2) : '—'}
                    {line.quantity > 1 && line.per_unit > 0 && (
                      <div style={{ fontSize: '0.55rem', color: 'var(--text-secondary)' }}>
                        {line.per_unit.toFixed(2)} ea
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', color: 'var(--text-secondary)' }}>
                    {line.margin_pct}%
                  </td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>
                    {line.with_margin > 0 ? line.with_margin.toFixed(2) : '—'}
                  </td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', color: 'var(--text-secondary)' }}>
                    {line.quantity > 1 ? `×${line.quantity}` : ''}
                    {line.quantity > 1 && line.allocation_per_unit != null && (
                      <div style={{ fontSize: '0.55rem', color: 'var(--info)' }}>
                        {line.allocation_per_unit.toFixed(1)}/ea
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'center' }}>
                    {childMargin != null ? (
                      <span style={{
                        display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
                        background: STATUS_COLORS[childStatus],
                      }} title={`${childMargin.toFixed(0)}% margin`} />
                    ) : (
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.6rem' }}>—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
          <tfoot>
            <tr style={{ borderTop: '2px solid var(--border)' }}>
              <td style={{ padding: '0.3rem 0.4rem', fontWeight: 700 }}>Total</td>
              {activeBudget === 'power' ? (
                <>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                    {totalChildAlloc > 0 ? totalChildAlloc.toFixed(2) : '—'}
                  </td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                    {budget.total_avg_power?.toFixed(2) || '0.00'}
                  </td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                    {budget.total_peak_power?.toFixed(2) || '0.00'}
                  </td>
                  <td /><td /><td /><td />
                </>
              ) : activeBudget === 'data' ? (
                <>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                    {budget.total_data_rate_mbps?.toFixed(3) || '0.000'}
                  </td>
                  <td />
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                    {budget.lines.reduce((s: number, l: any) => s + (l.volume_per_orbit_mb || 0), 0).toFixed(2)}
                  </td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                    {budget.total_data_volume_gb_per_day?.toFixed(3) || '0.000'}
                  </td>
                  <td />
                </>
              ) : (
                <>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                    {totalChildAlloc > 0 ? totalChildAlloc.toFixed(2) : '—'}
                  </td>
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                    {budget.sum_nominal.toFixed(2)}
                  </td>
                  <td />
                  <td style={{ padding: '0.3rem 0.4rem', textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                    {budget.sum_with_margin.toFixed(2)}
                  </td>
                  <td /><td />
                </>
              )}
            </tr>
          </tfoot>
        </table>
      ) : (
        <div style={{ color: 'var(--text-secondary)', padding: '0.5rem 0' }}>
          No child elements. Add elements in the Blocks panel first.
        </div>
      )}
    </div>
  )
}

const thL: React.CSSProperties = { textAlign: 'left', padding: '0.3rem 0.4rem', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.65rem', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...thL, textAlign: 'right' }
const thC: React.CSSProperties = { ...thL, textAlign: 'center' }

/** Inline allocation input that shows current value and allows editing */
function AllocationInput({ currentValue, onSet, unit }: { currentValue: number | null | undefined; onSet: (v: number) => void; unit: string }) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState('')

  if (editing) {
    return (
      <input
        type="number"
        autoFocus
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
        style={{
          width: 65, padding: '0.15rem 0.3rem', fontSize: '0.7rem', borderRadius: '3px', textAlign: 'right',
          background: 'var(--bg-primary)', border: '1px solid var(--accent)', color: 'var(--text-primary)',
        }}
      />
    )
  }

  return (
    <button
      onClick={() => { setValue(currentValue != null ? String(currentValue) : ''); setEditing(true) }}
      style={{
        background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.72rem',
        fontFamily: 'monospace', fontWeight: 600, padding: '0.1rem 0.2rem', borderRadius: '2px',
        color: currentValue != null ? 'var(--text-primary)' : 'var(--text-secondary)',
        textDecoration: currentValue == null ? 'underline dotted' : 'none',
      }}
      title="Click to set allocation"
    >
      {currentValue != null ? `${currentValue.toFixed(1)}` : 'set'}
    </button>
  )
}
