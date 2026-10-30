/**
 * MissionBudgetSummary — compact mission-level budget overview.
 *
 * SYSTEM-V Break 4: Shows mission-level rollup across all segments,
 * comparing totals against the mission envelope from requirements.
 * Designed to embed as a header above SystemBudgetEditor.
 */
import { useMemo } from 'react'
import { useModelStore } from '../stores/modelStore'
import { useDesignStore } from '../stores/designStore'

export function MissionBudgetSummary() {
  const elements = useModelStore(s => s.elements)
  const computeHierarchicalBudget = useModelStore(s => s.computeHierarchicalBudget)
  const requirements = useDesignStore(s => s.requirements)
  const result = useDesignStore(s => s.result)
  const params = result?.parameters || {}
  const get = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  // Find segment elements
  const segments = useMemo(() => {
    const segs: { id: string; name: string; segment: string; mass: number; power: number; cost: number }[] = []
    for (const el of elements.values()) {
      if (el.element_type === 'segment' || el.element_type === 'system') {
        // Only include top-level systems (whose parent is a segment or null/mission)
        const parent = el.parent_id ? elements.get(el.parent_id) : null
        if (el.element_type === 'system' && parent && parent.element_type !== 'segment' && parent.element_type !== 'mission') continue

        const mass = computeHierarchicalBudget(el.id, 'mass')
        const power = computeHierarchicalBudget(el.id, 'power')
        const cost = computeHierarchicalBudget(el.id, 'cost')
        segs.push({ id: el.id, name: el.name, segment: el.segment || el.name, mass, power, cost })
      }
    }
    return segs
  }, [elements, computeHierarchicalBudget])

  if (segments.length === 0) return null

  const totalMass = segments.reduce((s, r) => s + r.mass, 0)
  const totalPower = segments.reduce((s, r) => s + r.power, 0)
  const totalCost = segments.reduce((s, r) => s + r.cost, 0)

  // Mission envelope from requirements
  const massEnv = requirements.target_mass_kg || 0
  const powerEnv = get('power.sa_power_eol_w') || 30
  const costEnv = (requirements.target_cost_meur || 0) * 1000 // kEUR

  const marginStatus = (used: number, env: number): { color: string; label: string } => {
    if (env <= 0) return { color: '#6b7280', label: 'No envelope' }
    const pct = ((env - used) / env) * 100
    if (pct < 0) return { color: '#ef4444', label: `EXCEEDED ${(-pct).toFixed(0)}%` }
    if (pct < 10) return { color: '#ef4444', label: `${pct.toFixed(0)}% margin` }
    if (pct < 20) return { color: '#f59e0b', label: `${pct.toFixed(0)}% margin` }
    return { color: '#10b981', label: `${pct.toFixed(0)}% margin` }
  }

  const budgets = [
    { label: 'Mass', used: totalMass, env: massEnv, unit: 'kg' },
    { label: 'Power', used: totalPower, env: powerEnv, unit: 'W' },
    { label: 'Cost', used: totalCost, env: costEnv, unit: 'kEUR' },
  ]

  return (
    <div style={{
      padding: '0.6rem 1rem', marginBottom: '0.5rem',
      background: 'var(--bg-secondary, #1f2937)',
      borderRadius: '6px', border: '1px solid #374151',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
        <span style={{ fontSize: '0.82rem', fontWeight: 700 }}>Mission Budget Overview</span>
        <span style={{ fontSize: '0.65rem', color: '#6b7280' }}>
          Hierarchical rollup across {segments.length} element{segments.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Compact budget bars */}
      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
        {budgets.map(b => {
          const status = marginStatus(b.used, b.env)
          const fillPct = b.env > 0 ? Math.min((b.used / b.env) * 100, 100) : 0
          return (
            <div key={b.label} style={{ flex: '1 1 120px', minWidth: '120px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', marginBottom: '0.15rem' }}>
                <span style={{ fontWeight: 600 }}>{b.label}</span>
                <span style={{ color: status.color, fontWeight: 600 }}>{status.label}</span>
              </div>
              {/* Bar */}
              <div style={{
                height: '6px', borderRadius: '3px', background: '#1f2937',
                border: '1px solid #374151', overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%', borderRadius: '3px',
                  width: `${fillPct}%`,
                  background: status.color,
                  transition: 'width 0.3s',
                }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6rem', color: '#6b7280', marginTop: '0.1rem' }}>
                <span>{b.used.toFixed(1)} {b.unit}</span>
                <span>{b.env > 0 ? `${b.env.toFixed(1)} ${b.unit}` : 'unset'}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Segment breakdown (compact) */}
      {segments.length > 1 && (
        <div style={{ marginTop: '0.4rem', display: 'flex', gap: '0.5rem', fontSize: '0.62rem', color: '#9ca3af', flexWrap: 'wrap' }}>
          {segments.map(seg => (
            <span key={seg.id}>
              {seg.name}: {seg.mass.toFixed(1)}kg / {seg.power.toFixed(1)}W / {seg.cost.toFixed(0)}kEUR
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
