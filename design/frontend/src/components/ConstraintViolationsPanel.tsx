/**
 * ConstraintViolationsPanel — Real-time constraint violation display.
 *
 * Calls the 187-connection constraint propagation engine whenever the design
 * state changes, showing violations with root causes, downstream impacts,
 * and inline resolution options.
 */
import { useState, useEffect, useCallback } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useSessionStore } from '../stores/sessionStore'
import { useEquipmentView } from '../hooks/useEquipmentView'

interface Violation {
  id: string; name: string; budget: string; parameter: string
  current: number; limit: number; margin_pct: number
  root_causes: string[]
  downstream_impacts: Array<{ target: string; budget: string; desc: string }>
  resolutions: Array<{ id: string; desc: string; param: string; dir: string; trade_off: string }>
}

const BUDGET_COLORS: Record<string, string> = {
  mass: '#ef4444', power: '#f59e0b', link: '#3b82f6',
  volume: '#8b5cf6', data: '#06b6d4', cost: '#f97316',
}

export function ConstraintViolationsPanel() {
  const selectedEquipment = useEquipmentView()
  const result = useDesignStore(s => s.result)
  const requirements = useDesignStore(s => s.requirements)
  const designStale = useDesignStore(s => s.designStale)

  const [violations, setViolations] = useState<Violation[]>([])
  const [loading, setLoading] = useState(false)
  const [lastCheck, setLastCheck] = useState<string>('')

  const buildDesignParams = useCallback(() => {
    const params: Record<string, number> = {}

    // Roll up from selected equipment
    let totalMass = 0, totalPower = 0, totalCost = 0
    for (const eq of selectedEquipment) {
      totalMass += eq.mass_kg * eq.quantity
      totalPower += eq.power_w * eq.quantity
      totalCost += eq.cost_keur * eq.quantity
    }
    params['mass.dry_mass_kg'] = totalMass
    params['power.total_demand_w'] = totalPower
    params['cost.total_keur'] = totalCost

    // From design result if available
    if (result?.parameters) {
      const p = result.parameters as Record<string, any>
      if (p.link_margin_db !== undefined) params['link.margin_db'] = p.link_margin_db
      if (p.pointing_error_deg !== undefined) params['pointing.error_deg'] = p.pointing_error_deg
      if (p.data_volume_gb !== undefined) params['data.balance_gb'] = p.data_volume_gb
      if (p.volume_utilisation_pct !== undefined) params['volume.utilisation_pct'] = p.volume_utilisation_pct
    }

    return params
  }, [selectedEquipment, result])

  const buildConstraints = useCallback(() => {
    const c: Record<string, number> = {}
    if (requirements.target_mass_kg) c['mass_allocation_kg'] = requirements.target_mass_kg
    if (requirements.target_cost_meur) c['cost_ceiling_keur'] = requirements.target_cost_meur * 1000
    // Default CubeSat power budget (~30W for 6U)
    c['power_available_w'] = requirements.payload?.power_w ? requirements.payload.power_w * 3 : 30
    return c
  }, [requirements])

  const checkConstraints = useCallback(async () => {
    const params = buildDesignParams()
    // Don't call if no meaningful data
    if (Object.values(params).every(v => v === 0)) return

    setLoading(true)
    try {
      const res = await fetch('/api/lifecycle/constraints/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ design_params: params, constraints: buildConstraints() }),
      })
      if (res.ok) {
        const data = await res.json()
        setViolations(data.violations || [])
        setLastCheck(new Date().toLocaleTimeString())
      }
    } catch { /* silent */ }
    setLoading(false)
  }, [buildDesignParams, buildConstraints])

  // Re-check when design state changes
  useEffect(() => {
    checkConstraints()
  }, [selectedEquipment.length, designStale, result])

  if (violations.length === 0 && !loading) {
    return (
      <div className="card" style={{ borderColor: 'var(--success)' }}>
        <h3 style={{ color: 'var(--success)', fontSize: '0.85rem' }}>No Constraint Violations</h3>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          All budgets within limits. {lastCheck && `Last checked: ${lastCheck}`}
        </p>
        <button onClick={checkConstraints} className="btn btn-sm"
          style={{ fontSize: '0.68rem', marginTop: '0.3rem', background: '#374151' }}>
          Re-check Now
        </button>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '0.75rem', color: '#ef4444', fontWeight: 600 }}>
          {violations.length} Violation{violations.length > 1 ? 's' : ''} Detected
        </span>
        <button onClick={checkConstraints} className="btn btn-sm"
          style={{ fontSize: '0.65rem', background: '#374151', padding: '0.15rem 0.5rem' }}>
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {violations.map(v => (
        <ViolationCard key={v.id} violation={v} />
      ))}

      {lastCheck && (
        <p style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '0.5rem', textAlign: 'right' }}>
          Last: {lastCheck}
        </p>
      )}
    </div>
  )
}

