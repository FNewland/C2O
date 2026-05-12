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

export interface CollaborationUser {
  name: string
  connected_at?: string
}

// ─── Shared collaboration state (Zustand) ───

interface CollabStore {
  connected: boolean
  users: CollaborationUser[]
  locks: Map<string, string>  // element_id → held_by
  setConnected: (c: boolean) => void
  setUsers: (u: CollaborationUser[]) => void
  setLock: (elementId: string, heldBy: string) => void
  removeLock: (elementId: string) => void
  setLocksFromState: (locks: Array<{ element_id: string; held_by: string }>) => void
}

const useCollabStore = create<CollabStore>((set) => ({
  connected: false,
  users: [],
  locks: new Map(),
  setConnected: (c) => set({ connected: c }),
  setUsers: (u) => set({ users: u }),
  setLock: (elementId, heldBy) => set(s => { const n = new Map(s.locks); n.set(elementId, heldBy); return { locks: n } }),
  removeLock: (elementId) => set(s => { const n = new Map(s.locks); n.delete(elementId); return { locks: n } }),
  setLocksFromState: (locks) => set({ locks: new Map(locks.map(l => [l.element_id, l.held_by])) }),
}))

// ─── Module-level singleton WebSocket ───

let _ws: WebSocket | null = null
let _heartbeatTimer: number | null = null
let _reconnectTimer: number | null = null
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
  const url = `${base}/ws/study/${studyId}?name=${encodeURIComponent(userName)}`

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
          case 'users_update':
            store.setUsers(msg.users || [])
            break
          case 'locks_state':
            store.setLocksFromState(msg.locks || [])
            break
          case 'element_locked':
          case 'lock_granted':
            store.setLock(msg.element_id, msg.held_by || userName)
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
            // Invalidate + force refetch with cache bust
            _qcRef?.invalidateQueries({ queryKey: ['elements', studyId], refetchType: 'all' })
            _qcRef?.invalidateQueries({ queryKey: ['budget'], refetchType: 'all' })
            _qcRef?.invalidateQueries({ queryKey: ['escalation'], refetchType: 'all' })
            break
          case 'interface_created':
          case 'interface_deleted':
            _qcRef?.invalidateQueries({ queryKey: ['interfaces', studyId], refetchType: 'all' })
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
      _reconnectTimer = window.setTimeout(() => _connect(studyId, userName), delay)
    }
  } catch { /* onclose handles reconnect */ }
}

function _disconnect() {
  if (_ws) { _ws.close(); _ws = null }
  if (_heartbeatTimer) { clearInterval(_heartbeatTimer); _heartbeatTimer = null }
  if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null }
  _connectedStudyId = null
  _connectedName = null
  useCollabStore.getState().setConnected(false)
  useCollabStore.getState().setUsers([])
}

// ─── Hook (connects on mount, all callers share one connection) ───

export function useCollaboration() {
  const studyId = useUIStore(s => s.studyId)
  const userName = useUIStore(s => s.userName)
  const qc = useQueryClient()

  // Store QueryClient ref for WebSocket handler
  _qcRef = qc

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

  const isLockedByOther = useCallback((elementId: string) => {
    const holder = locks.get(elementId)
    return holder != null && holder !== userName
  }, [locks, userName])

  const lockHolder = useCallback((elementId: string) => {
    return locks.get(elementId) || null
  }, [locks])

  return { connected, users, locks, myName: userName || '', requestLock, releaseLock, isLockedByOther, lockHolder }
}
