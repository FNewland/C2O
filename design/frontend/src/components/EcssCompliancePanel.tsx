import { useMemo, useState } from 'react'
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

      {/* DID Document Generator */}
      <DidGenerator studyId={studyId} />

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

const DID_TYPES = [
  { id: 'mrd', name: 'Mission Requirements Document', standard: 'ECSS-E-ST-10C Annex A' },
  { id: 'ts', name: 'Technical Specification', standard: 'ECSS-E-ST-10-06C' },
  { id: 'ird', name: 'Interface Requirements Document', standard: 'ECSS-E-ST-10-24C' },
  { id: 'semp', name: 'SE Management Plan', standard: 'NASA SEH App J / ECSS-M-ST-10C' },
  { id: 'rmp', name: 'Risk Management Plan', standard: 'ECSS-M-ST-80C' },
  { id: 'conops', name: 'Concept of Operations', standard: 'NASA SEH Appendix S' },
  { id: 'test_plan', name: 'Test Plan', standard: 'ECSS-E-ST-10-03C' },
]

function DidGenerator({ studyId }: { studyId: string | null }) {
  const [generating, setGenerating] = useState<string | null>(null)
  const [generatedDoc, setGeneratedDoc] = useState<any>(null)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())

  const generateDid = async (didType: string) => {
    setGenerating(didType)
    setGeneratedDoc(null)
    try {
      const res = await fetch(`/api/ecss/dids/${didType}/generate${studyId ? `?study_id=${studyId}` : ''}`, { method: 'POST' })
      if (res.ok) {
        const doc = await res.json()
        setGeneratedDoc(doc)
        setExpandedSections(new Set())
      }
    } catch {}
    setGenerating(null)
  }

  const toggleSection = (num: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(num)) next.delete(num)
      else next.add(num)
      return next
    })
  }

  return (
    <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border, #374151)', paddingTop: '1rem' }}>
      <h3 style={{ fontSize: '0.95rem', marginBottom: '0.4rem' }}>Document Generator (DIDs)</h3>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Generate ECSS/NASA document templates populated from the current design state.
      </p>

      <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
        {DID_TYPES.map(d => (
          <button key={d.id} className="btn btn-sm" onClick={() => generateDid(d.id)}
            disabled={generating !== null}
            style={{
              fontSize: '0.7rem',
              background: generatedDoc?.document?.toLowerCase().includes(d.name.toLowerCase().split(' ')[0]) ? '#10b981' : undefined,
            }}>
            {generating === d.id ? 'Generating...' : d.name}
          </button>
        ))}
      </div>

      {/* Generated document viewer */}
      {generatedDoc && (
        <div style={{
          padding: '0.75rem', borderRadius: '6px',
          background: 'var(--bg-primary, #0a0e1a)', border: '1px solid var(--border, #374151)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{generatedDoc.document}</span>
            <span style={{ fontSize: '0.68rem', color: '#6b7280', fontFamily: 'monospace' }}>{generatedDoc.standard}</span>
          </div>
          <div style={{ fontSize: '0.68rem', color: '#6b7280', marginBottom: '0.5rem' }}>
            Study: {generatedDoc.study_name} | Phase: {generatedDoc.phase} | Generated: {new Date(generatedDoc.generated).toLocaleString()}
          </div>

          {/* Document outline */}
          {generatedDoc.sections?.map((section: any) => (
            <div key={section.number} style={{ marginBottom: '0.3rem' }}>
              <button onClick={() => toggleSection(section.number)} style={{
                background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left',
                padding: '0.3rem 0.5rem', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '0.3rem',
                color: '#d1d5db', fontSize: '0.82rem', fontWeight: 600,
              }}>
                <span style={{ color: '#6b7280', fontSize: '0.7rem', width: 14 }}>
                  {expandedSections.has(section.number) ? '\u25BC' : '\u25B6'}
                </span>
                {section.number}. {section.title}
              </button>
              {expandedSections.has(section.number) && section.subsections?.map((sub: any) => (
                <div key={sub.number} style={{
                  marginLeft: '1.5rem', padding: '0.3rem 0.5rem', borderLeft: '2px solid #374151',
                  marginBottom: '0.2rem',
                }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 500, color: '#9ca3af' }}>
                    {sub.number} {sub.title}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: '#6b7280', whiteSpace: 'pre-wrap', marginTop: '0.1rem' }}>
                    {sub.content}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
