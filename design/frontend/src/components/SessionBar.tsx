import { useSessionStore } from '../stores/sessionStore'
import type { WSStatus } from '../hooks/useSessionSocket'

const POSITION_COLOR: Record<string, string> = {
  systems_engineer: '#8b5cf6',
  mission_analyst: '#3b82f6',
  payload_lead: '#10b981',
  power_engineer: '#f59e0b',
  aocs_engineer: '#06b6d4',
  thermal_engineer: '#ef4444',
  comms_engineer: '#ec4899',
  propulsion_engineer: '#f97316',
  structures_engineer: '#84cc16',
  cost_engineer: '#a855f7',
}

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

      {positionId && (
        <div style={{ color: 'var(--text-secondary, #9ca3af)' }}>
          You: <span style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
            padding: '0.15rem 0.5rem', borderRadius: '4px',
            background: `${POSITION_COLOR[positionId] || '#6b7280'}22`,
            color: POSITION_COLOR[positionId] || '#9ca3af',
            fontWeight: 600,
          }}>{positionId.replace(/_/g, ' ')}</span>
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
