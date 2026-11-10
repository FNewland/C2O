/**
 * ValidationPanel — validation activities and need validation (wave 3, 3.S5).
 *
 * Verification asks "did we build it right?" against the requirements; validation asks "did we
 * build the right thing?" with the people the mission is for, in their setting. So every activity
 * names its performer from the stakeholder register; an activity performed by the engineering team
 * alone is flagged. ORR and CRR appear as validation stages, not as review gates.
 *
 * Server: routers/validation.py (GET /studies/{id}/validation/activities, POST …/propose,
 * PATCH …/activities/{code}, GET …/need-validation, GET …/coverage).
 * Mounted in AitPanel (agent A, one line): <ValidationPanel studyId={studyId} />
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { Button, DataTable, Disclosure, Note, Panel, Select, StatusBadge, Tag } from '../components/ui'

const API = '/api'

interface Activity {
  id: string; code: string; title: string; title_fr: string; objectives: string[]; needs: string[]; moes: string[]
  requirement_codes: string[]; method: string; method_text: string; stage: string; stages: string[]; when: string
  performer: string; performer_ids: string[]; acceptance: string; status: string; engineers_only: boolean; origin: string
}
interface NeedRow { need_code: string; activity_codes: string[]; method: string; stages: string[]; stage_text: string }
interface Coverage {
  objectives: Record<string, { priority: string; activities: string[]; stakeholder_performed: boolean; in_orbit: boolean }>
  primary: string[]; uncovered_primary: string[]; needs_without_validation: string[]; ok: boolean; activities: number
}

// English text is the i18n key
const STATUS_LABEL: Record<string, string> = {
  proposed: 'proposed', planned: 'planned', in_progress: 'in progress', done: 'done', failed: 'failed',
}
// English text is the i18n key
const METHOD_LABEL: Record<string, string> = {
  walkthrough: 'walkthrough with stakeholders', scenario_trace: 'scenario tracing', simulated_products: 'simulated products',
  operational_rehearsal: 'operational rehearsal', in_orbit_matchup: 'in-orbit comparison', operational_assessment: 'operational assessment',
  results_review: 'results review', user_acceptance: 'user acceptance', other: 'other',
}
const STATUSES = ['proposed', 'planned', 'in_progress', 'done', 'failed']

export function ValidationPanel({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const fr = i18n.language === 'fr'
  const [busy, setBusy] = useState(false)
  const key = ['se-validation', studyId]
  const { data } = useQuery({
    queryKey: key,
    queryFn: async () => {
      const [a, n, c] = await Promise.all(['activities', 'need-validation', 'coverage'].map(p =>
        fetch(`${API}/studies/${studyId}/validation/${p}`).then(r => (r.ok ? r.json() : null))))
      return { activities: (a?.items ?? []) as Activity[], needs: (n?.items ?? []) as NeedRow[], coverage: c as Coverage | null }
    },
    enabled: !!studyId,
  })
  if (!studyId) return null
  const refresh = () => qc.invalidateQueries({ queryKey: key })
  const acts = data?.activities ?? []
  const cov = data?.coverage

  const propose = async () => {
    setBusy(true)
    try { await fetch(`${API}/studies/${studyId}/validation/propose`, { method: 'POST' }) }
    finally { setBusy(false); refresh() }
  }
  const setStatus = async (a: Activity, status: string) => {
    await fetch(`${API}/studies/${studyId}/validation/activities/${encodeURIComponent(a.code)}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }),
    })
    refresh()
  }

  return (
    <Panel level={2} title={t('Validation')}
      meta={t('Did we build the right thing? Needs → measures of effectiveness → validation with the stakeholders')}
      actions={<Button size="sm" onClick={propose} busy={busy}
        title={t('Proposes one activity for each primary objective that has none; the team then edits it')}>
        {t('Propose for the primary objectives')}</Button>}>
      {acts.length === 0 && <Note>{t('No validation activity yet. Propose writes one per primary objective, performed by the stakeholders who hold its needs.')}</Note>}
      {cov && cov.primary.length > 0 && (
        <div className="row gap-2 mb-2" role="list" aria-label={t('Coverage of the objectives')}>
          {Object.entries(cov.objectives).map(([o, v]) => (
            <span role="listitem" key={o}>
              <StatusBadge status={v.stakeholder_performed ? 'ok' : (v.priority === 'primary' ? 'caution' : 'neutral')}
                title={v.activities.join(', ') || t('no activity')}>
                {o} · {v.activities.length}
              </StatusBadge>
            </span>
          ))}
        </div>
      )}
      {cov && cov.uncovered_primary.length > 0 && (
        <Note tone="caution">{t('No stakeholder-performed validation yet for {{list}}.', { list: cov.uncovered_primary.join(', ') })}</Note>
      )}

      {acts.length > 0 && (
        <DataTable dense caption={t('Validation activities')} rows={acts} rowKey={a => a.code} columns={[
          { key: 'code', header: t('Activity'), sort: a => a.code,
            render: a => <span><span className="mono t-12">{a.code}</span> {(fr ? a.title_fr : a.title) || a.title}</span> },
          { key: 'obj', header: t('Objectives'), render: a => <span className="mono t-12">{a.objectives.join(', ') || '—'}</span> },
          { key: 'method', header: t('Method'), render: a => <span className="t-12" title={a.method_text}>{t(METHOD_LABEL[a.method] ?? a.method)}</span> },
          { key: 'stage', header: t('Stage'), sort: a => a.stage,
            render: a => <span className="row gap-1">{(a.stages.length ? a.stages : [a.stage]).map(s => <Tag key={s} mono>{s === 'PHASE_E' ? t('Phase E') : s}</Tag>)}</span> },
          { key: 'who', header: t('Performer'),
            render: a => <span className="t-12">{a.performer}{a.engineers_only && <> <StatusBadge status="caution">{t('engineers only')}</StatusBadge></>}</span> },
          { key: 'acc', header: t('Acceptance'), render: a => <span className="t-12">{a.acceptance}</span> },
          { key: 'status', header: t('Status'), sort: a => a.status,
            render: a => <Select aria-label={t('Status of {{code}}', { code: a.code })} value={a.status}
              onChange={e => void setStatus(a, e.target.value)}>
              {STATUSES.map(s => <option key={s} value={s}>{t(STATUS_LABEL[s])}</option>)}
            </Select> },
        ]} />
      )}

      {(data?.needs.length ?? 0) > 0 && (
        <Disclosure summary={t('Validation of each stakeholder need')} meta={String(data?.needs.length ?? 0)} ruled>
          <DataTable dense caption={t('Validation of each stakeholder need')} rows={data?.needs ?? []} rowKey={n => n.need_code} columns={[
            { key: 'need', header: t('Need'), render: n => <span className="mono t-12">{n.need_code}</span>, sort: n => n.need_code },
            { key: 'acts', header: t('Activities'), render: n => <span className="mono t-12">{n.activity_codes.join(', ') || '—'}</span> },
            { key: 'how', header: t('How'), render: n => <span className="t-12">{n.method}</span> },
            { key: 'when', header: t('When'), render: n => <span className="t-12">{n.stage_text}</span> },
          ]} />
        </Disclosure>
      )}
    </Panel>
  )
}

export default ValidationPanel
