/**
 * useCollaboration — Singleton WebSocket for multi-user collaboration.
 *
 * Uses a module-level WebSocket so all components share ONE connection.
 * State is stored in Zustand for reactive updates across components.
 */
import { useEffect, useCallback } from 'react'
import { create } from 'zustand'
import { useQueryClient } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'
import { ARCADIA_WS_PREFIXES, ANALYSIS_WS_PREFIXES, ANALYSIS_QUERY_KEYS } from '../types/arcadia'
import { setArcadiaInvalidator } from '../hooks/useSessionSocket'

/** Query keys owned by the SCDF-160 components. */
const ARCADIA_QUERY_KEYS = ['options', 'option-compare', 'functions-tree', 'functional-exchanges', 'icd', 'exchange-items', 'element-parameters', 'study-parameters', 'traceability-tree', 'requirements', 'elements', 'interfaces']
function isArcadiaEvent(type: string | undefined): boolean {
  return !!type && ARCADIA_WS_PREFIXES.some(p => type.startsWith(p))
}
/** SCDF-178: analysis_started / analysis_completed / conflict_resolved / option_* / verification_item_* / ground_station_* / element_position_* */
function isAnalysisEvent(type: string | undefined): boolean {
  return !!type && ANALYSIS_WS_PREFIXES.some(p => type.startsWith(p))
}
function invalidateAnalysisKeys(qc: any) {
  for (const key of ANALYSIS_QUERY_KEYS) qc?.invalidateQueries({ queryKey: [key] })
}

export interface CollaborationUser {
  /** Identity (IAP email, else this browser's client id): two people may share a name (WP0). */
  id?: string
  name: string
  connections?: number
  connected_at?: string
}

/** A stable id for this browser, sent with the study socket so presence is not keyed by name. */
export function clientId(): string {
  const KEY = 'scdf.client_id'
  try {
    let id = localStorage.getItem(KEY)
    if (!id) {
      id = (globalThis.crypto?.randomUUID?.() ?? `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`).replace(/[^A-Za-z0-9_-]/g, '')
      localStorage.setItem(KEY, id)
    }
    return id
  } catch { return '' }
}

// ─── Shared collaboration state (Zustand) ───

interface LockHolder { name: string; id: string }

interface CollabStore {
  connected: boolean
  me: string                       // my identity, from the server's welcome message
  users: CollaborationUser[]
  locks: Map<string, LockHolder>   // element_id → holder
  setConnected: (c: boolean) => void
  setMe: (id: string) => void
  setUsers: (u: CollaborationUser[]) => void
  setLock: (elementId: string, heldBy: LockHolder) => void
  removeLock: (elementId: string) => void
  setLocksFromState: (locks: Array<{ element_id: string; held_by: string; held_by_id?: string }>) => void
}

const useCollabStore = create<CollabStore>((set) => ({
  connected: false,
  me: '',
  users: [],
  locks: new Map(),
  setConnected: (c) => set({ connected: c }),
  setMe: (id) => set({ me: id }),
  setUsers: (u) => set({ users: u }),
  setLock: (elementId, heldBy) => set(s => { const n = new Map(s.locks); n.set(elementId, heldBy); return { locks: n } }),
  removeLock: (elementId) => set(s => { const n = new Map(s.locks); n.delete(elementId); return { locks: n } }),
  setLocksFromState: (locks) => set({ locks: new Map(locks.map(l => [l.element_id, { name: l.held_by, id: l.held_by_id || '' }])) }),
}))

// ─── Module-level singleton WebSocket ───

let _ws: WebSocket | null = null
let _heartbeatTimer: number | null = null
let _backoff = 1000
let _connectedStudyId: string | null = null
let _connectedName: string | null = null
let _qcRef: any = null  // QueryClient reference for cache invalidation

function _send(msg: any) {
  if (_ws?.readyState === WebSocket.OPEN) {
    _ws.send(JSON.stringify(msg))
  }
}

