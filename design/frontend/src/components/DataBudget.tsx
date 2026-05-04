/**
 * DataBudget — Data pipeline budget from generation to user delivery.
 *
 * Shows: generation rate → storage capacity → downlink capacity → latency.
 */
import { useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'

export function DataBudget() {
  const reqs = useDesignStore(s => s.requirements)
  const params = useActiveParameters()
  const get = (id: string) => { const p = params[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  const pipeline = useMemo(() => {
    const pl = reqs.payloads?.[0]
    const dataRateMbps = pl?.data_rate_mbps || 10
    const dutyCyclePct = pl?.duty_cycle_percent || 25
    const orbitPeriodMin = 95 // ~500km LEO

    // Generation
    const genRateGbPerDay = (dataRateMbps * dutyCyclePct / 100 * orbitPeriodMin * 60 * 15) / (8 * 1e3)
    // ~15 orbits per day, duty cycle active per orbit

    // Storage
    const storageGb = get('data.storage_gb') || 32
    const fillTimeDays = storageGb / Math.max(genRateGbPerDay, 0.01)

    // Downlink
    const contactMinPerDay = get('link.contact_min_per_day') || 30
    const dlRateMbps = get('link.downlink_data_rate_mbps') || dataRateMbps
    const dlCapacityGbPerDay = (dlRateMbps * contactMinPerDay * 60) / (8 * 1e3)

    // Balance
    const dataBalance = dlCapacityGbPerDay - genRateGbPerDay
    const latencyHours = genRateGbPerDay > 0 ? (storageGb / genRateGbPerDay) * 24 / 2 : 0 // Average half-full

    return {
      generation: { rate_mbps: dataRateMbps, duty_pct: dutyCyclePct, daily_gb: genRateGbPerDay },
      storage: { capacity_gb: storageGb, fill_time_days: fillTimeDays },
      downlink: { rate_mbps: dlRateMbps, contact_min: contactMinPerDay, daily_gb: dlCapacityGbPerDay },
      balance: { surplus_gb: dataBalance, balanced: dataBalance >= 0 },
      latency: { avg_hours: latencyHours, worst_hours: latencyHours * 2 },
    }
  }, [reqs, params])

  const p = pipeline

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.9rem', marginBottom: '0.3rem' }}>Data Pipeline Budget</h3>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Generation → Storage → Downlink → User. Must balance: downlink ≥ generation.
      </p>

      {/* Flow diagram */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', marginBottom: '0.75rem', fontSize: '0.72rem', flexWrap: 'wrap' }}>
        <FlowBox label="Generate" value={`${p.generation.daily_gb.toFixed(1)} GB/day`} sub={`${p.generation.rate_mbps} Mbps × ${p.generation.duty_pct}%`} color="#8b5cf6" />
        <Arrow />
        <FlowBox label="Store" value={`${p.storage.capacity_gb} GB`} sub={`fills in ${p.storage.fill_time_days.toFixed(1)} days`} color="#3b82f6" />
        <Arrow />
        <FlowBox label="Downlink" value={`${p.downlink.daily_gb.toFixed(1)} GB/day`} sub={`${p.downlink.rate_mbps} Mbps × ${p.downlink.contact_min} min`} color="#10b981" />
        <Arrow />
        <FlowBox label="User" value={`${p.latency.avg_hours.toFixed(0)}h avg latency`} sub={`${p.latency.worst_hours.toFixed(0)}h worst case`} color="#f59e0b" />
      </div>

      {/* Balance indicator */}
      <div style={{
        padding: '0.4rem 0.6rem', borderRadius: '4px', fontSize: '0.78rem',
        background: p.balance.balanced ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
        border: `1px solid ${p.balance.balanced ? '#10b981' : '#ef4444'}`,
        display: 'flex', alignItems: 'center', gap: '0.5rem',
      }}>
        <span style={{ fontWeight: 700, color: p.balance.balanced ? '#10b981' : '#ef4444' }}>
          {p.balance.balanced ? 'BALANCED' : 'OVERFLOW'}
        </span>
        <span style={{ color: '#9ca3af' }}>
          Downlink {p.balance.balanced ? 'exceeds' : 'cannot keep up with'} generation by {Math.abs(p.balance.surplus_gb).toFixed(1)} GB/day
        </span>
        {!p.balance.balanced && (
          <span style={{ color: '#ef4444', fontSize: '0.72rem' }}>
            — need higher data rate, more contact time, or reduced duty cycle
          </span>
        )}
      </div>
    </div>
  )
}

function FlowBox({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  return (
    <div style={{
      padding: '0.3rem 0.5rem', borderRadius: '4px', minWidth: '100px', textAlign: 'center',
      background: `${color}11`, border: `1px solid ${color}40`,
    }}>
      <div style={{ fontSize: '0.65rem', color, fontWeight: 600, textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#d1d5db' }}>{value}</div>
      <div style={{ fontSize: '0.6rem', color: '#6b7280' }}>{sub}</div>
    </div>
  )
}

function Arrow() {
  return <span style={{ fontSize: '1rem', color: '#6b7280' }}>→</span>
}
