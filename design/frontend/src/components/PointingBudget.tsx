/**
 * PointingBudget — RSS error budget tree for pointing accuracy.
 *
 * Shows per-contributor error and RSS combination vs requirement.
 */
import { useState, useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'
import { useApplyToDesign } from '../hooks/useApplyToDesign'

interface ErrorContributor {
  id: string; name: string; value_deg: number; editable: boolean; notes: string
  category: 'knowledge' | 'control'
}

export function PointingBudget() {
  const params = useActiveParameters()
  const req = useDesignStore(s => s.requirements.payloads?.[0]?.pointing_accuracy_deg ?? 0.1)
  const setParam = useDesignStore(s => s.setParameter)
  const get = (id: string) => { const p = params[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  const [contributors, setContributors] = useState<ErrorContributor[]>([
    // Knowledge errors — how well we know where we're pointing
    { id: 'sensor', name: 'Attitude sensor accuracy', value_deg: 0.01, editable: true, notes: 'Star tracker: 0.003-0.01°; Sun sensor: 0.5-2°', category: 'knowledge' },
    { id: 'alignment', name: 'Payload-bus alignment knowledge', value_deg: 0.02, editable: true, notes: 'Calibration residual after I&T', category: 'knowledge' },
    { id: 'orbit', name: 'Orbit knowledge error', value_deg: 0.01, editable: true, notes: 'GPS: 0.001°; TLE: 0.01-0.1°', category: 'knowledge' },
    { id: 'thermal_k', name: 'Thermal distortion knowledge', value_deg: 0.005, editable: true, notes: 'Model uncertainty of thermal deformation', category: 'knowledge' },
    { id: 'timing', name: 'Timing synchronisation', value_deg: 0.002, editable: true, notes: 'Clock accuracy × slew rate', category: 'knowledge' },
    // Control errors — how well we can point where intended
    { id: 'actuator', name: 'Actuator resolution', value_deg: 0.005, editable: true, notes: 'Reaction wheel: 0.005°; Magnetorquer: 1-5°', category: 'control' },
    { id: 'deadband', name: 'Control deadband', value_deg: 0.01, editable: true, notes: 'Attitude control loop limit cycle', category: 'control' },
    { id: 'jitter', name: 'Micro-vibration jitter', value_deg: 0.005, editable: true, notes: 'Reaction wheel imbalance (with isolators)', category: 'control' },
    { id: 'thermal_c', name: 'Thermal structural distortion', value_deg: 0.01, editable: true, notes: 'Actual deformation over thermal cycle', category: 'control' },
    { id: 'flexibility', name: 'Structural flexibility', value_deg: 0.003, editable: true, notes: 'Appendage/panel flex during manoeuvre', category: 'control' },
  ])

  const knowledgeContribs = contributors.filter(c => c.category === 'knowledge')
  const controlContribs = contributors.filter(c => c.category === 'control')

  const rssKnowledge = useMemo(() => Math.sqrt(knowledgeContribs.reduce((s, c) => s + c.value_deg ** 2, 0)), [contributors])
  const rssControl = useMemo(() => Math.sqrt(controlContribs.reduce((s, c) => s + c.value_deg ** 2, 0)), [contributors])
  const rssTotal = useMemo(() => Math.sqrt(rssKnowledge ** 2 + rssControl ** 2), [rssKnowledge, rssControl])

  const margin = req - rssTotal
  const marginPct = req > 0 ? (margin / req) * 100 : 0

  const updateValue = (id: string, value: number) => {
    setContributors(prev => {
      const next = prev.map(c => c.id === id ? { ...c, value_deg: value } : c)
      const k = Math.sqrt(next.filter(c => c.category === 'knowledge').reduce((s, c) => s + c.value_deg ** 2, 0))
      const ctrl = Math.sqrt(next.filter(c => c.category === 'control').reduce((s, c) => s + c.value_deg ** 2, 0))
      const total = Math.sqrt(k ** 2 + ctrl ** 2)
      setParam('aocs.pointing_accuracy_deg', total, 'pointing-budget')
      setParam('aocs.pointing_knowledge_deg', k, 'pointing-budget')
      setParam('aocs.pointing_control_deg', ctrl, 'pointing-budget')
      return next
    })
  }

  const [applied, setApplied] = useState(false)
  const apply = useApplyToDesign({
    events: [
      { kind: 'parameter_override', target_id: 'aocs.pointing_accuracy_deg', new_value: rssTotal },
      { kind: 'parameter_override', target_id: 'aocs.pointing_knowledge_deg', new_value: rssKnowledge },
      { kind: 'parameter_override', target_id: 'aocs.pointing_control_deg', new_value: rssControl },
    ],
    correlation_id: 'pointing-budget',
    rationale: 'Manual pointing error budget tuning',
  })

  const renderGroup = (title: string, items: ErrorContributor[], rss: number, color: string) => (
    <>
      <tr><td colSpan={4} style={{ padding: '0.4rem 0.5rem', fontSize: '0.7rem', fontWeight: 700, color, background: `${color}10` }}>{title}</td></tr>
      {items.map(c => (
        <tr key={c.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <td style={{ ...td, paddingLeft: '1.2rem' }}>{c.name}</td>
          <td style={tdR}>
            <input className="input" type="number" step={0.001} value={c.value_deg}
              onChange={e => updateValue(c.id, Number(e.target.value))}
              style={{ width: '70px', fontSize: '0.72rem', textAlign: 'right' }} />
          </td>
          <td style={{ ...tdR, color: '#6b7280' }}>{(c.value_deg ** 2).toExponential(2)}</td>
          <td style={{ ...td, fontSize: '0.65rem', color: '#6b7280' }}>{c.notes}</td>
        </tr>
      ))}
      <tr style={{ borderBottom: '1px solid #374151' }}>
        <td style={{ ...td, paddingLeft: '1.2rem', fontWeight: 600, color }}>RSS ({title})</td>
        <td style={{ ...tdR, fontWeight: 600, color }}>{rss.toFixed(4)}°</td>
        <td style={tdR}></td>
        <td style={td}></td>
      </tr>
    </>
  )

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.9rem', marginBottom: '0.3rem' }}>Pointing Error Budget (RSS)</h3>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Separate knowledge and control error budgets per ECSS-E-ST-60-30C. Requirement: {req}°.
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
          {renderGroup('Knowledge Errors', knowledgeContribs, rssKnowledge, '#3b82f6')}
          {renderGroup('Control Errors', controlContribs, rssControl, '#f59e0b')}
          <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
            <td style={td}>TOTAL (Knowledge + Control RSS)</td>
            <td style={{ ...tdR, color: margin >= 0 ? '#10b981' : '#ef4444', fontWeight: 700, fontSize: '0.85rem' }}>
              {rssTotal.toFixed(4)}°
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
      <button className="btn" onClick={async () => { await apply(); setApplied(true); setTimeout(() => setApplied(false), 2000) }}
        style={{ marginTop: '0.5rem', width: '100%', background: applied ? '#10b981' : '#3b82f6', fontSize: '0.78rem' }}>
        {applied ? 'Applied — reconverging...' : 'Apply to Design'}
      </button>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
