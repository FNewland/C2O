/**
 * FdirPanel — the FDIR tab of the CDR model (ECSS-E-ST-70-11C, ST[12] / ST[19]).
 *
 * Monitors (parameter, check, limits, validity, repetition, severity — promoted from the rule-8
 * FMECA proposals or standard), event-actions (trigger side, TC function, on-clear), the FMECA
 * coverage chain failure mode → monitor → action (detection credit only from accepted monitors),
 * the load-shed table on the named bus-protection levels, the safe mode, FDIR levels and the
 * MCS limits derived from the monitors.
 */
import { Fragment, useState } from 'react'
import { useWhereSection } from '../where/where'
import { useTranslation } from 'react-i18next'
import { DataTable, NoData, StatusBadge, Tabs, Tag, tabPanelProps, type Column } from '../components/ui'
import { pickLang } from '../types/interfaces'
import { hex4, live, type CdrRow, type CdrView } from './cdrApi'
import { CdrFrame, CheckCell, NumCell, OwnerTag, RowState, Section, SelectCell } from './cdrParts'
import { bil, fmt, rowClass, useCdrPanel, type CdrPanelCtx } from './cdrUtil'

type Sub = 'monitors' | 'actions' | 'fmeca' | 'shed' | 'levels'

// English text is the i18n key: which S12 limit arms an event-action (s19_rules.yaml trigger.limit)
const LIMIT_LABEL: Record<string, string> = { high: 'High side', low: 'Low side', any: 'Either side' }

export function FdirPanel() {
  const { t } = useTranslation()
  const ctx = useCdrPanel()
  const [sub, setSub] = useState<Sub>('monitors')
  useWhereSection('fdir', sec => { if (['monitors', 'actions', 'fmeca', 'shed', 'levels'].includes(sec)) setSub(sec as Sub) })
  return (
    <CdrFrame ctx={ctx} group="fdir" testId="fdir-panel" title={t('FDIR design')}
      owners={t('Monitors and limits belong to the seat of their subsystem, event-actions and safe mode to Systems, the load-shed table to Power.')}>
      {view => (
        <>
          <Tabs<Sub> label={t('FDIR sections')} idBase="fdir" variant="segmented" value={sub} onChange={setSub}
            items={[
              { id: 'monitors', label: t('Monitors'), meta: String(live(view.rows.monitors).length) },
              { id: 'actions', label: t('Event-actions'), meta: String(live(view.rows.event_actions).length) },
              { id: 'fmeca', label: t('FMECA coverage'), meta: `${view.fmeca.summary.critical_recovered}/${view.fmeca.summary.critical}` },
              { id: 'shed', label: t('Load shed and safe mode') },
              { id: 'levels', label: t('Levels and limits'), meta: String(live(view.rows.limits).length) },
            ]} />
          <div {...tabPanelProps('fdir', sub)} className="pt-2">
            {sub === 'monitors' && <Monitors ctx={ctx} view={view} />}
            {sub === 'actions' && <Actions ctx={ctx} view={view} />}
            {sub === 'fmeca' && <Fmeca view={view} />}
            {sub === 'shed' && <ShedSafe ctx={ctx} view={view} />}
            {sub === 'levels' && <Levels ctx={ctx} view={view} />}
          </div>
        </>
      )}
    </CdrFrame>
  )
}

