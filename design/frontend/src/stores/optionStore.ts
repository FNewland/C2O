/**
 * optionStore — the active design option per study (SCDF-172).
 *
 * `activeByStudy[studyId]` is the option id the user is working in, or
 * `null` for the baseline. Persisted in localStorage (`spacecdf-options`)
 * so a reload keeps the selection. Consumers append `?option_id=` to every
 * parameter / analysis request through `optionQuery()`; the baseline sends
 * no parameter at all (the API also accepts the baseline option's own id).
 *
 * `uiStore.ts` is owned by the workbench work, so this lives in its own store;
 * SCDF-178 mounts `OptionSwitcher` (which drives this store) in the status bar.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { useUIStore } from './uiStore'

interface OptionStore {
  activeByStudy: Record<string, string | null>
  setActiveOption: (studyId: string, optionId: string | null) => void
  getActiveOption: (studyId: string | null | undefined) => string | null
}

export const useOptionStore = create<OptionStore>()(persist((set, get) => ({
  activeByStudy: {},
  setActiveOption: (studyId, optionId) =>
    set(s => ({ activeByStudy: { ...s.activeByStudy, [studyId]: optionId || null } })),
  getActiveOption: (studyId) => (studyId ? get().activeByStudy[studyId] ?? null : null),
}), { name: 'spacecdf-options', partialize: s => ({ activeByStudy: s.activeByStudy }) }))

/** Active option id for a study (null = baseline). Falls back to the workbench study. */
export function useActiveOptionId(studyId?: string | null): string | null {
  const wbStudy = useUIStore(s => s.studyId)
  const sid = studyId ?? wbStudy
  return useOptionStore(s => (sid ? s.activeByStudy[sid] ?? null : null))
}

/** `?option_id=…` (or `&option_id=…` when the URL already has a query) — empty for the baseline. */
export function optionQuery(optionId: string | null | undefined, hasQuery = false): string {
  if (!optionId) return ''
  return `${hasQuery ? '&' : '?'}option_id=${encodeURIComponent(optionId)}`
}
