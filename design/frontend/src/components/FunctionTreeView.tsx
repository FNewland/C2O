import { useState, useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'

interface FunctionNode {
  id: string; name: string; function_type: string
  parent_function_id: string | null
  objective_ids: string[]; derived_requirement_ids: string[]
  allocated_to: string[]; performance_criteria: string[]
  level: number
}

// Mission-type-aware starter functions
function getDemoFunctions(missionType: string): FunctionNode[] {
  // Universal functions (all missions)
  const universal: FunctionNode[] = [
    { id: 'F-005', name: 'Generate electrical power', function_type: 'power', parent_function_id: null, objective_ids: [], derived_requirement_ids: ['REQ-PWR-001'], allocated_to: ['power'], performance_criteria: ['positive power margin in all modes'], level: 0 },
    { id: 'F-007', name: 'Maintain thermal environment', function_type: 'protect', parent_function_id: null, objective_ids: [], derived_requirement_ids: [], allocated_to: ['thermal'], performance_criteria: ['all components within operating range'], level: 0 },
    { id: 'F-008', name: 'Survive launch environment', function_type: 'launch', parent_function_id: null, objective_ids: [], derived_requirement_ids: [], allocated_to: ['structure'], performance_criteria: ['first natural freq > 45 Hz'], level: 0 },
    { id: 'F-009', name: 'Communicate with ground (TTC)', function_type: 'command', parent_function_id: null, objective_ids: [], derived_requirement_ids: [], allocated_to: ['communications'], performance_criteria: [], level: 0 },
    { id: 'F-010', name: 'Dispose of spacecraft at end of life', function_type: 'dispose', parent_function_id: null, objective_ids: [], derived_requirement_ids: [], allocated_to: ['structure'], performance_criteria: ['comply with debris mitigation rules'], level: 0 },
  ]

  // Mission-specific primary function
  if (missionType === 'earth_observation' || missionType === 'science_planetary') {
    return [
      { id: 'F-001', name: 'Acquire imagery of target', function_type: 'observe', parent_function_id: null, objective_ids: ['obj-1'], derived_requirement_ids: ['REQ-PL-001'], allocated_to: ['payload'], performance_criteria: ['GSD meets requirement', 'SNR >= threshold'], level: 0 },
      { id: 'F-002', name: 'Point instrument at target', function_type: 'point', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: ['REQ-AOCS-001'], allocated_to: ['aocs'], performance_criteria: ['pointing meets requirement'], level: 1 },
      { id: 'F-003', name: 'Store acquired data onboard', function_type: 'store', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: ['data'], performance_criteria: ['storage >= 2x daily volume'], level: 1 },
      { id: 'F-004', name: 'Downlink data to ground station', function_type: 'communicate', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: ['REQ-TTC-001'], allocated_to: ['communications'], performance_criteria: ['link margin >= 3 dB'], level: 1 },
      ...universal,
    ]
  } else if (missionType === 'communications' || missionType === 'rf_relay') {
    return [
      { id: 'F-001', name: 'Relay communications between users', function_type: 'communicate', parent_function_id: null, objective_ids: ['obj-1'], derived_requirement_ids: ['REQ-PL-001'], allocated_to: ['payload', 'link'], performance_criteria: ['data rate meets requirement', 'latency meets requirement'], level: 0 },
      { id: 'F-002', name: 'Receive uplink signal', function_type: 'communicate', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: ['payload'], performance_criteria: ['receiver sensitivity meets requirement'], level: 1 },
      { id: 'F-003', name: 'Process and route data', function_type: 'store', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: ['data'], performance_criteria: ['processing latency < threshold'], level: 1 },
      { id: 'F-004', name: 'Transmit downlink signal', function_type: 'communicate', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: ['communications'], performance_criteria: ['EIRP meets link budget'], level: 1 },
      ...universal,
    ]
  } else if (missionType === 'sar') {
    return [
      { id: 'F-001', name: 'Acquire SAR imagery', function_type: 'observe', parent_function_id: null, objective_ids: ['obj-1'], derived_requirement_ids: ['REQ-PL-001'], allocated_to: ['payload'], performance_criteria: ['resolution meets requirement', 'swath meets requirement'], level: 0 },
      { id: 'F-002', name: 'Point antenna at target', function_type: 'point', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: ['aocs'], performance_criteria: ['pointing meets SAR geometry'], level: 1 },
      { id: 'F-003', name: 'Store SAR data onboard', function_type: 'store', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: ['data'], performance_criteria: ['storage >= daily SAR volume'], level: 1 },
      { id: 'F-004', name: 'Downlink SAR data', function_type: 'communicate', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: ['communications'], performance_criteria: ['X-band link margin >= 3 dB'], level: 1 },
      ...universal,
    ]
  } else {
    // Technology demo, AIS, generic
    return [
      { id: 'F-001', name: 'Operate mission payload', function_type: 'observe', parent_function_id: null, objective_ids: ['obj-1'], derived_requirement_ids: ['REQ-PL-001'], allocated_to: ['payload'], performance_criteria: ['payload performance meets requirement'], level: 0 },
      { id: 'F-003', name: 'Store mission data onboard', function_type: 'store', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: ['data'], performance_criteria: ['storage sufficient'], level: 1 },
      { id: 'F-004', name: 'Downlink data to ground', function_type: 'communicate', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: ['communications'], performance_criteria: ['link margin >= 3 dB'], level: 1 },
      ...universal,
    ]
  }
}

const SUBSYSTEM_COLORS: Record<string, string> = {
  payload: 'var(--status-ok)', power: 'var(--status-caution)', aocs: 'var(--interactive)',
  link: 'var(--cat-6)', communications: 'var(--cat-6)', thermal: 'var(--status-alarm)', structure: 'var(--cat-7)',
  propulsion: 'var(--status-caution)', data: 'var(--cat-2)',
  ground_station: 'var(--cat-3)', ground_processing: 'var(--cat-2)', ground_sensor: 'var(--status-caution)',
  systems: 'var(--text-3)',
}

const DOMAIN_OPTIONS = [
  'payload', 'power', 'aocs', 'communications', 'thermal', 'structure', 'propulsion', 'data', 'systems',
  'ground_station', 'ground_processing', 'ground_sensor', '',
]

export function FunctionTreeView() {
  const missionType = useDesignStore(s => s.requirements?.mission_type ?? 'earth_observation')
  const [functions, setFunctionsLocal] = useState<FunctionNode[]>(() => getDemoFunctions(missionType))
  // Sync functions to store for cross-component access (requirement linking)
  const setFunctions = (updater: FunctionNode[] | ((prev: FunctionNode[]) => FunctionNode[])) => {
    setFunctionsLocal(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      useDesignStore.setState({ functionsList: next.map(f => ({ id: f.id, name: f.name, allocated_to: f.allocated_to })) })
      return next
    })
  }
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set(getDemoFunctions(missionType).map(f => f.id)))
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editDomain, setEditDomain] = useState('')
  const [editCriteria, setEditCriteria] = useState('')

  const addFunction = (parentId: string | null) => {
    const newId = `F-${Date.now()}`
    setFunctions(prev => [...prev, {
      id: newId, name: 'New function', function_type: 'observe',
      parent_function_id: parentId, objective_ids: [],
      derived_requirement_ids: [], allocated_to: [],
      performance_criteria: [], level: parentId ? 1 : 0,
    }])
    setExpanded(prev => new Set([...prev, newId]))
  }

  const removeFunction = (id: string) => {
    setFunctions(prev => prev.filter(f => f.id !== id && f.parent_function_id !== id))
  }

  const startEdit = (f: FunctionNode) => {
    setEditingId(f.id)
    setEditName(f.name)
    setEditDomain(Array.isArray(f.allocated_to) ? f.allocated_to.join(', ') : f.allocated_to)
    setEditCriteria(f.performance_criteria.join('; '))
  }

  const saveEdit = () => {
    if (!editingId) return
    setFunctions(prev => prev.map(f => f.id === editingId ? {
      ...f, name: editName, allocated_to: editDomain.split(',').map(s => s.trim()).filter(Boolean),
      performance_criteria: editCriteria.split(';').map(c => c.trim()).filter(Boolean),
    } : f))
    setEditingId(null)
  }

  const roots = useMemo(() => functions.filter(f => !f.parent_function_id), [functions])

  const getChildren = (parentId: string) => functions.filter(f => f.parent_function_id === parentId)

  const toggleExpand = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  // Stats
  const leaves = functions.filter(f => !functions.some(c => c.parent_function_id === f.id))
  const uncovered = leaves.filter(f => f.derived_requirement_ids.length === 0)
  const unallocated = functions.filter(f => !f.allocated_to || (Array.isArray(f.allocated_to) && f.allocated_to.length === 0))

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Functional Decomposition</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.75rem' }}>
        Objective → Function → Subfunction → Requirement. Each leaf function should trace to at least one requirement.
      </p>

      {/* Stats bar */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', fontSize: fs.label, alignItems: 'center' }}>
        <span>{functions.length} functions</span>
        <span>{leaves.length} leaves</span>
        <span style={{ color: uncovered.length > 0 ? 'var(--status-caution)' : 'var(--status-ok)' }}>
          {uncovered.length} uncovered {uncovered.length > 0 && '(need requirements)'}
        </span>
        {unallocated.length > 0 && <span style={{ color: 'var(--status-alarm)' }}>{unallocated.length} unallocated</span>}
        <span style={{ flex: 1 }} />
        <button className="btn btn-sm" onClick={() => addFunction(null)} style={{ fontSize: fs.label }}>+ Add Function</button>
      </div>

      {/* Tree */}
      {roots.map(root => (
        <FunctionNodeView key={root.id} node={root} depth={0}
          getChildren={getChildren} expanded={expanded} toggleExpand={toggleExpand}
          allFunctions={functions}
          editingId={editingId} editName={editName} editDomain={editDomain} editCriteria={editCriteria}
          onStartEdit={startEdit} onSaveEdit={saveEdit} onCancelEdit={() => setEditingId(null)}
          onEditName={setEditName} onEditDomain={setEditDomain} onEditCriteria={setEditCriteria}
          onAddChild={(parentId) => addFunction(parentId)} onRemove={removeFunction}
        />
      ))}
    </div>
  )
}

