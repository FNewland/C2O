/**
 * Logbook UI state: panel open/tab, "Log this" prefill, the context pieces
 * other screens report (wizard step, review gate), and the end-of-session
 * prompt. Server data comes from react-query (api.ts), not from here.
 */
import { create } from 'zustand'
import type { Context, EntryKind } from './api'

export type PanelTab = 'entries' | 'worksheets'
export type EndReason = 'button' | 'gate' | 'leave'

export interface Prefill {
  kind: EntryKind
  /** Extra context for this entry, e.g. { decision: 'Link EPS → OBC (Power)' }. */
  context: Context
  nonce: number
}

interface LogbookUI {
  open: boolean
  tab: PanelTab
  prefill: Prefill | null
  wizardStep: string | null
  gate: string | null
  endSession: { reason: EndReason; gate?: string | null } | null

  setOpen: (open: boolean) => void
  toggle: () => void
  setTab: (tab: PanelTab) => void
  /** "Log this": open the panel on the entry box with the context prefilled. Never blocks. */
  logThis: (context: Context, kind?: EntryKind) => void
  setWizardStep: (step: string | null) => void
  setGate: (gate: string | null) => void
  requestEndSession: (reason: EndReason, gate?: string | null) => void
  closeEndSession: () => void
}

let nonce = 0

export const useLogbookUI = create<LogbookUI>((set) => ({
  open: false,
  tab: 'entries',
  prefill: null,
  wizardStep: null,
  gate: null,
  endSession: null,

  setOpen: (open) => set({ open }),
  toggle: () => set(s => ({ open: !s.open })),
  setTab: (tab) => set({ tab }),
  logThis: (context, kind = 'decision') => set({ open: true, tab: 'entries', prefill: { kind, context, nonce: ++nonce } }),
  setWizardStep: (wizardStep) => set({ wizardStep }),
  setGate: (gate) => set({ gate }),
  requestEndSession: (reason, gate = null) => set({ endSession: { reason, gate } }),
  closeEndSession: () => set({ endSession: null }),
}))
