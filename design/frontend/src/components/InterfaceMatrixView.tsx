import { useState } from 'react'

// Standard subsystem interface data (matches interfaces.py)
const SUBSYSTEMS = ['power', 'aocs', 'link', 'thermal', 'structure', 'propulsion', 'data', 'payload']

interface InterfaceCell {
  types: string[]
  description: string
  hasConflict: boolean
  conflictTitle?: string
}

// Pre-populated from generate_standard_interface_matrix()
const INTERFACE_DATA: Record<string, InterfaceCell> = {
  'power-aocs': { types: ['electrical'], description: 'Power bus to AOCS electronics + reaction wheels', hasConflict: false },
  'power-link': { types: ['electrical'], description: 'Power bus to TTC transponder + PA', hasConflict: false },
  'power-thermal': { types: ['electrical', 'thermal'], description: 'Power bus to heaters; SA thermal coupling', hasConflict: true, conflictTitle: 'Radiator area vs SA area competition' },
  'power-data': { types: ['electrical'], description: 'Power bus to OBC', hasConflict: true, conflictTitle: 'Power bus voltage compatibility' },
  'power-payload': { types: ['electrical'], description: 'Power bus to payload; peak power switching', hasConflict: false },
  'power-propulsion': { types: ['electrical'], description: 'Power bus to valve drivers / EP PPU', hasConflict: true, conflictTitle: 'Thruster plume impingement on solar array' },
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
  'link-payload': { types: ['rf'], description: 'RF interference; antenna pattern vs payload FOV', hasConflict: true, conflictTitle: 'EMC: TX interference with payload' },
  'link-aocs': { types: ['rf', 'optical'], description: 'Antenna deployment vs star tracker FOV', hasConflict: true, conflictTitle: 'Solar array vs star tracker FOV' },
  'propulsion-aocs': { types: ['mechanical'], description: 'Thruster alignment; plume impingement on SA/sensors', hasConflict: false },
  'aocs-payload': { types: ['mechanical'], description: 'Reaction wheel vibration vs payload stability', hasConflict: true, conflictTitle: 'Reaction wheel vibration vs payload stability' },
}

const TYPE_COLORS: Record<string, string> = {
  mechanical: '#84cc16', electrical: '#f59e0b', thermal: '#ef4444',
  data: '#3b82f6', rf: '#ec4899', optical: '#8b5cf6', propulsion: '#f97316', software: '#06b6d4',
}

function getCell(a: string, b: string): InterfaceCell | null {
  return INTERFACE_DATA[`${a}-${b}`] || INTERFACE_DATA[`${b}-${a}`] || null
}

export function InterfaceMatrixView() {
  const [hoveredCell, setHoveredCell] = useState<string | null>(null)
  const [selectedCell, setSelectedCell] = useState<string | null>(null)

  const selectedData = selectedCell ? (INTERFACE_DATA[selectedCell] || null) : null

  const conflictCount = Object.values(INTERFACE_DATA).filter(c => c.hasConflict).length

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Interface Matrix</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Subsystem-to-subsystem interfaces. Red borders = detected conflict area. Click a cell for details.
      </p>

      <div style={{ fontSize: '0.75rem', marginBottom: '0.75rem' }}>
        <span>{Object.keys(INTERFACE_DATA).length} interfaces</span>
        <span style={{ color: '#ef4444', marginLeft: '0.75rem' }}>{conflictCount} conflict areas</span>
      </div>

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
                  if (row === col) {
                    return <td key={col} style={{ background: '#1a1a2e', width: 65, height: 35 }} />
                  }
                  const cell = getCell(row, col)
                  const cellKey = `${row}-${col}`
                  const isHovered = hoveredCell === cellKey
                  const isSelected = selectedCell === cellKey || selectedCell === `${col}-${row}`
                  return (
                    <td key={col}
                      onMouseEnter={() => setHoveredCell(cellKey)}
                      onMouseLeave={() => setHoveredCell(null)}
                      onClick={() => cell && setSelectedCell(isSelected ? null : (INTERFACE_DATA[cellKey] ? cellKey : `${col}-${row}`))}
                      style={{
                        width: 65, height: 35, textAlign: 'center', cursor: cell ? 'pointer' : 'default',
                        background: cell ? (isSelected ? 'rgba(59,130,246,0.2)' : isHovered ? 'rgba(255,255,255,0.05)' : 'var(--bg-secondary, #1f2937)') : 'transparent',
                        border: cell?.hasConflict ? '2px solid #ef4444' : '1px solid var(--border, #374151)',
                      }}>
                      {cell && (
                        <div style={{ display: 'flex', gap: '1px', justifyContent: 'center', flexWrap: 'wrap' }}>
                          {cell.types.map(t => (
                            <span key={t} style={{
                              width: 8, height: 8, borderRadius: '50%',
                              background: TYPE_COLORS[t] || '#6b7280',
                            }} title={t} />
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
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
            {type}
          </span>
        ))}
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
          <span style={{ width: 10, height: 10, border: '2px solid #ef4444' }} />
          conflict
        </span>
      </div>

      {/* Detail panel */}
      {selectedData && (
        <div style={{
          marginTop: '0.75rem', padding: '0.75rem', borderRadius: '6px',
          background: selectedData.hasConflict ? 'rgba(239,68,68,0.08)' : 'var(--bg-secondary, #1f2937)',
          border: `1px solid ${selectedData.hasConflict ? '#ef4444' : 'var(--border, #374151)'}`,
        }}>
          <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.3rem' }}>
            {selectedCell?.replace('-', ' ↔ ')}
          </div>
          <div style={{ fontSize: '0.78rem', marginBottom: '0.3rem' }}>{selectedData.description}</div>
          <div style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
            Types: {selectedData.types.join(', ')}
          </div>
          {selectedData.hasConflict && (
            <div style={{ marginTop: '0.3rem', fontSize: '0.78rem', color: '#ef4444', fontWeight: 500 }}>
              Conflict: {selectedData.conflictTitle}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
