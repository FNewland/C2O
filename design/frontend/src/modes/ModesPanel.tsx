/**
 * ModesPanel — the ConOps mode machine and the budgets per mode (Nov 2026).
 *
 * Six views, picture first:
 *  - Machine: the state diagram, the modes table and the transitions table (both editable);
 *  - Power by mode: the mode × unit matrix (state, W, data rate), proposed by rule MO-01
 *    from the KB per-mode power or the C2O default state table, accepted / edited / rejected
 *    cell by cell; a changed part marks accepted cells "stale, review" (rule 13);
 *  - Energy: per-mode load with maturity and system margins against generation, energy per
 *    orbit, depth of discharge, the operational orbit and the sustainable duty of short modes;
 *  - Data chain: generated → stored → downlinked per day (contact plan, link-budget rate);
 *  - Equipment: every unit's contribution to every budget (mass, power and heat per mode,
 *    data, cost, link) with its maturity category;
 *  - Rules: FDIR monitor / event-action stubs, risk entries, heaters, KB staleness.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { useUIStore } from '../stores/uiStore'
import { useWhereSection } from '../where/where'
import { Button, DataTable, Disclosure, Note, NoData, Panel, Select, StatusBadge, Tabs, Tag, askConfirm, fmtNum, showAlert,
  tabPanelProps, type Column, type Status } from '../components/ui'
import { ModeDiagram } from './ModeDiagram'
import { ConopsPhases } from '../workbench/ConopsPhases'
import { bi, get, modeKeys, send, useInvalidateModes, useModes, type DailyCase, type DataChain, type Energy, type EquipBudgets,
  type Member, type Mode, type ModesOverview, type Proposal, type StaleRow, type SystemMargin, type Transition, type Unit } from './api'
import { KIND_LABELS, PHASE_LABELS, POINTING_LABELS, PROPOSAL_KIND_LABELS, STATE_LABELS, STATUS_LABELS, TRIGGER_LABELS } from './labels'
import './modes.css'

type View = 'machine' | 'matrix' | 'energy' | 'data' | 'equipment' | 'rules'

// English text is the i18n key
const VIEW_LABELS: Record<View, string> = {
  machine: 'Mode machine', matrix: 'Power by mode', energy: 'Energy per orbit', data: 'Data chain',
  equipment: 'Equipment → budgets', rules: 'Rules & proposals',
}
const VIEWS = Object.keys(VIEW_LABELS) as View[]

function statusOf(s: string): Status {
  return s === 'pass' ? 'ok' : s === 'fail' ? 'alarm' : s === 'warn' ? 'caution' : 'nodata'
}

export function ModesPanel() {
  const { t } = useTranslation()
  const sid = useUIStore(s => s.studyId)
  const [view, setView] = useState<View>('machine')
  useWhereSection('modes', sec => { if (['machine', 'matrix', 'energy', 'data', 'equipment', 'rules'].includes(sec)) setView(sec as View) })
  const { data, error, isLoading } = useModes(sid)
  const invalidate = useInvalidateModes(sid)
  const [busy, setBusy] = useState(false)

  if (!sid) return <div className="c2o-pane c2o-pane--empty c-2">{t('Open a study first.')}</div>
  if (isLoading) return <div className="c2o-pane c-2">{t('Loading…')}</div>
  if (error || !data) return <div className="c2o-pane"><Note tone="alarm">{t('Modes unavailable: {{msg}}', { msg: String((error as Error)?.message ?? '') })}</Note></div>

  const createTemplate = async (source: 'template' | 'conops') => {
    setBusy(true)
    try { await send(`/studies/${sid}/modes/template`, 'POST', { source, lang: i18n.language === 'fr' ? 'fr' : 'en' }); invalidate() }
    catch (e) { await showAlert(t('Could not create the modes: {{msg}}', { msg: (e as Error).message })) }
    finally { setBusy(false) }
  }

  if (!data.modes.length) {
    return (
      <div className="c2o-pane stack gap-3 measure">
        <p className="t-13 c-2 m-0">{t('No modes yet. Start from the ConOps set (LEOP, commissioning, nominal, imaging, downlink, safe, survival) and edit it, or import the study ConOps modes once.')}</p>
        <div className="row gap-2">
          <Button variant="primary" busy={busy} onClick={() => createTemplate('template')}>{t('Create the ConOps modes')}</Button>
          <Button busy={busy} onClick={() => createTemplate('conops')}>{t('Import the ConOps modes')}</Button>
        </div>
        <p className="t-12 c-3 m-0">{t('Source: {{ref}}', { ref: data.template_ref.standard_ref })}</p>
      </div>
    )
  }

  return (
    <div className="c2o-pane stack gap-4 mdl-pane">
      <Tabs idBase="modes" variant="segmented" label={t('Mode views')} value={view} onChange={setView}
        items={VIEWS.map(v => ({ id: v, label: t(VIEW_LABELS[v]) }))} />
      <div {...tabPanelProps('modes', view)} className="stack gap-4">
        {view === 'machine' && <MachineView data={data} sid={sid} onChange={invalidate} />}
        {view === 'machine' && <ConopsPhases studyId={sid} />}
        {view === 'matrix' && <MatrixView data={data} sid={sid} onChange={invalidate} />}
        {view === 'energy' && <EnergyView sid={sid} />}
        {view === 'data' && <DataChainView sid={sid} />}
        {view === 'equipment' && <EquipmentView sid={sid} />}
        {view === 'rules' && <RulesView sid={sid} />}
      </div>
    </div>
  )
}

// ───────────────────────────────────────────────────────────── machine

function MachineView({ data, sid, onChange }: { data: ModesOverview; sid: string; onChange: () => void }) {
  const { t } = useTranslation()
  const [sel, setSel] = useState<string | null>(null)
  const name = (id: string) => data.modes.find(m => m.id === id)?.name ?? id
  const patchMode = async (m: Mode, body: Record<string, unknown>) => {
    try { await send(`/studies/${sid}/modes/${m.id}`, 'PATCH', body); onChange() }
    catch (e) { await showAlert((e as Error).message) }
  }
  const addMode = async () => { await send(`/studies/${sid}/modes`, 'POST', { name: t('New mode'), kind: 'custom' }); onChange() }
  const delMode = async (m: Mode) => {
    if (!(await askConfirm(t('Delete mode "{{name}}" and its transitions?', { name: m.name }), { danger: true }))) return
    await send(`/studies/${sid}/modes/${m.id}`, 'DELETE'); onChange()
  }
  const addTransition = async () => {
    if (data.modes.length < 2) return
    await send(`/studies/${sid}/mode-transitions`, 'POST', { from_mode_id: data.modes[0].id, to_mode_id: data.modes[1].id, trigger: 'ground_tc' })
    onChange()
  }
  const patchTr = async (tr: Transition, body: Record<string, unknown>) => {
    try { await send(`/studies/${sid}/mode-transitions/${tr.id}`, 'PATCH', body); onChange() }
    catch (e) { await showAlert((e as Error).message) }
  }
  const delTr = async (tr: Transition) => { await send(`/studies/${sid}/mode-transitions/${tr.id}`, 'DELETE'); onChange() }
  const opsSum = data.modes.filter(m => ['nominal', 'imaging', 'downlink'].includes(m.kind)).reduce((s, m) => s + (m.orbit_fraction ?? 0), 0)

  const modeCols: Column<Mode>[] = [
    { key: 'name', header: t('Mode'), render: m => (
      <input className="c2o-input c2o-input--sm" defaultValue={m.name} aria-label={t('Name of {{name}}', { name: m.name })}
        onBlur={e => e.target.value.trim() && e.target.value !== m.name && patchMode(m, { name: e.target.value })} />) },
    { key: 'kind', header: t('Kind'), render: m => (
      <Select dense value={m.kind} aria-label={t('Kind of {{name}}', { name: m.name })} onChange={e => patchMode(m, { kind: e.target.value })}>
        {data.vocabulary.kinds.map(k => <option key={k} value={k}>{t(KIND_LABELS[k] ?? k)}</option>)}
      </Select>) },
    { key: 'phase', header: t('Phase'), render: m => <span className="t-12">{t(PHASE_LABELS[m.phase] ?? m.phase)}</span> },
    { key: 'pointing', header: t('Pointing'), render: m => (
      <Select dense value={m.pointing} aria-label={t('Pointing of {{name}}', { name: m.name })} onChange={e => patchMode(m, { pointing: e.target.value })}>
        {data.vocabulary.pointing.map(k => <option key={k} value={k}>{t(POINTING_LABELS[k] ?? k)}</option>)}
      </Select>) },
    { key: 'frac', header: t('Share of orbit'), num: true, render: m => (
      <input type="number" min={0} max={100} step={1} className="c2o-input c2o-input--sm c2o-input--num mdl-num"
        defaultValue={m.orbit_fraction != null ? Math.round(m.orbit_fraction * 1000) / 10 : ''}
        aria-label={t('Share of orbit for {{name}} (%)', { name: m.name })}
        onBlur={e => e.target.value !== '' && patchMode(m, { orbit_fraction: Number(e.target.value) / 100 })} />) },
    { key: 'sun', header: t('Daylight only'), center: true, render: m => (
      <input type="checkbox" checked={m.sunlit_only} aria-label={t('{{name}} only in daylight', { name: m.name })}
        onChange={e => patchMode(m, { sunlit_only: e.target.checked })} />) },
    { key: 'init', header: t('Initial'), center: true, render: m => (
      <input type="radio" name="mdl-initial" checked={m.initial} aria-label={t('{{name}} is the initial mode', { name: m.name })}
        onChange={() => patchMode(m, { initial: true })} />) },
    { key: 'del', header: '', render: m => <Button size="sm" variant="quiet" onClick={() => delMode(m)} aria-label={t('Delete {{name}}', { name: m.name })}>{t('Delete')}</Button> },
  ]
  const trCols: Column<Transition>[] = [
    { key: 'from', header: t('From'), render: tr => (
      <Select dense value={tr.from_mode_id} aria-label={t('From mode')} onChange={e => patchTr(tr, { from_mode_id: e.target.value })}>
        {data.modes.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
      </Select>) },
    { key: 'to', header: t('To'), render: tr => (
      <Select dense value={tr.to_mode_id} aria-label={t('To mode')} onChange={e => patchTr(tr, { to_mode_id: e.target.value })}>
        {data.modes.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
      </Select>) },
    { key: 'trig', header: t('Trigger'), render: tr => (
      <Select dense value={tr.trigger} aria-label={t('Trigger')} onChange={e => patchTr(tr, { trigger: e.target.value })}>
        {data.vocabulary.triggers.map(k => <option key={k} value={k}>{t(TRIGGER_LABELS[k] ?? k)}</option>)}
      </Select>) },
    { key: 'guard', header: t('Guard (monitored parameter, or text)'), render: tr => <GuardEditor tr={tr} onSave={g => patchTr(tr, { guard: g })} /> },
    { key: 'del', header: '', render: tr => <Button size="sm" variant="quiet" onClick={() => delTr(tr)} aria-label={t('Delete transition {{a}} to {{b}}', { a: name(tr.from_mode_id), b: name(tr.to_mode_id) })}>{t('Delete')}</Button> },
  ]

  return (
    <>
      <div className="row ai-s gap-5 wrap">
        <div className="ovf-auto mdl-diagram">
          <ModeDiagram modes={data.modes} transitions={data.transitions} findings={data.findings} selected={sel} onSelect={setSel} />
        </div>
        <div className="stack gap-2 mdl-findings">
          <h4 className="c2o-panel__title m-0">{t('Checks on the mode machine')}</h4>
          {data.findings.length === 0
            ? <StatusBadge status="ok">{t('Every mode reachable and left; autonomous transitions name a monitored parameter.')}</StatusBadge>
            : <ul className="list-reset stack gap-1">{data.findings.map((f, i) => (
                <li key={i}><StatusBadge status={f.severity === 'major' ? 'alarm' : 'caution'}>{bi(f.text)}</StatusBadge></li>))}</ul>}
          {Math.abs(opsSum - 1) > 0.005 && (
            <Note tone="caution">{t('The operational modes (nominal, imaging, downlink) share {{pct}} % of the orbit; they should add up to 100 %.', { pct: Math.round(opsSum * 1000) / 10 })}</Note>)}
        </div>
      </div>
      <Panel title={t('Modes')} meta={t('{{count}} modes', { count: data.modes.length, defaultValue_one: '{{count}} mode' })}
        actions={<Button size="sm" onClick={addMode}>{t('Add mode')}</Button>}>
        <DataTable dense caption={t('Modes')} columns={modeCols} rows={data.modes} rowKey={m => m.id}
          isSelected={m => m.id === sel} onRowClick={m => setSel(m.id)} />
      </Panel>
      <Panel title={t('Transitions')} meta={t('{{count}} transitions', { count: data.transitions.length, defaultValue_one: '{{count}} transition' })}
        actions={<Button size="sm" onClick={addTransition} disabled={data.modes.length < 2}>{t('Add transition')}</Button>}>
        <DataTable dense caption={t('Transitions')} columns={trCols}
          rows={sel ? data.transitions.filter(tr => tr.from_mode_id === sel || tr.to_mode_id === sel) : data.transitions}
          rowKey={tr => tr.id} empty={<NoData label={t('no transitions')} />} />
        {sel && <button type="button" className="link t-12" onClick={() => setSel(null)}>{t('Show all transitions')}</button>}
      </Panel>
      <p className="t-12 c-3 m-0">{t('Template and guard thresholds: {{ref}}', { ref: data.template_ref.standard_ref })}</p>
    </>
  )
}

function GuardEditor({ tr, onSave }: { tr: Transition; onSave: (g: Record<string, unknown>) => void }) {
  const { t } = useTranslation()
  const g = tr.guard || {}
  const text = g.param ? `${g.param} ${g.op ?? '<'} ${g.value ?? ''}${g.unit ? ' ' + g.unit : ''}` : (g.text ?? '')
  return (
    <input className="c2o-input c2o-input--sm mdl-guard" defaultValue={text} aria-label={t('Guard')}
      placeholder={t('e.g. battery.soc_percent < 20 %')}
      onBlur={e => {
        const v = e.target.value.trim()
        if (v === text) return
        const m = v.match(/^([\w.]+)\s*(<=|>=|<|>|==)\s*(-?[\d.]+)\s*(\S*)$/)
        onSave(m ? { param: m[1], op: m[2], value: Number(m[3]), unit: m[4] || undefined } : { text: v })
      }} />
  )
}

// ───────────────────────────────────────────────────────────── matrix

function MatrixView({ data, sid, onChange }: { data: ModesOverview; sid: string; onChange: () => void }) {
  const { t } = useTranslation()
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const cell = useMemo(() => {
    const m = new Map<string, Member>()
    for (const r of data.members) m.set(`${r.mode_id}|${r.element_id}`, r)
    return m
  }, [data.members])
  const counts = data.members.reduce<Record<string, number>>((acc, r) => { acc[r.status] = (acc[r.status] ?? 0) + 1; return acc }, {})
  const propose = async () => {
    setBusy(true)
    try {
      const r = await send<{ counts: Record<string, number> }>(`/studies/${sid}/modes/propose`, 'POST')
      setMsg(t('{{new}} new, {{refreshed}} refreshed, {{stale}} marked stale, {{kept}} unchanged', r.counts))
      onChange()
    } catch (e) { await showAlert((e as Error).message) } finally { setBusy(false) }
  }
  const acceptAll = async () => { await send(`/studies/${sid}/modes/members/accept-all`, 'POST'); onChange() }
  const totals = data.modes.map(m => data.members.filter(r => r.mode_id === m.id && r.status !== 'rejected')
    .reduce((s, r) => s + (r.power_w_in_mode ?? 0) * (r.duty_cycle_percent ?? 100) / 100, 0))
  const rates = data.modes.map(m => data.members.filter(r => r.mode_id === m.id && r.status !== 'rejected')
    .reduce((s, r) => s + (r.data_rate_bps ?? 0), 0))

  return (
    <>
      <div className="row wrap gap-2">
        <Button variant="primary" busy={busy} onClick={propose}
          title={t('Proposes each unit’s state, power and data rate in every mode (rule MO-01)')}>{t('Propose powers per mode')}</Button>
        {(counts.suggested || counts.stale) ? <Button onClick={acceptAll}>{t('Accept {{n}} suggested or stale', { n: (counts.suggested ?? 0) + (counts.stale ?? 0) })}</Button> : null}
        <span className="grow" />
        {Object.entries(counts).map(([k, v]) => <Tag key={k}>{t(STATUS_LABELS[k] ?? k)} · {v}</Tag>)}
      </div>
      {msg && <Note tone="info" role="status">{msg}</Note>}
      <p className="t-12 c-3 m-0">{t('Cell: power in the mode (W) and the unit state. Italic with a dashed outline = suggested by a rule; a clock = stale, the part or its inputs changed since you accepted. Click a cell to edit, accept or reject it. Defaults: {{ref}}.', { ref: data.states_ref.standard_ref })}</p>
      {!data.units.length
        ? <Note>{t('No hardware units yet: add components with a power figure in the Blocks panel.')}</Note>
        : (
          <div className="ovf-auto">
            <table className="c2o-table c2o-table--dense mdl-matrix">
              <caption className="sr-only">{t('Power of each unit in each mode')}</caption>
              <thead>
                <tr>
                  <th scope="col">{t('Unit')}</th>
                  {data.modes.map(m => (
                    <th key={m.id} scope="col" className="num">{m.name}
                      {t(KIND_LABELS[m.kind] ?? m.kind) !== m.name && <div className="t-12 c-3 w-400">{t(KIND_LABELS[m.kind] ?? m.kind)}</div>}
                    </th>))}
                </tr>
              </thead>
              <tbody>
                {data.units.map(u => (
                  <tr key={u.id}>
                    <th scope="row" className="w-500">
                      {u.name}{u.quantity > 1 ? ` ×${u.quantity}` : ''}
                      <div className="t-12 c-3 w-400">{u.unit_class}{u.stale ? ' · ' : ''}{u.stale && <StatusBadge status="stale">{t('KB part changed')}</StatusBadge>}</div>
                    </th>
                    {data.modes.map(m => <MatrixCell key={m.id} sid={sid} mode={m} unit={u} row={cell.get(`${m.id}|${u.id}`)} onChange={onChange} />)}
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row">{t('Total (W, current best estimate)')}</th>
                  {totals.map((v, i) => <td key={i} className="ta-r mono w-600">{fmtNum(v, 1)}</td>)}
                </tr>
                <tr>
                  <th scope="row">{t('Data produced (kbit/s)')}</th>
                  {rates.map((v, i) => <td key={i} className="ta-r mono">{fmtNum(v / 1000, v >= 1e5 ? 0 : 1)}</td>)}
                </tr>
              </tfoot>
            </table>
          </div>
        )}
    </>
  )
}

function MatrixCell({ sid, mode, unit, row, onChange }: { sid: string; mode: Mode; unit: Unit; row?: Member; onChange: () => void }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [w, setW] = useState('')
  const [st, setSt] = useState('nominal')
  if (!row) return <td className="ta-r"><NoData label={t('not set')} /></td>
  const put = async (body: Record<string, unknown>) => {
    try { await send(`/studies/${sid}/modes/${mode.id}/members/${unit.id}`, 'PUT', body); setOpen(false); onChange() }
    catch (e) { await showAlert((e as Error).message) }
  }
  const cls = `ta-r mdl-cell mdl-cell--${row.status}`
  const label = t('{{unit}} in {{mode}}', { unit: unit.name, mode: mode.name })
  if (open) {
    return (
      <td className={cls}>
        <div className="stack gap-1 mdl-cell-edit">
          <input type="number" min={0} step={0.1} autoFocus className="c2o-input c2o-input--sm c2o-input--num" value={w}
            aria-label={t('Power (W) of {{what}}', { what: label })} onChange={e => setW(e.target.value)}
            onKeyDown={e => { if (e.key === 'Escape') setOpen(false); if (e.key === 'Enter') void put({ power_w_in_mode: Number(w), power_state: st }) }} />
          <Select dense value={st} aria-label={t('State of {{what}}', { what: label })} onChange={e => setSt(e.target.value)}>
            {['off', 'standby', 'nominal', 'peak'].map(s => <option key={s} value={s}>{t(STATE_LABELS[s])}</option>)}
          </Select>
          <div className="row gap-1">
            <Button size="sm" variant="primary" onClick={() => put({ power_w_in_mode: Number(w), power_state: st })}>{t('Save')}</Button>
            {row.status !== 'accepted' && <Button size="sm" onClick={() => put({ action: 'accept' })}>{t('Accept')}</Button>}
            {row.status !== 'rejected' && <Button size="sm" variant="quiet" onClick={() => put({ action: 'reject' })}>{t('Reject')}</Button>}
          </div>
          {row.source_ref && <span className="t-12 c-3">{row.source_ref}</span>}
        </div>
      </td>
    )
  }
  return (
    <td className={cls}>
      <button type="button" className="bare mdl-cell-btn" aria-label={`${label}: ${fmtNum(row.power_w_in_mode ?? 0, 2)} W, ${t(STATE_LABELS[row.power_state ?? 'nominal'] ?? '')}, ${t(STATUS_LABELS[row.status] ?? row.status)}`}
        title={[row.notes, row.source_ref].filter(Boolean).join(' · ')}
        onClick={() => { setW(String(row.power_w_in_mode ?? 0)); setSt(row.power_state ?? 'nominal'); setOpen(true) }}>
        {row.status === 'stale' && <StatusBadge status="stale"><span className="sr-only">{t('Stale, review')}</span></StatusBadge>}
        <span className="mono">{fmtNum(row.power_w_in_mode ?? 0, (row.power_w_in_mode ?? 0) < 10 ? 2 : 1)}</span>
        <span className="t-12 c-3 mdl-state">{t(STATE_LABELS[row.power_state ?? 'nominal'] ?? '')}</span>
      </button>
    </td>
  )
}

// ───────────────────────────────────────────────────────────── energy

function MarginNote({ sm }: { sm: SystemMargin | undefined }) {
  const { t } = useTranslation()
  if (!sm) return null
  const pct = sm.percent ?? sm.power_percent
  return (
    <p className="t-12 c-3 m-0 measure">
      {t('System margin {{pct}} % at {{gate}} ({{label}}); maturity margins per unit from the margin policy.', {
        pct, gate: (sm.gate ?? '—').toUpperCase(), label: bi(sm.label) })}{' '}
      {bi(sm.convention?.text)}
    </p>
  )
}

function EnergyView({ sid }: { sid: string }) {
  const { t } = useTranslation()
  const { data, error } = useQuery<Energy>({ queryKey: modeKeys(sid).energy, queryFn: () => get(`/studies/${sid}/modes/energy`), refetchInterval: 8000 })
  if (error) return <Note tone="alarm">{(error as Error).message}</Note>
  if (!data) return <p className="t-13 c-2">{t('Loading…')}</p>
  const rows = data.modes
  const maxW = Math.max(1, ...rows.map(r => Math.max(r.power_total_w, r.generation_sunlit_w * (data.orbit.sunlit_s / data.orbit.period_s))))
  const maxWh = Math.max(1, ...rows.map(r => Math.abs(r.balance_wh ?? 0)))
  const cols: Column<typeof rows[number]>[] = [
    { key: 'name', header: t('Mode'), render: r => <span className="w-500">{r.name}</span> },
    { key: 'cbe', header: t('Load CBE (W)'), num: true, render: r => fmtNum(r.power_cbe_w, 2), sort: r => r.power_cbe_w },
    { key: 'mat', header: t('+ maturity (W)'), num: true, render: r => fmtNum(r.power_with_maturity_w, 2) },
    { key: 'tot', header: t('+ system (W)'), num: true, render: r => <span className="w-600">{fmtNum(r.power_total_w, 2)}</span>, sort: r => r.power_total_w },
    { key: 'gen', header: t('Array in sun (W)'), num: true, render: r => `${fmtNum(r.generation_sunlit_w, 1)} (×${r.array_factor})` },
    { key: 'bal', header: t('Balance per orbit (Wh)'), num: true, render: r => r.balance_wh == null ? <NoData label={t('no data')} /> : fmtNum(r.balance_wh, 2), sort: r => r.balance_wh },
    { key: 'dod', header: t('DoD (%)'), num: true, render: r => r.dod_percent == null ? <NoData label={t('no data')} /> : fmtNum(r.dod_percent, 1), sort: r => r.dod_percent },
    { key: 'st', header: t('Held a full orbit'), render: r => (
      r.status === 'fail' && !r.held_full_orbit
        ? <StatusBadge status="caution" title={t('A short mode: its share of the orbit is checked under Operational orbit.')}>{t('Short mode only')}</StatusBadge>
        : <StatusBadge status={statusOf(r.status)}>{r.status === 'pass' ? t('Sustainable') : r.status === 'fail' ? t('Not sustainable') : t('Not evaluated')}</StatusBadge>) },
  ]
  const ops = data.operational_orbit
  return (
    <>
      <MarginNote sm={data.system_margin} />
      {data.warnings.map((w, i) => <Note key={i} tone="caution">{w}</Note>)}
      <Panel title={t('Power and energy per mode')} meta={t('orbit {{min}} min, eclipse {{pct}} %', { min: fmtNum(data.orbit.period_s / 60, 1), pct: fmtNum(data.orbit.eclipse_fraction * 100, 1) })}>
        <svg role="img" aria-label={t('Load with margins against orbit-average generation, and energy balance per orbit, for each mode')}
          viewBox={`0 0 780 ${rows.length * 30 + 34}`} className="mdl-chart" width="100%">
          <text x={0} y={12} className="mdl-axis">{t('Load with margins vs orbit-average generation (W)')}</text>
          <text x={470} y={12} className="mdl-axis">{t('Energy balance per orbit (Wh)')}</text>
          <line x1={600} x2={600} y1={20} y2={rows.length * 30 + 26} className="mdl-zero" />
          {rows.map((r, i) => {
            const y = 26 + i * 30
            const lw = (r.power_total_w / maxW) * 230
            const gAvg = r.generation_sunlit_w * (data.orbit.sunlit_s / data.orbit.period_s)
            const gx = 110 + (gAvg / maxW) * 230
            const b = r.balance_wh ?? 0
            const bw = (Math.abs(b) / maxWh) * 120
            return (
              <g key={r.mode_id}>
                <text x={104} y={y + 12} textAnchor="end" className="mdl-label">{r.name.length > 15 ? r.name.slice(0, 14) + '…' : r.name}</text>
                <rect x={110} y={y + 2} width={Math.max(lw, 1)} height={14} className="mdl-bar" />
                <text x={114 + lw} y={y + 13} className="mdl-val">{fmtNum(r.power_total_w, 1)}</text>
                {data.inputs.sa_power_eol_w ? <line x1={gx} x2={gx} y1={y - 1} y2={y + 19} className="mdl-gen"><title>{t('Orbit-average generation {{w}} W', { w: fmtNum(gAvg, 1) })}</title></line> : null}
                {r.balance_wh != null && (
                  <>
                    <rect x={b >= 0 ? 600 : 600 - bw} y={y + 2} width={Math.max(bw, 1)} height={14}
                      className={b >= 0 ? 'mdl-bal mdl-bal--pos' : 'mdl-bal mdl-bal--neg'} />
                    <text x={b >= 0 ? 604 + bw : 596 - bw} y={y + 13} textAnchor={b >= 0 ? 'start' : 'end'} className="mdl-val">{fmtNum(b, 1)}</text>
                  </>
                )}
              </g>
            )
          })}
        </svg>
        <div className="row wrap gap-4 t-12 c-3">
          <span className="row gap-1"><svg width="14" height="10" aria-hidden="true"><rect width="14" height="10" className="mdl-bar" /></svg>{t('Load with maturity and system margins')}</span>
          <span className="row gap-1"><svg width="10" height="14" aria-hidden="true"><line x1="5" x2="5" y1="0" y2="14" className="mdl-gen" /></svg>{t('Orbit-average generation in the mode’s attitude')}</span>
          <span className="row gap-1"><svg width="14" height="10" aria-hidden="true"><rect width="14" height="10" className="mdl-bal mdl-bal--neg" /></svg>{t('Energy deficit (battery drains)')}</span>
        </div>
      </Panel>
      <DataTable dense caption={t('Energy per mode')} columns={cols} rows={rows} rowKey={r => r.mode_id} />
      {ops && (
        <Panel title={t('Operational orbit')} meta={ops.modes.map(m => `${m.name} ${Math.round(m.orbit_fraction * 100)} %`).join(' · ')}>
          <div className="row wrap gap-5">
            <Figure label={t('Generated')} value={fmtNum(ops.generated_wh, 1)} unit="Wh" />
            <Figure label={t('Needed (incl. battery losses)')} value={fmtNum(ops.needed_wh, 1)} unit="Wh" />
            <Figure label={t('Balance')} value={ops.balance_wh == null ? '—' : fmtNum(ops.balance_wh, 1)} unit="Wh" />
            <Figure label={t('Depth of discharge')} value={ops.dod_percent == null ? '—' : fmtNum(ops.dod_percent, 1)} unit="%" />
            <StatusBadge status={statusOf(ops.status)} boxed>{ops.status === 'pass' ? t('Positive with margins') : ops.status === 'fail' ? t('Negative or DoD over limit') : t('Not evaluated')}</StatusBadge>
          </div>
          {data.sustainable_duty.length > 0 && (
            <ul className="list-reset stack gap-1 mt-3">
              {data.sustainable_duty.map(d => (
                <li key={d.mode_id} className="t-13">
                  <StatusBadge status={statusOf(d.status)}>
                    {t('{{name}}: up to {{max}} % of the orbit is sustainable (planned {{plan}} %)', { name: d.name,
                      max: fmtNum(d.sustainable_fraction * 100, 1), plan: fmtNum((d.planned_fraction ?? 0) * 100, 1) })}
                  </StatusBadge>
                </li>))}
            </ul>
          )}
        </Panel>
      )}
      <p className="t-12 c-3 m-0">{t('Array {{sa}} W EOL ({{sas}}), battery {{bat}} Wh ({{bats}}), round trip {{eta}}, DoD limit {{dod}} %. Attitude factors: {{ref}}.', {
        sa: data.inputs.sa_power_eol_w ?? '—', sas: data.inputs.sa_power_source || t('not set'), bat: data.inputs.battery_capacity_wh ?? '—',
        bats: data.inputs.battery_source || t('not set'), eta: data.inputs.battery_efficiency, dod: data.inputs.max_dod_percent,
        ref: data.inputs.array_factor_ref.standard_ref })}</p>
    </>
  )
}

function Figure({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="stack gap-0">
      <span className="t-12 c-3">{label}</span>
      <span><span className="mono t-15 c-v w-600">{value}</span> <span className="t-12 c-3">{unit}</span></span>
    </div>
  )
}

// ───────────────────────────────────────────────────────────── data chain

function DataChainView({ sid }: { sid: string }) {
  const { t } = useTranslation()
  const { data, error } = useQuery<DataChain>({ queryKey: modeKeys(sid).data, queryFn: () => get(`/studies/${sid}/modes/data-chain`), refetchInterval: 10000 })
  if (error) return <Note tone="alarm">{(error as Error).message}</Note>
  if (!data) return <p className="t-13 c-2">{t('Loading…')}</p>
  const chk = Object.fromEntries(data.checks.map(c => [c.id, c]))
  const st = data.storage, dl = data.downlink
  return (
    <>
      <div className="mdl-flow" role="group" aria-label={t('Data chain')}>
        <div className="mdl-flow__box">
          <span className="t-12 c-3">{t('Generated')}</span>
          <span><span className="mono t-20 c-v">{fmtNum(data.generated_gb_per_day, 2)}</span> <span className="t-12 c-3">{t('GB/day')}</span></span>
          <span className="t-12 c-3">{data.housekeeping?.designed
            ? t('payload in each mode + stored housekeeping from the TM/TC SIDs ({{mb}} MB/day)', { mb: fmtNum(data.housekeeping.stored_mb_per_day, 2) })
            : t('payload in each mode + {{hk}} kbit/s housekeeping', { hk: fmtNum(data.housekeeping_bps / 1000, 1) })}</span>
        </div>
        <span className="mdl-flow__arrow" aria-hidden="true">→</span>
        <div className="mdl-flow__box">
          <span className="t-12 c-3">{t('Stored on board')}</span>
          <span><span className="mono t-20 c-v">{st.capacity_gb == null ? '—' : fmtNum(st.capacity_gb, 1)}</span> <span className="t-12 c-3">GB</span></span>
          <span className="t-12 c-3">{t('needs {{need}} GB ({{days}} day + {{m}} %)', { need: fmtNum(st.need_with_margin_gb, 2), days: st.buffer_days, m: st.margin_percent })}</span>
          {chk['DC-STORAGE'] && <StatusBadge status={statusOf(chk['DC-STORAGE'].status)}>{bi(chk['DC-STORAGE'].label)}</StatusBadge>}
        </div>
        <span className="mdl-flow__arrow" aria-hidden="true">→</span>
        <div className="mdl-flow__box">
          <span className="t-12 c-3">{dl.capacity_basis === 'after_realtime_hk' ? t('Downlink capacity left for stored data') : t('Downlink capacity')}</span>
          {dl.capacity_gb_per_day < 1
            ? <span><span className="mono t-20 c-v">{fmtNum(dl.capacity_gb_per_day * 1000, 2)}</span> <span className="t-12 c-3">{t('MB/day')}</span></span>
            : <span><span className="mono t-20 c-v">{fmtNum(dl.capacity_gb_per_day, 2)}</span> <span className="t-12 c-3">{t('GB/day')}</span></span>}
          {dl.capacity_basis === 'after_realtime_hk' && dl.total_capacity_mb_per_day != null &&
            <span className="t-12 c-3">{t('of {{total}} MB/day channel capacity (data budget)', { total: fmtNum(dl.total_capacity_mb_per_day, 2) })}</span>}
          <span className="t-12 c-3">{t('{{min}} min/day at {{rate}} Mbit/s ({{band}}-band) × {{eff}}', { min: fmtNum(dl.contact_min_per_day, 1),
            rate: fmtNum(dl.rate_bps / 1e6, 4), band: dl.band ?? '?', eff: dl.protocol_efficiency })}</span>
          {dl.contact_basis === 'union' && <span className="t-12 c-3">{t('union of the passes (the stations add up to {{sum}} min/day; one transmitter)', { sum: fmtNum(dl.sum_of_stations_min_per_day ?? 0, 1) })}</span>}
          {data.housekeeping?.designed && <span className="t-12 c-3">{t('after {{rt}} MB/day of real-time housekeeping in contact', { rt: fmtNum(data.housekeeping.realtime_mb_per_day, 2) })}</span>}
          {chk['DC-DOWNLINK'] && <StatusBadge status={statusOf(chk['DC-DOWNLINK'].status)}>{bi(chk['DC-DOWNLINK'].label)}</StatusBadge>}
        </div>
      </div>
      {data.data_budget?.closure && <DailyClosure c={data.data_budget.closure} />}
      {data.backlog_growth_gb_per_day > 0
        ? <Note tone="alarm">{t('The backlog grows by {{gb}} GB per day{{full}}.', { gb: fmtNum(data.backlog_growth_gb_per_day, 2),
            full: data.days_to_full != null ? t('; storage is full after {{d}} days', { d: fmtNum(data.days_to_full, 1) }) : '' })}</Note>
        : <Note tone="ok">{t('Every day’s data is downlinked the same day.')}</Note>}
      {chk['DC-LINK-MARGIN'] && <Note tone="caution">{bi(chk['DC-LINK-MARGIN'].label)} — {chk['DC-LINK-MARGIN'].standard_ref}</Note>}
      {data.warnings.map((w, i) => <Note key={i} tone="caution">{w}</Note>)}
      <div className="row ai-s wrap gap-5">
        <Panel title={t('Generation per mode')}>
          <DataTable dense caption={t('Generation per mode')} rows={data.per_mode} rowKey={r => r.mode_id} columns={[
            { key: 'n', header: t('Mode'), render: r => r.name },
            { key: 'r', header: t('kbit/s'), num: true, render: r => fmtNum(r.generation_bps / 1000, 1) },
            { key: 'h', header: t('Stored HK (bit/s)'), num: true, render: r => r.hk_stored_bps == null ? '' : fmtNum(r.hk_stored_bps, 1) },
            { key: 'rt', header: t('Real-time HK in contact (bit/s)'), num: true, render: r => r.hk_realtime_bps == null ? '' : fmtNum(r.hk_realtime_bps, 0) },
            { key: 'f', header: t('Share of orbit'), num: true, render: r => r.orbit_fraction != null ? `${fmtNum(r.orbit_fraction * 100, 0)} %` : '' },
            { key: 'o', header: t('MB per orbit'), num: true, render: r => fmtNum(r.per_orbit_mb, 1) },
          ]} />
        </Panel>
        <Panel title={t('Contact plan')}>
          <DataTable dense caption={t('Contact plan')} rows={dl.stations} rowKey={r => r.name} empty={<NoData label={t('no station')} />} columns={[
            { key: 'n', header: t('Station'), render: r => r.name },
            { key: 'm', header: t('min/day'), num: true, render: r => fmtNum(r.contact_min_per_day, 1) },
            { key: 'g', header: t('Margin (dB)'), num: true, render: r => r.margin_db == null ? <NoData label={t('no data')} /> : fmtNum(r.margin_db, 1) },
            { key: 'c', header: t('GB/day'), num: true, render: r => fmtNum(r.capacity_gb_per_day, 3) },
            { key: 's', header: t('Used'), render: r => <StatusBadge status={!r.used ? 'alarm' : r.low_margin ? 'caution' : 'ok'}>{!r.used ? t('Link does not close') : r.low_margin ? t('Low margin') : t('Yes')}</StatusBadge> },
          ]} />
        </Panel>
      </div>
    </>
  )
}

/** W3.05: the daily closure case of the data budget, as the Data budget page and the exports quote it. */
function closureText(c: DailyCase): { capacity: string; demand: string; margin: string; tone: 'ok' | 'caution' | 'alarm' | 'nodata' } {
  return {
    capacity: fmtNum(c.capacity_mb, 2), demand: fmtNum(c.demand_mb, 2),
    margin: c.margin_pct == null ? '—' : `${c.margin_pct >= 0 ? '+' : ''}${fmtNum(c.margin_pct, 1)}`,
    tone: c.status === 'pass' ? 'ok' : c.status === 'warn' ? 'caution' : c.status === 'fail' ? 'alarm' : 'nodata',
  }
}

