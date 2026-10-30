/**
 * MarginEnforcement — ECSS margin enforcement display.
 *
 * Shows per-domain margin status vs phase-appropriate ECSS policy.
 */
import { useState, useEffect } from 'react'

interface MarginCheck {
  domain: string; standard: string; parameter: string
  required_margin: number; actual_margin: number; unit: string
  severity: string; message: string
}

export function MarginEnforcement({ studyId }: { studyId: string | null }) {
  const [checks, setChecks] = useState<MarginCheck[]>([])
  const [loading, setLoading] = useState(false)
  const [compliant, setCompliant] = useState(true)

  useEffect(() => {
    if (!studyId) return
    setLoading(true)
    fetch(`/api/ecss/margins/${studyId}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          setChecks(data.checks || [])
          setCompliant(data.compliant)
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [studyId])

  if (!studyId) return null

  const severityColor: Record<string, string> = {
    critical: '#ef4444', major: '#f59e0b', info: '#10b981',
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
        <h3 style={{ fontSize: '0.9rem', margin: 0 }}>ECSS Margin Enforcement</h3>
        <span style={{
          fontSize: '0.65rem', padding: '0.1rem 0.4rem', borderRadius: '3px', fontWeight: 700,
          background: compliant ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
          color: compliant ? '#10b981' : '#ef4444',
        }}>{compliant ? 'COMPLIANT' : 'VIOLATIONS'}</span>
      </div>

      {loading ? (
        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Checking margins...</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
              <th style={th}>Domain</th>
              <th style={th}>Standard</th>
              <th style={thR}>Required</th>
              <th style={thR}>Actual</th>
              <th style={th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {checks.map((c, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ ...td, fontWeight: 500, textTransform: 'capitalize' }}>{c.domain}</td>
                <td style={{ ...td, fontSize: '0.68rem', color: '#6b7280', fontFamily: 'monospace' }}>{c.standard}</td>
                <td style={tdR}>{c.required_margin}{c.unit}</td>
                <td style={{ ...tdR, color: severityColor[c.severity] || '#d1d5db', fontWeight: 600 }}>
                  {c.actual_margin}{c.unit}
                </td>
                <td style={td}>
                  <span style={{
                    fontSize: '0.65rem', padding: '0.1rem 0.35rem', borderRadius: '3px',
                    background: `${severityColor[c.severity] || '#6b7280'}22`,
                    color: severityColor[c.severity] || '#6b7280', fontWeight: 600,
                    textTransform: 'uppercase',
                  }}>{c.severity}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.68rem', color: '#9ca3af', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
