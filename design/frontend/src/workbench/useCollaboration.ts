/**
 * useCollaboration — WebSocket hook for real-time multi-user collaboration.
 *
 * Connects to ws://host/ws/study/{studyId}?name=UserName
 * Handles:
 * - Real-time element/interface/requirement sync
 * - Edit locking (pessimistic — one editor at a time per element)
 * - Presence tracking (who's connected)
 * - Heartbeat (10s interval, 30s timeout for lock expiry)
 * - Auto-reconnect with exponential backoff
 */
import { useEffect, useRef, useCallback, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'

export interface CollaborationUser {
  name: string
  connected_at?: string
}

export interface ElementLock {
  element_id: string
  held_by: string
}

interface CollaborationState {
  connected: boolean
  users: CollaborationUser[]
  locks: Map<string, string>  // element_id → held_by name
  myName: string
  requestLock: (elementId: string) => void
  releaseLock: (elementId: string) => void
  isLockedByOther: (elementId: string) => boolean
  lockHolder: (elementId: string) => string | null
}

const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`

export function useCollaboration(): CollaborationState {
  const studyId = useUIStore(s => s.studyId)
  const userName = useUIStore(s => s.userName)
  const qc = useQueryClient()

  const wsRef = useRef<WebSocket | null>(null)
  const heartbeatRef = useRef<number | null>(null)
  const reconnectRef = useRef<number | null>(null)
  const backoffRef = useRef(1000)

  const [connected, setConnected] = useState(false)
  const [users, setUsers] = useState<CollaborationUser[]>([])
  const [locks, setLocks] = useState<Map<string, string>>(new Map())

  const send = useCallback((msg: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  const connect = useCallback(() => {
    if (!studyId || !userName) return
    const url = `${WS_BASE}/ws/study/${studyId}?name=${encodeURIComponent(userName)}`

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        backoffRef.current = 1000

        // Start heartbeat
        if (heartbeatRef.current) clearInterval(heartbeatRef.current)
        heartbeatRef.current = window.setInterval(() => {
          send({ type: 'heartbeat' })
        }, 10000)
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          switch (msg.type) {
            case 'users_update':
              setUsers(msg.users || [])
              break
            case 'locks_state':
              const newLocks = new Map<string, string>()
              for (const lock of (msg.locks || [])) {
                newLocks.set(lock.element_id, lock.held_by)
              }
              setLocks(newLocks)
              break
            case 'element_locked':
              setLocks(prev => { const n = new Map(prev); n.set(msg.element_id, msg.held_by); return n })
              break
            case 'lock_granted':
              setLocks(prev => { const n = new Map(prev); n.set(msg.element_id, userName); return n })
              break
            case 'lock_denied':
              // Could show a toast — for now just update state
              break
            case 'lock_released':
            case 'lock_expired':
              setLocks(prev => { const n = new Map(prev); n.delete(msg.element_id); return n })
              break
            case 'element_created':
            case 'element_updated':
            case 'element_deleted':
              qc.invalidateQueries({ queryKey: ['elements', studyId] })
              break
            case 'interface_created':
            case 'interface_deleted':
              qc.invalidateQueries({ queryKey: ['interfaces', studyId] })
              break
            case 'pong':
              break
          }
        } catch { /* ignore parse errors */ }
      }

      ws.onclose = () => {
        setConnected(false)
        if (heartbeatRef.current) { clearInterval(heartbeatRef.current); heartbeatRef.current = null }

        // Auto-reconnect with backoff
        const delay = Math.min(backoffRef.current, 30000)
        backoffRef.current *= 1.5
        reconnectRef.current = window.setTimeout(connect, delay)
      }

      ws.onerror = () => { /* onclose will fire */ }
    } catch { /* connection failed — onclose will handle reconnect */ }
  }, [studyId, userName, send, qc])

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null }
      if (heartbeatRef.current) clearInterval(heartbeatRef.current)
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
    }
  }, [connect])

  const requestLock = useCallback((elementId: string) => {
    send({ type: 'lock_request', element_id: elementId })
  }, [send])

  const releaseLock = useCallback((elementId: string) => {
    send({ type: 'lock_release', element_id: elementId })
  }, [send])

  const isLockedByOther = useCallback((elementId: string) => {
    const holder = locks.get(elementId)
    return holder != null && holder !== userName
  }, [locks, userName])

  const lockHolder = useCallback((elementId: string) => {
    return locks.get(elementId) || null
  }, [locks])

  return { connected, users, locks, myName: userName || '', requestLock, releaseLock, isLockedByOther, lockHolder }
}
