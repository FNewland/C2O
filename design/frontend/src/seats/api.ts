/**
 * SpaceCDF seats (redesign WP9) — client state and the fetch wrapper.
 *
 * Every same-origin /api request carries who is asking and from which seat:
 *   X-C2O-Client  this browser's id (localStorage)   — laptop identity
 *   X-C2O-Name    the typed name (URI-encoded)        — display only
 *   X-C2O-Seat    the active seat                     — the seat the write is recorded for
 * Behind IAP the server reads the signed-in e-mail instead and ignores the client id.
 *
 * Ruling 5 in the browser: a write the server answers with 409 `owned_by_other_seat` asks
 * "owned by Power — your change goes to them for review"; on Continue it is sent again with
 * X-C2O-Confirm-Review: 1 and comes back 202 + pending_change (a toast says so). Every
 * component that edits the model gets this without changes of its own.
 */
import { create } from 'zustand'
import i18n from '../i18n'
import { askConfirm } from '../components/ui/Dialog'
import { useUIStore } from '../stores/uiStore'
import { clientId } from '../workbench/useCollaboration'

export type Lang2 = { en: string; fr: string }
export type ActivityTab = 'blocks' | 'spacecraft' | 'budget' | 'requirements' | 'functions' | 'interfaces' | 'icd' | 'trace' | 'decide' | 'analyses'

export interface SeatDef {
  id: string
  label: Lang2
  kind: 'lead' | 'systems' | 'domain' | 'customer' | 'observer' | 'instructor'
  exclusive: boolean
  optional?: boolean
  fallback?: string
  sees_first?: { view: 'top' | 'spacecraft' | 'vv'; panel: ActivityTab; focus?: Lang2 }
  tabs?: ActivityTab[]
  prefixes: string[]
}
export interface Catalogue {
  seats: SeatDef[]
  presets: { id: string; label: Lang2; groups: string[][] }[]
  timing: { idle_after_s: number; reclaimable_after_s: number; handover_timeout_s: number }
}
export interface Holder {
  person_id: string; name: string; verified: boolean; since: string; assigned_by: string
  status: 'active' | 'idle' | 'reclaimable'; active_seat?: string | null; last_action?: string | null
  last_action_at?: string | null; hand?: boolean
}
export interface SeatView {
  id: string; label: Lang2; kind: SeatDef['kind']; exclusive: boolean
  state: 'free' | 'held' | 'idle' | 'locked'; holders: Holder[]; reclaimable: boolean
  locked?: { by: string; at: string } | null
  request?: { person_id: string; name: string; expires: number; timeout_s: number } | null
}
export interface TeamMessage { id: string; at: string; from: string; text: string; scope: 'all' | 'team'; kind: string; code?: string }
export interface TeamView {
  study_id: string; enabled: boolean; preset: string | null; optional: string[]; groups: string[][]
  seats: SeatView[]
  frozen: { by: string; at: string } | null
  timer: { ends_at: number; minutes: number; label: string; set_by: string } | null
  messages: TeamMessage[]
  hands: Record<string, { name: string; seat: string | null; at: string }>
  me?: {
    id: string; name: string; verified: boolean; email: string | null
    held: string[]; active: string | null; instructor: boolean
    requests_to_me: { seat: string; person_id: string; name: string; expires: number; timeout_s: number }[]
    my_requests: { seat: string; expires: number }[]
  }
}
export interface Me {
  id: string; name: string; verified: boolean; email: string | null
  instructor: boolean; instructor_status: 'listed' | 'claimed' | null
  instructor_mode: 'list' | 'laptop'; instructors_configured: number
  laptop_instructor: { name: string; since: string } | null
}
export interface PendingChange {
  id: string; study_id: string; owner_seat: string; kind: string; element_id: string; element_name: string
  param_keys: string[]; old: Record<string, unknown>; new: Record<string, unknown>
  by_person: string; by_name: string; by_seat: string; created_at: string
  status: 'pending' | 'accepted' | 'rejected' | 'withdrawn'
  reviewed_name: string; reviewed_seat: string; reviewed_at: string | null; comment: string
}

// ─── store ──────────────────────────────────────────────────────────────────

export type DrawerTab = 'seats' | 'review' | 'subs' | 'ledger' | 'activity'
interface Toast { id: number; text: string; tone: 'ok' | 'caution' | 'alarm' | 'info' }

