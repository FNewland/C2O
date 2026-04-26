import { useMemo } from 'react'
import { useEcssCompliance, type DrdEntry } from '../hooks/useTemplates'

interface Props {
  studyId: string | null
}

const STATUS_META: Record<DrdEntry['produced_by'], { label: string; color: string; icon: string }> = {
  spacecdf: { label: 'Auto-produced', color: '#10b981', icon: '✓' },
  partial:  { label: 'Partial',       color: '#f59e0b', icon: '◐' },
  planned:  { label: 'Planned',       color: '#6366f1', icon: '…' },
  external: { label: 'External',      color: '#6b7280', icon: '↗' },
}

export function EcssCompliancePanel({ studyId }: Props) {
  const { data, isLoading, error } = useEcssCompliance(studyId)

  const grouped = useMemo(() => {
    if (!data?.drds) return {}
    const out: Record<string, DrdEntry[]> = {}
    data.drds.forEach(d => {
      out[d.produced_by] = out[d.produced_by] || []
      out[d.produced_by].push(d)
    })
    return out
  }, [data])

  if (!studyId) {
    return (
      <div style={{ padding: '1rem' }}>
        <p style={{ color: 'var(--text-secondary, #9ca3af)' }}>
          Create or load a study to see its ECSS review-gate compliance status.
        </p>
      </div>
    )
  }

  if (isLoading) return <div style={{ padding: '1rem' }}>Loading ECSS compliance…</div>
  if (error) return (
    <div style={{ padding: '1rem', color: 'var(--danger, #f87171)' }}>
      Failed to load: {String(error)}
    </div>
  )
  if (!data) return null

  const order: Array<DrdEntry['produced_by']> = ['spacecdf', 'partial', 'planned', 'external']

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ marginBottom: '0.75rem' }}>
        <h2 style={{ margin: 0 }}>
          ECSS Review Gate — {data.gate}
        </h2>
        <div style={{ color: 'var(--text-secondary, #9ca3af)', fontSize: '0.85rem' }}>
          {data.gate_name} · {data.phase.toUpperCase().replace('_', ' ')}
        </div>
      </div>

      <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary, #d1d5db)', marginTop: 0 }}>
        {data.description}
      </p>

      {/* Coverage bar */}
      <div style={{ margin: '1rem 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.3rem' }}>
          <span>SpaceCDF coverage of expected DRDs</span>
          <strong>{data.coverage_percent}%</strong>
        </div>
        <div style={{
          height: '8px',
          borderRadius: '4px',
          background: 'var(--bg-secondary, #1f2937)',
          overflow: 'hidden',
          position: 'relative',
        }}>
          <div style={{
            height: '100%',
            width: `${data.coverage_percent}%`,
            background: data.coverage_percent > 60 ? '#10b981' :
                        data.coverage_percent > 30 ? '#f59e0b' : '#ef4444',
            transition: 'width 0.3s ease',
          }} />
        </div>
        <div style={{
          display: 'flex',
          gap: '0.75rem',
          fontSize: '0.72rem',
          color: 'var(--text-secondary, #9ca3af)',
          marginTop: '0.4rem',
        }}>
          <span>✓ {data.produced} auto</span>
          <span>◐ {data.partial} partial</span>
          <span>… {data.planned} planned</span>
          <span>↗ {data.external} external</span>
          <span style={{ marginLeft: 'auto' }}>Total: {data.total}</span>
        </div>
      </div>

      {/* Grouped DRD list */}
      {order.map(status => {
        const items = grouped[status] || []
        if (items.length === 0) return null
        const meta = STATUS_META[status]
        return (
          <div key={status} style={{ marginBottom: '1rem' }}>
            <h4 style={{ margin: '0.75rem 0 0.4rem 0', color: meta.color }}>
              {meta.icon} {meta.label} ({items.length})
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {items.map(d => (
                <div
                  key={d.id}
                  style={{
                    background: 'var(--bg-secondary, #1f2937)',
                    border: '1px solid var(--border, #374151)',
                    borderLeft: `3px solid ${meta.color}`,
                    borderRadius: '4px',
                    padding: '0.5rem 0.7rem',
                    fontSize: '0.82rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem' }}>
                    <strong>{d.name}</strong>
                    <span style={{
                      fontFamily: 'monospace',
                      fontSize: '0.7rem',
                      color: 'var(--text-secondary, #9ca3af)',
                    }}>
                      {d.id}
                    </span>
                  </div>
                  <div style={{
                    fontSize: '0.72rem',
                    color: 'var(--text-secondary, #9ca3af)',
                    marginTop: '0.2rem',
                    fontFamily: 'monospace',
                  }}>
                    {d.standard} · Annex {d.annex}
                  </div>
                  {d.spacecdf_source && (
                    <div style={{ fontSize: '0.75rem', marginTop: '0.3rem', color: 'var(--text-secondary, #d1d5db)' }}>
                      <em>Source:</em> {d.spacecdf_source}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )
      })}

      <div style={{
        marginTop: '1.5rem',
        padding: '0.6rem',
        fontSize: '0.7rem',
        color: 'var(--text-secondary, #9ca3af)',
        borderTop: '1px solid var(--border, #374151)',
      }}>
        Expected DRDs per ECSS-E-ST-10C Rev.1 Annex A (Table A-1, informative) +
        ECSS-M-ST-10C Rev.1 phase/review structure. Tailoring per ECSS-S-ST-00-02
        may reduce the set for CubeSat / small-mission projects.
      </div>
    </div>
  )
}
