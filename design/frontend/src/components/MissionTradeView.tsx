/**
 * MissionTradeView — Computed space vs non-space mission trade analysis.
 *
 * Calls /api/lifecycle/mission-trade with the designer's objectives
 * and shows scored alternatives BEFORE they commit to building a satellite.
 * Replaces the manual "add alternatives" form in the Concept step.
 */
import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'

interface TradeAlternative {
  rank: number
  name: string
  category: string
  description: string
  gsd_m: number
  revisit_days: number
  coverage: string
  latency_hours: number
  cost_type: string
  annual_cost_keur: number
  total_3yr_cost_keur: number
  data_ownership: string
  scheduling_control: string
  pros: string[]
  cons: string[]
  scores: Record<string, number>
  total_score: number
  meets_objectives: boolean
}

interface TradeResult {
  question: string
  alternatives: TradeAlternative[]
  space_justified: boolean
  justification: string
  key_question: string
}

const CATEGORY_COLORS: Record<string, string> = {
  existing_satellite: '#10b981',
  commercial_tasking: '#3b82f6',
  aerial: '#f59e0b',
  ground: '#84cc16',
  new_satellite: '#8b5cf6',
  hybrid: '#06b6d4',
}

export function MissionTradeView({ onConceptSelected }: { onConceptSelected?: () => void }) {
  const { missionNeed } = useDesignStore()
  const [result, setResult] = useState<TradeResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState<number | null>(null)

  const { requirements } = useDesignStore()
  const missionType = requirements.mission_type

  // Explicit inputs — pre-populated from objectives where possible, editable
  const objectives = missionNeed.objectives
  const isOptical = missionType === 'earth_observation' || missionType === 'science_planetary'
  const isComms = missionType === 'communications' || missionType === 'relay' || missionType === 'iot'
  const isRealTime = missionType === 'relay' || missionType === 'communications'
  const [gsd, setGsd] = useState(_extractGSD(objectives) || 10)
  const [revisit, setRevisit] = useState(_extractRevisit(objectives) || 3)
  const [coverage, setCoverage] = useState('regional')
  const [latency, setLatency] = useState(isRealTime ? 0.01 : 24)
  const [budget, setBudget] = useState(500)
  const [needOwnership, setNeedOwnership] = useState(false)
  const [needControl, setNeedControl] = useState(false)
  // Comms-specific parameters
  const [throughput, setThroughput] = useState(10)  // Mbps
  const [availability, setAvailability] = useState(99.0)  // %
  const [linkContinuity, setLinkContinuity] = useState(isRealTime ? 24 : 0.5)  // hours

  const runTrade = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/lifecycle/mission-trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_gsd_m: isOptical ? gsd : 0,
          target_revisit_days: revisit,
          target_coverage: coverage,
          target_latency_hours: latency,
          max_annual_budget_keur: budget,
          require_data_ownership: needOwnership,
          require_scheduling_control: needControl,
          mission_type: missionType,
          num_spacecraft: coverage === 'global' ? 4 : 1,  // Auto-suggest constellation for global
        }),
      })
      if (res.ok) setResult(await res.json())
    } catch {}
    setLoading(false)
  }

  return (
    <div>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Is Space the Right Answer?</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Before building a satellite, consider all alternatives. This analysis compares
        existing data, commercial services, aerial, ground, and dedicated satellite options
        against your objectives.
      </p>

      {/* Trade analysis inputs */}
      <div className="card" style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '0.85rem', marginBottom: '0.25rem' }}>What do you need?</h3>
        <p style={{ fontSize: '0.68rem', color: '#6b7280', marginBottom: '0.5rem' }}>
          Parameters adapted for: <strong style={{ color: '#3b82f6' }}>{missionType?.replace(/_/g, ' ') || 'earth observation'}</strong>
          {isComms && ' — showing throughput, availability, and link continuity'}
          {isOptical && ' — showing resolution, revisit, and coverage'}
          {!isComms && !isOptical && ' — showing general mission parameters'}
        </p>
        <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
          Set your performance and budget targets. The analysis will compare all available
          options — existing satellite data, commercial services, aerial, ground, and a new satellite.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem' }}>
          {isOptical && (
            <div className="form-group" style={{ margin: 0 }}>
              <label>Ground resolution (m)</label>
              <input className="input" type="number" min={0.1} step={1} value={gsd}
                onChange={e => setGsd(Number(e.target.value) || 10)} />
            </div>
          )}
          {isComms && (
            <>
              <div className="form-group" style={{ margin: 0 }}>
                <label>Throughput (Mbps)</label>
                <input className="input" type="number" min={0.01} step={1} value={throughput}
                  onChange={e => setThroughput(Number(e.target.value) || 10)} />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label>Availability (%)</label>
                <input className="input" type="number" min={50} max={100} step={0.1} value={availability}
                  onChange={e => setAvailability(Number(e.target.value) || 99)} />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label>Link continuity (hours)</label>
                <input className="input" type="number" min={0} step={0.5} value={linkContinuity}
                  onChange={e => setLinkContinuity(Number(e.target.value) || 0.5)} />
              </div>
            </>
          )}
          {!isRealTime && (
            <div className="form-group" style={{ margin: 0 }}>
              <label>{isComms ? 'Service gap tolerance (hours)' : 'Revisit time (days)'}</label>
              <input className="input" type="number" min={0.1} step={1} value={revisit}
                onChange={e => setRevisit(Number(e.target.value) || 3)} />
            </div>
          )}
          <div className="form-group" style={{ margin: 0 }}>
            <label>Coverage</label>
            <select className="select" value={coverage} onChange={e => setCoverage(e.target.value)}>
              <option value="global">Global</option>
              <option value="regional">Regional</option>
              <option value="local">Local / Point-to-point</option>
              {isComms && <option value="corridor">Corridor / Shipping lane</option>}
            </select>
          </div>
          {!isRealTime && (
            <div className="form-group" style={{ margin: 0 }}>
              <label>Max data latency (hours)</label>
              <input className="input" type="number" min={0.01} step={1} value={latency}
                onChange={e => setLatency(Number(e.target.value) || 24)} />
            </div>
          )}
          <div className="form-group" style={{ margin: 0 }}>
            <label>Annual budget (kEUR)</label>
            <input className="input" type="number" min={0} step={50} value={budget}
              onChange={e => setBudget(Number(e.target.value) || 500)} />
          </div>
          <div className="form-group" style={{ margin: 0 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={needOwnership} onChange={e => setNeedOwnership(e.target.checked)} />
              Must own data
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer', marginTop: '0.3rem' }}>
              <input type="checkbox" checked={needControl} onChange={e => setNeedControl(e.target.checked)} />
              Must control scheduling
            </label>
          </div>
          <div className="form-group" style={{ margin: 0 }}>
            <label style={{ fontSize: '0.68rem', color: '#6b7280' }}>
              Mission type: {missionType.replace(/_/g, ' ')} (from Step 3)
            </label>
          </div>
        </div>
        <button className="btn" onClick={runTrade} disabled={loading}
          style={{ marginTop: '0.75rem', width: '100%' }}>
          {loading ? 'Analysing alternatives...' : 'Run Mission Trade Analysis'}
        </button>
      </div>

      {result && (
        <>
          {/* Key question */}
          <div style={{
            padding: '0.6rem 0.75rem', borderRadius: '6px', marginBottom: '0.75rem',
            background: result.space_justified ? 'rgba(139,92,246,0.1)' : 'rgba(16,185,129,0.1)',
            border: `1px solid ${result.space_justified ? '#8b5cf6' : '#10b981'}`,
          }}>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: result.space_justified ? '#8b5cf6' : '#10b981', marginBottom: '0.3rem' }}>
              {result.space_justified ? 'Space mission may be justified' : 'Question: is a new satellite needed?'}
            </div>
            <div style={{ fontSize: '0.78rem', color: '#d1d5db' }}>{result.justification}</div>
            {!result.space_justified && (
              <div style={{ fontSize: '0.75rem', color: '#f59e0b', marginTop: '0.3rem', fontStyle: 'italic' }}>
                {result.key_question}
              </div>
            )}
          </div>

          {/* Alternatives table */}
          {result.alternatives.map((alt, i) => {
            const color = CATEGORY_COLORS[alt.category] || '#6b7280'
            const isExpanded = expanded === i
            return (
              <div key={i} style={{
                padding: '0.5rem 0.75rem', borderRadius: '6px', marginBottom: '0.4rem',
                background: 'var(--bg-secondary, #1f2937)', border: `1px solid var(--border, #374151)`,
                borderLeft: `3px solid ${color}`, cursor: 'pointer',
              }} onClick={() => setExpanded(isExpanded ? null : i)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#6b7280' }}>#{alt.rank}</span>
                  <span style={{ fontWeight: 600, fontSize: '0.82rem' }}>{alt.name}</span>
                  <span style={{
                    fontSize: '0.65rem', padding: '0.1rem 0.35rem', borderRadius: '3px',
                    background: `${color}22`, color,
                  }}>{alt.category.replace(/_/g, ' ')}</span>
                  {alt.meets_objectives && (
                    <span style={{ fontSize: '0.65rem', color: '#10b981' }}>meets objectives</span>
                  )}
                  <span style={{ marginLeft: 'auto', fontFamily: 'monospace', fontSize: '0.75rem', color }}>
                    {(alt.total_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.72rem', color: '#9ca3af' }}>
                  <span>{alt.gsd_m > 0 ? `${alt.gsd_m}m` : 'N/A'} GSD</span>
                  <span>{alt.revisit_days}d revisit</span>
                  <span>{alt.coverage}</span>
                  <span>{alt.cost_type === 'free' ? 'FREE' : `${alt.total_3yr_cost_keur} kEUR/3yr`}</span>
                  <span>{alt.data_ownership} data</span>
                </div>

                {isExpanded && (
                  <div style={{ marginTop: '0.4rem', fontSize: '0.75rem' }}>
                    <div style={{ color: '#d1d5db', marginBottom: '0.3rem' }}>{alt.description}</div>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ color: '#10b981', fontWeight: 600, fontSize: '0.7rem', marginBottom: '0.2rem' }}>Pros</div>
                        {alt.pros.map((p, j) => <div key={j} style={{ color: '#9ca3af', fontSize: '0.7rem' }}>+ {p}</div>)}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ color: '#ef4444', fontWeight: 600, fontSize: '0.7rem', marginBottom: '0.2rem' }}>Cons</div>
                        {alt.cons.map((c, j) => <div key={j} style={{ color: '#9ca3af', fontSize: '0.7rem' }}>- {c}</div>)}
                      </div>
                    </div>
                    {alt.category === 'new_satellite' && onConceptSelected && (
                      <button className="btn btn-sm" onClick={(e) => { e.stopPropagation(); onConceptSelected() }}
                        style={{ marginTop: '0.4rem', fontSize: '0.72rem', background: '#8b5cf6' }}>
                        Proceed with new satellite design →
                      </button>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </>
      )}

      {!result && !loading && objectives.length === 0 && (
        <div style={{ padding: '1rem', color: '#6b7280', fontSize: '0.8rem', textAlign: 'center' }}>
          Define mission objectives in Step 1 first. The trade analysis will compute
          alternatives automatically from your GSD, revisit, and coverage needs.
        </div>
      )}
    </div>
  )
}

// Extract GSD from objective measurable criteria (heuristic)
function _extractGSD(objectives: Array<{ measurable_criterion: string }>): number | null {
  for (const obj of objectives) {
    const m = obj.measurable_criterion.match(/(\d+)\s*m\b/i)
    if (m) return parseInt(m[1])
    const gsd = obj.measurable_criterion.match(/GSD\s*[<=]*\s*(\d+)/i)
    if (gsd) return parseInt(gsd[1])
  }
  return null
}

function _extractRevisit(objectives: Array<{ measurable_criterion: string }>): number | null {
  for (const obj of objectives) {
    const m = obj.measurable_criterion.match(/(\d+)\s*day/i)
    if (m) return parseInt(m[1])
    const rev = obj.measurable_criterion.match(/revisit\s*[<=]*\s*(\d+)/i)
    if (rev) return parseInt(rev[1])
  }
  return null
}
