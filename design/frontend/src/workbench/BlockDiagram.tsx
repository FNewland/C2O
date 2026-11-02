/**
 * BlockDiagram — Interactive block diagram of elements at the current level.
 *
 * Reads elements from server via React Query.
 * Renders with @xyflow/react.
 * Double-click to drill into a child element.
 * Drag to reposition (persisted via PATCH).
 */
import { useMemo, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  type NodeTypes,
  type NodeProps,
  type Connection,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { displayElementName } from './BlocksPanel'
import { subsystemStyle } from '../theme/tokens'
import { useTheme } from '../theme/useTheme'
import { askChoice, askText } from '../components/ui/Dialog'

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
  const { label, interfaceType, peerName } = data as any

  return (
    <div className="c2o-node c2o-node--port">
      <Handle type="target" position={Position.Left} className="c2o-node__handle" id="target" />
      <Handle type="source" position={Position.Right} className="c2o-node__handle" id="source" />
      <div className="c2o-node__kind caps">EXT {interfaceType}</div>
      <div className="c-1 w-500">{label}</div>
      <div className="c-2 t-12">↔ {peerName}</div>
    </div>
  )
}

const nodeTypes: NodeTypes = { element: ElementNode, externalPort: ExternalPortNode }

// ─── Block Diagram ───

