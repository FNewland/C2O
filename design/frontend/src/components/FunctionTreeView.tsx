import { useState, useMemo } from 'react'
import { POSITION_COLOR } from '../constants'

interface FunctionNode {
  id: string; name: string; function_type: string
  parent_function_id: string | null
  objective_ids: string[]; derived_requirement_ids: string[]
  allocated_to: string; performance_criteria: string[]
  level: number
}

// Starter decomposition for demo — in production loaded from backend
const DEMO_FUNCTIONS: FunctionNode[] = [
  { id: 'F-001', name: 'Acquire multispectral imagery', function_type: 'observe', parent_function_id: null, objective_ids: ['obj-1'], derived_requirement_ids: ['REQ-PL-001'], allocated_to: 'payload', performance_criteria: ['GSD <= 10m at nadir', 'SNR >= 100:1'], level: 0 },
  { id: 'F-002', name: 'Point instrument at target', function_type: 'point', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: ['REQ-AOCS-001'], allocated_to: 'aocs', performance_criteria: ['pointing <= 0.1 deg'], level: 1 },
  { id: 'F-003', name: 'Store acquired data onboard', function_type: 'store', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: [], allocated_to: 'data', performance_criteria: ['storage >= 2x daily volume'], level: 1 },
  { id: 'F-004', name: 'Downlink data to ground station', function_type: 'communicate', parent_function_id: 'F-001', objective_ids: ['obj-1'], derived_requirement_ids: ['REQ-TTC-001'], allocated_to: 'link', performance_criteria: ['link margin >= 3 dB', 'daily downlink >= daily generation'], level: 1 },
  { id: 'F-005', name: 'Generate electrical power', function_type: 'power', parent_function_id: null, objective_ids: [], derived_requirement_ids: ['REQ-PWR-001'], allocated_to: 'power', performance_criteria: ['positive power margin in all modes'], level: 0 },
  { id: 'F-006', name: 'Maintain orbit', function_type: 'navigate', parent_function_id: null, objective_ids: [], derived_requirement_ids: [], allocated_to: 'propulsion', performance_criteria: ['delta-V >= total budget'], level: 0 },
  { id: 'F-007', name: 'Maintain thermal environment', function_type: 'protect', parent_function_id: null, objective_ids: [], derived_requirement_ids: [], allocated_to: 'thermal', performance_criteria: ['all components within operating range'], level: 0 },
  { id: 'F-008', name: 'Survive launch environment', function_type: 'launch', parent_function_id: null, objective_ids: [], derived_requirement_ids: [], allocated_to: 'structure', performance_criteria: ['first natural freq > 45 Hz', 'positive MoS under launch loads'], level: 0 },
  { id: 'F-009', name: 'Communicate with ground (TTC)', function_type: 'command', parent_function_id: null, objective_ids: [], derived_requirement_ids: [], allocated_to: 'link', performance_criteria: [], level: 0 },
  { id: 'F-010', name: 'Dispose of spacecraft at end of life', function_type: 'dispose', parent_function_id: null, objective_ids: [], derived_requirement_ids: [], allocated_to: 'propulsion', performance_criteria: ['comply with 25-year rule'], level: 0 },
]

const SUBSYSTEM_COLORS: Record<string, string> = {
  payload: '#10b981', power: '#f59e0b', aocs: '#06b6d4',
  link: '#ec4899', thermal: '#ef4444', structure: '#84cc16',
  propulsion: '#f97316', data: '#8b5cf6',
}

const DOMAIN_OPTIONS = ['payload', 'power', 'aocs', 'link', 'thermal', 'structure', 'propulsion', 'data', 'systems', '']

