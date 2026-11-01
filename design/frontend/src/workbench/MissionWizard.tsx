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
import { useTranslation } from 'react-i18next'
import i18n, { fmtDate } from '../i18n'
import { fs } from '../theme/tokens'
import { Dialog, askConfirm, showAlert } from '../components/ui/Dialog'
import { HomeFrame } from '../components/ui/HomeFrame'

const API = '/api'

type WizardStep = 'home' | 'problem' | 'stakeholders' | 'alternatives' | 'architecture'

interface Stakeholder {
  id: string; name: string; role: string; need: string
}

interface Objective {
  id: string; text: string; priority: string; measurable_criterion: string
}

const MISSION_TYPES = [
  { value: 'earth_observation', desc: 'Imaging, SAR, multispectral' },
  { value: 'communications', desc: 'Data relay, IoT, broadband' },
  { value: 'navigation', desc: 'PNT, GNSS augmentation' },
  { value: 'science_planetary', desc: 'Lunar, Mars, asteroid' },
  { value: 'science_heliophysics', desc: 'Solar, magnetosphere' },
  { value: 'technology_demo', desc: 'In-orbit validation' },
  { value: 'lunar', desc: 'Cislunar, lunar orbit/surface' },
]

// English text is the i18n key: mission-type button labels (value → label).
const MISSION_TYPE_LABELS: Record<string, string> = {
  earth_observation: 'Earth Observation',
  communications: 'Communications',
  navigation: 'Navigation',
  science_planetary: 'Science (Planetary)',
  science_heliophysics: 'Science (Heliophysics)',
  technology_demo: 'Technology Demo',
  lunar: 'Lunar Mission',
}

// English text is the i18n key: stakeholder role labels (stored value → label).
const STAKEHOLDER_ROLES: Record<string, string> = {
  sponsor: 'Sponsor / Funder',
  user: 'End User',
  operator: 'Operator',
  science_pi: 'Science PI',
  regulator: 'Regulator',
  partner: 'Partner Organisation',
}

// English text is the i18n key for the segments at display time; the segment
// names themselves are POSTed as element names (stored data) and stay English.
const ARCH_PRESETS = [
  { id: 'single-leo', segments: ['Space Segment', 'Ground Segment', 'Launch Segment', 'Operations'] },
  { id: 'constellation', segments: ['Space Segment', 'Ground Segment', 'Launch Segment', 'User Segment', 'Operations'] },
  { id: 'lunar', segments: ['Space Segment', 'Ground Segment (DSN)', 'Launch Segment', 'Operations'] },
  { id: 'hybrid', segments: ['Space Segment', 'Ground Sensors', 'Ground Station', 'Data Centre', 'Operations'] },
  { id: 'blank', segments: [] },
]

// English text is the i18n key: architecture preset names (id → name), display only.
const ARCH_PRESET_NAMES: Record<string, string> = {
  'single-leo': 'Single Spacecraft (LEO)',
  constellation: 'Constellation',
  lunar: 'Lunar / Deep Space',
  hybrid: 'Hybrid Space + Ground',
  blank: 'Start Blank',
}

