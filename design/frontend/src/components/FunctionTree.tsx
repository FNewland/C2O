/**
 * FunctionTree — server-backed Arcadia function tree (SCDF-160).
 *
 * Reads GET /api/studies/{id}/functions/tree and edits through the
 * functions router: add child / rename / delete / layer / allocation to a
 * design element / ports / functional exchanges. Shows a
 * "Migrate legacy functions" button while the tree is empty.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { useDesignStore } from '../stores/designStore'
import {
  ARCADIA_LAYERS, LAYER_COLORS, LAYER_LABELS,
  type ArcadiaLayer, type FunctionNode, type FunctionalExchange, type FunctionPort, type FunctionUpdate,
} from '../types/arcadia'
import { fs } from '../theme/tokens'
import { askConfirm } from './ui/Dialog'

const API = '/api'

const inputStyle: React.CSSProperties = {
  padding: '0.15rem 0.35rem', fontSize: fs.label, borderRadius: '3px',
  background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
}
const smallBtn = (color = 'var(--text-secondary)'): React.CSSProperties => ({
  background: 'none', border: '1px solid var(--border)', borderRadius: '3px', cursor: 'pointer',
  fontSize: fs.label, padding: '0.1rem 0.35rem', color,
})

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    let msg = `${res.status}`
    try { const b = await res.json(); msg = typeof b.detail === 'string' ? b.detail : JSON.stringify(b.detail ?? b) } catch { /* noop */ }
    throw new Error(msg)
  }
  return res.status === 204 ? null : res.json()
}

function flatten(nodes: FunctionNode[], out: FunctionNode[] = []): FunctionNode[] {
  for (const n of nodes) { out.push(n); flatten(n.children || [], out) }
  return out
}

export function LayerBadge({ layer, onChange }: { layer: string; onChange?: (l: ArcadiaLayer) => void }) {
  const { t } = useTranslation()
  const color = LAYER_COLORS[layer as ArcadiaLayer] || 'var(--text-3)'
  const layerLabel = LAYER_LABELS[layer as ArcadiaLayer] ? t(LAYER_LABELS[layer as ArcadiaLayer]) : layer
  if (!onChange) {
    return <span title={layerLabel} style={{
      fontSize: fs.label, fontWeight: 700, padding: '0 0.3rem', borderRadius: '3px',
      background: `color-mix(in srgb, ${color} 15%, transparent)`, color, border: `1px solid color-mix(in srgb, ${color} 38%, transparent)`,
    }}>{layer}</span>
  }
  return (
    <select value={layer} onChange={e => onChange(e.target.value as ArcadiaLayer)}
      title={t('Arcadia layer: {{layer}}', { layer: layerLabel })}
      style={{ ...inputStyle, fontSize: fs.label, fontWeight: 700, padding: '0 0.2rem', color, borderColor: `color-mix(in srgb, ${color} 38%, transparent)`, background: `color-mix(in srgb, ${color} 8%, transparent)` }}>
      {ARCADIA_LAYERS.map(l => <option key={l} value={l}>{l}</option>)}
    </select>
  )
}

