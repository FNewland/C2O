/**
 * DesignTools — Context-sensitive design support tools.
 *
 * Shows different tools based on what element is focused:
 * - Constellation element (quantity > 1, space): orbit selector, Walker config
 * - Ground station element: location picker, frequency bands, elevation
 * - Any element with domain: relevant engineering parameters
 */
import { useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { fs } from '../theme/tokens'

const API = '/api'

const ORBIT_PRESETS = [
  { name: 'LEO SSO', altitude: 500, inclination: 97.4 },
  { name: 'LEO Equatorial', altitude: 400, inclination: 0 },
  { name: 'LEO Polar', altitude: 600, inclination: 90 },
  { name: 'MEO', altitude: 2000, inclination: 55 },
  { name: 'ISS', altitude: 410, inclination: 51.6 },
]

// English text is the i18n key: preset label and tooltip by preset name (display only).
const ORBIT_PRESET_TEXT: Record<string, { label: string; desc: string }> = {
  'LEO SSO': { label: 'LEO SSO', desc: 'Sun-synchronous, dawn-dusk LTAN' },
  'LEO Equatorial': { label: 'LEO Equatorial', desc: 'Equatorial low Earth orbit' },
  'LEO Polar': { label: 'LEO Polar', desc: 'Polar orbit, global coverage' },
  'MEO': { label: 'MEO', desc: 'Medium Earth orbit (GNSS-like)' },
  'ISS': { label: 'ISS', desc: 'ISS altitude and inclination' },
}

const FREQUENCY_BANDS = [
  { band: 'UHF', freq: '400 MHz' },
  { band: 'S-band', freq: '2.0-2.3 GHz' },
  { band: 'X-band', freq: '8.0-8.4 GHz' },
  { band: 'Ka-band', freq: '26-40 GHz' },
  { band: 'L-band', freq: '1.2-1.5 GHz' },
]

// English text is the i18n key: typical use per band (tooltip).
const FREQUENCY_BAND_USE: Record<string, string> = {
  'UHF': 'CubeSat TT&C, low data rate',
  'S-band': 'Standard TT&C, medium data rate',
  'X-band': 'High data rate downlink, Earth observation',
  'Ka-band': 'Very high data rate, weather-sensitive',
  'L-band': 'Navigation, AIS, low-rate data',
}

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
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)

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
    <div className="mt-2 bt pt-2">
      {/* Show what element we're configuring */}
      <div className="t-12 c-2 mb-1">
        {t('Configuring:')} <b className="c-1">{focusElement.name}</b>
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
  const { t } = useTranslation()
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
      <div className="t-12 w-600 c-accent caps mb-1">
        {t('Orbit & Constellation')}
      </div>

      {/* Current orbit */}
      {perf.orbit_altitude_km && (
        <div className="t-12 c-2 mb-1">
          {t('Current: {{alt}} km, {{incl}}° incl', { alt: perf.orbit_altitude_km, incl: perf.orbit_inclination_deg })}
          {quantity > 1 && t(' | {{planes}} planes × {{sats}} sats = {{total}}', { planes: perf.orbital_planes || '?', sats: perf.sats_per_plane || '?', total: quantity })}
        </div>
      )}

      {/* Orbit presets */}
      <div className="flex gap-1 wrap mb-1">
        {ORBIT_PRESETS.map(o => (
          <button key={o.name} onClick={() => setOrbit(o.altitude, o.inclination)} title={t(ORBIT_PRESET_TEXT[o.name].desc)}
            className="py-1 px-2 t-12 rounded bg-2 bd c-1 cursor-p">
            {t(ORBIT_PRESET_TEXT[o.name].label)} ({o.altitude}km)
          </button>
        ))}
      </div>

      {/* Walker constellation config */}
      {quantity > 1 && (
        <div className="flex gap-1 ai-c t-12">
          <span className="c-2">{t('Walker:')}</span>
          {[[1, 4], [2, 4], [3, 4], [4, 6], [6, 6]].map(([p, s]) => (
            <button key={`${p}x${s}`} onClick={() => setWalker(p, s)}
              style={{
                padding: '0.1rem 0.3rem', fontSize: fs.label, borderRadius: '2px',
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
  const { t } = useTranslation()
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
      <div className="t-12 w-600 c-accent caps mb-1">
        {t('Ground Station Configuration')}
      </div>

      {/* Current config */}
      {perf.location && (
        <div className="t-12 c-2 mb-1">
          {t('Location: {{name}} ({{lat}}°, {{lon}}°)', { name: perf.location, lat: perf.latitude?.toFixed(1), lon: perf.longitude?.toFixed(1) })}
          {perf.bands?.length > 0 && t(' | Bands: {{bands}}', { bands: perf.bands.join(', ') })}
        </div>
      )}

      {/* Location picker */}
      <div className="mb-1">
        <div className="t-12 c-2 mb-1">{t('Location:')}</div>
        <div className="flex gap-1 wrap">
          {GS_LOCATIONS.map(loc => (
            <button key={loc.name} onClick={() => setLocation(loc)}
              title={`${loc.provider} — ${loc.lat.toFixed(1)}°N, ${loc.lon.toFixed(1)}°E`}
              style={{
                padding: '0.1rem 0.35rem', fontSize: fs.label, borderRadius: '3px',
                background: perf.location === loc.name ? 'var(--interactive)' : 'var(--bg-card)',
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
        <div className="t-12 c-2 mb-1">{t('Frequency bands (click to toggle):')}</div>
        <div className="flex gap-1 wrap">
          {FREQUENCY_BANDS.map(fb => {
            const active = (perf.bands || []).includes(fb.band)
            return (
              <button key={fb.band} onClick={() => setBand(fb.band)} title={`${fb.freq} — ${t(FREQUENCY_BAND_USE[fb.band])}`}
                style={{
                  padding: '0.1rem 0.35rem', fontSize: fs.label, borderRadius: '3px',
                  background: active ? 'var(--cat-6)' : 'var(--bg-card)',
                  color: active ? 'white' : 'var(--text-secondary)',
                  border: `1px solid ${active ? 'var(--cat-6)' : 'var(--border)'}`, cursor: 'pointer',
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
