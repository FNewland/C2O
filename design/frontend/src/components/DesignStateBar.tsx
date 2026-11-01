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
import { fs } from '../theme/tokens'

export function DesignStateBar({ autoReconverge, onToggleAuto }: {
  autoReconverge?: boolean
  onToggleAuto?: () => void
}) {
  const designStale = useDesignStore(s => s.designStale)
  const lastChangeSource = useDesignStore(s => s.lastChangeSource)
  const isRunning = useDesignStore(s => s.isRunning)
  const result = useDesignStore(s => s.result)
  const pendingConflicts = useDesignStore(s => s.pendingConflicts)
  const runDesign = useDesignStore(s => s.runDesign)

  const conflicts = result?.conflicts || []
  const criticalConflicts = conflicts.filter(c => c.severity === 'critical')

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
      borderBottom: `2px solid ${designStale ? 'var(--status-caution)' : criticalConflicts.length > 0 ? 'var(--status-alarm)' : 'var(--interactive)'}`,
      display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap',
      fontSize: fs.label,
    }}>
      {isRunning && (
        <span style={{ color: 'var(--interactive)', fontWeight: 600 }}>
          Reconverging design...
        </span>
      )}

      {designStale && !isRunning && (
        <>
          <span style={{ color: 'var(--status-caution)', fontWeight: 600 }}>
            Design outdated
          </span>
          <span style={{ color: 'var(--text-2)' }}>
            — {sourceLabels[lastChangeSource] || lastChangeSource} changed since last run
          </span>
          <button className="btn btn-sm" onClick={runDesign}
            style={{ background: autoReconverge ? 'var(--line)' : 'var(--status-caution)', color: autoReconverge ? 'var(--text-2)' : 'var(--on-fill)', fontSize: fs.label, fontWeight: autoReconverge ? 400 : 600 }}>
            {autoReconverge ? 'Force Re-run' : 'Run Design'}
          </button>
          {onToggleAuto && (
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: fs.label, color: 'var(--text-3)', cursor: 'pointer' }}>
              <input type="checkbox" checked={autoReconverge} onChange={onToggleAuto}
                style={{ accentColor: 'var(--interactive)' }} />
              Auto-reconverge
            </label>
          )}
        </>
      )}

      {criticalConflicts.length > 0 && (
        <span style={{ color: 'var(--status-alarm)', fontWeight: 600 }}>
          {criticalConflicts.length} critical conflict{criticalConflicts.length !== 1 ? 's' : ''}: {criticalConflicts.map(c => c.title).join(', ')}
        </span>
      )}

      {!designStale && !isRunning && conflicts.length > 0 && criticalConflicts.length === 0 && (
        <span style={{ color: 'var(--status-caution)' }}>
          {conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''} to review
        </span>
      )}

      {pendingConflicts.length > 0 && !designStale && (
        <span style={{ color: 'var(--text-3)', fontSize: fs.label }}>
          Review conflicts in Interfaces tab
        </span>
      )}
    </div>
  )
}
