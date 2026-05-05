/**
 * MissionArchitectureEditor — Interactive drag-drop mission architecture diagram.
 *
 * Uses @xyflow/react for:
 * - Draggable nodes (satellite, ground station, antenna, sensor, user, GNSS, etc.)
 * - Labelled connections between nodes
 * - Custom node types with standard space mission symbols
 * - Pan/zoom
 * - Editable labels
 *
 * This replaces the static SVG in ConOpsEditor for Level 1 (Mission Architecture).
 * The architecture diagram drives what systems need to be defined at Level 2.
 */
import { useCallback, useMemo, useState } from 'react'
import {
  ReactFlow, addEdge, useNodesState, useEdgesState, Handle, Position, Controls, Background, MiniMap,
  type Node, type Edge, type Connection, type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useDesignStore } from '../stores/designStore'

// --- Custom Node Components ---

function SatelliteNode({ data }: { data: { label: string } }) {
  return (
    <div style={{ padding: '8px 12px', border: '2px solid #3b82f6', borderRadius: 8, background: '#1e3a5f', textAlign: 'center', minWidth: 100 }}>
      <Handle type="target" position={Position.Top} />
      <svg width="32" height="32" viewBox="0 0 32 32">
        <rect x="10" y="10" width="12" height="12" fill="#3b82f6" rx="2" />
        <rect x="2" y="12" width="8" height="8" fill="#60a5fa" rx="1" />
        <rect x="22" y="12" width="8" height="8" fill="#60a5fa" rx="1" />
      </svg>
      <div style={{ fontSize: '0.72rem', color: '#93c5fd', fontWeight: 600 }}>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

function GroundStationNode({ data }: { data: { label: string } }) {
  return (
    <div style={{ padding: '8px 12px', border: '2px solid #10b981', borderRadius: 8, background: '#052e16', textAlign: 'center', minWidth: 100 }}>
      <Handle type="target" position={Position.Top} />
      <svg width="32" height="32" viewBox="0 0 32 32">
        <path d="M16 4 L4 16 L28 16 Z" fill="#10b981" />
        <rect x="14" y="16" width="4" height="12" fill="#6b7280" />
      </svg>
      <div style={{ fontSize: '0.72rem', color: '#86efac', fontWeight: 600 }}>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

function UserNode({ data }: { data: { label: string } }) {
  return (
    <div style={{ padding: '8px 12px', border: '2px solid #f59e0b', borderRadius: 8, background: '#451a03', textAlign: 'center', minWidth: 100 }}>
      <Handle type="target" position={Position.Top} />
      <svg width="32" height="32" viewBox="0 0 32 32">
        <circle cx="16" cy="10" r="6" fill="#f59e0b" />
        <path d="M8 28 Q16 20 24 28" fill="#f59e0b" />
      </svg>
      <div style={{ fontSize: '0.72rem', color: '#fbbf24', fontWeight: 600 }}>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

function SensorNode({ data }: { data: { label: string } }) {
  return (
    <div style={{ padding: '8px 12px', border: '2px solid #f97316', borderRadius: 8, background: '#431407', textAlign: 'center', minWidth: 90 }}>
      <Handle type="target" position={Position.Top} />
      <svg width="28" height="28" viewBox="0 0 28 28">
        <circle cx="14" cy="14" r="10" fill="none" stroke="#f97316" strokeWidth="2" />
        <circle cx="14" cy="14" r="4" fill="#f97316" />
        <line x1="14" y1="4" x2="14" y2="0" stroke="#f97316" strokeWidth="2" />
      </svg>
      <div style={{ fontSize: '0.68rem', color: '#fb923c', fontWeight: 600 }}>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

function GNSSNode({ data }: { data: { label: string } }) {
  return (
    <div style={{ padding: '8px 12px', border: '2px solid #8b5cf6', borderRadius: 8, background: '#2e1065', textAlign: 'center', minWidth: 90 }}>
      <Handle type="target" position={Position.Top} />
      <svg width="28" height="28" viewBox="0 0 28 28">
        <circle cx="14" cy="14" r="12" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="3 2" />
        <circle cx="14" cy="14" r="6" fill="none" stroke="#8b5cf6" strokeWidth="1.5" />
        <circle cx="14" cy="14" r="2" fill="#8b5cf6" />
      </svg>
      <div style={{ fontSize: '0.68rem', color: '#a78bfa', fontWeight: 600 }}>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

function ProcessingNode({ data }: { data: { label: string } }) {
  return (
    <div style={{ padding: '8px 12px', border: '2px solid #06b6d4', borderRadius: 8, background: '#083344', textAlign: 'center', minWidth: 100 }}>
      <Handle type="target" position={Position.Top} />
      <svg width="28" height="28" viewBox="0 0 28 28">
        <rect x="4" y="8" width="20" height="12" fill="#06b6d4" rx="2" />
        <rect x="8" y="4" width="12" height="4" fill="#0891b2" rx="1" />
      </svg>
      <div style={{ fontSize: '0.72rem', color: '#67e8f9', fontWeight: 600 }}>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

const nodeTypes: NodeTypes = {
  satellite: SatelliteNode,
  groundStation: GroundStationNode,
  user: UserNode,
  sensor: SensorNode,
  gnss: GNSSNode,
  processing: ProcessingNode,
}

// Default mission architecture
const defaultNodes: Node[] = [
  { id: 'sat1', type: 'satellite', position: { x: 300, y: 20 }, data: { label: 'Spacecraft' } },
  { id: 'gs1', type: 'groundStation', position: { x: 100, y: 200 }, data: { label: 'Ground Station' } },
  { id: 'mcc', type: 'processing', position: { x: 300, y: 200 }, data: { label: 'Mission Control' } },
  { id: 'proc', type: 'processing', position: { x: 500, y: 200 }, data: { label: 'Data Processing' } },
  { id: 'user1', type: 'user', position: { x: 500, y: 380 }, data: { label: 'End Users' } },
]

const defaultEdges: Edge[] = [
  { id: 'e-sat-gs', source: 'sat1', target: 'gs1', label: 'S-band TM/TC', style: { stroke: '#06b6d4' } },
  { id: 'e-sat-proc', source: 'sat1', target: 'proc', label: 'X-band Data', style: { stroke: '#ec4899' } },
  { id: 'e-gs-mcc', source: 'gs1', target: 'mcc', label: 'Ground Network', style: { stroke: '#6b7280' } },
  { id: 'e-proc-user', source: 'proc', target: 'user1', label: 'Data Products', style: { stroke: '#f59e0b' } },
]

// Node palette for adding new nodes
const NODE_PALETTE = [
  { type: 'satellite', label: 'Satellite', color: '#3b82f6' },
  { type: 'groundStation', label: 'Ground Station', color: '#10b981' },
  { type: 'processing', label: 'Processing', color: '#06b6d4' },
  { type: 'user', label: 'User', color: '#f59e0b' },
  { type: 'sensor', label: 'Sensor', color: '#f97316' },
  { type: 'gnss', label: 'GNSS/External', color: '#8b5cf6' },
]

export function MissionArchitectureEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState(defaultNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(defaultEdges)
  const markStale = useDesignStore(s => s.markStale)

  const onConnect = useCallback(
    (connection: Connection) => {
      const label = prompt('Connection label (e.g., "S-band TM/TC", "Data Products"):') || ''
      setEdges(eds => addEdge({ ...connection, label }, eds))
      markStale('architecture')
    },
    [setEdges, markStale],
  )

  const addNode = (type: string, label: string) => {
    const id = `node-${Date.now()}`
    const customLabel = prompt(`Label for new ${label}:`, label) || label
    setNodes(nds => [...nds, {
      id, type,
      position: { x: 200 + Math.random() * 200, y: 100 + Math.random() * 200 },
      data: { label: customLabel },
    }])
    markStale('architecture')
  }

  const deleteSelected = () => {
    setNodes(nds => nds.filter(n => !n.selected))
    setEdges(eds => eds.filter(e => !e.selected))
    markStale('architecture')
  }

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
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          style={{ background: '#0a0e1a' }}
          defaultEdgeOptions={{ style: { strokeWidth: 2, stroke: '#6b7280' }, animated: true }}
        >
          <Controls style={{ button: { background: '#1f2937', color: '#d1d5db', border: '1px solid #374151' } }} />
          <Background color="#374151" gap={20} />
          <MiniMap nodeStrokeWidth={3} style={{ background: '#111827', border: '1px solid #374151' }} />
        </ReactFlow>
      </div>

      {/* Instructions */}
      <div style={{ padding: '0.3rem 0.75rem', borderTop: '1px solid var(--border, #374151)', fontSize: '0.65rem', color: '#6b7280' }}>
        Drag nodes to position. Connect nodes by dragging from a handle (dot) to another. Click a connection to select it. Use toolbar to add/delete.
      </div>
    </div>
  )
}
