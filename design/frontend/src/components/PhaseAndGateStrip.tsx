/**
 * PhaseAndGateStrip — Current design phase + gate criteria status.
 *
 * Shows which ECSS phase the design is in and pass/fail on key gate criteria.
 * Renders below the MarginTower in the app shell.
 */
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'

const PHASES = [
  { id: 'phase_a', label: 'A', name: 'Feasibility' },
  { id: 'phase_b', label: 'B', name: 'Preliminary' },
  { id: 'phase_c', label: 'C', name: 'Detailed' },
  { id: 'phase_d', label: 'D', name: 'AIT' },
]

const GATE_CRITERIA = [
  { id: 'reqs', label: 'Requirements', check: (s: any) => (Array.isArray((s as any).generatedRequirements) ? (s as any).generatedRequirements : []).filter((r: any) => r.status === 'accepted').length >= 3 },
  { id: 'arch', label: 'Architecture', check: (_s: any, elements?: Map<string, any>) => {
    if (!elements) return false
    for (const el of elements.values()) { if (el.element_type === 'subsystem') return true }
    return false
  } },
  { id: 'budgets', label: 'Budgets', check: (s: any) => !!s.result },
  { id: 'equipment', label: 'Equipment', check: (_s: any, elements?: Map<string, any>) => {
    if (!elements) return false
    for (const el of elements.values()) { if (el.element_type === 'component') return true }
    return false
  } },
]

export function PhaseAndGateStrip() {
  const result = useDesignStore(s => s.result)
  const store = useDesignStore()
  const elements = useModelStore(s => s.elements)

  if (!result) return null

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.2rem 0.5rem', background: 'var(--bg-primary, #0a0e1a)', borderBottom: '1px solid var(--border, #374151)', fontSize: '0.65rem' }}>
      <span style={{ color: '#6b7280', marginRight: '0.2rem' }}>Phase:</span>
      {PHASES.map(p => (
        <span key={p.id} style={{
          padding: '0.1rem 0.35rem', borderRadius: '3px', fontWeight: 600,
          background: p.id === 'phase_a' ? '#3b82f620' : '#11182720',
          color: p.id === 'phase_a' ? '#3b82f6' : '#6b7280',
          border: `1px solid ${p.id === 'phase_a' ? '#3b82f640' : '#37415140'}`,
        }} title={p.name}>
          {p.label}
        </span>
      ))}
      <span style={{ color: '#374151', margin: '0 0.2rem' }}>|</span>
      <span style={{ color: '#6b7280' }}>Gate:</span>
      {GATE_CRITERIA.map(g => {
        const pass = g.check(store, elements)
        return (
          <span key={g.id} style={{ color: pass ? '#10b981' : '#6b7280', fontWeight: pass ? 600 : 400 }}>
            {pass ? '\u2713' : '\u25cb'} {g.label}
          </span>
        )
      })}
    </div>
  )
}
