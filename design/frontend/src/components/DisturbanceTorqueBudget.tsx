/**
 * DisturbanceTorqueBudget — RSS torque budget for AOCS validation.
 *
 * Surfaces disturbance torques computed by the AOCS agent (gravity gradient,
 * solar pressure, aerodynamic, magnetic) with margin against reaction wheel capability.
 * Read-only — values come from the last design convergence.
 */
import { useActiveParameters } from '../hooks/useActiveParameters'

interface TorqueRow {
  name: string; paramId: string; color: string
}

const TORQUE_SOURCES: TorqueRow[] = [
  { name: 'Gravity Gradient', paramId: 'aocs.torque_gravity_gradient_nm', color: '#3b82f6' },
  { name: 'Solar Radiation Pressure', paramId: 'aocs.torque_solar_pressure_nm', color: '#f59e0b' },
  { name: 'Aerodynamic Drag', paramId: 'aocs.torque_aerodynamic_nm', color: '#06b6d4' },
  { name: 'Residual Magnetic', paramId: 'aocs.torque_magnetic_nm', color: '#8b5cf6' },
]

export function DisturbanceTorqueBudget() {
  const params = useActiveParameters()
  const get = (id: string) => {
    const p = params[id]
    return p && typeof p.value === 'number' ? p.value : 0
  }

  const torques = TORQUE_SOURCES.map(s => ({
    ...s,
    value: get(s.paramId),
  }))

  const rssTotal = Math.sqrt(torques.reduce((s, t) => s + t.value ** 2, 0))
  const rwMomentum = get('aocs.wheel_momentum_nms')
  // Wheel torque capacity is momentum / orbit_period (rough)
  const orbitPeriod = get('orbit.period_s') || 5400
  const rwTorqueCapacity = rwMomentum > 0 ? rwMomentum / (orbitPeriod / 4) : 0
  const margin = rwTorqueCapacity > 0 ? ((rwTorqueCapacity - rssTotal) / rwTorqueCapacity) * 100 : 0
  const hasData = torques.some(t => t.value > 0)

  if (!hasData) {
    return (
      <div className="card" style={{ borderLeft: '3px solid #6b7280' }}>
        <h3 style={{ fontSize: '0.85rem', color: '#6b7280' }}>Disturbance Torque Budget</h3>
        <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>Run a design to see disturbance torques.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Disturbance Torque Budget (RSS)</h3>
      <p style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '0.4rem' }}>
        Environmental torques vs reaction wheel capacity. All values in N·m.
      </p>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
            <th style={th}>Source</th>
            <th style={thR}>Torque (N·m)</th>
            <th style={thR}>Contribution</th>
            <th style={{ ...th, width: '60px' }}>Bar</th>
          </tr>
        </thead>
        <tbody>
          {torques.map(t => {
            const pct = rssTotal > 0 ? (t.value ** 2 / rssTotal ** 2) * 100 : 0
            return (
              <tr key={t.paramId} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={td}>
                  <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: t.color, marginRight: '0.4rem' }} />
                  {t.name}
                </td>
                <td style={{ ...tdR, fontFamily: 'monospace' }}>{t.value.toExponential(2)}</td>
                <td style={{ ...tdR, color: '#6b7280' }}>{pct.toFixed(1)}%</td>
                <td style={td}>
                  <div style={{ height: 8, background: '#1f2937', borderRadius: 2 }}>
                    <div style={{ height: '100%', width: `${Math.min(pct, 100)}%`, background: t.color, borderRadius: 2 }} />
                  </div>
                </td>
              </tr>
            )
          })}
          <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
            <td style={td}>RSS Total</td>
            <td style={{ ...tdR, fontFamily: 'monospace', fontSize: '0.82rem' }}>{rssTotal.toExponential(2)}</td>
            <td style={tdR}>100%</td>
            <td style={td} />
          </tr>
        </tbody>
      </table>

      {/* Margin bar */}
      <div style={{ marginTop: '0.5rem', padding: '0.4rem', background: margin >= 10 ? 'rgba(16,185,129,0.08)' : margin >= 0 ? 'rgba(245,158,11,0.08)' : 'rgba(239,68,68,0.08)', borderRadius: '4px', border: `1px solid ${margin >= 10 ? '#10b98140' : margin >= 0 ? '#f59e0b40' : '#ef444440'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '0.2rem' }}>
          <span>RW Capacity: {rwTorqueCapacity.toExponential(2)} N·m</span>
          <span>Disturbance: {rssTotal.toExponential(2)} N·m</span>
          <span style={{ fontWeight: 700, color: margin >= 10 ? '#10b981' : margin >= 0 ? '#f59e0b' : '#ef4444' }}>
            Margin: {margin.toFixed(0)}%
          </span>
        </div>
        <div style={{ height: 8, background: '#1f2937', borderRadius: 4 }}>
          <div style={{ height: '100%', width: `${Math.min(100, (rssTotal / rwTorqueCapacity) * 100 || 0)}%`, background: margin >= 10 ? '#10b981' : margin >= 0 ? '#f59e0b' : '#ef4444', borderRadius: 4 }} />
        </div>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right' }