function FunctionNodeView({ node, depth, getChildren, expanded, toggleExpand, allFunctions,
  editingId, editName, editDomain, editCriteria,
  onStartEdit, onSaveEdit, onCancelEdit, onEditName, onEditDomain, onEditCriteria,
  onAddChild, onRemove,
}: {
  node: FunctionNode; depth: number
  getChildren: (id: string) => FunctionNode[]
  expanded: Set<string>; toggleExpand: (id: string) => void
  allFunctions: FunctionNode[]
  editingId?: string | null; editName?: string; editDomain?: string; editCriteria?: string
  onStartEdit?: (f: FunctionNode) => void; onSaveEdit?: () => void; onCancelEdit?: () => void
  onEditName?: (n: string) => void; onEditDomain?: (d: string) => void; onEditCriteria?: (c: string) => void
  onAddChild?: (parentId: string) => void; onRemove?: (id: string) => void
}) {
  const children = getChildren(node.id)
  const hasChildren = children.length > 0
  const isExpanded = expanded.has(node.id)
  const isLeaf = !hasChildren
  const hasCoverage = node.derived_requirement_ids.length > 0
  const allocList = Array.isArray(node.allocated_to) ? node.allocated_to : [node.allocated_to].filter(Boolean)
  const color = SUBSYSTEM_COLORS[allocList[0]] || 'var(--text-3)'

  return (
    <div style={{ marginLeft: depth * 16 }}>
      <div style={{
        display: 'flex', alignItems: 'flex-start', gap: '0.3rem', padding: '0.3rem 0.4rem',
        borderRadius: '4px', marginBottom: '0.2rem',
        background: 'var(--bg-secondary, var(--surface-2))',
        borderLeft: `3px solid ${color}`,
      }}>
        {hasChildren ? (
          <button onClick={() => toggleExpand(node.id)} style={{
            background: 'none', border: 'none', color: 'var(--text-2)', cursor: 'pointer',
            fontSize: fs.label, padding: 0, width: 14, flexShrink: 0, marginTop: '0.15rem',
          }}>
            {isExpanded ? '▼' : '▶'}
          </button>
        ) : (
          <span style={{ width: 14, flexShrink: 0 }} />
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: fs.body, fontWeight: 500 }}>{node.name}</span>
            {allocList.length > 0 && allocList.map(domain => (
              <span key={domain} style={{
                fontSize: fs.label, padding: '0 0.3rem', borderRadius: '3px',
                background: `color-mix(in srgb, ${SUBSYSTEM_COLORS[domain] || 'var(--text-3)'} 13%, transparent)`,
                color: SUBSYSTEM_COLORS[domain] || 'var(--text-3)', fontWeight: 600,
              }}>{domain}</span>
            ))}
            {isLeaf && !hasCoverage && (
              <span style={{ fontSize: fs.label, padding: '0 0.3rem', borderRadius: '3px', background: 'rgba(245,158,11,0.2)', color: 'var(--status-caution)' }}>
                no requirements
              </span>
            )}
            {isLeaf && hasCoverage && (
              <span style={{ fontSize: fs.label, padding: '0 0.3rem', borderRadius: '3px', background: 'rgba(16,185,129,0.2)', color: 'var(--status-ok)' }}>
                {node.derived_requirement_ids.length} req(s)
              </span>
            )}
          </div>
          {node.performance_criteria.length > 0 && (
            <div style={{ fontSize: fs.label, color: 'var(--text-3)', marginTop: '0.1rem' }}>
              {node.performance_criteria.join(' · ')}
            </div>
          )}
        </div>
        <span style={{ fontSize: fs.label, color: 'var(--text-3)', fontFamily: 'monospace', flexShrink: 0 }}>{node.id}</span>
        {/* Edit/delete buttons */}
        {onStartEdit && editingId !== node.id && (
          <div style={{ display: 'flex', gap: '0.2rem', flexShrink: 0 }}>
            <button onClick={(e) => { e.stopPropagation(); onStartEdit(node) }}
              style={{ background: 'none', border: 'none', color: 'var(--interactive)', cursor: 'pointer', fontSize: fs.label }}>edit</button>
            {onAddChild && (
              <button onClick={(e) => { e.stopPropagation(); onAddChild(node.id) }}
                style={{ background: 'none', border: 'none', color: 'var(--status-ok)', cursor: 'pointer', fontSize: fs.label }}>+sub</button>
            )}
            {onRemove && (
              <button onClick={(e) => { e.stopPropagation(); onRemove(node.id) }}
                style={{ background: 'none', border: 'none', color: 'var(--status-alarm)', cursor: 'pointer', fontSize: fs.label }}>x</button>
            )}
          </div>
        )}
      </div>
      {/* Inline edit form */}
      {editingId === node.id && onEditName && onEditDomain && onEditCriteria && (
        <div style={{ marginLeft: depth * 16 + 20, padding: '0.4rem', background: 'rgba(59,130,246,0.08)', borderRadius: '4px', marginBottom: '0.2rem', border: '1px solid rgba(59,130,246,0.3)' }}>
          <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem' }}>
            <input className="input" value={editName} onChange={e => onEditName(e.target.value)}
              placeholder="Function name (verb-noun)" style={{ flex: 1, fontSize: fs.label }} />
            <select className="select" value={editDomain} onChange={e => onEditDomain(e.target.value)}
              style={{ width: '120px', fontSize: fs.label }}>
              <option value="">Unallocated</option>
              {DOMAIN_OPTIONS.filter(Boolean).map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <input className="input" value={editCriteria} onChange={e => onEditCriteria(e.target.value)}
            placeholder="Performance criteria (semicolon-separated, e.g. GSD <= 10m; SNR >= 100)"
            style={{ width: '100%', fontSize: fs.label, marginBottom: '0.3rem' }} />
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            <button className="btn btn-sm" onClick={onSaveEdit} style={{ fontSize: fs.label, background: 'var(--status-ok)' }}>Save</button>
            <button className="btn btn-sm" onClick={onCancelEdit} style={{ fontSize: fs.label, background: 'var(--line)' }}>Cancel</button>
          </div>
        </div>
      )}
      {isExpanded && children.map(child => (
        <FunctionNodeView key={child.id} node={child} depth={depth + 1}
          getChildren={getChildren} expanded={expanded} toggleExpand={toggleExpand}
          allFunctions={allFunctions}
          editingId={editingId} editName={editName} editDomain={editDomain} editCriteria={editCriteria}
          onStartEdit={onStartEdit} onSaveEdit={onSaveEdit} onCancelEdit={onCancelEdit}
          onEditName={onEditName} onEditDomain={onEditDomain} onEditCriteria={onEditCriteria}
          onAddChild={onAddChild} onRemove={onRemove}
        />
      ))}
    </div>
  )
}
