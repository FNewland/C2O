import { useEffect, useMemo, useState } from 'react'
import {
  useOptimizerConfig,
  useOptimizerRun,
  useStartOptimization,
  type DefaultVariable,
} from '../hooks/useOptimizer'

interface Props {
  sessionId: string | null
}

interface VarRow {
  id: string
  enabled: boolean
  lower: number
  upper: number
}

export function OptimizerPanel({ sessionId }: Props) {
  const { data: config, isLoading: cfgLoading } = useOptimizerConfig()
  const start = useStartOptimization()
  const [objective, setObjective] = useState<string>('min_mass')
  const [maxEvals, setMaxEvals] = useState<number>(120)
  const [seed, setSeed] = useState<number>(42)
  const [vars, setVars] = useState<VarRow[]>([])
  const [runId, setRunId] = useState<number | null>(null)

  // Poll the active run — stops once status transitions away from running
  const { data: run } = useOptimizerRun(runId, runId !== null)

  useEffect(() => {
    if (!config) return
    setVars(config.default_variables.map(d => ({
      id: d.id, enabled: false, lower: d.lower, upper: d.upper,
    })))
  }, [config])

  // Seed a sensible default: enable the first 2 variables
  useEffect(() => {
    setVars(rows => {
      if (rows.length === 0 || rows.some(r => r.enabled)) return rows
      return rows.map((r, i) => i < 2 ? { ...r, enabled: true } : r)
    })
  }, [vars.length])

  const enabled = useMemo(() => vars.filter(v => v.enabled), [vars])

  if (!sessionId) {
    return (
      <div style={{ padding: '1rem' }}>
        <p style={{ color: 'var(--text-secondary, #9ca3af)' }}>
          Join a session to run the design optimiser.
        </p>
      </div>
    )
  }

  const handleStart = async () => {
    if (enabled.length === 0) { alert('Select at least one design variable'); return }
    try {
      const res = await start.mutateAsync({
        sessionId,
        objective,
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

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ margin: '0 0 0.75rem 0' }}>Design Optimiser</h2>

      {cfgLoading && <div>Loading config…</div>}

      {config && (
        <>
          {/* Objective + evals */}
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
            disabled={start.isPending || enabled.length === 0 || run?.status === 'running'}
          >
            {start.isPending ? 'Starting…' :
              run?.status === 'running' ? 'Running…' :
              `Run (${enabled.length} vars × ${maxEvals} evals)`}
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

              {/* Best result */}
              {run.best_y !== null && (
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
