import { useEffect } from 'react'
import { useSessionStore } from '../stores/sessionStore'

const TOAST_TIMEOUT_MS = 3000

export function LiveEditToast() {
  const toasts = useSessionStore(s => s.toasts)
  const dismissToast = useSessionStore(s => s.dismissToast)

  useEffect(() => {
    if (toasts.length === 0) return
    const timers = toasts.map(t => setTimeout(() => dismissToast(t.id), TOAST_TIMEOUT_MS))
    return () => timers.forEach(clearTimeout)
  }, [toasts, dismissToast])

  if (toasts.length === 0) return null

  return (
    <div style={{
      position: 'fixed', bottom: '1rem', right: '1rem', zIndex: 9999,
      display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: '380px',
    }}>
      {toasts.map(t => {
        const border = t.isError ? 'var(--danger, #ef4444)' : 'var(--accent, #3b82f6)'
        return (
          <div
            key={t.id}
            onClick={() => dismissToast(t.id)}
            style={{
              background: 'var(--bg-card, #1f2937)',
              border: `1px solid ${border}`,
              borderLeft: `4px solid ${border}`,
              borderRadius: '6px', padding: '0.6rem 0.8rem',
              cursor: 'pointer', fontSize: '0.8rem',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              animation: 'slideIn 0.2s ease-out',
            }}
          >
            {t.isError ? (
              <>
                <div style={{ fontWeight: 600, color: 'var(--danger, #ef4444)' }}>Edit rejected</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)', marginTop: '0.2rem' }}>
                  {t.errorMessage || `Could not edit ${t.parameterId}`}
                </div>
              </>
            ) : (
              <>
                <div>
                  <strong>{t.actor}</strong>
                  {' '}set{' '}
                  <code style={{ fontSize: '0.75rem' }}>{t.parameterId}</code>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)', marginTop: '0.2rem' }}>
                  {formatValue(t.oldValue)} → <strong>{formatValue(t.newValue)}</strong>
                  {t.equipmentId && (
                    <span style={{ marginLeft: '0.3rem', color: 'var(--accent, #3b82f6)' }}>
                      [{t.equipmentId}]
                    </span>
                  )}
                </div>
              </>
            )}
          </div>
        )
      })}
    </div>
  )
}

function formatValue(v: any): string {
  if (v === null || v === undefined) return 'N/A'
  if (typeof v === 'number') {
    if (Math.abs(v) >= 100) return v.toFixed(1)
    if (Math.abs(v) >= 1) return v.toFixed(2)
    return v.toPrecision(3)
  }
  return String(v)
}
