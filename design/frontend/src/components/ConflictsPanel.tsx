import { useDesignStore } from '../stores/designStore'

const SEVERITY_STYLES: Record<string, { border: string; bg: string; label: string }> = {
  critical: { border: 'var(--danger)', bg: 'rgba(239,68,68,0.1)', label: 'CRITICAL' },
  major: { border: 'var(--warning)', bg: 'rgba(245,158,11,0.1)', label: 'MAJOR' },
  minor: { border: 'var(--info)', bg: 'rgba(6,182,212,0.1)', label: 'MINOR' },
}

export function ConflictsPanel() {
  const { result } = useDesignStore()
  const conflicts = result?.conflicts || []

  if (!result) return null
  if (conflicts.length === 0) {
    return (
      <div className="card" style={{ borderColor: 'var(--success)' }}>
        <h3 style={{ color: 'var(--success)' }}>No Cross-Domain Conflicts</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          All subsystem designs are compatible. No position conflicts detected.
        </p>
      </div>
    )
  }

  const critical = conflicts.filter((c: any) => c.severity === 'critical').length
  const major = conflicts.filter((c: any) => c.severity === 'major').length
  const minor = conflicts.filter((c: any) => c.severity === 'minor').length

  return (
    <div>
      {/* Summary bar */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
        {critical > 0 && <span className="badge badge-red">{critical} Critical</span>}
        {major > 0 && <span className="badge badge-amber">{major} Major</span>}
        {minor > 0 && <span className="badge" style={{ background: 'rgba(6,182,212,0.2)', color: 'var(--info)' }}>{minor} Minor</span>}
      </div>

      {/* Conflict cards */}
      {conflicts.map((conflict: any) => {
        const style = SEVERITY_STYLES[conflict.severity] || SEVERITY_STYLES.minor
        return (
          <div
            key={conflict.id}
            className="card"
            style={{ borderLeft: `4px solid ${style.border}`, background: style.bg, marginBottom: '0.75rem' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <h3 style={{ fontSize: '0.85rem' }}>{conflict.title}</h3>
              <span className={`badge badge-${conflict.severity === 'critical' ? 'red' : conflict.severity === 'major' ? 'amber' : 'green'}`}>
                {style.label}
              </span>
            </div>

            <p style={{ fontSize: '0.8rem', marginBottom: '0.5rem' }}>{conflict.description}</p>

            {/* Positions involved */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <span><strong>{conflict.position_a?.replace('_', ' ')}</strong>: {conflict.value_a_str}</span>
              <span>↔</span>
              <span><strong>{conflict.position_b?.replace('_', ' ')}</strong>: {conflict.value_b_str}</span>
            </div>

            {/* Resolutions */}
            {conflict.resolutions?.length > 0 && (
              <div style={{ marginTop: '0.5rem' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  SUGGESTED RESOLUTIONS:
                </div>
                {conflict.resolutions.map((res: any, i: number) => (
                  <div key={i} style={{ fontSize: '0.75rem', padding: '0.25rem 0', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                    <strong>{res.position_responsible?.replace('_', ' ')}:</strong> {res.description}
                    {res.estimated_impact && <span style={{ color: 'var(--text-secondary)' }}> — {res.estimated_impact}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
