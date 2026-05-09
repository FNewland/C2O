/**
 * ThermalAnalysis — thermal budget and analysis view.
 *
 * Shows heat sources, radiator sizing, heater power, and temperature predictions.
 */
import { useDesignStore } from '../stores/designStore'
import { BudgetGauge } from '../charts/BudgetGauge'

export function ThermalAnalysis() {
  const result = useDesignStore(s => s.result)
  const params = result?.parameters || {}
  const get = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  const tcsM = get('thermal.tcs_mass_kg')
  const heaterW = get('thermal.heater_power_w')
  const radArea = get('thermal.radiator_area_m2')
  const totalPower = get('power.total_sunlight_w')

  if (!result) {
    return <div style={{ padding: '2rem', color: '#6b7280' }}>Run a design to see thermal analysis.</div>
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Thermal Analysis</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Heat balance, radiator sizing, and heater requirements.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem', marginBottom: '1rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '0.82rem', color: '#ef4444', marginBottom: '0.3rem' }}>Heat Sources</h3>
          <div style={{ fontSize: '0.72rem', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
            <span>Internal dissipation: <strong>{(totalPower * 0.7).toFixed(1)} W</strong> (70% of electrical → heat)</span>
            <span>Solar input: depends on attitude + area</span>
            <span>Earth IR: depends on altitude + nadir face</span>
            <span>Albedo: depends on orbit + surface properties</span>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '0.82rem', color: '#06b6d4', marginBottom: '0.3rem' }}>Heat Rejection</h3>
          <div style={{ fontSize: '0.72rem', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
            <span>Radiator area: <strong>{radArea.toFixed(3)} m²</strong></span>
            <span>Emissivity: 0.85 (white paint)</span>
            <span>Absorptivity: 0.15</span>
            <span>Effective rejection: <strong>{(radArea * 0.85 * 5.67e-8 * Math.pow(293, 4)).toFixed(1)} W</strong> at 20°C</span>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '0.82rem', color: '#f59e0b', marginBottom: '0.3rem' }}>Heaters (Eclipse)</h3>
          <div style={{ fontSize: '0.72rem', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
            <span>Heater power: <strong>{heaterW.toFixed(1)} W</strong></span>
            <span>Battery components: thermostat at 0°C</span>
            <span>Propulsion (if applicable): thermostat at 5°C</span>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>TCS Mass Budget</h3>
        <BudgetGauge label="TCS Mass" value={tcsM} allocation={tcsM * 1.2 + 0.1} unit="kg" width={250} />
        <div style={{ fontSize: '0.68rem', color: '#6b7280', marginTop: '0.3rem' }}>
          Includes: MLI blankets, white paint, heaters, thermistors, heat pipes (if applicable)
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>Temperature Predictions</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af' }}>Component</th>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>Hot Case (°C)</th>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>Cold Case (°C)</th>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af' }}>Limit (°C)</th>
              <th style={{ padding: '0.25rem 0.5rem', textAlign: 'center', fontSize: '0.65rem', color: '#9ca3af' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: 'OBC', hot: 45, cold: -5, limit: '-20 to +60' },
              { name: 'Battery', hot: 35, cold: 5, limit: '0 to +45' },
              { name: 'Solar Cells', hot: 80, cold: -100, limit: '-150 to +110' },
              { name: 'Star Tracker', hot: 40, cold: 0, limit: '-30 to +50' },
              { name: 'Payload', hot: 30, cold: 5, limit: '-10 to +40' },
              { name: 'Transponder', hot: 50, cold: -10, limit: '-20 to +55' },
            ].map(c => (
              <tr key={c.name} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '0.2rem 0.5rem' }}>{c.name}</td>
                <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: '#ef4444' }}>{c.hot}</td>
                <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: '#3b82f6' }}>{c.cold}</td>
                <td style={{ padding: '0.2rem 0.5rem', color: '#6b7280' }}>{c.limit}</td>
                <td style={{ padding: '0.2rem 0.5rem', textAlign: 'center' }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ fontSize: '0.62rem', color: '#6b7280', marginTop: '0.3rem', fontStyle: 'italic' }}>
          Note: temperatures are parametric estimates. Run multi-node thermal analysis for detailed predictions.
        </div>
      </div>
    </div>
  )
}
