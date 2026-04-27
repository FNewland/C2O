import { useState, useEffect } from 'react'
import { useSessionHistory } from '../hooks/useSession'
import { useSessionStore } from '../stores/sessionStore'

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
          background: 'var(--bg-card, #1f2937)', color: 'var(--text-primary, #f3f4f6)',
          border: '1px solid var(--border, #374151)', borderRadius: '6px',
          padding: '0.5rem 0.8rem', fontSize: '0.75rem', cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: '0.4rem',
        }}
      >
        <span>History</span>
        <span style={{
          background: edits.length > 0 ? 'var(--accent, #3b82f6)' : '#374151',
          color: 'white', borderRadius: '10px', padding: '0 0.4rem',
          fontSize: '0.65rem', fontWeight: 700, minWidth: '18px', textAlign: 'center',
        }}>{edits.length}</span>
      </button>

      {isOpen && (
        <div style={{
          position: 'fixed', top: 0, right: 0, bottom: 0, width: '420px',
          background: 'var(--bg-secondary, #1f2937)', borderLeft: '1px solid var(--border, #374151)',
          zIndex: 8000, display: 'flex', flexDirection: 'column',
          boxShadow: '-4px 0 12px rgba(0,0,0,0.3)',
        }}>
          <div style={{
            padding: '0.75rem 1rem', borderBottom: '1px solid var(--border, #374151)',
            display: 'flex', alignItems: 'center',
          }}>
            <h2 style={{ margin: 0, fontSize: '1rem' }}>Edit History</h2>
            <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: '#9ca3af' }}>
              {edits.length} edit{edits.length !== 1 ? 's' : ''}
            </span>
            <div style={{ flex: 1 }} />
            <button className="btn btn-sm" onClick={() => refetch()} style={{ marginRight: '0.5rem', fontSize: '0.7rem' }}>
              Refresh
            </button>
            <button className="btn btn-sm" onClick={() => setIsOpen(false)}>Close</button>
          </div>

          <div style={{ flex: 1, overflow: 'auto', padding: '0.5rem' }}>
            {isLoading && <div className="loading"><div className="spinner" /> Loading...</div>}
            {edits.length === 0 && !isLoading && (
              <div style={{ padding: '1rem', fontSize: '0.85rem', color: '#9ca3af' }}>
                No edits recorded yet. Edit a parameter to see changes here.
              </div>
            )}
            {edits.map((e) => {
              const posId = e.editedBy
              const color = POSITION_COLOR[posId] || '#6b7280'
              const initials = posId.split('_').map((p: string) => p[0]).join('').toUpperCase().slice(0, 2)
              return (
                <div key={e.id + e.timestamp} style={{
                  padding: '0.5rem 0.75rem', borderLeft: `3px solid ${color}`,
                  background: 'var(--bg-primary, #111827)', borderRadius: '0 4px 4px 0',
                  marginBottom: '0.4rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.2rem' }}>
                    <span style={{
                      width: '20px', height: '20px', borderRadius: '50%',
                      background: color, color: 'white',
                      fontSize: '0.6rem', fontWeight: 700,
                      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                    }}>{initials}</span>
                    <strong style={{ fontSize: '0.8rem', color }}>
                      {posId.replace(/_/g, ' ')}
                    </strong>
                    {e.source === 'live' && (
                      <span style={{ fontSize: '0.6rem', background: 'rgba(16,185,129,0.2)', color: '#10b981', padding: '0 0.3rem', borderRadius: '3px' }}>live</span>
                    )}
                    <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: '#9ca3af' }}>
                      {formatTime(e.timestamp)}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', marginLeft: '1.6rem' }}>
                    set <code style={{ fontSize: '0.7rem' }}>{e.paramId}</code>
                  </div>
                  <div style={{ fontSize: '0.75rem', marginLeft: '1.6rem', color: '#9ca3af' }}>
                    {formatValue(e.oldValue)} → <strong style={{ color: '#f3f4f6' }}>{formatValue(e.newValue)}</strong>
                    {e.equipmentId && <span style={{ marginLeft: '0.4rem', color: '#3b82f6' }}>[{e.equipmentId}]</span>}
                  </div>
                  {e.rationale && (
                    <div style={{ fontSize: '0.7rem', marginLeft: '1.6rem', marginTop: '0.2rem', fontStyle: 'italic', color: '#9ca3af' }}>
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
