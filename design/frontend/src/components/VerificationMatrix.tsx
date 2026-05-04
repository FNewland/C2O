/**
 * VerificationMatrix — Per-requirement V&V assignment.
 *
 * Each requirement gets: method (A/T/R/I), phase, level, status, responsible.
 * Per ECSS-E-ST-10-02C.
 */
import { useState, useEffect, useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'

interface VVEntry {
  req_id: string
  req_text: string
  domain: string
  method: 'A' | 'T' | 'R' | 'I'  // Analysis, Test, Review, Inspection
  phase: string   // phase_b, phase_c, phase_d
  level: string   // unit, subsystem, system
  status: 'planned' | 'in_progress' | 'complete' | 'waived'
  responsible: string
}

const METHOD_LABELS: Record<string, { label: string; color: string; full: string }> = {
  A: { label: 'A', color: '#3b82f6', full: 'Analysis' },
  T: { label: 'T', color: '#10b981', full: 'Test' },
  R: { label: 'R', color: '#f59e0b', full: 'Review' },
  I: { label: 'I', color: '#8b5cf6', full: 'Inspection' },
}

const STATUS_COLORS: Record<string, string> = {
  planned: '#6b7280', in_progress: '#f59e0b', complete: '#10b981', waived: '#9ca3af',
}

// Default V&V assignments by domain
function defaultMethod(domain: string): 'A' | 'T' | 'R' | 'I' {
  if (['mass', 'power', 'link', 'thermal', 'aocs'].includes(domain)) return 'A'
  if (['structure', 'propulsion'].includes(domain)) return 'T'
  if (['cost', 'systems'].includes(domain)) return 'R'
  return 'A'
}

function defaultPhase(method: string): string {
  if (method === 'T') return 'phase_c'
  if (method === 'I') return 'phase_d'
  return 'phase_b'
}

export function VerificationMatrix({ studyId }: { studyId: string | null }) {
  const result = useDesignStore(s => s.result)
  const [entries, setEntries] = useState<VVEntry[]>([])
  const [filter, setFilter] = useState<string>('all')

  // Generate V&V entries from compliance data
  useEffect(() => {
    if (!studyId) return
    fetch(`/api/engineering/verification?study_id=${studyId}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data?.requirements) return
        const vv: VVEntry[] = data.requirements.map((r: any) => {
          const method = defaultMethod(r.domain || 'systems')
          return {
            req_id: r.id,
            req_text: r.text || '',
            domain: r.domain || 'systems',
            method,
            phase: defaultPhase(method),
            level: r.domain === 'systems' ? 'system' : 'subsystem',
            status: 'planned',
            responsible: r.position || 'systems_engineer',
          }
        })
        setEntries(vv)
      })
      .catch(() => {})
  }, [studyId])

  const updateEntry = (reqId: string, field: string, value: string) => {
    setEntries(prev => prev.map(e => e.req_id === reqId ? { ...e, [field]: value } : e))
  }

  const filtered = filter === 'all' ? entries : entries.filter(e => e.method === filter || e.domain === filter)

  const stats = useMemo(() => ({
    total: entries.length,
    analysis: entries.filter(e => e.method === 'A').length,
    test: entries.filter(e => e.method === 'T').length,
    review: entries.filter(e => e.method === 'R').length,
    inspection: entries.filter(e => e.method === 'I').length,
    complete: entries.filter(e => e.status === 'complete').length,
  }), [entries])

  if (!studyId) {
    return <div style={{ padding: '1rem', color: '#6b7280' }}>Run a design to generate the verification matrix.</div>
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Verification & Validation Matrix</h2>
      <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Per ECSS-E-ST-10-02C. Assign method (ATRI), phase, level, and responsible position per requirement.
      </p>

      {/* Stats */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.75rem', fontSize: '0.75rem', flexWrap: 'wrap' }}>
        <span>{stats.total} requirements</span>
        {Object.entries(METHOD_LABELS).map(([m, info]) => (
          <button key={m} onClick={() => setFilter(filter === m ? 'all' : m)}
            style={{
              background: filter === m ? `${info.color}22` : 'transparent',
              border: `1px solid ${filter === m ? info.color : '#374151'}`,
              color: info.color, borderRadius: '3px', padding: '0.1rem 0.4rem',
              fontSize: '0.72rem', cursor: 'pointer',
            }}>
            {info.full}: {entries.filter(e => e.method === m).length}
          </button>
        ))}
        <span style={{ color: '#10b981' }}>{stats.complete} complete</span>
      </div>

      {/* Matrix table */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
            <th style={th}>ID</th>
            <th style={{ ...th, maxWidth: '300px' }}>Requirement</th>
            <th style={thC}>Method</th>
            <th style={thC}>Phase</th>
            <th style={thC}>Level</th>
            <th style={thC}>Status</th>
            <th style={th}>Responsible</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map(e => (
            <tr key={e.req_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={{ ...td, fontFamily: 'monospace', fontSize: '0.68rem', color: '#6b7280' }}>{e.req_id}</td>
              <td style={{ ...td, maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={e.req_text}>
                {e.req_text}
              </td>
              <td style={tdC}>
                <select className="select" value={e.method} onChange={ev => updateEntry(e.req_id, 'method', ev.target.value)}
                  style={{ fontSize: '0.68rem', width: '45px', textAlign: 'center', color: METHOD_LABELS[e.method]?.color }}>
                  {Object.entries(METHOD_LABELS).map(([m, info]) => (
                    <option key={m} value={m}>{info.label}</option>
                  ))}
                </select>
              </td>
              <td style={tdC}>
                <select className="select" value={e.phase} onChange={ev => updateEntry(e.req_id, 'phase', ev.target.value)}
                  style={{ fontSize: '0.68rem', width: '70px' }}>
                  <option value="phase_a">Phase A</option>
                  <option value="phase_b">Phase B</option>
                  <option value="phase_c">Phase C</option>
                  <option value="phase_d">Phase D</option>
                </select>
              </td>
              <td style={tdC}>
                <select className="select" value={e.level} onChange={ev => updateEntry(e.req_id, 'level', ev.target.value)}
                  style={{ fontSize: '0.68rem', width: '75px' }}>
                  <option value="unit">Unit</option>
                  <option value="subsystem">Subsystem</option>
                  <option value="system">System</option>
                </select>
              </td>
              <td style={tdC}>
                <select className="select" value={e.status} onChange={ev => updateEntry(e.req_id, 'status', ev.target.value)}
                  style={{ fontSize: '0.68rem', width: '80px', color: STATUS_COLORS[e.status] }}>
                  <option value="planned">Planned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="complete">Complete</option>
                  <option value="waived">Waived</option>
                </select>
              </td>
              <td style={{ ...td, fontSize: '0.68rem', color: '#9ca3af' }}>{e.responsible.replace(/_/g, ' ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.62rem', color: '#9ca3af', textTransform: 'uppercase' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
