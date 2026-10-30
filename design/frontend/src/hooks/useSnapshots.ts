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

export interface SnapshotInfo {
  id: number
  session_id: string
  name: string | null
  label: string
  version: number
  parent_snapshot_id: number | null
  tags: string[]
  created_at: string
}

export interface ParamDelta {
  param_id: string
  value_a: any
  value_b: any
  unit: string
  source_a: string | null
  source_b: string | null
  change_type: 'added' | 'removed' | 'changed' | 'unchanged'
  delta: number | null
  delta_percent: number | null
}

export interface DiffPayload {
  a: SnapshotInfo
  b: SnapshotInfo
  summary: {
    total_diffs: number
    changed: number
    added: number
    removed: number
  }
  deltas: ParamDelta[]
}

export function useSnapshots(sessionId: string | null) {
  return useQuery<SnapshotInfo[]>({
    queryKey: ['snapshots', sessionId],
    queryFn: () => api<SnapshotInfo[]>(`/snapshots/sessions/${sessionId}`),
    enabled: !!sessionId,
    staleTime: 5_000,
  })
}

export function useCreateSnapshot() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ sessionId, name, tags }: { sessionId: string; name: string; tags?: string[] }) =>
      api<SnapshotInfo>(`/snapshots/sessions/${sessionId}`, {
        method: 'POST',
        body: JSON.stringify({ name, label: 'manual', tags: tags || [] }),
      }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ['snapshots', vars.sessionId] })
    },
  })
}

export function useDiffSnapshots(a: number | null, b: number | null) {
  return useQuery<DiffPayload>({
    queryKey: ['snapshot-diff', a, b],
    queryFn: () => api<DiffPayload>(`/snapshots/diff?a=${a}&b=${b}`),
    enabled: a !== null && b !== null && a !== b,
    staleTime: 30_000,
  })
}

export function useMbseExport() {
  return useMutation({
    mutationFn: (studyId: string) =>
      api<any>(`/exports/mbse/${studyId}`, { method: 'POST' }),
  })
}