function DailyClosure({ c }: { c: DailyCase }) {
  const { t } = useTranslation()
  const x = closureText(c)
  return (
    <p className="t-13 c-2 m-0 row gap-2 ai-c" data-testid="daily-closure">
      <StatusBadge status={x.tone}>{t('Daily closure {{case}}: {{margin}} %', { case: c.id, margin: x.margin })}</StatusBadge>
      <span>{t('{{demand}} MB/day of {{capacity}} MB/day downlink capacity (real-time HK, stored HK, science); same numbers as the Data budget page', { demand: x.demand, capacity: x.capacity })}</span>
    </p>
  )
}

// ───────────────────────────────────────────────────────────── equipment → budgets

type Measure = 'power' | 'data' | 'heat'
// English text is the i18n key
const MEASURE_LABELS: Record<Measure, string> = { power: 'Power (W)', data: 'Data (kbit/s)', heat: 'Heat (W)' }

function EquipmentView({ sid }: { sid: string }) {
  const { t } = useTranslation()
  const [measure, setMeasure] = useState<Measure>('power')
  const { data, error } = useQuery<EquipBudgets>({ queryKey: modeKeys(sid).equip, queryFn: () => get(`/studies/${sid}/budgets/equipment`), refetchInterval: 8000 })
  if (error) return <Note tone="alarm">{(error as Error).message}</Note>
  if (!data) return <p className="t-13 c-2">{t('Loading…')}</p>
  const pick = (r: EquipBudgets['rows'][number], mid: string) =>
    measure === 'power' ? r.power_by_mode_w[mid] : measure === 'data' ? (r.data_by_mode_bps[mid] ?? 0) / 1000 : r.dissipation_by_mode_w[mid]
  const tot = (mid: string) => measure === 'power' ? data.totals.power_by_mode_w[mid] : measure === 'data'
    ? (data.totals.data_by_mode_bps[mid] ?? 0) / 1000 : data.totals.dissipation_by_mode_w[mid]
  const cols: Column<EquipBudgets['rows'][number]>[] = [
    { key: 'n', header: t('Unit'), render: r => <span className="w-500">{r.name}{r.quantity > 1 ? ` ×${r.quantity}` : ''}{r.stale && <> <StatusBadge status="stale">{t('stale')}</StatusBadge></>}</span>, sort: r => r.name },
    { key: 'cat', header: t('Maturity'), render: r => <span title={r.maturity_from}><Tag mono>{r.maturity_category}</Tag> {r.maturity_percent} %</span>, sort: r => r.maturity_percent },
    { key: 'm', header: t('Mass (kg)'), num: true, render: r => fmtNum(r.mass_kg, 3), sort: r => r.mass_kg, foot: fmtNum(data.totals.mass_cbe_kg, 3) },
    { key: 'mm', header: t('+ maturity (kg)'), num: true, render: r => fmtNum(r.mass_with_maturity_kg, 3), foot: fmtNum(data.totals.mass_with_maturity_kg, 3) },
    { key: 'c', header: t('Cost (kEUR)'), num: true, render: r => r.cost_keur == null ? <NoData label={t('no data')} /> : fmtNum(r.cost_keur, 1), foot: fmtNum(data.totals.cost_keur, 1) },
    ...data.modes.map(m => ({
      key: `m-${m.id}`, header: m.name, num: true,
      render: (r: EquipBudgets['rows'][number]) => pick(r, m.id) == null ? <NoData label={t('n/a')} /> : fmtNum(pick(r, m.id), measure === 'data' ? 0 : 2),
      foot: tot(m.id) != null ? fmtNum(tot(m.id), measure === 'data' ? 0 : 1) : '',
    })),
    { key: 'l', header: t('Link'), render: r => r.link ? <span className="t-12">{[r.link.band, r.link.tx_power_w != null ? `${r.link.tx_power_w} W RF` : null,
      r.link.data_rate_bps ? `${fmtNum(r.link.data_rate_bps / 1e6, 2)} Mbit/s` : null].filter(Boolean).join(' · ')}</span> : '' },
  ]
  return (
    <>
      <div className="row wrap gap-3">
        <Tabs idBase="eqm" variant="segmented" label={t('Per-mode figure')} value={measure} onChange={setMeasure}
          items={(Object.keys(MEASURE_LABELS) as Measure[]).map(k => ({ id: k, label: t(MEASURE_LABELS[k]) }))} />
        <span className="grow" />
        <Figure label={t('Mass with maturity and system margin')} value={fmtNum(data.totals.mass_total_kg, 2)} unit="kg" />
      </div>
      <MarginNote sm={{ ...data.system_margin, percent: data.system_margin.mass_percent }} />
      <DataTable dense caption={t('Equipment to budgets')} columns={cols} rows={data.rows} rowKey={r => r.element_id} />
      {measure === 'power' && (
        <p className="t-12 c-3 m-0">{t('With maturity and system margins per mode (W): {{list}}', {
          list: data.modes.map(m => `${m.name} ${fmtNum(data.totals.power_by_mode_total_w[m.id] ?? 0, 1)}`).join(' · ') })}</p>)}
      <p className="t-12 c-3 m-0">{bi(data.note)}</p>
    </>
  )
}

