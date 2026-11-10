/**
 * TmtcPanel — the TM/TC tab: the CDR TM/TC database (ECSS-E-ST-70-41C PUS-C) and the TT&C
 * rate ladder. Owned by Comms & OBDH; every parameter by the seat of its subsystem (ruling 5).
 *
 * Sections: database (spacecraft id, APIDs, PUS services), parameters, housekeeping with the
 * downlink budget per regime and per mode, telecommands (S8 functions), events (S5), rate
 * ladder with beacon and command-loss timer.
 */
import { useMemo, useState } from 'react'
import { useWhereSection } from '../where/where'
import { useTranslation } from 'react-i18next'
import { DataTable, MarginBar, NoData, Note, StatusBadge, Tabs, Tag, tabPanelProps, type Column } from '../components/ui'
import { CommitInput } from '../workbench/electricalParts'
import { useUIStore } from '../stores/uiStore'
import { hex4, live, tmtcExportUrl, useDataBudget, type CdrRow, type CdrView, type DataBudgetView, type DbSid } from './cdrApi'
import { CdrFrame, CheckCell, Filter, NumCell, OwnerTag, RowState, Section, SelectCell } from './cdrParts'
import { bil, fmt, num, rowClass, useCdrPanel, type CdrPanelCtx } from './cdrUtil'

type Sub = 'db' | 'params' | 'hk' | 'tc' | 'events' | 'ladder'

// English text is the i18n key: HK budget regimes (services/cdr_checks.hk_budget)
const REGIME_LABEL: Record<string, string> = {
  bootloader: 'Bootloader (beacon)', safe: 'Safe', nominal: 'Nominal', downlink: 'Downlink pass',
}
// English text is the i18n key: telecommand criticality
const CRIT_LABEL: Record<string, string> = { normal: 'Normal command', caution: 'Caution command', critical: 'Critical command' }

export function TmtcPanel() {
  const { t } = useTranslation()
  const ctx = useCdrPanel()
  const [sub, setSub] = useState<Sub>('params')
  useWhereSection('tmtc', sec => { if (['db', 'params', 'hk', 'tc', 'events', 'ladder'].includes(sec)) setSub(sec as Sub) })
  return (
    <CdrFrame ctx={ctx} group="tmtc" testId="tmtc-panel" title={t('TM/TC database')}
      owners={t('Owned by Comms & OBDH; each parameter by the seat of its subsystem.')}>
      {view => (
        <>
          <Tabs<Sub> label={t('TM/TC database sections')} idBase="tmtc" variant="segmented" value={sub} onChange={setSub}
            items={[
              { id: 'db', label: t('Database'), meta: String(live(view.rows.apids).length) },
              { id: 'params', label: t('Parameters'), meta: String(live(view.rows.parameters).length) },
              { id: 'hk', label: t('Housekeeping'), meta: String(live(view.rows.hk).length) },
              { id: 'tc', label: t('Telecommands'), meta: String(live(view.rows.commands).length) },
              { id: 'events', label: t('Events'), meta: String(live(view.rows.events).length) },
              { id: 'ladder', label: t('Rate ladder'), meta: String(live(view.rows.rate_tiers).length) },
            ]} />
          <div {...tabPanelProps('tmtc', sub)} className="pt-2">
            {sub === 'db' && <DbSection ctx={ctx} view={view} />}
            {sub === 'params' && <ParamsSection ctx={ctx} view={view} />}
            {sub === 'hk' && <HkSection ctx={ctx} view={view} />}
            {sub === 'tc' && <TcSection ctx={ctx} view={view} />}
            {sub === 'events' && <EventsSection ctx={ctx} view={view} />}
            {sub === 'ladder' && <LadderSection ctx={ctx} view={view} />}
          </div>
        </>
      )}
    </CdrFrame>
  )
}

