/**
 * SystemArchitectureEditor -- Select architecture options per subsystem.
 *
 * For each subsystem, shows selectable option cards with mass/power/cost/TRL,
 * pros/cons, and derived requirements. Selection updates the design.
 *
 * Per NASA SEH Process 4 (Design Solution Definition).
 */
import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useSessionStore } from '../stores/sessionStore'

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
  eps: { name: 'Power (EPS)', color: '#f59e0b' },
  aocs: { name: 'AOCS', color: '#06b6d4' },
  ttc: { name: 'Comms (TTC)', color: '#ec4899' },
  thermal: { name: 'Thermal', color: '#ef4444' },
  structure: { name: 'Structure', color: '#84cc16' },
  propulsion: { name: 'Propulsion', color: '#f97316' },
  obc: { name: 'OBC / C&DH', color: '#8b5cf6' },
  ground: { name: 'Ground Segment', color: '#0ea5e9' },
}

// Map positions to their primary subsystem for default view
const POSITION_SUBSYSTEM: Record<string, string> = {
  systems_engineer: 'eps', power_engineer: 'eps', aocs_engineer: 'aocs',
  comms_engineer: 'ttc', thermal_engineer: 'thermal', structures_engineer: 'structure',
  propulsion_engineer: 'propulsion', software_engineer: 'obc',
  ground_segment: 'ground', mission_ops: 'ground',
  payload_lead: 'eps', mission_analyst: 'aocs', cost_engineer: 'eps',
  compliance_engineer: 'ttc', user_representative: 'ground',
}

