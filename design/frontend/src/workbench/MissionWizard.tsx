/**
 * MissionWizard — Guided mission definition before design begins.
 *
 * 4-step wizard that mirrors real CDF Phase 0:
 * 1. The Problem — what needs solving?
 * 2. Stakeholders & Objectives — who cares and what do they need?
 * 3. Is Space the Right Answer? — alternatives analysis
 * 4. Initial Architecture — select starting configuration
 *
 * Only after completing all steps does the study get created.
 */
import { useState, useCallback } from 'react'
import { useUIStore } from '../stores/uiStore'
import { useQueryClient } from '@tanstack/react-query'

const API = '/api'

type WizardStep = 'home' | 'problem' | 'stakeholders' | 'alternatives' | 'architecture'

interface Stakeholder {
  id: string; name: string; role: string; need: string
}

interface Objective {
  id: string; text: string; priority: string; measurable_criterion: string
}

const MISSION_TYPES = [
  { value: 'earth_observation', label: 'Earth Observation', desc: 'Imaging, SAR, multispectral' },
  { value: 'communications', label: 'Communications', desc: 'Data relay, IoT, broadband' },
  { value: 'navigation', label: 'Navigation', desc: 'PNT, GNSS augmentation' },
  { value: 'science_planetary', label: 'Science (Planetary)', desc: 'Lunar, Mars, asteroid' },
  { value: 'science_heliophysics', label: 'Science (Heliophysics)', desc: 'Solar, magnetosphere' },
  { value: 'technology_demo', label: 'Technology Demo', desc: 'In-orbit validation' },
  { value: 'lunar', label: 'Lunar Mission', desc: 'Cislunar, lunar orbit/surface' },
]

const STAKEHOLDER_ROLES = [
  { value: 'sponsor', label: 'Sponsor / Funder' },
  { value: 'user', label: 'End User' },
  { value: 'operator', label: 'Operator' },
  { value: 'science_pi', label: 'Science PI' },
  { value: 'regulator', label: 'Regulator' },
  { value: 'partner', label: 'Partner Organisation' },
]

const ARCH_PRESETS = [
  { id: 'single-leo', name: 'Single Spacecraft (LEO)', segments: ['Space Segment', 'Ground Segment', 'Launch Segment', 'Operations'] },
  { id: 'constellation', name: 'Constellation', segments: ['Space Segment', 'Ground Segment', 'Launch Segment', 'User Segment', 'Operations'] },
  { id: 'lunar', name: 'Lunar / Deep Space', segments: ['Space Segment', 'Ground Segment (DSN)', 'Launch Segment', 'Operations'] },
  { id: 'hybrid', name: 'Hybrid Space + Ground', segments: ['Space Segment', 'Ground Sensors', 'Ground Station', 'Data Centre', 'Operations'] },
  { id: 'blank', name: 'Start Blank', segments: [] },
]

