import { useSessionStore } from '../stores/sessionStore'
import { POSITION_COLOR } from '../constants'
import type { WSStatus } from '../hooks/useSessionSocket'

function initials(positionId: string): string {
  return positionId.split('_').map(p => p[0]).join('').toUpperCase().slice(0, 2)
}

function statusDot(status: WSStatus): { color: string; label: string } {
  switch (status) {
    case 'connected': return { color: 'var(--success, #10b981)', label: 'Live' }
    case 'connecting': return { color: 'var(--warning, #f59e0b)', label: 'Connecting' }
    case 'reconnecting': return { color: 'var(--warning, #f59e0b)', label: 'Reconnecting' }
    case 'error': return { color: 'var(--danger, #ef4444)', label: 'Error' }
    default: return { color: 'var(--text-secondary, #6b7280)', label: 'Offline' }
  }
}

export function SessionBar({ wsStatus, onStartSession, onLeaveSession }: {
  wsStatus: WSStatus
  onStartSession: () => void
  onLeaveSession: () => void
}) {
  const sessionId = useSessionStore(s => s.sessionId)
  const positionId = useSessionStore(s => s.positionId)
  const positionIds = useSessionStore(s => s.positionIds)
  const activePositions = useSessionStore(s => s.activePositions)
  const lastConvergence = useSessionStore(s => s.lastConvergence)
  const dot = statusDot(wsStatus)

  if (!sessionId) {
    return (
      <div style={{
        padding: '0.5rem 1rem', background: 'var(--bg-secondary, #1f2937)',
        borderBottom: '1px solid var(--border, #374151)',
        display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.85rem',
      }}>
        <span style={{ color: 'var(--text-secondary, #9ca3af)' }}>
          No active session — run a single-user design or create a session to collaborate
        </span>
        <div style={{ flex: 1 }} />
        <button className="btn btn-sm" onClick={onStartSession}>Start Session</button>
      </div>
    )
  }

  return (
    <div style={{
      padding: '0.5rem 1rem', background: 'var(--bg-secondary, #1f2937)',
      borderBottom: '1px solid var(--border, #374151)',
      display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.85rem', flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{
          width: '8px', height: '8px', borderRadius: '50%',
          background: dot.color, boxShadow: `0 0 6px ${dot.color}`,
        }} />
        <span style={{ color: 'var(--text-secondary, #9ca3af)' }}>{dot.label}</span>
      </div>

      <div style={{ color: 'var(--text-secondary, #9ca3af)' }}>
        Session <strong style={{ color: 'var(--text-primary, #f3f4f6)', fontFamily: 'monospace' }}>{sessionId}</strong>
      </div>

      {positionIds.length > 0 && (
        <div style={{ color: 'var(--text-secondary, #9ca3af)', display: 'flex', alignItems: 'center', gap: '0.3rem', flexWrap: 'wrap' }}>
          <span>You:</span>
          {positionIds.map(pid => (
            <span key={pid} style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
              padding: '0.1rem 0.45rem', borderRadius: '4px', fontSize: '0.75rem',
              background: `${POSITION_COLOR[pid] || '#6b7280'}22`,
              color: POSITION_COLOR[pid] || '#9ca3af',
              fontWeight: 600,
            }}>{pid.replace(/_/g, ' ')}</span>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
        <span style={{ color: 'var(--text-secondary, #9ca3af)', fontSize: '0.75rem' }}>Online:</span>
        <div style={{ display: 'flex', gap: '-0.25rem' }}>
          {activePositions.length === 0 && (
            <span style={{ color: 'var(--text-secondary, #6b7280)', fontSize: '0.75rem', fontStyle: 'italic' }}>none</span>
          )}
          {activePositions.map(pid => (
            <span
              key={pid}
              title={pid.replace(/_/g, ' ')}
              style={{
                width: '24px', height: '24px', borderRadius: '50%',
                background: POSITION_COLOR[pid] || '#6b7280', color: 'white',
                fontSize: '0.65rem', fontWeight: 700,
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                border: '2px solid var(--bg-secondary, #1f2937)',
                marginLeft: '-4px',
              }}
            >{initials(pid)}</span>
          ))}
        </div>
      </div>

      {lastConvergence && (
        <div style={{ color: 'var(--text-secondary, #9ca3af)', fontSize: '0.75rem' }}>
          Last reconv: {lastConvergence.cascadeRounds} rounds, {lastConvergence.timeMs?.toFixed(1)}ms,
          {' '}{lastConvergence.changedParams.length} params
        </div>
      )}

      <div style={{ flex: 1 }} />

      <button className="btn btn-sm" onClick={onLeaveSession} style={{ background: 'var(--danger, #ef4444)' }}>
        Leave
      </button>
    </div>
  )
}
