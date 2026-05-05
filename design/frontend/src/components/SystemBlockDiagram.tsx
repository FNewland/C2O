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

const nodeTypes: NodeTypes = { subsystem: SubsystemNode }

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
    { id: 'gs-antenna', type: 'subsystem', position: { x: 50, y: 30 }, data: { label: 'GS Antenna', color: '#10b981', blocks: ['Tracking', 'RF Front-End'] } },
    { id: 'gs-mcc', type: 'subsystem', position: { x: 250, y: 30 }, data: { label: 'Mission Control', color: '#d946ef', blocks: ['Scheduling', 'Commanding'] } },
    { id: 'gs-proc', type: 'subsystem', position: { x: 450, y: 30 }, data: { label: 'Data Processing', color: '#14b8a6', blocks: ['L0->L1->L2'] } },
    { id: 'gs-archive', type: 'subsystem', position: { x: 450, y: 160 }, data: { label: 'Archive & Distribution', color: '#6366f1', blocks: ['API', 'Portal'] } },
    { id: 'gs-network', type: 'subsystem', position: { x: 250, y: 160 }, data: { label: 'Ground Network', color: '#6b7280', blocks: ['Fibre', 'Internet'] } },
  ]

  const edges: Edge[] = [
    { id: 'ge-ant-mcc', source: 'gs-antenna', target: 'gs-mcc', label: 'TM/TC', style: { stroke: '#10b981' } },
    { id: 'ge-ant-proc', source: 'gs-antenna', target: 'gs-proc', label: 'Payload data', style: { stroke: '#14b8a6' } },
    { id: 'ge-proc-arch', source: 'gs-proc', target: 'gs-archive', label: 'Products', style: { stroke: '#6366f1' } },
    { id: 'ge-mcc-net', source: 'gs-mcc', target: 'gs-network', label: 'Ops data', style: { stroke: '#6b7280' } },
  ]

  return { nodes, edges }
}

type Segment = 'space' | 'ground'

export function SystemBlockDiagram() {
  const archReqs = useDesignStore(s => s.architectureDerivedReqs)
  const [segment, setSegment] = useState<Segment>('space')

  const { initialNodes, initialEdges } = useMemo(() => {
    if (segment === 'space') {
      const { nodes, edges } = generateSpaceSegmentDiagram(archReqs)
      return { initialNodes: nodes, initialEdges: edges }
    } else {
      const { nodes, edges } = generateGroundSegmentDiagram()
      return { initialNodes: nodes, initialEdges: edges }
    }
  }, [segment, archReqs])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const onConnect = useCallback(
    (connection: Connection) => {
      const label = prompt('Interface label:') || ''
      setEdges(eds => addEdge({ ...connection, label }, eds))
    },
    [setEdges],
  )

  // Reset when segment changes
  const switchSegment = (s: Segment) => {
    setSegment(s)
    if (s === 'space') {
      const { nodes: n, edges: e } = generateSpaceSegmentDiagram(archReqs)
      setNodes(n)
      setEdges(e)
    } else {
      const { nodes: n, edges: e } = generateGroundSegmentDiagram()
      setNodes(n)
      setEdges(e)
    }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Segment selector */}
      <div style={{ padding: '0.4rem 0.75rem', borderBottom: '1px solid var(--border, #374151)', display: 'flex', gap: '0.3rem', alignItems: 'center' }}>
        <span style={{ fontSize: '0.75rem', color: '#9ca3af', marginRight: '0.3rem' }}>Segment:</span>
        {(['space', 'ground'] as Segment[]).map(s => (
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
          {segment === 'space' ? 'Platform subsystems + interfaces (from Architecture selections)' :
           'Ground station + MCC + data processing pipeline'}
        </span>
      </div>

      {/* Block diagram */}
      <div style={{ flex: 1, minHeight: 300 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
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

