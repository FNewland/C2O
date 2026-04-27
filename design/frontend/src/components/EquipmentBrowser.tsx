import { useState, useMemo } from 'react'
import { useEquipmentSearch } from '../hooks/useSession'

// All 6 KB component categories
const CATEGORIES = [
  { id: 'batteries', name: 'Batteries', domain: 'power' },
  { id: 'solar_cells', name: 'Solar Cells', domain: 'power' },
  { id: 'reaction_wheels', name: 'Reaction Wheels', domain: 'aocs' },
  { id: 'star_trackers', name: 'Star Trackers', domain: 'aocs' },
  { id: 'transponders', name: 'Transponders', domain: 'link' },
  { id: 'thrusters', name: 'Thrusters', domain: 'propulsion' },
]

// Map each KB category to the parameter edits that selecting a component produces.
// Each entry: { paramId, extractor(component) → value }
// This replaces the old single-param-per-category approach.
const SELECTION_EFFECTS: Record<string, { paramId: string; extract: (c: any) => number | null; label: string }[]> = {
  batteries: [
    { paramId: 'power.battery_capacity_wh', extract: c => c.performance?.capacity_wh ?? null, label: 'Battery Capacity' },
    { paramId: 'power.battery_mass_kg', extract: c => c.mass_kg ?? null, label: 'Battery Mass' },
  ],
  solar_cells: [
    { paramId: 'power.sa_power_eol_w', extract: c => c.performance?.power_w ?? null, label: 'SA Power EOL' },
    { paramId: 'power.sa_mass_kg', extract: c => c.mass_kg ?? null, label: 'SA Mass' },
  ],
  reaction_wheels: [
    { paramId: 'aocs.mass_kg', extract: c => c.mass_kg ? c.mass_kg * 4 : null, label: 'AOCS Mass (4x wheels)' },
    { paramId: 'aocs.wheel_momentum_nms', extract: c => c.performance?.momentum_nms ?? null, label: 'Wheel Momentum' },
  ],
  star_trackers: [
    { paramId: 'aocs.pointing_accuracy_deg', extract: c => c.performance?.accuracy_arcsec ? c.performance.accuracy_arcsec / 3600 : null, label: 'Pointing Accuracy' },
  ],
  transponders: [
    { paramId: 'link.ttc_mass_kg', extract: c => c.mass_kg ?? null, label: 'TTC Mass' },
    { paramId: 'link.ttc_power_w', extract: c => c.power_w ?? null, label: 'TTC Power' },
  ],
  thrusters: [
    { paramId: 'propulsion.isp_s', extract: c => c.performance?.isp_s ?? null, label: 'Isp' },
    { paramId: 'propulsion.total_mass_kg', extract: c => c.mass_kg ?? null, label: 'Thruster Mass' },
  ],
}

interface SelectedEquipment {
  category: string
  component: any
  timestamp: number
}

interface Props {
  studyId: string | null
  onClose: () => void
  onSelect: (category: string, component: any) => void
}

