import { useState } from 'react'
import { useCompliance } from '../hooks/useSession'

const WORST_CASES = [
  { id: 'nominal', name: 'Nominal' },
  { id: 'eol', name: 'End of Life' },
  { id: 'hot', name: 'Hot Case' },
  { id: 'cold', name: 'Cold Case' },
]

const STATUS_COLORS: Record<string, { bg: string; fg: string; label: string }> = {
  compliant: { bg: 'rgba(16,185,129,0.2)', fg: 'var(--success, #10b981)', label: '✓ OK' },
  marginal: { bg: 'rgba(245,158,11,0.2)', fg: 'var(--warning, #f59e0b)', label: '⚠ MARGINAL' },
  non_compliant: { bg: 'rgba(239,68,68,0.2)', fg: 'var(--danger, #ef4444)', label: '✗ FAIL' },
  not_verified: { bg: 'rgba(107,114,128,0.15)', fg: 'var(--text-secondary, #9ca3af)', label: '— N/V' },
}

export function ComplianceMatrix({ studyId }: { studyId: string | null }) {
  const [worstCase, setWorstCase] = useState('nominal')
  const { data, isLoading, error } = useCompliance(studyId, worstCase)

  if (!studyId) {
    return <div style={{ padding: '1rem', color: 'var(--text-secondary, #9ca3af)' }}>Run a design first to see compliance.</div>
  }
  if (isLoading) return <div className="loading"><div className="spinner" /> Verifying...</div>
  if (error) return <div className="warning-item">Failed: {String(error)}</div>

  const d: any = data
  if (!d) return null

  const verifications = d.verifications || []
  const reqs: any[] = d.requirements || []
  const reqMap = Object.fromEntries(reqs.map((r: any) => [r.id, r]))

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Requirement Compliance</h2>

      {/* Summary + worst-case toggle */}
      <div className="card" style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {WORST_CASES.map(wc => (
            <button
              key={wc.id}
              onClick={() => setWorstCase(wc.id)}
              style={{
                background: worstCase === wc.id ? 'var(--accent, #3b82f6)' : 'transparent',
                color: worstCase === wc.id ? 'white' : 'var(--text-secondary, #9ca3af)',
                border: '1px solid var(--border, #374151)', borderRadius: '4px',
                padding: '0.3rem 0.7rem', fontSize: '0.75rem', cursor: 'pointer',
              }}
            >{wc.name}</button>
          ))}
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
          <span><strong style={{ color: 'var(--success, #10b981)' }}>{d.compliant}</strong> compliant</span>
          <span><strong style={{ color: 'var(--warning, #f59e0b)' }}>{d.marginal}</strong> marginal</span>
          <span><strong style={{ color: 'var(--danger, #ef4444)' }}>{d.non_compliant}</strong> non-compliant</span>
          <span>of <strong>{d.total_requirements}</strong> ({d.compliance_percent?.toFixed(0)}%)</span>
        </div>
      </div>

      {/* Matrix table */}
      <div style={{ overflow: 'auto', marginTop: '1rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
          <thead>
            <tr style={{ background: 'var(--bg-secondary, #1f2937)' }}>
              <th style={th}>ID</th>
              <th style={th}>Requirement</th>
              <th style={th}>Position</th>
              <th style={thNum}>Threshold</th>
              <th style={thNum}>Achieved</th>
              <th style={thNum}>Margin</th>
              <th style={th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {verifications.map((v: any) => {
              const req = reqMap[v.requirement_id] || {}
              const s = STATUS_COLORS[v.status] || STATUS_COLORS.not_verified
              return (
                <tr key={v.requirement_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: '0.75rem' }}>{v.requirement_id}</td>
                  <td style={{ ...td, maxWidth: '500px' }}>{v.requirement_text || req.text || ''}</td>
                  <td style={{ ...td, fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)' }}>
                    {(req.position || '').replace(/_/g, ' ')}
                  </td>
                  <td style={tdNum}>
                    {req.operator || ''} {fmtNum(req.threshold)} {req.unit || ''}
                  </td>
                  <td style={tdNum}>{fmtNum(v.achieved_value)}</td>
                  <td style={tdNum}>
                    {v.margin_percent !== null && v.margin_percent !== undefined && (
                      <span style={{ color: s.fg, fontWeight: 600 }}>
                        {v.margin_percent >= 0 ? '+' : ''}{v.margin_percent.toFixed(0)}%
                      </span>
                    )}
                  </td>
                  <td style={td}>
                    <span style={{
                      display: 'inline-block', padding: '0.15rem 0.5rem',
                      borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700,
                      background: s.bg, color: s.fg,
                    }}>{s.label}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.5rem', textAlign: 'left', fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-secondary, #9ca3af)', letterSpacing: '0.03em' }
const thNum: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.4rem 0.5rem', verticalAlign: 'top' }
const tdNum: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }

function fmtNum(v: any): string {
  if (v === null || v === undefined) return '—'
  if (typeof v !== 'number') return String(v)
  if (Math.abs(v) >= 1000) return v.toFixed(0)
  if (Math.abs(v) >= 1) return v.toFixed(2)
  return v.toPrecision(3)
}
