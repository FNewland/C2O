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

const PHASE_COLORS: Record<string, string> = {
  leop: '#ef4444', commissioning: '#f59e0b', nominal: '#10b981', extended: '#3b82f6', disposal: '#6b7280',
}

interface MissionPhase {
  id: string; name: string; duration_days: number; description: string
}

interface OperationalMode {
  id: string; name: string; description: string
  subsystems_active: string[]; pointing: string; dataflow: string
}

const DEFAULT_PHASES: MissionPhase[] = [
  { id: 'leop', name: 'LEOP', duration_days: 3, description: 'Launch, deployment, first contact, initial checkout' },
  { id: 'commissioning', name: 'Commissioning', duration_days: 30, description: 'Subsystem checkout, calibration, first light' },
  { id: 'nominal', name: 'Nominal Operations', duration_days: 900, description: 'Primary science/service data collection and delivery' },
  { id: 'disposal', name: 'Disposal', duration_days: 14, description: 'Passivation, deorbit, final telemetry' },
]

const DEFAULT_MODES: OperationalMode[] = [
  { id: 'safe', name: 'Safe Mode', description: 'Minimum power survival. Entered on anomaly. Sun-pointing, no payload.',
    subsystems_active: ['EPS', 'OBC', 'TTC (beacon)', 'AOCS (coarse)'], pointing: 'Sun-pointing', dataflow: 'Beacon only → ground' },
  { id: 'science', name: 'Science / Imaging', description: 'Primary data acquisition. Payload active, nadir-pointing.',
    subsystems_active: ['EPS', 'OBC', 'Payload', 'AOCS (fine)', 'OBDH'], pointing: 'Nadir (target)', dataflow: 'Instrument → OBDH storage' },
  { id: 'downlink', name: 'Downlink', description: 'Ground station pass. TX active, data download.',
    subsystems_active: ['EPS', 'OBC', 'TTC (full)', 'OBDH'], pointing: 'Ground station', dataflow: 'OBDH → TX → GS → processing → user' },
  { id: 'eclipse', name: 'Eclipse', description: 'Battery-powered. Reduced operations, heaters active.',
    subsystems_active: ['EPS (battery)', 'OBC', 'TCS (heaters)', 'AOCS (coarse)'], pointing: 'Inertial hold', dataflow: 'None' },
]

