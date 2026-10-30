/**
 * SEMPQuestionnaire — Step-by-step modal wizard for collecting
 * Systems Engineering Management Plan inputs.
 *
 * 5 pages: Model Philosophy, Risk & CM, Reviews & Schedule,
 * Organisation, Sustainability.
 */
import React, { useState, useEffect, useCallback } from 'react'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface SEMPAnswers {
  model_philosophy: Record<string, string>
  risk_matrix_size: string
  risk_tolerance: string
  ccb_membership: string
  baseline_dates: Record<string, string>
  review_dates: Record<string, string>
  mission_duration_override: number
  team_size: number
  se_responsible: string
  subcontractors: string
  disposal_approach: string
  passivation_approach: string
  twenty_five_year_compliance: boolean
}

interface SEMPQuestionnaireProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (answers: SEMPAnswers) => void
  subsystemTRLs: Record<string, number>
  orbitAltitude: number
  missionDurationYears?: number
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const DOMAINS = [
  'power', 'aocs', 'ttc', 'thermal', 'structure', 'propulsion', 'obc', 'payload',
] as const

const DOMAIN_LABELS: Record<string, string> = {
  power: 'Power', aocs: 'AOCS', ttc: 'TT&C', thermal: 'Thermal',
  structure: 'Structure', propulsion: 'Propulsion', obc: 'OBC', payload: 'Payload',
}

const MODEL_OPTIONS = ['EM+QM+FM', 'QM+FM', 'PFM', 'Custom'] as const

const REVIEW_GATES = ['SRR', 'PDR', 'CDR', 'QR', 'AR', 'FRR'] as const

const BASELINE_GATES = [
  { key: 'functional_srr', label: 'Functional baseline (SRR)' },
  { key: 'allocated_pdr', label: 'Allocated baseline (PDR)' },
  { key: 'product_cdr', label: 'Product baseline (CDR)' },
]

const PAGE_TITLES = [
  'Model Philosophy',
  'Risk & Configuration Management',
  'Reviews & Schedule',
  'Organisation',
  'Sustainability',
]

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function defaultModelPhilosophy(trl: number): string {
  if (trl >= 9) return 'PFM'
  if (trl >= 6) return 'QM+FM'
  return 'EM+QM+FM'
}

