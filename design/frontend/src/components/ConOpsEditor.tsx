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
        <svg width="100%" height="200" viewBox="0 0 700 200" style={{ background: 'var(--bg-primary, #0a0e1a)', borderRadius: '6px' }}>
          <rect x="250" y="20" width="200" height="60" rx="8" fill="#1f2937" stroke="#3b82f6" strokeWidth="2"/>
          <text x="350" y="45" textAnchor="middle" fill="#3b82f6" fontSize="12" fontWeight="600">Space Segment</text>
          <text x="350" y="62" textAnchor="middle" fill="#9ca3af" fontSize="9">Spacecraft + Payload</text>
          <rect x="50" y="130" width="160" height="50" rx="8" fill="#1f2937" stroke="#10b981" strokeWidth="2"/>
          <text x="130" y="152" textAnchor="middle" fill="#10b981" fontSize="11" fontWeight="600">Ground Segment</text>
          <text x="130" y="167" textAnchor="middle" fill="#9ca3af" fontSize="9">GS + MCC + Processing</text>
          <rect x="490" y="130" width="160" height="50" rx="8" fill="#1f2937" stroke="#f59e0b" strokeWidth="2"/>
          <text x="570" y="152" textAnchor="middle" fill="#f59e0b" fontSize="11" fontWeight="600">End Users</text>
          <text x="570" y="167" textAnchor="middle" fill="#9ca3af" fontSize="9">Data Products + Services</text>
          <line x1="300" y1="80" x2="130" y2="130" stroke="#06b6d4" strokeWidth="1.5" strokeDasharray="4 2"/>
          <text x="195" y="108" fill="#06b6d4" fontSize="8" transform="rotate(-25 195 108)">TM/TC + Science Data</text>
          <line x1="160" y1="130" x2="280" y2="80" stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="4 2"/>
          <text x="200" y="98" fill="#8b5cf6" fontSize="8" transform="rotate(-25 200 98)">Commands</text>
          <line x1="210" y1="155" x2="490" y2="155" stroke="#f59e0b" strokeWidth="1.5"/>
          <text x="350" y="148" textAnchor="middle" fill="#f59e0b" fontSize="8">Data Products (L1/L2/L3)</text>
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
