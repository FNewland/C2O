/**
 * PersistenceWarningBanner — Shows when DB writes are failing.
 *
 * Per SPINE_SPEC §5. Displays an amber banner when persistence is degraded.
 * Auto-dismisses when persistence recovers.
 */
import { useState } from 'react'
import { useSessionStore } from '../stores/sessionStore'

export function PersistenceWarningBanner() {
  const persistenceOk = useSessionStore(s => s.persistenceOk)
  const [dismissed, setDismissed] = useState(false)

  if (persistenceOk || dismissed) return null

  return (
    <div style={{
      padding: '0.4rem 1rem', background: 'rgba(245,158,11,0.15)',
      borderBottom: '2px solid #f59e0b', display: 'flex',
      alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: '#f59e0b',
    }}>
      <span style={{ fontWeight: 600 }}>Warning:</span>
      <span>Edits queued — retrying database writes. Your changes are safe in memory.</span>
      <span style={{ flex: 1 }} />
      <button onClick={() => setDismissed(true)}
        style={{ background: 'none', border: 'none', color: '#f59e0b', cursor: 'pointer', fontSize: '0.75rem' }}>
        Dismiss
      </button>
    </div>
  )
}
