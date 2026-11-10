/**
 * ProjectPanel — schedule-lite, work packages, long-lead items and the bottom-up cost (W11a).
 *
 * Picture first: the milestones on a month line (reviews of the gate profile, QR, AR, the Flight
 * Readiness Review, model deliveries, launch). Then the cost of the selected equipment in EUR and
 * the reporting currency (CAD), the five longest-lead items and, one click deeper, the WBS.
 * Settings: project start, currency, "launch provided by the agency" (removes the launch cost).
 *
 * Server: routers/schedule.py (GET /studies/{id}/schedule, PUT …/schedule/settings,
 * POST …/schedule/propose). Mounted from the Budget panel's Cost tab.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { Button, DataTable, Disclosure, Field, Input, Note, Panel, Select, Tag, fmtNum } from '../components/ui'
import { CostModel } from './CostModel'

const API = '/api'

interface Milestone { id?: string; code: string; kind: string; name: string; name_fr: string; month: number | null; date: string; origin?: string }
interface WorkPackage { id?: string; code: string; parent_code: string; name: string; name_fr: string; owner_seat: string; start_month: number | null; end_month: number | null }
interface LongLead { name: string; min_weeks: number; max_weeks: number; source: string }
interface Money { keur: number; kcad: number }
interface NeedBy { name: string; lead_time_weeks: number; model: string | null; model_month?: number; need_by_month?: number; order_by_month?: number; freeze_by_month?: number; order_by_date?: string; freeze_by_date?: string; before_project_start?: boolean }
interface SchedWarning { code: string; kind: string; month: number | null; text: { en: string; fr: string } }

// English text is the i18n key
const KIND_LABEL: Record<string, string> = { review: 'review', model: 'model', launch: 'launch', filing: 'licence filing', other: 'other' }

export function ProjectPanel({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const fr = i18n.language === 'fr'
  const [busy, setBusy] = useState(false)

  const { data } = useQuery({
    queryKey: ['schedule', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/schedule`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId,
  })
  if (!studyId) return null
  const refresh = () => qc.invalidateQueries({ queryKey: ['schedule', studyId] })

  const settings = data?.settings ?? {}
  const milestones: Milestone[] = data?.milestones ?? []
  const wps: WorkPackage[] = data?.work_packages ?? []
  const lead: LongLead[] = data?.long_lead ?? []
  const cost = data?.cost ?? {}
  const cad = (settings.currency ?? 'EUR') === 'CAD'
  const money = (m?: Money) => (m ? (cad ? `${fmtNum(m.kcad, 1)} kCAD` : `${fmtNum(m.keur, 1)} kEUR`) : '—')
  const needBy: NeedBy[] = data?.need_by ?? []
  const warnings: SchedWarning[] = data?.warnings ?? []
  const lastMonth = Math.max(37, ...milestones.map(m => m.month ?? 0))
  const firstMonth = Math.min(0, ...milestones.map(m => m.month ?? 0))
  const pos = (month: number | null) => (((month ?? 0) - firstMonth) / Math.max(1, lastMonth - firstMonth)) * 100

  const save = async (patch: Record<string, unknown>) => {
    await fetch(`${API}/studies/${studyId}/schedule/settings`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch),
    })
    refresh()
  }
  const propose = async () => {
    setBusy(true)
    try { await fetch(`${API}/studies/${studyId}/schedule/propose`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }) }
    finally { setBusy(false); refresh() }
  }

  return (
    <Panel level={2} title={t('Project: schedule, work packages and cost')}
      meta={t('Milestones per review gate, the WBS, long-lead items and the cost of the selected equipment')}
      actions={<Button size="sm" onClick={propose} busy={busy}
        title={t('Milestones from the gate profile (with QR, AR and FRR) and work packages from the product tree; rows you changed are kept')}>
        {milestones.length ? t('Update the proposal') : t('Propose')}
      </Button>}>
      <div className="row wrap gap-4 mb-3">
        <Field label={t('Project start')} help={t('Year and month (YYYY-MM)')}>
          <Input defaultValue={settings.start_date ?? ''} key={`start-${settings.start_date}`} style={{ width: '8em' }}
            onBlur={e => { if (e.target.value && e.target.value !== settings.start_date) void save({ start_date: e.target.value }) }} />
        </Field>
        <Field label={t('Currency')}>
          <Select value={settings.currency ?? 'EUR'} onChange={e => void save({ currency: e.target.value })}>
            <option value="EUR">EUR</option>
            <option value="CAD">CAD</option>
          </Select>
        </Field>
        <label className="row gap-1 t-13" style={{ alignSelf: 'end' }}>
          <input type="checkbox" checked={!!settings.launch_provided} onChange={e => void save({ launch_provided: e.target.checked })} />
          {t('Launch provided by the agency (no launch cost)')}
        </label>
      </div>

      {milestones.length === 0 ? (
        <Note>{t('No schedule yet. Propose dates the review gates, the model deliveries and the launch from the project start.')}</Note>
      ) : (
        <section aria-label={t('Milestones')} className="mb-4">
          <div role="list" aria-label={t('Milestones on the month line')}
            style={{ position: 'relative', height: 64, borderBottom: '1px solid var(--c2o-line, #8884)', margin: '0 2em' }}>
            {milestones.map((m, i) => (
              <div key={m.id ?? m.code} role="listitem" title={`${(fr ? m.name_fr : m.name) || m.name} · ${m.date}`}
                style={{ position: 'absolute', left: `${pos(m.month)}%`, transform: 'translateX(-50%)',
                  bottom: i % 2 ? 26 : 2, textAlign: 'center', whiteSpace: 'nowrap' }}>
                <Tag mono accent={m.kind === 'review' || m.kind === 'launch'}>{m.kind === 'filing' ? t('licence') : m.code}</Tag>
                <div className="t-12 c-3">{m.date}</div>
              </div>
            ))}
          </div>
          <Disclosure summary={t('Milestone table')} meta={t('{{n}} milestones', { n: milestones.length })} ruled>
            <DataTable dense caption={t('Milestones')} rows={milestones} rowKey={m => m.id ?? m.code} columns={[
              { key: 'code', header: t('Milestone'), render: m => <span><span className="mono t-12">{m.code}</span> {(fr ? m.name_fr : m.name) || m.name}</span>, sort: m => m.month },
              { key: 'kind', header: t('Kind'), render: m => t(KIND_LABEL[m.kind] ?? m.kind) },
              { key: 'month', header: t('Month'), num: true, render: m => m.month ?? '—', sort: m => m.month },
              { key: 'date', header: t('Date'), render: m => m.date, sort: m => m.date },
            ]} />
          </Disclosure>
        </section>
      )}

      {warnings.length > 0 && (
        <Note tone="caution" role="status">
          <ul className="m-0">
            {warnings.map(w => <li key={`${w.kind}-${w.code}`}>{fr ? w.text.fr : w.text.en}</li>)}
          </ul>
        </Note>
      )}

      <section aria-label={t('Cost')} className="mb-4">
        <dl className="c2o-stats">
          <div><dt>{t('Flight hardware')}</dt><dd>{money(cost.flight_hardware)}</dd></div>
          <div><dt>{t('Ground hardware')}</dt><dd>{money(cost.ground_hardware)}</dd></div>
          <div><dt>{t('Launch')}</dt><dd>{money(cost.launch)}</dd></div>
          <div><dt>{t('Total')}</dt><dd>{money(cost.total)}</dd></div>
          <div><dt>P50 / P90</dt><dd>{money(cost.p50)} / {money(cost.p90)}</dd></div>
        </dl>
        {cost.launch?.basis && <p className="t-12 c-3 m-0">{t('Launch')}: {cost.launch.basis}</p>}
        {(cost.missing_prices?.length ?? 0) > 0 && (
          <Note tone="caution">{t('{{n}} unit(s) have a mass but no price; they are not costed: {{names}}', {
            n: cost.missing_prices.length, names: cost.missing_prices.map((m: { name: string }) => m.name).join(', ') })}</Note>
        )}
      </section>

      {lead.length > 0 && (
        <section aria-label={t('Long-lead items')} className="mb-4">
          <h3 className="t-13 w-600 m-0 mb-2">{t('Long-lead items')}</h3>
          <DataTable dense caption={t('Long-lead items')} rows={lead} rowKey={l => l.name} columns={[
            { key: 'n', header: t('Item'), render: l => l.name },
            { key: 'w', header: t('Lead time (weeks)'), num: true, sort: l => l.max_weeks,
              render: l => (l.min_weeks === l.max_weeks ? String(l.max_weeks) : `${l.min_weeks}–${l.max_weeks}`) },
            { key: 's', header: t('Source'), render: l => (l.source === 'kb' ? t('catalogue') : t('element')) },
          ]} />
        </section>
      )}

      {needBy.length > 0 && (
        <section aria-label={t('Need-by dates')} className="mb-4">
          <h3 className="t-13 w-600 m-0 mb-2">{t('Need-by dates')}</h3>
          <p className="t-12 c-3 m-0 mb-2">{t('Each part is needed one month before the first model built with flight-representative hardware; the order goes out its lead time earlier and the specification freezes one month before the order.')}</p>
          <DataTable dense caption={t('Need-by dates')} rows={needBy} rowKey={l => l.name} columns={[
            { key: 'n', header: t('Item'), render: l => l.name },
            { key: 'w', header: t('Lead time (weeks)'), num: true, render: l => String(l.lead_time_weeks), sort: l => l.lead_time_weeks },
            { key: 'm', header: t('Model'), render: l => l.model ? `${l.model} · ${t('month {{m}}', { m: l.model_month ?? '?' })}` : '—' },
            { key: 'f', header: t('Freeze by'), render: l => l.freeze_by_month != null ? `${t('month {{m}}', { m: l.freeze_by_month })}${l.freeze_by_date ? ` · ${l.freeze_by_date}` : ''}` : '—', sort: l => l.freeze_by_month ?? null },
            { key: 'o', header: t('Order by'), render: l => l.order_by_month != null ? <span className={l.before_project_start ? 'c-alarm' : undefined}>{t('month {{m}}', { m: l.order_by_month })}{l.order_by_date ? ` · ${l.order_by_date}` : ''}</span> : '—', sort: l => l.order_by_month ?? null },
          ]} />
        </section>
      )}

      <CostModel studyId={studyId} />

      {wps.length > 0 && (
        <Disclosure summary={t('Work breakdown structure')} meta={t('{{n}} work packages', { n: wps.length })} ruled>
          <DataTable dense caption={t('Work breakdown structure')} rows={wps} rowKey={w => w.id ?? w.code} columns={[
            { key: 'code', header: t('WBS'), render: w => <span className="mono t-12">{w.code}</span> },
            { key: 'name', header: t('Work package'), render: w => <span style={{ paddingLeft: w.parent_code ? '1.5em' : 0 }}>{(fr ? w.name_fr : w.name) || w.name}</span> },
            { key: 'owner', header: t('Owner seat'), render: w => <span className="t-12 c-2">{w.owner_seat}</span> },
            { key: 'span', header: t('Months'), render: w => `${w.start_month ?? '?'}–${w.end_month ?? '?'}` },
          ]} />
        </Disclosure>
      )}
    </Panel>
  )
}
