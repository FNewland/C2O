/**
 * PassPlan — the per-pass downlink plan (W3.04): the day in the life from the union of the
 * station passes, each pass with its class (OPS / DUMP / SHORT / ANOMALY / LEOP) and the virtual
 * channel served first after the real-time HK (delayed HK = VC1, payload files = VC2), the daily
 * closure cases and the 7-day backlog of the HK and payload queues. The operators' choices are
 * the study's ``pass_plan`` row (Mission analysis & ops); every number comes from
 * GET /studies/{id}/data-budget (services/data_budget.py).
 */
import { useTranslation } from 'react-i18next'
import { DataTable, NoData, Note, Select, StatusBadge, type Column } from '../components/ui'
import { createCdr, live, useDataBudget, type CdrView, type DbCase, type DbPass } from './cdrApi'
import { Section } from './cdrParts'
import { bil, fmt, type CdrPanelCtx } from './cdrUtil'

// English text is the i18n key: pass classes (cdr_rules.yaml data_budget.pass_classes)
const CLASS_LABEL: Record<string, string> = {
  OPS: 'Operations pass', DUMP: 'Payload dump', SHORT: 'Short pass', ANOMALY_SAFE: 'Anomaly / safe', LEOP_COMMISSIONING: 'LEOP / commissioning',
}
// English text is the i18n key: what the pass serves after the real-time HK
const VC_LABEL: Record<string, string> = { VC1: 'Delayed HK first', VC2: 'Payload data first' }

