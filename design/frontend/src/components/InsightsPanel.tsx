import { useDesignStore } from '../stores/designStore'

export function InsightsPanel() {
  const { result } = useDesignStore()

  if (!result) {
    return (
      <div>
        <h2>Insights</h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          Run a design to see warnings, recommendations, and TRL innovation opportunities.
        </p>
      </div>
    )
  }

  // Extract innovation recommendations
  const innovations = result.recommendations.filter(r => r.includes('[INNOVATION]'))
  const otherRecs = result.recommendations.filter(r => !r.includes('[INNOVATION]'))

  return (
    <div>
      <h2>Design Insights</h2>

      {/* Convergence status */}
      <div className="card">
        <h3>Convergence</h3>
        <div className="param-row">
          <span className="param-name">Status</span>
          <span className={`badge ${result.converged ? 'badge-green' : 'badge-red'}`}>
            {result.converged ? 'Converged' : 'Not Converged'}
          </span>
        </div>
        <div className="param-row">
          <span className="param-name">Iterations</span>
          <span className="param-value">{result.iterations}</span>
        </div>
        <div className="param-row">
          <span className="param-name">Time</span>
          <span className="param-value">{result.total_time_s}s</span>
        </div>
      </div>

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <>
          <h2 style={{ marginTop: '1rem' }}>Warnings ({result.warnings.length})</h2>
          {result.warnings.map((w, i) => (
            <div key={i} className="warning-item">{w}</div>
          ))}
        </>
      )}

      {/* TRL Innovations */}
      {innovations.length > 0 && (
        <>
          <h2 style={{ marginTop: '1rem' }}>Innovation Opportunities</h2>
          {innovations.map((r, i) => (
            <div key={i} className="recommendation-item">
              {r.replace('[INNOVATION] ', '')}
            </div>
          ))}
        </>
      )}

      {/* Other recommendations */}
      {otherRecs.length > 0 && (
        <>
          <h2 style={{ marginTop: '1rem' }}>Recommendations</h2>
          {otherRecs.map((r, i) => (
            <div key={i} className="recommendation-item">{r}</div>
          ))}
        </>
      )}
    </div>
  )
}
