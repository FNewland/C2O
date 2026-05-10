/**
 * SystemBlockDiagram — Per-segment internal block diagram.
 *
 * Shows the internal structure of a selected segment (space, ground).
 * Generated from architecture selections — each selected architecture
 * adds its blocks and connections to the diagram.
 *
 * Level 2 in the System-V: system architecture within each segment.
 */
import { useMemo, useCallback, useState } from 'react'
import {
  ReactFlow, useNodesState, useEdgesState, Handle, Position, Controls, Background,
  type Node, type Edge, type NodeTypes, type Connection, addEdge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'

// Subsystem node component
function SubsystemNode({ data }: { data: { label: string; color: string; blocks?: string[] } }) {
  return (
    <div style={{
      padding: '8px 14px', border: `2px solid ${data.color}`, borderRadius: 8,
      background: `${data.color}15`, textAlign: 'center', minWidth: 120,
    }}>
      <Handle type="target" position={Position.Top} />
      <Handle type="target" position={Position.Left} id="left" />
      <div style={{ fontSize: '0.78rem', color: data.color, fontWeight: 700 }}>{data.label}</div>
      {data.blocks && data.blocks.length > 0 && (
        <div style={{ fontSize: '0.6rem', color: '#9ca3af', marginTop: '0.2rem' }}>
          {data.blocks.join(' | ')}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} id="right" />
    </div>
  )
}

// Container node — resizable boundary box for segments/systems
function ContainerNode({ data }: { data: { label: string; color: string; childCount?: number } }) {
  const w = data.childCount ? Math.max(400, (Math.min(data.childCount, 4)) * 200 + 60) : 400
  const h = data.childCount ? Math.max(300, Math.ceil(data.childCount / 4) * 150 + 80) : 300
  return (
    <div style={{
      width: w, height: h, minWidth: 300, minHeight: 200,
      border: `2px dashed ${data.color}`, borderRadius: 12,
      background: `${data.color}08`,
      position: 'relative',
    }}>
      {/* Title bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        padding: '4px 12px',
        background: `${data.color}20`,
        borderBottom: `1px solid ${data.color}40`,
        borderRadius: '10px 10px 0 0',
        fontSize: '0.75rem', fontWeight: 700, color: data.color,
        textTransform: 'uppercase', letterSpacing: '0.05em',
      }}>
        {data.label}
      </div>
      <Handle type="target" position={Position.Top} />
      <Handle type="target" position={Position.Left} id="left" />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} id="right" />
    </div>
  )
}

const nodeTypes: NodeTypes = { subsystem: SubsystemNode, container: ContainerNode }

const SUBSYSTEM_COLORS: Record<string, string> = {
  payload: '#10b981', eps: '#f59e0b', aocs: '#06b6d4', ttc: '#ec4899',
  thermal: '#ef4444', structure: '#84cc16', propulsion: '#f97316',
  obc: '#8b5cf6', ground_ops: '#0ea5e9', data_proc: '#14b8a6',
  archive: '#6366f1', mcc: '#d946ef',
}

// Generate space segment diagram from architecture selections
function generateSpaceSegmentDiagram(archReqs: any[]): { nodes: Node[]; edges: Edge[] } {
  const subsystems = ['payload', 'eps', 'aocs', 'ttc', 'obc', 'thermal', 'structure', 'propulsion']
  const nodes: Node[] = subsystems.map((ss, i) => {
    const col = i % 4
    const row = Math.floor(i / 4)
    const blocks = archReqs.filter(r => r.subsystem === ss).map(r => r.id).slice(0, 2)
    return {
      id: `ss-${ss}`, type: 'subsystem',
      position: { x: 50 + col * 180, y: 30 + row * 130 },
      data: { label: ss.toUpperCase(), color: SUBSYSTEM_COLORS[ss] || '#6b7280', blocks },
    }
  })

  // Standard inter-subsystem connections
  const edges: Edge[] = [
    { id: 'e-eps-all', source: 'ss-eps', target: 'ss-obc', label: 'Power Bus', style: { stroke: '#f59e0b' } },
    { id: 'e-obc-aocs', source: 'ss-obc', target: 'ss-aocs', label: 'ADCS cmds', style: { stroke: '#8b5cf6' } },
    { id: 'e-obc-ttc', source: 'ss-obc', target: 'ss-ttc', label: 'TM/TC', style: { stroke: '#ec4899' } },
    { id: 'e-obc-payload', source: 'ss-obc', target: 'ss-payload', label: 'Payload data', style: { stroke: '#10b981' } },
    { id: 'e-aocs-payload', source: 'ss-aocs', target: 'ss-payload', label: 'Pointing', style: { stroke: '#06b6d4' }, animated: true },
    { id: 'e-eps-thermal', source: 'ss-eps', target: 'ss-thermal', label: 'Heater pwr', style: { stroke: '#ef4444' } },
  ]

  return { nodes, edges }
}

// Generate ground segment diagram
function generateGroundSegmentDiagram(): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [
    // Row 1: RF chain
    { id: 'gs-antenna', type: 'subsystem', position: { x: 50, y: 30 }, data: { label: 'GS Antenna', color: '#10b981', blocks: ['Tracking', 'RF Front-End'] } },
    { id: 'gs-modem', type: 'subsystem', position: { x: 250, y: 30 }, data: { label: 'Modem/Baseband', color: '#10b981', blocks: ['Demod', 'Decode', 'Frame Sync'] } },
    // Row 2: Control
    { id: 'gs-mcc', type: 'subsystem', position: { x: 50, y: 160 }, data: { label: 'Mission Control', color: '#d946ef', blocks: ['Scheduling', 'Commanding', 'FDIR'] } },
    { id: 'gs-fds', type: 'subsystem', position: { x: 250, y: 160 }, data: { label: 'Flight Dynamics', color: '#8b5cf6', blocks: ['Orbit Det.', 'Manoeuvre Plan'] } },
    // Row 3: Data
    { id: 'gs-proc', type: 'subsystem', position: { x: 450, y: 30 }, data: { label: 'Data Processing', color: '#14b8a6', blocks: ['L0', 'L1', 'L2', 'QC'] } },
    { id: 'gs-archive', type: 'subsystem', position: { x: 450, y: 160 }, data: { label: 'Archive & Catalogue', color: '#6366f1', blocks: ['Storage', 'Metadata', 'API'] } },
    // Row 4: Support
    { id: 'gs-network', type: 'subsystem', position: { x: 250, y: 290 }, data: { label: 'Ground Network', color: '#6b7280', blocks: ['WAN', 'VPN', 'Internet'] } },
    { id: 'gs-security', type: 'subsystem', position: { x: 50, y: 290 }, data: { label: 'Security / CyberSec', color: '#ef4444', blocks: ['Auth', 'Encryption', 'Audit'] } },
    { id: 'gs-distrib', type: 'subsystem', position: { x: 450, y: 290 }, data: { label: 'User Services', color: '#f59e0b', blocks: ['Portal', 'Dissemination', 'SLA'] } },
  ]

  const edges: Edge[] = [
    { id: 'ge-ant-modem', source: 'gs-antenna', target: 'gs-modem', label: 'RF/IF', style: { stroke: '#10b981' } },
    { id: 'ge-modem-mcc', source: 'gs-modem', target: 'gs-mcc', label: 'TM frames', style: { stroke: '#d946ef' } },
    { id: 'ge-modem-proc', source: 'gs-modem', target: 'gs-proc', label: 'Payload data', style: { stroke: '#14b8a6' } },
    { id: 'ge-mcc-fds', source: 'gs-mcc', target: 'gs-fds', label: 'Orbit/Att TM', style: { stroke: '#8b5cf6' } },
    { id: 'ge-fds-mcc', source: 'gs-fds', target: 'gs-mcc', label: 'Manoeuvre cmds', style: { stroke: '#8b5cf6' }, animated: true },
    { id: 'ge-proc-arch', source: 'gs-proc', target: 'gs-archive', label: 'Products', style: { stroke: '#6366f1' } },
    { id: 'ge-arch-distrib', source: 'gs-archive', target: 'gs-distrib', label: 'Data products', style: { stroke: '#f59e0b' } },
    { id: 'ge-mcc-net', source: 'gs-mcc', target: 'gs-network', label: 'Ops data', style: { stroke: '#6b7280' } },
    { id: 'ge-sec-mcc', source: 'gs-security', target: 'gs-mcc', label: 'TC auth', style: { stroke: '#ef4444' } },
    { id: 'ge-sec-net', source: 'gs-security', target: 'gs-network', label: 'VPN/TLS', style: { stroke: '#ef4444' } },
  ]

  return { nodes, edges }
}

// Generate segment-level interface diagram (Space ↔ Ground ↔ User)
function generateSegmentInterfaceDiagram(): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [
    { id: 'seg-space', type: 'subsystem', position: { x: 250, y: 20 }, data: { label: 'SPACE SEGMENT', color: '#3b82f6', blocks: ['Spacecraft', 'Constellation'] } },
    { id: 'seg-ground', type: 'subsystem', position: { x: 100, y: 180 }, data: { label: 'GROUND SEGMENT', color: '#10b981', blocks: ['GS Network', 'MCC', 'FDS'] } },
    { id: 'seg-user', type: 'subsystem', position: { x: 400, y: 180 }, data: { label: 'USER SEGMENT', color: '#f59e0b', blocks: ['End Users', 'Applications'] } },
    { id: 'seg-launch', type: 'subsystem', position: { x: 50, y: 20 }, data: { label: 'LAUNCH SEGMENT', color: '#f43f5e', blocks: ['LV', 'Integration'] } },
    { id: 'seg-external', type: 'subsystem', position: { x: 450, y: 20 }, data: { label: 'EXTERNAL SERVICES', color: '#8b5cf6', blocks: ['GNSS', 'TDRSS', 'SSA'] } },
  ]

  const edges: Edge[] = [
    { id: 'si-space-ground', source: 'seg-space', target: 'seg-ground', label: 'TM/TC (S/X-band)', style: { stroke: '#3b82f6', strokeWidth: 3 }, animated: true },
    { id: 'si-ground-space', source: 'seg-ground', target: 'seg-space', label: 'TC Uplink', style: { stroke: '#10b981', strokeWidth: 2 } },
    { id: 'si-ground-user', source: 'seg-ground', target: 'seg-user', label: 'Data Products (API/FTP)', style: { stroke: '#f59e0b', strokeWidth: 2 } },
    { id: 'si-user-ground', source: 'seg-user', target: 'seg-ground', label: 'Tasking Requests', style: { stroke: '#f59e0b' } },
    { id: 'si-launch-space', source: 'seg-launch', target: 'seg-space', label: 'Deployment I/F', style: { stroke: '#f43f5e', strokeWidth: 2 } },
    { id: 'si-ext-space', source: 'seg-external', target: 'seg-space', label: 'Nav/Relay', style: { stroke: '#8b5cf6' } },
    { id: 'si-ext-ground', source: 'seg-external', target: 'seg-ground', label: 'Ephemeris/SSA', style: { stroke: '#8b5cf6' } },
  ]

  return { nodes, edges }
}

type Segment = 'space' | 'ground' | 'segments'

// SYSTEM-V: Generate diagram from element tree if populated
function generateFromElementTree(
  elements: Map<string, any>,
  interfaces: Map<string, any>,
  seg: 'space' | 'ground',
): { nodes: Node[]; edges: Edge[] } | null {
  const allEls = Array.from(elements.values())

  // Find segment and system container elements for this segment
  const containers = allEls.filter(
    el => (el.element_type === 'segment' || el.element_type === 'system') && el.segment === seg
  )

  // Find subsystem elements for this segment
  const subsystems = allEls.filter(
    el => el.element_type === 'subsystem' && el.segment === seg
  )
  if (subsystems.length < 2) return null // Not enough data, fall back to static

  const nodes: Node[] = []

  // Container color map for segments/systems
  const CONTAINER_COLORS: Record<string, string> = {
    space: '#3b82f6', ground: '#10b981', launch: '#f43f5e',
  }

  // Build container nodes for segment and system elements
  const containerIds = new Set<string>()
  containers.forEach((el, i) => {
    const childCount = allEls.filter(c => c.parent_id === el.id).length
    const col = i % 2
    const row = Math.floor(i / 2)
    const color = CONTAINER_COLORS[el.segment] || '#6b7280'
    nodes.push({
      id: `el-${el.id}`,
      type: 'container',
      position: { x: el.diagram_x ?? (20 + col * 440), y: el.diagram_y ?? (20 + row * 340) },
      data: { label: el.name, color, childCount },
      style: { width: Math.max(400, Math.min(childCount, 4) * 200 + 60), height: Math.max(300, Math.ceil(childCount / 4) * 150 + 80) },
    })
    containerIds.add(el.id)
  })

  // Build subsystem nodes — parent them inside their container if applicable
  subsystems.forEach((el, i) => {
    const col = i % 4
    const row = Math.floor(i / 4)
    const domain = el.subsystem_domain || el.name.toLowerCase()
    const children = allEls.filter(c => c.parent_id === el.id)
    const blocks = children.slice(0, 3).map((c: any) => c.name)

    const parentContainerId = el.parent_id && containerIds.has(el.parent_id) ? el.parent_id : undefined
    // If parented, position is relative to container; use stored pos or layout within container
    let posX: number, posY: number
    if (parentContainerId) {
      // Count siblings to compute layout position within the container
      const siblings = subsystems.filter(s => s.parent_id === parentContainerId)
      const sibIdx = siblings.indexOf(el)
      const sCol = sibIdx % 4
      const sRow = Math.floor(sibIdx / 4)
      posX = el.diagram_x ?? (30 + sCol * 180)
      posY = el.diagram_y ?? (40 + sRow * 130)
    } else {
      posX = el.diagram_x ?? (50 + col * 180)
      posY = el.diagram_y ?? (30 + row * 130)
    }

    const node: Node = {
      id: `el-${el.id}`,
      type: 'subsystem',
      position: { x: posX, y: posY },
      data: {
        label: el.name,
        color: SUBSYSTEM_COLORS[domain] || '#6b7280',
        blocks,
      },
    }
    if (parentContainerId) {
      node.parentId = `el-${parentContainerId}`
      node.extent = 'parent' as const
    }
    nodes.push(node)
  })

  // Build edges from model interfaces
  const edges: Edge[] = []
  for (const iface of interfaces.values()) {
    const fromNode = nodes.find(n => n.id === `el-${iface.from_element_id}`)
    const toNode = nodes.find(n => n.id === `el-${iface.to_element_id}`)
    if (fromNode && toNode) {
      edges.push({
        id: `iface-${iface.id}`,
        source: fromNode.id,
        target: toNode.id,
        label: iface.diagram_label || iface.name || '',
        style: { stroke: '#6b7280' },
      })
    }
  }

  return { nodes, edges }
}

export function SystemBlockDiagram() {
  const archReqs = useDesignStore(s => s.architectureDerivedReqs)
  const modelElements = useModelStore(s => s.elements)
  const modelInterfaces = useModelStore(s => s.interfaces)
  const [segment, setSegment] = useState<Segment>('space')

  const { initialNodes, initialEdges } = useMemo(() => {
    if (segment === 'space') {
      // Try element tree first, fall back to static generator
      const fromTree = generateFromElementTree(modelElements, modelInterfaces, 'space')
      if (fromTree) return { initialNodes: fromTree.nodes, initialEdges: fromTree.edges }
      const { nodes, edges } = generateSpaceSegmentDiagram(archReqs)
      return { initialNodes: nodes, initialEdges: edges }
    } else if (segment === 'segments') {
      const { nodes, edges } = generateSegmentInterfaceDiagram()
      return { initialNodes: nodes, initialEdges: edges }
    } else {
      const fromTree = generateFromElementTree(modelElements, modelInterfaces, 'ground')
      if (fromTree) return { initialNodes: fromTree.nodes, initialEdges: fromTree.edges }
      const { nodes, edges } = generateGroundSegmentDiagram()
      return { initialNodes: nodes, initialEdges: edges }
    }
  }, [segment, archReqs, modelElements, modelInterfaces])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const updateElement = useModelStore(s => s.updateElement)
  const createInterface = useModelStore(s => s.createInterface)
  const studyId = useDesignStore(s => s.studyId)

  const onConnect = useCallback(
    (connection: Connection) => {
      const label = prompt('Interface label:') || ''
      setEdges(eds => addEdge({ ...connection, label }, eds))

      // SYSTEM-V: Also create interface in modelStore if nodes are from element tree
      if (studyId && connection.source?.startsWith('el-') && connection.target?.startsWith('el-')) {
        const fromId = connection.source.replace('el-', '')
        const toId = connection.target.replace('el-', '')
        createInterface(studyId, {
          name: label,
          interface_type: 'data',
          direction: 'bidirectional',
          from_element_id: fromId,
          to_element_id: toId,
          diagram_label: label,
          status: 'defined',
        } as any)
      }
    },
    [setEdges, studyId, createInterface],
  )

  // SYSTEM-V: Persist node positions back to modelStore on drag end
  const onNodeDragStop = useCallback(
    (_event: any, node: Node) => {
      if (node.id.startsWith('el-')) {
        const elementId = node.id.replace('el-', '')
        updateElement(elementId, {
          diagram_x: Math.round(node.position.x),
          diagram_y: Math.round(node.position.y),
        })
      }
    },
    [updateElement],
  )

  // Reset when segment changes — prefer element tree, fall back to static
  const switchSegment = (s: Segment) => {
    setSegment(s)
    if (s === 'space') {
      const fromTree = generateFromElementTree(modelElements, modelInterfaces, 'space')
      if (fromTree) { setNodes(fromTree.nodes); setEdges(fromTree.edges) }
      else { const { nodes: n, edges: e } = generateSpaceSegmentDiagram(archReqs); setNodes(n); setEdges(e) }
    } else if (s === 'segments') {
      const { nodes: n, edges: e } = generateSegmentInterfaceDiagram()
      setNodes(n); setEdges(e)
    } else {
      const fromTree = generateFromElementTree(modelElements, modelInterfaces, 'ground')
      if (fromTree) { setNodes(fromTree.nodes); setEdges(fromTree.edges) }
      else { const { nodes: n, edges: e } = generateGroundSegmentDiagram(); setNodes(n); setEdges(e) }
    }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Segment selector */}
      <div style={{ padding: '0.4rem 0.75rem', borderBottom: '1px solid var(--border, #374151)', display: 'flex', gap: '0.3rem', alignItems: 'center' }}>
        <span style={{ fontSize: '0.75rem', color: '#9ca3af', marginRight: '0.3rem' }}>Segment:</span>
        {(['space', 'ground', 'segments'] as Segment[]).map(s => (
          <button key={s} onClick={() => switchSegment(s)} style={{
            padding: '0.25rem 0.6rem', fontSize: '0.72rem', borderRadius: '4px', cursor: 'pointer',
            background: segment === s ? '#3b82f6' : 'transparent',
            color: segment === s ? 'white' : '#9ca3af',
            border: `1px solid ${segment === s ? '#3b82f6' : '#374151'}`,
            textTransform: 'capitalize',
          }}>{s} Segment</button>
        ))}
        <span style={{ flex: 1 }} />
        <span style={{ fontSize: '0.65rem', color: '#6b7280' }}>
          {segment === 'space' ? 'Platform subsystems + interfaces' :
           segment === 'ground' ? 'Ground station + MCC + data processing pipeline' :
           'Mission segment interfaces (Space ↔ Ground ↔ User)'}
        </span>
        {segment !== 'segments' && (
          <span style={{
            fontSize: '0.58rem', padding: '0.1rem 0.35rem', borderRadius: '3px',
            background: nodes.some(n => n.id.startsWith('el-')) ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
            color: nodes.some(n => n.id.startsWith('el-')) ? '#10b981' : '#f59e0b',
          }}>
            {nodes.some(n => n.id.startsWith('el-')) ? 'From element tree' : 'Template — run design to populate'}
          </span>
        )}
      </div>

      {/* Block diagram */}
      <div style={{ flex: 1, minHeight: 300 }} key={segment}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDragStop={onNodeDragStop}
          nodeTypes={nodeTypes}
          fitView
          style={{ background: '#0a0e1a' }}
          defaultEdgeOptions={{ style: { strokeWidth: 1.5, stroke: '#6b7280' } }}
        >
          <Controls />
          <Background color="#374151" gap={20} />
        </ReactFlow>
      </div>
    </div>
  )
}

