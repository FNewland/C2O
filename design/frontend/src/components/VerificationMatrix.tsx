/**
 * VerificationMatrix — Per-requirement V&V assignment.
 *
 * Each requirement gets: method (A/T/R/I), phase, level, status, responsible.
 * Per ECSS-E-ST-10-02C.
 */
import React, { useState, useEffect, useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'

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

  // Generate V&V entries from ALL requirement sources
  const rawGenReqs = useDesignStore(s => s.generatedRequirements)
  const archReqs = useDesignStore(s => s.architectureDerivedReqs)
  const modelElements = useModelStore(s => s.elements)

  useEffect(() => {
    const allReqs: VVEntry[] = []
    const seen = new Set<string>()

    // From generated requirements (all levels)
    const genReqs = Array.isArray(rawGenReqs) ? rawGenReqs : []
    for (const r of genReqs) {
      if (r.status !== 'accepted') continue
      const method = r.verification_method ? r.verification_method[0].toUpperCase() as 'A'|'T'|'R'|'I' : defaultMethod(r.domain || 'systems')
      allReqs.push({
        req_id: r.id, req_text: r.text || '', domain: r.domain || 'systems',
        method, phase: defaultPhase(method),
        level: r.level || (r.req_type === 'mission' ? 'system' : r.req_type === 'subsystem' ? 'unit' : 'subsystem'),
        status: 'planned', responsible: 'systems_engineer',
      })
      seen.add(r.id)
    }

    // From architecture-derived requirements
    if (Array.isArray(archReqs)) {
      for (const r of archReqs) {
        if (seen.has(r.id)) continue
        allReqs.push({
          req_id: r.id, req_text: r.text || '', domain: (r as any).subsystem || 'systems',
          method: defaultMethod((r as any).subsystem || 'systems'),
          phase: 'CDR', level: r.level === 'system' ? 'system' : 'subsystem',
          status: 'planned', responsible: 'systems_engineer',
        })
        seen.add(r.id)
      }
    }

    // SYSTEM-V Item 11: Component-level verification entries from element tree
    // Each component in the tree gets an inspection/test entry
    for (const el of modelElements.values()) {
      if (el.element_type === 'component' && el.kb_component_id) {
        const reqId = `VER-${el.id.slice(0, 8)}`
        if (seen.has(reqId)) continue
        const trl = el.trl || 9
        // Low-TRL components need test; high-TRL need inspection
        const method: 'A'|'T'|'R'|'I' = trl < 6 ? 'T' : 'I'
        allReqs.push({
          req_id: reqId,
          req_text: `Verify ${el.name} (${el.manufacturer || 'unknown'}) meets specification`,
          domain: el.subsystem_domain || 'systems',
          method,
          phase: method === 'T' ? 'phase_c' : 'phase_d',
          level: 'unit',
          status: 'planned',
          responsible: el.owner_position || 'systems_engineer',
        })
        seen.add(reqId)
      }
    }

    // Also try API if studyId available
    if (studyId) {
      fetch(`/api/engineering/verification?study_id=${studyId}`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data?.requirements) {
            for (const r of data.requirements) {
              if (seen.has(r.id)) continue
              allReqs.push({
                req_id: r.id, req_text: r.text || '', domain: r.domain || 'systems',
                method: defaultMethod(r.domain || 'systems'),
                phase: defaultPhase(defaultMethod(r.domain || 'systems')),
                level: r.domain === 'systems' ? 'system' : 'subsystem',
                status: 'planned', responsible: r.position || 'systems_engineer',
              })
            }
          }
          setEntries([...allReqs])
        })
        .catch(() => setEntries([...allReqs]))
    } else {
      setEntries(allReqs)
    }
  }, [studyId, rawGenReqs, archReqs, modelElements])

  const addVVChange = useDesignStore(s => s.addVVChange)
  const vvChangeLog = useDesignStore(s => s.vvChangeLog)
  const [showHistory, setShowHistory] = useState<string | null>(null)

  const updateEntry = (reqId: string, field: string, value: string) => {
    const prev = entries.find(e => e.req_id === reqId)
    if (prev) {
      const oldVal = (prev as any)[field] || ''
      if (oldVal !== value) {
        addVVChange(reqId, field, String(oldVal), value)
      }
    }
    setEntries(prevEntries => prevEntries.map(e => e.req_id === reqId ? { ...e, [field]: value } : e))
  }

  // Save V&V state
  const saveVV = () => {
    const data = { entries, exportedAt: new Date().toISOString(), missionId: useDesignStore.getState().missionId }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url
    a.download = `vv-matrix-${new Date().toISOString().slice(0, 10)}.json`
    a.click(); URL.revokeObjectURL(url)
  }

  // Load V&V state (respects ID immutability — loaded IDs are preserved, never reassigned)
  const loadVV = () => {
    const input = document.createElement('input'); input.type = 'file'; input.accept = '.json'
    input.onchange = (e: any) => {
      const file = e.target.files?.[0]; if (!file) return
      const reader = new FileReader()
      reader.onload = (ev) => {
        try {
          const data = JSON.parse(ev.target?.result as string)
          if (data.entries && Array.isArray(data.entries)) {
            setEntries(data.entries)
          }
        } catch { alert('Invalid V&V file') }
      }
      reader.readAsText(file)
    }
    input.click()
  }

  // Export CSV
  const exportCSV = () => {
    const headers = ['ID', 'Requirement', 'Domain', 'Method', 'Phase', 'Level', 'Status', 'Responsible']
    const rows = entries.map(e => [e.req_id, `"${e.req_text.replace(/"/g, '""')}"`, e.domain, e.method, e.phase, e.level, e.status, e.responsible].join(','))
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'vv-matrix.csv'; a.click(); URL.revokeObjectURL(url)
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

  if (!studyId && !result) {
    return (
      <div style={{ padding: '2rem', color: '#6b7280' }}>
        <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: '#9ca3af' }}>Verification & Validation Matrix</h3>
        <p style={{ fontSize: '0.78rem', marginBottom: '0.75rem' }}>
          The V&V matrix is populated from three sources:
        </p>
        <ol style={{ fontSize: '0.72rem', paddingLeft: '1.2rem', lineHeight: 1.6 }}>
          <li><strong>Generated requirements</strong> — accept requirements in the Requirements Editor (Phase 0/1)</li>
          <li><strong>Architecture-derived requirements</strong> — select architecture options in Phase 2</li>
          <li><strong>Component verification</strong> — select equipment in Phase 3</li>
        </ol>
        <p style={{ fontSize: '0.72rem', marginTop: '0.5rem' }}>
          Run a design first, then accept requirements to start building the matrix.
        </p>
      </div>
    )
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
        <span style={{ flex: 1 }} />
        <button className="btn btn-sm" onClick={saveVV} style={{ fontSize: '0.65rem' }}>Save V&V</button>
        <button className="btn btn-sm" onClick={loadVV} style={{ fontSize: '0.65rem' }}>Load V&V</button>
        <button className="btn btn-sm" onClick={exportCSV} style={{ fontSize: '0.65rem', background: '#10b981' }}>CSV</button>
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
            <th style={thC}>History</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map(e => (
            <React.Fragment key={e.req_id}>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
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
              <td style={tdC}>
                {(() => {
                  const changes = vvChangeLog.filter(c => c.req_id === e.req_id)
                  if (changes.length === 0) return <span style={{ color: '#374151' }}>—</span>
                  return (
                    <button onClick={() => setShowHistory(showHistory === e.req_id ? null : e.req_id)}
                      style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: '0.65rem' }}>
                      {changes.length} change{changes.length !== 1 ? 's' : ''}
                    </button>
                  )
                })()}
              </td>
            </tr>
            {showHistory === e.req_id && (
              <tr>
                <td colSpan={8} style={{ padding: '0.3rem 0.5rem', background: 'rgba(59,130,246,0.05)' }}>
                  <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>
                    {vvChangeLog.filter(c => c.req_id === e.req_id).map((c, i) => (
                      <div key={i} style={{ marginBottom: '0.15rem' }}>
                        <span style={{ color: '#6b7280' }}>{new Date(c.timestamp).toLocaleString()}</span>
                        {' '}<strong>{c.field}</strong>: <span style={{ color: '#ef4444' }}>{c.old_value}</span> → <span style={{ color: '#10b981' }}>{c.new_value}</span>
                      </div>
                    ))}
                  </div>
                </td>
              </tr>
            )}
            </React.Fragment>
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
