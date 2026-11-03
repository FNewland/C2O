/**
 * BlockDiagram — Interactive block diagram of elements at the current level.
 *
 * Reads elements and interfaces from the server via React Query, renders
 * with @xyflow/react. Double-click drills into a child element; dragging a
 * block persists its position (PATCH).
 *
 * Links are drawn per canonical interface type: the type's categorical
 * colour PLUS its glyph and a short label on the edge, so the type never
 * rides on colour alone. Suggested links (rule proposals) are dashed and
 * labelled; rejected links are not drawn. A key in the corner is the legend
 * and the type filter. Clicking a link opens a popover to accept, edit or
 * reject it. Several links between one pair fan out side by side.
 */
import { useMemo, useCallback, useEffect, useRef, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  BaseEdge,
  EdgeLabelRenderer,
  type Node,
  type Edge,
  type EdgeProps,
  type EdgeTypes,
  type NodeTypes,
  type NodeProps,
  type Connection,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { RecordDecision } from '../logbook'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { displayElementName } from './BlocksPanel'
import { subsystemStyle } from '../theme/tokens'
import { useTheme } from '../theme/useTheme'
import { askChoice, askText } from '../components/ui/Dialog'
import { Button } from '../components/ui'
import { INTERFACE_TYPES, TYPE_META, pickLang, type DesignInterface, type InterfaceType } from '../types/interfaces'
import { InterfaceGlyph } from './InterfaceGlyph'
import { createInterface, patchInterface, useInterfaces, useInvalidateLinks } from './interfaceApi'
import { LinkEditor, LinkStatusChip, TypeLabel, linkDecision, originText, propsSummary, type EndpointOption } from './linkParts'

const API = '/api'

// Subsystem identity: categorical palette + letter badge (theme/tokens.ts).
// Non-subsystem blocks (mission, segment, system) stay neutral.

// ─── Custom Node ───

function ElementNode({ data }: NodeProps) {
  const { t } = useTranslation()
  const { label, elementType, domain, mass_kg, power_w, in_scope, frozen, childCount, externalInterfaces, quantity, location } = data as any

  const ss = domain ? subsystemStyle(domain) : null
  const accent = ss ? ss.color : 'var(--line-strong)'
  const isMulti = quantity > 1
  const outOfScope = in_scope === false
  const typeLabel = domain ? domain.toUpperCase() : t(TYPE_LABEL[elementType] ?? elementType)

  const cls = ['c2o-node', frozen && 'is-frozen', outOfScope && 'is-external'].filter(Boolean).join(' ')
  const box = (
    <div className={cls} style={{ borderLeftColor: accent }}>
      <Handle type="target" position={Position.Top} className="c2o-node__handle" />

      {isMulti && <div className="c2o-node__qty">×{quantity}</div>}

      {/* Identity row: badge + type, then state words (text, not colour) */}
      <div className="c2o-node__kind">
        {ss?.badge && <span className="c2o-ss-badge" style={{ background: ss.color }} aria-hidden="true">{ss.badge}</span>}
        <span className="w-500">{typeLabel}</span>
        {frozen && <span className="w-600 c-2">{t('FROZEN')}</span>}
        {outOfScope && <span className="w-600 c-2">{t('EXT')}</span>}
      </div>

      <div className="c2o-node__name">{label}</div>

      <div className="c2o-node__vals">
        {mass_kg != null && <span>{isMulti ? t('{{mass}} kg ea ({{total}} total)', { mass: mass_kg.toFixed(1), total: (mass_kg * quantity).toFixed(1) }) : `${mass_kg.toFixed(1)} kg`}</span>}
        {power_w != null && <span>{power_w.toFixed(0)} W</span>}
        {childCount > 0 && <span className="c2o-node__sans">{t('{{count}} children', { count: childCount })}</span>}
      </div>

      {location && <div className="c2o-node__meta">{location}</div>}

      {externalInterfaces > 0 && (
        <div className="c2o-node__meta">
          {t('{{count}} ext ifaces', { count: externalInterfaces, defaultValue_one: '{{count}} ext iface' })}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="c2o-node__handle" />
    </div>
  )

  if (isMulti) {
    return (
      <div className="rel">
        <div className={`c2o-node__layer${outOfScope ? ' is-external' : ''}`} style={{ top: 6, left: 6 }} />
        <div className={`c2o-node__layer${outOfScope ? ' is-external' : ''}`} style={{ top: 3, left: 3 }} />
        {box}
      </div>
    )
  }

  return box
}

// English text is the i18n key: element types for non-subsystem blocks (ECSS product tree).
const TYPE_LABEL: Record<string, string> = {
  mission: 'Mission', segment: 'Segment', system: 'System / element', subsystem: 'Subsystem', component: 'Equipment',
}

/** External port node — represents a parent-level interface flowing into this block */
function ExternalPortNode({ data }: NodeProps) {
  const { t } = useTranslation()
  const { label, interfaceType, peerName, suggested } = data as any
  return (
    <div className={`c2o-node c2o-node--port${suggested ? ' is-suggested' : ''}`}>
      <Handle type="target" position={Position.Left} className="c2o-node__handle" id="target" />
      <Handle type="source" position={Position.Right} className="c2o-node__handle" id="source" />
      <div className="c2o-node__kind"><TypeLabel type={interfaceType} short /><span className="c-3">{t('external')}</span></div>
      <div className="c-1 w-500">{label}</div>
      <div className="c-2 t-12">↔ {peerName}</div>
    </div>
  )
}

const nodeTypes: NodeTypes = { element: ElementNode, externalPort: ExternalPortNode }

// ─── Typed link edge ───

interface LinkEdgeData extends Record<string, unknown> {
  iface: DesignInterface
  offset: number
  selected: boolean
  onPick: (id: string) => void
}

/** Straight link, bowed sideways by `offset` px so parallel links between one pair stay apart. */
function LinkEdge({ id, sourceX, sourceY, targetX, targetY, data }: EdgeProps) {
  const { t } = useTranslation()
  const d = data as LinkEdgeData
  const iface = d.iface
  const meta = TYPE_META[iface.type]
  const dx = targetX - sourceX, dy = targetY - sourceY
  const len = Math.hypot(dx, dy) || 1
  const nx = -dy / len, ny = dx / len
  const cx = (sourceX + targetX) / 2 + nx * d.offset * 2
  const cy = (sourceY + targetY) / 2 + ny * d.offset * 2
  const path = `M${sourceX},${sourceY} Q${cx},${cy} ${targetX},${targetY}`
  // label at the curve's midpoint (t = 0.5 of the quadratic)
  const lx = 0.25 * sourceX + 0.5 * cx + 0.25 * targetX
  const ly = 0.25 * sourceY + 0.5 * cy + 0.25 * targetY
  const suggested = iface.status === 'suggested'
  const word = t(meta.short)
  return (
    <>
      <BaseEdge id={id} path={path} interactionWidth={14}
        style={{
          stroke: meta.color, strokeWidth: d.selected ? 2.75 : 1.5,
          strokeDasharray: suggested ? '6 4' : undefined, opacity: suggested && !d.selected ? 0.9 : 1,
        }} />
      <EdgeLabelRenderer>
        <button type="button"
          className={`c2o-edge-label nodrag nopan${suggested ? ' is-suggested' : ''}${d.selected ? ' is-selected' : ''}`}
          style={{ transform: `translate(-50%, -50%) translate(${lx}px, ${ly}px)` }}
          aria-label={suggested
            ? t('Suggested {{type}} link. Open to accept, edit or reject.', { type: t(meta.label) })
            : t('{{type}} link. Open to edit.', { type: t(meta.label) })}
          onClick={e => { e.stopPropagation(); d.onPick(iface.id) }}>
          <InterfaceGlyph type={iface.type} size={11} />
          <span className="c2o-edge-label__w" aria-hidden="true">{word}{suggested ? ` · ${t('suggested')}` : ''}</span>
        </button>
      </EdgeLabelRenderer>
    </>
  )
}

const edgeTypes: EdgeTypes = { link: LinkEdge }

// ─── Legend + type filter ───

const FILTER_KEY = 'scdf.linkFilter'
function readFilter(): { hidden: InterfaceType[]; suggested: boolean; open: boolean } {
  try {
    const v = JSON.parse(localStorage.getItem(FILTER_KEY) || 'null')
    if (v && Array.isArray(v.hidden)) return { hidden: v.hidden, suggested: v.suggested !== false, open: !!v.open }
  } catch { /* storage blocked */ }
  return { hidden: [], suggested: true, open: false }
}

function DiagramKey({ counts, hidden, toggle, showSuggested, setShowSuggested, open, setOpen }: {
  counts: Record<string, number>; hidden: Set<InterfaceType>; toggle: (t: InterfaceType) => void
  showSuggested: boolean; setShowSuggested: (v: boolean) => void; open: boolean; setOpen: (v: boolean) => void
}) {
  const { t } = useTranslation()
  const present = INTERFACE_TYPES.filter(k => counts[k])
  const shownTypes = present.filter(k => !hidden.has(k))
  return (
    <div className="c2o-dkey" role="group" aria-label={t('Link key and filter')}>
      <div className="c2o-dkey__bar">
        <b>{t('Links')}</b>
        {!open && shownTypes.slice(0, 6).map(k => (
          <span key={k} className="c2o-dkey__line"><InterfaceGlyph type={k} size={11} />{t(TYPE_META[k].short)}</span>
        ))}
        {!open && hidden.size > 0 && <span className="c-3">{t('{{n}} types hidden', { n: present.length - shownTypes.length })}</span>}
        <Button size="sm" variant="quiet" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? t('Close key') : t('Filter')}
        </Button>
      </div>
      {open && (
        <>
          <div className="c2o-dkey__list">
            {INTERFACE_TYPES.map(k => (
              <label key={k} className={`c2o-dkey__item${hidden.has(k) ? ' is-off' : ''}`}>
                <input type="checkbox" checked={!hidden.has(k)} onChange={() => toggle(k)} />
                <svg width="22" height="8" aria-hidden="true"><line x1="1" y1="4" x2="21" y2="4" stroke={TYPE_META[k].color} strokeWidth="2" /></svg>
                <InterfaceGlyph type={k} size={11} />
                <span>{t(TYPE_META[k].label)}</span>
                <span className="c2o-dkey__n">{counts[k] ?? 0}</span>
              </label>
            ))}
          </div>
          <div className="c2o-dkey__styles">
            <span className="c2o-dkey__line"><svg width="26" height="8" aria-hidden="true"><line x1="1" y1="4" x2="25" y2="4" stroke="currentColor" strokeWidth="1.5" /></svg>{t('accepted')}</span>
            <label className="c2o-dkey__line cursor-p">
              <input type="checkbox" checked={showSuggested} onChange={e => setShowSuggested(e.target.checked)} />
              <svg width="26" height="8" aria-hidden="true"><line x1="1" y1="4" x2="25" y2="4" stroke="currentColor" strokeWidth="1.5" strokeDasharray="6 4" /></svg>
              {t('suggested, to review')}
            </label>
            <span>{t('Rejected links are not drawn.')}</span>
          </div>
        </>
      )}
    </div>
  )
}

// ─── Edge popover ───

function EdgePopover({ iface, x, y, nameOf, endpoints, onClose, studyId }: {
  iface: DesignInterface; x: number; y: number; nameOf: (id: string) => string; endpoints: EndpointOption[]
  onClose: () => void; studyId: string
}) {
  const { t, i18n } = useTranslation()
  const invalidate = useInvalidateLinks(studyId)
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { ref.current?.querySelector<HTMLElement>('button, select, input')?.focus() }, [editing])
  const act = async (patch: Parameters<typeof patchInterface>[2]) => {
    setBusy(true); setErr(null)
    try { await patchInterface(studyId, iface.id, { version: iface.version, ...patch }); invalidate(); onClose() }
    catch (e) { setErr(String((e as Error).message || e)) } finally { setBusy(false) }
  }
  const why = pickLang(iface.rationale, i18n.language)
  const sum = propsSummary(iface, t)
  return (
    <div ref={ref} className="c2o-epop nodrag nopan" role="dialog" aria-label={t('Link {{from}} to {{to}}', { from: nameOf(iface.from_element_id), to: nameOf(iface.to_element_id) })}
      style={{ left: x, top: y }}
      onKeyDown={e => { if (e.key === 'Escape') { e.stopPropagation(); onClose() } }}>
      <div className="c2o-epop__head">
        <TypeLabel type={iface.type} />
        <LinkStatusChip status={iface.status} />
        <Button size="sm" variant="icon" aria-label={t('Close')} onClick={onClose}>×</Button>
      </div>
      <p className="m-0 mb-1 t-13"><span className="w-600">{nameOf(iface.from_element_id)}</span> <span className="c-3" aria-hidden="true">{iface.direction === 'unidirectional' || iface.direction === 'out' ? '→' : '↔'}</span> <span className="w-600">{nameOf(iface.to_element_id)}</span>
        {sum && <span className="mono t-12 c-2"> · {sum}</span>}</p>
      {why && <p className="c2o-epop__why">{why}</p>}
      <p className="c2o-epop__ref">{[iface.standard_ref, originText(iface, t)].filter(Boolean).join(' · ')}</p>
      {err && <p className="t-12 c-alarm m-0 mb-2" role="alert">{t('The server refused the change: {{message}}', { message: err })}</p>}
      {editing
        ? <LinkEditor compact iface={iface} endpoints={endpoints} saving={busy} onCancel={() => setEditing(false)} onSave={p => act(p)} />
        : (
          <div className="c2o-epop__acts">
            {iface.status === 'suggested' && <Button size="sm" variant="primary" busy={busy} onClick={() => act({ status: 'accepted' })}>{t('Accept')}</Button>}
            <Button size="sm" onClick={() => setEditing(true)}>{t('Edit')}</Button>
            <Button size="sm" busy={busy} onClick={() => act({ status: 'rejected' })}>{t('Reject')}</Button>
            <RecordDecision decision="D-2.4-INTERFACES" capture="blocks:link" label={t('Record')}
              prefill={() => linkDecision(iface, nameOf, t, i18n.language, iface.status === 'accepted' ? 'accept' : iface.status === 'rejected' ? 'reject' : undefined)} />
          </div>
        )}
    </div>
  )
}

// ─── Block Diagram ───

export function BlockDiagram() {
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const drillInto = useUIStore(s => s.drillInto)
  const qc = useQueryClient()
  const { t, i18n } = useTranslation()
  const theme = useTheme()
  const invalidate = useInvalidateLinks(studyId)

  // Fetch all elements for this study
  const { data: allElements = [] } = useQuery<any[]>({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId,
    structuralSharing: false, refetchInterval: 3000,
  })
  const { interfaces: allInterfaces } = useInterfaces(studyId)

  // Legend / filter (a per-viewer convenience, kept in this browser)
  const [filter, setFilter] = useState(readFilter)
  useEffect(() => { try { localStorage.setItem(FILTER_KEY, JSON.stringify(filter)) } catch { /* storage blocked */ } }, [filter])
  const hidden = useMemo(() => new Set(filter.hidden), [filter.hidden])
  const [picked, setPicked] = useState<{ id: string; x: number; y: number } | null>(null)
  const wrapRef = useRef<HTMLDivElement>(null)
  useEffect(() => { setPicked(null) }, [focusElementId])

  const children = useMemo(() => allElements.filter((el: any) =>
    focusElementId ? el.parent_id === focusElementId : !el.parent_id
  ), [allElements, focusElementId])
  const visibleIds = useMemo(() => new Set(children.map((el: any) => el.id)), [children])
  const live = useMemo(() => allInterfaces.filter(i => i.status !== 'rejected'), [allInterfaces])

  const nameOf = useCallback((id: string) => {
    const n = allElements.find((e: any) => e.id === id)?.name
    return n ? displayElementName(n, t) : t('External')
  }, [allElements, t])
  const endpoints: EndpointOption[] = useMemo(() => children.map((el: any) => ({ id: el.id, name: displayElementName(el.name, t) })), [children, t])

  // Nodes (uncontrolled; remounted when the element set changes)
  const initialNodes = useMemo(() => {
    const childCounts = new Map<string, number>()
    for (const el of allElements) {
      if (el.parent_id) childCounts.set(el.parent_id, (childCounts.get(el.parent_id) || 0) + 1)
    }
    // External interfaces per element: one end visible, the other not (or out of scope)
    const extIfaceCounts = new Map<string, number>()
    const bump = (id: string) => extIfaceCounts.set(id, (extIfaceCounts.get(id) || 0) + 1)
    const outOfScopeIds = new Set(children.filter((el: any) => el.in_scope === false).map((el: any) => el.id))
    for (const iface of live) {
      const fromVisible = visibleIds.has(iface.from_element_id)
      const toVisible = visibleIds.has(iface.to_element_id)
      if (fromVisible && !toVisible) bump(iface.from_element_id)
      if (toVisible && !fromVisible) bump(iface.to_element_id)
      if (fromVisible && outOfScopeIds.has(iface.to_element_id)) bump(iface.from_element_id)
      if (toVisible && outOfScopeIds.has(iface.from_element_id)) bump(iface.to_element_id)
    }

    const nodes: Node[] = children.map((el: any, i: number) => {
      const col = i % 4
      const row = Math.floor(i / 4)
      return {
        id: el.id,
        type: 'element',
        position: { x: el.diagram_x ?? (80 + col * 220), y: el.diagram_y ?? (40 + row * 170) },
        data: {
          label: displayElementName(el.name, t),
          elementType: el.element_type,
          domain: el.subsystem_domain,
          mass_kg: el.mass_kg,
          power_w: el.power_avg_w,
          in_scope: el.in_scope,
          frozen: el.frozen,
          quantity: el.quantity || 1,
          location: el.performance?.location || null,
          childCount: childCounts.get(el.id) || 0,
          externalInterfaces: extIfaceCounts.get(el.id) || 0,
        },
      }
    })

    // External ports: parent-level interfaces that connect to the focus element
    if (focusElementId) {
      const parentInterfaces = live.filter(iface =>
        (iface.from_element_id === focusElementId || iface.to_element_id === focusElementId) &&
        !visibleIds.has(iface.from_element_id === focusElementId ? iface.to_element_id : iface.from_element_id)
      )
      parentInterfaces.forEach((iface, i) => {
        const isIncoming = iface.to_element_id === focusElementId
        const peerId = isIncoming ? iface.from_element_id : iface.to_element_id
        nodes.push({
          id: `ext-port-${iface.id}`,
          type: 'externalPort',
          position: { x: isIncoming ? -160 : 940, y: 40 + i * 84 },
          data: {
            label: iface.diagram_label || iface.name || t(TYPE_META[iface.type].label),
            interfaceType: iface.type,
            peerName: nameOf(peerId),
            direction: isIncoming ? 'in' : 'out',
            suggested: iface.status === 'suggested',
          },
        })
      })
    }
    return nodes
  }, [allElements, children, live, visibleIds, focusElementId, nameOf, t])

  // The edge label sits in flow coordinates; the popover opens beside the pointer, in screen space.
  const lastPointer = useRef({ x: 16, y: 16 })
  const onPick = useCallback((id: string) => {
    setPicked(p => (p?.id === id ? null : { id, x: lastPointer.current.x, y: lastPointer.current.y }))
  }, [])

  // Edges (controlled): visible pairs only, filtered by type and suggested toggle, fanned out per pair
  const { edges, counts } = useMemo(() => {
    const here = live.filter(i => visibleIds.has(i.from_element_id) && visibleIds.has(i.to_element_id))
    const counts: Record<string, number> = {}
    for (const i of here) counts[i.type] = (counts[i.type] || 0) + 1
    const shown = here.filter(i => !hidden.has(i.type) && (filter.suggested || i.status !== 'suggested'))
    const pairKey = (i: DesignInterface) => [i.from_element_id, i.to_element_id].sort().join('|')
    const groups = new Map<string, DesignInterface[]>()
    for (const i of shown) { const k = pairKey(i); groups.set(k, [...(groups.get(k) ?? []), i]) }
    const edges: Edge[] = []
    for (const list of groups.values()) {
      list.sort((a, b) => INTERFACE_TYPES.indexOf(a.type) - INTERFACE_TYPES.indexOf(b.type))
      list.forEach((iface, k) => {
        // keep the bow direction consistent for both from/to orders
        const flip = iface.from_element_id > iface.to_element_id ? -1 : 1
        edges.push({
          id: iface.id, type: 'link', source: iface.from_element_id, target: iface.to_element_id,
          data: { iface, offset: (k - (list.length - 1) / 2) * 26 * flip, selected: picked?.id === iface.id, onPick } satisfies LinkEdgeData,
        })
      })
    }
    return { edges, counts }
  }, [live, visibleIds, hidden, filter.suggested, picked, onPick])

  const diagramKey = useMemo(() => `${initialNodes.map(n => n.id).sort().join(',')}|${i18n.language}`, [initialNodes, i18n.language])

  const onNodeDoubleClick = useCallback((_event: any, node: Node) => {
    const childCount = (node.data as any).childCount || 0
    const containerTypes = ['mission', 'segment', 'system', 'subsystem']
    if (childCount > 0 || containerTypes.includes((node.data as any).elementType)) {
      drillInto(node.id, (node.data as any).label)
    }
  }, [drillInto])

  const onNodeDragStop = useCallback((_event: any, node: Node) => {
    const el = allElements.find((e: any) => e.id === node.id)
    fetch(`${API}/elements/${node.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ diagram_x: Math.round(node.position.x), diagram_y: Math.round(node.position.y), version: el?.version || 1 }),
    }).then(() => qc.invalidateQueries({ queryKey: ['elements', studyId] })).catch(() => {})
  }, [allElements, studyId, qc])

  // New connections — element-to-element or external-port-to-element
  const onConnect = useCallback(async (connection: Connection) => {
    const { source, target } = connection
    if (!source || !target || !studyId) return
    const sourceIsExtPort = source.startsWith('ext-port-')
    const targetIsExtPort = target.startsWith('ext-port-')
    if (sourceIsExtPort && targetIsExtPort) return

    try {
      if (sourceIsExtPort || targetIsExtPort) {
        // Refine a parent-level interface one level down: same type, from the peer to the child
        const extPortId = sourceIsExtPort ? source : target
        const childElementId = sourceIsExtPort ? target : source
        const parentIface = allInterfaces.find(i => i.id === extPortId.replace('ext-port-', ''))
        if (!parentIface) return
        const peerId = parentIface.from_element_id === focusElementId ? parentIface.to_element_id : parentIface.from_element_id
        await createInterface(studyId, {
          type: parentIface.type,
          subtype: parentIface.subtype,
          name: parentIface.name ? `${parentIface.name} (internal)` : `Internal ${parentIface.type}`,
          direction: parentIface.direction === 'unidirectional' ? 'unidirectional' : 'bidirectional',
          from_element_id: sourceIsExtPort ? peerId : childElementId,
          to_element_id: sourceIsExtPort ? childElementId : peerId,
          diagram_label: parentIface.diagram_label || parentIface.name || undefined,
          properties: parentIface.properties,
        })
      } else {
        const resolvedType = await askChoice(t('Interface type'),
          INTERFACE_TYPES.map(k => ({ value: k, label: t(TYPE_META[k].label) })), 'data', { title: t('New interface') })
        if (!resolvedType) return
        const label = (await askText(t('Interface label (optional):'), '', { title: t('New interface') })) ?? ''
        await createInterface(studyId, {
          type: resolvedType as InterfaceType,
          name: label || `${nameOf(source)} → ${nameOf(target)}`,
          from_element_id: source, to_element_id: target, diagram_label: label || undefined,
        })
      }
      invalidate()
    } catch { /* the Interfaces panel shows server errors; the diagram stays as it was */ }
  }, [studyId, allInterfaces, focusElementId, invalidate, nameOf, t])

  const pickedIface = picked ? allInterfaces.find(i => i.id === picked.id) : null

  if (!studyId) return null

  if (initialNodes.length === 0) {
    return (
      <div className="c2o-diagram-empty">
        <span className="t-20">+</span>
        <span>{t('No elements at this level yet.')}</span>
        <span className="t-12">{t('Use the Blocks panel below to add elements.')}</span>
      </div>
    )
  }

  return (
    <div ref={wrapRef} className="rel w-full" style={{ height: '100%' }}
      onPointerDownCapture={e => {
        const r = wrapRef.current?.getBoundingClientRect()
        if (r) lastPointer.current = { x: Math.min(Math.max(8, e.clientX - r.left + 8), Math.max(8, r.width - 448)), y: Math.min(e.clientY - r.top + 8, Math.max(8, r.height - 260)) }
      }}>
      <ReactFlow
        proOptions={{ hideAttribution: true }}
        key={diagramKey}
        defaultNodes={initialNodes}
        edges={edges}
        onConnect={onConnect}
        onNodeDoubleClick={onNodeDoubleClick}
        onNodeDragStop={onNodeDragStop}
        onPaneClick={() => setPicked(null)}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        colorMode={theme}
      >
        <Background color="var(--line)" gap={20} />
        <Controls showInteractive={false} position="bottom-right" />
      </ReactFlow>
      {Object.keys(counts).length > 0 && (
        <DiagramKey counts={counts} hidden={hidden}
          toggle={k => setFilter(f => ({ ...f, hidden: f.hidden.includes(k) ? f.hidden.filter(x => x !== k) : [...f.hidden, k] }))}
          showSuggested={filter.suggested} setShowSuggested={v => setFilter(f => ({ ...f, suggested: v }))}
          open={filter.open} setOpen={v => setFilter(f => ({ ...f, open: v }))} />
      )}
      {pickedIface && picked && (
        <EdgePopover key={pickedIface.id} iface={pickedIface} x={picked.x} y={picked.y} nameOf={nameOf} endpoints={endpoints}
          studyId={studyId} onClose={() => setPicked(null)} />
      )}
    </div>
  )
}
