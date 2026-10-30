/**
 * useGateReview — evaluates a study against one review gate (MCR / SRR / PDR)
 * on the backend (POST /api/ecss/gate-evaluate/{study}/{gate}), which reads
 * configs/gate_exit_criteria.yaml. The client's current Mission Need and
 * design parameters are sent so the result matches what the user sees.
 */
import { useQuery } from '@tanstack/react-query'

const API = '/api'

export type GateId = 'mcr' | 'srr' | 'pdr'

export interface GateCriterion {
  id: string
  question: string
  category: string
  priority: 'must_pass' | 'should_pass' | string
  advisory: boolean
  status: 'pass' | 'fail' | 'manual' | 'not_evaluated'
  verdict: 'pass' | 'fail' | 'advisory' | 'manual' | 'not_evaluated'
  evidence_required?: string
  evidence_found: string
  evidence_key?: string
  evidence_params?: Record<string, string | number>
}

export interface GateResult {
  phase: string
  gate: string
  gate_name: string
  found: boolean
  criteria: GateCriterion[]
  summary: { total: number; pass: number; fail: number; manual: number; not_evaluated: number;
             advisory: number; must_pass: number; must_pass_met: number }
  ready: boolean
  ready_pending_manual: boolean
}

export function useGateReview(
  studyId: string | null, gate: GateId, missionNeed: unknown, params: Record<string, { value: unknown }>,
) {
  const parameters: Record<string, number> = {}
  for (const [id, p] of Object.entries(params || {})) {
    if (p && typeof p.value === 'number' && Number.isFinite(p.value)) parameters[id] = p.value
  }
  return useQuery<GateResult>({
    queryKey: ['gate-review', studyId, gate, missionNeed, parameters],
    queryFn: async () => {
      const res = await fetch(`${API}/ecss/gate-evaluate/${encodeURIComponent(studyId || 'local')}/${gate}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mission_need: missionNeed, parameters }),
      })
      if (!res.ok) throw new Error(`${res.status}`)
      const data = await res.json()
      if (!data || !Array.isArray(data.criteria) || !data.found) throw new Error('bad response')
      return data as GateResult
    },
    retry: 1,
    staleTime: 5_000,
    structuralSharing: false,
  })
}