export function MissionWizard() {
  const setStudyId = useUIStore(s => s.setStudyId)
  const qc = useQueryClient()

  const [step, setStep] = useState<WizardStep>('home')
  const [creating, setCreating] = useState(false)

  // Step 1: Problem
  const [problemStatement, setProblemStatement] = useState('')
  const [operationalContext, setOperationalContext] = useState('')
  const [missionType, setMissionType] = useState('earth_observation')
  const [missionName, setMissionName] = useState('')

  // Step 2: Stakeholders & Objectives
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([
    { id: '1', name: '', role: 'sponsor', need: '' },
  ])
  const [objectives, setObjectives] = useState<Objective[]>([
    { id: '1', text: '', priority: 'primary', measurable_criterion: '' },
  ])

  // Step 3: Alternatives
  const [tradeResult, setTradeResult] = useState<any>(null)
  const [tradeLoading, setTradeLoading] = useState(false)
  const [selectedAlt, setSelectedAlt] = useState<string | null>(null)
  const [selectionRationale, setSelectionRationale] = useState('')

  // Step 4: Architecture
  const [selectedArch, setSelectedArch] = useState('single-leo')
  const [lifetime, setLifetime] = useState('3')
  const [massTarget, setMassTarget] = useState('6')

  // Run alternatives analysis
  const runTradeAnalysis = async () => {
    setTradeLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/mission-trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          // Derive trade parameters from mission type
          target_gsd_m: ['earth_observation'].includes(missionType) ? 5 : 0,
          target_revisit_days: ['earth_observation'].includes(missionType) ? 3 : ['communications'].includes(missionType) ? 0 : 1,
          target_coverage: ['communications', 'navigation'].includes(missionType) ? 'global' : 'regional',
          target_latency_hours: ['communications'].includes(missionType) ? 0.1 : ['earth_observation'].includes(missionType) ? 6 : 24,
          require_data_ownership: ['science_planetary', 'lunar', 'technology_demo'].includes(missionType),
          require_scheduling_control: ['science_planetary', 'lunar', 'technology_demo'].includes(missionType),
          max_annual_budget_keur: 2000,
          mission_type: missionType,
          num_spacecraft: ['communications', 'navigation'].includes(missionType) ? 4 : 1,
        }),
      })
      if (res.ok) setTradeResult(await res.json())
    } finally { setTradeLoading(false) }
  }

  // Create study + elements
  const createMission = async () => {
    setCreating(true)
    try {
      const name = missionName || `Mission-${Date.now().toString(36)}`
      const selectedAltData = tradeResult?.alternatives?.find((a: any) => a.name === selectedAlt)

      // Create study with full mission need
      const studyRes = await fetch(`${API}/studies/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirements: {
            name,
            mission_type: missionType,
            spacecraft_class: 'nano',
            orbit: { orbit_type: 'sso', altitude_km: 500, inclination_deg: 97.4, mission_duration_years: parseInt(lifetime), deorbit_required: true },
            payloads: [{ name: 'Payload', mass_kg: 1, power_w: 10, data_rate_mbps: 10, pointing_accuracy_deg: 1, duty_cycle_percent: 25 }],
            design_lifetime_years: parseInt(lifetime),
            target_mass_kg: parseFloat(massTarget),
            target_cost_meur: 2,
            ground_stations: ['KSAT Svalbard'],
          },
          mission_need: {
            problem_statement: problemStatement,
            operational_context: operationalContext,
            stakeholders: stakeholders.filter(s => s.name).map(s => ({
              id: s.id, name: s.name, role: s.role, needs: [s.need], constraints: [], priority: 'high',
            })),
            objectives: objectives.filter(o => o.text).map(o => ({
              id: o.id, text: o.text, priority: o.priority, type: 'performance',
              measurable_criterion: o.measurable_criterion, status: 'draft',
            })),
            alternatives: tradeResult?.alternatives?.slice(0, 5).map((a: any) => ({
              id: a.name, name: a.name, type: a.category, description: a.description,
              pros: a.pros || [], cons: a.cons || [], feasibility_score: a.total_score || 0.5,
              decision: a.name === selectedAlt ? 'selected' : 'rejected',
              decision_rationale: a.name === selectedAlt ? selectionRationale : '',
            })) || [],
            selected_alternative_id: selectedAlt,
            selection_rationale: selectionRationale,
            conops_summary: '',
          },
        }),
      })
      if (!studyRes.ok) { alert('Failed to create study'); return }
      const study = await studyRes.json()
      const studyId = study.id

      // Create mission root element
      const missionEl = await fetch(`${API}/elements/?study_id=${studyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, element_type: 'mission', segment: 'space' }),
      }).then(r => r.json())

      // Create segments from selected architecture
      const arch = ARCH_PRESETS.find(a => a.id === selectedArch)
      if (arch) {
        for (let i = 0; i < arch.segments.length; i++) {
          const seg = arch.segments[i]
          const segment = seg.toLowerCase().includes('ground') ? 'ground'
            : seg.toLowerCase().includes('launch') ? 'launch'
            : seg.toLowerCase().includes('operations') || seg.toLowerCase().includes('ops') ? 'operations'
            : seg.toLowerCase().includes('user') ? 'user'
            : 'space'
          await fetch(`${API}/elements/?study_id=${studyId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: seg, element_type: 'segment', segment,
              parent_id: missionEl.id,
              diagram_x: 80 + (i % 4) * 200, diagram_y: 40 + Math.floor(i / 4) * 140,
            }),
          })
        }
      }

      // Create initial mission-level requirements from objectives
      for (const obj of objectives.filter(o => o.text)) {
        await fetch(`${API}/requirements/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            study_id: studyId, element_id: missionEl.id, level: 'mission',
            text: `The mission shall ${obj.text}`,
            rationale: 'functional',
            verification_method: 'A', status: 'draft',
          }),
        })
      }

      setStudyId(studyId)
      qc.invalidateQueries()
    } finally {
      setCreating(false)
    }
  }

  // Load from file
  const handleLoad = () => {
    const input = document.createElement('input')
    input.type = 'file'; input.accept = '.json'
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0]; if (!file) return
      try {
        const data = JSON.parse(await file.text())
        if (!data.elements) { alert('Invalid save file'); return }
        const studyRes = await fetch(`${API}/studies/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ requirements: { name: 'Loaded Mission' }, mission_need: {} }),
        })
        if (!studyRes.ok) return
        const newStudy = await studyRes.json()
        const oldToNew = new Map<string, string>()
        const sorted: any[] = []; const remaining = [...data.elements]; const created = new Set<string>()
        while (remaining.length > 0) {
          const batch = remaining.filter((el: any) => !el.parent_id || created.has(el.parent_id))
          if (batch.length === 0) { sorted.push(...remaining); break }
          for (const el of batch) { sorted.push(el); created.add(el.id); remaining.splice(remaining.indexOf(el), 1) }
        }
        for (const el of sorted) {
          const res = await fetch(`${API}/elements/?study_id=${newStudy.id}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...el, id: undefined, study_id: undefined, parent_id: el.parent_id ? oldToNew.get(el.parent_id) || null : null }),
          })
          if (res.ok) { const c = await res.json(); oldToNew.set(el.id, c.id) }
        }
        if (data.interfaces) {
          for (const i of data.interfaces) {
            const from = oldToNew.get(i.from_element_id), to = oldToNew.get(i.to_element_id)
            if (from && to) await fetch(`${API}/interfaces/?study_id=${newStudy.id}`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ...i, id: undefined, from_element_id: from, to_element_id: to }),
            })
          }
        }
        setStudyId(newStudy.id); qc.invalidateQueries()
      } catch { alert('Load failed') }
    }
    input.click()
  }

  // Load example
  const handleExample = async () => {
    try {
      const res = await fetch(`${API}/lifecycle/example-missions`)
      const data = await res.json()
      const missions = data.missions || []
      if (missions.length === 0) { alert('No examples available'); return }
      const choice = prompt(missions.map((m: any, i: number) => `${i + 1}. ${m.name} — ${m.description}`).join('\n') + '\n\nEnter number:')
      if (!choice) return
      const idx = parseInt(choice) - 1
      if (idx < 0 || idx >= missions.length) return
      const full = await fetch(`${API}/lifecycle/example-missions/${missions[idx].id}`).then(r => r.json())
      const studyRes = await fetch(`${API}/studies/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: full.requirements || { name: missions[idx].name }, mission_need: full.mission_need || {} }),
      })
      if (studyRes.ok) { setStudyId((await studyRes.json()).id); qc.invalidateQueries() }
    } catch { alert('Failed to load example') }
  }

  // ─── HOME SCREEN ───
  if (step === 'home') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-primary)', gap: '1rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <h1 style={{ fontSize: '2rem', color: '#8B0000', fontWeight: 700, margin: 0 }}>SpaceCDF</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0.3rem 0' }}>Concurrent Design Facility</p>
          <p style={{ fontSize: '0.7rem', color: '#8B0000' }}>University of Ottawa — SEDTI</p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', width: 320 }}>
          <button onClick={() => setStep('problem')} style={{ ...wizBtn, background: 'var(--accent)', color: 'white', fontSize: '0.9rem', padding: '0.7rem' }}>
            Create New Mission
          </button>
          <button onClick={handleLoad} style={{ ...wizBtn, background: 'var(--bg-card)' }}>
            Load Existing Study
          </button>
          <button onClick={handleExample} style={{ ...wizBtn, background: 'var(--bg-card)', borderColor: '#8B0000', color: '#8B0000' }}>
            Load Example Mission
          </button>
        </div>
      </div>
    )
  }

  // ─── STEP 1: THE PROBLEM ───
  if (step === 'problem') {
    return (
      <WizardFrame step={1} title="What problem does this mission solve?" onBack={() => setStep('home')}
        onNext={() => setStep('stakeholders')} canNext={!!problemStatement}>
        <Field label="Mission Name">
          <input value={missionName} onChange={e => setMissionName(e.target.value)} placeholder="e.g., ArcticWatch-1" style={inputStyle} />
        </Field>
        <Field label="Problem Statement *" hint="What gap exists? Who is affected? What happens if we do nothing?">
          <textarea value={problemStatement} onChange={e => setProblemStatement(e.target.value)}
            placeholder="e.g., Agricultural monitoring in the Canadian prairies requires frequent multispectral imagery to detect crop stress early, but existing satellite data lacks the spatial resolution and revisit frequency needed for field-level decisions..."
            style={{ ...inputStyle, height: 100, resize: 'vertical' }} />
        </Field>
        <Field label="Operational Context" hint="When, where, and how will the mission products be used?">
          <textarea value={operationalContext} onChange={e => setOperationalContext(e.target.value)}
            placeholder="e.g., Data products will be delivered to farming cooperatives within 6 hours of acquisition during the growing season (May-September)..."
            style={{ ...inputStyle, height: 60, resize: 'vertical' }} />
        </Field>
        <Field label="Mission Type">
          <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
            {MISSION_TYPES.map(t => (
              <button key={t.value} onClick={() => setMissionType(t.value)} style={{
                padding: '0.3rem 0.6rem', fontSize: '0.7rem', borderRadius: '4px', cursor: 'pointer',
                background: missionType === t.value ? 'var(--accent)' : 'var(--bg-card)',
                color: missionType === t.value ? 'white' : 'var(--text-secondary)',
                border: `1px solid ${missionType === t.value ? 'var(--accent)' : 'var(--border)'}`,
              }}>
                {t.label}
              </button>
            ))}
          </div>
        </Field>
      </WizardFrame>
    )
  }

  // ─── STEP 2: STAKEHOLDERS & OBJECTIVES ───
  if (step === 'stakeholders') {
    const hasEnough = stakeholders.some(s => s.name) && objectives.filter(o => o.text).length >= 2
    return (
      <WizardFrame step={2} title="Who cares, and what do they need?" onBack={() => setStep('problem')}
        onNext={() => { runTradeAnalysis(); setStep('alternatives') }} canNext={hasEnough}>
        <Field label="Stakeholders" hint="Who benefits from, funds, or operates this mission?">
          {stakeholders.map((s, i) => (
            <div key={s.id} style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem' }}>
              <input value={s.name} onChange={e => { const n = [...stakeholders]; n[i].name = e.target.value; setStakeholders(n) }}
                placeholder="Name / organisation" style={{ ...inputStyle, flex: 1 }} />
              <select value={s.role} onChange={e => { const n = [...stakeholders]; n[i].role = e.target.value; setStakeholders(n) }}
                style={{ ...inputStyle, width: 130 }}>
                {STAKEHOLDER_ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
              <input value={s.need} onChange={e => { const n = [...stakeholders]; n[i].need = e.target.value; setStakeholders(n) }}
                placeholder="Key need" style={{ ...inputStyle, flex: 1 }} />
              {stakeholders.length > 1 && (
                <button onClick={() => setStakeholders(stakeholders.filter((_, j) => j !== i))}
                  style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>×</button>
              )}
            </div>
          ))}
          <button onClick={() => setStakeholders([...stakeholders, { id: String(Date.now()), name: '', role: 'user', need: '' }])}
            style={{ fontSize: '0.7rem', color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>
            + Add stakeholder
          </button>
        </Field>

        <Field label="Mission Objectives (minimum 2)" hint="What must the mission achieve? Be specific and measurable.">
          {objectives.map((o, i) => (
            <div key={o.id} style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem' }}>
              <select value={o.priority} onChange={e => { const n = [...objectives]; n[i].priority = e.target.value; setObjectives(n) }}
                style={{ ...inputStyle, width: 90 }}>
                <option value="primary">Primary</option>
                <option value="secondary">Secondary</option>
                <option value="constraint">Constraint</option>
              </select>
              <input value={o.text} onChange={e => { const n = [...objectives]; n[i].text = e.target.value; setObjectives(n) }}
                placeholder="e.g., Acquire 5m GSD multispectral imagery" style={{ ...inputStyle, flex: 2 }} />
              <input value={o.measurable_criterion} onChange={e => { const n = [...objectives]; n[i].measurable_criterion = e.target.value; setObjectives(n) }}
                placeholder="How to measure" style={{ ...inputStyle, flex: 1 }} />
              {objectives.length > 1 && (
                <button onClick={() => setObjectives(objectives.filter((_, j) => j !== i))}
                  style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>×</button>
              )}
            </div>
          ))}
          <button onClick={() => setObjectives([...objectives, { id: String(Date.now()), text: '', priority: 'secondary', measurable_criterion: '' }])}
            style={{ fontSize: '0.7rem', color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>
            + Add objective
          </button>
        </Field>
      </WizardFrame>
    )
  }

  // ─── STEP 3: IS SPACE THE RIGHT ANSWER? ───
  if (step === 'alternatives') {
    return (
      <WizardFrame step={3} title="Is space the right answer?" onBack={() => setStep('stakeholders')}
        onNext={() => setStep('architecture')} canNext={!!selectedAlt && !!selectionRationale}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', lineHeight: 1.5 }}>
          Before committing to a space mission, consider all alternatives.
          Could existing satellite data, commercial services, drones, or ground sensors meet your objectives?
        </div>

        {tradeLoading && <div style={{ color: 'var(--accent)', padding: '1rem', textAlign: 'center' }}>Analysing alternatives...</div>}

        {tradeResult?.alternatives && (
          <>
            {tradeResult.key_question && (
              <div style={{ padding: '0.4rem 0.5rem', background: 'rgba(245,158,11,0.1)', borderRadius: '4px', borderLeft: '3px solid var(--warning)', marginBottom: '0.5rem', fontSize: '0.72rem', color: 'var(--warning)' }}>
                Key question: {tradeResult.key_question}
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', marginBottom: '0.5rem', maxHeight: 300, overflow: 'auto' }}>
              {tradeResult.alternatives.map((alt: any) => (
                <button key={alt.name} onClick={() => setSelectedAlt(alt.name)}
                  style={{
                    padding: '0.4rem 0.5rem', borderRadius: '4px', textAlign: 'left', cursor: 'pointer',
                    background: selectedAlt === alt.name ? 'rgba(59,130,246,0.15)' : 'var(--bg-card)',
                    border: `2px solid ${selectedAlt === alt.name ? 'var(--accent)' : 'var(--border)'}`,
                    color: 'var(--text-primary)',
                  }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.15rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.78rem' }}>{alt.name}</span>
                    <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>#{alt.rank} — {alt.category}</span>
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{alt.description?.slice(0, 120)}</div>
                  {alt.gsd_m != null && (
                    <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                      GSD: {alt.gsd_m}m | Revisit: {alt.revisit_days}d | Cost: {alt.annual_cost_keur || alt.total_3yr_cost_keur} kEUR
                    </div>
                  )}
                </button>
              ))}
            </div>

            {selectedAlt && (
              <Field label="Why this approach?" hint="Explain why the selected alternative best meets the mission objectives.">
                <textarea value={selectionRationale} onChange={e => setSelectionRationale(e.target.value)}
                  placeholder="e.g., Existing commercial imagery (Sentinel-2, Planet) lacks the spectral bands needed for our specific crop stress detection algorithm. A dedicated instrument with custom band selection is required..."
                  style={{ ...inputStyle, height: 60, resize: 'vertical' }} />
              </Field>
            )}

            {tradeResult.recommendation && (
              <div style={{ padding: '0.3rem 0.5rem', background: 'rgba(16,185,129,0.1)', borderRadius: '4px', fontSize: '0.68rem', color: 'var(--success)', marginTop: '0.3rem' }}>
                {tradeResult.recommendation}
              </div>
            )}
          </>
        )}

        {!tradeResult && !tradeLoading && (
          <button onClick={runTradeAnalysis} style={{ ...wizBtn, background: 'var(--accent)', color: 'white' }}>
            Analyse Alternatives
          </button>
        )}
      </WizardFrame>
    )
  }

  // ─── STEP 4: INITIAL ARCHITECTURE ───
  if (step === 'architecture') {
    return (
      <WizardFrame step={4} title="Select starting architecture" onBack={() => setStep('alternatives')}
        onNext={createMission} canNext={!creating} nextLabel={creating ? 'Creating...' : 'Create Mission & Start Design'}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          Choose an initial architecture to start with. You can modify this later by adding, removing, or renaming segments.
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', marginBottom: '0.5rem' }}>
          {ARCH_PRESETS.map(arch => (
            <button key={arch.id} onClick={() => setSelectedArch(arch.id)}
              style={{
                padding: '0.4rem 0.5rem', borderRadius: '4px', textAlign: 'left', cursor: 'pointer',
                background: selectedArch === arch.id ? 'rgba(59,130,246,0.15)' : 'var(--bg-card)',
                border: `2px solid ${selectedArch === arch.id ? 'var(--accent)' : 'var(--border)'}`,
                color: 'var(--text-primary)',
              }}>
              <span style={{ fontWeight: 600 }}>{arch.name}</span>
              {arch.segments.length > 0 && (
                <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                  Segments: {arch.segments.join(' → ')}
                </div>
              )}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Field label="Design Lifetime (years)">
            <input type="number" value={lifetime} onChange={e => setLifetime(e.target.value)} style={{ ...inputStyle, width: 60 }} />
          </Field>
          <Field label="Target Mass (kg)">
            <input type="number" value={massTarget} onChange={e => setMassTarget(e.target.value)} style={{ ...inputStyle, width: 60 }} />
          </Field>
        </div>
      </WizardFrame>
    )
  }

  return null
}

// ─── Shared Components ───

function WizardFrame({ step, title, children, onBack, onNext, canNext, nextLabel }: {
  step: number; title: string; children: React.ReactNode
  onBack: () => void; onNext: () => void; canNext: boolean; nextLabel?: string
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div style={{ padding: '0.5rem 1rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '0.7rem', color: '#8B0000', fontWeight: 700 }}>SpaceCDF</span>
        <span style={{ color: 'var(--border)' }}>|</span>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Mission Definition</span>
        <span style={{ flex: 1 }} />
        {/* Step indicators */}
        {[1, 2, 3, 4].map(s => (
          <span key={s} style={{
            width: 20, height: 20, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.6rem', fontWeight: 700,
            background: s === step ? 'var(--accent)' : s < step ? 'var(--success)' : 'var(--bg-card)',
            color: s <= step ? 'white' : 'var(--text-secondary)',
            border: `1px solid ${s === step ? 'var(--accent)' : s < step ? 'var(--success)' : 'var(--border)'}`,
          }}>{s < step ? '✓' : s}</span>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto', padding: '1.5rem', maxWidth: 700, margin: '0 auto', width: '100%' }}>
        <h2 style={{ fontSize: '1.1rem', margin: '0 0 1rem', color: 'var(--text-primary)' }}>
          Step {step}: {title}
        </h2>
        {children}
      </div>

      {/* Footer */}
      <div style={{ padding: '0.5rem 1rem', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between' }}>
        <button onClick={onBack} style={{ ...wizBtn, background: 'var(--bg-card)', width: 100 }}>← Back</button>
        <button onClick={onNext} disabled={!canNext} style={{
          ...wizBtn, background: canNext ? 'var(--accent)' : 'var(--border)',
          color: 'white', width: 200, opacity: canNext ? 1 : 0.5,
        }}>
          {nextLabel || 'Next →'}
        </button>
      </div>
    </div>
  )
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.2rem' }}>
        {label}
      </label>
      {hint && <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{hint}</div>}
      {children}
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  padding: '0.4rem 0.5rem', fontSize: '0.78rem', borderRadius: '4px', width: '100%',
  background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)',
}

const wizBtn: React.CSSProperties = {
  padding: '0.4rem 0.75rem', fontSize: '0.78rem', fontWeight: 600, borderRadius: '4px',
  border: '1px solid var(--border)', cursor: 'pointer', color: 'var(--text-secondary)',
  background: 'var(--bg-card)',
}