// ───────────────────────────────────────────────────────────── rules & proposals

function RulesView({ sid }: { sid: string }) {
  const { t } = useTranslation()
  const invalidate = useInvalidateModes(sid)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const { data } = useQuery<{ proposals: Proposal[]; refs: { function_catalogue: { id: string; name: { en: string; fr: string } }[]; config_errors: string[] } }>({
    queryKey: modeKeys(sid).proposals, queryFn: () => get(`/studies/${sid}/design-rules/proposals`), refetchInterval: 10000 })
  const { data: stale } = useQuery<{ stale: StaleRow[] }>({ queryKey: modeKeys(sid).stale, queryFn: () => get(`/studies/${sid}/kb-staleness`) })
  const run = async () => {
    setBusy(true)
    try {
      const r = await send<{ counts: Record<string, number> }>(`/studies/${sid}/design-rules/run`, 'POST')
      setResult(t('{{new}} new, {{refreshed}} refreshed, {{stale}} marked stale, {{withdrawn}} withdrawn', r.counts))
      invalidate()
    } catch (e) { await showAlert((e as Error).message) } finally { setBusy(false) }
  }
  const decide = async (p: Proposal, action: 'accept' | 'reject') => {
    try { await send(`/studies/${sid}/design-rules/proposals/${p.id}/${action}`, 'POST'); invalidate() }
    catch (e) { await showAlert((e as Error).message) }
  }
  const markStale = async () => { await send(`/studies/${sid}/kb-staleness/mark`, 'POST'); invalidate() }
  const refresh = async (eid: string) => {
    try { await send(`/elements/${eid}/kb-refresh`, 'POST'); invalidate() } catch (e) { await showAlert((e as Error).message) }
  }
  const props = data?.proposals ?? []
  const kinds: Proposal['kind'][] = ['monitor', 'action', 'risk', 'heater']
  return (
    <>
      <div className="row wrap gap-2">
        <Button variant="primary" busy={busy} onClick={run}
          title={t('FMECA → monitors and event-actions, single points and analysis-only verification → risks, cold case → heaters')}>{t('Run the rules')}</Button>
        <span className="t-12 c-3">{t('Proposals are kept: a rejected one is never proposed again; an accepted one whose inputs change is marked stale.')}</span>
      </div>
      {result && <Note tone="info" role="status">{result}</Note>}
      <Note>{t('Monitors and event-actions are proposals only: the TM/TC and FDIR design model comes in phase 2. Actions are checked against a placeholder function catalogue.')}</Note>
      {kinds.map(k => {
        const list = props.filter(p => p.kind === k)
        return (
          <Disclosure key={k} summary={t(PROPOSAL_KIND_LABELS[k])} meta={t('{{count}} proposals', { count: list.length, defaultValue_one: '{{count}} proposal' })} ruled defaultOpen={k === 'monitor' || k === 'heater'}>
            {list.length === 0 ? <p className="t-13 c-3 m-0">{t('None yet. Run the rules.')}</p> : (
              <ul className="list-reset stack gap-2">
                {list.map(p => <ProposalRow key={p.id} p={p} onDecide={decide} />)}
              </ul>
            )}
          </Disclosure>
        )
      })}
      <Panel title={t('Knowledge-base changes')} meta={t('{{count}} elements', { count: stale?.stale.length ?? 0, defaultValue_one: '{{count}} element' })}
        actions={stale?.stale.some(s => s.reason !== 'never_copied') ? <Button size="sm" onClick={markStale}>{t('Mark stale for review')}</Button> : undefined}>
        {!stale?.stale.length ? <StatusBadge status="ok">{t('Every element matches its KB part.')}</StatusBadge> : (
          <ul className="list-reset stack gap-1">
            {stale.stale.map(s => (
              <li key={s.element_id} className="row wrap gap-2 t-13">
                <StatusBadge status="stale">{s.name}</StatusBadge>
                <span className="c-3 t-12">{s.reason === 'kb_changed' ? t('KB part changed: {{f}}', { f: s.changed.join(', ') || '—' })
                  : s.reason === 'kb_part_missing' ? t('KB part no longer in the catalogue') : t('copied before Nov 2026: re-apply once')}</span>
                {s.reason !== 'kb_part_missing' && <Button size="sm" onClick={() => refresh(s.element_id)}>{t('Re-apply KB part')}</Button>}
              </li>))}
          </ul>
        )}
      </Panel>
    </>
  )
}