function Monitors({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t } = useTranslation()
  const sev = view.vocabulary.monitor_severities.map(s => ({ value: s, label: s }))
  const checks = view.vocabulary.check_types.map(s => ({ value: s, label: s }))
  const cols: Column<CdrRow>[] = [
    { key: 'id', header: t('Monitor'), sort: r => r.data.pmon_id, render: r => (
      <span className="stack gap-0"><span className="mono w-500">{r.data.pmon_id}</span>
        <span className="t-12 c-3">{r.data.name}</span></span>) },
    { key: 'p', header: t('Parameter'), sort: r => r.data.parameter, render: r => <span className="mono">{r.data.parameter} <span className="c-3">{hex4(r.data.param_id)}</span></span> },
    { key: 'chk', header: t('Check'), render: r => <SelectCell ctx={ctx} kind="monitors" row={r} field="check" label={t('Check of {{id}}', { id: r.data.pmon_id })} options={checks} /> },
    { key: 'lo', header: t('Low'), num: true, render: r => <NumCell ctx={ctx} kind="monitors" row={r} field="low" label={t('Low limit of {{id}}', { id: r.data.pmon_id })} /> },
    { key: 'hi', header: t('High'), num: true, render: r => <NumCell ctx={ctx} kind="monitors" row={r} field="high" label={t('High limit of {{id}}', { id: r.data.pmon_id })} /> },
    { key: 'rep', header: t('Repetition'), num: true, render: r => <NumCell ctx={ctx} kind="monitors" row={r} field="repetition" label={t('Repetition of {{id}}', { id: r.data.pmon_id })} digits={0} width={56} /> },
    { key: 'val', header: t('Valid when'), render: r => (r.data.validity
      ? <span className="mono t-12" title={t('Checked only while (value & mask) == expected')}>{r.data.validity.parameter ?? hex4(r.data.validity.param_id)} = {r.data.validity.value}</span>
      : <span className="c-3 t-12">{t('always')}</span>) },
    { key: 'sev', header: t('Severity'), render: r => <SelectCell ctx={ctx} kind="monitors" row={r} field="severity" label={t('Severity of {{id}}', { id: r.data.pmon_id })} options={sev} /> },
    { key: 'own', header: t('Owner'), render: r => <OwnerTag seat={r.owner_seat} /> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="monitors" row={r} label={r.data.pmon_id} /> },
  ]
  return (
    <Section id="fdir-mon" title={t('On-board monitors (ST[12])')}
      note={t('Promoted from the FMECA monitor proposals (rule 8) onto TM parameters, plus the standard power and computer monitors. A monitor on a switched unit is checked only while its line is on. Only an accepted monitor earns FMECA detection credit.')}>
      <DataTable dense rows={view.rows.monitors} rowKey={r => r.id} columns={cols} caption={t('On-board monitors')} rowClassName={rowClass}
        empty={t('No monitor yet: run the design rules (Modes tab) and propose the database.')} />
    </Section>
  )
}

function Actions({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t } = useTranslation()
  const lims = view.vocabulary.limits.map(l => ({ value: l, label: t(LIMIT_LABEL[l] ?? l) }))
  const evName = new Map<number, string>(view.rows.events.map(e => [e.data.event_id, e.data.name]))
  const trig = (r: CdrRow) => {
    const tr = r.data.trigger ?? {}
    const eid = tr.event_id ?? tr.id
    if (tr.kind === 'event') return <span className="mono">{t('event')} {tr.event ?? evName.get(eid) ?? hex4(eid)}{!tr.event && evName.get(eid) ? <span className="c-3"> {hex4(eid)}</span> : null}</span>
    if (tr.kind === 'threshold') return <span className="mono">{tr.parameter} {tr.condition ?? ''} {tr.threshold ?? ''}{tr.persist_s ? ` · ${tr.persist_s} s` : ''}</span>
    return <span className="mono">{tr.monitor ?? tr.parameter ?? hex4(tr.param_id ?? tr.id)}</span>
  }
  const cols: Column<CdrRow>[] = [
    { key: 'ea', header: t('Rule'), sort: r => r.data.ea_id ?? 9999, render: r => (
      <span className="stack gap-0"><span className="mono w-500">{r.data.ea_id ?? '–'}</span><span className="t-12 c-3">{r.data.name}</span></span>) },
    { key: 'trig', header: t('Trigger'), render: trig },
    { key: 'side', header: t('Armed on'), render: r => (r.data.trigger?.kind === 'param'
      ? (r.origin.startsWith('import:') ? t(LIMIT_LABEL[r.data.trigger.limit] ?? r.data.trigger.limit)
        : <SelectCellNested ctx={ctx} row={r} options={lims} label={t('Trigger side of {{name}}', { name: r.data.name })} />)
      : <span className="c-3">–</span>) },
    { key: 'act', header: t('Action'), render: r => (
      <span className="mono">{r.data.action ?? r.data.engine_action ?? hex4(r.data.action_func_id)}{(r.data.action_data ?? []).length ? `(${r.data.action_data.join(', ')})` : ''}</span>) },
    { key: 'clr', header: t('On clear'), render: r => r.data.on_clear ? <span className="mono">{r.data.on_clear}</span> : <span className="c-3">–</span> },
    { key: 'lvl', header: t('Level'), num: true, render: r => r.data.level ?? '–' },
    { key: 'en', header: t('Enabled'), center: true, render: r => <CheckCell ctx={ctx} kind="event_actions" row={r} field="enabled" label={t('{{name}} enabled', { name: r.data.name })} /> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="event_actions" row={r} label={r.data.name} /> },
  ]
  return (
    <Section id="fdir-ea" title={t('Event-actions (ST[19]) and the rule table')}
      note={t('Each action must be a function of the TC catalogue and may not switch off the OBC, EPS, battery or receiver line. An over-temperature rule acts on the high side only; the cold side is the heater’s job.')}>
      <DataTable dense rows={view.rows.event_actions} rowKey={r => r.id} columns={cols} caption={t('Event-actions')} rowClassName={rowClass}
        empty={t('No event-action yet.')} />
    </Section>
  )
}

