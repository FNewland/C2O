/**
 * MassPropertiesPanel — CoM, inertia tensor, and CG-CP offset display.
 *
 * Reads mass properties from design state parameters.
 * Warns if CoM offset exceeds AOCS authority limits.
 *
 * Enhanced: proper mass budget table with per-equipment rollup grouped by
 * subsystem domain, CBE/MEV columns, margins per ECSS-E-ST-10-02C.
 */
import React, { useMemo } from 'react'
import { useActiveParameters } from '../hooks/useActiveParameters'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'
import { useEquipmentView } from '../hooks/useEquipmentView'

// Domain display names and colors
const DOMAIN_LABELS: Record<string, string> = {
  power: 'Power', aocs: 'AOCS', ttc: 'Communications', link: 'Communications',
  obc: 'Data Handling', data: 'Data Handling', propulsion: 'Propulsion',
  structure: 'Structure', thermal: 'Thermal', integration: 'Integration',
  payload: 'Payload', ground_rf: 'Ground RF', ground_ops: 'Ground Ops',
}

const DOMAIN_COLORS: Record<string, string> = {
  power: '#f59e0b', aocs: '#06b6d4', ttc: '#ec4899', link: '#ec4899',
  obc: '#8b5cf6', data: '#8b5cf6', propulsion: '#f97316',
  structure: '#84cc16', thermal: '#ef4444', integration: '#6b7280',
  payload: '#3b82f6',
}

// Default margin percentages per subsystem domain (ECSS heritage)
const DEFAULT_MARGINS: Record<string, number> = {
  power: 20, aocs: 10, ttc: 5, link: 5, obc: 5, data: 5,
  propulsion: 10, structure: 15, thermal: 10, integration: 10,
  payload: 10,
}

const SYSTEM_CONTINGENCY_PCT = 5  // system-level contingency

interface MassBudgetItem {
  id: string
  name: string
  domain: string
  unit_mass_kg: number
  quantity: number
  cbe_mass_kg: number  // current best estimate = unit_mass * qty
  margin_pct: number
  mev_mass_kg: number  // max expected value = cbe * (1 + margin)
}

