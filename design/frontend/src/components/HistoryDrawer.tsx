import { useState } from 'react'
import { useSessionHistory } from '../hooks/useSession'

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

  if (!sessionId) return null

  const edits: any[] = (data as any)?.edits || []

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
        <span>📜</span>
        <span>History ({edits.length || '—'})</span>
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
            <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)' }}>
              {edits.length} edits
            </span>
            <div style={{ flex: 1 }} />
            <button className="btn btn-sm" onClick={() => setIsOpen(false)}>Close</button>
          </div>

          <div style={{ flex: 1, overflow: 'auto', padding: '0.5rem' }}>
            {isLoading && <div className="loading"><div className="spinner" /> Loading...</div>}
            {edits.length === 0 && !isLoading && (
              <div style={{ padding: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary, #9ca3af)' }}>
                No edits recorded yet. Join a session and start editing to see changes here.
              </div>
            )}
            {[...edits].reverse().map((e: any) => {
              const color = POSITION_COLOR[e.position_id] || '#6b7280'
              const initials = (e.position_id || '?').split('_').map((p: string) => p[0]).join('').toUpperCase().slice(0, 2)
              return (
                <div key={e.id} style={{
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
                      {(e.actor_label || e.position_id || 'unknown').replace(/_/g, ' ')}
                    </strong>
                    <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: 'var(--text-secondary, #9ca3af)' }}>
                      {formatTime(e.created_at)}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', marginLeft: '1.6rem' }}>
                    set <code style={{ fontSize: '0.7rem' }}>{e.param_path}</code>
                  </div>
                  <div style={{ fontSize: '0.75rem', marginLeft: '1.6rem', color: 'var(--text-secondary, #9ca3af)' }}>
                    {formatValue(e.old_value)} → <strong style={{ color: 'var(--text-primary, #f3f4f6)' }}>{formatValue(e.new_value)}</strong>
                    {e.equipment_id && <span style={{ marginLeft: '0.4rem', color: 'var(--accent, #3b82f6)' }}>[{e.equipment_id}]</span>}
                  </div>
                  {e.rationale && (
                    <div style={{ fontSize: '0.7rem', marginLeft: '1.6rem', marginTop: '0.2rem', fontStyle: 'italic', color: 'var(--text-secondary, #9ca3af)' }}>
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
  if (typeof v === 'string') {
    // Values are stored as strings in DB; try to parse as number
    const n = Number(v)
    if (!isNaN(n)) {
      if (Math.abs(n) >= 100) return n.toFixed(1)
      if (Math.abs(n) >= 1) return n.toFixed(3)
      return n.toPrecision(3)
    }
    return v
  }
  if (typeof v === 'number') {
    if (Math.abs(v) >= 100) return v.toFixed(1)
    if (Math.abs(v) >= 1) return v.toFixed(3)
    return v.toPrecision(3)
  }
  return String(v)
}

function formatTime(iso: string | undefined): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString()
  } catch { return iso }
}
