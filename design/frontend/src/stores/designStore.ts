import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface DesignParam {
  value: number | string | boolean
  unit: string
  confidence: number
  margin_percent: number
  source: string
  domain: string
}

export interface BudgetInfo {
  total_nominal: number
  total_with_margin: number
  allocation: number
  margin_percent: number
  status: 'green' | 'amber' | 'red' | 'exceeded'
  lines: Array<{
    subsystem: string
    equipment: string
    nominal_value: number
    margin_percent: number
    unit: string
  }>
}

export interface ConflictResolution {
  description: string
  position_responsible: string
  parameter_to_change: string
  suggested_direction: string
  estimated_impact?: string
}

export interface CrossDomainConflict {
  id: string
  severity: 'critical' | 'major' | 'minor'
  title: string
  description: string
  domain_a: string
  domain_b: string
  position_a: string
  position_b: string
  param_a: string
  param_b: string
  value_a_str: string
  value_b_str: string
  resolutions: ConflictResolution[]
}

export interface DesignResult {
  converged: boolean
  iterations: number
  total_time_s: number
  parameters: Record<string, DesignParam>
  budgets: Record<string, BudgetInfo>
  warnings: string[]
  recommendations: string[]
  conflicts: CrossDomainConflict[]
}

export interface MissionPhase {
  id: string; name: string; duration_days: number; description: string
}

export interface OperationalMode {
  id: string; name: string; description: string
  subsystems_active: string[]; pointing: string; dataflow: string
}

export interface MissionRequirements {
  name: string
  mission_type: string
  spacecraft_class: string
  orbit: {
    orbit_type: string
    altitude_km: number
    inclination_deg: number
    mission_duration_years: number
    deorbit_required: boolean
    delta_v_insertion_ms?: number
    delta_v_maintenance_ms?: number
  }
  payloads: Array<{
    name: string
    mass_kg: number
    power_w: number
    data_rate_mbps: number
    pointing_accuracy_deg: number
    duty_cycle_percent: number
  }>
  design_lifetime_years: number
  target_mass_kg?: number
  target_cost_meur?: number
  ground_stations: string[]
}

export interface MissionNeedState {
  problem_statement: string
  operational_context: string
  stakeholders: Array<{ id: string; name: string; role: string; needs: string[]; constraints: string[]; priority: string }>
  objectives: Array<{ id: string; text: string; priority: string; type: string; measurable_criterion: string; status: string }>
  success_criteria: string[]
  alternatives: Array<{
    id: string; name: string; type: string; description: string
    pros: string[]; cons: string[]; feasibility_score: number
    decision: string; decision_rationale: string
  }>
  selected_alternative_id: string | null
  selection_rationale: string
  conops_summary: string
}

interface ChangeRecord {
  timestamp: number
  source: string  // which tab/component made the change
  paramId: string
  oldValue: any
  newValue: any
}

interface DesignStore {
  missionNeed: MissionNeedState
  requirements: MissionRequirements
  result: DesignResult | null
  isRunning: boolean
  error: string | null
  studyId: string | null
  missionId: string  // Human-readable unique mission identifier (e.g., "SCDF-2026-001")

  // Architecture selections (persisted)
  architectureSelections: Record<string, any>
  // Architecture-derived requirements
  architectureDerivedReqs: Array<{ id: string; level: string; text: string; subsystem: string }>
  // Generated requirements (persisted)
  generatedRequirements: Array<{ id: string; text: string; req_type: string; domain: string; threshold: number; operator: string; unit: string; verification_method: string; objective_id: string; function_id: string; rationale: string; status: string; level: string; parent_id: string | null }>
  // Functions list (for requirement linking)
  functionsList: Array<{ id: string; name: string; allocated_to: string[] }>
  // Selected equipment (persisted) — feeds into budget roll-up
  selectedEquipment: Array<{ category: string; componentId: string; name: string; mass_kg: number; power_w: number; cost_keur: number; quantity: number }>

  // ConOps state (persisted so it survives tab switches)
  missionPhases: MissionPhase[]
  operationalModes: OperationalMode[]

  setMissionPhases: (phases: MissionPhase[]) => void
  setOperationalModes: (modes: OperationalMode[]) => void

