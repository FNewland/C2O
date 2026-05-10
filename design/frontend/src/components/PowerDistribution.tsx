/**
 * PowerDistribution — power generation, storage, and distribution diagram.
 *
 * Shows: solar array → BCR → battery → PDM → switched/unswitched rails → loads.
 * Each rail shows voltage, current, connected equipment, and status.
 * User can assign equipment to rails and check voltage compatibility.
 *
 * Enhanced: per-mode duty cycle table, margin/contingency rows per ECSS,
 * power generation vs consumption balance per mode.
 */
import { useMemo, useState } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'
import { SVGBarChart } from '../charts/SVGBarChart'
import { BudgetGauge } from '../charts/BudgetGauge'

// Default duty cycles per mode for each subsystem domain
const DEFAULT_DUTY_CYCLES: Record<string, Record<string, number>> = {
  // domain: { safe, science, downlink, eclipse }
  power:      { safe: 1.0, science: 1.0, downlink: 1.0, eclipse: 1.0 },
  aocs:       { safe: 0.3, science: 1.0, downlink: 0.8, eclipse: 0.3 },
  ttc:        { safe: 0.1, science: 0.0, downlink: 1.0, eclipse: 0.0 },
  link:       { safe: 0.1, science: 0.0, downlink: 1.0, eclipse: 0.0 },
  obc:        { safe: 1.0, science: 1.0, downlink: 1.0, eclipse: 1.0 },
  data:       { safe: 1.0, science: 1.0, downlink: 1.0, eclipse: 1.0 },
  thermal:    { safe: 0.5, science: 0.3, downlink: 0.3, eclipse: 1.0 },
  payload:    { safe: 0.0, science: 1.0, downlink: 0.0, eclipse: 0.0 },
  propulsion: { safe: 0.0, science: 0.0, downlink: 0.0, eclipse: 0.0 },
  structure:  { safe: 0.0, science: 0.0, downlink: 0.0, eclipse: 0.0 },
  integration:{ safe: 0.0, science: 0.0, downlink: 0.0, eclipse: 0.0 },
}

