import { useEffect, useMemo, useState } from 'react'
import {
  useOptimizerConfig,
  useOptimizerRun,
  useStartOptimization,
  type ParetoPoint,
} from '../hooks/useOptimizer'
import { useDesignStore } from '../stores/designStore'

interface Props {
  sessionId: string | null
}

interface VarRow {
  id: string
  enabled: boolean
  lower: number
  upper: number
}

type Mode = 'single' | 'pareto'

export function OptimizerPanel({ sessionId }: Props) {
  const missionType = useDesignStore(s => s.requirements.mission_type)
  const pointingDeg = useDesignStore(s => s.requirements.payloads?.[0]?.pointing_accuracy_deg ?? 1.0)
  const { data: config, isLoading: cfgLoading } = useOptimizerConfig(missionType, false, pointingDeg)
  const start = useStartOptimization()

  const [mode, setMode] = useState<Mode>('single')
  const [objective, setObjective] = useState<string>('min_mass')
  const [objectives, setObjectives] = useState<string[]>(['min_mass', 'min_cost'])
  const [maxEvals, setMaxEvals] = useState<number>(120)
  const [seed, setSeed] = useState<number>(42)
  const [popSize, setPopSize] = useState<number>(40)
  const [nGens, setNGens] = useState<number>(30)
  const [vars, setVars] = useState<VarRow[]>([])
  const [runId, setRunId] = useState<number | null>(null)

  const { data: run } = useOptimizerRun(runId, runId !== null)

  useEffect(() => {
    if (!config) return
    setVars(config.default_variables.map((d: any) => ({
      id: d.id, enabled: d.relevant !== false, lower: d.lower, upper: d.upper,
    })))
  }, [config])

  useEffect(() => {
    setVars(rows => {
      if (rows.length === 0 || rows.some(r => r.enabled)) return rows
      return rows.map((r, i) => i < 2 ? { ...r, enabled: true } : r)
    })
  }, [vars.length])

  const enabled = useMemo(() => vars.filter(v => v.enabled), [vars])

  // Optimizer works in both session and solo mode
  const effectiveSessionId = sessionId || 'solo'

  const handleStart = async () => {
    if (enabled.length === 0) { alert('Select at least one design variable'); return }
    try {
      const res = await start.mutateAsync({
        sessionId: effectiveSessionId,
        ...(mode === 'pareto'
          ? { objectives, pop_size: popSize, n_generations: nGens }
          : { objective }),
        variables: enabled.map(v => v.id),
        bounds: enabled.map(v => [v.lower, v.upper] as [number, number]),
        max_evals: maxEvals,
        seed,
      })
      setRunId(res.run_id)
    } catch (e) {
      alert(`Failed to start: ${e}`)
    }
  }

  const progress = run?.latest_event?.fraction ?? (
    run ? (run.num_evals / Math.max(maxEvals, 1)) : 0
  )
  const pct = Math.round((progress || 0) * 100)

  const toggleObjective = (key: string) => {
    setObjectives(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    )
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ margin: '0 0 0.75rem 0' }}>Design Optimiser</h2>

      {cfgLoading && <div>Loading config...</div>}

      {config && (
        <>
          {/* Mode toggle */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <button
              className={`btn ${mode === 'single' ? 'btn-active' : ''}`}
              onClick={() => setMode('single')}
              style={{
                padding: '0.3rem 0.8rem', fontSize: '0.8rem',
                background: mode === 'single' ? 'var(--accent, #3b82f6)' : 'var(--bg-secondary, #1f2937)',
                color: mode === 'single' ? '#fff' : 'var(--text-secondary, #9ca3af)',
                border: '1px solid var(--border, #374151)', borderRadius: '4px', cursor: 'pointer',
              }}
            >
              Single objective
            </button>
            <button
              className={`btn ${mode === 'pareto' ? 'btn-active' : ''}`}
              onClick={() => setMode('pareto')}
              style={{
                padding: '0.3rem 0.8rem', fontSize: '0.8rem',
                background: mode === 'pareto' ? 'var(--accent, #3b82f6)' : 'var(--bg-secondary, #1f2937)',
                color: mode === 'pareto' ? '#fff' : 'var(--text-secondary, #9ca3af)',
                border: '1px solid var(--border, #374151)', borderRadius: '4px', cursor: 'pointer',
              }}
            >
              Pareto (NSGA-II)
            </button>
          </div>

          {/* Objective selection */}
          {mode === 'single' ? (
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <div style={{ flex: '1 1 220px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)' }}>Objective</label>
                <select className="select" value={objective} onChange={e => setObjective(e.target.value)} style={{ width: '100%' }}>
                  {config.objectives.map(o => (
                    <option key={o.key} value={o.key}>{o.description}</option>
                  ))}
                </select>
              </div>
              <div style={{ width: '100px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)' }}>Max evals</label>
                <input className="input" type="number" min={20} max={1000} value={maxEvals}
                  onChange={e => setMaxEvals(Math.max(20, Number(e.target.value) || 120))}
                  style={{ width: '100%' }} />
              </div>
              <div style={{ width: '80px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)' }}>Seed</label>
                <input className="input" type="number" value={seed}
                  onChange={e => setSeed(Number(e.target.value) || 0)}
                  style={{ width: '100%' }} />
              </div>
            </div>
          ) : (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)', display: 'block', marginBottom: '0.3rem' }}>
                Objectives (select 2+)
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.75rem' }}>
                {config.objectives.map(o => (
                  <label key={o.key} style={{
                    display: 'flex', alignItems: 'center', gap: '0.3rem',
                    fontSize: '0.8rem', padding: '0.2rem 0.5rem',
                    background: objectives.includes(o.key) ? 'rgba(59,130,246,0.15)' : 'transparent',
                    border: '1px solid var(--border, #374151)', borderRadius: '4px', cursor: 'pointer',
                  }}>
                    <input type="checkbox" checked={objectives.includes(o.key)}
                      onChange={() => toggleObjective(o.key)} />
                    {o.description}
                  </label>
                ))}
              </div>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <div style={{ width: '100px' }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)' }}>Pop size</label>
                  <input className="input" type="number" min={10} max={200} value={popSize}
                    onChange={e => setPopSize(Math.max(10, Number(e.target.value) || 40))}
                    style={{ width: '100%' }} />
                </div>
                <div style={{ width: '100px' }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)' }}>Generations</label>
                  <input className="input" type="number" min={5} max={200} value={nGens}
                    onChange={e => setNGens(Math.max(5, Number(e.target.value) || 30))}
                    style={{ width: '100%' }} />
                </div>
                <div style={{ width: '80px' }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)' }}>Seed</label>
                  <input className="input" type="number" value={seed}
                    onChange={e => setSeed(Number(e.target.value) || 0)}
                    style={{ width: '100%' }} />
                </div>
              </div>
            </div>
          )}

          {/* Design variables */}
          <h3 style={{ fontSize: '0.95rem', margin: '0.5rem 0' }}>Design variables</h3>
          <table style={{ width: '100%', fontSize: '0.8rem', borderCollapse: 'collapse', marginBottom: '1rem' }}>
            <thead>
              <tr style={{ color: 'var(--text-secondary, #9ca3af)', textAlign: 'left' }}>
                <th style={{ padding: '0.25rem' }}></th>
                <th style={{ padding: '0.25rem' }}>Parameter</th>
                <th style={{ padding: '0.25rem' }}>Lower</th>
                <th style={{ padding: '0.25rem' }}>Upper</th>
              </tr>
            </thead>
            <tbody>
              {vars.map((v, i) => (
                <tr key={v.id} style={{ borderTop: '1px solid rgba(55,65,81,0.4)' }}>
                  <td style={{ padding: '0.2rem' }}>
                    <input type="checkbox" checked={v.enabled}
                      onChange={e => setVars(vs => vs.map((x, j) => j === i ? { ...x, enabled: e.target.checked } : x))} />
                  </td>
                  <td style={{ padding: '0.2rem', fontFamily: 'monospace', fontSize: '0.74rem' }}>{v.id}</td>
                  <td style={{ padding: '0.2rem' }}>
                    <input className="input" type="number" step="any" value={v.lower}
                      onChange={e => setVars(vs => vs.map((x, j) => j === i ? { ...x, lower: Number(e.target.value) } : x))}
                      style={{ width: '80px', fontSize: '0.75rem' }}
                      disabled={!v.enabled} />
                  </td>
                  <td style={{ padding: '0.2rem' }}>
                    <input className="input" type="number" step="any" value={v.upper}
                      onChange={e => setVars(vs => vs.map((x, j) => j === i ? { ...x, upper: Number(e.target.value) } : x))}
                      style={{ width: '80px', fontSize: '0.75rem' }}
                      disabled={!v.enabled} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <button
            className="btn"
            onClick={handleStart}
            disabled={
              start.isPending ||
              enabled.length === 0 ||
              run?.status === 'running' ||
              (mode === 'pareto' && objectives.length < 2)
            }
          >
            {start.isPending ? 'Starting...' :
              run?.status === 'running' ? 'Running...' :
              mode === 'single'
                ? `Run (${enabled.length} vars x ${maxEvals} evals)`
                : `Pareto (${objectives.length} obj x ${enabled.length} vars x ${nGens} gen)`}
          </button>

          {run && (
            <div style={{
              marginTop: '1.25rem',
              padding: '0.75rem',
              background: 'var(--bg-secondary, #1f2937)',
              border: '1px solid var(--border, #374151)',
              borderRadius: '6px',
            }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'baseline' }}>
                <strong>Run #{run.id}</strong>
                <span style={{
                  fontSize: '0.72rem',
                  padding: '0.1rem 0.4rem',
                  borderRadius: '3px',
                  background: run.status === 'done' ? 'rgba(16,185,129,0.2)' :
                              run.status === 'failed' ? 'rgba(239,68,68,0.2)' :
                              'rgba(245,158,11,0.2)',
                  color: run.status === 'done' ? '#10b981' :
                         run.status === 'failed' ? '#ef4444' : '#f59e0b',
                }}>
                  {run.status}
                </span>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary, #9ca3af)' }}>
                  {run.num_evals} eval{run.num_evals === 1 ? '' : 's'}
                  {run.duration_ms > 0 && ` · ${run.duration_ms.toFixed(0)} ms`}
                </span>
              </div>

              {/* Progress bar */}
              <div style={{ height: '6px', borderRadius: '3px', background: 'var(--bg-primary, #111827)', overflow: 'hidden', margin: '0.5rem 0' }}>
                <div style={{
                  height: '100%',
                  width: `${pct}%`,
                  background: run.status === 'done' ? '#10b981' : '#3b82f6',
                  transition: 'width 0.3s',
                }} />
              </div>

              {/* Pareto front display */}
              {run.pareto_front && run.pareto_front.length > 0 && (
                <ParetoFrontView pareto={run.pareto_front} />
              )}

              {/* Single-objective best result */}
              {(!run.pareto_front || run.pareto_front.length === 0) && run.best_y !== null && (
                <div style={{ fontSize: '0.82rem' }}>
                  <div>
                    <strong>Best {run.objective}:</strong>{' '}
                    {typeof run.best_y === 'number' ? run.best_y.toFixed(3) : run.best_y}
                  </div>
                  {Object.keys(run.best_x).length > 0 && (
                    <div style={{ marginTop: '0.4rem' }}>
                      <div style={{ color: 'var(--text-secondary, #9ca3af)', fontSize: '0.75rem' }}>At:</div>
                      {Object.entries(run.best_x).map(([k, v]) => (
                        <div key={k} style={{ fontFamily: 'monospace', fontSize: '0.74rem', paddingLeft: '0.5rem' }}>
                          {k} = {typeof v === 'number' ? v.toFixed(3) : v}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {run.error && (
                <div style={{ color: 'var(--danger, #f87171)', fontSize: '0.78rem', marginTop: '0.4rem' }}>
                  Error: {run.error}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}


// ---------------------------------------------------------------------------
// Pareto Front visualisation (SVG scatter)
// ---------------------------------------------------------------------------

function ParetoFrontView({ pareto }: { pareto: ParetoPoint[] }) {
  if (pareto.length === 0) return null

  const objKeys = Object.keys(pareto[0].objectives)
  if (objKeys.length < 2) return null

  const xKey = objKeys[0]
  const yKey = objKeys[1]

  const xVals = pareto.map(p => p.objectives[xKey])
  const yVals = pareto.map(p => p.objectives[yKey])

  const xMin = Math.min(...xVals)
  const xMax = Math.max(...xVals)
  const yMin = Math.min(...yVals)
  const yMax = Math.max(...yVals)
  const xRange = xMax - xMin || 1
  const yRange = yMax - yMin || 1

  const W = 280
  const H = 180
  const pad = 36

  const toSvgX = (v: number) => pad + ((v - xMin) / xRange) * (W - 2 * pad)
  const toSvgY = (v: number) => H - pad - ((v - yMin) / yRange) * (H - 2 * pad)

  const [hover, setHover] = useState<number | null>(null)

  return (
    <div style={{ marginTop: '0.75rem' }}>
      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary, #9ca3af)', marginBottom: '0.3rem' }}>
        Pareto front ({pareto.length} points)
      </div>
      <svg width={W} height={H} style={{ background: 'var(--bg-primary, #111827)', borderRadius: '4px' }}>
        {/* Axes labels */}
        <text x={W / 2} y={H - 6} textAnchor="middle" fontSize="9" fill="#9ca3af">{xKey}</text>
        <text x={6} y={H / 2} textAnchor="middle" fontSize="9" fill="#9ca3af"
          transform={`rotate(-90, 6, ${H / 2})`}>{yKey}</text>

        {/* Axis ticks */}
        <text x={pad} y={H - pad + 12} textAnchor="middle" fontSize="8" fill="#6b7280">{xMin.toFixed(1)}</text>
        <text x={W - pad} y={H - pad + 12} textAnchor="middle" fontSize="8" fill="#6b7280">{xMax.toFixed(1)}</text>
        <text x={pad - 4} y={H - pad} textAnchor="end" fontSize="8" fill="#6b7280">{yMin.toFixed(1)}</text>
        <text x={pad - 4} y={pad} textAnchor="end" fontSize="8" fill="#6b7280">{yMax.toFixed(1)}</text>

        {/* Grid lines */}
        <line x1={pad} y1={pad} x2={pad} y2={H - pad} stroke="#374151" strokeWidth={0.5} />
        <line x1={pad} y1={H - pad} x2={W - pad} y2={H - pad} stroke="#374151" strokeWidth={0.5} />

        {/* Pareto line connecting sorted points */}
        <polyline
          points={pareto.map(p => `${toSvgX(p.objectives[xKey])},${toSvgY(p.objectives[yKey])}`).join(' ')}
          fill="none"
          stroke="rgba(59,130,246,0.4)"
          strokeWidth={1}
        />

        {/* Points */}
        {pareto.map((p, i) => (
          <circle
            key={i}
            cx={toSvgX(p.objectives[xKey])}
            cy={toSvgY(p.objectives[yKey])}
            r={hover === i ? 5 : 3}
            fill={hover === i ? '#f59e0b' : '#3b82f6'}
            stroke="#fff"
            strokeWidth={0.5}
            style={{ cursor: 'pointer' }}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          />
        ))}
      </svg>

      {/* Hover detail */}
      {hover !== null && pareto[hover] && (
        <div style={{
          fontSize: '0.74rem', marginTop: '0.3rem', padding: '0.4rem',
          background: 'rgba(245,158,11,0.1)', borderRadius: '4px',
          border: '1px solid rgba(245,158,11,0.3)',
        }}>
          <div style={{ fontWeight: 600, marginBottom: '0.2rem' }}>Point #{hover + 1}</div>
          {Object.entries(pareto[hover].objectives).map(([k, v]) => (
            <div key={k} style={{ fontFamily: 'monospace' }}>{k}: {v.toFixed(3)}</div>
          ))}
          <div style={{ color: 'var(--text-secondary, #9ca3af)', marginTop: '0.2rem', fontSize: '0.7rem' }}>
            {Object.entries(pareto[hover].x).map(([k, v]) => `${k}=${v.toFixed(2)}`).join(', ')}
          </div>
        </div>
      )}

      {/* Pareto table */}
      {pareto.length <= 20 && (
        <details style={{ marginTop: '0.5rem' }}>
          <summary style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)', cursor: 'pointer' }}>
            All {pareto.length} Pareto-optimal points
          </summary>
          <table style={{ width: '100%', fontSize: '0.72rem', borderCollapse: 'collapse', marginTop: '0.3rem' }}>
            <thead>
              <tr style={{ color: 'var(--text-secondary, #9ca3af)' }}>
                <th style={{ padding: '0.2rem', textAlign: 'left' }}>#</th>
                {objKeys.map(k => <th key={k} style={{ padding: '0.2rem', textAlign: 'right' }}>{k}</th>)}
              </tr>
            </thead>
            <tbody>
              {pareto.map((p, i) => (
                <tr key={i} style={{ borderTop: '1px solid rgba(55,65,81,0.3)' }}>
                  <td style={{ padding: '0.2rem' }}>{i + 1}</td>
                  {objKeys.map(k => (
                    <td key={k} style={{ padding: '0.2rem', textAlign: 'right', fontFamily: 'monospace' }}>
                      {p.objectives[k].toFixed(3)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </div>
  )
}
