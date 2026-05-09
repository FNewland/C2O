/**
 * GroundStationDesigner — define ground stations with location, equipment, and cost.
 *
 * For each station: name, lat/lon, antenna diameter, frequency bands, cost.
 * Shows world map with station markers and coverage footprints.
 */
import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'

interface GroundStation {
  id: string
  name: string
  latitude: number
  longitude: number
  antenna_m: number
  bands: string[]
  min_elevation: number
  cost_keur: number
  owned: boolean
}

const DEFAULT_STATIONS: GroundStation[] = [
  { id: 'gs1', name: 'Svalbard', latitude: 78.2, longitude: 15.4, antenna_m: 13, bands: ['S', 'X'], min_elevation: 5, cost_keur: 500, owned: false },
  { id: 'gs2', name: 'Kiruna', latitude: 67.9, longitude: 20.2, antenna_m: 13, bands: ['S', 'X'], min_elevation: 5, cost_keur: 400, owned: false },
  { id: 'gs3', name: 'Weilheim', latitude: 47.9, longitude: 11.1, antenna_m: 15, bands: ['S', 'X', 'Ka'], min_elevation: 5, cost_keur: 600, owned: false },
]

export function GroundStationDesigner() {
  const storedStations = useDesignStore(s => s.groundStations) as GroundStation[]
  const setStoredStations = useDesignStore(s => s.setGroundStations)
  const [stations, setStationsLocal] = useState<GroundStation[]>(storedStations?.length ? storedStations : DEFAULT_STATIONS)
  const setStations = (updater: GroundStation[] | ((prev: GroundStation[]) => GroundStation[])) => {
    setStationsLocal(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      setStoredStations(next)
      return next
    })
  }
  const [editing, setEditing] = useState<string | null>(null)

  const addStation = () => {
    const newStation: GroundStation = {
      id: `gs-${Date.now()}`,
      name: 'New Station',
      latitude: 0, longitude: 0, antenna_m: 5,
      bands: ['S'], min_elevation: 5, cost_keur: 100, owned: true,
    }
    setStations(prev => [...prev, newStation])
    setEditing(newStation.id)
  }

  const updateStation = (id: string, field: keyof GroundStation, value: any) => {
    setStations(prev => prev.map(s => s.id === id ? { ...s, [field]: value } : s))
  }

  const removeStation = (id: string) => {
    setStations(prev => prev.filter(s => s.id !== id))
  }

  const totalCost = stations.reduce((s, gs) => s + gs.cost_keur, 0)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1rem', margin: 0 }}>Ground Station Network</h2>
          <p style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
            {stations.length} stations, total cost: {totalCost} kEUR/year
          </p>
        </div>
        <button onClick={addStation} className="btn btn-sm" style={{ background: '#10b981', fontSize: '0.72rem' }}>
          + Add Station
        </button>
      </div>

      {/* World map (simplified SVG) */}
      <div className="card" style={{ marginBottom: '0.75rem', padding: '0.5rem' }}>
        <svg width="100%" height="200" viewBox="-180 -90 360 180" style={{ background: '#0a0e1a', borderRadius: '4px' }}>
          {/* Simplified continent outlines */}
          <rect x="-180" y="-90" width="360" height="180" fill="#0f172a" />
          {/* Grid lines */}
          {[-60, -30, 0, 30, 60].map(lat => (
            <line key={lat} x1="-180" y1={-lat} x2="180" y2={-lat} stroke="#1f2937" strokeWidth="0.5" />
          ))}
          {[-120, -60, 0, 60, 120].map(lon => (
            <line key={lon} x1={lon} y1="-90" x2={lon} y2="90" stroke="#1f2937" strokeWidth="0.5" />
          ))}
          {/* Station markers */}
          {stations.map(gs => (
            <g key={gs.id}>
              <circle cx={gs.longitude} cy={-gs.latitude} r={3} fill="#10b981" stroke="#065f46" strokeWidth={1} />
              {/* Coverage footprint (rough: antenna elevation mask) */}
              <circle cx={gs.longitude} cy={-gs.latitude} r={gs.antenna_m * 1.5} fill="none" stroke="#10b98140" strokeWidth={0.5} strokeDasharray="2 1" />
              <text x={gs.longitude + 4} y={-gs.latitude + 2} fill="#9ca3af" fontSize="4">{gs.name}</text>
            </g>
          ))}
        </svg>
      </div>

      {/* Station table */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
            <th style={th}>Station</th>
            <th style={thR}>Lat</th>
            <th style={thR}>Lon</th>
            <th style={thR}>Antenna (m)</th>
            <th style={th}>Bands</th>
            <th style={thR}>Cost (kEUR)</th>
            <th style={thC}>Own/Lease</th>
            <th style={thC}></th>
          </tr>
        </thead>
        <tbody>
          {stations.map(gs => (
            <tr key={gs.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={td}>
                {editing === gs.id ? (
                  <input value={gs.name} onChange={e => updateStation(gs.id, 'name', e.target.value)}
                    style={{ ...inputStyle, width: '100px' }} />
                ) : (
                  <span onClick={() => setEditing(gs.id)} style={{ cursor: 'pointer' }}>{gs.name}</span>
                )}
              </td>
              <td style={tdR}>
                <input type="number" value={gs.latitude} onChange={e => updateStation(gs.id, 'latitude', Number(e.target.value))}
                  style={{ ...inputStyle, width: '55px' }} />
              </td>
              <td style={tdR}>
                <input type="number" value={gs.longitude} onChange={e => updateStation(gs.id, 'longitude', Number(e.target.value))}
                  style={{ ...inputStyle, width: '55px' }} />
              </td>
              <td style={tdR}>
                <input type="number" value={gs.antenna_m} step={0.5} onChange={e => updateStation(gs.id, 'antenna_m', Number(e.target.value))}
                  style={{ ...inputStyle, width: '45px' }} />
              </td>
              <td style={td}>
                <input value={gs.bands.join(',')} onChange={e => updateStation(gs.id, 'bands', e.target.value.split(',').map(s => s.trim()))}
                  style={{ ...inputStyle, width: '60px' }} />
              </td>
              <td style={tdR}>
                <input type="number" value={gs.cost_keur} onChange={e => updateStation(gs.id, 'cost_keur', Number(e.target.value))}
                  style={{ ...inputStyle, width: '55px' }} />
              </td>
              <td style={tdC}>
                <select value={gs.owned ? 'own' : 'lease'} onChange={e => updateStation(gs.id, 'owned', e.target.value === 'own')}
                  style={{ ...inputStyle, width: '55px' }}>
                  <option value="lease">Lease</option>
                  <option value="own">Own</option>
                </select>
              </td>
              <td style={tdC}>
                <button onClick={() => removeStation(gs.id)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.7rem' }}>×</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
const inputStyle: React.CSSProperties = { background: 'var(--bg-primary, #111827)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db', fontSize: '0.7rem', padding: '0.1rem 0.3rem', textAlign: 'right' }
