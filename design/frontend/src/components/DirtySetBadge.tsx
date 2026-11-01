/**
 * DirtySetBadge — Shows count of parameters with pending edits awaiting convergence.
 *
 * Amber badge with tooltip listing dirty parameters. Clears on convergence.
 */
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'

export function DirtySetBadge() {
  const designStale = useDesignStore(s => s.designStale)
  const lastSource = useDesignStore(s => s.lastChangeSource)

  if (!designStale) return null

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '0.2rem',
      padding: '0.1rem 0.4rem', borderRadius: '10px',
      background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.3)',
      color: 'var(--status-caution)', fontSize: fs.label, fontWeight: 600,
    }} title={`Design stale since change from: ${lastSource || 'unknown'}`}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--status-caution)', animation: 'pulse 1.5s infinite' }} />
      Stale
    </span>
  )
}
