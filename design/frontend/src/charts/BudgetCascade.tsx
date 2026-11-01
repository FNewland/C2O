import { fs } from '../theme/tokens'
/**
 * BudgetCascade — shows envelope → bucket → used → margin at each level.
 *
 * Displays the budget hierarchy: mission sets envelope, system assigns buckets,
 * subsystem fills them. Color-coded: green (>20% margin), amber (0-20%), red (exceeded).
 */

interface CascadeItem {
  label: string
  allocation: number
  used: number
  unit: string
}

interface Props {
  title: string
  envelope: number
  unit: string
  items: CascadeItem[]
}

export function BudgetCascade({ title, envelope, unit, items }: Props) {
  const totalUsed = items.reduce((s, i) => s + i.used, 0)
  const totalAllocated = items.reduce((s, i) => s + i.allocation, 0)
  const envelopeMargin = envelope > 0 ? ((envelope - totalUsed) / envelope) * 100 : 0
  const envelopeColor = envelopeMargin > 20 ? 'var(--status-ok)' : envelopeMargin > 0 ? 'var(--status-caution)' : 'var(--status-alarm)'

  return (
    <div style={{ padding: '0.5rem', background: 'var(--bg-secondary, var(--surface-2))', borderRadius: '6px', border: '1px solid var(--border, var(--line))' }}>
      {/* Header: envelope */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
        <span style={{ fontSize: fs.label, fontWeight: 600 }}>{title}</span>
        <span style={{ fontSize: fs.value, fontFamily: 'monospace', color: envelopeColor }}>
          {totalUsed.toFixed(1)} / {envelope.toFixed(1)} {unit} ({envelopeMargin.toFixed(0)}%)
        </span>
      </div>

      {/* Envelope bar */}
      <div style={{ height: 8, background: 'var(--surface-1)', borderRadius: 4, marginBottom: '0.4rem', position: 'relative' }}>
        <div style={{ height: '100%', width: `${Math.min(100, (totalUsed / Math.max(envelope, 0.01)) * 100)}%`, background: envelopeColor, borderRadius: 4, transition: 'width 0.3s' }} />
      </div>

      {/* Per-subsystem buckets */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
        {items.filter(i => i.allocation > 0 || i.used > 0).map(item => {
          const pct = item.allocation > 0 ? (item.used / item.allocation) * 100 : 0
          const color = pct < 80 ? 'var(--status-ok)' : pct < 100 ? 'var(--status-caution)' : 'var(--status-alarm)'
          return (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: fs.label }}>
              <span style={{ width: '70px', color: 'var(--text-2)' }}>{item.label}</span>
              <div style={{ flex: 1, height: 5, background: 'var(--surface-1)', borderRadius: 2 }}>
                <div style={{ height: '100%', width: `${Math.min(100, pct)}%`, background: color, borderRadius: 2 }} />
              </div>
              <span style={{ width: '80px', textAlign: 'right', fontFamily: 'monospace', color }}>
                {item.used.toFixed(1)}/{item.allocation.toFixed(1)}
              </span>
            </div>
          )
        })}
      </div>

      {/* Unallocated margin */}
      {envelope > totalAllocated && (
        <div style={{ fontSize: fs.label, color: 'var(--text-3)', marginTop: '0.2rem', textAlign: 'right' }}>
          Unallocated: {(envelope - totalAllocated).toFixed(1)} {unit}
        </div>
      )}
    </div>
  )
}
