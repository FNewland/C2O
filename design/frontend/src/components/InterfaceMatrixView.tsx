import { useState, useMemo } from 'react'
import { useModelStore } from '../stores/modelStore'
import { useDesignStore } from '../stores/designStore'

const DEFAULT_SUBSYSTEMS = ['power', 'aocs', 'link', 'thermal', 'structure', 'propulsion', 'data', 'payload']

// Ground segment subsystems (added to matrix when ground elements exist)
const GROUND_SUBSYSTEMS = ['ground_rf', 'ground_ops', 'ground_data', 'ground_net']

// Map subsystem_domain values to display labels used in matrix
const DOMAIN_ALIASES: Record<string, string> = {
  eps: 'power', ttc: 'link', obc: 'data',
  // Ground system element names → matrix column keys
  'ground station network': 'ground_rf',
  'mission control centre': 'ground_ops',
  'data processing centre': 'ground_data',
  'network infrastructure': 'ground_net',
  'user services': 'ground_net',
}

const GROUND_INTERFACE_DATA: Record<string, InterfaceCell> = {
  'link-ground_rf': { types: ['rf'], description: 'TM/TC uplink/downlink via ground station RF chain', hasConflict: false },
  'ground_rf-ground_ops': { types: ['data'], description: 'Telemetry frames from modem to MCS', hasConflict: false },
  'ground_ops-ground_data': { types: ['data'], description: 'Science data products from MCS to processing', hasConflict: false },
  'ground_data-ground_net': { types: ['data'], description: 'Data distribution to users via network', hasConflict: false },
}

type ResolutionStatus = 'open' | 'under_discussion' | 'resolved' | 'accepted_risk' | 'deferred'

interface InterfaceCell {
  types: string[]
  description: string
  hasConflict: boolean
  conflictTitle?: string
  conflictSeverity?: 'critical' | 'major' | 'minor'
  resolutionOptions?: string[]
  affectedParameters?: string[]
  responsiblePositions?: string[]
}

interface ConflictResolution {
  cellKey: string
  status: ResolutionStatus
  selectedOption: string
  rationale: string
  resolvedBy: string
}

