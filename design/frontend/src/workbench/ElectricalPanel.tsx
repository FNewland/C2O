/**
 * ElectricalPanel — the Electrical tab: power rails and the power-line / switch matrix
 * (design rules EI-01, EB-08; §2.1).
 *
 * Rows come from the rules (proposed from the accepted and suggested power links and the
 * KB parts: one switched, current-limited line per load, LCL trip = 1.5 × peak current,
 * state at separation and at boot from the line policy) or from the Power seat. Every
 * proposal is accepted, edited or rejected here; an edited row is never overwritten, and
 * when its inputs change it is flagged "Needs review". The checks (line current P/V vs LCL,
 * rail capacity, EPS output channels, rail voltage vs the unit's input) sit above.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { useUIStore } from '../stores/uiStore'
import { Button, DataTable, Field, Input, NoData, Note, Panel, Select, Tag, type Column } from '../components/ui'
import { displayElementName } from './BlocksPanel'
import {
  createRow, deleteRow, patchRow, proposeElectrical, useElectrical, useInvalidateElectrical,
  type ElementLite, type Kind, type PowerLine, type Rail,
} from './electricalApi'
import { DiagramFigure } from '../diagrams/DiagramFigure'
import { CommitInput, FindingMark, FindingsList, ProfileNote, ProposalCell } from './electricalParts'

const API = '/api'

// English text is the i18n key: inhibit identifiers (configs/electrical_rules.yaml).
const INHIBIT_LABELS: Record<string, string> = {
  deployment_switch: 'Deployment switches',
  rbf: 'Remove-before-flight pin',
  rf_tx_timer: 'RF transmit timer',
}

const num = (s: string): number | null | undefined => {
  const v = s.trim().replace(',', '.')
  if (!v) return null
  const n = Number(v)
  return Number.isFinite(n) ? n : undefined
}
/** Locale number (decimal comma in French), no grouping: also what the inputs show and parse back. */
const fmt = (n: number | null | undefined, d = 2) => (n == null ? '' : n.toLocaleString(
  i18n.language?.startsWith('fr') ? 'fr-FR' : 'en-GB', { maximumFractionDigits: d, useGrouping: false }))

