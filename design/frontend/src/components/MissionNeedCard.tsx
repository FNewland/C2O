/**
 * Traceability › Mission need (Nov 2026 worksheet/screen audit): what the team entered in
 * Mission Definition (problem, stakeholders, objectives, the alternative chosen and why),
 * read-only. Before this, those answers disappeared once the study existed, yet
 * Worksheet 1.4 and decisions D-1.4-* ask students to revisit them.
 * Source: GET /api/studies/{id} → mission_need, requirements.mission_type.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Disclosure } from './ui/Disclosure'
import { MissionDefinitionEditor } from './MissionDefinitionEditor'
import { CLASS_LABELS, DISPOSAL_LABELS, orbitSummary } from '../workbench/missionDef'
import { ConopsPhases } from '../workbench/ConopsPhases'

const API = '/api'

// English text is the i18n key (the same labels as Mission Definition)
const ROLE_LABEL: Record<string, string> = {
  sponsor: 'Sponsor / Funder', user: 'End User', operator: 'Operator', science_pi: 'Science PI',
  regulator: 'Regulator', partner: 'Partner Organisation',
}
// English text is the i18n key
const TYPE_LABEL: Record<string, string> = {
  earth_observation: 'Earth Observation', communications: 'Communications', navigation: 'Navigation',
  science_planetary: 'Science (Planetary)', science_heliophysics: 'Science (Heliophysics)',
  technology_demo: 'Technology Demo', lunar: 'Lunar Mission',
}

interface Need {
  problem_statement?: string
  operational_context?: string
  stakeholders?: { id: string; name: string; role?: string; needs?: string[]; constraints?: string[] }[]
  objectives?: { id: string; text: string; priority?: string; measurable_criterion?: string }[]
  success_criteria?: string[]
  conops_summary?: string
  alternatives_considered?: { id: string; name: string; decision?: string; decision_rationale?: string; pros?: string[]; cons?: string[]; feasibility_score?: number }[]
}

export function MissionNeedCard({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const [editing, setEditing] = useState(false)
  const { data } = useQuery<{ mission_need?: Need; requirements?: any } | null>({
    queryKey: ['study', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId,
  })
  const need = data?.mission_need
  if (!need) return null
  const stakeholders = (need.stakeholders ?? []).filter(s => s.name)
  const objectives = (need.objectives ?? []).filter(o => o.text)
  const alts = need.alternatives_considered ?? []
  const chosen = alts.find(a => a.decision === 'selected')
  const mtype = data?.requirements?.mission_type
  const empty = <span className="c-3">{t('not entered')}</span>
  const req = data?.requirements
  const payloads: any[] = req?.payloads ?? []
  return (
    <div className="c2o-need mb-3" data-where="mission-need" data-testid="mission-need">
      <Disclosure defaultOpen ruled summary={t('Mission need')}
        meta={t('from Mission Definition')}>
        <div className="flex mb-1">
          <span className="grow" />
          {!editing && studyId && (
            <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => setEditing(true)} data-testid="edit-mission">
              {t('Edit mission definition')}
            </button>
          )}
        </div>
        {editing && studyId ? (
          <MissionDefinitionEditor studyId={studyId} study={data} onDone={() => setEditing(false)} />
        ) : (<>
        <dl className="c2o-need__dl">
          <dt>{t('Problem Statement')}</dt><dd>{need.problem_statement?.trim() || empty}</dd>
          <dt>{t('Operational Context')}</dt><dd>{need.operational_context?.trim() || empty}</dd>
          {mtype && (<><dt>{t('Mission type')}</dt><dd>{t(TYPE_LABEL[mtype] ?? mtype)}</dd></>)}
          {req?.orbit && (<><dt>{t('Orbit')}</dt><dd data-testid="mission-orbit">{orbitSummary(req)}</dd></>)}
          {req && (<><dt>{t('Spacecraft')}</dt><dd>{t('Class: {{cls}} · lifetime {{years}} years', { cls: CLASS_LABELS[req.spacecraft_class] ? t(CLASS_LABELS[req.spacecraft_class]) : req.spacecraft_class, years: req.design_lifetime_years })}
            {req.disposal_method && <span className="c-3"> · {t('disposal: {{m}}', { m: DISPOSAL_LABELS[req.disposal_method] ? t(DISPOSAL_LABELS[req.disposal_method]) : req.disposal_method })}</span>}
            {req.launch_vehicle && <span className="c-3"> · {t('launch: {{l}}', { l: req.launch_vehicle })}</span>}</dd></>)}
          {payloads.length > 0 && (<><dt>{t('Payload')}</dt><dd>
            <ul className="list-reset c2o-need__list">
              {payloads.map((p, i) => (
                <li key={i}><span className="w-600">{p.name}</span>
                  <span className="c-3"> · {p.mass_kg} kg · {p.power_w} W{p.power_peak_w ? ` (${t('peak')} ${p.power_peak_w} W)` : ''}
                    {p.gsd_m ? ` · GSD ${p.gsd_m} m` : ''}{p.swath_km ? ` · ${t('swath')} ${p.swath_km} km` : ''}
                    {p.wavelengths_nm?.length ? ` · ${p.wavelengths_nm.join(' / ')} nm` : ''}
                    {p.data_per_image_mb ? ` · ${p.data_per_image_mb} ${t('MB per image')}` : ''}</span>
                </li>
              ))}
            </ul></dd></>)}
          {(req?.link?.downlink_frequency_mhz || req?.link?.downlink_rate_bps) && (<><dt>{t('Communication link')}</dt><dd>
            {[req.link.band, req.link.downlink_frequency_mhz && `↓ ${req.link.downlink_frequency_mhz} MHz`, req.link.downlink_rate_bps && `${req.link.downlink_rate_bps} bit/s`,
              req.link.uplink_frequency_mhz && `↑ ${req.link.uplink_frequency_mhz} MHz`].filter(Boolean).join(' · ')}</dd></>)}
          <dt>{t('Stakeholders')}</dt>
          <dd>
            {stakeholders.length === 0 ? empty : (
              <ul className="list-reset c2o-need__list">
                {stakeholders.map(s => (
                  <li key={s.id}><span className="w-600">{s.name}</span>
                    {s.role && <span className="c-3"> · {t(ROLE_LABEL[s.role] ?? s.role)}</span>}
                    {(s.needs ?? []).filter(Boolean).length > 0 && <span> — {(s.needs ?? []).filter(Boolean).join('; ')}</span>}
                    {(s.constraints ?? []).filter(Boolean).length > 0 && <span className="c-3"> · {t('constraints: {{c}}', { c: (s.constraints ?? []).filter(Boolean).join('; ') })}</span>}
                  </li>
                ))}
              </ul>
            )}
          </dd>
          <dt>{t('Objectives')}</dt>
          <dd>
            {objectives.length === 0 ? empty : (
              <ul className="list-reset c2o-need__list">
                {objectives.map(o => (
                  <li key={o.id}>
                    {o.priority && <span className="c2o-tag">{o.priority === 'primary' ? t('Primary') : o.priority === 'secondary' ? t('Secondary', { context: 'priority' }) : t('Constraint', { context: 'priority' })}</span>}{' '}
                    {o.text}
                    {o.measurable_criterion && <span className="c-3"> — {t('measured by: {{c}}', { c: o.measurable_criterion })}</span>}
                  </li>
                ))}
              </ul>
            )}
          </dd>
          <dt>{t('Success criteria')}</dt>
          <dd data-testid="mission-success-criteria">
            {(need.success_criteria ?? []).filter(Boolean).length === 0 ? empty : (
              <ul className="list-reset c2o-need__list">
                {(need.success_criteria ?? []).filter(Boolean).map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            )}
          </dd>
          <dt>{t('ConOps summary')}</dt><dd data-testid="mission-conops-summary">{need.conops_summary?.trim() || empty}</dd>
          <dt>{t('Alternative chosen')}</dt>
          <dd>
            {chosen ? (<>
              <span className="w-600">{chosen.name}</span>
              {chosen.decision_rationale && <span> — {chosen.decision_rationale}</span>}
              <span className="c-3"> {t('({{n}} alternatives considered)', { n: alts.length })}</span>
              {((chosen.pros ?? []).length > 0 || (chosen.cons ?? []).length > 0) && (
                <div className="t-12 c-2">
                  {(chosen.pros ?? []).length > 0 && <span>{t('pros: {{p}}', { p: (chosen.pros ?? []).join('; ') })}</span>}
                  {(chosen.cons ?? []).length > 0 && <span> · {t('cons: {{c}}', { c: (chosen.cons ?? []).join('; ') })}</span>}
                </div>
              )}
            </>) : empty}
          </dd>
        </dl>
        <p className="t-12 c-3 m-0 mt-1">{t('Entered when the study was created and editable here; every analysis reads these values. The objectives below carry on into the requirements.')}</p>
        </>)}
        <ConopsPhases studyId={studyId} />
      </Disclosure>
    </div>
  )
}
