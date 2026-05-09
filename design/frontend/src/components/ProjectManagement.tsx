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
import React, { useState } from 'react'

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
  start_date: string  // ISO date
  end_date: string    // ISO date
  depends_on: string  // WP or milestone ID
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
  { id: 'WP-1.0', name: 'Programme Management', description: 'Project planning, reporting, reviews', responsible: 'project_manager', effort_hours: 200, status: 'in_progress', phase: 'All', start_date: '', end_date: '', depends_on: '' },
  { id: 'WP-2.0', name: 'Systems Engineering', description: 'Requirements, architecture, budgets, V&V', responsible: 'systems_engineer', effort_hours: 300, status: 'in_progress', phase: 'All', start_date: '', end_date: '', depends_on: '' },
  { id: 'WP-3.0', name: 'Payload Development', description: 'Instrument design, build, calibration', responsible: 'payload_lead', effort_hours: 400, status: 'not_started', phase: 'B-C', start_date: '', end_date: '', depends_on: 'WP-2.0' },
  { id: 'WP-4.0', name: 'Bus Procurement', description: 'COTS component procurement and acceptance', responsible: 'systems_engineer', effort_hours: 100, status: 'not_started', phase: 'C', start_date: '', end_date: '', depends_on: 'WP-2.0' },
  { id: 'WP-5.0', name: 'Integration & Test', description: 'Assembly, functional test, environmental test', responsible: 'structures_engineer', effort_hours: 250, status: 'not_started', phase: 'C-D', start_date: '', end_date: '', depends_on: 'WP-3.0' },
  { id: 'WP-6.0', name: 'Software Development', description: 'FSW, GSW, ops procedures', responsible: 'software_engineer', effort_hours: 350, status: 'not_started', phase: 'B-D', start_date: '', end_date: '', depends_on: 'WP-2.0' },
  { id: 'WP-7.0', name: 'Ground Segment', description: 'Station setup, MCS, data pipeline', responsible: 'ground_segment', effort_hours: 150, status: 'not_started', phase: 'C-D', start_date: '', end_date: '', depends_on: 'WP-2.0' },
  { id: 'WP-8.0', name: 'Launch Campaign', description: 'Launch procurement, integration, shipping', responsible: 'project_manager', effort_hours: 100, status: 'not_started', phase: 'D', start_date: '', end_date: '', depends_on: 'WP-5.0' },
  { id: 'WP-9.0', name: 'Operations', description: 'LEOP, commissioning, nominal ops', responsible: 'mission_ops', effort_hours: 500, status: 'not_started', phase: 'E', start_date: '', end_date: '', depends_on: 'WP-8.0' },
]

