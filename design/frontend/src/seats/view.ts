/**
 * Seat view hooks (WP9): which activity tabs the active seat works in (the others behind
 * "Show all", read-only) and "sees first" navigation when the active seat changes.
 */
import { useEffect, useMemo, useRef } from 'react'
import { useUIStore, type Level } from '../stores/uiStore'
import { useLogbookUI } from '../logbook'
import { seatDef, useSeatStore, type ActivityTab } from './api'

const enc = encodeURIComponent

/** Tabs a seat works in; the others are behind "Show all", read-only. */
export function useSeatView() {
  const team = useSeatStore(s => s.team)
  const shadow = useSeatStore(s => s.shadow)
  const showAll = useSeatStore(s => s.showAll)
  const catalogue = useSeatStore(s => s.catalogue)
  const enabled = !!team?.enabled
  const active = enabled ? team?.me?.active ?? null : null
  const def = active ? catalogue?.seats.find(s => s.id === active) : undefined
  const instructor = !!team?.me?.instructor
  const held = team?.me?.held ?? []
  const readOnlyAll = !!shadow || (enabled && !instructor && (held.length === 0 || def?.kind === 'observer'))
  const ownTabs: ActivityTab[] | null = enabled && def?.tabs ? def.tabs : null
  return {
    enabled, active, def, showAll, shadow, instructor, held,
    /** null = no filtering */
    ownTabs,
    readOnly(tab: ActivityTab): boolean {
      if (readOnlyAll) return true
      if (def?.kind === 'customer') return tab !== 'requirements'
      return !!ownTabs && !ownTabs.includes(tab)
    },
    visible(tab: ActivityTab): boolean {
      return !ownTabs || showAll || ownTabs.includes(tab)
    },
  }
}

// ─── "sees first" ───────────────────────────────────────────────────────────

const SEES_KEY = 'scdf.seat.seesFirst'
function readSeesFirst(): string { try { return sessionStorage.getItem(SEES_KEY) || '' } catch { return '' } }

/** When the active seat changes, open the seat's first panel (view + tab). */
export function useSeesFirst() {
  const team = useSeatStore(s => s.team)
  const shadow = useSeatStore(s => s.shadow)
  const studyId = useUIStore(s => s.studyId)
  const active = team?.enabled && !shadow ? team.me?.active ?? null : null
  const lastRef = useRef<string>(readSeesFirst())
  const key = useMemo(() => `${studyId}|${active}`, [studyId, active])
  useEffect(() => {
    if (!active || lastRef.current === key) return
    lastRef.current = key
    // Once per seat switch, not on every reload of the tab.
    try { sessionStorage.setItem(SEES_KEY, key) } catch { /* private mode */ }
    const def = seatDef(active)
    // Logbook: decisions open on the active seat's own (catalogue seat ids = seat ids).
    if (def && ['lead', 'systems', 'domain'].includes(def.kind)) useLogbookUI.getState().setSeat(active)
    const sf = def?.sees_first
    if (!sf) return
    const ui = useUIStore.getState()
    ui.setActivePanel(sf.panel)
    if (sf.view === 'vv') { useSeatStore.getState().openVV('gates'); ui.goToLevel(4 as Level); return }
    if (sf.view === 'top') { ui.drillUp(-1); return }
    // spacecraft: open the space system so its subsystems show
    void fetch(`/api/studies/${enc(studyId!)}/elements`).then(r => r.json()).then((els: any[]) => {
      if (!Array.isArray(els)) return
      const byId = new Map(els.map(e => [e.id, e]))
      const sys = els.find(e => e.element_type === 'system' && (e.segment || 'space') === 'space')
      if (!sys) return
      const chain: { id: string; name: string }[] = []
      let cur: any = sys
      while (cur) { chain.unshift({ id: cur.id, name: cur.name }); cur = cur.parent_id ? byId.get(cur.parent_id) : null }
      ui.drillUp(-1)
      for (const c of chain) useUIStore.getState().drillInto(c.id, c.name)
    }).catch(() => { /* stay where we are */ })
  }, [key, active, studyId])
}

