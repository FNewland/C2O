/**
 * SystemArchitectureEditor -- Select architecture options per subsystem.
 *
 * For each subsystem, shows selectable option cards with mass/power/cost/TRL,
 * pros/cons, and derived requirements. Selection creates real child elements
 * in the element tree (single source of truth).
 *
 * Per NASA SEH Process 4 (Design Solution Definition).
 */
import { useState, useEffect, useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useSessionStore } from '../stores/sessionStore'
import { useModelStore } from '../stores/modelStore'
import { fs } from '../theme/tokens'

interface ArchOption {
  id: string; name: string; description: string
  mass_kg: number; power_w: number; cost_keur: number; trl: number
  pointing_deg: number | null; data_rate_mbps: number | null
  pros: string[]; cons: string[]
  num_derived_requirements: number
}

interface SelectedArch {
  option_id: string; option_name: string; description: string
  mass_kg: number; power_w: number; cost_keur: number; trl: number
  derived_requirements: { id: string; level: string; text: string }[]
  blocks: { id: string; name: string; type: string }[]
  connections: { from: string; to: string; label: string }[]
}

const SUBSYSTEM_LABELS: Record<string, { name: string; color: string }> = {
  eps: { name: 'Power (EPS)', color: 'var(--status-caution)' },
  aocs: { name: 'AOCS', color: 'var(--interactive)' },
  ttc: { name: 'Comms (TTC)', color: 'var(--cat-6)' },
  thermal: { name: 'Thermal', color: 'var(--status-alarm)' },
  structure: { name: 'Structure', color: 'var(--cat-7)' },
  propulsion: { name: 'Propulsion', color: 'var(--status-caution)' },
  obc: { name: 'OBC / C&DH', color: 'var(--cat-2)' },
  ground: { name: 'Ground Segment', color: 'var(--interactive)' },
}

const POSITION_SUBSYSTEM: Record<string, string> = {
  systems_engineer: 'eps', power_engineer: 'eps', aocs_engineer: 'aocs',
  comms_engineer: 'ttc', thermal_engineer: 'thermal', structures_engineer: 'structure',
  propulsion_engineer: 'propulsion', software_engineer: 'obc',
  ground_segment: 'ground', mission_ops: 'ground',
  payload_lead: 'eps', mission_analyst: 'aocs', cost_engineer: 'eps',
  compliance_engineer: 'ttc', user_representative: 'ground',
}

