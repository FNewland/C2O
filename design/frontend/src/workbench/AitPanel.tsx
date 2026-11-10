/**
 * AitPanel — model philosophy, AIT test matrix and verification plan (W8a).
 *
 * Picture first: the models on a month line (breadboards, engineering model, protoflight model),
 * then the test matrix (test × model), then the verification items by close-out stage
 * (PDR, CDR, QR, AR, IOV). "Propose" writes the default protoflight philosophy and the 12-test
 * matrix; rows the team edits are kept by later proposals. The Word verification plan is one click.
 *
 * Server: routers/ait.py (GET /studies/{id}/ait, POST …/ait/propose, PATCH …/ait/models/{id},
 * GET …/ait/verification-plan[?fmt=docx]). Mounted from VVPanel (one line).
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { Button, DataTable, Disclosure, Input, Note, Panel, Tag, Tabs, tabPanelProps } from '../components/ui'
import { ReliabilityPanel } from './ReliabilityPanel'
import { ThermalModelPanel } from './ThermalModelPanel'
import { ValidationPanel } from './ValidationPanel'

const API = '/api'

interface AitModel {
  id: string; code: string; name: string; name_fr: string; level: string; due_month: number | null
  purpose: string; purpose_fr: string; philosophy: string; origin: string
}
interface AitTest {
  id: string; code: string; name: string; name_fr: string; category: string; models: string[]; level: string
  stage: string; facility: string; level_source: string; requirement_codes: string[]; origin: string
}
interface VpItem { code: string; text: string; methods: string[]; stage: string; level: string; facility: string; tests: string[] }

const STAGES = ['PRR', 'SRR', 'PDR', 'CDR', 'QR', 'AR', 'IOV'] as const
// English text is the i18n key
const STAGE_LABEL: Record<string, string> = {
  PRR: 'Preliminary requirements review', SRR: 'System requirements review',
  PDR: 'Preliminary design review', CDR: 'Critical design review', QR: 'Qualification review',
  AR: 'Acceptance review', IOV: 'In-orbit verification', unassigned: 'No stage yet',
}
// English text is the i18n key
const CATEGORY_LABEL: Record<string, string> = {
  environmental: 'environmental', functional: 'functional', performance: 'performance', emc: 'EMC',
  deployment: 'deployment', end_to_end: 'end to end', mission: 'mission', physical: 'physical',
  analysis: 'analysis', inspection: 'inspection', review: 'review', in_orbit: 'in orbit',
}
// English text is the i18n key
const LEVEL_LABEL: Record<string, string> = {
  unit: 'unit', subsystem: 'subsystem', system: 'system', segment: 'segment', mission: 'mission',
}

export function AitPanel({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const fr = i18n.language === 'fr'
  const [busy, setBusy] = useState(false)
  const [stage, setStage] = useState<string>('PDR')

  const { data: ait } = useQuery({
    queryKey: ['ait', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/ait`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId,
  })
  const { data: vp } = useQuery({
    queryKey: ['ait-vp', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/ait/verification-plan`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId,
  })
  if (!studyId) return null

  const models: AitModel[] = ait?.models ?? []
  const tests: AitTest[] = ait?.tests ?? []
  const items: VpItem[] = vp?.items ?? []
  const byStage: Record<string, number> = vp?.counts?.by_stage ?? {}
  const refresh = () => { qc.invalidateQueries({ queryKey: ['ait', studyId] }); qc.invalidateQueries({ queryKey: ['ait-vp', studyId] }) }

  const propose = async () => {
    setBusy(true)
    try { await fetch(`${API}/studies/${studyId}/ait/propose`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }) }
    finally { setBusy(false); refresh() }
  }
  const setDue = async (m: AitModel, month: number) => {
    await fetch(`${API}/studies/${studyId}/ait/models/${m.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ due_month: month }),
    })
    refresh()
  }
  const lastMonth = Math.max(36, ...models.map(m => m.due_month ?? 0))
  const stageItems = items.filter(i => i.stage === stage)
  const stageTabs = [...STAGES.filter(st => (st !== 'PRR' && st !== 'SRR') || byStage[st]), ...(byStage.unassigned ? ['unassigned'] : [])]

  return (
    <Panel level={2} title={t('AIT and verification plan')}
      meta={t('Model philosophy, test matrix and the verification items by close-out stage')}
      actions={<div className="row gap-2">
        <Button size="sm" onClick={propose} busy={busy}
          title={t('Writes the default protoflight philosophy and test matrix; rows you changed are kept')}>
          {models.length ? t('Update the proposal') : t('Propose')}
        </Button>
        <Button size="sm" onClick={() => window.open(`${API}/studies/${studyId}/ait/verification-plan?fmt=docx&lang=${fr ? 'fr' : 'en'}`, '_blank')}>
          {t('Verification plan (DOCX)')}
        </Button>
      </div>}>
      {models.length === 0 && (
        <Note>{t('No model philosophy yet. Propose writes breadboards, an engineering model and a protoflight model with a 12-test matrix that you can then edit.')}</Note>
      )}

      {models.length > 0 && (
        <section aria-label={t('Model philosophy')} className="stack gap-2 mb-4">
          <h3 className="t-13 w-600 m-0">{t('Model philosophy')}: <span className="c-2">{models[0]?.philosophy ?? ''}</span></h3>
          <div className="c2o-ait-line" role="list" aria-label={t('Models on the month line')}
            style={{ position: 'relative', height: 44, borderBottom: '1px solid var(--c2o-line, #8884)' }}>
            {models.map(m => (
              <div key={m.id} role="listitem" title={(fr ? m.purpose_fr : m.purpose) || m.purpose}
                style={{ position: 'absolute', left: `${((m.due_month ?? 0) / lastMonth) * 100}%`, transform: 'translateX(-50%)', bottom: 4, textAlign: 'center' }}>
                <Tag mono accent>{m.code}</Tag>
                <div className="t-12 c-3">{t('month {{m}}', { m: m.due_month ?? '?' })}</div>
              </div>
            ))}
          </div>
          <DataTable dense caption={t('Model philosophy')} rows={models} rowKey={m => m.id} columns={[
            { key: 'code', header: t('Model'), render: m => <span className="w-500">{m.code} · {(fr ? m.name_fr : m.name) || m.name}</span>, sort: m => m.code },
            { key: 'level', header: t('Level'), render: m => t(LEVEL_LABEL[m.level] ?? m.level) },
            { key: 'due', header: t('Due (month)'), num: true, sort: m => m.due_month,
              render: m => <Input numeric aria-label={t('Due month of {{model}}', { model: m.code })} defaultValue={m.due_month ?? ''}
                style={{ width: '5em' }}
                onBlur={e => { const v = parseInt(e.target.value, 10); if (!Number.isNaN(v) && v !== m.due_month) void setDue(m, v) }} /> },
            { key: 'purpose', header: t('Purpose'), render: m => <span className="t-12">{(fr ? m.purpose_fr : m.purpose) || m.purpose}</span> },
          ]} />
        </section>
      )}

      {tests.length > 0 && (
        <Disclosure summary={t('Test matrix')} meta={t('{{n}} tests × {{m}} models', { n: tests.length, m: models.length })} ruled>
          <DataTable dense caption={t('Test matrix')} rows={tests} rowKey={x => x.id} columns={[
            { key: 'test', header: t('Test'), render: x => <span><span className="mono t-12">{x.code}</span> {(fr ? x.name_fr : x.name) || x.name}</span>, sort: x => x.code },
            { key: 'cat', header: t('Category'), render: x => t(CATEGORY_LABEL[x.category] ?? x.category), sort: x => x.category },
            ...models.map(m => ({ key: `m-${m.code}`, header: m.code, render: (x: AitTest) => (x.models.includes(m.code) ? '✕' : '') })),
            { key: 'level', header: t('Level'), render: x => t(LEVEL_LABEL[x.level] ?? x.level) },
            { key: 'stage', header: t('Stage'), render: x => x.stage, sort: x => x.stage },
            { key: 'src', header: t('Level source'), render: x => <span className="t-12 c-2">{x.level_source}</span> },
            { key: 'req', header: t('Verifies'), render: x => <span className="mono t-12">{x.requirement_codes.join(', ') || '—'}</span> },
          ]} />
        </Disclosure>
      )}

      <section aria-label={t('Verification items by stage')} className="stack gap-2 mt-4">
        <h3 className="t-13 w-600 m-0">{t('Verification items by stage')} <span className="c-3 t-12">({items.length})</span></h3>
        <Tabs idBase="ait-stage" variant="segmented" label={t('Close-out stage')} value={stage} onChange={setStage}
          items={stageTabs.map(s => ({ id: s, label: `${s === 'unassigned' ? t('none') : s} · ${byStage[s] ?? 0}` }))} />
        <div {...tabPanelProps('ait-stage', stage)}>
          <p className="t-12 c-3 m-0">{t(STAGE_LABEL[stage] ?? stage)}</p>
          <DataTable dense caption={t('Verification items by stage')} rows={stageItems} rowKey={i => i.code}
            empty={t('No item closes at this stage.')} columns={[
              { key: 'code', header: t('Code'), render: i => <span className="mono t-12">{i.code}</span>, sort: i => i.code },
              { key: 'text', header: t('Requirement'), render: i => <span className="t-12">{i.text}</span> },
              { key: 'm', header: t('Method'), render: i => i.methods.join('+') || '—', sort: i => i.methods.join('') },
              { key: 'l', header: t('Level'), render: i => t(LEVEL_LABEL[i.level] ?? i.level), sort: i => i.level },
              { key: 't', header: t('Tests'), render: i => <span className="mono t-12">{i.tests.join(', ') || '—'}</span> },
            ]} />
        </div>
      </section>

      {/* wave 3 (3.A5, 3.A6): reliability and FMEA, thermal model — PDR evidence */}
      <div className="stack gap-4 mt-4">
        <ReliabilityPanel studyId={studyId} />
        <ThermalModelPanel studyId={studyId} />
        {/* wave 3 (3.S5): validation activities and need validation (agent S) */}
        <ValidationPanel studyId={studyId} />
      </div>
    </Panel>
  )
}