export function PassPlan({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const { data, error } = useDataBudget(ctx.studyId)
  if (error) return <Note tone="alarm">{(error as Error).message}</Note>
  if (!data) return <p className="t-13 c-3">{t('Loading…')}</p>
  const planRow = live(view.rows.pass_plan)[0]
  const overrides: Record<string, { class?: string; first?: string }> = (planRow?.data.overrides as Record<string, { class?: string; first?: string }>) ?? {}
  const classes = live(view.rows.pass_classes).map(r => String(r.data.name))
  const classOpts = (classes.length ? classes : Object.keys(CLASS_LABEL)).map(c => ({ value: c, label: t(CLASS_LABEL[c] ?? c) }))
  const save = (idx: number, change: { class?: string; first?: string }) => ctx.run(`pass-${idx}`, async () => {
    const next = { ...overrides, [String(idx)]: { ...(overrides[String(idx)] ?? {}), ...change } }
    if (planRow) await ctx.patchData('pass_plan', planRow.id, { overrides: next })
    else await createCdr(ctx.studyId!, 'pass_plan', { overrides: next })
  })
  const dil = data.day_in_the_life
  const cols: Column<DbPass>[] = [
    { key: 'l', header: t('Local time'), render: r => <span className="mono">{r.local}</span> },
    { key: 'm', header: t('min'), num: true, render: r => fmt(r.minutes, 1) },
    { key: 'e', header: t('Max el. (°)'), num: true, render: r => fmt(r.max_elevation_deg, 0) },
    { key: 's', header: t('Stations'), render: r => <span className="t-12">{r.stations.join(', ')}</span> },
    { key: 'c', header: t('Class'), render: r => (
      <Select dense aria-label={t('Class of the pass at {{time}}', { time: r.local })} value={r.class}
        onChange={e => save(r.index, { class: e.target.value })}>
        {!classOpts.some(o => o.value === r.class) && <option value={r.class}>{r.class}</option>}
        {classOpts.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </Select>) },
    { key: 'v', header: t('After real-time HK'), render: r => (
      <Select dense aria-label={t('Delayed HK or payload first at {{time}}', { time: r.local })} value={r.first_vc}
        onChange={e => save(r.index, { first: e.target.value })}>
        {Object.entries(VC_LABEL).map(([k, v]) => <option key={k} value={k}>{t(v)}</option>)}
      </Select>) },
    { key: 'u', header: t('Usable min'), num: true, render: r => fmt(r.usable_min, 1) },
    { key: 'ch', header: t('Channel MB'), num: true, render: r => fmt(r.channel_mb, 2) },
    { key: 'rt', header: t('Real-time HK MB'), num: true, render: r => fmt(r.rt_hk_mb, 3) },
    { key: 'dh', header: t('Delayed HK MB'), num: true, render: r => fmt(r.delayed_hk_mb, 3) },
    { key: 'p', header: t('Payload MB'), num: true, render: r => fmt(r.payload_mb, 2) },
  ]
  const caseCols: Column<DbCase>[] = [
    { key: 'id', header: t('Case'), render: r => <span className="mono w-500">{r.id}</span> },
    { key: 'l', header: t('Description'), render: r => bil(r.label, i18n.language) },
    { key: 'cap', header: t('Capacity'), num: true, render: r => fmt(r.capacity_mb, 2) },
    { key: 'rt', header: t('Real-time HK'), num: true, render: r => fmt(r.rt_hk_mb, 2) },
    { key: 'st', header: t('Stored HK'), num: true, render: r => fmt(r.stored_hk_mb, 2) },
    { key: 'sc', header: t('Science'), num: true, render: r => fmt(r.science_mb, 2) },
    { key: 'o', header: t('Other'), num: true, render: r => fmt(r.other_mb, 2) },
    { key: 'm', header: t('Margin'), num: true, render: r => (
      <StatusBadge status={r.status === 'pass' ? 'ok' : r.status === 'warn' ? 'caution' : r.status === 'fail' ? 'alarm' : 'nodata'}>
        {r.margin_pct == null ? '–' : `${fmt(r.margin_pct, 1)} %`}</StatusBadge>) },
  ]
  return (
    <>
      <Section id="ops-passplan" title={t('Pass plan: a day in the life')}
        note={t('The union of the station passes on a representative day (local time, UTC{{off}}). Per pass the real-time HK goes first (VC0), then the channel the operators choose: delayed HK (VC1) or payload data (VC2), then the other. Before the {{av}} % availability.',
          { off: dil.utc_offset_h >= 0 ? `+${dil.utc_offset_h}` : String(dil.utc_offset_h), av: fmt(data.framing.availability * 100, 0) })}>
        <DataTable dense rows={dil.windows} rowKey={r => String(r.index)} columns={cols} caption={t('Pass plan')}
          empty={<NoData label={t('No contact window: add ground stations')} />} />
        {dil.windows.length > 0 && (
          <p className="t-12 c-2 m-0 pt-1" data-testid="pass-plan-totals">
            {t('Day: {{min}} min, {{ch}} MB on the channel, {{rt}} MB real-time HK, {{dh}} MB delayed HK, {{p}} MB payload.', {
              min: fmt(dil.totals.minutes, 1), ch: fmt(dil.totals.channel_mb, 2), rt: fmt(dil.totals.rt_hk_mb, 2),
              dh: fmt(dil.totals.delayed_hk_mb, 2), p: fmt(dil.totals.payload_mb, 2) })}
          </p>)}
      </Section>
      <Section id="ops-closure" title={t('Daily data budget')}
        note={t('Science of {{sci}} MB/day delivered after {{cr}}:1 lossless compression ({{need}}:1 needed for the planned products); CFDP efficiency {{cfdp}}. Required margin {{m}} %.', {
          sci: fmt(data.science.delivered_mb_per_day, 2), cr: fmt(data.science.compression_ratio, 2),
          need: data.science.compression_needed == null ? '–' : fmt(data.science.compression_needed, 2),
          cfdp: fmt(data.science.cfdp_efficiency, 2), m: data.margin_required_percent })}>
        <DataTable dense rows={data.cases} rowKey={r => r.id} columns={caseCols} caption={t('Daily data budget')} />
      </Section>
      <Section id="ops-backlog" title={t('Backlog over 7 days')}
        note={t('What is left on board at the end of each day: the HK store (delayed HK and events) and the payload store.')}>
        {data.backlog.days.length === 0 ? <NoData label={t('no data')} /> : (
          <table className="c2o-table c2o-table--dense" data-testid="backlog">
            <caption className="sr-only">{t('Backlog over 7 days')}</caption>
            <thead><tr><th scope="col">{t('Day')}</th>{data.backlog.days.map(d => <th key={d} scope="col" className="num">{d}</th>)}</tr></thead>
            <tbody>
              <tr><th scope="row">{t('Delayed HK (MB)')}</th>{data.backlog.vc1_mb.map((v, i) => <td key={i} className="mono num">{fmt(v, 2)}</td>)}</tr>
              <tr><th scope="row">{t('Payload (MB)')}</th>{data.backlog.vc2_mb.map((v, i) => <td key={i} className="mono num">{fmt(v, 2)}</td>)}</tr>
            </tbody>
          </table>)}
        {data.backlog.growing && <Note tone="alarm">{t('The payload backlog grows from day to day: the downlink does not keep up.')}</Note>}
      </Section>
    </>
  )
}
