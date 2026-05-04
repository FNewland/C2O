import { useState, useMemo } from 'react'
import { useEquipmentSearch } from '../hooks/useSession'

// All 15 KB component categories, grouped by domain
const CATEGORIES = [
  // Power
  { id: 'batteries', name: 'Batteries', domain: 'power' },
  { id: 'solar_cells', name: 'Solar Cells', domain: 'power' },
  { id: 'solar_panels', name: 'Solar Panels', domain: 'power' },
  { id: 'eps_boards', name: 'EPS Boards', domain: 'power' },
  // AOCS
  { id: 'reaction_wheels', name: 'Reaction Wheels', domain: 'aocs' },
  { id: 'star_trackers', name: 'Star Trackers', domain: 'aocs' },
  { id: 'sun_sensors', name: 'Sun Sensors', domain: 'aocs' },
  { id: 'magnetorquers', name: 'Magnetorquers', domain: 'aocs' },
  // Communications
  { id: 'transponders', name: 'Transponders', domain: 'link' },
  { id: 'antennas', name: 'Antennas', domain: 'link' },
  { id: 'gps_receivers', name: 'GPS Receivers', domain: 'link' },
  // Propulsion
  { id: 'thrusters', name: 'Thrusters', domain: 'propulsion' },
  // Structure
  { id: 'cubesat_structures', name: 'CubeSat Structures', domain: 'structure' },
  { id: 'deployers', name: 'Deployers', domain: 'structure' },
  // Data handling
  { id: 'obcs', name: 'OBCs', domain: 'data' },
]

const DOMAIN_LABELS: Record<string, string> = {
  power: 'Power', aocs: 'AOCS', link: 'Comms', propulsion: 'Propulsion',
  structure: 'Structure', data: 'Data Handling',
}

const DOMAIN_COLORS: Record<string, string> = {
  power: '#f59e0b', aocs: '#06b6d4', link: '#ec4899', propulsion: '#f97316',
  structure: '#84cc16', data: '#8b5cf6',
}

