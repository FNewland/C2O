/**
 * FMECAPanel — failure mode awareness during design decisions.
 *
 * Shows failure modes, RPN scores, and redundancy recommendations
 * for the current architecture. Helps engineers make informed
 * architecture choices at system level.
 */
import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'

interface FailureMode {
  id: string
  component: string
  mode: string
  cause: string
  local_effect: string
  system_effect: string
  severity: number
  occurrence: number
  detection: number
  rpn: number
  mitigation: string
}

interface FMECAResult {
  failure_modes: FailureMode[]
  total_rpn: number
  critical_count: number
  top_risks: FailureMode[]
  redundancy_recommendations: { failure_mode_id: string; component: string; recommendation: string; expected_rpn_reduction: number }[]
}

export function FMECAPanel() {
  const [result, setResult] = useState<FMECAResult | null>(null)
  const [loading, setLoading] = useState(false)
  const requirements = useDesignStore(s => s.requirements)

  useEffect(() => {
    setLoading(true)
    fetch('/api/fmeca/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        spacecraft_class: requirements.spacecraft_class || 'nano',
        subsystems: ['eps', 'aocs', 'ttc', 'obc', 'thermal', 'structure'],
        include_redundancy: true,
      }),
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setResult(data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [requirements.spacecraft_class])

  if (loading) return <div style={{ padding: '1rem', color: '#6b7280' }}>Analysing failure modes...</div>

  if (!result) return (
    <div style={{ padding: '1rem', color: '#6b7280' }}>
      <h3>FMECA — Failure Mode Analysis</h3>
      <p style={{ fontSize: '0.78rem' }}>No failure mode data available. Check backend connection.</p>
    </div>
  )

  const riskColor = (rpn: number) => rpn >= 60 ? '#ef4444' : rpn >= 30 ? '#f59e0b' : '#10b981'

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>FMECA — Design Risk Awareness</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Failure modes for current architecture. Use this to inform redundancy and architecture decisions.
        Critical items (RPN ≥ 60) should drive architecture changes.
      </p>

      {/* Summary */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{ padding: '0.5rem 0.75rem', background: '#1f2937', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#d1d5db' }}>{result.failure_modes.length}</div>
          <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>Failure modes</div>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: '#1f2937', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: result.critical_count > 0 ? '#ef4444' : '#10b981' }}>{result.critical_count}</div>
          <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>Critical (RPN ≥ 60)</div>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: '#1f2937', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f59e0b' }}>{result.total_rpn}</div>
          <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>Total RPN</div>
        </div>
      </div>

      {/* Top risks */}
      {result.top_risks.length > 0 && (
        <div className="card" style={{ borderLeft: '3px solid #ef4444', marginBottom: '0.75rem' }}>
          <h3 style={{ fontSize: '0.85rem', color: '#ef4444', marginBottom: '0.3rem' }}>Top Risks</h3>
          {result.top_risks.slice(0, 5).map(fm => (
            <div key={fm.id} style={{ padding: '0.3rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.72rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600 }}>{fm.component}: {fm.mode}</span>
                <span style={{ fontFamily: 'monospace', color: riskColor(fm.rpn), fontWeight: 700 }}>RPN {fm.rpn}</span>
              </div>
              <div style={{ color: '#9ca3af', fontSize: '0.68rem' }}>{fm.system_effect}</div>
              <div style={{ color: '#6b7280', fontSize: '0.65rem' }}>Mitigation: {fm.mitigation}</div>
            </div>
          ))}
        </div>
      )}

      {/* Redundancy recommendations */}
      {result.redundancy_recommendations && result.redundancy_recommendations.length > 0 && (
        <div className="card" style={{ borderLeft: '3px solid #3b82f6', marginBottom: '0.75rem' }}>
          <h3 style={{ fontSize: '0.85rem', color: '#3b82f6', marginBottom: '0.3rem' }}>Redundancy Recommendations</h3>
          {result.redundancy_recommendations.map((s: any, i: number) => (
            <div key={i} style={{ padding: '0.2rem 0', fontSize: '0.72rem' }}>
              <span style={{ fontWeight: 600 }}>{s.component}:</span> {s.recommendation}
              {s.expected_rpn_reduction && <span style={{ color: '#10b981', marginLeft: '0.3rem' }}>(RPN -{s.expected_rpn_reduction})</span>}
            </div>
          ))}
        </div>
      )}

      {/* Full failure mode table */}
      <div className="card">
        <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>All Failure Modes</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.68rem' }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
              <th style={th}>Component</th>
              <th style={th}>Failure Mode</th>
              <th style={thC}>S</th>
              <th style={thC}>O</th>
              <th style={thC}>D</th>
              <th style={thC}>RPN</th>
              <th style={th}>Mitigation</th>
            </tr>
          </thead>
          <tbody>
            {result.failure_modes.map(fm => (
              <tr key={fm.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={td}>{fm.component}</td>
                <td style={td}>{fm.mode}</td>
                <td style={tdC}>{fm.severity}</td>
                <td style={tdC}>{fm.occurrence}</td>
                <td style={tdC}>{fm.detection}</td>
                <td style={{ ...tdC, color: riskColor(fm.rpn), fontWeight: 700 }}>{fm.rpn}</td>
                <td style={{ ...td, fontSize: '0.62rem', color: '#9ca3af' }}>{fm.mitigation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.6rem', color: '#9ca3af', textTransform: 'uppercase' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
