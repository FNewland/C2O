import { create } from 'zustand'

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

interface DesignStore {
  missionNeed: MissionNeedState
  requirements: MissionRequirements
  result: DesignResult | null
  isRunning: boolean
  error: string | null
  studyId: string | null

  setMissionNeed: (need: Partial<MissionNeedState>) => void
  setRequirements: (req: Partial<MissionRequirements>) => void
  setOrbit: (orbit: Partial<MissionRequirements['orbit']>) => void
  setStudyId: (id: string | null) => void
  runDesign: () => Promise<void>
  createStudy: () => Promise<string | null>
}

const defaultRequirements: MissionRequirements = {
  name: 'New Mission',
  mission_type: 'earth_observation',
  spacecraft_class: 'small',
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

export const useDesignStore = create<DesignStore>((set, get) => ({
  missionNeed: defaultMissionNeed,
  requirements: defaultRequirements,
  result: null,
  isRunning: false,
  error: null,
  studyId: null,

  setMissionNeed: (need) => set((s) => ({
    missionNeed: { ...s.missionNeed, ...need }
  })),

  setRequirements: (req) => set((s) => ({
    requirements: { ...s.requirements, ...req }
  })),

  setOrbit: (orbit) => set((s) => ({
    requirements: {
      ...s.requirements,
      orbit: { ...s.requirements.orbit, ...orbit }
    }
  })),

  setStudyId: (id) => set({ studyId: id }),

  createStudy: async () => {
    try {
      const res = await fetch(`${API_BASE}/studies/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(get().requirements),
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
      const res = await fetch(`${API_BASE}/design/quick-design`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(get().requirements),
      })
      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`)
      }
      const data: DesignResult = await res.json()
      set({ result: data, isRunning: false })
    } catch (err) {
      set({ error: String(err), isRunning: false })
    }
  },
}))
