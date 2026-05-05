/**
 * ProjectManagement — Risk matrix, schedule (Gantt), WBS, and PM tools.
 *
 * Provides:
 * - Interactive 5x5 risk matrix (likelihood x consequence)
 * - Project schedule with milestones and phase gates
 * - Work Breakdown Structure with work packages
 *
 * Per ECSS-M-ST-80C (Risk Management), NPR 8000.4, ECSS-M-ST-10C (Project Management).
 */
import { useState } from 'react'

type PMTab = 'risk' | 'schedule' | 'wbs'

interface Risk {
  id: string; title: string; description: string
  likelihood: number; consequence: number
  category: string; owner: string
  mitigation: string; status: 'open' | 'mitigating' | 'closed' | 'accepted'
}

interface Milestone {
  id: string; name: string; date: string
  phase: string; status: 'planned' | 'in_progress' | 'complete'
  dependencies: string[]
}

interface WorkPackage {
  id: string; name: string; description: string
  responsible: string; effort_hours: number
  status: 'not_started' | 'in_progress' | 'complete'
  phase: string
}

const RISK_COLORS: Record<number, string> = {
  1: '#10b981', 2: '#10b981', 3: '#84cc16', 4: '#84cc16',
  5: '#f59e0b', 6: '#f59e0b', 8: '#f59e0b', 9: '#f97316',
  10: '#f97316', 12: '#ef4444', 15: '#ef4444', 16: '#ef4444',
  20: '#ef4444', 25: '#dc2626',
}

const getRiskColor = (score: number) => {
  if (score <= 4) return '#10b981'
  if (score <= 9) return '#f59e0b'
  if (score <= 15) return '#f97316'
  return '#ef4444'
}

const DEFAULT_RISKS: Risk[] = [
  { id: 'R-001', title: 'Deployment failure', description: 'SA or antenna fails to deploy', likelihood: 3, consequence: 4, category: 'technical', owner: 'structures_engineer', mitigation: 'Redundant deployment mechanism; 100+ deployment test cycles', status: 'open' },
  { id: 'R-002', title: 'Communication loss after separation', description: 'No first contact acquired', likelihood: 2, consequence: 5, category: 'technical', owner: 'comms_engineer', mitigation: 'Beacon mode; multiple ground stations; timer-based recovery', status: 'open' },
  { id: 'R-003', title: 'Launch delay', description: 'Launch vehicle failure or manifest slip', likelihood: 3, consequence: 2, category: 'programmatic', owner: 'project_manager', mitigation: 'Manifest on multiple vehicles; schedule buffer', status: 'open' },
  { id: 'R-004', title: 'Spectrum licensing delay', description: 'ISED/ITU filing takes longer than expected', likelihood: 3, consequence: 2, category: 'regulatory', owner: 'compliance_engineer', mitigation: 'Start filing 18+ months before launch', status: 'open' },
  { id: 'R-005', title: 'Power budget negative in eclipse', description: 'Battery DoD exceeds limit', likelihood: 2, consequence: 4, category: 'technical', owner: 'power_engineer', mitigation: 'Conservative duty cycling; 30% DoD limit; margin in battery sizing', status: 'open' },
]

const DEFAULT_MILESTONES: Milestone[] = [
  { id: 'M-001', name: 'Mission Need Approved', date: '', phase: 'Pre-A', status: 'complete', dependencies: [] },
  { id: 'M-002', name: 'MCR (Mission Concept Review)', date: '', phase: 'Pre-A', status: 'planned', dependencies: ['M-001'] },
  { id: 'M-003', name: 'SRR (System Requirements Review)', date: '', phase: 'A', status: 'planned', dependencies: ['M-002'] },
  { id: 'M-004', name: 'PDR (Preliminary Design Review)', date: '', phase: 'B', status: 'planned', dependencies: ['M-003'] },
  { id: 'M-005', name: 'CDR (Critical Design Review)', date: '', phase: 'C', status: 'planned', dependencies: ['M-004'] },
  { id: 'M-006', name: 'TRR (Test Readiness Review)', date: '', phase: 'D', status: 'planned', dependencies: ['M-005'] },
  { id: 'M-007', name: 'FRR (Flight Readiness Review)', date: '', phase: 'D', status: 'planned', dependencies: ['M-006'] },
  { id: 'M-008', name: 'Launch', date: '', phase: 'D', status: 'planned', dependencies: ['M-007'] },
  { id: 'M-009', name: 'LEOP Complete', date: '', phase: 'E', status: 'planned', dependencies: ['M-008'] },
  { id: 'M-010', name: 'Commissioning Complete', date: '', phase: 'E', status: 'planned', dependencies: ['M-009'] },
]

