/**
 * FMECAPanel — failure mode awareness during design decisions.
 *
 * Shows failure modes, RPN scores, and redundancy recommendations
 * for the current architecture. Helps engineers make informed
 * architecture choices at system level.
 *
 * Two modes (SCDF-177): the catalogue analysis (``POST /api/fmeca/analyze``,
 * default, no study needed) and "Run from study" — the study-driven closure
 * (``POST /api/studies/{id}/analyses/fmeca/run``) whose failure modes are built
 * from the element tree, carry the functions allocated to each element and
 * flag single-point failures on critical elements.
 */
import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'
import type { FMECARunResponse, StudyFailureMode } from '../types/analyses'

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

export function FMECAPanel({ studyId }: { studyId?: string | null } = {}) {
  const [result, setResult] = useState<FMECAResult | null>(null)
  const [loading, setLoading] = useState(false)
  const requirements = useDesignStore(s => s.requirements)
  const [studyRun, setStudyRun] = useState<FMECARunResponse | null>(null)
  const [studyBusy, setStudyBusy] = useState(false)
  const [studyError, setStudyError] = useState<string | null>(null)

  const runFromStudy = async () => {
    if (!studyId) return
    setStudyBusy(true); setStudyError(null)
    try {
      const r = await fetch(`/api/studies/${studyId}/analyses/fmeca/run`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ critical: [] }),
      })
      if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
      setStudyRun(await r.json())
    } catch (e) {
      setStudyError(e instanceof Error ? e.message : String(e))
    } finally {
      setStudyBusy(false)
    }
  }

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
    <div style={{ padding: '2rem', color: '#6b7280' }}>
      <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: '#9ca3af' }}>FMECA — Failure Mode, Effects & Criticality Analysis</h3>
      <p style={{ fontSize: '0.78rem', marginBottom: '0.75rem' }}>
        FMECA identifies potential failure modes in your design and assesses their risk using the Risk Priority Number (RPN = Severity x Occurrence x Detection).
      </p>
      <div style={{ fontSize: '0.72rem', marginBottom: '0.75rem' }}>
        <p style={{ fontWeight: 600, marginBottom: '0.3rem' }}>How to address FMECA issues:</p>
        <ol style={{ paddingLeft: '1.2rem', lineHeight: 1.8 }}>
          <li><strong>Review top risks</strong> — focus on failure modes with RPN &gt; 60 (critical) or RPN &gt; 30 (major)</li>
          <li><strong>Add redundancy</strong> — the tool recommends where redundancy reduces risk most effectively (e.g., 3-of-4 reaction wheels instead of 3-of-3)</li>
          <li><strong>Select higher-TRL components</strong> — TRL 9 (flight-proven) components have lower occurrence scores</li>
          <li><strong>Improve detection</strong> — add health monitoring (voltage/current sensors, temperature telemetry, watchdog timers)</li>
          <li><strong>Accept risk</strong> — for 1U/educational missions, some single-point failures may be acceptable with documented rationale</li>
        </ol>
      </div>
      <p style={{ fontSize: '0.72rem', color: '#f59e0b' }}>
        Waiting for FMECA analysis... If this persists, check that the backend is running and the /api/fmeca/analyze endpoint is available.
      </p>
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

      {/* SCDF-177: study-driven run */}
      {studyId && (
        <div className="card" style={{ borderLeft: '3px solid #8b5cf6', marginBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
            <h3 style={{ fontSize: '0.85rem', color: '#8b5cf6', margin: 0 }}>From the study model</h3>
            <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>failure modes per element, functions allocated, single points on critical elements</span>
            <span style={{ flex: 1 }} />
            <button disabled={studyBusy} onClick={runFromStudy}
                    style={{ cursor: 'pointer', fontSize: '0.66rem', padding: '0.2rem 0.6rem', borderRadius: 4, border: '1px solid #8b5cf6', background: '#8b5cf622', color: '#c4b5fd' }}>
              {studyBusy ? 'Running…' : studyRun ? 'Re-run from study' : 'Run from study'}
            </button>
          </div>
          {studyError && <div style={{ color: '#ef4444', fontSize: '0.68rem' }}>{studyError}</div>}
          {studyRun && (
            <>
              <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.68rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
                <span>{studyRun.summary.fmeca_modes ?? studyRun.modes.length} modes</span>
                <span style={{ color: (studyRun.summary.fmeca_single_point_failures ?? 0) > 0 ? '#f59e0b' : '#10b981' }}>{studyRun.summary.fmeca_single_point_failures ?? 0} single points</span>
                <span style={{ color: (studyRun.summary.fmeca_critical_modes ?? 0) > 0 ? '#ef4444' : '#10b981' }}>{studyRun.summary.fmeca_critical_modes ?? 0} on critical elements</span>
                <span>max RPN {studyRun.summary.fmeca_max_rpn}</span>
                <span style={{ color: '#6b7280' }}>{studyRun.conflicts.length} conflict{studyRun.conflicts.length === 1 ? '' : 's'} published</span>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.66rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                    <th style={th}>Element</th><th style={th}>Failure mode</th><th style={th}>Functions</th>
                    <th style={thC}>S</th><th style={thC}>O</th><th style={thC}>D</th><th style={thC}>RPN</th><th style={th}>Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {studyRun.modes.map((m: StudyFailureMode) => (
                    <tr key={m.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: m.single_point && m.critical ? '#ef444411' : undefined }}>
                      <td style={td}>{m.element_name}<span style={{ color: '#6b7280', marginLeft: 4, fontSize: '0.6rem' }}>{m.subsystem && m.subsystem !== m.element_name ? m.subsystem : m.domain}</span></td>
                      <td style={td}>{m.mode}</td>
                      <td style={{ ...td, color: '#9ca3af' }}>{m.functions.length ? m.functions.join(', ') : '—'}</td>
                      <td style={tdC}>{m.severity}</td><td style={tdC}>{m.occurrence}</td><td style={tdC}>{m.detection}</td>
                      <td style={{ ...tdC, color: riskColor(m.rpn), fontWeight: 700 }}>{m.rpn}</td>
                      <td style={td}>
                        {m.single_point && <span style={{ color: m.critical ? '#ef4444' : '#f59e0b', fontWeight: 600 }}>single point{m.critical ? ' · critical' : ''}</span>}
                        {m.redundant && <span style={{ color: '#10b981' }}>{m.redundancy_type ? `${m.redundancy_type} redundant` : `x${m.quantity}`}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

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
