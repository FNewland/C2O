/**
 * LensView — renders the design model through a specific engineering lens.
 *
 * Each lens reads the same model data but emphasises different properties.
 * The lens doesn't change the data — it changes the presentation.
 */
import { useModelStore, type DesignElement } from '../stores/modelStore'
import { useDesignStore } from '../stores/designStore'
import { SVGBarChart } from '../charts/SVGBarChart'
import { BudgetGauge } from '../charts/BudgetGauge'
import type { Lens } from '../types/phases'
import { LENS_LABELS } from '../types/phases'

interface Props {
  lens: Lens
  segment?: string
}

// What each lens cares about per element
const LENS_PROPERTIES: Record<Lens, { primary: string; secondary: string; unit: string; filterFn?: (el: DesignElement) => boolean }> = {
  mechanical: { primary: 'mass_kg', secondary: 'volume_cm3', unit: 'kg' },
  electrical: { primary: 'power_avg_w', secondary: 'power_peak_w', unit: 'W' },
  rf_comms: { primary: 'power_avg_w', secondary: 'mass_kg', unit: 'W', filterFn: (el) => el.subsystem_domain === 'ttc' || el.name.toLowerCase().includes('antenna') || el.name.toLowerCase().includes('transponder') },
  thermal: { primary: 'power_avg_w', secondary: 'mass_kg', unit: 'W', filterFn: (el) => el.subsystem_domain === 'thermal' || (el.power_avg_w || 0) > 0 },
  data: { primary: 'mass_kg', secondary: 'power_avg_w', unit: 'kg', filterFn: (el) => el.subsystem_domain === 'obc' || el.name.toLowerCase().includes('data') || el.name.toLowerCase().includes('storage') },
  mission: { primary: 'mass_kg', secondary: 'cost_recurring_keur', unit: 'kg' },
  software: { primary: 'power_avg_w', secondary: 'mass_kg', unit: 'W', filterFn: (el) => el.element_type === 'software' || el.subsystem_domain === 'obc' },
}

