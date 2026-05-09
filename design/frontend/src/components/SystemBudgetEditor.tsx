/**
 * SystemBudgetEditor — editable budget allocation at system level.
 *
 * Phase 2 tool: mission sets envelope, system engineer assigns buckets to subsystems.
 * Each budget type (mass, power, cost, delta-V, volume, data) gets a cascading view.
 */
import { useState, useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'
import { BudgetCascade } from '../charts/BudgetCascade'

type BudgetType = 'mass' | 'power' | 'cost' | 'volume' | 'deltav' | 'data'

const BUDGET_CONFIGS: { type: BudgetType; label: string; unit: string; color: string }[] = [
  { type: 'mass', label: 'Mass', unit: 'kg', color: '#3b82f6' },
  { type: 'power', label: 'Power', unit: 'W', color: '#f59e0b' },
  { type: 'cost', label: 'Cost', unit: 'kEUR', color: '#10b981' },
  { type: 'volume', label: 'Volume', unit: 'cm³', color: '#8b5cf6' },
  { type: 'deltav', label: 'Delta-V', unit: 'm/s', color: '#f97316' },
  { type: 'data', label: 'Data', unit: 'GB/day', color: '#06b6d4' },
]

// Each budget type has its own decomposition logic
const BUDGET_DECOMPOSITION: Record<BudgetType, string[]> = {
  mass: ['Payload', 'EPS', 'AOCS', 'Comms', 'OBC', 'Thermal', 'Structure', 'Propulsion', 'Harness', 'Margin'],
  power: ['Generation (SA)', 'Storage (Battery)', 'Payload Use', 'Platform Use', 'Heater Use', 'Margin'],
  cost: ['Space Segment', 'Ground Segment', 'Operations', 'Launch', 'PM/SE', 'Margin'],
  volume: ['Payload', 'EPS', 'AOCS', 'Comms', 'OBC', 'Thermal', 'Propulsion', 'Margin'],
  deltav: ['Orbit Insertion', 'Station-keeping', 'Orbit Maintenance', 'Collision Avoidance', 'Deorbit', 'Margin'],
  data: ['Data Collection', 'Onboard Storage', 'Downlink Capacity', 'Ground Processing', 'Margin'],
}

export function SystemBudgetEditor() {
  const [activeBudget, setActiveBudget] = useState<BudgetType>('mass')
  const requirements = useDesignStore(s => s.requirements)
  const result = useDesignStore(s => s.result)
  const setParam = useDesignStore(s => s.setParameter)
  const storedAllocations = useDesignStore(s => s.budgetAllocations)
  const persistAllocations = useDesignStore(s => s.setBudgetAllocations)
  const studyId = useDesignStore(s => s.studyId)

  // Budget allocations — restored from designStore (persisted), initialized from parametric if empty
  const initGet = (id: string) => { const p = (result?.parameters as any)?.[id]; return p && typeof p.value === 'number' ? p.value : 0 }
  const [allocations, setAllocationsLocal] = useState<Record<string, Record<string, number>>>(() => {
    // If we have persisted allocations, use them
    if (storedAllocations && Object.keys(storedAllocations).length > 0) return storedAllocations

    const massEnv = requirements.target_mass_kg || 6
    const hasResult = !!result
    return {
      mass: {
        Payload: hasResult ? (initGet('payload.mass_kg') || requirements.payloads?.[0]?.mass_kg || massEnv * 0.25) * 1.2 : massEnv * 0.25,
        EPS: hasResult ? initGet('power.eps_mass_kg') * 1.2 : massEnv * 0.22,
        AOCS: hasResult ? initGet('aocs.mass_kg') * 1.2 : massEnv * 0.18,
        Comms: hasResult ? initGet('link.ttc_mass_kg') * 1.2 : massEnv * 0.08,
        OBC: hasResult ? initGet('data.obdh_mass_kg') * 1.2 : massEnv * 0.03,
        Thermal: hasResult ? initGet('thermal.tcs_mass_kg') * 1.2 : massEnv * 0.05,
        Structure: hasResult ? initGet('structure.mass_kg') * 1.2 : massEnv * 0.14,
        Propulsion: hasResult ? initGet('propulsion.total_mass_kg') * 1.2 : 0,
        Harness: massEnv * 0.04,
        Margin: massEnv * 0.05,
      },
      power: {
        Payload: requirements.payloads?.[0]?.power_w || 10,
        EPS: 0, AOCS: hasResult ? initGet('aocs.power_w') * 1.2 : 5,
        Comms: hasResult ? initGet('link.ttc_power_w') * 1.2 : 8,
        OBC: 2, Thermal: hasResult ? initGet('thermal.heater_power_w') * 1.2 : 3,
        Structure: 0, Propulsion: 0, Margin: 2,
      },
      cost: {
        Payload: 200, EPS: 100, AOCS: 150, Comms: 100, OBC: 50, Thermal: 30, Structure: 50, Propulsion: 0, Margin: 50,
      },
    }
  })

  // Persist allocations to designStore (survives tab switches + page refresh)
  const setAllocations = (updater: (prev: Record<string, Record<string, number>>) => Record<string, Record<string, number>>) => {
    setAllocationsLocal(prev => {
      const next = updater(prev)
      persistAllocations(next)
      return next
    })
  }

  // SYSTEM-V: "Used" values come from the ELEMENT TREE.
  // For each subsystem element, sum its component children's properties.
  // This is the REAL budget rollup — Phase 3 equipment → Phase 2 budgets.
  const elements = useModelStore(s => s.elements)
  const getChildren = useModelStore(s => s.getChildren)
  const params = result?.parameters || {}
  const get = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  // Compute "used" from element tree: sum component children of each subsystem
  const usedValues = useMemo(() => {
    const massUsed: Record<string, number> = {}
    const powerUsed: Record<string, number> = {}
    const costUsed: Record<string, number> = {}

    // Map subsystem domain → budget label
    const domainToLabel: Record<string, string> = {
      payload: 'Payload', power: 'EPS', aocs: 'AOCS', ttc: 'Comms',
      obc: 'OBC', thermal: 'Thermal', structure: 'Structure', propulsion: 'Propulsion',
    }

    // Initialize all to zero
    for (const label of BUDGET_DECOMPOSITION.mass) { massUsed[label] = 0 }
    for (const label of BUDGET_DECOMPOSITION.power) { powerUsed[label] = 0 }
    for (const label of BUDGET_DECOMPOSITION.cost) { costUsed[label] = 0 }

    // Iterate subsystem elements and sum their children
    for (const el of elements.values()) {
      if (el.element_type !== 'subsystem') continue
      const label = domainToLabel[el.subsystem_domain || '']
      if (!label) continue

      // Get children (components) of this subsystem
      const children = getChildren(el.id)
      let childMass = 0, childPower = 0, childCost = 0
      for (const child of children) {
        childMass += (child.mass_kg || 0) * (child.quantity || 1)
        childPower += (child.power_avg_w || 0) * (child.quantity || 1)
        childCost += (child.cost_recurring_keur || 0) * (child.quantity || 1)
      }

      // If no children, use the subsystem's own values (from architecture selection)
      const usedMass = childMass > 0 ? childMass : (el.mass_kg || 0) * (el.quantity || 1)
      const usedPower = childPower > 0 ? childPower : (el.power_avg_w || 0) * (el.quantity || 1)
      const usedCost = childCost > 0 ? childCost : (el.cost_recurring_keur || 0) * (el.quantity || 1)

      if (label in massUsed) massUsed[label] = usedMass
      // Power goes to "Platform Use" for most subsystems
      if (label !== 'Payload') powerUsed['Platform Use'] = (powerUsed['Platform Use'] || 0) + usedPower
      else powerUsed['Payload Use'] = usedPower
    }

    // Also check flat store as fallback (parametric estimates when no elements exist)
    if (elements.size < 5) {
      // No meaningful element tree — show parametric estimates
      massUsed['Payload'] = get('payload.mass_kg') || requirements.payloads?.[0]?.mass_kg || 0
      massUsed['EPS'] = get('power.eps_mass_kg')
      massUsed['AOCS'] = get('aocs.mass_kg')
      massUsed['Comms'] = get('link.ttc_mass_kg')
      massUsed['Structure'] = get('structure.mass_kg')
      powerUsed['Generation (SA)'] = get('power.sa_power_eol_w')
      powerUsed['Payload Use'] = requirements.payloads?.[0]?.power_w || 0
    }

    return { mass: massUsed, power: powerUsed, cost: costUsed }
  }, [elements, requirements, result])

  const envelopes: Record<string, number> = {
    mass: requirements.target_mass_kg || 6,
    power: get('power.sa_power_eol_w') || 30,
    cost: (requirements.target_cost_meur || 2) * 1000,
    volume: requirements.spacecraft_class === 'nano' ? 3000 : 6000,
    deltav: get('propulsion.delta_v_total_ms') || 0,
    data: 10,
  }

  const config = BUDGET_CONFIGS.find(c => c.type === activeBudget)!
  const currentAllocations = allocations[activeBudget] || {}
  const currentUsed = usedValues[activeBudget] || {}
  const envelope = envelopes[activeBudget]

  const updateAllocation = (subsys: string, value: number) => {
    setAllocations(prev => ({
      ...prev,
      [activeBudget]: { ...(prev[activeBudget] || {}), [subsys]: value },
    }))

    // Also sync to backend BudgetAllocationRow if we have a study + matching element
    if (studyId) {
      const domainMap: Record<string, string> = {
        Payload: 'payload', EPS: 'power', AOCS: 'aocs', Comms: 'ttc',
        OBC: 'obc', Thermal: 'thermal', Structure: 'structure', Propulsion: 'propulsion',
      }
      const domain = domainMap[subsys]
      if (domain) {
        // Find the subsystem element to attach the allocation to
        for (const el of elements.values()) {
          if (el.element_type === 'subsystem' && el.subsystem_domain === domain) {
            fetch(`/api/elements/${el.id}/allocations`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                budget_type: activeBudget, allocation_value: value,
                unit: config.unit, source: 'manual',
              }),
            }).catch(() => {}) // Best-effort backend sync
            break
          }
        }
      }
    }
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>System Budget Allocation</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Assign budget buckets from the mission envelope to each subsystem. Subsystem design fills the buckets.
        {result ? (
          <span style={{ display: 'block', fontSize: '0.65rem', color: '#f59e0b', marginTop: '0.2rem' }}>
            "Used" values are parametric estimates from agents — will update when equipment is selected at subsystem level.
          </span>
        ) : (
          <span style={{ display: 'block', fontSize: '0.65rem', color: '#6b7280', marginTop: '0.2rem' }}>
            Run a design to populate budget estimates.
          </span>
        )}
      </p>

      {/* Budget type selector */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {BUDGET_CONFIGS.map(bc => (
          <button key={bc.type} onClick={() => setActiveBudget(bc.type)} style={{
            padding: '0.3rem 0.75rem', fontSize: '0.75rem', borderRadius: '4px', cursor: 'pointer',
            background: activeBudget === bc.type ? bc.color : 'var(--bg-secondary, #1f2937)',
            color: activeBudget === bc.type ? 'white' : '#9ca3af',
            border: `1px solid ${activeBudget === bc.type ? bc.color : '#374151'}`,
          }}>{bc.label} ({bc.unit})</button>
        ))}
      </div>

      {/* Volume: form factor selector */}
      {activeBudget === 'volume' && (
        <div className="card" style={{ marginBottom: '0.5rem' }}>
          <h3 style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>Spacecraft Form Factor</h3>
          <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
            {[
              { label: '1U', volume: 1000, mass: 1.33 },
              { label: '2U', volume: 2000, mass: 2.66 },
              { label: '3U', volume: 3000, mass: 4.0 },
              { label: '6U', volume: 6000, mass: 12.0 },
              { label: '12U', volume: 12000, mass: 24.0 },
              { label: '16U', volume: 16000, mass: 32.0 },
            ].map(ff => (
              <button key={ff.label} className="btn btn-sm" onClick={() => {
                // Update volume envelope
                envelopes.volume = ff.volume
              }} style={{
                fontSize: '0.72rem',
                background: envelope === ff.volume ? '#8b5cf6' : '#374151',
                color: envelope === ff.volume ? 'white' : '#9ca3af',
              }}>{ff.label} ({(ff.volume / 1000).toFixed(0)}L, ≤{ff.mass}kg)</button>
            ))}
          </div>
        </div>
      )}

      {/* Delta-V: estimation helper */}
      {activeBudget === 'deltav' && (
        <div className="card" style={{ marginBottom: '0.5rem', fontSize: '0.72rem', color: '#9ca3af' }}>
          <h3 style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>Delta-V Estimation Guide</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.3rem' }}>
            <span>LEO drag makeup (400-600 km): 1-5 m/s/yr</span>
            <span>SSO maintenance: 2-10 m/s/yr</span>
            <span>Collision avoidance: 0.5-2 m/s/event</span>
            <span>Deorbit (LEO): 50-150 m/s</span>
            <span>GTO insertion correction: 10-50 m/s</span>
            <span>Lunar orbit insertion: 800-1000 m/s</span>
          </div>
        </div>
      )}

      {/* Data: estimation helper */}
      {activeBudget === 'data' && (
        <div className="card" style={{ marginBottom: '0.5rem', fontSize: '0.72rem', color: '#9ca3af' }}>
          <h3 style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>Data Budget Estimation</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.3rem' }}>
            <span>Payload data = rate × duty cycle × time</span>
            <span>HK telemetry: ~1-10 kbps continuous</span>
            <span>Storage = 2× daily data volume (buffer)</span>
            <span>Downlink capacity = rate × contact time</span>
          </div>
        </div>
      )}

      {/* SYSTEM-V: Cross-level conflict detection */}
      {(() => {
        const conflicts: { subsystem: string; allocated: number; used: number; overage: number }[] = []
        for (const ss of (BUDGET_DECOMPOSITION[activeBudget] || BUDGET_DECOMPOSITION.mass)) {
          const alloc = currentAllocations[ss] || 0
          const used = currentUsed[ss] || 0
          if (alloc > 0 && used > alloc) {
            conflicts.push({ subsystem: ss, allocated: alloc, used, overage: used - alloc })
          }
        }
        const totalAlloc = Object.values(currentAllocations).reduce((s, v) => s + (v || 0), 0)
        if (totalAlloc > envelope) {
          conflicts.push({ subsystem: 'TOTAL', allocated: envelope, used: totalAlloc, overage: totalAlloc - envelope })
        }
        if (conflicts.length === 0) return null
        return (
          <div style={{
            padding: '0.5rem 0.75rem', marginBottom: '0.75rem', borderRadius: '6px',
            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
          }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#ef4444', marginBottom: '0.3rem' }}>
              Budget Conflicts Detected
            </div>
            {conflicts.map(c => (
              <div key={c.subsystem} style={{ fontSize: '0.72rem', color: '#fca5a5', marginBottom: '0.15rem' }}>
                <strong>{c.subsystem}</strong>: used {c.used.toFixed(1)} {config.unit} exceeds
                {c.subsystem === 'TOTAL' ? ' envelope' : ' allocation'} of {c.allocated.toFixed(1)} {config.unit}
                {' '}(+{c.overage.toFixed(1)} {config.unit})
              </div>
            ))}
          </div>
        )
      })()}

      {/* Cascade view */}
      <BudgetCascade
        title={`${config.label} Budget`}
        envelope={envelope}
        unit={config.unit}
        items={(BUDGET_DECOMPOSITION[activeBudget] || BUDGET_DECOMPOSITION.mass).map(ss => ({
          label: ss,
          allocation: currentAllocations[ss] || 0,
          used: currentUsed[ss] || 0,
          unit: config.unit,
        }))}
      />

      {/* Editable allocation table */}
      <div className="card" style={{ marginTop: '0.75rem' }}>
        <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Allocations (editable)</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af' }}>Subsystem</th>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>Allocation ({config.unit})</th>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>Used</th>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>Margin</th>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'center', fontSize: '0.65rem', color: '#9ca3af' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {(BUDGET_DECOMPOSITION[activeBudget] || BUDGET_DECOMPOSITION.mass).map(ss => {
              const alloc = currentAllocations[ss] || 0
              const used = currentUsed[ss] || 0
              const margin = alloc > 0 ? ((alloc - used) / alloc * 100) : (used === 0 ? 100 : -100)
              const exceeded = alloc > 0 && used > alloc
              const color = exceeded ? '#ef4444' : margin > 20 ? '#10b981' : margin > 0 ? '#f59e0b' : '#ef4444'
              return (
                <tr key={ss} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '0.2rem 0.5rem' }}>{ss}</td>
                  <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right' }}>
                    <input type="number" step={0.1} value={alloc}
                      onChange={e => updateAllocation(ss, Number(e.target.value))}
                      style={{ width: '60px', fontSize: '0.72rem', textAlign: 'right', background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db', padding: '0.1rem 0.3rem' }} />
                  </td>
                  <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: '#9ca3af' }}>
                    {used.toFixed(2)}
                  </td>
                  <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color }}>
                    {alloc > 0 ? `${margin.toFixed(0)}%` : '—'}
                  </td>
                  <td style={{ padding: '0.2rem 0.5rem', textAlign: 'center' }}>
                    <span style={{
                      width: exceeded ? 10 : 8, height: exceeded ? 10 : 8, borderRadius: '50%',
                      background: alloc > 0 ? color : '#374151', display: 'inline-block',
                      boxShadow: exceeded ? '0 0 6px #ef4444' : 'none',
                    }} title={exceeded ? `EXCEEDED by ${(used - alloc).toFixed(1)} ${config.unit}` : ''} />
                  </td>
                </tr>
              )
            })}
            <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
              <td style={{ padding: '0.2rem 0.5rem' }}>Total</td>
              <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                {Object.values(currentAllocations).reduce((s, v) => s + (v || 0), 0).toFixed(1)}
              </td>
              <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                {Object.values(currentUsed).reduce((s, v) => s + (v || 0), 0).toFixed(2)}
              </td>
              <td colSpan={2} style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#6b7280' }}>
                Envelope: {envelope.toFixed(1)} {config.unit}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
