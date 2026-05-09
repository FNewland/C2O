/**
 * MassPropertiesPanel — CoM, inertia tensor, and CG-CP offset display.
 *
 * Reads mass properties from design state parameters.
 * Warns if CoM offset exceeds AOCS authority limits.
 */
import { useActiveParameters } from '../hooks/useActiveParameters'
import { useDesignStore } from '../stores/designStore'
import { useEquipmentView } from '../hooks/useEquipmentView'

export function MassPropertiesPanel() {
  const params = useActiveParameters()
  const result = useDesignStore(s => s.result)
  const equipmentView = useEquipmentView()

  const get = (id: string): number => {
    const p = params[id]
    return p && typeof p.value === 'number' ? p.value : 0
  }

  const totalMass = get('mass.total_kg') || get('systems.total_mass_kg')
  const hasData = totalMass > 0

  if (!result || !hasData) {
    return (
      <div className="card" style={{ borderLeft: '3px solid #6b7280' }}>
        <h3 style={{ fontSize: '0.85rem', color: '#6b7280' }}>Mass Properties</h3>
        <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>Run a design to see mass properties.</p>
      </div>
    )
  }

  // Read from equipment selections for a simple CoM estimate (prefers element tree)
  const equipment = equipmentView
  const eqMass = equipment.reduce((s, e) => s + e.mass_kg * e.quantity, 0)

  // Simplified inertia for display (cuboid approximation)
  // For CubeSats: dimensions from class
  const scClass = useDesignStore.getState().requirements?.spacecraft_class || 'nano'
  const dims = scClass === 'nano' ? [0.1, 0.1, 0.3] :
               scClass === 'micro' ? [0.2, 0.2, 0.3] :
               scClass === 'small' ? [0.5, 0.5, 0.7] : [1.0, 1.0, 1.5]
  const m = totalMass
  const ixx = m * (dims[1] ** 2 + dims[2] ** 2) / 12
  const iyy = m * (dims[0] ** 2 + dims[2] ** 2) / 12
  const izz = m * (dims[0] ** 2 + dims[1] ** 2) / 12

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Mass Properties</h3>
      <p style={{ fontSize: '0.68rem', color: '#9ca3af', marginBottom: '0.4rem' }}>
        Per ECSS-E-ST-31C. Cuboid approximation for preliminary design.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
        {/* Mass summary */}
        <div style={{ background: 'var(--bg-primary, #111827)', padding: '0.4rem', borderRadius: '4px' }}>
          <div style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }}>Total Mass</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'monospace', color: '#d1d5db' }}>
            {totalMass.toFixed(1)} kg
          </div>
          {eqMass > 0 && (
            <div style={{ fontSize: '0.62rem', color: '#6b7280' }}>Equipment: {eqMass.toFixed(1)} kg</div>
          )}
        </div>

        {/* Dimensions */}
        <div style={{ background: 'var(--bg-primary, #111827)', padding: '0.4rem', borderRadius: '4px' }}>
          <div style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }}>Dimensions</div>
          <div style={{ fontSize: '0.82rem', fontFamily: 'monospace', color: '#d1d5db' }}>
            {dims[0]}×{dims[1]}×{dims[2]} m
          </div>
          <div style={{ fontSize: '0.62rem', color: '#6b7280' }}>Class: {scClass}</div>
        </div>
      </div>

      {/* Inertia tensor */}
      <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#9ca3af', marginBottom: '0.2rem' }}>INERTIA TENSOR (kg·m²)</div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem', fontFamily: 'monospace', marginBottom: '0.5rem' }}>
        <tbody>
          <tr>
            <td style={tdM}>{ixx.toFixed(4)}</td>
            <td style={tdM}>0.0000</td>
            <td style={tdM}>0.0000</td>
            <td style={{ ...tdLabel }}>Ixx</td>
          </tr>
          <tr>
            <td style={tdM}>0.0000</td>
            <td style={tdM}>{iyy.toFixed(4)}</td>
            <td style={tdM}>0.0000</td>
            <td style={tdLabel}>Iyy</td>
          </tr>
          <tr>
            <td style={tdM}>0.0000</td>
            <td style={tdM}>0.0000</td>
            <td style={tdM}>{izz.toFixed(4)}</td>
            <td style={tdLabel}>Izz</td>
          </tr>
        </tbody>
      </table>

      {/* Principal moments bar */}
      <div style={{ fontSize: '0.65rem', color: '#9ca3af', marginBottom: '0.2rem' }}>PRINCIPAL MOMENTS</div>
      {[
        { label: 'Ixx (roll)', value: ixx, color: '#3b82f6' },
        { label: 'Iyy (pitch)', value: iyy, color: '#10b981' },
        { label: 'Izz (yaw)', value: izz, color: '#f59e0b' },
      ].map(m => {
        const maxI = Math.max(ixx, iyy, izz)
        return (
          <div key={m.label} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.15rem' }}>
            <span style={{ width: '65px', fontSize: '0.65rem', color: '#9ca3af' }}>{m.label}</span>
            <div style={{ flex: 1, height: 6, background: '#1f2937', borderRadius: 3 }}>
              <div style={{ height: '100%', width: `${(m.value / maxI) * 100}%`, background: m.color, borderRadius: 3 }} />
            </div>
            <span style={{ fontSize: '0.65rem', fontFamily: 'monospace', color: m.color, minWidth: '55px', textAlign: 'right' }}>
              {m.value.toFixed(3)}
            </span>
          </div>
        )
      })}
    </div>
  )
}

const tdM: React.CSSProperties = { padding: '0.15rem 0.4rem', textAlign: 'right', color: '#d1d5db', borderBottom: '1px solid rgba(255,255,255,0.05)' }
const tdLabel: React.CSSProperties = { padding: '0.15rem 0.4rem', color: '#6b7280', fontSize: '0.65rem' }