export function PowerDistribution() {
  const result = useDesignStore(s => s.result)
  const requirements = useDesignStore(s => s.requirements)
  const operationalModes = useDesignStore(s => s.operationalModes)
  const elements = useModelStore(s => s.elements)

  const [dutyCycleOverrides, setDutyCycleOverrides] = useState<Record<string, Record<string, number>>>({})

  const params = result?.parameters || {}
  const get = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  const saEol = get('power.sa_power_eol_w')
  const saBol = get('power.sa_power_bol_w')
  const battCap = get('power.battery_capacity_wh')
  const battDod = get('power.battery_dod_pct')
  const sunlightDemand = get('power.total_sunlight_w')
  const eclipseDemand = get('power.total_eclipse_w')
  const heaterPower = get('thermal.heater_power_w')

  // Power consumers from element tree (components with power > 0)
  const consumers = useMemo(() => {
    const result: { name: string; power_w: number; rail: string; domain: string; id: string }[] = []
    for (const el of elements.values()) {
      if (el.power_avg_w && el.power_avg_w > 0 && (el.element_type === 'subsystem' || el.element_type === 'component')) {
        result.push({
          id: el.id,
          name: el.name,
          power_w: el.power_avg_w * (el.quantity || 1),
          rail: el.subsystem_domain === 'aocs' || el.subsystem_domain === 'thermal' ? 'switched' : 'unswitched',
          domain: el.subsystem_domain || '',
        })
      }
    }
    return result
  }, [elements])

  // Mode IDs for the table columns
  const modeIds = useMemo(() => {
    if (operationalModes && operationalModes.length > 0) {
      return operationalModes.map(m => ({ id: m.id, name: m.name }))
    }
    return [
      { id: 'safe', name: 'Safe Mode' },
      { id: 'science', name: 'Science' },
      { id: 'downlink', name: 'Downlink' },
      { id: 'eclipse', name: 'Eclipse' },
    ]
  }, [operationalModes])

  // Get duty cycle for a component in a given mode
  const getDutyCycle = (domain: string, modeId: string): number => {
    const overrideKey = domain
    if (dutyCycleOverrides[overrideKey]?.[modeId] !== undefined) {
      return dutyCycleOverrides[overrideKey][modeId]
    }
    return DEFAULT_DUTY_CYCLES[domain]?.[modeId] ?? 1.0
  }

  const setDutyCycle = (domain: string, modeId: string, value: number) => {
    setDutyCycleOverrides(prev => ({
      ...prev,
      [domain]: { ...(prev[domain] || {}), [modeId]: Math.max(0, Math.min(1, value)) },
    }))
  }

  // Per-mode power consumption
  const modeConsumption = useMemo(() => {
    const result: Record<string, number> = {}
    for (const mode of modeIds) {
      let total = 0
      for (const c of consumers) {
        total += c.power_w * getDutyCycle(c.domain, mode.id)
      }
      result[mode.id] = total
    }
    return result
  }, [consumers, modeIds, dutyCycleOverrides])

  // Margins per ECSS-E-ST-20C
  const MARGIN_PCT = 20   // system margin
  const CONTINGENCY_PCT = 5  // contingency

  const modeWithMargins = useMemo(() => {
    const result: Record<string, { subtotal: number; margin: number; contingency: number; total: number }> = {}
    for (const mode of modeIds) {
      const subtotal = modeConsumption[mode.id] || 0
      const margin = subtotal * MARGIN_PCT / 100
      const contingency = subtotal * CONTINGENCY_PCT / 100
      result[mode.id] = { subtotal, margin, contingency, total: subtotal + margin + contingency }
    }
    return result
  }, [modeConsumption, modeIds])

  // Power generation per mode (0 in eclipse)
  const modeGeneration = useMemo(() => {
    const result: Record<string, number> = {}
    for (const mode of modeIds) {
      result[mode.id] = mode.id === 'eclipse' ? 0 : saEol
    }
    return result
  }, [modeIds, saEol])

  // Power balance per mode
  const modeBalance = useMemo(() => {
    const result: Record<string, number> = {}
    for (const mode of modeIds) {
      result[mode.id] = modeGeneration[mode.id] - (modeWithMargins[mode.id]?.total || 0)
    }
    return result
  }, [modeIds, modeGeneration, modeWithMargins])

  const switchedTotal = consumers.filter(c => c.rail === 'switched').reduce((s, c) => s + c.power_w, 0)
  const unswitchedTotal = consumers.filter(c => c.rail === 'unswitched').reduce((s, c) => s + c.power_w, 0)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Power Budget</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Generation, storage, and distribution with duty cycles and margins per ECSS-E-ST-20C.
      </p>

      {/* Generation + Storage summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem', marginBottom: '1rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '0.82rem', color: '#f59e0b', marginBottom: '0.3rem' }}>Generation (Solar Array)</h3>
          <div style={{ fontSize: '0.72rem', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
            <span>BOL: <strong>{saBol.toFixed(1)} W</strong></span>
            <span>EOL: <strong>{saEol.toFixed(1)} W</strong></span>
            <span>Degradation: <strong>{saBol > 0 ? ((1 - saEol / saBol) * 100).toFixed(1) : 0}%</strong> over {requirements.design_lifetime_years || 3} yr</span>
          </div>
          <BudgetGauge label="SA vs Demand" value={sunlightDemand} allocation={saEol || 1} unit="W" width={190} />
        </div>

        <div className="card">
          <h3 style={{ fontSize: '0.82rem', color: '#10b981', marginBottom: '0.3rem' }}>Storage (Battery)</h3>
          <div style={{ fontSize: '0.72rem', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
            <span>Capacity: <strong>{battCap.toFixed(1)} Wh</strong></span>
            <span>Max DOD: <strong>{battDod.toFixed(0)}%</strong></span>
            <span>Usable: <strong>{(battCap * battDod / 100).toFixed(1)} Wh</strong></span>
          </div>
          <BudgetGauge label="DOD" value={battDod} allocation={30} unit="%" width={190} />
        </div>

        <div className="card">
          <h3 style={{ fontSize: '0.82rem', color: '#ef4444', marginBottom: '0.3rem' }}>Demand</h3>
          <div style={{ fontSize: '0.72rem', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
            <span>Sunlight (peak): <strong>{sunlightDemand.toFixed(1)} W</strong></span>
            <span>Eclipse: <strong>{eclipseDemand.toFixed(1)} W</strong></span>
            <span>Heaters: <strong>{heaterPower.toFixed(1)} W</strong></span>
          </div>
        </div>
      </div>

      {/* Distribution diagram */}
      <div className="card" style={{ marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '0.82rem', marginBottom: '0.4rem' }}>Power Distribution</h3>
        <svg width="100%" height="200" viewBox="0 0 600 200" style={{ background: '#0a0e1a', borderRadius: '4px' }}>
          {/* SA → BCR → Battery → PDM */}
          <rect x="10" y="20" width="80" height="40" rx="4" fill="#f59e0b20" stroke="#f59e0b" strokeWidth="1.5" />
          <text x="50" y="37" textAnchor="middle" fill="#f59e0b" fontSize="9" fontWeight="600">Solar Array</text>
          <text x="50" y="50" textAnchor="middle" fill="#9ca3af" fontSize="7">{saEol.toFixed(0)}W EOL</text>

          <line x1="90" y1="40" x2="120" y2="40" stroke="#f59e0b" strokeWidth="2" />

          <rect x="120" y="20" width="60" height="40" rx="4" fill="#06b6d420" stroke="#06b6d4" strokeWidth="1.5" />
          <text x="150" y="37" textAnchor="middle" fill="#06b6d4" fontSize="9" fontWeight="600">BCR</text>
          <text x="150" y="50" textAnchor="middle" fill="#9ca3af" fontSize="7">MPPT</text>

          <line x1="180" y1="40" x2="210" y2="40" stroke="#06b6d4" strokeWidth="2" />

          <rect x="210" y="10" width="80" height="60" rx="4" fill="#10b98120" stroke="#10b981" strokeWidth="1.5" />
          <text x="250" y="32" textAnchor="middle" fill="#10b981" fontSize="9" fontWeight="600">Battery</text>
          <text x="250" y="45" textAnchor="middle" fill="#9ca3af" fontSize="7">{battCap.toFixed(0)} Wh</text>
          <text x="250" y="58" textAnchor="middle" fill="#9ca3af" fontSize="7">DOD {battDod.toFixed(0)}%</text>

          <line x1="290" y1="40" x2="320" y2="40" stroke="#10b981" strokeWidth="2" />

          <rect x="320" y="20" width="60" height="40" rx="4" fill="#3b82f620" stroke="#3b82f6" strokeWidth="1.5" />
          <text x="350" y="37" textAnchor="middle" fill="#3b82f6" fontSize="9" fontWeight="600">PDM</text>
          <text x="350" y="50" textAnchor="middle" fill="#9ca3af" fontSize="7">Switch</text>

          {/* Switched rail */}
          <line x1="380" y1="30" x2="420" y2="30" stroke="#f59e0b" strokeWidth="2" />
          <text x="400" y="24" textAnchor="middle" fill="#f59e0b" fontSize="7">Switched</text>

          {/* Unswitched rail */}
          <line x1="380" y1="50" x2="420" y2="50" stroke="#ef4444" strokeWidth="2" />
          <text x="400" y="64" textAnchor="middle" fill="#ef4444" fontSize="7">Unswitched</text>

          {/* Loads on switched rail */}
          {consumers.filter(c => c.rail === 'switched').map((c, i) => (
            <g key={i}>
              <rect x={430} y={10 + i * 28} width={140} height={22} rx={3} fill="#1f2937" stroke="#f59e0b40" strokeWidth={1} />
              <text x={435} y={24 + i * 28} fill="#d1d5db" fontSize={8}>{c.name}: {c.power_w.toFixed(1)}W</text>
              <line x1={420} y1={30} x2={430} y2={21 + i * 28} stroke="#f59e0b40" strokeWidth={0.5} />
            </g>
          ))}

          {/* Loads on unswitched rail */}
          {consumers.filter(c => c.rail === 'unswitched').map((c, i) => (
            <g key={i}>
              <rect x={430} y={100 + i * 28} width={140} height={22} rx={3} fill="#1f2937" stroke="#ef444440" strokeWidth={1} />
              <text x={435} y={114 + i * 28} fill="#d1d5db" fontSize={8}>{c.name}: {c.power_w.toFixed(1)}W</text>
              <line x1={420} y1={50} x2={430} y2={111 + i * 28} stroke="#ef444440" strokeWidth={0.5} />
            </g>
          ))}

          {/* Totals */}
          <text x={580} y={30} textAnchor="end" fill="#f59e0b" fontSize={8}>Switched: {switchedTotal.toFixed(1)}W</text>
          <text x={580} y={110} textAnchor="end" fill="#ef4444" fontSize={8}>Unswitched: {unswitchedTotal.toFixed(1)}W</text>
        </svg>
      </div>

      {/* Per-mode duty cycle table */}
      <div className="card" style={{ marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>Power by Operational Mode (Duty Cycle Table)</h3>
        <p style={{ fontSize: '0.65rem', color: '#6b7280', marginBottom: '0.4rem' }}>
          Cells show power consumed = component power x duty cycle. Click a duty cycle to edit.
        </p>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem', fontFamily: 'monospace' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={thStyle}>Component</th>
                <th style={thStyle}>Unit Power (W)</th>
                {modeIds.map(m => (
                  <th key={m.id} style={thStyle}>{m.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {consumers.map(c => (
                <tr key={c.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={tdStyle}>{c.name}</td>
                  <td style={tdNumStyle}>{c.power_w.toFixed(1)}</td>
                  {modeIds.map(m => {
                    const dc = getDutyCycle(c.domain, m.id)
                    const power = c.power_w * dc
                    return (
                      <td key={m.id} style={tdNumStyle}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.1rem' }}>
                          <span style={{ color: power > 0 ? '#d1d5db' : '#4b5563' }}>{power.toFixed(1)}</span>
                          <input type="number" min={0} max={1} step={0.1} value={dc}
                            onChange={e => setDutyCycle(c.domain, m.id, Number(e.target.value))}
                            style={{
                              width: '40px', fontSize: '0.6rem', textAlign: 'right',
                              background: 'transparent', border: '1px solid #374151',
                              borderRadius: '2px', color: '#6b7280', padding: '0 2px',
                            }}
                            title={`Duty cycle for ${c.domain} in ${m.name}`}
                          />
                        </div>
                      </td>
                    )
                  })}
                </tr>
              ))}
              {/* Subtotal row */}
              <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
                <td style={tdStyle} colSpan={2}>Subtotal</td>
                {modeIds.map(m => (
                  <td key={m.id} style={{ ...tdNumStyle, color: '#d1d5db' }}>
                    {(modeWithMargins[m.id]?.subtotal || 0).toFixed(1)}
                  </td>
                ))}
              </tr>
              {/* Margin row (20%) */}
              <tr style={{ color: '#f59e0b' }}>
                <td style={tdStyle} colSpan={2}>System Margin ({MARGIN_PCT}%)</td>
                {modeIds.map(m => (
                  <td key={m.id} style={tdNumStyle}>
                    {(modeWithMargins[m.id]?.margin || 0).toFixed(1)}
                  </td>
                ))}
              </tr>
              {/* Contingency row (5%) */}
              <tr style={{ color: '#f97316' }}>
                <td style={tdStyle} colSpan={2}>Contingency ({CONTINGENCY_PCT}%)</td>
                {modeIds.map(m => (
                  <td key={m.id} style={tdNumStyle}>
                    {(modeWithMargins[m.id]?.contingency || 0).toFixed(1)}
                  </td>
                ))}
              </tr>
              {/* Total demand */}
              <tr style={{ borderTop: '2px solid #374151', fontWeight: 700 }}>
                <td style={tdStyle} colSpan={2}>Total Demand (W)</td>
                {modeIds.map(m => (
                  <td key={m.id} style={{ ...tdNumStyle, color: '#ef4444', fontWeight: 700 }}>
                    {(modeWithMargins[m.id]?.total || 0).toFixed(1)}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Power Generation section */}
      <div className="card" style={{ marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>Power Generation by Mode</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem', fontFamily: 'monospace' }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
              <th style={thStyle}>Source</th>
              {modeIds.map(m => <th key={m.id} style={thStyle}>{m.name}</th>)}
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={tdStyle}>Solar Array (EOL)</td>
              {modeIds.map(m => (
                <td key={m.id} style={{ ...tdNumStyle, color: modeGeneration[m.id] > 0 ? '#10b981' : '#4b5563' }}>
                  {modeGeneration[m.id].toFixed(1)}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Power Balance Summary */}
      <div className="card" style={{ marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>Power Balance (Generation - Demand)</h3>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {modeIds.map(m => {
            const balance = modeBalance[m.id] || 0
            const positive = balance >= 0
            return (
              <div key={m.id} style={{
                padding: '0.4rem 0.6rem', borderRadius: '4px', minWidth: '120px', textAlign: 'center',
                background: positive ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                border: `1px solid ${positive ? '#10b981' : '#ef4444'}`,
              }}>
                <div style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase', marginBottom: '0.15rem' }}>
                  {m.name}
                </div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'monospace', color: positive ? '#10b981' : '#ef4444' }}>
                  {balance >= 0 ? '+' : ''}{balance.toFixed(1)} W
                </div>
                <div style={{ fontSize: '0.6rem', color: '#6b7280' }}>
                  {positive ? 'Surplus' : m.id === 'eclipse' ? 'Battery required' : 'DEFICIT'}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Legacy bar chart */}
      <div className="card">
        <h3 style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>Power Summary</h3>
        <SVGBarChart
          data={[
            { label: 'Sunlight', value: sunlightDemand, color: '#f59e0b' },
            { label: 'Eclipse', value: eclipseDemand, color: '#6b7280' },
            { label: 'SA Gen', value: saEol, color: '#10b981' },
          ].filter(d => d.value > 0)}
          width={350} height={150} unit=" W"
        />
      </div>
    </div>
  )
}

const thStyle: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', textTransform: 'uppercase', color: '#9ca3af', letterSpacing: '0.03em' }
const tdStyle: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdNumStyle: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }
