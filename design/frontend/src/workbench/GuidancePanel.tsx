/**
 * GuidancePanel — Session guidance, worked examples, and contextual help.
 *
 * Shown as a collapsible sidebar or modal.
 * Content varies by current level and element context.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useUIStore, type Level } from '../stores/uiStore'

const API = '/api'

const LEVEL_GUIDANCE: Record<Level, { title: string; sessions: string[]; objectives: string[]; tips: string[] }> = {
  0: {
    title: 'Mission Level — Define the Problem',
    sessions: ['1.1 Mission Need & Stakeholders', '1.2 Concept of Operations', '1.3 Trade Studies', '1.4 Architecture Selection'],
    objectives: [
      'Define the mission problem statement and objectives',
      'Identify stakeholders and their needs',
      'Consider space AND non-space alternatives (drones, ground sensors, commercial data)',
      'Select mission architecture through systematic trade study',
      'Define segments: Space, Ground, Launch, Operations',
      'Mark in-scope vs out-of-scope segments',
      'Set top-level budgets (mass, power, cost)',
      'Define mission-level requirements (functional, performance, interface, regulatory, process)',
      'Define segment-to-segment interfaces',
      'Freeze when all checks pass',
    ],
    tips: [
      'Start with "Design Assist" presets to quickly set up segments',
      'Use the "Decide" tab for systematic mission trade analysis',
      'Consider orbit trade early — it drives many downstream decisions',
      'Mark external segments (Launch) as OUT-OF-SCOPE — define interfaces only',
      'Set budget allocations before freezing — they become constraints for Level 1',
    ],
  },
  1: {
    title: 'Systems Level — What Systems Compose Each Segment?',
    sessions: ['2.1 System-V Decomposition', '2.2 Requirements Engineering', '2.3 Functional Decomposition', '2.4 Interface Matrix'],
    objectives: [
      'For each in-scope segment, define the systems within it',
      'For Space: how many spacecraft? Constellation or single?',
      'For Ground: how many ground stations? Where?',
      'Derive system requirements from mission requirements (use "flow ↓")',
      'Define system-to-system interfaces (electrical, data, RF)',
      'Set system-level budget allocations',
      'Use constellation sizing if multi-satellite',
      'Use ground station trade if selecting GS network',
      'Freeze when all systems defined, budgeted, and requirements allocated',
    ],
    tips: [
      'Double-click a segment to drill into it and see/add its systems',
      'Use "Decide" tab for constellation sizing and ground station trade',
      'Set quantity > 1 for constellation spacecraft — budget multiplies automatically',
      'Consider cost learning curves for multi-unit production',
      'External interfaces from Level 0 appear as dashed port nodes — connect them to systems',
    ],
  },
  2: {
    title: 'Subsystems Level — Break Systems into Subsystems',
    sessions: ['3.1 Payload & Power', '3.2 Comms & Thermal', '3.3 AOCS & Structure', '3.4 Equipment Selection Trades'],
    objectives: [
      'For each system, define its subsystems (EPS, AOCS, TTC, OBC, Thermal, Structure, Propulsion, Payload)',
      'Use "Standard Spacecraft Bus" preset to quickly populate subsystems',
      'For ground stations: Antenna, RF Front End, Modem, Network subsystems',
      'Derive subsystem requirements from system requirements',
      'Define subsystem-to-subsystem interfaces',
      'Allocate budgets from system level to subsystems',
      'Begin considering equipment options (use "Decide" tab for trade studies)',
    ],
    tips: [
      'Use the Pugh Matrix in "Decide" tab for subsystem architecture trades',
      'Use pairwise comparison to derive criteria weights for trade studies',
      'Each subsystem should have at least one requirement before freezing',
      'Check SMART compliance using the SMART Check button in Requirements tab',
    ],
  },
  3: {
    title: 'Equipment Level — Select or Define Components',
    sessions: ['4.1 Equipment Selection', '4.2 Integration Planning', '4.3 Risk & FMECA', '4.4 Design Review Preparation'],
    objectives: [
      'For each subsystem, select equipment from the KB catalog or define custom components',
      'Each component has: mass, power, cost, TRL, manufacturer',
      'Actuals roll up to subsystem budgets — check margins',
      'Derive equipment-level requirements if needed',
      'Define equipment interfaces (connectors, protocols)',
      'Run analysis to compute parametric estimates for missing values',
      'Check maturity: all components should have real data, not estimates',
    ],
    tips: [
      'Equipment Browser auto-selects the domain matching the parent subsystem',
      'Use "Define Custom Equipment" if nothing in the catalog fits',
      'Set quantity for redundant or multi-unit components',
      'Run "SMART Check" on all requirements before proceeding to V&V',
      'The escalation banner warns if equipment choices exceed budget at any level',
    ],
  },
  4: {
    title: 'V&V Level — Verify the Design Closes',
    sessions: ['5.1 Verification Planning', '5.2 Compliance Assessment', '5.3 Test Planning', '5.4 Disposal & Closeout'],
    objectives: [
      'Review budget rollups across all levels — do the numbers add up?',
      'Check requirement traceability — every requirement should trace to an element',
      'Run FMECA for failure mode analysis',
      'Evaluate review gate readiness (MCR, SRR, PDR, CDR)',
      'Trace budgets to stakeholder impact — what happens if we exceed?',
      'Generate export documents for review',
    ],
    tips: [
      'Use the Budget Rollup tab to see the full element tree with mass/power/cost',
      'The Requirements tab highlights orphan requirements (no parent derivation)',
      'Review Gates tab evaluates real MCR/SRR/PDR/CDR criteria',
      'FMECA identifies critical failure modes by subsystem',
      'Budget Traceability traces exceedances to stakeholder needs with recovery options',
    ],
  },
}

export function GuidancePanel({ onClose }: { onClose: () => void }) {
  const studyId = useUIStore(s => s.studyId)
  const currentLevel = useUIStore(s => s.currentLevel)
  const setStudyId = useUIStore(s => s.setStudyId)
  const qc = useQueryClient()
  const [loadingExample, setLoadingExample] = useState(false)

  const guidance = LEVEL_GUIDANCE[currentLevel]

  // Fetch example missions
  const { data: examples } = useQuery({
    queryKey: ['example-missions'],
    queryFn: () => fetch(`${API}/lifecycle/example-missions`).then(r => r.ok ? r.json() : { missions: [] }),
  })

  const loadExample = async (missionId: string) => {
    setLoadingExample(true)
    try {
      const res = await fetch(`${API}/lifecycle/example-missions/${missionId}`)
      if (!res.ok) return
      const mission = await res.json()
      // Create a study from the example
      const studyRes = await fetch(`${API}/studies/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: mission.requirements || { name: mission.name }, mission_need: mission.mission_need || {} }),
      })
      if (studyRes.ok) {
        const study = await studyRes.json()
        setStudyId(study.id)
        qc.invalidateQueries()
        onClose()
      }
    } finally { setLoadingExample(false) }
  }

  return (
    <div style={{
      position: 'fixed', top: 0, right: 0, bottom: 0, width: 380,
      background: 'var(--bg-secondary)', borderLeft: '1px solid var(--border)',
      overflow: 'auto', zIndex: 1000, padding: '1rem',
      boxShadow: '-4px 0 20px rgba(0,0,0,0.3)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h2 style={{ fontSize: '0.9rem', margin: 0, color: 'var(--accent)' }}>Facilitator Guide</h2>
        <span style={{ flex: 1 }} />
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.2rem' }}>×</button>
      </div>

      {/* Current level guidance */}
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '0.8rem', color: '#f59e0b', marginBottom: '0.3rem' }}>{guidance.title}</h3>

        <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.15rem', textTransform: 'uppercase' }}>
          Related Sessions
        </div>
        <div style={{ marginBottom: '0.4rem' }}>
          {guidance.sessions.map((s, i) => (
            <div key={i} style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', padding: '0.1rem 0' }}>
              {s}
            </div>
          ))}
        </div>

        <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.15rem', textTransform: 'uppercase' }}>
          Learning Objectives
        </div>
        <div style={{ marginBottom: '0.4rem' }}>
          {guidance.objectives.map((o, i) => (
            <div key={i} style={{ display: 'flex', gap: '0.3rem', fontSize: '0.68rem', padding: '0.1rem 0' }}>
              <span style={{ color: 'var(--success)', flexShrink: 0 }}>•</span>
              <span>{o}</span>
            </div>
          ))}
        </div>

        <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.15rem', textTransform: 'uppercase' }}>
          Tips
        </div>
        <div>
          {guidance.tips.map((t, i) => (
            <div key={i} style={{
              fontSize: '0.65rem', padding: '0.2rem 0.3rem', marginBottom: '0.15rem',
              background: 'rgba(59,130,246,0.08)', borderRadius: '3px', borderLeft: '2px solid var(--accent)',
            }}>
              {t}
            </div>
          ))}
        </div>
      </div>

      {/* Example missions */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
        <h3 style={{ fontSize: '0.8rem', color: '#10b981', marginBottom: '0.3rem' }}>Worked Examples</h3>
        <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
          Load a pre-built mission to explore or use as a starting point:
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
          {(examples?.missions || []).map((m: any) => (
            <button key={m.id} onClick={() => loadExample(m.id)} disabled={loadingExample}
              style={{
                padding: '0.3rem 0.5rem', borderRadius: '4px', textAlign: 'left',
                background: 'var(--bg-card)', border: '1px solid var(--border)',
                color: 'var(--text-primary)', cursor: 'pointer', fontSize: '0.68rem',
              }}>
              <div style={{ fontWeight: 600 }}>{m.name}</div>
              <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>{m.description}</div>
            </button>
          ))}
          {(!examples?.missions || examples.missions.length === 0) && (
            <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>
              No example missions available from server.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
