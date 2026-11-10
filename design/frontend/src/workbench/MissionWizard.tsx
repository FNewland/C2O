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
import { useState, useCallback, useEffect } from 'react'
import { useUIStore } from '../stores/uiStore'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import i18n, { fmtDate } from '../i18n'
import { Note } from '../components/ui/Panel'
import { Tag } from '../components/ui/StatusBadge'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import { LanguageToggle } from '../i18n/LanguageToggle'
import { Dialog, askConfirm, showAlert } from '../components/ui/Dialog'
import { HomeFrame } from '../components/ui/HomeFrame'
import { useSeatStore } from '../seats/api'
import { useWhereStore } from '../where/where'
import { LogbookBanner, LogbookButton, RecordDecision, useLogbookUI } from '../logbook'
import { MissionDefinitionFields } from './MissionDefinitionFields'
import { defaultMissionDef, toRequirements, validateDraft, type MissionDefDraft } from './missionDef'

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

// English text is the i18n key for the tree at display time. The tree itself is built by
// the server (POST /studies/{id}/product-tree/default, services/product_tree.py ARCHITECTURES):
// Mission → segments → systems (a Spacecraft gets the standard subsystems) — the ECSS levels.
// Element names are stored data and stay English.
const ARCH_PRESETS: Array<{ id: string; segments: Array<{ name: string; systems: string[]; qty?: number }> }> = [
  { id: 'single-leo', segments: [
    { name: 'Space Segment', systems: ['Spacecraft'] }, { name: 'Ground Segment', systems: ['Ground Station'] },
    { name: 'Launch Segment', systems: [] }, { name: 'Operations', systems: [] }] },
  { id: 'constellation', segments: [
    { name: 'Space Segment', systems: ['Spacecraft'], qty: 4 }, { name: 'Ground Segment', systems: ['Ground Station'] },
    { name: 'Launch Segment', systems: [] }, { name: 'User Segment', systems: [] }, { name: 'Operations', systems: [] }] },
  { id: 'lunar', segments: [
    { name: 'Space Segment', systems: ['Spacecraft'] }, { name: 'Ground Segment (DSN)', systems: ['DSN Ground Station'] },
    { name: 'Launch Segment', systems: [] }, { name: 'Operations', systems: [] }] },
  { id: 'hybrid', segments: [
    { name: 'Space Segment', systems: ['Spacecraft'] },
    { name: 'Ground Segment', systems: ['Ground Station', 'Ground Sensors', 'Data Centre'] },
    { name: 'Operations', systems: [] }] },
  { id: 'blank', segments: [] },
]

/** "Space Segment (Spacecraft) → Ground Segment (Ground Station) → …", translated. */
function archSummary(arch: (typeof ARCH_PRESETS)[number], t: TFunction): string {
  return arch.segments.map(sg => (sg.systems.length
    ? `${t(sg.name)} (${sg.systems.map(x => t(x)).join(', ')}${sg.qty ? ` ×${sg.qty}` : ''})` : t(sg.name))).join(' → ')
}

// English text is the i18n key: architecture preset names (id → name), display only.
const ARCH_PRESET_NAMES: Record<string, string> = {
  'single-leo': 'Single Spacecraft (LEO)',
  constellation: 'Constellation',
  lunar: 'Lunar / Deep Space',
  hybrid: 'Hybrid Space + Ground',
  blank: 'Start Blank',
}

