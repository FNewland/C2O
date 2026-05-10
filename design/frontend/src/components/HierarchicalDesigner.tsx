/**
 * HierarchicalDesigner — drill-down hierarchical block diagram editor.
 *
 * PRIMARY design interface for SpaceCDF. Replaces flat block diagrams with
 * a navigable tree: Mission > Segments > Systems > Subsystems > Components.
 *
 * Double-click any block to drill into its children. Breadcrumb bar for
 * navigation back up. Budget sidebar shows roll-up totals at each level.
 * Equipment browser integration at subsystem level for component selection.
 */
import { useMemo, useCallback, useEffect, useState } from 'react'
import {
  ReactFlow, useNodesState, useEdgesState, Handle, Position, Controls, Background, MiniMap,
  type Node, type Edge, type NodeTypes, type Connection, addEdge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useDesignStore } from '../stores/designStore'
import { useModelStore, type DesignElement } from '../stores/modelStore'
import { EquipmentBrowser } from './EquipmentBrowser'

// ─── Colors by element_type ───
const TYPE_COLORS: Record<string, string> = {
  mission: '#8b5cf6',
  segment: '#3b82f6',
  system: '#06b6d4',
  subsystem: '#10b981',
  component: '#f59e0b',
  logical: '#8b5cf6',
  software: '#a78bfa',
  mode: '#6b7280',
}

// ─── Colors by subsystem_domain ───
const DOMAIN_COLORS: Record<string, string> = {
  power: '#f59e0b', aocs: '#06b6d4', ttc: '#ec4899', link: '#ec4899',
  propulsion: '#f97316', structure: '#84cc16', data: '#8b5cf6', obc: '#8b5cf6',
  thermal: '#ef4444', integration: '#6b7280', payload: '#3b82f6',
  ground_rf: '#0ea5e9', ground_ops: '#10b981',
}

// ─── Element type options for creation ───
const ELEMENT_TYPES = ['segment', 'system', 'subsystem', 'component'] as const

// ─── Custom node component ───
function HierarchyNode({ data }: { data: {
  label: string; elementType: string; color: string;
  mass: number | null; power: number | null; childCount: number;
  domain: string | null; selected?: boolean
}}) {
  const borderColor = data.color
  return (
    <div style={{
      padding: '10px 14px', border: `2px solid ${borderColor}`,
      borderRadius: 8, background: `${borderColor}12`,
      minWidth: 140, maxWidth: 220,
    }}>
      <Handle type="target" position={Position.Top} style={{ background: borderColor }} />

      {/* Type badge */}
      <div style={{
        fontSize: '0.58rem', textTransform: 'uppercase', letterSpacing: '0.06em',
        color: borderColor, fontWeight: 700, marginBottom: '0.2rem',
      }}>
        {data.elementType}
        {data.domain && <span style={{ marginLeft: '0.3rem', opacity: 0.7 }}>/ {data.domain}</span>}
      </div>

      {/* Name */}
      <div style={{
        fontSize: '0.82rem', fontWeight: 600, color: '#e5e7eb',
        marginBottom: '0.3rem', lineHeight: 1.2,
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
      }}>
        {data.label}
      </div>

      {/* Mass / Power summary */}
      <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.65rem', color: '#9ca3af' }}>
        {data.mass !== null && data.mass > 0 && (
          <span style={{ fontFamily: 'monospace' }}>{data.mass.toFixed(2)} kg</span>
        )}
        {data.power !== null && data.power > 0 && (
          <span style={{ fontFamily: 'monospace' }}>{data.power.toFixed(1)} W</span>
        )}
      </div>

      {/* Children indicator */}
      {data.childCount > 0 && (
        <div style={{
          fontSize: '0.6rem', color: '#6b7280', marginTop: '0.25rem',
          borderTop: `1px solid ${borderColor}30`, paddingTop: '0.2rem',
        }}>
          {data.childCount} item{data.childCount !== 1 ? 's' : ''} — double-click to expand
        </div>
      )}

      <Handle type="source" position={Position.Bottom} style={{ background: borderColor }} />
    </div>
  )
}

const nodeTypes: NodeTypes = { hierarchy: HierarchyNode }

// ─── Props ───
interface Props {
  studyId: string | null
  initialElementId?: string | null
}

