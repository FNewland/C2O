/**
 * DesignStateBar — Shows design freshness, pending conflicts, and re-run prompt.
 *
 * Displays at the top of the design area when:
 * - The design is stale (requirements changed since last run)
 * - There are unresolved conflicts
 * - Convergence results need review
 *
 * This is the primary cross-tool connection indicator.
 */
import { useDesignStore } from '../stores/designStore'

export function DesignStateBar() {
  const designStale = useDesignStore(s => s.designStale)
  const lastChangeSource = useDesignStore(s => s.lastChangeSource)
  const isRunning = useDesignStore(s => s.isRunning)
  const result = useDesignStore(s => s.result)
  const pendingConflicts = useDesignStore(s => s.pendingConflicts)
  const runDesign = useDesignStore(s => s.runDesign)

  const conflicts = result?.conflicts || []
  const criticalConflicts = conflicts.filter(c => c.severity === 'critical')
  const warnings = result?.warnings || []

  // Nothing to show if design is fresh and no conflicts
  if (!designStale && criticalConflicts.length === 0 && !isRunning) return null

  const sourceLabels: Record<string, string> = {
    mission_need: 'Mission Need', requirements: 'Requirements', orbit: 'Orbit',
    equipment: 'Equipment', conops: 'ConOps', functions: 'Functions',
  }

  return (
    <div style={{
      padding: '0.4rem 1rem',
      background: designStale ? 'rgba(245,158,11,0.1)' : criticalConflicts.length > 0 ? 'rgba(239,68,68,0.1)' : 'rgba(59,130,246,0.1)',
      borderBottom: `2px solid ${designStale ? '#f59e0b' : criticalConflicts.length > 0 ? '#ef4444' : '#3b82f6'}`,
      display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap',
      fontSize: '0.78rem',
    }}>
      {isRunning && (
        <span style={{ color: '#3b82f6', fontWeight: 600 }}>
          Reconverging design...
        </span>
      )}

      {designStale && !isRunning && (
        <>
          <span style={{ color: '#f59e0b', fontWeight: 600 }}>
            Design outdated
          </span>
          <span style={{ color: '#9ca3af' }}>
            — {sourceLabels[lastChangeSource] || lastChangeSource} changed since last run
          </span>
          <button className="btn btn-sm" onClick={runDesign}
            style={{ background: '#f59e0b', color: '#000', fontSize: '0.72rem', fontWeight: 600 }}>
            Re-run Design
          </button>
        </>
      )}

      {criticalConflicts.length > 0 && (
        <span style={{ color: '#ef4444', fontWeight: 600 }}>
          {criticalConflicts.length} critical conflict{criticalConflicts.length !== 1 ? 's' : ''}: {criticalConflicts.map(c => c.title).join(', ')}
        </span>
      )}

      {!designStale && !isRunning && conflicts.length > 0 && criticalConflicts.length === 0 && (
        <span style={{ color: '#f59e0b' }}>
          {conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''} to review
        </span>
      )}

      {pendingConflicts.length > 0 && !designStale && (
        <span style={{ color: '#6b7280', fontSize: '0.72rem' }}>
          Review conflicts in Interfaces tab
        </span>
      )}
    </div>
  )
}