export function LensView({ lens, segment }: Props) {
  const elements = useModelStore(s => s.elements)
  const interfaces = useModelStore(s => s.interfaces)
  const result = useDesignStore(s => s.result)
  const requirements = useDesignStore(s => s.requirements)

  const lensInfo = LENS_LABELS[lens]
  const lensConfig = LENS_PROPERTIES[lens]

  // Get elements visible through this lens
  const visibleElements: DesignElement[] = []
  for (const el of elements.values()) {
    if (segment && el.segment !== segment) continue
    if (el.element_type === 'mission' || el.element_type === 'segment') continue
    if (lensConfig.filterFn && !lensConfig.filterFn(el)) continue
    visibleElements.push(el)
  }

  // Get relevant interfaces
  const visibleInterfaces = []
  for (const iface of interfaces.values()) {
    if (lens === 'electrical' && iface.interface_type !== 'electrical') continue
    if (lens === 'rf_comms' && iface.interface_type !== 'rf') continue
    if (lens === 'data' && iface.interface_type !== 'data') continue
    if (lens === 'thermal' && iface.interface_type !== 'thermal') continue
    if (lens === 'mechanical' && iface.interface_type !== 'mechanical') continue
    // mission and software lenses show all interfaces
    visibleInterfaces.push(iface)
  }

  // Group by subsystem
  const bySubsystem: Record<string, DesignElement[]> = {}
  for (const el of visibleElements) {
    const key = el.subsystem_domain || el.element_type || 'other'
    if (!bySubsystem[key]) bySubsystem[key] = []
    bySubsystem[key].push(el)
  }

  // Compute totals per subsystem for chart
  const chartData = Object.entries(bySubsystem).map(([domain, els]) => {
    const total = els.reduce((s, el) => s + ((el[lensConfig.primary as keyof DesignElement] as number) || 0) * el.quantity, 0)
    return { label: domain, value: total, color: undefined }
  }).filter(d => d.value > 0)

  // Params from result for additional context
  const params = result?.parameters || {}
  const get = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '1.2rem' }}>{lensInfo.icon}</span>
        <h2 style={{ fontSize: '1rem', margin: 0 }}>{lensInfo.name} View</h2>
        <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>
          {visibleElements.length} elements, {visibleInterfaces.length} interfaces
        </span>
      </div>

      {visibleElements.length === 0 ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
          <p>No elements visible through this lens. Run a design to populate the element tree.</p>
        </div>
      ) : (
        <>
          {/* Budget summary for this lens */}
          {lens === 'mechanical' && (
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              <BudgetGauge label="Total Mass" value={visibleElements.reduce((s, el) => s + (el.mass_kg || 0) * el.quantity, 0)} allocation={requirements.target_mass_kg || 6} unit="kg" width={150} />
              <BudgetGauge label="Total Volume" value={visibleElements.reduce((s, el) => s + (el.volume_cm3 || 0) * el.quantity, 0)} allocation={3000} unit="cm³" width={150} />
            </div>
          )}
          {lens === 'electrical' && (
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              <BudgetGauge label="Total Power" value={visibleElements.reduce((s, el) => s + (el.power_avg_w || 0) * el.quantity, 0)} allocation={get('power.sa_power_eol_w') || 30} unit="W" width={150} />
              <BudgetGauge label="Peak Power" value={visibleElements.reduce((s, el) => s + (el.power_peak_w || el.power_avg_w || 0) * el.quantity, 0)} allocation={get('power.sa_power_eol_w') || 30} unit="W" width={150} />
            </div>
          )}

          {/* Mission lens: show requirements compliance + KPIs instead of mass chart */}
          {lens === 'mission' && (
            <div className="card" style={{ marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>Mission Capability Assessment</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                    <th style={th}>KPI</th>
                    <th style={thR}>Design Value</th>
                    <th style={thR}>Requirement</th>
                    <th style={thR}>Margin</th>
                    <th style={th}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { kpi: 'Total Mass', value: visibleElements.reduce((s, el) => s + (el.mass_kg || 0) * el.quantity, 0), req: requirements.target_mass_kg || 6, unit: 'kg' },
                    { kpi: 'Orbit Average Power', value: get('power.sa_power_eol_w'), req: visibleElements.reduce((s, el) => s + (el.power_avg_w || 0) * el.quantity, 0) || 10, unit: 'W' },
                    { kpi: 'Data Rate', value: get('link.data_rate_kbps') / 1000, req: requirements.payloads?.[0]?.data_rate_mbps || 1, unit: 'Mbps' },
                    { kpi: 'Pointing Accuracy', value: get('aocs.pointing_accuracy_deg'), req: requirements.payloads?.[0]?.pointing_accuracy_deg || 1, unit: 'deg' },
                    { kpi: 'Design Lifetime', value: requirements.orbit?.mission_duration_years || 3, req: requirements.design_lifetime_years || 3, unit: 'yr' },
                    { kpi: 'Mission Cost', value: get('cost.total_mission_meur') || (requirements.target_cost_meur || 2), req: requirements.target_cost_meur || 10, unit: 'MEUR' },
                  ].map(row => {
                    const margin = row.req > 0 ? ((row.req - row.value) / row.req * 100) : 0
                    const ok = row.kpi === 'Pointing Accuracy' ? row.value <= row.req : row.value <= row.req * 1.2
                    return (
                      <tr key={row.kpi} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={td}>{row.kpi}</td>
                        <td style={{ ...tdR, fontFamily: 'monospace' }}>{row.value > 0 ? row.value.toFixed(2) : '—'} {row.unit}</td>
                        <td style={{ ...tdR, fontFamily: 'monospace', color: '#6b7280' }}>{row.req.toFixed(2)} {row.unit}</td>
                        <td style={{ ...tdR, fontFamily: 'monospace', color: ok ? '#10b981' : '#ef4444' }}>{row.value > 0 ? `${margin.toFixed(0)}%` : '—'}</td>
                        <td style={td}>
                          <span style={{ width: 8, height: 8, borderRadius: '50%', background: row.value > 0 ? (ok ? '#10b981' : '#ef4444') : '#6b7280', display: 'inline-block' }} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              <p style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '0.3rem' }}>
                Green = meets requirement with margin. Red = exceeds allocation or fails requirement.
              </p>
            </div>
          )}

          {/* Bar chart of primary property by subsystem (not for mission lens) */}
          {lens !== 'mission' && (
          <div className="card" style={{ marginBottom: '1rem' }}>
            <SVGBarChart
              data={chartData}
              orientation="horizontal"
              unit={` ${lensConfig.unit}`}
              width={500} height={Math.max(120, chartData.length * 28 + 40)}
              title={`${lensInfo.name}: ${lensConfig.primary.replace('_', ' ')} by subsystem`}
            />
          </div>
          )}

          {/* Element table */}
          <div className="card">
            <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Elements</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                  <th style={th}>Name</th>
                  <th style={th}>Type</th>
                  <th style={thR}>Qty</th>
                  <th style={thR}>{lensConfig.primary.replace(/_/g, ' ')}</th>
                  <th style={thR}>{lensConfig.secondary.replace(/_/g, ' ')}</th>
                  <th style={th}>Domain</th>
                </tr>
              </thead>
              <tbody>
                {visibleElements.map(el => (
                  <tr key={el.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={td}>{el.name}</td>
                    <td style={{ ...td, color: '#6b7280', fontSize: '0.65rem' }}>{el.element_type}</td>
                    <td style={tdR}>{el.quantity}</td>
                    <td style={{ ...tdR, fontFamily: 'monospace' }}>{((el[lensConfig.primary as keyof DesignElement] as number) || 0).toFixed(2)}</td>
                    <td style={{ ...tdR, fontFamily: 'monospace', color: '#6b7280' }}>{((el[lensConfig.secondary as keyof DesignElement] as number) || 0).toFixed(2)}</td>
                    <td style={{ ...td, color: '#6b7280' }}>{el.subsystem_domain || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Interfaces for this lens */}
          {visibleInterfaces.length > 0 && (
            <div className="card" style={{ marginTop: '0.75rem' }}>
              <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>
                {lens === 'electrical' ? 'Electrical Interfaces' :
                 lens === 'rf_comms' ? 'RF Interfaces' :
                 lens === 'data' ? 'Data Interfaces' :
                 lens === 'thermal' ? 'Thermal Interfaces' :
                 `Interfaces (${visibleInterfaces.length})`}
              </h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                    <th style={th}>From</th>
                    <th style={th}>To</th>
                    <th style={th}>Type</th>
                    <th style={th}>Label</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleInterfaces.map(iface => (
                    <tr key={iface.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={td}>{elements.get(iface.from_element_id)?.name || iface.from_element_id}</td>
                      <td style={td}>{elements.get(iface.to_element_id)?.name || iface.to_element_id}</td>
                      <td style={{ ...td, color: '#6b7280' }}>{iface.interface_type}</td>
                      <td style={{ ...td, color: '#9ca3af' }}>{iface.diagram_label || iface.name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right' }
