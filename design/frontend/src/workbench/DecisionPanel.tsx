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
import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'

const API = '/api'

export function DecisionPanel() {
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const currentLevel = useUIStore(s => s.currentLevel)

  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId,
  })

  const focusElement = allElements.find((e: any) => e.id === focusElementId)
  const isSpaceSegment = focusElement?.segment === 'space'
  const isGroundSegment = focusElement?.segment === 'ground'

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: '0.75rem', overflow: 'auto', maxHeight: '100%' }}>
      <div style={{ fontWeight: 600, fontSize: '0.78rem', marginBottom: '0.5rem', color: '#f59e0b' }}>
        Decision Support — Level {currentLevel}
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
      <PairwiseWeightingWidget />
      <PughMatrixWidget />
    </div>
  )
}

// ─── Mission Trade: Space vs Non-Space ───

function MissionTradeWidget({ studyId }: { studyId: string | null }) {
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
    <ToolSection title="Mission Trade: Space vs Alternatives" color="#3b82f6">
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
        <label style={labelStyle}>GSD (m): <input type="number" value={gsd} onChange={e => setGsd(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>Revisit (days): <input type="number" value={revisit} onChange={e => setRevisit(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>Budget (kEUR/yr): <input type="number" value={budget} onChange={e => setBudget(e.target.value)} style={inputStyle} /></label>
      </div>
      <button onClick={runTrade} disabled={loading} style={btnStyle}>
        {loading ? 'Analysing...' : 'Evaluate Alternatives'}
      </button>
      {result?.alternatives && (
        <div style={{ marginTop: '0.4rem' }}>
          {result.question && (
            <div style={{ fontSize: '0.65rem', color: 'var(--accent)', fontWeight: 600, marginBottom: '0.3rem' }}>{result.question}</div>
          )}
          {result.alternatives.map((alt: any, i: number) => {
            const score = alt.score ?? (alt.rank ? (1 - (alt.rank - 1) * 0.15) : 0.5)
            return (
              <div key={i} style={{ ...rowStyle, borderLeft: `3px solid ${score > 0.7 ? 'var(--success)' : score > 0.4 ? 'var(--warning)' : 'var(--danger)'}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.15rem' }}>
                  <span style={{ fontWeight: 600 }}>{alt.name}</span>
                  <span style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>
                    {alt.category && <span style={{ marginRight: '0.3rem' }}>{alt.category}</span>}
                    #{alt.rank || i + 1}
                  </span>
                </div>
                <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>{alt.description}</div>
                {alt.gsd_m && (
                  <div style={{ fontSize: '0.55rem', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                    GSD: {alt.gsd_m}m | Revisit: {alt.revisit_days}d | Cost: {alt.annual_cost_keur} kEUR/yr
                  </div>
                )}
              </div>
            )
          })}
          {result.recommendation && (
            <div style={{ marginTop: '0.3rem', padding: '0.3rem', background: 'rgba(16,185,129,0.1)', borderRadius: '3px', fontSize: '0.68rem', color: 'var(--success)' }}>
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
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const runTrade = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/orbit-trade/${studyId}`)
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection title="Orbit Trade Study" color="#8b5cf6">
      <button onClick={runTrade} disabled={loading} style={btnStyle}>
        {loading ? 'Computing...' : 'Evaluate Orbit Options'}
      </button>
      {result?.candidates && (
        <div style={{ marginTop: '0.4rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.65rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                <th style={thL}>Orbit</th>
                <th style={thR}>Alt</th>
                <th style={thR}>Inc</th>
                <th style={thR}>GSD</th>
                <th style={thR}>Revisit</th>
                <th style={thR}>Lifetime</th>
                <th style={thR}>Score</th>
                <th style={thC}>Deorbit</th>
              </tr>
            </thead>
            <tbody>
              {result.candidates.map((c: any, i: number) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '0.2rem 0.3rem', fontWeight: 500 }}>{c.name || c.orbit_type}</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace' }}>{c.altitude_km}</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace' }}>{c.inclination_deg?.toFixed(1)}</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace', color: c.meets_gsd ? 'var(--success)' : 'var(--text-secondary)' }}>{c.achievable_gsd_m?.toFixed(1)}m</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace' }}>{c.revisit_days?.toFixed(0)}d</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace', fontSize: '0.6rem' }}>{c.natural_lifetime_years?.toFixed(0)}yr</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace', color: 'var(--success)' }}>{((c.total_score || c.weighted_score || c.score || 0) * 100).toFixed(0)}%</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'center' }}>
                    {c.compliant_25yr != null ? (
                      <span style={{ color: c.compliant_25yr ? 'var(--success)' : 'var(--danger)' }}>
                        {c.compliant_25yr ? '✓' : '✗'} {c.natural_lifetime_years != null ? `(${c.natural_lifetime_years}yr)` : ''}
                      </span>
                    ) : '—'}
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

function ConstellationWidget({ studyId }: { studyId: string | null }) {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
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
    <ToolSection title="Constellation Sizing" color="#06b6d4">
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
        <label style={labelStyle}>Alt (km): <input type="number" value={altitude} onChange={e => setAltitude(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>Inc (°): <input type="number" value={inclination} onChange={e => setInclination(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>Revisit (h): <input type="number" value={revisitHours} onChange={e => setRevisitHours(e.target.value)} style={inputStyle} /></label>
      </div>
      <button onClick={runDesign} disabled={loading} style={btnStyle}>
        {loading ? 'Computing...' : 'Size Constellation'}
      </button>
      {result && (
        <div style={{ marginTop: '0.4rem', fontSize: '0.68rem' }}>
          {(result.candidates || result.options || []).map((opt: any, i: number) => (
            <div key={i} style={rowStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600 }}>
                  {opt.walker_notation || `${opt.num_planes || opt.planes}P × ${opt.sats_per_plane}S = ${opt.total_satellites || opt.total_sats} sats`}
                </span>
                <span style={{ color: 'var(--accent)', fontFamily: 'monospace' }}>
                  {opt.total_cost_meur != null ? `${opt.total_cost_meur.toFixed(1)}M€` : ''}
                </span>
              </div>
              <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>
                Revisit: {(opt.max_revisit_hours || opt.revisit_hours)?.toFixed(1)}h max, {(opt.mean_revisit_hours)?.toFixed(1)}h mean
                {opt.coverage_percent != null && ` | Coverage: ${opt.coverage_percent.toFixed(0)}%`}
                {opt.total_mass_kg != null && ` | Mass: ${opt.total_mass_kg}kg`}
                {opt.spares != null && ` | Spares: ${opt.spares}`}
              </div>
            </div>
          ))}
          {result.count != null && (
            <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              {result.count} configurations evaluated
            </div>
          )}
        </div>
      )}
    </ToolSection>
  )
}

// ─── Ground Segment Trade ───

function GroundTradeWidget({ studyId }: { studyId: string | null }) {
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
    <ToolSection title="Ground Segment Trade" color="#10b981">
      <button onClick={runTrade} disabled={loading} style={btnStyle}>
        {loading ? 'Analysing...' : 'Evaluate Ground Architectures'}
      </button>
      {result?.alternatives && (
        <div style={{ marginTop: '0.4rem' }}>
          {result.alternatives.map((alt: any, i: number) => (
            <div key={i} style={rowStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600 }}>{alt.name}</span>
                <span style={{ fontFamily: 'monospace', color: 'var(--success)' }}>{((alt.score || 0) * 100).toFixed(0)}%</span>
              </div>
              <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>
                {alt.stations?.join(', ') || alt.description}
                {alt.contact_minutes_per_day && ` | ${alt.contact_minutes_per_day.toFixed(0)} min/day contact`}
                {alt.annual_cost_keur && ` | ${alt.annual_cost_keur} kEUR/yr`}
              </div>
            </div>
          ))}
          {result.recommendation && (
            <div style={{ marginTop: '0.3rem', padding: '0.3rem', background: 'rgba(16,185,129,0.1)', borderRadius: '3px', fontSize: '0.68rem', color: 'var(--success)' }}>
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
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const runSchedule = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/ground/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ orbit: { altitude_km: 500, inclination_deg: 97.4 } }),
      })
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection title="Ground Contact Schedule" color="#0ea5e9">
      <button onClick={runSchedule} disabled={loading} style={btnStyle}>
        {loading ? 'Computing...' : 'Predict Contact Windows'}
      </button>
      {result && (
        <div style={{ marginTop: '0.4rem', fontSize: '0.68rem' }}>
          {(result.coverage_stats || result.contacts) && (
            <div style={rowStyle}>
              <span>Contacts: <b>{result.contacts?.length || result.coverage_stats?.total_passes_per_day || '?'}</b></span>
              {result.coverage_stats?.total_contact_minutes_per_day && (
                <span style={{ marginLeft: '0.5rem' }}>Contact: <b>{result.coverage_stats.total_contact_minutes_per_day.toFixed(1)} min/day</b></span>
              )}
            </div>
          )}
          {(result.contacts || result.windows)?.slice(0, 8).map((w: any, i: number) => {
            const dur = w.duration_min ?? ((w.end_s - w.start_s) / 60)
            return (
              <div key={i} style={{ padding: '0.15rem 0.3rem', fontSize: '0.6rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{w.station || w.station_id}</span>
                {' '}{dur.toFixed(1)} min | max el: {w.max_elevation_deg?.toFixed(0)}°
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

function PughMatrixWidget() {
  // Persist Pugh matrix state in localStorage
  const loadSaved = () => {
    try { const s = localStorage.getItem('spacecdf-pugh'); return s ? JSON.parse(s) : null } catch { return null }
  }
  const saved = loadSaved()
  const [criteria, setCriteria] = useState<string[]>(saved?.criteria || ['Mass', 'Power', 'Cost', 'TRL', 'Risk'])
  const [options, setOptions] = useState<string[]>(saved?.options || ['Option A', 'Option B', 'Option C'])
  const [datum, setDatum] = useState(saved?.datum || 0)
  const [scores, setScores] = useState<Record<string, Record<string, number>>>(saved?.scores || {})
  const [newCriterion, setNewCriterion] = useState('')
  const [newOption, setNewOption] = useState('')

  // Auto-save on change
  const saveState = useCallback(() => {
    localStorage.setItem('spacecdf-pugh', JSON.stringify({ criteria, options, datum, scores }))
  }, [criteria, options, datum, scores])
  useState(() => { saveState() })

  const setScore = (opt: string, crit: string, val: number) => {
    setScores(prev => ({ ...prev, [opt]: { ...(prev[opt] || {}), [crit]: val } }))
  }

  const getScore = (opt: string, crit: string) => scores[opt]?.[crit] ?? 0

  // Compute totals
  const totals = options.map((opt, i) => {
    if (i === datum) return { plus: 0, minus: 0, net: 0 }
    const vals = criteria.map(c => getScore(opt, c))
    return { plus: vals.filter(v => v > 0).reduce((s, v) => s + v, 0), minus: vals.filter(v => v < 0).reduce((s, v) => s + v, 0), net: vals.reduce((s, v) => s + v, 0) }
  })

  return (
    <ToolSection title="Pugh Matrix (Relative Scoring)" color="#ec4899">
      <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
        Score each option relative to the datum: +2 much better, +1 better, 0 same, −1 worse, −2 much worse
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.65rem', marginBottom: '0.3rem' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            <th style={thL}>Criteria</th>
            {options.map((opt, i) => (
              <th key={opt} style={{ ...thC, background: i === datum ? 'rgba(59,130,246,0.1)' : undefined, cursor: 'pointer' }}
                onClick={() => setDatum(i)} title="Click to set as datum">
                {opt} {i === datum && '(D)'}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {criteria.map(crit => (
            <tr key={crit} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
              <td style={{ padding: '0.15rem 0.3rem', fontWeight: 500 }}>{crit}</td>
              {options.map((opt, i) => (
                <td key={opt} style={{ padding: '0.15rem', textAlign: 'center' }}>
                  {i === datum ? (
                    <span style={{ color: 'var(--text-secondary)' }}>DATUM</span>
                  ) : (
                    <select value={getScore(opt, crit)} onChange={e => setScore(opt, crit, parseInt(e.target.value))}
                      style={{ width: 45, fontSize: '0.6rem', padding: '0.1rem', borderRadius: '2px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: getScore(opt, crit) > 0 ? 'var(--success)' : getScore(opt, crit) < 0 ? 'var(--danger)' : 'var(--text-secondary)', textAlign: 'center' }}>
                      <option value={2}>+2</option><option value={1}>+1</option><option value={0}>0</option><option value={-1}>−1</option><option value={-2}>−2</option>
                    </select>
                  )}
                </td>
              ))}
            </tr>
          ))}
          <tr style={{ borderTop: '2px solid var(--border)' }}>
            <td style={{ padding: '0.2rem 0.3rem', fontWeight: 700 }}>Totals</td>
            {totals.map((t, i) => (
              <td key={i} style={{ padding: '0.2rem', textAlign: 'center', fontWeight: 600, color: i === datum ? 'var(--text-secondary)' : t.net > 0 ? 'var(--success)' : t.net < 0 ? 'var(--danger)' : 'var(--text-primary)' }}>
                {i === datum ? '—' : `+${t.plus} / ${t.minus} = ${t.net}`}
              </td>
            ))}
          </tr>
        </tbody>
      </table>

      <div style={{ display: 'flex', gap: '0.2rem', flexWrap: 'wrap' }}>
        <input value={newCriterion} onChange={e => setNewCriterion(e.target.value)} placeholder="+ criterion" style={{ ...inputStyle, width: 80 }}
          onKeyDown={e => { if (e.key === 'Enter' && newCriterion) { setCriteria(p => [...p, newCriterion]); setNewCriterion('') } }} />
        <input value={newOption} onChange={e => setNewOption(e.target.value)} placeholder="+ option" style={{ ...inputStyle, width: 80 }}
          onKeyDown={e => { if (e.key === 'Enter' && newOption) { setOptions(p => [...p, newOption]); setNewOption('') } }} />
      </div>
    </ToolSection>
  )
}

// ─── Pairwise Comparison Weighting ───

function PairwiseWeightingWidget() {
  const [criteria, setCriteria] = useState<string[]>(['Mass', 'Power', 'Cost', 'TRL'])
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

  // Generate pairs
  const pairs: Array<[string, string]> = []
  for (let i = 0; i < criteria.length; i++) {
    for (let j = i + 1; j < criteria.length; j++) {
      pairs.push([criteria[i], criteria[j]])
    }
  }

  return (
    <ToolSection title="Pairwise Comparison Weighting" color="#8b5cf6">
      <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
        For each pair: which criterion is more important? 1 = left wins, 0.5 = equal, 0 = right wins
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginBottom: '0.4rem' }}>
        {pairs.map(([a, b]) => (
          <div key={`${a}-${b}`} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.65rem' }}>
            <span style={{ width: 60, textAlign: 'right', fontWeight: 500 }}>{a}</span>
            <input type="range" min={0} max={1} step={0.5} value={comparisons[pairKey(a, b)] ?? 0.5}
              onChange={e => setComparison(a, b, parseFloat(e.target.value))}
              style={{ width: 80 }} />
            <span style={{ width: 60, fontWeight: 500 }}>{b}</span>
            <span style={{ fontSize: '0.55rem', color: 'var(--text-secondary)', width: 20 }}>
              {(comparisons[pairKey(a, b)] ?? 0.5) === 1 ? '←' : (comparisons[pairKey(a, b)] ?? 0.5) === 0 ? '→' : '='}
            </span>
          </div>
        ))}
      </div>

      {/* Derived weights */}
      <div style={{ fontSize: '0.65rem', fontWeight: 600, marginBottom: '0.2rem', color: 'var(--text-secondary)' }}>Derived Weights:</div>
      <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
        {normalizedWeights.sort((a, b) => b.weight - a.weight).map(w => (
          <div key={w.criterion} style={{ padding: '0.15rem 0.4rem', borderRadius: '3px', background: 'var(--bg-card)', fontSize: '0.65rem' }}>
            <span style={{ fontWeight: 500 }}>{w.criterion}</span>
            <span style={{ marginLeft: '0.3rem', color: 'var(--accent)', fontWeight: 600 }}>{(w.weight * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>

      <input value={newCrit} onChange={e => setNewCrit(e.target.value)} placeholder="+ criterion"
        style={{ ...inputStyle, marginTop: '0.3rem', width: 100 }}
        onKeyDown={e => { if (e.key === 'Enter' && newCrit) { setCriteria(p => [...p, newCrit]); setNewCrit('') } }} />
    </ToolSection>
  )
}

// ─── Constellation Cost Learning Curve ───

function CostLearningCurveWidget() {
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
    <ToolSection title="Constellation Cost Learning Curve" color="#f59e0b">
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
        <label style={labelStyle}>First unit (kEUR): <input type="number" value={unitCost} onChange={e => setUnitCost(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>Quantity: <input type="number" value={quantity} onChange={e => setQuantity(e.target.value)} style={inputStyle} /></label>
        <label style={labelStyle}>Learning rate: <input type="number" value={learningRate} onChange={e => setLearningRate(e.target.value)} step="0.01" min="0.7" max="1.0" style={inputStyle} /></label>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.3rem', fontSize: '0.68rem' }}>
        <span>Total: <b>{Math.round(cumulative).toLocaleString()} kEUR</b></span>
        <span>Average: <b>{avgCost.toLocaleString()} kEUR/unit</b></span>
        <span>Savings vs flat: <b>{Math.round((1 - cumulative / (c1 * n)) * 100)}%</b></span>
      </div>

      {/* Mini bar chart */}
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 1, height: 50, marginBottom: '0.2rem' }}>
        {units.map(u => (
          <div key={u.unit} style={{
            flex: 1, background: 'var(--accent)',
            height: `${(u.cost / c1) * 100}%`,
            borderRadius: '2px 2px 0 0', minWidth: 3,
          }} title={`Unit ${u.unit}: ${u.cost} kEUR`} />
        ))}
      </div>
      <div style={{ fontSize: '0.55rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
        Unit cost decreases with production experience (Wright learning curve)
      </div>
    </ToolSection>
  )
}

// ─── Shared components ───

// ─── 3-Bin Decision Categorizer ───

const DECISION_ITEMS_BY_LEVEL: Record<number, Array<{ item: string; category: 'obvious' | 'trade' | 'explore'; rationale: string }>> = {
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

const BIN_COLORS = { obvious: '#10b981', trade: '#f59e0b', explore: '#8b5cf6' }
const BIN_LABELS = { obvious: 'Obvious Choice', trade: 'Trade Study', explore: 'Design Space' }
const BIN_ICONS = { obvious: '✓', trade: '⇄', explore: '?' }

function DecisionCategorizer({ currentLevel, focusElement }: { currentLevel: number; focusElement: any }) {
  const items = DECISION_ITEMS_BY_LEVEL[currentLevel] || []
  if (items.length === 0) return null

  const bins = { obvious: items.filter(i => i.category === 'obvious'), trade: items.filter(i => i.category === 'trade'), explore: items.filter(i => i.category === 'explore') }

  return (
    <ToolSection title="Decision Categorization" color="#06b6d4">
      <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
        Categorize decisions at this level: what's obvious, what needs a trade, what needs exploration.
      </div>
      <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.2rem' }}>
        {(['obvious', 'trade', 'explore'] as const).map(bin => (
          <div key={bin} style={{ flex: 1, fontSize: '0.55rem', textAlign: 'center', padding: '0.15rem', borderRadius: '3px', background: `${BIN_COLORS[bin]}15`, color: BIN_COLORS[bin], fontWeight: 700 }}>
            {BIN_ICONS[bin]} {BIN_LABELS[bin]} ({bins[bin].length})
          </div>
        ))}
      </div>
      {items.map((item, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.15rem 0.3rem', fontSize: '0.63rem', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: BIN_COLORS[item.category], flexShrink: 0 }} />
          <span style={{ fontWeight: 500, flex: 1 }}>{item.item}</span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.55rem', maxWidth: 200 }}>{item.rationale}</span>
        </div>
      ))}
    </ToolSection>
  )
}

// ─── Architecture Trade Templates ───

const ARCH_TRADES: Record<string, Array<{ name: string; driver: string; options: Array<{ name: string; when: string }> }>> = {
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

function ArchitectureTradeWidget({ currentLevel, focusElement }: { currentLevel: number; focusElement: any }) {
  const domain = focusElement?.subsystem_domain
  const trades = domain ? (ARCH_TRADES[domain] || []) : (currentLevel === 2 ? Object.values(ARCH_TRADES).flat() : [])
  if (trades.length === 0) return null

  return (
    <ToolSection title="Architecture Trades" color="#ec4899">
      <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
        Which architecture is right? The driving requirement determines the answer.
      </div>
      {trades.map((trade, i) => (
        <div key={i} style={{ marginBottom: '0.4rem' }}>
          <div style={{ fontWeight: 600, fontSize: '0.68rem', marginBottom: '0.1rem' }}>{trade.name}</div>
          <div style={{ fontSize: '0.6rem', color: 'var(--warning)', marginBottom: '0.2rem' }}>Driver: {trade.driver}</div>
          {trade.options.map((opt, j) => (
            <div key={j} style={{ display: 'flex', gap: '0.3rem', padding: '0.1rem 0.3rem', fontSize: '0.6rem', borderLeft: '2px solid var(--border)', marginLeft: '0.3rem', marginBottom: '0.1rem' }}>
              <span style={{ fontWeight: 500, minWidth: 120 }}>{opt.name}</span>
              <span style={{ color: 'var(--text-secondary)' }}>→ {opt.when}</span>
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
        background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.72rem',
        fontWeight: 600, color, padding: 0, marginBottom: '0.2rem',
      }}>
        {open ? '▾' : '▸'} {title}
      </button>
      {open && <div style={{ paddingTop: '0.2rem' }}>{children}</div>}
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  padding: '0.3rem 0.6rem', fontSize: '0.68rem', fontWeight: 600, borderRadius: '4px',
  background: 'var(--accent)', color: 'white', border: 'none', cursor: 'pointer',
}
const rowStyle: React.CSSProperties = {
  padding: '0.25rem 0.3rem', borderRadius: '3px', background: 'var(--bg-card)',
  marginBottom: '0.2rem', fontSize: '0.68rem',
}
const inputStyle: React.CSSProperties = {
  width: 60, padding: '0.15rem 0.3rem', fontSize: '0.65rem', borderRadius: '3px',
  background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
  marginLeft: '0.2rem',
}
const labelStyle: React.CSSProperties = { fontSize: '0.63rem', color: 'var(--text-secondary)' }
const thL: React.CSSProperties = { textAlign: 'left', padding: '0.2rem 0.3rem', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.6rem' }
const thR: React.CSSProperties = { ...thL, textAlign: 'right' }
const thC: React.CSSProperties = { ...thL, textAlign: 'center' }
