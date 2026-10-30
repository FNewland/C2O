/**
 * ConflictReviewModal — Forces review of conflicts before proceeding.
 *
 * After convergence detects conflicts, this modal appears requiring the
 * user to resolve, accept risk, or defer each conflict before continuing
 * to edit parameters in the conflicting domains.
 */
import { useState } from 'react'
import { useDesignStore, type CrossDomainConflict } from '../stores/designStore'

type Resolution = 'resolve' | 'accept_risk' | 'defer' | 'pending'

interface ConflictDecision {
  conflictId: string
  resolution: Resolution
  rationale: string
  resolvedBy: string
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444', major: '#f59e0b', minor: '#3b82f6',
}

export function ConflictReviewModal({ onClose }: { onClose: () => void }) {
  const conflicts = useDesignStore(s => s.result?.conflicts || [])
  const [decisions, setDecisions] = useState<Map<string, ConflictDecision>>(new Map())
  const [activeConflict, setActiveConflict] = useState<string | null>(null)
  const [rationale, setRationale] = useState('')

  if (conflicts.length === 0) {
    onClose()
    return null
  }

  const unresolvedCount = conflicts.length - decisions.size
  const allResolved = unresolvedCount === 0

  const handleDecision = (conflictId: string, resolution: Resolution) => {
    setDecisions(prev => {
      const next = new Map(prev)
      next.set(conflictId, {
        conflictId,
        resolution,
        rationale: rationale || `${resolution} by systems engineer`,
        resolvedBy: 'systems_engineer',
      })
      return next
    })
    setActiveConflict(null)
    setRationale('')
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      zIndex: 10000, display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{
        background: 'var(--bg-primary, #111827)', border: '1px solid var(--border, #374151)',
        borderRadius: '8px', width: '90%', maxWidth: '700px', maxHeight: '80vh',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '0.75rem 1rem', borderBottom: '1px solid var(--border, #374151)',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ef4444' }}>
            {conflicts.length} Conflict{conflicts.length !== 1 ? 's' : ''} Detected
          </span>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
            {decisions.size}/{conflicts.length} resolved
          </span>
          {allResolved && (
            <button className="btn btn-sm" onClick={onClose}
              style={{ background: '#10b981', fontSize: '0.75rem' }}>
              Accept & Continue
            </button>
          )}
        </div>

        {/* Conflict list */}
        <div style={{ padding: '0.75rem', overflowY: 'auto', flex: 1 }}>
          <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
            These conflicts were detected during design convergence.
            Each must be resolved, accepted as a risk, or deferred before proceeding.
          </p>

          {conflicts.map(c => {
            const decision = decisions.get(c.id)
            const isActive = activeConflict === c.id
            return (
              <div key={c.id} style={{
                padding: '0.5rem 0.75rem', borderRadius: '6px', marginBottom: '0.4rem',
                background: decision ? 'rgba(16,185,129,0.05)' : 'var(--bg-secondary, #1f2937)',
                border: `1px solid ${decision ? '#10b98140' : SEVERITY_COLORS[c.severity] + '40'}`,
                borderLeft: `3px solid ${decision ? '#10b981' : SEVERITY_COLORS[c.severity]}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.2rem' }}>
                  <span style={{
                    fontSize: '0.6rem', fontWeight: 700, padding: '0.1rem 0.35rem', borderRadius: '3px',
                    textTransform: 'uppercase',
                    background: `${SEVERITY_COLORS[c.severity]}22`, color: SEVERITY_COLORS[c.severity],
                  }}>{c.severity}</span>
                  <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>{c.title}</span>
                  {decision && (
                    <span style={{
                      fontSize: '0.6rem', padding: '0.1rem 0.35rem', borderRadius: '3px',
                      background: 'rgba(16,185,129,0.15)', color: '#10b981', fontWeight: 600,
                    }}>{decision.resolution.replace('_', ' ').toUpperCase()}</span>
                  )}
                </div>
                <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.2rem' }}>
                  {c.description}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#6b7280' }}>
                  {c.domain_a} ({c.param_a}: {c.value_a_str}) vs {c.domain_b} ({c.param_b}: {c.value_b_str})
                </div>

                {!decision && !isActive && (
                  <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.3rem' }}>
                    <button className="btn btn-sm" onClick={() => setActiveConflict(c.id)}
                      style={{ fontSize: '0.68rem', background: '#3b82f6' }}>Review</button>
                  </div>
                )}

                {isActive && (
                  <div style={{
                    marginTop: '0.4rem', padding: '0.4rem', borderRadius: '4px',
                    background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)',
                  }}>
                    {c.resolutions.length > 0 && (
                      <div style={{ fontSize: '0.72rem', color: '#d1d5db', marginBottom: '0.3rem' }}>
                        Suggested resolutions:
                        {c.resolutions.map((r, i) => (
                          <div key={i} style={{ fontSize: '0.68rem', color: '#9ca3af', marginLeft: '0.5rem' }}>
                            - {r.description}: change {r.parameter_to_change} {r.suggested_direction}
                          </div>
                        ))}
                      </div>
                    )}
                    <textarea className="input" value={rationale} onChange={e => setRationale(e.target.value)}
                      placeholder="Rationale (optional)..." rows={2}
                      style={{ width: '100%', fontSize: '0.72rem', marginBottom: '0.3rem' }} />
                    <div style={{ display: 'flex', gap: '0.3rem' }}>
                      <button className="btn btn-sm" onClick={() => handleDecision(c.id, 'resolve')}
                        style={{ background: '#10b981', fontSize: '0.68rem' }}>Resolve</button>
                      <button className="btn btn-sm" onClick={() => handleDecision(c.id, 'accept_risk')}
                        style={{ background: '#8b5cf6', fontSize: '0.68rem' }}>Accept Risk</button>
                      <button className="btn btn-sm" onClick={() => handleDecision(c.id, 'defer')}
                        style={{ background: '#6b7280', fontSize: '0.68rem' }}>Defer</button>
                      <button className="btn btn-sm" onClick={() => setActiveConflict(null)}
                        style={{ background: '#374151', fontSize: '0.68rem' }}>Cancel</button>
                    </div>
                  </div>
                )}

                {decision && (
                  <div style={{ fontSize: '0.68rem', color: '#6b7280', marginTop: '0.2rem' }}>
                    {decision.rationale}
                    <button onClick={() => {
                      setDecisions(prev => { const n = new Map(prev); n.delete(c.id); return n })
                    }} style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: '0.65rem', marginLeft: '0.3rem' }}>
                      Re-evaluate
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Footer */}
        <div style={{
          padding: '0.5rem 1rem', borderTop: '1px solid var(--border, #374151)',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          {!allResolved && (
            <span style={{ fontSize: '0.75rem', color: '#f59e0b' }}>
              {unresolvedCount} conflict{unresolvedCount !== 1 ? 's' : ''} remaining — resolve all to continue
            </span>
          )}
          <span style={{ flex: 1 }} />
          {allResolved && (
            <button className="btn btn-sm" onClick={onClose}
              style={{ background: '#10b981', fontSize: '0.75rem' }}>
              All Resolved — Continue
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