export function FunctionTree({ studyId: studyIdProp }: { studyId?: string | null }) {
  const uiStudyId = useUIStore(s => s.studyId)
  const designStudyId = useDesignStore(s => s.studyId)
  const studyId = studyIdProp ?? uiStudyId ?? designStudyId
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const [showExchanges, setShowExchanges] = useState(true)

  const { data: tree = [], isLoading } = useQuery<FunctionNode[]>({
    queryKey: ['functions-tree', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/functions/tree`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })
  const { data: elements = [] } = useQuery<any[]>({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })
  const { data: exchanges = [] } = useQuery<FunctionalExchange[]>({
    queryKey: ['functional-exchanges', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/functional-exchanges`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['functions-tree', studyId] })
    qc.invalidateQueries({ queryKey: ['functional-exchanges', studyId] })
  }
  const onErr = (e: Error) => setError(e.message)

  const createFn = useMutation({
    mutationFn: (body: { name: string; parent_id: string | null; layer: string; level: number }) =>
      fetch(`${API}/functions/?study_id=${studyId}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const updateFn = useMutation({
    mutationFn: ({ id, body }: { id: string; body: FunctionUpdate }) =>
      fetch(`${API}/functions/${id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const deleteFn = useMutation({
    mutationFn: (id: string) => fetch(`${API}/functions/${id}`, { method: 'DELETE' }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const allocate = useMutation({
    mutationFn: ({ id, element_id, layer }: { id: string; element_id: string; layer: string }) =>
      fetch(`${API}/functions/${id}/allocate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ element_id, layer }),
      }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const unallocate = useMutation({
    mutationFn: ({ id, layer }: { id: string; layer: string }) =>
      fetch(`${API}/functions/${id}/allocate/${layer}`, { method: 'DELETE' }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const createPort = useMutation({
    mutationFn: ({ id, name, direction }: { id: string; name: string; direction: string }) =>
      fetch(`${API}/functions/${id}/ports`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, direction }),
      }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const deletePort = useMutation({
    mutationFn: (portId: string) => fetch(`${API}/function-ports/${portId}`, { method: 'DELETE' }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const createExchange = useMutation({
    mutationFn: (body: { name: string; from_port_id: string; to_port_id: string }) =>
      fetch(`${API}/functional-exchanges/?study_id=${studyId}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const deleteExchange = useMutation({
    mutationFn: (id: string) => fetch(`${API}/functional-exchanges/${id}`, { method: 'DELETE' }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const migrate = useMutation({
    mutationFn: () => fetch(`${API}/studies/${studyId}/functions/migrate-legacy`, { method: 'POST' }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })

  if (!studyId) {
    return <div style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: fs.label }}>{t('Create or join a study to edit functions.')}</div>
  }

  const all = flatten(tree)
  const portsById = new Map<string, { port: FunctionPort; fn: FunctionNode }>()
  for (const fn of all) for (const p of fn.ports || []) portsById.set(p.id, { port: p, fn })
  const unallocated = all.filter(f => (f.allocations || []).length === 0).length

  const toggle = (id: string) => setCollapsed(prev => {
    const n = new Set(prev); if (n.has(id)) n.delete(id); else n.add(id); return n
  })

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: fs.label, overflow: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
        <span style={{ fontWeight: 600, fontSize: fs.label }}>{t('Functions ({{n}})', { n: all.length })}</span>
        <span style={{ color: 'var(--text-secondary)', fontSize: fs.label }}>
          {unallocated > 0 ? t('{{n}} unallocated', { n: unallocated }) : t('all allocated')} · {t('{{n}} exchanges', { n: exchanges.length })}
        </span>
        <span style={{ flex: 1 }} />
        {ARCADIA_LAYERS.map(l => <LayerBadge key={l} layer={l} />)}
        <button style={smallBtn('var(--interactive)')}
          onClick={() => createFn.mutate({ name: t('New function'), parent_id: null, layer: 'SA', level: 0 })}>
          {t('+ Root function')}
        </button>
        <button style={smallBtn()} onClick={() => setShowExchanges(v => !v)}>
          {showExchanges ? t('Hide exchanges') : t('Show exchanges')}
        </button>
      </div>

      {error && (
        <div style={{ color: 'var(--status-alarm)', fontSize: fs.label, marginBottom: '0.4rem', display: 'flex', gap: '0.5rem' }}>
          <span>{error}</span>
          <button style={smallBtn('var(--status-alarm)')} onClick={() => setError(null)}>{t('dismiss')}</button>
        </div>
      )}

      {isLoading && <div style={{ color: 'var(--text-secondary)' }}>{t('Loading…')}</div>}

      {!isLoading && tree.length === 0 && (
        <div className="card" style={{ borderLeft: '3px solid var(--status-caution)', marginBottom: '0.5rem' }}>
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
            {t("No functions in the model yet. Add a root function, or import the functions stored in the study's legacy functional decomposition.")}
          </div>
          <button style={{ ...smallBtn('var(--status-caution)'), padding: '0.25rem 0.6rem' }} disabled={migrate.isPending}
            onClick={() => migrate.mutate()}>
            {migrate.isPending ? t('Migrating…') : t('Migrate legacy functions')}
          </button>
          {migrate.data && (
            <div style={{ fontSize: fs.label, color: 'var(--status-ok)', marginTop: '0.3rem' }}>
              {Object.entries(migrate.data).filter(([k]) => k !== 'study_id').map(([k, v]) => `${k}: ${v}`).join(' · ')}
            </div>
          )}
        </div>
      )}

      {tree.map(node => (
        <FunctionRowView key={node.id} node={node} depth={0} elements={elements} collapsed={collapsed} toggle={toggle}
          onRename={(id, version, name) => updateFn.mutate({ id, body: { version, name } })}
          onLayer={(id, version, layer) => updateFn.mutate({ id, body: { version, layer } })}
          onAddChild={(parent) => createFn.mutate({ name: t('New function'), parent_id: parent.id, layer: parent.layer, level: (parent.level || 0) + 1 })}
          onDelete={async (id) => { if ((await askConfirm(t('Delete this function and its sub-functions?')))) deleteFn.mutate(id) }}
          onAllocate={(id, element_id, layer) => allocate.mutate({ id, element_id, layer })}
          onUnallocate={(id, layer) => unallocate.mutate({ id, layer })}
          onAddPort={(id, name, direction) => createPort.mutate({ id, name, direction })}
          onDeletePort={(portId) => deletePort.mutate(portId)}
        />
      ))}

      {showExchanges && all.length > 0 && (
        <ExchangesSection exchanges={exchanges} portsById={portsById}
          onCreate={(b) => createExchange.mutate(b)} onDelete={(id) => deleteExchange.mutate(id)} />
      )}
    </div>
  )
}

interface RowProps {
  node: FunctionNode
  depth: number
  elements: any[]
  collapsed: Set<string>
  toggle: (id: string) => void
  onRename: (id: string, version: number, name: string) => void
  onLayer: (id: string, version: number, layer: ArcadiaLayer) => void
  onAddChild: (parent: FunctionNode) => void
  onDelete: (id: string) => void
  onAllocate: (id: string, elementId: string, layer: string) => void
  onUnallocate: (id: string, layer: string) => void
  onAddPort: (id: string, name: string, direction: string) => void
  onDeletePort: (portId: string) => void
}

function FunctionRowView(p: RowProps) {
  const { node, depth } = p
  const { t } = useTranslation()
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(node.name)
  const [picking, setPicking] = useState(false)
  const [pickId, setPickId] = useState('')
  const [addingPort, setAddingPort] = useState(false)
  const [portName, setPortName] = useState('')
  const [portDir, setPortDir] = useState('out')
  const isCollapsed = p.collapsed.has(node.id)
  const kids = node.children || []
  const allocs = node.allocations || []
  const ports = node.ports || []

  const commitName = () => {
    setEditing(false)
    const v = name.trim()
    if (v && v !== node.name) p.onRename(node.id, node.version, v)
    else setName(node.name)
  }

  return (
    <div style={{ marginLeft: depth ? '1rem' : 0, borderLeft: depth ? '1px solid var(--border)' : 'none', paddingLeft: depth ? '0.5rem' : 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.15rem 0', flexWrap: 'wrap' }}>
        <button onClick={() => p.toggle(node.id)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', width: 14, padding: 0, fontSize: fs.label }}>
          {kids.length > 0 ? (isCollapsed ? '▸' : '▾') : '·'}
        </button>
        <LayerBadge layer={node.layer} onChange={(l) => p.onLayer(node.id, node.version, l)} />
        {editing ? (
          <input autoFocus value={name} onChange={e => setName(e.target.value)} onBlur={commitName}
            onKeyDown={e => { if (e.key === 'Enter') commitName(); if (e.key === 'Escape') { setName(node.name); setEditing(false) } }}
            style={{ ...inputStyle, minWidth: 180 }} />
        ) : (
          <span onDoubleClick={() => setEditing(true)} title={t('Double-click to rename')}
            style={{ fontWeight: depth === 0 ? 600 : 400, cursor: 'text' }}>
            {node.name}
          </span>
        )}
        {node.function_type && <span style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{node.function_type}</span>}

        {/* allocations */}
        {allocs.map(a => (
          <span key={a.id} title={t('Allocated at {{layer}}', { layer: a.layer })} style={{
            fontSize: fs.label, padding: '0 0.3rem', borderRadius: '3px',
            background: 'rgba(16,185,129,0.15)', color: 'var(--status-ok)', border: '1px solid rgba(16,185,129,0.4)',
          }}>
            → {a.element?.name || a.element_id.slice(0, 8)} <span style={{ opacity: 0.6 }}>[{a.layer}]</span>
            <button onClick={() => p.onUnallocate(node.id, a.layer)} title={t('Remove allocation')}
              style={{ background: 'none', border: 'none', color: 'var(--status-ok)', cursor: 'pointer', padding: '0 0 0 0.2rem', fontSize: fs.label }}>×</button>
          </span>
        ))}
        {allocs.length === 0 && <span style={{ fontSize: fs.label, color: 'var(--status-caution)' }}>{t('unallocated')}</span>}

        <span style={{ flex: 1 }} />
        <button style={smallBtn()} onClick={() => setEditing(true)}>{t('rename')}</button>
        <button style={smallBtn()} onClick={() => setPicking(v => !v)}>{t('Allocate to…')}</button>
        <button style={smallBtn()} onClick={() => setAddingPort(v => !v)}>{t('+ port')}</button>
        <button style={smallBtn('var(--interactive)')} onClick={() => p.onAddChild(node)}>{t('+ child')}</button>
        <button style={smallBtn('var(--status-alarm)')} onClick={() => p.onDelete(node.id)}>{t('delete')}</button>
      </div>

      {picking && (
        <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', margin: '0.15rem 0 0.25rem 1.2rem' }}>
          <select value={pickId} onChange={e => setPickId(e.target.value)} style={{ ...inputStyle, minWidth: 220 }}>
            <option value="">{t('Select element…')}</option>
            {p.elements.map((el: any) => (
              <option key={el.id} value={el.id}>{el.name} ({el.element_type}{el.subsystem_domain ? ` / ${el.subsystem_domain}` : ''})</option>
            ))}
          </select>
          <button style={smallBtn('var(--status-ok)')} disabled={!pickId}
            onClick={() => { p.onAllocate(node.id, pickId, node.layer); setPicking(false); setPickId('') }}>
            {t('Allocate at {{layer}}', { layer: node.layer })}
          </button>
          <button style={smallBtn()} onClick={() => setPicking(false)}>{t('cancel')}</button>
        </div>
      )}

      {addingPort && (
        <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', margin: '0.15rem 0 0.25rem 1.2rem' }}>
          <input value={portName} placeholder={t('port name')} onChange={e => setPortName(e.target.value)} style={inputStyle}
            onKeyDown={e => { if (e.key === 'Enter' && portName.trim()) { p.onAddPort(node.id, portName.trim(), portDir); setPortName(''); setAddingPort(false) } }} />
          <select value={portDir} onChange={e => setPortDir(e.target.value)} style={inputStyle}>
            <option value="in">in</option><option value="out">out</option><option value="inout">inout</option>
          </select>
          <button style={smallBtn('var(--status-ok)')} disabled={!portName.trim()}
            onClick={() => { p.onAddPort(node.id, portName.trim(), portDir); setPortName(''); setAddingPort(false) }}>{t('add')}</button>
          <button style={smallBtn()} onClick={() => setAddingPort(false)}>{t('cancel')}</button>
        </div>
      )}

      {ports.length > 0 && (
        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', margin: '0 0 0.2rem 1.2rem' }}>
          {ports.map(port => (
            <span key={port.id} style={{ fontSize: fs.label, padding: '0 0.3rem', borderRadius: '3px', background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
              {port.direction === 'in' ? '⇥' : port.direction === 'out' ? '⇤' : '⇆'} {port.name}
              {(port.exchange_item_ids || []).length > 0 && <span style={{ opacity: 0.7 }}> {t('({{n}} items)', { n: port.exchange_item_ids.length })}</span>}
              <button onClick={() => p.onDeletePort(port.id)} title={t('Delete port')}
                style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '0 0 0 0.2rem', fontSize: fs.label }}>×</button>
            </span>
          ))}
        </div>
      )}

      {!isCollapsed && kids.map(c => <FunctionRowView key={c.id} {...p} node={c} depth={depth + 1} />)}
    </div>
  )
}

function ExchangesSection({ exchanges, portsById, onCreate, onDelete }: {
  exchanges: FunctionalExchange[]
  portsById: Map<string, { port: FunctionPort; fn: FunctionNode }>
  onCreate: (b: { name: string; from_port_id: string; to_port_id: string }) => void
  onDelete: (id: string) => void
}) {
  const { t } = useTranslation()
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [name, setName] = useState('')
  const label = (pid: string) => {
    const e = portsById.get(pid)
    return e ? `${e.fn.name}.${e.port.name}` : pid.slice(0, 8)
  }
  const portOptions = [...portsById.values()]
  return (
    <div style={{ marginTop: '0.75rem', borderTop: '1px solid var(--border)', paddingTop: '0.4rem' }}>
      <div style={{ fontWeight: 600, fontSize: fs.label, marginBottom: '0.3rem' }}>{t('Functional exchanges ({{n}})', { n: exchanges.length })}</div>
      {exchanges.length === 0 && <div style={{ color: 'var(--text-secondary)', fontSize: fs.label }}>{t('None yet — add ports to functions, then connect them.')}</div>}
      {exchanges.map(x => (
        <div key={x.id} style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', fontSize: fs.label, padding: '0.1rem 0' }}>
          <span style={{ color: 'var(--cat-2)' }}>{x.name || t('(unnamed)')}</span>
          <span style={{ color: 'var(--text-secondary)' }}>{label(x.from_port_id)} → {label(x.to_port_id)}</span>
          {x.realized_by_interface_id && <span style={{ fontSize: fs.label, color: 'var(--status-ok)' }}>{t('realized')}</span>}
          <span style={{ flex: 1 }} />
          <button style={smallBtn('var(--status-alarm)')} onClick={() => onDelete(x.id)}>×</button>
        </div>
      ))}
      {portOptions.length >= 2 && (
        <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', marginTop: '0.3rem', flexWrap: 'wrap' }}>
          <input value={name} onChange={e => setName(e.target.value)} placeholder={t('exchange name')} style={inputStyle} />
          <select value={from} onChange={e => setFrom(e.target.value)} style={inputStyle}>
            <option value="">{t('from port…')}</option>
            {portOptions.map(({ port, fn }) => <option key={port.id} value={port.id}>{fn.name}.{port.name} ({port.direction})</option>)}
          </select>
          <span>→</span>
          <select value={to} onChange={e => setTo(e.target.value)} style={inputStyle}>
            <option value="">{t('to port…')}</option>
            {portOptions.map(({ port, fn }) => <option key={port.id} value={port.id}>{fn.name}.{port.name} ({port.direction})</option>)}
          </select>
          <button style={smallBtn('var(--status-ok)')} disabled={!from || !to || from === to}
            onClick={() => { onCreate({ name, from_port_id: from, to_port_id: to }); setName(''); setFrom(''); setTo('') }}>
            {t('+ exchange')}
          </button>
        </div>
      )}
    </div>
  )
}

export default FunctionTree