function ProposalRow({ p, onDecide }: { p: Proposal; onDecide: (p: Proposal, a: 'accept' | 'reject') => void }) {
  const { t } = useTranslation()
  const st: Status = p.status === 'accepted' ? 'ok' : p.status === 'rejected' ? 'neutral' : p.status === 'stale' ? 'stale' : 'info'
  const pl = p.payload
  let detail = ''
  if (p.kind === 'monitor') detail = `${pl.parameter} · ${pl.check}${pl.low != null ? ` ≥ ${pl.low}` : ''}${pl.high != null ? ` ≤ ${pl.high}` : ''}${pl.expected != null ? ` = ${pl.expected}` : ''} · ×${pl.persistence} @ ${pl.period_s} s`
  if (p.kind === 'action') detail = `${pl.event_from} → ${pl.function_id}${pl.level ? ` (L${pl.level})` : ''}`
  if (p.kind === 'risk') detail = `L${pl.likelihood} × C${pl.consequence}`
  if (p.kind === 'heater') detail = `${pl.power_w} W · ${t('on {{on}} / off {{off}} °C', { on: pl.on_c, off: pl.off_c })} · ${pl.line?.name ?? ''}`
  return (
    <li className={`mdl-prop mdl-prop--${p.status}`}>
      <div className="row wrap gap-2">
        <Tag mono>{p.rule_id}</Tag>
        <StatusBadge status={st}>{t(STATUS_LABELS[p.status] ?? p.status)}</StatusBadge>
        <span className="t-13 grow">{bi(p.rationale)}</span>
        {p.status !== 'accepted' && <Button size="sm" onClick={() => onDecide(p, 'accept')}>{t('Accept')}</Button>}
        {p.status !== 'rejected' && <Button size="sm" variant="quiet" onClick={() => onDecide(p, 'reject')}>{t('Reject')}</Button>}
      </div>
      <div className="t-12 c-3 mono mdl-prop__detail">{detail}</div>
      {p.kind === 'action' && pl.replaced && (
        <div className="t-12 c-caution">{t('{{f}} replaced: {{why}}', { f: pl.replaced.function_id, why: bi(pl.replaced.problems?.[0]?.text) })}</div>)}
      <div className="t-12 c-3">{p.c2o_default ? <Tag>{t('C2O default')}</Tag> : null} {p.standard_ref}{p.result_ref ? ` · ${p.result_ref}` : ''}</div>
    </li>
  )
}
