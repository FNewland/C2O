/**
 * ModelBlockDiagram — renders the design element tree as an interactive block diagram.
 *
 * Reads from modelStore. Adding/moving/connecting nodes mutates the model via API.
 * This is the PRIMARY design editor — the diagram IS the data model.
 */
import { useMemo, useCallback, useEffect } from 'react'
import {
  ReactFlow, useNodesState, useEdgesState, Handle, Position, Controls, Background, MiniMap,
  type Node, type Edge, type NodeTypes, type Connection, addEdge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useModelStore, type DesignElement } from '../stores/modelStore'
import { useDesignStore } from '../stores/designStore'

// Color by element type
const TYPE_COLORS: Record<string, string> = {
  mission: '#8b5cf6', segment: '#3b82f6', system: '#06b6d4',
  subsystem: '#10b981', component: '#f59e0b', software: '#ec4899',
  mode: '#f97316', logical: '#6b7280',
}

// Color by subsystem domain
const DOMAIN_COLORS: Record<string, string> = {
  power: '#f59e0b', aocs: '#06b6d4', ttc: '#ec4899', thermal: '#ef4444',
  structure: '#84cc16', propulsion: '#f97316', obc: '#8b5cf6', payload: '#10b981',
  ground: '#0ea5e9',
}

function ElementNode({ data }: { data: { element: DesignElement } }) {
  const el = data.element
  const color = DOMAIN_COLORS[el.subsystem_domain || ''] || TYPE_COLORS[el.element_type] || '#6b7280'

  return (
    <div style={{
      padding: '6px 10px', border: `2px solid ${color}`, borderRadius: 6,
      background: `${color}10`, textAlign: 'center', minWidth: 100, maxWidth: 160,
    }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontSize: '0.72rem', color, fontWeight: 700 }}>{el.name}</div>
      {el.mass_kg !== null && (
        <div style={{ fontSize: '0.58rem', color: '#9ca3af' }}>
          {(el.mass_kg * el.quantity).toFixed(2)} kg
          {el.quantity > 1 && ` (×${el.quantity})`}
        </div>
      )}
      {el.power_avg_w !== null && (
        <div style={{ fontSize: '0.58rem', color: '#9ca3af' }}>{el.power_avg_w} W</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

function ContainerNode({ data }: { data: { element: DesignElement } }) {
  const el = data.element
  const color = TYPE_COLORS[el.element_type] || '#374151'
  return (
    <div style={{
      padding: '8px', border: `2px dashed ${color}`, borderRadius: 8,
      background: `${color}08`, minWidth: 400, minHeight: 200,
    }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontSize: '0.8rem', color, fontWeight: 700, marginBottom: '0.3rem' }}>
        {el.name}
      </div>
      <div style={{ fontSize: '0.6rem', color: '#6b7280' }}>{el.description || el.element_type}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

const nodeTypes: NodeTypes = { element: ElementNode, container: ContainerNode }

interface Props {
  studyId: string | null
  segment?: string  // filter by segment
  level?: string    // filter by element_type
}

export function ModelBlockDiagram({ studyId, segment, level }: Props) {
  const elements = useModelStore(s => s.elements)
  const interfaces = useModelStore(s => s.interfaces)
  const loadModel = useModelStore(s => s.loadStudyModel)
  const updateElement = useModelStore(s => s.updateElement)
  const createInterface = useModelStore(s => s.createInterface)

  // Load model on mount if studyId available
  useEffect(() => {
    if (studyId && elements.size === 0) {
      loadModel(studyId)
    }
  }, [studyId])

  // Convert elements to xyflow nodes
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node[] = []
    const edges: Edge[] = []

    let col = 0
    let row = 0

    for (const el of elements.values()) {
      // Filter
      if (segment && el.segment !== segment) continue
      if (level && el.element_type !== level) continue

      const color = DOMAIN_COLORS[el.subsystem_domain || ''] || TYPE_COLORS[el.element_type] || '#6b7280'

      const isContainer = el.element_type === 'segment' || el.element_type === 'system'
      nodes.push({
        id: el.id,
        type: isContainer ? 'container' : 'element',
        position: { x: el.diagram_x ?? (col * 180 + 50), y: el.diagram_y ?? (row * 120 + 30) },
        data: { element: el },
        ...(el.parent_id && elements.has(el.parent_id) && !isContainer ? { parentId: el.parent_id, extent: 'parent' as const } : {}),
        style: isContainer ? { width: 420, height: 220 } : undefined,
      })

      col++
      if (col > 4) { col = 0; row++ }

      // Parent-child edges (hierarchy)
      if (el.parent_id && elements.has(el.parent_id)) {
        const parentInView = !segment || elements.get(el.parent_id)?.segment === segment
        if (parentInView) {
          edges.push({
            id: `h-${el.parent_id}-${el.id}`,
            source: el.parent_id,
            target: el.id,
            style: { stroke: '#374151', strokeDasharray: '4 2' },
            animated: false,
          })
        }
      }
    }

    // Interface edges
    for (const iface of interfaces.values()) {
      const from = elements.get(iface.from_element_id)
      const to = elements.get(iface.to_element_id)
      if (!from || !to) continue
      if (segment && (from.segment !== segment || to.segment !== segment)) continue

      const ifaceColor = iface.interface_type === 'electrical' ? '#f59e0b' :
                         iface.interface_type === 'data' ? '#3b82f6' :
                         iface.interface_type === 'rf' ? '#ec4899' :
                         iface.interface_type === 'thermal' ? '#ef4444' : '#6b7280'

      edges.push({
        id: `i-${iface.id}`,
        source: iface.from_element_id,
        target: iface.to_element_id,
        label: iface.diagram_label || iface.name,
        style: { stroke: ifaceColor, strokeWidth: 2 },
        animated: iface.interface_type === 'rf',
      })
    }

    return { initialNodes: nodes, initialEdges: edges }
  }, [elements, interfaces, segment, level])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Sync when model changes
  useEffect(() => {
    setNodes(initialNodes)
    setEdges(initialEdges)
  }, [initialNodes, initialEdges])

  // Save node positions back to model on drag end
  const onNodeDragStop = useCallback((_: any, node: Node) => {
    updateElement(node.id, {
      diagram_x: node.position.x,
      diagram_y: node.position.y,
    })
  }, [updateElement])

  // Create interface when connecting two nodes
  const onConnect = useCallback((connection: Connection) => {
    if (!studyId || !connection.source || !connection.target) return
    const label = prompt('Interface label (e.g., "Power Bus", "SpaceWire"):') || ''
    const ifType = prompt('Type (electrical/data/rf/mechanical/thermal):') || 'data'
    createInterface(studyId, {
      name: label,
      interface_type: ifType,
      from_element_id: connection.source,
      to_element_id: connection.target,
      diagram_label: label,
    })
    setEdges(eds => addEdge({ ...connection, label }, eds))
  }, [studyId, createInterface, setEdges])

  if (elements.size === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
        <h3>System Block Diagram</h3>
        <p style={{ fontSize: '0.82rem' }}>Run a design first to generate the element tree.</p>
        <p style={{ fontSize: '0.72rem', color: '#374151' }}>
          The block diagram will auto-populate from the design result.
          You can then edit, add, and connect elements.
        </p>
      </div>
    )
  }

  return (
    <div style={{ height: '100%', minHeight: 400 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={onNodeDragStop}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        style={{ background: '#0a0e1a' }}
        defaultEdgeOptions={{ style: { strokeWidth: 1.5, stroke: '#6b7280' } }}
      >
        <Controls style={{ button: { background: '#1f2937', color: '#d1d5db', border: '1px solid #374151' } } as any} />
        <Background color="#374151" gap={20} />
        <MiniMap nodeStrokeWidth={3} style={{ background: '#111827', border: '1px solid #374151' }} />
      </ReactFlow>
    </div>
  )
}