function _connect(studyId: string, userName: string) {
  if (_ws && _connectedStudyId === studyId && _connectedName === userName) return  // already connected
  if (_ws) { _ws.close(); _ws = null }

  const base = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
  const url = `${base}/ws/study/${studyId}?name=${encodeURIComponent(userName)}&client_id=${encodeURIComponent(clientId())}`

  try {
    const ws = new WebSocket(url)
    _ws = ws
    _connectedStudyId = studyId
    _connectedName = userName

    ws.onopen = () => {
      useCollabStore.getState().setConnected(true)
      _backoff = 1000
      if (_heartbeatTimer) clearInterval(_heartbeatTimer)
      _heartbeatTimer = window.setInterval(() => _send({ type: 'heartbeat' }), 10000)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const store = useCollabStore.getState()
        switch (msg.type) {
          case 'welcome':
            store.setMe(msg.you?.id || '')
            break
          case 'gate_state_changed':
          case 'gate_profile_changed':
          case 'study_records_changed':
            for (const key of ['gates', 'gate-review', 'risks', 'trade', 'logbook-decisions', 'margin-ladder']) _qcRef?.invalidateQueries({ queryKey: [key] })
            break
          case 'team_changed':
            // Seats (WP9): holders, requests, pending changes, messages, freeze, timer
            for (const key of ['team', 'seat-pending', 'seat-subs', 'seat-ledger', 'seat-next', 'seat-events', 'gates', 'gate-review']) _qcRef?.invalidateQueries({ queryKey: [key] })
            if (msg.what === 'inject' || msg.what === 'pending') _qcRef?.refetchQueries({ type: 'active' })
            break
          case 'users_update':
            store.setUsers(msg.users || [])
            break
          case 'locks_state':
            store.setLocksFromState(msg.locks || [])
            break
          case 'element_locked':
          case 'lock_granted':
            store.setLock(msg.element_id, { name: msg.held_by || userName, id: msg.held_by_id || '' })
            break
          case 'lock_denied':
            break
          case 'lock_released':
          case 'lock_expired':
            store.removeLock(msg.element_id)
            break
          case 'element_created':
          case 'element_updated':
          case 'element_deleted':
          case 'interface_created':
          case 'interface_changed':
          case 'interfaces_proposed':
          case 'interface_deleted':
            // Refetch ALL active queries — ensures budget, requirements,
            // interfaces, escalation, readiness all update immediately
            _qcRef?.refetchQueries({ type: 'active' })
            break
          default:
            // SCDF-160 Arcadia spine events (function_*, functions_migrated,
            // functional_exchange_*, exchange_item_*, interface_exchange_items_*,
            // relation_*, realization_*, parameter_*, parameters_recomputed,
            // model_imported): invalidate the spine queries so trees / ICD /
            // parameters / traceability refetch.
            if (isArcadiaEvent(msg.type)) {
              for (const key of ARCADIA_QUERY_KEYS) _qcRef?.invalidateQueries({ queryKey: [key] })
              if (msg.type === 'model_imported' || msg.type === 'functions_migrated') _qcRef?.refetchQueries({ type: 'active' })
            }
            // SCDF-178: analyses / options / V&V / ground stations / positions →
            // analyses, conflicts, parameters, options (and budgets/escalation) refetch.
            if (isAnalysisEvent(msg.type)) invalidateAnalysisKeys(_qcRef)
            break
        }
      } catch { /* ignore */ }
    }

    ws.onclose = () => {
      useCollabStore.getState().setConnected(false)
      _ws = null
      if (_heartbeatTimer) { clearInterval(_heartbeatTimer); _heartbeatTimer = null }
      const delay = Math.min(_backoff, 30000)
      _backoff *= 1.5
      window.setTimeout(() => _connect(studyId, userName), delay)
    }
  } catch { /* onclose handles reconnect */ }
}


// ─── Hook (connects on mount, all callers share one connection) ───

export function useCollaboration() {
  const studyId = useUIStore(s => s.studyId)
  const userName = useUIStore(s => s.userName)
  const qc = useQueryClient()

  // Store QueryClient ref for WebSocket handler
  _qcRef = qc
  // Legacy session socket (useSessionSocket) forwards Arcadia spine events here too
  setArcadiaInvalidator((type) => {
    if (isArcadiaEvent(type)) for (const key of ARCADIA_QUERY_KEYS) qc.invalidateQueries({ queryKey: [key] })
    if (isAnalysisEvent(type)) invalidateAnalysisKeys(qc)
  })

  // Connect/reconnect when studyId or userName changes
  useEffect(() => {
    if (studyId && userName) {
      _connect(studyId, userName)
    }
    return () => {
      // Don't disconnect on unmount — other components may still need it
      // Only disconnect when studyId changes (handled by the effect re-running)
    }
  }, [studyId, userName])

  const connected = useCollabStore(s => s.connected)
  const users = useCollabStore(s => s.users)
  const locks = useCollabStore(s => s.locks)

  const requestLock = useCallback((elementId: string) => {
    _send({ type: 'lock_request', element_id: elementId })
  }, [])

  const releaseLock = useCallback((elementId: string) => {
    _send({ type: 'lock_release', element_id: elementId })
  }, [])

  const me = useCollabStore(s => s.me)
  const isLockedByOther = useCallback((elementId: string) => {
    const holder = locks.get(elementId)
    if (holder == null) return false
    return holder.id && me ? holder.id !== me : holder.name !== userName
  }, [locks, userName, me])

  const lockHolder = useCallback((elementId: string) => {
    return locks.get(elementId)?.name || null
  }, [locks])

  return { connected, users, locks, me, myName: userName || '', requestLock, releaseLock, isLockedByOther, lockHolder }
}
