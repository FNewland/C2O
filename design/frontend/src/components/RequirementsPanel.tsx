import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'

function OrbitTradeAdvisor({ onSelect }: { onSelect: (alt: number, inc: number) => void }) {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [gsd, setGsd] = useState(10)
  const [revisit, setRevisit] = useState(3)
  const [lifetime, setLifetime] = useState(3)
  const [latMin, setLatMin] = useState(-30)
  const [latMax, setLatMax] = useState(30)
  const [maxCost, setMaxCost] = useState(10)
  const [aperture, setAperture] = useState(0.15)

  const runTrade = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/lifecycle/orbit-trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_gsd_m: gsd, target_revisit_days: revisit,
          min_lifetime_years: lifetime, max_cost_meur: maxCost,
          aperture_m: aperture,
          target_latitude_band: [latMin, latMax],
        }),
      })
      if (res.ok) setResult(await res.json())
    } catch {}
    setLoading(false)
  }

  return (
    <div className="card" style={{ borderLeft: '3px solid #8b5cf6' }}>
      <h3 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Orbit Selection Advisor</h3>
      <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Set your performance needs. The advisor computes candidate orbits with coverage,
        resolution, lifetime, debris compliance, and launch cost for each.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label>GSD target (m)</label>
          <input className="input" type="number" min={0.1} step={1} value={gsd} onChange={e => setGsd(Number(e.target.value) || 10)} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Revisit (days)</label>
          <input className="input" type="number" min={0.1} step={1} value={revisit} onChange={e => setRevisit(Number(e.target.value) || 3)} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Min lifetime (years)</label>
          <input className="input" type="number" min={0.5} step={0.5} value={lifetime} onChange={e => setLifetime(Number(e.target.value) || 3)} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Aperture (m)</label>
          <input className="input" type="number" min={0.01} step={0.01} value={aperture} onChange={e => setAperture(Number(e.target.value) || 0.15)} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Target latitude (°)</label>
          <div style={{ display: 'flex', gap: '0.25rem' }}>
            <input className="input" type="number" min={-90} max={90} value={latMin} onChange={e => setLatMin(Number(e.target.value))} style={{ width: '50%' }} placeholder="min" />
            <input className="input" type="number" min={-90} max={90} value={latMax} onChange={e => setLatMax(Number(e.target.value))} style={{ width: '50%' }} placeholder="max" />
          </div>
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Max budget (MEUR)</label>
          <input className="input" type="number" min={1} step={1} value={maxCost} onChange={e => setMaxCost(Number(e.target.value) || 10)} />
        </div>
      </div>
      <button className="btn btn-sm" onClick={runTrade} disabled={loading} style={{ marginBottom: '0.5rem' }}>
        {loading ? 'Computing...' : 'Compute Orbit Options'}
      </button>
      {result && (
        <div>
          <div style={{ fontSize: '0.78rem', color: '#d1d5db', marginBottom: '0.4rem' }}>
            {result.recommendation?.split('.').slice(0, 2).join('.')}.
          </div>
          <table style={{ width: '100%', fontSize: '0.75rem', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ color: '#9ca3af', textAlign: 'left', fontSize: '0.68rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '0.25rem' }}>#</th>
                <th style={{ padding: '0.25rem' }}>Orbit</th>
                <th style={{ padding: '0.25rem' }}>GSD</th>
                <th style={{ padding: '0.25rem' }}>Revisit</th>
                <th style={{ padding: '0.25rem' }}>Lifetime</th>
                <th style={{ padding: '0.25rem' }}>5yr rule</th>
                <th style={{ padding: '0.25rem' }}>Contact</th>
                <th style={{ padding: '0.25rem' }}>Launch</th>
                <th style={{ padding: '0.25rem' }}>Score</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {result.candidates?.slice(0, 8).map((c: any) => (
                <tr key={c.name} style={{ borderTop: '1px solid #374151' }}>
                  <td style={{ padding: '0.25rem', color: '#6b7280' }}>{c.rank}</td>
                  <td style={{ padding: '0.25rem', fontWeight: c.rank <= 3 ? 600 : 400 }}>{c.name}</td>
                  <td style={{ padding: '0.25rem', color: c.meets_gsd ? '#10b981' : '#ef4444' }}>{c.achievable_gsd_m}m</td>
                  <td style={{ padding: '0.25rem', color: c.meets_revisit ? '#10b981' : '#ef4444' }}>{c.revisit_days}d</td>
                  <td style={{ padding: '0.25rem' }}>{c.natural_lifetime_years > 1000 ? '>1000yr' : c.natural_lifetime_years + 'yr'}</td>
                  <td style={{ padding: '0.25rem', color: c.compliant_5yr ? '#10b981' : '#ef4444' }}>{c.compliant_5yr ? 'Yes' : 'No'}</td>
                  <td style={{ padding: '0.25rem' }}>{c.contact_min_per_day}min</td>
                  <td style={{ padding: '0.25rem' }}>{c.launch_cost_keur}k</td>
                  <td style={{ padding: '0.25rem', fontFamily: 'monospace', color: '#8b5cf6' }}>{(c.total_score * 100).toFixed(0)}%</td>
                  <td style={{ padding: '0.25rem' }}>
                    <button onClick={() => onSelect(c.altitude_km, c.inclination_deg)}
                      style={{ background: 'none', border: '1px solid #374151', borderRadius: '3px', color: '#3b82f6', cursor: 'pointer', fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                      Use
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function ClassAdvisor({ onSelect }: { onSelect: (cls: string, massRange: number[], costRange: number[]) => void }) {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [gsd, setGsd] = useState<number | undefined>(10)
  const [lifetime, setLifetime] = useState<number | undefined>(3)
  const [budget, setBudget] = useState<number | undefined>(10)
  const [schedule, setSchedule] = useState<number | undefined>(18)
  const [pointing, setPointing] = useState<number | undefined>(0.1)
  const [dataRate, setDataRate] = useState<number | undefined>(100)

  const runAdvisor = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/lifecycle/class-advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_gsd_m: gsd, target_lifetime_years: lifetime,
          max_budget_meur: budget, max_schedule_months: schedule,
          target_pointing_deg: pointing, target_data_rate_mbps: dataRate,
        }),
      })
      if (res.ok) setResult(await res.json())
    } catch {}
    setLoading(false)
  }

  return (
    <div className="card" style={{ borderLeft: '3px solid #06b6d4' }}>
      <h3 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Mission Class Advisor</h3>
      <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Enter what you know — all fields are optional. The advisor recommends
        which spacecraft class fits and sets realistic mass/cost targets.
        Leave fields blank if unknown; the advisor will use typical values.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label>GSD target (m) <span style={{ color: '#6b7280', fontWeight: 400 }}>— optical only</span></label>
          <input className="input" type="number" min={0.1} step={1} value={gsd ?? ''} placeholder="e.g. 10" onChange={e => setGsd(e.target.value ? Number(e.target.value) : undefined)} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Lifetime (years)</label>
          <input className="input" type="number" min={0.5} step={0.5} value={lifetime ?? ''} placeholder="e.g. 3" onChange={e => setLifetime(e.target.value ? Number(e.target.value) : undefined)} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Max budget (MEUR) <span style={{ color: '#6b7280', fontWeight: 400 }}>— optional</span></label>
          <input className="input" type="number" min={0.5} step={1} value={budget ?? ''} placeholder="e.g. 10" onChange={e => setBudget(e.target.value ? Number(e.target.value) : undefined)} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Schedule (months) <span style={{ color: '#6b7280', fontWeight: 400 }}>— optional</span></label>
          <input className="input" type="number" min={3} step={3} value={schedule ?? ''} placeholder="e.g. 18" onChange={e => setSchedule(e.target.value ? Number(e.target.value) : undefined)} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Pointing (deg) <span style={{ color: '#6b7280', fontWeight: 400 }}>— optional</span></label>
          <input className="input" type="number" min={0.001} step={0.01} value={pointing ?? ''} placeholder="e.g. 0.1" onChange={e => setPointing(e.target.value ? Number(e.target.value) : undefined)} />
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label>Data rate (Mbps) <span style={{ color: '#6b7280', fontWeight: 400 }}>— optional</span></label>
          <input className="input" type="number" min={0.1} step={10} value={dataRate ?? ''} placeholder="e.g. 100" onChange={e => setDataRate(e.target.value ? Number(e.target.value) : undefined)} />
        </div>
      </div>
      <button className="btn btn-sm" onClick={runAdvisor} disabled={loading} style={{ marginBottom: '0.5rem' }}>
        {loading ? 'Computing...' : 'Compute Class Recommendation'}
      </button>
      {result && (
        <div>
          <div style={{ fontSize: '0.78rem', color: '#d1d5db', marginBottom: '0.4rem' }}>
            {result.recommendation?.split('.')[0]}.
          </div>
          {result.classes?.slice(0, 4).map((c: any) => (
            <div key={c.class} style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.3rem',
              fontSize: '0.78rem', marginBottom: '0.2rem', borderRadius: '4px',
              background: c.fit_percent >= 80 ? 'rgba(16,185,129,0.05)' : 'transparent',
            }}>
              <span style={{ fontWeight: 600, flex: 1 }}>{c.name}</span>
              <span style={{ color: c.fit_percent >= 80 ? '#10b981' : c.fit_percent >= 50 ? '#f59e0b' : '#ef4444', fontWeight: 600 }}>
                {c.fit_percent}%
              </span>
              <span style={{ color: '#6b7280', fontSize: '0.7rem' }}>{c.mass_range_kg[0]}-{c.mass_range_kg[1]}kg</span>
              <span style={{ color: '#6b7280', fontSize: '0.7rem' }}>{c.cost_range_meur[0]}-{c.cost_range_meur[1]}M</span>
              <span style={{ color: '#6b7280', fontSize: '0.7rem' }}>{c.schedule_range_months[0]}-{c.schedule_range_months[1]}mo</span>
              <button onClick={() => onSelect(c.class, c.mass_range_kg, c.cost_range_meur)}
                style={{ background: 'none', border: '1px solid #374151', borderRadius: '3px', color: '#3b82f6', cursor: 'pointer', fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                Use
              </button>
            </div>
          ))}
          {result.classes?.[0]?.gaps?.length > 0 && (
            <div style={{ fontSize: '0.72rem', color: '#f59e0b', marginTop: '0.3rem' }}>
              Gaps: {result.classes[0].gaps.join('; ')}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function RequirementsPanel() {
  const { requirements, setRequirements, setOrbit, runDesign, isRunning } = useDesignStore()

  const [orbitSelected, setOrbitSelected] = useState(false)
  const [classSelected, setClassSelected] = useState(false)

  const handleOrbitSelect = (alt: number, inc: number) => {
    setOrbit({ altitude_km: alt, inclination_deg: inc, orbit_type: 'sso' as any })
    setOrbitSelected(true)
    // Scroll to orbit form to show the change
    setTimeout(() => {
      document.getElementById('orbit-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 100)
  }

  const handleClassSelect = (cls: string, massRange: number[], costRange: number[]) => {
    // Set class AND realistic targets from the class profile
    setRequirements({
      spacecraft_class: cls,
      target_mass_kg: massRange[1],  // Upper end of class range as target
      target_cost_meur: costRange[1], // Upper end as ceiling
    })
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

      <div className="card" id="orbit-form" style={orbitSelected ? { borderLeft: '3px solid #10b981' } : undefined}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <h3 style={{ margin: 0 }}>Orbit</h3>
          {orbitSelected && <span style={{ fontSize: '0.68rem', color: '#10b981', background: 'rgba(16,185,129,0.15)', padding: '0.1rem 0.4rem', borderRadius: '3px' }}>Set from advisor</span>}
        </div>
        <div className="form-group">
          <label>Type</label>
          <select
            className="select"
            value={requirements.orbit.orbit_type}
            onChange={(e) => { setOrbit({ orbit_type: e.target.value }); setOrbitSelected(false) }}
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
        {isRunning ? 'Running Design Loop...' : 'Run Design (solo)'}
      </button>

      {/* Session guidance */}
      <div className="card" style={{ marginTop: '1rem', borderLeft: '3px solid #f59e0b' }}>
        <h3 style={{ fontSize: '0.85rem', color: '#f59e0b', marginBottom: '0.3rem' }}>When do I need a session?</h3>
        <div style={{ fontSize: '0.78rem', color: '#d1d5db', lineHeight: 1.5 }}>
          <p style={{ marginBottom: '0.4rem' }}>
            <strong>Solo design (no session needed):</strong> Click "Run Design" above to converge the design
            on your own. Good for initial exploration and concept sizing.
          </p>
          <p style={{ marginBottom: '0.4rem' }}>
            <strong>Collaborative session (start a session):</strong> Use the "Start Session" button in the
            header bar when you want to:
          </p>
          <ul style={{ paddingLeft: '1.2rem', marginBottom: '0.4rem', color: '#9ca3af' }}>
            <li>Invite team members to edit parameters in real-time</li>
            <li>Select equipment from the component browser (requires session for edits)</li>
            <li>Have multiple engineers working on different subsystems simultaneously</li>
            <li>Record an audit trail of who changed what and why</li>
          </ul>
          <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>
            You can run the design solo first, then start a session to refine it with the team.
          </p>
        </div>
      </div>
    </div>
  )
}
