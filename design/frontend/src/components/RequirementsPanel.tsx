import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'

function OrbitTradeAdvisor({ onSelect }: { onSelect: (alt: number, inc: number) => void }) {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const runTrade = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/lifecycle/orbit-trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_gsd_m: 10, target_revisit_days: 3, min_lifetime_years: 3 }),
      })
      if (res.ok) setResult(await res.json())
    } catch {}
    setLoading(false)
  }

  return (
    <div className="card" style={{ borderLeft: '3px solid #8b5cf6' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ fontSize: '0.85rem', margin: 0 }}>Orbit Selection Advisor</h3>
        <button className="btn btn-sm" onClick={runTrade} disabled={loading}
          style={{ fontSize: '0.7rem' }}>
          {loading ? 'Computing...' : result ? 'Recompute' : 'Show orbit options'}
        </button>
      </div>
      {!result && (
        <p style={{ fontSize: '0.75rem', color: '#9ca3af', margin: '0.3rem 0 0' }}>
          Click to compute orbit options based on your GSD, revisit, and lifetime needs.
          Results will pre-populate the orbit fields below.
        </p>
      )}
      {result && (
        <div style={{ marginTop: '0.4rem' }}>
          <div style={{ fontSize: '0.72rem', color: '#d1d5db', marginBottom: '0.3rem' }}>
            {result.recommendation?.split('.')[0]}.
          </div>
          <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
            {result.candidates?.slice(0, 5).map((c: any) => (
              <div key={c.name} style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.2rem 0.3rem',
                fontSize: '0.72rem', borderRadius: '3px', marginBottom: '0.15rem',
                background: c.rank === 1 ? 'rgba(139,92,246,0.1)' : 'transparent',
              }}>
                <span style={{ color: '#6b7280', width: 18 }}>#{c.rank}</span>
                <span style={{ flex: 1, fontWeight: c.rank === 1 ? 600 : 400 }}>{c.name}</span>
                <span style={{ color: c.meets_gsd ? '#10b981' : '#ef4444', fontSize: '0.65rem' }}>{c.achievable_gsd_m}m</span>
                <span style={{ color: c.meets_revisit ? '#10b981' : '#ef4444', fontSize: '0.65rem' }}>{c.revisit_days}d</span>
                <span style={{ fontFamily: 'monospace', fontSize: '0.65rem', color: '#8b5cf6' }}>{(c.total_score * 100).toFixed(0)}%</span>
                <button onClick={() => onSelect(c.altitude_km, c.inclination_deg)}
                  style={{
                    background: 'none', border: '1px solid #374151', borderRadius: '3px',
                    color: '#3b82f6', cursor: 'pointer', fontSize: '0.6rem', padding: '0.1rem 0.3rem',
                  }}>Use</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ClassAdvisor({ onSelect }: { onSelect: (cls: string) => void }) {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const runAdvisor = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/lifecycle/class-advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_gsd_m: 10, target_lifetime_years: 3, max_budget_meur: 10 }),
      })
      if (res.ok) setResult(await res.json())
    } catch {}
    setLoading(false)
  }

  return (
    <div className="card" style={{ borderLeft: '3px solid #06b6d4' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ fontSize: '0.85rem', margin: 0 }}>Mission Class Advisor</h3>
        <button className="btn btn-sm" onClick={runAdvisor} disabled={loading}
          style={{ fontSize: '0.7rem' }}>
          {loading ? 'Computing...' : result ? 'Recompute' : 'What class fits?'}
        </button>
      </div>
      {result && (
        <div style={{ marginTop: '0.3rem' }}>
          <div style={{ fontSize: '0.72rem', color: '#d1d5db', marginBottom: '0.3rem' }}>
            {result.recommendation?.split('.')[0]}.
          </div>
          {result.classes?.slice(0, 3).map((c: any) => (
            <div key={c.class} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', marginBottom: '0.1rem' }}>
              <span style={{ fontWeight: 600, flex: 1 }}>{c.name}</span>
              <span style={{ color: c.fit_percent >= 80 ? '#10b981' : c.fit_percent >= 50 ? '#f59e0b' : '#ef4444' }}>
                {c.fit_percent}% fit
              </span>
              <span style={{ color: '#6b7280', fontSize: '0.65rem' }}>{c.cost_range_meur[0]}-{c.cost_range_meur[1]} MEUR</span>
              <button onClick={() => onSelect(c.class)}
                style={{
                  background: 'none', border: '1px solid #374151', borderRadius: '3px',
                  color: '#3b82f6', cursor: 'pointer', fontSize: '0.6rem', padding: '0.1rem 0.3rem',
                }}>Use</button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function RequirementsPanel() {
  const { requirements, setRequirements, setOrbit, runDesign, isRunning } = useDesignStore()

  const handleOrbitSelect = (alt: number, inc: number) => {
    setOrbit({ altitude_km: alt, inclination_deg: inc, orbit_type: 'sso' as any })
  }

  const handleClassSelect = (cls: string) => {
    setRequirements({ spacecraft_class: cls })
  }

  return (
    <div>
      <h2>Mission Requirements</h2>

      {/* Decision support BEFORE the form fields */}
      <OrbitTradeAdvisor onSelect={handleOrbitSelect} />
      <ClassAdvisor onSelect={handleClassSelect} />

      <div className="card">
        <h3>Mission</h3>
        <div className="form-group">
          <label>Name</label>
          <input
            className="input"
            value={requirements.name}
            onChange={(e) => setRequirements({ name: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label>Type</label>
          <select
            className="select"
            value={requirements.mission_type}
            onChange={(e) => setRequirements({ mission_type: e.target.value })}
          >
            <option value="earth_observation">Earth Observation</option>
            <option value="communications">Communications</option>
            <option value="science_planetary">Science (Planetary)</option>
            <option value="science_astrophysics">Science (Astrophysics)</option>
            <option value="technology_demo">Technology Demo</option>
            <option value="lunar">Lunar</option>
            <option value="mars">Mars</option>
          </select>
        </div>
        <div className="form-group">
          <label>Spacecraft Class</label>
          <select
            className="select"
            value={requirements.spacecraft_class}
            onChange={(e) => setRequirements({ spacecraft_class: e.target.value })}
          >
            <option value="nano">Nano (1-20 kg)</option>
            <option value="micro">Micro (20-100 kg)</option>
            <option value="small">Small (100-500 kg)</option>
            <option value="medium">Medium (500-2000 kg)</option>
            <option value="large">Large (2000-5000 kg)</option>
            <option value="flagship">Flagship (5000+ kg)</option>
          </select>
        </div>
      </div>

      <div className="card">
        <h3>Orbit</h3>
        <div className="form-group">
          <label>Type</label>
          <select
            className="select"
            value={requirements.orbit.orbit_type}
            onChange={(e) => setOrbit({ orbit_type: e.target.value })}
          >
            <option value="leo">LEO</option>
            <option value="sso">SSO</option>
            <option value="meo">MEO</option>
            <option value="geo">GEO</option>
            <option value="lunar">Lunar</option>
            <option value="interplanetary">Interplanetary</option>
          </select>
        </div>
        <div className="form-group">
          <label>Altitude (km)</label>
          <input
            className="input"
            type="number"
            value={requirements.orbit.altitude_km}
            onChange={(e) => setOrbit({ altitude_km: Number(e.target.value) })}
          />
        </div>
        <div className="form-group">
          <label>Inclination (deg)</label>
          <input
            className="input"
            type="number"
            step="0.1"
            value={requirements.orbit.inclination_deg}
            onChange={(e) => setOrbit({ inclination_deg: Number(e.target.value) })}
          />
        </div>
        <div className="form-group">
          <label>Mission Duration (years)</label>
          <input
            className="input"
            type="number"
            step="0.5"
            value={requirements.orbit.mission_duration_years}
            onChange={(e) => setOrbit({ mission_duration_years: Number(e.target.value) })}
          />
        </div>
      </div>

      <div className="card">
        <h3>Payload</h3>
        {requirements.payloads.map((pl, i) => (
          <div key={i}>
            <div className="form-group">
              <label>Name</label>
              <input
                className="input"
                value={pl.name}
                onChange={(e) => {
                  const payloads = [...requirements.payloads]
                  payloads[i] = { ...payloads[i], name: e.target.value }
                  setRequirements({ payloads })
                }}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div className="form-group">
                <label>Mass (kg)</label>
                <input className="input" type="number" value={pl.mass_kg}
                  onChange={(e) => {
                    const payloads = [...requirements.payloads]
                    payloads[i] = { ...payloads[i], mass_kg: Number(e.target.value) }
                    setRequirements({ payloads })
                  }} />
              </div>
              <div className="form-group">
                <label>Power (W)</label>
                <input className="input" type="number" value={pl.power_w}
                  onChange={(e) => {
                    const payloads = [...requirements.payloads]
                    payloads[i] = { ...payloads[i], power_w: Number(e.target.value) }
                    setRequirements({ payloads })
                  }} />
              </div>
              <div className="form-group">
                <label>Data Rate (Mbps)</label>
                <input className="input" type="number" value={pl.data_rate_mbps}
                  onChange={(e) => {
                    const payloads = [...requirements.payloads]
                    payloads[i] = { ...payloads[i], data_rate_mbps: Number(e.target.value) }
                    setRequirements({ payloads })
                  }} />
              </div>
              <div className="form-group">
                <label>Pointing (deg)</label>
                <input className="input" type="number" step="0.01" value={pl.pointing_accuracy_deg}
                  onChange={(e) => {
                    const payloads = [...requirements.payloads]
                    payloads[i] = { ...payloads[i], pointing_accuracy_deg: Number(e.target.value) }
                    setRequirements({ payloads })
                  }} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Targets</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <div className="form-group">
            <label>Mass (kg)</label>
            <input className="input" type="number" value={requirements.target_mass_kg || ''}
              onChange={(e) => setRequirements({ target_mass_kg: Number(e.target.value) || undefined })} />
          </div>
          <div className="form-group">
            <label>Cost (MEUR)</label>
            <input className="input" type="number" value={requirements.target_cost_meur || ''}
              onChange={(e) => setRequirements({ target_cost_meur: Number(e.target.value) || undefined })} />
          </div>
        </div>
      </div>

      <button className="btn" onClick={runDesign} disabled={isRunning} style={{ width: '100%' }}>
        {isRunning ? 'Running Design Loop...' : 'Run Design'}
      </button>
    </div>
  )
}