  // Reactive state
  designStale: boolean  // true when requirements changed since last design run
  lastChangeSource: string  // which tab made the last change
  changeHistory: ChangeRecord[]  // recent changes for audit trail
  pendingConflicts: string[]  // conflicts detected from latest change

  // Ground stations (shared between Phase 1 and Phase 2)
  groundStations: Array<{ id: string; name: string; latitude: number; longitude: number; antenna_m: number; bands: string[]; min_elevation: number; cost_keur: number; owned: boolean }>
  setGroundStations: (stations: any[]) => void

  // Design constraints from selections
  selectedRfBand: string | null  // constrains transponder/antenna selection
  selectedLaunchProvider: string | null  // constrains mass allocation
  selectedLicenseType: string  // amateur/experimental/commercial

  // Requirement ID sequence counters — never decrement, never reuse
  reqSequence: Record<string, number>  // { mission: 3, system: 14, subsystem: 32 }
  nextReqId: (level: string) => string  // Returns e.g. "SUPERDOVE-SYS-015"

  // V&V change log — tracks all changes to verification entries
  vvChangeLog: Array<{ req_id: string; field: string; old_value: string; new_value: string; timestamp: number; changed_by: string }>
  addVVChange: (req_id: string, field: string, old_value: string, new_value: string) => void

  // Budget allocations (persisted) — assigned by systems engineer in SystemBudgetEditor
  budgetAllocations: Record<string, Record<string, number>>
  setBudgetAllocations: (allocations: Record<string, Record<string, number>>) => void

  // Interface conflict resolutions (persisted)
  interfaceResolutions: Record<string, { status: string; selectedOption: string; rationale: string; resolvedBy: string }>
  setInterfaceResolutions: (resolutions: Record<string, { status: string; selectedOption: string; rationale: string; resolvedBy: string }>) => void

  // Phase completion tracking
  phaseCompletion: Record<number, boolean>
  setPhaseComplete: (phase: number, complete: boolean) => void

  // SEMP questionnaire answers (persisted)
  sempAnswers: Record<string, any>
  setSempAnswers: (answers: Record<string, any>) => void

  // Parameter overrides — user-set values that persist and override agent defaults
  // Any component can write here via setParameter(). Values are sent to backend
  // on runDesign() and injected as sticky (POSITION_OVERRIDE) so agents don't overwrite.
  parameterOverrides: Record<string, number | string | boolean>

  // Constellation/fleet variants (persisted)
  constellationVariants: Array<{ id: string; name: string; quantity: number; altitude_km: number; inclination_deg: number; cost_modifier: number }>
  setConstellationVariants: (variants: any[]) => void

  // Mission operations concept (persisted)
  missionOps: { controlCentre: string; staffingModel: string; location: string }
  setMissionOps: (ops: { controlCentre: string; staffingModel: string; location: string }) => void

  // Operations activities (persisted)
  operationsActivities: Array<{ id: string; name: string; phase: string; systems_involved: string[]; staffing: string; frequency: string; automation_level: string }>
  setOperationsActivities: (activities: any[]) => void

  // Project WBS (persisted) — work packages with inputs/activities/outputs
  projectWbs: Array<{ id: string; name: string; description: string; responsible: string; effort_hours: number; status: string; phase: string; start_date: string; end_date: string; depends_on: string; inputs: string; work_content: string; outputs: string }>
  setProjectWbs: (wbs: Array<{ id: string; name: string; description: string; responsible: string; effort_hours: number; status: string; phase: string; start_date: string; end_date: string; depends_on: string; inputs: string; work_content: string; outputs: string }>) => void

  setMissionNeed: (need: Partial<MissionNeedState>) => void
  setRequirements: (req: Partial<MissionRequirements>) => void
  setOrbit: (orbit: Partial<MissionRequirements['orbit']>) => void
  setStudyId: (id: string | null) => void
  markStale: (source: string) => void
  setParameter: (paramId: string, value: number | string | boolean, source?: string) => void
  applyConvergenceResult: (params: Record<string, DesignParam>, conflicts: CrossDomainConflict[]) => void
  undoLastChange: () => void
  runDesign: () => Promise<void>
  createStudy: () => Promise<string | null>
}