/** Trigger side lives inside data.trigger: patch the whole trigger. */
function SelectCellNested({ ctx, row, options, label }: { ctx: CdrPanelCtx; row: CdrRow; options: { value: string; label: string }[]; label: string }) {
  const v = String(row.data.trigger?.limit ?? 'any')
  return (
    <select className="c2o-select c2o-select--sm" aria-label={label} value={v}
      onChange={e => ctx.patchData('event_actions', row.id, { trigger: { ...row.data.trigger, limit: e.target.value } })}>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  )
}

function Fmeca({ view }: { view: CdrView }) {
  const { t, i18n } = useTranslation()
  const rows = [...view.fmeca.rows].sort((a, b) => b.severity - a.severity)
  type R = CdrView['fmeca']['rows'][number]
  const cols: Column<R>[] = [
    { key: 'c', header: t('Unit'), sort: r => r.component, render: r => r.component },
    { key: 'm', header: t('Failure mode'), render: r => (typeof r.mode === 'string' ? r.mode : pickLang(r.mode, i18n.language)) },
    { key: 's', header: t('S'), num: true, sort: r => r.severity, render: r => <span className={r.critical ? 'w-600' : ''}>{r.severity}</span> },
    { key: 'chain', header: t('Detection → recovery'), render: r => (
      <span className="c2o-cdr__chain">
        {r.monitors.length ? r.monitors.map(m => <Tag key={m} mono title={r.monitors_counted.includes(m) ? t('accepted: counts') : t('proposed: does not count yet')}>
          {m}{r.monitors_counted.includes(m) ? '' : ' ?'}</Tag>) : <span className="c-3">{t('no monitor')}</span>}
        <span className="arrow" aria-hidden="true">→</span>
        {r.actions.length ? r.actions.map(a => <Tag key={a} mono>{a}</Tag>) : <span className="c-3">{t('no action')}</span>}
      </span>) },
    { key: 'v', header: t('Verdict'), render: r => (!r.critical ? <span className="c-3 t-12">{t('not critical')}</span>
      : r.detected && r.recovered ? <StatusBadge status="ok">{t('detected and recovered')}</StatusBadge>
        : r.detected ? <StatusBadge status="caution">{t('detected only')}</StatusBadge>
          : <StatusBadge status="alarm">{t('not detected')}</StatusBadge>) },
  ]
  const s = view.fmeca.summary
  return (
    <Section id="fdir-fmeca" title={t('FMECA coverage')}
      note={t('Failure modes of severity {{s}} or more need an accepted monitor and an event-action. {{det}}/{{n}} detected, {{rec}}/{{n}} detected and recovered.',
        { s: view.fmeca.severity_needing_recovery, det: s.critical_detected, rec: s.critical_recovered, n: s.critical })}>
      <DataTable dense rows={rows} rowKey={r => r.fmeca_row_id} columns={cols} caption={t('FMECA coverage')}
        rowClassName={r => (r.critical && !r.detected ? 'is-alarm' : undefined)}
        empty={view.dataset === 'reference' ? t('The reference database has no FMECA of its own.') : t('No FMECA row yet: select equipment first.')} />
    </Section>
  )
}

