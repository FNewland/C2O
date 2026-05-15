/**
 * PresenceBar — Shows connected users and connection status.
 */
import { useCollaboration } from './useCollaboration'
import { AIStatusIndicator } from '../ai'

export function PresenceBar() {
  const { connected, users, myName } = useCollaboration()

  if (!myName) return null

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '0.4rem',
      padding: '0.15rem 1rem', fontSize: '0.6rem',
      background: connected ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
      borderBottom: `1px solid ${connected ? 'var(--success)' : 'var(--danger)'}`,
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: '50%',
        background: connected ? 'var(--success)' : 'var(--danger)',
      }} />
      <span style={{ color: connected ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>
        {connected ? 'Connected' : 'Reconnecting...'}
      </span>
      <span style={{ color: 'var(--border)' }}>|</span>
      {users.length > 0 ? (
        users.map((u, i) => (
          <span key={u.name} style={{
            color: u.name === myName ? 'var(--accent)' : 'var(--text-secondary)',
            fontWeight: u.name === myName ? 600 : 400,
          }}>
            {u.name === myName ? `${u.name} (you)` : u.name}
            {i < users.length - 1 ? ' · ' : ''}
          </span>
        ))
      ) : (
        <span style={{ color: 'var(--text-secondary)' }}>{myName} (you)</span>
      )}
      <span style={{ color: 'var(--text-secondary)', marginLeft: '0.3rem' }}>
        — {users.length || 1} connected
      </span>
      <span style={{ marginLeft: 'auto' }}>
        <AIStatusIndicator />
      </span>
    </div>
  )
}