function DbSection({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const settings = live(view.rows.settings)[0]
  const apidCols: Column<CdrRow>[] = [
    { key: 'apid', header: t('APID'), num: true, sort: r => r.data.apid, render: r => <span className="mono">{r.data.apid} <span className="c-3">({hex4(r.data.apid)})</span></span> },
    { key: 'name', header: t('Application process'), render: r => r.data.name },
    { key: 'role', header: t('Role'), render: r => <Tag>{r.data.role}</Tag> },
    { key: 'sub', header: t('Subsystem'), render: r => r.data.subsystem },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="apids" row={r} label={`APID ${r.data.apid}`} /> },
  ]
  const svcCols: Column<CdrRow>[] = [
    { key: 's', header: t('Service'), num: true, sort: r => r.data.service, render: r => <span className="mono">ST[{String(r.data.service).padStart(2, '0')}]</span> },
    { key: 'n', header: t('Name'), render: r => bil(r.data.name, i18n.language) },
    { key: 'u', header: t('Used'), center: true, render: r => <CheckCell ctx={ctx} kind="services" row={r} field="used" label={t('Service {{n}} used', { n: r.data.service })} /> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="services" row={r} label={`ST[${r.data.service}]`} /> },
  ]
  return (
    <>
      <Section id="tmtc-db" title={t('Spacecraft and packet identifiers')}>
        {settings ? (
          <dl className="c2o-cdr__kv">
            <dt>{t('Spacecraft id (SCID)')}</dt><dd className="mono">{settings.data.spacecraft_id}</dd>
            <dt>{t('PUS version')}</dt><dd className="mono">{settings.data.pus_version}</dd>
            <dt>{t('Time code')}</dt><dd>{settings.data.time_code}</dd>
            <dt>{t('Application / bootloader APID')}</dt><dd className="mono">{settings.data.application_apid} / {settings.data.bootloader_apid}</dd>
            <dt>{t('Owner')}</dt><dd><OwnerTag seat={settings.owner_seat} /> <RowState ctx={ctx} kind="settings" row={settings} label={t('Database settings')} /></dd>
          </dl>
        ) : <NoData label={t('No database settings yet')} />}
        <DataTable dense rows={view.rows.apids} rowKey={r => r.id} columns={apidCols} caption={t('APIDs')} rowClassName={rowClass} empty={t('No APID yet.')} />
      </Section>
      <Section id="tmtc-pus" title={t('PUS services (ECSS-E-ST-70-41C)')}>
        <DataTable dense rows={view.rows.services} rowKey={r => r.id} columns={svcCols} caption={t('PUS services')} rowClassName={rowClass}
          defaultSort={{ key: 's', dir: 'asc' }} empty={t('No PUS service yet.')} />
      </Section>
    </>
  )
}

