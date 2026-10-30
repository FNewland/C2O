/**
 * ChangeAuditPanel — Shows all parameter changes with undo capability.
 *
 * Displays a reverse-chronological list of every change made in the
 * current session, with who/what changed, old/new values, and undo.
 */
import { useDesignStore } from '../stores/designStore'

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  mission_need: { label: 'Mission Need', color: '#8b5cf6' },
  requirements: { label: 'Requirements', color: '#3b82f6' },
  orbit: { label: 'Orbit', color: '#06b6d4' },
  equipment: { label: 'Equipment', color: '#10b981' },
  conops: { label: 'ConOps', color: '#f59e0b' },
  functions: { label: 'Functions', color: '#ec4899' },
}

export function ChangeAuditPanel() {
  const changeHistory = useDesignStore(s => s.changeHistory)
  const undoLastChange = useDesignStore(s => s.undoLastChange)

  if (changeHistory.length === 0) {
    return (
      <div style={{ padding: '1rem', color: '#6b7280', fontSize: '0.78rem' }}>
        No changes recorded yet. Edit mission parameters to see the audit trail.
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <h2 style={{ margin: 0 }}>Change History</h2>
        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>{changeHistory.length} changes</span>
        <span style={{ flex: 1 }} />
        {changeHistory.length > 0 && (
          <button className="btn btn-sm" onClick={undoLastChange}
            style={{ fontSize: '0.7rem', background: '#f59e0b', color: '#000' }}>
            Undo Last Change
          </button>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {[...changeHistory].reverse().map((change, i) => {
          const info = SOURCE_LABELS[change.source] || { label: change.source, color: '#6b7280' }
          const time = new Date(change.timestamp).toLocaleTimeString()
          const isLatest = i === 0

          return (
            <div key={change.timestamp} style={{
              display: 'flex', alignItems: 'flex-start', gap: '0.5rem',
              padding: '0.35rem 0.5rem', borderRadius: '4px',
              background: isLatest ? 'rgba(59,130,246,0.05)' : 'transparent',
              borderLeft: `3px solid ${info.color}`,
              fontSize: '0.75rem',
            }}>
              <span style={{ fontSize: '0.65rem', color: '#6b7280', whiteSpace: 'nowrap', marginTop: '0.1rem' }}>
                {time}
              </span>
              <span style={{
                fontSize: '0.6rem', padding: '0.1rem 0.3rem', borderRadius: '3px',
                background: `${info.color}22`, color: info.color, fontWeight: 600,
                whiteSpace: 'nowrap',
              }}>{info.label}</span>
              <span style={{ color: '#d1d5db', flex: 1 }}>
                <span style={{ fontFamily: 'monospace', fontSize: '0.7rem' }}>{change.paramId}</span>
              </span>
              <span style={{ color: '#6b7280', fontSize: '0.68rem', whiteSpace: 'nowrap' }}>
                {formatValue(change.oldValue)} → {formatValue(change.newValue)}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function formatValue(v: any): string {
  if (v === undefined || v === null) return '—'
  if (Array.isArray(v)) return v.map(formatValue).join(', ')
  if (typeof v === 'number') return v.toFixed?.(2) || String(v)
  if (typeof v === 'string' && v.length > 30) return v.slice(0, 27) + '...'
  return String(v)
}
