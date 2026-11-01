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
import React, { useState, useCallback } from 'react'
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'

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
  inputs: string       // What inputs are needed
  work_content: string // What the work consists of
  outputs: string      // What outputs come from it
}


const getRiskColor = (score: number) => {
  if (score <= 4) return 'var(--status-ok)'
  if (score <= 9) return 'var(--status-caution)'
  if (score <= 15) return 'var(--status-caution)'
  return 'var(--status-alarm)'
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
  { id: 'WP-1.0', name: 'Programme Management', description: 'Project planning, reporting, reviews', responsible: 'project_manager', effort_hours: 200, status: 'in_progress', phase: 'All', start_date: '', end_date: '', depends_on: '', inputs: '', work_content: '', outputs: '' },
  { id: 'WP-2.0', name: 'Systems Engineering', description: 'Requirements, architecture, budgets, V&V', responsible: 'systems_engineer', effort_hours: 300, status: 'in_progress', phase: 'All', start_date: '', end_date: '', depends_on: '', inputs: '', work_content: '', outputs: '' },
  { id: 'WP-3.0', name: 'Payload Development', description: 'Instrument design, build, calibration', responsible: 'payload_lead', effort_hours: 400, status: 'not_started', phase: 'B-C', start_date: '', end_date: '', depends_on: 'WP-2.0', inputs: '', work_content: '', outputs: '' },
  { id: 'WP-4.0', name: 'Bus Procurement', description: 'COTS component procurement and acceptance', responsible: 'systems_engineer', effort_hours: 100, status: 'not_started', phase: 'C', start_date: '', end_date: '', depends_on: 'WP-2.0', inputs: '', work_content: '', outputs: '' },
  { id: 'WP-5.0', name: 'Integration & Test', description: 'Assembly, functional test, environmental test', responsible: 'structures_engineer', effort_hours: 250, status: 'not_started', phase: 'C-D', start_date: '', end_date: '', depends_on: 'WP-3.0', inputs: '', work_content: '', outputs: '' },
  { id: 'WP-6.0', name: 'Software Development', description: 'FSW, GSW, ops procedures', responsible: 'software_engineer', effort_hours: 350, status: 'not_started', phase: 'B-D', start_date: '', end_date: '', depends_on: 'WP-2.0', inputs: '', work_content: '', outputs: '' },
  { id: 'WP-7.0', name: 'Ground Segment', description: 'Station setup, MCS, data pipeline', responsible: 'ground_segment', effort_hours: 150, status: 'not_started', phase: 'C-D', start_date: '', end_date: '', depends_on: 'WP-2.0', inputs: '', work_content: '', outputs: '' },
  { id: 'WP-8.0', name: 'Launch Campaign', description: 'Launch procurement, integration, shipping', responsible: 'project_manager', effort_hours: 100, status: 'not_started', phase: 'D', start_date: '', end_date: '', depends_on: 'WP-5.0', inputs: '', work_content: '', outputs: '' },
  { id: 'WP-9.0', name: 'Operations', description: 'LEOP, commissioning, nominal ops', responsible: 'mission_ops', effort_hours: 500, status: 'not_started', phase: 'E', start_date: '', end_date: '', depends_on: 'WP-8.0', inputs: '', work_content: '', outputs: '' },
]

