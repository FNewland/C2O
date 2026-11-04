/**
 * uiStore — UI-only state for the Level Workbench.
 *
 * Level is DERIVED from the element in focus (its product-tree type, workbench/blockLevels.ts),
 * not from the breadcrumb depth — a wizard study has a mission root above the segments:
 *   top / mission        → Level 0 (Mission: viewing segments)
 *   segment              → Level 1 (viewing the segment's systems: spacecraft, stations)
 *   system (spacecraft)  → Level 2 (viewing its subsystems)
 *   subsystem            → Level 3 (viewing its equipment)
 *   Level 4 is the V&V view (goToLevel(4)); drilling never lands there.
 */
import { create } from 'zustand'
import i18n, { getLang, normalizeLang, setLang as setI18nLang, type Lang } from '../i18n'
import { loadBreadcrumb, loadStudyId, saveBreadcrumb, saveStudyId, type KV } from './studySession'
import { crumbIndexForLevel, workbenchLevel, type Crumb } from '../workbench/blockLevels'

function storage(): KV | null {
  try { return window.localStorage } catch { return null }
}
const initialStudy = loadStudyId(storage(), typeof window !== 'undefined' ? window.location.search : '')
const initialCrumbs = loadBreadcrumb(storage(), initialStudy)

export type Level = 0 | 1 | 2 | 3 | 4
export type ActivityPanel = 'blocks' | 'spacecraft' | 'budget' | 'requirements' | 'functions' | 'interfaces' | 'icd' | 'trace' | 'decide' | 'analyses' | 'modes' | 'electrical' | 'data'

interface UIStore {
  studyId: string | null
  setStudyId: (id: string | null) => void

  // Drill-down state — level is derived from breadcrumb length
  focusElementId: string | null
  breadcrumb: Crumb[]

  // Derived: product-tree level of the focus (0-3), or 4 while the V&V view is open
  currentLevel: Level

  drillInto: (elementId: string, elementName: string, elementType?: string | null) => void
  /** Give crumbs saved without an element type their type (reload of an older session). */
  annotateCrumbs: (types: Record<string, string>) => void
  drillUp: (toIndex: number) => void  // -1 = root, 0 = first crumb, etc.
  goToLevel: (level: Level) => void   // Navigate to a level by trimming breadcrumb

  // Activity panel
  activePanel: ActivityPanel
  setActivePanel: (panel: ActivityPanel) => void

  // Analysis
  analysisRunning: boolean
  setAnalysisRunning: (running: boolean) => void

  // User identity
  userName: string
  setUserName: (name: string) => void

  // UI language (i18n packet C0). Source of truth is i18next; this mirrors it
  // so components can subscribe. setLang persists to localStorage 'scdf.lang'
  // and updates <html lang>. Stored design data is never translated.
  lang: Lang
  setLang: (lang: Lang) => void

  // Modals
  showExport: boolean
  setShowExport: (show: boolean) => void
  showGuide: boolean
  setShowGuide: (show: boolean) => void
}

function levelFromBreadcrumb(bc: Crumb[]): Level {
  return workbenchLevel(bc)
}

export const useUIStore = create<UIStore>((set, get) => ({
  // Persisted across reloads (WP0): stores/studySession.ts
  studyId: initialStudy,
  setStudyId: (id) => {
    saveStudyId(storage(), id)
    if (id !== get().studyId) {
      saveBreadcrumb(storage(), id, [])
      set({ studyId: id, focusElementId: null, breadcrumb: [], currentLevel: 0 })
    } else set({ studyId: id })
  },

  focusElementId: initialCrumbs.length ? initialCrumbs[initialCrumbs.length - 1].id : null,
  breadcrumb: initialCrumbs,
  currentLevel: levelFromBreadcrumb(initialCrumbs),

  drillInto: (elementId, elementName, elementType) => {
    const { breadcrumb } = get()
    const newBc = [...breadcrumb, elementType ? { id: elementId, name: elementName, type: elementType } : { id: elementId, name: elementName }]
    set({
      focusElementId: elementId,
      breadcrumb: newBc,
      currentLevel: levelFromBreadcrumb(newBc),
    })
  },

  annotateCrumbs: (types) => {
    const { breadcrumb, currentLevel } = get()
    if (!breadcrumb.some(c => !c.type && types[c.id])) return
    const newBc = breadcrumb.map(c => (!c.type && types[c.id] ? { ...c, type: types[c.id] } : c))
    set({ breadcrumb: newBc, currentLevel: currentLevel === 4 ? 4 : levelFromBreadcrumb(newBc) })
  },

  drillUp: (toIndex) => {
    const { breadcrumb } = get()
    if (toIndex < 0) {
      set({ focusElementId: null, breadcrumb: [], currentLevel: 0 })
    } else {
      const target = breadcrumb[toIndex]
      const newBc = breadcrumb.slice(0, toIndex + 1)
      set({
        focusElementId: target.id,
        breadcrumb: newBc,
        currentLevel: levelFromBreadcrumb(newBc),
      })
    }
  },

  goToLevel: (level) => {
    const { breadcrumb } = get()
    if (level === 4) {
      // V&V is a special view — keep breadcrumb but switch to level 4
      set({ currentLevel: 4 })
    } else {
      // back to the deepest crumb at or above that product-tree level (a mission root is level 0)
      const idx = crumbIndexForLevel(breadcrumb, level)
      if (idx < 0) {
        set({ focusElementId: null, breadcrumb: [], currentLevel: 0 })
      } else {
        const newBc = breadcrumb.slice(0, idx + 1)
        set({ focusElementId: newBc[newBc.length - 1].id, breadcrumb: newBc, currentLevel: levelFromBreadcrumb(newBc) })
      }
    }
  },

  activePanel: 'blocks',
  setActivePanel: (panel) => set({ activePanel: panel }),

  analysisRunning: false,
  setAnalysisRunning: (running) => set({ analysisRunning: running }),

  userName: localStorage.getItem('spacecdf-username') || '',
  setUserName: (name) => { localStorage.setItem('spacecdf-username', name); set({ userName: name }) },

  lang: getLang(),
  setLang: (lang) => { void setI18nLang(lang); set({ lang }) },

  showExport: false,
  setShowExport: (show) => set({ showExport: show }),

  showGuide: false,
  setShowGuide: (show) => set({ showGuide: show }),
}))

// Keep the store in step if anything else calls i18n.changeLanguage().
i18n.on('languageChanged', (lng) => {
  const lang = normalizeLang(lng) ?? 'en'
  if (useUIStore.getState().lang !== lang) useUIStore.setState({ lang })
})

// Keep the drill-down with its study across reloads (WP0).
useUIStore.subscribe((st, prev) => {
  if (st.breadcrumb !== prev.breadcrumb || st.studyId !== prev.studyId) saveBreadcrumb(storage(), st.studyId, st.breadcrumb)
})
