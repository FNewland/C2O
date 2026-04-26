import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useSensitivity, useEOLCurves } from '../hooks/useSession'

const SWEEP_PARAMS = [
  { id: 'orbit.altitude_km', label: 'Orbit altitude (km)', min: 300, max: 800 },
  { id: 'payloads.0.mass_kg', label: 'Payload mass (kg)', min: 1, max: 200 },
  { id: 'payloads.0.power_w', label: 'Payload power (W)', min: 5, max: 500 },
  { id: 'payloads.0.data_rate_mbps', label: 'Payload data rate (Mbps)', min: 1, max: 1000 },
  { id: 'design_lifetime_years', label: 'Mission duration (years)', min: 1, max: 15 },
]

const KEY_METRICS = [
  { id: 'mass.dry_mass_kg', label: 'Dry mass (kg)', color: '#3b82f6' },
  { id: 'power.sa_power_eol_w', label: 'SA power EOL (W)', color: '#10b981' },
  { id: 'cost.total_meur', label: 'Cost (MEUR)', color: '#f59e0b' },
  { id: 'link.downlink_margin_db', label: 'Link margin (dB)', color: '#8b5cf6' },
]

export function TradeStudyPanel({ studyId }: { studyId: string | null }) {
  const [sweepParam, setSweepParam] = useState(SWEEP_PARAMS[0].id)
  const [numPoints, setNumPoints] = useState(10)
  const sensitivity = useSensitivity()
  const eol = useEOLCurves(studyId)

  const meta = SWEEP_PARAMS.find(p => p.id === sweepParam)
  const [minVal, setMinVal] = useState(meta?.min || 0)
  const [maxVal, setMaxVal] = useState(meta?.max || 100)

  const runSweep = () => {
    if (!studyId) return
    sensitivity.mutate({
      sweep_param: sweepParam,
      sweep_min: minVal,
      sweep_max: maxVal,
      num_points: numPoints,
      study_id: studyId,
    })
  }

  // Transform sensitivity result into recharts data
  const sweepData = (sensitivity.data as any)?.points
    ? ((sensitivity.data as any).points as any[]).map((p: any) => ({
        sweep: p.sweep_value,
        ...p.key_params,
      }))
    : []

  // EOL degradation data
  const eolData = (eol.data as any)?.curves || []

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Trade Studies & Sensitivity</h2>

      {/* Sensitivity controls */}
      <div className="card">
        <h3>Parameter Sweep</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <div className="form-group">
            <label>Parameter</label>
            <select className="select" value={sweepParam} onChange={e => {
              const next = SWEEP_PARAMS.find(p => p.id === e.target.value)
              if (next) {
                setSweepParam(next.id)
                setMinVal(next.min)
                setMaxVal(next.max)
              }
            }}>
              {SWEEP_PARAMS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Min</label>
            <input className="input" type="number" value={minVal} onChange={e => setMinVal(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>Max</label>
            <input className="input" type="number" value={maxVal} onChange={e => setMaxVal(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>Points</label>
            <input className="input" type="number" min={3} max={40} value={numPoints} onChange={e => setNumPoints(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>&nbsp;</label>
            <button className="btn" onClick={runSweep} disabled={sensitivity.isPending || !studyId}>
              {sensitivity.isPending ? 'Running...' : 'Run Sweep'}
            </button>
          </div>
        </div>

        {sensitivity.data && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)', marginBottom: '0.5rem' }}>
            Swept {numPoints} points in {(sensitivity.data as any).total_time_ms?.toFixed(0) || '?'}ms
          </div>
        )}

        {sweepData.length > 0 && (
          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer>
              <LineChart data={sweepData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="sweep" tick={{ fontSize: 10, fill: '#9ca3af' }} label={{ value: meta?.label || 'Sweep', position: 'insideBottom', offset: -5, fill: '#9ca3af', fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} />
                <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', fontSize: '0.75rem' }} />
                <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                {KEY_METRICS.map(m => (
                  <Line key={m.id} type="monotone" dataKey={m.id} name={m.label} stroke={m.color} strokeWidth={2} dot={{ r: 3 }} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* EOL degradation curves */}
      <div className="card">
        <h3>End-of-Life Degradation</h3>
        {eolData.length === 0 ? (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)' }}>Select a study to view EOL curves.</div>
        ) : (
          <div style={{ width: '100%', height: '260px' }}>
            <ResponsiveContainer>
              <LineChart data={eolData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#9ca3af' }} label={{ value: 'Mission year', position: 'insideBottom', offset: -5, fill: '#9ca3af', fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} />
                <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', fontSize: '0.75rem' }} />
                <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                <Line type="monotone" dataKey="sa_power_w" name="SA power (W)" stroke="#3b82f6" strokeWidth={2} />
                <Line type="monotone" dataKey="battery_capacity_wh" name="Battery (Wh)" stroke="#10b981" strokeWidth={2} />
                <Line type="monotone" dataKey="link_margin_db" name="Link margin (dB)" stroke="#8b5cf6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}