const defaultRequirements: MissionRequirements = {
  name: 'New Mission',
  mission_type: 'earth_observation',
  spacecraft_class: 'nano',
  orbit: {
    orbit_type: 'sso',
    altitude_km: 500,
    inclination_deg: 97.4,
    mission_duration_years: 3,
    deorbit_required: true,
  },
  payloads: [{
    name: 'Payload',
    mass_kg: 10,
    power_w: 30,
    data_rate_mbps: 100,
    pointing_accuracy_deg: 0.1,
    duty_cycle_percent: 25,
  }],
  design_lifetime_years: 3,
  target_mass_kg: 200,
  target_cost_meur: 20,
  ground_stations: ['KSAT Svalbard'],
}

const API_BASE = '/api'

const defaultMissionNeed: MissionNeedState = {
  problem_statement: '',
  operational_context: '',
  stakeholders: [],
  objectives: [],
  success_criteria: [],
  alternatives: [],
  selected_alternative_id: null,
  selection_rationale: '',
  conops_summary: '',
}

export const useDesignStore = create<DesignStore>()(persist((set, get) => ({
  missionNeed: defaultMissionNeed,
  requirements: defaultRequirements,
  result: null,
  isRunning: false,
  error: null,
  studyId: null,
  missionId: `SCDF-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 900) + 100)}`,
  architectureSelections: {},
  architectureDerivedReqs: [],
  generatedRequirements: [],
  functionsList: [],
  selectedEquipment: [],
  missionPhases: [
    { id: 'phase_a', name: 'Phase A (Feasibility)', duration_days: 180, description: 'Concept and technology development, SRR' },
    { id: 'phase_b', name: 'Phase B (Preliminary Design)', duration_days: 270, description: 'Preliminary design, PDR, technology maturation' },
    { id: 'phase_c', name: 'Phase C (Detailed Design)', duration_days: 180, description: 'Detailed design, CDR, procurement' },
    { id: 'phase_d', name: 'Phase D (AIT & Launch)', duration_days: 180, description: 'Assembly, integration, test, launch campaign' },
    { id: 'leop', name: 'LEOP', duration_days: 3, description: 'Launch, deployment, first contact, initial checkout' },
    { id: 'commissioning', name: 'Commissioning', duration_days: 30, description: 'Subsystem checkout, calibration, first light' },
    { id: 'nominal', name: 'Nominal Operations', duration_days: 900, description: 'Primary science/service data collection and delivery' },
    { id: 'extended', name: 'Extended Operations', duration_days: 365, description: 'Beyond design lifetime, degraded modes, reduced capability' },
    { id: 'phase_e', name: 'Phase E (Utilisation)', duration_days: 1095, description: 'Full operational phase: science/service, maintenance, orbit manoeuvres' },
    { id: 'phase_f', name: 'Phase F (Disposal)', duration_days: 30, description: 'End-of-life: passivation, deorbit/graveyard, final data archive' },
    { id: 'disposal', name: 'Disposal', duration_days: 14, description: 'Passivation, deorbit, final telemetry' },
  ],
  operationalModes: [
    { id: 'safe', name: 'Safe Mode', description: 'Minimum power survival. Entered on anomaly. Sun-pointing, no payload.',
      subsystems_active: ['EPS', 'OBC', 'TTC (beacon)', 'AOCS (coarse)'], pointing: 'Sun-pointing', dataflow: 'Beacon only → ground' },
    { id: 'science', name: 'Science / Imaging', description: 'Primary data acquisition. Payload active, nadir-pointing.',
      subsystems_active: ['EPS', 'OBC', 'Payload', 'AOCS (fine)', 'OBDH'], pointing: 'Nadir (target)', dataflow: 'Instrument → OBDH storage' },
    { id: 'downlink', name: 'Downlink', description: 'Ground station pass. TX active, data download.',
      subsystems_active: ['EPS', 'OBC', 'TTC (full)', 'OBDH'], pointing: 'Ground station', dataflow: 'OBDH → TX → GS → processing → user' },
    { id: 'eclipse', name: 'Eclipse', description: 'Battery-powered. Reduced operations, heaters active.',
      subsystems_active: ['EPS (battery)', 'OBC', 'TCS (heaters)', 'AOCS (coarse)'], pointing: 'Inertial hold', dataflow: 'None' },
  ],
  designStale: false,
  lastChangeSource: '',
  changeHistory: [],
  pendingConflicts: [],
  selectedRfBand: null,
  selectedLaunchProvider: null,
  selectedLicenseType: 'commercial',
  groundStations: [
    { id: 'gs1', name: 'Svalbard', latitude: 78.2, longitude: 15.4, antenna_m: 13, bands: ['S', 'X'], min_elevation: 5, cost_keur: 500, owned: false },
    { id: 'gs2', name: 'Kiruna', latitude: 67.9, longitude: 20.2, antenna_m: 13, bands: ['S', 'X'], min_elevation: 5, cost_keur: 400, owned: false },
    { id: 'gs3', name: 'Weilheim', latitude: 47.9, longitude: 11.1, antenna_m: 15, bands: ['S', 'X', 'Ka'], min_elevation: 5, cost_keur: 600, owned: false },
  ],
  setGroundStations: (stations) => set({ groundStations: stations }),
  reqSequence: { mission: 0, system: 0, subsystem: 0 },
  nextReqId: (level) => {
    const state = get()
    const prefix = (state.requirements?.name || 'MISSION').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12)
    const levelCode: Record<string, string> = { mission: 'MIS', system: 'SYS', subsystem: 'SUB' }
    const code = levelCode[level] || level.toUpperCase().slice(0, 3)
    const seq = (state.reqSequence[level] || 0) + 1
    set({ reqSequence: { ...state.reqSequence, [level]: seq } })
    return `${prefix}-${code}-${String(seq).padStart(3, '0')}`
  },
  sempAnswers: {},
  setSempAnswers: (answers) => set({ sempAnswers: answers }),
  vvChangeLog: [],
  addVVChange: (req_id, field, old_value, new_value) => set(s => ({
    vvChangeLog: [...s.vvChangeLog, {
      req_id, field, old_value, new_value,
      timestamp: Date.now(), changed_by: 'systems_engineer',
    }],
  })),
  budgetAllocations: {},
  setBudgetAllocations: (allocations) => set({ budgetAllocations: allocations }),
  interfaceResolutions: {},
  setInterfaceResolutions: (resolutions) => set({ interfaceResolutions: resolutions }),
  phaseCompletion: {},
  setPhaseComplete: (phase, complete) => set(s => ({ phaseCompletion: { ...s.phaseCompletion, [phase]: complete } })),
  parameterOverrides: {},
  constellationVariants: [],
  setConstellationVariants: (variants) => set({ constellationVariants: variants }),
  missionOps: { controlCentre: '', staffingModel: 'pass_based', location: '' },
  setMissionOps: (ops) => set({ missionOps: ops }),
  operationsActivities: [],
  setOperationsActivities: (activities) => set({ operationsActivities: activities }),
  projectWbs: [],
  setProjectWbs: (wbs) => set({ projectWbs: wbs }),

  setParameter: (paramId, value, source = 'user') => set((s) => ({
    parameterOverrides: { ...s.parameterOverrides, [paramId]: value },
    designStale: true,
    lastChangeSource: source,
    changeHistory: [...s.changeHistory.slice(-49), {
      timestamp: Date.now(), source, paramId,
      oldValue: s.parameterOverrides[paramId], newValue: value,
    }],
  })),

  setMissionPhases: (phases) => set({ missionPhases: phases }),
  setOperationalModes: (modes) => set({ operationalModes: modes }),

  setMissionNeed: (need) => set((s) => {
    const record: ChangeRecord = {
      timestamp: Date.now(), source: 'mission_need',
      paramId: Object.keys(need).join(', '),
      oldValue: Object.keys(need).map(k => (s.missionNeed as any)[k]),
      newValue: Object.values(need),
    }

    // Auto-infer mission type from objectives when objectives change
    let reqUpdate: Partial<MissionRequirements> = {}
    if (need.objectives) {
      const allText = need.objectives.map(o => o.text).join(' ').toLowerCase()
      if (allText.match(/communi|relay|iot|m2m|data link|connect/)) {
        reqUpdate = { mission_type: 'communications' }
      } else if (allText.match(/sar|radar|synthetic aperture/)) {
        reqUpdate = { mission_type: 'sar' }
      } else if (allText.match(/ais|maritime|ship track/)) {
        reqUpdate = { mission_type: 'earth_observation' }
      } else if (allText.match(/imag|gsd|resolution|spectral|optical|photo/)) {
        reqUpdate = { mission_type: 'earth_observation' }
      } else if (allText.match(/lunar|moon|cislunar/)) {
        reqUpdate = { mission_type: 'lunar' }
      } else if (allText.match(/mars|deep.?space|interplanet/)) {
        reqUpdate = { mission_type: 'mars' }
      } else if (allText.match(/tech.?demo|demonstrat|experiment|test/)) {
        reqUpdate = { mission_type: 'technology_demo' }
      }
    }

    return {
      missionNeed: { ...s.missionNeed, ...need },
      requirements: Object.keys(reqUpdate).length > 0 ? { ...s.requirements, ...reqUpdate } : s.requirements,
      designStale: true, lastChangeSource: 'mission_need',
      changeHistory: [...s.changeHistory.slice(-49), record],
    }
  }),

  setRequirements: (req) => set((s) => {
    const record: ChangeRecord = {
      timestamp: Date.now(), source: 'requirements',
      paramId: Object.keys(req).join(', '),
      oldValue: Object.keys(req).map(k => (s.requirements as any)[k]),
      newValue: Object.values(req),
    }
    return {
      requirements: { ...s.requirements, ...req },
      designStale: true, lastChangeSource: 'requirements',
      changeHistory: [...s.changeHistory.slice(-49), record],
    }
  }),

  setOrbit: (orbit) => set((s) => {
    const record: ChangeRecord = {
      timestamp: Date.now(), source: 'orbit',
      paramId: Object.keys(orbit).join(', '),
      oldValue: Object.keys(orbit).map(k => (s.requirements.orbit as any)[k]),
      newValue: Object.values(orbit),
    }
    return {
      requirements: {
        ...s.requirements,
        orbit: { ...s.requirements.orbit, ...orbit }
      },
      designStale: true, lastChangeSource: 'orbit',
      changeHistory: [...s.changeHistory.slice(-49), record],
    }
  }),

  setStudyId: (id) => set({ studyId: id }),

  undoLastChange: () => set((s) => {
    if (s.changeHistory.length === 0) return {}
    const last = s.changeHistory[s.changeHistory.length - 1]
    const history = s.changeHistory.slice(0, -1)

    // Restore the old values based on source
    if (last.source === 'orbit') {
      const keys = last.paramId.split(', ')
      const oldVals = Array.isArray(last.oldValue) ? last.oldValue : [last.oldValue]
      const patch: any = {}
      keys.forEach((k, i) => { patch[k] = oldVals[i] })
      return {
        requirements: { ...s.requirements, orbit: { ...s.requirements.orbit, ...patch } },
        changeHistory: history, designStale: true,
      }
    }
    if (last.source === 'requirements') {
      const keys = last.paramId.split(', ')
      const oldVals = Array.isArray(last.oldValue) ? last.oldValue : [last.oldValue]
      const patch: any = {}
      keys.forEach((k, i) => { patch[k] = oldVals[i] })
      return {
        requirements: { ...s.requirements, ...patch },
        changeHistory: history, designStale: true,
      }
    }
    if (last.source === 'mission_need') {
      const keys = last.paramId.split(', ')
      const oldVals = Array.isArray(last.oldValue) ? last.oldValue : [last.oldValue]
      const patch: any = {}
      keys.forEach((k, i) => { patch[k] = oldVals[i] })
      return {
        missionNeed: { ...s.missionNeed, ...patch },
        changeHistory: history, designStale: true,
      }
    }
    return { changeHistory: history }
  }),

  markStale: (source) => set({ designStale: true, lastChangeSource: source }),

  applyConvergenceResult: (params, conflicts) => set((s) => {
    // Merge convergence results back into the design result
    if (!s.result) return {}
    const merged = { ...s.result }
    merged.parameters = { ...merged.parameters, ...params }
    merged.conflicts = conflicts
    return { result: merged, pendingConflicts: conflicts.map(c => c.title) }
  }),

  createStudy: async () => {
    try {
      const { requirements, missionNeed } = get()
      const res = await fetch(`${API_BASE}/studies/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirements,
          mission_need: missionNeed,
        }),
      })
      if (!res.ok) throw new Error(`${res.status}`)
      const data = await res.json()
      set({ studyId: data.id })
      return data.id
    } catch (err) {
      set({ error: String(err) })
      return null
    }
  },

  runDesign: async () => {
    set({ isRunning: true, error: null })
    try {
      const { requirements, missionNeed } = get()

      // Ensure a study exists so studyId is available for requirements, compliance, etc.
      if (!get().studyId) {
        const createRes = await fetch(`${API_BASE}/studies/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ requirements, mission_need: missionNeed }),
        })
        if (createRes.ok) {
          const studyData = await createRes.json()
          set({ studyId: studyData.id })
        }
      }

      const parameterOverrides = get().parameterOverrides
      const res = await fetch(`${API_BASE}/design/quick-design`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirements,
          mission_need: missionNeed,
          parameter_overrides: Object.keys(parameterOverrides).length > 0 ? parameterOverrides : undefined,
        }),
      })
      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`)
      }
      const data: DesignResult = await res.json()

      // Prune overrides where agent computed the same value (cleanup stale overrides)
      const currentOverrides = get().parameterOverrides
      const prunedOverrides: Record<string, number | string | boolean> = {}
      for (const [pid, ov] of Object.entries(currentOverrides)) {
        const computed = data.parameters?.[pid]
        // Keep override only if agent computed a different value (or param doesn't exist)
        if (!computed || computed.value !== ov) {
          prunedOverrides[pid] = ov
        }
      }

      set({
        result: data, isRunning: false, designStale: false,
        pendingConflicts: (data.conflicts || []).map(c => c.title),
        parameterOverrides: prunedOverrides,
      })

      // Seed the element tree from design results (model-centric architecture)
      const sid = get().studyId
      if (sid && data.parameters) {
        try {
          await fetch(`${API_BASE}/studies/${sid}/seed-elements`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              parameters: data.parameters,
              mission_type: requirements.mission_type || 'earth_observation',
              spacecraft_class: requirements.spacecraft_class || 'nano',
            }),
          })
        } catch { /* seed is best-effort — don't block design run on seed failure */ }
      }
    } catch (err) {
      set({ error: String(err), isRunning: false })
    }
  },
}), {
  name: 'spacecdf-design-state',
  partialize: (state) => ({
    // Persist these fields across page refreshes:
    missionNeed: state.missionNeed,
    requirements: state.requirements,
    result: state.result,
    studyId: state.studyId,
    missionId: state.missionId,
    architectureSelections: state.architectureSelections,
    groundStations: state.groundStations,
    architectureDerivedReqs: state.architectureDerivedReqs,
    generatedRequirements: state.generatedRequirements,
    functionsList: state.functionsList,
    selectedEquipment: state.selectedEquipment,
    missionPhases: state.missionPhases,
    operationalModes: state.operationalModes,
    selectedRfBand: state.selectedRfBand,
    selectedLaunchProvider: state.selectedLaunchProvider,
    selectedLicenseType: state.selectedLicenseType,
    changeHistory: state.changeHistory,
    parameterOverrides: state.parameterOverrides,
    sempAnswers: state.sempAnswers,
    reqSequence: state.reqSequence,
    vvChangeLog: state.vvChangeLog,
    budgetAllocations: state.budgetAllocations,
    interfaceResolutions: state.interfaceResolutions,
    phaseCompletion: state.phaseCompletion,
    constellationVariants: state.constellationVariants,
    missionOps: state.missionOps,
    operationsActivities: state.operationsActivities,
    projectWbs: state.projectWbs,
    // Don't persist: isRunning, error, designStale, pendingConflicts (transient)
  }),
}))
