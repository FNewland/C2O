import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'

interface ExitCriterion {
  id: string
  question: string
  category: string
  priority: string
  status: 'pass' | 'fail' | 'manual' | 'not_evaluated'
  evidence: string
  fixAction?: string
  fixTab?: string
}

function evaluateMCR(missionNeed: any, params: Record<string, any>): ExitCriterion[] {
  const mn = missionNeed || {}
  const get = (id: string) => { const p = params[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  return [
    {
      id: 'MCR-EC-01', question: 'Is the mission need clearly defined and justified?',
      category: 'Mission Need', priority: 'must_pass',
      status: mn.problem_statement?.trim() ? 'pass' : 'fail',
      evidence: mn.problem_statement?.trim() ? 'Problem statement defined' : 'Problem statement is empty',
      fixAction: 'Define the problem statement in the Mission Need step',
      fixTab: 'need',
    },
    {
      id: 'MCR-EC-02', question: 'Are the key stakeholders identified?',
      category: 'Mission Need', priority: 'must_pass',
      status: (mn.stakeholders?.length || 0) >= 1 ? 'pass' : 'fail',
      evidence: `${mn.stakeholders?.length || 0} stakeholder(s) identified`,
      fixAction: 'Add stakeholders in the Mission Need step',
      fixTab: 'need',
    },
    {
      id: 'MCR-EC-03', question: 'Are mission objectives defined with measurable success criteria?',
      category: 'Mission Need', priority: 'must_pass',
      status: (mn.objectives?.filter((o: any) => o.priority === 'primary' && o.measurable_criterion)?.length || 0) >= 1 ? 'pass' : 'fail',
      evidence: `${mn.objectives?.filter((o: any) => o.measurable_criterion)?.length || 0} objective(s) with criteria`,
      fixAction: 'Add measurable criteria to primary objectives',
      fixTab: 'need',
    },
    {
      id: 'MCR-EC-04', question: 'Have alternatives been considered including non-space options?',
      category: 'Alternatives', priority: 'must_pass',
      status: (() => {
        const alts = mn.alternatives || []
        const nonSpace = alts.some((a: any) => ['aerial_drone', 'aerial_aircraft', 'ground_sensor', 'ground_network', 'space_existing'].includes(a.type))
        return alts.length >= 2 && nonSpace ? 'pass' : 'no'
      })() === 'pass' ? 'pass' : 'fail',
      evidence: `${mn.alternatives?.length || 0} alternatives, non-space: ${mn.alternatives?.some((a: any) => !a.type?.startsWith('space_dedicated')) ? 'yes' : 'no'}`,
      fixAction: 'Run the Mission Trade analysis in the Concept step',
      fixTab: 'concept',
    },
    {
      id: 'MCR-EC-05', question: 'Is the selected concept justified?',
      category: 'Alternatives', priority: 'must_pass',
      status: mn.selected_alternative_id && mn.selection_rationale?.trim() ? 'pass' : 'fail',
      evidence: mn.selected_alternative_id ? 'Concept selected with rationale' : 'No concept selected',
      fixAction: 'Select a preferred alternative in the Concept step',
      fixTab: 'concept',
    },
    {
      id: 'MCR-EC-06', question: 'Is a preliminary Concept of Operations documented?',
      category: 'ConOps', priority: 'should_pass',
      status: mn.conops_summary?.trim() ? 'pass' : 'fail',
      evidence: mn.conops_summary?.trim() ? 'ConOps summary documented' : 'ConOps is empty',
      fixAction: 'Document the ConOps in the ConOps tab',
      fixTab: 'conops',
    },
    {
      id: 'MCR-EC-07', question: 'Has a feasible system concept been identified?',
      category: 'Feasibility', priority: 'must_pass',
      status: get('systems.mass_margin_percent') > -50 ? 'pass' : 'fail',
      evidence: `Mass margin: ${get('systems.mass_margin_percent').toFixed(0)}%`,
      fixAction: 'Run the design loop to check feasibility, then adjust requirements if margin is negative',
      fixTab: 'design',
    },
    {
      id: 'MCR-EC-08', question: 'Is the mission sustainable (debris, casualty risk)?',
      category: 'Sustainability', priority: 'should_pass',
      status: get('debris.compliance_score') >= 50 ? 'pass' : get('debris.compliance_score') > 0 ? 'fail' : 'not_evaluated',
      evidence: `Debris compliance: ${get('debris.compliance_score').toFixed(0)}/100`,
      fixAction: 'Run the design loop to evaluate sustainability, check orbit altitude and deorbit plan',
      fixTab: 'design',
    },
    {
      id: 'MCR-EC-09', question: 'Are key requirements traceable to objectives?',
      category: 'Requirements', priority: 'should_pass',
      status: 'manual',
      evidence: 'Requires manual review of requirement traceability',
      fixAction: 'Review the requirements in the Requirements tab — each should trace to an objective',
      fixTab: 'requirements',
    },
    {
      id: 'MCR-EC-10', question: 'Are interface conflicts identified and managed?',
      category: 'Interfaces', priority: 'should_pass',
      status: 'manual',
      evidence: 'Requires review of interface matrix',
      fixAction: 'Review the Interface Matrix tab and resolve open conflicts',
      fixTab: 'interfaces',
    },
  ]
}

const STATUS_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  pass: { bg: 'rgba(16,185,129,0.15)', color: '#10b981', label: 'PASS' },
  fail: { bg: 'rgba(239,68,68,0.15)', color: '#ef4444', label: 'FAIL' },
  manual: { bg: 'rgba(59,130,246,0.15)', color: '#3b82f6', label: 'REVIEW' },
  not_evaluated: { bg: 'rgba(107,114,128,0.15)', color: '#6b7280', label: 'N/A' },
}

export function GateReviewPanel({ studyId, onNavigate }: { studyId: string | null; onNavigate?: (tab: string) => void }) {
  const { missionNeed } = useDesignStore()
  const params = useActiveParameters()

  const criteria = evaluateMCR(missionNeed, params)
  const mustPass = criteria.filter(c => c.priority === 'must_pass')
  const shouldPass = criteria.filter(c => c.priority === 'should_pass')
  const allMustPass = mustPass.every(c => c.status === 'pass')
  const passCount = criteria.filter(c => c.status === 'pass').length

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Gate Review: MCR</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Mission Concept Review — evaluating readiness to proceed from Pre-Phase A to Phase A.
        Click "Go fix" on any failing criterion to navigate to the relevant step.
      </p>

      {/* Readiness indicator */}
      <div style={{
        padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem',
        background: allMustPass ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
        border: `1px solid ${allMustPass ? '#10b981' : '#ef4444'}`,
        display: 'flex', alignItems: 'center', gap: '0.75rem',
      }}>
        <div style={{
          width: 48, height: 48, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: allMustPass ? '#10b981' : '#ef4444', color: 'white', fontSize: '1.5rem', fontWeight: 700,
        }}>
          {allMustPass ? '\u2713' : '\u2717'}
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '1rem', color: allMustPass ? '#10b981' : '#ef4444' }}>
            {allMustPass ? 'Ready for MCR' : 'Not Ready'}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#9ca3af' }}>
            {passCount}/{criteria.length} criteria met — {mustPass.filter(c => c.status === 'pass').length}/{mustPass.length} mandatory
          </div>
        </div>
      </div>

      {/* Criteria */}
      <h3 style={{ fontSize: '0.9rem', margin: '0.75rem 0 0.4rem 0' }}>Mandatory Criteria</h3>
      {mustPass.map(c => <CriterionRow key={c.id} criterion={c} onNavigate={onNavigate} />)}

      <h3 style={{ fontSize: '0.9rem', margin: '0.75rem 0 0.4rem 0' }}>Recommended Criteria</h3>
      {shouldPass.map(c => <CriterionRow key={c.id} criterion={c} onNavigate={onNavigate} />)}
    </div>
  )
}

