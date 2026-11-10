/**
 * StakeholderEditor — the stakeholder register, the needs and the measures of effectiveness (wave 3, 3.S3).
 *
 * The register keeps five categories apart on purpose (decision authority, beneficiary, affected
 * party, rights-holder, non-human): a body that decides is not consulted like a beneficiary. Each
 * stakeholder states what it decides (authority) and how the team engages it. MOEs say how each
 * objective will be judged; an MOE that the stakeholders must define themselves is shown "to
 * co-define" and is never filled in by the team.
 *
 * Server: routers/moes.py (GET /studies/{id}/stakeholders, PUT …/stakeholders/{stk}, GET/POST/PATCH
 * …/moes). Mounted in MissionNeedCard (agent D, one line): <StakeholderEditor studyId={studyId} />
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Button, DataTable, Disclosure, Input, Note, Panel, Select, StatusBadge, Tag, askText } from './ui'

const API = '/api'

export interface Stakeholder {
  id: string; name: string; role: string; category: string; categories: string[]
  authority: string; engagement: string; need_ids: string[]; note: string; consent_status: string
}
export interface StakeholderNeed { id: string; text: string; stakeholder_ids: string[]; stakeholder: string; traces_to: string[] }
export interface Moe {
  id: string; code: string; measure: string; threshold: string; objectives: string[]; needs: string[]
  defined_by: string; placeholder: boolean; pending_parts: string[]; approval: string
}
interface Register {
  items: Stakeholder[]; needs: StakeholderNeed[]; moes: Moe[]
  counts: { stakeholders: number; needs: number; moes: number; placeholder_moes: number; categories: number; by_category: Record<string, number>; unclassified: number; needs_without_moe: string[] }
}

export const CATEGORIES = ['decision_authority', 'beneficiary', 'affected_party', 'rights_holder', 'non_human'] as const
// English text is the i18n key
export const CATEGORY_LABEL: Record<string, string> = {
  decision_authority: 'Decision authority', beneficiary: 'Beneficiary', affected_party: 'Affected party',
  rights_holder: 'Rights-holder', non_human: 'Non-human stakeholder',
}

const json = (method: string, body: unknown) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export function StakeholderEditor({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [busy, setBusy] = useState(false)
  const { data } = useQuery<Register | null>({
    queryKey: ['se-stakeholders', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/stakeholders`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId,
  })
  if (!studyId) return null
  const refresh = () => qc.invalidateQueries({ queryKey: ['se-stakeholders', studyId] })
  const items = data?.items ?? []
  const moes = data?.moes ?? []
  const c = data?.counts

  const saveStakeholder = async (s: Stakeholder, patch: Partial<Stakeholder>) => {
    await fetch(`${API}/studies/${studyId}/stakeholders/${encodeURIComponent(s.id)}`, json('PUT', patch))
    refresh()
  }
  const addStakeholder = async () => {
    const name = await askText(t('Name'), '', { title: t('Add a stakeholder') })
    if (!name) return
    setBusy(true)
    const n = items.length + 1
    try { await fetch(`${API}/studies/${studyId}/stakeholders/STK-${String(n).padStart(2, '0')}`, json('PUT', { name })) }
    finally { setBusy(false); refresh() }
  }
  const saveMoe = async (m: Moe, patch: Partial<Moe>) => {
    await fetch(`${API}/studies/${studyId}/moes/${encodeURIComponent(m.code)}`, json('PATCH', patch))
    refresh()
  }
  const addMoe = async () => {
    const measure = await askText(t('Measure'), '', { title: t('Add a measure of effectiveness') })
    if (!measure) return
    await fetch(`${API}/studies/${studyId}/moes`, json('POST', { measure }))
    refresh()
  }

  return (
    <Panel level={3} title={t('Stakeholders and measures of effectiveness')}
      meta={c ? t('{{n}} stakeholders in {{k}} categories · {{m}} MOEs', { n: c.stakeholders, k: c.categories, m: c.moes }) : undefined}
      actions={<Button size="sm" onClick={addStakeholder} busy={busy}>{t('Add a stakeholder')}</Button>}>
      {items.length === 0 && <Note>{t('No stakeholder yet. Name who decides, who benefits, who is affected and who holds rights over the lands or data concerned.')}</Note>}
      {c && c.unclassified > 0 && <Note tone="caution">{t('{{n}} stakeholders have no category yet.', { n: c.unclassified })}</Note>}

      {items.length > 0 && (
        <DataTable dense caption={t('Stakeholder register')} rows={items} rowKey={s => s.id} columns={[
          { key: 'name', header: t('Stakeholder'), sort: s => s.name,
            render: s => <span><span className="mono t-12 c-3">{s.id}</span> {s.name}</span> },
          { key: 'cat', header: t('Category'), sort: s => s.category,
            render: s => (
              <div className="stack gap-1">
                <Select aria-label={t('Category of {{name}}', { name: s.name })} value={s.category}
                  onChange={e => void saveStakeholder(s, { category: e.target.value })}>
                  <option value="">{t('Not classified')}</option>
                  {CATEGORIES.map(k => <option key={k} value={k}>{t(CATEGORY_LABEL[k])}</option>)}
                </Select>
                {s.categories.slice(1).map(k => <Tag key={k}>{t(CATEGORY_LABEL[k] ?? k)}</Tag>)}
              </div>) },
          { key: 'auth', header: t('Authority'),
            render: s => <Input aria-label={t('Authority of {{name}}', { name: s.name })} defaultValue={s.authority}
              onBlur={e => { if (e.target.value !== s.authority) void saveStakeholder(s, { authority: e.target.value }) }} /> },
          { key: 'eng', header: t('Engagement'),
            render: s => <Input aria-label={t('Engagement of {{name}}', { name: s.name })} defaultValue={s.engagement}
              onBlur={e => { if (e.target.value !== s.engagement) void saveStakeholder(s, { engagement: e.target.value }) }} /> },
          { key: 'needs', header: t('Needs'), render: s => <span className="mono t-12">{s.need_ids.join(', ') || '—'}</span> },
        ]} />
      )}

      {(data?.needs?.length ?? 0) > 0 && (
        <Disclosure summary={t('Stakeholder needs')} meta={String(data?.needs.length ?? 0)} ruled>
          <DataTable dense caption={t('Stakeholder needs')} rows={data?.needs ?? []} rowKey={n => n.id} columns={[
            { key: 'id', header: t('Need'), render: n => <span className="mono t-12">{n.id}</span>, sort: n => n.id },
            { key: 'text', header: t('Statement'), render: n => <span className="t-12">{n.text}</span> },
            { key: 'who', header: t('Held by'), render: n => <span className="mono t-12">{n.stakeholder_ids.join(', ') || '—'}</span> },
          ]} />
        </Disclosure>
      )}

      <section className="stack gap-2 mt-4" aria-label={t('Measures of effectiveness')}>
        <div className="row gap-2">
          <h3 className="t-13 w-600 m-0">{t('Measures of effectiveness')}</h3>
          <Button size="sm" variant="quiet" onClick={addMoe}>{t('Add an MOE')}</Button>
        </div>
        {(c?.placeholder_moes ?? 0) > 0 && (
          <Note tone="info">{t('MOEs marked "to co-define" are set by the stakeholders named, not by the engineering team.')}</Note>
        )}
        <DataTable dense caption={t('Measures of effectiveness')} rows={moes} rowKey={m => m.code}
          empty={t('No MOE yet: say how each objective will be judged.')} columns={[
            { key: 'code', header: t('MOE'), render: m => <span className="mono t-12">{m.code}</span>, sort: m => m.code },
            { key: 'measure', header: t('Measure'), render: m => <span className="t-12">{m.measure}</span> },
            { key: 'thr', header: t('Threshold'),
              render: m => m.placeholder
                ? <StatusBadge status="caution" title={m.pending_parts.join(' · ')}>{t('to co-define')}</StatusBadge>
                : <Input aria-label={t('Threshold of {{code}}', { code: m.code })} defaultValue={m.threshold}
                    onBlur={e => { if (e.target.value !== m.threshold) void saveMoe(m, { threshold: e.target.value }) }} /> },
            { key: 'obj', header: t('Objectives'), render: m => <span className="mono t-12">{m.objectives.join(', ')}</span> },
            { key: 'needs', header: t('Needs'), render: m => <span className="mono t-12">{m.needs.join(', ')}</span> },
            { key: 'by', header: t('Defined by'), render: m => <span className="t-12">{m.defined_by}</span> },
          ]} />
        {(c?.needs_without_moe?.length ?? 0) > 0 && (
          <p className="t-12 c-3 m-0">{t('Needs with no MOE yet: {{list}}', { list: c?.needs_without_moe.join(', ') })}</p>
        )}
      </section>
    </Panel>
  )
}

export default StakeholderEditor