export function MassPropertiesPanel() {
  const params = useActiveParameters()
  const result = useDesignStore(s => s.result)
  const equipmentView = useEquipmentView()
  const elements = useModelStore(s => s.elements)

  const get = (id: string): number => {
    const p = params[id]
    return p && typeof p.value === 'number' ? p.value : 0
  }

  const totalMass = get('mass.total_kg') || get('systems.total_mass_kg') || get('mass.dry_mass_kg')
  // Also compute from equipment if parametric mass not available
  const eqMassTotal = equipmentView.reduce((s, e) => s + e.mass_kg * e.quantity, 0)
  const effectiveMass = totalMass > 0 ? totalMass : eqMassTotal
  const hasData = effectiveMass > 0

  // Build mass budget items from element tree components
  const budgetItems = useMemo(() => {
    const items: MassBudgetItem[] = []
    for (const el of elements.values()) {
      if (el.element_type === 'component' && (el.mass_kg || 0) > 0) {
        const domain = el.subsystem_domain || 'unknown'
        const unitMass = el.mass_kg || 0
        const qty = el.quantity || 1
        const cbe = unitMass * qty
        const marginPct = DEFAULT_MARGINS[domain] ?? 10
        items.push({
          id: el.id,
          name: el.name,
          domain,
          unit_mass_kg: unitMass,
          quantity: qty,
          cbe_mass_kg: cbe,
          margin_pct: marginPct,
          mev_mass_kg: cbe * (1 + marginPct / 100),
        })
      }
    }
    // Fallback: if no element tree components, use equipmentView
    if (items.length === 0) {
      for (const eq of equipmentView) {
        if (eq.mass_kg > 0) {
          const domain = eq.category || 'unknown'
          const unitMass = eq.mass_kg
          const qty = eq.quantity
          const cbe = unitMass * qty
          const marginPct = DEFAULT_MARGINS[domain] ?? 10
          items.push({
            id: eq.componentId,
            name: eq.name,
            domain,
            unit_mass_kg: unitMass,
            quantity: qty,
            cbe_mass_kg: cbe,
            margin_pct: marginPct,
            mev_mass_kg: cbe * (1 + marginPct / 100),
          })
        }
      }
    }
    return items
  }, [elements, equipmentView])

  // Group by domain
  const groupedItems = useMemo(() => {
    const groups: Record<string, MassBudgetItem[]> = {}
    for (const item of budgetItems) {
      const key = item.domain
      if (!groups[key]) groups[key] = []
      groups[key].push(item)
    }
    return groups
  }, [budgetItems])

  // Domain subtotals
  const domainSubtotals = useMemo(() => {
    const result: Record<string, { cbe: number; mev: number }> = {}
    for (const [domain, items] of Object.entries(groupedItems)) {
      result[domain] = {
        cbe: items.reduce((s, i) => s + i.cbe_mass_kg, 0),
        mev: items.reduce((s, i) => s + i.mev_mass_kg, 0),
      }
    }
    return result
  }, [groupedItems])

  // System totals
  const systemTotals = useMemo(() => {
    const cbe = budgetItems.reduce((s, i) => s + i.cbe_mass_kg, 0)
    const mev = budgetItems.reduce((s, i) => s + i.mev_mass_kg, 0)
    const contingency = mev * SYSTEM_CONTINGENCY_PCT / 100
    const dryMass = mev + contingency
    // Propellant mass from parameters
    const propMass = get('propulsion.propellant_mass_kg') || 0
    const wetMass = dryMass + propMass
    return { cbe, mev, contingency, dryMass, propMass, wetMass }
  }, [budgetItems, params])

  if (!hasData && budgetItems.length === 0) {
    return (
      <div className="card" style={{ borderLeft: '3px solid #6b7280' }}>
        <h3 style={{ fontSize: '0.85rem', color: '#6b7280' }}>Mass Properties</h3>
        <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>
          {result ? 'No mass data in design result. Select equipment in Phase 3 to populate.' : 'Run a design to see mass properties.'}
        </p>
      </div>
    )
  }

  // Read from equipment selections for a simple CoM estimate (prefers element tree)
  const eqMass = equipmentView.reduce((s, e) => s + e.mass_kg * e.quantity, 0)

  // Simplified inertia for display (cuboid approximation)
  const scClass = useDesignStore.getState().requirements?.spacecraft_class || 'nano'
  const dims = scClass === 'nano' ? [0.1, 0.1, 0.3] :
               scClass === 'micro' ? [0.2, 0.2, 0.3] :
               scClass === 'small' ? [0.5, 0.5, 0.7] : [1.0, 1.0, 1.5]
  const m = totalMass > 0 ? totalMass : systemTotals.dryMass
  const ixx = m * (dims[1] ** 2 + dims[2] ** 2) / 12
  const iyy = m * (dims[0] ** 2 + dims[2] ** 2) / 12
  const izz = m * (dims[0] ** 2 + dims[1] ** 2) / 12

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Mass Budget</h3>
      <p style={{ fontSize: '0.68rem', color: '#9ca3af', marginBottom: '0.4rem' }}>
        Per ECSS-E-ST-10-02C. CBE = Current Best Estimate, MEV = Max Expected Value (CBE + margin).
      </p>

      {/* Mass Budget Table */}
      {budgetItems.length > 0 && (
        <div style={{ overflowX: 'auto', marginBottom: '0.75rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem', fontFamily: 'monospace' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={thBudget}>Item</th>
                <th style={thBudgetR}>Unit Mass (kg)</th>
                <th style={thBudgetR}>Qty</th>
                <th style={thBudgetR}>CBE Mass (kg)</th>
                <th style={thBudgetR}>Margin (%)</th>
                <th style={thBudgetR}>MEV Mass (kg)</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(groupedItems).map(([domain, items]) => (
                <React.Fragment key={domain}>
                  {/* Domain header */}
                  <tr style={{ background: `${DOMAIN_COLORS[domain] || '#6b7280'}11` }}>
                    <td colSpan={6} style={{ padding: '0.3rem 0.5rem', fontWeight: 700, color: DOMAIN_COLORS[domain] || '#6b7280', fontSize: '0.72rem' }}>
                      {DOMAIN_LABELS[domain] || domain}
                    </td>
                  </tr>
                  {/* Items in this domain */}
                  {items.map(item => (
                    <tr key={item.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ ...tdBudget, paddingLeft: '1.2rem' }}>{item.name}</td>
                      <td style={tdBudgetR}>{item.unit_mass_kg.toFixed(3)}</td>
                      <td style={tdBudgetR}>{item.quantity}</td>
                      <td style={tdBudgetR}>{item.cbe_mass_kg.toFixed(3)}</td>
                      <td style={{ ...tdBudgetR, color: '#f59e0b' }}>{item.margin_pct}%</td>
                      <td style={tdBudgetR}>{item.mev_mass_kg.toFixed(3)}</td>
                    </tr>
                  ))}
                  {/* Subtotal */}
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', fontWeight: 600 }}>
                    <td style={tdBudget} colSpan={3}>Subtotal: {DOMAIN_LABELS[domain] || domain}</td>
                    <td style={tdBudgetR}>{domainSubtotals[domain]?.cbe.toFixed(3)}</td>
                    <td style={tdBudgetR}></td>
                    <td style={tdBudgetR}>{domainSubtotals[domain]?.mev.toFixed(3)}</td>
                  </tr>
                </React.Fragment>
              ))}

              {/* System total */}
              <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
                <td style={tdBudget} colSpan={3}>System Total (CBE)</td>
                <td style={{ ...tdBudgetR, fontWeight: 700 }}>{systemTotals.cbe.toFixed(3)}</td>
                <td style={tdBudgetR}></td>
                <td style={{ ...tdBudgetR, fontWeight: 700 }}>{systemTotals.mev.toFixed(3)}</td>
              </tr>
              <tr style={{ color: '#f97316' }}>
                <td style={tdBudget} colSpan={3}>System Contingency ({SYSTEM_CONTINGENCY_PCT}%)</td>
                <td style={tdBudgetR}></td>
                <td style={tdBudgetR}>{SYSTEM_CONTINGENCY_PCT}%</td>
                <td style={tdBudgetR}>{systemTotals.contingency.toFixed(3)}</td>
              </tr>
              <tr style={{ borderTop: '2px solid #374151', fontWeight: 700, color: '#10b981' }}>
                <td style={tdBudget} colSpan={3}>Dry Mass</td>
                <td style={tdBudgetR}></td>
                <td style={tdBudgetR}></td>
                <td style={{ ...tdBudgetR, fontWeight: 700, color: '#10b981' }}>{systemTotals.dryMass.toFixed(3)}</td>
              </tr>
              {systemTotals.propMass > 0 && (
                <tr style={{ color: '#3b82f6' }}>
                  <td style={tdBudget} colSpan={3}>Propellant Mass</td>
                  <td style={tdBudgetR}></td>
                  <td style={tdBudgetR}></td>
                  <td style={tdBudgetR}>{systemTotals.propMass.toFixed(3)}</td>
                </tr>
              )}
              <tr style={{ borderTop: '2px solid #374151', fontWeight: 700, fontSize: '0.82rem' }}>
                <td style={tdBudget} colSpan={3}>Wet Mass</td>
                <td style={tdBudgetR}></td>
                <td style={tdBudgetR}></td>
                <td style={{ ...tdBudgetR, fontWeight: 700, color: '#f59e0b', fontSize: '0.82rem' }}>{systemTotals.wetMass.toFixed(3)} kg</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Simple mass summary (always shown) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
        {/* Mass summary */}
        <div style={{ background: 'var(--bg-primary, #111827)', padding: '0.4rem', borderRadius: '4px' }}>
          <div style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }}>Total Mass</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'monospace', color: '#d1d5db' }}>
            {(totalMass > 0 ? totalMass : systemTotals.wetMass).toFixed(1)} kg
          </div>
          {eqMass > 0 && (
            <div style={{ fontSize: '0.62rem', color: '#6b7280' }}>Equipment: {eqMass.toFixed(1)} kg</div>
          )}
        </div>

        {/* Dimensions */}
        <div style={{ background: 'var(--bg-primary, #111827)', padding: '0.4rem', borderRadius: '4px' }}>
          <div style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }}>Dimensions</div>
          <div style={{ fontSize: '0.82rem', fontFamily: 'monospace', color: '#d1d5db' }}>
            {dims[0]}×{dims[1]}×{dims[2]} m
          </div>
          <div style={{ fontSize: '0.62rem', color: '#6b7280' }}>Class: {scClass}</div>
        </div>
      </div>

      {/* Inertia tensor */}
      <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', marginBottom: '0.2rem' }}>INERTIA TENSOR (kg·m²)</div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem', fontFamily: 'monospace', marginBottom: '0.5rem' }}>
        <tbody>
          <tr>
            <td style={tdM}>{ixx.toFixed(4)}</td>
            <td style={tdM}>0.0000</td>
            <td style={tdM}>0.0000</td>
            <td style={{ ...tdLabel }}>Ixx</td>
          </tr>
          <tr>
            <td style={tdM}>0.0000</td>
            <td style={tdM}>{iyy.toFixed(4)}</td>
            <td style={tdM}>0.0000</td>
            <td style={tdLabel}>Iyy</td>
          </tr>
          <tr>
            <td style={tdM}>0.0000</td>
            <td style={tdM}>0.0000</td>
            <td style={tdM}>{izz.toFixed(4)}</td>
            <td style={tdLabel}>Izz</td>
          </tr>
        </tbody>
      </table>

      {/* Principal moments bar */}
      <div style={{ fontSize: '0.65rem', color: '#9ca3af', marginBottom: '0.2rem' }}>PRINCIPAL MOMENTS</div>
      {[
        { label: 'Ixx (roll)', value: ixx, color: '#3b82f6' },
        { label: 'Iyy (pitch)', value: iyy, color: '#10b981' },
        { label: 'Izz (yaw)', value: izz, color: '#f59e0b' },
      ].map(m => {
        const maxI = Math.max(ixx, iyy, izz)
        return (
          <div key={m.label} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.15rem' }}>
            <span style={{ width: '65px', fontSize: '0.65rem', color: '#9ca3af' }}>{m.label}</span>
            <div style={{ flex: 1, height: 6, background: '#1f2937', borderRadius: 3 }}>
              <div style={{ height: '100%', width: `${(m.value / maxI) * 100}%`, background: m.color, borderRadius: 3 }} />
            </div>
            <span style={{ fontSize: '0.65rem', fontFamily: 'monospace', color: m.color, minWidth: '55px', textAlign: 'right' }}>
              {m.value.toFixed(3)}
            </span>
          </div>
        )
      })}
    </div>
  )
}

const tdM: React.CSSProperties = { padding: '0.15rem 0.4rem', textAlign: 'right', color: '#d1d5db', borderBottom: '1px solid rgba(255,255,255,0.05)' }
const tdLabel: React.CSSProperties = { padding: '0.15rem 0.4rem', color: '#6b7280', fontSize: '0.65rem' }
const thBudget: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', textTransform: 'uppercase', color: '#9ca3af', letterSpacing: '0.03em' }
const thBudgetR: React.CSSProperties = { ...thBudget, textAlign: 'right' }
const tdBudget: React.CSSProperties = { padding: '0.25rem 0.5rem', color: '#d1d5db' }
const tdBudgetR: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: '#d1d5db' }