export function SystemArchitectureEditor() {
  const positionIds = useSessionStore(s => s.positionIds)
  const primaryPos = positionIds?.[0] || 'systems_engineer'
  const [subsystems, setSubsystems] = useState<string[]>([])
  const [activeSubsystem, setActiveSubsystem] = useState<string>(POSITION_SUBSYSTEM[primaryPos] || 'eps')
  const [options, setOptions] = useState<ArchOption[]>([])
  const [selected, setSelected] = useState<Record<string, SelectedArch>>({})
  const [loading, setLoading] = useState(false)
  const markStale = useDesignStore(s => s.markStale)

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
      const data = await res.json()
      setSelected(prev => {
        const next = { ...prev, [activeSubsystem]: data }
        // Push ALL derived requirements from ALL selections to designStore
        const allReqs = Object.entries(next).flatMap(([ss, sel]) =>
          (sel.derived_requirements || []).map((r: any) => ({ ...r, subsystem: ss }))
        )
        useDesignStore.setState({ architectureDerivedReqs: allReqs })
        return next
      })
      markStale('architecture')
    }
  }

  const currentSelection = selected[activeSubsystem]
  const info = SUBSYSTEM_LABELS[activeSubsystem] || { name: activeSubsystem, color: '#6b7280' }
  const selectedCount = Object.keys(selected).length
  const totalCount = subsystems.length
  const totalDerivedReqs = Object.values(selected).reduce((s, sel) => s + (sel.derived_requirements?.length || 0), 0)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>System Architecture</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Select architecture options for each subsystem. Each choice derives system and subsystem requirements.
      </p>

      {/* Progress bar */}
      <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem', marginBottom: '0.75rem', alignItems: 'center' }}>
        <span style={{ color: selectedCount === totalCount ? '#10b981' : '#f59e0b', fontWeight: 600 }}>
          {selectedCount}/{totalCount} subsystems configured
        </span>
        <span style={{ color: '#6b7280' }}>{totalDerivedReqs} requirements derived</span>
        {primaryPos !== 'systems_engineer' && (
          <span style={{ fontSize: '0.68rem', color: '#3b82f6' }}>
            Your subsystem: {SUBSYSTEM_LABELS[POSITION_SUBSYSTEM[primaryPos] || '']?.name || primaryPos}
          </span>
        )}
      </div>

      {/* Subsystem tabs */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {subsystems.map(ss => {
          const ssInfo = SUBSYSTEM_LABELS[ss] || { name: ss, color: '#6b7280' }
          const isActive = activeSubsystem === ss
          const isSelected = !!selected[ss]
          return (
            <button key={ss} onClick={() => setActiveSubsystem(ss)} style={{
              padding: '0.3rem 0.75rem', fontSize: '0.78rem', borderRadius: '4px', cursor: 'pointer',
              background: isActive ? ssInfo.color : 'var(--bg-secondary, #1f2937)',
              color: isActive ? 'white' : '#9ca3af',
              border: `1px solid ${isActive ? ssInfo.color : isSelected ? ssInfo.color + '60' : '#374151'}`,
            }}>
              {ssInfo.name}
              {isSelected && <span style={{ marginLeft: '0.3rem', fontSize: '0.6rem' }}>selected</span>}
            </button>
          )
        })}
      </div>

      {/* Options for active subsystem */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
        {loading && <div style={{ color: '#6b7280' }}>Loading options...</div>}
        {options.map(opt => {
          const isChosen = currentSelection?.option_id === opt.id
          return (
            <div key={opt.id} onClick={() => handleSelect(opt.id)} style={{
              padding: '0.6rem 0.75rem', borderRadius: '6px', cursor: 'pointer',
              background: isChosen ? `${info.color}15` : 'var(--bg-secondary, #1f2937)',
              border: `2px solid ${isChosen ? info.color : '#374151'}`,
              transition: 'all 0.15s',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{opt.name}</span>
                {isChosen && <span style={{ fontSize: '0.65rem', color: info.color, fontWeight: 700 }}>SELECTED</span>}
                <span style={{ flex: 1 }} />
                <span style={{ fontSize: '0.68rem', color: '#6b7280', fontFamily: 'monospace' }}>
                  {opt.mass_kg}kg | {opt.power_w}W | {opt.cost_keur}kEUR | TRL{opt.trl}
                </span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.3rem' }}>{opt.description}</div>
              <div style={{ display: 'flex', gap: '1rem', fontSize: '0.68rem' }}>
                <div>
                  <span style={{ color: '#10b981' }}>Pros: </span>
                  {opt.pros.slice(0, 3).join(', ')}
                </div>
                <div>
                  <span style={{ color: '#ef4444' }}>Cons: </span>
                  {opt.cons.slice(0, 3).join(', ')}
                </div>
              </div>
              <div style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '0.2rem' }}>
                Derives {opt.num_derived_requirements} requirements
                {opt.pointing_deg !== null && ` | Pointing: ${opt.pointing_deg}deg`}
                {opt.data_rate_mbps !== null && ` | Data rate: ${opt.data_rate_mbps} Mbps`}
              </div>
            </div>
          )
        })}
      </div>

      {/* Selected architecture details */}
      {currentSelection && (
        <div className="card" style={{ borderLeft: `3px solid ${info.color}` }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '0.4rem' }}>
            {info.name}: {currentSelection.option_name}
          </h3>

          {/* Block diagram */}
          {currentSelection.blocks.length > 0 && (
            <div style={{ marginBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#9ca3af', marginBottom: '0.3rem' }}>Block Diagram</div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                {currentSelection.blocks.map((block, i) => (
                  <span key={block.id} style={{ display: 'contents' }}>
                    <span style={{
                      padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 500,
                      background: block.type === 'sensor' ? 'rgba(6,182,212,0.15)' :
                        block.type === 'actuator' ? 'rgba(16,185,129,0.15)' :
                        block.type === 'processor' ? 'rgba(59,130,246,0.15)' :
                        block.type === 'source' ? 'rgba(245,158,11,0.15)' :
                        'rgba(107,114,128,0.15)',
                      border: `1px solid ${block.type === 'sensor' ? '#06b6d440' :
                        block.type === 'actuator' ? '#10b98140' :
                        block.type === 'processor' ? '#3b82f640' :
                        block.type === 'source' ? '#f59e0b40' : '#6b728040'}`,
                      color: '#d1d5db',
                    }}>{block.name}</span>
                    {i < currentSelection.blocks.length - 1 && (
                      <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>-></span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Derived requirements */}
          {currentSelection.derived_requirements.length > 0 && (
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#9ca3af', marginBottom: '0.3rem' }}>
                Derived Requirements ({currentSelection.derived_requirements.length})
              </div>
              {currentSelection.derived_requirements.map(req => (
                <div key={req.id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: '0.4rem',
                  padding: '0.2rem 0', fontSize: '0.72rem',
                }}>
                  <span style={{
                    fontSize: '0.6rem', padding: '0.1rem 0.3rem', borderRadius: '3px', flexShrink: 0,
                    background: req.level === 'system' ? 'rgba(59,130,246,0.15)' : 'rgba(6,182,212,0.15)',
                    color: req.level === 'system' ? '#3b82f6' : '#06b6d4',
                    fontWeight: 600, textTransform: 'uppercase',
                  }}>{req.level}</span>
                  <span style={{ fontFamily: 'monospace', color: '#6b7280', fontSize: '0.65rem', flexShrink: 0 }}>{req.id}</span>
                  <span style={{ color: '#d1d5db' }}>{req.text}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