// Map each KB category to the parameter edits that selecting a component produces.
const SELECTION_EFFECTS: Record<string, { paramId: string; extract: (c: any) => number | null; label: string }[]> = {
  batteries: [
    { paramId: 'power.battery_capacity_wh', extract: c => c.performance?.capacity_wh ?? null, label: 'Battery Capacity' },
    { paramId: 'power.battery_mass_kg', extract: c => c.mass_kg ?? null, label: 'Battery Mass' },
  ],
  solar_cells: [
    { paramId: 'power.sa_power_eol_w', extract: c => c.performance?.power_w ?? null, label: 'SA Power EOL' },
    { paramId: 'power.sa_mass_kg', extract: c => c.mass_kg ?? null, label: 'SA Mass' },
  ],
  solar_panels: [
    { paramId: 'power.sa_power_eol_w', extract: c => c.performance?.power_w ?? null, label: 'SA Power EOL' },
    { paramId: 'power.sa_mass_kg', extract: c => c.mass_kg ?? null, label: 'SA Mass' },
  ],
  eps_boards: [
    { paramId: 'power.eps_mass_kg', extract: c => c.mass_kg ?? null, label: 'EPS Mass' },
    { paramId: 'power.eps_power_w', extract: c => c.power_w ?? null, label: 'EPS Power' },
  ],
  reaction_wheels: [
    { paramId: 'aocs.mass_kg', extract: c => c.mass_kg ? c.mass_kg * 4 : null, label: 'AOCS Mass (4x wheels)' },
    { paramId: 'aocs.wheel_momentum_nms', extract: c => c.performance?.momentum_nms ?? null, label: 'Wheel Momentum' },
  ],
  star_trackers: [
    { paramId: 'aocs.pointing_accuracy_deg', extract: c => c.performance?.accuracy_arcsec ? c.performance.accuracy_arcsec / 3600 : null, label: 'Pointing Accuracy' },
    { paramId: 'aocs.tracker_mass_kg', extract: c => c.mass_kg ?? null, label: 'Star Tracker Mass' },
  ],
  sun_sensors: [
    { paramId: 'aocs.sun_sensor_mass_kg', extract: c => c.mass_kg ?? null, label: 'Sun Sensor Mass' },
  ],
  magnetorquers: [
    { paramId: 'aocs.magnetorquer_mass_kg', extract: c => c.mass_kg ? c.mass_kg * 3 : null, label: 'Magnetorquer Mass (3-axis)' },
  ],
  transponders: [
    { paramId: 'link.ttc_mass_kg', extract: c => c.mass_kg ?? null, label: 'TTC Mass' },
    { paramId: 'link.ttc_power_w', extract: c => c.power_w ?? null, label: 'TTC Power' },
  ],
  antennas: [
    { paramId: 'link.antenna_mass_kg', extract: c => c.mass_kg ?? null, label: 'Antenna Mass' },
  ],
  gps_receivers: [
    { paramId: 'link.gps_mass_kg', extract: c => c.mass_kg ?? null, label: 'GPS Mass' },
    { paramId: 'link.gps_power_w', extract: c => c.power_w ?? null, label: 'GPS Power' },
  ],
  thrusters: [
    { paramId: 'propulsion.isp_s', extract: c => c.performance?.isp_s ?? null, label: 'Isp' },
    { paramId: 'propulsion.total_mass_kg', extract: c => c.mass_kg ?? null, label: 'Thruster Mass' },
  ],
  cubesat_structures: [
    { paramId: 'structure.mass_kg', extract: c => c.mass_kg ?? null, label: 'Structure Mass' },
  ],
  deployers: [
    { paramId: 'structure.deployer_mass_kg', extract: c => c.mass_kg ?? null, label: 'Deployer Mass' },
  ],
  obcs: [
    { paramId: 'data.obc_mass_kg', extract: c => c.mass_kg ?? null, label: 'OBC Mass' },
    { paramId: 'data.obc_power_w', extract: c => c.power_w ?? null, label: 'OBC Power' },
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
  const [compareMode, setCompareMode] = useState(false)
  const [compareIds, setCompareIds] = useState<Set<string>>(new Set())
  const [showCustomForm, setShowCustomForm] = useState(false)
  const [customComp, setCustomComp] = useState({ name: '', manufacturer: '', mass_kg: 0, power_w: 0, cost_keur: 0, trl: 5, notes: '' })

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
  }

  const handleApplyAndClose = () => {
    for (const [category, sel] of selections) {
      onSelect(category, sel.component)
    }
    onClose()
  }

  const toggleCompare = (id: string) => {
    setCompareIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else if (next.size < 3) next.add(id)
      return next
    })
  }

  const handleCustomSubmit = () => {
    const comp = {
      id: `custom-${Date.now()}`,
      ...customComp,
      heritage_missions: [],
      performance: {},
      custom: true,
    }
    handleSelectComponent(activeCategory, comp)
    setShowCustomForm(false)
    setCustomComp({ name: '', manufacturer: '', mass_kg: 0, power_w: 0, cost_keur: 0, trl: 5, notes: '' })
  }

  const selectedInCategory = selections.get(activeCategory)?.component?.id

  // Items for comparison
  const compareItems = useMemo(() => {
    if (!compareMode || compareIds.size === 0) return []
    return activeRows.filter(r => {
      const c = r.component || r
      return compareIds.has(c.id || c.name)
    })
  }, [compareMode, compareIds, activeRows])

  // Group categories by domain for sidebar
  const groupedCategories = useMemo(() => {
    const groups: Record<string, typeof CATEGORIES> = {}
    for (const cat of CATEGORIES) {
      if (!groups[cat.domain]) groups[cat.domain] = []
      groups[cat.domain].push(cat)
    }
    return groups
  }, [])

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
          <span style={{ fontSize: '0.68rem', color: '#6b7280' }}>
            {CATEGORIES.length} categories · {activeRows.length} components
          </span>
          <div style={{ flex: 1 }} />
          <button className="btn btn-sm" onClick={() => { setCompareMode(!compareMode); setCompareIds(new Set()) }}
            style={{ fontSize: '0.7rem', background: compareMode ? '#8b5cf6' : undefined }}>
            {compareMode ? 'Exit Compare' : 'Compare'}
          </button>
          <button className="btn btn-sm" onClick={() => setShowCustomForm(!showCustomForm)}
            style={{ fontSize: '0.7rem', background: showCustomForm ? '#f59e0b' : undefined }}>
            {showCustomForm ? 'Cancel Custom' : 'Design Custom'}
          </button>
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
                {sel.component.custom && <span style={{ fontSize: '0.6rem', color: '#f59e0b' }}>(custom)</span>}
                <button onClick={() => handleDeselectCategory(cat)}
                  style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.8rem', padding: 0, lineHeight: 1 }}>
                  x
                </button>
              </span>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Category sidebar — grouped by domain */}
          <div style={{
            width: '180px', borderRight: '1px solid var(--border, #374151)',
            overflowY: 'auto', flexShrink: 0,
          }}>
            {Object.entries(groupedCategories).map(([domain, cats]) => (
              <div key={domain}>
                <div style={{
                  fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
                  color: DOMAIN_COLORS[domain] || '#6b7280', padding: '0.5rem 0.75rem 0.15rem',
                  letterSpacing: '0.05em',
                }}>{DOMAIN_LABELS[domain] || domain}</div>
                {cats.map(cat => {
                  const isActive = activeCategory === cat.id
                  const hasSelection = selections.has(cat.id)
                  return (
                    <button key={cat.id} onClick={() => setActiveCategory(cat.id)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '0.4rem', width: '100%',
                        padding: '0.4rem 0.75rem', border: 'none', cursor: 'pointer', textAlign: 'left',
                        background: isActive ? 'var(--bg-secondary, #1f2937)' : 'transparent',
                        borderLeft: isActive ? `3px solid ${DOMAIN_COLORS[cat.domain] || '#3b82f6'}` : '3px solid transparent',
                        fontSize: '0.78rem', color: isActive ? '#f3f4f6' : '#9ca3af',
                      }}>
                      {hasSelection && (
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', flexShrink: 0 }} />
                      )}
                      <span>{cat.name}</span>
                    </button>
                  )
                })}
              </div>
            ))}
          </div>

          {/* Component table + custom form + compare view */}
          <div style={{ flex: 1, overflow: 'auto', padding: '0.75rem' }}>
            {/* Custom equipment form */}
            {showCustomForm && (
              <div style={{
                padding: '0.75rem', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)',
                borderRadius: '6px', marginBottom: '0.75rem',
              }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f59e0b', marginBottom: '0.4rem' }}>
                  Design Custom Component — {CATEGORIES.find(c => c.id === activeCategory)?.name}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.4rem', marginBottom: '0.4rem' }}>
                  <div>
                    <label style={formLabel}>Name</label>
                    <input className="input" value={customComp.name} onChange={e => setCustomComp(p => ({ ...p, name: e.target.value }))} placeholder="Custom component name" style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>Manufacturer</label>
                    <input className="input" value={customComp.manufacturer} onChange={e => setCustomComp(p => ({ ...p, manufacturer: e.target.value }))} placeholder="In-house / vendor" style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>TRL</label>
                    <input className="input" type="number" min={1} max={9} value={customComp.trl} onChange={e => setCustomComp(p => ({ ...p, trl: Number(e.target.value) }))} style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>Mass (kg)</label>
                    <input className="input" type="number" step={0.01} value={customComp.mass_kg} onChange={e => setCustomComp(p => ({ ...p, mass_kg: Number(e.target.value) }))} style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>Power (W)</label>
                    <input className="input" type="number" step={0.1} value={customComp.power_w} onChange={e => setCustomComp(p => ({ ...p, power_w: Number(e.target.value) }))} style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>Cost (kEUR)</label>
                    <input className="input" type="number" step={1} value={customComp.cost_keur} onChange={e => setCustomComp(p => ({ ...p, cost_keur: Number(e.target.value) }))} style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                </div>
                <input className="input" value={customComp.notes} onChange={e => setCustomComp(p => ({ ...p, notes: e.target.value }))}
                  placeholder="Notes (interface details, performance specs, rationale...)" style={{ fontSize: '0.72rem', width: '100%', marginBottom: '0.4rem' }} />
                <button className="btn btn-sm" onClick={handleCustomSubmit} disabled={!customComp.name}
                  style={{ background: '#f59e0b', fontSize: '0.72rem' }}>Add Custom to Selection</button>
              </div>
            )}

            {/* Compare view */}
            {compareMode && compareIds.size >= 2 && (
              <div style={{
                padding: '0.75rem', background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.3)',
                borderRadius: '6px', marginBottom: '0.75rem',
              }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#8b5cf6', marginBottom: '0.4rem' }}>
                  Side-by-Side Comparison ({compareIds.size} components)
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                  <thead>
                    <tr style={{ background: 'rgba(139,92,246,0.1)' }}>
                      <th style={th}>Parameter</th>
                      {compareItems.map(r => {
                        const c = r.component || r
                        return <th key={c.id || c.name} style={{ ...th, textAlign: 'center' }}>{c.name}</th>
                      })}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: 'Manufacturer', get: (c: any) => c.manufacturer || '—' },
                      { label: 'Mass (kg)', get: (c: any) => c.mass_kg?.toFixed(3) || '—', best: 'min' },
                      { label: 'Power (W)', get: (c: any) => c.power_w?.toFixed(1) || '—', best: 'min' },
                      { label: 'Cost (kEUR)', get: (c: any) => c.cost_keur?.toFixed(0) || '—', best: 'min' },
                      { label: 'TRL', get: (c: any) => String(c.trl || '—'), best: 'max' },
                      { label: 'Heritage', get: (c: any) => (c.heritage_missions || []).join(', ') || 'None' },
                      { label: 'Fit Score', get: (c: any, r: any) => r.fit_score !== undefined ? `${(r.fit_score * 100).toFixed(0)}%` : '—', best: 'max' },
                    ].map(row => {
                      const values = compareItems.map(r => {
                        const c = r.component || r
                        return { val: row.get(c, r), num: parseFloat(row.get(c, r)) }
                      })
                      const nums = values.map(v => v.num).filter(n => !isNaN(n))
                      const bestVal = row.best === 'min' ? Math.min(...nums) : row.best === 'max' ? Math.max(...nums) : null
                      return (
                        <tr key={row.label} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                          <td style={{ ...td, fontWeight: 600, color: '#9ca3af' }}>{row.label}</td>
                          {values.map((v, i) => (
                            <td key={i} style={{
                              ...td, textAlign: 'center', fontFamily: 'monospace',
                              color: bestVal !== null && v.num === bestVal ? '#10b981' : '#d1d5db',
                              fontWeight: bestVal !== null && v.num === bestVal ? 700 : 400,
                            }}>{v.val}</td>
                          ))}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}

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
              {compareMode && <span style={{ fontSize: '0.68rem', color: '#8b5cf6', marginLeft: '0.5rem' }}>Click rows to compare (max 3)</span>}
            </div>

            {isLoading && <div className="loading"><div className="spinner" /> Loading...</div>}
            {error && <div className="warning-item">Failed to load: {String(error)}</div>}

            {activeRows.length > 0 && (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary, #1f2937)' }}>
                    {compareMode && <th style={th}>Cmp</th>}
                    <th style={th}>Name</th>
                    <th style={th}>Manufacturer</th>
                    <th style={th}>Mass (kg)</th>
                    <th style={th}>Power (W)</th>
                    <th style={th}>Cost (kEUR)</th>
                    <th style={th}>TRL</th>
                    <th style={th}>Heritage</th>
                    <th style={th}>Fit</th>
                    <th style={th}>Req Status</th>
                    <th style={th}></th>
                  </tr>
                </thead>
                <tbody>
                  {sortRows(activeRows).map((row: any) => {
                    const c = row.component || row
                    const id = c.id || c.name
                    const heritage = Array.isArray(c.heritage_missions) ? c.heritage_missions.join(', ') : ''
                    const isChosen = selectedInCategory === id
                    const isComparing = compareIds.has(id)
                    const notes: string[] = row.notes || []
                    const hasGaps = notes.some((n: string) => n.includes('BELOW'))
                    const meetsAll = notes.length > 0 && !hasGaps
                    return (
                      <tr key={id}
                        onClick={compareMode ? () => toggleCompare(id) : undefined}
                        style={{
                          background: isChosen ? 'rgba(16,185,129,0.12)' : isComparing ? 'rgba(139,92,246,0.1)' : 'transparent',
                          borderBottom: '1px solid rgba(255,255,255,0.05)',
                          cursor: compareMode ? 'pointer' : 'default',
                        }}>
                        {compareMode && (
                          <td style={td}>
                            <input type="checkbox" checked={isComparing} readOnly
                              style={{ accentColor: '#8b5cf6' }} />
                          </td>
                        )}
                        <td style={td}>
                          <div style={{ fontWeight: 600 }}>{c.name}</div>
                          <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>{id}</div>
                        </td>
                        <td style={td}>{c.manufacturer || '—'}</td>
                        <td style={tdNum}>{c.mass_kg?.toFixed(3) || '—'}</td>
                        <td style={tdNum}>{c.power_w?.toFixed(1) || '—'}</td>
                        <td style={tdNum}>{c.cost_keur?.toFixed(0) || '—'}</td>
                        <td style={tdNum}>{c.trl || '—'}</td>
                        <td style={{ ...td, fontSize: '0.68rem', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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
                          {hasGaps ? (
                            <span title={notes.filter((n: string) => n.includes('BELOW')).join('\n')}
                              style={{ fontSize: '0.68rem', padding: '0.1rem 0.35rem', borderRadius: '3px', background: 'rgba(239,68,68,0.15)', color: '#ef4444', cursor: 'help' }}>
                              {notes.filter((n: string) => n.includes('BELOW')).length} gap{notes.filter((n: string) => n.includes('BELOW')).length !== 1 ? 's' : ''}
                            </span>
                          ) : meetsAll ? (
                            <span style={{ fontSize: '0.68rem', padding: '0.1rem 0.35rem', borderRadius: '3px', background: 'rgba(16,185,129,0.15)', color: '#10b981' }}>
                              meets
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.68rem', color: '#6b7280' }}>—</span>
                          )}
                        </td>
                        <td style={td}>
                          {!compareMode && (
                            isChosen ? (
                              <span style={{ color: '#10b981', fontWeight: 600, fontSize: '0.72rem' }}>Selected</span>
                            ) : (
                              <button className="btn btn-sm"
                                onClick={() => handleSelectComponent(activeCategory, c)}
                                style={{ padding: '0.18rem 0.55rem', fontSize: '0.7rem' }}
                              >Select</button>
                            )
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
                No components in this category. Try a different domain search or design a custom component.
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

const formLabel: React.CSSProperties = { display: 'block', fontSize: '0.65rem', color: '#9ca3af', marginBottom: '0.15rem', textTransform: 'uppercase', letterSpacing: '0.03em' }
const th: React.CSSProperties = { padding: '0.35rem 0.5rem', textAlign: 'left', fontSize: '0.68rem', textTransform: 'uppercase', color: '#9ca3af', letterSpacing: '0.03em' }
const td: React.CSSProperties = { padding: '0.35rem 0.5rem', verticalAlign: 'top' }
const tdNum: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }

function fitColor(score: number, alpha: number): string {
  if (score > 0.7) return `rgba(16,185,129,${alpha})`
  if (score > 0.4) return `rgba(245,158,11,${alpha})`
  return `rgba(239,68,68,${alpha})`
}