export function MissionWizard() {
  const { t } = useTranslation()
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
      if (!studyRes.ok) { void showAlert(i18n.t('Failed to create study')); return }
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
        if (!data.elements) { void showAlert(i18n.t('Invalid save file')); return }
        const studyReq = data.studyMetadata?.requirements || { name: data.studyMetadata?.name || 'Loaded Mission' }
        const studyNeed = data.studyMetadata?.mission_need || {}
        const studyRes = await fetch(`${API}/studies/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ requirements: studyReq, mission_need: studyNeed }),
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
        // Restore requirements
        if (data.requirements) {
          for (const req of data.requirements) {
            const elementId = req.element_id ? oldToNew.get(req.element_id) : undefined
            await fetch(`${API}/requirements/`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ...req, id: undefined, study_id: newStudy.id, element_id: elementId || undefined, derived_from_requirement_id: undefined }),
            })
          }
        }
        // Restore budget allocations
        if (data.allocations) {
          for (const alloc of data.allocations) {
            const elementId = oldToNew.get(alloc.element_id)
            if (elementId) {
              await fetch(`${API}/elements/${elementId}/allocations`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ budget_type: alloc.budget_type, allocation_value: alloc.allocation_value, unit: alloc.unit || '', source: alloc.source || 'loaded', rationale: alloc.rationale || '' }),
              })
            }
          }
        }
        // Restore risk register and pugh matrix to localStorage
        if (data.riskRegister?.length > 0) {
          localStorage.setItem(`spacecdf-risks-${newStudy.id}`, JSON.stringify(data.riskRegister))
        }
        if (data.pughMatrix && Object.keys(data.pughMatrix).length > 0) {
          localStorage.setItem('spacecdf-pugh', JSON.stringify(data.pughMatrix))
        }
        // Restore UI state
        setStudyId(newStudy.id)
        if (data.uiState?.breadcrumb) {
          const mapped = data.uiState.breadcrumb
            .map((c: any) => ({ id: oldToNew.get(c.id) || c.id, name: c.name }))
            .filter((c: any) => c.id)
          for (const crumb of mapped) { useUIStore.getState().drillInto(crumb.id, crumb.name) }
        }
        qc.invalidateQueries()
      } catch { void showAlert(i18n.t('Load failed')) }
    }
    input.click()
  }

  // Load example: pick from a card list (replaces the old numbered window.prompt)
  const [examples, setExamples] = useState<Array<{ id: string; name: string; description: string }> | null>(null)
  const [loadingExample, setLoadingExample] = useState<string | null>(null)
  const openExamples = async () => {
    try {
      const res = await fetch(`${API}/lifecycle/example-missions`)
      const data = await res.json()
      const missions = data.missions || []
      if (missions.length === 0) { void showAlert(i18n.t('No examples available')); return }
      setExamples(missions)
    } catch { void showAlert(i18n.t('Failed to load example')) }
  }
  const loadExample = async (m: { id: string; name: string }) => {
    setLoadingExample(m.id)
    try {
      const full = await fetch(`${API}/lifecycle/example-missions/${m.id}`).then(r => r.json())
      const studyRes = await fetch(`${API}/studies/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: full.requirements || { name: m.name }, mission_need: full.mission_need || {} }),
      })
      if (studyRes.ok) { setExamples(null); setStudyId((await studyRes.json()).id); qc.invalidateQueries() }
      else void showAlert(i18n.t('Failed to load example'))
    } catch { void showAlert(i18n.t('Failed to load example')) }
    finally { setLoadingExample(null) }
  }

  // ─── HOME SCREEN ───
  if (step === 'home') {
    const row: React.CSSProperties = {
      display: 'grid', gridTemplateColumns: 'minmax(180px, 220px) 1fr', alignItems: 'center',
      columnGap: 'var(--sp-4)', rowGap: 'var(--sp-1)', padding: 'var(--sp-3) 0', borderTop: '1px solid var(--line)',
    }
    const note: React.CSSProperties = { fontSize: fs.body, color: 'var(--text-2)', margin: 0, minWidth: 0 }
    return (
      <HomeFrame title={t('Start a design study')} lead={t('Define a new mission from the problem up, join a study already in progress, or open a saved or example design.')}>
        <div className="c2o-home" style={{ maxWidth: 760 }}>
          <div style={row}>
            <button type="button" className="c2o-btn c2o-btn--primary c2o-btn--lg" onClick={() => setStep('problem')}>
              {t('Create New Mission')}
            </button>
            <p style={note}>{t('Four guided steps: problem, stakeholders, alternatives, initial architecture.')}</p>
          </div>
          <div style={{ ...row, alignItems: 'start' }}>
            <ActiveStudies onJoin={(id) => { setStudyId(id); qc.invalidateQueries() }} />
          </div>
          <div style={row}>
            <button type="button" className="c2o-btn" onClick={handleLoad}>{t('Load from File')}</button>
            <p style={note}>{t('Open a .json design saved from the workbench.')}</p>
          </div>
          <div style={{ ...row, borderBottom: '1px solid var(--line)' }}>
            <button type="button" className="c2o-btn" onClick={openExamples}>{t('Load Example Mission')}</button>
            <p style={note}>{t('Start from a worked CubeSat mission.')}</p>
          </div>
        </div>
        <Dialog open={!!examples} title={t('Example missions')} onClose={() => setExamples(null)} width={560}
          actions={<button type="button" className="c2o-btn" onClick={() => setExamples(null)}>{t('Cancel')}</button>}>
          <ul role="list" style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
            {(examples || []).map(m => (
              <li key={m.id}>
                <button type="button" data-example-card={m.id} className="c2o-example-card"
                  onClick={() => loadExample(m)} disabled={!!loadingExample} aria-busy={loadingExample === m.id}>
                  <span className="c2o-example-card__name">{m.name}</span>
                  <span className="c2o-example-card__desc">{m.description}</span>
                  {loadingExample === m.id && <span className="c2o-example-card__desc">{t('Loading...')}</span>}
                </button>
              </li>
            ))}
          </ul>
        </Dialog>
      </HomeFrame>
    )
  }

  // ─── STEP 1: THE PROBLEM ───
  if (step === 'problem') {
    return (
      <WizardFrame step={1} title={t('What problem does this mission solve?')} onBack={() => setStep('home')}
        onNext={() => setStep('stakeholders')} canNext={!!problemStatement}>
        <Field label={t('Mission Name')}>
          <input value={missionName} onChange={e => setMissionName(e.target.value)} placeholder={t('e.g., ArcticWatch-1')} style={inputStyle} />
        </Field>
        <Field label={t('Problem Statement *')} hint={t('What gap exists? Who is affected? What happens if we do nothing?')}>
          <textarea value={problemStatement} onChange={e => setProblemStatement(e.target.value)}
            placeholder={t('e.g., Agricultural monitoring in the Canadian prairies requires frequent multispectral imagery to detect crop stress early, but existing satellite data lacks the spatial resolution and revisit frequency needed for field-level decisions...')}
            style={{ ...inputStyle, height: 100, resize: 'vertical' }} />
        </Field>
        <Field label={t('Operational Context')} hint={t('When, where, and how will the mission products be used?')}>
          <textarea value={operationalContext} onChange={e => setOperationalContext(e.target.value)}
            placeholder={t('e.g., Data products will be delivered to farming cooperatives within 6 hours of acquisition during the growing season (May-September)...')}
            style={{ ...inputStyle, height: 60, resize: 'vertical' }} />
        </Field>
        <Field label={t('Mission Type')}>
          <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
            {MISSION_TYPES.map(mt => (
              <button key={mt.value} onClick={() => setMissionType(mt.value)} style={{
                padding: '0.3rem 0.6rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
                background: missionType === mt.value ? 'var(--accent)' : 'var(--bg-card)',
                color: missionType === mt.value ? 'white' : 'var(--text-secondary)',
                border: `1px solid ${missionType === mt.value ? 'var(--accent)' : 'var(--border)'}`,
              }}>
                {t(MISSION_TYPE_LABELS[mt.value])}
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
      <WizardFrame step={2} title={t('Who cares, and what do they need?')} onBack={() => setStep('problem')}
        onNext={() => { runTradeAnalysis(); setStep('alternatives') }} canNext={hasEnough}>
        <Field label={t('Stakeholders')} hint={t('Who benefits from, funds, or operates this mission?')}>
          {stakeholders.map((s, i) => (
            <div key={s.id} style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem' }}>
              <input value={s.name} onChange={e => { const n = [...stakeholders]; n[i].name = e.target.value; setStakeholders(n) }}
                placeholder={t('Name / organisation')} style={{ ...inputStyle, flex: 1 }} />
              <select value={s.role} onChange={e => { const n = [...stakeholders]; n[i].role = e.target.value; setStakeholders(n) }}
                style={{ ...inputStyle, width: 130 }}>
                {Object.entries(STAKEHOLDER_ROLES).map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
              </select>
              <input value={s.need} onChange={e => { const n = [...stakeholders]; n[i].need = e.target.value; setStakeholders(n) }}
                placeholder={t('Key need')} style={{ ...inputStyle, flex: 1 }} />
              {stakeholders.length > 1 && (
                <button onClick={() => setStakeholders(stakeholders.filter((_, j) => j !== i))}
                  style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>×</button>
              )}
            </div>
          ))}
          <button onClick={() => setStakeholders([...stakeholders, { id: String(Date.now()), name: '', role: 'user', need: '' }])}
            style={{ fontSize: fs.label, color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>
            {t('+ Add stakeholder')}
          </button>
        </Field>

        <Field label={t('Mission Objectives (minimum 2)')} hint={t('What must the mission achieve? Be specific and measurable.')}>
          {objectives.map((o, i) => (
            <div key={o.id} style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.3rem' }}>
              <select value={o.priority} onChange={e => { const n = [...objectives]; n[i].priority = e.target.value; setObjectives(n) }}
                style={{ ...inputStyle, width: 90 }}>
                <option value="primary">{t('Primary')}</option>
                <option value="secondary">{t('Secondary', { context: 'priority' })}</option>
                <option value="constraint">{t('Constraint', { context: 'priority' })}</option>
              </select>
              <input value={o.text} onChange={e => { const n = [...objectives]; n[i].text = e.target.value; setObjectives(n) }}
                placeholder={t('e.g., Acquire 5m GSD multispectral imagery')} style={{ ...inputStyle, flex: 2 }} />
              <input value={o.measurable_criterion} onChange={e => { const n = [...objectives]; n[i].measurable_criterion = e.target.value; setObjectives(n) }}
                placeholder={t('How to measure')} style={{ ...inputStyle, flex: 1 }} />
              {objectives.length > 1 && (
                <button onClick={() => setObjectives(objectives.filter((_, j) => j !== i))}
                  style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>×</button>
              )}
            </div>
          ))}
          <button onClick={() => setObjectives([...objectives, { id: String(Date.now()), text: '', priority: 'secondary', measurable_criterion: '' }])}
            style={{ fontSize: fs.label, color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>
            {t('+ Add objective')}
          </button>
        </Field>
      </WizardFrame>
    )
  }

  // ─── STEP 3: IS SPACE THE RIGHT ANSWER? ───
  if (step === 'alternatives') {
    return (
      <WizardFrame step={3} title={t('Is space the right answer?')} onBack={() => setStep('stakeholders')}
        onNext={() => setStep('architecture')} canNext={!!selectedAlt && !!selectionRationale}>
        <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.5rem', lineHeight: 1.5 }}>
          {t('Before committing to a space mission, consider all alternatives. Could existing satellite data, commercial services, drones, or ground sensors meet your objectives?')}
        </div>

        {tradeLoading && <div style={{ color: 'var(--accent)', padding: '1rem', textAlign: 'center' }}>{t('Analysing alternatives...')}</div>}

        {tradeResult?.alternatives && (
          <>
            {tradeResult.key_question && (
              <div style={{ padding: '0.4rem 0.5rem', background: 'rgba(245,158,11,0.1)', borderRadius: '4px', borderLeft: '3px solid var(--warning)', marginBottom: '0.5rem', fontSize: fs.label, color: 'var(--warning)' }}>
                {t('Key question: {{question}}', { question: tradeResult.key_question })}
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
                    <span style={{ fontWeight: 600, fontSize: fs.label }}>{alt.name}</span>
                    <span style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>#{alt.rank} — {alt.category}</span>
                  </div>
                  <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{alt.description?.slice(0, 120)}</div>
                  {alt.gsd_m != null && (
                    <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                      {t('GSD: {{gsd}}m | Revisit: {{revisit}}d | Cost: {{cost}} kEUR', { gsd: alt.gsd_m, revisit: alt.revisit_days, cost: alt.annual_cost_keur || alt.total_3yr_cost_keur })}
                    </div>
                  )}
                </button>
              ))}
            </div>

            {selectedAlt && (
              <Field label={t('Why this approach?')} hint={t('Explain why the selected alternative best meets the mission objectives.')}>
                <textarea value={selectionRationale} onChange={e => setSelectionRationale(e.target.value)}
                  placeholder={t('e.g., Existing commercial imagery (Sentinel-2, Planet) lacks the spectral bands needed for our specific crop stress detection algorithm. A dedicated instrument with custom band selection is required...')}
                  style={{ ...inputStyle, height: 60, resize: 'vertical' }} />
              </Field>
            )}

            {tradeResult.recommendation && (
              <div style={{ padding: '0.3rem 0.5rem', background: 'rgba(16,185,129,0.1)', borderRadius: '4px', fontSize: fs.label, color: 'var(--success)', marginTop: '0.3rem' }}>
                {tradeResult.recommendation}
              </div>
            )}
          </>
        )}

        {!tradeResult && !tradeLoading && (
          <button onClick={runTradeAnalysis} style={{ ...wizBtn, background: 'var(--accent)', color: 'white' }}>
            {t('Analyse Alternatives')}
          </button>
        )}
      </WizardFrame>
    )
  }

  // ─── STEP 4: INITIAL ARCHITECTURE ───
  if (step === 'architecture') {
    return (
      <WizardFrame step={4} title={t('Select starting architecture')} onBack={() => setStep('alternatives')}
        onNext={createMission} canNext={!creating} nextLabel={creating ? t('Creating...') : t('Create Mission & Start Design')}>
        <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          {t('Choose an initial architecture to start with. You can modify this later by adding, removing, or renaming segments.')}
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
              <span style={{ fontWeight: 600 }}>{t(ARCH_PRESET_NAMES[arch.id])}</span>
              {arch.segments.length > 0 && (
                <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                  {t('Segments: {{list}}', { list: arch.segments.map(sg => t(sg)).join(' → ') })}
                </div>
              )}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Field label={t('Design Lifetime (years)')}>
            <input type="number" value={lifetime} onChange={e => setLifetime(e.target.value)} style={{ ...inputStyle, width: 60 }} />
          </Field>
          <Field label={t('Target Mass (kg)')}>
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
  const { t } = useTranslation()
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-primary)' }}>
      {/* Header */}
      {/* right padding keeps the step dots clear of the fixed language toggle (App.tsx) */}
      <div style={{ padding: '0.5rem 7rem 0.5rem 1rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: fs.label, color: 'var(--brand)', fontWeight: 700 }}>SpaceCDF</span>
        <span style={{ color: 'var(--border)' }}>|</span>
        <span style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{t('Mission Definition')}</span>
        <span style={{ flex: 1 }} />
        {/* Step indicators */}
        {[1, 2, 3, 4].map(s => (
          <span key={s} style={{
            width: 20, height: 20, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: fs.label, fontWeight: 700,
            background: s === step ? 'var(--accent)' : s < step ? 'var(--success)' : 'var(--bg-card)',
            color: s <= step ? 'white' : 'var(--text-secondary)',
            border: `1px solid ${s === step ? 'var(--accent)' : s < step ? 'var(--success)' : 'var(--border)'}`,
          }}>{s < step ? '✓' : s}</span>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto', padding: '1.5rem', maxWidth: 700, margin: '0 auto', width: '100%' }}>
        <h2 style={{ fontSize: fs.title, margin: '0 0 1rem', color: 'var(--text-primary)' }}>
          {t('Step {{step}}: {{title}}', { step, title })}
        </h2>
        {children}
      </div>

      {/* Footer */}
      <div style={{ padding: '0.5rem 1rem', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between' }}>
        <button onClick={onBack} style={{ ...wizBtn, background: 'var(--bg-card)', width: 100 }}>{t('← Back')}</button>
        <button onClick={onNext} disabled={!canNext} style={{
          ...wizBtn, background: canNext ? 'var(--accent)' : 'var(--border)',
          color: 'white', width: 200, opacity: canNext ? 1 : 0.5,
        }}>
          {nextLabel || t('Next →')}
        </button>
      </div>
    </div>
  )
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <label style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.2rem' }}>
        {label}
      </label>
      {hint && <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{hint}</div>}
      {children}
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  padding: '0.4rem 0.5rem', fontSize: fs.label, borderRadius: '4px', width: '100%',
  background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)',
}

const wizBtn: React.CSSProperties = {
  padding: '0.4rem 0.75rem', fontSize: fs.label, fontWeight: 600, borderRadius: '4px',
  border: '1px solid var(--border)', cursor: 'pointer', color: 'var(--text-secondary)',
  background: 'var(--bg-card)',
}

// ─── Active Studies List ───

function ActiveStudies({ onJoin }: { onJoin: (studyId: string) => void }) {
  const { t } = useTranslation()
  const directJoin = useCallback((id: string) => {
    useUIStore.getState().setStudyId(id)
    // Also reset breadcrumb to root
    useUIStore.getState().drillUp(-1)
    onJoin(id)
  }, [onJoin])
  const [studies, setStudies] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const refresh = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/studies/`)
      if (res.ok) {
        const data = await res.json()
        // API may return array or {studies: [...]}
        const list = Array.isArray(data) ? data : (data.studies || [])
        setStudies(list)
      }
    } finally { setLoading(false) }
  }

  if (!expanded) {
    return (
      <>
        <button type="button" className="c2o-btn" aria-expanded={false} onClick={() => { setExpanded(true); refresh() }}>
          {t('Join Active Study')}
        </button>
        <p style={{ fontSize: fs.body, color: 'var(--text-2)', margin: 0 }}>{t('Work on a study with your team in real time.')}</p>
      </>
    )
  }

  return (
    <div style={{ gridColumn: '1 / -1', padding: 'var(--sp-2) var(--sp-3)', borderRadius: 'var(--radius)', background: 'var(--surface-1)', border: '1px solid var(--line-strong)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', marginBottom: 'var(--sp-2)' }}>
        <h2 style={{ fontWeight: 600, fontSize: fs.body, margin: 0 }}>{t('Active Studies')}</h2>
        <span style={{ flex: 1 }} />
        <button type="button" className="c2o-btn c2o-btn--quiet" onClick={refresh} disabled={loading}>
          {loading ? t('Loading...') : t('Refresh')}
        </button>
        <button type="button" className="c2o-btn" aria-expanded={true} onClick={() => setExpanded(false)}>
          {t('Close')}
        </button>
      </div>

      {studies.length === 0 ? (
        <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', padding: '0.3rem 0' }}>
          {loading ? t('Loading...') : t('No active studies found. Create a new mission to start.')}
        </div>
      ) : (
        <>
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
            {t('{{count}} studies — most recent first', { count: studies.length, defaultValue_one: '{{count}} studies — most recent first' })}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', maxHeight: 200, overflow: 'auto' }}>
            {studies.slice().reverse().map((s: any) => (
              <div key={s.id} style={{
                display: 'flex', alignItems: 'center', gap: '0.3rem',
                padding: '0.3rem 0.5rem', borderRadius: '4px',
                background: 'var(--bg-primary)', border: '1px solid var(--border)',
              }}>
                <button type="button" onClick={() => directJoin(s.id)} style={{
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--interactive)',
                  fontWeight: 600, fontSize: fs.body, flex: 1, textAlign: 'left', padding: 0, minHeight: 24,
                }}>
                  {s.name || s.id}
                </button>
                {s.phase && (
                  <span style={{ fontSize: fs.label, color: 'var(--accent)', textTransform: 'uppercase' }}>{s.phase}</span>
                )}
                {s.created && (
                  <span style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>
                    {fmtDate(s.created, {})}
                  </span>
                )}
                <button onClick={async (e) => {
                  e.stopPropagation()
                  if (!(await askConfirm(t('Delete study "{{name}}"? This cannot be undone.', { name: s.name || s.id }), { danger: true, confirmLabel: t('Delete') }))) return
                  await fetch(`${API}/studies/${s.id}`, { method: 'DELETE' })
                  refresh()
                }} style={{
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger)',
                  fontSize: fs.label, padding: '0 0.2rem', flexShrink: 0,
                }} title={t('Delete study')} aria-label={t('Delete study')}>
                  ×
                </button>
              </div>
            ))}
          </div>
          {studies.length > 5 && (
            <button onClick={async () => {
              if (!(await askConfirm(t('Delete all {{count}} studies? This cannot be undone.', { count: studies.length }), { danger: true, confirmLabel: t('Delete') }))) return
              for (const s of studies) { await fetch(`${API}/studies/${s.id}`, { method: 'DELETE' }) }
              refresh()
            }} style={{ fontSize: fs.label, color: 'var(--danger)', background: 'none', border: 'none', cursor: 'pointer', marginTop: '0.2rem' }}>
              {t('Delete all studies')}
            </button>
          )}
        </>
      )}
    </div>
  )
}
