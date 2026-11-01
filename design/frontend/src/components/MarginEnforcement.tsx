/**
 * MarginEnforcement — ECSS margin enforcement display.
 *
 * Shows per-domain margin status vs phase-appropriate ECSS policy.
 */
import { useState, useEffect } from 'react'
import { fs } from '../theme/tokens'

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
    critical: 'var(--status-alarm)', major: 'var(--status-caution)', info: 'var(--status-ok)',
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
        <h3 style={{ fontSize: fs.value, margin: 0 }}>ECSS Margin Enforcement</h3>
        <span style={{
          fontSize: fs.label, padding: '0.1rem 0.4rem', borderRadius: '3px', fontWeight: 700,
          background: compliant ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
          color: compliant ? 'var(--status-ok)' : 'var(--status-alarm)',
        }}>{compliant ? 'COMPLIANT' : 'VIOLATIONS'}</span>
      </div>

      {loading ? (
        <div style={{ fontSize: fs.label, color: 'var(--text-3)' }}>Checking margins...</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
              <th style={th}>Domain</th>
              <th style={th}>Standard</th>
              <th style={thR}>Required</th>
              <th style={thR}>Actual</th>
              <th style={th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {checks.map((c, i) => (
              <tr key={i} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                <td style={{ ...td, fontWeight: 500, textTransform: 'capitalize' }}>{c.domain}</td>
                <td style={{ ...td, fontSize: fs.label, color: 'var(--text-3)', fontFamily: 'monospace' }}>{c.standard}</td>
                <td style={tdR}>{c.required_margin}{c.unit}</td>
                <td style={{ ...tdR, color: severityColor[c.severity] || 'var(--text)', fontWeight: 600 }}>
                  {c.actual_margin}{c.unit}
                </td>
                <td style={td}>
                  <span style={{
                    fontSize: fs.label, padding: '0.1rem 0.35rem', borderRadius: '3px',
                    background: `color-mix(in srgb, ${severityColor[c.severity] || 'var(--text-3)'} 13%, transparent)`,
                    color: severityColor[c.severity] || 'var(--text-3)', fontWeight: 600,
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

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
