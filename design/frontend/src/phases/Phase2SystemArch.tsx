/**
 * Phase 2: System Architecture
 *
 * Architecture decisions per subsystem, system block diagrams,
 * interfaces, budget bucket allocation, FMECA awareness.
 * Multi-lens views: mechanical / electrical / RF / thermal / data / mission.
 */
import { useState } from 'react'
import { SystemArchitectureEditor } from '../components/SystemArchitectureEditor'
import { ModelBlockDiagram } from '../components/ModelBlockDiagram'
import { LensView } from '../views/LensView'
import { InterfaceMatrixView } from '../components/InterfaceMatrixView'
import { SystemBudgetEditor } from '../components/SystemBudgetEditor'
import { useDesignStore } from '../stores/designStore'
import { SEGMENT_LABELS, LENS_LABELS, type Segment, type Lens } from '../types/phases'
import { BudgetCascade } from '../charts/BudgetCascade'
import { FMECAPanel } from '../components/FMECAPanel'
import { GroundSystemsArch } from '../components/GroundSystemsArch'
import { OpsSystemsArch } from '../components/OpsSystemsArch'
// GroundStationDesigner is at Phase 1 (mission level); Phase 2 uses GroundSystemsArch

type SubView = 'architecture' | 'block_diagram' | 'interfaces' | 'budgets' | 'fmeca' | 'compliance'

export function Phase2SystemArch() {
  const [segment, setSegment] = useState<Segment>('space')
  const [subView, setSubView] = useState<SubView>('architecture')
  const [lens, setLens] = useState<Lens | null>(null)
  const requirements = useDesignStore(s => s.requirements)

  // Budget cascade data
  const massEnvelope = requirements.target_mass_kg || 6
  const result = useDesignStore(s => s.result)
  const params = result?.parameters || {}
  const get = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  const massBuckets = [
    { label: 'Payload', allocation: massEnvelope * 0.25, used: get('payload.mass_kg') || requirements.payloads?.[0]?.mass_kg || 0, unit: 'kg' },
    { label: 'EPS', allocation: massEnvelope * 0.22, used: get('power.eps_mass_kg'), unit: 'kg' },
    { label: 'AOCS', allocation: massEnvelope * 0.18, used: get('aocs.mass_kg'), unit: 'kg' },
    { label: 'Comms', allocation: massEnvelope * 0.08, used: get('link.ttc_mass_kg'), unit: 'kg' },
    { label: 'Thermal', allocation: massEnvelope * 0.06, used: get('thermal.tcs_mass_kg'), unit: 'kg' },
    { label: 'Structure', allocation: massEnvelope * 0.16, used: get('structure.mass_kg'), unit: 'kg' },
    { label: 'Margin', allocation: massEnvelope * 0.05, used: 0, unit: 'kg' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Segment + lens bar */}
      <div style={{ display: 'flex', gap: '0.25rem', padding: '0.4rem 1rem', borderBottom: '1px solid var(--border, #374151)', alignItems: 'center', flexWrap: 'wrap' }}>
        {(['space', 'ground', 'operations'] as Segment[]).map(s => (
          <button key={s} onClick={() => setSegment(s)} style={{
            padding: '0.3rem 0.75rem', fontSize: '0.75rem', borderRadius: '4px', cursor: 'pointer',
            background: segment === s ? '#06b6d4' : 'transparent',
            color: segment === s ? 'white' : '#9ca3af',
            border: `1px solid ${segment === s ? '#06b6d4' : '#374151'}`,
            textTransform: 'capitalize',
          }}>{s}</button>
        ))}
        <span style={{ color: '#374151', margin: '0 0.3rem' }}>|</span>
        {/* Sub-views — filtered by segment */}
        {(segment === 'space'
          ? ['architecture', 'block_diagram', 'interfaces', 'budgets', 'fmeca'] as SubView[]
          : segment === 'ground'
          ? ['architecture', 'block_diagram', 'interfaces', 'budgets'] as SubView[]
          : ['architecture', 'budgets'] as SubView[]
        ).map(v => (
          <button key={v} onClick={() => setSubView(v)} style={{
            padding: '0.25rem 0.6rem', fontSize: '0.7rem', borderRadius: '3px', cursor: 'pointer',
            background: subView === v ? 'rgba(6,182,212,0.15)' : 'transparent',
            color: subView === v ? '#67e8f9' : '#6b7280',
            border: 'none',
          }}>{v.replace('_', ' ')}</button>
        ))}
        <span style={{ flex: 1 }} />
        {/* Lens selector */}
        <span style={{ fontSize: '0.62rem', color: '#6b7280', marginRight: '0.3rem' }}>Lens:</span>
        {(Object.entries(LENS_LABELS) as [Lens, typeof LENS_LABELS[Lens]][]).map(([l, info]) => (
          <button key={l} onClick={() => setLens(lens === l ? null : l)} style={{
            padding: '0.15rem 0.4rem', fontSize: '0.6rem', borderRadius: '3px', cursor: 'pointer',
            background: lens === l ? `${info.color}20` : 'transparent',
            color: lens === l ? info.color : '#6b7280',
            border: `1px solid ${lens === l ? `${info.color}60` : 'transparent'}`,
          }}>{info.name}</button>
        ))}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: 'auto', display: 'flex' }}>
        <div style={{ flex: 1, overflow: 'auto' }}>
          {/* Lens view takes over when a lens is active */}
          {lens ? (
            <LensView lens={lens} segment={segment} />
          ) : segment === 'space' ? (
            <>
              {subView === 'architecture' && <SystemArchitectureEditor />}
              {subView === 'block_diagram' && <ModelBlockDiagram studyId={useDesignStore.getState().studyId} segment="space" />}
              {subView === 'interfaces' && <InterfaceMatrixView onNavigate={() => {}} />}
              {subView === 'budgets' && <SystemBudgetEditor />}
              {subView === 'fmeca' && <FMECAPanel />}
              {subView === 'compliance' && (
                requirements ? (
                  <div style={{ padding: '1rem' }}>
                    <h2 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>System-Level Compliance</h2>
                    <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
                      Check system requirements against current design parameters. Run at each phase gate.
                    </p>
                    <div className="card">
                      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Quick Compliance Check</h3>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
                        <thead>
                          <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                            <th style={{ padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af' }}>Requirement</th>
                            <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>Target</th>
                            <th style={{ padding: '0.25rem 0.5rem', textAlign: 'right', fontSize: '0.65rem', color: '#9ca3af' }}>Current</th>
                            <th style={{ padding: '0.25rem 0.5rem', textAlign: 'center', fontSize: '0.65rem', color: '#9ca3af' }}>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[
                            { req: `Mass ≤ ${requirements.target_mass_kg || 6} kg`, target: requirements.target_mass_kg || 6, current: get('mass.dry_mass_kg'), op: '<=' },
                            { req: `Cost ≤ ${requirements.target_cost_meur || 2} MEUR`, target: (requirements.target_cost_meur || 2), current: get('cost.total_meur'), op: '<=' },
                            { req: 'Link margin ≥ 3 dB', target: 3, current: get('link.ttc_margin_db'), op: '>=' },
                            { req: `Lifetime ≥ ${requirements.design_lifetime_years || 3} yr`, target: requirements.design_lifetime_years || 3, current: requirements.design_lifetime_years || 3, op: '>=' },
                          ].map((c, i) => {
                            const pass = c.op === '<=' ? c.current <= c.target : c.current >= c.target
                            return (
                              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                <td style={{ padding: '0.2rem 0.5rem' }}>{c.req}</td>
                                <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>{c.target}</td>
                                <td style={{ padding: '0.2rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: pass ? '#10b981' : '#ef4444' }}>{typeof c.current === 'number' ? c.current.toFixed(2) : '—'}</td>
                                <td style={{ padding: '0.2rem 0.5rem', textAlign: 'center' }}>
                                  <span style={{ color: pass ? '#10b981' : '#ef4444', fontWeight: 700 }}>{pass ? '✓' : '✗'}</span>
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : <div style={{ padding: '2rem', color: '#6b7280' }}>Run a design to check compliance.</div>
              )}
            </>
          ) : segment === 'ground' ? (
            <GroundSystemsArch />
          ) : segment === 'operations' ? (
            <OpsSystemsArch />
          ) : null}
        </div>

        {/* Budget cascade sidebar */}
        <div style={{ width: '250px', padding: '0.5rem', borderLeft: '1px solid var(--border, #374151)', overflowY: 'auto' }}>
          <BudgetCascade title="Mass Budget" envelope={massEnvelope} unit="kg" items={massBuckets} />
        </div>
      </div>
    </div>
  )
}
