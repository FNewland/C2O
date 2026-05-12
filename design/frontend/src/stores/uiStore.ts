/**
 * uiStore — UI-only state for the Level Workbench.
 *
 * Level is DERIVED from breadcrumb depth:
 *   breadcrumb empty     → Level 0 (Mission: viewing segments)
 *   1 crumb (segment)    → Level 1 (Systems: viewing systems under a segment)
 *   2 crumbs (system)    → Level 2 (Subsystems: viewing subsystems under a system)
 *   3 crumbs (subsystem) → Level 3 (Equipment: viewing components under a subsystem)
 *   4+ crumbs            → Level 4 (V&V)
 */
import { create } from 'zustand'

export type Level = 0 | 1 | 2 | 3 | 4
export type ActivityPanel = 'blocks' | 'budget' | 'requirements' | 'interfaces' | 'decide'

interface UIStore {
  studyId: string | null
  setStudyId: (id: string | null) => void

  // Drill-down state — level is derived from breadcrumb length
  focusElementId: string | null
  breadcrumb: Array<{ id: string; name: string }>

  // Derived: currentLevel = min(breadcrumb.length, 4)
  currentLevel: Level

  drillInto: (elementId: string, elementName: string) => void
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

  // Modals
  showExport: boolean
  setShowExport: (show: boolean) => void
  showGuide: boolean
  setShowGuide: (show: boolean) => void
}

function levelFromBreadcrumb(bc: Array<{ id: string; name: string }>): Level {
  return Math.min(bc.length, 4) as Level
}

export const useUIStore = create<UIStore>((set, get) => ({
  studyId: null,
  setStudyId: (id) => set({ studyId: id }),

  focusElementId: null,
  breadcrumb: [],
  currentLevel: 0,

  drillInto: (elementId, elementName) => {
    const { breadcrumb } = get()
    const newBc = [...breadcrumb, { id: elementId, name: elementName }]
    set({
      focusElementId: elementId,
      breadcrumb: newBc,
      currentLevel: levelFromBreadcrumb(newBc),
    })
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
    } else if (level === 0) {
      set({ focusElementId: null, breadcrumb: [], currentLevel: 0 })
    } else if (level <= breadcrumb.length) {
      const newBc = breadcrumb.slice(0, level)
      set({
        focusElementId: newBc[newBc.length - 1].id,
        breadcrumb: newBc,
        currentLevel: levelFromBreadcrumb(newBc),
      })
    }
  },

  activePanel: 'blocks',
  setActivePanel: (panel) => set({ activePanel: panel }),

  analysisRunning: false,
  setAnalysisRunning: (running) => set({ analysisRunning: running }),

  userName: localStorage.getItem('spacecdf-username') || '',
  setUserName: (name) => { localStorage.setItem('spacecdf-username', name); set({ userName: name }) },

  showExport: false,
  setShowExport: (show) => set({ showExport: show }),

  showGuide: false,
  setShowGuide: (show) => set({ showGuide: show }),
}))
