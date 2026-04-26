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

export interface OptimizerObjective {
  key: string
  description: string
  parameter_id: string
  direction: 'min' | 'max'
}

export interface DefaultVariable {
  id: string
  lower: number
  upper: number
}

export interface OptimizerConfigResponse {
  objectives: OptimizerObjective[]
  default_variables: DefaultVariable[]
}

export interface OptimizeRun {
  id: number
  session_id: string
  study_id: string | null
  algo: string
  objective: string
  variables: string[]
  status: 'running' | 'done' | 'failed' | 'queued' | string
  num_evals: number
  best_x: Record<string, number>
  best_y: number | null
  duration_ms: number
  error: string | null
  created_at: string
  finished_at: string | null
  latest_event?: any
}

export function useOptimizerConfig() {
  return useQuery<OptimizerConfigResponse>({
    queryKey: ['optimizer-config'],
    queryFn: () => api<OptimizerConfigResponse>('/optimize/config'),
    staleTime: 300_000,
  })
}

export function useStartOptimization() {
  return useMutation({
    mutationFn: (args: {
      sessionId: string
      objective: string
      variables: string[]
      bounds: [number, number][]
      max_evals: number
      seed?: number
    }) =>
      api<{ run_id: number }>(`/optimize/sessions/${args.sessionId}`, {
        method: 'POST',
        body: JSON.stringify({
          objective: args.objective,
          variables: args.variables,
          bounds: args.bounds,
          max_evals: args.max_evals,
          seed: args.seed ?? 42,
        }),
      }),
  })
}

export function useOptimizerRun(runId: number | null, poll: boolean = true) {
  return useQuery<OptimizeRun>({
    queryKey: ['optimize-run', runId],
    queryFn: () => api<OptimizeRun>(`/optimize/runs/${runId}`),
    enabled: runId !== null,
    refetchInterval: poll ? 500 : false,
    staleTime: 0,
  })
}
