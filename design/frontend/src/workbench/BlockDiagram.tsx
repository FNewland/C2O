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
import { useUIStore } from '../stores/uiStore'

const API = '/api'

const DOMAIN_COLORS: Record<string, string> = {
  power: '#f59e0b', aocs: '#06b6d4', ttc: '#ec4899', thermal: '#ef4444',
  structure: '#84cc16', propulsion: '#f97316', obc: '#8b5cf6', payload: '#10b981',
  ground: '#0ea5e9',
}

const TYPE_COLORS: Record<string, string> = {
  mission: '#3b82f6', segment: '#6366f1', system: '#8b5cf6',
  subsystem: '#06b6d4', component: '#10b981',
}

// ─── Custom Node ───

function ElementNode({ data }: NodeProps) {
  const { label, elementType, domain, mass_kg, power_w, in_scope, frozen, childCount, externalInterfaces, quantity, location } = data as any

  const borderColor = domain ? (DOMAIN_COLORS[domain] || '#6b7280') : (TYPE_COLORS[elementType] || '#6b7280')
  const bgAlpha = frozen ? '30' : '15'
  const isMulti = quantity > 1
  const borderStyle = in_scope === false ? 'dashed' : 'solid'
  const border = `2px ${borderStyle} ${in_scope === false ? '#6b728060' : borderColor}`

  // Stacked-box effect for multi-quantity elements (constellations, ground station networks)
  const box = (
    <div style={{
      padding: '0.5rem 0.75rem', borderRadius: '6px', minWidth: 130,
      background: `${borderColor}${bgAlpha}`,
      border,
      cursor: 'pointer',
      position: 'relative',
    }}>
      <Handle type="target" position={Position.Top} style={{ background: borderColor, width: 6, height: 6 }} />

      {/* Quantity badge (top-right) */}
      {isMulti && (
        <div style={{
          position: 'absolute', top: -8, right: -8,
          background: borderColor, color: 'white', fontWeight: 700,
          fontSize: '0.6rem', width: 20, height: 20, borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          border: '2px solid var(--bg-primary)',
        }}>
          ×{quantity}
        </div>
      )}

      {/* Type badge */}
      <div style={{ fontSize: '0.55rem', color: borderColor, fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.15rem' }}>
        {domain || elementType}
        {frozen && <span style={{ marginLeft: '0.3rem', color: '#f59e0b' }}>FROZEN</span>}
        {in_scope === false && <span style={{ marginLeft: '0.3rem', color: '#6b7280' }}>EXT</span>}
      </div>

      {/* Name */}
      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
        {label}
      </div>

      {/* Properties */}
      <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {mass_kg != null && <span>{mass_kg.toFixed(1)} kg{isMulti ? ` ea (${(mass_kg * quantity).toFixed(1)} total)` : ''}</span>}
        {power_w != null && <span>{power_w.toFixed(0)} W</span>}
        {childCount > 0 && <span style={{ color: borderColor }}>{childCount} children</span>}
      </div>

      {/* Location (for ground stations) */}
      {location && (
        <div style={{ fontSize: '0.5rem', color: '#06b6d4', marginTop: '0.1rem' }}>
          📍 {location}
        </div>
      )}

      {/* External interfaces indicator */}
      {externalInterfaces > 0 && (
        <div style={{
          fontSize: '0.5rem', color: '#ec4899', fontWeight: 600, marginTop: '0.15rem',
          display: 'flex', alignItems: 'center', gap: '0.2rem',
        }}>
          <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#ec4899', display: 'inline-block' }} />
          {externalInterfaces} ext iface{externalInterfaces > 1 ? 's' : ''}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} style={{ background: borderColor, width: 6, height: 6 }} />
    </div>
  )

  // For multi-quantity: render stacked shadow boxes behind the main box
  if (isMulti) {
    return (
      <div style={{ position: 'relative' }}>
        {/* Shadow layers (back to front) */}
        <div style={{
          position: 'absolute', top: 6, left: 6,
          width: '100%', height: '100%', borderRadius: '6px',
          background: `${borderColor}08`, border,
        }} />
        <div style={{
          position: 'absolute', top: 3, left: 3,
          width: '100%', height: '100%', borderRadius: '6px',
          background: `${borderColor}10`, border,
        }} />
        {box}
      </div>
    )
  }

  return box
}

/** External port node — represents a parent-level interface flowing into this block */
function ExternalPortNode({ data }: NodeProps) {
  const { label, interfaceType, peerName, direction } = data as any
  const IFACE_COLORS: Record<string, string> = {
    electrical: '#f59e0b', data: '#8b5cf6', rf: '#ec4899',
    mechanical: '#84cc16', thermal: '#ef4444',
  }
  const color = IFACE_COLORS[interfaceType] || '#6b7280'

  return (
    <div style={{
      padding: '0.3rem 0.6rem', borderRadius: '12px', minWidth: 100,
      background: `${color}15`, border: `2px dashed ${color}`,
      fontSize: '0.65rem', textAlign: 'center',
    }}>
      <Handle type="target" position={Position.Left} style={{ background: color, width: 6, height: 6 }} id="target" />
      <Handle type="source" position={Position.Right} style={{ background: color, width: 6, height: 6 }} id="source" />
      <div style={{ color, fontWeight: 700, textTransform: 'uppercase', fontSize: '0.5rem' }}>
        EXT {interfaceType}
      </div>
      <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{label}</div>
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.55rem' }}>↔ {peerName}</div>
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
          label: el.name,
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
      const nameOfEl = (id: string) => allElements.find((e: any) => e.id === id)?.name || 'External'

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
        style: { stroke: '#6b7280' },
      }))

    return { nodes, edges }
  }, [allElements, allInterfaces, focusElementId])

  // Use ReactFlow in uncontrolled mode — pass initialNodes/initialEdges via key reset
  // This avoids the infinite loop from useNodesState + useEffect sync
  const diagramKey = useMemo(() => {
    // Generate a stable key from element IDs + interface IDs so ReactFlow remounts on data change
    const elIds = initialNodes.map(n => n.id).sort().join(',')
    const ifIds = initialEdges.map(e => e.id).sort().join(',')
    return `${elIds}|${ifIds}`
  }, [initialNodes, initialEdges])

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
  const onConnect = useCallback((connection: Connection) => {
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
      const ifaceType = prompt('Interface type?\n\n1. electrical\n2. data\n3. rf\n4. mechanical\n5. thermal\n\nEnter type or number:', 'data')
      if (!ifaceType) return
      const typeMap: Record<string, string> = { '1': 'electrical', '2': 'data', '3': 'rf', '4': 'mechanical', '5': 'thermal' }
      const resolvedType = typeMap[ifaceType] || ifaceType
      const label = prompt('Interface label (optional):', '') || ''

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
  }, [studyId, allInterfaces, focusElementId, qc])

  if (!studyId) return null

  if (initialNodes.length === 0) {
    return (
      <div style={{
        height: '100%', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-secondary)', fontSize: '0.85rem', gap: '0.5rem',
      }}>
        <span style={{ fontSize: '1.5rem' }}>+</span>
        <span>No elements at this level yet.</span>
        <span style={{ fontSize: '0.72rem' }}>Use the Blocks panel below to add elements.</span>
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
      style={{ background: 'var(--bg-primary)' }}
    >
      <Background color="#1f2937" gap={20} />
      <Controls showInteractive={false} />
    </ReactFlow>
  )
}
