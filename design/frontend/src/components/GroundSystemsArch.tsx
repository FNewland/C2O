/**
 * GroundSystemsArch — define ground segment systems at Phase 2.
 *
 * Shows the ground systems that need to be designed:
 * - Ground Station Network (per station: antenna, RF, baseband)
 * - Mission Control Centre (TM/TC, FD, planning, infrastructure)
 * - Data Processing Centre (ingest, L0-L2, QC, archive, distribution)
 * - Network Infrastructure (WAN, VPN, timing)
 *
 * Each system creates elements in the model tree as children of the Ground Segment.
 * Supports adding free-form custom ground system blocks via the "Add System" button.
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  ReactFlow, useNodesState, useEdgesState, Handle, Position, Controls, Background,
  type Node, type Edge, type NodeTypes, type Connection, addEdge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'

interface GroundSystem {
  id: string
  name: string
  description: string
  subsystems: string[]
  estimatedCost: string
  selected: boolean
}

const GROUND_SYSTEMS: GroundSystem[] = [
  {
    id: 'gs_network', name: 'Ground Station Network',
    description: 'Antenna systems, RF chains, modems for spacecraft communication',
    subsystems: ['Antenna System', 'RF Chain (TX/RX)', 'Baseband / Modem', 'Tracking Mount', 'Station Infrastructure'],
    estimatedCost: '150-2000 kEUR per station', selected: true,
  },
  {
    id: 'gs_mcc', name: 'Mission Control Centre',
    description: 'Telemetry processing, commanding, flight dynamics, mission planning',
    subsystems: ['TM Processing', 'TC Generation', 'Flight Dynamics', 'Mission Planning', 'Anomaly Management', 'IT Infrastructure'],
    estimatedCost: '200-1000 kEUR', selected: true,
  },
  {
    id: 'gs_dataproc', name: 'Data Processing Centre',
    description: 'Payload data reception, processing pipeline (L0→L1→L2), quality control, archive',
    subsystems: ['Data Ingest', 'L0 Processing', 'L1/L2 Processing', 'Quality Control', 'Archive & Catalogue', 'Distribution Services'],
    estimatedCost: '100-500 kEUR', selected: true,
  },
  {
    id: 'gs_network_infra', name: 'Network Infrastructure',
    description: 'WAN connectivity between stations and MCC, VPN, timing distribution',
    subsystems: ['WAN / Fibre', 'VPN / Security', 'Time Distribution (GPS-DO)', 'Monitoring'],
    estimatedCost: '50-200 kEUR', selected: false,
  },
  {
    id: 'gs_user_services', name: 'User Services',
    description: 'Data portal, API, user accounts, SLA management',
    subsystems: ['Web Portal', 'Data API', 'User Management', 'SLA Monitoring'],
    estimatedCost: '50-300 kEUR', selected: false,
  },
]

const GROUND_SYSTEM_COLORS = [
  '#10b981', '#d946ef', '#14b8a6', '#6b7280', '#f59e0b',
  '#06b6d4', '#8b5cf6', '#ef4444', '#84cc16', '#ec4899',
]

// Ground system block node
function GroundBlockNode({ data }: { data: { label: string; color: string; subsystems?: string[] } }) {
  return (
    <div style={{
      padding: '8px 14px', border: `2px solid ${data.color}`, borderRadius: 8,
      background: `${data.color}15`, textAlign: 'center', minWidth: 130,
    }}>
      <Handle type="target" position={Position.Top} />
      <Handle type="target" position={Position.Left} id="left" />
      <div style={{ fontSize: '0.78rem', color: data.color, fontWeight: 700 }}>{data.label}</div>
      {data.subsystems && data.subsystems.length > 0 && (
        <div style={{ fontSize: '0.58rem', color: '#9ca3af', marginTop: '0.2rem', maxWidth: 160 }}>
          {data.subsystems.slice(0, 4).join(' | ')}
          {data.subsystems.length > 4 && ` +${data.subsystems.length - 4}`}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} id="right" />
    </div>
  )
}

const nodeTypes: NodeTypes = { groundBlock: GroundBlockNode }

export function GroundSystemsArch() {
  const studyId = useDesignStore(s => s.studyId)
  const createElement = useModelStore(s => s.createElement)
  const elements = useModelStore(s => s.elements)
  const updateElement = useModelStore(s => s.updateElement)
  const [systems, setSystems] = useState(GROUND_SYSTEMS)
  const [createdIds, setCreatedIds] = useState<Set<string>>(new Set())

  // Check which ground systems already exist in the element tree
  useEffect(() => {
    const existing = new Set<string>()
    for (const el of elements.values()) {
      if (el.segment === 'ground' && el.element_type === 'system') {
        existing.add(el.name)
      }
    }
    if (existing.size > 0) {
      setSystems(prev => prev.map(s => ({ ...s, selected: existing.has(s.name) })))
    }
  }, [elements])

  const toggleSystem = async (sysId: string) => {
    setSystems(prev => prev.map(s => s.id === sysId ? { ...s, selected: !s.selected } : s))

    const sys = systems.find(s => s.id === sysId)
    if (!sys || !studyId) return

    if (!sys.selected && !createdIds.has(sysId)) {
      // Create system element in model tree
      // Find ground segment parent
      let groundParentId: string | undefined
      for (const el of elements.values()) {
        if (el.element_type === 'segment' && el.segment === 'ground') {
          groundParentId = el.id
          break
        }
      }

      const systemId = await createElement(studyId, {
        name: sys.name,
        element_type: 'system',
        segment: 'ground',
        parent_id: groundParentId || null,
        description: sys.description,
        cost_recurring_keur: parseInt(sys.estimatedCost) || null,
      } as any)

      if (systemId) {
        // Create subsystem elements
        for (const sub of sys.subsystems) {
          await createElement(studyId, {
            name: sub,
            element_type: 'subsystem',
            segment: 'ground',
            parent_id: systemId,
            subsystem_domain: 'ground',
          } as any)
        }
        setCreatedIds(prev => new Set([...prev, sysId]))
      }
    }
  }

  // Add custom ground system
  const addCustomSystem = async () => {
    const name = prompt('Enter new ground system name:')
    if (!name || !name.trim() || !studyId) return

    // Find ground segment parent
    let groundParentId: string | undefined
    for (const el of elements.values()) {
      if (el.element_type === 'segment' && el.segment === 'ground') {
        groundParentId = el.id
        break
      }
    }

    await createElement(studyId, {
      name: name.trim(),
      element_type: 'system',
      segment: 'ground',
      parent_id: groundParentId || null,
      description: 'Custom ground system',
    } as any)
  }

  // Build ReactFlow nodes/edges from all ground system elements in modelStore
  const groundSystems = useMemo(() => {
    return Array.from(elements.values()).filter(
      el => el.segment === 'ground' && el.element_type === 'system'
    )
  }, [elements])

  const { diagramNodes, diagramEdges } = useMemo(() => {
    const dNodes: Node[] = groundSystems.map((el, i) => {
      const col = i % 3
      const row = Math.floor(i / 3)
      // Gather subsystem children for display
      const children = Array.from(elements.values()).filter(c => c.parent_id === el.id)
      const subsystemNames = children.slice(0, 6).map((c: any) => c.name)
      return {
        id: `gs-${el.id}`,
        type: 'groundBlock',
        position: {
          x: (el as any).diagram_x ?? (40 + col * 220),
          y: (el as any).diagram_y ?? (30 + row * 140),
        },
        data: {
          label: el.name,
          color: GROUND_SYSTEM_COLORS[i % GROUND_SYSTEM_COLORS.length],
          subsystems: subsystemNames,
        },
      }
    })
    // No automatic edges; users draw them via onConnect
    return { diagramNodes: dNodes, diagramEdges: [] as Edge[] }
  }, [groundSystems, elements])

  const [nodes, setNodes, onNodesChange] = useNodesState(diagramNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(diagramEdges)

  // Sync when diagramNodes changes (new elements added)
  useEffect(() => {
    setNodes(diagramNodes)
  }, [diagramNodes, setNodes])

  const onConnect = useCallback(
    (connection: Connection) => {
      const label = prompt('Interface label:') || ''
      setEdges(eds => addEdge({ ...connection, label }, eds))
    },
    [setEdges],
  )

  // Persist drag positions back to modelStore
  const onNodeDragStop = useCallback(
    (_event: any, node: Node) => {
      if (node.id.startsWith('gs-')) {
        const elementId = node.id.replace('gs-', '')
        updateElement(elementId, {
          diagram_x: Math.round(node.position.x),
          diagram_y: Math.round(node.position.y),
        })
      }
    },
    [updateElement],
  )

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Ground Segment — System Architecture</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Define which ground systems are needed. Each system will be decomposed into subsystems at Phase 3.
      </p>

      {/* System selection cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '0.75rem' }}>
        {systems.map(sys => (
          <div key={sys.id} onClick={() => toggleSystem(sys.id)} style={{
            padding: '0.6rem 0.75rem', borderRadius: '6px', cursor: 'pointer',
            background: sys.selected ? 'rgba(16,185,129,0.08)' : 'var(--bg-secondary, #1f2937)',
            border: `2px solid ${sys.selected ? '#10b981' : '#374151'}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
              <span style={{ width: 16, height: 16, borderRadius: 3, border: `2px solid ${sys.selected ? '#10b981' : '#6b7280'}`, background: sys.selected ? '#10b981' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.6rem', color: 'white' }}>
                {sys.selected ? '✓' : ''}
              </span>
              <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{sys.name}</span>
              <span style={{ flex: 1 }} />
              <span style={{ fontSize: '0.65rem', color: '#6b7280' }}>{sys.estimatedCost}</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.2rem', marginLeft: '1.5rem' }}>
              {sys.description}
            </div>
            <div style={{ fontSize: '0.65rem', color: '#6b7280', marginLeft: '1.5rem' }}>
              Subsystems: {sys.subsystems.join(' · ')}
            </div>
          </div>
        ))}
      </div>

      {/* Add custom system button */}
      <button
        onClick={addCustomSystem}
        style={{
          padding: '0.4rem 0.8rem', fontSize: '0.75rem', borderRadius: '5px',
          background: '#1e3a5f', color: '#60a5fa', border: '1px solid #3b82f6',
          cursor: 'pointer', marginBottom: '0.75rem',
        }}
      >
        + Add Custom System
      </button>

      {/* ReactFlow block diagram of all ground systems from modelStore */}
      <div className="card" style={{ height: '350px' }}>
        <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Ground Segment Block Diagram</h3>
        <div style={{ height: '300px' }}>
          {groundSystems.length > 0 ? (
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
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: '0.8rem' }}>
              Select or add ground systems above to populate the diagram
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