export function FunctionTreeView() {
  const [functions, setFunctions] = useState<FunctionNode[]>(DEMO_FUNCTIONS)
  const [expanded, setExpanded] = useState<Set<string>>(new Set(DEMO_FUNCTIONS.map(f => f.id)))
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editDomain, setEditDomain] = useState('')
  const [editCriteria, setEditCriteria] = useState('')

  const addFunction = (parentId: string | null) => {
    const newId = `F-${Date.now()}`
    setFunctions(prev => [...prev, {
      id: newId, name: 'New function', function_type: 'observe',
      parent_function_id: parentId, objective_ids: [],
      derived_requirement_ids: [], allocated_to: '',
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
    setEditDomain(f.allocated_to)
    setEditCriteria(f.performance_criteria.join('; '))
  }

  const saveEdit = () => {
    if (!editingId) return
    setFunctions(prev => prev.map(f => f.id === editingId ? {
      ...f, name: editName, allocated_to: editDomain,
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
  const unallocated = functions.filter(f => !f.allocated_to)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Functional Decomposition</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Objective → Function → Subfunction → Requirement. Each leaf function should trace to at least one requirement.
      </p>

      {/* Stats bar */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', fontSize: '0.75rem', alignItems: 'center' }}>
        <span>{functions.length} functions</span>
        <span>{leaves.length} leaves</span>
        <span style={{ color: uncovered.length > 0 ? '#f59e0b' : '#10b981' }}>
          {uncovered.length} uncovered {uncovered.length > 0 && '(need requirements)'}
        </span>
        {unallocated.length > 0 && <span style={{ color: '#ef4444' }}>{unallocated.length} unallocated</span>}
        <span style={{ flex: 1 }} />
        <button className="btn btn-sm" onClick={() => addFunction(null)} style={{ fontSize: '0.7rem' }}>+ Add Function</button>
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
  const color = SUBSYSTEM_COLORS[node.allocated_to] || '#6b7280'

  return (
    <div style={{ marginLeft: depth * 16 }}>
      <div style={{
        display: 'flex', alignItems: 'flex-start', gap: '0.3rem', padding: '0.3rem 0.4rem',
        borderRadius: '4px', marginBottom: '0.2rem',
        background: 'var(--bg-secondary, #1f2937)',
        borderLeft: `3px solid ${color}`,
      }}>
        {hasChildren ? (
          <button onClick={() => toggleExpand(node.id)} style={{
            background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer',
            fontSize: '0.7rem', padding: 0, width: 14, flexShrink: 0, marginTop: '0.15rem',
          }}>
            {isExpanded ? '▼' : '▶'}
          </button>
        ) : (
          <span style={{ width: 14, flexShrink: 0 }} />
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>{node.name}</span>
            {node.allocated_to && (
              <span style={{
                fontSize: '0.6rem', padding: '0 0.3rem', borderRadius: '3px',
                background: `${color}22`, color, fontWeight: 600,
              }}>{node.allocated_to}</span>
            )}
            {isLeaf && !hasCoverage && (
              <span style={{ fontSize: '0.6rem', padding: '0 0.3rem', borderRadius: '3px', background: 'rgba(245,158,11,0.2)', color: '#f59e0b' }}>
                no requirements
              </span>
            )}
            {isLeaf && hasCoverage && (
              <span style={{ fontSize: '0.6rem', padding: '0 0.3rem', borderRadius: '3px', background: 'rgba(16,185,129,0.2)', color: '#10b981' }}>
                {node.derived_requirement_ids.length} req(s)
              </span>
            )}
          </div>
          {node.performance_criteria.length > 0 && (
            <div style={{ fontSize: '0.68rem', color: '#6b7280', marginTop: '0.1rem' }}>
              {node.performance_criteria.join(' · ')}
            </div>
          )}
        </div>
        <span style={{ fontSize: '0.6rem', color: '#6b7280', fontFamily: 'monospace', flexShrink: 0 }}>{node.id}</span>
        {/* Edit/delete buttons */}
        {onStartEdit && editingId !== node.id && (
          <div style={{ display: 'flex', gap: '0.2rem', flexShrink: 0 }}>
            <button onClick={(e) => { e.stopPropagation(); onStartEdit(node) }}
              style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: '0.6rem' }}>edit</button>
            {onAddChild && (
              <button onClick={(e) => { e.stopPropagation(); onAddChild(node.id) }}
                style={{ background: 'none', border: 'none', color: '#10b981', cursor: 'pointer', fontSize: '0.6rem' }}>+sub</button>
            )}
            {onRemove && (
              <button onClick={(e) => { e.stopPropagation(); onRemove(node.id) }}
                style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.6rem' }}>x</button>
            )}
          </div>
        )}
      </div>
      {/* Inline edit form */}
      {editingId === node.id && onEditName && onEditDomain && onEditCriteria && (
        <div style={{ marginLeft: depth * 16 + 20, padding: '0.4rem', background: 'rgba(59,130,246,0.08)', borderRadius: '4px', marginBottom: '0.2rem', border: '1px solid rgba(59,130,246,0.3)' }}>
          <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem' }}>
            <input className="input" value={editName} onChange={e => onEditName(e.target.value)}
              placeholder="Function name (verb-noun)" style={{ flex: 1, fontSize: '0.78rem' }} />
            <select className="select" value={editDomain} onChange={e => onEditDomain(e.target.value)}
              style={{ width: '120px', fontSize: '0.75rem' }}>
              <option value="">Unallocated</option>
              {DOMAIN_OPTIONS.filter(Boolean).map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <input className="input" value={editCriteria} onChange={e => onEditCriteria(e.target.value)}
            placeholder="Performance criteria (semicolon-separated, e.g. GSD <= 10m; SNR >= 100)"
            style={{ width: '100%', fontSize: '0.72rem', marginBottom: '0.3rem' }} />
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            <button className="btn btn-sm" onClick={onSaveEdit} style={{ fontSize: '0.68rem', background: '#10b981' }}>Save</button>
            <button className="btn btn-sm" onClick={onCancelEdit} style={{ fontSize: '0.68rem', background: '#374151' }}>Cancel</button>
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
