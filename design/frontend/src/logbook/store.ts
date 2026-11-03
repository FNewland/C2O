/**
 * Logbook UI state: panel open/tab, "Log this" prefill, the context pieces
 * other screens report (wizard step, review gate), and the end-of-session
 * prompt. Server data comes from react-query (api.ts), not from here.
 */
import { create } from 'zustand'
import type { Context, DecisionRecord, EntryKind } from './api'

export type PanelTab = 'entries' | 'decisions' | 'worksheets'

/**
 * A decision record being written: what the tool knew at the point of
 * decision (options shown, the one picked, the numbers) plus the catalogue
 * id. The student adds what the tool cannot know (criteria, rationale, risks).
 */
export interface DecisionDraft extends Partial<Omit<DecisionRecord, 'decision_id'>> {
  decision: string
  /** Extra context saved with the entry (e.g. { element: 'EPS' }). */
  context?: Context
  /** Editing this existing entry instead of adding one. */
  entryId?: string
  /** No capture point in front of the student: ask the server what the study already says. */
  fromStudy?: boolean
  nonce: number
}
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
  draft: DecisionDraft | null
  /** Seat filter in the Decisions tab ('' = all). */
  seat: string

  setOpen: (open: boolean) => void
  toggle: () => void
  setTab: (tab: PanelTab) => void
  /** "Log this": open the panel on the entry box with the context prefilled. Never blocks. */
  logThis: (context: Context, kind?: EntryKind) => void
  setWizardStep: (step: string | null) => void
  setGate: (gate: string | null) => void
  requestEndSession: (reason: EndReason, gate?: string | null) => void
  closeEndSession: () => void
  /** "Record decision": open the panel on the decision record, prefilled. Never blocks the action. */
  recordDecision: (draft: Omit<DecisionDraft, 'nonce'>) => void
  closeDraft: () => void
  setSeat: (seat: string) => void
}

const SEAT_KEY = 'scdf.logbook.seat'
function readSeat(): string {
  try { return localStorage.getItem(SEAT_KEY) || '' } catch { return '' }
}

let nonce = 0

export const useLogbookUI = create<LogbookUI>((set) => ({
  open: false,
  tab: 'entries',
  prefill: null,
  wizardStep: null,
  gate: null,
  endSession: null,
  draft: null,
  seat: readSeat(),

  setOpen: (open) => set({ open }),
  toggle: () => set(s => ({ open: !s.open })),
  setTab: (tab) => set({ tab }),
  logThis: (context, kind = 'decision') => set({ open: true, tab: 'entries', prefill: { kind, context, nonce: ++nonce } }),
  setWizardStep: (wizardStep) => set({ wizardStep }),
  setGate: (gate) => set({ gate }),
  requestEndSession: (reason, gate = null) => set({ endSession: { reason, gate } }),
  closeEndSession: () => set({ endSession: null }),
  recordDecision: (draft) => set({ open: true, tab: 'decisions', draft: { ...draft, nonce: ++nonce } }),
  closeDraft: () => set({ draft: null }),
  setSeat: (seat) => {
    try { if (seat) localStorage.setItem(SEAT_KEY, seat); else localStorage.removeItem(SEAT_KEY) } catch { /* private mode */ }
    set({ seat })
  },
}))
