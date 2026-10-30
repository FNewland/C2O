/**
 * PropulsionAnalysis — delta-V budget and propulsion system analysis.
 *
 * Shows manoeuvre budget (not by subsystem but by mission activity),
 * propulsion type selection, and sizing.
 */
import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'
import { SVGBarChart } from '../charts/SVGBarChart'

interface Manoeuvre {
  id: string
  name: string
  delta_v_ms: number
  frequency: string  // e.g., "once", "yearly", "monthly"
  occurrences: number
  total_dv_ms: number
}

const DEFAULT_MANOEUVRES: Manoeuvre[] = [
  { id: 'm1', name: 'Orbit insertion correction', delta_v_ms: 5, frequency: 'once', occurrences: 1, total_dv_ms: 5 },
  { id: 'm2', name: 'Drag makeup (LEO)', delta_v_ms: 2, frequency: 'yearly', occurrences: 3, total_dv_ms: 6 },
  { id: 'm3', name: 'Collision avoidance', delta_v_ms: 0.5, frequency: 'yearly', occurrences: 6, total_dv_ms: 3 },
  { id: 'm4', name: 'Orbit maintenance', delta_v_ms: 1, frequency: 'yearly', occurrences: 3, total_dv_ms: 3 },
  { id: 'm5', name: 'Deorbit', delta_v_ms: 50, frequency: 'once', occurrences: 1, total_dv_ms: 50 },
]

export function PropulsionAnalysis() {
  const result = useDesignStore(s => s.result)
  const requirements = useDesignStore(s => s.requirements)
  const [manoeuvres, setManoeuvres] = useState<Manoeuvre[]>(DEFAULT_MANOEUVRES)

  const params = result?.parameters || {}
  const get = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  const totalDv = manoeuvres.reduce((s, m) => s + m.total_dv_ms, 0)
  const propMass = get('propulsion.total_mass_kg')
  const propType = get('propulsion.type') || 'cold gas'

  const addManoeuvre = () => {
    setManoeuvres(prev => [...prev, {
      id: `m-${Date.now()}`, name: 'New manoeuvre', delta_v_ms: 1, frequency: 'once', occurrences: 1, total_dv_ms: 1,
    }])
  }

  const updateManoeuvre = (id: string, field: keyof Manoeuvre, value: any) => {
    setManoeuvres(prev => prev.map(m => {
      if (m.id !== id) return m
      const updated = { ...m, [field]: value }
      updated.total_dv_ms = updated.delta_v_ms * updated.occurrences
      return updated
    }))
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Propulsion & Delta-V Budget</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Define manoeuvres over the mission lifetime. Total delta-V drives propulsion system sizing.
      </p>

      {/* Summary */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{ padding: '0.5rem 0.75rem', background: '#1f2937', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f59e0b', fontFamily: 'monospace' }}>{totalDv.toFixed(1)}</div>
          <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>Total ΔV (m/s)</div>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: '#1f2937', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#06b6d4', fontFamily: 'monospace' }}>{propMass.toFixed(2)}</div>
          <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>Propulsion mass (kg)</div>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: '#1f2937', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#d1d5db' }}>{manoeuvres.length}</div>
          <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>Manoeuvres defined</div>
        </div>
      </div>

      {/* Manoeuvre chart */}
      <div className="card" style={{ marginBottom: '0.75rem' }}>
        <SVGBarChart
          data={manoeuvres.map(m => ({ label: m.name.slice(0, 15), value: m.total_dv_ms, color: '#f97316' }))}
          orientation="horizontal" unit=" m/s" width={450} height={Math.max(120, manoeuvres.length * 28 + 40)}
          title="Delta-V by Manoeuvre"
        />
      </div>

      {/* Editable manoeuvre table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
          <h3 style={{ fontSize: '0.85rem', margin: 0 }}>Manoeuvre Budget</h3>
          <button onClick={addManoeuvre} className="btn btn-sm" style={{ fontSize: '0.68rem', background: '#374151' }}>+ Add</button>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
              <th style={th}>Manoeuvre</th>
              <th style={thR}>ΔV (m/s)</th>
              <th style={th}>Frequency</th>
              <th style={thR}>Count</th>
              <th style={thR}>Total ΔV</th>
              <th style={thC}></th>
            </tr>
          </thead>
          <tbody>
            {manoeuvres.map(m => (
              <tr key={m.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={td}>
                  <input value={m.name} onChange={e => updateManoeuvre(m.id, 'name', e.target.value)}
                    style={inputS} />
                </td>
                <td style={tdR}>
                  <input type="number" step={0.1} value={m.delta_v_ms} onChange={e => updateManoeuvre(m.id, 'delta_v_ms', Number(e.target.value))}
                    style={{ ...inputS, width: '50px', textAlign: 'right' }} />
                </td>
                <td style={td}>
                  <select value={m.frequency} onChange={e => updateManoeuvre(m.id, 'frequency', e.target.value)}
                    style={{ ...inputS, width: '80px' }}>
                    <option value="once">Once</option>
                    <option value="yearly">Per year</option>
                    <option value="monthly">Per month</option>
                    <option value="weekly">Per week</option>
                  </select>
                </td>
                <td style={tdR}>
                  <input type="number" min={1} value={m.occurrences} onChange={e => updateManoeuvre(m.id, 'occurrences', Number(e.target.value))}
                    style={{ ...inputS, width: '40px', textAlign: 'right' }} />
                </td>
                <td style={{ ...tdR, fontFamily: 'monospace', fontWeight: 600, color: '#f97316' }}>
                  {m.total_dv_ms.toFixed(1)}
                </td>
                <td style={tdC}>
                  <button onClick={() => setManoeuvres(prev => prev.filter(mm => mm.id !== m.id))}
                    style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.7rem' }}>×</button>
                </td>
              </tr>
            ))}
            <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
              <td style={td}>Total</td>
              <td style={tdR}></td>
              <td style={td}></td>
              <td style={tdR}></td>
              <td style={{ ...tdR, fontFamily: 'monospace', color: '#f97316' }}>{totalDv.toFixed(1)} m/s</td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
const inputS: React.CSSProperties = { background: 'transparent', border: 'none', color: '#d1d5db', fontSize: '0.72rem', width: '100%' }
