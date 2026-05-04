/**
 * TimingBudget — Orbit timeline showing mode durations and transitions.
 *
 * Shows one orbit as a circular/linear timeline with mode segments,
 * transition times, and total time accounting.
 */
import { useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'

interface ModeSegment {
  name: string; duration_min: number; power_w: number; color: string; description: string
}

export function TimingBudget() {
  const reqs = useDesignStore(s => s.requirements)
  const orbitPeriod = useMemo(() => {
    const alt = reqs.orbit.altitude_km || 500
    const a = (6371 + alt) * 1000
    return 2 * Math.PI * Math.sqrt(a ** 3 / 3.986004418e14) / 60
  }, [reqs.orbit.altitude_km])

  const eclipseFrac = 0.35
  const sunlightMin = orbitPeriod * (1 - eclipseFrac)
  const eclipseMin = orbitPeriod * eclipseFrac

  const dutyCyclePct = reqs.payloads?.[0]?.duty_cycle_percent || 25
  const imagingMin = sunlightMin * dutyCyclePct / 100

  const segments = useMemo<ModeSegment[]>(() => {
    const contactMin = 8 // Typical ground pass
    const slewMin = 2   // Attitude manoeuvre
    const idleMin = Math.max(0, sunlightMin - imagingMin - contactMin - slewMin * 2)

    return [
      { name: 'Idle / Housekeeping', duration_min: idleMin, power_w: 2, color: '#6b7280', description: 'OBC, ADCS standby, beacon' },
      { name: 'Slew to Target', duration_min: slewMin, power_w: 5, color: '#06b6d4', description: 'Attitude manoeuvre pre-imaging' },
      { name: 'Imaging / Science', duration_min: imagingMin, power_w: 6, color: '#8b5cf6', description: 'Payload active, data recording' },
      { name: 'Slew to GS', duration_min: slewMin, power_w: 5, color: '#06b6d4', description: 'Attitude manoeuvre pre-downlink' },
      { name: 'Downlink', duration_min: contactMin, power_w: 8, color: '#10b981', description: 'TX active, data download' },
      { name: 'Eclipse', duration_min: eclipseMin, power_w: 3, color: '#1f2937', description: 'Battery-powered, heaters' },
    ]
  }, [sunlightMin, eclipseMin, imagingMin])

  const totalMin = segments.reduce((s, seg) => s + seg.duration_min, 0)

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.9rem', marginBottom: '0.3rem' }}>Orbit Timing Budget</h3>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        One orbit ({orbitPeriod.toFixed(1)} min) broken into operational modes with transitions.
      </p>

      {/* Timeline bar */}
      <div style={{ display: 'flex', height: 28, borderRadius: '4px', overflow: 'hidden', marginBottom: '0.5rem' }}>
        {segments.map((seg, i) => {
          const pct = (seg.duration_min / totalMin) * 100
          return (
            <div key={i} title={`${seg.name}: ${seg.duration_min.toFixed(1)} min (${pct.toFixed(0)}%)`}
              style={{
                width: `${pct}%`, background: seg.color, display: 'flex', alignItems: 'center',
                justifyContent: 'center', minWidth: pct > 5 ? 0 : 2, borderRight: '1px solid #0a0e1a',
              }}>
              {pct > 10 && <span style={{ fontSize: '0.55rem', color: 'white', fontWeight: 600, whiteSpace: 'nowrap' }}>{seg.name.split(' ')[0]}</span>}
            </div>
          )
        })}
      </div>

      {/* Mode table */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
            <th style={th}>Mode</th>
            <th style={thR}>Duration</th>
            <th style={thR}>% Orbit</th>
            <th style={thR}>Power</th>
            <th style={thR}>Energy</th>
            <th style={th}>Description</th>
          </tr>
        </thead>
        <tbody>
          {segments.map((seg, i) => (
            <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={td}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: seg.color, border: seg.color === '#1f2937' ? '1px solid #374151' : 'none' }} />
                  {seg.name}
                </span>
              </td>
              <td style={tdR}>{seg.duration_min.toFixed(1)} min</td>
              <td style={tdR}>{((seg.duration_min / totalMin) * 100).toFixed(0)}%</td>
              <td style={tdR}>{seg.power_w} W</td>
              <td style={tdR}>{(seg.power_w * seg.duration_min / 60).toFixed(2)} Wh</td>
              <td style={{ ...td, fontSize: '0.68rem', color: '#6b7280' }}>{seg.description}</td>
            </tr>
          ))}
          <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
            <td style={td}>Total</td>
            <td style={tdR}>{totalMin.toFixed(1)} min</td>
            <td style={tdR}>100%</td>
            <td style={tdR}></td>
            <td style={tdR}>{segments.reduce((s, seg) => s + seg.power_w * seg.duration_min / 60, 0).toFixed(2)} Wh</td>
            <td style={td}></td>
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
