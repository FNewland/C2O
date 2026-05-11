/**
 * GroundStationDesigner — define ground stations as elements in the tree.
 *
 * For each station: name, lat/lon, antenna diameter, frequency bands, cost.
 * Shows world map with station markers and coverage footprints.
 *
 * Stations are component elements under the Ground Segment with
 * performance JSON holding lat/lon/antenna/bands/elevation.
 */
import { useState, useMemo, useCallback } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'

interface GroundStationView {
  elementId: string
  name: string
  latitude: number
  longitude: number
  antenna_m: number
  bands: string[]
  min_elevation: number
  cost_keur: number
  owned: boolean
}

export function GroundStationDesigner() {
  const studyId = useDesignStore(s => s.studyId)
  const elements = useModelStore(s => s.elements)
  const createElement = useModelStore(s => s.createElement)
  const updateElement = useModelStore(s => s.updateElement)
  const deleteElement = useModelStore(s => s.deleteElement)
  const [editing, setEditing] = useState<string | null>(null)

  // Find the Ground Segment element (or any ground system)
  const groundSegmentId = useMemo(() => {
    for (const el of elements.values()) {
      if (el.element_type === 'segment' && el.segment === 'ground') return el.id
    }
    return null
  }, [elements])

  // Find or identify a "Ground Station Network" system under ground segment
  const gsNetworkId = useMemo(() => {
    if (!groundSegmentId) return null
    for (const el of elements.values()) {
      if (el.parent_id === groundSegmentId && el.element_type === 'system' &&
          el.name?.toLowerCase().includes('station')) return el.id
    }
    // Fall back to ground segment itself if no network system exists
    return groundSegmentId
  }, [elements, groundSegmentId])

  // Extract ground station views from element tree
  const stations: GroundStationView[] = useMemo(() => {
    const result: GroundStationView[] = []
    const parentId = gsNetworkId || groundSegmentId
    if (!parentId) return result
    for (const el of elements.values()) {
      if (el.parent_id === parentId && el.element_type === 'component' && el.segment === 'ground') {
        const perf = el.performance || {}
        result.push({
          elementId: el.id,
          name: el.name,
          latitude: perf.latitude ?? 0,
          longitude: perf.longitude ?? 0,
          antenna_m: perf.antenna_m ?? 5,
          bands: perf.bands ?? ['S'],
          min_elevation: perf.min_elevation ?? 5,
          cost_keur: el.cost_recurring_keur ?? 0,
          owned: perf.owned ?? false,
        })
      }
    }
    return result
  }, [elements, gsNetworkId, groundSegmentId])

  const addStation = useCallback(async () => {
    if (!studyId || !gsNetworkId) return
    const id = await createElement(studyId, {
      name: 'New Station',
      element_type: 'component',
      segment: 'ground',
      parent_id: gsNetworkId,
      cost_recurring_keur: 100,
      performance: { latitude: 0, longitude: 0, antenna_m: 5, bands: ['S'], min_elevation: 5, owned: true },
    } as any)
    if (id) setEditing(id)
    useDesignStore.getState().markStale('ground_stations')
  }, [studyId, gsNetworkId, createElement])

  const updateStation = useCallback((elementId: string, field: string, value: any) => {
    const el = elements.get(elementId)
    if (!el) return
    const perf = { ...(el.performance || {}) }
    if (field === 'name') {
      updateElement(elementId, { name: value })
    } else if (field === 'cost_keur') {
      updateElement(elementId, { cost_recurring_keur: value })
    } else {
      perf[field] = value
      updateElement(elementId, { performance: perf })
    }
    useDesignStore.getState().markStale('ground_stations')
  }, [elements, updateElement])

  const removeStation = useCallback((elementId: string) => {
    deleteElement(elementId)
    useDesignStore.getState().markStale('ground_stations')
  }, [deleteElement])

  const totalCost = stations.reduce((s, gs) => s + gs.cost_keur, 0)

  if (!groundSegmentId) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>
        <p>No Ground Segment found in the element tree.</p>
        <p style={{ fontSize: '0.75rem' }}>Add a "Ground Segment" element in the Mission Architecture view first.</p>
      </div>
    )
  }

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
          <rect x="-180" y="-90" width="360" height="180" fill="#0f172a" />
          {[-60, -30, 0, 30, 60].map(lat => (
            <line key={lat} x1="-180" y1={-lat} x2="180" y2={-lat} stroke="#1f2937" strokeWidth="0.5" />
          ))}
          {[-120, -60, 0, 60, 120].map(lon => (
            <line key={lon} x1={lon} y1="-90" x2={lon} y2="90" stroke="#1f2937" strokeWidth="0.5" />
          ))}
          {stations.map(gs => (
            <g key={gs.elementId}>
              <circle cx={gs.longitude} cy={-gs.latitude} r={3} fill="#10b981" stroke="#065f46" strokeWidth={1} />
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
            <tr key={gs.elementId} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={td}>
                {editing === gs.elementId ? (
                  <input value={gs.name} onChange={e => updateStation(gs.elementId, 'name', e.target.value)}
                    onBlur={() => setEditing(null)}
                    style={{ ...inputStyle, width: '100px' }} />
                ) : (
                  <span onClick={() => setEditing(gs.elementId)} style={{ cursor: 'pointer' }}>{gs.name}</span>
                )}
              </td>
              <td style={tdR}>
                <input type="number" value={gs.latitude} onChange={e => updateStation(gs.elementId, 'latitude', Number(e.target.value))}
                  style={{ ...inputStyle, width: '55px' }} />
              </td>
              <td style={tdR}>
                <input type="number" value={gs.longitude} onChange={e => updateStation(gs.elementId, 'longitude', Number(e.target.value))}
                  style={{ ...inputStyle, width: '55px' }} />
              </td>
              <td style={tdR}>
                <input type="number" value={gs.antenna_m} step={0.5} onChange={e => updateStation(gs.elementId, 'antenna_m', Number(e.target.value))}
                  style={{ ...inputStyle, width: '45px' }} />
              </td>
              <td style={td}>
                <input value={gs.bands.join(',')} onChange={e => updateStation(gs.elementId, 'bands', e.target.value.split(',').map(s => s.trim()))}
                  style={{ ...inputStyle, width: '60px' }} />
              </td>
              <td style={tdR}>
                <input type="number" value={gs.cost_keur} onChange={e => updateStation(gs.elementId, 'cost_keur', Number(e.target.value))}
                  style={{ ...inputStyle, width: '55px' }} />
              </td>
              <td style={tdC}>
                <select value={gs.owned ? 'own' : 'lease'} onChange={e => updateStation(gs.elementId, 'owned', e.target.value === 'own')}
                  style={{ ...inputStyle, width: '55px' }}>
                  <option value="lease">Lease</option>
                  <option value="own">Own</option>
                </select>
              </td>
              <td style={tdC}>
                <button onClick={() => removeStation(gs.elementId)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.7rem' }}>×</button>
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
