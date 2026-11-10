/**
 * DataBudget — the daily data budget of the study, read from the one data-budget service
 * (GET /api/studies/{id}/data-budget, services/data_budget.py, W3.04).
 *
 * Generation (science after compression, stored housekeeping), the downlink capacity from the
 * union of the station passes after framing, acquisition and availability, real-time HK in
 * contact, the daily closure and its cases. Housekeeping is designed in TM/TC → Housekeeping
 * (SIDs per mode) and the per-pass choices in Operations → Pass plan: this page has no local HK
 * input any more, so it quotes the same numbers as the Modes data chain and the review packs.
 */
import { useTranslation } from 'react-i18next'
import { useDataBudget } from '../cdr/cdrApi'
import { fmt } from '../cdr/cdrUtil'
import { useUIStore } from '../stores/uiStore'
import { pickLang } from '../types/interfaces'
import { DataTable, MarginBar, NoData, Note, Panel, StatusBadge } from './ui'

export function DataBudget() {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const { data, error, isLoading } = useDataBudget(studyId)
  if (!studyId) return null
  if (isLoading) return <div className="card t-13 c-3">{t('Loading…')}</div>
  if (error || !data) return <div className="card"><Note tone="alarm">{t('The data budget could not be loaded: {{message}}', { message: String((error as Error)?.message ?? '') })}</Note></div>
  const c = data.closure
  const sci = data.science
  return (
    <Panel title={t('Data budget')} meta={c.margin_pct == null ? '' : t('{{m}} % margin ({{case}})', { m: fmt(c.margin_pct, 1), case: c.id })}>
      <p className="t-12 c-2 m-0 pb-2">
        {t('Housekeeping comes from the TM/TC SIDs (TM/TC → Housekeeping) and the per-pass choices from Operations → Pass plan. MB = 10⁶ bytes.')}
      </p>
      {data.status !== 'designed' && <Note tone="caution">{t('Housekeeping is not designed per mode yet: the budget uses one period per SID (or the 2 kbit/s default when there is no SID).')}</Note>}
      {data.warnings.map((w, i) => <Note key={i} tone="caution">{w}</Note>)}
      <div className="row ai-s wrap gap-5" data-testid="data-budget-flow">
        <Figure label={t('Science delivered')} value={fmt(sci.delivered_mb_per_day, 2)} unit={t('MB/day')}
          sub={t('after {{cr}}:1 lossless compression; {{ch}} MB/day on the channel', { cr: fmt(sci.compression_ratio, 2), ch: fmt(sci.on_channel_mb_per_day, 2) })} />
        <Figure label={t('Stored HK')} value={fmt(data.stored.mb_per_day, 2)} unit={t('MB/day')}
          sub={t('{{bps}} bit/s over the operational mix, events included', { bps: fmt(data.stored.mix_bps, 1) })} />
        <Figure label={t('Real-time HK in contact')} value={fmt(data.realtime.full_designed_bps, 0)} unit="bit/s"
          sub={data.realtime.full_allocation_bps != null ? t('{{a}} bit/s allocated; LEAN {{l}} bit/s', { a: fmt(data.realtime.full_allocation_bps, 0), l: fmt(data.realtime.lean_bps, 0) }) : t('LEAN {{l}} bit/s', { l: fmt(data.realtime.lean_bps, 0) })} />
        <Figure label={t('Downlink capacity')} value={fmt(data.capacity.capacity_mb_per_day, 2)} unit={t('MB/day')}
          sub={t('{{u}} min/day union of the passes ({{us}} usable) at {{r}} kbit/s × {{e}}', { u: fmt(data.capacity.union_min_per_day, 1),
            us: fmt(data.capacity.usable_min_per_day, 1), r: fmt(data.framing.raw_rate_bps / 1000, 1), e: fmt(data.framing.frame_efficiency, 3) })} />
      </div>
      <MarginBar lead label={t('Daily demand against capacity ({{case}})', { case: c.id })} unit={t('MB/day')}
        nominal={c.demand_mb} allocation={c.capacity_mb} digits={2} cautionBelowPct={data.margin_required_percent} />
      {sci.compression_needed != null && (
        <p className="t-12 c-2 m-0 pb-2">
          <StatusBadge status={sci.compression_ok ? 'ok' : 'alarm'}>{t('Compression {{cr}}:1 against {{need}}:1 needed', { cr: fmt(sci.compression_ratio, 2), need: fmt(sci.compression_needed, 2) })}</StatusBadge>
          {' '}{t('Planned products: {{raw}} MB/day before compression.', { raw: fmt(sci.raw_mb_per_day, 2) })}
        </p>)}
      <DataTable dense caption={t('Daily data budget')} rows={data.cases} rowKey={r => r.id}
        empty={<NoData label={t('no data')} />} columns={[
          { key: 'id', header: t('Case'), render: r => <span className="mono">{r.id}</span> },
          { key: 'l', header: t('Description'), render: r => pickLang(r.label, i18n.language) },
          { key: 'cap', header: t('Capacity'), num: true, render: r => fmt(r.capacity_mb, 2) },
          { key: 'd', header: t('Demand'), num: true, render: r => fmt(r.demand_mb, 2) },
          { key: 'm', header: t('Margin'), num: true, render: r => (
            <StatusBadge status={r.status === 'pass' ? 'ok' : r.status === 'warn' ? 'caution' : r.status === 'fail' ? 'alarm' : 'nodata'}>
              {r.margin_pct == null ? '–' : `${fmt(r.margin_pct, 1)} %`}</StatusBadge>) },
        ]} />
    </Panel>
  )
}

function Figure({ label, value, unit, sub }: { label: string; value: string; unit: string; sub: string }) {
  return (
    <div className="stack gap-0" style={{ minWidth: 160 }}>
      <span className="t-12 c-3">{label}</span>
      <span><span className="mono t-20 c-v">{value}</span> <span className="t-12 c-3">{unit}</span></span>
      <span className="t-12 c-3">{sub}</span>
    </div>
  )
}
