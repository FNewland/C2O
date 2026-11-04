/**
 * AocsModesPanel — the AOCS modes tab of the CDR model (ECSS-E-ST-60-30C): the AOCS mode
 * table (codes, sensors and actuators per mode, PD gains ωn / ζ, deadband, minimum dwell),
 * the transitions with their triggers and guards, the control-law parameters (B-dot gain,
 * desaturation law, wheel bias) and the power-line states per spacecraft mode (the electrical
 * switch matrix, Power seat).
 */
import { useTranslation } from 'react-i18next'
import { DataTable, NoData, Tag, type Column } from '../components/ui'
import { live, type CdrRow, type CdrView } from './cdrApi'
import { CdrFrame, NumCell, OwnerTag, RowState, Section } from './cdrParts'
import { bil, fmt, rowClass, useCdrPanel, type CdrPanelCtx } from './cdrUtil'

// English text is the i18n key: unit classes (configs/mode_rules.yaml states.classes)
const CLASS_LABEL: Record<string, string> = {
  wheel: 'Reaction wheels', magnetorquer: 'Magnetorquers', star_tracker: 'Star tracker', adcs_sensor: 'Sun sensors / magnetometer',
  gnss: 'GNSS', gyro: 'Gyro',
}
// English text is the i18n key: transition triggers (mode_rules.yaml trigger_kinds)
const TRIGGER_LABEL: Record<string, string> = { ground_tc: 'Ground TC', autonomous: 'Autonomous', timer: 'Timer', event: 'Event' }

export function AocsModesPanel() {
  const { t } = useTranslation()
  const ctx = useCdrPanel()
  return (
    <CdrFrame ctx={ctx} group="aocs" testId="aocs-panel" title={t('AOCS modes and line states')}
      owners={t('AOCS modes and control belong to AOCS; the line states per mode to Power.')}>
      {view => (
        <>
          <ModesTable ctx={ctx} view={view} />
          <Transitions ctx={ctx} view={view} />
          <Control ctx={ctx} view={view} />
          <LineStates ctx={ctx} view={view} />
        </>
      )}
    </CdrFrame>
  )
}

