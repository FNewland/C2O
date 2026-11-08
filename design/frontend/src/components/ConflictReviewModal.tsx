/**
 * ConflictReviewModal — Forces review of conflicts before proceeding.
 *
 * After convergence detects conflicts, this modal appears requiring the
 * user to resolve, accept risk, or defer each conflict before continuing
 * to edit parameters in the conflicting domains.
 */
import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'
import { serverText } from '../i18n/serverText'

type Resolution = 'resolve' | 'accept_risk' | 'defer' | 'pending'

interface ConflictDecision {
  conflictId: string
  resolution: Resolution
  rationale: string
  resolvedBy: string
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--status-alarm)', major: 'var(--status-caution)', minor: 'var(--interactive)',
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
        background: 'var(--bg-primary, var(--surface-1))', border: '1px solid var(--border, var(--line))',
        borderRadius: '8px', width: '90%', maxWidth: '700px', maxHeight: '80vh',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '0.75rem 1rem', borderBottom: '1px solid var(--border, var(--line))',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          <span style={{ fontSize: fs.title, fontWeight: 700, color: 'var(--status-alarm)' }}>
            {conflicts.length} Conflict{conflicts.length !== 1 ? 's' : ''} Detected
          </span>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: fs.label, color: 'var(--text-2)' }}>
            {decisions.size}/{conflicts.length} resolved
          </span>
          {allResolved && (
            <button className="btn btn-sm" onClick={onClose}
              style={{ background: 'var(--status-ok)', fontSize: fs.label }}>
              Accept & Continue
            </button>
          )}
        </div>

        {/* Conflict list */}
        <div style={{ padding: '0.75rem', overflowY: 'auto', flex: 1 }}>
          <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.75rem' }}>
            These conflicts were detected during design convergence.
            Each must be resolved, accepted as a risk, or deferred before proceeding.
          </p>

          {conflicts.map(c => {
            const decision = decisions.get(c.id)
            const isActive = activeConflict === c.id
            return (
              <div key={c.id} style={{
                padding: '0.5rem 0.75rem', borderRadius: '6px', marginBottom: '0.4rem',
                background: decision ? 'rgba(16,185,129,0.05)' : 'var(--bg-secondary, var(--surface-2))',
                border: `1px solid ${decision ? 'color-mix(in srgb, var(--status-ok) 25%, transparent)' : `color-mix(in srgb, ${SEVERITY_COLORS[c.severity]} 25%, transparent)`}`,
                borderLeft: `3px solid ${decision ? 'var(--status-ok)' : SEVERITY_COLORS[c.severity]}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.2rem' }}>
                  <span style={{
                    fontSize: fs.label, fontWeight: 700, padding: '0.1rem 0.35rem', borderRadius: '3px',
                    textTransform: 'uppercase',
                    background: `color-mix(in srgb, ${SEVERITY_COLORS[c.severity]} 13%, transparent)`, color: SEVERITY_COLORS[c.severity],
                  }}>{c.severity}</span>
                  <span style={{ fontSize: fs.body, fontWeight: 600 }}>{serverText(c.title)}</span>
                  {decision && (
                    <span style={{
                      fontSize: fs.label, padding: '0.1rem 0.35rem', borderRadius: '3px',
                      background: 'rgba(16,185,129,0.15)', color: 'var(--status-ok)', fontWeight: 600,
                    }}>{decision.resolution.replace('_', ' ').toUpperCase()}</span>
                  )}
                </div>
                <div style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.2rem' }}>
                  {serverText(c.description)}
                </div>
                <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>
                  {c.domain_a} ({c.param_a}: {c.value_a_str}) vs {c.domain_b} ({c.param_b}: {c.value_b_str})
                </div>

                {!decision && !isActive && (
                  <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.3rem' }}>
                    <button className="btn btn-sm" onClick={() => setActiveConflict(c.id)}
                      style={{ fontSize: fs.label, background: 'var(--interactive)' }}>Review</button>
                  </div>
                )}

                {isActive && (
                  <div style={{
                    marginTop: '0.4rem', padding: '0.4rem', borderRadius: '4px',
                    background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)',
                  }}>
                    {c.resolutions.length > 0 && (
                      <div style={{ fontSize: fs.label, color: 'var(--text)', marginBottom: '0.3rem' }}>
                        Suggested resolutions:
                        {c.resolutions.map((r, i) => (
                          <div key={i} style={{ fontSize: fs.label, color: 'var(--text-2)', marginLeft: '0.5rem' }}>
                            - {serverText(r.description)}: change {r.parameter_to_change} {r.suggested_direction}
                          </div>
                        ))}
                      </div>
                    )}
                    <textarea className="input" value={rationale} onChange={e => setRationale(e.target.value)}
                      placeholder="Rationale (optional)..." rows={2}
                      style={{ width: '100%', fontSize: fs.label, marginBottom: '0.3rem' }} />
                    <div style={{ display: 'flex', gap: '0.3rem' }}>
                      <button className="btn btn-sm" onClick={() => handleDecision(c.id, 'resolve')}
                        style={{ background: 'var(--status-ok)', fontSize: fs.label }}>Resolve</button>
                      <button className="btn btn-sm" onClick={() => handleDecision(c.id, 'accept_risk')}
                        style={{ background: 'var(--cat-2)', fontSize: fs.label }}>Accept Risk</button>
                      <button className="btn btn-sm" onClick={() => handleDecision(c.id, 'defer')}
                        style={{ background: 'var(--text-3)', fontSize: fs.label }}>Defer</button>
                      <button className="btn btn-sm" onClick={() => setActiveConflict(null)}
                        style={{ background: 'var(--line)', fontSize: fs.label }}>Cancel</button>
                    </div>
                  </div>
                )}

                {decision && (
                  <div style={{ fontSize: fs.label, color: 'var(--text-3)', marginTop: '0.2rem' }}>
                    {decision.rationale}
                    <button onClick={() => {
                      setDecisions(prev => { const n = new Map(prev); n.delete(c.id); return n })
                    }} style={{ background: 'none', border: 'none', color: 'var(--interactive)', cursor: 'pointer', fontSize: fs.label, marginLeft: '0.3rem' }}>
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
          padding: '0.5rem 1rem', borderTop: '1px solid var(--border, var(--line))',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          {!allResolved && (
            <span style={{ fontSize: fs.label, color: 'var(--status-caution)' }}>
              {unresolvedCount} conflict{unresolvedCount !== 1 ? 's' : ''} remaining — resolve all to continue
            </span>
          )}
          <span style={{ flex: 1 }} />
          {allResolved && (
            <button className="btn btn-sm" onClick={onClose}
              style={{ background: 'var(--status-ok)', fontSize: fs.label }}>
              All Resolved — Continue
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
