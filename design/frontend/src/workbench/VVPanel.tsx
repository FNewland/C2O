/**
 * VVPanel — Verification & Validation view for Level 4.
 *
 * Five sections:
 * 1. Budget Rollup: mass/power/cost hierarchy
 * 2. Requirement Traceability: derivation chains, orphans, SMART status
 * 3. Review Gate Checklist: MCR/SRR/PDR gate evaluation (from gate_evaluator; default PDR, ruling Q23)
 * 4. FMECA Summary: failure mode analysis results
 * 5. Budget Traceability: trace budget exceedance to stakeholder impact
 */
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'

import { TraceabilityTree } from '../components/TraceabilityTree'
import { VVPlanPanel } from '../components/VVPlanPanel'
import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'
import { useGateReview, type GateId } from '../components/useGateReview'
import { STATUS_LABEL, badgeKind, evidenceText } from '../components/gateReviewText'
import { fs, subsystemStyle } from '../theme/tokens'

const API = '/api'

const STATUS_COLORS: Record<string, string> = {
  green: 'var(--status-ok)', amber: 'var(--status-caution)', red: 'var(--status-alarm)', undefined: 'var(--text-3)',
  pass: 'var(--status-ok)', fail: 'var(--status-alarm)', advisory: 'var(--status-caution)', manual: 'var(--text-2)', not_evaluated: 'var(--text-3)',
}

const REQ_STATUS_COLORS: Record<string, string> = {
  draft: 'var(--text-secondary)', approved: 'var(--accent)', verified: 'var(--success)', violated: 'var(--danger)',
}

// Display labels for stored enum values (the values themselves are never translated).
// English text is the i18n key
const REQ_STATUS_LABEL: Record<string, string> = {
  draft: 'draft', approved: 'approved', verified: 'verified', violated: 'violated',
}
// English text is the i18n key
const REQ_LEVEL_LABEL: Record<string, string> = {
  mission: 'mission', system: 'system', subsystem: 'subsystem',
}
// English text is the i18n key
const BUDGET_LABEL: Record<string, string> = {
  mass: 'mass', power: 'power', cost: 'cost', link: 'link',
}