export function ProjectManagement() {
  const [activeTab, setActiveTab] = useState<PMTab>('wbs')
  const [risks, setRisks] = useState<Risk[]>(DEFAULT_RISKS)
  const [milestones, setMilestones] = useState<Milestone[]>(DEFAULT_MILESTONES)
  const [wbs, setWbs] = useState<WorkPackage[]>(DEFAULT_WBS)
  const [expandedWp, setExpandedWp] = useState<string | null>(null)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Project Management</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Risk register (ECSS-M-ST-80C), schedule milestones, and work breakdown structure.
      </p>

      {/* Tab selector */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '1rem' }}>
        {[
          { id: 'wbs' as PMTab, label: 'WBS' },
          { id: 'schedule' as PMTab, label: 'Schedule' },
          { id: 'risk' as PMTab, label: 'Risk Matrix' },
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
                  <td style={td}>
                    <input value={r.title} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, title: e.target.value } : rr))}
                      style={{ background: 'transparent', border: 'none', color: '#d1d5db', width: '100%', fontSize: '0.72rem', fontWeight: 500 }} />
                  </td>
                  <td style={tdC}>
                    <input type="number" min={1} max={5} value={r.likelihood} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, likelihood: Number(e.target.value) } : rr))}
                      style={{ width: '30px', textAlign: 'center', background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db', fontSize: '0.72rem' }} />
                  </td>
                  <td style={tdC}>
                    <input type="number" min={1} max={5} value={r.consequence} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, consequence: Number(e.target.value) } : rr))}
                      style={{ width: '30px', textAlign: 'center', background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db', fontSize: '0.72rem' }} />
                  </td>
                  <td style={{ ...tdC, color: getRiskColor(r.likelihood * r.consequence), fontWeight: 700 }}>{r.likelihood * r.consequence}</td>
                  <td style={td}>
                    <input value={r.mitigation} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, mitigation: e.target.value } : rr))}
                      style={{ background: 'transparent', border: 'none', color: '#9ca3af', width: '100%', fontSize: '0.68rem' }} />
                  </td>
                  <td style={tdC}>
                    <select value={r.status} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, status: e.target.value as Risk['status'] } : rr))}
                      style={{ background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: r.status === 'closed' ? '#10b981' : r.status === 'mitigating' ? '#3b82f6' : '#f59e0b', fontSize: '0.6rem', padding: '0.1rem' }}>
                      <option value="open">Open</option>
                      <option value="mitigating">Mitigating</option>
                      <option value="accepted">Accepted</option>
                      <option value="closed">Closed</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={() => setRisks(prev => [...prev, {
            id: `R-${String(prev.length + 1).padStart(3, '0')}`, title: 'New risk', description: '',
            likelihood: 2, consequence: 2, category: 'technical', owner: 'systems_engineer',
            mitigation: '', status: 'open' as const,
          }])} className="btn btn-sm" style={{ marginTop: '0.5rem', fontSize: '0.7rem', background: '#374151' }}>
            + Add Risk
          </button>
        </div>
      )}

      {/* Schedule / Gantt with editable dates + WBS items */}
      {activeTab === 'schedule' && (
        <div>
          <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
            Milestones + work packages. Set dependencies between items (FS = Finish-to-Start, FF, SS, SF).
          </p>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem', marginBottom: '0.5rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={th}>ID</th><th style={th}>Item</th><th style={th}>Phase</th>
                <th style={th}>Date</th><th style={th}>Depends On</th><th style={thC}>Status</th><th style={th}>Gantt</th>
              </tr>
            </thead>
            <tbody>
              {milestones.map((m, i) => {
                const statusColor = m.status === 'complete' ? '#10b981' : m.status === 'in_progress' ? '#3b82f6' : '#6b7280'
                // Simple Gantt: position based on index
                const barLeft = (i / milestones.length) * 100
                return (
                  <tr key={m.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ ...td, fontFamily: 'monospace', fontSize: '0.65rem' }}>{m.id}</td>
                    <td style={{ ...td, fontWeight: 500 }}>{m.name}</td>
                    <td style={{ ...td, fontSize: '0.65rem', color: '#9ca3af' }}>{m.phase}</td>
                    <td style={td}>
                      <input type="date" value={m.date}
                        onChange={e => setMilestones(prev => prev.map(ms => ms.id === m.id ? { ...ms, date: e.target.value } : ms))}
                        style={{ background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db', fontSize: '0.68rem', padding: '0.1rem 0.3rem' }} />
                    </td>
                    <td style={td}>
                      <select value={m.dependencies[0] || ''} onChange={e => setMilestones(prev => prev.map(ms => ms.id === m.id ? { ...ms, dependencies: e.target.value ? [e.target.value] : [] } : ms))}
                        style={{ background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: '#6b7280', fontSize: '0.6rem', padding: '0.1rem', width: '70px' }}>
                        <option value="">None</option>
                        {milestones.filter(mm => mm.id !== m.id).map(mm => (
                          <option key={mm.id} value={mm.id}>{mm.id} (FS)</option>
                        ))}
                      </select>
                    </td>
                    <td style={tdC}>
                      <select value={m.status}
                        onChange={e => setMilestones(prev => prev.map(ms => ms.id === m.id ? { ...ms, status: e.target.value as Milestone['status'] } : ms))}
                        style={{ background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: statusColor, fontSize: '0.65rem', padding: '0.1rem' }}>
                        <option value="planned">Planned</option>
                        <option value="in_progress">In Progress</option>
                        <option value="complete">Complete</option>
                      </select>
                    </td>
                    <td style={{ ...td, width: '120px' }}>
                      <div style={{ position: 'relative', height: '12px', background: '#1f2937', borderRadius: '2px' }}>
                        <div style={{
                          position: 'absolute', left: `${barLeft}%`, top: '2px', width: '8px', height: '8px',
                          borderRadius: '50%', background: statusColor,
                        }} />
                        {i > 0 && (
                          <div style={{
                            position: 'absolute', left: `${((i - 1) / milestones.length) * 100}%`, top: '5px',
                            width: `${(1 / milestones.length) * 100}%`, height: '2px', background: `${statusColor}60`,
                          }} />
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
              {/* WBS work packages in schedule */}
              {wbs.map((wp, i) => (
                <tr key={`wp-${wp.id}`} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(59,130,246,0.03)' }}>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: '0.65rem', color: '#3b82f6' }}>{wp.id}</td>
                  <td style={{ ...td, fontWeight: 500, color: '#93c5fd' }}>{wp.name}</td>
                  <td style={{ ...td, fontSize: '0.65rem', color: '#9ca3af' }}>{wp.phase}</td>
                  <td style={td}>—</td>
                  <td style={td}>—</td>
                  <td style={tdC}>
                    <span style={{ fontSize: '0.6rem', padding: '0.1rem 0.3rem', borderRadius: '3px', background: wp.status === 'complete' ? '#10b98122' : wp.status === 'in_progress' ? '#3b82f622' : '#37415180', color: wp.status === 'complete' ? '#10b981' : wp.status === 'in_progress' ? '#3b82f6' : '#6b7280' }}>
                      {wp.status.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td style={td}>
                    <div style={{ height: 12, background: '#1f2937', borderRadius: 2 }}>
                      <div style={{ height: '100%', width: `${wp.status === 'complete' ? 100 : wp.status === 'in_progress' ? 50 : 0}%`, background: '#3b82f640', borderRadius: 2 }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ fontSize: '0.68rem', color: '#6b7280' }}>
            Milestones (white) + WBS work packages (blue). Dependencies: FS = Finish-to-Start.
          </div>
        </div>
      )}

      {/* WBS — editable with add/remove */}
      {activeTab === 'wbs' && (
        <div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={th}>WP</th><th style={th}>Name</th><th style={th}>Responsible</th><th style={thC}>Effort (h)</th><th style={th}>Phase</th><th style={th}>Start</th><th style={th}>End</th><th style={th}>Depends On</th><th style={thC}>Status</th><th style={thC}></th>
              </tr>
            </thead>
            <tbody>
              {wbs.map(wp => (<React.Fragment key={wp.id}>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: '0.65rem' }}>{wp.id}</td>
                  <td style={td}>
                    <input className="input" value={wp.name}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, name: e.target.value } : w))}
                      style={{ width: '100%', fontSize: '0.72rem', background: 'transparent', border: 'none', color: '#d1d5db', fontWeight: 500 }} />
                  </td>
                  <td style={td}>
                    <input className="input" value={wp.responsible}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, responsible: e.target.value } : w))}
                      style={{ width: '100%', fontSize: '0.68rem', background: 'transparent', border: 'none', color: '#9ca3af' }} />
                  </td>
                  <td style={tdC}>
                    <input className="input" type="number" value={wp.effort_hours}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, effort_hours: Number(e.target.value) } : w))}
                      style={{ width: '55px', fontSize: '0.72rem', textAlign: 'center' }} />
                  </td>
                  <td style={td}>
                    <input className="input" value={wp.phase}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, phase: e.target.value } : w))}
                      style={{ width: '50px', fontSize: '0.68rem', background: 'transparent', border: 'none', color: '#6b7280' }} />
                  </td>
                  <td style={td}>
                    <input type="date" value={wp.start_date}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, start_date: e.target.value } : w))}
                      style={{ background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db', fontSize: '0.62rem', padding: '0.1rem' }} />
                  </td>
                  <td style={td}>
                    <input type="date" value={wp.end_date}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, end_date: e.target.value } : w))}
                      style={{ background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db', fontSize: '0.62rem', padding: '0.1rem' }} />
                  </td>
                  <td style={td}>
                    <select value={wp.depends_on} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, depends_on: e.target.value } : w))}
                      style={{ background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: '#6b7280', fontSize: '0.6rem', padding: '0.1rem', width: '65px' }}>
                      <option value="">None</option>
                      {wbs.filter(w => w.id !== wp.id).map(w => <option key={w.id} value={w.id}>{w.id}</option>)}
                    </select>
                  </td>
                  <td style={tdC}>
                    <select value={wp.status}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, status: e.target.value as WorkPackage['status'] } : w))}
                      style={{ background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: wp.status === 'complete' ? '#10b981' : wp.status === 'in_progress' ? '#3b82f6' : '#6b7280', fontSize: '0.6rem', padding: '0.1rem' }}>
                      <option value="not_started">Not Started</option>
                      <option value="in_progress">In Progress</option>
                      <option value="complete">Complete</option>
                    </select>
                  </td>
                  <td style={tdC}>
                    <button onClick={() => setExpandedWp(expandedWp === wp.id ? null : wp.id)}
                      style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: '0.6rem', marginRight: '0.2rem' }}
                      title="Work Package Description">WPD</button>
                    <button onClick={() => setWbs(prev => prev.filter(w => w.id !== wp.id))}
                      style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.7rem' }}>×</button>
                  </td>
                </tr>
                {expandedWp === wp.id && (
                  <tr>
                    <td colSpan={7} style={{ padding: '0.5rem', background: 'var(--bg-primary, #0a0e1a)' }}>
                      <div style={{ fontSize: '0.72rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                        <label style={{ color: '#9ca3af' }}>Description:
                          <textarea className="input" value={wp.description} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, description: e.target.value } : w))}
                            rows={2} style={{ width: '100%', fontSize: '0.72rem', resize: 'vertical' }} placeholder="What this work package delivers..." />
                        </label>
                        <label style={{ color: '#9ca3af' }}>People / Skills:
                          <input className="input" value={(wp as any).people || ''} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, people: e.target.value } as any : w))}
                            style={{ width: '100%', fontSize: '0.72rem' }} placeholder="e.g., 2 × SE, 1 × thermal" />
                        </label>
                        <label style={{ color: '#9ca3af' }}>Inputs:
                          <input className="input" value={(wp as any).inputs || ''} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, inputs: e.target.value } as any : w))}
                            style={{ width: '100%', fontSize: '0.72rem' }} placeholder="e.g., Requirements baseline, architecture decisions" />
                        </label>
                        <label style={{ color: '#9ca3af' }}>Outputs / Deliverables:
                          <input className="input" value={(wp as any).outputs || ''} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, outputs: e.target.value } as any : w))}
                            style={{ width: '100%', fontSize: '0.72rem' }} placeholder="e.g., Test report, flight model, procedures" />
                        </label>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>))}
              <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
                <td style={td}></td><td style={td}>Total</td><td style={td}></td>
                <td style={tdC}>{wbs.reduce((s, wp) => s + wp.effort_hours, 0)}</td>
                <td></td><td></td><td></td><td></td><td></td><td></td>
              </tr>
            </tbody>
          </table>
          <button onClick={() => {
            const id = `WP-${wbs.length + 1}.0`
            setWbs(prev => [...prev, { id, name: 'New Work Package', description: '', responsible: 'systems_engineer', effort_hours: 0, status: 'not_started' as const, phase: '', start_date: '', end_date: '', depends_on: '' }])
          }} className="btn btn-sm" style={{ marginTop: '0.5rem', fontSize: '0.7rem', background: '#374151' }}>
            + Add Work Package
          </button>
        </div>
      )}
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
