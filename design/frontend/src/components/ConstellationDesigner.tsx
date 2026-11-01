/**
 * ConstellationDesigner — define spacecraft variants, quantities, and fleet economics.
 *
 * Supports multiple spacecraft types (e.g., comms primary + spare + gateway).
 * Applies learning curve for volume production. Shows fleet cost rollup.
 */
import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'
import { SVGBarChart } from '../charts/SVGBarChart'
import { fs } from '../theme/tokens'

interface Variant {
  id: string
  name: string
  quantity: number
  planes: number
  sats_per_plane: number
  altitude_km: number
  inclination_deg: number
  mass_delta_kg: number
  cost_modifier: number
  description: string
}

export function ConstellationDesigner() {
  const requirements = useDesignStore(s => s.requirements)
  const result = useDesignStore(s => s.result)
  const params = result?.parameters || {}
  const get = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  const baseCost = get('cost.total_keur') || 700

  const storedVariants = useDesignStore(s => s.constellationVariants)
  const persistVariants = useDesignStore(s => s.setConstellationVariants)

  const defaultVariant: Variant = { id: 'v1', name: 'Primary', quantity: requirements.num_spacecraft || 1, planes: 1, sats_per_plane: requirements.num_spacecraft || 1, altitude_km: requirements.orbit.altitude_km, inclination_deg: requirements.orbit.inclination_deg, mass_delta_kg: 0, cost_modifier: 1.0, description: 'Main operational spacecraft' }

  const [variants, setVariantsLocal] = useState<Variant[]>(
    storedVariants.length > 0
      ? storedVariants.map(sv => ({ ...defaultVariant, ...sv }))
      : [defaultVariant]
  )
  const setVariants = (updater: Variant[] | ((prev: Variant[]) => Variant[])) => {
    setVariantsLocal(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      persistVariants(next)
      return next
    })
  }
  const [learningCurve, setLearningCurve] = useState(0.90) // 90% learning rate

  const totalSats = variants.reduce((s, v) => s + v.quantity, 0)

  // Learning curve cost: unit N costs = first_unit × N^(log(learning_rate)/log(2))
  const computeFleetCost = () => {
    let total = 0
    let unitNum = 0
    for (const v of variants) {
      for (let i = 0; i < v.quantity; i++) {
        unitNum++
        const unitCost = (baseCost * v.cost_modifier) * Math.pow(unitNum, Math.log(learningCurve) / Math.log(2))
        total += unitCost
      }
    }
    return total
  }

  const fleetCost = computeFleetCost()
  const avgCostPerUnit = totalSats > 0 ? fleetCost / totalSats : baseCost

  const addVariant = () => {
    setVariants(prev => [...prev, {
      id: `v-${Date.now()}`, name: 'New Variant', quantity: 1, planes: 1, sats_per_plane: 1,
      altitude_km: requirements.orbit.altitude_km, inclination_deg: requirements.orbit.inclination_deg,
      mass_delta_kg: 0, cost_modifier: 1.0, description: '',
    }])
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: fs.value, marginBottom: '0.25rem' }}>Constellation / Fleet Design</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.75rem' }}>
        Define spacecraft variants, orbital planes, and quantities. Learning curve applied for volume production.
      </p>

      {/* Fleet summary */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{ padding: '0.5rem 0.75rem', background: 'var(--surface-2)', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: fs.value, fontWeight: 700, color: 'var(--interactive)', fontFamily: 'monospace' }}>{totalSats}</div>
          <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>Total Spacecraft</div>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: 'var(--surface-2)', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: fs.value, fontWeight: 700, color: 'var(--status-ok)', fontFamily: 'monospace' }}>{(fleetCost / 1000).toFixed(1)}</div>
          <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>Fleet Cost (MEUR)</div>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: 'var(--surface-2)', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: fs.value, fontWeight: 700, color: 'var(--status-caution)', fontFamily: 'monospace' }}>{(avgCostPerUnit / 1000).toFixed(2)}</div>
          <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>Avg Per-Unit (MEUR)</div>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: 'var(--surface-2)', borderRadius: '6px' }}>
          <div style={{ fontSize: fs.label, color: 'var(--text-2)' }}>Learning Curve</div>
          <input type="range" min={0.8} max={1.0} step={0.01} value={learningCurve}
            onChange={e => setLearningCurve(Number(e.target.value))}
            style={{ width: '100px' }} />
          <div style={{ fontSize: fs.label, color: 'var(--text-3)', textAlign: 'center' }}>{(learningCurve * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* Cost by unit chart */}
      {totalSats > 1 && (
        <div className="card" style={{ marginBottom: '0.75rem' }}>
          <SVGBarChart
            data={Array.from({ length: Math.min(totalSats, 20) }, (_, i) => ({
              label: `#${i + 1}`,
              value: (baseCost * Math.pow(i + 1, Math.log(learningCurve) / Math.log(2))) / 1000,
              color: 'var(--interactive)',
            }))}
            width={500} height={150} unit=" M" title="Per-Unit Cost with Learning Curve"
          />
        </div>
      )}

      {/* Variant table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
          <h3 style={{ fontSize: fs.body, margin: 0 }}>Spacecraft Variants</h3>
          <button onClick={addVariant} className="btn btn-sm" style={{ fontSize: fs.label, background: 'var(--line)' }}>+ Add Variant</button>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
              <th style={th}>Variant</th>
              <th style={thR}>Qty</th>
              <th style={thR}>Planes</th>
              <th style={thR}>Sats/Plane</th>
              <th style={thR}>Alt (km)</th>
              <th style={thR}>Incl (°)</th>
              <th style={thR}>Mass Δ (kg)</th>
              <th style={thR}>Cost ×</th>
              <th style={thC}></th>
            </tr>
          </thead>
          <tbody>
            {variants.map(v => (
              <tr key={v.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                <td style={td}><input value={v.name} onChange={e => setVariants(prev => prev.map(vv => vv.id === v.id ? { ...vv, name: e.target.value } : vv))} style={inputS} /></td>
                <td style={tdR}><input type="number" min={1} value={v.quantity} onChange={e => setVariants(prev => prev.map(vv => vv.id === v.id ? { ...vv, quantity: Number(e.target.value) } : vv))} style={{ ...inputS, width: '40px', textAlign: 'right' }} /></td>
                <td style={tdR}><input type="number" min={1} value={v.planes} onChange={e => setVariants(prev => prev.map(vv => vv.id === v.id ? { ...vv, planes: Number(e.target.value) } : vv))} style={{ ...inputS, width: '35px', textAlign: 'right' }} /></td>
                <td style={tdR}><input type="number" min={1} value={v.sats_per_plane} onChange={e => setVariants(prev => prev.map(vv => vv.id === v.id ? { ...vv, sats_per_plane: Number(e.target.value) } : vv))} style={{ ...inputS, width: '35px', textAlign: 'right' }} /></td>
                <td style={tdR}><input type="number" value={v.altitude_km} onChange={e => setVariants(prev => prev.map(vv => vv.id === v.id ? { ...vv, altitude_km: Number(e.target.value) } : vv))} style={{ ...inputS, width: '55px', textAlign: 'right' }} /></td>
                <td style={tdR}><input type="number" value={v.inclination_deg} step={0.1} onChange={e => setVariants(prev => prev.map(vv => vv.id === v.id ? { ...vv, inclination_deg: Number(e.target.value) } : vv))} style={{ ...inputS, width: '45px', textAlign: 'right' }} /></td>
                <td style={tdR}><input type="number" value={v.mass_delta_kg} step={0.1} onChange={e => setVariants(prev => prev.map(vv => vv.id === v.id ? { ...vv, mass_delta_kg: Number(e.target.value) } : vv))} style={{ ...inputS, width: '45px', textAlign: 'right' }} /></td>
                <td style={tdR}><input type="number" value={v.cost_modifier} step={0.1} min={0.1} onChange={e => setVariants(prev => prev.map(vv => vv.id === v.id ? { ...vv, cost_modifier: Number(e.target.value) } : vv))} style={{ ...inputS, width: '40px', textAlign: 'right' }} /></td>
                <td style={tdC}>{variants.length > 1 && <button onClick={() => setVariants(prev => prev.filter(vv => vv.id !== v.id))} style={{ background: 'none', border: 'none', color: 'var(--status-alarm)', cursor: 'pointer' }}>×</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
const inputS: React.CSSProperties = { background: 'transparent', border: 'none', color: 'var(--text)', fontSize: fs.label, width: '100%' }
