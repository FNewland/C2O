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
  const envelopeColor = envelopeMargin > 20 ? '#10b981' : envelopeMargin > 0 ? '#f59e0b' : '#ef4444'

  return (
    <div style={{ padding: '0.5rem', background: 'var(--bg-secondary, #1f2937)', borderRadius: '6px', border: '1px solid var(--border, #374151)' }}>
      {/* Header: envelope */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
        <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>{title}</span>
        <span style={{ fontSize: '0.7rem', fontFamily: 'monospace', color: envelopeColor }}>
          {totalUsed.toFixed(1)} / {envelope.toFixed(1)} {unit} ({envelopeMargin.toFixed(0)}%)
        </span>
      </div>

      {/* Envelope bar */}
      <div style={{ height: 8, background: '#111827', borderRadius: 4, marginBottom: '0.4rem', position: 'relative' }}>
        <div style={{ height: '100%', width: `${Math.min(100, (totalUsed / Math.max(envelope, 0.01)) * 100)}%`, background: envelopeColor, borderRadius: 4, transition: 'width 0.3s' }} />
      </div>

      {/* Per-subsystem buckets */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
        {items.filter(i => i.allocation > 0 || i.used > 0).map(item => {
          const pct = item.allocation > 0 ? (item.used / item.allocation) * 100 : 0
          const color = pct < 80 ? '#10b981' : pct < 100 ? '#f59e0b' : '#ef4444'
          return (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.68rem' }}>
              <span style={{ width: '70px', color: '#9ca3af' }}>{item.label}</span>
              <div style={{ flex: 1, height: 5, background: '#111827', borderRadius: 2 }}>
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
        <div style={{ fontSize: '0.62rem', color: '#6b7280', marginTop: '0.2rem', textAlign: 'right' }}>
          Unallocated: {(envelope - totalAllocated).toFixed(1)} {unit}
        </div>
      )}
    </div>
  )
}
