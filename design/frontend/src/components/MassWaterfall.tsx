import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts'

const SUBSYSTEM_COLORS: Record<string, string> = {
  Payload: '#10b981',
  EPS: '#f59e0b',
  AOCS: '#06b6d4',
  TTC: '#ec4899',
  TCS: '#ef4444',
  Structure: '#84cc16',
  'Prop (dry)': '#f97316',
  Propellant: '#a855f7',
  OBDH: '#8b5cf6',
  Margin: '#374151',
}

interface Props {
  parameters: Record<string, { value: number | string; unit?: string }>
}

export function MassWaterfall({ parameters }: Props) {
  const data = useMemo(() => {
    const get = (id: string) => {
      const p = parameters[id]
      return p && typeof p.value === 'number' ? p.value : 0
    }

    const payload = get('mass.payload_kg')
    const eps = get('power.eps_mass_kg')
    const aocs = get('aocs.mass_kg')
    const ttc = get('link.ttc_mass_kg')
    const tcs = get('thermal.tcs_mass_kg')
    const structure = get('structure.mass_kg')
    const propDry = get('propulsion.total_mass_kg') - get('propulsion.propellant_mass_kg')
    const propellant = get('propulsion.propellant_mass_kg')
    const obdh = get('data.obdh_mass_kg')
    const dryMass = get('mass.dry_mass_kg')
    const wetMass = get('mass.wet_mass_kg')

    const items = [
      { name: 'Payload', value: payload },
      { name: 'EPS', value: eps },
      { name: 'AOCS', value: aocs },
      { name: 'TTC', value: ttc },
      { name: 'TCS', value: tcs },
      { name: 'Structure', value: structure },
      { name: 'OBDH', value: obdh },
      { name: 'Prop (dry)', value: Math.max(0, propDry) },
      { name: 'Propellant', value: propellant },
    ].filter(d => d.value > 0.01)

    return { items, dryMass, wetMass }
  }, [parameters])

  if (data.items.length === 0) return null

  return (
    <div style={{ background: 'var(--bg-secondary, #1f2937)', borderRadius: '8px', padding: '0.75rem', border: '1px solid var(--border, #374151)' }}>
      <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>Mass Breakdown</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data.items} layout="vertical" margin={{ left: 60, right: 20, top: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
          <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} unit=" kg" />
          <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} width={65} />
          <Tooltip
            contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', fontSize: '0.8rem' }}
            formatter={(v: number) => [`${v.toFixed(2)} kg`]}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.items.map((entry) => (
              <Cell key={entry.name} fill={SUBSYSTEM_COLORS[entry.name] || '#6b7280'} />
            ))}
          </Bar>
          {data.dryMass > 0 && (
            <ReferenceLine x={data.dryMass} stroke="#10b981" strokeDasharray="5 3" label={{ value: `Dry ${data.dryMass.toFixed(1)}`, fill: '#10b981', fontSize: 10, position: 'top' }} />
          )}
        </BarChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem', justifyContent: 'center' }}>
        <span>Dry: <strong style={{ color: '#10b981' }}>{data.dryMass.toFixed(1)} kg</strong></span>
        <span>Wet: <strong style={{ color: '#3b82f6' }}>{data.wetMass.toFixed(1)} kg</strong></span>
      </div>
    </div>
  )
}
