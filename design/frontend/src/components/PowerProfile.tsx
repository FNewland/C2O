import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface Props {
  parameters: Record<string, { value: number | string; unit?: string }>
}

export function PowerProfile({ parameters }: Props) {
  const data = useMemo(() => {
    const get = (id: string) => {
      const p = parameters[id]
      return p && typeof p.value === 'number' ? p.value : 0
    }

    return [
      { name: 'Sunlight\nDemand', demand: get('power.total_sunlight_w'), generation: 0 },
      { name: 'Eclipse\nDemand', demand: get('power.total_eclipse_w'), generation: 0 },
      { name: 'SA BOL', demand: 0, generation: get('power.sa_power_bol_w') },
      { name: 'SA EOL', demand: 0, generation: get('power.sa_power_eol_w') },
    ]
  }, [parameters])

  const get = (id: string) => {
    const p = parameters[id]
    return p && typeof p.value === 'number' ? p.value : 0
  }

  const batteryWh = get('power.battery_capacity_wh')
  const saArea = get('power.sa_area_m2')
  const sunlightDemand = get('power.total_sunlight_w')
  const saEol = get('power.sa_power_eol_w')
  const marginW = saEol - sunlightDemand
  const marginPct = sunlightDemand > 0 ? (marginW / sunlightDemand * 100) : 0

  if (saEol === 0 && sunlightDemand === 0) return null

  return (
    <div style={{ background: 'var(--bg-secondary, #1f2937)', borderRadius: '8px', padding: '0.75rem', border: '1px solid var(--border, #374151)' }}>
      <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>Power Budget</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ left: 10, right: 10, top: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} />
          <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} unit=" W" />
          <Tooltip
            contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', fontSize: '0.8rem' }}
            formatter={(v: number, name: string) => [v > 0 ? `${v.toFixed(1)} W` : '', name]}
          />
          <Legend wrapperStyle={{ fontSize: '0.7rem' }} />
          <Bar dataKey="demand" name="Demand" fill="#f59e0b" radius={[4, 4, 0, 0]} />
          <Bar dataKey="generation" name="Generation" fill="#10b981" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem', justifyContent: 'center', flexWrap: 'wrap' }}>
        <span>Battery: <strong style={{ color: '#3b82f6' }}>{batteryWh.toFixed(0)} Wh</strong></span>
        <span>SA Area: <strong>{saArea.toFixed(3)} m²</strong></span>
        <span>Margin: <strong style={{ color: marginPct > 20 ? '#10b981' : marginPct > 0 ? '#f59e0b' : '#ef4444' }}>
          {marginW.toFixed(1)} W ({marginPct.toFixed(0)}%)
        </strong></span>
      </div>
    </div>
  )
}
