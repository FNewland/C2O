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
import { useTranslation, Trans } from 'react-i18next'
import { useDesignStore } from '../stores/designStore'
import type { FMECARunResponse, StudyFailureMode } from '../types/analyses'
import { fs } from '../theme/tokens'

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

export function FMECAPanel({ studyId, optionId }: { studyId?: string | null; optionId?: string | null } = {}) {
  const { t } = useTranslation()
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
      const r = await fetch(`/api/studies/${studyId}/analyses/fmeca/run${optionId ? `?option_id=${encodeURIComponent(optionId)}` : ''}`, {
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

  if (loading) return <div style={{ padding: '1rem', color: 'var(--text-3)' }}>{t('Analysing failure modes...')}</div>

  if (!result) return (
    <div style={{ padding: '2rem', color: 'var(--text-3)' }}>
      <h3 style={{ fontSize: fs.value, marginBottom: '0.5rem', color: 'var(--text-2)' }}>{t('FMECA — Failure Mode, Effects & Criticality Analysis')}</h3>
      <p style={{ fontSize: fs.label, marginBottom: '0.75rem' }}>
        {t('FMECA identifies potential failure modes in your design and assesses their risk using the Risk Priority Number (RPN = Severity x Occurrence x Detection).')}
      </p>
      <div style={{ fontSize: fs.label, marginBottom: '0.75rem' }}>
        <p style={{ fontWeight: 600, marginBottom: '0.3rem' }}>{t('How to address FMECA issues:')}</p>
        <ol style={{ paddingLeft: '1.2rem', lineHeight: 1.8 }}>
          <li><Trans i18nKey="<0>Review top risks</0> — focus on failure modes with RPN > 60 (critical) or RPN > 30 (major)" components={{ 0: <strong /> }} /></li>
          <li><Trans i18nKey="<0>Add redundancy</0> — the tool recommends where redundancy reduces risk most effectively (e.g., 3-of-4 reaction wheels instead of 3-of-3)" components={{ 0: <strong /> }} /></li>
          <li><Trans i18nKey="<0>Select higher-TRL components</0> — TRL 9 (flight-proven) components have lower occurrence scores" components={{ 0: <strong /> }} /></li>
          <li><Trans i18nKey="<0>Improve detection</0> — add health monitoring (voltage/current sensors, temperature telemetry, watchdog timers)" components={{ 0: <strong /> }} /></li>
          <li><Trans i18nKey="<0>Accept risk</0> — for 1U/educational missions, some single-point failures may be acceptable with documented rationale" components={{ 0: <strong /> }} /></li>
        </ol>
      </div>
      <p style={{ fontSize: fs.label, color: 'var(--status-caution)' }}>
        {t('Waiting for FMECA analysis... If this persists, check that the backend is running and the /api/fmeca/analyze endpoint is available.')}
      </p>
    </div>
  )

  const riskColor = (rpn: number) => rpn >= 60 ? 'var(--status-alarm)' : rpn >= 30 ? 'var(--status-caution)' : 'var(--status-ok)'

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: fs.value, marginBottom: '0.25rem' }}>{t('FMECA — Design Risk Awareness')}</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.75rem' }}>
        {t('Failure modes for current architecture. Use this to inform redundancy and architecture decisions. Critical items (RPN ≥ 60) should drive architecture changes.')}
      </p>

      {/* SCDF-177: study-driven run */}
      {studyId && (
        <div className="card" style={{ borderLeft: '3px solid var(--cat-2)', marginBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
            <h3 style={{ fontSize: fs.body, color: 'var(--cat-2)', margin: 0 }}>{t('From the study model')}</h3>
            <span style={{ fontSize: fs.label, color: 'var(--text-2)' }}>{t('failure modes per element, functions allocated, single points on critical elements')}</span>
            <span style={{ flex: 1 }} />
            <button disabled={studyBusy} onClick={runFromStudy}
                    style={{ cursor: 'pointer', fontSize: fs.label, padding: '0.2rem 0.6rem', borderRadius: 4, border: '1px solid var(--cat-2)', background: 'color-mix(in srgb, var(--cat-2) 13%, transparent)', color: 'var(--cat-2)' }}>
              {studyBusy ? t('Running…') : studyRun ? t('Re-run from study') : t('Run from study')}
            </button>
          </div>
          {studyError && <div style={{ color: 'var(--status-alarm)', fontSize: fs.label }}>{studyError}</div>}
          {studyRun && (
            <>
              <div style={{ display: 'flex', gap: '0.75rem', fontSize: fs.label, marginBottom: '0.4rem', flexWrap: 'wrap' }}>
                <span>{t('{{count}} modes', { count: studyRun.summary.fmeca_modes ?? studyRun.modes.length })}</span>
                <span style={{ color: (studyRun.summary.fmeca_single_point_failures ?? 0) > 0 ? 'var(--status-caution)' : 'var(--status-ok)' }}>{t('{{count}} single points', { count: studyRun.summary.fmeca_single_point_failures ?? 0, defaultValue_one: '{{count}} single point' })}</span>
                <span style={{ color: (studyRun.summary.fmeca_critical_modes ?? 0) > 0 ? 'var(--status-alarm)' : 'var(--status-ok)' }}>{t('{{n}} on critical elements', { n: studyRun.summary.fmeca_critical_modes ?? 0 })}</span>
                <span>{t('max RPN {{rpn}}', { rpn: studyRun.summary.fmeca_max_rpn })}</span>
                <span style={{ color: 'var(--text-3)' }}>{t('{{count}} conflicts published', { count: studyRun.conflicts.length, defaultValue_one: '{{count}} conflict published' })}</span>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
                <thead>
                  <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
                    <th style={th}>{t('Element')}</th><th style={th}>{t('Failure mode')}</th><th style={th}>{t('Functions')}</th>
                    <th style={thC}>{t('S')}</th><th style={thC}>{t('O')}</th><th style={thC}>{t('D')}</th><th style={thC}>RPN</th><th style={th}>{t('Flags')}</th>
                  </tr>
                </thead>
                <tbody>
                  {studyRun.modes.map((m: StudyFailureMode) => (
                    <tr key={m.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)', background: m.single_point && m.critical ? 'color-mix(in srgb, var(--status-alarm) 7%, transparent)' : undefined }}>
                      <td style={td}>{m.element_name}<span style={{ color: 'var(--text-3)', marginLeft: 4, fontSize: fs.label }}>{m.subsystem && m.subsystem !== m.element_name ? m.subsystem : m.domain}</span></td>
                      <td style={td}>{m.mode}</td>
                      <td style={{ ...td, color: 'var(--text-2)' }}>{m.functions.length ? m.functions.join(', ') : '—'}</td>
                      <td style={tdC}>{m.severity}</td><td style={tdC}>{m.occurrence}</td><td style={tdC}>{m.detection}</td>
                      <td style={{ ...tdC, color: riskColor(m.rpn), fontWeight: 700 }}>{m.rpn}</td>
                      <td style={td}>
                        {m.single_point && <span style={{ color: m.critical ? 'var(--status-alarm)' : 'var(--status-caution)', fontWeight: 600 }}>{m.critical ? t('single point · critical') : t('single point')}</span>}
                        {m.redundant && <span style={{ color: 'var(--status-ok)' }}>{m.redundancy_type ? t('{{type}} redundant', { type: m.redundancy_type }) : `x${m.quantity}`}</span>}
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
        <div style={{ padding: '0.5rem 0.75rem', background: 'var(--surface-2)', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: fs.title, fontWeight: 700, color: 'var(--text)' }}>{result.failure_modes.length}</div>
          <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>{t('Failure modes')}</div>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: 'var(--surface-2)', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: fs.title, fontWeight: 700, color: result.critical_count > 0 ? 'var(--status-alarm)' : 'var(--status-ok)' }}>{result.critical_count}</div>
          <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>{t('Critical (RPN ≥ 60)')}</div>
        </div>
        <div style={{ padding: '0.5rem 0.75rem', background: 'var(--surface-2)', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: fs.title, fontWeight: 700, color: 'var(--status-caution)' }}>{result.total_rpn}</div>
          <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>{t('Total RPN')}</div>
        </div>
      </div>

      {/* Top risks */}
      {result.top_risks.length > 0 && (
        <div className="card" style={{ borderLeft: '3px solid var(--status-alarm)', marginBottom: '0.75rem' }}>
          <h3 style={{ fontSize: fs.body, color: 'var(--status-alarm)', marginBottom: '0.3rem' }}>{t('Top Risks')}</h3>
          {result.top_risks.slice(0, 5).map(fm => (
            <div key={fm.id} style={{ padding: '0.3rem 0', borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)', fontSize: fs.label }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600 }}>{fm.component}: {fm.mode}</span>
                <span style={{ fontFamily: 'monospace', color: riskColor(fm.rpn), fontWeight: 700 }}>RPN {fm.rpn}</span>
              </div>
              <div style={{ color: 'var(--text-2)', fontSize: fs.label }}>{fm.system_effect}</div>
              <div style={{ color: 'var(--text-3)', fontSize: fs.label }}>{t('Mitigation: {{mitigation}}', { mitigation: fm.mitigation })}</div>
            </div>
          ))}
        </div>
      )}

      {/* Redundancy recommendations */}
      {result.redundancy_recommendations && result.redundancy_recommendations.length > 0 && (
        <div className="card" style={{ borderLeft: '3px solid var(--interactive)', marginBottom: '0.75rem' }}>
          <h3 style={{ fontSize: fs.body, color: 'var(--interactive)', marginBottom: '0.3rem' }}>{t('Redundancy Recommendations')}</h3>
          {result.redundancy_recommendations.map((s: any, i: number) => (
            <div key={i} style={{ padding: '0.2rem 0', fontSize: fs.label }}>
              <span style={{ fontWeight: 600 }}>{s.component}:</span> {s.recommendation}
              {s.expected_rpn_reduction && <span style={{ color: 'var(--status-ok)', marginLeft: '0.3rem' }}>(RPN -{s.expected_rpn_reduction})</span>}
            </div>
          ))}
        </div>
      )}

      {/* Full failure mode table */}
      <div className="card">
        <h3 style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>{t('All Failure Modes')}</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
              <th style={th}>{t('Component')}</th>
              <th style={th}>{t('Failure Mode')}</th>
              <th style={thC}>{t('S')}</th>
              <th style={thC}>{t('O')}</th>
              <th style={thC}>{t('D')}</th>
              <th style={thC}>RPN</th>
              <th style={th}>{t('Mitigation')}</th>
            </tr>
          </thead>
          <tbody>
            {result.failure_modes.map(fm => (
              <tr key={fm.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                <td style={td}>{fm.component}</td>
                <td style={td}>{fm.mode}</td>
                <td style={tdC}>{fm.severity}</td>
                <td style={tdC}>{fm.occurrence}</td>
                <td style={tdC}>{fm.detection}</td>
                <td style={{ ...tdC, color: riskColor(fm.rpn), fontWeight: 700 }}>{fm.rpn}</td>
                <td style={{ ...td, fontSize: fs.label, color: 'var(--text-2)' }}>{fm.mitigation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
