/**
 * ConOpsEditor — Mission Architecture and Concept of Operations.
 *
 * NOT a power budget tool. Shows:
 * 1. Mission architecture diagram (space → ground → user with data interfaces)
 * 2. Mission phases timeline (LEOP → commissioning → nominal → disposal)
 * 3. Operational modes with subsystem activation and data flow
 * 4. Data flow pipeline: instrument → storage → downlink → processing → user
 *
 * Power profiles are in the engineering budgets tab.
 */
import { useState } from 'react'
import { useApplyToDesign } from '../hooks/useApplyToDesign'
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'
import { askText } from './ui/Dialog'

const PHASE_COLORS: Record<string, string> = {
  phase_a: 'var(--cat-2)', phase_b: 'var(--interactive)', phase_c: 'var(--interactive)', phase_d: 'var(--status-caution)',
  leop: 'var(--status-alarm)', commissioning: 'var(--status-caution)', nominal: 'var(--status-ok)', extended: 'var(--interactive)', disposal: 'var(--text-3)',
  phase_e: 'var(--status-ok)', phase_f: 'var(--text-3)',
}


export function ConOpsEditor() {
  const phases = useDesignStore(s => s.missionPhases)
  const setPhases = useDesignStore(s => s.setMissionPhases)
  const modes = useDesignStore(s => s.operationalModes)
  const setModes = useDesignStore(s => s.setOperationalModes)
  const [editingPhase, setEditingPhase] = useState<string | null>(null)
  const [editingMode, setEditingMode] = useState<string | null>(null)
  const [pipelineSteps, setPipelineSteps] = useState<string[]>(['Instrument', 'Onboard Storage', 'Downlink', 'Ground Processing', 'Archive', 'User'])
  const totalDays = phases.reduce((s, p) => s + p.duration_days, 0)
  const [applied, setApplied] = useState(false)

  // Compute duty cycle from modes — payload active fraction
  const payloadModes = modes.filter(m => m.subsystems_active.some(s => s.toLowerCase().includes('payload')))
  const totalModes = modes.length || 1
  const payloadDutyCycle = payloadModes.length / totalModes  // Simplified: equal time per mode
  // Heater mode detection
  const heaterModes = modes.filter(m => m.subsystems_active.some(s => s.toLowerCase().includes('heater') || s.toLowerCase().includes('tcs')))
  const heaterDutyCycle = heaterModes.length / totalModes

  const applyModes = useApplyToDesign({
    events: [
      // Write mode definitions
      ...modes.map(m => ({
        kind: 'conops_edit' as const,
        target_id: `conops.mode.${m.id}`,
        target_kind: 'conops_mode',
        new_value: { name: m.name, subsystems_active: m.subsystems_active, pointing: m.pointing, dataflow: m.dataflow },
      })),
      // Write derived duty cycles that the power agent reads
      { kind: 'parameter_override' as const, target_id: 'payload.0.duty_cycle', new_value: payloadDutyCycle },
      { kind: 'parameter_override' as const, target_id: 'conops.payload_duty_cycle', new_value: payloadDutyCycle },
      { kind: 'parameter_override' as const, target_id: 'conops.heater_duty_cycle', new_value: heaterDutyCycle },
      { kind: 'parameter_override' as const, target_id: 'conops.num_modes', new_value: modes.length },
    ],
    correlation_id: 'conops-editor',
    rationale: 'ConOps operational modes update',
  })
  // Overlap/collision check: warn if phases are too short relative to total
  const overlapWarnings = phases.filter(p => (p.duration_days / totalDays) < 0.02 && p.duration_days > 0)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Concept of Operations</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '1rem' }}>
        How the mission operates: architecture, phases, modes, and data flow.
        Power profiles are in the engineering budgets.
      </p>
      {overlapWarnings.length > 0 && (
        <div style={{ padding: '0.3rem 0.6rem', marginBottom: '0.5rem', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '4px', fontSize: fs.label, color: 'var(--status-caution)' }}>
          ⚠ {overlapWarnings.length} phase{overlapWarnings.length > 1 ? 's' : ''} too short to display clearly: {overlapWarnings.map(p => p.name).join(', ')}. Consider adjusting durations or merging.
        </div>
      )}

      {/* Architecture diagram is shown in the parent (Phase1MissionArch) — not duplicated here */}
      {/* Hide the old static SVG */}
      {false && <div className="card"><div style={{ display: 'none' }}>
        <svg width="100%" height="280" viewBox="0 0 780 280" style={{ background: 'var(--bg-primary, var(--surface-0))', borderRadius: '6px' }}>
          {/* Space Segment */}
          <rect x="250" y="10" width="280" height="70" rx="8" fill="var(--surface-2)" stroke="var(--interactive)" strokeWidth="2"/>
          <text x="390" y="32" textAnchor="middle" fill="var(--interactive)" fontSize={fs.label} fontWeight="600">Space Segment</text>
          {/* Sub-boxes inside space segment */}
          <rect x="260" y="40" width="80" height="30" rx="4" fill="var(--surface-0)" stroke="color-mix(in srgb, var(--interactive) 50%, transparent)" strokeWidth="1"/>
          <text x="300" y="59" textAnchor="middle" fill="var(--interactive)" fontSize={fs.label}>Platform</text>
          <rect x="350" y="40" width="80" height="30" rx="4" fill="var(--surface-0)" stroke="color-mix(in srgb, var(--cat-2) 50%, transparent)" strokeWidth="1"/>
          <text x="390" y="59" textAnchor="middle" fill="var(--cat-2)" fontSize={fs.label}>Payload/Sensor</text>
          <rect x="440" y="40" width="80" height="30" rx="4" fill="var(--surface-0)" stroke="color-mix(in srgb, var(--interactive) 50%, transparent)" strokeWidth="1"/>
          <text x="480" y="59" textAnchor="middle" fill="var(--interactive)" fontSize={fs.label}>Comms (TTC)</text>

          {/* Ground Operations */}
          <rect x="30" y="120" width="150" height="55" rx="8" fill="var(--surface-2)" stroke="var(--status-ok)" strokeWidth="2"/>
          <text x="105" y="140" textAnchor="middle" fill="var(--status-ok)" fontSize={fs.label} fontWeight="600">Ground Operations</text>
          <text x="105" y="153" textAnchor="middle" fill="var(--text-2)" fontSize={fs.label}>GS Antenna + MCC</text>
          <text x="105" y="164" textAnchor="middle" fill="var(--text-3)" fontSize={fs.label}>TM/TC, Commanding</text>

          {/* Payload Processing */}
          <rect x="220" y="120" width="170" height="55" rx="8" fill="var(--surface-2)" stroke="var(--cat-2)" strokeWidth="2"/>
          <text x="305" y="140" textAnchor="middle" fill="var(--cat-2)" fontSize={fs.label} fontWeight="600">Payload Data Centre</text>
          <text x="305" y="153" textAnchor="middle" fill="var(--text-2)" fontSize={fs.label}>Reception + Processing</text>
          <text x="305" y="164" textAnchor="middle" fill="var(--text-3)" fontSize={fs.label}>L0→L1→L2 Pipeline</text>

          {/* End Users */}
          <rect x="560" y="120" width="140" height="55" rx="8" fill="var(--surface-2)" stroke="var(--status-caution)" strokeWidth="2"/>
          <text x="630" y="140" textAnchor="middle" fill="var(--status-caution)" fontSize={fs.label} fontWeight="600">End Users</text>
          <text x="630" y="153" textAnchor="middle" fill="var(--text-2)" fontSize={fs.label}>Data Products</text>
          <text x="630" y="164" textAnchor="middle" fill="var(--text-3)" fontSize={fs.label}>API / Portal / Archive</text>

          {/* Ground Sensors (optional) */}
          <rect x="430" y="120" width="110" height="55" rx="8" fill="var(--surface-2)" stroke="var(--status-caution)" strokeWidth="1.5" strokeDasharray="4 2"/>
          <text x="485" y="140" textAnchor="middle" fill="var(--status-caution)" fontSize={fs.label} fontWeight="600">Ground Sensors</text>
          <text x="485" y="153" textAnchor="middle" fill="var(--text-2)" fontSize={fs.label}>(if applicable)</text>
          <text x="485" y="164" textAnchor="middle" fill="var(--text-3)" fontSize={fs.label}>In-situ / Relay / IoT</text>

          {/* Data flow arrows with direction markers */}
          {/* Space → Ground Ops: TM + Housekeeping (S-band) */}
          <defs>
            <marker id="arrow-down" markerWidth="6" markerHeight="4" refX="3" refY="2" orient="auto">
              <polygon points="0 0, 6 2, 0 4" fill="var(--interactive)"/>
            </marker>
            <marker id="arrow-up" markerWidth="6" markerHeight="4" refX="3" refY="2" orient="auto">
              <polygon points="6 0, 0 2, 6 4" fill="var(--cat-2)"/>
            </marker>
            <marker id="arrow-right" markerWidth="6" markerHeight="4" refX="3" refY="2" orient="auto">
              <polygon points="0 0, 6 2, 0 4" fill="var(--status-caution)"/>
            </marker>
          </defs>
          {/* S-band TM downlink */}
          <line x1="310" y1="80" x2="105" y2="120" stroke="var(--interactive)" strokeWidth="1.5" markerEnd="url(#arrow-down)"/>
          <text x="185" y="96" fill="var(--interactive)" fontSize={fs.label} transform="rotate(-22 185 96)">S-band TM/HK ↓</text>
          {/* S-band TC uplink */}
          <line x1="115" y1="120" x2="320" y2="80" stroke="var(--cat-2)" strokeWidth="1.5" strokeDasharray="3 2" markerEnd="url(#arrow-up)"/>
          <text x="195" y="108" fill="var(--cat-2)" fontSize={fs.label} transform="rotate(-22 195 108)">S-band TC ↑</text>
          {/* X-band science data downlink */}
          <line x1="400" y1="80" x2="305" y2="120" stroke="var(--cat-6)" strokeWidth="2" markerEnd="url(#arrow-down)"/>
          <text x="370" y="100" fill="var(--cat-6)" fontSize={fs.label} transform="rotate(-30 370 100)">X-band Science ↓</text>
          {/* Payload processing → Users */}
          <line x1="390" y1="147" x2="560" y2="147" stroke="var(--status-caution)" strokeWidth="1.5" markerEnd="url(#arrow-right)"/>
          <text x="475" y="142" textAnchor="middle" fill="var(--status-caution)" fontSize={fs.label}>L2/L3 Products (HTTPS)</text>
          {/* Ground ops → payload processing */}
          <line x1="180" y1="155" x2="220" y2="155" stroke="var(--text-3)" strokeWidth="1" markerEnd="url(#arrow-right)"/>
          <text x="200" y="168" textAnchor="middle" fill="var(--text-3)" fontSize={fs.label}>Orbit/TLE</text>
          {/* Ground sensors → processing (if applicable) */}
          <line x1="485" y1="175" x2="370" y2="175" stroke="var(--status-caution)" strokeWidth="1" strokeDasharray="3 2"/>
          <text x="430" y="185" textAnchor="middle" fill="var(--status-caution)" fontSize={fs.label}>Sensor data (IP/radio)</text>

          {/* Legend */}
          <text x="30" y="210" fill="var(--text-3)" fontSize={fs.label} fontWeight="600">LEGEND:</text>
          <line x1="30" y1="222" x2="50" y2="222" stroke="var(--interactive)" strokeWidth="1.5"/>
          <text x="55" y="225" fill="var(--text-3)" fontSize={fs.label}>S-band (TM/TC)</text>
          <line x1="150" y1="222" x2="170" y2="222" stroke="var(--cat-6)" strokeWidth="2"/>
          <text x="175" y="225" fill="var(--text-3)" fontSize={fs.label}>X-band (payload data)</text>
          <line x1="300" y1="222" x2="320" y2="222" stroke="var(--status-caution)" strokeWidth="1.5"/>
          <text x="325" y="225" fill="var(--text-3)" fontSize={fs.label}>Ground network (fibre/IP)</text>
          <line x1="470" y1="222" x2="490" y2="222" stroke="var(--status-caution)" strokeWidth="1" strokeDasharray="3 2"/>
          <text x="495" y="225" fill="var(--text-3)" fontSize={fs.label}>Optional ground sensor link</text>
        </svg>
      </div></div>}

      {/* Mission Phases Timeline */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <h3 style={{ fontSize: fs.value, margin: 0 }}>Mission Phases</h3>
          <span style={{ fontSize: fs.label, color: 'var(--text-2)' }}>Total: {(totalDays / 365).toFixed(1)} years</span>
        </div>
        <div style={{ display: 'flex', height: 28, borderRadius: '4px', overflow: 'hidden', marginBottom: '0.5rem' }}>
          {phases.map(p => {
            const pct = (p.duration_days / totalDays * 100)
            return (
              <div key={p.id} title={`${p.name}: ${p.duration_days} days`}
                style={{ width: `${pct}%`, background: PHASE_COLORS[p.id] || 'var(--line)', display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: pct > 5 ? 0 : 20 }}>
                {pct > 8 && <span style={{ fontSize: fs.label, color: 'white', fontWeight: 600 }}>{p.name}</span>}
              </div>
            )
          })}
        </div>
        {phases.map(p => (
          <div key={p.id} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', padding: '0.3rem 0', borderTop: '1px solid var(--line)', fontSize: fs.label }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: PHASE_COLORS[p.id] || 'var(--line)', flexShrink: 0, marginTop: '0.2rem' }} />
            <div style={{ flex: 1 }}>
              <span style={{ fontWeight: 600 }}>{p.name}</span>
              <span style={{ color: 'var(--text-3)' }}> ({p.duration_days} days)</span>
              {editingPhase === p.id ? (
                <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.2rem' }}>
                  <input className="input" value={p.description}
                    onChange={e => setPhases(phases.map(ph => ph.id === p.id ? { ...ph, description: e.target.value } : ph))}
                    style={{ flex: 1, fontSize: fs.label }} />
                  <input className="input" type="number" value={p.duration_days}
                    onChange={e => setPhases(phases.map(ph => ph.id === p.id ? { ...ph, duration_days: Number(e.target.value) || 1 } : ph))}
                    style={{ width: '60px', fontSize: fs.label }} />
                  <button onClick={() => setEditingPhase(null)} style={{ background: 'none', border: 'none', color: 'var(--status-ok)', cursor: 'pointer', fontSize: fs.label }}>Done</button>
                </div>
              ) : (
                <div style={{ color: 'var(--text-2)', fontSize: fs.label, cursor: 'pointer' }} onClick={() => setEditingPhase(p.id)}>{p.description}</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Operational Modes */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <h3 style={{ fontSize: fs.value, margin: 0 }}>Operational Modes</h3>
          <button className="btn btn-sm" onClick={() => setModes([...modes, { id: `m-${Date.now()}`, name: 'New Mode', description: '', subsystems_active: [], pointing: '', dataflow: '' }])} style={{ fontSize: fs.label }}>+ Add Mode</button>
        </div>
        {modes.map(m => (
          <div key={m.id} style={{ padding: '0.5rem 0.75rem', background: 'var(--bg-primary, var(--surface-0))', borderRadius: '6px', marginBottom: '0.35rem', border: '1px solid var(--line)' }}>
            {editingMode === m.id ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                <input className="input" value={m.name} onChange={e => setModes(modes.map(mm => mm.id === m.id ? { ...mm, name: e.target.value } : mm))} placeholder="Mode name" style={{ fontSize: fs.body, fontWeight: 600 }} />
                <input className="input" value={m.description} onChange={e => setModes(modes.map(mm => mm.id === m.id ? { ...mm, description: e.target.value } : mm))} placeholder="Description" style={{ fontSize: fs.label }} />
                <input className="input" value={m.subsystems_active.join(', ')} onChange={e => setModes(modes.map(mm => mm.id === m.id ? { ...mm, subsystems_active: e.target.value.split(',').map(s => s.trim()) } : mm))} placeholder="Active subsystems (comma-separated)" style={{ fontSize: fs.label }} />
                <div style={{ display: 'flex', gap: '0.3rem' }}>
                  <input className="input" value={m.pointing} onChange={e => setModes(modes.map(mm => mm.id === m.id ? { ...mm, pointing: e.target.value } : mm))} placeholder="Pointing" style={{ flex: 1, fontSize: fs.label }} />
                  <input className="input" value={m.dataflow} onChange={e => setModes(modes.map(mm => mm.id === m.id ? { ...mm, dataflow: e.target.value } : mm))} placeholder="Data flow" style={{ flex: 1, fontSize: fs.label }} />
                </div>
                <button onClick={() => setEditingMode(null)} className="btn btn-sm" style={{ fontSize: fs.label, alignSelf: 'flex-start' }}>Done</button>
              </div>
            ) : (
              <div onClick={() => setEditingMode(m.id)} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ fontWeight: 600, fontSize: fs.body }}>{m.name}</span>
                  <span style={{ flex: 1 }} />
                  <button onClick={e => { e.stopPropagation(); setModes(modes.filter(mm => mm.id !== m.id)) }}
                    style={{ background: 'none', border: 'none', color: 'var(--status-alarm)', cursor: 'pointer', fontSize: fs.label }}>remove</button>
                </div>
                <div style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.15rem' }}>{m.description}</div>
                <div style={{ display: 'flex', gap: '0.75rem', fontSize: fs.label, color: 'var(--text-3)', flexWrap: 'wrap' }}>
                  <span>Active: <span style={{ color: 'var(--text)' }}>{m.subsystems_active.join(', ') || '—'}</span></span>
                  <span>Pointing: <span style={{ color: 'var(--text)' }}>{m.pointing || '—'}</span></span>
                  {m.dataflow && <span>Data: <span style={{ color: 'var(--text)' }}>{m.dataflow}</span></span>}
                </div>
              </div>
            )}
          </div>
        ))}
        <button className="btn" onClick={async () => { await applyModes(); setApplied(true); setTimeout(() => setApplied(false), 2000) }}
          style={{ marginTop: '0.5rem', width: '100%', background: applied ? 'var(--status-ok)' : 'var(--interactive)', fontSize: fs.label }}>
          {applied ? 'Applied — reconverging...' : 'Apply Modes to Design'}
        </button>
      </div>

      {/* Data Flow Pipeline — editable */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <h3 style={{ fontSize: fs.value, margin: 0 }}>Data Flow Pipeline</h3>
          <button className="btn btn-sm" onClick={async () => {
            const step = (await askText('Add pipeline step (e.g., "On-board Compression", "Relay Satellite"):'))
            if (step) setPipelineSteps(prev => [...prev.slice(0, -1), step, prev[prev.length - 1]])
          }} style={{ fontSize: fs.label }}>+ Add Step</button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', flexWrap: 'wrap', fontSize: fs.label }}>
          {pipelineSteps.map((step, i) => (
            <span key={i} style={{ display: 'contents' }}>
              <span style={{
                padding: '0.25rem 0.5rem', background: 'var(--surface-2)',
                border: '1px solid var(--line)', borderRadius: '4px', color: 'var(--text)',
                cursor: 'pointer',
              }} onClick={async () => {
                const newName = (await askText(`Rename step "${step}":`, step))
                if (newName) setPipelineSteps(prev => prev.map((s, j) => j === i ? newName : s))
              }} title="Click to rename">{step}</span>
              {i < pipelineSteps.length - 1 && (
                <span style={{ color: 'var(--text-3)' }}>{'\u2192'}</span>
              )}
            </span>
          ))}
        </div>
        <div style={{ fontSize: fs.label, color: 'var(--text-3)', marginTop: '0.4rem' }}>
          Click a step to rename. Click "+ Add Step" to insert a new stage. End-to-end latency depends on: ground station access, data volume, processing pipeline, and distribution method.
        </div>
      </div>

      {/* Power profile removed — belongs at subsystem level, not mission level */}
    </div>
  )
}

