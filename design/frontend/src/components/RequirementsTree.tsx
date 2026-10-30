/**
 * RequirementsTree — hierarchical requirement tree view (SCDF-114).
 *
 * Per SPINE_SPEC §6.6. Replaces flat list with a mission→system→subsystem tree.
 * Shows: code, text (truncated), level badge, status pill (green/amber/red/grey).
 * Expand/collapse per node. "Derive child" button on every node.
 */
import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'

interface TreeReq {
  id: string; code: string; text: string; level: string
  parent_id: string | null; status: string
  threshold_param_path?: string; threshold_op?: string; threshold_value?: string
  verification_method?: string; responsible_position?: string
  children?: TreeReq[]
}

const LEVEL_COLORS: Record<string, string> = {
  mission: '#8b5cf6', system: '#3b82f6', subsystem: '#06b6d4',
}

const STATUS_COLORS: Record<string, string> = {
  draft: '#6b7280', approved: '#10b981', violated: '#ef4444', verified: '#3b82f6', retired: '#374151',
}

export function RequirementsTree({ studyId }: { studyId: string | null }) {
  const [requirements, setRequirements] = useState<TreeReq[]>([])
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)

  // Load from API
  useEffect(() => {
    if (!studyId) return
    setLoading(true)
    fetch(`/api/requirements/tree?study_id=${studyId}`)
      .then(r => r.ok ? r.json() : [])
      .then(data => setRequirements(Array.isArray(data) ? data : []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [studyId])

  // Also include generated requirements from the design store
  const genReqs = useDesignStore(s => s.generatedRequirements)
  const storeReqs: TreeReq[] = (Array.isArray(genReqs) ? genReqs : [])
    .filter((r: any) => r.status === 'accepted')
    .map((r: any) => ({
      id: r.id, code: r.id, text: r.text, level: r.level || r.req_type || 'system',
      parent_id: r.parent_id || null, status: 'approved',
      threshold_param_path: undefined, threshold_op: r.operator, threshold_value: String(r.threshold || ''),
      verification_method: r.verification_method,
    }))

  const allReqs = [...requirements, ...storeReqs.filter(sr => !requirements.find(r => r.id === sr.id))]

  // Build tree
  const buildTree = (reqs: TreeReq[]): TreeReq[] => {
    const map = new Map<string, TreeReq & { children: TreeReq[] }>()
    const roots: TreeReq[] = []
    for (const r of reqs) {
      map.set(r.id, { ...r, children: [] })
    }
    for (const r of reqs) {
      const node = map.get(r.id)!
      if (r.parent_id && map.has(r.parent_id)) {
        map.get(r.parent_id)!.children.push(node)
      } else {
        roots.push(node)
      }
    }
    return roots
  }

  const tree = buildTree(allReqs)

  const toggleExpand = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const deriveChild = async (parentId: string) => {
    const text = prompt('Child requirement text:')
    if (!text) return
    try {
      await fetch(`/api/requirements/${parentId}/derive`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, code: `SR-${Date.now().toString(36)}` }),
      })
      // Refresh
      if (studyId) {
        const res = await fetch(`/api/requirements/tree?study_id=${studyId}`)
        if (res.ok) setRequirements(await res.json())
      }
    } catch { /* silent */ }
  }

  if (allReqs.length === 0 && !loading) {
    return (
      <div className="card" style={{ borderLeft: '3px solid #6b7280' }}>
        <h3 style={{ fontSize: '0.85rem', color: '#6b7280' }}>Requirements Tree</h3>
        <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>
          No requirements yet. Generate requirements from the Requirements tab or create them manually.
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.4rem' }}>Requirements Hierarchy</h3>
      <p style={{ fontSize: '0.68rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        {allReqs.length} requirements ({tree.length} roots). Click to expand/collapse.
      </p>
      {tree.map(node => <TreeNode key={node.id} node={node} depth={0} expanded={expanded} onToggle={toggleExpand} onDerive={deriveChild} />)}
    </div>
  )
}

function TreeNode({ node, depth, expanded, onToggle, onDerive }: {
  node: TreeReq & { children?: TreeReq[] }; depth: number
  expanded: Set<string>; onToggle: (id: string) => void; onDerive: (id: string) => void
}) {
  const hasChildren = (node.children?.length || 0) > 0
  const isExpanded = expanded.has(node.id)
  const levelColor = LEVEL_COLORS[node.level] || '#6b7280'
  const statusColor = STATUS_COLORS[node.status] || '#6b7280'

  return (
    <div style={{ marginLeft: depth * 16 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.25rem 0.4rem',
        borderLeft: `2px solid ${levelColor}`, marginBottom: '0.15rem',
        background: depth === 0 ? 'var(--bg-primary, #111827)' : 'transparent',
        borderRadius: '2px', cursor: hasChildren ? 'pointer' : 'default',
      }} onClick={() => hasChildren && onToggle(node.id)}>
        {hasChildren && <span style={{ fontSize: '0.6rem', color: '#6b7280', width: 12 }}>{isExpanded ? '▼' : '▶'}</span>}
        {!hasChildren && <span style={{ width: 12 }} />}
        <span style={{ fontSize: '0.58rem', padding: '0.05rem 0.25rem', borderRadius: '2px', background: `${levelColor}20`, color: levelColor, fontWeight: 600, textTransform: 'uppercase' }}>
          {node.level.slice(0, 3)}
        </span>
        <span style={{ fontSize: '0.65rem', fontFamily: 'monospace', color: '#6b7280' }}>{node.code}</span>
        <span style={{ fontSize: '0.72rem', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {node.text}
        </span>
        <span style={{ fontSize: '0.55rem', padding: '0.05rem 0.2rem', borderRadius: '2px', background: `${statusColor}20`, color: statusColor, fontWeight: 600 }}>
          {node.status}
        </span>
        {node.level !== 'subsystem' && (
          <button onClick={e => { e.stopPropagation(); onDerive(node.id) }}
            style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: '0.6rem', padding: '0 0.2rem' }}
            title="Derive child requirement">+</button>
        )}
      </div>
      {isExpanded && node.children?.map(child => (
        <TreeNode key={child.id} node={child as any} depth={depth + 1} expanded={expanded} onToggle={onToggle} onDerive={onDerive} />
      ))}
    </div>
  )
}
