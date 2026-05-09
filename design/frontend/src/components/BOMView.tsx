/**
 * BOMView — Bill of Materials from the element tree.
 *
 * Grouped by subsystem, with maturity colour-coding, export buttons,
 * and SVG summary table. Reads from both element tree and backend endpoint.
 */
import { useState, useMemo } from 'react'
import { useModelStore, type MaturityLevel } from '../stores/modelStore'
import { useDesignStore } from '../stores/designStore'

const MATURITY_COLORS: Record<string, string> = {
  specified: '#10b981',
  selected: '#3b82f6',
  estimated: '#f59e0b',
  parametric: '#f97316',
  undefined: '#6b7280',
}

const PROCUREMENT_LABELS: Record<string, { label: string; color: string }> = {
  catalogue: { label: 'Catalogue', color: '#10b981' },
  identified: { label: 'Identified', color: '#3b82f6' },
  tbd: { label: 'TBD', color: '#f59e0b' },
  available: { label: 'Available', color: '#10b981' },
}

interface BOMLine {
  line: number
  item_id: string
  name: string
  subsystem: string
  subsystem_domain: string
  segment: string
  quantity: number
  unit_mass_kg: number
  total_mass_kg: number
  unit_power_w: number
  total_power_w: number
  unit_cost_keur: number
  total_cost_keur: number
  trl: number
  manufacturer: string
  model_level: string
  procurement_status: string
  export_control: string
  lead_time_weeks: number
  criticality: string
  maturity: string
}

