/**
 * VVPanel — Verification & Validation view for Level 4.
 *
 * Five sections:
 * 1. Budget Rollup: mass/power/cost hierarchy
 * 2. Requirement Traceability: derivation chains, orphans, SMART status
 * 3. Review Gate Checklist: MCR/SRR/PDR/CDR gate evaluation (from gate_evaluator)
 * 4. FMECA Summary: failure mode analysis results
 * 5. Budget Traceability: trace budget exceedance to stakeholder impact
 */
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'

const API = '/api'

const STATUS_COLORS: Record<string, string> = {
  green: 'var(--success)', amber: 'var(--warning)', red: 'var(--danger)', undefined: 'var(--text-secondary)',
  pass: 'var(--success)', fail: 'var(--danger)', manual: 'var(--warning)', not_evaluated: 'var(--text-secondary)',
}

const REQ_STATUS_COLORS: Record<string, string> = {
  draft: 'var(--text-secondary)', approved: 'var(--accent)', verified: 'var(--success)', violated: 'var(--danger)',
}

export function VVPanel() {
  const studyId = useUIStore(s => s.studyId)
  const [activeSection, setActiveSection] = useState<'budget' | 'reqs' | 'gates' | 'fmeca' | 'trace' | 'risks' | 'bom' | 'maturity'>('budget')

  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })

  const { data: allRequirements = [] } = useQuery({
    queryKey: ['requirements', studyId],
    queryFn: () => fetch(`${API}/requirements/tree?study_id=${studyId}`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })

  const sections = [
    { id: 'budget' as const, label: 'Budget Rollup', color: '#f59e0b' },
    { id: 'reqs' as const, label: 'Requirements', color: '#8b5cf6' },
    { id: 'gates' as const, label: 'Review Gates', color: '#3b82f6' },
    { id: 'fmeca' as const, label: 'FMECA', color: '#ef4444' },
    { id: 'trace' as const, label: 'Traceability', color: '#10b981' },
    { id: 'risks' as const, label: 'Risk Register', color: '#f43f5e' },
    { id: 'bom' as const, label: 'BOM', color: '#06b6d4' },
    { id: 'maturity' as const, label: 'Maturity', color: '#a855f7' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Section tabs */}
      <div style={{ display: 'flex', gap: '1px', padding: '0.3rem 1rem', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
        {sections.map(s => (
          <button key={s.id} onClick={() => setActiveSection(s.id)} style={{
            padding: '0.3rem 0.8rem', fontSize: '0.72rem', fontWeight: 600, borderRadius: '3px 3px 0 0',
            background: activeSection === s.id ? 'var(--bg-primary)' : 'transparent',
            color: activeSection === s.id ? s.color : 'var(--text-secondary)',
            border: 'none', cursor: 'pointer',
            borderBottom: activeSection === s.id ? `2px solid ${s.color}` : '2px solid transparent',
          }}>
            {s.label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
        {activeSection === 'budget' && <BudgetRollup elements={allElements} />}
        {activeSection === 'reqs' && <RequirementTraceability requirements={allRequirements} elements={allElements} studyId={studyId} />}
        {activeSection === 'gates' && <ReviewGates studyId={studyId} />}
        {activeSection === 'fmeca' && <FMECASummary studyId={studyId} />}
        {activeSection === 'trace' && <BudgetTraceability studyId={studyId} />}
        {activeSection === 'risks' && <RiskRegister studyId={studyId} />}
        {activeSection === 'bom' && <BOMSection elements={allElements} />}
        {activeSection === 'maturity' && <MaturitySection elements={allElements} />}
      </div>
    </div>
  )
}

// ─── Budget Rollup ───

function BudgetRollup({ elements }: { elements: any[] }) {
  return (
    <div>
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>Budget Rollup — All Elements</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            <th style={thL}>Element</th><th style={thL}>Type</th>
            <th style={thR}>Mass (kg)</th><th style={thR}>Power (W)</th><th style={thR}>Cost (kEUR)</th><th style={thR}>Qty</th>
          </tr>
        </thead>
        <tbody>
          {elements.map((el: any) => {
            const depth = getDepth(el, elements)
            return (
              <tr key={el.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <td style={{ padding: '0.2rem 0.4rem', paddingLeft: `${0.4 + depth * 1}rem`, fontWeight: depth < 2 ? 600 : 400 }}>{el.name}</td>
                <td style={{ padding: '0.2rem 0.4rem' }}>
                  <span style={{ fontSize: '0.55rem', padding: '0.05rem 0.2rem', borderRadius: '2px', background: 'rgba(59,130,246,0.1)', color: 'var(--accent)', textTransform: 'uppercase' }}>
                    {el.subsystem_domain || el.element_type}
                  </span>
                </td>
                <td style={{ ...tdR, fontFamily: 'monospace' }}>{el.mass_kg != null ? (el.mass_kg * (el.quantity || 1)).toFixed(2) : '—'}</td>
                <td style={{ ...tdR, fontFamily: 'monospace' }}>{el.power_avg_w != null ? (el.power_avg_w * (el.quantity || 1)).toFixed(1) : '—'}</td>
                <td style={{ ...tdR, fontFamily: 'monospace' }}>{el.cost_recurring_keur != null ? (el.cost_recurring_keur * (el.quantity || 1)).toFixed(0) : '—'}</td>
                <td style={{ ...tdR, color: 'var(--text-secondary)' }}>{(el.quantity || 1) > 1 ? `×${el.quantity}` : ''}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ─── Requirement Traceability ───

function RequirementTraceability({ requirements, elements, studyId }: { requirements: any[]; elements: any[]; studyId: string | null }) {
  const nameOf = (id: string) => elements.find((e: any) => e.id === id)?.name || '—'

  // Compute traceability stats
  const stats = useMemo(() => {
    const total = requirements.length
    const byStatus: Record<string, number> = {}
    const byLevel: Record<string, number> = {}
    let orphans = 0
    let withElement = 0
    for (const r of requirements) {
      byStatus[r.status] = (byStatus[r.status] || 0) + 1
      byLevel[r.level] = (byLevel[r.level] || 0) + 1
      if (r.level !== 'mission' && !r.derived_from_requirement_id && !r.parent_id) orphans++
      if (r.element_id) withElement++
    }
    return { total, byStatus, byLevel, orphans, withElement, coverage: total > 0 ? (withElement / total * 100) : 0 }
  }, [requirements])

  return (
    <div>
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Requirement Traceability</h3>

      {/* Stats */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem', fontSize: '0.68rem', flexWrap: 'wrap' }}>
        <span>Total: <b>{stats.total}</b></span>
        {Object.entries(stats.byStatus).map(([s, n]) => (
          <span key={s} style={{ color: REQ_STATUS_COLORS[s] || 'var(--text-secondary)' }}>{s}: <b>{n}</b></span>
        ))}
        <span style={{ color: 'var(--border)' }}>|</span>
        {Object.entries(stats.byLevel).map(([l, n]) => (
          <span key={l} style={{ color: 'var(--text-secondary)' }}>{l}: <b>{n}</b></span>
        ))}
        <span style={{ color: 'var(--border)' }}>|</span>
        <span style={{ color: stats.orphans > 0 ? 'var(--warning)' : 'var(--success)' }}>Orphans: <b>{stats.orphans}</b></span>
        <span>Element coverage: <b>{stats.coverage.toFixed(0)}%</b></span>
      </div>

      {/* Table */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            <th style={thL}>Code</th><th style={thL}>Level</th><th style={thL}>Element</th>
            <th style={{ ...thL, width: '35%' }}>Text</th><th style={thC}>V&V</th><th style={thC}>Status</th><th style={thC}>Derived</th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((req: any) => {
            const isOrphan = req.level !== 'mission' && !req.derived_from_requirement_id && !req.parent_id
            return (
              <tr key={req.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', background: isOrphan ? 'rgba(245,158,11,0.05)' : undefined }}>
                <td style={{ padding: '0.2rem 0.4rem', fontFamily: 'monospace', color: 'var(--accent)', fontSize: '0.65rem' }}>{req.code}</td>
                <td style={{ padding: '0.2rem 0.4rem' }}>
                  <span style={{ fontSize: '0.5rem', padding: '0.05rem 0.2rem', borderRadius: '2px', background: 'rgba(59,130,246,0.1)', color: 'var(--accent)', textTransform: 'uppercase' }}>{req.level}</span>
                </td>
                <td style={{ padding: '0.2rem 0.4rem', fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{req.element_id ? nameOf(req.element_id) : '—'}</td>
                <td style={{ padding: '0.2rem 0.4rem', fontSize: '0.68rem' }}>{req.text}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', color: 'var(--success)', fontWeight: 600, fontSize: '0.6rem' }}>{req.verification_method || '—'}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center' }}>
                  <span style={{ fontSize: '0.55rem', padding: '0.05rem 0.2rem', borderRadius: '2px', background: `${REQ_STATUS_COLORS[req.status]}20`, color: REQ_STATUS_COLORS[req.status], fontWeight: 600 }}>{req.status}</span>
                </td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', fontSize: '0.55rem' }}>
                  {req.derived_from_requirement_id ? (
                    <span style={{ color: 'var(--success)' }}>✓</span>
                  ) : isOrphan ? (
                    <span style={{ color: 'var(--warning)' }} title="Not derived from parent requirement">orphan</span>
                  ) : (
                    <span style={{ color: 'var(--text-secondary)' }}>—</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ─── Review Gates ───

function ReviewGates({ studyId }: { studyId: string | null }) {
  const gates = ['mcr', 'srr', 'pdr', 'cdr']
  const [activeGate, setActiveGate] = useState('srr')

  const { data: gateResult, isLoading } = useQuery({
    queryKey: ['gate-evaluate', studyId, activeGate],
    queryFn: () => fetch(`${API}/ecss/gate-evaluate/${studyId}/${activeGate}`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })

  return (
    <div>
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Review Gate Evaluation</h3>

      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.5rem' }}>
        {gates.map(g => (
          <button key={g} onClick={() => setActiveGate(g)} style={{
            padding: '0.3rem 0.8rem', fontSize: '0.72rem', fontWeight: 700, borderRadius: '4px',
            background: activeGate === g ? 'var(--accent)' : 'var(--bg-card)',
            color: activeGate === g ? 'white' : 'var(--text-secondary)',
            border: 'none', cursor: 'pointer', textTransform: 'uppercase',
          }}>
            {g}
          </button>
        ))}
      </div>

      {isLoading && <div style={{ color: 'var(--text-secondary)' }}>Evaluating...</div>}

      {gateResult && (
        <div>
          {/* Summary */}
          <div style={{
            display: 'flex', gap: '0.75rem', marginBottom: '0.5rem', padding: '0.4rem 0.5rem',
            background: gateResult.ready ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
            borderRadius: '4px', fontSize: '0.72rem',
          }}>
            <span style={{ fontWeight: 700, color: gateResult.ready ? 'var(--success)' : 'var(--danger)' }}>
              {gateResult.ready ? 'READY' : 'NOT READY'}
            </span>
            {gateResult.summary && (
              <>
                <span style={{ color: 'var(--success)' }}>Pass: {gateResult.summary.pass}</span>
                <span style={{ color: 'var(--danger)' }}>Fail: {gateResult.summary.fail}</span>
                <span style={{ color: 'var(--warning)' }}>Manual: {gateResult.summary.manual}</span>
              </>
            )}
          </div>

          {/* Criteria list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            {(gateResult.criteria || []).map((c: any, i: number) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.25rem 0.4rem',
                background: 'var(--bg-card)', borderRadius: '3px', fontSize: '0.68rem',
                borderLeft: `3px solid ${STATUS_COLORS[c.status] || 'var(--text-secondary)'}`,
              }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: STATUS_COLORS[c.status], flexShrink: 0 }} />
                <span style={{ flex: 1 }}>{c.question}</span>
                {c.evidence_found && <span style={{ fontSize: '0.55rem', color: 'var(--text-secondary)' }}>{c.evidence_found}</span>}
                <span style={{ fontSize: '0.55rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{c.priority}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── FMECA Summary ───

function FMECASummary({ studyId }: { studyId: string | null }) {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const runFMECA = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/fmeca/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ study_id: studyId, subsystems: ['power', 'aocs', 'ttc', 'obc', 'thermal', 'structure', 'propulsion'] }),
      })
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <div>
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Failure Mode Analysis (FMECA)</h3>
      <button onClick={runFMECA} disabled={loading} style={{
        padding: '0.3rem 0.6rem', fontSize: '0.68rem', fontWeight: 600, borderRadius: '4px',
        background: 'var(--accent)', color: 'white', border: 'none', cursor: 'pointer', marginBottom: '0.5rem',
      }}>
        {loading ? 'Analysing...' : 'Run FMECA'}
      </button>

      {result?.failure_modes && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.68rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={thL}>Subsystem</th><th style={thL}>Failure Mode</th><th style={thC}>Severity</th>
              <th style={thC}>Probability</th><th style={thC}>RPN</th><th style={thL}>Mitigation</th>
            </tr>
          </thead>
          <tbody>
            {result.failure_modes.slice(0, 20).map((fm: any, i: number) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <td style={{ padding: '0.2rem 0.4rem', fontWeight: 500 }}>{fm.subsystem}</td>
                <td style={{ padding: '0.2rem 0.4rem' }}>{fm.failure_mode || fm.description}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', color: (fm.severity || 0) > 7 ? 'var(--danger)' : 'var(--warning)' }}>{fm.severity}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center' }}>{fm.probability || fm.occurrence}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', fontWeight: 600, color: (fm.rpn || 0) > 100 ? 'var(--danger)' : 'var(--text-primary)' }}>{fm.rpn}</td>
                <td style={{ padding: '0.2rem 0.4rem', fontSize: '0.6rem', color: 'var(--text-secondary)' }}>{fm.mitigation || fm.recommended_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {result?.summary && (
        <div style={{ marginTop: '0.4rem', padding: '0.3rem 0.5rem', background: 'var(--bg-card)', borderRadius: '4px', fontSize: '0.68rem' }}>
          Total failure modes: <b>{result.summary.total || result.failure_modes?.length}</b>
          {result.summary.critical > 0 && <span style={{ color: 'var(--danger)', marginLeft: '0.5rem' }}>Critical: <b>{result.summary.critical}</b></span>}
        </div>
      )}
    </div>
  )
}

// ─── Budget Traceability ───

function BudgetTraceability({ studyId }: { studyId: string | null }) {
  const budgets = ['mass', 'power', 'cost', 'link', 'delta_v']
  const [activeBudget, setActiveBudget] = useState('mass')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const trace = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/traceability/${studyId}/${activeBudget}`)
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <div>
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Budget → Stakeholder Traceability</h3>

      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.4rem' }}>
        {budgets.map(b => (
          <button key={b} onClick={() => setActiveBudget(b)} style={{
            padding: '0.2rem 0.5rem', fontSize: '0.65rem', borderRadius: '3px',
            background: activeBudget === b ? 'var(--accent)' : 'var(--bg-card)',
            color: activeBudget === b ? 'white' : 'var(--text-secondary)',
            border: 'none', cursor: 'pointer',
          }}>
            {b}
          </button>
        ))}
        <button onClick={trace} disabled={loading} style={{
          padding: '0.2rem 0.5rem', fontSize: '0.65rem', fontWeight: 600, borderRadius: '3px',
          background: 'var(--success)', color: 'white', border: 'none', cursor: 'pointer', marginLeft: '0.3rem',
        }}>
          {loading ? '...' : 'Trace'}
        </button>
      </div>

      {result && (
        <div>
          {/* Trace chain */}
          {result.chain?.length > 0 && (
            <div style={{ marginBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Trace Chain:</div>
              {result.chain.map((link: any, i: number) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.2rem 0', fontSize: '0.68rem' }}>
                  <span style={{ fontSize: '0.5rem', padding: '0.05rem 0.2rem', borderRadius: '2px', background: 'rgba(59,130,246,0.1)', color: 'var(--accent)', textTransform: 'uppercase' }}>{link.level}</span>
                  <span>{link.text}</span>
                  {i < (result.chain?.length || 0) - 1 && <span style={{ color: 'var(--text-secondary)' }}>→</span>}
                </div>
              ))}
            </div>
          )}

          {/* Recovery options */}
          {result.recovery_options?.length > 0 && (
            <div>
              <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--warning)', marginBottom: '0.2rem' }}>Recovery Options:</div>
              {result.recovery_options.map((opt: any, i: number) => (
                <div key={i} style={{ padding: '0.25rem 0.4rem', background: 'var(--bg-card)', borderRadius: '3px', marginBottom: '0.2rem', fontSize: '0.68rem' }}>
                  <div style={{ fontWeight: 500 }}>{opt.description}</div>
                  <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>
                    Subsystem: {opt.subsystem} | Impact: {opt.impact} | Feasibility: {opt.feasibility}
                  </div>
                </div>
              ))}
            </div>
          )}

          {result.stakeholder_impact && (
            <div style={{ marginTop: '0.3rem', padding: '0.3rem', background: 'rgba(245,158,11,0.1)', borderRadius: '3px', fontSize: '0.68rem', color: 'var(--warning)' }}>
              Stakeholder impact: {result.stakeholder_impact}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Helpers ───

// ─── Risk Register ───

interface Risk {
  id: string; description: string; category: string
  likelihood: number; consequence: number; rpn: number
  mitigation: string; owner: string; status: string
}

const RISK_CATEGORIES = ['Technical', 'Schedule', 'Cost', 'Programmatic', 'Safety', 'Regulatory']
const L_LABELS = ['', 'Rare', 'Unlikely', 'Possible', 'Likely', 'Almost Certain']
const C_LABELS = ['', 'Negligible', 'Minor', 'Moderate', 'Major', 'Catastrophic']

function RiskRegister({ studyId }: { studyId: string | null }) {
  const storageKey = `spacecdf-risks-${studyId}`
  const loadRisks = (): Risk[] => { try { return JSON.parse(localStorage.getItem(storageKey) || '[]') } catch { return [] } }
  const [risks, setRisks] = useState<Risk[]>(loadRisks)
  const [showAdd, setShowAdd] = useState(false)
  const [newDesc, setNewDesc] = useState('')
  const [newCat, setNewCat] = useState('Technical')
  const [newL, setNewL] = useState(3)
  const [newC, setNewC] = useState(3)
  const [newMit, setNewMit] = useState('')
  const [newOwner, setNewOwner] = useState('')

  const save = (r: Risk[]) => { setRisks(r); localStorage.setItem(storageKey, JSON.stringify(r)) }

  const addRisk = () => {
    if (!newDesc) return
    const r: Risk = {
      id: `RSK-${String(risks.length + 1).padStart(3, '0')}`,
      description: newDesc, category: newCat,
      likelihood: newL, consequence: newC, rpn: newL * newC,
      mitigation: newMit, owner: newOwner, status: 'open',
    }
    save([...risks, r])
    setNewDesc(''); setNewMit(''); setNewOwner(''); setShowAdd(false)
  }

  const updateRisk = (idx: number, field: string, value: any) => {
    const updated = [...risks]
    ;(updated[idx] as any)[field] = value
    if (field === 'likelihood' || field === 'consequence') {
      updated[idx].rpn = updated[idx].likelihood * updated[idx].consequence
    }
    save(updated)
  }

  const riskColor = (rpn: number) => rpn >= 15 ? 'var(--danger)' : rpn >= 8 ? 'var(--warning)' : 'var(--success)'

  // Stats
  const critical = risks.filter(r => r.rpn >= 15).length
  const high = risks.filter(r => r.rpn >= 8 && r.rpn < 15).length
  const open = risks.filter(r => r.status === 'open').length

  return (
    <div>
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Risk Register</h3>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem', fontSize: '0.68rem' }}>
        <span>Total: <b>{risks.length}</b></span>
        <span style={{ color: 'var(--danger)' }}>Critical: <b>{critical}</b></span>
        <span style={{ color: 'var(--warning)' }}>High: <b>{high}</b></span>
        <span>Open: <b>{open}</b></span>
      </div>

      {/* Risk matrix heatmap (5×5) */}
      <div style={{ marginBottom: '0.5rem' }}>
        <div style={{ fontSize: '0.55rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Likelihood × Consequence Matrix:</div>
        <div style={{ display: 'grid', gridTemplateColumns: '40px repeat(5, 1fr)', gap: 1, fontSize: '0.5rem' }}>
          <div />
          {C_LABELS.slice(1).map(c => <div key={c} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '0.1rem' }}>{c}</div>)}
          {[5, 4, 3, 2, 1].map(l => (
            <>
              <div key={`l${l}`} style={{ textAlign: 'right', paddingRight: '0.2rem', color: 'var(--text-secondary)' }}>{L_LABELS[l]}</div>
              {[1, 2, 3, 4, 5].map(c => {
                const rpn = l * c
                const count = risks.filter(r => r.likelihood === l && r.consequence === c).length
                return (
                  <div key={`${l}-${c}`} style={{
                    textAlign: 'center', padding: '0.1rem', borderRadius: '2px',
                    background: rpn >= 15 ? 'rgba(239,68,68,0.3)' : rpn >= 8 ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.15)',
                    color: count > 0 ? 'var(--text-primary)' : 'var(--text-secondary)',
                    fontWeight: count > 0 ? 700 : 400,
                  }}>
                    {count > 0 ? count : rpn}
                  </div>
                )
              })}
            </>
          ))}
        </div>
      </div>

      {/* Risk table */}
      {risks.length > 0 && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.65rem', marginBottom: '0.5rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={thL}>ID</th><th style={thL}>Description</th><th style={thC}>Cat</th>
              <th style={thC}>L</th><th style={thC}>C</th><th style={thC}>RPN</th>
              <th style={thL}>Mitigation</th><th style={thL}>Owner</th><th style={thC}>Status</th>
              <th style={thC}></th>
            </tr>
          </thead>
          <tbody>
            {risks.map((r, i) => (
              <tr key={r.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <td style={{ padding: '0.2rem 0.3rem', fontFamily: 'monospace', color: riskColor(r.rpn) }}>{r.id}</td>
                <td style={{ padding: '0.2rem 0.3rem', maxWidth: 200 }}>{r.description}</td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center', fontSize: '0.55rem' }}>{r.category}</td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center' }}>
                  <select value={r.likelihood} onChange={e => updateRisk(i, 'likelihood', parseInt(e.target.value))}
                    style={{ width: 30, fontSize: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
                    {[1,2,3,4,5].map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                </td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center' }}>
                  <select value={r.consequence} onChange={e => updateRisk(i, 'consequence', parseInt(e.target.value))}
                    style={{ width: 30, fontSize: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
                    {[1,2,3,4,5].map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                </td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center', fontWeight: 700, color: riskColor(r.rpn) }}>{r.rpn}</td>
                <td style={{ padding: '0.2rem 0.3rem', fontSize: '0.6rem' }}>{r.mitigation}</td>
                <td style={{ padding: '0.2rem 0.3rem', fontSize: '0.6rem' }}>{r.owner}</td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center' }}>
                  <select value={r.status} onChange={e => updateRisk(i, 'status', e.target.value)}
                    style={{ fontSize: '0.55rem', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: r.status === 'closed' ? 'var(--success)' : 'var(--text-primary)' }}>
                    <option value="open">Open</option><option value="mitigating">Mitigating</option>
                    <option value="accepted">Accepted</option><option value="closed">Closed</option>
                  </select>
                </td>
                <td style={{ padding: '0.2rem' }}>
                  <button onClick={() => save(risks.filter((_, j) => j !== i))}
                    style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.7rem' }}>×</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Add risk form */}
      {showAdd ? (
        <div style={{ padding: '0.4rem', background: 'var(--bg-card)', borderRadius: '4px', border: '1px solid var(--danger)', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            <select value={newCat} onChange={e => setNewCat(e.target.value)}
              style={{ padding: '0.2rem', fontSize: '0.65rem', borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
              {RISK_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <input value={newDesc} onChange={e => setNewDesc(e.target.value)} placeholder="Risk description" autoFocus
              style={{ flex: 1, padding: '0.2rem 0.3rem', fontSize: '0.65rem', borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
          </div>
          <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', fontSize: '0.63rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>L:</span>
            <select value={newL} onChange={e => setNewL(parseInt(e.target.value))}
              style={{ width: 40, fontSize: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
              {[1,2,3,4,5].map(v => <option key={v} value={v}>{v} — {L_LABELS[v]}</option>)}
            </select>
            <span style={{ color: 'var(--text-secondary)' }}>C:</span>
            <select value={newC} onChange={e => setNewC(parseInt(e.target.value))}
              style={{ width: 40, fontSize: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
              {[1,2,3,4,5].map(v => <option key={v} value={v}>{v} — {C_LABELS[v]}</option>)}
            </select>
            <span style={{ fontWeight: 700, color: riskColor(newL * newC) }}>RPN: {newL * newC}</span>
          </div>
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            <input value={newMit} onChange={e => setNewMit(e.target.value)} placeholder="Mitigation action"
              style={{ flex: 1, padding: '0.2rem 0.3rem', fontSize: '0.65rem', borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
            <input value={newOwner} onChange={e => setNewOwner(e.target.value)} placeholder="Owner"
              style={{ width: 80, padding: '0.2rem 0.3rem', fontSize: '0.65rem', borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
          </div>
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            <button onClick={addRisk} disabled={!newDesc} style={{ padding: '0.2rem 0.5rem', fontSize: '0.65rem', fontWeight: 600, borderRadius: '3px', background: 'var(--danger)', color: 'white', border: 'none', cursor: 'pointer' }}>Add Risk</button>
            <button onClick={() => setShowAdd(false)} style={{ padding: '0.2rem 0.5rem', fontSize: '0.65rem', borderRadius: '3px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: 'none', cursor: 'pointer' }}>Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowAdd(true)} style={{ padding: '0.3rem 0.6rem', fontSize: '0.68rem', fontWeight: 600, borderRadius: '4px', background: 'var(--danger)', color: 'white', border: 'none', cursor: 'pointer' }}>
          + Add Risk
        </button>
      )}
    </div>
  )
}

// ─── BOM Section ───

function BOMSection({ elements }: { elements: any[] }) {
  const components = useMemo(() => elements.filter((el: any) => el.element_type === 'component'), [elements])

  const totals = useMemo(() => {
    let mass = 0, power = 0, cost = 0
    for (const c of components) {
      const qty = c.quantity || 1
      mass += (c.mass_kg || 0) * qty
      power += (c.power_avg_w || 0) * qty
      cost += (c.cost_recurring_keur || 0) * qty
    }
    return { mass, power, cost }
  }, [components])

  const exportCSV = () => {
    const headers = ['Name', 'Subsystem', 'Mass (kg)', 'Power (W)', 'Cost (kEUR)', 'TRL', 'Manufacturer', 'Qty', 'KB ID']
    const rows = components.map((c: any) => {
      const qty = c.quantity || 1
      return [
        `"${(c.name || '').replace(/"/g, '""')}"`,
        c.subsystem_domain || '',
        ((c.mass_kg || 0) * qty).toFixed(3),
        ((c.power_avg_w || 0) * qty).toFixed(1),
        ((c.cost_recurring_keur || 0) * qty).toFixed(1),
        c.trl || '',
        `"${(c.manufacturer || '').replace(/"/g, '""')}"`,
        qty,
        c.kb_component_id || '',
      ].join(',')
    })
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'bom-export.csv'; a.click(); URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
        <h3 style={{ fontSize: '0.85rem', margin: 0 }}>Bill of Materials</h3>
        <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>{components.length} components</span>
        <span style={{ flex: 1 }} />
        <button onClick={exportCSV} style={{
          padding: '0.2rem 0.5rem', fontSize: '0.65rem', fontWeight: 600, borderRadius: '3px',
          background: '#06b6d4', color: 'white', border: 'none', cursor: 'pointer',
        }}>Export CSV</button>
      </div>

      {/* Summary */}
      <div style={{
        display: 'flex', gap: '1rem', padding: '0.35rem 0.5rem', marginBottom: '0.5rem',
        background: 'rgba(6,182,212,0.06)', borderRadius: '4px', border: '1px solid rgba(6,182,212,0.15)',
        fontSize: '0.72rem',
      }}>
        <span>Mass: <b style={{ fontFamily: 'monospace' }}>{totals.mass.toFixed(2)} kg</b></span>
        <span>Power: <b style={{ fontFamily: 'monospace' }}>{totals.power.toFixed(1)} W</b></span>
        <span>Cost: <b style={{ fontFamily: 'monospace' }}>{totals.cost.toFixed(0)} kEUR</b></span>
      </div>

      {components.length === 0 ? (
        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', padding: '1rem 0' }}>
          No components in the element tree yet. Run a design and select equipment to populate the BOM.
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={thL}>Name</th><th style={thL}>Subsystem</th>
              <th style={thR}>Mass (kg)</th><th style={thR}>Power (W)</th><th style={thR}>Cost (kEUR)</th>
              <th style={thC}>TRL</th><th style={thL}>Manufacturer</th><th style={thC}>Qty</th><th style={thL}>KB ID</th>
            </tr>
          </thead>
          <tbody>
            {components.map((c: any) => {
              const qty = c.quantity || 1
              const DOMAIN_LABELS: Record<string, string> = {
                power: 'EPS', aocs: 'AOCS', ttc: 'TTC', obc: 'OBC',
                thermal: 'Thermal', structure: 'Structure', propulsion: 'Propulsion',
                payload: 'Payload', ground_rf: 'Ground RF', ground_ops: 'Ground Ops',
              }
              return (
                <tr key={c.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '0.2rem 0.4rem', fontWeight: 500 }}>{c.name}</td>
                  <td style={{ padding: '0.2rem 0.4rem' }}>
                    <span style={{ fontSize: '0.55rem', padding: '0.05rem 0.2rem', borderRadius: '2px', background: 'rgba(6,182,212,0.1)', color: '#06b6d4', textTransform: 'uppercase' }}>
                      {DOMAIN_LABELS[c.subsystem_domain] || c.subsystem_domain || '—'}
                    </span>
                  </td>
                  <td style={{ ...tdR, fontFamily: 'monospace' }}>{(c.mass_kg != null ? (c.mass_kg * qty).toFixed(3) : '—')}</td>
                  <td style={{ ...tdR, fontFamily: 'monospace' }}>{(c.power_avg_w != null ? (c.power_avg_w * qty).toFixed(1) : '—')}</td>
                  <td style={{ ...tdR, fontFamily: 'monospace' }}>{(c.cost_recurring_keur != null ? (c.cost_recurring_keur * qty).toFixed(1) : '—')}</td>
                  <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center' }}>
                    <span style={{ color: (c.trl || 0) >= 7 ? 'var(--success)' : (c.trl || 0) >= 5 ? 'var(--warning)' : 'var(--danger)', fontWeight: 600 }}>
                      {c.trl || '?'}
                    </span>
                  </td>
                  <td style={{ padding: '0.2rem 0.4rem', fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{c.manufacturer || '—'}</td>
                  <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', color: qty > 1 ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                    {qty > 1 ? `x${qty}` : qty}
                  </td>
                  <td style={{ padding: '0.2rem 0.4rem', fontFamily: 'monospace', fontSize: '0.6rem', color: 'var(--text-secondary)' }}>
                    {c.kb_component_id ? c.kb_component_id.slice(0, 12) : '—'}
                  </td>
                </tr>
              )
            })}
            {/* Totals row */}
            <tr style={{ borderTop: '2px solid var(--border)', fontWeight: 700 }}>
              <td style={{ padding: '0.3rem 0.4rem' }}>TOTAL</td>
              <td />
              <td style={{ ...tdR, fontFamily: 'monospace' }}>{totals.mass.toFixed(2)}</td>
              <td style={{ ...tdR, fontFamily: 'monospace' }}>{totals.power.toFixed(1)}</td>
              <td style={{ ...tdR, fontFamily: 'monospace' }}>{totals.cost.toFixed(0)}</td>
              <td /><td /><td /><td />
            </tr>
          </tbody>
        </table>
      )}
    </div>
  )
}

// ─── Maturity Section ───

const MATURITY_BADGE: Record<string, { label: string; color: string; bg: string }> = {
  parametric: { label: 'Parametric', color: '#f97316', bg: 'rgba(249,115,22,0.15)' },
  catalogue:  { label: 'Catalogue',  color: '#3b82f6', bg: 'rgba(59,130,246,0.15)' },
  specified:  { label: 'Specified',  color: '#10b981', bg: 'rgba(16,185,129,0.15)' },
  verified:   { label: 'Verified',   color: '#059669', bg: 'rgba(5,150,105,0.15)' },
}

function MaturitySection({ elements }: { elements: any[] }) {
  const subsystems = useMemo(() => {
    // Group components by subsystem_domain
    const groups: Record<string, any[]> = {}
    for (const el of elements) {
      if (el.element_type !== 'component') continue
      const domain = el.subsystem_domain || 'unassigned'
      if (!groups[domain]) groups[domain] = []
      groups[domain].push(el)
    }

    // Determine maturity per subsystem
    const DOMAIN_LABELS: Record<string, string> = {
      power: 'EPS', aocs: 'AOCS', ttc: 'TTC', obc: 'OBC',
      thermal: 'Thermal', structure: 'Structure', propulsion: 'Propulsion',
      payload: 'Payload', ground_rf: 'Ground RF', ground_ops: 'Ground Ops',
      unassigned: 'Unassigned',
    }

    return Object.entries(groups).map(([domain, comps]) => {
      let level: string
      const allFrozen = comps.every((c: any) => c.frozen === true)
      const allSpecified = comps.every((c: any) => c.manufacturer && c.mass_kg != null && c.power_avg_w != null)
      const anyKb = comps.some((c: any) => c.kb_component_id)

      if (allFrozen) {
        level = 'verified'
      } else if (allSpecified) {
        level = 'specified'
      } else if (anyKb) {
        level = 'catalogue'
      } else {
        level = 'parametric'
      }

      return {
        domain,
        label: DOMAIN_LABELS[domain] || domain,
        components: comps.length,
        level,
      }
    }).sort((a, b) => a.label.localeCompare(b.label))
  }, [elements])

  const maturityOrder = ['parametric', 'catalogue', 'specified', 'verified']

  return (
    <div>
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Design Maturity by Subsystem</h3>
      <p style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
        Maturity is determined from component data completeness within each subsystem domain.
      </p>

      {subsystems.length === 0 ? (
        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', padding: '1rem 0' }}>
          No components in the element tree yet. Run a design and select equipment to see maturity.
        </div>
      ) : (
        <>
          {/* Maturity grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.4rem', marginBottom: '0.75rem' }}>
            {subsystems.map(ss => {
              const badge = MATURITY_BADGE[ss.level] || MATURITY_BADGE.parametric
              return (
                <div key={ss.domain} style={{
                  padding: '0.5rem 0.6rem', borderRadius: '6px',
                  background: 'var(--bg-card)', border: `1px solid ${badge.color}30`,
                  display: 'flex', flexDirection: 'column', gap: '0.25rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>{ss.label}</span>
                    <span style={{ fontSize: '0.55rem', color: 'var(--text-secondary)' }}>{ss.components} comp.</span>
                  </div>
                  <span style={{
                    fontSize: '0.62rem', fontWeight: 600, padding: '0.1rem 0.35rem', borderRadius: '3px',
                    background: badge.bg, color: badge.color, alignSelf: 'flex-start',
                  }}>
                    {badge.label}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Legend */}
          <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.62rem', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
            {maturityOrder.map(level => {
              const badge = MATURITY_BADGE[level]
              return (
                <span key={level} style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: badge.color }} />
                  {badge.label}
                </span>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

// ─── Helpers ───

function getDepth(el: any, allElements: any[]): number {
  let depth = 0, current = el
  while (current.parent_id) {
    depth++
    current = allElements.find((e: any) => e.id === current.parent_id)
    if (!current) break
  }
  return depth
}

const thL: React.CSSProperties = { textAlign: 'left', padding: '0.2rem 0.4rem', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.6rem', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...thL, textAlign: 'right' }
const thC: React.CSSProperties = { ...thL, textAlign: 'center' }
const tdR: React.CSSProperties = { padding: '0.2rem 0.4rem', textAlign: 'right' }