const DEFAULT_WBS: WorkPackage[] = [
  { id: 'WP-1.0', name: 'Programme Management', description: 'Project planning, reporting, reviews', responsible: 'project_manager', effort_hours: 200, status: 'in_progress', phase: 'All' },
  { id: 'WP-2.0', name: 'Systems Engineering', description: 'Requirements, architecture, budgets, V&V', responsible: 'systems_engineer', effort_hours: 300, status: 'in_progress', phase: 'All' },
  { id: 'WP-3.0', name: 'Payload Development', description: 'Instrument design, build, calibration', responsible: 'payload_lead', effort_hours: 400, status: 'not_started', phase: 'B-C' },
  { id: 'WP-4.0', name: 'Bus Procurement', description: 'COTS component procurement and acceptance', responsible: 'systems_engineer', effort_hours: 100, status: 'not_started', phase: 'C' },
  { id: 'WP-5.0', name: 'Integration & Test', description: 'Assembly, functional test, environmental test', responsible: 'structures_engineer', effort_hours: 250, status: 'not_started', phase: 'C-D' },
  { id: 'WP-6.0', name: 'Software Development', description: 'FSW, GSW, ops procedures', responsible: 'software_engineer', effort_hours: 350, status: 'not_started', phase: 'B-D' },
  { id: 'WP-7.0', name: 'Ground Segment', description: 'Station setup, MCS, data pipeline', responsible: 'ground_segment', effort_hours: 150, status: 'not_started', phase: 'C-D' },
  { id: 'WP-8.0', name: 'Launch Campaign', description: 'Launch procurement, integration, shipping', responsible: 'project_manager', effort_hours: 100, status: 'not_started', phase: 'D' },
  { id: 'WP-9.0', name: 'Operations', description: 'LEOP, commissioning, nominal ops', responsible: 'mission_ops', effort_hours: 500, status: 'not_started', phase: 'E' },
]