function CriterionRow({ criterion: c, onNavigate }: { criterion: ExitCriterion; onNavigate?: (tab: string) => void }) {
  const s = STATUS_STYLE[c.status]
  const showFix = c.status === 'fail' || c.status === 'manual'
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
          {s.label}
        </span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 500 }}>{c.question}</div>
          <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '0.1rem' }}>{c.evidence}</div>
        </div>
        <span style={{ fontSize: '0.65rem', color: '#6b7280', fontFamily: 'monospace' }}>{c.id}</span>
      </div>
      {showFix && c.fixAction && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.35rem',
          padding: '0.3rem 0.5rem', borderRadius: '4px',
          background: c.status === 'fail' ? 'rgba(239,68,68,0.06)' : 'rgba(59,130,246,0.06)',
        }}>
          <span style={{ fontSize: '0.72rem', color: '#9ca3af', flex: 1 }}>{c.fixAction}</span>
          {onNavigate && c.fixTab && (
            <button className="btn btn-sm" onClick={() => onNavigate(c.fixTab!)}
              style={{ fontSize: '0.68rem', background: c.status === 'fail' ? '#ef4444' : '#3b82f6', whiteSpace: 'nowrap' }}>
              Go fix
            </button>
          )}
        </div>
      )}
    </div>
  )
}