export function MissionWizard() {
  const seatCatalogue = useSeatStore(st => st.catalogue)
  const { t } = useTranslation()
  const setStudyId = useUIStore(s => s.setStudyId)
  const qc = useQueryClient()

  const [step, setStep] = useState<WizardStep>('home')
  // The logbook captures the wizard step as context and offers its worksheets.
  useEffect(() => {
    useLogbookUI.getState().setWizardStep(step)
    return () => useLogbookUI.getState().setWizardStep(null)
  }, [step])
  const [creating, setCreating] = useState(false)
  // "Where in SpaceCDF" links from the logbook open a step (where/where.ts checks it is reachable)
  const whereStep = useWhereStore(s => s.wizard)
  useEffect(() => { if (whereStep) setStep(whereStep.step as WizardStep) }, [whereStep?.n])  // eslint-disable-line react-hooks/exhaustive-deps

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
  // Orbit, payload, class, lifetime, launch / disposal, link (editable later: Traceability › Mission need)
  const [missionDef, setMissionDef] = useState<MissionDefDraft>(defaultMissionDef)
  const lifetime = missionDef.design_lifetime_years
  const massTarget = missionDef.target_mass_kg
  const defErrors = validateDraft(missionDef)
  // Seats (WP9): team size chosen at creation; "solo" = no seats (everyone edits everything).
  const [teamSize, setTeamSize] = useState<string>('9')
  const [optionalSeats, setOptionalSeats] = useState<string[]>([])

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
            ...toRequirements(missionDef),
            target_cost_meur: 2,
            // Stations with coordinates are added in Analyses › Ground segment (elements)
            ground_stations: [],
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
            // The model field is alternatives_considered (an `alternatives` key was dropped
            // silently), and every ranked option is kept: the chosen one may be below #5 (WP0).
            // `type` is the trade category; the server maps it to an AlternativeType.
            alternatives_considered: tradeResult?.alternatives?.map((a: any) => ({
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

      // The starting product tree (ECSS levels): Mission → segments → Spacecraft → standard
      // subsystems, Ground Segment → ground station. Built by the server in one call.
      const tree = await fetch(`${API}/studies/${studyId}/product-tree/default`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ architecture: selectedArch, mission_name: name, spacecraft_class: missionDef.spacecraft_class }),
      }).then(r => (r.ok ? r.json() : null))
      const missionEl = { id: tree?.mission_id as string | undefined }

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

      // Seats last: the tree above is built while the study is still open to everyone.
      if (teamSize !== 'solo') {
        await fetch(`${API}/studies/${encodeURIComponent(studyId)}/team/preset`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ team_size: teamSize, optional: optionalSeats }),
        })
        useSeatStore.getState().setDrawer('seats')
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
        // Restore the team records to the new study on the server (WP0: they were localStorage)
        if (data.riskRegister?.length > 0) {
          await fetch(`${API}/studies/${newStudy.id}/risks/import`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ risks: data.riskRegister, only_if_empty: false }),
          })
        }
        if (data.pughMatrix && Object.keys(data.pughMatrix).length > 0) {
          await fetch(`${API}/studies/${newStudy.id}/trades/pugh`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: data.pughMatrix }),
          })
        }
        // Restore UI state
        setStudyId(newStudy.id)
        if (data.uiState?.breadcrumb) {
          const mapped = data.uiState.breadcrumb
            .map((c: any) => ({ id: oldToNew.get(c.id) || c.id, name: c.name, type: c.type }))
            .filter((c: any) => c.id)
          for (const crumb of mapped) { useUIStore.getState().drillInto(crumb.id, crumb.name, crumb.type) }
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
      // The server builds the study WITH the example's element tree and design result
      // (WP0: posting only requirements + mission need opened the example with no elements).
      const studyRes = await fetch(`${API}/lifecycle/example-missions/${encodeURIComponent(m.id)}/load`, { method: 'POST' })
      if (studyRes.ok) { setExamples(null); setStudyId((await studyRes.json()).id); qc.invalidateQueries() }
      else void showAlert(i18n.t('Failed to load example'))
    } catch { void showAlert(i18n.t('Failed to load example')) }
    finally { setLoadingExample(null) }
  }

  // ─── HOME SCREEN ───
  if (step === 'home') {
    return (
      <HomeFrame logbook title={t('Start a design study')} lead={t('Define a new mission from the problem up, join a study already in progress, or open a saved or example design.')}>
        <div className="c2o-home">
          <div className="c2o-home__row">
            <button type="button" className="c2o-btn c2o-btn--primary c2o-btn--lg" onClick={() => setStep('problem')}>
              {t('Create New Mission')}
            </button>
            <p className="c2o-home__note">{t('Four guided steps: problem, stakeholders, alternatives, initial architecture.')}</p>
          </div>
          <div className="c2o-home__row ai-s">
            <ActiveStudies onJoin={(id) => { setStudyId(id); qc.invalidateQueries() }} />
          </div>
          <div className="c2o-home__row">
            <button type="button" className="c2o-btn" onClick={handleLoad}>{t('Load from File')}</button>
            <p className="c2o-home__note">{t('Open a .json design saved from the workbench.')}</p>
          </div>
          <div className="c2o-home__row c2o-home__row--last">
            <button type="button" className="c2o-btn" onClick={openExamples}>{t('Load Example Mission')}</button>
            <p className="c2o-home__note">{t('Start from a worked CubeSat mission.')}</p>
          </div>
        </div>
        <Dialog open={!!examples} title={t('Example missions')} onClose={() => setExamples(null)} width={560}
          actions={<button type="button" className="c2o-btn" onClick={() => setExamples(null)}>{t('Cancel')}</button>}>
          <ul role="list" className="list-reset m-0 p-0 stack gap-2">
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
          <input value={missionName} onChange={e => setMissionName(e.target.value)} placeholder={t('e.g., ArcticWatch-1')} className="c2o-input" />
        </Field>
        <Field label={t('Problem Statement *')} hint={t('What gap exists? Who is affected? What happens if we do nothing?')}>
          <textarea value={problemStatement} onChange={e => setProblemStatement(e.target.value)}
            placeholder={t('e.g., Agricultural monitoring in the Canadian prairies requires frequent multispectral imagery to detect crop stress early, but existing satellite data lacks the spatial resolution and revisit frequency needed for field-level decisions...')}
            className="c2o-textarea" rows={5} />
        </Field>
        <Field label={t('Operational Context')} hint={t('When, where, and how will the mission products be used?')}>
          <textarea value={operationalContext} onChange={e => setOperationalContext(e.target.value)}
            placeholder={t('e.g., Data products will be delivered to farming cooperatives within 6 hours of acquisition during the growing season (May-September)...')}
            className="c2o-textarea" rows={3} />
        </Field>
        <Field group label={t('Mission Type')}>
          <div className="flex gap-1 wrap">
            {MISSION_TYPES.map(mt => (
              <button key={mt.value} type="button" onClick={() => setMissionType(mt.value)} aria-pressed={missionType === mt.value}
                className="c2o-choice-chip" title={t(mt.desc)}>
                {t(MISSION_TYPE_LABELS[mt.value])}
              </button>
            ))}
          </div>
        </Field>
        {problemStatement.trim() && (
          <div className="row mb-3">
            <RecordDecision decision="D-1.4-PROBLEM" capture="wizard:problem" prefill={() => ({
              choice: problemStatement.trim(),
              evidence: [
                { label: t('Mission type'), value: t(MISSION_TYPE_LABELS[missionType]) },
                ...(operationalContext.trim() ? [{ label: t('Operational Context'), value: operationalContext.trim().slice(0, 200) }] : []),
              ],
            })} />
          </div>
        )}
      </WizardFrame>
    )
  }

  // ─── STEP 2: STAKEHOLDERS & OBJECTIVES ───
  if (step === 'stakeholders') {
    const hasEnough = stakeholders.some(s => s.name) && objectives.filter(o => o.text).length >= 2
    return (
      <WizardFrame step={2} title={t('Who cares, and what do they need?')} onBack={() => setStep('problem')}
        onNext={() => { runTradeAnalysis(); setStep('alternatives') }} canNext={hasEnough}>
        <Field group label={t('Stakeholders')} hint={t('Who benefits from, funds, or operates this mission?')}>
          {stakeholders.map((s, i) => (
            <div key={s.id} className="flex gap-1 mb-1">
              <input value={s.name} onChange={e => { const n = [...stakeholders]; n[i].name = e.target.value; setStakeholders(n) }}
                placeholder={t('Name / organisation')} aria-label={t('Stakeholder {{n}}: name / organisation', { n: i + 1 })} className="c2o-input grow" />
              <select value={s.role} onChange={e => { const n = [...stakeholders]; n[i].role = e.target.value; setStakeholders(n) }}
                aria-label={t('Stakeholder {{n}}: role', { n: i + 1 })} className="c2o-select w-auto">
                {Object.entries(STAKEHOLDER_ROLES).map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}
              </select>
              <input value={s.need} onChange={e => { const n = [...stakeholders]; n[i].need = e.target.value; setStakeholders(n) }}
                placeholder={t('Key need')} aria-label={t('Stakeholder {{n}}: key need', { n: i + 1 })} className="c2o-input grow" />
              {stakeholders.length > 1 && (
                <button type="button" onClick={() => setStakeholders(stakeholders.filter((_, j) => j !== i))}
                  className="c2o-btn c2o-btn--icon" aria-label={t('Remove stakeholder {{n}}', { n: i + 1 })}>×</button>
              )}
            </div>
          ))}
          <button onClick={() => setStakeholders([...stakeholders, { id: String(Date.now()), name: '', role: 'user', need: '' }])}
            type="button" className="c2o-btn c2o-btn--quiet c2o-btn--sm">
            {t('+ Add stakeholder')}
          </button>
        </Field>

        <Field group label={t('Mission Objectives (minimum 2)')} hint={t('What must the mission achieve? Be specific and measurable.')}>
          {objectives.map((o, i) => (
            <div key={o.id} className="flex gap-1 mb-1">
              <select value={o.priority} onChange={e => { const n = [...objectives]; n[i].priority = e.target.value; setObjectives(n) }}
                aria-label={t('Objective {{n}}: priority', { n: i + 1 })} className="c2o-select w-auto">
                <option value="primary">{t('Primary')}</option>
                <option value="secondary">{t('Secondary', { context: 'priority' })}</option>
                <option value="constraint">{t('Constraint', { context: 'priority' })}</option>
              </select>
              <input value={o.text} onChange={e => { const n = [...objectives]; n[i].text = e.target.value; setObjectives(n) }}
                placeholder={t('e.g., Acquire 5m GSD multispectral imagery')} aria-label={t('Objective {{n}}', { n: i + 1 })} className="c2o-input c2o-grow-2" />
              <input value={o.measurable_criterion} onChange={e => { const n = [...objectives]; n[i].measurable_criterion = e.target.value; setObjectives(n) }}
                placeholder={t('How to measure')} aria-label={t('Objective {{n}}: how to measure', { n: i + 1 })} className="c2o-input grow" />
              {objectives.length > 1 && (
                <button type="button" onClick={() => setObjectives(objectives.filter((_, j) => j !== i))}
                  className="c2o-btn c2o-btn--icon" aria-label={t('Remove objective {{n}}', { n: i + 1 })}>×</button>
              )}
            </div>
          ))}
          <button onClick={() => setObjectives([...objectives, { id: String(Date.now()), text: '', priority: 'secondary', measurable_criterion: '' }])}
            type="button" className="c2o-btn c2o-btn--quiet c2o-btn--sm">
            {t('+ Add objective')}
          </button>
        </Field>
        <div className="row gap-2 mb-3">
          <RecordDecision decision="D-1.4-STAKEHOLDERS" capture="wizard:stakeholders" label={t('Record stakeholder decision')}
            prefill={() => ({
              options: stakeholders.filter(x => x.name.trim()).map(x => ({
                name: x.name.trim(), summary: x.need.trim(), values: { [t('Role')]: t(STAKEHOLDER_ROLES[x.role] ?? x.role) },
              })),
            })} />
          <RecordDecision decision="D-1.4-OBJECTIVES" capture="wizard:stakeholders" label={t('Record objectives decision')}
            prefill={() => ({
              options: objectives.filter(o => o.text.trim()).map(o => ({
                name: o.text.trim(), summary: o.measurable_criterion.trim(),
                values: { [t('Priority')]: o.priority === 'primary' ? t('Primary') : o.priority === 'secondary' ? t('Secondary', { context: 'priority' }) : t('Constraint', { context: 'priority' }) },
                chosen: o.priority === 'primary' || undefined,
              })),
              evidence: [{ label: t('Objectives with a measurable criterion'), value: `${objectives.filter(o => o.text.trim() && o.measurable_criterion.trim()).length} / ${objectives.filter(o => o.text.trim()).length}` }],
            })} />
        </div>
      </WizardFrame>
    )
  }

  // ─── STEP 3: IS SPACE THE RIGHT ANSWER? ───
  if (step === 'alternatives') {
    return (
      <WizardFrame step={3} title={t('Is space the right answer?')} onBack={() => setStep('stakeholders')}
        onNext={() => setStep('architecture')} canNext={!!selectedAlt && !!selectionRationale}>
        <div className="t-12 c-2 mb-2 lh-text">
          {t('Before committing to a space mission, consider all alternatives. Could existing satellite data, commercial services, drones, or ground sensors meet your objectives?')}
        </div>

        {tradeLoading && <div className="c-accent p-4 ta-c">{t('Analysing alternatives...')}</div>}

        {tradeResult?.alternatives && (
          <>
            {tradeResult.key_question && (
              <Note tone="caution" className="mb-2">
                {t('Key question: {{question}}', { question: tradeResult.key_question })}
              </Note>
            )}

            <div className="stack gap-1 mb-3" role="group" aria-label={t('Alternatives')}>
              {tradeResult.alternatives.map((alt: any) => (
                <button key={alt.name} type="button" onClick={() => setSelectedAlt(alt.name)} aria-pressed={selectedAlt === alt.name}
                  className="c2o-choice-card">
                  <div className="flex jc-sb mb-1">
                    <span className="w-600 t-12">{alt.name}</span>
                    <span className="t-12 c-2">#{alt.rank} — {alt.category}</span>
                  </div>
                  <div className="t-12 c-2">{alt.description?.slice(0, 120)}</div>
                  {alt.gsd_m != null && (
                    <div className="t-12 c-2 mt-1">
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
                  className="c2o-textarea" rows={3} />
              </Field>
            )}
            {selectedAlt && (
              <div className="row mb-3">
                <RecordDecision decision="D-1.4-SPACE" capture="wizard:alternatives" prefill={() => ({
                  options: (tradeResult?.alternatives ?? []).map((a: any) => ({
                    name: String(a.name), summary: String(a.description || '').slice(0, 200),
                    values: {
                      ...(a.gsd_m != null ? { 'GSD (m)': a.gsd_m } : {}),
                      ...(a.revisit_days != null ? { [t('Revisit (d)')]: a.revisit_days } : {}),
                      ...((a.annual_cost_keur ?? a.total_3yr_cost_keur) != null ? { kEUR: a.annual_cost_keur ?? a.total_3yr_cost_keur } : {}),
                      ...(a.rank != null ? { [t('Rank')]: a.rank } : {}),
                    },
                    ...(typeof a.total_score === 'number' ? { score: a.total_score } : {}),
                    chosen: a.name === selectedAlt || undefined,
                  })),
                  choice: selectedAlt,
                  rationale: selectionRationale.trim() || undefined,
                  evidence: tradeResult?.recommendation ? [{ label: t('Tool recommendation'), value: String(tradeResult.recommendation).slice(0, 200) }] : undefined,
                })} />
              </div>
            )}

            {tradeResult.recommendation && (
              <Note tone="info" className="mt-2">
                {tradeResult.recommendation}
              </Note>
            )}
          </>
        )}

        {!tradeResult && !tradeLoading && (
          <button type="button" onClick={runTradeAnalysis} className="c2o-btn c2o-btn--primary">
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
        onNext={createMission} canNext={!creating && defErrors.length === 0} nextLabel={creating ? t('Creating...') : t('Create Mission & Start Design')}>
        <div className="t-12 c-2 mb-2">
          {t('Choose an initial architecture to start with. You can modify this later by adding, removing, or renaming segments.')}
        </div>

        <div className="stack gap-1 mb-2">
          {ARCH_PRESETS.map(arch => (
            <button key={arch.id} type="button" onClick={() => setSelectedArch(arch.id)} aria-pressed={selectedArch === arch.id}
              className="c2o-choice-card">
              <span className="w-600">{t(ARCH_PRESET_NAMES[arch.id])}</span>
              {arch.segments.length > 0 && (
                <div className="t-12 c-2 mt-1">
                  {t('Segments: {{list}}', { list: archSummary(arch, t) })}
                </div>
              )}
            </button>
          ))}
        </div>

        <div className="row mb-2">
          <RecordDecision decision="D-1.4-ARCHITECTURE" capture="wizard:architecture" prefill={() => ({
            options: ARCH_PRESETS.map(a => ({
              name: t(ARCH_PRESET_NAMES[a.id]),
              summary: archSummary(a, t),
              chosen: a.id === selectedArch || undefined,
            })),
            choice: t(ARCH_PRESET_NAMES[selectedArch]),
            evidence: [
              { label: t('Design Lifetime (years)'), value: Number(lifetime) || lifetime },
              { label: t('Target Mass (kg)'), value: Number(massTarget) || massTarget },
            ],
          })} />
        </div>
        <div className="t-12 c-2 mb-1">
          {t('Mission definition: the values every analysis starts from. You can change them later in Traceability › Mission need.')}
        </div>
        <MissionDefinitionFields value={missionDef} onChange={setMissionDef} />
        {defErrors.length > 0 && (
          <ul className="m-0 pl-4 c-alarm t-12 mt-1" role="alert">
            {defErrors.map(e => <li key={e}>{t(e)}</li>)}
          </ul>
        )}
        <div className="flex wrap ai-e gap-2 mt-2">
          <Field label={t('Team size (seats)')} hint={t('Each person takes a seat that owns its parameters. Changing another seat\u2019s value sends it to them for review.')}>
            <select className="c2o-select" value={teamSize} onChange={e => setTeamSize(e.target.value)} data-testid="wizard-team-size">
              <option value="solo">{t('Solo (no seats)')}</option>
              {(seatCatalogue?.presets ?? []).map(p => <option key={p.id} value={p.id}>{i18n.language.startsWith('fr') ? p.label.fr : p.label.en}</option>)}
            </select>
          </Field>
          {teamSize !== 'solo' && (seatCatalogue?.seats ?? []).filter(s => s.optional).map(s => (
            <label key={s.id} className="c2o-check t-12">
              <input type="checkbox" checked={optionalSeats.includes(s.id)}
                onChange={e => setOptionalSeats(o => e.target.checked ? [...o, s.id] : o.filter(x => x !== s.id))} />
              {i18n.language.startsWith('fr') ? s.label.fr : s.label.en}
            </label>
          ))}
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
    <div className="c2o-wizard">
      <header className="c2o-home-frame__bar">
        <span className="c2o-appbar__mark">SpaceCDF</span>
        <span className="t-13 c-2">{t('Mission Definition')}</span>
        <ol className="c2o-steps list-reset" aria-label={t('Steps')}>
          {STEP_NAMES.map((name, i) => {
            const s = i + 1
            return (
              <li key={s} className={s === step ? 'c2o-steps__item is-current' : s < step ? 'c2o-steps__item is-done' : 'c2o-steps__item'}
                aria-current={s === step ? 'step' : undefined}>
                <span className="c2o-steps__num" aria-hidden="true">{s < step ? '✓' : s}</span>
                <span className="c2o-steps__label">{t(name)}</span>
                {s < step && <span className="sr-only">{t('done')}</span>}
              </li>
            )
          })}
        </ol>
        <span className="ml-auto row gap-2">
          <LogbookButton />
          <LanguageToggle />
          <ThemeToggle />
        </span>
      </header>
      <LogbookBanner />

      <main className="c2o-wizard__main">
        <h1 className="t-20 w-600 mb-4 c-1">
          {t('Step {{step}}: {{title}}', { step, title })}
        </h1>
        {children}
      </main>

      <footer className="c2o-wizard__foot">
        <button type="button" onClick={onBack} className="c2o-btn">{t('← Back')}</button>
        <button type="button" onClick={() => { if (canNext) onNext() }} aria-disabled={!canNext || undefined}
          data-reason={!canNext ? t('Complete the required fields on this step first') : undefined}
          className="c2o-btn c2o-btn--primary c2o-btn--lg c2o-reason-end c2o-reason-up">
          {nextLabel || t('Next →')}
        </button>
      </footer>
    </div>
  )
}

// English text is the i18n key: wizard step names.
const STEP_NAMES = ['Problem', 'Stakeholders', 'Alternatives', 'Architecture']

function Field({ label, hint, children, group }: { label: string; hint?: string; children: React.ReactNode; group?: boolean }) {
  // A single control: the label wraps it. Several controls: a fieldset with a legend.
  if (group) {
    return (
      <fieldset className="c2o-wfield">
        <legend className="c2o-wfield__label">{label}</legend>
        {hint && <span className="c2o-wfield__hint">{hint}</span>}
        {children}
      </fieldset>
    )
  }
  return (
    <label className="c2o-wfield">
      <span className="c2o-wfield__label">{label}</span>
      {hint && <span className="c2o-wfield__hint">{hint}</span>}
      {children}
    </label>
  )
}

// ─── Active Studies List ───
function ActiveStudies({ onJoin }: { onJoin: (studyId: string) => void }) {
  // Only the instructor deletes studies (WP9; open on a laptop until someone is instructor).
  const seatMe = useSeatStore(st => st.me)
  const canDelete = !seatMe || seatMe.instructor || (seatMe.instructor_mode === 'laptop' && !seatMe.laptop_instructor)
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
        <p className="t-13 c-2 m-0">{t('Work on a study with your team in real time.')}</p>
      </>
    )
  }

  return (
    <div className="c2o-studies">
      <div className="flex ai-c gap-2 mb-2">
        <h2 className="w-600 t-13 m-0">{t('Active Studies')}</h2>
        <span className="grow" />
        <button type="button" className="c2o-btn c2o-btn--quiet" onClick={refresh} disabled={loading}>
          {loading ? t('Loading...') : t('Refresh')}
        </button>
        <button type="button" className="c2o-btn" aria-expanded={true} onClick={() => setExpanded(false)}>
          {t('Close')}
        </button>
      </div>

      {studies.length === 0 ? (
        <div className="t-12 c-2 py-1 px-0">
          {loading ? t('Loading...') : t('No active studies found. Create a new mission to start.')}
        </div>
      ) : (
        <>
          <div className="t-12 c-2 mb-1">
            {t('{{count}} studies — most recent first', { count: studies.length, defaultValue_one: '{{count}} studies — most recent first' })}
          </div>
          <ul className="list-reset c2o-studies__list">
            {studies.slice().reverse().map((s: any) => (
              <li key={s.id} className="c2o-studies__row">
                <button type="button" onClick={() => directJoin(s.id)} className="c2o-studies__join">
                  {s.name || s.id}
                </button>
                {s.phase && <Tag mono>{s.phase}</Tag>}
                {s.created && (
                  <span className="t-12 c-2">
                    {fmtDate(s.created, {})}
                  </span>
                )}
                {canDelete && <button onClick={async (e) => {
                  e.stopPropagation()
                  if (!(await askConfirm(t('Delete study "{{name}}"? This cannot be undone.', { name: s.name || s.id }), { danger: true, confirmLabel: t('Delete') }))) return
                  await fetch(`${API}/studies/${s.id}`, { method: 'DELETE' })
                  refresh()
                }} type="button" className="c2o-btn c2o-btn--icon" title={t('Delete study')} aria-label={t('Delete study "{{name}}"', { name: s.name || s.id })}>
                  ×
                </button>}
              </li>
            ))}
          </ul>
          {canDelete && studies.length > 5 && (
            <button onClick={async () => {
              if (!(await askConfirm(t('Delete all {{count}} studies? This cannot be undone.', { count: studies.length }), { danger: true, confirmLabel: t('Delete') }))) return
              for (const s of studies) { await fetch(`${API}/studies/${s.id}`, { method: 'DELETE' }) }
              refresh()
            }} type="button" className="c2o-btn c2o-btn--danger c2o-btn--sm mt-2">
              {t('Delete all studies')}
            </button>
          )}
        </>
      )}
    </div>
  )
}
