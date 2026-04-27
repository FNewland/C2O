import { create } from 'zustand'
import type { DesignParam } from './designStore'

export interface SessionToast {
  id: string
  actor: string
  parameterId: string
  oldValue: any
  newValue: any
  equipmentId: string | null
  timestamp: string
  isError?: boolean
  errorMessage?: string
}

export interface ConvergenceInfo {
  cascadeRounds: number
  changedParams: string[]
  timeMs: number
  triggeredBy: string
}

export type SendEditFn = (
  parameterId: string,
  newValue: number | string | boolean,
  opts?: { rationale?: string; equipmentId?: string; editType?: string },
) => boolean

interface SessionState {
  sessionId: string | null
  positionId: string | null
  positionIds: string[]           // All claimed positions (multi-role support)
  displayName: string
  activePositions: string[]
  parameters: Record<string, DesignParam>
  pendingEdits: Map<string, { value: any; timestamp: number }>
  toasts: SessionToast[]
  lastConvergence: ConvergenceInfo | null
  sendEdit: SendEditFn | null

  setSession: (sessionId: string, positionId: string, displayName?: string, positionIds?: string[]) => void
  clearSession: () => void
  setStateSnapshot: (params: Record<string, any>, activePositions: string[]) => void
  applyStateUpdate: (updates: Record<string, any>) => void
  applyIncomingEdit: (msg: any) => void
  setPresence: (activePositions: string[], msg: any) => void
  pushToast: (toast: SessionToast) => void
  dismissToast: (id: string) => void
  setConvergenceInfo: (info: ConvergenceInfo) => void
  addOptimisticEdit: (parameterId: string, value: any) => void
  setSendEdit: (fn: SendEditFn | null) => void
}

function toDesignParam(raw: any): DesignParam {
  return {
    value: raw.value,
    unit: raw.unit || '',
    confidence: raw.confidence ?? 0.8,
    margin_percent: raw.margin_percent ?? 0,
    source: raw.source || 'computed',
    domain: raw.domain || '',
  }
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessionId: null,
  positionId: null,
  positionIds: [],
  displayName: '',
  activePositions: [],
  parameters: {},
  pendingEdits: new Map(),
  toasts: [],
  lastConvergence: null,
  sendEdit: null,

  setSendEdit: (fn) => set({ sendEdit: fn }),

  setSession: (sessionId, positionId, displayName = '', positionIds) =>
    set({
      sessionId, positionId, displayName,
      positionIds: positionIds || [positionId],
      parameters: {}, activePositions: [], toasts: [], pendingEdits: new Map(),
    }),

  clearSession: () =>
    set({ sessionId: null, positionId: null, positionIds: [], displayName: '', activePositions: [], parameters: {}, toasts: [], pendingEdits: new Map() }),

  setStateSnapshot: (params, activePositions) => {
    const parameters: Record<string, DesignParam> = {}
    for (const [pid, raw] of Object.entries(params)) {
      parameters[pid] = toDesignParam(raw)
    }
    set({ parameters, activePositions })
  },

  applyStateUpdate: (updates) =>
    set(state => {
      const parameters = { ...state.parameters }
      for (const [pid, raw] of Object.entries(updates)) {
        parameters[pid] = toDesignParam(raw)
      }
      return { parameters }
    }),

  applyIncomingEdit: (msg) => {
    const paramId = msg.parameter_id
    const newValue = msg.new_value
    set(state => {
      const parameters = { ...state.parameters }
      const existing = parameters[paramId]
      parameters[paramId] = {
        value: newValue,
        unit: existing?.unit || '',
        confidence: msg.equipment_id ? 0.95 : 0.9,
        margin_percent: msg.equipment_id ? 5 : 10,
        source: msg.equipment_id ? 'kb_component' : 'position_override',
        domain: existing?.domain || paramId.split('.')[0],
      }
      // Remove optimistic edit if it matches
      const pendingEdits = new Map(state.pendingEdits)
      pendingEdits.delete(paramId)
      return { parameters, pendingEdits }
    })
  },

  setPresence: (activePositions) => set({ activePositions }),

  pushToast: (toast) =>
    set(state => ({ toasts: [...state.toasts.slice(-9), toast] })),

  dismissToast: (id) =>
    set(state => ({ toasts: state.toasts.filter(t => t.id !== id) })),

  setConvergenceInfo: (info) => set({ lastConvergence: info }),

  addOptimisticEdit: (parameterId, value) =>
    set(state => {
      const pendingEdits = new Map(state.pendingEdits)
      pendingEdits.set(parameterId, { value, timestamp: Date.now() })
      return { pendingEdits }
    }),
}))
