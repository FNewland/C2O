/**
 * SolarArrayDecayPlot — Shows solar array power degradation over mission lifetime.
 *
 * Plots BOL power declining to EOL via radiation + UV degradation.
 * Uses exponential decay model: P(t) = P_BOL × (1 - degradation_rate)^t
 */
import { useMemo } from 'react'
import { useActiveParameters } from '../hooks/useActiveParameters'
import { useDesignStore } from '../stores/designStore'

export function SolarArrayDecayPlot() {
  const params = useActiveParameters()
  const lifetime = useDesignStore(s => s.requirements.design_lifetime_years) || 3

  const get = (id: string): number => {
    const p = params[id]
    return p && typeof p.value === 'number' ? p.value : 0
  }

  const bolPower = get('power.sa_power_bol_w')
  const eolPower = get('power.sa_power_eol_w')

  const decay = useMemo(() => {
    if (bolPower <= 0) return []
    // Compute annual degradation rate from BOL/EOL
    const rate = lifetime > 0 && eolPower > 0 ? 1 - Math.pow(eolPower / bolPower, 1 / lifetime) : 0.025
    const points: { year: number; power: number }[] = []
    for (let y = 0; y <= lifetime; y += 0.5) {
      points.push({ year: y, power: bolPower * Math.pow(1 - rate, y) })
    }
    return points
  }, [bolPower, eolPower, lifetime])

  if (bolPower <= 0) {
    return (
      <div className="card" style={{ borderLeft: '3px solid #6b7280' }}>
        <h3 style={{ fontSize: '0.85rem', color: '#6b7280' }}>Solar Array Degradation</h3>
        <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>Run a design to see SA power decay.</p>
      </div>
    )
  }

  const maxPower = bolPower * 1.05
  const barWidth = 100 / decay.length

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.2rem' }}>Solar Array Degradation (BOL → EOL)</h3>
      <p style={{ fontSize: '0.68rem', color: '#9ca3af', marginBottom: '0.4rem' }}>
        BOL: {bolPower.toFixed(1)} W → EOL: {eolPower.toFixed(1)} W over {lifetime} years
        ({((1 - eolPower / bolPower) * 100).toFixed(1)}% total degradation)
      </p>

      {/* Simple area chart */}
      <div style={{ position: 'relative', height: 80, background: '#111827', borderRadius: 4, overflow: 'hidden' }}>
        <svg width="100%" height="80" viewBox={`0 0 ${decay.length} 80`} preserveAspectRatio="none">
          <defs>
            <linearGradient id="saDecay" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.05" />
            </linearGradient>
          </defs>
          <path d={`M0,80 ${decay.map((d, i) => `L${i},${80 - (d.power / maxPower) * 80}`).join(' ')} L${decay.length - 1},80 Z`}
            fill="url(#saDecay)" />
          <path d={`M${decay.map((d, i) => `${i},${80 - (d.power / maxPower) * 80}`).join(' L')}`}
            fill="none" stroke="#f59e0b" strokeWidth="1.5" />
          {/* EOL requirement line */}
          <line x1="0" y1={80 - (eolPower / maxPower) * 80} x2={decay.length} y2={80 - (eolPower / maxPower) * 80}
            stroke="#ef4444" strokeWidth="0.5" strokeDasharray="2,2" />
        </svg>
        <div style={{ position: 'absolute', bottom: 2, right: 4, fontSize: '0.58rem', color: '#ef4444' }}>EOL req</div>
        <div style={{ position: 'absolute', top: 2, left: 4, fontSize: '0.58rem', color: '#f59e0b' }}>BOL {bolPower.toFixed(0)}W</div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.58rem', color: '#6b7280', marginTop: '0.1rem' }}>
        <span>Year 0</span>
        <span>Year {lifetime}</span>
      </div>
    </div>
  )
}
