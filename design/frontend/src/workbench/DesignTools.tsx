/**
 * DesignTools — Context-sensitive design support tools.
 *
 * Shows different tools based on what element is focused:
 * - Constellation element (quantity > 1, space): orbit selector, Walker config
 * - Ground station element: location picker, frequency bands, elevation
 * - Any element with domain: relevant engineering parameters
 */
import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'

const API = '/api'

const ORBIT_PRESETS = [
  { name: 'LEO SSO', altitude: 500, inclination: 97.4, desc: 'Sun-synchronous, dawn-dusk LTAN' },
  { name: 'LEO Equatorial', altitude: 400, inclination: 0, desc: 'Equatorial low Earth orbit' },
  { name: 'LEO Polar', altitude: 600, inclination: 90, desc: 'Polar orbit, global coverage' },
  { name: 'MEO', altitude: 2000, inclination: 55, desc: 'Medium Earth orbit (GNSS-like)' },
  { name: 'ISS', altitude: 410, inclination: 51.6, desc: 'ISS altitude and inclination' },
]

const FREQUENCY_BANDS = [
  { band: 'UHF', freq: '400 MHz', use: 'CubeSat TT&C, low data rate' },
  { band: 'S-band', freq: '2.0-2.3 GHz', use: 'Standard TT&C, medium data rate' },
  { band: 'X-band', freq: '8.0-8.4 GHz', use: 'High data rate downlink, Earth observation' },
  { band: 'Ka-band', freq: '26-40 GHz', use: 'Very high data rate, weather-sensitive' },
  { band: 'L-band', freq: '1.2-1.5 GHz', use: 'Navigation, AIS, low-rate data' },
]

const GS_LOCATIONS = [
  { name: 'Svalbard', lat: 78.2, lon: 15.4, provider: 'KSAT' },
  { name: 'Kiruna', lat: 67.9, lon: 20.2, provider: 'SSC' },
  { name: 'Weilheim', lat: 47.9, lon: 11.1, provider: 'DLR' },
  { name: 'Kourou', lat: 5.2, lon: -52.8, provider: 'ESA/CNES' },
  { name: 'Maspalomas', lat: 27.8, lon: -15.6, provider: 'INTA' },
  { name: 'Inuvik', lat: 68.3, lon: -133.7, provider: 'CSA' },
  { name: 'Gatineau', lat: 45.6, lon: -75.6, provider: 'CSA' },
  { name: 'Prince Albert', lat: 53.2, lon: -105.9, provider: 'CSA' },
  { name: 'Troll', lat: -72.0, lon: 2.5, provider: 'KSAT' },
  { name: 'Hartebeesthoek', lat: -25.9, lon: 27.7, provider: 'SANSA' },
]

export function DesignTools() {
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const qc = useQueryClient()

  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })

  const focusElement = allElements.find((e: any) => e.id === focusElementId)
  if (!focusElement) return null

  const isConstellation = (focusElement.quantity || 1) > 1 && focusElement.segment === 'space'
  const isGroundStation = focusElement.domain === 'ground' || focusElement.segment === 'ground'
    || focusElement.subsystem_domain === 'ground'
  const isSpacecraft = (focusElement.element_type === 'system' || focusElement.element_type === 'subsystem'
    || focusElement.element_type === 'segment') && focusElement.segment === 'space'

  if (!isGroundStation && !isSpacecraft) return null

  return (
    <div style={{ marginTop: '0.5rem', borderTop: '1px solid var(--border)', paddingTop: '0.5rem' }}>
      {/* Show what element we're configuring */}
      <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
        Configuring: <b style={{ color: 'var(--text-primary)' }}>{focusElement.name}</b>
        <span style={{ marginLeft: '0.3rem' }}>({focusElement.element_type}, {focusElement.segment})</span>
      </div>
      {(isConstellation || isSpacecraft) && (
        <OrbitTools elementId={focusElement.id} element={focusElement} version={focusElement.version} />
      )}
      {isGroundStation && (
        <GroundStationTools elementId={focusElement.id} element={focusElement} version={focusElement.version} />
      )}
    </div>
  )
}

