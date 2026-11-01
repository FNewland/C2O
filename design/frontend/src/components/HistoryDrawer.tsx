import { useState, useEffect } from 'react'
import { useSessionHistory } from '../hooks/useSession'
import { useSessionStore } from '../stores/sessionStore'
import { POSITION_COLOR } from '../constants'
import { fs } from '../theme/tokens'

export function HistoryDrawer({ sessionId }: { sessionId: string | null }) {
  const [isOpen, setIsOpen] = useState(false)
  const { data, isLoading, refetch } = useSessionHistory(sessionId)
  const toasts = useSessionStore(s => s.toasts)

  // Auto-refetch when new toasts arrive (indicating edits happened)
  const toastCount = toasts.length
  useEffect(() => {
    if (isOpen && sessionId) refetch()
  }, [toastCount, isOpen, sessionId])

  if (!sessionId) return null

  // Normalise edit records from backend (handles both DB field names and in-memory names)
  const rawEdits: any[] = (data as any)?.edits || []
  const edits = rawEdits.map(e => ({
    id: e.id || '',
    paramId: e.parameter_id || e.param_path || '',
    oldValue: e.old_value,
    newValue: e.new_value,
    editedBy: e.edited_by || e.position_id || e.actor_label || 'unknown',
    displayName: e.display_name || e.actor_label || e.edited_by || 'unknown',
    timestamp: e.timestamp || e.created_at || '',
    rationale: e.rationale || '',
    editType: e.edit_type || 'override',
    equipmentId: e.equipment_id || null,
    source: e.source || 'persisted',
  }))

  return (
    <>
      <button
        onClick={() => { setIsOpen(true); refetch() }}
        style={{
          position: 'fixed', bottom: '1rem', left: '1rem', zIndex: 500,
          background: 'var(--bg-card, var(--surface-2))', color: 'var(--text-primary, var(--text))',
          border: '1px solid var(--border, var(--line))', borderRadius: '6px',
          padding: '0.5rem 0.8rem', fontSize: fs.label, cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: '0.4rem',
        }}
      >
        <span>History</span>
        <span style={{
          background: edits.length > 0 ? 'var(--accent, var(--interactive))' : 'var(--line)',
          color: 'white', borderRadius: '10px', padding: '0 0.4rem',
          fontSize: fs.label, fontWeight: 700, minWidth: '18px', textAlign: 'center',
        }}>{edits.length}</span>
      </button>

      {isOpen && (
        <div style={{
          position: 'fixed', top: 0, right: 0, bottom: 0, width: '420px',
          background: 'var(--bg-secondary, var(--surface-2))', borderLeft: '1px solid var(--border, var(--line))',
          zIndex: 8000, display: 'flex', flexDirection: 'column',
          boxShadow: '-4px 0 12px rgba(0,0,0,0.3)',
        }}>
          <div style={{
            padding: '0.75rem 1rem', borderBottom: '1px solid var(--border, var(--line))',
            display: 'flex', alignItems: 'center',
          }}>
            <h2 style={{ margin: 0, fontSize: fs.value }}>Edit History</h2>
            <span style={{ marginLeft: '0.5rem', fontSize: fs.label, color: 'var(--text-2)' }}>
              {edits.length} edit{edits.length !== 1 ? 's' : ''}
            </span>
            <div style={{ flex: 1 }} />
            <button className="btn btn-sm" onClick={() => refetch()} style={{ marginRight: '0.5rem', fontSize: fs.label }}>
              Refresh
            </button>
            <button className="btn btn-sm" onClick={() => setIsOpen(false)}>Close</button>
          </div>

          <div style={{ flex: 1, overflow: 'auto', padding: '0.5rem' }}>
            {isLoading && <div className="loading"><div className="spinner" /> Loading...</div>}
            {edits.length === 0 && !isLoading && (
              <div style={{ padding: '1rem', fontSize: fs.body, color: 'var(--text-2)' }}>
                No edits recorded yet. Edit a parameter to see changes here.
              </div>
            )}
            {edits.map((e) => {
              const posId = e.editedBy
              const color = POSITION_COLOR[posId] || 'var(--text-3)'
              const initials = posId.split('_').map((p: string) => p[0]).join('').toUpperCase().slice(0, 2)
              return (
                <div key={e.id + e.timestamp} style={{
                  padding: '0.5rem 0.75rem', borderLeft: `3px solid ${color}`,
                  background: 'var(--bg-primary, var(--surface-1))', borderRadius: '0 4px 4px 0',
                  marginBottom: '0.4rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.2rem' }}>
                    <span style={{
                      width: '20px', height: '20px', borderRadius: '50%',
                      background: color, color: 'white',
                      fontSize: fs.label, fontWeight: 700,
                      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                    }}>{initials}</span>
                    <strong style={{ fontSize: fs.body, color }}>
                      {posId.replace(/_/g, ' ')}
                    </strong>
                    {e.source === 'live' && (
                      <span style={{ fontSize: fs.label, background: 'rgba(16,185,129,0.2)', color: 'var(--status-ok)', padding: '0 0.3rem', borderRadius: '3px' }}>live</span>
                    )}
                    <span style={{ marginLeft: 'auto', fontSize: fs.label, color: 'var(--text-2)' }}>
                      {formatTime(e.timestamp)}
                    </span>
                  </div>
                  <div style={{ fontSize: fs.label, marginLeft: '1.6rem' }}>
                    set <code style={{ fontSize: fs.label }}>{e.paramId}</code>
                  </div>
                  <div style={{ fontSize: fs.label, marginLeft: '1.6rem', color: 'var(--text-2)' }}>
                    {formatValue(e.oldValue)} → <strong style={{ color: 'var(--text)' }}>{formatValue(e.newValue)}</strong>
                    {e.equipmentId && <span style={{ marginLeft: '0.4rem', color: 'var(--interactive)' }}>[{e.equipmentId}]</span>}
                  </div>
                  {e.rationale && (
                    <div style={{ fontSize: fs.label, marginLeft: '1.6rem', marginTop: '0.2rem', fontStyle: 'italic', color: 'var(--text-2)' }}>
                      "{e.rationale}"
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </>
  )
}

function formatValue(v: any): string {
  if (v === null || v === undefined) return 'N/A'
  if (typeof v === 'number') {
    if (Math.abs(v) >= 100) return v.toFixed(1)
    if (Math.abs(v) >= 1) return v.toFixed(3)
    return v.toPrecision(3)
  }
  const n = Number(v)
  if (!isNaN(n) && v !== '') {
    if (Math.abs(n) >= 100) return n.toFixed(1)
    if (Math.abs(n) >= 1) return n.toFixed(3)
    return n.toPrecision(3)
  }
  return String(v)
}

function formatTime(iso: string | undefined): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString()
  } catch { return iso }
}
