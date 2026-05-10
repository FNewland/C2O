import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const API = '/api'

async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export interface SessionSummary {
  id: string
  study_id: string
  name: string
  state: string
  participants: Array<{ position_id: string; display_name: string; is_active: boolean }>
  active_positions: string[]
  convergence_count: number
  edit_count: number
  created: string
  persisted?: boolean
  in_memory?: boolean
}

export function useSessions() {
  return useQuery<SessionSummary[]>({
    queryKey: ['sessions'],
    queryFn: () => api('/sessions/'),
    refetchInterval: 5000,
  })
}

export function useSession(sessionId: string | null) {
  return useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => api(`/sessions/${sessionId}`),
    enabled: !!sessionId,
  })
}

export function useSessionState(sessionId: string | null) {
  return useQuery({
    queryKey: ['session-state', sessionId],
    queryFn: () => api(`/sessions/${sessionId}/state`),
    enabled: !!sessionId,
  })
}

export function useCreateSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { study_id: string; name?: string }) =>
      api<{ id: string }>('/sessions/', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sessions'] }),
  })
}

export function useResumeSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) =>
      api<{ id: string }>(`/sessions/${sessionId}/resume`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sessions'] }),
  })
}

export function useSessionHistory(sessionId: string | null) {
  return useQuery({
    queryKey: ['session-history', sessionId],
    queryFn: () => api<{ edits: any[] }>(`/sessions/${sessionId}/history`),
    enabled: !!sessionId,
  })
}

// Engineering endpoints

export function useEquipmentSearch(domain: string | null, studyId: string | null) {
  return useQuery({
    queryKey: ['equipment', domain, studyId],
    queryFn: () => api(`/engineering/equipment/${domain}/search${studyId ? `?study_id=${studyId}` : ''}`),
    enabled: !!domain,
  })
}

export function useCompliance(studyId: string | null, worstCase = 'nominal') {
  return useQuery({
    queryKey: ['compliance', studyId, worstCase],
    queryFn: () =>
      api(`/engineering/verification${studyId ? `?study_id=${studyId}&worst_case=${worstCase}` : `?worst_case=${worstCase}`}`),
    enabled: !!studyId,
  })
}

export function useCostEstimate(studyId: string | null) {
  return useQuery({
    queryKey: ['cost', studyId],
    queryFn: () => api(`/engineering/cost${studyId ? `?study_id=${studyId}` : ''}`),
    enabled: !!studyId,
    retry: false,  // Don't retry 404s
  })
}

export function useSensitivity() {
  return useMutation({
    mutationFn: (body: { sweep_param: string; sweep_min: number; sweep_max: number; num_points: number; study_id?: string }) => {
      const query = body.study_id ? `?study_id=${body.study_id}` : ''
      return api(`/engineering/analysis/sensitivity${query}`, {
        method: 'POST',
        body: JSON.stringify(body),
      })
    },
  })
}

export function useEOLCurves(studyId: string | null) {
  return useQuery({
    queryKey: ['eol', studyId],
    queryFn: () => api(`/engineering/analysis/eol-curves${studyId ? `?study_id=${studyId}` : ''}`),
    enabled: !!studyId,
  })
}
