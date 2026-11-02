/**
 * GuidancePanel — Session guidance, worked examples, and contextual help.
 *
 * Shown as a collapsible sidebar or modal.
 * Content varies by current level and element context.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import i18n from '../i18n'
import { useUIStore, type Level } from '../stores/uiStore'

const API = '/api'

const levelGuidance = (t: TFunction): Record<Level, { title: string; sessions: string[]; objectives: string[]; tips: string[] }> => ({
  0: {
    title: t('Mission Level — Define the Problem'),
    sessions: [t('1.1 Mission Need & Stakeholders'), t('1.2 Concept of Operations'), t('1.3 Trade Studies'), t('1.4 Architecture Selection')],
    objectives: [
      t('Define the mission problem statement and objectives'),
      t('Identify stakeholders and their needs'),
      t('Consider space AND non-space alternatives (drones, ground sensors, commercial data)'),
      t('Select mission architecture through systematic trade study'),
      t('Define segments: Space, Ground, Launch, Operations'),
      t('Mark in-scope vs out-of-scope segments'),
      t('Set top-level budgets (mass, power, cost)'),
      t('Define mission-level requirements (functional, performance, interface, regulatory, process)'),
      t('Define segment-to-segment interfaces'),
      t('Freeze when all checks pass'),
    ],
    tips: [
      t('Start with "Design Assist" presets to quickly set up segments'),
      t('Use the "Decide" tab for systematic mission trade analysis'),
      t('Consider orbit trade early — it drives many downstream decisions'),
      t('Mark external segments (Launch) as OUT-OF-SCOPE — define interfaces only'),
      t('Set budget allocations before freezing — they become constraints for Level 1'),
    ],
  },
  1: {
    title: t('Systems Level — What Systems Compose Each Segment?'),
    sessions: [t('2.1 System-V Decomposition'), t('2.2 Requirements Engineering'), t('2.3 Functional Decomposition'), t('2.4 Interface Matrix')],
    objectives: [
      t('For each in-scope segment, define the systems within it'),
      t('For Space: how many spacecraft? Constellation or single?'),
      t('For Ground: how many ground stations? Where?'),
      t('Derive system requirements from mission requirements (use "flow ↓")'),
      t('Define system-to-system interfaces (electrical, data, RF)'),
      t('Set system-level budget allocations'),
      t('Use constellation sizing if multi-satellite'),
      t('Use ground station trade if selecting GS network'),
      t('Freeze when all systems defined, budgeted, and requirements allocated'),
    ],
    tips: [
      t('Double-click a segment to drill into it and see/add its systems'),
      t('Use "Decide" tab for constellation sizing and ground station trade'),
      t('Set quantity > 1 for constellation spacecraft — budget multiplies automatically'),
      t('Consider cost learning curves for multi-unit production'),
      t('External interfaces from Level 0 appear as dashed port nodes — connect them to systems'),
    ],
  },
  2: {
    title: t('Subsystems Level — Break Systems into Subsystems'),
    sessions: [t('3.1 Payload & Power'), t('3.2 Comms & Thermal'), t('3.3 AOCS & Structure'), t('3.4 Equipment Selection Trades')],
    objectives: [
      t('For each system, define its subsystems (EPS, AOCS, TTC, OBC, Thermal, Structure, Propulsion, Payload)'),
      t('Use "Standard Spacecraft Bus" preset to quickly populate subsystems'),
      t('For ground stations: Antenna, RF Front End, Modem, Network subsystems'),
      t('Derive subsystem requirements from system requirements'),
      t('Define subsystem-to-subsystem interfaces'),
      t('Allocate budgets from system level to subsystems'),
      t('Begin considering equipment options (use "Decide" tab for trade studies)'),
    ],
    tips: [
      t('Use the Pugh Matrix in "Decide" tab for subsystem architecture trades'),
      t('Use pairwise comparison to derive criteria weights for trade studies'),
      t('Each subsystem should have at least one requirement before freezing'),
      t('Check SMART compliance using the SMART Check button in Requirements tab'),
    ],
  },
  3: {
    title: t('Equipment Level — Select or Define Components'),
    sessions: [t('4.1 Equipment Selection'), t('4.2 Integration Planning'), t('4.3 Risk & FMECA'), t('4.4 Design Review Preparation')],
    objectives: [
      t('For each subsystem, select equipment from the KB catalog or define custom components'),
      t('Each component has: mass, power, cost, TRL, manufacturer'),
      t('Actuals roll up to subsystem budgets — check margins'),
      t('Derive equipment-level requirements if needed'),
      t('Define equipment interfaces (connectors, protocols)'),
      t('Run analysis to compute parametric estimates for missing values'),
      t('Check maturity: all components should have real data, not estimates'),
    ],
    tips: [
      t('Equipment Browser auto-selects the domain matching the parent subsystem'),
      t('Use "Define Custom Equipment" if nothing in the catalog fits'),
      t('Set quantity for redundant or multi-unit components'),
      t('Run "SMART Check" on all requirements before proceeding to V&V'),
      t('The escalation banner warns if equipment choices exceed budget at any level'),
    ],
  },
  4: {
    title: t('V&V Level — Verify the Design Closes'),
    sessions: [t('5.1 Verification Planning'), t('5.2 Compliance Assessment'), t('5.3 Test Planning'), t('5.4 Disposal & Closeout')],
    objectives: [
      t('Review budget rollups across all levels — do the numbers add up?'),
      t('Check requirement traceability — every requirement should trace to an element'),
      t('Run FMECA for failure mode analysis'),
      t('Evaluate review gate readiness (MCR, SRR, PDR, CDR)'),
      t('Trace budgets to stakeholder impact — what happens if we exceed?'),
      t('Generate export documents for review'),
    ],
    tips: [
      t('Use the Budget Rollup tab to see the full element tree with mass/power/cost'),
      t('The Requirements tab highlights orphan requirements (no parent derivation)'),
      t('Review Gates tab evaluates real MCR/SRR/PDR/CDR criteria'),
      t('FMECA identifies critical failure modes by subsystem'),
      t('Budget Traceability traces exceedances to stakeholder needs with recovery options'),
    ],
  },
})

interface Worksheet {
  title: string
  description: string
  sections: Array<{ heading: string; content: string }>
}

// Worksheet text is shown and used for the Markdown fallback download, translated at that time.
// One object per level keeps each within the key scanner's 2000-character window.
// English text is the i18n key
const WORKSHEETS_L0: Record<string, Worksheet> = {
  missionNeed: { title: 'Mission Need Statement', description: 'Define problem, stakeholders, objectives, success criteria',
    sections: [
      { heading: 'Problem Statement', content: 'What problem does this mission solve?\n\n[Write here]' },
      { heading: 'Stakeholders', content: 'Who benefits? Who funds? Who operates?\n\nStakeholder | Role | Needs | Priority\n---|---|---|---\n | | |' },
      { heading: 'Mission Objectives', content: 'ID | Objective | Priority | Measurable Criterion\n---|---|---|---\nOBJ-001 | | |' },
      { heading: 'Alternatives Considered', content: 'Option | Type | Pros | Cons | Feasibility\n---|---|---|---|---\n | | | |' },
    ]
  },
  tradeStudy: { title: 'Architecture Trade Study', description: 'Compare mission architecture options systematically',
    sections: [
      { heading: 'Trade Criteria', content: 'Criterion | Weight | Direction | Threshold\n---|---|---|---\nCost | | minimize |\nPerformance | | maximize |' },
      { heading: 'Options', content: 'Option | Description | Pros | Cons\n---|---|---|---\n | | |' },
      { heading: 'Scoring Matrix', content: '[Use the Pugh Matrix in the Decide tab]' },
      { heading: 'Decision & Rationale', content: 'Selected option:\nRationale:\n' },
    ]
  },
}

// English text is the i18n key
const WORKSHEETS_L1: Record<string, Worksheet> = {
  systemReqs: { title: 'System Requirements Derivation', description: 'Derive system requirements from mission requirements',
    sections: [
      { heading: 'Parent Requirement', content: 'MIS-XXX: [mission requirement text]' },
      { heading: 'Derived System Requirements', content: 'ID | System | Text | V&V Method\n---|---|---|---\nSYS-001 | | |' },
      { heading: 'Traceability Check', content: 'Does each system requirement trace to a mission requirement? [Y/N]' },
    ]
  },
}

// English text is the i18n key
const WORKSHEETS_L2: Record<string, Worksheet> = {
  subsystemDesign: { title: 'Subsystem Design Worksheet', description: 'Define subsystem architecture and requirements',
    sections: [
      { heading: 'Subsystem', content: 'Name:\nDomain:\nDriving requirement:' },
      { heading: 'Architecture Options', content: 'Option | Description | Mass | Power | Cost | TRL\n---|---|---|---|---|---\n | | | | |' },
      { heading: 'Selected Architecture', content: 'Selection:\nRationale:' },
      { heading: 'Interface Requirements', content: 'Interface | Type | To/From | Properties\n---|---|---|---\n | | |' },
    ]
  },
}

// English text is the i18n key
const WORKSHEETS_L3: Record<string, Worksheet> = {
  equipmentSelection: { title: 'Equipment Selection Worksheet', description: 'Compare and select equipment from catalog',
    sections: [
      { heading: 'Subsystem', content: 'Name:\nBudget allocation: mass=__kg, power=__W, cost=__kEUR' },
      { heading: 'Candidate Components', content: 'Component | Manufacturer | Mass | Power | Cost | TRL | Notes\n---|---|---|---|---|---|---\n | | | | | |' },
      { heading: 'Selection', content: 'Selected:\nRationale:\nMargin remaining:' },
    ]
  },
}

const LEVEL_WORKSHEETS: Record<number, Worksheet[]> = {
  0: Object.values(WORKSHEETS_L0),
  1: Object.values(WORKSHEETS_L1),
  2: Object.values(WORKSHEETS_L2),
  3: Object.values(WORKSHEETS_L3),
  4: [],
}

async function downloadWorksheet(ws: Worksheet) {
  // Try branded DOCX from backend first
  const templateId = ws.title.toLowerCase().includes('mission need') ? 'mission_need'
    : ws.title.toLowerCase().includes('trade') ? 'trade_study'
    : ws.title.toLowerCase().includes('requirement') ? 'requirements'
    : ws.title.toLowerCase().includes('subsystem') ? 'subsystem_design'
    : ws.title.toLowerCase().includes('equipment') ? 'equipment_selection'
    : null

  if (templateId) {
    try {
      const res = await fetch(`/api/exports/worksheet/${templateId}`, { method: 'POST' })
      if (res.ok) {
        const blob = await res.blob()
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = `SpaceCDF_Worksheet_${templateId}.docx`
        a.click()
        URL.revokeObjectURL(a.href)
        return
      }
    } catch { /* fall back to markdown */ }
  }

  // Fallback: Markdown, in the UI language (the file name stays English)
  const tr = (k: string) => i18n.t(k)
  const md = `# ${tr(ws.title)}\n\n${ws.sections.map(s => `## ${tr(s.heading)}\n\n${tr(s.content)}\n`).join('\n')}`
  const blob = new Blob([md], { type: 'text/markdown' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${ws.title.replace(/\s+/g, '_')}.md`
  a.click()
  URL.revokeObjectURL(a.href)
}

export function GuidancePanel({ onClose }: { onClose: () => void }) {
  const currentLevel = useUIStore(s => s.currentLevel)
  const setStudyId = useUIStore(s => s.setStudyId)
  const qc = useQueryClient()
  const { t } = useTranslation()
  const [loadingExample, setLoadingExample] = useState(false)

  const guidance = levelGuidance(t)[currentLevel]

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
    <aside className="c2o-drawer" aria-labelledby="c2o-guide-title"
      onKeyDown={e => { if (e.key === 'Escape') onClose() }}>
      <div className="c2o-drawer__head">
        <h2 id="c2o-guide-title" className="t-15 w-600 m-0">{t('Facilitator Guide')}</h2>
        <button type="button" onClick={onClose} className="c2o-btn c2o-btn--icon" aria-label={t('Close')} autoFocus>×</button>
      </div>

      {/* Current level guidance */}
      <div className="mb-4">
        <h3 className="t-13 w-600 mb-2">{guidance.title}</h3>

        <div className="t-12 w-600 c-2 mb-1 caps">
          {t('Related Sessions')}
        </div>
        <div className="mb-2">
          {guidance.sessions.map((s, i) => (
            <div key={i} className="t-12 c-2 py-1 px-0">
              {s}
            </div>
          ))}
        </div>

        <div className="t-12 w-600 c-2 mb-1 caps">
          {t('Learning Objectives')}
        </div>
        <div className="mb-2">
          {guidance.objectives.map((o, i) => (
            <div key={i} className="flex gap-1 t-12 py-1 px-0">
              <span className="c-ok shrink-0">•</span>
              <span>{o}</span>
            </div>
          ))}
        </div>

        <div className="t-12 w-600 c-2 mb-1 caps">
          {t('Tips')}
        </div>
        <div>
          {guidance.tips.map((tip, i) => (
            <div key={i} className="t-12 p-1 mb-1 bg-accent rounded bl-accent">
              {tip}
            </div>
          ))}
        </div>
      </div>

      {/* Downloadable worksheets */}
      <div className="bt pt-3 mb-3">
        <h3 className="t-13 w-600 mb-1">{t('Worksheets')}</h3>
        <div className="t-12 c-2 mb-1">
          {t('Download worksheet templates for this level:')}
        </div>
        <div className="stack gap-1">
          {(LEVEL_WORKSHEETS[currentLevel] || []).map((ws, i) => (
            <button key={i} type="button" onClick={() => downloadWorksheet(ws)} className="c2o-example-card">
              <div className="w-500">{t(ws.title)}</div>
              <div className="t-12 c-2">{t(ws.description)}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Example missions */}
      <div className="bt pt-3">
        <h3 className="t-13 w-600 mb-1">{t('Worked Examples')}</h3>
        <div className="t-12 c-2 mb-1">
          {t('Load a pre-built mission to explore or use as a starting point:')}
        </div>
        <div className="stack gap-1">
          {(examples?.missions || []).map((m: any) => (
            <button key={m.id} type="button" onClick={() => loadExample(m.id)} disabled={loadingExample}
              className="c2o-example-card">
              <div className="w-600">{m.name}</div>
              <div className="t-12 c-2">{m.description}</div>
            </button>
          ))}
          {(!examples?.missions || examples.missions.length === 0) && (
            <div className="t-12 c-2">
              {t('No example missions available from server.')}
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
