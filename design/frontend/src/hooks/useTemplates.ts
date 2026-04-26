import { useQuery, useMutation } from '@tanstack/react-query'

const API = '/api'

async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export interface EquipmentHint {
  category: string
  component_id?: string | null
  rationale: string
}

export interface MissionTemplate {
  id: string
  name: string
  archetype: string
  description: string
  typical_use_cases: string[]
  tags: string[]
  requirements: any  // Full MissionRequirements blob
  target_phase: string
  margin_policy_percent: number
  applicable_ecss: string[]
  equipment_hints: EquipmentHint[]
  notes: string
}

export interface DrdEntry {
  id: string
  name: string
  standard: string
  annex: string
  produced_by: 'spacecdf' | 'partial' | 'planned' | 'external'
  spacecdf_source?: string
}

export interface ComplianceSummary {
  phase: string
  found: boolean
  gate: string
  gate_name: string
  description: string
  total: number
  produced: number
  partial: number
  planned: number
  external: number
  coverage_percent: number
  drds: DrdEntry[]
  study_id?: string
  study_name?: string
}

export function useTemplates() {
  return useQuery<MissionTemplate[]>({
    queryKey: ['templates'],
    queryFn: () => api<MissionTemplate[]>('/templates/'),
    staleTime: 60_000,
  })
}

export function useCreateStudyFromTemplate() {
  return useMutation({
    mutationFn: (templateId: string) =>
      api<any>(`/templates/${templateId}/instantiate`, { method: 'POST' }),
  })
}

export function useEcssCompliance(studyId: string | null) {
  return useQuery<ComplianceSummary>({
    queryKey: ['ecss-compliance', studyId],
    queryFn: () => api<ComplianceSummary>(`/ecss/compliance/by-study/${studyId}`),
    enabled: !!studyId,
    staleTime: 30_000,
  })
}

export function useEcssComplianceByPhase(phaseId: string | null) {
  return useQuery<ComplianceSummary>({
    queryKey: ['ecss-compliance-phase', phaseId],
    queryFn: () => api<ComplianceSummary>(`/ecss/compliance/${phaseId}`),
    enabled: !!phaseId,
    staleTime: 60_000,
  })
}