function ModesTable({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const chips = (xs: string[] | undefined) => (xs ?? []).length
    ? <span className="c2o-cdr__chips">{xs!.map(x => <Tag key={x}>{t(CLASS_LABEL[x] ?? x)}</Tag>)}</span> : <span className="c-3">–</span>
  const gain = (r: CdrRow, k: 'omega_n' | 'zeta') => {
    const g = r.data.gains
    if (r.origin.startsWith('import:') || !g) return g ? <span className="mono">{fmt(g[k])}</span> : <span className="c-3">–</span>
    return <NumCell ctx={{ ...ctx, patchData: (kind, id, d) => ctx.patchData(kind, id, { gains: { ...g, ...d } }) }}
      kind="aocs_modes" row={{ ...r, data: { ...r.data, [k]: g[k] } }} field={k} label={t('{{k}} of {{name}}', { k, name: r.data.name })} width={60} />
  }
  const cols: Column<CdrRow>[] = [
    { key: 'code', header: t('Code'), num: true, sort: r => r.data.code, render: r => <span className="mono">{r.data.code}</span> },
    { key: 'name', header: t('Mode'), render: r => (
      <span className="stack gap-0"><span className="mono w-500">{r.data.name}</span><span className="t-12 c-3">{bil(r.data.description, i18n.language)}</span></span>) },
    { key: 'sen', header: t('Sensors'), render: r => chips(r.data.sensors) },
    { key: 'act', header: t('Actuators'), render: r => chips(r.data.actuators) },
    { key: 'wn', header: t('ωn (rad/s)'), num: true, render: r => gain(r, 'omega_n') },
    { key: 'z', header: t('ζ'), num: true, render: r => gain(r, 'zeta') },
    { key: 'db', header: t('Deadband (°)'), num: true, render: r => (r.data.deadband_deg != null ? <span className="mono">{fmt(r.data.deadband_deg)}</span> : <span className="c-3">–</span>) },
    { key: 'dw', header: t('Min dwell (s)'), num: true, render: r => <NumCell ctx={ctx} kind="aocs_modes" row={r} field="min_dwell_s" label={t('Minimum dwell of {{name}} (s)', { name: r.data.name })} digits={0} width={56} /> },
    { key: 'pw', header: t('Power (W)'), num: true, render: r => <span className="mono">{fmt(r.data.power_w, 1)}</span> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="aocs_modes" row={r} label={r.data.name} /> },
  ]
  return (
    <Section id="aocs-modes" title={t('AOCS mode table')}
      note={t('Modes the selected sensors and actuators can fly; gains follow Kp = 2·I·ωn², Kd = 2·ζ·I·ωn. {{src}}', { src: view.refs.aocs?.standard_ref ?? '' })}>
      <DataTable dense rows={view.rows.aocs_modes} rowKey={r => r.id} columns={cols} caption={t('AOCS mode table')} rowClassName={rowClass}
        defaultSort={{ key: 'code', dir: 'asc' }} empty={t('No AOCS mode yet (no AOCS unit in the design).')} />
    </Section>
  )
}

function Transitions({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const cols: Column<CdrRow>[] = [
    { key: 'f', header: t('From'), sort: r => r.data.from, render: r => <span className="mono">{r.data.from}</span> },
    { key: 'to', header: t('To'), render: r => <span className="mono">{r.data.to}</span> },
    { key: 'tr', header: t('Trigger'), render: r => <Tag>{t(TRIGGER_LABEL[r.data.trigger] ?? r.data.trigger)}</Tag> },
    { key: 'g', header: t('Guard'), render: r => <span>{bil(r.data.guard, i18n.language)}{r.data.param ? <span className="mono c-3"> · {r.data.param}</span> : null}</span> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="aocs_transitions" row={r} label={`${r.data.from} → ${r.data.to}`} /> },
  ]
  return (
    <Section id="aocs-trans" title={t('Transitions')}>
      <DataTable dense rows={view.rows.aocs_transitions} rowKey={r => r.id} columns={cols} caption={t('AOCS transitions')} rowClassName={rowClass}
        empty={view.dataset === 'reference' ? t('The simulator keeps its AOCS transitions in code (aocs_basic.py).') : t('No transition yet.')} />
    </Section>
  )
}

function Control({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t } = useTranslation()
  const c = live(view.rows.aocs_control)[0]
  if (!c) return null
  const d = c.data
  const ds = d.desaturation ?? {}
  return (
    <Section id="aocs-ctl" title={t('Control laws')}>
      <dl className="c2o-cdr__kv">
        <dt>{t('B-dot gain (A·m²/(T/s))')}</dt><dd><NumCell ctx={ctx} kind="aocs_control" row={c} field="bdot_gain_am2_per_tps" label={t('B-dot gain')} digits={0} width={90} />
          {' '}<span className="t-12 c-3">{d.mtq_max_dipole_am2 ? t('{{n}} rods × {{m}} A·m²', { n: d.mtq_count, m: fmt(d.mtq_max_dipole_am2) }) : ''}</span></dd>
        <dt>{t('DETUMBLE exit rate')}</dt><dd className="mono">{fmt(d.detumble_exit_rate_dps)} °/s</dd>
        <dt>{t('Desaturation')}</dt><dd className="mono">{t('k = {{k}} s⁻¹, deadband {{db}} N·m·s, timeout {{to}} s', { k: fmt(ds.gain_per_s, 4), db: fmt(ds.deadband_nms, 5), to: fmt(ds.timeout_s, 0) })}</dd>
        <dt>{t('Wheels')}</dt><dd className="mono">{d.wheel_count ? t('{{n}} × max {{s}} rpm, {{tq}} N·m, bias {{b}} rpm', { n: d.wheel_count, s: fmt(d.wheel_max_speed_rpm, 0), tq: fmt(d.wheel_max_torque_nm, 4), b: fmt(d.wheel_bias_rpm, 0) }) : <NoData label={t('no wheel')} />}</dd>
        <dt>{t('FINE deadband')}</dt><dd className="mono">{fmt(d.attitude_error_deadband_deg, 4)} °</dd>
        {Array.isArray(d.inertia_kgm2) && <><dt>{t('Inertia (kg·m²)')}</dt><dd className="mono t-12">{JSON.stringify(d.inertia_kgm2)}</dd></>}
        <dt>{t('Owner')}</dt><dd><OwnerTag seat={c.owner_seat} /> <RowState ctx={ctx} kind="aocs_control" row={c} label={t('Control laws')} /></dd>
      </dl>
    </Section>
  )
}

function LineStates({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t } = useTranslation()
  const rows = live(view.rows.line_states)
  if (!rows.length) {
    return <Section id="aocs-lines" title={t('Power-line states per mode')}><NoData label={t('No line states yet: define the modes and the power lines first.')} /></Section>
  }
  const lineIds = Array.from(new Set(rows.flatMap(r => Object.keys(r.data.states ?? {}))))
  const names: Record<string, string> = Object.assign({}, ...rows.map(r => r.data.line_names ?? {}))
  const toggle = (r: CdrRow, lid: string) => {
    const cur = r.data.states?.[lid]
    ctx.patchData('line_states', r.id, { states: { ...r.data.states, [lid]: cur === 'on' ? 'off' : 'on' } })
  }
  return (
    <Section id="aocs-lines" title={t('Power-line states per mode')}
      note={t('Proposed from the mode matrix: a line is on when a load on it is on in the mode, or when it is always-on. Click a cell to switch it.')}>
      <div className="c2o-table-wrap">
        <table className="c2o-cdr__matrix" aria-label={t('Power-line states per mode')}>
          <thead><tr><th>{t('Mode')}</th>{lineIds.map(l => <th key={l} scope="col">{names[l] ?? l}</th>)}<th>{t('Status')}</th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id} className={rowClass(r)}>
                <th scope="row">{r.data.mode}</th>
                {lineIds.map(l => {
                  const on = r.data.states?.[l] === 'on'
                  return (
                    <td key={l}>
                      <button type="button" className="c2o-cdr__state" aria-pressed={on} disabled={r.origin.startsWith('import:') || ctx.busy === r.id}
                        aria-label={t('Line {{line}} in mode {{mode}}: {{state}}', { line: names[l] ?? l, mode: r.data.mode, state: on ? t('on') : t('off') })}
                        onClick={() => toggle(r, l)}>{on ? t('on') : t('off')}</button>
                    </td>
                  )
                })}
                <td><RowState ctx={ctx} kind="line_states" row={r} label={r.data.mode} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  )
}
