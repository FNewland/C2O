import { useState } from 'react'
import { useEquipmentSearch } from '../hooks/useSession'

const DOMAINS = [
  { id: 'power', name: 'Power' },
  { id: 'aocs', name: 'AOCS' },
  { id: 'link', name: 'Communications' },
  { id: 'propulsion', name: 'Propulsion' },
]

interface ComponentMatch {
  component: any
  fit_score?: number
  notes?: string[]
}

interface Props {
  studyId: string | null
  onClose: () => void
  onSelect: (category: string, component: any) => void
}

export function EquipmentBrowser({ studyId, onClose, onSelect }: Props) {
  const [domain, setDomain] = useState<string>('power')
  const [sortKey, setSortKey] = useState<'fit' | 'mass' | 'cost' | 'trl'>('fit')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const { data, isLoading, error } = useEquipmentSearch(domain, studyId)

  const categories: Record<string, ComponentMatch[]> = (data as any)?.categories || {}

  const toggleCompare = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else if (next.size < 3) next.add(id)
      return next
    })
  }

  const sortRows = (rows: ComponentMatch[]) => {
    return [...rows].sort((a, b) => {
      const ca: any = a.component || a
      const cb: any = b.component || b
      switch (sortKey) {
        case 'mass': return (ca.mass_kg || 0) - (cb.mass_kg || 0)
        case 'cost': return (ca.cost_keur || 999999) - (cb.cost_keur || 999999)
        case 'trl': return (cb.trl || 0) - (ca.trl || 0)
        default: return (b.fit_score || 0) - (a.fit_score || 0)
      }
    })
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
      zIndex: 9000, display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg-primary, #111827)', border: '1px solid var(--border, #374151)',
        borderRadius: '8px', width: '92%', maxWidth: '1100px', maxHeight: '88vh',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }} onClick={e => e.stopPropagation()}>
        <div style={{
          padding: '0.75rem 1rem', borderBottom: '1px solid var(--border, #374151)',
          display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap',
        }}>
          <h2 style={{ fontSize: '1rem', margin: 0 }}>Equipment Browser</h2>
          <select className="select" value={domain} onChange={e => setDomain(e.target.value)} style={{ width: 'auto' }}>
            {DOMAINS.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)' }}>Sort by:</span>
          {(['fit', 'mass', 'cost', 'trl'] as const).map(k => (
            <button key={k} onClick={() => setSortKey(k)}
              style={{
                background: sortKey === k ? 'var(--accent, #3b82f6)' : 'transparent',
                color: sortKey === k ? 'white' : 'var(--text-secondary, #9ca3af)',
                border: '1px solid var(--border, #374151)', borderRadius: '4px',
                padding: '0.2rem 0.5rem', fontSize: '0.7rem', cursor: 'pointer', textTransform: 'uppercase',
              }}
            >{k}</button>
          ))}
          <div style={{ flex: 1 }} />
          {selectedIds.size > 0 && (
            <span style={{ fontSize: '0.75rem', color: 'var(--accent, #3b82f6)' }}>
              {selectedIds.size} selected for compare
            </span>
          )}
          <button className="btn btn-sm" onClick={onClose}>Close</button>
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
          {isLoading && <div className="loading"><div className="spinner" /> Loading components...</div>}
          {error && <div className="warning-item">Failed to load: {String(error)}</div>}

          {Object.entries(categories).map(([catName, rows]) => (
            <div key={catName} style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '0.85rem', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary, #9ca3af)' }}>
                {catName.replace(/_/g, ' ')} ({rows.length})
              </h3>
              <div style={{ overflow: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-secondary, #1f2937)' }}>
                      <th style={th}>Sel</th>
                      <th style={th}>Name</th>
                      <th style={th}>Manufacturer</th>
                      <th style={th}>Mass (kg)</th>
                      <th style={th}>Power (W)</th>
                      <th style={th}>Cost (kEUR)</th>
                      <th style={th}>TRL</th>
                      <th style={th}>Heritage</th>
                      <th style={th}>Fit</th>
                      <th style={th}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortRows(rows).map(row => {
                      const c = row.component || row
                      const id = c.id || c.name
                      const heritage = Array.isArray(c.heritage_missions) ? c.heritage_missions.join(', ') : ''
                      const isSelected = selectedIds.has(id)
                      return (
                        <tr key={id} style={{
                          background: isSelected ? 'rgba(59,130,246,0.1)' : 'transparent',
                          borderBottom: '1px solid rgba(255,255,255,0.05)',
                        }}>
                          <td style={td}>
                            <input type="checkbox" checked={isSelected} onChange={() => toggleCompare(id)} />
                          </td>
                          <td style={td}>
                            <div style={{ fontWeight: 600 }}>{c.name}</div>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #9ca3af)' }}>{id}</div>
                          </td>
                          <td style={td}>{c.manufacturer || '—'}</td>
                          <td style={tdNum}>{c.mass_kg?.toFixed(3) || '—'}</td>
                          <td style={tdNum}>{c.power_w?.toFixed(1) || '—'}</td>
                          <td style={tdNum}>{c.cost_keur?.toFixed(0) || '—'}</td>
                          <td style={tdNum}>{c.trl || '—'}</td>
                          <td style={{ ...td, fontSize: '0.7rem', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {heritage || '—'}
                          </td>
                          <td style={tdNum}>
                            {row.fit_score !== undefined && (
                              <span style={{
                                display: 'inline-block', padding: '0.1rem 0.4rem',
                                borderRadius: '3px', fontSize: '0.7rem', fontWeight: 600,
                                background: fitColor(row.fit_score, 0.2), color: fitColor(row.fit_score, 1),
                              }}>{(row.fit_score * 100).toFixed(0)}%</span>
                            )}
                          </td>
                          <td style={td}>
                            <button className="btn btn-sm"
                              onClick={() => onSelect(catName, c)}
                              style={{ padding: '0.2rem 0.6rem', fontSize: '0.7rem' }}
                            >Select</button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.4rem 0.6rem', textAlign: 'left', fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-secondary, #9ca3af)', letterSpacing: '0.03em' }
const td: React.CSSProperties = { padding: '0.4rem 0.6rem', verticalAlign: 'top' }
const tdNum: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }

function fitColor(score: number, alpha: number): string {
  if (score > 0.7) return `rgba(16,185,129,${alpha})`
  if (score > 0.4) return `rgba(245,158,11,${alpha})`
  return `rgba(239,68,68,${alpha})`
}