export function HierarchicalDesigner({ studyId, initialElementId }: Props) {
  // ─── State ───
  const [currentId, setCurrentId] = useState<string | null>(initialElementId || null)
  const [breadcrumbs, setBreadcrumbs] = useState<Array<{ id: string | null; name: string }>>([
    { id: null, name: 'Mission' },
  ])
  const [showEquipment, setShowEquipment] = useState(false)
  const [budgetAllocations, setBudgetAllocations] = useState<Record<string, Record<string, number>>>({})

  // ─── Store ───
  const elements = useModelStore(s => s.elements)
  const interfaces = useModelStore(s => s.interfaces)
  const createElement = useModelStore(s => s.createElement)
  const updateElement = useModelStore(s => s.updateElement)
  const deleteElement = useModelStore(s => s.deleteElement)
  const createInterface = useModelStore(s => s.createInterface)
  const getChildren = useModelStore(s => s.getChildren)
  const getRoots = useModelStore(s => s.getRoots)
  const computeHierarchicalBudget = useModelStore(s => s.computeHierarchicalBudget)
  const loadModel = useModelStore(s => s.loadStudyModel)
  const markStale = useDesignStore(s => s.markStale)
  const generatedRequirements = useDesignStore(s => s.generatedRequirements)

  // Load model on mount
  useEffect(() => {
    if (studyId && elements.size === 0) {
      loadModel(studyId)
    }
  }, [studyId])

  // Initialize breadcrumbs when starting at a specific element
  useEffect(() => {
    if (initialElementId && elements.size > 0) {
      // Build breadcrumb path from root to initialElementId
      const path: Array<{ id: string | null; name: string }> = [{ id: null, name: 'Mission' }]
      let el = elements.get(initialElementId)
      const chain: DesignElement[] = []
      while (el) {
        chain.unshift(el)
        el = el.parent_id ? elements.get(el.parent_id) : undefined
      }
      for (const ancestor of chain) {
        path.push({ id: ancestor.id, name: ancestor.name })
      }
      setBreadcrumbs(path)
      setCurrentId(initialElementId)
    }
  }, [initialElementId, elements.size])

  // ─── Current element info ───
  const currentElement = currentId ? elements.get(currentId) : null

  // ─── Children of current level ───
  const childElements = useMemo(() => {
    const raw = currentId === null ? getRoots() : getChildren(currentId)
    return raw.filter(el => !(el as any).deleted_at && el.element_type !== 'mode')
  }, [currentId, elements])

  // ─── Build ReactFlow nodes ───
  const modelNodes = useMemo(() => {
    const cols = Math.max(3, Math.ceil(Math.sqrt(childElements.length)))
    return childElements.map((el, i): Node => {
      const color = el.subsystem_domain
        ? (DOMAIN_COLORS[el.subsystem_domain] || TYPE_COLORS[el.element_type] || '#6b7280')
        : (TYPE_COLORS[el.element_type] || '#6b7280')

      // Count children for indicator
      const kids = getChildren(el.id).filter(c => !(c as any).deleted_at && c.element_type !== 'mode')

      // Get mass and power — either from element directly or rolled up
      let mass = el.mass_kg
      let power = el.power_avg_w
      if (kids.length > 0) {
        const rolledMass = computeHierarchicalBudget(el.id, 'mass')
        const rolledPower = computeHierarchicalBudget(el.id, 'power')
        if (rolledMass > 0) mass = rolledMass
        if (rolledPower > 0) power = rolledPower
      }

      const col = i % cols
      const row = Math.floor(i / cols)

      return {
        id: el.id,
        type: 'hierarchy',
        position: {
          x: el.diagram_x ?? (80 + col * 220),
          y: el.diagram_y ?? (60 + row * 180),
        },
        data: {
          label: el.name,
          elementType: el.element_type,
          color,
          mass,
          power,
          childCount: kids.length,
          domain: el.subsystem_domain,
        },
      }
    })
  }, [childElements, elements])

  // ─── Build edges from interfaces between children ───
  const modelEdges = useMemo(() => {
    const childIdSet = new Set(childElements.map(c => c.id))
    const edges: Edge[] = []
    for (const iface of interfaces.values()) {
      if (childIdSet.has(iface.from_element_id) && childIdSet.has(iface.to_element_id)) {
        edges.push({
          id: iface.id,
          source: iface.from_element_id,
          target: iface.to_element_id,
          label: iface.diagram_label || iface.name,
          style: { stroke: '#6b7280', strokeWidth: 2 },
          animated: iface.interface_type === 'rf',
        })
      }
    }
    return edges
  }, [interfaces, childElements])

  const [nodes, setNodes, onNodesChange] = useNodesState(modelNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(modelEdges)

  // Sync when model or navigation changes
  useEffect(() => {
    setNodes(modelNodes)
    setEdges(modelEdges)
  }, [modelNodes, modelEdges])

  // ─── Double-click to drill in ───
  const onNodeDoubleClick = useCallback((_event: React.MouseEvent, node: Node) => {
    const el = elements.get(node.id)
    if (!el) return
    // Only drill if element has children (or could have)
    const kids = getChildren(el.id).filter(c => !(c as any).deleted_at)
    if (el.element_type === 'component' && kids.length === 0) return // Leaf — no drill
    setBreadcrumbs(prev => [...prev, { id: el.id, name: el.name }])
    setCurrentId(el.id)
  }, [elements])

  // ─── Connect nodes = create interface ───
  const onConnect = useCallback(async (connection: Connection) => {
    const label = prompt('Connection label (e.g., "Power bus", "Data link"):') || ''
    const ifType = prompt('Interface type (electrical/data/rf/mechanical/thermal/optical):') || 'data'

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

  // ─── Drag stop = update position ───
  const onNodeDragStop = useCallback((_: any, node: Node) => {
    if (elements.has(node.id)) {
      updateElement(node.id, { diagram_x: node.position.x, diagram_y: node.position.y } as any)
    }
  }, [elements, updateElement])

  // ─── Add block ───
  const handleAddBlock = async () => {
    const name = prompt('Block name:')
    if (!name) return

    // Suggest element type based on current level
    const suggestedType = currentElement
      ? (currentElement.element_type === 'segment' ? 'system'
        : currentElement.element_type === 'system' ? 'subsystem'
        : currentElement.element_type === 'subsystem' ? 'component'
        : 'system')
      : 'segment'

    const typeInput = prompt(
      `Element type (${ELEMENT_TYPES.join('/')}):`,
      suggestedType
    )
    if (!typeInput) return
    const elementType = ELEMENT_TYPES.includes(typeInput as any) ? typeInput : suggestedType

    // Optional domain for subsystems
    let domain: string | null = null
    if (elementType === 'subsystem') {
      domain = prompt('Subsystem domain (power/aocs/ttc/thermal/structure/propulsion/obc/payload):') || null
    }

    if (studyId) {
      const id = await createElement(studyId, {
        name,
        element_type: elementType,
        parent_id: currentId,
        subsystem_domain: domain,
        segment: currentElement?.segment || 'space',
        diagram_x: 100 + Math.random() * 300,
        diagram_y: 80 + Math.random() * 200,
      } as any)
      if (id) markStale('architecture')
    }
  }

  // ─── Delete selected ───
  const handleDeleteSelected = async () => {
    const selectedNodeIds = nodes.filter(n => n.selected).map(n => n.id)
    if (selectedNodeIds.length === 0) return
    if (!confirm(`Delete ${selectedNodeIds.length} element(s)? This also removes their children.`)) return

    for (const id of selectedNodeIds) {
      if (elements.has(id)) {
        await deleteElement(id)
      }
    }
    markStale('architecture')
  }

  // ─── Equipment browser integration ───
  const isSubsystemLevel = currentElement?.element_type === 'subsystem'
    || currentElement?.element_type === 'system'

  const modelCreateElement = useModelStore(s => s.createElement)

  const handleEquipmentSelect = async (category: string, component: any) => {
    if (!studyId || !currentId) return

    // Domain mapping
    const domainMap: Record<string, string> = {
      batteries: 'power', solar_cells: 'power', solar_panels: 'power', eps_boards: 'power',
      reaction_wheels: 'aocs', star_trackers: 'aocs', magnetorquers: 'aocs', sun_sensors: 'aocs',
      transponders: 'ttc', antennas: 'ttc',
      obcs: 'obc', gps_receivers: 'obc',
      thrusters: 'propulsion',
      cubesat_structures: 'structure', deployers: 'structure', mechanical_hardware: 'structure', harnesses: 'structure',
      thermal_hardware: 'thermal',
      ground_antennas: 'ground_rf', ground_rf: 'ground_rf',
      ground_baseband: 'ground_rf', ground_software: 'ground_ops', ground_timing: 'ground_ops',
    }
    const domain = domainMap[category] || currentElement?.subsystem_domain || null

    await modelCreateElement(studyId, {
      name: component.name,
      element_type: 'component',
      subsystem_domain: domain,
      segment: currentElement?.segment || 'space',
      parent_id: currentId,
      mass_kg: component.mass_kg || null,
      power_avg_w: component.power_w || null,
      cost_recurring_keur: component.cost_keur || null,
      trl: component.trl || null,
      manufacturer: component.manufacturer || null,
      kb_component_id: component.id || null,
      quantity: 1,
    } as any)

    // Also write to designStore for backward compatibility
    const existing = useDesignStore.getState().selectedEquipment
    const key = `${category}:${component.id || component.name}`
    if (!existing.find(e => `${e.category}:${e.componentId}` === key)) {
      useDesignStore.setState({
        selectedEquipment: [...existing, {
          category, componentId: component.id || component.name,
          name: component.name, mass_kg: component.mass_kg || 0,
          power_w: component.power_w || 0, cost_keur: component.cost_keur || 0,
          quantity: 1,
        }],
      })
    }
    markStale('equipment')
  }

  // ─── Budget sidebar data ───
  const budgetData = useMemo(() => {
    if (!currentId) {
      // At root level, sum all roots
      const roots = getRoots()
      let totalMass = 0, totalPower = 0, totalCost = 0
      for (const r of roots) {
        totalMass += computeHierarchicalBudget(r.id, 'mass')
        totalPower += computeHierarchicalBudget(r.id, 'power')
        totalCost += computeHierarchicalBudget(r.id, 'cost')
      }
      return { mass: totalMass, power: totalPower, cost: totalCost }
    }
    return {
      mass: computeHierarchicalBudget(currentId, 'mass'),
      power: computeHierarchicalBudget(currentId, 'power'),
      cost: computeHierarchicalBudget(currentId, 'cost'),
    }
  }, [currentId, elements])

  // ─── Requirements for current level ───
  const levelRequirements = useMemo(() => {
    if (!currentElement) return generatedRequirements.filter(r => r.level === 'mission' || r.level === 'system')
    return generatedRequirements.filter(r =>
      r.level === currentElement.element_type ||
      r.domain === currentElement.subsystem_domain
    )
  }, [currentElement, generatedRequirements])

  // ─── Budget allocation helpers ───
  const getAllocation = (budgetType: string): number | null => {
    const key = currentId || '__root__'
    return budgetAllocations[key]?.[budgetType] ?? null
  }
  const setAllocation = (budgetType: string, value: number) => {
    const key = currentId || '__root__'
    setBudgetAllocations(prev => ({
      ...prev,
      [key]: { ...(prev[key] || {}), [budgetType]: value },
    }))
  }

  const budgetRows = [
    { label: 'Mass', type: 'mass', unit: 'kg', used: budgetData.mass },
    { label: 'Power', type: 'power', unit: 'W', used: budgetData.power },
    { label: 'Cost', type: 'cost', unit: 'kEUR', used: budgetData.cost },
  ]

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* ─── Breadcrumb bar ─── */}
      <div style={{
        display: 'flex', gap: '0.15rem', padding: '0.4rem 1rem',
        borderBottom: '1px solid #374151', alignItems: 'center', flexWrap: 'wrap',
      }}>
        {breadcrumbs.map((bc, i) => (
          <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.15rem' }}>
            {i > 0 && <span style={{ color: '#4b5563', fontSize: '0.7rem', margin: '0 0.1rem' }}>/</span>}
            <button
              onClick={() => {
                setCurrentId(bc.id)
                setBreadcrumbs(prev => prev.slice(0, i + 1))
              }}
              style={{
                background: i === breadcrumbs.length - 1 ? 'rgba(59,130,246,0.15)' : 'transparent',
                border: i === breadcrumbs.length - 1 ? '1px solid rgba(59,130,246,0.3)' : '1px solid transparent',
                borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.72rem',
                color: i === breadcrumbs.length - 1 ? '#93c5fd' : '#9ca3af',
                cursor: 'pointer', fontWeight: i === breadcrumbs.length - 1 ? 600 : 400,
              }}
            >
              {bc.name}
            </button>
          </span>
        ))}
        {currentElement && (
          <span style={{
            marginLeft: '0.5rem', fontSize: '0.6rem', padding: '0.1rem 0.4rem',
            background: `${TYPE_COLORS[currentElement.element_type] || '#6b7280'}20`,
            border: `1px solid ${TYPE_COLORS[currentElement.element_type] || '#6b7280'}40`,
            borderRadius: '3px', color: TYPE_COLORS[currentElement.element_type] || '#6b7280',
            textTransform: 'uppercase', letterSpacing: '0.04em',
          }}>
            {currentElement.element_type}
          </span>
        )}
      </div>

      {/* ─── Toolbar ─── */}
      <div style={{
        display: 'flex', gap: '0.3rem', padding: '0.35rem 1rem',
        borderBottom: '1px solid #374151', alignItems: 'center',
      }}>
        <button onClick={handleAddBlock} style={{
          padding: '0.22rem 0.6rem', fontSize: '0.7rem', borderRadius: '4px',
          border: '1px solid rgba(59,130,246,0.4)', background: 'rgba(59,130,246,0.1)',
          color: '#93c5fd', cursor: 'pointer',
        }}>
          + Add Block
        </button>
        <button onClick={handleDeleteSelected} style={{
          padding: '0.22rem 0.6rem', fontSize: '0.7rem', borderRadius: '4px',
          border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.1)',
          color: '#ef4444', cursor: 'pointer',
        }}>
          Delete Selected
        </button>
        {isSubsystemLevel && (
          <button onClick={() => setShowEquipment(true)} style={{
            padding: '0.22rem 0.6rem', fontSize: '0.7rem', borderRadius: '4px',
            border: '1px solid rgba(245,158,11,0.4)', background: 'rgba(245,158,11,0.1)',
            color: '#f59e0b', cursor: 'pointer',
          }}>
            + Add Equipment
          </button>
        )}
        <span style={{ flex: 1 }} />
        <span style={{ fontSize: '0.65rem', color: '#6b7280' }}>
          {childElements.length} block{childElements.length !== 1 ? 's' : ''}
          {nodes.filter(n => n.selected).length > 0 && (
            <span style={{ color: '#93c5fd', marginLeft: '0.4rem' }}>
              ({nodes.filter(n => n.selected).length} selected)
            </span>
          )}
        </span>
      </div>

      {/* ─── Main content: diagram + sidebar ─── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Diagram */}
        <div style={{ flex: 1 }}>
          {childElements.length === 0 ? (
            <div style={{
              height: '100%', display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', color: '#6b7280',
            }}>
              <div style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>
                {currentId ? 'No children defined' : 'No elements yet'}
              </div>
              <div style={{ fontSize: '0.75rem', marginBottom: '1rem' }}>
                Click "+ Add Block" to create {currentId ? 'child elements' : 'mission segments'}
              </div>
              {isSubsystemLevel && (
                <button onClick={() => setShowEquipment(true)} style={{
                  padding: '0.4rem 1rem', fontSize: '0.8rem', borderRadius: '6px',
                  border: '1px solid rgba(245,158,11,0.4)', background: 'rgba(245,158,11,0.1)',
                  color: '#f59e0b', cursor: 'pointer',
                }}>
                  Browse Equipment Catalogue
                </button>
              )}
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeDragStop={onNodeDragStop}
              onNodeDoubleClick={onNodeDoubleClick}
              nodeTypes={nodeTypes}
              fitView
              style={{ background: '#0a0e1a' }}
              defaultEdgeOptions={{ style: { strokeWidth: 2, stroke: '#6b7280' }, animated: true }}
            >
              <Controls style={{ button: { background: '#1f2937', color: '#d1d5db', border: '1px solid #374151' } } as any} />
              <Background color="#374151" gap={20} />
              <MiniMap nodeStrokeWidth={3} style={{ background: '#111827', border: '1px solid #374151' }} />
            </ReactFlow>
          )}
        </div>

        {/* ─── Budget + Requirements Sidebar ─── */}
        <div style={{
          width: '210px', borderLeft: '1px solid #374151',
          overflowY: 'auto', flexShrink: 0, padding: '0.5rem',
          background: 'rgba(0,0,0,0.2)',
        }}>
          {/* Current element header */}
          <div style={{
            fontSize: '0.82rem', fontWeight: 600, color: '#e5e7eb',
            marginBottom: '0.15rem',
          }}>
            {currentElement?.name || 'Mission'}
          </div>
          <div style={{
            fontSize: '0.6rem', textTransform: 'uppercase', color: '#6b7280',
            letterSpacing: '0.05em', marginBottom: '0.6rem',
          }}>
            {currentElement?.element_type || 'Root'} Level Budget
          </div>

          {/* Budget rows */}
          {budgetRows.map(row => {
            const allocation = getAllocation(row.type)
            const margin = allocation && allocation > 0
              ? ((allocation - row.used) / allocation) * 100
              : null
            const status = margin === null ? 'undefined'
              : margin < 0 ? 'exceeded'
              : margin < 10 ? 'red'
              : margin < 25 ? 'amber'
              : 'green'
            const statusColor = status === 'green' ? '#10b981'
              : status === 'amber' ? '#f59e0b'
              : status === 'red' || status === 'exceeded' ? '#ef4444'
              : '#6b7280'

            return (
              <div key={row.type} style={{
                marginBottom: '0.5rem', padding: '0.4rem',
                background: 'rgba(255,255,255,0.03)', borderRadius: '4px',
                border: `1px solid ${statusColor}30`,
              }}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  marginBottom: '0.2rem',
                }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#d1d5db' }}>
                    {row.label}
                  </span>
                  {margin !== null && (
                    <span style={{
                      fontSize: '0.58rem', padding: '0.08rem 0.3rem', borderRadius: '3px',
                      background: `${statusColor}20`, color: statusColor, fontWeight: 600,
                    }}>
                      {margin.toFixed(0)}%
                    </span>
                  )}
                </div>
                <div style={{
                  display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem',
                }}>
                  <span style={{ color: '#9ca3af' }}>Used:</span>
                  <span style={{ fontFamily: 'monospace', color: '#d1d5db' }}>
                    {row.used.toFixed(row.type === 'cost' ? 0 : 2)} {row.unit}
                  </span>
                </div>
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  fontSize: '0.68rem', marginTop: '0.15rem',
                }}>
                  <span style={{ color: '#9ca3af' }}>Alloc:</span>
                  <input
                    type="number"
                    step={row.type === 'cost' ? 10 : 0.1}
                    value={allocation ?? ''}
                    placeholder="--"
                    onChange={e => setAllocation(row.type, Number(e.target.value))}
                    style={{
                      width: '70px', background: 'transparent', border: '1px solid #374151',
                      borderRadius: '3px', color: '#d1d5db', fontSize: '0.65rem',
                      textAlign: 'right', padding: '0.1rem 0.25rem', fontFamily: 'monospace',
                    }}
                  />
                </div>
                {/* Progress bar */}
                {allocation && allocation > 0 && (
                  <div style={{
                    height: '3px', background: '#1f2937', borderRadius: '2px',
                    marginTop: '0.25rem', overflow: 'hidden',
                  }}>
                    <div style={{
                      height: '100%', width: `${Math.min(100, (row.used / allocation) * 100)}%`,
                      background: statusColor, borderRadius: '2px',
                      transition: 'width 0.3s ease',
                    }} />
                  </div>
                )}
              </div>
            )
          })}

          {/* ─── Requirements section ─── */}
          <div style={{
            borderTop: '1px solid #374151', paddingTop: '0.5rem', marginTop: '0.3rem',
          }}>
            <div style={{
              fontSize: '0.68rem', fontWeight: 600, color: '#9ca3af',
              textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.3rem',
            }}>
              Requirements ({levelRequirements.length})
            </div>
            {levelRequirements.length === 0 ? (
              <div style={{ fontSize: '0.65rem', color: '#4b5563' }}>
                No requirements at this level
              </div>
            ) : (
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {levelRequirements.slice(0, 20).map(req => {
                  const dotColor = req.status === 'verified' ? '#10b981'
                    : req.status === 'compliant' ? '#3b82f6'
                    : req.status === 'non-compliant' ? '#ef4444'
                    : req.status === 'partial' ? '#f59e0b'
                    : '#6b7280'
                  return (
                    <div key={req.id} style={{
                      display: 'flex', gap: '0.3rem', alignItems: 'flex-start',
                      marginBottom: '0.25rem', fontSize: '0.62rem',
                    }}>
                      <span style={{
                        width: 6, height: 6, borderRadius: '50%', background: dotColor,
                        flexShrink: 0, marginTop: '0.2rem',
                      }} />
                      <span style={{
                        color: '#9ca3af', lineHeight: 1.3,
                        overflow: 'hidden', textOverflow: 'ellipsis',
                        display: '-webkit-box', WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                      } as any}>
                        {req.text}
                      </span>
                    </div>
                  )
                })}
                {levelRequirements.length > 20 && (
                  <div style={{ fontSize: '0.6rem', color: '#4b5563', marginTop: '0.2rem' }}>
                    +{levelRequirements.length - 20} more
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ─── Equipment Browser Modal ─── */}
      {showEquipment && (
        <EquipmentBrowser
          studyId={studyId}
          onClose={() => setShowEquipment(false)}
          onSelect={handleEquipmentSelect}
          mode="modal"
          segment={currentElement?.segment}
        />
      )}
    </div>
  )
}
