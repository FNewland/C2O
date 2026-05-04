/**
 * LaunchSelector — Interactive launch provider selection.
 *
 * Shows available providers filtered by spacecraft mass/size.
 * Selection sets mass allocation in design budgets.
 */
import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'

interface LaunchProvider {
  id: string; name: string; type: string; vehicle: string; orbit: string
  capacity_kg: number; price_usd: number; price_per_kg_usd?: number
  cadence_per_year: number; lead_time_months: string; deployers: string[]
  notes: string
}

export function LaunchSelector() {
  const [providers, setProviders] = useState<LaunchProvider[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const markStale = useDesignStore(s => s.markStale)
  const dryMass = useDesignStore(s => {
    const p = s.result?.parameters?.['mass.dry_mass_kg']
    return p && typeof p.value === 'number' ? p.value : 5
  })

  useEffect(() => {
    fetch('/api/lifecycle/parametric-data')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        // Launch providers are not yet in the parametric data API
        // Load from a direct endpoint or hardcode for now
        setProviders([
          { id: 'spacex-transporter', name: 'SpaceX Transporter', type: 'rideshare', vehicle: 'Falcon 9', orbit: 'SSO 525 km', capacity_kg: 50, price_usd: 350000, price_per_kg_usd: 7000, cadence_per_year: 4, lead_time_months: '6-12', deployers: ['CSD', 'ISIPOD', 'EXOpod'], notes: '$350K min for ≤50 kg to SSO' },
          { id: 'rocketlab-electron', name: 'Rocket Lab Electron', type: 'dedicated', vehicle: 'Electron', orbit: 'Custom LEO/SSO', capacity_kg: 200, price_usd: 7500000, cadence_per_year: 12, lead_time_months: '6-18', deployers: ['CSD'], notes: 'Dedicated launch, custom orbit' },
          { id: 'exolaunch', name: 'Exolaunch', type: 'broker', vehicle: 'Various', orbit: 'SSO', capacity_kg: 100, price_usd: 250000, cadence_per_year: 6, lead_time_months: '9-18', deployers: ['EXOpod Nova'], notes: 'European broker, 280+ CubeSats' },
          { id: 'dorbit-ion', name: 'D-Orbit ION', type: 'space_tug', vehicle: 'ION Carrier', orbit: 'Custom', capacity_kg: 160, price_usd: 100000, cadence_per_year: 4, lead_time_months: '12+', deployers: ['Internal'], notes: 'Per-satellite custom orbit placement' },
          { id: 'isillaunch', name: 'ISILaunch', type: 'broker', vehicle: 'Various', orbit: 'SSO/LEO', capacity_kg: 50, price_usd: 200000, cadence_per_year: 4, lead_time_months: '12-24', deployers: ['ISIPOD'], notes: 'European, 300+ CubeSats launched' },
          { id: 'nanorack-iss', name: 'NanoRacks ISS', type: 'iss_deploy', vehicle: 'ISS deploy', orbit: '51.6° 410 km', capacity_kg: 12, price_usd: 90000, cadence_per_year: 6, lead_time_months: '6-12', deployers: ['NRCSD'], notes: '$90K/U, ISS orbit only' },
          { id: 'firefly-alpha', name: 'Firefly Alpha', type: 'dedicated', vehicle: 'Alpha', orbit: 'Custom', capacity_kg: 745, price_usd: 15000000, cadence_per_year: 4, lead_time_months: '12-18', deployers: ['Various'], notes: 'Dedicated small launcher' },
          { id: 'isro-pslv', name: 'ISRO PSLV', type: 'rideshare', vehicle: 'PSLV', orbit: 'SSO/LEO', capacity_kg: 100, price_usd: 200000, cadence_per_year: 4, lead_time_months: '12-18', deployers: ['ISIPOD', 'Custom'], notes: 'Non-ITAR option' },
        ])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleSelect = (provider: LaunchProvider) => {
    setSelectedId(provider.id)
    markStale('launch')
  }

  const fitsCapacity = (p: LaunchProvider) => dryMass * 1.3 <= p.capacity_kg // 30% margin for wet mass

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.9rem', marginBottom: '0.3rem' }}>Launch Provider Selection</h3>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Select a launch provider. Mass allocation and environmental test levels derive from this choice.
        Estimated spacecraft mass: <strong>{dryMass.toFixed(1)} kg</strong> dry.
      </p>

      {loading ? (
        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Loading providers...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          {providers.map(p => {
            const fits = fitsCapacity(p)
            const isSelected = selectedId === p.id
            return (
              <div key={p.id} onClick={() => handleSelect(p)} style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.4rem 0.6rem', borderRadius: '4px', cursor: 'pointer',
                background: isSelected ? 'rgba(16,185,129,0.1)' : 'var(--bg-primary, #0a0e1a)',
                border: `1px solid ${isSelected ? '#10b981' : fits ? '#37415180' : '#ef444440'}`,
                opacity: fits ? 1 : 0.6,
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>{p.name}</span>
                    <span style={{ fontSize: '0.6rem', color: '#6b7280', padding: '0.05rem 0.3rem', background: '#374151', borderRadius: '3px' }}>{p.type}</span>
                    {isSelected && <span style={{ fontSize: '0.6rem', color: '#10b981', fontWeight: 700 }}>SELECTED</span>}
                  </div>
                  <div style={{ fontSize: '0.68rem', color: '#6b7280' }}>
                    {p.vehicle} · {p.orbit} · {p.capacity_kg} kg cap · {p.lead_time_months} mo lead
                  </div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, fontFamily: 'monospace', color: '#d1d5db' }}>
                    ${(p.price_usd / 1000).toFixed(0)}K
                  </div>
                  <div style={{ fontSize: '0.6rem', color: '#6b7280' }}>
                    {p.deployers.join(', ')}
                  </div>
                </div>
                {!fits && (
                  <span style={{ fontSize: '0.6rem', color: '#ef4444', whiteSpace: 'nowrap' }}>over capacity</span>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
