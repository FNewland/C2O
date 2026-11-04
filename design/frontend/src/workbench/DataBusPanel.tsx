/**
 * DataBusPanel — the Data tab: data buses and the address plan (design rules EI-02, IF-07; §2.4).
 *
 * Buses are proposed per master and protocol from the TM/TC links (CAN with enough nodes is
 * split into segments A and B, as EOSAT-1's bus A = EPS, TCS, AOCS / bus B = TT&C, payload);
 * each node gets a default address from the C2O address plan, unique on its segment. The
 * checks flag duplicate or out-of-range addresses, too many devices, bus load above the 50 %
 * margin and units that do not speak the bus protocol.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { Button, DataTable, Field, Note, Panel, Select, StatusBadge, type Column } from '../components/ui'
import { displayElementName } from './BlocksPanel'
import {
  createRow, deleteRow, hex, parseAddress, patchRow, proposeElectrical, useElectrical, useInvalidateElectrical,
  type BusNode, type DataBus, type ElementLite, type Kind,
} from './electricalApi'
import { DiagramFigure } from '../diagrams/DiagramFigure'
import { CommitInput, FindingMark, FindingsList, ProfileNote, ProposalCell } from './electricalParts'

const API = '/api'
const kbit = (bps: number | null | undefined) => (bps == null ? '' : bps >= 1e6 ? `${bps / 1e6} Mbit/s` : `${bps / 1e3} kbit/s`)

export function DataBusPanel() {
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
  const [addFor, setAddFor] = useState<string | null>(null)
  const [addEl, setAddEl] = useState('')
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

  if (!studyId) return null
  if (isLoading) return <div className="c2o-pane t-13 c-3">{t('Loading…')}</div>
  if (loadError || !view) {
    return <div className="c2o-pane"><Note tone="alarm">{t('The electrical model could not be loaded: {{message}}', { message: String((loadError as Error)?.message ?? '') })}</Note></div>
  }

  const buses = [...view.buses].sort((a, b) => a.protocol.localeCompare(b.protocol) || a.name.localeCompare(b.name))
  const nodesOf = (bid: string) => view.nodes.filter(n => n.bus_id === bid)
  const findingsFor = (kind: string, id: string) => view.checks.filter(c => c.target_kind === kind && c.target_id === id)
  const dataChecks = view.checks.filter(c => c.target_kind === 'buses' || c.target_kind === 'nodes')
  const live = (xs: BusNode[]) => xs.filter(x => x.status !== 'rejected')
  const load = (b: DataBus) => live(nodesOf(b.id)).reduce((s, n) => s + (n.data_rate_bps ?? 0), 0)
  const components = elements.filter((e) => e.element_type === 'component' && !e.deleted_at)

  const busCols: Column<DataBus>[] = [
    { key: 'name', header: t('Bus'), sort: b => b.name, render: b => <span className="mono w-500">{b.name}</span> },
    { key: 'proto', header: t('Protocol'), sort: b => b.protocol, render: b => b.protocol },
    { key: 'seg', header: t('Segment'), render: b => (
      <CommitInput label={t('Segment of {{name}}', { name: b.name })} value={b.segment} width={44}
        onCommit={v => v.trim() && patch('buses', b.id, { segment: v.trim() })} />) },
    { key: 'rate', header: t('Bit rate'), num: true, sort: b => b.bit_rate_bps, render: b => <span className="mono">{kbit(b.bit_rate_bps)}</span> },
    { key: 'master', header: t('Master'), render: b => nameOf(b.master_element_id) },
    { key: 'nodes', header: t('Nodes'), num: true, render: b => `${live(nodesOf(b.id)).length}${b.max_devices ? ` / ${b.max_devices}` : ''}` },
    { key: 'load', header: t('Load', { context: 'bus' }), num: true, render: b => {
      const l = load(b)
      return b.bit_rate_bps ? <span className="mono">{`${Math.round(1000 * l / b.bit_rate_bps) / 10} %`}</span> : <span className="c-3">—</span>
    } },
    { key: 'red', header: t('Redundancy'), render: b => (
      <Select dense aria-label={t('Redundancy of {{name}}', { name: b.name })} value={b.redundancy}
        onChange={e => patch('buses', b.id, { redundancy: e.target.value })}>
        <option value="none">{t('None', { context: 'redundancy' })}</option>
        <option value="cold">{t('Cold redundant')}</option>
        <option value="hot">{t('Hot redundant')}</option>
      </Select>) },
    { key: 'chk', header: t('Check'), center: true, render: b => <FindingMark findings={[...findingsFor('buses', b.id), ...nodesOf(b.id).flatMap(n => findingsFor('nodes', n.id))]} /> },
    { key: 'st', header: t('Status'), render: b => <ProposalCell row={b} label={b.name} busy={busy === b.id} onPatch={x => patch('buses', b.id, x)} onDelete={() => remove('buses', b.id)} /> },
  ]

  const nodeCols = (b: DataBus): Column<BusNode>[] => {
    const p = view.protocols[b.protocol] ?? {}
    const range = p.address_min != null && p.address_max != null ? `${hex(p.address_min)}–${hex(p.address_max)}` : null
    return [
      { key: 'el', header: t('Element'), sort: n => nameOf(n.element_id), render: n => <span className="w-500">{nameOf(n.element_id)}</span> },
      { key: 'role', header: t('Role'), render: n => (n.role === 'master' ? t('Master') : t('Node')) },
      { key: 'addr', header: range ? t('Address ({{range}})', { range }) : t('Address'), num: true, sort: n => n.address, render: n => {
        const dup = findingsFor('nodes', n.id).some(f => f.id.startsWith('DATA-ADDR'))
        return range
          ? <CommitInput label={t('Address of {{name}} on {{bus}}', { name: nameOf(n.element_id), bus: b.name })} value={hex(n.address)} width={64} invalid={dup}
              onCommit={v => { const a = parseAddress(v); if (a !== undefined) patch('nodes', n.id, { address: a }) }} />
          : <span className="t-12 c-3">{t('point to point')}</span>
      } },
      { key: 'rate', header: t('Data rate (bit/s)'), num: true, render: n => (
        <CommitInput label={t('Data rate of {{name}} (bit/s)', { name: nameOf(n.element_id) })} value={n.data_rate_bps == null ? '' : String(n.data_rate_bps)} width={80}
          placeholder={t('unknown')}
          onCommit={v => { const x = v.trim() ? Number(v) : null; if (x === null || Number.isFinite(x)) patch('nodes', n.id, { data_rate_bps: x }) }} />) },
      { key: 'chk', header: t('Check'), center: true, render: n => <FindingMark findings={findingsFor('nodes', n.id)} /> },
      { key: 'st', header: t('Status'), render: n => <ProposalCell row={n} label={nameOf(n.element_id)} busy={busy === n.id} onPatch={x => patch('nodes', n.id, x)} onDelete={() => remove('nodes', n.id)} /> },
    ]
  }

  const summary = t('{{buses}} buses, {{nodes}} nodes, {{open}} to review', {
    buses: buses.filter(b => b.status !== 'rejected').length, nodes: live(view.nodes).length,
    open: [...view.buses, ...view.nodes].filter(r => r.status === 'suggested' || r.review).length,
  })

  return (
    <div className="c2o-pane c2o-el" data-testid="data-panel">
      <Panel title={t('Data buses and address plan')} meta={summary}
        actions={<Button size="sm" onClick={propose} busy={busy === 'propose'}
          title={t('Run the data bus rules. Rejected and edited rows are kept.')}>{t('Propose from links')}</Button>}>
        <ProfileNote view={view} />
        {lastRun && <p className="t-12 c-3 m-0 pb-2" role="status">{t('Rules run: {{summary}}', { summary: lastRun })}</p>}
        {error && <Note tone="alarm" role="alert">{t('The server refused the change: {{message}}', { message: error })}</Note>}
        <FindingsList findings={dataChecks} empty={t('No data bus finding.')} />

        <section className="c2o-el__sec" aria-labelledby="el-buses">
          <h4 id="el-buses" className="c2o-links__h">{t('Buses')}</h4>
          <DataTable dense rows={buses} rowKey={b => b.id} columns={busCols} caption={t('Buses')}
            rowClassName={b => (b.status === 'rejected' ? 'is-rejected' : b.status === 'suggested' ? 'is-suggested' : undefined)}
            empty={t('No bus yet. Accept the TM/TC links (Interfaces tab) and click "Propose from links".')} />
        </section>

        {buses.filter(b => b.status !== 'rejected').map(b => (
          <section key={b.id} className="c2o-el__sec" aria-label={t('Address plan of {{name}}', { name: b.name })}>
            <h4 className="c2o-links__h">
              <span>{t('Address plan: {{name}}', { name: b.name })}</span>
              {(() => {
                const dup = nodesOf(b.id).flatMap(n => findingsFor('nodes', n.id)).filter(f => f.id.startsWith('DATA-ADDR-DUP'))
                return dup.length > 0 && <StatusBadge status={dup.some(f => f.severity === 'alarm') ? 'alarm' : 'caution'}>{t('Address conflict')}</StatusBadge>
              })()}
              <Button size="sm" variant="quiet" className="ml-auto" onClick={() => { setAddFor(b.id); setAddEl('') }}>{t('+ Add node')}</Button>
            </h4>
            {addFor === b.id && (
              <form className="c2o-blocks__add mb-2" aria-label={t('Add node')} onSubmit={e => {
                e.preventDefault()
                if (addEl) run('add', async () => { await createRow(studyId!, 'nodes', { bus_id: b.id, element_id: addEl, role: 'node' }); setAddFor(null) })
              }}>
                <Field label={t('Element')}>
                  <Select dense value={addEl} onChange={e => setAddEl(e.target.value)}>
                    <option value="">{t('Choose an element')}</option>
                    {components.map((e) => <option key={e.id} value={e.id}>{displayElementName(e.name, t)}</option>)}
                  </Select>
                </Field>
                <span className="row gap-2">
                  <Button type="submit" variant="primary" size="sm" busy={busy === 'add'} disabledReason={!addEl ? t('Choose an element first') : undefined}>{t('Add')}</Button>
                  <Button size="sm" onClick={() => setAddFor(null)}>{t('Cancel')}</Button>
                </span>
              </form>
            )}
            <DataTable dense rows={nodesOf(b.id)} rowKey={n => n.id} columns={nodeCols(b)} caption={t('Address plan of {{name}}', { name: b.name })}
              defaultSort={{ key: 'addr', dir: 'asc' }}
              rowClassName={n => (n.status === 'rejected' ? 'is-rejected' : findingsFor('nodes', n.id).some(f => f.severity === 'alarm') ? 'is-alarm' : n.status === 'suggested' ? 'is-suggested' : undefined)}
              empty={t('No node on this bus.')} />
          </section>
        ))}
        <section className="c2o-dgm-embed" aria-label={t('Diagrams')}>
          <DiagramFigure studyId={studyId} kind="data_bus" compact />
        </section>
      </Panel>
    </div>
  )
}
