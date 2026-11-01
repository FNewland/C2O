/**
 * BudgetComparison — Shows parametric estimates vs selected equipment.
 *
 * Displays side-by-side: agent-computed parametric values and COTS-selected
 * actual values, with margin percentages and volume fit assessment.
 */
import { useMemo, useState } from 'react'
import { useDesignStore, type DesignParam } from '../stores/designStore'
import { useEquipmentView } from '../hooks/useEquipmentView'
import { fs } from '../theme/tokens'

// CDS internal volumes per form factor (cm³)
const CDS_VOLUMES: Record<string, number> = {
  '1U': 1000, '1.5U': 1500, '2U': 2000, '3U': 3000,
  '6U': 6000, '12U': 12000, '16U': 16000, '27U': 27000,
}

// Typical volume per subsystem (fraction of total bus volume)

interface BudgetRow {
  subsystem: string
  parametric_mass_kg: number
  selected_mass_kg: number | null
  parametric_power_w: number
  selected_power_w: number | null
  parametric_cost_keur: number
  selected_cost_keur: number | null
}

export function BudgetComparison() {
  // Use result.parameters directly (stable ref) to avoid recharts infinite loop
  const result = useDesignStore(s => s.result)
  const params = (result?.parameters || {}) as Record<string, DesignParam>
  const { requirements } = useDesignStore()
  const markStale = useDesignStore(s => s.markStale)
  const [editMode, setEditMode] = useState(false)
  const [allocations, setAllocations] = useState<Record<string, number>>({})

  const get = (id: string): number => {
    const p = params[id]
    return p && typeof p.value === 'number' ? p.value : 0
  }

  // Build comparison rows from parametric agent outputs
  const rows = useMemo<BudgetRow[]>(() => {
    const subsystems = [
      { id: 'payload', label: 'Payload', mass: 'payload.mass_kg', power: 'payload.power_w' },
      { id: 'power', label: 'EPS + Solar + Battery', mass: 'power.eps_mass_kg', power: 'power.total_sunlight_w' },
      { id: 'aocs', label: 'AOCS', mass: 'aocs.mass_kg', power: 'aocs.power_w' },
      { id: 'link', label: 'TTC / Comms', mass: 'link.ttc_mass_kg', power: 'link.ttc_power_w' },
      { id: 'data', label: 'OBC / Data', mass: 'data.obc_mass_kg', power: 'data.obc_power_w' },
      { id: 'thermal', label: 'Thermal', mass: 'thermal.tcs_mass_kg', power: 'thermal.heater_power_w' },
      { id: 'propulsion', label: 'Propulsion', mass: 'propulsion.total_mass_kg', power: 'propulsion.power_w' },
      { id: 'structure', label: 'Structure', mass: 'structure.mass_kg', power: '' },
    ]

    return subsystems.map(s => ({
      subsystem: s.label,
      parametric_mass_kg: get(s.mass),
      selected_mass_kg: null, // TODO: wire from equipment selections
      parametric_power_w: s.power ? get(s.power) : 0,
      selected_power_w: null,
      parametric_cost_keur: 0,
      selected_cost_keur: null,
    }))
  }, [params])

  const totalParametricMass = rows.reduce((s, r) => s + r.parametric_mass_kg, 0)
  const totalParametricPower = rows.reduce((s, r) => s + r.parametric_power_w, 0)

  // UPWARD FLOW: Equipment selections roll up into budget totals (prefers element tree)
  const selectedEquipment = useEquipmentView()
  const equipTotalMass = selectedEquipment.reduce((s, e) => s + (e.mass_kg * e.quantity), 0)
  const equipTotalPower = selectedEquipment.reduce((s, e) => s + (e.power_w * e.quantity), 0)
  const equipTotalCost = selectedEquipment.reduce((s, e) => s + (e.cost_keur * e.quantity), 0)
  const hasEquipment = selectedEquipment.length > 0

  // Use equipment totals if available (more accurate than parametric), otherwise parametric
  const dryMass = hasEquipment ? equipTotalMass : (get('mass.dry_mass_kg') || totalParametricMass)
  const massMargin = get('systems.mass_margin_percent')
  const powerMargin = get('systems.power_margin_percent')

  // Constraint violation check (UPWARD feedback to mission level)
  const targetMass = requirements.target_mass_kg
  const massExceeded = targetMass && dryMass > targetMass
  const totalCost = get('cost.total_meur')

  // Volume fit assessment
  const scClass = requirements.spacecraft_class || 'nano'
  const formFactor = scClass === 'nano' ? '3U' : scClass === 'micro' ? '6U' : '12U'
  const availableVolume = CDS_VOLUMES[formFactor] || 3000
  const volumeUtil = get('volume.utilisation_percent') || 0

  return (
    <div className="card">
      {/* UPWARD FEEDBACK: Constraint violation warning */}
      {massExceeded && (
        <div style={{
          padding: '0.4rem 0.6rem', marginBottom: '0.5rem', borderRadius: '4px',
          background: 'rgba(239,68,68,0.1)', border: '1px solid color-mix(in srgb, var(--status-alarm) 25%, transparent)',
          fontSize: fs.label, color: 'var(--status-alarm)', fontWeight: 600,
        }}>
          MISSION CONSTRAINT VIOLATED: Equipment mass ({dryMass.toFixed(1)} kg) exceeds
          mission target ({targetMass} kg). Reduce equipment or increase mass allocation.
        </div>
      )}
      {hasEquipment && !massExceeded && (
        <div style={{
          padding: '0.3rem 0.6rem', marginBottom: '0.5rem', borderRadius: '4px',
          background: 'rgba(16,185,129,0.08)', fontSize: fs.label, color: 'var(--status-ok)',
        }}>
          Equipment selected: {selectedEquipment.length} items, {equipTotalMass.toFixed(2)} kg, {equipTotalPower.toFixed(1)} W, {equipTotalCost.toFixed(0)} kEUR
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <h3 style={{ fontSize: fs.value, margin: 0 }}>Budget Breakdown</h3>
        <button className="btn btn-sm" onClick={() => setEditMode(!editMode)}
          style={{ fontSize: fs.label, background: editMode ? 'var(--status-caution)' : undefined }}>
          {editMode ? 'Done Editing' : 'Edit Allocations'}
        </button>
      </div>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.5rem' }}>
        {editMode ? 'Set mass allocations per subsystem. Margins computed against allocations.'
          : 'Parametric estimates from design agents. Click "Edit Allocations" to set subsystem budgets.'}
      </p>

      {/* Summary bar */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem', fontSize: fs.label }}>
        <div>
          <span style={{ color: 'var(--text-2)' }}>Dry Mass: </span>
          <span style={{ fontWeight: 700, fontFamily: 'monospace' }}>{dryMass.toFixed(1)} kg</span>
          <span style={{ color: massMargin >= 20 ? 'var(--status-ok)' : massMargin >= 0 ? 'var(--status-caution)' : 'var(--status-alarm)', marginLeft: '0.3rem' }}>
            ({massMargin >= 0 ? '+' : ''}{massMargin.toFixed(0)}% margin)
          </span>
        </div>
        <div>
          <span style={{ color: 'var(--text-2)' }}>Power: </span>
          <span style={{ fontWeight: 700, fontFamily: 'monospace' }}>{totalParametricPower.toFixed(1)} W</span>
          <span style={{ color: powerMargin >= 20 ? 'var(--status-ok)' : powerMargin >= 0 ? 'var(--status-caution)' : 'var(--status-alarm)', marginLeft: '0.3rem' }}>
            ({powerMargin >= 0 ? '+' : ''}{powerMargin.toFixed(0)}% margin)
          </span>
        </div>
        <div>
          <span style={{ color: 'var(--text-2)' }}>Cost: </span>
          <span style={{ fontWeight: 700, fontFamily: 'monospace' }}>{totalCost.toFixed(2)} MEUR</span>
        </div>
        <div>
          <span style={{ color: 'var(--text-2)' }}>Volume: </span>
          <span style={{ fontWeight: 700, fontFamily: 'monospace' }}>{formFactor}</span>
          <span style={{ color: volumeUtil <= 85 ? 'var(--status-ok)' : volumeUtil <= 100 ? 'var(--status-caution)' : 'var(--status-alarm)', marginLeft: '0.3rem' }}>
            ({volumeUtil.toFixed(0)}% used)
          </span>
        </div>
      </div>

      {/* Subsystem table with allocation column */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
            <th style={th}>Subsystem</th>
            <th style={thR}>Mass (kg)</th>
            <th style={thR}>% of dry</th>
            {editMode && <th style={thR}>Allocation (kg)</th>}
            <th style={thR}>Margin</th>
            <th style={thR}>Power (W)</th>
            <th style={thR}>% of total</th>
          </tr>
        </thead>
        <tbody>
          {rows.filter(r => r.parametric_mass_kg > 0 || r.parametric_power_w > 0).map(r => {
            const massPct = dryMass > 0 ? (r.parametric_mass_kg / dryMass) * 100 : 0
            const powerPct = totalParametricPower > 0 ? (r.parametric_power_w / totalParametricPower) * 100 : 0
            // Subsystem margin = system margin applied proportionally
            const subMarginPct = massMargin > -100 ? 20 : 0 // Default 20% per subsystem
            return (
              <tr key={r.subsystem} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                <td style={td}>{r.subsystem}</td>
                <td style={tdR}>{r.parametric_mass_kg.toFixed(2)}</td>
                <td style={tdR}>{massPct.toFixed(1)}%</td>
                {editMode && (
                  <td style={tdR}>
                    <input className="input" type="number" step={0.1}
                      value={allocations[r.subsystem] ?? r.parametric_mass_kg * 1.2}
                      onChange={e => {
                        setAllocations(prev => ({ ...prev, [r.subsystem]: Number(e.target.value) }))
                        markStale('budget_allocation')
                      }}
                      style={{ width: '60px', fontSize: fs.label, textAlign: 'right' }} />
                  </td>
                )}
                <td style={{ ...tdR, fontSize: fs.label, color: 'var(--text-3)' }}>+{subMarginPct}%</td>
                <td style={tdR}>{r.parametric_power_w.toFixed(1)}</td>
                <td style={tdR}>{powerPct.toFixed(1)}%</td>
              </tr>
            )
          })}
          <tr style={{ borderTop: '2px solid var(--line)', fontWeight: 700 }}>
            <td style={td}>Total</td>
            <td style={tdR}>{totalParametricMass.toFixed(2)}</td>
            <td style={tdR}>100%</td>
            <td style={{ ...tdR, color: massMargin >= 20 ? 'var(--status-ok)' : massMargin >= 0 ? 'var(--status-caution)' : 'var(--status-alarm)' }}>
              {massMargin >= 0 ? '+' : ''}{massMargin.toFixed(0)}% sys
            </td>
            <td style={tdR}>{totalParametricPower.toFixed(1)}</td>
            <td style={tdR}>100%</td>
          </tr>
        </tbody>
      </table>

      {/* Volume fit indicator */}
      <div style={{ marginTop: '0.75rem' }}>
        <div style={{ fontSize: fs.label, fontWeight: 600, marginBottom: '0.3rem' }}>
          Volume Fit: {formFactor} ({availableVolume} cm³)
        </div>
        <div style={{ height: 16, background: 'var(--surface-2)', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
          <div style={{
            height: '100%', width: `${Math.min(volumeUtil, 120)}%`,
            background: volumeUtil <= 85 ? 'var(--status-ok)' : volumeUtil <= 100 ? 'var(--status-caution)' : 'var(--status-alarm)',
            borderRadius: '4px', transition: 'width 0.3s',
          }} />
          <span style={{
            position: 'absolute', right: 4, top: 0, bottom: 0, display: 'flex', alignItems: 'center',
            fontSize: fs.label, color: 'white', fontWeight: 600,
          }}>{volumeUtil.toFixed(0)}%</span>
        </div>
        {volumeUtil > 100 && (
          <div style={{ fontSize: fs.label, color: 'var(--status-alarm)', marginTop: '0.2rem' }}>
            Equipment exceeds {formFactor} internal volume — consider larger form factor or remove components
          </div>
        )}
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.3rem', fontSize: fs.label, color: 'var(--text-3)' }}>
          {Object.entries(CDS_VOLUMES).slice(0, 6).map(([ff, vol]) => (
            <span key={ff} style={{
              color: ff === formFactor ? 'var(--interactive)' : 'var(--text-3)',
              fontWeight: ff === formFactor ? 700 : 400,
            }}>{ff}: {vol} cm³</span>
          ))}
        </div>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: fs.label, textTransform: 'uppercase', color: 'var(--text-2)' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }
