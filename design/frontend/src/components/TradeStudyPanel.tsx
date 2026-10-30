import { useState, useEffect } from 'react'
import { SVGBarChart } from '../charts/SVGBarChart'
import { useSensitivity, useEOLCurves } from '../hooks/useSession'

// --- Tabular Trade Study Types ---
interface TradeCriterion { id: string; name: string; weight: number; direction: string; unit: string; category: string }
interface TradeOption { id: string; name: string; description: string; scores: Record<string, string | number> }
interface TradeTemplate { id: string; name: string; criteria: TradeCriterion[] }
interface TradeResult { rank: number; option_id: string; option_name: string; total_score: number; all_thresholds_met: boolean; normalised_scores: Record<string, number>; weighted_scores: Record<string, number> }

const SWEEP_PARAMS = [
  { id: 'orbit.altitude_km', label: 'Orbit altitude (km)', min: 300, max: 800 },
  { id: 'payloads.0.mass_kg', label: 'Payload mass (kg)', min: 1, max: 200 },
  { id: 'payloads.0.power_w', label: 'Payload power (W)', min: 5, max: 500 },
  { id: 'payloads.0.data_rate_mbps', label: 'Payload data rate (Mbps)', min: 1, max: 1000 },
  { id: 'design_lifetime_years', label: 'Mission duration (years)', min: 1, max: 15 },
]

const KEY_METRICS = [
  { id: 'mass.dry_mass_kg', label: 'Dry mass (kg)', color: '#3b82f6' },
  { id: 'power.sa_power_eol_w', label: 'SA power EOL (W)', color: '#10b981' },
  { id: 'cost.total_meur', label: 'Cost (MEUR)', color: '#f59e0b' },
  { id: 'link.downlink_margin_db', label: 'Link margin (dB)', color: '#8b5cf6' },
]

export function TradeStudyPanel({ studyId }: { studyId: string | null }) {
  const [sweepParam, setSweepParam] = useState(SWEEP_PARAMS[0].id)
  const [numPoints, setNumPoints] = useState(10)
  const sensitivity = useSensitivity()
  const eol = useEOLCurves(studyId)

  const meta = SWEEP_PARAMS.find(p => p.id === sweepParam)
  const [minVal, setMinVal] = useState(meta?.min || 0)
  const [maxVal, setMaxVal] = useState(meta?.max || 100)

  const runSweep = () => {
    if (!studyId) return
    sensitivity.mutate({
      sweep_param: sweepParam,
      sweep_min: minVal,
      sweep_max: maxVal,
      num_points: numPoints,
      study_id: studyId,
    })
  }

  // Transform sensitivity result into recharts data
  const sweepData = (sensitivity.data as any)?.points
    ? ((sensitivity.data as any).points as any[]).map((p: any) => ({
        sweep: p.sweep_value,
        ...p.key_params,
      }))
    : []

  // EOL degradation data
  const eolData = (eol.data as any)?.curves || []

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Trade Studies & Sensitivity</h2>

      {/* Sensitivity controls */}
      <div className="card">
        <h3>Parameter Sweep</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <div className="form-group">
            <label>Parameter</label>
            <select className="select" value={sweepParam} onChange={e => {
              const next = SWEEP_PARAMS.find(p => p.id === e.target.value)
              if (next) {
                setSweepParam(next.id)
                setMinVal(next.min)
                setMaxVal(next.max)
              }
            }}>
              {SWEEP_PARAMS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Min</label>
            <input className="input" type="number" value={minVal} onChange={e => setMinVal(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>Max</label>
            <input className="input" type="number" value={maxVal} onChange={e => setMaxVal(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>Points</label>
            <input className="input" type="number" min={3} max={40} value={numPoints} onChange={e => setNumPoints(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>&nbsp;</label>
            <button className="btn" onClick={runSweep} disabled={sensitivity.isPending || !studyId}>
              {sensitivity.isPending ? 'Running...' : 'Run Sweep'}
            </button>
          </div>
        </div>

        {sensitivity.data && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)', marginBottom: '0.5rem' }}>
            Swept {numPoints} points in {(sensitivity.data as any).total_time_ms?.toFixed(0) || '?'}ms
          </div>
        )}

        {sweepData.length > 0 && (
          <SVGBarChart
            data={sweepData.slice(0, 20).map((d: any) => ({ label: String(d.sweep), value: d.mass_kg || 0, color: '#3b82f6' }))}
            width={500} height={240} unit=" kg" title="Parametric Sweep"
          />
        )}
      </div>

      {/* Tabular Trade Study */}
      <TabularTradeSection />

      {/* EOL degradation curves */}
      <div className="card">
        <h3>End-of-Life Degradation</h3>
        {eolData.length === 0 ? (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)' }}>Select a study to view EOL curves.</div>
        ) : (
          <SVGBarChart
            data={eolData.map((d: any) => ({ label: `Yr ${d.year}`, value: d.sa_power_w || 0, color: '#3b82f6' }))}
            width={500} height={220} unit=" W" title="SA Power Degradation"
          />
        )}
      </div>
    </div>
  )
}


// --- Tabular Trade Study Section ---

function TabularTradeSection() {
  const [templates, setTemplates] = useState<TradeTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [criteria, setCriteria] = useState<TradeCriterion[]>([])
  const [options, setOptions] = useState<TradeOption[]>([])
  const [results, setResults] = useState<TradeResult[] | null>(null)
  const [recommendation, setRecommendation] = useState('')
  const [running, setRunning] = useState(false)
  const [tradeName, setTradeName] = useState('New Trade Study')

  // Load templates on mount
  useEffect(() => {
    fetch('/api/lifecycle/trade-templates')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.templates) setTemplates(data.templates) })
      .catch(() => {})
  }, [])

  const loadTemplate = (templateId: string) => {
    const tmpl = templates.find(t => t.id === templateId)
    if (!tmpl) return
    setSelectedTemplate(templateId)
    setTradeName(tmpl.name)
    setCriteria(tmpl.criteria)
    setResults(null)
    // Create 3 blank options
    setOptions([
      { id: 'opt-1', name: 'Option A', description: '', scores: {} },
      { id: 'opt-2', name: 'Option B', description: '', scores: {} },
      { id: 'opt-3', name: 'Option C', description: '', scores: {} },
    ])
  }

  const addOption = () => {
    const id = `opt-${Date.now()}`
    setOptions(prev => [...prev, { id, name: `Option ${prev.length + 1}`, description: '', scores: {} }])
  }

  const addCriterion = () => {
    const id = `crit-${Date.now()}`
    setCriteria(prev => [...prev, { id, name: 'New Criterion', weight: 0.5, direction: 'max', unit: '', category: '' }])
  }

  const updateOption = (optId: string, field: string, value: any) => {
    setOptions(prev => prev.map(o => o.id === optId ? { ...o, [field]: value } : o))
  }

  const updateScore = (optId: string, critId: string, value: string) => {
    setOptions(prev => prev.map(o =>
      o.id === optId ? { ...o, scores: { ...o.scores, [critId]: value } } : o
    ))
  }

  const updateCriterion = (critId: string, field: string, value: any) => {
    setCriteria(prev => prev.map(c => c.id === critId ? { ...c, [field]: value } : c))
  }

  const runTrade = async () => {
    setRunning(true)
    setResults(null)
    try {
      const res = await fetch('/api/lifecycle/trade-study', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: tradeName, criteria, options }),
      })
      if (res.ok) {
        const data = await res.json()
        setResults(data.results || [])
        setRecommendation(data.recommendation || '')
      }
    } catch {}
    setRunning(false)
  }

  return (
    <div className="card">
      <h3>Tabular Trade Study</h3>
      <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Define criteria with weightings, score options quantitatively or qualitatively
        (low/medium/high/excellent), and rank alternatives.
      </p>

      {/* Template selector */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <select className="select" value={selectedTemplate} onChange={e => loadTemplate(e.target.value)}
          style={{ fontSize: '0.78rem', maxWidth: '250px' }}>
          <option value="">Load template...</option>
          {templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <input className="input" value={tradeName} onChange={e => setTradeName(e.target.value)}
          placeholder="Trade study name" style={{ fontSize: '0.78rem', flex: 1, maxWidth: '250px' }} />
        <button className="btn btn-sm" onClick={addCriterion} style={{ fontSize: '0.7rem' }}>+ Criterion</button>
        <button className="btn btn-sm" onClick={addOption} style={{ fontSize: '0.7rem' }}>+ Option</button>
        <button className="btn btn-sm" onClick={runTrade} disabled={running || criteria.length === 0 || options.length === 0}
          style={{ fontSize: '0.7rem', background: '#10b981' }}>
          {running ? 'Computing...' : 'Run Trade'}
        </button>
      </div>

      {/* Criteria + Options matrix */}
      {criteria.length > 0 && options.length > 0 && (
        <div style={{ overflowX: 'auto', marginBottom: '0.75rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={thL}>Criterion</th>
                <th style={thC}>Weight</th>
                <th style={thC}>Dir</th>
                {options.map(o => (
                  <th key={o.id} style={thC}>
                    <input className="input" value={o.name} onChange={e => updateOption(o.id, 'name', e.target.value)}
                      style={{ fontSize: '0.72rem', width: '100%', textAlign: 'center', fontWeight: 600 }} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {criteria.map(c => (
                <tr key={c.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={tdL}>
                    <input className="input" value={c.name} onChange={e => updateCriterion(c.id, 'name', e.target.value)}
                      style={{ fontSize: '0.72rem', width: '100%' }} />
                  </td>
                  <td style={tdC}>
                    <input className="input" type="number" min={0} max={1} step={0.05} value={c.weight}
                      onChange={e => updateCriterion(c.id, 'weight', Number(e.target.value))}
                      style={{ fontSize: '0.72rem', width: '50px', textAlign: 'center' }} />
                  </td>
                  <td style={tdC}>
                    <select className="select" value={c.direction} onChange={e => updateCriterion(c.id, 'direction', e.target.value)}
                      style={{ fontSize: '0.68rem', width: '50px' }}>
                      <option value="max">max</option>
                      <option value="min">min</option>
                    </select>
                  </td>
                  {options.map(o => (
                    <td key={o.id} style={tdC}>
                      <input className="input" value={o.scores[c.id] ?? ''} placeholder="value or low/med/high"
                        onChange={e => updateScore(o.id, c.id, e.target.value)}
                        style={{ fontSize: '0.72rem', width: '100%', textAlign: 'center' }} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Results */}
      {results && (
        <div style={{ marginTop: '0.5rem' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#10b981', marginBottom: '0.4rem' }}>
            {recommendation}
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={thC}>Rank</th>
                <th style={thL}>Option</th>
                <th style={thC}>Score</th>
                <th style={thC}>Thresholds</th>
                {criteria.map(c => <th key={c.id} style={thC}>{c.name.slice(0, 12)}</th>)}
              </tr>
            </thead>
            <tbody>
              {results.map(r => (
                <tr key={r.option_id} style={{
                  borderBottom: '1px solid rgba(255,255,255,0.05)',
                  background: r.rank === 1 ? 'rgba(16,185,129,0.08)' : 'transparent',
                }}>
                  <td style={{ ...tdC, fontWeight: 700, color: r.rank === 1 ? '#10b981' : '#d1d5db' }}>#{r.rank}</td>
                  <td style={tdL}>{r.option_name}</td>
                  <td style={{ ...tdC, fontWeight: 700, fontFamily: 'monospace' }}>{(r.total_score * 100).toFixed(0)}%</td>
                  <td style={tdC}>
                    <span style={{ color: r.all_thresholds_met ? '#10b981' : '#ef4444', fontSize: '0.72rem' }}>
                      {r.all_thresholds_met ? 'PASS' : 'FAIL'}
                    </span>
                  </td>
                  {criteria.map(c => (
                    <td key={c.id} style={{ ...tdC, fontFamily: 'monospace' }}>
                      {r.normalised_scores[c.id] !== undefined ? (r.normalised_scores[c.id] * 100).toFixed(0) + '%' : '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {criteria.length === 0 && (
        <div style={{ fontSize: '0.78rem', color: '#6b7280', padding: '1rem', textAlign: 'center' }}>
          Select a template above or add criteria and options to build a custom trade study.
        </div>
      )}
    </div>
  )
}

const thL: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.68rem', color: '#9ca3af', textTransform: 'uppercase' }
const thC: React.CSSProperties = { ...thL, textAlign: 'center' }
const tdL: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdC: React.CSSProperties = { ...tdL, textAlign: 'center' }
