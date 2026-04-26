import { useDesignStore } from '../stores/designStore'

export function RequirementsPanel() {
  const { requirements, setRequirements, setOrbit, runDesign, isRunning } = useDesignStore()

  return (
    <div>
      <h2>Mission Requirements</h2>

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