export function SystemArchitectureEditor({ segment = 'space' }: { segment?: string }) {
  const modelCreateElement = useModelStore(s => s.createElement)
  const modelElements = useModelStore(s => s.elements)
  const positionIds = useSessionStore(s => s.positionIds)
  const primaryPos = positionIds?.[0] || 'systems_engineer'
  const [subsystems, setSubsystems] = useState<string[]>([])
  const [activeSubsystem, setActiveSubsystem] = useState<string>(POSITION_SUBSYSTEM[primaryPos] || 'eps')
  const [options, setOptions] = useState<ArchOption[]>([])
  // Track selections in local state — element tree is the source of truth for the actual elements
  const [selected, setSelected] = useState<Record<string, SelectedArch>>({})
  const [loading, setLoading] = useState(false)
  const [showCustomForm, setShowCustomForm] = useState(false)
  const [customName, setCustomName] = useState('')
  const [customDesc, setCustomDesc] = useState('')
  const [customMass, setCustomMass] = useState(0)
  const [customPower, setCustomPower] = useState(0)
  const [customCost, setCustomCost] = useState(0)
  const [customTrl, setCustomTrl] = useState(5)
  const markStale = useDesignStore(s => s.markStale)

  // Derive which subsystems have elements from the tree (shows as "configured")
  const configuredSubsystems = useMemo(() => {
    const configured = new Set<string>()
    for (const el of modelElements.values()) {
      if (el.element_type === 'subsystem' && el.subsystem_domain && el.segment === segment) {
        configured.add(el.subsystem_domain)
      }
    }
    return configured
  }, [modelElements, segment])

  // Load subsystem list
  useEffect(() => {
    fetch('/api/lifecycle/architecture/subsystems')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.subsystems) setSubsystems(d.subsystems) })
      .catch(() => {})
  }, [])

  // Load options for active subsystem
  useEffect(() => {
    if (!activeSubsystem) return
    setLoading(true)
    fetch(`/api/lifecycle/architecture/options/${activeSubsystem}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.options) setOptions(d.options) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [activeSubsystem])

  const handleSelect = async (optionId: string) => {
    const res = await fetch('/api/lifecycle/architecture/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subsystem: activeSubsystem, option_id: optionId }),
    })
    if (res.ok) {
      const data: SelectedArch = await res.json()
      setSelected(prev => ({ ...prev, [activeSubsystem]: data }))

      // Write architecture mass/power/cost to parameterOverrides so budgets update
      const setParam = useDesignStore.getState().setParameter
      if (data.mass_kg) setParam(`${activeSubsystem}.mass_kg`, data.mass_kg, 'architecture')
      if (data.power_w) setParam(`${activeSubsystem}.power_w`, data.power_w, 'architecture')
      if (data.cost_keur) setParam(`${activeSubsystem}.cost_keur`, data.cost_keur, 'architecture')

      // Create or update subsystem element in the element tree
      const sid = useDesignStore.getState().studyId
      if (sid) {
        // Find parent system element
        let parentId: string | undefined
        for (const el of modelElements.values()) {
          if (el.element_type === 'system' && el.segment === segment) {
            parentId = el.id
            break
          }
        }
        // If no system element, try segment
        if (!parentId) {
          for (const el of modelElements.values()) {
            if (el.element_type === 'segment' && el.segment === segment) {
              parentId = el.id
              break
            }
          }
        }

        // Check if subsystem element already exists
        const updateElement = useModelStore.getState().updateElement
        let existingSubsystemId: string | undefined
        for (const el of modelElements.values()) {
          if (el.element_type === 'subsystem' && el.subsystem_domain === activeSubsystem && el.segment === segment) {
            existingSubsystemId = el.id
            break
          }
        }

        if (existingSubsystemId) {
          // Update existing subsystem
          updateElement(existingSubsystemId, {
            name: data.option_name || activeSubsystem,
            mass_kg: data.mass_kg || null,
            power_avg_w: data.power_w || null,
            cost_recurring_keur: data.cost_keur || null,
            trl: data.trl || null,
            performance: { preset_id: optionId, preset_name: data.option_name },
          })
          // Create block children if they don't exist
          if (data.blocks?.length) {
            for (const block of data.blocks) {
              const exists = Array.from(modelElements.values()).some(
                el => el.parent_id === existingSubsystemId && el.name === block.name
              )
              if (!exists) {
                modelCreateElement(sid, {
                  name: block.name,
                  element_type: 'logical',
                  subsystem_domain: activeSubsystem,
                  segment: segment,
                  parent_id: existingSubsystemId,
                  description: `Architecture block from ${data.option_name} option`,
                } as any)
              }
            }
          }
        } else {
          // Create new subsystem element + block children
          const newSubId = await modelCreateElement(sid, {
            name: data.option_name || activeSubsystem,
            element_type: 'subsystem',
            subsystem_domain: activeSubsystem,
            segment: segment,
            parent_id: parentId || null,
            mass_kg: data.mass_kg || null,
            power_avg_w: data.power_w || null,
            cost_recurring_keur: data.cost_keur || null,
            trl: data.trl || null,
            performance: { preset_id: optionId, preset_name: data.option_name },
          } as any)
          if (newSubId && data.blocks?.length) {
            for (const block of data.blocks) {
              await modelCreateElement(sid, {
                name: block.name,
                element_type: 'logical',
                subsystem_domain: activeSubsystem,
                segment: segment,
                parent_id: newSubId,
                description: `Architecture block from ${data.option_name} option`,
              } as any)
            }
          }
        }
      }

      markStale('architecture')
    }
  }

  const addCustomOption = async () => {
    if (!customName) return
    const customOpt: ArchOption = {
      id: `custom-${activeSubsystem}-${Date.now()}`,
      name: customName, description: customDesc,
      mass_kg: customMass, power_w: customPower, cost_keur: customCost, trl: customTrl,
      pointing_deg: null, data_rate_mbps: null,
      pros: ['User-defined'], cons: ['No auto-derived requirements'],
      num_derived_requirements: 0,
    }
    setOptions(prev => [...prev, customOpt])
    setShowCustomForm(false)

    const sel: SelectedArch = {
      option_id: customOpt.id, option_name: customOpt.name, description: customOpt.description,
      mass_kg: customOpt.mass_kg, power_w: customOpt.power_w, cost_keur: customOpt.cost_keur, trl: customOpt.trl,
      derived_requirements: [], blocks: [], connections: [],
    }
    setSelected(prev => ({ ...prev, [activeSubsystem]: sel }))

    // Write to parameterOverrides
    const setParam = useDesignStore.getState().setParameter
    setParam(`${activeSubsystem}.mass_kg`, customMass, 'architecture')
    setParam(`${activeSubsystem}.power_w`, customPower, 'architecture')
    setParam(`${activeSubsystem}.cost_keur`, customCost, 'architecture')

    // Create subsystem element in tree
    const sid = useDesignStore.getState().studyId
    if (sid) {
      let parentId: string | undefined
      for (const el of modelElements.values()) {
        if ((el.element_type === 'system' || el.element_type === 'segment') && el.segment === segment) {
          parentId = el.id
          break
        }
      }
      await modelCreateElement(sid, {
        name: customName,
        element_type: 'subsystem',
        subsystem_domain: activeSubsystem,
        segment: segment,
        parent_id: parentId || null,
        mass_kg: customMass || null,
        power_avg_w: customPower || null,
        cost_recurring_keur: customCost || null,
        trl: customTrl || null,
        performance: { preset_id: customOpt.id, preset_name: customName },
      } as any)
    }

    setCustomName(''); setCustomDesc(''); setCustomMass(0); setCustomPower(0); setCustomCost(0); setCustomTrl(5)
    markStale('architecture')
  }

  const currentSelection = selected[activeSubsystem]
  const info = SUBSYSTEM_LABELS[activeSubsystem] || { name: activeSubsystem, color: 'var(--text-3)' }
  const selectedCount = configuredSubsystems.size
  const totalCount = subsystems.length

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>System Architecture</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.5rem' }}>
        Select architecture options for each subsystem. Each choice creates subsystem elements in the design tree.
      </p>

      {/* Progress bar */}
      <div style={{ display: 'flex', gap: '0.75rem', fontSize: fs.label, marginBottom: '0.75rem', alignItems: 'center' }}>
        <span style={{ color: selectedCount === totalCount ? 'var(--status-ok)' : 'var(--status-caution)', fontWeight: 600 }}>
          {selectedCount}/{totalCount} subsystems configured
        </span>
        {primaryPos !== 'systems_engineer' && (
          <span style={{ fontSize: fs.label, color: 'var(--interactive)' }}>
            Your subsystem: {SUBSYSTEM_LABELS[POSITION_SUBSYSTEM[primaryPos] || '']?.name || primaryPos}
          </span>
        )}
      </div>

      {/* Subsystem tabs */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {subsystems.filter(ss => segment === 'ground' ? ss === 'ground' : ss !== 'ground').map(ss => {
          const ssInfo = SUBSYSTEM_LABELS[ss] || { name: ss, color: 'var(--text-3)' }
          const isActive = activeSubsystem === ss
          const isConfigured = configuredSubsystems.has(ss) || !!selected[ss]
          return (
            <button key={ss} onClick={() => setActiveSubsystem(ss)} style={{
              padding: '0.3rem 0.75rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
              background: isActive ? ssInfo.color : 'var(--bg-secondary, var(--surface-2))',
              color: isActive ? 'white' : 'var(--text-2)',
              border: `1px solid ${isActive ? ssInfo.color : isConfigured ? `color-mix(in srgb, ${ssInfo.color} 38%, transparent)` : 'var(--line)'}`,
            }}>
              {ssInfo.name}
              {isConfigured && <span style={{ marginLeft: '0.3rem', fontSize: fs.label }}>configured</span>}
            </button>
          )
        })}
      </div>

      {/* Options for active subsystem */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
        {loading && <div style={{ color: 'var(--text-3)' }}>Loading options...</div>}
        {options.map(opt => {
          const isChosen = currentSelection?.option_id === opt.id
          return (
            <div key={opt.id} onClick={() => handleSelect(opt.id)} style={{
              padding: '0.6rem 0.75rem', borderRadius: '6px', cursor: 'pointer',
              background: isChosen ? `color-mix(in srgb, ${info.color} 8%, transparent)` : 'var(--bg-secondary, var(--surface-2))',
              border: `2px solid ${isChosen ? info.color : 'var(--line)'}`,
              transition: 'all 0.15s',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                <span style={{ fontWeight: 700, fontSize: fs.body }}>{opt.name}</span>
                {isChosen && <span style={{ fontSize: fs.label, color: info.color, fontWeight: 700 }}>SELECTED</span>}
                <span style={{ flex: 1 }} />
                <span style={{ fontSize: fs.label, color: 'var(--text-3)', fontFamily: 'monospace' }}>
                  {opt.mass_kg}kg | {opt.power_w}W | {opt.cost_keur}kEUR | TRL{opt.trl}
                </span>
              </div>
              <div style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.3rem' }}>{opt.description}</div>
              <div style={{ display: 'flex', gap: '1rem', fontSize: fs.label }}>
                <div>
                  <span style={{ color: 'var(--status-ok)' }}>Pros: </span>
                  {opt.pros.slice(0, 3).join(', ')}
                </div>
                <div>
                  <span style={{ color: 'var(--status-alarm)' }}>Cons: </span>
                  {opt.cons.slice(0, 3).join(', ')}
                </div>
              </div>
              <div style={{ fontSize: fs.label, color: 'var(--text-3)', marginTop: '0.2rem' }}>
                Derives {opt.num_derived_requirements} requirements
                {opt.pointing_deg !== null && ` | Pointing: ${opt.pointing_deg}deg`}
                {opt.data_rate_mbps !== null && ` | Data rate: ${opt.data_rate_mbps} Mbps`}
              </div>
            </div>
          )
        })}
      </div>

      {/* Custom option */}
      {!showCustomForm ? (
        <button onClick={() => setShowCustomForm(true)} className="btn btn-sm"
          style={{ marginBottom: '0.75rem', fontSize: fs.label, background: 'var(--line)' }}>
          + Define Custom Option
        </button>
      ) : (
        <div className="card" style={{ marginBottom: '0.75rem', borderLeft: `3px solid ${info.color}` }}>
          <h4 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>Custom {info.name} Option</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', marginBottom: '0.4rem' }}>
            <label style={{ fontSize: fs.label, color: 'var(--text-2)' }}>Name:
              <input className="input" value={customName} onChange={e => setCustomName(e.target.value)}
                style={{ width: '100%', fontSize: fs.label }} placeholder="e.g., Custom AOCS" />
            </label>
            <label style={{ fontSize: fs.label, color: 'var(--text-2)' }}>TRL:
              <input className="input" type="number" min={1} max={9} value={customTrl} onChange={e => setCustomTrl(Number(e.target.value))}
                style={{ width: '100%', fontSize: fs.label }} />
            </label>
            <label style={{ fontSize: fs.label, color: 'var(--text-2)' }}>Mass (kg):
              <input className="input" type="number" step={0.1} value={customMass} onChange={e => setCustomMass(Number(e.target.value))}
                style={{ width: '100%', fontSize: fs.label }} />
            </label>
            <label style={{ fontSize: fs.label, color: 'var(--text-2)' }}>Power (W):
              <input className="input" type="number" step={0.1} value={customPower} onChange={e => setCustomPower(Number(e.target.value))}
                style={{ width: '100%', fontSize: fs.label }} />
            </label>
            <label style={{ fontSize: fs.label, color: 'var(--text-2)' }}>Cost (kEUR):
              <input className="input" type="number" step={1} value={customCost} onChange={e => setCustomCost(Number(e.target.value))}
                style={{ width: '100%', fontSize: fs.label }} />
            </label>
          </div>
          <label style={{ fontSize: fs.label, color: 'var(--text-2)', display: 'block', marginBottom: '0.4rem' }}>Description:
            <input className="input" value={customDesc} onChange={e => setCustomDesc(e.target.value)}
              style={{ width: '100%', fontSize: fs.label }} placeholder="Brief description of the architecture option" />
          </label>
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            <button onClick={addCustomOption} className="btn btn-sm" style={{ fontSize: fs.label, background: 'var(--status-ok)' }}>Add & Select</button>
            <button onClick={() => setShowCustomForm(false)} className="btn btn-sm" style={{ fontSize: fs.label, background: 'var(--line)' }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Selected architecture details */}
      {currentSelection && (
        <div className="card" style={{ borderLeft: `3px solid ${info.color}` }}>
          <h3 style={{ fontSize: fs.value, marginBottom: '0.4rem' }}>
            {info.name}: {currentSelection.option_name}
          </h3>

          {/* Block diagram */}
          {currentSelection.blocks.length > 0 && (
            <div style={{ marginBottom: '0.5rem' }}>
              <div style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--text-2)', marginBottom: '0.3rem' }}>Block Diagram</div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                {currentSelection.blocks.map((block, i) => (
                  <span key={block.id} style={{ display: 'contents' }}>
                    <span style={{
                      padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: fs.label, fontWeight: 500,
                      background: block.type === 'sensor' ? 'rgba(6,182,212,0.15)' :
                        block.type === 'actuator' ? 'rgba(16,185,129,0.15)' :
                        block.type === 'processor' ? 'rgba(59,130,246,0.15)' :
                        block.type === 'source' ? 'rgba(245,158,11,0.15)' :
                        'rgba(107,114,128,0.15)',
                      border: `1px solid ${block.type === 'sensor' ? 'color-mix(in srgb, var(--interactive) 25%, transparent)' :
                        block.type === 'actuator' ? 'color-mix(in srgb, var(--status-ok) 25%, transparent)' :
                        block.type === 'processor' ? 'color-mix(in srgb, var(--interactive) 25%, transparent)' :
                        block.type === 'source' ? 'color-mix(in srgb, var(--status-caution) 25%, transparent)' : 'color-mix(in srgb, var(--text-3) 25%, transparent)'}`,
                      color: 'var(--text)',
                    }}>{block.name}</span>
                    {i < currentSelection.blocks.length - 1 && (
                      <span style={{ color: 'var(--text-3)', fontSize: fs.body }}>{'->'}</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Derived requirements */}
          {currentSelection.derived_requirements.length > 0 && (
            <div>
              <div style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--text-2)', marginBottom: '0.3rem' }}>
                Derived Requirements ({currentSelection.derived_requirements.length})
              </div>
              {currentSelection.derived_requirements.map((req: any) => {
                const typeColors: Record<string, string> = {
                  performance: 'var(--status-ok)', interface: 'var(--status-caution)', budget: 'var(--interactive)', functional: 'var(--cat-2)',
                }
                const typeColor = typeColors[req.type] || 'var(--text-3)'
                return (
                  <div key={req.id} style={{
                    display: 'flex', alignItems: 'flex-start', gap: '0.3rem',
                    padding: '0.2rem 0', fontSize: fs.label,
                  }}>
                    <span style={{
                      fontSize: fs.label, padding: '0.1rem 0.25rem', borderRadius: '3px', flexShrink: 0,
                      background: req.level === 'system' ? 'rgba(59,130,246,0.15)' : 'rgba(6,182,212,0.15)',
                      color: req.level === 'system' ? 'var(--interactive)' : 'var(--interactive)',
                      fontWeight: 600, textTransform: 'uppercase',
                    }}>{req.level}</span>
                    {req.type && (
                      <span style={{
                        fontSize: fs.label, padding: '0.1rem 0.25rem', borderRadius: '3px', flexShrink: 0,
                        background: `color-mix(in srgb, ${typeColor} 13%, transparent)`, color: typeColor, fontWeight: 600,
                      }}>{req.type}</span>
                    )}
                    <span style={{ fontFamily: 'monospace', color: 'var(--text-3)', fontSize: fs.label, flexShrink: 0 }}>{req.id}</span>
                    <span style={{ color: 'var(--text)', flex: 1 }}>{req.text}</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
