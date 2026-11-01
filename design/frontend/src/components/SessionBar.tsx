import { useSessionStore } from '../stores/sessionStore'
import { POSITION_COLOR } from '../constants'
import type { WSStatus } from '../hooks/useSessionSocket'
import { fs } from '../theme/tokens'

function initials(positionId: string): string {
  return positionId.split('_').map(p => p[0]).join('').toUpperCase().slice(0, 2)
}

function statusDot(status: WSStatus): { color: string; label: string } {
  switch (status) {
    case 'connected': return { color: 'var(--success, var(--status-ok))', label: 'Live' }
    case 'connecting': return { color: 'var(--warning, var(--status-caution))', label: 'Connecting' }
    case 'reconnecting': return { color: 'var(--warning, var(--status-caution))', label: 'Reconnecting' }
    case 'error': return { color: 'var(--danger, var(--status-alarm))', label: 'Error' }
    default: return { color: 'var(--text-secondary, var(--text-3))', label: 'Offline' }
  }
}

export function SessionBar({ wsStatus, onStartSession, onLeaveSession }: {
  wsStatus: WSStatus
  onStartSession: () => void
  onLeaveSession: () => void
}) {
  const sessionId = useSessionStore(s => s.sessionId)
  const positionIds = useSessionStore(s => s.positionIds)
  const activePositions = useSessionStore(s => s.activePositions)
  const lastConvergence = useSessionStore(s => s.lastConvergence)
  const dot = statusDot(wsStatus)

  if (!sessionId) {
    return (
      <div style={{
        padding: '0.5rem 1rem', background: 'var(--bg-secondary, var(--surface-2))',
        borderBottom: '1px solid var(--border, var(--line))',
        display: 'flex', alignItems: 'center', gap: '1rem', fontSize: fs.body,
      }}>
        <span style={{ color: 'var(--text-secondary, var(--text-2))' }}>
          No active session — run a single-user design or create a session to collaborate
        </span>
        <div style={{ flex: 1 }} />
        <button className="btn btn-sm" onClick={onStartSession}>Start Session</button>
      </div>
    )
  }

  return (
    <div style={{
      padding: '0.5rem 1rem', background: 'var(--bg-secondary, var(--surface-2))',
      borderBottom: '1px solid var(--border, var(--line))',
      display: 'flex', alignItems: 'center', gap: '1rem', fontSize: fs.body, flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{
          width: '8px', height: '8px', borderRadius: '50%',
          background: dot.color, boxShadow: `0 0 6px ${dot.color}`,
        }} />
        <span style={{ color: 'var(--text-secondary, var(--text-2))' }}>{dot.label}</span>
      </div>

      <div style={{ color: 'var(--text-secondary, var(--text-2))' }}>
        Session <strong style={{ color: 'var(--text-primary, var(--text))', fontFamily: 'monospace' }}>{sessionId}</strong>
      </div>

      {positionIds.length > 0 && (
        <div style={{ color: 'var(--text-secondary, var(--text-2))', display: 'flex', alignItems: 'center', gap: '0.3rem', flexWrap: 'wrap' }}>
          <span>You:</span>
          {positionIds.map(pid => (
            <span key={pid} style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
              padding: '0.1rem 0.45rem', borderRadius: '4px', fontSize: fs.label,
              background: `color-mix(in srgb, ${POSITION_COLOR[pid] || 'var(--text-3)'} 13%, transparent)`,
              color: POSITION_COLOR[pid] || 'var(--text-2)',
              fontWeight: 600,
            }}>{pid.replace(/_/g, ' ')}</span>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
        <span style={{ color: 'var(--text-secondary, var(--text-2))', fontSize: fs.label }}>Online:</span>
        <div style={{ display: 'flex', gap: '-0.25rem' }}>
          {activePositions.length === 0 && (
            <span style={{ color: 'var(--text-secondary, var(--text-3))', fontSize: fs.label, fontStyle: 'italic' }}>none</span>
          )}
          {activePositions.map(pid => (
            <span
              key={pid}
              title={pid.replace(/_/g, ' ')}
              style={{
                width: '24px', height: '24px', borderRadius: '50%',
                background: POSITION_COLOR[pid] || 'var(--text-3)', color: 'white',
                fontSize: fs.label, fontWeight: 700,
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                border: '2px solid var(--bg-secondary, var(--surface-2))',
                marginLeft: '-4px',
              }}
            >{initials(pid)}</span>
          ))}
        </div>
      </div>

      {lastConvergence && (
        <div style={{ color: 'var(--text-secondary, var(--text-2))', fontSize: fs.label }}>
          Last reconv: {lastConvergence.cascadeRounds} rounds, {lastConvergence.timeMs?.toFixed(1)}ms,
          {' '}{lastConvergence.changedParams.length} params
        </div>
      )}

      <div style={{ flex: 1 }} />

      <button className="btn btn-sm" onClick={onLeaveSession} style={{ background: 'var(--danger, var(--status-alarm))' }}>
        Leave
      </button>
    </div>
  )
}