const INTERFACE_DATA: Record<string, InterfaceCell> = {
  'power-aocs': { types: ['electrical'], description: 'Power bus to AOCS electronics + reaction wheels', hasConflict: false },
  'power-link': { types: ['electrical'], description: 'Power bus to TTC transponder + PA', hasConflict: false },
  'power-thermal': { types: ['electrical', 'thermal'], description: 'Power bus to heaters; SA thermal coupling', hasConflict: true,
    conflictTitle: 'Radiator area vs SA area competition',
    conflictSeverity: 'major',
    resolutionOptions: ['Relocate radiator to anti-sun face', 'Reduce SA area (use higher-efficiency cells)', 'Use deployable radiator', 'Accept reduced thermal margin'],
    affectedParameters: ['power.sa_area_m2', 'thermal.radiator_area_m2', 'thermal.hot_case_margin_c'],
    responsiblePositions: ['power', 'thermal'],
  },
  'power-data': { types: ['electrical'], description: 'Power bus to OBC', hasConflict: true,
    conflictTitle: 'Power bus voltage compatibility',
    conflictSeverity: 'minor',
    resolutionOptions: ['Add DC-DC converter', 'Select OBC with matching bus voltage', 'Use regulated bus'],
    affectedParameters: ['power.bus_voltage_v', 'data.obc_power_w'],
    responsiblePositions: ['power', 'data'],
  },
  'power-payload': { types: ['electrical'], description: 'Power bus to payload; peak power switching', hasConflict: false },
  'power-propulsion': { types: ['electrical'], description: 'Power bus to valve drivers / EP PPU', hasConflict: true,
    conflictTitle: 'Thruster plume impingement on solar array',
    conflictSeverity: 'major',
    resolutionOptions: ['Add plume shields / baffles', 'Relocate thrusters', 'Use cant angle on thrusters', 'Stow SA during manoeuvres'],
    affectedParameters: ['propulsion.cant_angle_deg', 'power.sa_degradation_factor', 'structure.mass_kg'],
    responsiblePositions: ['propulsion', 'power', 'structure'],
  },
  'structure-power': { types: ['mechanical', 'thermal'], description: 'SA mounting; panel thermal path', hasConflict: false },
  'structure-aocs': { types: ['mechanical'], description: 'RW + ST mounting alignment; vibration isolation', hasConflict: false },
  'structure-thermal': { types: ['mechanical', 'thermal'], description: 'Radiator mounting; heat pipe routing', hasConflict: false },
  'structure-propulsion': { types: ['mechanical'], description: 'Tank mounting; thrust vector alignment', hasConflict: false },
  'structure-payload': { types: ['mechanical', 'optical'], description: 'Payload mounting; alignment stability; FOV clearance', hasConflict: false },
  'data-aocs': { types: ['data'], description: 'Attitude data for payload pointing; mode commands', hasConflict: false },
  'data-link': { types: ['data'], description: 'Telemetry stream; telecommand routing', hasConflict: false },
  'data-payload': { types: ['data'], description: 'Science data acquisition; instrument commanding', hasConflict: false },
  'thermal-payload': { types: ['thermal'], description: 'Payload thermal control; detector cooling', hasConflict: false },
  'thermal-propulsion': { types: ['thermal'], description: 'Propellant tank heating; catalyst bed temperature', hasConflict: false },
  'link-payload': { types: ['rf'], description: 'RF interference; antenna pattern vs payload FOV', hasConflict: true,
    conflictTitle: 'EMC: TX interference with payload',
    conflictSeverity: 'critical',
    resolutionOptions: ['Frequency separation (filter)', 'Shielding on payload electronics', 'Time-division (no TX during observation)', 'Reduce TX power during science mode'],
    affectedParameters: ['link.ttc_power_w', 'payload.emc_margin_db'],
    responsiblePositions: ['link', 'payload'],
  },
  'link-aocs': { types: ['rf', 'optical'], description: 'Antenna deployment vs star tracker FOV', hasConflict: true,
    conflictTitle: 'Solar array / antenna vs star tracker FOV',
    conflictSeverity: 'major',
    resolutionOptions: ['Relocate star tracker', 'Add exclusion zone in AOCS software', 'Change antenna type (patch vs dipole)', 'Accept reduced sky coverage'],
    affectedParameters: ['aocs.fov_exclusion_deg', 'aocs.pointing_accuracy_deg'],
    responsiblePositions: ['aocs', 'link'],
  },
  'propulsion-aocs': { types: ['mechanical'], description: 'Thruster alignment; plume impingement on SA/sensors', hasConflict: false },
  'aocs-payload': { types: ['mechanical'], description: 'Reaction wheel vibration vs payload stability', hasConflict: true,
    conflictTitle: 'Reaction wheel vibration vs payload stability',
    conflictSeverity: 'major',
    resolutionOptions: ['Add vibration isolators (SMA / elastomeric)', 'Use low-jitter wheels', 'Image stabilisation in software', 'Schedule imaging outside wheel zero-crossing'],
    affectedParameters: ['aocs.jitter_arcsec', 'payload.mtf_degradation', 'aocs.mass_kg'],
    responsiblePositions: ['aocs', 'payload'],
  },
}

const TYPE_COLORS: Record<string, string> = {
  mechanical: '#84cc16', electrical: '#f59e0b', thermal: '#ef4444',
  data: '#3b82f6', rf: '#ec4899', optical: '#8b5cf6', propulsion: '#f97316', software: '#06b6d4',
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444', major: '#f59e0b', minor: '#3b82f6',
}

const STATUS_LABELS: Record<ResolutionStatus, { label: string; color: string }> = {
  open: { label: 'OPEN', color: '#ef4444' },
  under_discussion: { label: 'DISCUSSING', color: '#f59e0b' },
  resolved: { label: 'RESOLVED', color: '#10b981' },
  accepted_risk: { label: 'RISK ACCEPTED', color: '#8b5cf6' },
  deferred: { label: 'DEFERRED', color: '#6b7280' },
}

