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
  NodeResizer,
  type Node, type Edge, type NodeTypes, type Connection, addEdge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'
import { fs } from '../theme/tokens'
import { askText, showAlert } from './ui/Dialog'

// Subsystem node component
function SubsystemNode({ data }: { data: { label: string; color: string; blocks?: string[] } }) {
  return (
    <div style={{
      padding: '8px 14px', border: `2px solid ${data.color}`, borderRadius: 8,
      background: `color-mix(in srgb, ${data.color} 8%, transparent)`, textAlign: 'center', minWidth: 120,
    }}>
      <Handle type="target" position={Position.Top} />
      <Handle type="target" position={Position.Left} id="left" />
      <div style={{ fontSize: fs.label, color: data.color, fontWeight: 700 }}>{data.label}</div>
      {data.blocks && data.blocks.length > 0 && (
        <div style={{ fontSize: fs.label, color: 'var(--text-2)', marginTop: '0.2rem' }}>
          {data.blocks.join(' | ')}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} id="right" />
    </div>
  )
}

// Container node — resizable boundary box for segments/systems
function ContainerNode({ data, selected }: { data: { label: string; color: string; childCount?: number }; selected?: boolean }) {
  return (
    <div style={{
      width: '100%', height: '100%', minWidth: 300, minHeight: 200,
      border: `2px dashed ${data.color}`, borderRadius: 12,
      background: `color-mix(in srgb, ${data.color} 3%, transparent)`,
      position: 'relative',
    }}>
      <NodeResizer
        minWidth={300} minHeight={200}
        isVisible={!!selected}
        lineStyle={{ borderColor: data.color, borderWidth: 2 }}
        handleStyle={{ backgroundColor: data.color, width: 8, height: 8 }}
      />
      {/* Title bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        padding: '4px 12px',
        background: `color-mix(in srgb, ${data.color} 13%, transparent)`,
        borderBottom: `1px solid color-mix(in srgb, ${data.color} 25%, transparent)`,
        borderRadius: '10px 10px 0 0',
        fontSize: fs.label, fontWeight: 700, color: data.color,
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
  payload: 'var(--status-ok)', eps: 'var(--status-caution)', aocs: 'var(--interactive)', ttc: 'var(--cat-6)',
  thermal: 'var(--status-alarm)', structure: 'var(--cat-7)', propulsion: 'var(--status-caution)',
  obc: 'var(--cat-2)', ground_ops: 'var(--interactive)', data_proc: 'var(--cat-3)',
  archive: 'var(--interactive)', mcc: 'var(--cat-2)',
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
      data: { label: ss.toUpperCase(), color: SUBSYSTEM_COLORS[ss] || 'var(--text-3)', blocks },
    }
  })

  // Standard inter-subsystem connections
  const edges: Edge[] = [
    { id: 'e-eps-all', source: 'ss-eps', target: 'ss-obc', label: 'Power Bus', style: { stroke: 'var(--status-caution)' } },
    { id: 'e-obc-aocs', source: 'ss-obc', target: 'ss-aocs', label: 'ADCS cmds', style: { stroke: 'var(--cat-2)' } },
    { id: 'e-obc-ttc', source: 'ss-obc', target: 'ss-ttc', label: 'TM/TC', style: { stroke: 'var(--cat-6)' } },
    { id: 'e-obc-payload', source: 'ss-obc', target: 'ss-payload', label: 'Payload data', style: { stroke: 'var(--status-ok)' } },
    { id: 'e-aocs-payload', source: 'ss-aocs', target: 'ss-payload', label: 'Pointing', style: { stroke: 'var(--interactive)' }, animated: true },
    { id: 'e-eps-thermal', source: 'ss-eps', target: 'ss-thermal', label: 'Heater pwr', style: { stroke: 'var(--status-alarm)' } },
  ]

  return { nodes, edges }
}

// Generate ground segment diagram
function generateGroundSegmentDiagram(): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [
    // Row 1: RF chain
    { id: 'gs-antenna', type: 'subsystem', position: { x: 50, y: 30 }, data: { label: 'GS Antenna', color: 'var(--status-ok)', blocks: ['Tracking', 'RF Front-End'] } },
    { id: 'gs-modem', type: 'subsystem', position: { x: 250, y: 30 }, data: { label: 'Modem/Baseband', color: 'var(--status-ok)', blocks: ['Demod', 'Decode', 'Frame Sync'] } },
    // Row 2: Control
    { id: 'gs-mcc', type: 'subsystem', position: { x: 50, y: 160 }, data: { label: 'Mission Control', color: 'var(--cat-2)', blocks: ['Scheduling', 'Commanding', 'FDIR'] } },
    { id: 'gs-fds', type: 'subsystem', position: { x: 250, y: 160 }, data: { label: 'Flight Dynamics', color: 'var(--cat-2)', blocks: ['Orbit Det.', 'Manoeuvre Plan'] } },
    // Row 3: Data
    { id: 'gs-proc', type: 'subsystem', position: { x: 450, y: 30 }, data: { label: 'Data Processing', color: 'var(--cat-3)', blocks: ['L0', 'L1', 'L2', 'QC'] } },
    { id: 'gs-archive', type: 'subsystem', position: { x: 450, y: 160 }, data: { label: 'Archive & Catalogue', color: 'var(--interactive)', blocks: ['Storage', 'Metadata', 'API'] } },
    // Row 4: Support
    { id: 'gs-network', type: 'subsystem', position: { x: 250, y: 290 }, data: { label: 'Ground Network', color: 'var(--text-3)', blocks: ['WAN', 'VPN', 'Internet'] } },
    { id: 'gs-security', type: 'subsystem', position: { x: 50, y: 290 }, data: { label: 'Security / CyberSec', color: 'var(--status-alarm)', blocks: ['Auth', 'Encryption', 'Audit'] } },
    { id: 'gs-distrib', type: 'subsystem', position: { x: 450, y: 290 }, data: { label: 'User Services', color: 'var(--status-caution)', blocks: ['Portal', 'Dissemination', 'SLA'] } },
  ]

  const edges: Edge[] = [
    { id: 'ge-ant-modem', source: 'gs-antenna', target: 'gs-modem', label: 'RF/IF', style: { stroke: 'var(--status-ok)' } },
    { id: 'ge-modem-mcc', source: 'gs-modem', target: 'gs-mcc', label: 'TM frames', style: { stroke: 'var(--cat-2)' } },
    { id: 'ge-modem-proc', source: 'gs-modem', target: 'gs-proc', label: 'Payload data', style: { stroke: 'var(--cat-3)' } },
    { id: 'ge-mcc-fds', source: 'gs-mcc', target: 'gs-fds', label: 'Orbit/Att TM', style: { stroke: 'var(--cat-2)' } },
    { id: 'ge-fds-mcc', source: 'gs-fds', target: 'gs-mcc', label: 'Manoeuvre cmds', style: { stroke: 'var(--cat-2)' }, animated: true },
    { id: 'ge-proc-arch', source: 'gs-proc', target: 'gs-archive', label: 'Products', style: { stroke: 'var(--interactive)' } },
    { id: 'ge-arch-distrib', source: 'gs-archive', target: 'gs-distrib', label: 'Data products', style: { stroke: 'var(--status-caution)' } },
    { id: 'ge-mcc-net', source: 'gs-mcc', target: 'gs-network', label: 'Ops data', style: { stroke: 'var(--text-3)' } },
    { id: 'ge-sec-mcc', source: 'gs-security', target: 'gs-mcc', label: 'TC auth', style: { stroke: 'var(--status-alarm)' } },
    { id: 'ge-sec-net', source: 'gs-security', target: 'gs-network', label: 'VPN/TLS', style: { stroke: 'var(--status-alarm)' } },
  ]

  return { nodes, edges }
}

// Generate segment-level interface diagram (Space ↔ Ground ↔ User)
function generateSegmentInterfaceDiagram(): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [
    { id: 'seg-space', type: 'subsystem', position: { x: 250, y: 20 }, data: { label: 'SPACE SEGMENT', color: 'var(--interactive)', blocks: ['Spacecraft', 'Constellation'] } },
    { id: 'seg-ground', type: 'subsystem', position: { x: 100, y: 180 }, data: { label: 'GROUND SEGMENT', color: 'var(--status-ok)', blocks: ['GS Network', 'MCC', 'FDS'] } },
    { id: 'seg-user', type: 'subsystem', position: { x: 400, y: 180 }, data: { label: 'USER SEGMENT', color: 'var(--status-caution)', blocks: ['End Users', 'Applications'] } },
    { id: 'seg-launch', type: 'subsystem', position: { x: 50, y: 20 }, data: { label: 'LAUNCH SEGMENT', color: 'var(--status-alarm)', blocks: ['LV', 'Integration'] } },
    { id: 'seg-external', type: 'subsystem', position: { x: 450, y: 20 }, data: { label: 'EXTERNAL SERVICES', color: 'var(--cat-2)', blocks: ['GNSS', 'TDRSS', 'SSA'] } },
  ]

  const edges: Edge[] = [
    { id: 'si-space-ground', source: 'seg-space', target: 'seg-ground', label: 'TM/TC (S/X-band)', style: { stroke: 'var(--interactive)', strokeWidth: 3 }, animated: true },
    { id: 'si-ground-space', source: 'seg-ground', target: 'seg-space', label: 'TC Uplink', style: { stroke: 'var(--status-ok)', strokeWidth: 2 } },
    { id: 'si-ground-user', source: 'seg-ground', target: 'seg-user', label: 'Data Products (API/FTP)', style: { stroke: 'var(--status-caution)', strokeWidth: 2 } },
    { id: 'si-user-ground', source: 'seg-user', target: 'seg-ground', label: 'Tasking Requests', style: { stroke: 'var(--status-caution)' } },
    { id: 'si-launch-space', source: 'seg-launch', target: 'seg-space', label: 'Deployment I/F', style: { stroke: 'var(--status-alarm)', strokeWidth: 2 } },
    { id: 'si-ext-space', source: 'seg-external', target: 'seg-space', label: 'Nav/Relay', style: { stroke: 'var(--cat-2)' } },
    { id: 'si-ext-ground', source: 'seg-external', target: 'seg-ground', label: 'Ephemeris/SSA', style: { stroke: 'var(--cat-2)' } },
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
  const allEls = Array.from(elements.values()).filter(el => !(el as any).deleted_at)

  // Find segment and system container elements for this segment
  const containers = allEls.filter(
    el => (el.element_type === 'segment' || el.element_type === 'system') && el.segment === seg
  )

  // Find subsystem elements for this segment
  const subsystems = allEls.filter(
    el => el.element_type === 'subsystem' && el.segment === seg
  )
  if (subsystems.length < 1) return null // Not enough data, fall back to static

  const nodes: Node[] = []

  // Container color map for segments/systems
  const CONTAINER_COLORS: Record<string, string> = {
    space: 'var(--interactive)', ground: 'var(--status-ok)', launch: 'var(--status-alarm)',
  }

  // Build container nodes for segment and system elements
  const containerIds = new Set<string>()
  containers.forEach((el, i) => {
    const childCount = allEls.filter(c => c.parent_id === el.id).length
    const col = i % 2
    const row = Math.floor(i / 2)
    const color = CONTAINER_COLORS[el.segment] || 'var(--text-3)'
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
        color: SUBSYSTEM_COLORS[domain] || 'var(--text-3)',
        blocks,
      },
    }
    if (parentContainerId) {
      node.parentId = `el-${parentContainerId}`
      node.extent = 'parent' as const
    }
    nodes.push(node)
  })

  // Build component nodes inside subsystem containers
  const subsystemIds = new Set(subsystems.map(s => s.id))
  const components = allEls.filter(
    el => el.element_type === 'component' && el.parent_id && subsystemIds.has(el.parent_id)
  )
  components.forEach((el) => {
    const parentNodeId = `el-${el.parent_id}`
    // Count siblings for grid layout
    const siblings = components.filter(c => c.parent_id === el.parent_id)
    const sibIdx = siblings.indexOf(el)
    const cCol = sibIdx % 3
    const cRow = Math.floor(sibIdx / 3)
    const massStr = el.mass_kg != null ? ` (${el.mass_kg} kg)` : ''
    const parentDomain = subsystems.find(s => s.id === el.parent_id)?.subsystem_domain || ''
    const color = SUBSYSTEM_COLORS[parentDomain] || 'var(--text-3)'

    nodes.push({
      id: `el-${el.id}`,
      type: 'subsystem',
      position: { x: el.diagram_x ?? (10 + cCol * 140), y: el.diagram_y ?? (30 + cRow * 50) },
      parentId: parentNodeId,
      extent: 'parent' as const,
      data: {
        label: `${el.name}${massStr}`,
        color,
        blocks: [],
      },
      style: { fontSize: fs.label },
    } as Node)
  })

  // Expand subsystem containers to fit their components
  for (const ss of subsystems) {
    const childComps = components.filter(c => c.parent_id === ss.id)
    if (childComps.length > 0) {
      const ssNode = nodes.find(n => n.id === `el-${ss.id}`)
      if (ssNode && ssNode.type === 'subsystem') {
        // Upgrade subsystem to container so children can live inside
        ssNode.type = 'container'
        const cols = Math.min(childComps.length, 3)
        const rows = Math.ceil(childComps.length / 3)
        ssNode.style = {
          width: Math.max(200, cols * 140 + 30),
          height: Math.max(120, rows * 50 + 60),
        }
      }
    }
  }

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
        style: { stroke: 'var(--text-3)' },
      })
    }
  }

  return { nodes, edges }
}

export function SystemBlockDiagram() {
  const archReqs: any[] = []  // TODO: migrate to backend requirements API with element_id
  const modelElements = useModelStore(s => s.elements)
  const modelInterfaces = useModelStore(s => s.interfaces)
  const [segment, setSegment] = useState<Segment>('space')

  const { initialNodes, initialEdges } = useMemo(() => {
    if (segment === 'segments') {
      // Segment-level interface diagram is always available as a template
      const { nodes, edges } = generateSegmentInterfaceDiagram()
      return { initialNodes: nodes, initialEdges: edges }
    }
    // Primary: render from element tree
    const fromTree = generateFromElementTree(modelElements, modelInterfaces, segment === 'space' ? 'space' : 'ground')
    if (fromTree) return { initialNodes: fromTree.nodes, initialEdges: fromTree.edges }
    // No elements yet — show empty canvas
    return { initialNodes: [] as Node[], initialEdges: [] as Edge[] }
  }, [segment, modelElements, modelInterfaces])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const updateElement = useModelStore(s => s.updateElement)
  const createElement = useModelStore(s => s.createElement)
  const createInterface = useModelStore(s => s.createInterface)
  const studyId = useDesignStore(s => s.studyId)

  const onConnect = useCallback(
    async (connection: Connection) => {
      const label = (await askText('Interface label:')) || ''
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

  // Add Subsystem handler
  const handleAddSubsystem = async () => {
    if (!studyId || segment === 'segments') return
    const name = (await askText('Subsystem name:'))
    if (!name) return
    const DOMAINS = ['power', 'aocs', 'ttc', 'thermal', 'structure', 'propulsion', 'obc', 'payload']
    const domain = (await askText(`Domain (${DOMAINS.join('/')}):`))?.toLowerCase()
    if (!domain || !DOMAINS.includes(domain)) {
      void showAlert('Invalid domain. Choose from: ' + DOMAINS.join(', '))
      return
    }
    // Find system-level parent for this segment
    const allEls = Array.from(modelElements.values())
    const systemParent = allEls.find(
      el => el.element_type === 'system' && el.segment === segment
    )
    await createElement(studyId, {
      name,
      element_type: 'subsystem',
      subsystem_domain: domain,
      segment,
      parent_id: systemParent?.id || null,
    } as any)
  }

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
      <div style={{ padding: '0.4rem 0.75rem', borderBottom: '1px solid var(--border, var(--line))', display: 'flex', gap: '0.3rem', alignItems: 'center' }}>
        <span style={{ fontSize: fs.label, color: 'var(--text-2)', marginRight: '0.3rem' }}>Segment:</span>
        {(['space', 'ground', 'segments'] as Segment[]).map(s => (
          <button key={s} onClick={() => switchSegment(s)} style={{
            padding: '0.25rem 0.6rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
            background: segment === s ? 'var(--interactive)' : 'transparent',
            color: segment === s ? 'white' : 'var(--text-2)',
            border: `1px solid ${segment === s ? 'var(--interactive)' : 'var(--line)'}`,
            textTransform: 'capitalize',
          }}>{s} Segment</button>
        ))}
        {segment !== 'segments' && (
          <button onClick={handleAddSubsystem} style={{
            padding: '0.25rem 0.6rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
            background: 'var(--status-ok)', color: 'white', border: 'none', marginLeft: '0.5rem',
          }}>+ Add Subsystem</button>
        )}
        <span style={{ flex: 1 }} />
        <span style={{ fontSize: fs.label, color: 'var(--text-3)' }}>
          {segment === 'space' ? 'Platform subsystems + interfaces' :
           segment === 'ground' ? 'Ground station + MCC + data processing pipeline' :
           'Mission segment interfaces (Space ↔ Ground ↔ User)'}
        </span>
        {segment !== 'segments' && (
          <span style={{
            fontSize: fs.label, padding: '0.1rem 0.35rem', borderRadius: '3px',
            background: nodes.some(n => n.id.startsWith('el-')) ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
            color: nodes.some(n => n.id.startsWith('el-')) ? 'var(--status-ok)' : 'var(--status-caution)',
          }}>
            {nodes.some(n => n.id.startsWith('el-')) ? 'From element tree' : 'Template — run design to populate'}
          </span>
        )}
      </div>

      {/* Block diagram */}
      <div style={{ flex: 1, minHeight: 300 }} key={segment}>
        <ReactFlow
          proOptions={{ hideAttribution: true }}
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDragStop={onNodeDragStop}
          nodeTypes={nodeTypes}
          fitView
          style={{ background: 'var(--surface-0)' }}
          defaultEdgeOptions={{ style: { strokeWidth: 1.5, stroke: 'var(--text-3)' } }}
        >
          <Controls />
          <Background color="var(--line)" gap={20} />
        </ReactFlow>
      </div>
    </div>
  )
}

