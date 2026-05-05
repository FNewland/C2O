/**
 * EngineeringBudgets — Unified engineering budget view with margins and roll-up.
 *
 * Shows all budgets in one place: mass, power, link (up+down), pointing,
 * delta-V, volume, data, cost. Each with:
 * - Per-subsystem breakdown
 * - Configurable margins by design maturity
 * - Roll-up to system level
 * - Constraint violation warnings
 *
 * Per ECSS-E-HB-10-02A margin philosophy.
 */
import { useState, useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'

type BudgetType = 'mass' | 'power' | 'link' | 'pointing' | 'deltav' | 'volume' | 'data' | 'cost'

interface BudgetLine {
  subsystem: string
  value: number
  unit: string
  margin_pct: number
  value_with_margin: number
  source: string  // 'parametric' | 'equipment' | 'manual'
}

interface BudgetSummary {
  type: BudgetType
  label: string
  unit: string
  allocation: number
  total_nominal: number
  total_with_margin: number
  margin_remaining: number
  margin_pct: number
  status: 'green' | 'amber' | 'red'
  lines: BudgetLine[]
}

// Margin policy by design phase (configurable via Parametric tab)
const MARGIN_POLICY = {
  phase_a: { new_design: 20, modified: 10, off_the_shelf: 5, system: 20 },
  phase_b: { new_design: 15, modified: 7, off_the_shelf: 3, system: 15 },
  phase_c: { new_design: 10, modified: 5, off_the_shelf: 3, system: 10 },
}

const BUDGET_CONFIGS: { type: BudgetType; label: string; unit: string; color: string }[] = [
  { type: 'mass', label: 'Mass Budget', unit: 'kg', color: '#3b82f6' },
  { type: 'power', label: 'Power Budget', unit: 'W', color: '#f59e0b' },
  { type: 'link', label: 'Link Budget (Down)', unit: 'dB', color: '#ec4899' },
  { type: 'pointing', label: 'Pointing Budget', unit: 'deg', color: '#06b6d4' },
  { type: 'deltav', label: 'Delta-V Budget', unit: 'm/s', color: '#f97316' },
  { type: 'volume', label: 'Volume Budget', unit: 'cm3', color: '#84cc16' },
  { type: 'data', label: 'Data Budget', unit: 'GB/day', color: '#8b5cf6' },
  { type: 'cost', label: 'Cost Budget', unit: 'kEUR', color: '#14b8a6' },
]

export function EngineeringBudgets() {
  const params = useActiveParameters()
  const { requirements } = useDesignStore()
  const selectedEquipment = useDesignStore(s => s.selectedEquipment)
  const [activeBudget, setActiveBudget] = useState<BudgetType>('mass')
  const [designPhase, setDesignPhase] = useState<'phase_a' | 'phase_b' | 'phase_c'>('phase_a')

  const get = (id: string): number => {
    const p = params[id]
    return p && typeof p.value === 'number' ? p.value : 0
  }

  const margins = MARGIN_POLICY[designPhase]

  // Compute all budgets
  const budgets = useMemo<Record<BudgetType, BudgetSummary>>(() => {
    const equipMass = selectedEquipment.reduce((s, e) => s + e.mass_kg * e.quantity, 0)
    const equipPower = selectedEquipment.reduce((s, e) => s + e.power_w * e.quantity, 0)
    const equipCost = selectedEquipment.reduce((s, e) => s + e.cost_keur * e.quantity, 0)

    // Mass budget
    const massLines: BudgetLine[] = [
      { subsystem: 'Payload', value: get('payload.mass_kg') || (requirements.payloads?.[0]?.mass_kg || 0), unit: 'kg', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'EPS', value: get('power.eps_mass_kg'), unit: 'kg', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: selectedEquipment.some(e => e.category === 'batteries') ? 'equipment' : 'parametric' },
      { subsystem: 'AOCS', value: get('aocs.mass_kg'), unit: 'kg', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: selectedEquipment.some(e => e.category === 'reaction_wheels') ? 'equipment' : 'parametric' },
      { subsystem: 'TTC', value: get('link.ttc_mass_kg'), unit: 'kg', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'OBC', value: get('data.obc_mass_kg'), unit: 'kg', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'Thermal', value: get('thermal.tcs_mass_kg'), unit: 'kg', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'Structure', value: get('structure.mass_kg'), unit: 'kg', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'Propulsion', value: get('propulsion.total_mass_kg'), unit: 'kg', margin_pct: margins.modified, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'Harness', value: (get('mass.dry_mass_kg') || equipMass) * 0.04, unit: 'kg', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
    ]
    massLines.forEach(l => { l.value_with_margin = l.value * (1 + l.margin_pct / 100) })
    const massAlloc = requirements.target_mass_kg || 6
    const massTotalNom = massLines.reduce((s, l) => s + l.value, 0)
    const massTotalMarg = massLines.reduce((s, l) => s + l.value_with_margin, 0)
    // System margin on top
    const massTotalWithSys = massTotalMarg * (1 + margins.system / 100)
    const massMargRem = massAlloc - massTotalWithSys
    const massMargPct = massAlloc > 0 ? (massMargRem / massAlloc) * 100 : 0

    // Power budget (peak mode)
    const powerLines: BudgetLine[] = [
      { subsystem: 'Payload', value: requirements.payloads?.[0]?.power_w || 0, unit: 'W', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'AOCS', value: get('aocs.power_w') || 3, unit: 'W', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'TTC (TX)', value: get('link.ttc_power_w') || 6, unit: 'W', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'OBC', value: 1.5, unit: 'W', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
      { subsystem: 'Thermal', value: get('thermal.heater_power_w') || 2, unit: 'W', margin_pct: margins.off_the_shelf, value_with_margin: 0, source: 'parametric' },
    ]
    powerLines.forEach(l => { l.value_with_margin = l.value * (1 + l.margin_pct / 100) })
    const powerAlloc = get('power.sa_power_eol_w') || 15
    const powerTotalNom = powerLines.reduce((s, l) => s + l.value, 0)
    const powerTotalMarg = powerLines.reduce((s, l) => s + l.value_with_margin, 0)

    // Link budget
    const linkMargin = get('link.downlink_margin_db') || 0
    const linkAlloc = 3.0  // Minimum 3 dB per ECSS

    // Pointing
    const pointingTotal = get('aocs.pointing_accuracy_deg') || 0.1
    const pointingAlloc = requirements.payloads?.[0]?.pointing_accuracy_deg || 0.1

    // Delta-V
    const dvTotal = get('propulsion.delta_v_total_ms') || get('orbit.delta_v_total_ms') || 0
    const dvAlloc = dvTotal * 1.15  // 15% margin

    // Volume (CDS based)
    const volumeUsed = get('volume.utilisation_percent') || 50
    const formFactor = requirements.spacecraft_class === 'nano' ? 3000 : 6000
    const volumeAlloc = formFactor

    // Data
    const dataGen = get('data.generated_per_day_gb') || 5
    const dataDL = get('data.downlinked_per_day_gb') || 5
    const dataAlloc = dataDL

    // Cost
    const costTotal = get('cost.total_meur') ? get('cost.total_meur') * 1000 : equipCost + 200
    const costAlloc = (requirements.target_cost_meur || 5) * 1000

    return {
      mass: { type: 'mass', label: 'Mass', unit: 'kg', allocation: massAlloc, total_nominal: massTotalNom, total_with_margin: massTotalWithSys, margin_remaining: massMargRem, margin_pct: massMargPct, status: massMargPct > 20 ? 'green' : massMargPct > 0 ? 'amber' : 'red', lines: massLines },
      power: { type: 'power', label: 'Power (Peak)', unit: 'W', allocation: powerAlloc, total_nominal: powerTotalNom, total_with_margin: powerTotalMarg, margin_remaining: powerAlloc - powerTotalMarg, margin_pct: powerAlloc > 0 ? ((powerAlloc - powerTotalMarg) / powerAlloc * 100) : 0, status: powerTotalMarg < powerAlloc * 0.8 ? 'green' : powerTotalMarg < powerAlloc ? 'amber' : 'red', lines: powerLines },
      link: { type: 'link', label: 'Link (Downlink)', unit: 'dB', allocation: linkAlloc, total_nominal: linkMargin, total_with_margin: linkMargin, margin_remaining: linkMargin - linkAlloc, margin_pct: linkMargin > 0 ? ((linkMargin - linkAlloc) / linkAlloc * 100) : -100, status: linkMargin >= 6 ? 'green' : linkMargin >= 3 ? 'amber' : 'red', lines: [] },
      pointing: { type: 'pointing', label: 'Pointing', unit: 'deg', allocation: pointingAlloc, total_nominal: pointingTotal, total_with_margin: pointingTotal, margin_remaining: pointingAlloc - pointingTotal, margin_pct: pointingAlloc > 0 ? ((pointingAlloc - pointingTotal) / pointingAlloc * 100) : 0, status: pointingTotal < pointingAlloc * 0.8 ? 'green' : pointingTotal < pointingAlloc ? 'amber' : 'red', lines: [] },
      deltav: { type: 'deltav', label: 'Delta-V', unit: 'm/s', allocation: dvAlloc, total_nominal: dvTotal, total_with_margin: dvTotal, margin_remaining: dvAlloc - dvTotal, margin_pct: dvAlloc > 0 ? ((dvAlloc - dvTotal) / dvAlloc * 100) : 0, status: dvTotal > 0 ? 'green' : 'green', lines: [] },
      volume: { type: 'volume', label: 'Volume', unit: 'cm3', allocation: volumeAlloc, total_nominal: volumeUsed * volumeAlloc / 100, total_with_margin: volumeUsed * volumeAlloc / 100, margin_remaining: volumeAlloc * (1 - volumeUsed / 100), margin_pct: 100 - volumeUsed, status: volumeUsed < 85 ? 'green' : volumeUsed < 100 ? 'amber' : 'red', lines: [] },
      data: { type: 'data', label: 'Data', unit: 'GB/day', allocation: dataAlloc, total_nominal: dataGen, total_with_margin: dataGen, margin_remaining: dataDL - dataGen, margin_pct: dataDL > 0 ? ((dataDL - dataGen) / dataDL * 100) : 0, status: dataDL >= dataGen ? 'green' : 'red', lines: [] },
      cost: { type: 'cost', label: 'Cost', unit: 'kEUR', allocation: costAlloc, total_nominal: costTotal, total_with_margin: costTotal * 1.3, margin_remaining: costAlloc - costTotal * 1.3, margin_pct: costAlloc > 0 ? ((costAlloc - costTotal * 1.3) / costAlloc * 100) : 0, status: costTotal * 1.3 < costAlloc ? 'green' : costTotal < costAlloc ? 'amber' : 'red', lines: [] },
    }
  }, [params, requirements, selectedEquipment, margins])

  const active = budgets[activeBudget]
  const statusColors = { green: '#10b981', amber: '#f59e0b', red: '#ef4444' }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <h2 style={{ margin: 0 }}>Engineering Budgets</h2>
        <select className="select" value={designPhase} onChange={e => setDesignPhase(e.target.value as any)}
          style={{ fontSize: '0.72rem', width: 'auto' }}>
          <option value="phase_a">Phase A (20% margins)</option>
          <option value="phase_b">Phase B (15% margins)</option>
          <option value="phase_c">Phase C (10% margins)</option>
        </select>
      </div>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Per ECSS-E-HB-10-02A. Margins decrease with design maturity. Equipment margins: COTS {margins.off_the_shelf}%, modified {margins.modified}%, new {margins.new_design}%. System margin: {margins.system}%.
      </p>

      {/* Budget summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem', marginBottom: '1rem' }}>
        {BUDGET_CONFIGS.map(bc => {
          const b = budgets[bc.type]
          return (
            <button key={bc.type} onClick={() => setActiveBudget(bc.type)} style={{
              padding: '0.4rem', borderRadius: '6px', cursor: 'pointer', textAlign: 'center',
              background: activeBudget === bc.type ? `${bc.color}22` : 'var(--bg-secondary, #1f2937)',
              border: `1.5px solid ${activeBudget === bc.type ? bc.color : statusColors[b.status] + '60'}`,
              borderTop: `3px solid ${statusColors[b.status]}`,
            }}>
              <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>{bc.label}</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: statusColors[b.status], fontFamily: 'monospace' }}>
                {b.margin_pct.toFixed(0)}%
              </div>
              <div style={{ fontSize: '0.6rem', color: '#6b7280' }}>{bc.unit}</div>
            </button>
          )
        })}
      </div>

      {/* Active budget detail */}
      <div className="card" style={{ borderLeft: `3px solid ${BUDGET_CONFIGS.find(c => c.type === activeBudget)?.color || '#6b7280'}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
          <h3 style={{ fontSize: '0.9rem', margin: 0 }}>{active.label} Budget</h3>
          <span style={{
            fontSize: '0.65rem', padding: '0.1rem 0.4rem', borderRadius: '3px',
            background: `${statusColors[active.status]}22`, color: statusColors[active.status], fontWeight: 700,
          }}>{active.status === 'green' ? 'HEALTHY' : active.status === 'amber' ? 'TIGHT' : 'EXCEEDED'}</span>
        </div>

        {/* Summary bar */}
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', marginBottom: '0.5rem' }}>
          <span>Nominal: <strong>{active.total_nominal.toFixed(2)} {active.unit}</strong></span>
          <span>With margin: <strong>{active.total_with_margin.toFixed(2)} {active.unit}</strong></span>
          <span>Allocation: <strong>{active.allocation.toFixed(2)} {active.unit}</strong></span>
          <span style={{ color: statusColors[active.status], fontWeight: 700 }}>
            Margin: {active.margin_pct.toFixed(0)}% ({active.margin_remaining.toFixed(2)} {active.unit})
          </span>
        </div>

        {/* Progress bar */}
        <div style={{ height: 16, background: '#1f2937', borderRadius: '4px', overflow: 'hidden', marginBottom: '0.5rem', position: 'relative' }}>
          <div style={{ height: '100%', width: `${Math.min(100, (active.total_with_margin / Math.max(active.allocation, 0.01)) * 100)}%`, background: statusColors[active.status], borderRadius: '4px' }} />
          <span style={{ position: 'absolute', right: 4, top: 0, bottom: 0, display: 'flex', alignItems: 'center', fontSize: '0.6rem', color: 'white', fontWeight: 600 }}>
            {((active.total_with_margin / Math.max(active.allocation, 0.01)) * 100).toFixed(0)}% used
          </span>
        </div>

        {/* Per-subsystem breakdown (for mass and power) */}
        {active.lines.length > 0 && (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={{ padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af' }}>Subsystem</th>
                <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>Nominal</th>
                <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>Margin %</th>
                <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>With Margin</th>
                <th style={{ padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af' }}>Source</th>
              </tr>
            </thead>
            <tbody>
              {active.lines.filter(l => l.value > 0).map(l => (
                <tr key={l.subsystem} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '0.2rem 0.5rem' }}>{l.subsystem}</td>
                  <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>{l.value.toFixed(3)}</td>
                  <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', color: '#6b7280' }}>+{l.margin_pct}%</td>
                  <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>{l.value_with_margin.toFixed(3)}</td>
                  <td style={{ padding: '0.2rem 0.5rem', fontSize: '0.6rem', color: l.source === 'equipment' ? '#10b981' : '#6b7280' }}>{l.source}</td>
                </tr>
              ))}
              <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
                <td style={{ padding: '0.2rem 0.5rem' }}>Total + System ({margins.system}%)</td>
                <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>{active.total_nominal.toFixed(3)}</td>
                <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right' }}></td>
                <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: statusColors[active.status] }}>{active.total_with_margin.toFixed(3)}</td>
                <td></td>
              </tr>
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