export function EquipmentBrowser({ studyId, onClose, onSelect }: Props) {
  const [activeCategory, setActiveCategory] = useState<string>('batteries')
  const [sortKey, setSortKey] = useState<'fit' | 'mass' | 'cost' | 'trl'>('fit')
  const [selections, setSelections] = useState<Map<string, SelectedEquipment>>(new Map())

  // Load components for the active category's domain
  const activeDomain = CATEGORIES.find(c => c.id === activeCategory)?.domain || 'power'
  const { data, isLoading, error } = useEquipmentSearch(activeDomain, studyId)

  const categories: Record<string, any[]> = (data as any)?.categories || {}
  const activeRows = categories[activeCategory] || []

  const sortRows = (rows: any[]) => {
    return [...rows].sort((a, b) => {
      const ca = a.component || a
      const cb = b.component || b
      switch (sortKey) {
        case 'mass': return (ca.mass_kg || 0) - (cb.mass_kg || 0)
        case 'cost': return (ca.cost_keur || 999999) - (cb.cost_keur || 999999)
        case 'trl': return (cb.trl || 0) - (ca.trl || 0)
        default: return (b.fit_score || 0) - (a.fit_score || 0)
      }
    })
  }

  const handleSelectComponent = (category: string, component: any) => {
    setSelections(prev => {
      const next = new Map(prev)
      next.set(category, { category, component, timestamp: Date.now() })
      return next
    })
  }

  const handleDeselectCategory = (category: string) => {
    setSelections(prev => {
      const next = new Map(prev)
      next.delete(category)
      return next
    })
  }

  const handleApplyAll = () => {
    for (const [category, sel] of selections) {
      onSelect(category, sel.component)
    }
    // Don't close — let user review. They can click Close when done.
  }

  const handleApplyAndClose = () => {
    for (const [category, sel] of selections) {
      onSelect(category, sel.component)
    }
    onClose()
  }

  const selectedInCategory = selections.get(activeCategory)?.component?.id

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
      zIndex: 9000, display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg-primary, #111827)', border: '1px solid var(--border, #374151)',
        borderRadius: '8px', width: '95%', maxWidth: '1200px', maxHeight: '90vh',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={{
          padding: '0.6rem 1rem', borderBottom: '1px solid var(--border, #374151)',
          display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap',
        }}>
          <h2 style={{ fontSize: '1rem', margin: 0 }}>Equipment Browser</h2>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
            {selections.size} of {CATEGORIES.length} selected
          </span>
          {selections.size > 0 && (
            <>
              <button className="btn btn-sm" onClick={handleApplyAll}
                style={{ background: '#10b981', fontSize: '0.75rem' }}>
                Apply {selections.size} Selection{selections.size !== 1 ? 's' : ''}
              </button>
              <button className="btn btn-sm" onClick={handleApplyAndClose}
                style={{ background: '#3b82f6', fontSize: '0.75rem' }}>
                Apply & Close
              </button>
            </>
          )}
          <button className="btn btn-sm" onClick={onClose}>Close</button>
        </div>

        {/* Selected equipment summary bar */}
        {selections.size > 0 && (
          <div style={{
            padding: '0.5rem 1rem', background: 'rgba(16,185,129,0.08)',
            borderBottom: '1px solid var(--border, #374151)',
            display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center',
          }}>
            <span style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 600 }}>Selected:</span>
            {Array.from(selections.entries()).map(([cat, sel]) => (
              <span key={cat} style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)',
                borderRadius: '4px', padding: '0.15rem 0.5rem', fontSize: '0.72rem',
              }}>
                <span style={{ color: '#9ca3af' }}>{cat.replace(/_/g, ' ')}:</span>
                <span style={{ fontWeight: 600, color: '#10b981' }}>{sel.component.name}</span>
                <span style={{ color: '#6b7280', fontSize: '0.65rem' }}>{sel.component.mass_kg?.toFixed(2)} kg</span>
                <button onClick={() => handleDeselectCategory(cat)}
                  style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.8rem', padding: 0, lineHeight: 1 }}>
                  x
                </button>
              </span>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Category sidebar */}
          <div style={{
            width: '180px', borderRight: '1px solid var(--border, #374151)',
            overflowY: 'auto', flexShrink: 0,
          }}>
            {CATEGORIES.map(cat => {
              const isActive = activeCategory === cat.id
              const hasSelection = selections.has(cat.id)
              return (
                <button key={cat.id} onClick={() => setActiveCategory(cat.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '0.4rem', width: '100%',
                    padding: '0.6rem 0.75rem', border: 'none', cursor: 'pointer', textAlign: 'left',
                    background: isActive ? 'var(--bg-secondary, #1f2937)' : 'transparent',
                    borderLeft: isActive ? '3px solid var(--accent, #3b82f6)' : '3px solid transparent',
                    fontSize: '0.8rem', color: isActive ? '#f3f4f6' : '#9ca3af',
                  }}>
                  {hasSelection && (
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', flexShrink: 0 }} />
                  )}
                  <span>{cat.name}</span>
                </button>
              )
            })}
          </div>

          {/* Component table */}
          <div style={{ flex: 1, overflow: 'auto', padding: '0.75rem' }}>
            {/* Sort controls */}
            <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.5rem', alignItems: 'center' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Sort:</span>
              {(['fit', 'mass', 'cost', 'trl'] as const).map(k => (
                <button key={k} onClick={() => setSortKey(k)}
                  style={{
                    background: sortKey === k ? 'var(--accent, #3b82f6)' : 'transparent',
                    color: sortKey === k ? 'white' : '#9ca3af',
                    border: '1px solid var(--border, #374151)', borderRadius: '4px',
                    padding: '0.15rem 0.45rem', fontSize: '0.68rem', cursor: 'pointer', textTransform: 'uppercase',
                  }}
                >{k}</button>
              ))}
            </div>

            {isLoading && <div className="loading"><div className="spinner" /> Loading...</div>}
            {error && <div className="warning-item">Failed to load: {String(error)}</div>}

            {activeRows.length > 0 && (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary, #1f2937)' }}>
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
                  {sortRows(activeRows).map((row: any) => {
                    const c = row.component || row
                    const id = c.id || c.name
                    const heritage = Array.isArray(c.heritage_missions) ? c.heritage_missions.join(', ') : ''
                    const isChosen = selectedInCategory === id
                    return (
                      <tr key={id} style={{
                        background: isChosen ? 'rgba(16,185,129,0.12)' : 'transparent',
                        borderBottom: '1px solid rgba(255,255,255,0.05)',
                      }}>
                        <td style={td}>
                          <div style={{ fontWeight: 600 }}>{c.name}</div>
                          <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>{id}</div>
                        </td>
                        <td style={td}>{c.manufacturer || '—'}</td>
                        <td style={tdNum}>{c.mass_kg?.toFixed(3) || '—'}</td>
                        <td style={tdNum}>{c.power_w?.toFixed(1) || '—'}</td>
                        <td style={tdNum}>{c.cost_keur?.toFixed(0) || '—'}</td>
                        <td style={tdNum}>{c.trl || '—'}</td>
                        <td style={{ ...td, fontSize: '0.68rem', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {heritage || '—'}
                        </td>
                        <td style={tdNum}>
                          {row.fit_score !== undefined && (
                            <span style={{
                              padding: '0.1rem 0.35rem', borderRadius: '3px', fontSize: '0.68rem', fontWeight: 600,
                              background: fitColor(row.fit_score, 0.2), color: fitColor(row.fit_score, 1),
                            }}>{(row.fit_score * 100).toFixed(0)}%</span>
                          )}
                        </td>
                        <td style={td}>
                          {isChosen ? (
                            <span style={{ color: '#10b981', fontWeight: 600, fontSize: '0.72rem' }}>Selected</span>
                          ) : (
                            <button className="btn btn-sm"
                              onClick={() => handleSelectComponent(activeCategory, c)}
                              style={{ padding: '0.18rem 0.55rem', fontSize: '0.7rem' }}
                            >Select</button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}

            {!isLoading && activeRows.length === 0 && (
              <div style={{ color: '#6b7280', fontSize: '0.8rem', padding: '1rem' }}>
                No components in this category. Try a different domain search.
              </div>
            )}

            {/* Show what selecting this component would do */}
            {selections.has(activeCategory) && (
              <div style={{
                marginTop: '0.75rem', padding: '0.5rem 0.75rem', borderRadius: '6px',
                background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
              }}>
                <div style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 600, marginBottom: '0.3rem' }}>
                  Parameters affected by {selections.get(activeCategory)!.component.name}:
                </div>
                {(SELECTION_EFFECTS[activeCategory] || []).map(eff => {
                  const val = eff.extract(selections.get(activeCategory)!.component)
                  return val !== null ? (
                    <div key={eff.paramId} style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
                      <span style={{ fontFamily: 'monospace' }}>{eff.paramId}</span> = <strong style={{ color: '#10b981' }}>{typeof val === 'number' ? val.toFixed(3) : val}</strong>
                      <span style={{ color: '#6b7280' }}> ({eff.label})</span>
                    </div>
                  ) : null
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.35rem 0.5rem', textAlign: 'left', fontSize: '0.68rem', textTransform: 'uppercase', color: '#9ca3af', letterSpacing: '0.03em' }
const td: React.CSSProperties = { padding: '0.35rem 0.5rem', verticalAlign: 'top' }
const tdNum: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }

function fitColor(score: number, alpha: number): string {
  if (score > 0.7) return `rgba(16,185,129,${alpha})`
  if (score > 0.4) return `rgba(245,158,11,${alpha})`
  return `rgba(239,68,68,${alpha})`
}
