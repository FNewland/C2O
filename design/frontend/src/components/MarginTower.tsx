/**
 * MarginTower — Persistent budget margin indicators in the app header.
 *
 * Per SPINE_SPEC §10.3. Shows mass/power/link/cost/ΔV margin bars
 * with phase-rule colours from ECSSMarginEnforcer.
 * Updates on every convergence.
 */
import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'

interface MarginItem {
  id: string; label: string; paramId: string; limitParamId?: string
  unit: string; goodAbove: number; warnAbove: number
}

const MARGINS: MarginItem[] = [
  { id: 'mass', label: 'Mass', paramId: 'systems.mass_margin_percent', unit: '%', goodAbove: 20, warnAbove: 0 },
  { id: 'power', label: 'Power', paramId: 'power.margin_percent', unit: '%', goodAbove: 15, warnAbove: 0 },
  { id: 'link', label: 'Link', paramId: 'link.margin_db', unit: 'dB', goodAbove: 3, warnAbove: 0 },
  { id: 'cost', label: 'Cost', paramId: 'cost.margin_percent', unit: '%', goodAbove: 10, warnAbove: 0 },
  { id: 'deltav', label: 'ΔV', paramId: 'propulsion.delta_v_margin_percent', unit: '%', goodAbove: 10, warnAbove: 0 },
]

export function MarginTower() {
  const result = useDesignStore(s => s.result)
  const params = useActiveParameters()

  if (!result) return null

  const get = (id: string): number | null => {
    const p = params[id]
    return p && typeof p.value === 'number' ? p.value : null
  }

  return (
    <div style={{ display: 'flex', gap: '0.4rem', padding: '0.25rem 0.5rem', background: 'var(--bg-secondary, #1f2937)', borderBottom: '1px solid var(--border, #374151)', fontSize: '0.7rem' }}>
      {MARGINS.map(m => {
        const val = get(m.paramId)
        const color = val === null ? '#6b7280' : val >= m.goodAbove ? '#10b981' : val >= m.warnAbove ? '#f59e0b' : '#ef4444'
        const barPct = val !== null ? Math.min(100, Math.max(0, (val / m.goodAbove) * 50 + 50)) : 0
        return (
          <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', minWidth: '80px' }}>
            <span style={{ color: '#9ca3af', width: '30px', textAlign: 'right', fontSize: '0.62rem' }}>{m.label}</span>
            <div style={{ flex: 1, height: 6, background: '#111827', borderRadius: 3, minWidth: 30, position: 'relative' }}>
              <div style={{ height: '100%', width: `${barPct}%`, background: color, borderRadius: 3, transition: 'width 0.3s' }} />
            </div>
            <span style={{ color, fontFamily: 'monospace', fontWeight: 600, minWidth: '35px', textAlign: 'right', fontSize: '0.65rem' }}>
              {val !== null ? `${val.toFixed(0)}${m.unit}` : '—'}
            </span>
          </div>
        )
      })}
    </div>
  )
}
