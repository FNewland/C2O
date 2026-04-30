import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'

const MODE_TYPES = [
  'safe', 'nominal_science', 'downlink', 'slew', 'eclipse',
  'orbit_maintenance', 'commissioning', 'standby', 'peak_science', 'calibration',
]

interface Mode {
  id: string; name: string; mode_type: string
  power_w: number; payload_active: boolean; payload_power_w: number
  platform_power_w: number; heater_power_w: number
  pointing_requirement_deg: number; data_rate_mbps: number
  sun_illuminated: boolean; duty_cycle_percent: number
}

const DEFAULT_MODE: Mode = {
  id: '', name: '', mode_type: 'nominal_science',
  power_w: 50, payload_active: true, payload_power_w: 20,
  platform_power_w: 30, heater_power_w: 5,
  pointing_requirement_deg: 0.1, data_rate_mbps: 0,
  sun_illuminated: true, duty_cycle_percent: 100,
}

export function ConOpsEditor() {
  const [modes, setModes] = useState<Mode[]>([
    { ...DEFAULT_MODE, id: 'safe', name: 'Safe Mode', mode_type: 'safe', power_w: 25, payload_active: false, payload_power_w: 0, platform_power_w: 15, heater_power_w: 10, pointing_requirement_deg: 5, sun_illuminated: false },
    { ...DEFAULT_MODE, id: 'nominal', name: 'Nominal Science', mode_type: 'nominal_science', power_w: 50, pointing_requirement_deg: 0.1 },
    { ...DEFAULT_MODE, id: 'downlink', name: 'Downlink', mode_type: 'downlink', power_w: 65, payload_active: false, payload_power_w: 0, platform_power_w: 65, data_rate_mbps: 100, pointing_requirement_deg: 1 },
    { ...DEFAULT_MODE, id: 'eclipse', name: 'Eclipse', mode_type: 'eclipse', power_w: 30, payload_active: false, payload_power_w: 0, platform_power_w: 20, heater_power_w: 10, sun_illuminated: false, pointing_requirement_deg: 5 },
  ])

  const addMode = () => setModes(prev => [...prev, { ...DEFAULT_MODE, id: `mode-${Date.now()}`, name: 'New Mode' }])

  const updateMode = (i: number, partial: Partial<Mode>) => {
    setModes(prev => prev.map((m, j) => j === i ? { ...m, ...partial, power_w: (partial.payload_power_w ?? m.payload_power_w) + (partial.platform_power_w ?? m.platform_power_w) + (partial.heater_power_w ?? m.heater_power_w) } : m))
  }

  const removeMode = (i: number) => setModes(prev => prev.filter((_, j) => j !== i))

  // Worst-case identification
  const worstPower = modes.length > 0 ? modes.reduce((a, b) => a.power_w > b.power_w ? a : b) : null
  const worstEclipse = modes.filter(m => !m.sun_illuminated).reduce((a, b) => (a?.power_w ?? 0) > (b?.power_w ?? 0) ? a : b, null as Mode | null)
  const tightestPointing = modes.reduce((a, b) => (a?.pointing_requirement_deg ?? 999) < (b?.pointing_requirement_deg ?? 999) ? a : b, null as Mode | null)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <h2 style={{ margin: 0 }}>Concept of Operations</h2>
        <button className="btn btn-sm" onClick={addMode} style={{ fontSize: '0.7rem' }}>+ Add Mode</button>
      </div>

      {/* Worst-case summary */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {worstPower && (
          <div style={{ padding: '0.3rem 0.6rem', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '4px', fontSize: '0.72rem' }}>
            Peak power: <strong style={{ color: '#f59e0b' }}>{worstPower.name} ({worstPower.power_w}W)</strong> — drives SA sizing
          </div>
        )}
        {worstEclipse && (
          <div style={{ padding: '0.3rem 0.6rem', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '4px', fontSize: '0.72rem' }}>
            Eclipse worst: <strong style={{ color: '#3b82f6' }}>{worstEclipse.name} ({worstEclipse.power_w}W)</strong> — drives battery
          </div>
        )}
        {tightestPointing && (
          <div style={{ padding: '0.3rem 0.6rem', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '4px', fontSize: '0.72rem' }}>
            Tightest pointing: <strong style={{ color: '#10b981' }}>{tightestPointing.name} ({tightestPointing.pointing_requirement_deg}°)</strong> — drives AOCS
          </div>
        )}
      </div>

      {/* Mode cards */}
      {modes.map((mode, i) => (
        <div key={mode.id} style={{
          padding: '0.6rem', marginBottom: '0.5rem', borderRadius: '6px',
          background: 'var(--bg-secondary, #1f2937)', border: '1px solid var(--border, #374151)',
        }}>
          <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.4rem', alignItems: 'center' }}>
            <input className="input" value={mode.name} onChange={e => updateMode(i, { name: e.target.value })}
              style={{ flex: 1, fontSize: '0.82rem', fontWeight: 600 }} />
            <select className="select" value={mode.mode_type} onChange={e => updateMode(i, { mode_type: e.target.value })}
              style={{ width: '140px', fontSize: '0.72rem' }}>
              {MODE_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
            </select>
            <button onClick={() => removeMode(i)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}>x</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '0.3rem', fontSize: '0.72rem' }}>
            <label style={{ color: '#9ca3af' }}>Payload (W)
              <input className="input" type="number" value={mode.payload_power_w} onChange={e => updateMode(i, { payload_power_w: Number(e.target.value) })} style={{ width: '100%', fontSize: '0.72rem' }} />
            </label>
            <label style={{ color: '#9ca3af' }}>Platform (W)
              <input className="input" type="number" value={mode.platform_power_w} onChange={e => updateMode(i, { platform_power_w: Number(e.target.value) })} style={{ width: '100%', fontSize: '0.72rem' }} />
            </label>
            <label style={{ color: '#9ca3af' }}>Heater (W)
              <input className="input" type="number" value={mode.heater_power_w} onChange={e => updateMode(i, { heater_power_w: Number(e.target.value) })} style={{ width: '100%', fontSize: '0.72rem' }} />
            </label>
            <label style={{ color: '#9ca3af' }}>Pointing (°)
              <input className="input" type="number" step="0.01" value={mode.pointing_requirement_deg} onChange={e => updateMode(i, { pointing_requirement_deg: Number(e.target.value) })} style={{ width: '100%', fontSize: '0.72rem' }} />
            </label>
            <label style={{ color: '#9ca3af' }}>Data (Mbps)
              <input className="input" type="number" value={mode.data_rate_mbps} onChange={e => updateMode(i, { data_rate_mbps: Number(e.target.value) })} style={{ width: '100%', fontSize: '0.72rem' }} />
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: '#9ca3af' }}>
              <input type="checkbox" checked={mode.sun_illuminated} onChange={e => updateMode(i, { sun_illuminated: e.target.checked })} />
              Sunlit
            </label>
          </div>
          <div style={{ marginTop: '0.3rem', fontSize: '0.7rem', color: '#6b7280' }}>
            Total: <strong style={{ color: '#f3f4f6' }}>{mode.power_w}W</strong>
            {mode.id === worstPower?.id && <span style={{ color: '#f59e0b', marginLeft: '0.5rem' }}>Peak power driver</span>}
            {mode.id === worstEclipse?.id && <span style={{ color: '#3b82f6', marginLeft: '0.5rem' }}>Eclipse driver</span>}
            {mode.id === tightestPointing?.id && <span style={{ color: '#10b981', marginLeft: '0.5rem' }}>Pointing driver</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