function ShedSafe({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const shed = live(view.rows.load_shed)[0]
  const safe = live(view.rows.safe_mode)[0]
  const levels = Object.entries((shed?.data.bus_protection ?? {}) as Record<string, { value: number | null; label: { en: string; fr: string } }>)
  return (
    <>
      <Section id="fdir-shed" title={t('Load-shed table and bus-protection levels')}
        note={t('The named levels are fractions of the battery bus range (linear open-circuit approximation); monitors, events and the load shed refer to them by name.')}>
        {shed ? (
          <>
            <dl className="c2o-cdr__kv">
              {levels.map(([k, v]) => <Fragment key={k}><dt><span className="mono">{k}</span> · {bil(v.label, i18n.language)}</dt>
                <dd className="mono">{v.value == null ? <NoData label={t('n/a')} /> : `${fmt(v.value, 2)} V`}</dd></Fragment>)}
              <dt>{t('Battery bus range')}</dt><dd className="mono">{(shed.data.bus_range_v ?? []).every((x: number | null) => x == null) ? '–' : `${fmt(shed.data.bus_range_v[0])} – ${fmt(shed.data.bus_range_v[1])} V`}</dd>
              <dt>{t('Restore hysteresis')}</dt><dd className="mono">{fmt(shed.data.restore_hysteresis_v)} V{shed.data.auto_restore ? ` · ${t('automatic restore')}` : ''}</dd>
              <dt>{t('Owner')}</dt><dd><OwnerTag seat={shed.owner_seat} /> <RowState ctx={ctx} kind="load_shed" row={shed} label={t('Load-shed table')} /></dd>
            </dl>
            <table className="c2o-cdr__matrix" aria-label={t('Load-shed stages')}>
              <thead><tr><th>{t('Stage')}</th><th>{t('Lines shed')}</th><th>{t('Trigger')}</th></tr></thead>
              <tbody>
                {(shed.data.stages ?? []).map((s: { stage: number; lines: string[]; soc_pct: number | null; bus_level: string | null }) => (
                  <tr key={s.stage}><th scope="row">{s.stage}</th><td><span className="c2o-cdr__chips">{s.lines.map(l => <Tag key={l}>{l}</Tag>)}</span></td>
                    <td className="mono">{[s.bus_level, s.soc_pct != null ? t('SoC < {{p}} %', { p: s.soc_pct }) : null].filter(Boolean).join(' · ')}</td></tr>))}
              </tbody>
            </table>
          </>
        ) : <NoData label={t('No load-shed table yet (no power line in the electrical model).')} />}
      </Section>
      <Section id="fdir-safe" title={t('Safe mode')}>
        {safe ? (
          <dl className="c2o-cdr__kv">
            <dt>{t('Entered on')}</dt><dd><span className="c2o-cdr__chips">{(safe.data.entry ?? []).map((e: { kind: string; ref: string }) => <Tag key={`${e.kind}${e.ref}`} mono>{e.kind}: {e.ref}</Tag>)}</span></dd>
            <dt>{t('AOCS mode')}</dt><dd className="mono">{safe.data.aocs_mode ?? '–'}</dd>
            <dt>{t('TM rate tier')}</dt><dd className="mono">{safe.data.rate_tier ?? '–'}</dd>
            <dt>{t('Lines switched off')}</dt><dd>{(safe.data.lines_off ?? []).length ? <span className="c2o-cdr__chips">{safe.data.lines_off.map((l: string) => <Tag key={l}>{l}</Tag>)}</span> : <span className="c-3">{t('none')}</span>}</dd>
            <dt>{t('Heaters')}</dt><dd>{safe.data.heaters}</dd>
            {(safe.data.steps ?? []).length > 0 && <><dt>{t('Steps')}</dt><dd className="mono t-12">{safe.data.steps.map((s: { name: string; function?: string; func_id?: number }) => `${s.name} (${s.function ?? s.func_id})`).join(' → ')}</dd></>}
            <dt>{t('Left by')}</dt><dd><span className="mono">{safe.data.exit?.function ?? '–'}</span> · {bil(safe.data.exit?.condition, i18n.language)}</dd>
            <dt>{t('Owner')}</dt><dd><OwnerTag seat={safe.owner_seat} /> <RowState ctx={ctx} kind="safe_mode" row={safe} label={t('Safe mode')} /></dd>
          </dl>
        ) : <NoData label={t('No safe-mode definition yet.')} />}
      </Section>
    </>
  )
}

function Levels({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const lvCols: Column<CdrRow>[] = [
    { key: 'l', header: t('Level'), num: true, sort: r => r.data.level, render: r => <span className="mono w-500">{r.data.level}</span> },
    { key: 'n', header: t('Name'), render: r => bil(r.data.name, i18n.language) },
    { key: 's', header: t('Scope'), render: r => <span className="t-12">{bil(r.data.scope, i18n.language)}</span> },
    { key: 'p', header: t('Persistence (samples)'), num: true, render: r => <NumCell ctx={ctx} kind="fdir_levels" row={r} field="persistence_samples" label={t('Persistence of level {{n}}', { n: r.data.level })} digits={0} width={56} /> },
    { key: 'a', header: t('Attempts'), num: true, render: r => <NumCell ctx={ctx} kind="fdir_levels" row={r} field="max_attempts" label={t('Attempts at level {{n}}', { n: r.data.level })} digits={0} width={56} /> },
    { key: 'e', header: t('Escalates to'), num: true, render: r => r.data.escalate_to ?? '–' },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="fdir_levels" row={r} label={t('Level {{n}}', { n: r.data.level })} /> },
  ]
  const limCols: Column<CdrRow>[] = [
    { key: 'p', header: t('Parameter'), sort: r => r.data.parameter, render: r => <span className="mono">{r.data.parameter} <span className="c-3">{hex4(r.data.param_id)}</span></span> },
    { key: 'r', header: t('Red low / high'), num: true, render: r => <span className="mono">{fmt(r.data.red_low)} / {fmt(r.data.red_high)}</span> },
    { key: 'y', header: t('Yellow low / high'), num: true, render: r => <span className="mono">{fmt(r.data.yellow_low)} / {fmt(r.data.yellow_high)}</span> },
    { key: 'i', header: t('Check (s)'), num: true, render: r => <span className="mono">{fmt(r.data.check_interval_s)}</span> },
    { key: 'v', header: t('Valid when'), render: r => (r.data.valid_when ? <span className="mono t-12">{r.data.valid_when.parameter ?? hex4(r.data.valid_when.param_id)} = {r.data.valid_when.value}</span> : <span className="c-3 t-12">{t('always')}</span>) },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="limits" row={r} label={r.data.parameter} /> },
  ]
  return (
    <>
      <Section id="fdir-levels" title={t('FDIR levels and persistence')}>
        <DataTable dense rows={view.rows.fdir_levels} rowKey={r => r.id} columns={lvCols} caption={t('FDIR levels')} rowClassName={rowClass}
          defaultSort={{ key: 'l', dir: 'asc' }} empty={t('No FDIR level yet.')} />
      </Section>
      <Section id="fdir-limits" title={t('Ground limits (MCS)')} note={t('Yellow from the warning monitor, red from the alarm monitor: the ground twin of ST[12].')}>
        <DataTable dense rows={view.rows.limits} rowKey={r => r.id} columns={limCols} caption={t('Ground limits')} rowClassName={rowClass}
          empty={t('No ground limit yet.')} />
      </Section>
    </>
  )
}