export function ProjectManagement() {
  const [activeTab, setActiveTab] = useState<PMTab>('risk')
  const [risks, setRisks] = useState<Risk[]>(DEFAULT_RISKS)
  const [milestones] = useState<Milestone[]>(DEFAULT_MILESTONES)
  const [wbs] = useState<WorkPackage[]>(DEFAULT_WBS)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Project Management</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Risk register (ECSS-M-ST-80C), schedule milestones, and work breakdown structure.
      </p>

      {/* Tab selector */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '1rem' }}>
        {[
          { id: 'risk' as PMTab, label: 'Risk Matrix' },
          { id: 'schedule' as PMTab, label: 'Schedule' },
          { id: 'wbs' as PMTab, label: 'WBS' },
        ].map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: '0.3rem 0.75rem', fontSize: '0.78rem', borderRadius: '4px', cursor: 'pointer',
            background: activeTab === t.id ? '#3b82f6' : 'var(--bg-secondary, #1f2937)',
            color: activeTab === t.id ? 'white' : '#9ca3af',
            border: `1px solid ${activeTab === t.id ? '#3b82f6' : '#374151'}`,
          }}>{t.label}</button>
        ))}
      </div>

      {/* Risk Matrix */}
      {activeTab === 'risk' && (
        <div>
          {/* 5x5 matrix visualization */}
          <div style={{ display: 'grid', gridTemplateColumns: '50px repeat(5, 1fr)', gap: '2px', marginBottom: '1rem' }}>
            <div />
            {[1,2,3,4,5].map(c => (
              <div key={c} style={{ textAlign: 'center', fontSize: '0.6rem', color: '#9ca3af', padding: '0.2rem' }}>C{c}</div>
            ))}
            {[5,4,3,2,1].map(l => (
              <>
                <div key={`l${l}`} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.6rem', color: '#9ca3af' }}>L{l}</div>
                {[1,2,3,4,5].map(c => {
                  const score = l * c
                  const risksHere = risks.filter(r => r.likelihood === l && r.consequence === c)
                  return (
                    <div key={`${l}-${c}`} style={{
                      background: `${getRiskColor(score)}22`, border: `1px solid ${getRiskColor(score)}40`,
                      borderRadius: '3px', padding: '0.2rem', minHeight: '28px', textAlign: 'center',
                      fontSize: '0.55rem', color: getRiskColor(score),
                    }}>
                      {risksHere.length > 0 && risksHere.map(r => (
                        <div key={r.id} title={r.title} style={{ fontWeight: 600 }}>{r.id}</div>
                      ))}
                    </div>
                  )
                })}
              </>
            ))}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#6b7280', marginBottom: '0.75rem' }}>
            L = Likelihood (1-5) | C = Consequence (1-5) | Score = L x C | Green ≤4 | Amber 5-9 | Orange 10-15 | Red 16-25
          </div>

          {/* Risk register table */}
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={th}>ID</th><th style={th}>Risk</th><th style={thC}>L</th><th style={thC}>C</th><th style={thC}>Score</th><th style={th}>Mitigation</th><th style={thC}>Status</th>
              </tr>
            </thead>
            <tbody>
              {risks.map(r => (
                <tr key={r.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: '0.65rem' }}>{r.id}</td>
                  <td style={{ ...td, fontWeight: 500 }}>{r.title}</td>
                  <td style={tdC}>{r.likelihood}</td>
                  <td style={tdC}>{r.consequence}</td>
                  <td style={{ ...tdC, color: getRiskColor(r.likelihood * r.consequence), fontWeight: 700 }}>{r.likelihood * r.consequence}</td>
                  <td style={{ ...td, fontSize: '0.68rem', color: '#9ca3af' }}>{r.mitigation}</td>
                  <td style={tdC}>
                    <span style={{ fontSize: '0.6rem', padding: '0.1rem 0.3rem', borderRadius: '3px', background: r.status === 'closed' ? '#10b98122' : r.status === 'mitigating' ? '#3b82f622' : '#f59e0b22', color: r.status === 'closed' ? '#10b981' : r.status === 'mitigating' ? '#3b82f6' : '#f59e0b' }}>{r.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Schedule / Milestones */}
      {activeTab === 'schedule' && (
        <div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            {milestones.map((m, i) => (
              <div key={m.id} style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.6rem',
                background: 'var(--bg-secondary, #1f2937)', borderRadius: '4px',
                borderLeft: `3px solid ${m.status === 'complete' ? '#10b981' : m.status === 'in_progress' ? '#3b82f6' : '#374151'}`,
              }}>
                <span style={{ fontSize: '0.65rem', color: '#6b7280', fontFamily: 'monospace', width: '40px' }}>{m.id}</span>
                <span style={{ fontSize: '0.6rem', padding: '0.1rem 0.3rem', borderRadius: '3px', background: '#374151', color: '#9ca3af' }}>{m.phase}</span>
                <span style={{ flex: 1, fontSize: '0.78rem', fontWeight: 500 }}>{m.name}</span>
                <span style={{
                  fontSize: '0.6rem', padding: '0.1rem 0.3rem', borderRadius: '3px',
                  background: m.status === 'complete' ? '#10b98122' : m.status === 'in_progress' ? '#3b82f622' : '#37415180',
                  color: m.status === 'complete' ? '#10b981' : m.status === 'in_progress' ? '#3b82f6' : '#6b7280',
                }}>{m.status}</span>
              </div>
            ))}
          </div>
          <div style={{ fontSize: '0.68rem', color: '#6b7280', marginTop: '0.5rem' }}>
            Phase gates per ECSS-M-ST-10C / NASA NPR 7120.5. Edit dates and status to track progress.
          </div>
        </div>
      )}

      {/* WBS */}
      {activeTab === 'wbs' && (
        <div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={th}>WP</th><th style={th}>Name</th><th style={th}>Responsible</th><th style={thC}>Effort (h)</th><th style={th}>Phase</th><th style={thC}>Status</th>
              </tr>
            </thead>
            <tbody>
              {wbs.map(wp => (
                <tr key={wp.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: '0.65rem' }}>{wp.id}</td>
                  <td style={{ ...td, fontWeight: 500 }}>{wp.name}</td>
                  <td style={{ ...td, fontSize: '0.68rem', color: '#9ca3af' }}>{wp.responsible.replace(/_/g, ' ')}</td>
                  <td style={tdC}>{wp.effort_hours}</td>
                  <td style={{ ...td, fontSize: '0.68rem', color: '#6b7280' }}>{wp.phase}</td>
                  <td style={tdC}>
                    <span style={{ fontSize: '0.6rem', padding: '0.1rem 0.3rem', borderRadius: '3px', background: wp.status === 'complete' ? '#10b98122' : wp.status === 'in_progress' ? '#3b82f622' : '#37415180', color: wp.status === 'complete' ? '#10b981' : wp.status === 'in_progress' ? '#3b82f6' : '#6b7280' }}>{wp.status.replace(/_/g, ' ')}</span>
                  </td>
                </tr>
              ))}
              <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
                <td style={td}></td><td style={td}>Total</td><td style={td}></td>
                <td style={tdC}>{wbs.reduce((s, wp) => s + wp.effort_hours, 0)}</td>
                <td></td><td></td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
