/**
 * PersistenceWarningBanner — Shows when DB writes are failing.
 *
 * Per SPINE_SPEC §5. Displays an amber banner when persistence is degraded.
 * Auto-dismisses when persistence recovers.
 */
import { useState } from 'react'
import { useSessionStore } from '../stores/sessionStore'
import { fs } from '../theme/tokens'

export function PersistenceWarningBanner() {
  const persistenceOk = useSessionStore(s => s.persistenceOk)
  const [dismissed, setDismissed] = useState(false)

  if (persistenceOk || dismissed) return null

  return (
    <div style={{
      padding: '0.4rem 1rem', background: 'rgba(245,158,11,0.15)',
      borderBottom: '2px solid var(--status-caution)', display: 'flex',
      alignItems: 'center', gap: '0.5rem', fontSize: fs.label, color: 'var(--status-caution)',
    }}>
      <span style={{ fontWeight: 600 }}>Warning:</span>
      <span>Edits queued — retrying database writes. Your changes are safe in memory.</span>
      <span style={{ flex: 1 }} />
      <button onClick={() => setDismissed(true)}
        style={{ background: 'none', border: 'none', color: 'var(--status-caution)', cursor: 'pointer', fontSize: fs.label }}>
        Dismiss
      </button>
    </div>
  )
}