interface SeatStore {
  me: Me | null
  catalogue: Catalogue | null
  team: TeamView | null
  showAll: boolean
  shadow: string | null          // study id the instructor shadows (read-only)
  drawer: DrawerTab | null
  board: boolean                 // instructor class board open
  vvSection: string | null       // V&V sub-tab to open (gate checklist for the Team leader / Next card)
  toasts: Toast[]
  setMe: (m: Me | null) => void
  setCatalogue: (c: Catalogue) => void
  setTeam: (t: TeamView | null) => void
  setShowAll: (v: boolean) => void
  setShadow: (sid: string | null) => void
  setDrawer: (d: DrawerTab | null) => void
  setBoard: (b: boolean) => void
  openVV: (section: string | null) => void
  toast: (text: string, tone?: Toast['tone']) => void
  dismiss: (id: number) => void
}

let _toastId = 0
const SHADOW_KEY = 'scdf.seat.shadow'
function readShadow(): string | null { try { return sessionStorage.getItem(SHADOW_KEY) } catch { return null } }

export const useSeatStore = create<SeatStore>((set) => ({
  me: null, catalogue: null, team: null, showAll: false, shadow: readShadow(), drawer: null, board: false, vvSection: null, toasts: [],
  setMe: (me) => set({ me }),
  setCatalogue: (catalogue) => set({ catalogue }),
  setTeam: (team) => set({ team }),
  setShowAll: (showAll) => set({ showAll }),
  setShadow: (shadow) => {
    // Kept for this tab, so a reload stays read-only.
    try { if (shadow) sessionStorage.setItem(SHADOW_KEY, shadow); else sessionStorage.removeItem(SHADOW_KEY) } catch { /* private mode */ }
    set({ shadow })
  },
  setDrawer: (drawer) => set({ drawer }),
  setBoard: (board) => set({ board }),
  openVV: (vvSection) => set({ vvSection }),
  toast: (text, tone = 'info') => {
    const id = ++_toastId
    set(s => ({ toasts: [...s.toasts.slice(-3), { id, text, tone }] }))
    window.setTimeout(() => useSeatStore.getState().dismiss(id), 7000)
  },
  dismiss: (id) => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),
}))

/** The seat this browser writes from: the server's view of my active seat. */
export function activeSeat(): string | null {
  const s = useSeatStore.getState()
  if (s.shadow) return null
  return s.team?.enabled ? (s.team.me?.active ?? null) : null
}

export function seatDef(id: string | null | undefined): SeatDef | undefined {
  if (!id) return undefined
  return useSeatStore.getState().catalogue?.seats.find(s => s.id === id)
}

export function seatLabel(id: string | null | undefined, lang?: string): string {
  if (!id) return ''
  if (id === 'instructor') return i18n.t('Instructor')
  const d = seatDef(id)
  const l = (lang || i18n.language || 'en').startsWith('fr') ? 'fr' : 'en'
  return d ? d.label[l] : id
}

export function pick(l: Lang2 | null | undefined, lang?: string): string {
  if (!l) return ''
  return (lang || i18n.language || 'en').startsWith('fr') ? (l.fr || l.en) : l.en
}

// ─── HTTP ───────────────────────────────────────────────────────────────────

export function seatHeaders(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { ...(extra || {}) }
  const cid = clientId()
  if (cid) h['X-C2O-Client'] = cid
  const name = useUIStore.getState().userName
  if (name) h['X-C2O-Name'] = encodeURIComponent(name)
  const seat = activeSeat()
  if (seat) h['X-C2O-Seat'] = seat
  return h
}

export async function api<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { ...(init.body ? { 'Content-Type': 'application/json' } : {}), ...(init.headers as Record<string, string> || {}) },
  })
  if (!res.ok) {
    let detail: any = null
    try { detail = (await res.json()).detail } catch { /* not JSON */ }
    const err = new Error(seatErrorText(detail, res.status)) as Error & { status?: number; detail?: any }
    err.status = res.status
    err.detail = detail
    throw err
  }
  const ct = res.headers.get('content-type') || ''
  return (ct.includes('json') ? res.json() : res.text()) as Promise<T>
}

export const post = <T = any>(path: string, body: unknown = {}) =>
  api<T>(path, { method: 'POST', body: JSON.stringify(body) })