export function BOMView() {
  const elements = useModelStore(s => s.elements)
  const getElementMaturity = useModelStore(s => s.getElementMaturity)
  const studyId = useDesignStore(s => s.studyId)
  const missionName = useDesignStore(s => s.requirements?.name) || 'Mission'
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)
  const [bomData, setBomData] = useState<any>(null)

  // Build BOM from element tree (client-side for instant rendering)
  const clientBom = useMemo(() => {
    const components: BOMLine[] = []
    const groups: Record<string, BOMLine[]> = {}
    let lineNum = 0

    const byId = new Map<string, any>()
    for (const el of elements.values()) byId.set(el.id, el)

    for (const el of elements.values()) {
      if (el.element_type !== 'component') continue
      lineNum++
      const parent = byId.get(el.parent_id || '')
      const subsysName = parent?.name || 'Unassigned'
      const domain = el.subsystem_domain || parent?.subsystem_domain || ''
      const maturity = getElementMaturity(el.id)
      const trl = el.trl || 0

      const line: BOMLine = {
        line: lineNum,
        item_id: el.kb_component_id || el.id.slice(0, 12),
        name: el.name,
        subsystem: subsysName,
        subsystem_domain: domain,
        segment: el.segment || 'space',
        quantity: el.quantity || 1,
        unit_mass_kg: el.mass_kg || 0,
        total_mass_kg: (el.mass_kg || 0) * (el.quantity || 1),
        unit_power_w: el.power_avg_w || 0,
        total_power_w: (el.power_avg_w || 0) * (el.quantity || 1),
        unit_cost_keur: el.cost_recurring_keur || 0,
        total_cost_keur: (el.cost_recurring_keur || 0) * (el.quantity || 1),
        trl,
        manufacturer: el.manufacturer || '',
        model_level: trl >= 9 ? 'PFM' : trl >= 7 ? 'QM+FM' : trl >= 5 ? 'EM+QM+FM' : 'TBD',
        procurement_status: el.kb_component_id ? 'catalogue' : el.manufacturer ? 'identified' : 'tbd',
        export_control: 'none',
        lead_time_weeks: trl >= 9 ? 8 : trl >= 7 ? 16 : 26,
        criticality: domain && ['obc', 'power', 'ttc'].includes(domain) && !el.redundancy_type ? 'single-point' : 'standard',
        maturity: maturity.level,
      }
      components.push(line)
      if (!groups[subsysName]) groups[subsysName] = []
      groups[subsysName].push(line)
    }

    const totalMass = components.reduce((s, c) => s + c.total_mass_kg, 0)
    const totalPower = components.reduce((s, c) => s + c.total_power_w, 0)
    const totalCost = components.reduce((s, c) => s + c.total_cost_keur, 0)
    const meanTrl = components.length > 0 ? components.reduce((s, c) => s + c.trl, 0) / components.length : 0

    return { components, groups, totalMass, totalPower, totalCost, meanTrl }
  }, [elements])

  const toggleGroup = (name: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  const expandAll = () => setExpandedGroups(new Set(Object.keys(clientBom.groups)))
  const collapseAll = () => setExpandedGroups(new Set())

  // Export handlers
  const exportCSV = () => {
    const headers = ['Line', 'Item ID', 'Name', 'Subsystem', 'Segment', 'Qty', 'Mass (kg)', 'Power (W)', 'Cost (kEUR)', 'TRL', 'Manufacturer', 'Model Level', 'Procurement', 'Export Control', 'Lead Time (wk)', 'Criticality']
    const rows = clientBom.components.map(c => [
      c.line, c.item_id, c.name, c.subsystem, c.segment, c.quantity,
      c.total_mass_kg.toFixed(3), c.total_power_w.toFixed(1), c.total_cost_keur.toFixed(1),
      c.trl, c.manufacturer, c.model_level, c.procurement_status, c.export_control,
      c.lead_time_weeks, c.criticality,
    ].join(','))
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url
    a.download = `bom-${missionName.replace(/\s+/g, '_')}.csv`
    a.click(); URL.revokeObjectURL(url)
  }

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify({ title: `BOM — ${missionName}`, lines: clientBom.components, groups: clientBom.groups }, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url
    a.download = `bom-${missionName.replace(/\s+/g, '_')}.json`
    a.click(); URL.revokeObjectURL(url)
  }

  if (clientBom.components.length === 0) {
    return (
      <div style={{ padding: '2rem', color: '#6b7280' }}>
        <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: '#9ca3af' }}>Bill of Materials</h3>
        <p style={{ fontSize: '0.78rem', marginBottom: '1rem' }}>
          The BOM is generated from the element tree. To populate it:
        </p>
        <ol style={{ fontSize: '0.72rem', paddingLeft: '1.2rem', lineHeight: 1.6 }}>
          <li>Run a design (Phase 0) to seed the element tree</li>
          <li>Select architecture options (Phase 2) to create subsystems</li>
          <li>Select equipment (Phase 3) to add components</li>
        </ol>
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
        <h2 style={{ margin: 0 }}>Bill of Materials</h2>
        <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>
          {clientBom.components.length} components across {Object.keys(clientBom.groups).length} subsystems
        </span>
      </div>

      {/* Summary bar */}
      <div style={{
        display: 'flex', gap: '1rem', padding: '0.5rem 0.75rem', marginBottom: '0.75rem',
        background: 'rgba(16,185,129,0.06)', borderRadius: '6px', border: '1px solid rgba(16,185,129,0.15)',
        fontSize: '0.75rem', flexWrap: 'wrap',
      }}>
        <span>Mass: <strong style={{ color: '#d1d5db', fontFamily: 'monospace' }}>{clientBom.totalMass.toFixed(2)} kg</strong></span>
        <span>Power: <strong style={{ color: '#d1d5db', fontFamily: 'monospace' }}>{clientBom.totalPower.toFixed(1)} W</strong></span>
        <span>Cost: <strong style={{ color: '#d1d5db', fontFamily: 'monospace' }}>{clientBom.totalCost.toFixed(0)} kEUR</strong></span>
        <span>Mean TRL: <strong style={{ color: '#d1d5db', fontFamily: 'monospace' }}>{clientBom.meanTrl.toFixed(1)}</strong></span>
        <span style={{ flex: 1 }} />
        <button className="btn btn-sm" onClick={expandAll} style={{ fontSize: '0.65rem' }}>Expand All</button>
        <button className="btn btn-sm" onClick={collapseAll} style={{ fontSize: '0.65rem' }}>Collapse</button>
        <button className="btn btn-sm" onClick={exportCSV} style={{ fontSize: '0.65rem', background: '#10b981' }}>CSV</button>
        <button className="btn btn-sm" onClick={exportJSON} style={{ fontSize: '0.65rem', background: '#3b82f6' }}>JSON</button>
        {studyId && (
          <button className="btn btn-sm" onClick={() => {
            window.open(`/api/lifecycle/bom/${studyId}?fmt=csv`, '_blank')
          }} style={{ fontSize: '0.65rem', background: '#8b5cf6' }}>.docx</button>
        )}
      </div>

      {/* Grouped BOM table */}
      {Object.entries(clientBom.groups).map(([subsysName, lines]) => {
        const expanded = expandedGroups.has(subsysName)
        const groupMass = lines.reduce((s, l) => s + l.total_mass_kg, 0)
        const groupPower = lines.reduce((s, l) => s + l.total_power_w, 0)
        const groupCost = lines.reduce((s, l) => s + l.total_cost_keur, 0)

        return (
          <div key={subsysName} style={{ marginBottom: '0.35rem' }}>
            {/* Group header */}
            <button onClick={() => toggleGroup(subsysName)} style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.35rem 0.75rem', background: 'var(--bg-secondary, #1f2937)',
              border: '1px solid var(--border, #374151)', borderRadius: '4px',
              cursor: 'pointer', color: '#d1d5db', fontSize: '0.78rem',
            }}>
              <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>{expanded ? '▼' : '▶'}</span>
              <span style={{ fontWeight: 600 }}>{subsysName}</span>
              <span style={{ color: '#6b7280', fontSize: '0.68rem' }}>{lines.length} items</span>
              <span style={{ flex: 1 }} />
              <span style={{ fontFamily: 'monospace', fontSize: '0.68rem', color: '#9ca3af' }}>
                {groupMass.toFixed(2)} kg | {groupPower.toFixed(1)} W | {groupCost.toFixed(0)} kEUR
              </span>
            </button>

            {/* Component rows */}
            {expanded && (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.7rem', marginTop: '0.1rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                    <th style={th}>Item ID</th>
                    <th style={th}>Name</th>
                    <th style={thR}>Qty</th>
                    <th style={thR}>Mass (kg)</th>
                    <th style={thR}>Power (W)</th>
                    <th style={thR}>Cost (kEUR)</th>
                    <th style={thC}>TRL</th>
                    <th style={th}>Manufacturer</th>
                    <th style={thC}>Model</th>
                    <th style={thC}>Status</th>
                    <th style={thC}>Maturity</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map(line => {
                    const matColor = MATURITY_COLORS[line.maturity] || '#6b7280'
                    const procInfo = PROCUREMENT_LABELS[line.procurement_status] || { label: line.procurement_status, color: '#6b7280' }
                    return (
                      <tr key={line.line} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                        <td style={{ ...td, fontFamily: 'monospace', fontSize: '0.62rem', color: '#6b7280' }}>{line.item_id}</td>
                        <td style={td}>
                          {line.name}
                          {line.criticality === 'single-point' && (
                            <span style={{ fontSize: '0.55rem', color: '#ef4444', marginLeft: '0.3rem' }} title="Single-point failure">SPF</span>
                          )}
                        </td>
                        <td style={tdR}>{line.quantity}</td>
                        <td style={tdR}>{line.total_mass_kg.toFixed(3)}</td>
                        <td style={tdR}>{line.total_power_w.toFixed(1)}</td>
                        <td style={tdR}>{line.total_cost_keur.toFixed(1)}</td>
                        <td style={tdC}>
                          <span style={{
                            color: line.trl >= 7 ? '#10b981' : line.trl >= 5 ? '#f59e0b' : '#ef4444',
                            fontWeight: 600,
                          }}>{line.trl || '?'}</span>
                        </td>
                        <td style={{ ...td, fontSize: '0.65rem', color: '#9ca3af' }}>{line.manufacturer || '—'}</td>
                        <td style={{ ...tdC, fontSize: '0.6rem' }}>{line.model_level}</td>
                        <td style={tdC}>
                          <span style={{
                            fontSize: '0.58rem', padding: '0.05rem 0.3rem', borderRadius: '3px',
                            background: `${procInfo.color}15`, color: procInfo.color,
                          }}>{procInfo.label}</span>
                        </td>
                        <td style={tdC}>
                          <span style={{
                            width: 8, height: 8, borderRadius: '50%', background: matColor,
                            display: 'inline-block',
                          }} title={line.maturity} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        )
      })}

      {/* Maturity legend */}
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem', fontSize: '0.62rem', color: '#6b7280', flexWrap: 'wrap' }}>
        {Object.entries(MATURITY_COLORS).map(([level, color]) => (
          <span key={level} style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
            {level}
          </span>
        ))}
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.6rem', color: '#6b7280', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
