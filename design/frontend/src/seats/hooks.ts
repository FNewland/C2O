/**
 * Seat queries. The team document is polled (5 s) and refreshed on the study socket's
 * `team_changed`; the heartbeat (30 s) keeps my seats Held rather than Idle.
 */
import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'
import { api, post, useSeatStore, type Catalogue, type Me, type PendingChange, type TeamView } from './api'

const enc = encodeURIComponent

export function useSeatBootstrap() {
  const userName = useUIStore(s => s.userName)
  const setMe = useSeatStore(s => s.setMe)
  const setCatalogue = useSeatStore(s => s.setCatalogue)
  const me = useQuery<Me>({ queryKey: ['seat-me', userName], queryFn: () => api('/api/seats/me'), enabled: !!userName, staleTime: 30_000 })
  const cat = useQuery<Catalogue>({ queryKey: ['seat-catalogue'], queryFn: () => api('/api/seats/catalogue'), staleTime: Infinity })
  useEffect(() => { if (me.data) setMe(me.data) }, [me.data, setMe])
  useEffect(() => { if (cat.data) setCatalogue(cat.data) }, [cat.data, setCatalogue])
  return { me: me.data, refetchMe: me.refetch }
}

export function useTeam() {
  const studyId = useUIStore(s => s.studyId)
  const setTeam = useSeatStore(s => s.setTeam)
  const q = useQuery<TeamView>({
    queryKey: ['team', studyId],
    queryFn: () => api(`/api/studies/${enc(studyId!)}/team`),
    enabled: !!studyId, refetchInterval: 5000,
  })
  useEffect(() => { setTeam(q.data ?? null) }, [q.data, setTeam])
  // Heartbeat: presence for my seats (Idle after 3 min without one).
  useEffect(() => {
    if (!studyId) return
    const beat = () => { void post(`/api/studies/${enc(studyId)}/team/heartbeat`, {}).catch(() => {}) }
    beat()
    const id = window.setInterval(beat, 30_000)
    return () => window.clearInterval(id)
  }, [studyId])
  return q
}

export function usePending(opts: { seat?: string; mine?: boolean; status?: string }, enabled = true) {
  const studyId = useUIStore(s => s.studyId)
  const qs = new URLSearchParams()
  if (opts.seat) qs.set('seat', opts.seat)
  if (opts.mine) qs.set('mine', '1')
  qs.set('status', opts.status ?? 'pending')
  return useQuery<PendingChange[]>({
    queryKey: ['seat-pending', studyId, opts.seat ?? '', !!opts.mine, opts.status ?? 'pending'],
    queryFn: () => api(`/api/studies/${enc(studyId!)}/team/pending?${qs}`),
    enabled: !!studyId && enabled, refetchInterval: 10_000,
  })
}

export interface Subscription {
  element_id: string; element_name: string; field: string; param_key: string
  owner_seat: string | null; value: unknown; seen_value: unknown; changed: boolean; missing: boolean
}
export function useSubscriptions(seat: string | null) {
  const studyId = useUIStore(s => s.studyId)
  return useQuery<Subscription[]>({
    queryKey: ['seat-subs', studyId, seat],
    queryFn: () => api(`/api/studies/${enc(studyId!)}/team/subscriptions?seat=${enc(seat!)}`),
    enabled: !!studyId && !!seat, refetchInterval: 15_000,
  })
}

export interface LedgerRow {
  key: string; element_id: string | null; element_name: string | null; field: string | null; value: unknown
  wanted_by: string[]; owner_seat: string | null; owner_holder: string | null; status: 'unowned' | 'requested' | 'no_value' | 'provided'
  source: 'subscription' | 'wanted'; note?: string
}
export function useLedger(enabled = true) {
  const studyId = useUIStore(s => s.studyId)
  return useQuery<{ rows: LedgerRow[]; counts: Record<string, number> }>({
    queryKey: ['seat-ledger', studyId],
    queryFn: () => api(`/api/studies/${enc(studyId!)}/team/ledger`),
    enabled: !!studyId && enabled,
  })
}

export interface NextCardData {
  seat?: string
  kind: 'gate_item' | 'proposals' | 'subscriptions' | 'step' | 'none' | 'no_seat'
  gate?: string | null; criterion_id?: string; question?: string; fix?: string | null
  step?: string | null; step_label?: { en: string; fr: string } | null
  count?: number; first?: { element_name?: string; by_name?: string; by_seat?: string; field?: string; owner_seat?: string; fields?: string[] }
}
export function useNextCard(seat: string | null) {
  const studyId = useUIStore(s => s.studyId)
  return useQuery<NextCardData>({
    queryKey: ['seat-next', studyId, seat],
    queryFn: () => api(`/api/studies/${enc(studyId!)}/team/next?seat=${enc(seat!)}`),
    enabled: !!studyId && !!seat, refetchInterval: 20_000,
  })
}

export interface SeatEvent { ts: string; seat_id: string; person_id: string; person_name: string; verified: boolean; action: string; target: string; detail: Record<string, any> }
export function useSeatEvents(enabled = true) {
  const studyId = useUIStore(s => s.studyId)
  return useQuery<SeatEvent[]>({
    queryKey: ['seat-events', studyId],
    queryFn: () => api(`/api/studies/${enc(studyId!)}/team/events?limit=80`),
    enabled: !!studyId && enabled,
  })
}

export function useOwnership() {
  const studyId = useUIStore(s => s.studyId)
  return useQuery<{ enabled: boolean; owners: Record<string, string | null> }>({
    queryKey: ['seat-ownership', studyId],
    queryFn: () => api(`/api/studies/${enc(studyId!)}/team/ownership`),
    enabled: !!studyId, staleTime: 10_000,
  })
}
