/**
 * VVPanel — Verification & Validation view for Level 4.
 *
 * Five sections:
 * 1. Budget Rollup: mass/power/cost hierarchy
 * 2. Requirement Traceability: derivation chains, orphans, SMART status
 * 3. Review Gate Checklist: the gates of the study's profile (MDR/PRR/SRR/PDR by default),
 *    evaluated on the server; states Not ready → Ready → Under review → Passed → Reopened
 * 4. FMECA Summary: failure mode analysis results
 * 5. Budget Traceability: trace budget exceedance to stakeholder impact
 */
import { GateDiagrams } from '../diagrams/GateDiagrams'
import { DiagramFigure } from '../diagrams/DiagramFigure'
import { Fragment, useEffect, useRef, useState, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { irText } from './electricalApi'
import { useUIStore, type ActivityPanel } from '../stores/uiStore'
import { GateDecisions, RecordDecision, useLogbookUI } from '../logbook'

import { TraceabilityTree } from '../components/TraceabilityTree'
import { VVPlanPanel } from '../components/VVPlanPanel'
import { useSeatStore } from '../seats/api'
import { useWhereSection } from '../where/where'
import { GateActionError, gateAction, pick, setGateProfile, useGateProfiles, useGateReview, useStudyGates, type GateState } from '../components/useGateReview'
import { FIX_LABEL, STATE_LABEL, STATUS_LABEL, badgeKind, evidenceText } from '../components/gateReviewText'
import { getLang } from '../i18n'
import { subsystemStyle } from '../theme/tokens'
import { ArmButton, Button, DataTable, Disclosure, Field, Input, Note, NoData, Panel, Select, StatusBadge, Tabs, Tag, tabPanelProps, type Status } from '../components/ui'

const API = '/api'

// Display status (colour + glyph + text) for stored enum values.
const KIND_STATUS: Record<string, Status> = {
  pass: 'ok', fail: 'alarm', advisory: 'caution', manual: 'neutral', not_evaluated: 'nodata',
}
const REQ_STATUS: Record<string, Status> = {
  draft: 'neutral', approved: 'info', verified: 'ok', violated: 'alarm',
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
  const [activeSection, setActiveSection] = useState<'budget' | 'reqs' | 'gates' | 'fmeca' | 'trace' | 'risks' | 'bom' | 'maturity'>(
    () => (useSeatStore.getState().vvSection as 'gates' | null) ?? 'budget')
  // Seats (WP9): the Team leader opens on the gate checklist; the Next card opens it too.
  const wantSection = useSeatStore(st => st.vvSection)
  // "Where in SpaceCDF" links open a V&V section (where/where.ts)
  useWhereSection('vv', sec => { if (['budget', 'reqs', 'gates', 'fmeca', 'trace', 'risks', 'bom', 'maturity'].includes(sec)) setActiveSection(sec as 'budget') })
  useEffect(() => {
    if (wantSection === 'gates') { setActiveSection('gates'); useSeatStore.getState().openVV(null) }
  }, [wantSection])

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

  type Section = 'budget' | 'reqs' | 'gates' | 'fmeca' | 'trace' | 'risks' | 'bom' | 'maturity'
  const sections: Array<{ id: Section; label: string }> = [
    { id: 'budget', label: t('Budget Rollup') },
    { id: 'reqs', label: t('Requirements') },
    { id: 'gates', label: t('Review Gates') },
    { id: 'fmeca', label: 'FMECA' },
    { id: 'trace', label: t('Traceability') },
    { id: 'risks', label: t('Risk Register') },
    { id: 'bom', label: t('BOM') },
    { id: 'maturity', label: t('Maturity') },
  ]

  return (
    <div className="c2o-wb">
      <div className="c2o-wb__tabbar">
        <Tabs idBase="vv" label={t('V&V sections')} value={activeSection} onChange={setActiveSection} items={sections} className="c2o-wb__tabs" />
      </div>
      <div {...tabPanelProps('vv', activeSection)} className="c2o-wb__panel c2o-pane">
        {activeSection === 'budget' && <BudgetRollup elements={allElements} />}
        {activeSection === 'reqs' && <RequirementTraceability requirements={allRequirements} elements={allElements} studyId={studyId} />}
        {activeSection === 'gates' && <ReviewGates studyId={studyId} onOpenSection={sec => setActiveSection(sec as Section)} />}
        {activeSection === 'fmeca' && <FMECASummary studyId={studyId} />}
        {activeSection === 'trace' && (<>
          <div className="mb-4"><TraceabilityTree studyId={studyId} /></div>
          <div className="mb-4"><VVPlanPanel studyId={studyId} /></div>
          <div className="mb-4"><DiagramFigure studyId={studyId} kind="vcd" compact /></div>
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
  const rootMass = rows.find(r => r.depth === 0)?.mass ?? null
  const cell = (v: number | null, derived: boolean, digits: number) => v == null
    ? <NoData label={t('no data')} />
    : <span title={derived ? t('Sum of child elements') : undefined}>
        {derived && <span className="c2o-sigma" aria-label={t('Sum of child elements')}>Σ</span>}
        {v.toFixed(digits)}
      </span>
  return (
    <Panel level={2} title={t('Budget Rollup — All Elements')} meta={t('Σ marks a block without its own value: the figure is the sum of its children.')}>
      <div className="c2o-table-wrap" role="region" aria-label={t('Budget Rollup — All Elements')} tabIndex={0}>
        <table className="c2o-table c2o-rollup">
          <caption className="sr-only">{t('Budget Rollup — All Elements')}</caption>
          <thead>
            <tr>
              <th scope="col">{t('Element')}</th><th scope="col">{t('Type')}</th>
              <th scope="col" className="c2o-rollup__share">{t('Share of mission mass')}</th>
              <th scope="col" className="num">{t('Mass (kg)')}</th><th scope="col" className="num">{t('Power (W)')}</th>
              <th scope="col" className="num">{t('Cost (kEUR)')}</th><th scope="col" className="num">{t('Qty')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ el, depth, mass, power, cost, derived }) => {
              const ss = el.subsystem_domain ? subsystemStyle(el.subsystem_domain) : null
              const share = rootMass && mass != null ? Math.min(100, mass / rootMass * 100) : null
              return (
                <tr key={el.id} className={depth < 2 ? 'c2o-rollup__major' : undefined}>
                  <td className="c2o-rollup__name" style={{ paddingLeft: 8 + depth * 20 }}>
                    {depth > 0 && <span aria-hidden="true" className="c2o-rollup__elbow">└</span>}
                    {el.name}
                  </td>
                  <td>
                    <span className="c2o-blocks__kind">
                      {ss && <span className="c2o-ss-badge" aria-hidden="true" style={{ background: ss.color }}>{ss.badge}</span>}
                      {el.subsystem_domain || el.element_type}
                    </span>
                  </td>
                  <td className="c2o-rollup__share" aria-hidden="true">
                    {share != null && <span className="c2o-share"><span style={{ width: `${share}%` }} /></span>}
                  </td>
                  <td className="num c2o-rollup__val">{cell(mass, derived.mass, 2)}</td>
                  <td className="num c2o-rollup__val">{cell(power, derived.power, 1)}</td>
                  <td className="num c2o-rollup__val">{cell(cost, derived.cost, 0)}</td>
                  <td className="num c-2">{(el.quantity || 1) > 1 ? `×${el.quantity}` : ''}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </Panel>
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
      // an interface requirement traces to its interface (design rules IF-01), not to a parent
      if (r.level === 'interface' ? !r.ir_json?.interface_id : (r.level !== 'mission' && !r.derived_from_requirement_id && !r.parent_id)) orphans++
      if (r.element_id) withElement++
    }
    return { total, byStatus, byLevel, orphans, withElement, coverage: total > 0 ? (withElement / total * 100) : 0 }
  }, [requirements])

  return (
    <Panel level={2} title={t('Requirement Traceability')}>
      <dl className="c2o-stats">
        <div><dt>{t('Total')}</dt><dd>{stats.total}</dd></div>
        {Object.entries(stats.byStatus).map(([st, n]) => (
          <div key={st}><dt><StatusBadge status={REQ_STATUS[st] ?? 'neutral'}>{t(REQ_STATUS_LABEL[st] ?? st)}</StatusBadge></dt><dd>{n}</dd></div>
        ))}
        {Object.entries(stats.byLevel).map(([l, n]) => (
          <div key={l}><dt>{t(REQ_LEVEL_LABEL[l] ?? l)}</dt><dd>{n}</dd></div>
        ))}
        <div><dt>{stats.orphans > 0 ? <StatusBadge status="caution">{t('Orphans')}</StatusBadge> : t('Orphans')}</dt><dd>{stats.orphans}</dd></div>
        <div><dt>{t('Element coverage')}</dt><dd>{stats.coverage.toFixed(0)} %</dd></div>
      </dl>

      <DataTable dense caption={t('Requirement Traceability')} rows={requirements} rowKey={(r: any) => r.id}
        empty={t('No requirements yet. Add them in the Requirements tab at each level.')}
        columns={[
          { key: 'code', header: t('Code'), render: (r: any) => <span className="mono c-v">{r.code}</span>, sort: (r: any) => r.code },
          { key: 'level', header: t('Level'), render: (r: any) => <Tag>{t(REQ_LEVEL_LABEL[r.level] ?? r.level)}</Tag>, sort: (r: any) => r.level },
          { key: 'el', header: t('Element'), render: (r: any) => r.element_id ? nameOf(r.element_id) : <NoData label={t('none')} />, sort: (r: any) => nameOf(r.element_id) },
          { key: 'text', header: t('Text'), render: (r: any) => (r.level === 'interface' ? irText(r, i18n.language) : r.text), width: '38%' },
          { key: 'vv', header: 'V&V', render: (r: any) => r.verification_method ? <Tag>{r.verification_method}</Tag> : <NoData label={t('none')} /> },
          { key: 'st', header: t('Status'), render: (r: any) => <StatusBadge status={REQ_STATUS[r.status] ?? 'neutral'}>{t(REQ_STATUS_LABEL[r.status] ?? r.status)}</StatusBadge>, sort: (r: any) => r.status },
          {
            key: 'der', header: t('Derived'), render: (r: any) => {
              const isOrphan = r.level === 'interface' ? !r.ir_json?.interface_id
                : r.level !== 'mission' && !r.derived_from_requirement_id && !r.parent_id
              return r.derived_from_requirement_id || (r.level === 'interface' && !isOrphan) ? <StatusBadge status="ok">{t('traced')}</StatusBadge>
                : isOrphan ? <span title={t('Not derived from parent requirement')}><StatusBadge status="caution">{t('orphan')}</StatusBadge></span>
                : <span className="c2o-nodata">{t('top level')}</span>
            },
          },
        ]} />
    </Panel>
  )
}

// ─── Review Gates ───

/** Go / no-go record of a gate (decision_catalogue.yaml D-GATE-<canonical gate>): a merged
 *  profile gate records the decision of the last canonical gate it covers. */
const GATE_DECISION: Record<string, string> = { mdr: 'D-GATE-MDR', prr: 'D-GATE-PRR', srr: 'D-GATE-SRR', pdr: 'D-GATE-PDR' }
function gateDecisionId(covers: string[] | undefined, id: string): string {
  const last = covers && covers.length ? covers[covers.length - 1] : id === 'mcr' ? 'mdr' : id
  return GATE_DECISION[last] ?? GATE_DECISION.mdr
}

const STATE_STATUS: Record<GateState, Status> = {
  not_ready: 'alarm', ready: 'ok', under_review: 'info', passed: 'ok', reopened: 'caution',
}

function ReviewGates({ studyId, onOpenSection }: { studyId: string | null; onOpenSection: (s: string) => void }) {
  const { t } = useTranslation()
  const lang = useUIStore(s => s.lang)
  const userName = useUIStore(s => s.userName)
  const qc = useQueryClient()
  const { data: overview } = useStudyGates(studyId)
  const { data: profiles } = useGateProfiles()
  const gates = overview?.profile.gates ?? []
  const [picked, setPicked] = useState<string | null>(null)
  // Default tab: the gate the study is preparing for (first not passed).
  const activeGate = picked && gates.some(g => g.id === picked) ? picked : (overview?.current_gate ?? gates[0]?.id ?? null)
  const { data: gateResult, isLoading, isError } = useGateReview(studyId, activeGate)
  // Seats (WP9): gate decisions belong to the Team leader and the instructor (checked on the
  // server too); Customer and Observer do not record go / no-go.
  const seatTeam = useSeatStore(st => st.team)
  const seatShadow = useSeatStore(st => st.shadow)
  const seatHeld = seatTeam?.me?.held ?? []
  const canGate = !seatShadow && (!seatTeam?.enabled || !!seatTeam.me?.instructor || seatHeld.includes('team_leader'))
  const canRecordGo = !seatShadow && (!seatTeam?.enabled || !!seatTeam.me?.instructor
    || seatHeld.some(h => !['customer', 'observer'].includes(h)))
  const [busy, setBusy] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const failCount = gateResult ? gateResult.criteria.filter(c => c.verdict === 'fail').length : 0
  const short = gateResult?.gate.short ?? activeGate?.toUpperCase() ?? ''

  // Logbook: the gate under review is context for entries and worksheets.
  // Passing a gate (NOT READY → READY while watching) prompts the logbook
  // download, as does "Finish review"; neither blocks anything.
  const requestEnd = useLogbookUI(st => st.requestEndSession)
  useEffect(() => {
    useLogbookUI.getState().setGate(activeGate)
    return () => useLogbookUI.getState().setGate(null)
  }, [activeGate])
  const wasReady = useRef<Record<string, boolean>>({})
  useEffect(() => {
    if (!gateResult || !activeGate) return
    const before = wasReady.current[activeGate]
    wasReady.current[activeGate] = gateResult.ready
    if (before === false && gateResult.ready) requestEnd('gate', activeGate)
  }, [gateResult, activeGate, requestEnd])

  const refresh = () => {
    void qc.invalidateQueries({ queryKey: ['gates', studyId] })
    void qc.invalidateQueries({ queryKey: ['gate-review', studyId] })
    void qc.invalidateQueries({ queryKey: ['logbook-decisions'] })
    void qc.invalidateQueries({ queryKey: ['margin-ladder', studyId] })
  }
  const act = async (action: 'start' | 'cancel' | 'pass' | 'reopen') => {
    if (!studyId || !activeGate) return
    setBusy(action); setActionError(null)
    setPicked(activeGate)   // stay on this gate (passing it moves the "current" gate on)
    try {
      await gateAction(studyId, activeGate, action, userName)
      refresh()
    } catch (e) {
      const code = e instanceof GateActionError ? e.code : ''
      setActionError(code === 'not_ready' ? t('Not every must-pass item passes yet.') : t('The gate could not change state ({{code}}).', { code: code || String(e) }))
    } finally { setBusy(null) }
  }
  const changeProfile = async (pid: string) => {
    if (!studyId) return
    try { await setGateProfile(studyId, pid); setPicked(null); refresh() } catch { setActionError(t('The gate profile could not be changed.')) }
  }
  const openFix = (fix: string) => {
    if (fix.startsWith('vv:')) { onOpenSection(fix.slice(3)); return }
    const ui = useUIStore.getState()
    ui.drillUp(ui.breadcrumb.length - 1)   // leave V&V for the element in focus (its level)
    ui.setActivePanel(fix as ActivityPanel)
  }

  const state = gateResult?.state
  const verdictText = gateResult
    ? (state === 'not_ready'
      ? t('NOT READY ({{n}} failed)', { n: failCount || (gateResult.summary.must_pass - gateResult.summary.must_pass_met) })
      : t(STATE_LABEL[state ?? 'not_ready']))
    : ''

  return (
    <Panel level={2} title={t('Review Gate Evaluation')}
      meta={overview ? pick(overview.profile.label, lang) : undefined}
      actions={<>
        {profiles && overview && (
          <Select dense aria-label={t('Gate profile')} value={overview.profile.id} onChange={e => void changeProfile(e.target.value)}>
            {profiles.profiles.map(p => <option key={p.id} value={p.id}>{pick(p.label, lang)}</option>)}
          </Select>
        )}
        {gates.length > 0 && activeGate && (
          <Tabs idBase="gate" variant="segmented" label={t('Review gate')} value={activeGate} onChange={setPicked}
            items={gates.map(g => {
              const st = overview?.gates.find(x => x.id === g.id)?.state
              return { id: g.id, label: <span className="mono" title={`${pick(g.name, lang)}${st ? ` · ${t(STATE_LABEL[st])}` : ''}`}>{g.short}{st === 'passed' ? ' ✓' : ''}</span> }
            })} />
        )}
      </>}>
      <div {...(activeGate ? tabPanelProps('gate', activeGate) : {})}>
        {isLoading && <p className="c-2 m-0">{t('Evaluating...')}</p>}
        {isError && !gateResult && <Note tone="caution">{t('Gate review service unreachable.')}</Note>}

        {gateResult && (
          <>
            <p className="t-12 c-2 m-0 mb-2">
              <span className="w-600 c-1">{gateResult.gate.short} — {pick(gateResult.gate.name, lang)}</span>
              {gateResult.gate.covers.length > 1 && <> · {t('covers {{gates}}', { gates: gateResult.gate.covers.map(c => c.toUpperCase()).join(' + ') })}</>}
              {' · '}{t('Budgets use a {{pct}} % system margin (C2O default, added to the nominal value).', { pct: gateResult.system_margin.mass_percent })}
            </p>
            <div role="status" className="c2o-verdict">
              <StatusBadge status={state === 'not_ready' && failCount === 0 ? 'caution' : STATE_STATUS[state ?? 'not_ready']} boxed className="t-15">
                {verdictText}
              </StatusBadge>
              {gateResult.summary && (
                <span className="c2o-verdict__counts">
                  <span>{t('Must-pass: {{met}} of {{n}}', { met: gateResult.summary.must_pass_met, n: gateResult.summary.must_pass })}</span>
                  <span>{t('Pass: {{n}}', { n: gateResult.summary.pass })}</span>
                  <span className={failCount > 0 ? 'c-alarm w-600' : undefined}>{t('Fail: {{n}}', { n: failCount })}</span>
                  <span>{t('Advisory: {{n}}', { n: gateResult.summary.advisory })}</span>
                  <span>{t('Manual: {{n}}', { n: gateResult.summary.manual })}</span>
                </span>
              )}
              <span className="row gap-2 ml-auto wrap">
                {!canGate && <span className="t-12 c-3">{t('Gate decisions: Team leader or instructor')}</span>}
                {canGate && (state === 'ready' || (state === 'reopened' && gateResult.ready)) && (
                  <Button size="sm" variant="primary" busy={busy === 'start'} onClick={() => void act('start')}>{t('Start {{gate}} review', { gate: short })}</Button>
                )}
                {canGate && state === 'reopened' && !gateResult.ready && (
                  <Button size="sm" disabledReason={t('Every must-pass item must pass first')}>{t('Start {{gate}} review', { gate: short })}</Button>
                )}
                {canGate && state === 'under_review' && (<>
                  <Button size="sm" variant="primary" busy={busy === 'pass'} onClick={() => void act('pass')}
                    disabledReason={!gateResult.ready ? t('A must-pass item failed during the review') : undefined}
                    title={t('Pass the gate and save a baseline snapshot')}>{t('Pass {{gate}}', { gate: short })}</Button>
                  <Button size="sm" busy={busy === 'cancel'} onClick={() => void act('cancel')}>{t('Cancel review')}</Button>
                </>)}
                {canGate && state === 'passed' && (
                  <Button size="sm" busy={busy === 'reopen'} onClick={() => void act('reopen')}>{t('Reopen {{gate}}', { gate: short })}</Button>
                )}
                {canRecordGo && <RecordDecision decision={gateDecisionId(gateResult.gate.covers, gateResult.gate.id)} capture="gate:review" context={{ gate: gateResult.gate.id }}
                  label={t('Record go / no-go')}
                  prefill={() => {
                    const failed = gateResult.criteria.filter(c => c.verdict === 'fail')
                    const manual = gateResult.criteria.filter(c => badgeKind(c) === 'manual' || badgeKind(c) === 'advisory')
                    return {
                      options: [
                        { name: t('Go: hold the review now'), chosen: gateResult.ready || undefined },
                        { name: t('Go with actions: hold it, with the open criteria as actions') },
                        { name: t('No go: close the failed criteria first'), chosen: (!gateResult.ready && failCount > 0) || undefined },
                      ],
                      choice: verdictText,
                      evidence: [
                        { label: t('Criteria passed'), value: gateResult.summary?.pass ?? 0 },
                        { label: t('Criteria failed'), value: failCount },
                        { label: t('Advisory'), value: gateResult.summary?.advisory ?? 0 },
                        { label: t('Manual sign-off'), value: gateResult.summary?.manual ?? 0 },
                      ],
                      open_issues: [...failed, ...manual].slice(0, 12).map(c => `${c.id}: ${t(c.question)}`).join('\n') || undefined,
                    }
                  }} />}
                <Button size="sm" onClick={() => requestEnd('gate', activeGate)}
                  title={t('Close this review and download your logbook')}>
                  {t('Finish {{gate}} review', { gate: short })}
                </Button>
              </span>
            </div>
            {actionError && <Note tone="caution" className="mb-2">{actionError}</Note>}

            <ul className="list-reset c2o-criteria">
              {gateResult.criteria.map(c => {
                const kind = badgeKind(c)
                const seat = pick(c.owner_seat_label, lang) || c.owner_seat
                const step = c.step ? `${c.step} ${pick(c.step_label, lang)}`.trim() : ''
                return (
                  <li key={c.id} className="c2o-criteria__row">
                    <StatusBadge status={KIND_STATUS[kind] ?? 'nodata'}>{t(STATUS_LABEL[kind] || 'N/A')}</StatusBadge>
                    <span className="c2o-criteria__q">{t(c.question)}</span>
                    <span className="t-12 c-2">{evidenceText(c, t)}</span>
                    <span className="t-12 c-3 row gap-2 wrap ai-c">
                      <span className="mono">{c.id}</span>
                      {seat && <Tag>{t('Owner: {{seat}}', { seat })}</Tag>}
                      {step && <span title={t('Workflow step that closes it')}>{t('Step {{step}}', { step })}</span>}
                      {c.fix && kind !== 'pass' && (
                        <Button size="sm" variant="quiet" onClick={() => openFix(c.fix!)}>{t(FIX_LABEL[c.fix] ?? 'Fix')}</Button>
                      )}
                    </span>
                  </li>
                )
              })}
            </ul>

            {gateResult.checks.length > 0 && (
              <Disclosure ruled summary={t('Rule checks')} meta={t('{{n}} checks', { n: gateResult.checks.length })}>
                <ul className="list-reset c2o-criteria">
                  {gateResult.checks.map(ch => (
                    <li key={ch.id} className="c2o-criteria__row">
                      <StatusBadge status={CHECK_STATUS[ch.status] ?? 'nodata'}>{t(CHECK_LABEL[ch.status] ?? 'N/A')}</StatusBadge>
                      <span className="c2o-criteria__q">{pick(ch.label, lang)}</span>
                      <span className="t-12 c-2">{pick(ch.detail, lang)}</span>
                      <span className="t-12 c-3 mono">{ch.id}{ch.c2o_default ? ` · ${t('C2O default')}` : ''}</span>
                    </li>
                  ))}
                </ul>
              </Disclosure>
            )}

            {gateResult.baselines.length > 0 && (
              <div className="mt-3">
                <h4 className="c2o-reqs__group">{t('Baselines')}</h4>
                <ul className="list-reset stack gap-1 t-12">
                  {gateResult.baselines.map((b, i) => (
                    <li key={b.id ?? i}>
                      {t('{{gate}} passed {{date}} by {{who}}: baseline saved, {{n}} products baselined', {
                        gate: short, date: fmtDate(b.at), who: b.by || t('unknown'), n: b.products.length })}
                      {b.error && <span className="c-caution"> · {t('the snapshot could not be stored')}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <GateDiagrams studyId={studyId} gate={gateResult.gate.id} />

            <GateDecisions gate={gateResult.gate.id} />
          </>
        )}
      </div>
    </Panel>
  )
}

const CHECK_STATUS: Record<string, Status> = { pass: 'ok', warn: 'caution', fail: 'alarm', not_evaluated: 'nodata' }
// English text is the i18n key
const CHECK_LABEL: Record<string, string> = { pass: 'PASS', warn: 'CAUTION', fail: 'FAIL', not_evaluated: 'N/A' }

function fmtDate(iso: string): string {
  try { return new Date(iso).toLocaleString(getLang() === 'fr' ? 'fr-FR' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }) } catch { return iso }
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

  const modes: any[] = result?.failure_modes?.slice(0, 20) ?? []
  return (
    <Panel level={2} title={t('Failure Mode Analysis (FMECA)')}
      meta={result ? t('{{n}} failure modes', { n: result.failure_modes?.length ?? 0 }) : undefined}
      actions={<Button variant="primary" size="sm" onClick={runFMECA} busy={loading} active={loading}>{loading ? t('Analysing...') : t('Run FMECA')}</Button>}>
      {result && (
        <p className="t-12 c-3 m-0 mb-2">{t('S severity, O occurrence, D detection (1–5 each, 5 worst); RPN = S × O × D. Generic failure modes for each subsystem type: Analyses › FMECA builds them from your design.')}</p>
      )}
      {result ? (
        <DataTable dense caption={t('Failure Mode Analysis (FMECA)')} rows={modes} rowKey={(_: any, i) => String(i)}
          defaultSort={{ key: 'rpn', dir: 'desc' }}
          empty={t('No failure modes returned.')}
          columns={[
            { key: 'ss', header: t('Subsystem'), render: (fm: any) => <span className="w-500">{fm.component ?? fm.subsystem}</span>, sort: (fm: any) => fm.component ?? fm.subsystem },
            { key: 'fm', header: t('Failure Mode'), render: (fm: any) => fm.mode ?? fm.failure_mode ?? fm.description },
            { key: 'eff', header: t('System effect'), render: (fm: any) => <span className="c-2">{fm.system_effect}</span> },
            { key: 'sev', header: t('S'), num: true, sort: (fm: any) => fm.severity,
              render: (fm: any) => (fm.severity || 0) >= 5 ? <StatusBadge status="alarm">{String(fm.severity)}</StatusBadge> : fm.severity },
            { key: 'p', header: t('O'), num: true, render: (fm: any) => fm.occurrence ?? fm.probability, sort: (fm: any) => fm.occurrence ?? fm.probability },
            { key: 'd', header: t('D'), num: true, render: (fm: any) => fm.detection, sort: (fm: any) => fm.detection },
            { key: 'rpn', header: 'RPN', num: true, sort: (fm: any) => fm.rpn,
              render: (fm: any) => <span className="w-600">{fm.rpn}</span> },
            { key: 'mit', header: t('Mitigation'), render: (fm: any) => <span className="c-2">{fm.mitigation || fm.recommended_action}</span> },
          ]} />
      ) : (
        <p className="t-13 c-2 m-0">{t('Run FMECA to list failure modes for each subsystem, ranked by risk priority number (RPN).')}</p>
      )}
    </Panel>
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
    <Panel level={2} title={t('Budget → Stakeholder Traceability')}
      actions={<>
        <Tabs idBase="btrace" variant="segmented" label={t('Budget')} value={activeBudget} onChange={setActiveBudget}
          items={budgets.map(b => ({ id: b, label: BUDGET_LABEL[b] ? t(BUDGET_LABEL[b]) : b }))} />
        <Button size="sm" variant="primary" onClick={trace} busy={loading}>{loading ? t('Tracing...') : t('Trace')}</Button>
      </>}>
      <div {...tabPanelProps('btrace', activeBudget)}>
        {!result && <p className="t-13 c-2 m-0">{t('Pick a budget and trace it to the stakeholder needs it supports.')}</p>}
        {result && (
          <div className="stack gap-3">
            {result.chain?.length > 0 && (
              <ol className="list-reset c2o-chain" aria-label={t('Trace Chain:')}>
                {result.chain.map((link: any, i: number) => (
                  <li key={i} className="c2o-chain__step">
                    <Tag>{link.level}</Tag>
                    <span>{link.text}</span>
                  </li>
                ))}
              </ol>
            )}
            {result.recovery_options?.length > 0 && (
              <div>
                <h4 className="c2o-reqs__group">{t('Recovery Options:')}</h4>
                <ul className="list-reset stack gap-1">
                  {result.recovery_options.map((opt: any, i: number) => (
                    <li key={i} className="c2o-option-row">
                      <span className="w-500">{opt.description}</span>
                      <span className="t-12 c-2">
                        {t('Subsystem: {{subsystem}} | Impact: {{impact}} | Feasibility: {{feasibility}}', { subsystem: opt.subsystem, impact: opt.impact, feasibility: opt.feasibility })}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {result.stakeholder_impact && (
              <Note tone="caution">{t('Stakeholder impact: {{impact}}', { impact: result.stakeholder_impact })}</Note>
            )}
          </div>
        )}
      </div>
    </Panel>
  )
}

// ─── Helpers ───

// ─── Risk Register ───

/** A table cell that edits in place: commits on Enter or when focus leaves. */
function InlineText({ value, label, placeholder, narrow, onCommit }: {
  value: string; label: string; placeholder: string; narrow?: boolean; onCommit: (v: string) => void
}) {
  const [v, setV] = useState(value || '')
  useEffect(() => { setV(value || '') }, [value])
  const commit = () => { if (v !== (value || '')) onCommit(v) }
  return (
    <Input dense aria-label={label} placeholder={placeholder} value={v} style={{ width: narrow ? '9rem' : '100%', minWidth: narrow ? undefined : '14rem' }}
      onChange={e => setV(e.target.value)} onBlur={commit}
      onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); commit(); (e.target as HTMLInputElement).blur() } }} />
  )
}

interface Risk {
  id: string; description: string; category: string
  likelihood: number; consequence: number; rpn: number
  mitigation: string; owner: string; status: string
}

// Categories are stored with each risk: keep the English value, translate when shown.
// English text is the i18n key
const RISK_CATEGORIES = ['Technical', 'Schedule', 'Cost', 'Programmatic', 'Safety', 'Regulatory']
// English text is the i18n key
const L_LABELS = ['', 'Rare', 'Unlikely', 'Possible', 'Likely', 'Almost Certain']
// English text is the i18n key
const C_LABELS = ['', 'Negligible', 'Minor', 'Moderate', 'Major', 'Catastrophic']

/**
 * The team risk register, stored on the server per study (WP0, Nov 2026; it lived in
 * each browser's localStorage, invisible to teammates and to the gates). A register
 * left in this browser by the old version is moved to the study once.
 */
function RiskRegister({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const key = ['risks', studyId]
  const { data: risks = [] } = useQuery<Risk[]>({
    queryKey: key,
    queryFn: () => fetch(`${API}/studies/${studyId}/risks`).then(r => (r.ok ? r.json() : [])),
    enabled: !!studyId,
  })
  // One-time migration of the old browser-local register.
  useEffect(() => {
    if (!studyId) return
    const legacyKey = `spacecdf-risks-${studyId}`
    let legacy: Risk[] = []
    try { legacy = JSON.parse(localStorage.getItem(legacyKey) || '[]') } catch { legacy = [] }
    if (!Array.isArray(legacy) || legacy.length === 0) return
    void fetch(`${API}/studies/${studyId}/risks/import`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ risks: legacy, only_if_empty: false }),
    }).then(r => {
      if (r.ok) { try { localStorage.removeItem(legacyKey) } catch { /* private mode */ } void qc.invalidateQueries({ queryKey: key }) }
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId])
  const [showAdd, setShowAdd] = useState(false)
  const [newDesc, setNewDesc] = useState('')
  const [newCat, setNewCat] = useState('Technical')
  const [newL, setNewL] = useState(3)
  const [newC, setNewC] = useState(3)
  const [newMit, setNewMit] = useState('')
  const [newOwner, setNewOwner] = useState('')

  const send = async (url: string, method: string, body?: unknown) => {
    await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) })
    void qc.invalidateQueries({ queryKey: key })
    void qc.invalidateQueries({ queryKey: ['gate-review', studyId] })
  }

  const addRisk = () => {
    if (!newDesc || !studyId) return
    void send(`${API}/studies/${studyId}/risks`, 'POST', {
      description: newDesc, category: newCat, likelihood: newL, consequence: newC,
      mitigation: newMit, owner: newOwner, status: 'open',
    })
    setNewDesc(''); setNewMit(''); setNewOwner(''); setShowAdd(false)
  }

  const updateRisk = (r: Risk, field: string, value: string | number) => {
    if (!studyId) return
    void send(`${API}/studies/${studyId}/risks/${encodeURIComponent(r.id)}`, 'PATCH', { [field]: value })
  }
  const deleteRisk = (r: Risk) => {
    if (!studyId) return
    void send(`${API}/studies/${studyId}/risks/${encodeURIComponent(r.id)}`, 'DELETE')
  }

  // Bands of the textbook (§ 15.2): low 1–4 accept, medium 5–9, high 10–15 mitigate, critical 16–25 redesign
  const riskStatus = (rpn: number): Status => rpn >= 16 ? 'alarm' : rpn >= 10 ? 'caution' : 'neutral'
  const zone = (rpn: number) => rpn >= 16 ? 'is-crit' : rpn >= 10 ? 'is-high' : rpn >= 5 ? 'is-med' : 'is-low'

  // Stats
  const critical = risks.filter(r => r.rpn >= 16).length
  const high = risks.filter(r => r.rpn >= 10 && r.rpn < 16).length
  const open = risks.filter(r => r.status === 'open').length

  return (
    <Panel level={2} title={t('Risk Register')}
      actions={!showAdd && <Button variant="primary" size="sm" onClick={() => setShowAdd(true)}>{t('+ Add Risk')}</Button>}>
      <div className="c2o-risk">
        {/* Picture first: the 5×5 likelihood × consequence matrix with counts. */}
        <figure className="c2o-riskmx m-0" aria-label={t('Likelihood × Consequence Matrix:')}>
          <div className="c2o-riskmx__grid">
            <span className="c2o-riskmx__axis" aria-hidden="true" />
            {C_LABELS.slice(1).map(c => <span key={c} className="c2o-riskmx__head">{t(c)}</span>)}
            {[5, 4, 3, 2, 1].map(l => (
              <Fragment key={l}>
                <span className="c2o-riskmx__side">{t(L_LABELS[l])}</span>
                {[1, 2, 3, 4, 5].map(c => {
                  const rpn = l * c
                  const count = risks.filter(r => r.likelihood === l && r.consequence === c).length
                  return (
                    <span key={`${l}-${c}`} className={`c2o-riskmx__cell ${zone(rpn)}${count > 0 ? ' has-risk' : ''}`}
                      title={t('L{{l}} × C{{c}} = RPN {{rpn}}: {{count}} risks', { l, c, rpn, count })}>
                      {count > 0 ? count : ''}
                    </span>
                  )
                })}
              </Fragment>
            ))}
          </div>
          <figcaption className="t-12 c-3 mt-1">{t('Rows: likelihood. Columns: consequence. Figures: number of risks in the cell.')}</figcaption>
        </figure>
        <dl className="c2o-stats c2o-stats--col">
          <div><dt>{t('Total')}</dt><dd>{risks.length}</dd></div>
          <div><dt>{critical > 0 ? <StatusBadge status="alarm">{t('Critical')}</StatusBadge> : t('Critical')}</dt><dd>{critical}</dd></div>
          <div><dt>{high > 0 ? <StatusBadge status="caution">{t('High')}</StatusBadge> : t('High')}</dt><dd>{high}</dd></div>
          <div><dt>{t('Open')}</dt><dd>{open}</dd></div>
        </dl>
      </div>

      {risks.length > 0 && (
        <Disclosure ruled defaultOpen summary={t('Risk table')} meta={t('{{count}} risks', { count: risks.length, defaultValue_one: '{{count}} risk' })}>
          <DataTable dense caption={t('Risk Register')} rows={risks} rowKey={r => r.id}
            columns={[
              { key: 'id', header: 'ID', render: r => <span className="mono">{r.id}</span>, sort: r => r.id },
              { key: 'd', header: t('Description'), render: r => r.description },
              { key: 'cat', header: t('Cat'), render: r => <Tag>{t(r.category)}</Tag>, sort: r => r.category },
              { key: 'l', header: t('L'), num: true, sort: r => r.likelihood, render: r => (
                <Select dense className="c2o-num-select" aria-label={t('Likelihood of {{id}}', { id: r.id })} value={r.likelihood}
                  onChange={e => updateRisk(r, 'likelihood', parseInt(e.target.value))}>
                  {[1, 2, 3, 4, 5].map(v => <option key={v} value={v}>{v}</option>)}
                </Select>) },
              { key: 'c', header: t('C'), num: true, sort: r => r.consequence, render: r => (
                <Select dense className="c2o-num-select" aria-label={t('Consequence of {{id}}', { id: r.id })} value={r.consequence}
                  onChange={e => updateRisk(r, 'consequence', parseInt(e.target.value))}>
                  {[1, 2, 3, 4, 5].map(v => <option key={v} value={v}>{v}</option>)}
                </Select>) },
              { key: 'rpn', header: 'RPN', num: true, sort: r => r.rpn, render: r => riskStatus(r.rpn) === 'neutral' ? <span className="w-600">{r.rpn}</span> : <StatusBadge status={riskStatus(r.rpn)}>{String(r.rpn)}</StatusBadge> },
              { key: 'mit', header: t('Mitigation'), render: r => (
                <InlineText value={r.mitigation} label={t('Mitigation of {{id}}', { id: r.id })} placeholder={t('none')}
                  onCommit={v => updateRisk(r, 'mitigation', v)} />) },
              { key: 'own', header: t('Owner'), render: r => (
                <InlineText value={r.owner} label={t('Owner of {{id}}', { id: r.id })} placeholder={t('none')} narrow
                  onCommit={v => updateRisk(r, 'owner', v)} />) },
              { key: 'st', header: t('Status'), sort: r => r.status, render: r => (
                <Select dense aria-label={t('Status of {{id}}', { id: r.id })} value={r.status} onChange={e => updateRisk(r, 'status', e.target.value)}>
                  <option value="open">{t('Open', { context: 'risk' })}</option><option value="mitigating">{t('Mitigating', { context: 'risk' })}</option>
                  <option value="accepted">{t('Accepted', { context: 'risk' })}</option><option value="closed">{t('Closed', { context: 'risk' })}</option>
                </Select>) },
              { key: 'x', header: <span className="sr-only">{t('Delete')}</span>, render: r => (
                <ArmButton variant="icon" label="×" armedLabel={t('Delete')} aria-label={t('Delete {{code}}', { code: r.id })}
                  onConfirm={() => deleteRisk(r)} />) },
            ]} />
        </Disclosure>
      )}

      {showAdd && (
        <form className="c2o-blocks__add mt-3" aria-label={t('Add Risk')} onSubmit={e => { e.preventDefault(); addRisk() }}>
          <Field label={t('Category')}>
            <Select dense value={newCat} onChange={e => setNewCat(e.target.value)}>
              {RISK_CATEGORIES.map(c => <option key={c} value={c}>{t(c)}</option>)}
            </Select>
          </Field>
          <Field label={t('Risk description')} className="c2o-reqs__textfield">
            <Input dense value={newDesc} onChange={e => setNewDesc(e.target.value)} autoFocus />
          </Field>
          <Field label={t('Likelihood')}>
            <Select dense value={newL} onChange={e => setNewL(parseInt(e.target.value))}>
              {[1, 2, 3, 4, 5].map(v => <option key={v} value={v}>{v} — {t(L_LABELS[v])}</option>)}
            </Select>
          </Field>
          <Field label={t('Consequence')}>
            <Select dense value={newC} onChange={e => setNewC(parseInt(e.target.value))}>
              {[1, 2, 3, 4, 5].map(v => <option key={v} value={v}>{v} — {t(C_LABELS[v])}</option>)}
            </Select>
          </Field>
          <span className="t-13 pb-1">{t('RPN: {{rpn}}', { rpn: newL * newC })}</span>
          <Field label={t('Mitigation action')} className="c2o-reqs__textfield">
            <Input dense value={newMit} onChange={e => setNewMit(e.target.value)} />
          </Field>
          <Field label={t('Owner')}>
            <Input dense value={newOwner} onChange={e => setNewOwner(e.target.value)} />
          </Field>
          <span className="row gap-2">
            <Button type="submit" variant="primary" size="sm" disabledReason={!newDesc ? t('Describe the risk first') : undefined}>{t('Add Risk')}</Button>
            <Button size="sm" onClick={() => setShowAdd(false)}>{t('Cancel')}</Button>
          </span>
        </form>
      )}
    </Panel>
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

  // English text is the i18n key
  const DOMAIN_LABELS: Record<string, string> = {
    power: 'EPS', aocs: 'AOCS', ttc: 'TTC', obc: 'OBC',
    thermal: 'Thermal', structure: 'Structure', propulsion: 'Propulsion',
    payload: 'Payload', ground_rf: 'Ground RF', ground_ops: 'Ground Ops',
  }
  const nd = <NoData label={t('no data')} />
  const q = (c: any) => c.quantity || 1
  return (
    <Panel level={2} title={t('Bill of Materials')} meta={t('{{count}} components', { count: components.length })}
      actions={<Button size="sm" onClick={exportCSV} disabledReason={components.length === 0 ? t('No components to export yet') : undefined}>{t('Export CSV')}</Button>}>
      <dl className="c2o-stats">
        <div><dt>{t('Mass')}</dt><dd>{totals.mass.toFixed(2)} <span className="c2o-mbar__unit">kg</span></dd></div>
        <div><dt>{t('Power')}</dt><dd>{totals.power.toFixed(1)} <span className="c2o-mbar__unit">W</span></dd></div>
        <div><dt>{t('Cost')}</dt><dd>{totals.cost.toFixed(0)} <span className="c2o-mbar__unit">kEUR</span></dd></div>
      </dl>
      <DataTable dense caption={t('Bill of Materials')} rows={components} rowKey={(c: any) => c.id}
        empty={t('No components in the element tree yet. Run a design and select equipment to populate the BOM.')}
        columns={[
          { key: 'n', header: t('Name'), render: (c: any) => <span className="w-500">{c.name}</span>, sort: (c: any) => c.name },
          { key: 'ss', header: t('Subsystem'), sort: (c: any) => c.subsystem_domain, render: (c: any) => {
            const ss = c.subsystem_domain ? subsystemStyle(c.subsystem_domain) : null
            return <span className="c2o-blocks__kind">{ss && <span className="c2o-ss-badge" aria-hidden="true" style={{ background: ss.color }}>{ss.badge}</span>}{DOMAIN_LABELS[c.subsystem_domain] ? t(DOMAIN_LABELS[c.subsystem_domain]) : (c.subsystem_domain || t('none'))}</span>
          } },
          { key: 'm', header: t('Mass (kg)'), num: true, sort: (c: any) => (c.mass_kg ?? 0) * q(c), render: (c: any) => c.mass_kg != null ? (c.mass_kg * q(c)).toFixed(3) : nd, foot: totals.mass.toFixed(2) },
          { key: 'p', header: t('Power (W)'), num: true, sort: (c: any) => (c.power_avg_w ?? 0) * q(c), render: (c: any) => c.power_avg_w != null ? (c.power_avg_w * q(c)).toFixed(1) : nd, foot: totals.power.toFixed(1) },
          { key: 'c', header: t('Cost (kEUR)'), num: true, sort: (c: any) => (c.cost_recurring_keur ?? 0) * q(c), render: (c: any) => c.cost_recurring_keur != null ? (c.cost_recurring_keur * q(c)).toFixed(1) : nd, foot: totals.cost.toFixed(0) },
          { key: 'trl', header: 'TRL', num: true, sort: (c: any) => c.trl, render: (c: any) => c.trl == null ? nd
            : c.trl >= 7 ? <span>{c.trl}</span> : <StatusBadge status={c.trl >= 5 ? 'caution' : 'alarm'}>{String(c.trl)}</StatusBadge> },
          { key: 'mf', header: t('Manufacturer'), render: (c: any) => c.manufacturer || nd, sort: (c: any) => c.manufacturer },
          { key: 'q', header: t('Qty'), num: true, render: (c: any) => q(c) > 1 ? `×${q(c)}` : '1', sort: (c: any) => q(c) },
          { key: 'kb', header: 'KB ID', render: (c: any) => c.kb_component_id ? <span className="mono t-12 c-2">{c.kb_component_id.slice(0, 12)}</span> : nd },
        ]} />
    </Panel>
  )
}

// ─── Maturity Section ───

// English text is the i18n key
const MATURITY_LABEL: Record<string, string> = {
  parametric: 'Parametric', catalogue: 'Catalogue', specified: 'Specified', verified: 'Verified',
}
const MATURITY_ORDER = ['parametric', 'catalogue', 'specified', 'verified'] as const

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

  return (
    <Panel level={2} title={t('Design Maturity by Subsystem')} meta={t('Maturity is determined from component data completeness within each subsystem domain.')}>
      {subsystems.length === 0 ? (
        <p className="t-13 c-2 m-0">{t('No components in the element tree yet. Run a design and select equipment to see maturity.')}</p>
      ) : (
        <>
          {/* A four-step ladder per subsystem: parametric → catalogue → specified → verified. */}
          <div className="c2o-ladder" role="table" aria-label={t('Design Maturity by Subsystem')}>
            <div className="c2o-ladder__row c2o-ladder__head" role="row">
              <span role="columnheader">{t('Subsystem')}</span>
              {MATURITY_ORDER.map(m => <span key={m} role="columnheader">{t(MATURITY_LABEL[m])}</span>)}
              <span role="columnheader" className="ta-r">{t('Components')}</span>
            </div>
            {subsystems.map(ss => {
              const reached = MATURITY_ORDER.indexOf(ss.level as typeof MATURITY_ORDER[number])
              return (
                <div key={ss.domain} className="c2o-ladder__row" role="row">
                  <span role="rowheader" className="w-500">{t(ss.label)}</span>
                  {MATURITY_ORDER.map((m, i) => (
                    <span key={m} role="cell" className={i <= reached ? 'c2o-ladder__step is-on' : 'c2o-ladder__step'}>
                      <span className="sr-only">{i <= reached ? t('reached') : t('not reached')}</span>
                    </span>
                  ))}
                  <span role="cell" className="mono ta-r">{ss.components}</span>
                </div>
              )
            })}
          </div>
        </>
      )}
    </Panel>
  )
}

// ─── Helpers ───


