/**
 * ChangeAuditPanel — Shows all parameter changes with undo capability.
 *
 * Displays a reverse-chronological list of every change made in the
 * current session, with who/what changed, old/new values, and undo.
 */
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  mission_need: { label: 'Mission Need', color: 'var(--cat-2)' },
  requirements: { label: 'Requirements', color: 'var(--interactive)' },
  orbit: { label: 'Orbit', color: 'var(--interactive)' },
  equipment: { label: 'Equipment', color: 'var(--status-ok)' },
  conops: { label: 'ConOps', color: 'var(--status-caution)' },
  functions: { label: 'Functions', color: 'var(--cat-6)' },
}

export function ChangeAuditPanel() {
  const changeHistory = useDesignStore(s => s.changeHistory)
  const undoLastChange = useDesignStore(s => s.undoLastChange)

  if (changeHistory.length === 0) {
    return (
      <div style={{ padding: '1rem', color: 'var(--text-3)', fontSize: fs.label }}>
        No changes recorded yet. Edit mission parameters to see the audit trail.
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <h2 style={{ margin: 0 }}>Change History</h2>
        <span style={{ fontSize: fs.label, color: 'var(--text-3)' }}>{changeHistory.length} changes</span>
        <span style={{ flex: 1 }} />
        {changeHistory.length > 0 && (
          <button className="btn btn-sm" onClick={undoLastChange}
            style={{ fontSize: fs.label, background: 'var(--status-caution)', color: 'var(--on-fill)' }}>
            Undo Last Change
          </button>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {[...changeHistory].reverse().map((change, i) => {
          const info = SOURCE_LABELS[change.source] || { label: change.source, color: 'var(--text-3)' }
          const time = new Date(change.timestamp).toLocaleTimeString()
          const isLatest = i === 0

          return (
            <div key={change.timestamp} style={{
              display: 'flex', alignItems: 'flex-start', gap: '0.5rem',
              padding: '0.35rem 0.5rem', borderRadius: '4px',
              background: isLatest ? 'rgba(59,130,246,0.05)' : 'transparent',
              borderLeft: `3px solid ${info.color}`,
              fontSize: fs.label,
            }}>
              <span style={{ fontSize: fs.label, color: 'var(--text-3)', whiteSpace: 'nowrap', marginTop: '0.1rem' }}>
                {time}
              </span>
              <span style={{
                fontSize: fs.label, padding: '0.1rem 0.3rem', borderRadius: '3px',
                background: `color-mix(in srgb, ${info.color} 13%, transparent)`, color: info.color, fontWeight: 600,
                whiteSpace: 'nowrap',
              }}>{info.label}</span>
              <span style={{ color: 'var(--text)', flex: 1 }}>
                <span style={{ fontFamily: 'monospace', fontSize: fs.value }}>{change.paramId}</span>
              </span>
              <span style={{ color: 'var(--text-3)', fontSize: fs.label, whiteSpace: 'nowrap' }}>
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