export function BlockDiagram() {
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const drillInto = useUIStore(s => s.drillInto)
  const qc = useQueryClient()
  const { t, i18n } = useTranslation()
  const theme = useTheme()

  // Fetch all elements for this study
  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId,
    structuralSharing: false, refetchInterval: 3000,
  })

  // Fetch interfaces for this study
  const { data: allInterfaces = [] } = useQuery({
    queryKey: ['interfaces', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/interfaces`).then(r => r.json()),
    enabled: !!studyId,
    structuralSharing: false, refetchInterval: 3000,
  })

  // Filter to children of the focus element (or roots if no focus)
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const children = allElements.filter((el: any) =>
      focusElementId ? el.parent_id === focusElementId : !el.parent_id
    )

    // Count grandchildren for each child
    const childCounts = new Map<string, number>()
    for (const el of allElements) {
      if (el.parent_id) {
        childCounts.set(el.parent_id, (childCounts.get(el.parent_id) || 0) + 1)
      }
    }

    // Count external interfaces per element (interfaces where one end is outside the visible set)
    const visibleIds = new Set(children.map((el: any) => el.id))
    const extIfaceCounts = new Map<string, number>()
    for (const iface of allInterfaces) {
      const fromVisible = visibleIds.has(iface.from_element_id)
      const toVisible = visibleIds.has(iface.to_element_id)
      // External = one end is visible, the other is not (or connects to out-of-scope ancestor)
      if (fromVisible && !toVisible) {
        extIfaceCounts.set(iface.from_element_id, (extIfaceCounts.get(iface.from_element_id) || 0) + 1)
      }
      if (toVisible && !fromVisible) {
        extIfaceCounts.set(iface.to_element_id, (extIfaceCounts.get(iface.to_element_id) || 0) + 1)
      }
    }
    // Also count interfaces from parent level that involve out-of-scope siblings
    const outOfScopeIds = new Set(children.filter((el: any) => el.in_scope === false).map((el: any) => el.id))
    for (const iface of allInterfaces) {
      if (visibleIds.has(iface.from_element_id) && outOfScopeIds.has(iface.to_element_id)) {
        extIfaceCounts.set(iface.from_element_id, (extIfaceCounts.get(iface.from_element_id) || 0) + 1)
      }
      if (visibleIds.has(iface.to_element_id) && outOfScopeIds.has(iface.from_element_id)) {
        extIfaceCounts.set(iface.to_element_id, (extIfaceCounts.get(iface.to_element_id) || 0) + 1)
      }
    }

    const nodes: Node[] = children.map((el: any, i: number) => {
      const col = i % 4
      const row = Math.floor(i / 4)
      return {
        id: el.id,
        type: 'element',
        position: {
          x: el.diagram_x ?? (80 + col * 200),
          y: el.diagram_y ?? (40 + row * 140),
        },
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

    // Add external port nodes — parent-level interfaces that connect to the focus element
    // These represent "what comes in from outside this block"
    if (focusElementId) {
      const parentInterfaces = allInterfaces.filter((iface: any) =>
        (iface.from_element_id === focusElementId || iface.to_element_id === focusElementId) &&
        !visibleIds.has(iface.from_element_id === focusElementId ? iface.to_element_id : iface.from_element_id)
      )
      const nameOfEl = (id: string) => { const n = allElements.find((e: any) => e.id === id)?.name; return n ? displayElementName(n, t) : t('External') }

      parentInterfaces.forEach((iface: any, i: number) => {
        const isIncoming = iface.to_element_id === focusElementId
        const peerId = isIncoming ? iface.from_element_id : iface.to_element_id
        const portId = `ext-port-${iface.id}`
        nodes.push({
          id: portId,
          type: 'externalPort',
          position: { x: isIncoming ? -120 : 600, y: 40 + i * 80 },
          data: {
            label: iface.diagram_label || iface.name || iface.interface_type,
            interfaceType: iface.interface_type,
            peerName: nameOfEl(peerId),
            direction: isIncoming ? 'in' : 'out',
          },
        })
      })
    }

    // Build edges from interfaces between visible elements
    const edges: Edge[] = allInterfaces
      .filter((iface: any) => visibleIds.has(iface.from_element_id) && visibleIds.has(iface.to_element_id))
      .map((iface: any) => ({
        id: iface.id,
        source: iface.from_element_id,
        target: iface.to_element_id,
        label: iface.diagram_label || iface.name,
        style: { stroke: 'var(--text-3)' },
      }))

    return { nodes, edges }
  }, [allElements, allInterfaces, focusElementId, t])

  // Use ReactFlow in uncontrolled mode — pass initialNodes/initialEdges via key reset
  // This avoids the infinite loop from useNodesState + useEffect sync
  const diagramKey = useMemo(() => {
    // Generate a stable key from element IDs + interface IDs so ReactFlow remounts on data change
    const elIds = initialNodes.map(n => n.id).sort().join(',')
    const ifIds = initialEdges.map(e => e.id).sort().join(',')
    return `${elIds}|${ifIds}|${i18n.language}`
  }, [initialNodes, initialEdges, i18n.language])

  // Double-click to drill into element
  const onNodeDoubleClick = useCallback((_event: any, node: Node) => {
    const childCount = (node.data as any).childCount || 0
    // Only drill in if element has children or is a container type
    const containerTypes = ['mission', 'segment', 'system', 'subsystem']
    if (childCount > 0 || containerTypes.includes((node.data as any).elementType)) {
      drillInto(node.id, (node.data as any).label)
    }
  }, [drillInto])

  // Persist position on drag end
  const onNodeDragStop = useCallback((_event: any, node: Node) => {
    const el = allElements.find((e: any) => e.id === node.id)
    fetch(`${API}/elements/${node.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        diagram_x: Math.round(node.position.x),
        diagram_y: Math.round(node.position.y),
        version: el?.version || 1,
      }),
    }).then(() => {
      // Refresh to get new version number
      qc.invalidateQueries({ queryKey: ['elements', studyId] })
    }).catch(() => {})
  }, [allElements, studyId, qc])

  // Handle new connections — element-to-element or external-port-to-element
  const onConnect = useCallback(async (connection: Connection) => {
    const { source, target } = connection
    if (!source || !target || !studyId) return

    const sourceIsExtPort = source.startsWith('ext-port-')
    const targetIsExtPort = target.startsWith('ext-port-')

    if (sourceIsExtPort && targetIsExtPort) return // port-to-port not meaningful

    if (sourceIsExtPort || targetIsExtPort) {
      // External port connection: link parent-level interface to a child element
      const extPortId = sourceIsExtPort ? source : target
      const childElementId = sourceIsExtPort ? target : source
      const parentIfaceId = extPortId.replace('ext-port-', '')

      // Look up the parent interface to get metadata
      const parentIface = allInterfaces.find((iface: any) => iface.id === parentIfaceId)
      if (!parentIface) return

      // Determine direction based on which side the ext port is on
      const direction = sourceIsExtPort ? 'in' : 'out'

      // The from/to for the new interface:
      // If the ext port is the source (incoming to this block), the flow is from the
      // parent interface's peer element to the child element
      const peerId = parentIface.from_element_id === focusElementId
        ? parentIface.to_element_id
        : parentIface.from_element_id
      const fromId = sourceIsExtPort ? peerId : childElementId
      const toId = sourceIsExtPort ? childElementId : peerId

      fetch(`${API}/interfaces/?study_id=${studyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: parentIface.name ? `${parentIface.name} (internal)` : `Internal ${parentIface.interface_type}`,
          interface_type: parentIface.interface_type,
          direction,
          from_element_id: fromId,
          to_element_id: toId,
          diagram_label: parentIface.diagram_label || parentIface.name || parentIface.interface_type,
        }),
      }).then(r => {
        if (r.ok) {
          qc.invalidateQueries({ queryKey: ['interfaces', studyId] })
        }
      }).catch(() => {})
    } else {
      // Element-to-element connection — ask for interface type
      const resolvedType = await askChoice(t('Interface type'), [
        { value: 'electrical', label: t('Electrical') },
        { value: 'data', label: t('Data') },
        { value: 'rf', label: t('RF') },
        { value: 'mechanical', label: t('Mechanical') },
        { value: 'thermal', label: t('Thermal') },
      ], 'data', { title: t('New interface') })
      if (!resolvedType) return
      const label = (await askText(t('Interface label (optional):'), '', { title: t('New interface') })) ?? ''

      fetch(`${API}/interfaces/?study_id=${studyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: label || `${resolvedType} interface`,
          interface_type: resolvedType,
          direction: 'bidirectional',
          from_element_id: source,
          to_element_id: target,
          diagram_label: label,
        }),
      }).then(r => {
        if (r.ok) {
          qc.invalidateQueries({ queryKey: ['interfaces', studyId] })
        }
      }).catch(() => {})
    }
  }, [studyId, allInterfaces, focusElementId, qc, t])

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
    <ReactFlow
      key={diagramKey}
      defaultNodes={initialNodes}
      defaultEdges={initialEdges}
      onConnect={onConnect}
      onNodeDoubleClick={onNodeDoubleClick}
      onNodeDragStop={onNodeDragStop}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.3 }}
      colorMode={theme}
    >
      <Background color="var(--line)" gap={20} />
      <Controls showInteractive={false} />
    </ReactFlow>
  )
}
