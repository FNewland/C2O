/**
 * ConvergenceTrace — Line chart showing convergence iterations.
 *
 * Displays how quickly the design loop converges: iterations vs max delta.
 * Updates after each convergence. Useful for debugging oscillation.
 */
import { useState, useEffect } from 'react'
import { useSessionStore } from '../stores/sessionStore'

interface TracePoint {
  iteration: number
  maxDelta: number
  changedParams: number
  timestamp: string
}

export function ConvergenceTrace() {
  const convergence = useSessionStore(s => s.lastConvergence)
  const [history, setHistory] = useState<TracePoint[]>([])

  // Accumulate trace points on convergence changes
  useEffect(() => {
    if (!convergence) return
    const ts = new Date().toISOString().slice(0, 16)
    setHistory(prev => {
      if (prev.length > 0 && prev[prev.length - 1].timestamp === ts) return prev
      const point: TracePoint = {
        iteration: prev.length + 1,
        maxDelta: convergence.cascadeRounds || 0,
        changedParams: convergence.changedParams?.length || 0,
        timestamp: ts,
      }
      return [...prev.slice(-19), point]
    })
  }, [convergence])

  if (!convergence) {
    return (
      <div className="card" style={{ borderLeft: '3px solid #6b7280' }}>
        <h3 style={{ fontSize: '0.85rem', color: '#6b7280' }}>Convergence Trace</h3>
        <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>Run a design to see convergence history.</p>
      </div>
    )
  }

  const maxVal = Math.max(...history.map(h => h.changedParams), 1)

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Convergence Trace</h3>
      <p style={{ fontSize: '0.68rem', color: '#9ca3af', marginBottom: '0.4rem' }}>
        Last: {convergence.cascadeRounds} rounds, {convergence.changedParams?.length || 0} params changed, {convergence.timeMs}ms
      </p>

      {/* Simple bar chart */}
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 60 }}>
        {history.map((h, i) => (
          <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{
              width: '100%', background: h.changedParams > 10 ? '#f59e0b' : '#10b981',
              borderRadius: '2px 2px 0 0',
              height: `${(h.changedParams / maxVal) * 50}px`,
              minHeight: 2,
            }} title={`#${h.iteration}: ${h.changedParams} params, ${h.maxDelta} rounds`} />
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.58rem', color: '#6b7280', marginTop: '0.1rem' }}>
        <span>Oldest</span>
        <span>Latest</span>
      </div>

      {/* Triggered by */}
      {convergence.triggeredBy && (
        <div style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '0.3rem' }}>
          Triggered by: <span style={{ color: '#d1d5db' }}>{convergence.triggeredBy}</span>
        </div>
      )}
    </div>
  )
}
