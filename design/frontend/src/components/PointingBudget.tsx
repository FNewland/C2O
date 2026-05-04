/**
 * PointingBudget — RSS error budget tree for pointing accuracy.
 *
 * Shows per-contributor error and RSS combination vs requirement.
 */
import { useState, useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'

interface ErrorContributor {
  id: string; name: string; value_deg: number; editable: boolean; notes: string
}

export function PointingBudget() {
  const params = useActiveParameters()
  const req = useDesignStore(s => s.requirements.payloads?.[0]?.pointing_accuracy_deg ?? 0.1)
  const get = (id: string) => { const p = params[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  const [contributors, setContributors] = useState<ErrorContributor[]>([
    { id: 'sensor', name: 'Attitude sensor accuracy', value_deg: 0.01, editable: true, notes: 'Star tracker: 0.003-0.01°; Sun sensor: 0.5-2°' },
    { id: 'actuator', name: 'Actuator resolution', value_deg: 0.005, editable: true, notes: 'Reaction wheel: 0.005°; Magnetorquer: 1-5°' },
    { id: 'alignment', name: 'Payload-bus alignment', value_deg: 0.02, editable: true, notes: 'Mechanical alignment knowledge after I&T' },
    { id: 'thermal', name: 'Thermal distortion', value_deg: 0.01, editable: true, notes: 'Structure deformation over thermal cycle' },
    { id: 'jitter', name: 'Micro-vibration jitter', value_deg: 0.005, editable: true, notes: 'Reaction wheel imbalance (with isolators)' },
    { id: 'orbit', name: 'Orbit knowledge error', value_deg: 0.01, editable: true, notes: 'GPS: 0.001°; TLE: 0.01-0.1°' },
    { id: 'timing', name: 'Timing synchronisation', value_deg: 0.002, editable: true, notes: 'Clock accuracy × slew rate' },
  ])

  const rss = useMemo(() => {
    const sum = contributors.reduce((s, c) => s + c.value_deg ** 2, 0)
    return Math.sqrt(sum)
  }, [contributors])

  const margin = req - rss
  const marginPct = req > 0 ? (margin / req) * 100 : 0

  const updateValue = (id: string, value: number) => {
    setContributors(prev => prev.map(c => c.id === id ? { ...c, value_deg: value } : c))
  }

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.9rem', marginBottom: '0.3rem' }}>Pointing Error Budget (RSS)</h3>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Root-Sum-Square combination of independent error sources. Requirement: {req}°.
      </p>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
            <th style={th}>Error Source</th>
            <th style={thR}>Value (°)</th>
            <th style={thR}>Squared</th>
            <th style={th}>Notes</th>
          </tr>
        </thead>
        <tbody>
          {contributors.map(c => (
            <tr key={c.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={td}>{c.name}</td>
              <td style={tdR}>
                <input className="input" type="number" step={0.001} value={c.value_deg}
                  onChange={e => updateValue(c.id, Number(e.target.value))}
                  style={{ width: '70px', fontSize: '0.72rem', textAlign: 'right' }} />
              </td>
              <td style={{ ...tdR, color: '#6b7280' }}>{(c.value_deg ** 2).toExponential(2)}</td>
              <td style={{ ...td, fontSize: '0.65rem', color: '#6b7280' }}>{c.notes}</td>
            </tr>
          ))}
          <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
            <td style={td}>RSS Total</td>
            <td style={{ ...tdR, color: margin >= 0 ? '#10b981' : '#ef4444', fontWeight: 700, fontSize: '0.85rem' }}>
              {rss.toFixed(4)}°
            </td>
            <td style={tdR}></td>
            <td style={td}>
              <span style={{
                fontSize: '0.72rem', padding: '0.1rem 0.4rem', borderRadius: '3px',
                background: margin >= 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                color: margin >= 0 ? '#10b981' : '#ef4444', fontWeight: 600,
              }}>
                Margin: {margin >= 0 ? '+' : ''}{margin.toFixed(4)}° ({marginPct.toFixed(0)}%)
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
