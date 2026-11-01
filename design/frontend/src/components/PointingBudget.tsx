/**
 * PointingBudget — RSS error budget tree for pointing accuracy.
 *
 * Shows per-contributor error and RSS combination vs requirement.
 */
import { useState, useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useApplyToDesign } from '../hooks/useApplyToDesign'
import { fs } from '../theme/tokens'

interface ErrorContributor {
  id: string; name: string; value_deg: number; editable: boolean; notes: string
  category: 'knowledge' | 'control'
}

export function PointingBudget() {
  const req = useDesignStore(s => s.requirements.payloads?.[0]?.pointing_accuracy_deg ?? 0.1)
  const setParam = useDesignStore(s => s.setParameter)

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
      <tr><td colSpan={4} style={{ padding: '0.4rem 0.5rem', fontSize: fs.label, fontWeight: 700, color, background: `color-mix(in srgb, ${color} 6%, transparent)` }}>{title}</td></tr>
      {items.map(c => (
        <tr key={c.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
          <td style={{ ...td, paddingLeft: '1.2rem' }}>{c.name}</td>
          <td style={tdR}>
            <input className="input" type="number" step={0.001} value={c.value_deg}
              onChange={e => updateValue(c.id, Number(e.target.value))}
              style={{ width: '70px', fontSize: fs.label, textAlign: 'right' }} />
          </td>
          <td style={{ ...tdR, color: 'var(--text-3)' }}>{(c.value_deg ** 2).toExponential(2)}</td>
          <td style={{ ...td, fontSize: fs.label, color: 'var(--text-3)' }}>{c.notes}</td>
        </tr>
      ))}
      <tr style={{ borderBottom: '1px solid var(--line)' }}>
        <td style={{ ...td, paddingLeft: '1.2rem', fontWeight: 600, color }}>RSS ({title})</td>
        <td style={{ ...tdR, fontWeight: 600, color }}>{rss.toFixed(4)}°</td>
        <td style={tdR}></td>
        <td style={td}></td>
      </tr>
    </>
  )

  return (
    <div className="card">
      <h3 style={{ fontSize: fs.value, marginBottom: '0.3rem' }}>Pointing Error Budget (RSS)</h3>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.5rem' }}>
        Separate knowledge and control error budgets per ECSS-E-ST-60-30C. Requirement: {req}°.
      </p>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
            <th style={th}>Error Source</th>
            <th style={thR}>Value (°)</th>
            <th style={thR}>Squared</th>
            <th style={th}>Notes</th>
          </tr>
        </thead>
        <tbody>
          {renderGroup('Knowledge Errors', knowledgeContribs, rssKnowledge, 'var(--interactive)')}
          {renderGroup('Control Errors', controlContribs, rssControl, 'var(--status-caution)')}
          <tr style={{ borderTop: '2px solid var(--line)', fontWeight: 700 }}>
            <td style={td}>TOTAL (Knowledge + Control RSS)</td>
            <td style={{ ...tdR, color: margin >= 0 ? 'var(--status-ok)' : 'var(--status-alarm)', fontWeight: 700, fontSize: fs.body }}>
              {rssTotal.toFixed(4)}°
            </td>
            <td style={tdR}></td>
            <td style={td}>
              <span style={{
                fontSize: fs.label, padding: '0.1rem 0.4rem', borderRadius: '3px',
                background: margin >= 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                color: margin >= 0 ? 'var(--status-ok)' : 'var(--status-alarm)', fontWeight: 600,
              }}>
                Margin: {margin >= 0 ? '+' : ''}{margin.toFixed(4)}° ({marginPct.toFixed(0)}%)
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <button className="btn" onClick={async () => { await apply(); setApplied(true); setTimeout(() => setApplied(false), 2000) }}
        style={{ marginTop: '0.5rem', width: '100%', background: applied ? 'var(--status-ok)' : 'var(--interactive)', fontSize: fs.label }}>
        {applied ? 'Applied — reconverging...' : 'Apply to Design'}
      </button>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
