/**
 * Traceability › Mission need (Nov 2026 worksheet/screen audit): what the team entered in
 * Mission Definition (problem, stakeholders, objectives, the alternative chosen and why),
 * read-only. Before this, those answers disappeared once the study existed, yet
 * Worksheet 1.4 and decisions D-1.4-* ask students to revisit them.
 * Source: GET /api/studies/{id} → mission_need, requirements.mission_type.
 */
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Disclosure } from './ui/Disclosure'

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
  stakeholders?: { id: string; name: string; role?: string; needs?: string[] }[]
  objectives?: { id: string; text: string; priority?: string; measurable_criterion?: string }[]
  alternatives_considered?: { id: string; name: string; decision?: string; decision_rationale?: string }[]
}

export function MissionNeedCard({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const { data } = useQuery<{ mission_need?: Need; requirements?: { mission_type?: string } } | null>({
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
  return (
    <div className="c2o-need mb-3" data-where="mission-need" data-testid="mission-need">
      <Disclosure defaultOpen ruled summary={t('Mission need')}
        meta={t('from Mission Definition, read-only')}>
        <dl className="c2o-need__dl">
          <dt>{t('Problem Statement')}</dt><dd>{need.problem_statement?.trim() || empty}</dd>
          <dt>{t('Operational Context')}</dt><dd>{need.operational_context?.trim() || empty}</dd>
          {mtype && (<><dt>{t('Mission type')}</dt><dd>{t(TYPE_LABEL[mtype] ?? mtype)}</dd></>)}
          <dt>{t('Stakeholders')}</dt>
          <dd>
            {stakeholders.length === 0 ? empty : (
              <ul className="list-reset c2o-need__list">
                {stakeholders.map(s => (
                  <li key={s.id}><span className="w-600">{s.name}</span>
                    {s.role && <span className="c-3"> · {t(ROLE_LABEL[s.role] ?? s.role)}</span>}
                    {(s.needs ?? []).filter(Boolean).length > 0 && <span> — {(s.needs ?? []).filter(Boolean).join('; ')}</span>}
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
          <dt>{t('Alternative chosen')}</dt>
          <dd>
            {chosen ? (<>
              <span className="w-600">{chosen.name}</span>
              {chosen.decision_rationale && <span> — {chosen.decision_rationale}</span>}
              <span className="c-3"> {t('({{n}} alternatives considered)', { n: alts.length })}</span>
            </>) : empty}
          </dd>
        </dl>
        <p className="t-12 c-3 m-0 mt-1">{t('Entered when the study was created. The objectives below carry on into the requirements.')}</p>
      </Disclosure>
    </div>
  )
}