function ParamsSection({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const [q, setQ] = useState('')
  const inHk = useMemo(() => {
    const m = new Map<number, number[]>()
    for (const h of live(view.rows.hk)) for (const id of (h.data.parameter_ids as number[]) ?? []) m.set(id, [...(m.get(id) ?? []), h.data.sid])
    return m
  }, [view])
  const rows = view.rows.parameters.filter(r => !q || `${r.data.name} ${hex4(r.data.param_id)} ${r.data.subsystem}`.toLowerCase().includes(q.toLowerCase()))
  const types = view.vocabulary.types.map(x => ({ value: x, label: x }))
  const cols: Column<CdrRow>[] = [
    { key: 'id', header: t('Id'), num: true, sort: r => r.data.param_id, render: r => <span className="mono">{hex4(r.data.param_id)}</span> },
    { key: 'name', header: t('Name'), sort: r => r.data.name, render: r => (
      <span className="stack gap-0"><span className="mono w-500">{r.data.name}</span>
        <span className="t-12 c-3">{bil(r.data.description, i18n.language)}</span></span>) },
    { key: 'sub', header: t('Subsystem'), sort: r => r.data.subsystem, render: r => r.data.subsystem },
    { key: 'type', header: t('Type'), render: r => <SelectCell ctx={ctx} kind="parameters" row={r} field="type" label={t('Type of {{name}}', { name: r.data.name })} options={types} /> },
    { key: 'unit', header: t('Unit'), render: r => r.data.unit || <span className="c-3">–</span> },
    { key: 'cal', header: t('Calibration'), render: r => {
      const c = r.data.calibration ?? {}
      return c.type === 'linear' ? <span className="mono">÷ {fmt(c.scale)}</span> : c.type === 'enum' ? <Tag title={(c.values ?? []).join(', ')}>{t('enum')}</Tag> : <span className="c-3">{t('raw')}</span>
    } },
    { key: 'range', header: t('Range'), num: true, render: r => (Array.isArray(r.data.range) ? <span className="mono">{fmt(r.data.range[0])} … {fmt(r.data.range[1])}</span> : <span className="c-3">–</span>) },
    { key: 'hk', header: t('HK / sampling'), render: r => {
      const sids = inHk.get(r.data.param_id) ?? []
      return sids.length ? <span className="mono">SID {sids.join(', ')}{r.data.sampling_s ? ` · ${fmt(r.data.sampling_s)} s` : ''}</span>
        : r.data.on_demand ? <Tag>{t('on demand')}</Tag> : r.data.visibility ? <Tag>{r.data.visibility}</Tag> : <StatusBadge status="caution">{t('in no packet')}</StatusBadge>
    } },
    { key: 'own', header: t('Owner'), render: r => <OwnerTag seat={r.owner_seat} /> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="parameters" row={r} label={r.data.name} /> },
  ]
  return (
    <Section id="tmtc-params" title={t('TM parameters')}
      note={t('Proposed per subsystem, per unit (incl. the parameter its FDIR monitor watches), per power line, bus and heater; ids in the subsystem block.')}>
      <div className="c2o-cdr__bar"><Filter value={q} onChange={setQ} label={t('Filter by name, id or subsystem')} />
        <span className="t-12 c-3">{t('{{n}} shown', { n: rows.length })}</span></div>
      <DataTable dense rows={rows} rowKey={r => r.id} columns={cols} caption={t('TM parameters')} rowClassName={rowClass}
        defaultSort={{ key: 'id', dir: 'asc' }} empty={t('No parameter yet.')} />
    </Section>
  )
}

function HkSection({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t } = useTranslation()
  const [tab, setTab] = useState<HkTab>('rt')
  const db = useDataBudget(ctx.studyId)
  const b = view.budget
  const bySid = new Map(b.sids.map(s => [s.sid, s]))
  const cols: Column<CdrRow>[] = [
    { key: 'sid', header: t('SID'), num: true, sort: r => r.data.sid, render: r => <span className="mono w-500">{r.data.sid}{r.data.store_sid != null && <span className="c-3"> / {r.data.store_sid}</span>}</span> },
    { key: 'name', header: t('Packet'), render: r => <span>{r.data.name} {r.data.beacon && <Tag accent>{t('beacon')}</Tag>} {r.data.diagnostic && <Tag>{t('diagnostic')}</Tag>}</span> },
    { key: 'apid', header: t('APID'), num: true, render: r => <span className="mono">{r.data.apid}</span> },
    { key: 'n', header: t('Parameters'), num: true, render: r => (r.data.params ?? r.data.parameter_ids ?? []).length },
    { key: 'per', header: t('Period (s)'), num: true, render: r => <NumCell ctx={ctx} kind="hk" row={r} field="period_s" label={t('Period of SID {{n}} (s)', { n: r.data.sid })} width={56} /> },
    { key: 'bytes', header: t('Bytes'), num: true, render: r => <span className="mono">{bySid.get(r.data.sid)?.bytes ?? ''}</span> },
    { key: 'bps', header: t('bit/s'), num: true, sort: r => bySid.get(r.data.sid)?.bps ?? 0, render: r => <span className="mono">{fmt(bySid.get(r.data.sid)?.bps, 1)}</span> },
    { key: 'boot', header: t('On at boot'), center: true, render: r => <CheckCell ctx={ctx} kind="hk" row={r} field="enabled_at_boot" label={t('SID {{n}} enabled at boot', { n: r.data.sid })} /> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="hk" row={r} label={`SID ${r.data.sid}`} /> },
  ]
  return (
    <>
      <HkSummary data={db.data} />
      <Tabs<HkTab> label={t('Housekeeping views')} idBase="tmtc-hk" variant="segmented" value={tab} onChange={setTab}
        items={[
          { id: 'rt', label: t('Real time') }, { id: 'stored', label: t('Stored') },
          { id: 'stores', label: t('Stores'), meta: db.data ? String(db.data.stores.length) : undefined },
          { id: 'profiles', label: t('Profiles') }, { id: 'list', label: t('Structures') },
        ]} />
      <div {...tabPanelProps('tmtc-hk', tab)} className="pt-2">
        {(tab === 'rt' || tab === 'stored') && <SidMatrix ctx={ctx} view={view} data={db.data} copy={tab === 'rt' ? 'rt' : 'stored'} />}
        {tab === 'stores' && <StoresView data={db.data} />}
        {tab === 'profiles' && <ProfilesView data={db.data} view={view} />}
        {tab === 'list' && (
          <Section id="tmtc-hk" title={t('Housekeeping structures (ST[03])')}>
            <DataTable dense rows={view.rows.hk} rowKey={r => r.id} columns={cols} caption={t('Housekeeping structures')} rowClassName={rowClass}
              defaultSort={{ key: 'sid', dir: 'asc' }} empty={t('No housekeeping structure yet.')} />
          </Section>
        )}
      </div>
    </>
  )
}

type HkTab = 'rt' | 'stored' | 'stores' | 'profiles' | 'list'

function HkSummary({ data }: { data: DataBudgetView | undefined }) {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  if (!data) return <p className="t-13 c-3">{t('Loading…')}</p>
  const c = data.closure
  return (
    <Section id="tmtc-hk-sum" title={t('Housekeeping and downlink budget')}
      note={t('Real-time SIDs go down in contact; stored copies fill the HK store and go down as delayed TM. Capacity is the union of the station passes after framing ({{eff}}), {{acq}} s acquisition per pass and {{av}} % availability.',
        { eff: fmt(data.framing.frame_efficiency, 3), acq: data.framing.acquisition_s, av: fmt(data.framing.availability * 100, 0) })}>
      {data.status !== 'designed' && <Note tone="caution">{t('Housekeeping is not designed per mode yet: the budget uses one period per SID (or the 2 kbit/s default when there is no SID).')}</Note>}
      <dl className="c2o-cdr__kv" data-testid="hk-summary">
        <dt>{t('Real time FULL (designed / allocated)')}</dt><dd className="mono">{fmt(data.realtime.full_designed_bps, 0)} / {data.realtime.full_allocation_bps != null ? fmt(data.realtime.full_allocation_bps, 0) : '–'} bit/s</dd>
        <dt>{t('Real time LEAN')}</dt><dd className="mono">{fmt(data.realtime.lean_bps, 0)} bit/s</dd>
        <dt>{t('With diagnostics')}</dt><dd className="mono">{fmt(data.realtime.with_diag_bps, 0)} bit/s</dd>
        <dt>{t('Stored HK')}</dt><dd className="mono">{fmt(data.stored.mix_bps, 1)} bit/s · {fmt(data.stored.mb_per_day, 2)} {t('MB/day')}</dd>
        <dt>{t('Capacity')}</dt><dd className="mono">{fmt(data.capacity.capacity_mb_per_day, 2)} {t('MB/day')} ({fmt(data.capacity.union_min_per_day, 1)} {t('min/day union')})</dd>
        <dt>{t('Daily closure')}</dt><dd><StatusBadge status={c.status === 'pass' ? 'ok' : c.status === 'warn' ? 'caution' : c.status === 'fail' ? 'alarm' : 'nodata'}>
          {bil(c.label, i18n.language)}: {c.margin_pct == null ? '–' : `${fmt(c.margin_pct, 1)} %`}</StatusBadge></dd>
        <dt>{t('Packet overhead')}</dt><dd className="mono">{data.packet.overhead_bytes} B</dd>
      </dl>
      {studyId && <p className="t-12 m-0 pb-2"><a href={tmtcExportUrl(studyId, 'xlsx')} download>{t('Download the TM/TC database (XLSX)')}</a>
        {' · '}<a href={tmtcExportUrl(studyId, 'csv')} download>{t('CSV')}</a></p>}
    </Section>
  )
}

/** SID × mode matrix: interval per mode (s; empty = disabled), bit/s under it, a total row per mode. */
function SidMatrix({ ctx, view, data, copy }: { ctx: CdrPanelCtx; view: CdrView; data: DataBudgetView | undefined; copy: 'rt' | 'stored' }) {
  const { t } = useTranslation()
  if (!data) return <p className="t-13 c-3">{t('Loading…')}</p>
  const rowsById = new Map(view.rows.hk.map(r => [r.id, r]))
  const sids = data.sids.filter(s => copy === 'rt' || s.store_sid != null || s.store_period_by_mode)
  const field = copy === 'rt' ? 'rt_period_by_mode' : 'store_period_by_mode'
  const intervalOf = (s: DbSid, m: string) => (copy === 'rt' ? s.rt_interval_by_mode : s.store_interval_by_mode)[m]
  const bpsOf = (s: DbSid, m: string) => (copy === 'rt' ? s.rt_bps_by_mode : s.store_bps_by_mode)[m] ?? 0
  const enabled = (s: DbSid) => (copy === 'rt' ? s.enabled.realtime : s.enabled.stored)
  const total = (m: string) => sids.filter(s => enabled(s) && !s.diagnostic && !(copy === 'rt' && s.beacon)).reduce((a, s) => a + bpsOf(s, m), 0)
  const edit = (s: DbSid, m: string, v: string) => {
    const row = rowsById.get(s.row_id)
    if (!row) return
    const n = num(v)
    if (n === undefined) return
    const base = (row.data[field] as Record<string, number | null> | null) ?? Object.fromEntries(data.modes.map(x => [x.id, intervalOf(s, x.id) ?? null]))
    ctx.patchData('hk', row.id, { [field]: { ...base, [m]: n && n > 0 ? n : null } })
  }
  const toggle = (s: DbSid, on: boolean) => {
    const row = rowsById.get(s.row_id)
    if (row) ctx.patchData('hk', row.id, { enabled: { ...s.enabled, [copy === 'rt' ? 'realtime' : 'stored']: on } })
  }
  return (
    <Section id={`tmtc-hk-${copy}`} title={copy === 'rt' ? t('Real-time collection interval per mode (s)') : t('Stored-copy collection interval per mode (s)')}
      note={copy === 'rt' ? t('Real-time SIDs are enabled at acquisition of signal and disabled after loss of signal. An empty cell disables the SID in that mode. Diagnostic SIDs are not in the totals.')
        : t('Stored copies are routed to a packet store (ST[15]) and go down as delayed TM. Thermal is sampled once per minute.')}>
      <div className="c2o-cdr__matrix" style={{ overflowX: 'auto' }}>
        <table className="c2o-table c2o-table--dense" data-testid={`sid-matrix-${copy}`}>
          <caption className="sr-only">{t('SID × mode matrix')}</caption>
          <thead><tr>
            <th scope="col">{t('SID')}</th><th scope="col">{t('Packet')}</th><th scope="col">{t('Bytes')}</th><th scope="col">{t('Enabled')}</th>
            {data.modes.map(m => <th key={m.id} scope="col" className="num">{m.name}</th>)}
          </tr></thead>
          <tbody>
            {sids.map(s => {
              const row = rowsById.get(s.row_id)
              const ro = !row || row.origin.startsWith('import:')
              return (
                <tr key={`${s.sid}`} className={s.diagnostic ? 'is-suggested' : undefined}>
                  <th scope="row" className="mono">{copy === 'rt' ? s.sid : (s.store_sid ?? '–')}</th>
                  <td>{s.name} {s.beacon && <Tag accent>{t('beacon')}</Tag>} {s.diagnostic && <Tag>{t('diagnostic')}</Tag>}</td>
                  <td className="mono num">{s.bytes}</td>
                  <td className="center"><input type="checkbox" checked={enabled(s)} disabled={ro}
                    aria-label={t('SID {{n}} enabled', { n: s.sid })} onChange={e => toggle(s, e.target.checked)} /></td>
                  {data.modes.map(m => {
                    const iv = intervalOf(s, m.id)
                    return (
                      <td key={m.id} className="num">
                        {ro ? <span className="mono">{iv ?? '–'}</span>
                          : <CommitInput label={t('Interval of SID {{n}} in {{mode}} (s)', { n: s.sid, mode: m.name })} value={iv == null ? '' : fmt(iv, 2)}
                            width={52} placeholder="–" onCommit={v => edit(s, m.id, v)} />}
                        <div className="t-12 c-3 mono">{iv ? fmt(bpsOf(s, m.id), 1) : ''}</div>
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
          <tfoot><tr>
            <th scope="row" colSpan={4}>{copy === 'rt' ? t('Routine total (bit/s)') : t('Stored total (bit/s)')}</th>
            {data.modes.map(m => <td key={m.id} className="mono num w-600">{fmt(total(m.id), 1)}</td>)}
          </tr></tfoot>
        </table>
      </div>
    </Section>
  )
}

function StoresView({ data }: { data: DataBudgetView | undefined }) {
  const { t } = useTranslation()
  if (!data) return <p className="t-13 c-3">{t('Loading…')}</p>
  return (
    <Section id="tmtc-stores" title={t('Packet stores (ST[15])')}
      note={t('Days each store holds without a dump. The HK store must hold {{d}} days at the worst rate with the storage margin.', { d: data.stores.find(s => s.check)?.check?.min_days ?? 7 })}>
      {data.stores.length === 0 && <NoData label={t('No packet store yet')} />}
      {data.stores.map(s => {
        const days = s.days_held.nominal_mix ?? null
        return (
          <div key={`${s.id}`} className="pb-2">
            <MarginBar label={`${s.name} · ${s.size_mb != null ? fmt(s.size_mb, 0) + ' MB' : '–'}`} unit={t('days')}
              nominal={s.check ? s.check.min_days : null} allocation={days} digits={1}
              title={Object.entries(s.days_held).map(([k, v]) => `${k}: ${v ?? '–'}`).join(' · ')} />
            <p className="t-12 c-3 m-0">
              {Object.entries(s.fill_mb_per_day).map(([k, v]) => t('{{mode}}: {{mb}} MB/day, {{d}} days', { mode: k, mb: fmt(v, 3), d: s.days_held[k] ?? '–' })).join(' · ')}
              {s.orbits_held != null && t('{{mb}} MB per orbit, {{n}} orbits', { mb: fmt(s.fill_mb_per_orbit ?? 0, 3), n: fmt(s.orbits_held, 1) })}
              {s.check?.ok === false && <> <StatusBadge status="alarm">{t('too small')}</StatusBadge></>}
            </p>
          </div>
        )
      })}
    </Section>
  )
}

function ProfilesView({ data, view }: { data: DataBudgetView | undefined; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const b = view.budget
  if (!data) return <p className="t-13 c-3">{t('Loading…')}</p>
  return (
    <>
      <Section id="tmtc-profiles" title={t('Real-time profiles and the rate tiers')}
        note={t('HK may use {{share}} % of the information rate of a tier. The pass plan picks a profile per pass.', { share: b.hk_share_percent })}>
        {data.profiles.map(p => (
          <div key={p.name} className="pb-2">
            <p className="t-13 m-0"><span className="mono w-600">{p.name}</span> · {fmt(p.designed_bps, 0)} bit/s {t('designed')}
              {p.allocation_bps != null && <> · {fmt(p.allocation_bps, 0)} bit/s {t('allocated')}</>} <span className="c-3">{bil(p.description, i18n.language)}</span></p>
            {p.tier_fit.map(f => <MarginBar key={f.tier} label={`${f.tier} (${fmt(f.bps / 1000, 1)} kbit/s)`} unit="bit/s"
              nominal={p.pass_bps} allocation={f.hk_budget_bps} digits={0} />)}
          </div>
        ))}
      </Section>
      <Section id="tmtc-budget" title={t('Housekeeping downlink budget')}
        note={t('HK may use {{share}} % of the TM rate of each regime after {{eff}} frame efficiency; each packet carries {{ovh}} bytes of header, SID and CRC. {{src}}',
          { share: b.hk_share_percent, eff: fmt(b.frame_efficiency, 2), ovh: b.packet_overhead_bytes, src: b.standard_ref })}>
        <div className="c2o-cdr__budget">
          {b.regimes.map(r => (
            <MarginBar key={r.regime} label={`${t(REGIME_LABEL[r.regime] ?? r.regime)} · ${r.tier ?? t('no tier')}`} unit="bit/s"
              nominal={r.hk_bps} withMargin={r.hk_bps} allocation={r.budget_bps} digits={0}
              title={t('SIDs {{sids}}', { sids: r.sids.join(', ') })} />
          ))}
        </div>
        {b.modes.length > 0 && (
          <p className="t-12 c-2 m-0 pb-2">{t('Per mode:')}{' '}
            {b.modes.map(m => <span key={m.mode_id} className="c2o-cdr__chips" style={{ marginRight: 8 }}>
              <StatusBadge status={m.ok === false ? 'alarm' : m.ok ? 'ok' : 'nodata'}>{m.mode}: {fmt(m.hk_bps, 0)} bit/s</StatusBadge></span>)}
          </p>
        )}
      </Section>
    </>
  )
}

function TcSection({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const [q, setQ] = useState('')
  const rows = view.rows.commands.filter(r => !q || `${r.data.name} ${r.data.func_id ?? ''} ${r.data.subsystem ?? ''}`.toLowerCase().includes(q.toLowerCase()))
  const crit = view.vocabulary.criticalities.map(c => ({ value: c, label: t(CRIT_LABEL[c] ?? c) }))
  const args = (r: CdrRow) => ((r.data.args ?? []) as { name: string; type?: string; unit?: string; range?: number[]; enum?: string[]; values?: number[] }[])
    .map(a => `${a.name}${a.range ? ` [${a.range.join('…')}]` : a.values ? ` {${a.values.join(',')}}` : a.enum ? ` {${a.enum.slice(0, 6).join('|')}${a.enum.length > 6 ? '…' : ''}}` : ''}`).join(', ')
  const cols: Column<CdrRow>[] = [
    { key: 'svc', header: t('Service'), render: r => <span className="mono">{r.data.service},{r.data.subtype}</span> },
    { key: 'fid', header: t('Function'), num: true, sort: r => r.data.func_id ?? 999, render: r => <span className="mono">{r.data.func_id ?? ''}</span> },
    { key: 'name', header: t('Telecommand'), sort: r => r.data.name, render: r => (
      <span className="stack gap-0"><span className="mono w-500">{r.data.name}</span><span className="t-12 c-3">{bil(r.data.description, i18n.language)}</span></span>) },
    { key: 'args', header: t('Arguments'), render: r => <span className="mono t-12">{args(r) || '–'}</span> },
    { key: 'pos', header: t('Position'), render: r => r.data.position ? <Tag>{r.data.position}</Tag> : <span className="c-3">–</span> },
    { key: 'crit', header: t('Criticality'), render: r => <SelectCell ctx={ctx} kind="commands" row={r} field="criticality" label={t('Criticality of {{name}}', { name: r.data.name })} options={crit} /> },
    { key: 'arm', header: t('Arm, then execute'), center: true, render: r => <CheckCell ctx={ctx} kind="commands" row={r} field="arm_execute" label={t('{{name}} is arm-then-execute', { name: r.data.name })} /> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="commands" row={r} label={r.data.name} /> },
  ]
  return (
    <Section id="tmtc-tc" title={t('Telecommands')}
      note={t('S8 functions in the subsystem blocks; argument ranges from the design (power lines, wheels, heaters). Critical telecommands are armed, then executed.')}>
      <div className="c2o-cdr__bar"><Filter value={q} onChange={setQ} label={t('Filter by name, function or subsystem')} />
        <span className="t-12 c-3">{t('{{n}} shown', { n: rows.length })}</span></div>
      <DataTable dense rows={rows} rowKey={r => r.id} columns={cols} caption={t('Telecommands')} rowClassName={rowClass}
        defaultSort={{ key: 'fid', dir: 'asc' }} empty={t('No telecommand yet.')} />
    </Section>
  )
}

function EventsSection({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const [q, setQ] = useState('')
  const rows = view.rows.events.filter(r => !q || `${r.data.name} ${hex4(r.data.event_id)} ${r.data.subsystem}`.toLowerCase().includes(q.toLowerCase()))
  const sev = view.vocabulary.event_severities.map(s => ({ value: s, label: s }))
  const cols: Column<CdrRow>[] = [
    { key: 'id', header: t('Id'), num: true, sort: r => r.data.event_id, render: r => <span className="mono">{hex4(r.data.event_id)}</span> },
    { key: 'name', header: t('Event'), sort: r => r.data.name, render: r => (
      <span className="stack gap-0"><span className="mono w-500">{r.data.name}</span><span className="t-12 c-3">{bil(r.data.description, i18n.language)}</span></span>) },
    { key: 'sub', header: t('Subsystem'), render: r => r.data.subsystem },
    { key: 'sev', header: t('Severity'), render: r => <SelectCell ctx={ctx} kind="events" row={r} field="severity" label={t('Severity of {{name}}', { name: r.data.name })} options={sev} /> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="events" row={r} label={r.data.name} /> },
  ]
  return (
    <Section id="tmtc-ev" title={t('Events (ST[05])')}>
      <div className="c2o-cdr__bar"><Filter value={q} onChange={setQ} label={t('Filter by name, id or subsystem')} />
        <span className="t-12 c-3">{t('{{n}} shown', { n: rows.length })}</span></div>
      <DataTable dense rows={rows} rowKey={r => r.id} columns={cols} caption={t('Events')} rowClassName={rowClass}
        defaultSort={{ key: 'id', dir: 'asc' }} empty={t('No event yet.')} />
    </Section>
  )
}

function LadderSection({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t } = useTranslation()
  const ttc = live(view.rows.ttc)[0]
  const mods = view.vocabulary.modulations.map(m => ({ value: m, label: m }))
  const cods = view.vocabulary.codings.map(m => ({ value: m, label: m }))
  const roleOf = (r: CdrRow) => [ttc?.data.default_tier === r.data.name && t('default'), ttc?.data.beacon_tier === r.data.name && t('beacon'),
    ttc?.data.safe_tier === r.data.name && t('safe'), r.data.role === 'downlink' && t('Downlink pass')].filter(Boolean).join(', ')
  const cols: Column<CdrRow>[] = [
    { key: 'name', header: t('Tier'), render: r => <span className="mono w-500">{r.data.name}</span> },
    { key: 'role', header: t('Used for'), render: r => roleOf(r) || <span className="c-3">–</span> },
    { key: 'bps', header: t('bit/s'), num: true, sort: r => r.data.bps, render: r => <NumCell ctx={ctx} kind="rate_tiers" row={r} field="bps" label={t('Bit rate of {{name}}', { name: r.data.name })} digits={0} width={80} /> },
    { key: 'mod', header: t('Modulation'), render: r => <SelectCell ctx={ctx} kind="rate_tiers" row={r} field="modulation" label={t('Modulation of {{name}}', { name: r.data.name })} options={mods} /> },
    { key: 'cod', header: t('Coding'), render: r => <SelectCell ctx={ctx} kind="rate_tiers" row={r} field="coding" label={t('Coding of {{name}}', { name: r.data.name })} options={cods} /> },
    { key: 'cg', header: t('Coding gain (dB)'), num: true, render: r => <NumCell ctx={ctx} kind="rate_tiers" row={r} field="coding_gain_db" label={t('Coding gain of {{name}} (dB)', { name: r.data.name })} digits={1} width={56} /> },
    { key: 'gate', header: t('Gating'), render: r => (
      <span className="c2o-cdr__chips">
        {r.data.bootloader_only && <Tag>{t('bootloader only')}</Tag>}
        {r.data.requires_antenna && <Tag>{t('antenna deployed')}</Tag>}
        {r.data.requires_downlink_mode && <Tag>{t('downlink mode')}</Tag>}
        {r.data.min_elevation_deg != null && <Tag>{t('el ≥ {{d}}°', { d: r.data.min_elevation_deg })}</Tag>}
      </span>) },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="rate_tiers" row={r} label={r.data.name} /> },
  ]
  const b = ttc?.data.beacon ?? {}
  return (
    <>
      <Section id="tmtc-ladder" title={t('TM rate ladder')} note={t('Proposed from the transceiver: the low rate is capped by the part, the high rate is its maximum. {{src}}', { src: view.refs.ttc?.standard_ref ?? '' })}>
        <DataTable dense rows={view.rows.rate_tiers} rowKey={r => r.id} columns={cols} caption={t('TM rate ladder')} rowClassName={rowClass}
          defaultSort={{ key: 'bps', dir: 'asc' }} empty={t('No rate tier yet (no TT&C unit in the design).')} />
      </Section>
      <Section id="tmtc-ttc" title={t('Beacon, uplink and command loss')}>
        {ttc ? (
          <dl className="c2o-cdr__kv">
            <dt>{t('Command-loss timer (s)')}</dt><dd><NumCell ctx={ctx} kind="ttc" row={ttc} field="cmd_loss_switch_timeout_s" label={t('Command-loss timer (s)')} digits={0} width={90} />
              {' '}<span className="t-12 c-3">{t('{{h}} h', { h: fmt(Number(ttc.data.cmd_loss_switch_timeout_s) / 3600, 1) })}</span></dd>
            <dt>{t('Command-loss action')}</dt><dd className="mono">{ttc.data.cmd_loss_action ?? '–'}</dd>
            <dt>{t('RSSI threshold (dBm)')}</dt><dd><NumCell ctx={ctx} kind="ttc" row={ttc} field="cmd_loss_rssi_threshold_dbm" label={t('RSSI threshold (dBm)')} digits={1} /></dd>
            <dt>{t('TC uplink (bit/s)')}</dt><dd><NumCell ctx={ctx} kind="ttc" row={ttc} field="tc_uplink_rate_bps" label={t('TC uplink (bit/s)')} digits={0} /></dd>
            <dt>{t('Beacon')}</dt><dd>{b.enabled ? t('{{bps}} bit/s every {{p}} s, SID {{sid}}, line {{line}}', { bps: b.bps, p: b.period_s ?? '–', sid: b.hk_sid ?? '–', line: b.eps_line ?? '–' }) : t('off')}</dd>
            <dt>{t('Owner')}</dt><dd><OwnerTag seat={ttc.owner_seat} /> <RowState ctx={ctx} kind="ttc" row={ttc} label={t('TT&C settings')} /></dd>
          </dl>
        ) : <NoData label={t('No TT&C settings yet')} />}
      </Section>
    </>
  )
}