export function ElectricalPanel() {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const { data: view, isLoading, error: loadError } = useElectrical(studyId)
  const invalidate = useInvalidateElectrical(studyId)
  const { data: elements = [] } = useQuery<ElementLite[]>({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false, refetchInterval: 3000,
  })
  const els = useMemo(() => new Map<string, ElementLite>(elements.map(e => [e.id, e])), [elements])
  const nameOf = (id: string | null | undefined) => (id && els.get(id) ? displayElementName(els.get(id)!.name, t) : t('(unknown element)'))

  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastRun, setLastRun] = useState<string | null>(null)
  const run = async (key: string, fn: () => Promise<unknown>) => {
    setBusy(key); setError(null)
    try { await fn(); invalidate() } catch (e) { setError(String((e as Error).message || e)) } finally { setBusy(null) }
  }
  const patch = (kind: Kind, id: string, body: Record<string, unknown>) => run(id, () => patchRow(studyId!, kind, id, body))
  const remove = (kind: Kind, id: string) => run(id, () => deleteRow(studyId!, kind, id))
  const propose = () => run('propose', async () => {
    const r = await proposeElectrical(studyId!)
    setLastRun(t('{{created}} new, {{updated}} updated, {{unchanged}} unchanged', r))
  })

  const [showAdd, setShowAdd] = useState(false)
  const [addName, setAddName] = useState('')
  const [addRail, setAddRail] = useState('')
  const [addLoad, setAddLoad] = useState('')

  if (!studyId) return null
  if (isLoading) return <div className="c2o-pane t-13 c-3">{t('Loading…')}</div>
  if (loadError || !view) {
    return <div className="c2o-pane"><Note tone="alarm">{t('The electrical model could not be loaded: {{message}}', { message: String((loadError as Error)?.message ?? '') })}</Note></div>
  }

  const rails = [...view.rails].sort((a, b) => a.voltage_v - b.voltage_v)
  const railById = new Map(rails.map(r => [r.id, r]))
  const lines = [...view.lines].sort((a, b) => (a.eps_element_id ?? '').localeCompare(b.eps_element_id ?? '') || a.line_no - b.line_no)
  const live = <T extends { status: string }>(xs: T[]) => xs.filter(x => x.status !== 'rejected')
  const findingsFor = (kind: string, id: string) => view.checks.filter(c => c.target_kind === kind && c.target_id === id)
  const powerChecks = view.checks.filter(c => ['rails', 'lines'].includes(c.target_kind) || c.id.startsWith('PWR-'))
  const loadsOn = new Set(live(lines).flatMap(l => l.load_element_ids))
  const powered = elements.filter((e) => e.element_type === 'component' && !e.deleted_at && ((e.power_avg_w ?? 0) > 0 || (e.power_peak_w ?? 0) > 0))
  const lineCurrent = (l: PowerLine) => {
    const v = railById.get(l.rail_id ?? '')?.voltage_v
    if (!v) return null
    const w = l.load_element_ids.reduce((s, id) => {
      const e = els.get(id); if (!e) return s
      return s + (e.power_peak_w ?? e.power_avg_w ?? 0) * Math.max(1, e.quantity ?? 1)
    }, 0)
    return { w, a: w / v }
  }

  const railCols: Column<Rail>[] = [
    { key: 'name', header: t('Rail'), render: r => <span className="mono w-500">{r.name}</span>, sort: r => r.voltage_v },
    { key: 'eps', header: t('Provided by'), render: r => nameOf(r.eps_element_id), sort: r => nameOf(r.eps_element_id) },
    { key: 'kind', header: t('Kind'), render: r => r.regulated ? t('Regulated') : t('Unregulated battery bus') },
    { key: 'range', header: t('Range (V)'), num: true, render: r => (r.v_min != null && r.v_max != null ? `${fmt(r.v_min)}–${fmt(r.v_max)}` : <NoData label={t('n/a')} />) },
    { key: 'cap', header: t('Converter rating (A)'), num: true, render: r => (
      <CommitInput label={t('Converter rating of {{name}} (A)', { name: r.name })} value={fmt(r.max_current_a)} placeholder={t('unknown')}
        onCommit={v => { const n = num(v); if (n !== undefined) patch('rails', r.id, { max_current_a: n }) }} />) },
    { key: 'chk', header: t('Check'), center: true, render: r => <FindingMark findings={findingsFor('rails', r.id)} /> },
    { key: 'st', header: t('Status'), render: r => <ProposalCell row={r} label={r.name} busy={busy === r.id} onPatch={b => patch('rails', r.id, b)} onDelete={() => remove('rails', r.id)} /> },
  ]

  const lineCols: Column<PowerLine>[] = [
    { key: 'no', header: t('No.'), num: true, width: 64, sort: l => l.line_no, render: l => (
      <CommitInput label={t('Number of line {{name}}', { name: l.name })} value={String(l.line_no)} width={44}
        onCommit={v => { const n = num(v); if (n != null && Number.isInteger(n)) patch('lines', l.id, { line_no: n }) }} />) },
    { key: 'name', header: t('Line and loads'), sort: l => l.name, render: l => (
      <span className="stack gap-0">
        <span className="w-500">{l.name}</span>
        <span className="t-12 c-3">{l.load_element_ids.length ? l.load_element_ids.map(nameOf).join(', ') : t('no load')}</span>
      </span>) },
    { key: 'eps', header: t('EPS'), render: l => <span className="t-12">{nameOf(l.eps_element_id)}</span> },
    { key: 'rail', header: t('Rail'), render: l => (
      <Select dense aria-label={t('Rail of line {{name}}', { name: l.name })} value={l.rail_id ?? ''}
        onChange={e => patch('lines', l.id, { rail_id: e.target.value || null })}>
        <option value="">{t('(none)')}</option>
        {live(rails).filter(r => !l.eps_element_id || r.eps_element_id === l.eps_element_id).map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
      </Select>) },
    { key: 'cur', header: t('Peak current (A)'), num: true, sort: l => lineCurrent(l)?.a ?? null, render: l => {
      const c = lineCurrent(l)
      return c ? <span className="mono" title={t('{{w}} W / {{v}} V', { w: fmt(c.w), v: fmt(railById.get(l.rail_id ?? '')?.voltage_v) })}>{fmt(c.a, 3)}</span> : <NoData label={t('n/a')} />
    } },
    { key: 'lcl', header: t('LCL trip (A)'), num: true, sort: l => l.lcl_limit_a, render: l => (
      <CommitInput label={t('LCL trip current of line {{name}} (A)', { name: l.name })} value={fmt(l.lcl_limit_a)} width={60}
        onCommit={v => { const n = num(v); if (n !== undefined) patch('lines', l.id, { lcl_limit_a: n }) }} />) },
    { key: 'sw', header: t('Switchable'), center: true, render: l => (
      <input type="checkbox" checked={l.switchable} aria-label={t('Line {{name}} is switchable', { name: l.name })}
        onChange={e => patch('lines', l.id, { switchable: e.target.checked })} />) },
    { key: 'sep', header: t('On at separation'), center: true, render: l => (
      <input type="checkbox" checked={l.default_on_separation} aria-label={t('Line {{name}} on at separation', { name: l.name })}
        onChange={e => patch('lines', l.id, { default_on_separation: e.target.checked })} />) },
    { key: 'boot', header: t('On at boot'), center: true, render: l => (
      <input type="checkbox" checked={l.default_on_boot} aria-label={t('Line {{name}} on at boot', { name: l.name })}
        onChange={e => patch('lines', l.id, { default_on_boot: e.target.checked })} />) },
    { key: 'inh', header: t('Inhibits'), render: l => (
      <span className="row gap-1 wrap">{l.inhibits.length ? l.inhibits.map(i => <Tag key={i} title={i}>{t(INHIBIT_LABELS[i] ?? i)}</Tag>) : <span className="t-12 c-3">{t('none')}</span>}</span>) },
    { key: 'chk', header: t('Check'), center: true, render: l => <FindingMark findings={findingsFor('lines', l.id)} /> },
    { key: 'st', header: t('Status'), render: l => <ProposalCell row={l} label={l.name} busy={busy === l.id} onPatch={b => patch('lines', l.id, b)} onDelete={() => remove('lines', l.id)} /> },
  ]

  const eps = Array.from(new Set(live(rails).map(r => r.eps_element_id).filter(Boolean))) as string[]
  const addLine = () => run('add', async () => {
    const rail = railById.get(addRail)
    const next = Math.max(-1, ...lines.filter(l => l.eps_element_id === rail?.eps_element_id).map(l => l.line_no)) + 1
    await createRow(studyId!, 'lines', {
      name: addName || nameOf(addLoad), rail_id: addRail || null, eps_element_id: rail?.eps_element_id ?? eps[0] ?? null,
      line_no: next, switchable: true, load_element_ids: addLoad ? [addLoad] : [], inhibits: ['deployment_switch', 'rbf'],
    })
    setShowAdd(false); setAddName(''); setAddLoad('')
  })

  const summary = t('{{rails}} rails, {{lines}} lines, {{open}} to review', {
    rails: live(rails).length, lines: live(lines).length,
    open: [...rails, ...lines].filter(r => r.status === 'suggested' || r.review).length,
  })

  return (
    <div className="c2o-pane c2o-el" data-testid="electrical-panel">
      <Panel title={t('Electrical')} meta={summary}
        actions={<>
          <Button size="sm" onClick={propose} busy={busy === 'propose'}
            title={t('Run the power distribution rules. Rejected and edited rows are kept.')}>{t('Propose from links')}</Button>
          <Button variant="primary" size="sm" onClick={() => setShowAdd(true)}
            disabledReason={!live(rails).length ? t('Propose or add a rail first') : showAdd ? t('The add form is already open below') : undefined}>{t('+ Add line')}</Button>
        </>}>
        <ProfileNote view={view} />
        {lastRun && <p className="t-12 c-3 m-0 pb-2" role="status">{t('Rules run: {{summary}}', { summary: lastRun })}</p>}
        {error && <Note tone="alarm" role="alert">{t('The server refused the change: {{message}}', { message: error })}</Note>}
        <FindingsList findings={powerChecks} empty={t('No power distribution finding.')} />

        {showAdd && (
          <form className="c2o-blocks__add mb-3" aria-label={t('Add power line')} onSubmit={e => { e.preventDefault(); addLine() }}>
            <Field label={t('Rail')}>
              <Select dense value={addRail} onChange={e => setAddRail(e.target.value)}>
                <option value="">{t('Choose a rail')}</option>
                {live(rails).map(r => <option key={r.id} value={r.id}>{`${r.name} · ${nameOf(r.eps_element_id)}`}</option>)}
              </Select>
            </Field>
            <Field label={t('Load')}>
              <Select dense value={addLoad} onChange={e => setAddLoad(e.target.value)}>
                <option value="">{t('(none)')}</option>
                {powered.map((e) => <option key={e.id} value={e.id}>{displayElementName(e.name, t)}{loadsOn.has(e.id) ? ` ${t('(on a line)')}` : ''}</option>)}
              </Select>
            </Field>
            <Field label={t('Line name (optional)')}><Input dense value={addName} onChange={e => setAddName(e.target.value)} /></Field>
            <span className="row gap-2">
              <Button type="submit" variant="primary" size="sm" busy={busy === 'add'}
                disabledReason={!addRail ? t('Choose a rail first') : undefined}>{t('Add')}</Button>
              <Button size="sm" onClick={() => setShowAdd(false)}>{t('Cancel')}</Button>
            </span>
          </form>
        )}

        <section className="c2o-el__sec" aria-labelledby="el-rails">
          <h4 id="el-rails" className="c2o-links__h">{t('Power rails')}</h4>
          <DataTable dense rows={rails} rowKey={r => r.id} columns={railCols} caption={t('Power rails')}
            rowClassName={r => (r.status === 'rejected' ? 'is-rejected' : r.status === 'suggested' ? 'is-suggested' : undefined)}
            empty={t('No rail yet. Accept the power links (Interfaces tab) and click "Propose from links".')} />
        </section>

        <section className="c2o-el__sec" aria-labelledby="el-lines">
          <h4 id="el-lines" className="c2o-links__h">{t('Power lines and switches')}</h4>
          <p className="t-12 c-3 m-0 pb-2 measure">{t('One line per load: the EPS switches it (unless always-on) and its LCL trips above the set current. "On at separation" is the state once the deployment switches release, "On at boot" the state the flight software sets at first boot.')}</p>
          <DataTable dense rows={lines} rowKey={l => l.id} columns={lineCols} caption={t('Power lines and switches')}
            defaultSort={{ key: 'no', dir: 'asc' }}
            rowClassName={l => (l.status === 'rejected' ? 'is-rejected' : l.status === 'suggested' ? 'is-suggested' : undefined)}
            empty={t('No power line yet.')} />
        </section>

        <section className="c2o-dgm-embed" aria-label={t('Diagrams')}>
          <DiagramFigure studyId={studyId} kind="power" compact />
          <div className="mt-4"><DiagramFigure studyId={studyId} kind="switch_matrix" compact /></div>
        </section>
      </Panel>
    </div>
  )
}
