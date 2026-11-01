import { useEffect } from 'react'
import { useSessionStore } from '../stores/sessionStore'
import { fs } from '../theme/tokens'

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
        const border = t.isError ? 'var(--danger, var(--status-alarm))' : 'var(--accent, var(--interactive))'
        return (
          <div
            key={t.id}
            onClick={() => dismissToast(t.id)}
            style={{
              background: 'var(--bg-card, var(--surface-2))',
              border: `1px solid ${border}`,
              borderLeft: `4px solid ${border}`,
              borderRadius: '6px', padding: '0.6rem 0.8rem',
              cursor: 'pointer', fontSize: fs.body,
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              animation: 'slideIn 0.2s ease-out',
            }}
          >
            {t.isError ? (
              <>
                <div style={{ fontWeight: 600, color: 'var(--danger, var(--status-alarm))' }}>Edit rejected</div>
                <div style={{ fontSize: fs.label, color: 'var(--text-secondary, var(--text-2))', marginTop: '0.2rem' }}>
                  {t.errorMessage || `Could not edit ${t.parameterId}`}
                </div>
              </>
            ) : (
              <>
                <div>
                  <strong>{t.actor}</strong>
                  {' '}set{' '}
                  <code style={{ fontSize: fs.label }}>{t.parameterId}</code>
                </div>
                <div style={{ fontSize: fs.label, color: 'var(--text-secondary, var(--text-2))', marginTop: '0.2rem' }}>
                  {formatValue(t.oldValue)} → <strong>{formatValue(t.newValue)}</strong>
                  {t.equipmentId && (
                    <span style={{ marginLeft: '0.3rem', color: 'var(--accent, var(--interactive))' }}>
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
