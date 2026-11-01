/**
 * BOMView — Bill of Materials from the element tree.
 *
 * Grouped by subsystem, with maturity colour-coding, export buttons,
 * and SVG summary table. Reads from both element tree and backend endpoint.
 */
import { useState, useMemo } from 'react'
import { useModelStore } from '../stores/modelStore'
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'

const MATURITY_COLORS: Record<string, string> = {
  specified: 'var(--status-ok)',
  selected: 'var(--interactive)',
  estimated: 'var(--status-caution)',
  parametric: 'var(--status-caution)',
  undefined: 'var(--text-3)',
}

const PROCUREMENT_LABELS: Record<string, { label: string; color: string }> = {
  catalogue: { label: 'Catalogue', color: 'var(--status-ok)' },
  identified: { label: 'Identified', color: 'var(--interactive)' },
  tbd: { label: 'TBD', color: 'var(--status-caution)' },
  available: { label: 'Available', color: 'var(--status-ok)' },
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
      const DOMAIN_LABELS: Record<string, string> = {
        power: 'EPS', aocs: 'AOCS', ttc: 'TTC', obc: 'OBC',
        thermal: 'Thermal', structure: 'Structure', propulsion: 'Propulsion',
        payload: 'Payload', ground_rf: 'Ground RF', ground_ops: 'Ground Ops',
      }
      const subsysName = parent?.name || DOMAIN_LABELS[el.subsystem_domain || ''] || 'Unassigned'
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
      <div style={{ padding: '2rem', color: 'var(--text-3)' }}>
        <h3 style={{ fontSize: fs.value, marginBottom: '0.5rem', color: 'var(--text-2)' }}>Bill of Materials</h3>
        <p style={{ fontSize: fs.label, marginBottom: '1rem' }}>
          The BOM is generated from the element tree. To populate it:
        </p>
        <ol style={{ fontSize: fs.label, paddingLeft: '1.2rem', lineHeight: 1.6 }}>
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
        <span style={{ fontSize: fs.label, color: 'var(--text-3)' }}>
          {clientBom.components.length} components across {Object.keys(clientBom.groups).length} subsystems
        </span>
      </div>

      {/* Summary bar */}
      <div style={{
        display: 'flex', gap: '1rem', padding: '0.5rem 0.75rem', marginBottom: '0.75rem',
        background: 'rgba(16,185,129,0.06)', borderRadius: '6px', border: '1px solid rgba(16,185,129,0.15)',
        fontSize: fs.label, flexWrap: 'wrap',
      }}>
        <span>Mass: <strong style={{ color: 'var(--text)', fontFamily: 'monospace' }}>{clientBom.totalMass.toFixed(2)} kg</strong></span>
        <span>Power: <strong style={{ color: 'var(--text)', fontFamily: 'monospace' }}>{clientBom.totalPower.toFixed(1)} W</strong></span>
        <span>Cost: <strong style={{ color: 'var(--text)', fontFamily: 'monospace' }}>{clientBom.totalCost.toFixed(0)} kEUR</strong></span>
        <span>Mean TRL: <strong style={{ color: 'var(--text)', fontFamily: 'monospace' }}>{clientBom.meanTrl.toFixed(1)}</strong></span>
        <span style={{ flex: 1 }} />
        <button className="btn btn-sm" onClick={expandAll} style={{ fontSize: fs.label }}>Expand All</button>
        <button className="btn btn-sm" onClick={collapseAll} style={{ fontSize: fs.label }}>Collapse</button>
        <button className="btn btn-sm" onClick={exportCSV} style={{ fontSize: fs.label, background: 'var(--status-ok)' }}>CSV</button>
        <button className="btn btn-sm" onClick={exportJSON} style={{ fontSize: fs.label, background: 'var(--interactive)' }}>JSON</button>
        {studyId && (
          <button className="btn btn-sm" onClick={() => {
            window.open(`/api/lifecycle/bom/${studyId}?fmt=csv`, '_blank')
          }} style={{ fontSize: fs.label, background: 'var(--cat-2)' }}>.docx</button>
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
              padding: '0.35rem 0.75rem', background: 'var(--bg-secondary, var(--surface-2))',
              border: '1px solid var(--border, var(--line))', borderRadius: '4px',
              cursor: 'pointer', color: 'var(--text)', fontSize: fs.label,
            }}>
              <span style={{ fontSize: fs.label, color: 'var(--text-3)' }}>{expanded ? '▼' : '▶'}</span>
              <span style={{ fontWeight: 600 }}>{subsysName}</span>
              <span style={{ color: 'var(--text-3)', fontSize: fs.label }}>{lines.length} items</span>
              <span style={{ flex: 1 }} />
              <span style={{ fontFamily: 'monospace', fontSize: fs.label, color: 'var(--text-2)' }}>
                {groupMass.toFixed(2)} kg | {groupPower.toFixed(1)} W | {groupCost.toFixed(0)} kEUR
              </span>
            </button>

            {/* Component rows */}
            {expanded && (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label, marginTop: '0.1rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
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
                    const matColor = MATURITY_COLORS[line.maturity] || 'var(--text-3)'
                    const procInfo = PROCUREMENT_LABELS[line.procurement_status] || { label: line.procurement_status, color: 'var(--text-3)' }
                    return (
                      <tr key={line.line} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)' }}>
                        <td style={{ ...td, fontFamily: 'monospace', fontSize: fs.label, color: 'var(--text-3)' }}>{line.item_id}</td>
                        <td style={td}>
                          {line.name}
                          {line.criticality === 'single-point' && (
                            <span style={{ fontSize: fs.label, color: 'var(--status-alarm)', marginLeft: '0.3rem' }} title="Single-point failure">SPF</span>
                          )}
                        </td>
                        <td style={tdR}>{line.quantity}</td>
                        <td style={tdR}>{line.total_mass_kg.toFixed(3)}</td>
                        <td style={tdR}>{line.total_power_w.toFixed(1)}</td>
                        <td style={tdR}>{line.total_cost_keur.toFixed(1)}</td>
                        <td style={tdC}>
                          <span style={{
                            color: line.trl >= 7 ? 'var(--status-ok)' : line.trl >= 5 ? 'var(--status-caution)' : 'var(--status-alarm)',
                            fontWeight: 600,
                          }}>{line.trl || '?'}</span>
                        </td>
                        <td style={{ ...td, fontSize: fs.label, color: 'var(--text-2)' }}>{line.manufacturer || '—'}</td>
                        <td style={{ ...tdC, fontSize: fs.label }}>{line.model_level}</td>
                        <td style={tdC}>
                          <span style={{
                            fontSize: fs.label, padding: '0.05rem 0.3rem', borderRadius: '3px',
                            background: `color-mix(in srgb, ${procInfo.color} 8%, transparent)`, color: procInfo.color,
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
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem', fontSize: fs.label, color: 'var(--text-3)', flexWrap: 'wrap' }}>
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

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-3)', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