// getCell is now inside the component to access dynamicInterfaces

export function InterfaceMatrixView({ onNavigate }: { onNavigate?: (tab: string) => void }) {
  const modelInterfaces = useModelStore(s => s.interfaces)
  const modelElements = useModelStore(s => s.elements)
  const [hoveredCell, setHoveredCell] = useState<string | null>(null)
  const [selectedCell, setSelectedCell] = useState<string | null>(null)

  // Persisted resolutions — survive tab switches and page refresh
  const storedResolutions = useDesignStore(s => s.interfaceResolutions)
  const persistResolutions = useDesignStore(s => s.setInterfaceResolutions)
  const [resolutions, setResolutionsLocal] = useState<Map<string, ConflictResolution>>(() => {
    const map = new Map<string, ConflictResolution>()
    for (const [key, val] of Object.entries(storedResolutions || {})) {
      map.set(key, { cellKey: key, ...val } as ConflictResolution)
    }
    return map
  })
  const setResolutions = (updater: (prev: Map<string, ConflictResolution>) => Map<string, ConflictResolution>) => {
    setResolutionsLocal(prev => {
      const next = updater(prev)
      // Persist to designStore as plain object
      const obj: Record<string, { status: string; selectedOption: string; rationale: string; resolvedBy: string }> = {}
      for (const [k, v] of next) {
        obj[k] = { status: v.status, selectedOption: v.selectedOption, rationale: v.rationale, resolvedBy: v.resolvedBy }
      }
      persistResolutions(obj)
      return next
    })
  }

  // SYSTEM-V: Derive subsystem list from element tree (fall back to defaults)
  const SUBSYSTEMS = useMemo(() => {
    const domains = new Set<string>()
    for (const el of modelElements.values()) {
      if (el.element_type === 'subsystem' && el.subsystem_domain) {
        const alias = DOMAIN_ALIASES[el.subsystem_domain] || el.subsystem_domain
        domains.add(alias)
      }
      // Also include ground system elements (element_type 'system', segment 'ground')
      if (el.element_type === 'system' && el.segment === 'ground') {
        const alias = DOMAIN_ALIASES[el.name.toLowerCase()] || el.name.toLowerCase().replace(/\s+/g, '_')
        domains.add(alias)
      }
    }
    // If the element tree has subsystems, use them (in a consistent order)
    if (domains.size >= 3) {
      const ordered: string[] = []
      // Space subsystems first (in standard order)
      for (const d of DEFAULT_SUBSYSTEMS) {
        if (domains.has(d)) { ordered.push(d); domains.delete(d) }
      }
      // Ground subsystems next
      for (const d of GROUND_SUBSYSTEMS) {
        if (domains.has(d)) { ordered.push(d); domains.delete(d) }
      }
      // Any remaining
      for (const d of domains) ordered.push(d)
      return ordered
    }
    return DEFAULT_SUBSYSTEMS
  }, [modelElements])

  // Build dynamic interface data from model if available
  const dynamicInterfaces = useMemo(() => {
    const dynamic: Record<string, InterfaceCell> = {}
    for (const iface of modelInterfaces.values()) {
      const fromEl = modelElements.get(iface.from_element_id)
      const toEl = modelElements.get(iface.to_element_id)
      if (!fromEl || !toEl) continue
      const aRaw = fromEl.subsystem_domain || fromEl.name.toLowerCase().replace(/\s+/g, '_')
      const bRaw = toEl.subsystem_domain || toEl.name.toLowerCase().replace(/\s+/g, '_')
      const a = DOMAIN_ALIASES[aRaw] || aRaw
      const b = DOMAIN_ALIASES[bRaw] || bRaw
      const key = `${a}-${b}`
      if (!dynamic[key]) {
        dynamic[key] = { types: [iface.interface_type], description: iface.name || iface.diagram_label || '', hasConflict: false }
      } else {
        if (!dynamic[key].types.includes(iface.interface_type)) dynamic[key].types.push(iface.interface_type)
      }
    }
    return dynamic
  }, [modelInterfaces, modelElements])

  // Cell lookup: prefer model data, fall back to static (space + ground)
  const getCell = (a: string, b: string): InterfaceCell | null => {
    return dynamicInterfaces[`${a}-${b}`] || dynamicInterfaces[`${b}-${a}`]
      || INTERFACE_DATA[`${a}-${b}`] || INTERFACE_DATA[`${b}-${a}`]
      || GROUND_INTERFACE_DATA[`${a}-${b}`] || GROUND_INTERFACE_DATA[`${b}-${a}`]
      || null
  }

  const [resolvingCell, setResolvingCell] = useState<string | null>(null)
  const [selectedOption, setSelectedOption] = useState('')
  const [rationale, setRationale] = useState('')

  const selectedData = selectedCell ? (INTERFACE_DATA[selectedCell] || null) : null
  const conflicts = Object.entries(INTERFACE_DATA).filter(([, c]) => c.hasConflict)
  const resolvedCount = Array.from(resolutions.values()).filter(r => r.status === 'resolved' || r.status === 'accepted_risk').length

  const handleResolve = (cellKey: string, status: ResolutionStatus) => {
    if (!selectedOption && status === 'resolved') return
    setResolutions(prev => {
      const next = new Map(prev)
      next.set(cellKey, { cellKey, status, selectedOption, rationale, resolvedBy: 'systems' })
      return next
    })
    setResolvingCell(null)
    setSelectedOption('')
    setRationale('')
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Interface Matrix</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Subsystem-to-subsystem interfaces. Red borders = conflict. Click a cell for details and resolution.
      </p>

      <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem', marginBottom: '0.75rem', alignItems: 'center' }}>
        <span>{Object.keys(INTERFACE_DATA).length + Object.keys(dynamicInterfaces).filter(k => !INTERFACE_DATA[k]).length} interfaces</span>
        {modelInterfaces.size > 0 && (
          <span style={{ color: '#10b981', fontSize: '0.65rem' }}>({modelInterfaces.size} from model)</span>
        )}
        <span style={{ color: '#ef4444' }}>{conflicts.length} conflicts</span>
        <span style={{ color: '#10b981' }}>{resolvedCount} resolved</span>
        <span style={{ color: '#f59e0b' }}>{conflicts.length - resolvedCount} open</span>
      </div>

      {/* Conflict summary bar */}
      {conflicts.length > 0 && (
        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
          {conflicts.map(([key, cell]) => {
            const res = resolutions.get(key)
            const statusInfo = res ? STATUS_LABELS[res.status] : STATUS_LABELS.open
            return (
              <button key={key} onClick={() => { setSelectedCell(key); setResolvingCell(null) }}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.68rem',
                  padding: '0.2rem 0.5rem', borderRadius: '4px', border: 'none', cursor: 'pointer',
                  background: selectedCell === key ? 'rgba(59,130,246,0.2)' : 'var(--bg-secondary, #1f2937)',
                  color: statusInfo.color,
                }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: SEVERITY_COLORS[cell.conflictSeverity || 'minor'] }} />
                {key.replace('-', '/')}
                <span style={{ fontSize: '0.6rem', opacity: 0.8 }}>{statusInfo.label}</span>
              </button>
            )
          })}
        </div>
      )}

      {/* Matrix grid */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', fontSize: '0.68rem' }}>
          <thead>
            <tr>
              <th style={{ padding: '0.3rem', width: 70 }}></th>
              {SUBSYSTEMS.map(s => (
                <th key={s} style={{ padding: '0.3rem', textTransform: 'uppercase', color: '#9ca3af', width: 65, textAlign: 'center', fontSize: '0.6rem' }}>
                  {s.slice(0, 5)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SUBSYSTEMS.map(row => (
              <tr key={row}>
                <td style={{ padding: '0.3rem', textTransform: 'uppercase', color: '#9ca3af', fontWeight: 600, fontSize: '0.6rem' }}>
                  {row.slice(0, 5)}
                </td>
                {SUBSYSTEMS.map(col => {
                  if (row === col) return <td key={col} style={{ background: '#1a1a2e', width: 65, height: 35 }} />
                  const cell = getCell(row, col)
                  const cellKey = `${row}-${col}`
                  const altKey = `${col}-${row}`
                  const isHovered = hoveredCell === cellKey
                  const isSelected = selectedCell === cellKey || selectedCell === altKey
                  const res = resolutions.get(cellKey) || resolutions.get(altKey)
                  const isResolved = res && (res.status === 'resolved' || res.status === 'accepted_risk')
                  return (
                    <td key={col}
                      onMouseEnter={() => setHoveredCell(cellKey)}
                      onMouseLeave={() => setHoveredCell(null)}
                      onClick={() => cell && setSelectedCell(isSelected ? null : (INTERFACE_DATA[cellKey] ? cellKey : altKey))}
                      style={{
                        width: 65, height: 35, textAlign: 'center', cursor: cell ? 'pointer' : 'default',
                        background: cell ? (isSelected ? 'rgba(59,130,246,0.2)' : isHovered ? 'rgba(255,255,255,0.05)' : 'var(--bg-secondary, #1f2937)') : 'transparent',
                        border: cell?.hasConflict
                          ? isResolved ? '2px solid #10b981' : `2px solid ${SEVERITY_COLORS[cell.conflictSeverity || 'minor']}`
                          : '1px solid var(--border, #374151)',
                      }}>
                      {cell && (
                        <div style={{ display: 'flex', gap: '1px', justifyContent: 'center', flexWrap: 'wrap' }}>
                          {cell.types.map(t => (
                            <span key={t} style={{ width: 8, height: 8, borderRadius: '50%', background: TYPE_COLORS[t] || '#6b7280' }} title={t} />
                          ))}
                        </div>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.75rem', fontSize: '0.65rem', color: '#9ca3af' }}>
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <span key={type} style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: color }} /> {type}
          </span>
        ))}
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
          <span style={{ width: 10, height: 10, border: '2px solid #ef4444' }} /> critical
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
          <span style={{ width: 10, height: 10, border: '2px solid #f59e0b' }} /> major
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
          <span style={{ width: 10, height: 10, border: '2px solid #10b981' }} /> resolved
        </span>
      </div>

      {/* Detail + resolution panel */}
      {selectedData && selectedCell && (
        <div style={{
          marginTop: '0.75rem', padding: '0.75rem', borderRadius: '6px',
          background: selectedData.hasConflict ? 'rgba(239,68,68,0.08)' : 'var(--bg-secondary, #1f2937)',
          border: `1px solid ${selectedData.hasConflict ? SEVERITY_COLORS[selectedData.conflictSeverity || 'minor'] : 'var(--border, #374151)'}`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
            <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{selectedCell.replace('-', ' \u2194 ')}</span>
            {selectedData.conflictSeverity && (
              <span style={{
                fontSize: '0.6rem', padding: '0.1rem 0.35rem', borderRadius: '3px',
                background: `${SEVERITY_COLORS[selectedData.conflictSeverity]}22`,
                color: SEVERITY_COLORS[selectedData.conflictSeverity], fontWeight: 600, textTransform: 'uppercase',
              }}>{selectedData.conflictSeverity}</span>
            )}
            {resolutions.has(selectedCell) && (
              <span style={{
                fontSize: '0.6rem', padding: '0.1rem 0.35rem', borderRadius: '3px',
                background: `${STATUS_LABELS[resolutions.get(selectedCell)!.status].color}22`,
                color: STATUS_LABELS[resolutions.get(selectedCell)!.status].color,
                fontWeight: 600,
              }}>{STATUS_LABELS[resolutions.get(selectedCell)!.status].label}</span>
            )}
          </div>
          <div style={{ fontSize: '0.78rem', marginBottom: '0.3rem' }}>{selectedData.description}</div>
          <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.3rem' }}>
            Types: {selectedData.types.join(', ')}
          </div>

          {selectedData.hasConflict && (
            <>
              <div style={{ fontSize: '0.78rem', color: '#ef4444', fontWeight: 500, marginBottom: '0.3rem' }}>
                Conflict: {selectedData.conflictTitle}
              </div>

              {/* Affected parameters with "Go fix" links */}
              {selectedData.affectedParameters && (
                <div style={{ fontSize: '0.72rem', marginBottom: '0.3rem' }}>
                  <span style={{ color: '#9ca3af' }}>Affected parameters:</span>
                  <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginTop: '0.15rem' }}>
                    {selectedData.affectedParameters.map(p => (
                      <span key={p} style={{
                        fontFamily: 'monospace', fontSize: '0.68rem', padding: '0.1rem 0.35rem',
                        borderRadius: '3px', background: 'rgba(59,130,246,0.1)', color: '#3b82f6',
                        cursor: onNavigate ? 'pointer' : 'default',
                      }} onClick={() => onNavigate?.('design')} title="Click to navigate to design parameters">
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Responsible positions */}
              {selectedData.responsiblePositions && (
                <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.4rem' }}>
                  Responsible: {selectedData.responsiblePositions.join(', ')}
                </div>
              )}

              {/* Resolution panel */}
              {resolvingCell === selectedCell ? (
                <div style={{
                  padding: '0.5rem', background: 'rgba(59,130,246,0.08)', borderRadius: '4px',
                  border: '1px solid rgba(59,130,246,0.2)', marginTop: '0.3rem',
                }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#3b82f6', marginBottom: '0.3rem' }}>
                    Select Resolution
                  </div>
                  {selectedData.resolutionOptions?.map(opt => (
                    <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', marginBottom: '0.2rem', cursor: 'pointer' }}>
                      <input type="radio" name="resolution" checked={selectedOption === opt}
                        onChange={() => setSelectedOption(opt)} style={{ accentColor: '#3b82f6' }} />
                      {opt}
                    </label>
                  ))}
                  <textarea className="input" value={rationale} onChange={e => setRationale(e.target.value)}
                    placeholder="Rationale for this resolution..." rows={2}
                    style={{ width: '100%', fontSize: '0.72rem', marginTop: '0.3rem', resize: 'vertical' }} />
                  <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.3rem' }}>
                    <button className="btn btn-sm" onClick={() => handleResolve(selectedCell, 'resolved')}
                      disabled={!selectedOption} style={{ background: '#10b981', fontSize: '0.68rem' }}>Resolve</button>
                    <button className="btn btn-sm" onClick={() => handleResolve(selectedCell, 'accepted_risk')}
                      style={{ background: '#8b5cf6', fontSize: '0.68rem' }}>Accept Risk</button>
                    <button className="btn btn-sm" onClick={() => handleResolve(selectedCell, 'deferred')}
                      style={{ background: '#6b7280', fontSize: '0.68rem' }}>Defer</button>
                    <button className="btn btn-sm" onClick={() => setResolvingCell(null)}
                      style={{ background: '#374151', fontSize: '0.68rem' }}>Cancel</button>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.3rem' }}>
                  {!resolutions.has(selectedCell) && (
                    <button className="btn btn-sm" onClick={() => setResolvingCell(selectedCell)}
                      style={{ fontSize: '0.7rem', background: '#3b82f6' }}>Resolve Conflict</button>
                  )}
                  {resolutions.has(selectedCell) && (
                    <>
                      <div style={{ fontSize: '0.72rem', color: '#9ca3af', flex: 1 }}>
                        Resolution: <strong style={{ color: '#d1d5db' }}>{resolutions.get(selectedCell)!.selectedOption}</strong>
                        {resolutions.get(selectedCell)!.rationale && (
                          <div style={{ fontSize: '0.68rem', color: '#6b7280', marginTop: '0.1rem' }}>
                            {resolutions.get(selectedCell)!.rationale}
                          </div>
                        )}
                      </div>
                      <button className="btn btn-sm" onClick={() => setResolvingCell(selectedCell)}
                        style={{ fontSize: '0.68rem' }}>Re-evaluate</button>
                    </>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
