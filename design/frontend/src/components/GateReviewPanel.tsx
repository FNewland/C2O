/**
 * Gate Review tab (author ruling Q23): pick MCR / SRR / PDR (default PDR); the
 * criteria come from the backend's YAML-driven evaluator
 * (configs/gate_exit_criteria.yaml). Should-pass items are advisory: shown,
 * never blocking. If the backend cannot be reached, the old client-side MCR
 * checklist is shown instead, with a note.
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'
import { useGateReview, type GateCriterion, type GateId } from './useGateReview'
import { fixTargetFor, STATUS_LABEL, badgeKind, evidenceText } from './gateReviewText'

const GATES: GateId[] = ['mcr', 'srr', 'pdr']

// English text is the i18n key
const GATE_TITLE: Record<GateId, string> = {
  mcr: 'Mission Concept Review (MCR)',
  srr: 'System Requirements Review (SRR)',
  pdr: 'Preliminary Design Review (PDR)',
}

// English text is the i18n key
const GATE_PURPOSE: Record<GateId, string> = {
  mcr: 'Evaluating readiness to proceed from Pre-Phase A to Phase A.',
  srr: 'Evaluating whether the system requirements are complete, feasible and traceable to the mission objectives before preliminary design.',
  pdr: 'Evaluating whether the preliminary design meets the requirements and can proceed to detailed design.',
}

/** Old client-side MCR checklist — used only when the backend is unreachable. */
function evaluateMCRFallback(missionNeed: any, params: Record<string, any>, t: TFunction): GateCriterion[] {
  const mn = missionNeed || {}
  const get = (id: string) => { const p = params[id]; return p && typeof p.value === 'number' ? p.value : 0 }
  const alts: any[] = mn.alternatives || []
  const nonSpace = alts.some((a: any) => ['aerial_drone', 'aerial_aircraft', 'ground_sensor', 'ground_network', 'space_existing'].includes(a.type))
  const primary = (mn.objectives || []).filter((o: any) => o.priority === 'primary' && o.measurable_criterion).length
  const debris = get('debris.compliance_score')
  const c = (id: string, question: string, category: string, priority: string,
             status: GateCriterion['status'], evidence: string): GateCriterion => {
    const advisory = priority !== 'must_pass'
    const verdict = status === 'pass' ? 'pass' : advisory ? 'advisory' : status
    return { id, question, category, priority, advisory, status, verdict, evidence_found: evidence }
  }
  return [
    c('MCR-EC-01', t('Is the mission need clearly defined and justified?'), 'mission_need', 'must_pass',
      mn.problem_statement?.trim() ? 'pass' : 'fail',
      mn.problem_statement?.trim() ? t('Problem statement defined') : t('Problem statement is empty')),
    c('MCR-EC-02', t('Are the key stakeholders identified with their needs and constraints?'), 'mission_need', 'must_pass',
      (mn.stakeholders?.length || 0) >= 1 ? 'pass' : 'fail',
      t('{{n}} stakeholder(s) identified', { n: mn.stakeholders?.length || 0 })),
    c('MCR-EC-03', t('Are mission objectives defined with measurable success criteria?'), 'mission_need', 'must_pass',
      primary >= 1 ? 'pass' : 'fail',
      t('{{n}} primary objective(s) with measurable criteria', { n: primary })),
    c('MCR-EC-04', t('Have alternative solutions been considered, including non-space options?'), 'alternatives', 'must_pass',
      alts.length >= 2 && nonSpace ? 'pass' : 'fail',
      nonSpace ? t('{{n}} alternative(s), including a non-space option', { n: alts.length })
        : t('{{n}} alternative(s), no non-space option', { n: alts.length })),
    c('MCR-EC-05', t('Is the selected concept justified against the alternatives?'), 'alternatives', 'must_pass',
      mn.selected_alternative_id && mn.selection_rationale?.trim() ? 'pass' : 'fail',
      !mn.selected_alternative_id ? t('No concept selected')
        : mn.selection_rationale?.trim() ? t('Concept selected with rationale') : t('Concept selected, rationale missing')),
    c('MCR-EC-06', t('Is a preliminary Concept of Operations documented?'), 'conops', 'should_pass',
      mn.conops_summary?.trim() ? 'pass' : 'fail',
      mn.conops_summary?.trim() ? t('ConOps summary documented') : t('ConOps summary is empty')),
    c('MCR-EC-07', t('Has a feasible system concept been identified?'), 'feasibility', 'must_pass',
      get('systems.mass_margin_percent') > -50 ? 'pass' : 'fail',
      t('Mass margin {{mass}}%', { mass: get('systems.mass_margin_percent').toFixed(0) })),
    c('MCR-EC-08', t('Is the mission sustainable (debris, casualty risk)?'), 'sustainability', 'should_pass',
      debris >= 50 ? 'pass' : debris > 0 ? 'fail' : 'not_evaluated',
      t('Debris compliance score {{score}}/100', { score: debris.toFixed(0) })),
    c('MCR-EC-09', t('Are key requirements traceable to objectives?'), 'traceability', 'should_pass', 'manual',
      t('Requires manual review of requirement traceability')),
    c('MCR-EC-10', t('Are interface conflicts identified and managed?'), 'interfaces', 'should_pass', 'manual',
      t('Requires review of interface matrix')),
  ]
}

const STATUS_STYLE: Record<string, { bg: string; color: string }> = {
  pass: { bg: 'rgba(16,185,129,0.15)', color: '#10b981' },
  fail: { bg: 'rgba(239,68,68,0.15)', color: '#ef4444' },
  advisory: { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b' },
  manual: { bg: 'rgba(59,130,246,0.15)', color: '#3b82f6' },
  not_evaluated: { bg: 'rgba(107,114,128,0.15)', color: '#6b7280' },
}

export function GateReviewPanel({ studyId, onNavigate }: { studyId: string | null; onNavigate?: (tab: string) => void }) {
  const { t } = useTranslation()
  const { missionNeed } = useDesignStore()
  const params = useActiveParameters()
  const [gate, setGate] = useState<GateId>('pdr')

  const { data, isLoading, isError } = useGateReview(studyId, gate, missionNeed, params)
  const offline = isError && !data
  const criteria: GateCriterion[] = offline ? evaluateMCRFallback(missionNeed, params, t) : (data?.criteria || [])
  const shownGate: GateId = offline ? 'mcr' : gate

  const mustPass = criteria.filter(c => c.priority === 'must_pass')
  const shouldPass = criteria.filter(c => c.priority !== 'must_pass')
  const mustMet = mustPass.filter(c => c.status === 'pass').length
  const passCount = criteria.filter(c => c.status === 'pass').length
  const allMustPass = mustPass.length > 0 && mustMet === mustPass.length
  const pendingManual = !allMustPass && mustPass.length > 0 && mustPass.every(c => c.status === 'pass' || c.status === 'manual')
  const gateLabel = shownGate.toUpperCase()
  const tone = allMustPass ? '#10b981' : pendingManual ? '#3b82f6' : '#ef4444'

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>{t('Gate Review')}</h2>

      <div role="group" aria-label={t('Review gate')} style={{ display: 'flex', gap: '0.3rem', margin: '0.4rem 0 0.5rem 0' }}>
        {GATES.map(g => (
          <button key={g} onClick={() => setGate(g)} aria-pressed={gate === g} title={t(GATE_TITLE[g])} style={{
            padding: '0.3rem 0.8rem', fontSize: '0.72rem', fontWeight: 700, borderRadius: '4px',
            background: gate === g ? 'var(--accent, #3b82f6)' : 'var(--bg-secondary, #1f2937)',
            color: gate === g ? 'white' : '#9ca3af',
            border: 'none', cursor: 'pointer',
          }}>
            {g.toUpperCase()}
          </button>
        ))}
      </div>

      <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.2rem 0' }}>{t(GATE_TITLE[shownGate])}</h3>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        {t(GATE_PURPOSE[shownGate])}{' '}
        {t('Click "Go fix" on any failing criterion to navigate to the relevant step.')}
      </p>

      {offline && (
        <div role="status" style={{
          padding: '0.5rem 0.75rem', borderRadius: '6px', marginBottom: '0.75rem', fontSize: '0.75rem',
          background: 'rgba(245,158,11,0.1)', border: '1px solid #f59e0b', color: '#f59e0b',
        }}>
          {t('Gate review service unreachable: showing the built-in MCR checklist instead (offline fallback).')}
        </div>
      )}

      {isLoading && !offline && (
        <div style={{ color: '#9ca3af', fontSize: '0.8rem' }}>{t('Evaluating...')}</div>
      )}

      {criteria.length > 0 && (
        <>
          {/* Readiness indicator */}
          <div style={{
            padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem',
            background: `${tone}1a`, border: `1px solid ${tone}`,
            display: 'flex', alignItems: 'center', gap: '0.75rem',
          }}>
            <div style={{
              width: 48, height: 48, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: tone, color: 'white', fontSize: '1.5rem', fontWeight: 700, flexShrink: 0,
            }}>
              {allMustPass ? '✓' : pendingManual ? '?' : '✗'}
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: tone }}>
                {allMustPass ? t('Ready for {{gate}}', { gate: gateLabel })
                  : pendingManual ? t('Ready for {{gate}}, pending manual sign-off', { gate: gateLabel })
                  : t('Not Ready')}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#9ca3af' }}>
                {t('{{pass}}/{{total}} criteria met — {{mustMet}}/{{must}} mandatory',
                  { pass: passCount, total: criteria.length, mustMet, must: mustPass.length })}
              </div>
            </div>
          </div>

          <h3 style={{ fontSize: '0.9rem', margin: '0.75rem 0 0.4rem 0' }}>{t('Mandatory Criteria')}</h3>
          {mustPass.map(c => <CriterionRow key={c.id} criterion={c} onNavigate={onNavigate} />)}

          {shouldPass.length > 0 && (
            <>
              <h3 style={{ fontSize: '0.9rem', margin: '0.75rem 0 0.2rem 0' }}>{t('Recommended Criteria')}</h3>
              <p style={{ fontSize: '0.72rem', color: '#9ca3af', margin: '0 0 0.4rem 0' }}>
                {t('Recommended criteria are advisory: they are reported but do not block the gate.')}
              </p>
              {shouldPass.map(c => <CriterionRow key={c.id} criterion={c} onNavigate={onNavigate} />)}
            </>
          )}
        </>
      )}
    </div>
  )
}

function CriterionRow({ criterion: c, onNavigate }: { criterion: GateCriterion; onNavigate?: (tab: string) => void }) {
  const { t } = useTranslation()
  const kind = badgeKind(c)
  const s = STATUS_STYLE[kind] || STATUS_STYLE.not_evaluated
  const fix = c.status !== 'pass' ? fixTargetFor(c.id, c.category) : null
  // Backend messages carry an English template + params; translate when we know the template.
  const evidence = evidenceText(c, t)
  return (
    <div style={{
      padding: '0.5rem 0.75rem', borderRadius: '6px', marginBottom: '0.35rem',
      background: 'var(--bg-secondary, #1f2937)', border: '1px solid var(--border, #374151)',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
        <span style={{
          fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '3px',
          background: s.bg, color: s.color, whiteSpace: 'nowrap', marginTop: '0.1rem',
        }}>
          {t(STATUS_LABEL[kind] || 'N/A')}
        </span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 500 }}>{t(c.question)}</div>
          <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '0.1rem' }}>{evidence}</div>
        </div>
        <span style={{ fontSize: '0.65rem', color: '#6b7280', fontFamily: 'monospace' }}>{c.id}</span>
      </div>
      {fix && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.35rem',
          padding: '0.3rem 0.5rem', borderRadius: '4px',
          background: c.verdict === 'fail' ? 'rgba(239,68,68,0.06)' : 'rgba(59,130,246,0.06)',
        }}>
          <span style={{ fontSize: '0.72rem', color: '#9ca3af', flex: 1 }}>{t(fix.action)}</span>
          {onNavigate && (
            <button className="btn btn-sm" onClick={() => onNavigate(fix.tab)}
              style={{ fontSize: '0.68rem', background: c.verdict === 'fail' ? '#ef4444' : '#3b82f6', whiteSpace: 'nowrap' }}>
              {t('Go fix')}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