export function ConOpsEditor() {
  const [phases, setPhases] = useState<MissionPhase[]>(DEFAULT_PHASES)
  const [modes, setModes] = useState<OperationalMode[]>(DEFAULT_MODES)
  const [editingPhase, setEditingPhase] = useState<string | null>(null)
  const [editingMode, setEditingMode] = useState<string | null>(null)
  const totalDays = phases.reduce((s, p) => s + p.duration_days, 0)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Concept of Operations</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '1rem' }}>
        How the mission operates: architecture, phases, modes, and data flow.
        Power profiles are in the engineering budgets.
      </p>

      {/* Mission Architecture Diagram */}
      <div className="card">
        <h3 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Mission Architecture</h3>
        <svg width="100%" height="280" viewBox="0 0 780 280" style={{ background: 'var(--bg-primary, #0a0e1a)', borderRadius: '6px' }}>
          {/* Space Segment */}
          <rect x="250" y="10" width="280" height="70" rx="8" fill="#1f2937" stroke="#3b82f6" strokeWidth="2"/>
          <text x="390" y="32" textAnchor="middle" fill="#3b82f6" fontSize="12" fontWeight="600">Space Segment</text>
          {/* Sub-boxes inside space segment */}
          <rect x="260" y="40" width="80" height="30" rx="4" fill="#0f172a" stroke="#3b82f680" strokeWidth="1"/>
          <text x="300" y="59" textAnchor="middle" fill="#93c5fd" fontSize="8">Platform</text>
          <rect x="350" y="40" width="80" height="30" rx="4" fill="#0f172a" stroke="#8b5cf680" strokeWidth="1"/>
          <text x="390" y="59" textAnchor="middle" fill="#a78bfa" fontSize="8">Payload/Sensor</text>
          <rect x="440" y="40" width="80" height="30" rx="4" fill="#0f172a" stroke="#06b6d480" strokeWidth="1"/>
          <text x="480" y="59" textAnchor="middle" fill="#67e8f9" fontSize="8">Comms (TTC)</text>

          {/* Ground Operations */}
          <rect x="30" y="120" width="150" height="55" rx="8" fill="#1f2937" stroke="#10b981" strokeWidth="2"/>
          <text x="105" y="140" textAnchor="middle" fill="#10b981" fontSize="10" fontWeight="600">Ground Operations</text>
          <text x="105" y="153" textAnchor="middle" fill="#9ca3af" fontSize="8">GS Antenna + MCC</text>
          <text x="105" y="164" textAnchor="middle" fill="#6b7280" fontSize="7">TM/TC, Commanding</text>

          {/* Payload Processing */}
          <rect x="220" y="120" width="170" height="55" rx="8" fill="#1f2937" stroke="#8b5cf6" strokeWidth="2"/>
          <text x="305" y="140" textAnchor="middle" fill="#8b5cf6" fontSize="10" fontWeight="600">Payload Data Centre</text>
          <text x="305" y="153" textAnchor="middle" fill="#9ca3af" fontSize="8">Reception + Processing</text>
          <text x="305" y="164" textAnchor="middle" fill="#6b7280" fontSize="7">L0→L1→L2 Pipeline</text>

          {/* End Users */}
          <rect x="560" y="120" width="140" height="55" rx="8" fill="#1f2937" stroke="#f59e0b" strokeWidth="2"/>
          <text x="630" y="140" textAnchor="middle" fill="#f59e0b" fontSize="10" fontWeight="600">End Users</text>
          <text x="630" y="153" textAnchor="middle" fill="#9ca3af" fontSize="8">Data Products</text>
          <text x="630" y="164" textAnchor="middle" fill="#6b7280" fontSize="7">API / Portal / Archive</text>

          {/* Ground Sensors (optional) */}
          <rect x="430" y="120" width="110" height="55" rx="8" fill="#1f2937" stroke="#f97316" strokeWidth="1.5" strokeDasharray="4 2"/>
          <text x="485" y="140" textAnchor="middle" fill="#f97316" fontSize="9" fontWeight="600">Ground Sensors</text>
          <text x="485" y="153" textAnchor="middle" fill="#9ca3af" fontSize="7">(if applicable)</text>
          <text x="485" y="164" textAnchor="middle" fill="#6b7280" fontSize="7">In-situ / Relay / IoT</text>

          {/* Data flow arrows with direction markers */}
          {/* Space → Ground Ops: TM + Housekeeping (S-band) */}
          <defs>
            <marker id="arrow-down" markerWidth="6" markerHeight="4" refX="3" refY="2" orient="auto">
              <polygon points="0 0, 6 2, 0 4" fill="#06b6d4"/>
            </marker>
            <marker id="arrow-up" markerWidth="6" markerHeight="4" refX="3" refY="2" orient="auto">
              <polygon points="6 0, 0 2, 6 4" fill="#8b5cf6"/>
            </marker>
            <marker id="arrow-right" markerWidth="6" markerHeight="4" refX="3" refY="2" orient="auto">
              <polygon points="0 0, 6 2, 0 4" fill="#f59e0b"/>
            </marker>
          </defs>
          {/* S-band TM downlink */}
          <line x1="310" y1="80" x2="105" y2="120" stroke="#06b6d4" strokeWidth="1.5" markerEnd="url(#arrow-down)"/>
          <text x="185" y="96" fill="#06b6d4" fontSize="7" transform="rotate(-22 185 96)">S-band TM/HK ↓</text>
          {/* S-band TC uplink */}
          <line x1="115" y1="120" x2="320" y2="80" stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="3 2" markerEnd="url(#arrow-up)"/>
          <text x="195" y="108" fill="#8b5cf6" fontSize="7" transform="rotate(-22 195 108)">S-band TC ↑</text>
          {/* X-band science data downlink */}
          <line x1="400" y1="80" x2="305" y2="120" stroke="#ec4899" strokeWidth="2" markerEnd="url(#arrow-down)"/>
          <text x="370" y="100" fill="#ec4899" fontSize="7" transform="rotate(-30 370 100)">X-band Science ↓</text>
          {/* Payload processing → Users */}
          <line x1="390" y1="147" x2="560" y2="147" stroke="#f59e0b" strokeWidth="1.5" markerEnd="url(#arrow-right)"/>
          <text x="475" y="142" textAnchor="middle" fill="#f59e0b" fontSize="7">L2/L3 Products (HTTPS)</text>
          {/* Ground ops → payload processing */}
          <line x1="180" y1="155" x2="220" y2="155" stroke="#6b7280" strokeWidth="1" markerEnd="url(#arrow-right)"/>
          <text x="200" y="168" textAnchor="middle" fill="#6b7280" fontSize="6">Orbit/TLE</text>
          {/* Ground sensors → processing (if applicable) */}
          <line x1="485" y1="175" x2="370" y2="175" stroke="#f97316" strokeWidth="1" strokeDasharray="3 2"/>
          <text x="430" y="185" textAnchor="middle" fill="#f97316" fontSize="6">Sensor data (IP/radio)</text>

          {/* Legend */}
          <text x="30" y="210" fill="#6b7280" fontSize="7" fontWeight="600">LEGEND:</text>
          <line x1="30" y1="222" x2="50" y2="222" stroke="#06b6d4" strokeWidth="1.5"/>
          <text x="55" y="225" fill="#6b7280" fontSize="7">S-band (TM/TC)</text>
          <line x1="150" y1="222" x2="170" y2="222" stroke="#ec4899" strokeWidth="2"/>
          <text x="175" y="225" fill="#6b7280" fontSize="7">X-band (payload data)</text>
          <line x1="300" y1="222" x2="320" y2="222" stroke="#f59e0b" strokeWidth="1.5"/>
          <text x="325" y="225" fill="#6b7280" fontSize="7">Ground network (fibre/IP)</text>
          <line x1="470" y1="222" x2="490" y2="222" stroke="#f97316" strokeWidth="1" strokeDasharray="3 2"/>
          <text x="495" y="225" fill="#6b7280" fontSize="7">Optional ground sensor link</text>
        </svg>
      </div>

      {/* Mission Phases Timeline */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <h3 style={{ fontSize: '0.9rem', margin: 0 }}>Mission Phases</h3>
          <span style={{ fontSize: '0.72rem', color: '#9ca3af' }}>Total: {(totalDays / 365).toFixed(1)} years</span>
        </div>
        <div style={{ display: 'flex', height: 28, borderRadius: '4px', overflow: 'hidden', marginBottom: '0.5rem' }}>
          {phases.map(p => {
            const pct = (p.duration_days / totalDays * 100)
            return (
              <div key={p.id} title={`${p.name}: ${p.duration_days} days`}
                style={{ width: `${pct}%`, background: PHASE_COLORS[p.id] || '#374151', display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: pct > 5 ? 0 : 20 }}>
                {pct > 8 && <span style={{ fontSize: '0.6rem', color: 'white', fontWeight: 600 }}>{p.name}</span>}
              </div>
            )
          })}
        </div>
        {phases.map(p => (
          <div key={p.id} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', padding: '0.3rem 0', borderTop: '1px solid #374151', fontSize: '0.78rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: PHASE_COLORS[p.id] || '#374151', flexShrink: 0, marginTop: '0.2rem' }} />
            <div style={{ flex: 1 }}>
              <span style={{ fontWeight: 600 }}>{p.name}</span>
              <span style={{ color: '#6b7280' }}> ({p.duration_days} days)</span>
              {editingPhase === p.id ? (
                <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.2rem' }}>
                  <input className="input" value={p.description}
                    onChange={e => setPhases(prev => prev.map(ph => ph.id === p.id ? { ...ph, description: e.target.value } : ph))}
                    style={{ flex: 1, fontSize: '0.72rem' }} />
                  <input className="input" type="number" value={p.duration_days}
                    onChange={e => setPhases(prev => prev.map(ph => ph.id === p.id ? { ...ph, duration_days: Number(e.target.value) || 1 } : ph))}
                    style={{ width: '60px', fontSize: '0.72rem' }} />
                  <button onClick={() => setEditingPhase(null)} style={{ background: 'none', border: 'none', color: '#10b981', cursor: 'pointer', fontSize: '0.68rem' }}>Done</button>
                </div>
              ) : (
                <div style={{ color: '#9ca3af', fontSize: '0.72rem', cursor: 'pointer' }} onClick={() => setEditingPhase(p.id)}>{p.description}</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Operational Modes */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <h3 style={{ fontSize: '0.9rem', margin: 0 }}>Operational Modes</h3>
          <button className="btn btn-sm" onClick={() => setModes(prev => [...prev, { id: `m-${Date.now()}`, name: 'New Mode', description: '', subsystems_active: [], pointing: '', dataflow: '' }])} style={{ fontSize: '0.7rem' }}>+ Add Mode</button>
        </div>
        {modes.map(m => (
          <div key={m.id} style={{ padding: '0.5rem 0.75rem', background: 'var(--bg-primary, #0a0e1a)', borderRadius: '6px', marginBottom: '0.35rem', border: '1px solid #374151' }}>
            {editingMode === m.id ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                <input className="input" value={m.name} onChange={e => setModes(prev => prev.map(mm => mm.id === m.id ? { ...mm, name: e.target.value } : mm))} placeholder="Mode name" style={{ fontSize: '0.82rem', fontWeight: 600 }} />
                <input className="input" value={m.description} onChange={e => setModes(prev => prev.map(mm => mm.id === m.id ? { ...mm, description: e.target.value } : mm))} placeholder="Description" style={{ fontSize: '0.72rem' }} />
                <input className="input" value={m.subsystems_active.join(', ')} onChange={e => setModes(prev => prev.map(mm => mm.id === m.id ? { ...mm, subsystems_active: e.target.value.split(',').map(s => s.trim()) } : mm))} placeholder="Active subsystems (comma-separated)" style={{ fontSize: '0.72rem' }} />
                <div style={{ display: 'flex', gap: '0.3rem' }}>
                  <input className="input" value={m.pointing} onChange={e => setModes(prev => prev.map(mm => mm.id === m.id ? { ...mm, pointing: e.target.value } : mm))} placeholder="Pointing" style={{ flex: 1, fontSize: '0.72rem' }} />
                  <input className="input" value={m.dataflow} onChange={e => setModes(prev => prev.map(mm => mm.id === m.id ? { ...mm, dataflow: e.target.value } : mm))} placeholder="Data flow" style={{ flex: 1, fontSize: '0.72rem' }} />
                </div>
                <button onClick={() => setEditingMode(null)} className="btn btn-sm" style={{ fontSize: '0.68rem', alignSelf: 'flex-start' }}>Done</button>
              </div>
            ) : (
              <div onClick={() => setEditingMode(m.id)} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.82rem' }}>{m.name}</span>
                  <span style={{ flex: 1 }} />
                  <button onClick={e => { e.stopPropagation(); setModes(prev => prev.filter(mm => mm.id !== m.id)) }}
                    style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.6rem' }}>remove</button>
                </div>
                <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.15rem' }}>{m.description}</div>
                <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.68rem', color: '#6b7280', flexWrap: 'wrap' }}>
                  <span>Active: <span style={{ color: '#d1d5db' }}>{m.subsystems_active.join(', ') || '—'}</span></span>
                  <span>Pointing: <span style={{ color: '#d1d5db' }}>{m.pointing || '—'}</span></span>
                  {m.dataflow && <span>Data: <span style={{ color: '#d1d5db' }}>{m.dataflow}</span></span>}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Data Flow Pipeline */}
      <div className="card">
        <h3 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Data Flow Pipeline</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', flexWrap: 'wrap', fontSize: '0.78rem' }}>
          {['Instrument', '→', 'Onboard Storage', '→', 'Downlink', '→', 'Ground Processing', '→', 'Archive', '→', 'User'].map((step, i) => (
            <span key={i} style={{
              padding: step === '→' ? '0' : '0.25rem 0.5rem',
              background: step === '→' ? 'transparent' : '#1f2937',
              border: step === '→' ? 'none' : '1px solid #374151',
              borderRadius: step === '→' ? 0 : '4px',
              color: step === '→' ? '#6b7280' : '#d1d5db',
            }}>{step}</span>
          ))}
        </div>
        <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '0.4rem' }}>
          End-to-end latency depends on: ground station access, data volume, processing pipeline, and distribution method.
        </div>
      </div>
    </div>
  )
}