/** Rough 25-year natural decay estimate (below ~600 km decays in <25 yr) */
function estimateCompliance(altitudeKm: number): boolean {
  return altitudeKm <= 600
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function SEMPQuestionnaire({
  isOpen, onClose, onSubmit, subsystemTRLs, orbitAltitude, missionDurationYears,
}: SEMPQuestionnaireProps) {
  const [page, setPage] = useState(0)

  // Page 1 — Model philosophy
  const [modelPhilosophy, setModelPhilosophy] = useState<Record<string, string>>({})

  // Page 2 — Risk & CM
  const [riskMatrixSize, setRiskMatrixSize] = useState('5x5')
  const [riskTolerance, setRiskTolerance] = useState('Medium')
  const [ccbMembership, setCcbMembership] = useState('')
  const [baselineDates, setBaselineDates] = useState<Record<string, string>>({
    functional_srr: '', allocated_pdr: '', product_cdr: '',
  })

  // Page 3 — Reviews & schedule
  const [reviewDates, setReviewDates] = useState<Record<string, string>>(
    Object.fromEntries(REVIEW_GATES.map(g => [g, ''])),
  )
  const [missionDuration, setMissionDuration] = useState(missionDurationYears ?? 5)

  // Page 4 — Organisation
  const [teamSize, setTeamSize] = useState(10)
  const [seResponsible, setSeResponsible] = useState('')
  const [subcontractors, setSubcontractors] = useState('')

  // Page 5 — Sustainability
  const [disposalApproach, setDisposalApproach] = useState('Controlled re-entry')
  const [passivationApproach, setPassivationApproach] = useState('')
  const [compliance25, setCompliance25] = useState(estimateCompliance(orbitAltitude))

  /* Initialise model philosophy defaults from TRL when dialog opens */
  useEffect(() => {
    if (!isOpen) return
    const defaults: Record<string, string> = {}
    for (const d of DOMAINS) {
      const trl = subsystemTRLs[d] ?? 5
      defaults[d] = defaultModelPhilosophy(trl)
    }
    setModelPhilosophy(defaults)
    setCompliance25(estimateCompliance(orbitAltitude))
    setMissionDuration(missionDurationYears ?? 5)
    setPage(0)
  }, [isOpen, subsystemTRLs, orbitAltitude, missionDurationYears])

  const handleSubmit = useCallback(() => {
    const answers: SEMPAnswers = {
      model_philosophy: modelPhilosophy,
      risk_matrix_size: riskMatrixSize,
      risk_tolerance: riskTolerance,
      ccb_membership: ccbMembership,
      baseline_dates: baselineDates,
      review_dates: reviewDates,
      mission_duration_override: missionDuration,
      team_size: teamSize,
      se_responsible: seResponsible,
      subcontractors,
      disposal_approach: disposalApproach,
      passivation_approach: passivationApproach,
      twenty_five_year_compliance: compliance25,
    }
    onSubmit(answers)
  }, [
    modelPhilosophy, riskMatrixSize, riskTolerance, ccbMembership,
    baselineDates, reviewDates, missionDuration, teamSize,
    seResponsible, subcontractors, disposalApproach, passivationApproach,
    compliance25, onSubmit,
  ])

  if (!isOpen) return null

  /* ---- shared inline style tokens ---- */
  const labelStyle: React.CSSProperties = {
    fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem',
  }
  const sectionTitle: React.CSSProperties = {
    fontSize: '0.85rem', fontWeight: 600, color: '#d1d5db', marginBottom: '0.75rem',
  }

  /* ================================================================ */
  /*  Page renderers                                                   */
  /* ================================================================ */

  const renderPage1 = () => (
    <div>
      <div style={sectionTitle}>Subsystem Model Philosophy</div>
      <p style={{ fontSize: '0.72rem', color: '#6b7280', marginBottom: '0.75rem' }}>
        Select the build-philosophy for each domain. Defaults are derived from TRL.
      </p>
      <div style={{
        display: 'grid',
        gridTemplateColumns: '110px 50px repeat(4, 1fr)',
        gap: '0.35rem 0.5rem', alignItems: 'center',
      }}>
        {/* Header */}
        <span style={{ ...labelStyle, fontWeight: 600 }}>Subsystem</span>
        <span style={{ ...labelStyle, fontWeight: 600, textAlign: 'center' }}>TRL</span>
        {MODEL_OPTIONS.map(opt => (
          <span key={opt} style={{ ...labelStyle, fontWeight: 600, textAlign: 'center' }}>{opt}</span>
        ))}

        {DOMAINS.map(domain => {
          const trl = subsystemTRLs[domain] ?? 5
          return [
            <span key={`${domain}-name`} style={{ fontSize: '0.78rem', color: '#d1d5db' }}>
              {DOMAIN_LABELS[domain]}
            </span>,
            <span key={`${domain}-trl`} style={{
              fontSize: '0.78rem', color: '#3b82f6', textAlign: 'center', fontWeight: 600,
            }}>
              {trl}
            </span>,
            ...MODEL_OPTIONS.map(opt => (
              <label key={`${domain}-${opt}`} style={{
                display: 'flex', justifyContent: 'center', cursor: 'pointer',
              }}>
                <input
                  type="radio"
                  name={`model-${domain}`}
                  checked={modelPhilosophy[domain] === opt}
                  onChange={() => setModelPhilosophy(prev => ({ ...prev, [domain]: opt }))}
                  style={{ accentColor: '#3b82f6' }}
                />
              </label>
            )),
          ]
        })}
      </div>
    </div>
  )

  const renderPage2 = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div>
        <div style={sectionTitle}>Risk Matrix Size</div>
        <div style={{ display: 'flex', gap: '1.5rem' }}>
          {['3x3', '5x5'].map(sz => (
            <label key={sz} style={{ fontSize: '0.78rem', color: '#d1d5db', display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer' }}>
              <input type="radio" name="risk-size" checked={riskMatrixSize === sz}
                onChange={() => setRiskMatrixSize(sz)} style={{ accentColor: '#3b82f6' }} />
              {sz}
            </label>
          ))}
        </div>
      </div>

      <div>
        <div style={sectionTitle}>Risk Tolerance</div>
        <div style={{ display: 'flex', gap: '1.5rem' }}>
          {['Low', 'Medium', 'High'].map(t => (
            <label key={t} style={{ fontSize: '0.78rem', color: '#d1d5db', display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer' }}>
              <input type="radio" name="risk-tol" checked={riskTolerance === t}
                onChange={() => setRiskTolerance(t)} style={{ accentColor: '#3b82f6' }} />
              {t}
            </label>
          ))}
        </div>
      </div>

      <div>
        <div style={sectionTitle}>CCB Membership</div>
        <input className="input" placeholder="e.g. PM, SE, AIT lead, QA"
          value={ccbMembership} onChange={e => setCcbMembership(e.target.value)}
          style={{ width: '100%', fontSize: '0.78rem' }} />
      </div>

      <div>
        <div style={sectionTitle}>Baseline Freeze Dates</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {BASELINE_GATES.map(g => (
            <div key={g.key} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af', width: '180px' }}>{g.label}</span>
              <input className="input" type="date"
                value={baselineDates[g.key] || ''}
                onChange={e => setBaselineDates(prev => ({ ...prev, [g.key]: e.target.value }))}
                style={{ flex: 1, fontSize: '0.75rem' }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderPage3 = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div>
        <div style={sectionTitle}>Review Target Dates</div>
        <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: '0.5rem 0.75rem', alignItems: 'center' }}>
          {REVIEW_GATES.map(gate => (
            <React.Fragment key={gate}>
              <span style={{ fontSize: '0.78rem', color: '#d1d5db', fontWeight: 600 }}>{gate}</span>
              <input className="input" type="date"
                value={reviewDates[gate] || ''}
                onChange={e => setReviewDates(prev => ({ ...prev, [gate]: e.target.value }))}
                style={{ fontSize: '0.75rem' }} />
            </React.Fragment>
          ))}
        </div>
      </div>

      <div>
        <div style={sectionTitle}>Mission Duration Override</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <input className="input" type="number" min={0.5} step={0.5}
            value={missionDuration}
            onChange={e => setMissionDuration(Number(e.target.value))}
            style={{ width: '100px', fontSize: '0.78rem' }} />
          <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>years</span>
        </div>
      </div>
    </div>
  )

  const renderPage4 = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div>
        <div style={sectionTitle}>Team Size</div>
        <input className="input" type="number" min={1}
          value={teamSize} onChange={e => setTeamSize(Number(e.target.value))}
          style={{ width: '100px', fontSize: '0.78rem' }} />
      </div>

      <div>
        <div style={sectionTitle}>SE Responsible</div>
        <input className="input" placeholder="Name of lead systems engineer"
          value={seResponsible} onChange={e => setSeResponsible(e.target.value)}
          style={{ width: '100%', fontSize: '0.78rem' }} />
      </div>

      <div>
        <div style={sectionTitle}>Key Subcontractors</div>
        <textarea className="input" rows={4} placeholder="List key subcontractors, one per line"
          value={subcontractors} onChange={e => setSubcontractors(e.target.value)}
          style={{ width: '100%', fontSize: '0.78rem', resize: 'vertical' }} />
      </div>
    </div>
  )

  const renderPage5 = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div>
        <div style={sectionTitle}>Disposal Approach</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          {['Controlled re-entry', 'Natural decay', 'Graveyard orbit'].map(opt => (
            <label key={opt} style={{ fontSize: '0.78rem', color: '#d1d5db', display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer' }}>
              <input type="radio" name="disposal" checked={disposalApproach === opt}
                onChange={() => setDisposalApproach(opt)} style={{ accentColor: '#3b82f6' }} />
              {opt}
            </label>
          ))}
        </div>
      </div>

      <div>
        <div style={sectionTitle}>Passivation Approach</div>
        <input className="input" placeholder="e.g. Battery discharge, propellant venting"
          value={passivationApproach} onChange={e => setPassivationApproach(e.target.value)}
          style={{ width: '100%', fontSize: '0.78rem' }} />
      </div>

      <div>
        <div style={sectionTitle}>25-Year Compliance</div>
        <label style={{ fontSize: '0.78rem', color: '#d1d5db', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={compliance25}
            onChange={e => setCompliance25(e.target.checked)}
            style={{ accentColor: '#3b82f6' }} />
          Orbit naturally decays within 25 years
        </label>
        <p style={{ fontSize: '0.72rem', color: '#6b7280', marginTop: '0.25rem' }}>
          Auto-estimate based on {orbitAltitude} km altitude: {estimateCompliance(orbitAltitude) ? 'Compliant' : 'Non-compliant'}.
          Override manually if needed.
        </p>
      </div>
    </div>
  )

  const pages = [renderPage1, renderPage2, renderPage3, renderPage4, renderPage5]

  /* ================================================================ */
  /*  Layout                                                           */
  /* ================================================================ */

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      zIndex: 10000, display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{
        background: '#111827', border: '1px solid #374151',
        borderRadius: '8px', width: '92%', maxWidth: '720px', maxHeight: '85vh',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '0.75rem 1rem', borderBottom: '1px solid #374151',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#d1d5db' }}>
            SEMP Questionnaire
          </span>
          <button className="btn btn-sm" onClick={onClose}
            style={{ fontSize: '0.72rem', background: 'transparent', color: '#9ca3af', border: 'none', cursor: 'pointer' }}>
            Close
          </button>
        </div>

        {/* Progress bar */}
        <div style={{ padding: '0.5rem 1rem', borderBottom: '1px solid #1f2937' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
              Step {page + 1} of {PAGE_TITLES.length}
            </span>
            <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>&mdash;</span>
            <span style={{ fontSize: '0.75rem', color: '#3b82f6', fontWeight: 600 }}>
              {PAGE_TITLES[page]}
            </span>
          </div>
          <div style={{
            height: '4px', background: '#1f2937', borderRadius: '2px', overflow: 'hidden',
          }}>
            <div style={{
              height: '100%', width: `${((page + 1) / PAGE_TITLES.length) * 100}%`,
              background: '#3b82f6', borderRadius: '2px',
              transition: 'width 0.3s ease',
            }} />
          </div>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
          {pages[page]()}
        </div>

        {/* Footer — navigation */}
        <div style={{
          padding: '0.75rem 1rem', borderTop: '1px solid #374151',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <button className="btn btn-sm" disabled={page === 0}
            onClick={() => setPage(p => p - 1)}
            style={{
              fontSize: '0.75rem',
              opacity: page === 0 ? 0.35 : 1,
              cursor: page === 0 ? 'default' : 'pointer',
            }}>
            Previous
          </button>

          {page < PAGE_TITLES.length - 1 ? (
            <button className="btn btn-sm" onClick={() => setPage(p => p + 1)}
              style={{ fontSize: '0.75rem', background: '#3b82f6', color: '#fff' }}>
              Next
            </button>
          ) : (
            <button className="btn btn-sm" onClick={handleSubmit}
              style={{ fontSize: '0.75rem', background: '#10b981', color: '#fff', fontWeight: 600 }}>
              Generate SEMP
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default SEMPQuestionnaire
