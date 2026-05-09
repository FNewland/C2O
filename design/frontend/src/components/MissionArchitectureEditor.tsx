/**
 * MissionArchitectureEditor — interactive mission architecture diagram.
 *
 * SYSTEM-V INTEGRATION: Every node is a DesignElement in the backend tree.
 * Adding a node = createElement(). Moving = updateElement().
 * Connecting = createInterface(). This ensures Phase 2 can read what
 * systems were defined at mission level.
 *
 * Node types map to element_types:
 *   satellite → segment (space)
 *   groundStation → segment (ground)
 *   processing → system
 *   user → logical
 *   etc.
 */
import { useMemo, useCallback, useEffect, useState } from 'react'
import {
  ReactFlow, useNodesState, useEdgesState, Handle, Position, Controls, Background, MiniMap,
  type Node, type Edge, type NodeTypes, type Connection, addEdge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useDesignStore } from '../stores/designStore'
import { useModelStore, type DesignElement } from '../stores/modelStore'

// ─── Node type → element mapping ───
const NODE_TYPE_TO_ELEMENT: Record<string, { element_type: string; segment: string; subsystem_domain?: string }> = {
  satellite: { element_type: 'segment', segment: 'space' },
  relaySat: { element_type: 'system', segment: 'space' },
  groundStation: { element_type: 'system', segment: 'ground' },
  processing: { element_type: 'system', segment: 'ground' },
  user: { element_type: 'logical', segment: 'operations' },
  sensor: { element_type: 'system', segment: 'space' },
  gnss: { element_type: 'logical', segment: 'space' },
  aircraft: { element_type: 'system', segment: 'space' },
  groundVehicle: { element_type: 'system', segment: 'ground' },
  ship: { element_type: 'system', segment: 'ground' },
  launcher: { element_type: 'logical', segment: 'space' },
}

// ─── Simple node components ───
function GenericNode({ data }: { data: { label: string; color: string } }) {
  return (
    <div style={{ padding: '8px 12px', border: `2px solid ${data.color}`, borderRadius: 8, background: `${data.color}15`, textAlign: 'center', minWidth: 100 }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontSize: '0.75rem', color: data.color, fontWeight: 600 }}>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

const nodeTypes: NodeTypes = {
  satellite: GenericNode, relaySat: GenericNode, groundStation: GenericNode,
  processing: GenericNode, user: GenericNode, sensor: GenericNode,
  gnss: GenericNode, aircraft: GenericNode, groundVehicle: GenericNode,
  ship: GenericNode, launcher: GenericNode,
}

// ─── Palette ───
const NODE_PALETTE = [
  { type: 'satellite', label: 'Satellite', color: '#3b82f6' },
  { type: 'relaySat', label: 'Relay Sat', color: '#14b8a6' },
  { type: 'groundStation', label: 'Ground Station', color: '#10b981' },
  { type: 'processing', label: 'Processing', color: '#06b6d4' },
  { type: 'user', label: 'User', color: '#f59e0b' },
  { type: 'sensor', label: 'Sensor', color: '#f97316' },
  { type: 'gnss', label: 'GNSS/External', color: '#8b5cf6' },
  { type: 'aircraft', label: 'Aircraft', color: '#ec4899' },
  { type: 'groundVehicle', label: 'Vehicle', color: '#84cc16' },
  { type: 'ship', label: 'Ship/Maritime', color: '#0ea5e9' },
  { type: 'launcher', label: 'Launcher', color: '#f43f5e' },
]

const PALETTE_COLORS: Record<string, string> = Object.fromEntries(NODE_PALETTE.map(n => [n.type, n.color]))

export function MissionArchitectureEditor() {
  const studyId = useDesignStore(s => s.studyId)
  const elements = useModelStore(s => s.elements)
  const interfaces = useModelStore(s => s.interfaces)
  const createElement = useModelStore(s => s.createElement)
  const updateElement = useModelStore(s => s.updateElement)
  const deleteElement = useModelStore(s => s.deleteElement)
  const createInterface = useModelStore(s => s.createInterface)
  const loadModel = useModelStore(s => s.loadStudyModel)
  const markStale = useDesignStore(s => s.markStale)

  // Load model on mount
  useEffect(() => {
    if (studyId && elements.size === 0) {
      loadModel(studyId)
    }
  }, [studyId])

  // Convert model elements to xyflow nodes
  const modelNodes = useMemo(() => {
    const nodes: Node[] = []
    for (const el of elements.values()) {
      // Only show mission-level elements (segments, top-level systems)
      if (el.element_type === 'subsystem' || el.element_type === 'component') continue
      if (el.element_type === 'mode') continue

      // Find matching palette type
      const paletteType = el.segment === 'space' && el.element_type === 'segment' ? 'satellite' :
                          el.segment === 'ground' && el.element_type === 'system' ? 'groundStation' :
                          el.segment === 'ground' && el.element_type === 'segment' ? 'groundStation' :
                          el.element_type === 'logical' ? 'user' : 'processing'
      const color = PALETTE_COLORS[paletteType] || '#6b7280'

      nodes.push({
        id: el.id,
        type: paletteType,
        position: { x: el.diagram_x ?? 100, y: el.diagram_y ?? 100 },
        data: { label: el.name, color },
      })
    }
    return nodes
  }, [elements])

  // Convert model interfaces to xyflow edges
  const modelEdges = useMemo(() => {
    const edges: Edge[] = []
    for (const iface of interfaces.values()) {
      // Only show interfaces between mission-level elements
      const from = elements.get(iface.from_element_id)
      const to = elements.get(iface.to_element_id)
      if (!from || !to) continue
      if (from.element_type === 'subsystem' || to.element_type === 'subsystem') continue

      edges.push({
        id: iface.id,
        source: iface.from_element_id,
        target: iface.to_element_id,
        label: iface.diagram_label || iface.name,
        style: { stroke: '#6b7280', strokeWidth: 2 },
        animated: iface.interface_type === 'rf',
      })
    }
    return edges
  }, [interfaces, elements])

  // Merge model nodes with default nodes (when no model yet)
  const defaultNodes: Node[] = modelNodes.length > 0 ? [] : [
    { id: 'sat1', type: 'satellite', position: { x: 300, y: 20 }, data: { label: 'Spacecraft', color: '#3b82f6' } },
    { id: 'gs1', type: 'groundStation', position: { x: 100, y: 200 }, data: { label: 'Ground Station', color: '#10b981' } },
    { id: 'mcc', type: 'processing', position: { x: 300, y: 200 }, data: { label: 'Mission Control', color: '#06b6d4' } },
    { id: 'proc', type: 'processing', position: { x: 500, y: 200 }, data: { label: 'Data Processing', color: '#06b6d4' } },
    { id: 'user1', type: 'user', position: { x: 500, y: 380 }, data: { label: 'End Users', color: '#f59e0b' } },
  ]

  const [nodes, setNodes, onNodesChange] = useNodesState([...modelNodes, ...defaultNodes])
  const [edges, setEdges, onEdgesChange] = useEdgesState(modelEdges)

  // Sync when model changes
  useEffect(() => {
    if (modelNodes.length > 0) {
      setNodes(modelNodes)
      setEdges(modelEdges)
    }
  }, [modelNodes, modelEdges])

  // ─── SYSTEM-V: Add node = create element ───
  const addNode = async (type: string, label: string) => {
    const customLabel = prompt(`Label for new ${label}:`, label) || label
    const mapping = NODE_TYPE_TO_ELEMENT[type] || { element_type: 'system', segment: 'space' }
    const color = PALETTE_COLORS[type] || '#6b7280'

    if (studyId) {
      // Create in backend element tree
      const id = await createElement(studyId, {
        name: customLabel,
        element_type: mapping.element_type,
        segment: mapping.segment,
        diagram_x: 200 + Math.random() * 200,
        diagram_y: 100 + Math.random() * 200,
      } as any)
      if (id) {
        // Node will appear via modelNodes memo on next render
        markStale('architecture')
      }
    } else {
      // No study yet — add to local state only
      const id = `node-${Date.now()}`
      setNodes(nds => [...nds, {
        id, type,
        position: { x: 200 + Math.random() * 200, y: 100 + Math.random() * 200 },
        data: { label: customLabel, color },
      }])
      markStale('architecture')
    }
  }

  // ─── SYSTEM-V: Connect nodes = create interface ───
  const onConnect = useCallback(async (connection: Connection) => {
    const label = prompt('Connection label (e.g., "S-band TM/TC", "Data Products"):') || ''
    const ifType = prompt('Interface type (rf/data/electrical/mechanical):') || 'data'

    if (studyId && connection.source && connection.target) {
      await createInterface(studyId, {
        name: label,
        interface_type: ifType,
        from_element_id: connection.source,
        to_element_id: connection.target,
        diagram_label: label,
      } as any)
    }
    setEdges(eds => addEdge({ ...connection, label }, eds))
    markStale('architecture')
  }, [studyId, createInterface, setEdges, markStale])

  // ─── SYSTEM-V: Move node = update element position ───
  const onNodeDragStop = useCallback((_: any, node: Node) => {
    if (elements.has(node.id)) {
      updateElement(node.id, { diagram_x: node.position.x, diagram_y: node.position.y } as any)
    }
  }, [elements, updateElement])

  // ─── SYSTEM-V: Delete = delete element ───
  const deleteSelected = async () => {
    const selectedNodeIds = nodes.filter(n => n.selected).map(n => n.id)
    for (const id of selectedNodeIds) {
      if (elements.has(id)) {
        await deleteElement(id)
      }
    }
    setNodes(nds => nds.filter(n => !n.selected))
    setEdges(eds => eds.filter(e => !e.selected))
    markStale('architecture')
  }

  // ─── Systems to define (derived from diagram nodes) ───
  const systemsToDefine = useMemo(() => {
    const typeToSystems: Record<string, string[]> = {
      satellite: ['EPS', 'AOCS', 'TTC', 'OBC', 'Thermal', 'Structure', 'Payload'],
      relaySat: ['TTC (relay)', 'Propulsion', 'AOCS'],
      groundStation: ['GS Antenna', 'Modem', 'Ground Network'],
      processing: ['Data Processing', 'Archive'],
      aircraft: ['Airborne Terminal', 'Data Link'],
      ship: ['Maritime Terminal', 'Stabilisation'],
      groundVehicle: ['Mobile Terminal', 'Power'],
      launcher: ['Launch I/F', 'Dispenser'],
    }
    const usedTypes = new Set(nodes.map(n => n.type || ''))
    return [...usedTypes].flatMap(t => typeToSystems[t] || [])
  }, [nodes])

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Toolbar */}
      <div style={{ padding: '0.4rem 0.75rem', borderBottom: '1px solid var(--border, #374151)', display: 'flex', gap: '0.3rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: '0.72rem', color: '#9ca3af', marginRight: '0.3rem' }}>Add:</span>
        {NODE_PALETTE.map(n => (
          <button key={n.type} onClick={() => addNode(n.type, n.label)}
            style={{ padding: '0.2rem 0.5rem', fontSize: '0.68rem', borderRadius: '3px', border: `1px solid ${n.color}40`, background: `${n.color}15`, color: n.color, cursor: 'pointer' }}>
            + {n.label}
          </button>
        ))}
        <span style={{ flex: 1 }} />
        <button onClick={deleteSelected} style={{ padding: '0.2rem 0.5rem', fontSize: '0.68rem', borderRadius: '3px', border: '1px solid #ef444440', background: '#ef444415', color: '#ef4444', cursor: 'pointer' }}>
          Delete Selected
        </button>
        <span style={{ fontSize: '0.65rem', color: '#6b7280' }}>
          {nodes.length} nodes, {edges.length} connections
        </span>
      </div>

      {/* Diagram */}
      <div style={{ flex: 1 }}>
        <ReactFlow
          nodes={nodes} edges={edges}
          onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
          onConnect={onConnect} onNodeDragStop={onNodeDragStop}
          nodeTypes={nodeTypes} fitView
          style={{ background: '#0a0e1a' }}
          defaultEdgeOptions={{ style: { strokeWidth: 2, stroke: '#6b7280' }, animated: true }}
        >
          <Controls style={{ button: { background: '#1f2937', color: '#d1d5db', border: '1px solid #374151' } } as any} />
          <Background color="#374151" gap={20} />
          <MiniMap nodeStrokeWidth={3} style={{ background: '#111827', border: '1px solid #374151' }} />
        </ReactFlow>
      </div>

      {/* Systems to define */}
      {systemsToDefine.length > 0 && (
        <div style={{ padding: '0.4rem 0.75rem', borderTop: '1px solid var(--border, #374151)', fontSize: '0.7rem' }}>
          <span style={{ color: '#9ca3af', fontWeight: 600, marginRight: '0.5rem' }}>Systems to define at Phase 2:</span>
          {systemsToDefine.map((sys, i) => (
            <span key={i} style={{ display: 'inline-block', padding: '0.1rem 0.4rem', margin: '0.1rem', borderRadius: '3px', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', color: '#93c5fd', fontSize: '0.65rem' }}>
              {sys}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
