import { useEffect, useRef, useState, useCallback } from 'react'
import { useSessionStore } from '../stores/sessionStore'

// WebSocket client with auto-reconnect for SpaceCDF concurrent design sessions.
// Backs SessionBar, LiveEditToast, PositionPanel presence, and live parameter updates.

export type WSStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error'

export interface WSMessage {
  type: string
  [key: string]: any
}

const BACKOFF_MIN_MS = 1000
const BACKOFF_MAX_MS = 30000

export function useSessionSocket(sessionId: string | null, positionId: string | null, displayName = '') {
  const [status, setStatus] = useState<WSStatus>('disconnected')
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const backoffRef = useRef(BACKOFF_MIN_MS)
  const shouldReconnectRef = useRef(true)

  // Session store setters for message dispatch
  const applyIncomingEdit = useSessionStore(s => s.applyIncomingEdit)
  const setPresence = useSessionStore(s => s.setPresence)
  const setStateSnapshot = useSessionStore(s => s.setStateSnapshot)
  const applyStateUpdate = useSessionStore(s => s.applyStateUpdate)
  const pushToast = useSessionStore(s => s.pushToast)
  const setConvergenceInfo = useSessionStore(s => s.setConvergenceInfo)

  const dispatch = useCallback(
    (msg: WSMessage) => {
      setLastMessage(msg)
      switch (msg.type) {
        case 'state_snapshot':
          setStateSnapshot(msg.parameters || {}, msg.active_positions || [])
          break
        case 'parameter_update':
          applyIncomingEdit(msg)
          if (msg.edited_by !== positionId) {
            pushToast({
              id: `${msg.parameter_id}-${msg.timestamp}`,
              actor: msg.display_name || msg.edited_by,
              parameterId: msg.parameter_id,
              newValue: msg.new_value,
              oldValue: msg.old_value,
              equipmentId: msg.equipment_id,
              timestamp: msg.timestamp,
            })
          }
          break
        case 'state_update':
          applyStateUpdate(msg.updates || {})
          break
        case 'convergence_complete':
          setConvergenceInfo({
            cascadeRounds: msg.cascade_rounds,
            changedParams: msg.changed_params || [],
            timeMs: msg.time_ms,
            triggeredBy: msg.triggered_by,
          })
          break
        case 'participant_joined':
        case 'participant_left':
          setPresence(msg.active_positions || [], msg)
          break
        case 'edit_rejected':
          pushToast({
            id: `reject-${Date.now()}`,
            actor: 'System',
            parameterId: msg.parameter_id,
            newValue: null,
            oldValue: null,
            equipmentId: null,
            timestamp: new Date().toISOString(),
            isError: true,
            errorMessage: msg.reason,
          })
          break
        case 'error':
          console.warn('WS error:', msg.message)
          break
        default:
          break
      }
    },
    [positionId, applyIncomingEdit, setPresence, setStateSnapshot, applyStateUpdate, pushToast, setConvergenceInfo],
  )

  useEffect(() => {
    if (!sessionId || !positionId) return

    shouldReconnectRef.current = true
    backoffRef.current = BACKOFF_MIN_MS

    const connect = () => {
      if (!shouldReconnectRef.current) return
      setStatus(prev => (prev === 'connected' ? 'reconnecting' : 'connecting'))

      const host = window.location.host.replace(/:\d+$/, ':8000')
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
      // Send all claimed positions as comma-separated position_ids for multi-role support
      const allPositions = useSessionStore.getState().positionIds
      const posIds = allPositions.length > 0 ? allPositions.join(',') : positionId
      const url = `${proto}://${host}/ws/session/${sessionId}?position_id=${encodeURIComponent(positionId!)}&position_ids=${encodeURIComponent(posIds)}&display_name=${encodeURIComponent(displayName)}`

      try {
        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => {
          setStatus('connected')
          backoffRef.current = BACKOFF_MIN_MS
        }

        ws.onmessage = (ev) => {
          try {
            const msg: WSMessage = JSON.parse(ev.data)
            dispatch(msg)
          } catch (e) {
            console.warn('WS message parse failed:', e)
          }
        }

        ws.onerror = () => {
          setStatus('error')
        }

        ws.onclose = () => {
          wsRef.current = null
          if (shouldReconnectRef.current) {
            setStatus('reconnecting')
            const delay = backoffRef.current
            backoffRef.current = Math.min(BACKOFF_MAX_MS, backoffRef.current * 2)
            reconnectTimerRef.current = setTimeout(connect, delay)
          } else {
            setStatus('disconnected')
          }
        }
      } catch (e) {
        console.warn('WS connect failed:', e)
        setStatus('error')
        reconnectTimerRef.current = setTimeout(connect, backoffRef.current)
        backoffRef.current = Math.min(BACKOFF_MAX_MS, backoffRef.current * 2)
      }
    }

    connect()

    return () => {
      shouldReconnectRef.current = false
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      if (wsRef.current) {
        try { wsRef.current.close() } catch { /* noop */ }
        wsRef.current = null
      }
      setStatus('disconnected')
    }
  }, [sessionId, positionId, displayName, dispatch])

  const send = useCallback((msg: WSMessage) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg))
      return true
    }
    return false
  }, [])

  const sendEdit = useCallback(
    (parameterId: string, newValue: number | string | boolean, opts?: { rationale?: string; equipmentId?: string; editType?: string }) => {
      return send({
        type: 'parameter_edit',
        parameter_id: parameterId,
        new_value: newValue,
        rationale: opts?.rationale || '',
        equipment_id: opts?.equipmentId,
        edit_type: opts?.editType || 'override',
      })
    },
    [send],
  )

  const requestConvergence = useCallback(() => send({ type: 'request_convergence' }), [send])

  return { status, lastMessage, send, sendEdit, requestConvergence }
}
