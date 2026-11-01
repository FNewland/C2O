/**
 * PowerRailEditor — Interactive power distribution topology view (SCDF-261).
 *
 * Shows the power bus architecture: solar array → battery → regulators → loads.
 * Each rail shows voltage, current capacity, and connected subsystems.
 * Read-only for now; interactive editing in future iteration.
 */
import { useActiveParameters } from '../hooks/useActiveParameters'
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'

interface PowerRail {
  id: string; name: string; voltage_v: number; current_a: number
  source: string; loads: string[]
}

export function PowerRailEditor() {
  const params = useActiveParameters()
  const result = useDesignStore(s => s.result)

  const get = (id: string): number => {
    const p = params[id]
    return p && typeof p.value === 'number' ? p.value : 0
  }

  const saPower = get('power.sa_power_eol_w')
  const batteryCapacity = get('power.battery_capacity_wh')
  const totalPower = get('power.total_sunlight_w')

  // Build power rails from design state
  const rails: PowerRail[] = [
    { id: 'sa', name: 'Solar Array Bus', voltage_v: 8.0, current_a: saPower / 8, source: 'Solar Array', loads: ['Battery Charger', 'MPPT'] },
    { id: 'batt', name: 'Battery Bus', voltage_v: 7.4, current_a: batteryCapacity > 0 ? totalPower / 7.4 : 0, source: 'Li-Ion Battery', loads: ['Bus Regulator'] },
    { id: 'reg5v', name: '5V Regulated', voltage_v: 5.0, current_a: totalPower * 0.3 / 5, source: 'DC-DC Converter', loads: ['OBC', 'Sensors', 'Star Tracker'] },
    { id: 'reg3v3', name: '3.3V Regulated', voltage_v: 3.3, current_a: totalPower * 0.2 / 3.3, source: 'LDO', loads: ['Radio', 'GPS', 'Magnetometer'] },
    { id: 'unreg', name: 'Unregulated Bus', voltage_v: 7.4, current_a: totalPower * 0.5 / 7.4, source: 'Battery Direct', loads: ['Reaction Wheels', 'Heaters', 'Payload'] },
  ]

  if (!result || totalPower <= 0) {
    return (
      <div className="card" style={{ borderLeft: '3px solid var(--text-3)' }}>
        <h3 style={{ fontSize: fs.body, color: 'var(--text-3)' }}>Power Distribution Topology</h3>
        <p style={{ fontSize: fs.label, color: 'var(--text-3)' }}>Run a design to see power rail architecture.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>Power Distribution Topology</h3>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.5rem' }}>
        Bus architecture: {saPower.toFixed(0)}W EOL generation, {totalPower.toFixed(0)}W demand
      </p>

      {/* Visual topology */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
        {rails.map((rail, i) => (
          <div key={rail.id} style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.3rem 0.5rem', background: 'var(--bg-primary, var(--surface-1))',
            borderRadius: '4px', borderLeft: `3px solid ${i === 0 ? 'var(--status-caution)' : i === 1 ? 'var(--status-ok)' : 'var(--interactive)'}`,
          }}>
            {/* Source */}
            <div style={{ minWidth: '80px' }}>
              <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>Source</div>
              <div style={{ fontSize: fs.label, fontWeight: 600 }}>{rail.source}</div>
            </div>

            {/* Rail line */}
            <div style={{ flex: 1, position: 'relative', height: 20 }}>
              <div style={{ position: 'absolute', top: 9, left: 0, right: 0, height: 2, background: i === 0 ? 'var(--status-caution)' : i === 1 ? 'var(--status-ok)' : 'var(--interactive)' }} />
              <div style={{ position: 'absolute', top: 2, left: '50%', transform: 'translateX(-50%)', fontSize: fs.label, fontFamily: 'monospace', color: 'var(--text)', background: 'var(--bg-primary, var(--surface-1))', padding: '0 0.3rem' }}>
                {rail.voltage_v}V / {rail.current_a.toFixed(1)}A
              </div>
            </div>

            {/* Loads */}
            <div style={{ minWidth: '120px' }}>
              <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>Loads</div>
              <div style={{ fontSize: fs.label, color: 'var(--text-2)' }}>{rail.loads.join(', ')}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: fs.label, color: 'var(--text-3)' }}>
        <span>Total rails: {rails.length}</span>
        <span>Peak current: {(totalPower / 7.4).toFixed(1)} A</span>
        <span>Battery: {batteryCapacity.toFixed(0)} Wh</span>
      </div>
    </div>
  )
}
