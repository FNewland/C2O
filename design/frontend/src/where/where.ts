/**
 * "Where in SpaceCDF" links (Nov 2026 worksheet/screen audit).
 *
 * A worksheet question or a catalogue decision names the places that answer it
 * (configs/worksheets/where_map.yaml → the logbook API → `where: WhereTarget[]`).
 * goWhere() switches the workbench there: Mission Definition step, level, activity
 * tab, the section inside the tab (panels listen with useWhereSection), a V&V
 * section or a toolbar dialog, then scrolls to and briefly highlights the anchor.
 * The logbook stays open beside it.
 */
import { useEffect } from 'react'
import type { TFunction } from 'i18next'
import { create } from 'zustand'
import { useUIStore, type ActivityPanel, type Level } from '../stores/uiStore'
import { useLogbookUI } from '../logbook/store'
import { pathToLevel, type El } from './path'

export interface WhereTarget {
  id: string
  label: string
  tab?: ActivityPanel
  level?: 0 | 1 | 2 | 3
  /** subsystem domain to open at level 3 (power, aocs, ttc, …) */
  domain?: string
  /** section inside the tab: a sub-tab, an analysis card, a Decide tool */
  section?: string
  /** V&V section (level 4) */
  vv?: string
  dialog?: 'export' | 'guide'
  /** Mission Definition step (only before the study exists) */
  wizard?: string
  /** data-where value to scroll to and highlight */
  anchor?: string
}

export type WhereResult = 'ok' | 'study-open' | 'no-study' | 'later-step' | 'not-found'

interface Pending { panel: string; section: string; n: number; at: number }

interface WhereState {
  pending: Pending | null
  wizard: { step: string; n: number } | null
  request: (panel: string, section: string) => void
  requestWizard: (step: string) => void
}

let seq = 0
export const useWhereStore = create<WhereState>(set => ({
  pending: null,
  wizard: null,
  request: (panel, section) => set({ pending: { panel, section, n: ++seq, at: Date.now() } }),
  requestWizard: (step) => set({ wizard: { step, n: ++seq } }),
}))

/** How long a request waits for its panel to mount (a level change fetches first). */
const PENDING_MS = 5000

/**
 * A panel with sections: `apply(section)` runs when a where-link asks for one of them,
 * also when the panel mounts just after the request. The request is then consumed, so
 * opening the tab later by hand does not jump again.
 */
export function useWhereSection(panel: string, apply: (section: string) => void): void {
  const pending = useWhereStore(s => s.pending)
  useEffect(() => {
    if (!pending || pending.panel !== panel) return
    if (Date.now() - pending.at <= PENDING_MS) apply(pending.section)
    // consume after every listener of this commit has seen it
    window.setTimeout(() => {
      if (useWhereStore.getState().pending?.n === pending.n) useWhereStore.setState({ pending: null })
    }, 0)
  }, [pending?.n, panel])  // eslint-disable-line react-hooks/exhaustive-deps
}

export const WIZARD_ORDER = ['home', 'problem', 'stakeholders', 'alternatives', 'architecture']

async function goLevel(level: 0 | 1 | 2 | 3, domain?: string): Promise<boolean> {
  const ui = useUIStore.getState()
  if (!ui.studyId) return false
  if (ui.currentLevel === level && level < 3 && !domain) return true
  let elements: El[] = []
  try {
    const r = await fetch(`/api/studies/${encodeURIComponent(ui.studyId)}/elements`)
    elements = r.ok ? await r.json() : []
  } catch { return false }
  const path = pathToLevel(Array.isArray(elements) ? elements : [], level, domain)
  if (!path) return false
  const st = useUIStore.getState()
  const same = st.breadcrumb.length === path.length && st.currentLevel === level
    && path.every((p, i) => st.breadcrumb[i]?.id === p.id)
  if (same) return true
  st.drillUp(-1)
  for (const p of path) useUIStore.getState().drillInto(p.id, p.name, p.element_type ?? null)
  return true
}

/** Scroll to `[data-where=anchor]` once it renders, and highlight it for a moment. */
export function flashAnchor(anchor: string, timeoutMs = 4000): void {
  if (typeof document === 'undefined') return
  const started = Date.now()
  const sel = `[data-where="${anchor.replace(/["\\]/g, '')}"]`
  const tick = () => {
    const el = document.querySelector<HTMLElement>(sel)
    if (el) {
      el.scrollIntoView({ block: 'center', behavior: 'smooth' })
      el.classList.remove('c2o-where-flash')
      void el.offsetWidth  // restart the animation
      el.classList.add('c2o-where-flash')
      window.setTimeout(() => el.classList.remove('c2o-where-flash'), 2400)
      return
    }
    if (Date.now() - started < timeoutMs) window.setTimeout(tick, 150)
  }
  window.setTimeout(tick, 60)
}

export async function goWhere(t: WhereTarget): Promise<WhereResult> {
  const ui = useUIStore.getState()
  if (t.wizard) {
    if (ui.studyId) return 'study-open'
    const cur = useLogbookUI.getState().wizardStep ?? 'home'
    const want = WIZARD_ORDER.indexOf(t.wizard)
    const have = WIZARD_ORDER.indexOf(cur)
    if (want > Math.max(have, 1)) return 'later-step'
    useWhereStore.getState().requestWizard(t.wizard)
    return 'ok'
  }
  if (!ui.studyId) return 'no-study'
  if (t.dialog === 'export') { ui.setShowExport(true); return 'ok' }
  if (t.dialog === 'guide') { ui.setShowGuide(true); return 'ok' }
  if (t.vv) {
    ui.goToLevel(4 as Level)
    useWhereStore.getState().request('vv', t.vv)
    if (t.anchor) flashAnchor(t.anchor)
    return 'ok'
  }
  let found = true
  if (t.level != null) found = await goLevel(t.level, t.domain)
  else if (useUIStore.getState().currentLevel === 4) {
    // leave V&V for the element in focus (as the gate "Fix" buttons do)
    const st = useUIStore.getState()
    st.drillUp(st.breadcrumb.length - 1)
  }
  if (t.tab) useUIStore.getState().setActivePanel(t.tab)
  if (t.tab && t.section) useWhereStore.getState().request(t.tab, t.section)
  const anchor = t.anchor ?? (t.section ? `${t.tab}:${t.section}` : null)
  if (anchor) flashAnchor(anchor)
  return found ? 'ok' : 'not-found'
}

/** Open-textbook reference: "7.2" → "§7.2"; "21" → "ch. 21" */
export function bookRef(ref: string, t: TFunction): string {
  return ref.includes('.') ? `§${ref}` : t('ch. {{n}}', { n: ref })
}
