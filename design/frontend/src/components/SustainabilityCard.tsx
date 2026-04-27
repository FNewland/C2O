import { useMemo } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'

interface Props {
  parameters: Record<string, { value: number | string; unit?: string }>
}

const GRADE_COLORS: Record<string, string> = {
  A: '#10b981', B: '#3b82f6', C: '#f59e0b', D: '#f97316', F: '#ef4444',
}

function TrafficLight({ label, on }: { label: string; on: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem' }}>
      <div style={{
        width: 12, height: 12, borderRadius: '50%',
        background: on ? '#10b981' : '#ef4444',
        border: '1px solid rgba(255,255,255,0.15)',
      }} />
      <span style={{ color: on ? '#10b981' : '#ef4444' }}>{label}</span>
    </div>
  )
}

export function SustainabilityCard({ parameters }: Props) {
  const get = (id: string): number => {
    const p = parameters[id]
    return p && typeof p.value === 'number' ? p.value : 0
  }
  const getStr = (id: string): string => {
    const p = parameters[id]
    return p ? String(p.value) : ''
  }

  const grade = getStr('sustainability.grade') || '?'
  const score = get('sustainability.score')
  const gradeColor = GRADE_COLORS[grade] || '#6b7280'

  const radarData = useMemo(() => [
    { subject: 'Orbit', value: get('sustainability.orbit_responsibility') / 25 * 100, fullMark: 100 },
    { subject: 'EOL', value: get('sustainability.eol_readiness') / 25 * 100, fullMark: 100 },
    { subject: 'Track', value: get('sustainability.trackability') / 20 * 100, fullMark: 100 },
    { subject: 'Collision', value: get('sustainability.collision_preparedness') / 15 * 100, fullMark: 100 },
    { subject: 'Efficiency', value: get('sustainability.mission_index') / 15 * 100, fullMark: 100 },
  ], [parameters])

  const lifetime = get('debris.lifetime_years')
  const c25 = get('debris.compliant_25yr') === 1
  const c5 = get('debris.compliant_5yr') === 1
  const passivation = get('debris.passivation_score')

  // Don't render if no sustainability data
  if (!parameters['sustainability.grade']) return null

  return (
    <div style={{
      background: 'var(--bg-secondary, #1f2937)', borderRadius: '8px', padding: '0.75rem',
      border: '1px solid var(--border, #374151)',
    }}>
      <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>Sustainability</h3>

      {/* Grade + Score */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
        <div style={{
          fontSize: '3rem', fontWeight: 800, lineHeight: 1, color: gradeColor,
          width: 60, textAlign: 'center',
        }}>
          {grade}
        </div>
        <div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'monospace' }}>{score}/100</div>
          <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Sustainability Score</div>
        </div>
      </div>

      {/* Radar chart */}
      <ResponsiveContainer width="100%" height={180}>
        <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 9 }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
          <Radar dataKey="value" stroke={gradeColor} fill={gradeColor} fillOpacity={0.25} strokeWidth={2} />
        </RadarChart>
      </ResponsiveContainer>

      {/* Debris compliance */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '0.25rem' }}>
        <TrafficLight label="25-yr rule" on={c25} />
        <TrafficLight label="5-yr rule" on={c5} />
        <span style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
          Lifetime: {lifetime > 1000 ? `${(lifetime / 1000).toFixed(0)}k yr` : `${lifetime.toFixed(1)} yr`}
        </span>
        <span style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
          Passivation: {(passivation * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  )
}