export function VVPanel() {
  const { t } = useTranslation()
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
    { id: 'budget' as const, label: t('Budget Rollup'), color: 'var(--status-caution)' },
    { id: 'reqs' as const, label: t('Requirements'), color: 'var(--cat-2)' },
    { id: 'gates' as const, label: t('Review Gates'), color: 'var(--interactive)' },
    { id: 'fmeca' as const, label: 'FMECA', color: 'var(--status-alarm)' },
    { id: 'trace' as const, label: t('Traceability'), color: 'var(--status-ok)' },
    { id: 'risks' as const, label: t('Risk Register'), color: 'var(--status-alarm)' },
    { id: 'bom' as const, label: t('BOM'), color: 'var(--interactive)' },
    { id: 'maturity' as const, label: t('Maturity'), color: 'var(--cat-2)' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Section tabs */}
      <div role="tablist" aria-label={t('V&V sections')} className="c2o-tabs" style={{ padding: '0 var(--sp-3)', background: 'var(--surface-1)', borderBottom: '1px solid var(--line)' }}>
        {sections.map(s => (
          <button key={s.id} type="button" role="tab" className="c2o-tab" aria-selected={activeSection === s.id}
            onClick={() => setActiveSection(s.id)}>
            {s.label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
        {activeSection === 'budget' && <BudgetRollup elements={allElements} />}
        {activeSection === 'reqs' && <RequirementTraceability requirements={allRequirements} elements={allElements} studyId={studyId} />}
        {activeSection === 'gates' && <ReviewGates studyId={studyId} />}
        {activeSection === 'fmeca' && <FMECASummary studyId={studyId} />}
        {activeSection === 'trace' && (<>
          <div style={{ marginBottom: '0.75rem' }}><TraceabilityTree studyId={studyId} /></div>
          <div style={{ marginBottom: '0.75rem' }}><VVPlanPanel studyId={studyId} /></div>
          <BudgetTraceability studyId={studyId} />
        </>)}
        {activeSection === 'risks' && <RiskRegister studyId={studyId} />}
        {activeSection === 'bom' && <BOMSection elements={allElements} />}
        {activeSection === 'maturity' && <MaturitySection elements={allElements} />}
      </div>
    </div>
  )
}

// ─── Budget Rollup ───

type RollRow = { el: any; depth: number; mass: number | null; power: number | null; cost: number | null; derived: { mass: boolean; power: boolean; cost: boolean } }

/**
 * Depth-first product tree with roll-ups. Rows are ordered parent → children,
 * so a block is only ever indented under its real parent (R3 problem 14).
 * A block with no own value shows the sum of its children ("Σ"), so the Space
 * Segment carries its subsystems' mass instead of "—".
 */
function rollupRows(elements: any[]): RollRow[] {
  const kids = new Map<string | null, any[]>()
  const ids = new Set(elements.map(e => e.id))
  for (const el of elements) {
    const p = el.parent_id && ids.has(el.parent_id) ? el.parent_id : null
    kids.set(p, [...(kids.get(p) || []), el])
  }
  const out: RollRow[] = []
  const walk = (el: any, depth: number): { mass: number | null; power: number | null; cost: number | null } => {
    const row: RollRow = { el, depth, mass: null, power: null, cost: null, derived: { mass: false, power: false, cost: false } }
    out.push(row)
    const q = el.quantity || 1
    const sums = { mass: null as number | null, power: null as number | null, cost: null as number | null }
    for (const c of kids.get(el.id) || []) {
      const r = walk(c, depth + 1)
      for (const k of ['mass', 'power', 'cost'] as const) if (r[k] != null) sums[k] = (sums[k] ?? 0) + r[k]!
    }
    const own = { mass: el.mass_kg, power: el.power_avg_w, cost: el.cost_recurring_keur }
    for (const k of ['mass', 'power', 'cost'] as const) {
      if (own[k] != null) row[k] = own[k] * q
      else if (sums[k] != null) { row[k] = sums[k]! * q; row.derived[k] = true }
    }
    return { mass: row.mass, power: row.power, cost: row.cost }
  }
  for (const root of kids.get(null) || []) walk(root, 0)
  return out
}

function BudgetRollup({ elements }: { elements: any[] }) {
  const { t } = useTranslation()
  const rows = useMemo(() => rollupRows(elements), [elements])
  const cell = (v: number | null, derived: boolean, digits: number) => v == null
    ? <span style={{ color: 'var(--text-3)', fontFamily: 'var(--font-sans)', fontSize: fs.label }}>{t('no data')}</span>
    : <span title={derived ? t('Sum of child elements') : undefined}>
        {derived && <span style={{ color: 'var(--text-3)', marginRight: 4 }} aria-label={t('Sum of child elements')}>Σ</span>}
        {v.toFixed(digits)}
      </span>
  return (
    <div>
      <h3 style={{ fontSize: fs.body, fontWeight: 600, margin: '0 0 var(--sp-1)' }}>{t('Budget Rollup — All Elements')}</h3>
      <p style={{ fontSize: fs.label, color: 'var(--text-3)', margin: '0 0 var(--sp-2)' }}>
        {t('Σ marks a block without its own value: the figure is the sum of its children.')}
      </p>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.body }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--line-strong)' }}>
            <th style={thL}>{t('Element')}</th><th style={thL}>{t('Type')}</th>
            <th style={thR}>{t('Mass (kg)')}</th><th style={thR}>{t('Power (W)')}</th><th style={thR}>{t('Cost (kEUR)')}</th><th style={thR}>{t('Qty')}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ el, depth, mass, power, cost, derived }) => {
            const ss = el.subsystem_domain ? subsystemStyle(el.subsystem_domain) : null
            return (
              <tr key={el.id} style={{ borderBottom: '1px solid var(--line)' }}>
                <td style={{ padding: '6px 8px', paddingLeft: `${8 + depth * 20}px`, fontWeight: depth < 2 ? 600 : 400 }}>
                  {depth > 0 && <span aria-hidden="true" style={{ color: 'var(--line-strong)', marginRight: 6 }}>└</span>}
                  {el.name}
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: fs.label, color: 'var(--text-3)', textTransform: 'uppercase' }}>
                    {ss && <span className="c2o-ss-badge" aria-hidden="true" style={{ background: ss.color }}>{ss.badge}</span>}
                    {el.subsystem_domain || el.element_type}
                  </span>
                </td>
                <td style={{ ...tdR, ...tdVal }}>{cell(mass, derived.mass, 2)}</td>
                <td style={{ ...tdR, ...tdVal }}>{cell(power, derived.power, 1)}</td>
                <td style={{ ...tdR, ...tdVal }}>{cell(cost, derived.cost, 0)}</td>
                <td style={{ ...tdR, color: 'var(--text-2)' }}>{(el.quantity || 1) > 1 ? `×${el.quantity}` : ''}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ─── Requirement Traceability ───

function RequirementTraceability({ requirements, elements }: { requirements: any[]; elements: any[]; studyId: string | null }) {
  const { t } = useTranslation()
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
      <h3 style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>{t('Requirement Traceability')}</h3>

      {/* Stats */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem', fontSize: fs.label, flexWrap: 'wrap' }}>
        <span>{t('Total:')} <b>{stats.total}</b></span>
        {Object.entries(stats.byStatus).map(([s, n]) => (
          <span key={s} style={{ color: REQ_STATUS_COLORS[s] || 'var(--text-secondary)' }}>{t('{{label}}:', { label: t(REQ_STATUS_LABEL[s] ?? s) })} <b>{n}</b></span>
        ))}
        <span style={{ color: 'var(--border)' }}>|</span>
        {Object.entries(stats.byLevel).map(([l, n]) => (
          <span key={l} style={{ color: 'var(--text-secondary)' }}>{t('{{label}}:', { label: t(REQ_LEVEL_LABEL[l] ?? l) })} <b>{n}</b></span>
        ))}
        <span style={{ color: 'var(--border)' }}>|</span>
        <span style={{ color: stats.orphans > 0 ? 'var(--warning)' : 'var(--success)' }}>{t('Orphans:')} <b>{stats.orphans}</b></span>
        <span>{t('Element coverage:')} <b>{stats.coverage.toFixed(0)}%</b></span>
      </div>

      {/* Table */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            <th style={thL}>{t('Code')}</th><th style={thL}>{t('Level')}</th><th style={thL}>{t('Element')}</th>
            <th style={{ ...thL, width: '35%' }}>{t('Text')}</th><th style={thC}>V&V</th><th style={thC}>{t('Status')}</th><th style={thC}>{t('Derived')}</th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((req: any) => {
            const isOrphan = req.level !== 'mission' && !req.derived_from_requirement_id && !req.parent_id
            return (
              <tr key={req.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)', background: isOrphan ? 'rgba(245,158,11,0.05)' : undefined }}>
                <td style={{ padding: '0.2rem 0.4rem', fontFamily: 'monospace', color: 'var(--accent)', fontSize: fs.label }}>{req.code}</td>
                <td style={{ padding: '0.2rem 0.4rem' }}>
                  <span style={{ fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px', background: 'rgba(59,130,246,0.1)', color: 'var(--accent)', textTransform: 'uppercase' }}>{t(REQ_LEVEL_LABEL[req.level] ?? req.level)}</span>
                </td>
                <td style={{ padding: '0.2rem 0.4rem', fontSize: fs.label, color: 'var(--text-secondary)' }}>{req.element_id ? nameOf(req.element_id) : '—'}</td>
                <td style={{ padding: '0.2rem 0.4rem', fontSize: fs.label }}>{req.text}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', color: 'var(--success)', fontWeight: 600, fontSize: fs.label }}>{req.verification_method || '—'}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center' }}>
                  <span style={{ fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px', background: `color-mix(in srgb, ${REQ_STATUS_COLORS[req.status]} 13%, transparent)`, color: REQ_STATUS_COLORS[req.status], fontWeight: 600 }}>{t(REQ_STATUS_LABEL[req.status] ?? req.status)}</span>
                </td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', fontSize: fs.label }}>
                  {req.derived_from_requirement_id ? (
                    <span style={{ color: 'var(--success)' }}>✓</span>
                  ) : isOrphan ? (
                    <span style={{ color: 'var(--warning)' }} title={t('Not derived from parent requirement')}>{t('orphan')}</span>
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
  const { t } = useTranslation()
  // Ruling Q23: MCR / SRR / PDR from configs/gate_exit_criteria.yaml, default PDR.
  const gates: GateId[] = ['mcr', 'srr', 'pdr']
  const [activeGate, setActiveGate] = useState<GateId>('pdr')
  const missionNeed = useDesignStore(s => s.missionNeed)
  const params = useActiveParameters()

  const { data: gateResult, isLoading, isError } = useGateReview(studyId, activeGate, missionNeed, params)
  const pending = !!gateResult && !gateResult.ready && gateResult.ready_pending_manual
  // Verdict (R3 problem 14): green only for READY, red only when a check failed,
  // otherwise amber "NOT READY (n manual/advisory)".
  const failCount = gateResult ? gateResult.criteria.filter(c => c.verdict === 'fail').length : 0
  const openCount = gateResult?.summary ? (gateResult.summary.manual || 0) + (gateResult.summary.advisory || 0) : 0
  const tone = gateResult?.ready ? 'var(--status-ok)' : failCount > 0 ? 'var(--status-alarm)' : 'var(--status-caution)'
  const wash = gateResult?.ready ? 'var(--status-ok-wash)' : failCount > 0 ? 'var(--status-alarm-wash)' : 'var(--status-caution-wash)'
  const glyph = gateResult?.ready ? '✓' : failCount > 0 ? '▲' : '◆'

  return (
    <div>
      <h3 style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>{t('Review Gate Evaluation')}</h3>

      <div role="group" aria-label={t('Review gate')} style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.5rem' }}>
        {gates.map(g => (
          <button key={g} type="button" onClick={() => setActiveGate(g)} aria-pressed={activeGate === g}
            className={activeGate === g ? 'c2o-btn c2o-btn--primary' : 'c2o-btn'}
            style={{ textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
            {g}
          </button>
        ))}
      </div>

      {isLoading && <div style={{ color: 'var(--text-secondary)' }}>{t('Evaluating...')}</div>}
      {isError && !gateResult && (
        <div style={{ color: 'var(--warning)', fontSize: fs.label }}>
          {t('Gate review service unreachable.')}
        </div>
      )}

      {gateResult && (
        <div>
          {/* Summary */}
          <div role="status" style={{
            display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', gap: 'var(--sp-4)', marginBottom: 'var(--sp-2)',
            padding: 'var(--sp-2) var(--sp-3)', background: wash, borderLeft: `3px solid ${tone}`,
            borderRadius: 'var(--radius)', fontSize: fs.body,
          }}>
            <span style={{ fontWeight: 600, fontSize: fs.value, color: tone }}>
              <span aria-hidden="true" style={{ marginRight: 6 }}>{glyph}</span>
              {gateResult.ready ? t('READY')
                : failCount > 0 ? t('NOT READY ({{n}} failed)', { n: failCount })
                : t('NOT READY ({{n}} manual/advisory)', { n: openCount })}
            </span>
            {pending && <span style={{ color: 'var(--text-2)' }}>{t('Ready for {{gate}}, pending manual sign-off', { gate: activeGate.toUpperCase() })}</span>}
            {gateResult.summary && (
              <span style={{ display: 'inline-flex', gap: 'var(--sp-3)', fontFamily: 'var(--font-mono)', fontSize: fs.label, color: 'var(--text-2)' }}>
                <span>{t('Pass: {{n}}', { n: gateResult.summary.pass })}</span>
                <span style={failCount > 0 ? { color: 'var(--status-alarm)', fontWeight: 600 } : undefined}>{t('Fail: {{n}}', { n: failCount })}</span>
                <span>{t('Advisory: {{n}}', { n: gateResult.summary.advisory })}</span>
                <span>{t('Manual: {{n}}', { n: gateResult.summary.manual })}</span>
              </span>
            )}
          </div>

          {/* Criteria list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            {gateResult.criteria.map(c => {
              const kind = badgeKind(c)
              const color = STATUS_COLORS[kind] || 'var(--text-secondary)'
              return (
                <div key={c.id} style={{
                  display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.25rem 0.4rem',
                  background: 'var(--bg-card)', borderRadius: '3px', fontSize: fs.label,
                  borderLeft: `3px solid ${color}`,
                }}>
                  <span style={{ fontSize: fs.label, fontWeight: 700, color, whiteSpace: 'nowrap' }}>{t(STATUS_LABEL[kind] || 'N/A')}</span>
                  <span style={{ flex: 1 }}>{t(c.question)}</span>
                  <span style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{evidenceText(c, t)}</span>
                  <span style={{ fontSize: fs.label, color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{c.id}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── FMECA Summary ───

function FMECASummary({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
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
      <h3 style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>{t('Failure Mode Analysis (FMECA)')}</h3>
      <button onClick={runFMECA} disabled={loading} style={{
        padding: '0.3rem 0.6rem', fontSize: fs.label, fontWeight: 600, borderRadius: '4px',
        background: 'var(--accent)', color: 'white', border: 'none', cursor: 'pointer', marginBottom: '0.5rem',
      }}>
        {loading ? t('Analysing...') : t('Run FMECA')}
      </button>

      {result?.failure_modes && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={thL}>{t('Subsystem')}</th><th style={thL}>{t('Failure Mode')}</th><th style={thC}>{t('Severity')}</th>
              <th style={thC}>{t('Probability')}</th><th style={thC}>RPN</th><th style={thL}>{t('Mitigation')}</th>
            </tr>
          </thead>
          <tbody>
            {result.failure_modes.slice(0, 20).map((fm: any, i: number) => (
              <tr key={i} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)' }}>
                <td style={{ padding: '0.2rem 0.4rem', fontWeight: 500 }}>{fm.subsystem}</td>
                <td style={{ padding: '0.2rem 0.4rem' }}>{fm.failure_mode || fm.description}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', color: (fm.severity || 0) > 7 ? 'var(--danger)' : 'var(--warning)' }}>{fm.severity}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center' }}>{fm.probability || fm.occurrence}</td>
                <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', fontWeight: 600, color: (fm.rpn || 0) > 100 ? 'var(--danger)' : 'var(--text-primary)' }}>{fm.rpn}</td>
                <td style={{ padding: '0.2rem 0.4rem', fontSize: fs.label, color: 'var(--text-secondary)' }}>{fm.mitigation || fm.recommended_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {result?.summary && (
        <div style={{ marginTop: '0.4rem', padding: '0.3rem 0.5rem', background: 'var(--bg-card)', borderRadius: '4px', fontSize: fs.label }}>
          {t('Total failure modes:')} <b>{result.summary.total || result.failure_modes?.length}</b>
          {result.summary.critical > 0 && <span style={{ color: 'var(--danger)', marginLeft: '0.5rem' }}>{t('Critical:')} <b>{result.summary.critical}</b></span>}
        </div>
      )}
    </div>
  )
}

// ─── Budget Traceability ───

function BudgetTraceability({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
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
      <h3 style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>{t('Budget → Stakeholder Traceability')}</h3>

      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.4rem' }}>
        {budgets.map(b => (
          <button key={b} onClick={() => setActiveBudget(b)} style={{
            padding: '0.2rem 0.5rem', fontSize: fs.label, borderRadius: '3px',
            background: activeBudget === b ? 'var(--accent)' : 'var(--bg-card)',
            color: activeBudget === b ? 'white' : 'var(--text-secondary)',
            border: 'none', cursor: 'pointer',
          }}>
            {BUDGET_LABEL[b] ? t(BUDGET_LABEL[b]) : b}
          </button>
        ))}
        <button onClick={trace} disabled={loading} style={{
          padding: '0.2rem 0.5rem', fontSize: fs.label, fontWeight: 600, borderRadius: '3px',
          background: 'var(--success)', color: 'white', border: 'none', cursor: 'pointer', marginLeft: '0.3rem',
        }}>
          {loading ? '...' : t('Trace')}
        </button>
      </div>

      {result && (
        <div>
          {/* Trace chain */}
          {result.chain?.length > 0 && (
            <div style={{ marginBottom: '0.5rem' }}>
              <div style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{t('Trace Chain:')}</div>
              {result.chain.map((link: any, i: number) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.2rem 0', fontSize: fs.label }}>
                  <span style={{ fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px', background: 'rgba(59,130,246,0.1)', color: 'var(--accent)', textTransform: 'uppercase' }}>{link.level}</span>
                  <span>{link.text}</span>
                  {i < (result.chain?.length || 0) - 1 && <span style={{ color: 'var(--text-secondary)' }}>→</span>}
                </div>
              ))}
            </div>
          )}

          {/* Recovery options */}
          {result.recovery_options?.length > 0 && (
            <div>
              <div style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--warning)', marginBottom: '0.2rem' }}>{t('Recovery Options:')}</div>
              {result.recovery_options.map((opt: any, i: number) => (
                <div key={i} style={{ padding: '0.25rem 0.4rem', background: 'var(--bg-card)', borderRadius: '3px', marginBottom: '0.2rem', fontSize: fs.label }}>
                  <div style={{ fontWeight: 500 }}>{opt.description}</div>
                  <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>
                    {t('Subsystem: {{subsystem}} | Impact: {{impact}} | Feasibility: {{feasibility}}', { subsystem: opt.subsystem, impact: opt.impact, feasibility: opt.feasibility })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {result.stakeholder_impact && (
            <div style={{ marginTop: '0.3rem', padding: '0.3rem', background: 'rgba(245,158,11,0.1)', borderRadius: '3px', fontSize: fs.label, color: 'var(--warning)' }}>
              {t('Stakeholder impact: {{impact}}', { impact: result.stakeholder_impact })}
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

// Categories are stored with each risk in localStorage: keep the English value, translate when shown.
// English text is the i18n key
const RISK_CATEGORIES = ['Technical', 'Schedule', 'Cost', 'Programmatic', 'Safety', 'Regulatory']
// English text is the i18n key
const L_LABELS = ['', 'Rare', 'Unlikely', 'Possible', 'Likely', 'Almost Certain']
// English text is the i18n key
const C_LABELS = ['', 'Negligible', 'Minor', 'Moderate', 'Major', 'Catastrophic']

function RiskRegister({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
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
      <h3 style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>{t('Risk Register')}</h3>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem', fontSize: fs.label }}>
        <span>{t('Total:')} <b>{risks.length}</b></span>
        <span style={{ color: 'var(--danger)' }}>{t('Critical:')} <b>{critical}</b></span>
        <span style={{ color: 'var(--warning)' }}>{t('High:')} <b>{high}</b></span>
        <span>{t('Open:')} <b>{open}</b></span>
      </div>

      {/* Risk matrix heatmap (5×5) */}
      <div style={{ marginBottom: '0.5rem' }}>
        <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{t('Likelihood × Consequence Matrix:')}</div>
        <div style={{ display: 'grid', gridTemplateColumns: '40px repeat(5, 1fr)', gap: 1, fontSize: fs.label }}>
          <div />
          {C_LABELS.slice(1).map(c => <div key={c} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '0.1rem' }}>{t(c)}</div>)}
          {[5, 4, 3, 2, 1].map(l => (
            <>
              <div key={`l${l}`} style={{ textAlign: 'right', paddingRight: '0.2rem', color: 'var(--text-secondary)' }}>{t(L_LABELS[l])}</div>
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
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label, marginBottom: '0.5rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={thL}>ID</th><th style={thL}>{t('Description')}</th><th style={thC}>{t('Cat')}</th>
              <th style={thC}>{t('L')}</th><th style={thC}>{t('C')}</th><th style={thC}>RPN</th>
              <th style={thL}>{t('Mitigation')}</th><th style={thL}>{t('Owner')}</th><th style={thC}>{t('Status')}</th>
              <th style={thC}></th>
            </tr>
          </thead>
          <tbody>
            {risks.map((r, i) => (
              <tr key={r.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)' }}>
                <td style={{ padding: '0.2rem 0.3rem', fontFamily: 'monospace', color: riskColor(r.rpn) }}>{r.id}</td>
                <td style={{ padding: '0.2rem 0.3rem', maxWidth: 200 }}>{r.description}</td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center', fontSize: fs.label }}>{t(r.category)}</td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center' }}>
                  <select value={r.likelihood} onChange={e => updateRisk(i, 'likelihood', parseInt(e.target.value))}
                    style={{ width: 30, fontSize: fs.label, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
                    {[1,2,3,4,5].map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                </td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center' }}>
                  <select value={r.consequence} onChange={e => updateRisk(i, 'consequence', parseInt(e.target.value))}
                    style={{ width: 30, fontSize: fs.label, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
                    {[1,2,3,4,5].map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                </td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center', fontWeight: 700, color: riskColor(r.rpn) }}>{r.rpn}</td>
                <td style={{ padding: '0.2rem 0.3rem', fontSize: fs.label }}>{r.mitigation}</td>
                <td style={{ padding: '0.2rem 0.3rem', fontSize: fs.label }}>{r.owner}</td>
                <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center' }}>
                  <select value={r.status} onChange={e => updateRisk(i, 'status', e.target.value)}
                    style={{ fontSize: fs.label, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: r.status === 'closed' ? 'var(--success)' : 'var(--text-primary)' }}>
                    <option value="open">{t('Open', { context: 'risk' })}</option><option value="mitigating">{t('Mitigating', { context: 'risk' })}</option>
                    <option value="accepted">{t('Accepted', { context: 'risk' })}</option><option value="closed">{t('Closed', { context: 'risk' })}</option>
                  </select>
                </td>
                <td style={{ padding: '0.2rem' }}>
                  <button onClick={() => save(risks.filter((_, j) => j !== i))}
                    style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: fs.label }}>×</button>
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
              style={{ padding: '0.2rem', fontSize: fs.label, borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
              {RISK_CATEGORIES.map(c => <option key={c} value={c}>{t(c)}</option>)}
            </select>
            <input value={newDesc} onChange={e => setNewDesc(e.target.value)} placeholder={t('Risk description')} autoFocus
              style={{ flex: 1, padding: '0.2rem 0.3rem', fontSize: fs.label, borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
          </div>
          <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', fontSize: fs.label }}>
            <span style={{ color: 'var(--text-secondary)' }}>{t('L:')}</span>
            <select value={newL} onChange={e => setNewL(parseInt(e.target.value))}
              style={{ width: 40, fontSize: fs.label, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
              {[1,2,3,4,5].map(v => <option key={v} value={v}>{v} — {t(L_LABELS[v])}</option>)}
            </select>
            <span style={{ color: 'var(--text-secondary)' }}>{t('C:')}</span>
            <select value={newC} onChange={e => setNewC(parseInt(e.target.value))}
              style={{ width: 40, fontSize: fs.label, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
              {[1,2,3,4,5].map(v => <option key={v} value={v}>{v} — {t(C_LABELS[v])}</option>)}
            </select>
            <span style={{ fontWeight: 700, color: riskColor(newL * newC) }}>{t('RPN: {{rpn}}', { rpn: newL * newC })}</span>
          </div>
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            <input value={newMit} onChange={e => setNewMit(e.target.value)} placeholder={t('Mitigation action')}
              style={{ flex: 1, padding: '0.2rem 0.3rem', fontSize: fs.label, borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
            <input value={newOwner} onChange={e => setNewOwner(e.target.value)} placeholder={t('Owner')}
              style={{ width: 80, padding: '0.2rem 0.3rem', fontSize: fs.label, borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
          </div>
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            <button onClick={addRisk} disabled={!newDesc} style={{ padding: '0.2rem 0.5rem', fontSize: fs.label, fontWeight: 600, borderRadius: '3px', background: 'var(--danger)', color: 'white', border: 'none', cursor: 'pointer' }}>{t('Add Risk')}</button>
            <button onClick={() => setShowAdd(false)} style={{ padding: '0.2rem 0.5rem', fontSize: fs.label, borderRadius: '3px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: 'none', cursor: 'pointer' }}>{t('Cancel')}</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowAdd(true)} style={{ padding: '0.3rem 0.6rem', fontSize: fs.label, fontWeight: 600, borderRadius: '4px', background: 'var(--danger)', color: 'white', border: 'none', cursor: 'pointer' }}>
          {t('+ Add Risk')}
        </button>
      )}
    </div>
  )
}

// ─── BOM Section ───

function BOMSection({ elements }: { elements: any[] }) {
  const { t } = useTranslation()
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
        <h3 style={{ fontSize: fs.body, margin: 0 }}>{t('Bill of Materials')}</h3>
        <span style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{t('{{count}} components', { count: components.length })}</span>
        <span style={{ flex: 1 }} />
        <button onClick={exportCSV} style={{
          padding: '0.2rem 0.5rem', fontSize: fs.label, fontWeight: 600, borderRadius: '3px',
          background: 'var(--interactive)', color: 'white', border: 'none', cursor: 'pointer',
        }}>{t('Export CSV')}</button>
      </div>

      {/* Summary */}
      <div style={{
        display: 'flex', gap: '1rem', padding: '0.35rem 0.5rem', marginBottom: '0.5rem',
        background: 'rgba(6,182,212,0.06)', borderRadius: '4px', border: '1px solid rgba(6,182,212,0.15)',
        fontSize: fs.label,
      }}>
        <span>{t('Mass:')} <b style={{ fontFamily: 'monospace' }}>{totals.mass.toFixed(2)} kg</b></span>
        <span>{t('Power:')} <b style={{ fontFamily: 'monospace' }}>{totals.power.toFixed(1)} W</b></span>
        <span>{t('Cost:')} <b style={{ fontFamily: 'monospace' }}>{totals.cost.toFixed(0)} kEUR</b></span>
      </div>

      {components.length === 0 ? (
        <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', padding: '1rem 0' }}>
          {t('No components in the element tree yet. Run a design and select equipment to populate the BOM.')}
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              <th style={thL}>{t('Name')}</th><th style={thL}>{t('Subsystem')}</th>
              <th style={thR}>{t('Mass (kg)')}</th><th style={thR}>{t('Power (W)')}</th><th style={thR}>{t('Cost (kEUR)')}</th>
              <th style={thC}>TRL</th><th style={thL}>{t('Manufacturer')}</th><th style={thC}>{t('Qty')}</th><th style={thL}>KB ID</th>
            </tr>
          </thead>
          <tbody>
            {components.map((c: any) => {
              const qty = c.quantity || 1
              // English text is the i18n key
              const DOMAIN_LABELS: Record<string, string> = {
                power: 'EPS', aocs: 'AOCS', ttc: 'TTC', obc: 'OBC',
                thermal: 'Thermal', structure: 'Structure', propulsion: 'Propulsion',
                payload: 'Payload', ground_rf: 'Ground RF', ground_ops: 'Ground Ops',
              }
              return (
                <tr key={c.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)' }}>
                  <td style={{ padding: '0.2rem 0.4rem', fontWeight: 500 }}>{c.name}</td>
                  <td style={{ padding: '0.2rem 0.4rem' }}>
                    <span style={{ fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px', background: 'rgba(6,182,212,0.1)', color: 'var(--interactive)', textTransform: 'uppercase' }}>
                      {DOMAIN_LABELS[c.subsystem_domain] ? t(DOMAIN_LABELS[c.subsystem_domain]) : (c.subsystem_domain || '—')}
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
                  <td style={{ padding: '0.2rem 0.4rem', fontSize: fs.label, color: 'var(--text-secondary)' }}>{c.manufacturer || '—'}</td>
                  <td style={{ padding: '0.2rem 0.4rem', textAlign: 'center', color: qty > 1 ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                    {qty > 1 ? `x${qty}` : qty}
                  </td>
                  <td style={{ padding: '0.2rem 0.4rem', fontFamily: 'monospace', fontSize: fs.label, color: 'var(--text-secondary)' }}>
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

// English text is the i18n key
const MATURITY_LABEL: Record<string, string> = {
  parametric: 'Parametric', catalogue: 'Catalogue', specified: 'Specified', verified: 'Verified',
}
const MATURITY_BADGE: Record<string, { label: string; color: string; bg: string }> = {
  parametric: { label: MATURITY_LABEL.parametric, color: 'var(--status-caution)', bg: 'rgba(249,115,22,0.15)' },
  catalogue:  { label: MATURITY_LABEL.catalogue,  color: 'var(--interactive)', bg: 'rgba(59,130,246,0.15)' },
  specified:  { label: MATURITY_LABEL.specified,  color: 'var(--status-ok)', bg: 'rgba(16,185,129,0.15)' },
  verified:   { label: MATURITY_LABEL.verified,   color: 'var(--status-ok)', bg: 'rgba(5,150,105,0.15)' },
}

function MaturitySection({ elements }: { elements: any[] }) {
  const { t } = useTranslation()
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
    // English text is the i18n key
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
      <h3 style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>{t('Design Maturity by Subsystem')}</h3>
      <p style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
        {t('Maturity is determined from component data completeness within each subsystem domain.')}
      </p>

      {subsystems.length === 0 ? (
        <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', padding: '1rem 0' }}>
          {t('No components in the element tree yet. Run a design and select equipment to see maturity.')}
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
                  background: 'var(--bg-card)', border: `1px solid color-mix(in srgb, ${badge.color} 19%, transparent)`,
                  display: 'flex', flexDirection: 'column', gap: '0.25rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: fs.label, fontWeight: 600 }}>{t(ss.label)}</span>
                    <span style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{t('{{n}} comp.', { n: ss.components })}</span>
                  </div>
                  <span style={{
                    fontSize: fs.label, fontWeight: 600, padding: '0.1rem 0.35rem', borderRadius: '3px',
                    background: badge.bg, color: badge.color, alignSelf: 'flex-start',
                  }}>
                    {t(badge.label)}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Legend */}
          <div style={{ display: 'flex', gap: '0.75rem', fontSize: fs.label, color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
            {maturityOrder.map(level => {
              const badge = MATURITY_BADGE[level]
              return (
                <span key={level} style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: badge.color }} />
                  {t(badge.label)}
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


const thL: React.CSSProperties = { textAlign: 'left', padding: '6px 8px', color: 'var(--text-2)', fontWeight: 600, fontSize: fs.label }
const thR: React.CSSProperties = { ...thL, textAlign: 'right' }
const thC: React.CSSProperties = { ...thL, textAlign: 'center' }
const tdR: React.CSSProperties = { padding: '6px 8px', textAlign: 'right' }
const tdVal: React.CSSProperties = { fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums', fontSize: fs.value, color: 'var(--text-value)' }