/** A readable, translated reason for a seat refusal. */
export function seatErrorText(detail: any, status?: number): string {
  const code = detail && typeof detail === 'object' ? detail.code : null
  switch (code) {
    case 'no_seat': return i18n.t('Claim a seat to edit this study.')
    case 'observer_read_only': return i18n.t('Observers have read-only access.')
    case 'customer_requirements_only': return i18n.t('The Customer writes mission requirements only.')
    case 'read_only_seat': return i18n.t('Your seat cannot edit design parameters.')
    case 'study_frozen': return i18n.t('The instructor froze this study. Edits are paused.')
    case 'lead_only': return i18n.t('Only the Team leader or the instructor can do this.')
    case 'instructor_only': return i18n.t('Only the instructor can do this.')
    case 'delete_not_allowed': return i18n.t('Only the owning seat, the Team leader, Systems or the instructor delete this element.')
    case 'seat_held': return i18n.t('{{seat}} is held by {{name}}. Use Request seat.', { seat: seatLabel(detail.seat), name: detail.holder })
    case 'seat_locked': return i18n.t('The instructor locked this seat.')
    case 'not_owner': return i18n.t('Only the owning seat reviews this change.')
    case 'comment_required': return i18n.t('Say why you reject the change.')
    case 'no_request': return i18n.t('The request timed out.')
    case 'instructor_taken': return i18n.t('Someone else is already the instructor.')
    case 'instructor_list': return i18n.t('Instructors are set on the server (SPACECDF_INSTRUCTORS).')
    case 'anonymous': return i18n.t('Enter your name first.')
  }
  if (detail && typeof detail === 'object' && detail.message) return String(detail.message)
  if (typeof detail === 'string') return detail
  return i18n.t('Request failed ({{status}})', { status: status ?? '?' })
}

const QUIET_CODES = new Set(['owned_by_other_seat'])
const TOAST_CODES = new Set(['no_seat', 'observer_read_only', 'customer_requirements_only', 'read_only_seat',
  'study_frozen', 'lead_only', 'instructor_only', 'delete_not_allowed'])

function isApi(input: RequestInfo | URL): string | null {
  const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
  try {
    const u = new URL(url, window.location.href)
    if (u.origin !== window.location.origin || !u.pathname.startsWith('/api/')) return null
    return u.pathname
  } catch { return null }
}

let _installed = false

/** Wrap window.fetch once (main.tsx): identity headers + the ruling-5 review flow. */
export function installSeatFetch(): void {
  if (_installed || typeof window === 'undefined') return
  _installed = true
  const orig = window.fetch.bind(window)
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const path = isApi(input)
    if (!path || input instanceof Request) return orig(input, init)
    const headers = new Headers(init?.headers || {})
    for (const [k, v] of Object.entries(seatHeaders())) if (!headers.has(k)) headers.set(k, v)
    const res = await orig(input, { ...init, headers })
    const method = (init?.method || 'GET').toUpperCase()
    if (method === 'GET' || res.ok && res.status !== 202) return res
    if (res.status === 202) {
      try {
        const body = await res.clone().json()
        if (body?.pending_change) {
          useSeatStore.getState().toast(i18n.t('Sent to {{seat}} for review. Their value stands until they accept.',
            { seat: seatLabel(body.pending_change.owner_seat) }), 'info')
        }
      } catch { /* not JSON */ }
      return res
    }
    let detail: any = null
    try { detail = (await res.clone().json()).detail } catch { return res }
    const code = detail && typeof detail === 'object' ? detail.code : null
    if (res.status === 409 && code === 'owned_by_other_seat') {
      const seat = seatLabel(detail.owner_seat)
      const fields = (detail.fields || []).join(', ')
      const holder = detail.owner_holder ? ` (${detail.owner_holder})` : ''
      const ok = await askConfirm(
        i18n.t('{{element}} · {{fields}} is owned by {{seat}}{{holder}} — your change goes to them for review. Until they accept, their value stands in every analysis.',
          { element: detail.element_name || '', fields, seat, holder }),
        { title: i18n.t('Owned by {{seat}}', { seat }), confirmLabel: i18n.t('Send for review') })
      if (!ok) return res
      headers.set('X-C2O-Confirm-Review', '1')
      const again = await orig(input, { ...init, headers })
      if (again.status === 202) {
        useSeatStore.getState().toast(i18n.t('Sent to {{seat}} for review. Their value stands until they accept.', { seat }), 'info')
      }
      return again
    }
    if (code && TOAST_CODES.has(code) && !QUIET_CODES.has(code)) {
      useSeatStore.getState().toast(seatErrorText(detail, res.status), code === 'study_frozen' ? 'caution' : 'alarm')
    }
    return res
  }
}
