/**
 * MaturityOverview — Shows design maturity level for every element in the tree.
 *
 * Colour-coded by maturity: grey=undefined, orange=parametric, amber=estimated,
 * blue=selected, green=specified, emerald=verified.
 * Provides a quick "how complete is this design?" view.
 */
import { useMemo } from 'react'
import { useModelStore, type MaturityLevel } from '../stores/modelStore'
import { fs } from '../theme/tokens'

const MATURITY_ORDER: MaturityLevel[] = ['undefined', 'parametric', 'estimated', 'selected', 'specified', 'verified']

const MATURITY_COLORS: Record<MaturityLevel, string> = {
  undefined: 'var(--text-3)',
  parametric: 'var(--status-caution)',
  estimated: 'var(--status-caution)',
  selected: 'var(--interactive)',
  specified: 'var(--status-ok)',
  verified: 'var(--status-ok)',
}

const MATURITY_LABELS: Record<MaturityLevel, string> = {
  undefined: 'Undefined',
  parametric: 'Parametric',
  estimated: 'Estimated',
  selected: 'Selected',
  specified: 'Specified',
  verified: 'Verified',
}

export function MaturityOverview() {
  const elements = useModelStore(s => s.elements)
  const getElementMaturity = useModelStore(s => s.getElementMaturity)

  const { tree, stats } = useMemo(() => {
    // Build hierarchical maturity view
    const byParent = new Map<string | null, any[]>()

    for (const el of elements.values()) {
      const parentKey = el.parent_id || '__root__'
      if (!byParent.has(parentKey)) byParent.set(parentKey, [])
      byParent.get(parentKey)!.push(el)
    }

    const buildTree = (parentId: string | null): any[] => {
      const children = byParent.get(parentId || '__root__') || []
      return children.map(el => ({
        el,
        maturity: getElementMaturity(el.id),
        children: buildTree(el.id),
      }))
    }

    const tree = buildTree(null)

    // Compute stats
    const counts: Record<MaturityLevel, number> = {
      undefined: 0, parametric: 0, estimated: 0, selected: 0, specified: 0, verified: 0,
    }
    for (const el of elements.values()) {
      const m = getElementMaturity(el.id)
      counts[m.level]++
    }
    const total = elements.size
    const avgCompleteness = total > 0
      ? Math.round(Array.from(elements.values()).reduce((s, el) => s + getElementMaturity(el.id).completeness, 0) / total)
      : 0

    return { tree, stats: { counts, total, avgCompleteness } }
  }, [elements])

  if (elements.size === 0) {
    return (
      <div style={{ padding: '2rem', color: 'var(--text-3)' }}>
        <h3 style={{ fontSize: fs.value, marginBottom: '0.5rem', color: 'var(--text-2)' }}>Design Maturity</h3>
        <p style={{ fontSize: fs.label }}>
          Run a design to populate the element tree. Maturity tracking shows how complete
          each element's definition is — from parametric estimates through to verified hardware.
        </p>
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Design Maturity</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.75rem' }}>
        Element-by-element maturity assessment. Green = fully specified from catalogue.
        Orange = parametric estimate only.
      </p>

      {/* Overall maturity bar */}
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', height: 20, borderRadius: 4, overflow: 'hidden', border: '1px solid var(--line)' }}>
          {MATURITY_ORDER.map(level => {
            const pct = stats.total > 0 ? (stats.counts[level] / stats.total * 100) : 0
            if (pct === 0) return null
            return (
              <div key={level} style={{
                width: `${pct}%`, background: MATURITY_COLORS[level],
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: fs.label, color: 'white', fontWeight: 600, minWidth: pct > 5 ? 'auto' : 0,
              }} title={`${MATURITY_LABELS[level]}: ${stats.counts[level]} (${pct.toFixed(0)}%)`}>
                {pct > 10 ? `${stats.counts[level]}` : ''}
              </div>
            )
          })}
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.35rem', fontSize: fs.label, color: 'var(--text-2)', flexWrap: 'wrap' }}>
          {MATURITY_ORDER.map(level => (
            stats.counts[level] > 0 ? (
              <span key={level} style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: MATURITY_COLORS[level] }} />
                {MATURITY_LABELS[level]}: {stats.counts[level]}
              </span>
            ) : null
          ))}
          <span style={{ marginLeft: 'auto', fontWeight: 600, color: 'var(--text)' }}>
            {stats.avgCompleteness}% complete
          </span>
        </div>
      </div>

      {/* Element tree with maturity indicators */}
      {tree.map(node => (
        <TreeNode key={node.el.id} node={node} depth={0} />
      ))}
    </div>
  )
}

function TreeNode({ node, depth }: { node: any; depth: number }) {
  const { el, maturity, children } = node
  return (
    <div style={{ marginLeft: depth * 16 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.4rem',
        padding: '0.25rem 0.5rem', borderRadius: '4px',
        background: depth === 0 ? 'color-mix(in srgb, var(--text) 3%, transparent)' : 'transparent',
        marginBottom: '0.15rem',
      }}>
        {/* Maturity dot */}
        <span style={{
          width: 10, height: 10, borderRadius: '50%',
          background: maturity.color, flexShrink: 0,
        }} title={maturity.description} />

        {/* Element name */}
        <span style={{ fontSize: fs.label, fontWeight: depth < 2 ? 600 : 400, color: 'var(--text)' }}>
          {el.name}
        </span>

        {/* Type badge */}
        <span style={{
          fontSize: fs.label, padding: '0.05rem 0.3rem', borderRadius: '3px',
          background: 'color-mix(in srgb, var(--text) 5%, transparent)', color: 'var(--text-3)', textTransform: 'uppercase',
        }}>
          {el.element_type}
        </span>

        {/* Maturity label */}
        <span style={{
          fontSize: fs.label, padding: '0.05rem 0.35rem', borderRadius: '3px',
          background: `color-mix(in srgb, ${maturity.color} 13%, transparent)`, color: maturity.color, fontWeight: 500,
        }}>
          {maturity.label}
        </span>

        {/* Completeness bar */}
        {el.element_type === 'component' && (
          <div style={{ width: 40, height: 4, background: 'var(--line)', borderRadius: 2, marginLeft: 'auto' }}>
            <div style={{ width: `${maturity.completeness}%`, height: '100%', background: maturity.color, borderRadius: 2 }} />
          </div>
        )}

        {/* Missing fields */}
        {maturity.missingFields.length > 0 && el.element_type === 'component' && (
          <span style={{ fontSize: fs.label, color: 'var(--status-caution)' }} title={`Missing: ${maturity.missingFields.join(', ')}`}>
            {maturity.missingFields.length} gaps
          </span>
        )}
      </div>

      {/* Children */}
      {children.map((child: any) => (
        <TreeNode key={child.el.id} node={child} depth={depth + 1} />
      ))}
    </div>
  )
}