export function ProjectManagement() {
  const [activeTab, setActiveTab] = useState<PMTab>('wbs')
  const [risks, setRisks] = useState<Risk[]>(DEFAULT_RISKS)
  const [milestones, setMilestones] = useState<Milestone[]>(DEFAULT_MILESTONES)
  const [expandedWp, setExpandedWp] = useState<string | null>(null)

  // WBS persistence: initialize from designStore, fall back to defaults
  const storedWbs = useDesignStore(s => s.projectWbs)
  const setStoredWbs = useDesignStore(s => s.setProjectWbs)
  const [wbs, setWbsLocal] = useState<WorkPackage[]>(() => {
    if (storedWbs && storedWbs.length > 0) {
      return storedWbs as WorkPackage[]
    }
    return DEFAULT_WBS
  })

  // Wrap setWbs to also persist to designStore
  const setWbs: React.Dispatch<React.SetStateAction<WorkPackage[]>> = useCallback((action) => {
    setWbsLocal(prev => {
      const next = typeof action === 'function' ? action(prev) : action
      setStoredWbs(next)
      return next
    })
  }, [setStoredWbs])

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Project Management</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.5rem' }}>
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
            padding: '0.3rem 0.75rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
            background: activeTab === t.id ? 'var(--interactive)' : 'var(--bg-secondary, var(--surface-2))',
            color: activeTab === t.id ? 'white' : 'var(--text-2)',
            border: `1px solid ${activeTab === t.id ? 'var(--interactive)' : 'var(--line)'}`,
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
              <div key={c} style={{ textAlign: 'center', fontSize: fs.label, color: 'var(--text-2)', padding: '0.2rem' }}>C{c}</div>
            ))}
            {[5,4,3,2,1].map(l => (
              <>
                <div key={`l${l}`} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: fs.label, color: 'var(--text-2)' }}>L{l}</div>
                {[1,2,3,4,5].map(c => {
                  const score = l * c
                  const risksHere = risks.filter(r => r.likelihood === l && r.consequence === c)
                  return (
                    <div key={`${l}-${c}`} style={{
                      background: `color-mix(in srgb, ${getRiskColor(score)} 13%, transparent)`, border: `1px solid color-mix(in srgb, ${getRiskColor(score)} 25%, transparent)`,
                      borderRadius: '3px', padding: '0.2rem', minHeight: '28px', textAlign: 'center',
                      fontSize: fs.label, color: getRiskColor(score),
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
          <div style={{ fontSize: fs.label, color: 'var(--text-3)', marginBottom: '0.75rem' }}>
            L = Likelihood (1-5) | C = Consequence (1-5) | Score = L x C | Green ≤4 | Amber 5-9 | Orange 10-15 | Red 16-25
          </div>

          {/* Risk register table */}
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
                <th style={th}>ID</th><th style={th}>Risk</th><th style={thC}>L</th><th style={thC}>C</th><th style={thC}>Score</th><th style={th}>Mitigation</th><th style={thC}>Status</th>
              </tr>
            </thead>
            <tbody>
              {risks.map(r => (
                <tr key={r.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: fs.label }}>{r.id}</td>
                  <td style={td}>
                    <input value={r.title} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, title: e.target.value } : rr))}
                      style={{ background: 'transparent', border: 'none', color: 'var(--text)', width: '100%', fontSize: fs.label, fontWeight: 500 }} />
                  </td>
                  <td style={tdC}>
                    <input type="number" min={1} max={5} value={r.likelihood} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, likelihood: Number(e.target.value) } : rr))}
                      style={{ width: '30px', textAlign: 'center', background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: 'var(--text)', fontSize: fs.label }} />
                  </td>
                  <td style={tdC}>
                    <input type="number" min={1} max={5} value={r.consequence} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, consequence: Number(e.target.value) } : rr))}
                      style={{ width: '30px', textAlign: 'center', background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: 'var(--text)', fontSize: fs.label }} />
                  </td>
                  <td style={{ ...tdC, color: getRiskColor(r.likelihood * r.consequence), fontWeight: 700 }}>{r.likelihood * r.consequence}</td>
                  <td style={td}>
                    <input value={r.mitigation} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, mitigation: e.target.value } : rr))}
                      style={{ background: 'transparent', border: 'none', color: 'var(--text-2)', width: '100%', fontSize: fs.label }} />
                  </td>
                  <td style={tdC}>
                    <select value={r.status} onChange={e => setRisks(prev => prev.map(rr => rr.id === r.id ? { ...rr, status: e.target.value as Risk['status'] } : rr))}
                      style={{ background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: r.status === 'closed' ? 'var(--status-ok)' : r.status === 'mitigating' ? 'var(--interactive)' : 'var(--status-caution)', fontSize: fs.label, padding: '0.1rem' }}>
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
          }])} className="btn btn-sm" style={{ marginTop: '0.5rem', fontSize: fs.label, background: 'var(--line)' }}>
            + Add Risk
          </button>
        </div>
      )}

      {/* Schedule / Gantt with editable dates + WBS items */}
      {activeTab === 'schedule' && (
        <div>
          <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.5rem' }}>
            Milestones + work packages. Set dependencies between items (FS = Finish-to-Start, FF, SS, SF).
          </p>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label, marginBottom: '0.5rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
                <th style={th}>ID</th><th style={th}>Item</th><th style={th}>Phase</th>
                <th style={th}>Date</th><th style={th}>Depends On</th><th style={thC}>Status</th><th style={th}>Gantt</th>
              </tr>
            </thead>
            <tbody>
              {milestones.map((m, i) => {
                const statusColor = m.status === 'complete' ? 'var(--status-ok)' : m.status === 'in_progress' ? 'var(--interactive)' : 'var(--text-3)'
                // Simple Gantt: position based on index
                const barLeft = (i / milestones.length) * 100
                return (
                  <tr key={m.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                    <td style={{ ...td, fontFamily: 'monospace', fontSize: fs.label }}>{m.id}</td>
                    <td style={{ ...td, fontWeight: 500 }}>{m.name}</td>
                    <td style={{ ...td, fontSize: fs.label, color: 'var(--text-2)' }}>{m.phase}</td>
                    <td style={td}>
                      <input type="date" value={m.date}
                        onChange={e => setMilestones(prev => prev.map(ms => ms.id === m.id ? { ...ms, date: e.target.value } : ms))}
                        style={{ background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: 'var(--text)', fontSize: fs.label, padding: '0.1rem 0.3rem' }} />
                    </td>
                    <td style={td}>
                      <select value={m.dependencies[0] || ''} onChange={e => setMilestones(prev => prev.map(ms => ms.id === m.id ? { ...ms, dependencies: e.target.value ? [e.target.value] : [] } : ms))}
                        style={{ background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: 'var(--text-3)', fontSize: fs.label, padding: '0.1rem', width: '70px' }}>
                        <option value="">None</option>
                        {milestones.filter(mm => mm.id !== m.id).map(mm => (
                          <option key={mm.id} value={mm.id}>{mm.id} (FS)</option>
                        ))}
                      </select>
                    </td>
                    <td style={tdC}>
                      <select value={m.status}
                        onChange={e => setMilestones(prev => prev.map(ms => ms.id === m.id ? { ...ms, status: e.target.value as Milestone['status'] } : ms))}
                        style={{ background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: statusColor, fontSize: fs.label, padding: '0.1rem' }}>
                        <option value="planned">Planned</option>
                        <option value="in_progress">In Progress</option>
                        <option value="complete">Complete</option>
                      </select>
                    </td>
                    <td style={{ ...td, width: '120px' }}>
                      <div style={{ position: 'relative', height: '12px', background: 'var(--surface-2)', borderRadius: '2px' }}>
                        <div style={{
                          position: 'absolute', left: `${barLeft}%`, top: '2px', width: '8px', height: '8px',
                          borderRadius: '50%', background: statusColor,
                        }} />
                        {i > 0 && (
                          <div style={{
                            position: 'absolute', left: `${((i - 1) / milestones.length) * 100}%`, top: '5px',
                            width: `${(1 / milestones.length) * 100}%`, height: '2px', background: `color-mix(in srgb, ${statusColor} 38%, transparent)`,
                          }} />
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
              {/* WBS work packages in schedule */}
              {wbs.map((wp) => (
                <tr key={`wp-${wp.id}`} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)', background: 'rgba(59,130,246,0.03)' }}>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: fs.label, color: 'var(--interactive)' }}>{wp.id}</td>
                  <td style={{ ...td, fontWeight: 500, color: 'var(--interactive)' }}>{wp.name}</td>
                  <td style={{ ...td, fontSize: fs.label, color: 'var(--text-2)' }}>{wp.phase}</td>
                  <td style={td}>—</td>
                  <td style={td}>—</td>
                  <td style={tdC}>
                    <span style={{ fontSize: fs.label, padding: '0.1rem 0.3rem', borderRadius: '3px', background: wp.status === 'complete' ? 'color-mix(in srgb, var(--status-ok) 13%, transparent)' : wp.status === 'in_progress' ? 'color-mix(in srgb, var(--interactive) 13%, transparent)' : 'color-mix(in srgb, var(--line) 50%, transparent)', color: wp.status === 'complete' ? 'var(--status-ok)' : wp.status === 'in_progress' ? 'var(--interactive)' : 'var(--text-3)' }}>
                      {wp.status.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td style={td}>
                    <div style={{ height: 12, background: 'var(--surface-2)', borderRadius: 2 }}>
                      <div style={{ height: '100%', width: `${wp.status === 'complete' ? 100 : wp.status === 'in_progress' ? 50 : 0}%`, background: 'color-mix(in srgb, var(--interactive) 25%, transparent)', borderRadius: 2 }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>
            Milestones (white) + WBS work packages (blue). Dependencies: FS = Finish-to-Start.
          </div>
        </div>
      )}

      {/* WBS — editable with add/remove */}
      {activeTab === 'wbs' && (
        <div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
                <th style={th}>WP</th><th style={th}>Name</th><th style={th}>Responsible</th><th style={thC}>Effort (h)</th><th style={th}>Phase</th><th style={th}>Start</th><th style={th}>End</th><th style={th}>Depends On</th><th style={thC}>Status</th><th style={thC}></th>
              </tr>
            </thead>
            <tbody>
              {wbs.map(wp => (<React.Fragment key={wp.id}>
                <tr style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: fs.label }}>{wp.id}</td>
                  <td style={td}>
                    <input className="input" value={wp.name}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, name: e.target.value } : w))}
                      style={{ width: '100%', fontSize: fs.label, background: 'transparent', border: 'none', color: 'var(--text)', fontWeight: 500 }} />
                  </td>
                  <td style={td}>
                    <input className="input" value={wp.responsible}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, responsible: e.target.value } : w))}
                      style={{ width: '100%', fontSize: fs.label, background: 'transparent', border: 'none', color: 'var(--text-2)' }} />
                  </td>
                  <td style={tdC}>
                    <input className="input" type="number" value={wp.effort_hours}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, effort_hours: Number(e.target.value) } : w))}
                      style={{ width: '55px', fontSize: fs.label, textAlign: 'center' }} />
                  </td>
                  <td style={td}>
                    <input className="input" value={wp.phase}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, phase: e.target.value } : w))}
                      style={{ width: '50px', fontSize: fs.label, background: 'transparent', border: 'none', color: 'var(--text-3)' }} />
                  </td>
                  <td style={td}>
                    <input type="date" value={wp.start_date}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, start_date: e.target.value } : w))}
                      style={{ background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: 'var(--text)', fontSize: fs.label, padding: '0.1rem' }} />
                  </td>
                  <td style={td}>
                    <input type="date" value={wp.end_date}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, end_date: e.target.value } : w))}
                      style={{ background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: 'var(--text)', fontSize: fs.label, padding: '0.1rem' }} />
                  </td>
                  <td style={td}>
                    <select value={wp.depends_on} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, depends_on: e.target.value } : w))}
                      style={{ background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: 'var(--text-3)', fontSize: fs.label, padding: '0.1rem', width: '65px' }}>
                      <option value="">None</option>
                      {wbs.filter(w => w.id !== wp.id).map(w => <option key={w.id} value={w.id}>{w.id}</option>)}
                    </select>
                  </td>
                  <td style={tdC}>
                    <select value={wp.status}
                      onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, status: e.target.value as WorkPackage['status'] } : w))}
                      style={{ background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--line)', borderRadius: '3px', color: wp.status === 'complete' ? 'var(--status-ok)' : wp.status === 'in_progress' ? 'var(--interactive)' : 'var(--text-3)', fontSize: fs.label, padding: '0.1rem' }}>
                      <option value="not_started">Not Started</option>
                      <option value="in_progress">In Progress</option>
                      <option value="complete">Complete</option>
                    </select>
                  </td>
                  <td style={tdC}>
                    <button onClick={() => setExpandedWp(expandedWp === wp.id ? null : wp.id)}
                      style={{ background: 'none', border: 'none', color: 'var(--interactive)', cursor: 'pointer', fontSize: fs.label, marginRight: '0.2rem' }}
                      title="Work Package Description">WPD</button>
                    <button onClick={() => setWbs(prev => prev.filter(w => w.id !== wp.id))}
                      style={{ background: 'none', border: 'none', color: 'var(--status-alarm)', cursor: 'pointer', fontSize: fs.label }}>×</button>
                  </td>
                </tr>
                {expandedWp === wp.id && (
                  <tr>
                    <td colSpan={10} style={{ padding: '0.5rem', background: 'var(--bg-primary, var(--surface-0))' }}>
                      <div style={{ fontSize: fs.label, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                        <label style={{ color: 'var(--text-2)' }}>Description:
                          <textarea className="input" value={wp.description} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, description: e.target.value } : w))}
                            rows={2} style={{ width: '100%', fontSize: fs.label, resize: 'vertical' }} placeholder="What this work package delivers..." />
                        </label>
                        <label style={{ color: 'var(--text-2)' }}>People / Skills:
                          <input className="input" value={(wp as any).people || ''} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, people: e.target.value } as any : w))}
                            style={{ width: '100%', fontSize: fs.label }} placeholder="e.g., 2 × SE, 1 × thermal" />
                        </label>
                      </div>
                      <div style={{ fontSize: fs.label, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginTop: '0.5rem' }}>
                        <label style={{ color: 'var(--text-2)' }}>Inputs Required:
                          <textarea className="input" value={wp.inputs || ''} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, inputs: e.target.value } : w))}
                            rows={3} style={{ width: '100%', fontSize: fs.label, resize: 'vertical' }} placeholder="What needs to be in place before this WP starts (e.g., requirements baseline, architecture decisions, approved budgets)" />
                        </label>
                        <label style={{ color: 'var(--text-2)' }}>Work Activities:
                          <textarea className="input" value={wp.work_content || ''} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, work_content: e.target.value } : w))}
                            rows={3} style={{ width: '100%', fontSize: fs.label, resize: 'vertical' }} placeholder="What the WP consists of (e.g., detailed design, analysis, fabrication, coding, testing)" />
                        </label>
                        <label style={{ color: 'var(--text-2)' }}>Deliverables / Outputs:
                          <textarea className="input" value={wp.outputs || ''} onChange={e => setWbs(prev => prev.map(w => w.id === wp.id ? { ...w, outputs: e.target.value } : w))}
                            rows={3} style={{ width: '100%', fontSize: fs.label, resize: 'vertical' }} placeholder="What comes out of this WP (e.g., test report, flight model, procedures, data products)" />
                        </label>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>))}
              <tr style={{ borderTop: '2px solid var(--line)', fontWeight: 700 }}>
                <td style={td}></td><td style={td}>Total</td><td style={td}></td>
                <td style={tdC}>{wbs.reduce((s, wp) => s + wp.effort_hours, 0)}</td>
                <td></td><td></td><td></td><td></td><td></td><td></td>
              </tr>
            </tbody>
          </table>
          <button onClick={() => {
            const id = `WP-${wbs.length + 1}.0`
            setWbs(prev => [...prev, { id, name: 'New Work Package', description: '', responsible: 'systems_engineer', effort_hours: 0, status: 'not_started' as const, phase: '', start_date: '', end_date: '', depends_on: '', inputs: '', work_content: '', outputs: '' }])
          }} className="btn btn-sm" style={{ marginTop: '0.5rem', fontSize: fs.label, background: 'var(--line)' }}>
            + Add Work Package
          </button>
        </div>
      )}
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
