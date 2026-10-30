/**
 * ImpactPreview — Shows predicted downstream effects before an edit is accepted.
 *
 * Call with a list of parameter IDs that are about to change.
 * Fetches the impact prediction from the backend and displays:
 * - Which agents will re-run
 * - Which budgets will be affected
 * - A human-readable summary
 */
import { useState, useEffect } from 'react'

interface ImpactData {
  agents_affected: string[]
  affected_domains: string[]
  budget_impacts: string[]
  description: string
  estimated_cascade_depth: number
}

export function useImpactPreview(parameterIds: string[]) {
  const [impact, setImpact] = useState<ImpactData | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (parameterIds.length === 0) { setImpact(null); return }

    let cancelled = false
    setLoading(true)

    fetch('/api/engineering/impact-preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parameter_ids: parameterIds }),
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (!cancelled && data) setImpact(data) })
      .finally(() => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
  }, [parameterIds.join(',')])

  return { impact, loading }
}

const DOMAIN_COLORS: Record<string, string> = {
  orbit: '#3b82f6', payload: '#10b981', power: '#f59e0b', aocs: '#06b6d4',
  thermal: '#ef4444', link: '#ec4899', data: '#8b5cf6', propulsion: '#f97316',
  structure: '#84cc16', mass: '#d1d5db', cost: '#a855f7',
}

export function ImpactPreviewBanner({ parameterIds, onProceed, onCancel }: {
  parameterIds: string[]
  onProceed: () => void
  onCancel: () => void
}) {
  const { impact, loading } = useImpactPreview(parameterIds)

  if (loading) {
    return (
      <div style={{ padding: '0.5rem 0.75rem', background: 'rgba(59,130,246,0.08)', borderRadius: '6px', fontSize: '0.75rem', color: '#3b82f6' }}>
        Analysing impact...
      </div>
    )
  }

  if (!impact) return null

  return (
    <div style={{
      padding: '0.5rem 0.75rem', borderRadius: '6px', marginBottom: '0.5rem',
      background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)',
    }}>
      <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#3b82f6', marginBottom: '0.3rem' }}>
        Impact Preview
      </div>
      <div style={{ fontSize: '0.72rem', color: '#d1d5db', marginBottom: '0.3rem' }}>
        {impact.description}
      </div>

      {impact.budget_impacts.length > 0 && (
        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginBottom: '0.3rem' }}>
          {impact.budget_impacts.map(b => (
            <span key={b} style={{
              fontSize: '0.65rem', padding: '0.1rem 0.4rem', borderRadius: '3px',
              background: 'rgba(245,158,11,0.15)', color: '#f59e0b',
            }}>{b}</span>
          ))}
        </div>
      )}

      {impact.affected_domains.length > 0 && (
        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap', marginBottom: '0.4rem' }}>
          {impact.affected_domains.map(d => (
            <span key={d} style={{
              fontSize: '0.6rem', padding: '0.1rem 0.3rem', borderRadius: '3px',
              background: `${DOMAIN_COLORS[d] || '#6b7280'}22`, color: DOMAIN_COLORS[d] || '#6b7280',
            }}>{d}</span>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: '0.3rem' }}>
        <button className="btn btn-sm" onClick={onProceed}
          style={{ background: '#10b981', fontSize: '0.68rem' }}>Accept & Re-converge</button>
        <button className="btn btn-sm" onClick={onCancel}
          style={{ background: '#374151', fontSize: '0.68rem' }}>Cancel</button>
      </div>
    </div>
  )
}