function OrbitTools({ elementId, element, version }: { elementId: string; element: any; version: number }) {
  const qc = useQueryClient()
  const studyId = useUIStore(s => s.studyId)
  const perf = element.performance || {}
  const quantity = element.quantity || 1

  const setOrbit = useCallback(async (altitude: number, inclination: number) => {
    const newPerf = { ...perf, orbit_altitude_km: altitude, orbit_inclination_deg: inclination }
    await fetch(`${API}/elements/${elementId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ performance: newPerf, version }),
    })
    qc.invalidateQueries({ queryKey: ['elements', studyId] })
  }, [elementId, perf, version, qc, studyId])

  const setWalker = useCallback(async (planes: number, satsPerPlane: number) => {
    const total = planes * satsPerPlane
    const newPerf = { ...perf, constellation: true, orbital_planes: planes, sats_per_plane: satsPerPlane }
    await fetch(`${API}/elements/${elementId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ performance: newPerf, quantity: total, version }),
    })
    qc.invalidateQueries({ queryKey: ['elements', studyId] })
  }, [elementId, perf, version, qc, studyId])

  return (
    <div>
      <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--info)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>
        Orbit & Constellation
      </div>

      {/* Current orbit */}
      {perf.orbit_altitude_km && (
        <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
          Current: {perf.orbit_altitude_km} km, {perf.orbit_inclination_deg}° incl
          {quantity > 1 && ` | ${perf.orbital_planes || '?'} planes × ${perf.sats_per_plane || '?'} sats = ${quantity}`}
        </div>
      )}

      {/* Orbit presets */}
      <div style={{ display: 'flex', gap: '0.2rem', flexWrap: 'wrap', marginBottom: '0.3rem' }}>
        {ORBIT_PRESETS.map(o => (
          <button key={o.name} onClick={() => setOrbit(o.altitude, o.inclination)} title={o.desc}
            style={{
              padding: '0.15rem 0.4rem', fontSize: '0.6rem', borderRadius: '3px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              color: 'var(--text-primary)', cursor: 'pointer',
            }}>
            {o.name} ({o.altitude}km)
          </button>
        ))}
      </div>

      {/* Walker constellation config */}
      {quantity > 1 && (
        <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', fontSize: '0.68rem' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Walker:</span>
          {[[1, 4], [2, 4], [3, 4], [4, 6], [6, 6]].map(([p, s]) => (
            <button key={`${p}x${s}`} onClick={() => setWalker(p, s)}
              style={{
                padding: '0.1rem 0.3rem', fontSize: '0.6rem', borderRadius: '2px',
                background: (perf.orbital_planes === p && perf.sats_per_plane === s) ? 'var(--accent)' : 'var(--bg-card)',
                color: (perf.orbital_planes === p && perf.sats_per_plane === s) ? 'white' : 'var(--text-secondary)',
                border: 'none', cursor: 'pointer',
              }}>
              {p}×{s}={p * s}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function GroundStationTools({ elementId, element, version }: { elementId: string; element: any; version: number }) {
  const qc = useQueryClient()
  const studyId = useUIStore(s => s.studyId)
  const perf = element.performance || {}

  const setLocation = useCallback(async (loc: typeof GS_LOCATIONS[0]) => {
    const newPerf = { ...perf, latitude: loc.lat, longitude: loc.lon, location: loc.name, provider: loc.provider }
    await fetch(`${API}/elements/${elementId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ performance: newPerf, version }),
    })
    // Propagate location to child antenna/subsystem elements
    if (studyId) {
      const allEls: any[] = qc.getQueryData(['elements', studyId]) || []
      for (const child of allEls.filter((e: any) => e.parent_id === elementId)) {
        const childPerf = { ...(child.performance || {}), latitude: loc.lat, longitude: loc.lon, location: loc.name }
        fetch(`${API}/elements/${child.id}`, {
          method: 'PATCH', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ performance: childPerf, version: child.version }),
        }).catch(() => {})
      }
    }
    qc.invalidateQueries({ queryKey: ['elements', studyId] })
  }, [elementId, perf, version, qc, studyId])

  const setBand = useCallback(async (band: string) => {
    const bands = perf.bands || []
    const newBands = bands.includes(band) ? bands.filter((b: string) => b !== band) : [...bands, band]
    const newPerf = { ...perf, bands: newBands }
    await fetch(`${API}/elements/${elementId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ performance: newPerf, version }),
    })
    qc.invalidateQueries({ queryKey: ['elements', studyId] })
  }, [elementId, perf, version, qc, studyId])

  return (
    <div>
      <div style={{ fontSize: '0.65rem', fontWeight: 600, color: '#0ea5e9', textTransform: 'uppercase', marginBottom: '0.3rem' }}>
        Ground Station Configuration
      </div>

      {/* Current config */}
      {perf.location && (
        <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
          Location: {perf.location} ({perf.latitude?.toFixed(1)}°, {perf.longitude?.toFixed(1)}°)
          {perf.bands?.length > 0 && ` | Bands: ${perf.bands.join(', ')}`}
        </div>
      )}

      {/* Location picker */}
      <div style={{ marginBottom: '0.3rem' }}>
        <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: '0.15rem' }}>Location:</div>
        <div style={{ display: 'flex', gap: '0.2rem', flexWrap: 'wrap' }}>
          {GS_LOCATIONS.map(loc => (
            <button key={loc.name} onClick={() => setLocation(loc)}
              title={`${loc.provider} — ${loc.lat.toFixed(1)}°N, ${loc.lon.toFixed(1)}°E`}
              style={{
                padding: '0.1rem 0.35rem', fontSize: '0.58rem', borderRadius: '3px',
                background: perf.location === loc.name ? '#0ea5e9' : 'var(--bg-card)',
                color: perf.location === loc.name ? 'white' : 'var(--text-secondary)',
                border: '1px solid var(--border)', cursor: 'pointer',
              }}>
              {loc.name}
            </button>
          ))}
        </div>
      </div>

      {/* Frequency bands */}
      <div>
        <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: '0.15rem' }}>Frequency bands (click to toggle):</div>
        <div style={{ display: 'flex', gap: '0.2rem', flexWrap: 'wrap' }}>
          {FREQUENCY_BANDS.map(fb => {
            const active = (perf.bands || []).includes(fb.band)
            return (
              <button key={fb.band} onClick={() => setBand(fb.band)} title={`${fb.freq} — ${fb.use}`}
                style={{
                  padding: '0.1rem 0.35rem', fontSize: '0.58rem', borderRadius: '3px',
                  background: active ? '#ec4899' : 'var(--bg-card)',
                  color: active ? 'white' : 'var(--text-secondary)',
                  border: `1px solid ${active ? '#ec4899' : 'var(--border)'}`, cursor: 'pointer',
                }}>
                {fb.band}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
