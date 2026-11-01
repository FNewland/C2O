/**
 * DecisionPanel — Context-sensitive decision support tools.
 *
 * Shows different tools depending on what element is focused and what level:
 * - Level 0: Mission trade (space vs non-space), orbit trade, launch selection
 * - Level 1: Constellation sizing, ground station trade, system architecture trade
 * - Level 2: Subsystem architecture trade
 * - Level 3: Equipment trade (weighted scoring from KB)
 * - Any: Generic trade study builder
 */
import { useState, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n, { fmtProse } from '../i18n'
import { useUIStore } from '../stores/uiStore'
import { fs } from '../theme/tokens'
import { showAlert } from '../components/ui/Dialog'

const API = '/api'

// English text is the i18n key: default trade criteria, kept in English in state and
// localStorage; displayed with t(c, { context: 'criterion' }) (user-added names fall through).
const DEFAULT_CRITERIA = ['Mass', 'Power', 'Cost', 'TRL', 'Risk']

export function DecisionPanel() {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const currentLevel = useUIStore(s => s.currentLevel)

  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })

  const [pairwiseWeights, setPairwiseWeights] = useState<Record<string, number>>({})
  const [sharedCriteria, setSharedCriteria] = useState<string[]>(DEFAULT_CRITERIA)

  const focusElement = allElements.find((e: any) => e.id === focusElementId)
  const isSpaceSegment = focusElement?.segment === 'space'
  const isGroundSegment = focusElement?.segment === 'ground'

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: fs.label, overflow: 'auto', maxHeight: '100%' }}>
      <div style={{ fontWeight: 600, fontSize: fs.label, marginBottom: '0.5rem', color: 'var(--status-caution)' }}>
        {t('Decision Support — Level {{level}}', { level: currentLevel })}
      </div>

      {/* Decision categorization — always shown */}
      <DecisionCategorizer currentLevel={currentLevel} focusElement={focusElement} />

      {/* Architecture trades driven by requirements */}
      <ArchitectureTradeWidget currentLevel={currentLevel} focusElement={focusElement} />

      {/* Level 0: Mission-level decisions */}
      {currentLevel === 0 && <MissionTradeWidget studyId={studyId} />}
      {currentLevel === 0 && <OrbitTradeWidget studyId={studyId} />}

      {/* Level 1: System-level decisions */}
      {(currentLevel === 1 || isSpaceSegment) && <ConstellationWidget studyId={studyId} />}
      {currentLevel === 1 && isSpaceSegment && <CostLearningCurveWidget />}
      {(currentLevel === 1 || isGroundSegment) && <GroundTradeWidget studyId={studyId} />}
      {currentLevel >= 1 && <ContactScheduleWidget studyId={studyId} />}

      {/* Any level: Decision tools — weighting first, then scoring */}
      <PairwiseWeightingWidget onWeightsChanged={setPairwiseWeights} criteria={sharedCriteria} onCriteriaChanged={setSharedCriteria} />
      <PughMatrixWidget weights={pairwiseWeights} criteria={sharedCriteria} onCriteriaChanged={setSharedCriteria} />
    </div>
  )
}

// ─── Mission Trade: Space vs Non-Space ───

function MissionTradeWidget(_props: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [gsd, setGsd] = useState('5')
  const [revisit, setRevisit] = useState('1')
  const [budget, setBudget] = useState('2000')

  const runTrade = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/mission-trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_gsd_m: parseFloat(gsd) || 5,
          target_revisit_days: parseFloat(revisit) || 1,
          target_coverage: 'regional',
          target_latency_hours: 24,
          require_data_ownership: true,
          max_annual_budget_keur: parseFloat(budget) || 2000,
          mission_type: 'earth_observation',
          num_spacecraft: 1,
        }),
      })
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection title={t('Mission Trade: Space vs Alternatives')} color="var(--interactive)">
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
        <label style={labelStyle}>{t('GSD (m):')} <input type="number" value={gsd} onChange={e => setGsd(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>{t('Revisit (days):')} <input type="number" value={revisit} onChange={e => setRevisit(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>{t('Budget (kEUR/yr):')} <input type="number" value={budget} onChange={e => setBudget(e.target.value)} style={inputStyle} /></label>
      </div>
      <button onClick={runTrade} disabled={loading} style={btnStyle}>
        {loading ? t('Analysing...') : t('Evaluate Alternatives')}
      </button>
      {result?.alternatives && (
        <div style={{ marginTop: '0.4rem' }}>
          {result.question && (
            <div style={{ fontSize: fs.label, color: 'var(--accent)', fontWeight: 600, marginBottom: '0.3rem' }}>{result.question}</div>
          )}
          {result.alternatives.map((alt: any, i: number) => {
            const score = alt.score ?? (alt.rank ? (1 - (alt.rank - 1) * 0.15) : 0.5)
            return (
              <div key={i} style={{ ...rowStyle, borderLeft: `3px solid ${score > 0.7 ? 'var(--success)' : score > 0.4 ? 'var(--warning)' : 'var(--danger)'}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.15rem' }}>
                  <span style={{ fontWeight: 600 }}>{alt.name}</span>
                  <span style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>
                    {alt.category && <span style={{ marginRight: '0.3rem' }}>{alt.category}</span>}
                    #{alt.rank || i + 1}
                  </span>
                </div>
                <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{alt.description}</div>
                {alt.gsd_m && (
                  <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                    {t('GSD: {{gsd}}m | Revisit: {{revisit}}d | Cost: {{cost}} kEUR/yr', { gsd: alt.gsd_m, revisit: alt.revisit_days, cost: alt.annual_cost_keur })}
                  </div>
                )}
              </div>
            )
          })}
          {result.recommendation && (
            <div style={{ marginTop: '0.3rem', padding: '0.3rem', background: 'rgba(16,185,129,0.1)', borderRadius: '3px', fontSize: fs.label, color: 'var(--success)' }}>
              {result.recommendation}
            </div>
          )}
        </div>
      )}
    </ToolSection>
  )
}

// ─── Orbit Trade ───

function OrbitTradeWidget({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const qc = useQueryClient()

  const runTrade = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/orbit-trade/${studyId}`)
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection title={t('Orbit Trade Study')} color="var(--cat-2)">
      <button onClick={runTrade} disabled={loading} style={btnStyle}>
        {loading ? t('Computing...') : t('Evaluate Orbit Options')}
      </button>
      {result?.candidates && (
        <div style={{ marginTop: '0.4rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                <th style={thL}>{t('Orbit')}</th>
                <th style={thR}>{t('Alt', { context: 'column' })}</th>
                <th style={thR}>{t('Inc', { context: 'column' })}</th>
                <th style={thR}>GSD</th>
                <th style={thR}>{t('Revisit')}</th>
                <th style={thR}>{t('Lifetime')}</th>
                <th style={thR}>{t('Score')}</th>
                <th style={thC}>{t('Deorbit')}</th>
                <th style={thC}></th>
              </tr>
            </thead>
            <tbody>
              {result.candidates.map((c: any, i: number) => (
                <tr key={i} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)' }}>
                  <td style={{ padding: '0.2rem 0.3rem', fontWeight: 500 }}>{c.name || c.orbit_type}</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace' }}>{c.altitude_km}</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace' }}>{c.inclination_deg?.toFixed(1)}</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace', color: c.meets_gsd ? 'var(--success)' : 'var(--text-secondary)' }}>{c.achievable_gsd_m?.toFixed(1)}m</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace' }}>{c.revisit_days?.toFixed(0)}d</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace', fontSize: fs.label }}>{c.natural_lifetime_years?.toFixed(0)}yr</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace', color: 'var(--success)' }}>{((c.total_score || c.weighted_score || c.score || 0) * 100).toFixed(0)}%</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center' }}>
                    {c.compliant_25yr != null ? (
                      <span style={{ color: c.compliant_25yr ? 'var(--success)' : 'var(--danger)' }}>
                        {c.compliant_25yr ? '✓' : '✗'} {c.natural_lifetime_years != null ? `(${c.natural_lifetime_years}yr)` : ''}
                      </span>
                    ) : '—'}
                  </td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center' }}>
                    <button onClick={async () => {
                      // Apply this orbit to the focused spacecraft element
                      const fid = useUIStore.getState().focusElementId
                      const sid = useUIStore.getState().studyId
                      if (!fid || !sid) { void showAlert(i18n.t('Drill into a spacecraft element first')); return }
                      const els: any[] = qc.getQueryData(['elements', sid]) || []
                      const el = els.find((e: any) => e.id === fid)
                      if (!el) return
                      await fetch(`${API}/elements/${fid}`, {
                        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          performance: { ...((el as any).performance || {}), orbit_altitude_km: c.altitude_km, orbit_inclination_deg: c.inclination_deg, orbit_type: c.orbit_type },
                          version: el.version,
                        }),
                      })
                      qc.invalidateQueries({ queryKey: ['elements'] })
                      void showAlert(i18n.t('Applied: {{name}} ({{alt}}km, {{incl}}°)', { name: c.name, alt: c.altitude_km, incl: c.inclination_deg }))
                    }} style={{ ...btnStyle, fontSize: fs.label, padding: '0.1rem 0.3rem', background: 'var(--success)' }}>
                      {t('Apply')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </ToolSection>
  )
}

// ─── Constellation Sizing ───

function ConstellationWidget(_props: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const qc = useQueryClient()
  const [altitude, setAltitude] = useState('500')
  const [inclination, setInclination] = useState('97.4')
  const [revisitHours, setRevisitHours] = useState('24')

  const runDesign = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/constellation/design`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          altitude_km: parseFloat(altitude),
          inclination_deg: parseFloat(inclination),
          target_revisit_hours: parseFloat(revisitHours),
        }),
      })
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection title={t('Constellation Sizing')} color="var(--interactive)">
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
        <label style={labelStyle}>{t('Alt (km):')} <input type="number" value={altitude} onChange={e => setAltitude(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>{t('Inc (°):')} <input type="number" value={inclination} onChange={e => setInclination(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>{t('Revisit (h):')} <input type="number" value={revisitHours} onChange={e => setRevisitHours(e.target.value)} style={inputStyle} /></label>
      </div>
      <button onClick={runDesign} disabled={loading} style={btnStyle}>
        {loading ? t('Computing...') : t('Size Constellation')}
      </button>
      {result && (
        <div style={{ marginTop: '0.4rem', fontSize: fs.label }}>
          {(result.candidates || result.options || []).map((opt: any, i: number) => (
            <div key={i} style={rowStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600 }}>
                  {opt.walker_notation || t('{{planes}}P × {{sats}}S = {{total}} sats', { planes: opt.num_planes || opt.planes, sats: opt.sats_per_plane, total: opt.total_satellites || opt.total_sats })}
                </span>
                <span style={{ color: 'var(--accent)', fontFamily: 'monospace' }}>
                  {opt.total_cost_meur != null ? `${opt.total_cost_meur.toFixed(1)}M€` : ''}
                </span>
              </div>
              <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>
                {t('Revisit: {{max}}h max, {{mean}}h mean', { max: (opt.max_revisit_hours || opt.revisit_hours)?.toFixed(1), mean: (opt.mean_revisit_hours)?.toFixed(1) })}
                {opt.coverage_percent != null && t(' | Coverage: {{pct}}%', { pct: opt.coverage_percent.toFixed(0) })}
                {opt.total_mass_kg != null && t(' | Mass: {{mass}}kg', { mass: opt.total_mass_kg })}
                {opt.spares != null && t(' | Spares: {{n}}', { n: opt.spares })}
              </div>
              <button onClick={async () => {
                const fid = useUIStore.getState().focusElementId
                const sid = useUIStore.getState().studyId
                if (!fid || !sid) { void showAlert(i18n.t('Drill into a spacecraft element first')); return }
                const els: any[] = qc.getQueryData(['elements', sid]) || []
                const el = els.find((e: any) => e.id === fid)
                if (!el) return
                await fetch(`${API}/elements/${fid}`, {
                  method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    quantity: opt.total_satellites || opt.total_sats,
                    performance: { ...((el as any).performance || {}), constellation: true, orbital_planes: opt.num_planes || opt.planes, sats_per_plane: opt.sats_per_plane, walker_notation: opt.walker_notation },
                    version: el.version,
                  }),
                })
                qc.invalidateQueries({ queryKey: ['elements'] })
                void showAlert(i18n.t('Applied: {{what}}', { what: opt.walker_notation || i18n.t('{{n}} sats', { n: opt.total_satellites }) }))
              }} style={{ ...btnStyle, fontSize: fs.label, padding: '0.1rem 0.3rem', background: 'var(--success)', marginTop: '0.15rem' }}>
                {t('Apply to Design')}
              </button>
            </div>
          ))}
          {result.count != null && (
            <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              {t('{{count}} configurations evaluated', { count: result.count })}
            </div>
          )}
        </div>
      )}
    </ToolSection>
  )
}

// ─── Ground Segment Trade ───

function GroundTradeWidget({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const runTrade = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/ground/trade/${studyId}`)
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection title={t('Ground Segment Trade')} color="var(--status-ok)">
      <button onClick={runTrade} disabled={loading} style={btnStyle}>
        {loading ? t('Analysing...') : t('Evaluate Ground Architectures')}
      </button>
      {result?.alternatives && (
        <div style={{ marginTop: '0.4rem' }}>
          {result.alternatives.map((alt: any, i: number) => (
            <div key={i} style={rowStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600 }}>{alt.name}</span>
                <span style={{ fontFamily: 'monospace', color: 'var(--success)' }}>{((alt.score || 0) * 100).toFixed(0)}%</span>
              </div>
              <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>
                {alt.stations?.join(', ') || alt.description}
                {alt.contact_minutes_per_day && t(' | {{min}} min/day contact', { min: alt.contact_minutes_per_day.toFixed(0) })}
                {alt.annual_cost_keur && t(' | {{cost}} kEUR/yr', { cost: alt.annual_cost_keur })}
              </div>
            </div>
          ))}
          {result.recommendation && (
            <div style={{ marginTop: '0.3rem', padding: '0.3rem', background: 'rgba(16,185,129,0.1)', borderRadius: '3px', fontSize: fs.label, color: 'var(--success)' }}>
              {result.recommendation}
            </div>
          )}
        </div>
      )}
    </ToolSection>
  )
}

// ─── Contact Schedule ───

function ContactScheduleWidget({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const qc = useQueryClient()

  const runSchedule = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      // Read actual orbit and ground stations from the design
      const elements: any[] = qc.getQueryData(['elements', studyId]) || await fetch(`${API}/studies/${studyId}/elements`).then(r => r.json())

      // Find orbit params from spacecraft element performance or use defaults
      let altitude = 500, inclination = 97.4
      for (const el of elements) {
        const perf = el.performance || {}
        if (perf.orbit_altitude_km) { altitude = perf.orbit_altitude_km; inclination = perf.orbit_inclination_deg || inclination; break }
      }

      // Find ground stations from elements
      const gsElements = elements.filter((e: any) => e.segment === 'ground' && (e.performance || {}).latitude)
      const customStations = gsElements.map((e: any) => ({
        id: e.name.toLowerCase().replace(/\s+/g, '_'),
        name: e.name,
        lat: e.performance.latitude,
        lon: e.performance.longitude,
        antenna_m: e.performance.antenna_diameter_m || e.performance.antenna_m || 3.7,
        min_elevation_deg: e.performance.min_elevation_deg || 5,
        bands: e.performance.bands || ['S'],
      }))

      // Find number of spacecraft
      const spacecraft = elements.filter((e: any) => e.segment === 'space' && e.element_type === 'system')
      const totalSats = spacecraft.reduce((s: number, e: any) => s + (e.quantity || 1), 0)

      const body: any = { orbit: { altitude_km: altitude, inclination_deg: inclination } }
      if (customStations.length > 0) body.custom_stations = customStations

      const res = await fetch(`${API}/ground/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        const data = await res.json()
        data._design_context = { altitude, inclination, ground_stations: gsElements.length, spacecraft: totalSats }
        setResult(data)
      }
    } finally { setLoading(false) }
  }

  return (
    <ToolSection title={t('Ground Contact Schedule')} color="var(--interactive)">
      <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
        {t("Uses your design's orbit parameters and ground stations from the element tree.")}
      </div>
      <button onClick={runSchedule} disabled={loading} style={btnStyle}>
        {loading ? t('Computing...') : t('Predict Contact Windows')}
      </button>
      {result?._design_context && (
        <div style={{ fontSize: fs.label, color: 'var(--info)', marginTop: '0.2rem' }}>
          {t('Using: {{alt}}km, {{incl}}° inc, {{count}} ground stations, {{sc}} spacecraft', { alt: result._design_context.altitude, incl: result._design_context.inclination, count: result._design_context.ground_stations, sc: result._design_context.spacecraft, defaultValue_one: 'Using: {{alt}}km, {{incl}}° inc, {{count}} ground station, {{sc}} spacecraft' })}
        </div>
      )}
      {result && (
        <div style={{ marginTop: '0.4rem', fontSize: fs.label }}>
          {(result.coverage_stats || result.contacts) && (
            <div style={rowStyle}>
              <span>{t('Contacts:')} <b>{result.contacts?.length || result.coverage_stats?.total_passes_per_day || '?'}</b></span>
              {result.coverage_stats?.total_contact_minutes_per_day && (
                <span style={{ marginLeft: '0.5rem' }}>{t('Contact:')} <b>{t('{{min}} min/day', { min: result.coverage_stats.total_contact_minutes_per_day.toFixed(1) })}</b></span>
              )}
            </div>
          )}
          {(result.contacts || result.windows)?.slice(0, 8).map((w: any, i: number) => {
            const dur = w.duration_min ?? ((w.end_s - w.start_s) / 60)
            return (
              <div key={i} style={{ padding: '0.15rem 0.3rem', fontSize: fs.label, color: 'var(--text-secondary)', borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)' }}>
                <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{w.station || w.station_id}</span>
                {' '}{t('{{dur}} min | max el: {{el}}°', { dur: dur.toFixed(1), el: w.max_elevation_deg?.toFixed(0) })}
                {w.data_volume_mbit && ` | ${(w.data_volume_mbit / 1000).toFixed(1)} Gbit`}
              </div>
            )
          })}
        </div>
      )}
    </ToolSection>
  )
}

// ─── Pugh Matrix ───

function PughMatrixWidget({ weights, criteria, onCriteriaChanged }: { weights?: Record<string, number>; criteria: string[]; onCriteriaChanged: (c: string[]) => void }) {
  const { t } = useTranslation()
  const loadSaved = () => { try { const s = localStorage.getItem('spacecdf-pugh'); return s ? JSON.parse(s) : null } catch { return null } }
  const saved = loadSaved()
  const [options, setOptions] = useState<string[]>(saved?.options || [t('Option A'), t('Option B'), t('Option C')])
  const [datum, setDatum] = useState(saved?.datum || 0)
  const [scores, setScores] = useState<Record<string, Record<string, number>>>(saved?.scores || {})
  const [newCriterion, setNewCriterion] = useState('')
  const [newOption, setNewOption] = useState('')

  const saveState = useCallback(() => {
    const state = { criteria, options, datum, scores }
    localStorage.setItem('spacecdf-pugh', JSON.stringify(state))
  }, [criteria, options, datum, scores])
  useState(() => { saveState() })

  const setScore = (opt: string, crit: string, val: number) => {
    setScores(prev => ({ ...prev, [opt]: { ...(prev[opt] || {}), [crit]: val } }))
  }
  const getScore = (opt: string, crit: string) => scores[opt]?.[crit] ?? 0
  const hasWeights = weights && Object.keys(weights).length > 0

  // Compute weighted totals
  const totals = options.map((opt, i) => {
    if (i === datum) return { unweighted: 0, weighted: 0 }
    let unweighted = 0, weighted = 0
    for (const c of criteria) {
      const s = getScore(opt, c)
      unweighted += s
      const w = weights?.[c] ?? (1 / criteria.length)
      weighted += s * w
    }
    return { unweighted, weighted: Math.round(weighted * 100) / 100 }
  })

  const best = totals.reduce((bi, t, i) => (i !== datum && t.weighted > (totals[bi]?.weighted ?? -999) ? i : bi), datum === 0 ? 1 : 0)

  return (
    <ToolSection title={hasWeights ? t('Pugh Matrix (Weighted)') : t('Pugh Matrix (Unweighted)')} color="var(--cat-6)">
      <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
        {t('Score each option vs datum: +2 much better, +1 better, 0 same, −1 worse, −2 much worse.')}
        {' '}{hasWeights ? t('Weights from pairwise comparison applied.') : t('Define weights above for weighted scoring.')}
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label, marginBottom: '0.3rem' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            <th style={thL}>{t('Criteria')}</th>
            {hasWeights && <th style={thR}>{t('Wt')}</th>}
            {options.map((opt, i) => (
              <th key={opt} style={{ ...thC, background: i === datum ? 'rgba(59,130,246,0.1)' : i === best ? 'rgba(16,185,129,0.1)' : undefined, cursor: 'pointer' }}
                onClick={() => setDatum(i)} title={t('Click to set as datum')}>
                {opt} {i === datum ? '(D)' : i === best ? '★' : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {criteria.map(crit => (
            <tr key={crit} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)' }}>
              <td style={{ padding: '0.15rem 0.3rem', fontWeight: 500 }}>{t(crit, { context: 'criterion' })}</td>
              {hasWeights && <td style={{ padding: '0.15rem 0.3rem', textAlign: 'right', fontSize: fs.label, color: 'var(--accent)' }}>{((weights?.[crit] ?? 0) * 100).toFixed(0)}%</td>}
              {options.map((opt, i) => (
                <td key={opt} style={{ padding: '0.15rem', textAlign: 'center' }}>
                  {i === datum ? <span style={{ color: 'var(--text-secondary)' }}>D</span> : (
                    <select value={getScore(opt, crit)} onChange={e => setScore(opt, crit, parseInt(e.target.value))}
                      style={{ width: 40, fontSize: fs.label, padding: '0.1rem', borderRadius: '2px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: getScore(opt, crit) > 0 ? 'var(--success)' : getScore(opt, crit) < 0 ? 'var(--danger)' : 'var(--text-secondary)', textAlign: 'center' }}>
                      <option value={2}>+2</option><option value={1}>+1</option><option value={0}>0</option><option value={-1}>−1</option><option value={-2}>−2</option>
                    </select>
                  )}
                </td>
              ))}
            </tr>
          ))}
          <tr style={{ borderTop: '2px solid var(--border)' }}>
            <td style={{ padding: '0.2rem 0.3rem', fontWeight: 700 }}>{hasWeights ? t('Weighted Total') : t('Total')}</td>
            {hasWeights && <td />}
            {totals.map((tot, i) => (
              <td key={i} style={{ padding: '0.2rem', textAlign: 'center', fontWeight: 700, color: i === datum ? 'var(--text-secondary)' : i === best ? 'var(--success)' : tot.weighted > 0 ? 'var(--success)' : tot.weighted < 0 ? 'var(--danger)' : 'var(--text-primary)' }}>
                {i === datum ? '—' : hasWeights ? tot.weighted.toFixed(2) : tot.unweighted}
              </td>
            ))}
          </tr>
        </tbody>
      </table>

      <div style={{ display: 'flex', gap: '0.2rem', flexWrap: 'wrap' }}>
        <input value={newCriterion} onChange={e => setNewCriterion(e.target.value)} placeholder={t('+ criterion')} style={{ ...inputStyle, width: 80 }}
          onKeyDown={e => { if (e.key === 'Enter' && newCriterion) { onCriteriaChanged([...criteria, newCriterion]); setNewCriterion('') } }} />
        <input value={newOption} onChange={e => setNewOption(e.target.value)} placeholder={t('+ option')} style={{ ...inputStyle, width: 80 }}
          onKeyDown={e => { if (e.key === 'Enter' && newOption) { setOptions(p => [...p, newOption]); setNewOption('') } }} />
      </div>
    </ToolSection>
  )
}

// ─── Pairwise Comparison Weighting ───

function PairwiseWeightingWidget({ onWeightsChanged, criteria, onCriteriaChanged }: {
  onWeightsChanged?: (weights: Record<string, number>) => void
  criteria: string[]
  onCriteriaChanged: (c: string[]) => void
}) {
  const { t } = useTranslation()
  const [comparisons, setComparisons] = useState<Record<string, number>>({})
  const [newCrit, setNewCrit] = useState('')

  const pairKey = (a: string, b: string) => `${a}|${b}`

  const setComparison = (a: string, b: string, val: number) => {
    setComparisons(prev => ({ ...prev, [pairKey(a, b)]: val }))
  }

  // Derive weights from pairwise comparisons
  const weights = criteria.map(c => {
    let score = 0
    for (const other of criteria) {
      if (other === c) continue
      const val = comparisons[pairKey(c, other)]
      if (val != null) score += val
      else {
        const rev = comparisons[pairKey(other, c)]
        if (rev != null) score += (1 - rev)
      }
    }
    return { criterion: c, rawScore: score }
  })
  const totalRaw = weights.reduce((s, w) => s + Math.max(w.rawScore, 0), 0) || 1
  const normalizedWeights = weights.map(w => ({ ...w, weight: Math.max(w.rawScore, 0) / totalRaw }))

  // Notify parent of weight changes
  const weightMap = Object.fromEntries(normalizedWeights.map(w => [w.criterion, w.weight]))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useMemo(() => { onWeightsChanged?.(weightMap) }, [JSON.stringify(weightMap)])

  // Generate pairs
  const pairs: Array<[string, string]> = []
  for (let i = 0; i < criteria.length; i++) {
    for (let j = i + 1; j < criteria.length; j++) {
      pairs.push([criteria[i], criteria[j]])
    }
  }

  return (
    <ToolSection title={t('Pairwise Comparison Weighting')} color="var(--cat-2)">
      <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
        {t('For each pair: which criterion is more important? 1 = left wins, 0.5 = equal, 0 = right wins')}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginBottom: '0.4rem' }}>
        {pairs.map(([a, b]) => (
          <div key={`${a}-${b}`} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: fs.label }}>
            <span style={{ width: 60, textAlign: 'right', fontWeight: 500 }}>{t(a, { context: 'criterion' })}</span>
            <input type="range" min={0} max={1} step={0.5} value={comparisons[pairKey(a, b)] ?? 0.5}
              onChange={e => setComparison(a, b, parseFloat(e.target.value))}
              style={{ width: 80 }} />
            <span style={{ width: 60, fontWeight: 500 }}>{t(b, { context: 'criterion' })}</span>
            <span style={{ fontSize: fs.label, color: 'var(--text-secondary)', width: 20 }}>
              {(comparisons[pairKey(a, b)] ?? 0.5) === 1 ? '←' : (comparisons[pairKey(a, b)] ?? 0.5) === 0 ? '→' : '='}
            </span>
          </div>
        ))}
      </div>

      {/* Derived weights */}
      <div style={{ fontSize: fs.label, fontWeight: 600, marginBottom: '0.2rem', color: 'var(--text-secondary)' }}>{t('Derived Weights:')}</div>
      <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
        {normalizedWeights.sort((a, b) => b.weight - a.weight).map(w => (
          <div key={w.criterion} style={{ padding: '0.15rem 0.4rem', borderRadius: '3px', background: 'var(--bg-card)', fontSize: fs.label }}>
            <span style={{ fontWeight: 500 }}>{t(w.criterion, { context: 'criterion' })}</span>
            <span style={{ marginLeft: '0.3rem', color: 'var(--accent)', fontWeight: 600 }}>{(w.weight * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>

      <input value={newCrit} onChange={e => setNewCrit(e.target.value)} placeholder={t('+ criterion')}
        style={{ ...inputStyle, marginTop: '0.3rem', width: 100 }}
        onKeyDown={e => { if (e.key === 'Enter' && newCrit) { onCriteriaChanged([...criteria, newCrit]); setNewCrit('') } }} />
    </ToolSection>
  )
}

// ─── Constellation Cost Learning Curve ───

function CostLearningCurveWidget() {
  const { t } = useTranslation()
  const [unitCost, setUnitCost] = useState('500')
  const [quantity, setQuantity] = useState('12')
  const [learningRate, setLearningRate] = useState('0.90')

  // C_total = C_1 × Σ(i^log2(L))
  const c1 = parseFloat(unitCost) || 500
  const n = parseInt(quantity) || 12
  const lr = parseFloat(learningRate) || 0.90
  const b = Math.log2(lr)

  const units: Array<{ unit: number; cost: number; cumulative: number }> = []
  let cumulative = 0
  for (let i = 1; i <= n; i++) {
    const cost = c1 * Math.pow(i, b)
    cumulative += cost
    units.push({ unit: i, cost: Math.round(cost), cumulative: Math.round(cumulative) })
  }
  const avgCost = n > 0 ? Math.round(cumulative / n) : 0

  return (
    <ToolSection title={t('Constellation Cost Learning Curve')} color="var(--status-caution)">
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
        <label style={labelStyle}>{t('First unit (kEUR):')} <input type="number" value={unitCost} onChange={e => setUnitCost(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>{t('Quantity:')} <input type="number" value={quantity} onChange={e => setQuantity(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>{t('Learning rate:')} <input type="number" value={learningRate} onChange={e => setLearningRate(e.target.value)} step="0.01" min="0.7" max="1.0" style={inputStyle} /></label>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.3rem', fontSize: fs.label }}>
        <span>{t('Total:')} <b>{fmtProse(Math.round(cumulative))} kEUR</b></span>
        <span>{t('Average:')} <b>{t('{{cost}} kEUR/unit', { cost: fmtProse(avgCost) })}</b></span>
        <span>{t('Savings vs flat:')} <b>{Math.round((1 - cumulative / (c1 * n)) * 100)}%</b></span>
      </div>

      {/* Mini bar chart */}
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 1, height: 50, marginBottom: '0.2rem' }}>
        {units.map(u => (
          <div key={u.unit} style={{
            flex: 1, background: 'var(--accent)',
            height: `${(u.cost / c1) * 100}%`,
            borderRadius: '2px 2px 0 0', minWidth: 3,
          }} title={t('Unit {{n}}: {{cost}} kEUR', { n: u.unit, cost: u.cost })} />
        ))}
      </div>
      <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', textAlign: 'center' }}>
        {t('Unit cost decreases with production experience (Wright learning curve)')}
      </div>
    </ToolSection>
  )
}

// ─── Shared components ───

// ─── 3-Bin Decision Categorizer ───

type DecisionItems = Record<number, Array<{ item: string; category: 'obvious' | 'trade' | 'explore'; rationale: string }>>

// English text is the i18n key: item and rationale are translated at render time
// (split in two literals so each stays short enough for the i18n key scanner).
const DECISION_ITEMS_L01: DecisionItems = {
  0: [
    { item: 'Orbit type (SSO for EO)', category: 'obvious', rationale: 'SSO is standard for EO; other types for comms/science' },
    { item: 'Mission vs non-space alternative', category: 'trade', rationale: 'Commercial data may meet needs at lower cost — run mission trade' },
    { item: 'Constellation vs single sat', category: 'trade', rationale: 'Revisit requirement drives this — run constellation sizing' },
    { item: 'Ground station network', category: 'trade', rationale: 'Data volume and latency drive GS selection — run ground trade' },
    { item: 'Launch vehicle', category: 'trade', rationale: 'Mass, orbit, cost, schedule constraints — compare options' },
    { item: 'Regulatory regime', category: 'obvious', rationale: 'Driven by operator country and orbit — ISED/ITU for Canada' },
  ],
  1: [
    { item: 'Spacecraft bus architecture', category: 'obvious', rationale: 'Standard subsystem decomposition for CubeSats' },
    { item: 'Number of spacecraft', category: 'trade', rationale: 'Coverage, revisit, and cost trade-off' },
    { item: 'Ground station locations', category: 'trade', rationale: 'Contact time, data throughput, redundancy trade' },
    { item: 'Inter-satellite links', category: 'explore', rationale: 'Reduces ground dependency but adds mass/power/complexity' },
    { item: 'Operations concept (autonomous vs manual)', category: 'explore', rationale: 'Drives staffing, software, ground segment design' },
  ],
}

// English text is the i18n key (continued).
const DECISION_ITEMS_L234: DecisionItems = {
  2: [
    { item: 'AOCS architecture', category: 'trade', rationale: 'Pointing requirement drives 3-axis/spin/gravity-gradient — see arch trades' },
    { item: 'EPS topology (MPPT vs DET)', category: 'trade', rationale: 'Power regulation approach trades efficiency vs complexity' },
    { item: 'TTC frequency band', category: 'trade', rationale: 'UHF/S/X/Ka — data rate vs antenna size vs regulatory' },
    { item: 'Thermal control (passive vs active)', category: 'obvious', rationale: 'CubeSats use passive (coatings + heaters); active only for extreme thermal' },
    { item: 'Propulsion type', category: 'trade', rationale: 'Delta-V drives cold gas vs monoprop vs electric — run propulsion trade' },
    { item: 'Structure form factor', category: 'obvious', rationale: 'Driven by payload volume and mass constraints' },
  ],
  3: [
    { item: 'Component selection (COTS)', category: 'trade', rationale: 'Compare KB options by mass, power, cost, TRL — use equipment browser' },
    { item: 'Redundancy approach', category: 'trade', rationale: 'Cold/warm/hot redundancy trades reliability vs mass/cost' },
    { item: 'Custom hardware design', category: 'explore', rationale: 'When no COTS meets requirements — needs design space analysis' },
  ],
  4: [],
}

const DECISION_ITEMS_BY_LEVEL: DecisionItems = { ...DECISION_ITEMS_L01, ...DECISION_ITEMS_L234 }

const BIN_COLORS = { obvious: 'var(--status-ok)', trade: 'var(--status-caution)', explore: 'var(--cat-2)' }
// English text is the i18n key.
const BIN_LABELS = { obvious: 'Obvious Choice', trade: 'Trade Study', explore: 'Design Space' }
const BIN_ICONS = { obvious: '✓', trade: '⇄', explore: '?' }

function DecisionCategorizer({ currentLevel }: { currentLevel: number; focusElement: any }) {
  const { t } = useTranslation()
  const items = DECISION_ITEMS_BY_LEVEL[currentLevel] || []
  if (items.length === 0) return null

  const bins = { obvious: items.filter(i => i.category === 'obvious'), trade: items.filter(i => i.category === 'trade'), explore: items.filter(i => i.category === 'explore') }

  return (
    <ToolSection title={t('Decision Categorization')} color="var(--interactive)">
      <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
        {t("Categorize decisions at this level: what's obvious, what needs a trade, what needs exploration.")}
      </div>
      <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.2rem' }}>
        {(['obvious', 'trade', 'explore'] as const).map(bin => (
          <div key={bin} style={{ flex: 1, fontSize: fs.label, textAlign: 'center', padding: '0.15rem', borderRadius: '3px', background: `color-mix(in srgb, ${BIN_COLORS[bin]} 8%, transparent)`, color: BIN_COLORS[bin], fontWeight: 700 }}>
            {BIN_ICONS[bin]} {t(BIN_LABELS[bin])} ({bins[bin].length})
          </div>
        ))}
      </div>
      {items.map((item, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.15rem 0.3rem', fontSize: fs.label, borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)' }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: BIN_COLORS[item.category], flexShrink: 0 }} />
          <span style={{ fontWeight: 500, flex: 1 }}>{t(item.item)}</span>
          <span style={{ color: 'var(--text-secondary)', fontSize: fs.label, maxWidth: 200 }}>{t(item.rationale)}</span>
        </div>
      ))}
    </ToolSection>
  )
}

// ─── Architecture Trade Templates ───

type ArchTrades = Record<string, Array<{ name: string; driver: string; options: Array<{ name: string; when: string }> }>>

// English text is the i18n key: name/driver/option name/when are translated at render time.
const ARCH_TRADES_AOCS_EPS: ArchTrades = {
  aocs: [
    { name: 'AOCS Architecture', driver: 'Pointing accuracy requirement',
      options: [
        { name: '3-axis stabilized (reaction wheels + star tracker)', when: 'Pointing < 0.1° — EO, science, comms' },
        { name: 'Spin-stabilized', when: 'Pointing 1-5° — simple missions, low cost' },
        { name: 'Gravity gradient + magnetorquer', when: 'Pointing 5-10° — IoT, AIS, tech demo' },
        { name: 'Momentum bias (1 wheel + magnetorquers)', when: 'Pointing 0.5-2° — moderate cost, good reliability' },
      ],
    },
  ],
  power: [
    { name: 'EPS Architecture', driver: 'Power demand and eclipse duration',
      options: [
        { name: 'Body-mounted cells + Li-ion battery', when: '< 15W average — simple CubeSats' },
        { name: 'Deployable panels + Li-ion', when: '15-80W — most 3U-6U missions' },
        { name: 'Dual-deploy + high-capacity battery', when: '> 80W — 12U+ or high-power payloads' },
        { name: 'RTG (radioisotope)', when: 'Deep space, no solar — lunar night, outer planets' },
      ],
    },
  ],
}

// English text is the i18n key: name/driver/option name/when are translated at render time.
const ARCH_TRADES_TTC_PROP: ArchTrades = {
  ttc: [
    { name: 'TTC Architecture', driver: 'Data rate and ground station infrastructure',
      options: [
        { name: 'UHF simplex (400 MHz)', when: '< 9.6 kbps — beacon, IoT, AIS' },
        { name: 'UHF/VHF duplex', when: '< 100 kbps — command + low-rate telemetry' },
        { name: 'S-band', when: '100 kbps - 2 Mbps — standard TT&C' },
        { name: 'X-band downlink + S-band TT&C', when: '2-100 Mbps — EO payload data' },
        { name: 'Ka-band', when: '> 100 Mbps — high-throughput, weather-dependent' },
      ],
    },
  ],
  propulsion: [
    { name: 'Propulsion Architecture', driver: 'Total delta-V requirement',
      options: [
        { name: 'No propulsion (drag deorbit)', when: 'ΔV = 0, altitude < 600 km — natural decay' },
        { name: 'Cold gas', when: 'ΔV < 10 m/s — attitude control, small maneuvers' },
        { name: 'Green monopropellant', when: 'ΔV 10-200 m/s — orbit maintenance, deorbit' },
        { name: 'Hall-effect electric', when: 'ΔV 100-2000 m/s, time available — orbit raising, station-keeping' },
        { name: 'Bipropellant', when: 'ΔV > 500 m/s, time-critical — lunar transfer, fast maneuvers' },
      ],
    },
  ],
}

// English text is the i18n key: name/driver/option name/when are translated at render time.
const ARCH_TRADES_THERMAL: ArchTrades = {
  thermal: [
    { name: 'Thermal Architecture', driver: 'Internal dissipation and orbit environment',
      options: [
        { name: 'Passive (surface coatings + MLI)', when: '< 20W dissipation — most CubeSats' },
        { name: 'Passive + heaters', when: 'Cold case concern — eclipse survival, battery protection' },
        { name: 'Active (heat pipes + radiator)', when: '> 50W or tight temp control — large payloads' },
        { name: 'Louvers', when: 'Variable dissipation — mode-dependent thermal load' },
      ],
    },
  ],
}

const ARCH_TRADES: ArchTrades = { ...ARCH_TRADES_AOCS_EPS, ...ARCH_TRADES_TTC_PROP, ...ARCH_TRADES_THERMAL }

function ArchitectureTradeWidget({ currentLevel, focusElement }: { currentLevel: number; focusElement: any }) {
  const { t } = useTranslation()
  const domain = focusElement?.subsystem_domain
  const trades = domain ? (ARCH_TRADES[domain] || []) : (currentLevel === 2 ? Object.values(ARCH_TRADES).flat() : [])
  if (trades.length === 0) return null

  return (
    <ToolSection title={t('Architecture Trades')} color="var(--cat-6)">
      <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
        {t('Which architecture is right? The driving requirement determines the answer.')}
      </div>
      {trades.map((trade, i) => (
        <div key={i} style={{ marginBottom: '0.4rem' }}>
          <div style={{ fontWeight: 600, fontSize: fs.label, marginBottom: '0.1rem' }}>{t(trade.name)}</div>
          <div style={{ fontSize: fs.label, color: 'var(--warning)', marginBottom: '0.2rem' }}>{t('Driver: {{driver}}', { driver: t(trade.driver) })}</div>
          {trade.options.map((opt, j) => (
            <div key={j} style={{ display: 'flex', gap: '0.3rem', padding: '0.1rem 0.3rem', fontSize: fs.label, borderLeft: '2px solid var(--border)', marginLeft: '0.3rem', marginBottom: '0.1rem' }}>
              <span style={{ fontWeight: 500, minWidth: 120 }}>{t(opt.name)}</span>
              <span style={{ color: 'var(--text-secondary)' }}>→ {t(opt.when)}</span>
            </div>
          ))}
        </div>
      ))}
    </ToolSection>
  )
}

// ─── Shared components ───

function ToolSection({ title, color, children }: { title: string; color: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ marginBottom: '0.5rem', borderLeft: `3px solid ${color}`, paddingLeft: '0.5rem' }}>
      <button onClick={() => setOpen(!open)} style={{
        background: 'none', border: 'none', cursor: 'pointer', fontSize: fs.label,
        fontWeight: 600, color, padding: 0, marginBottom: '0.2rem',
      }}>
        {open ? '▾' : '▸'} {title}
      </button>
      {open && <div style={{ paddingTop: '0.2rem' }}>{children}</div>}
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  padding: '0.3rem 0.6rem', fontSize: fs.label, fontWeight: 600, borderRadius: '4px',
  background: 'var(--accent)', color: 'white', border: 'none', cursor: 'pointer',
}
const rowStyle: React.CSSProperties = {
  padding: '0.25rem 0.3rem', borderRadius: '3px', background: 'var(--bg-card)',
  marginBottom: '0.2rem', fontSize: fs.label,
}
const inputStyle: React.CSSProperties = {
  width: 60, padding: '0.15rem 0.3rem', fontSize: fs.label, borderRadius: '3px',
  background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
  marginLeft: '0.2rem',
}
const labelStyle: React.CSSProperties = { fontSize: fs.label, color: 'var(--text-secondary)' }
const thL: React.CSSProperties = { textAlign: 'left', padding: '0.2rem 0.3rem', color: 'var(--text-secondary)', fontWeight: 500, fontSize: fs.label }
const thR: React.CSSProperties = { ...thL, textAlign: 'right' }
const thC: React.CSSProperties = { ...thL, textAlign: 'center' }