function ViolationCard({ violation: v }: { violation: Violation }) {
  const [expanded, setExpanded] = useState(false)
  const [cycles, setCycles] = useState<Record<string, string[][]>>({})
  const [appliedRes, setAppliedRes] = useState<string | null>(null)
  const sendEdit = useSessionStore(s => s.sendEdit)
  const color = BUDGET_COLORS[v.budget] || '#ef4444'

  const checkCycles = async (resParam: string) => {
    if (cycles[resParam]) return // Already checked
    try {
      const res = await fetch('/api/lifecycle/constraints/circular-deps', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ starting_param: v.parameter, resolution_param: resParam }),
      })
      if (res.ok) {
        const data = await res.json()
        setCycles(prev => ({ ...prev, [resParam]: data.cycles || [] }))
      }
    } catch { /* silent */ }
  }

  return (
    <div className="card" style={{
      borderLeft: `4px solid ${color}`, marginBottom: '0.5rem',
      background: `${color}11`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}>
        <div>
          <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>{v.name}</span>
          <span style={{ fontSize: '0.68rem', color: '#6b7280', marginLeft: '0.5rem' }}>
            {v.current.toFixed(1)} / {v.limit.toFixed(1)} ({v.margin_pct > 0 ? '+' : ''}{v.margin_pct.toFixed(0)}%)
          </span>
        </div>
        <span style={{ fontSize: '0.7rem', color }}>{expanded ? '▼' : '▶'}</span>
      </div>

      {expanded && (
        <div style={{ marginTop: '0.5rem' }}>
          {/* Root causes */}
          {v.root_causes.length > 0 && (
            <div style={{ marginBottom: '0.4rem' }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 600, color: '#9ca3af', marginBottom: '0.2rem' }}>ROOT CAUSES</div>
              {v.root_causes.map((cause, i) => (
                <div key={i} style={{ fontSize: '0.72rem', padding: '0.1rem 0', color: '#d1d5db' }}>• {cause}</div>
              ))}
            </div>
          )}

          {/* Downstream impacts */}
          {v.downstream_impacts.length > 0 && (
            <div style={{ marginBottom: '0.4rem' }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 600, color: '#9ca3af', marginBottom: '0.2rem' }}>DOWNSTREAM IMPACTS</div>
              {v.downstream_impacts.map((imp, i) => (
                <div key={i} style={{ fontSize: '0.72rem', padding: '0.1rem 0', color: '#fbbf24' }}>
                  → {imp.budget}: {imp.desc}
                </div>
              ))}
            </div>
          )}

          {/* Resolution options */}
          {v.resolutions.length > 0 && (
            <div>
              <div style={{ fontSize: '0.65rem', fontWeight: 600, color: '#9ca3af', marginBottom: '0.2rem' }}>RESOLUTIONS</div>
              {v.resolutions.map((res, i) => (
                <div key={i} style={{
                  fontSize: '0.72rem', padding: '0.3rem 0.4rem', marginBottom: '0.2rem',
                  background: 'rgba(255,255,255,0.03)', borderRadius: '4px',
                }}
                  onMouseEnter={() => res.param && checkCycles(res.param)}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <span style={{ color: '#10b981' }}>{res.desc}</span>
                    {res.dir && <span style={{ fontSize: '0.6rem', color: '#6b7280' }}>({res.dir})</span>}
                  </div>
                  {res.trade_off && (
                    <div style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '0.1rem' }}>
                      Trade-off: {res.trade_off}
                    </div>
                  )}
                  {res.param && sendEdit && (
                    <button className="btn btn-sm" onClick={() => {
                      sendEdit(res.param, res.dir === 'decrease' ? v.limit * 0.9 : v.limit * 1.1, { rationale: `Auto-fix: ${res.desc}` })
                      setAppliedRes(res.id); setTimeout(() => setAppliedRes(null), 2000)
                    }} style={{ marginTop: '0.2rem', fontSize: '0.6rem', padding: '0.1rem 0.4rem', background: appliedRes === res.id ? '#10b981' : '#3b82f6' }}>
                      {appliedRes === res.id ? 'Applied' : 'Apply Fix'}
                    </button>
                  )}
                  {/* Circular dependency warning */}
                  {cycles[res.param] && cycles[res.param].length > 0 && (
                    <div style={{ marginTop: '0.2rem', padding: '0.2rem 0.3rem', background: 'rgba(239,68,68,0.1)', borderRadius: '3px', border: '1px solid rgba(239,68,68,0.3)' }}>
                      <div style={{ fontSize: '0.62rem', fontWeight: 600, color: '#ef4444' }}>⚠ CIRCULAR DEPENDENCY</div>
                      {cycles[res.param].map((cycle, ci) => (
                        <div key={ci} style={{ fontSize: '0.6rem', color: '#fca5a5', marginTop: '0.1rem' }}>
                          {cycle.join(' → ')}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
