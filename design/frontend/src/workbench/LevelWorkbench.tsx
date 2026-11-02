/**
 * LevelWorkbench — The primary view.
 *
 * Levels 0-3: BlockDiagram (top) + ActivityPanel tabs (bottom)
 * Level 4: Full-screen V&V panel
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useUIStore, type ActivityPanel } from '../stores/uiStore'
import { BlockDiagram } from './BlockDiagram'
import { BlocksPanel } from './BlocksPanel'
import { BudgetPanel } from './BudgetPanel'
import { RequirementsPanel } from './RequirementsPanel'
import { InterfacesPanel } from './InterfacesPanel'
import { DecisionPanel } from './DecisionPanel'
import { VVPanel } from './VVPanel'
import { FunctionTree } from '../components/FunctionTree'
import { ICDTable } from '../components/ICDTable'
import { TraceabilityTree } from '../components/TraceabilityTree'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { AnalysesPanel } from './AnalysesPanel'

const PANELS: ActivityPanel[] = ['blocks', 'budget', 'requirements', 'functions', 'interfaces', 'icd', 'trace', 'decide', 'analyses']

/** Tabs that are tables or lists: the diagram collapses to a strip so they get the height. */
const TABLE_PANELS = new Set<ActivityPanel>(['budget', 'requirements', 'functions', 'icd', 'trace', 'decide', 'analyses'])

const MIN_PANEL = 160

function storageKey(user: string) { return `scdf.panelHeight.${user || 'anon'}` }
function readHeight(user: string): number {
  try { const v = Number(localStorage.getItem(storageKey(user))); return Number.isFinite(v) && v >= MIN_PANEL ? v : 320 } catch { return 320 }
}

// English text is the i18n key: tab labels, translated at render time with t().
// Also the ErrorBoundary phaseName values below ('Functions', 'ICD', …).
const PANEL_LABELS: Partial<Record<ActivityPanel, string>> = {
  blocks: 'Blocks',
  budget: 'Budget',
  requirements: 'Requirements',
  functions: 'Functions',
  interfaces: 'Interfaces',
  icd: 'ICD',
  trace: 'Traceability',
  decide: 'Decide',
  analyses: 'Analyses',
}

export function LevelWorkbench() {
  const { t } = useTranslation()
  const activePanel = useUIStore(s => s.activePanel)
  const setActivePanel = useUIStore(s => s.setActivePanel)
  const currentLevel = useUIStore(s => s.currentLevel)
  const userName = useUIStore(s => s.userName)
  const [panelHeight, setPanelHeight] = useState(() => readHeight(userName))
  const [showDiagram, setShowDiagram] = useState<Partial<Record<ActivityPanel, boolean>>>({})
  const rootRef = useRef<HTMLDivElement>(null)
  const tabsRef = useRef<HTMLDivElement>(null)

  // Persist per user (the name entered at sign-in).
  useEffect(() => { setPanelHeight(readHeight(userName)) }, [userName])
  const commit = useCallback((h: number) => {
    try { localStorage.setItem(storageKey(userName), String(Math.round(h))) } catch { /* private mode */ }
  }, [userName])

  const clamp = useCallback((h: number) => {
    const total = rootRef.current?.clientHeight ?? 800
    return Math.max(MIN_PANEL, Math.min(h, total - 120))
  }, [])

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault()
    const startY = e.clientY, startH = panelHeight
    const el = e.currentTarget
    el.setPointerCapture(e.pointerId)
    let last = startH
    const move = (ev: PointerEvent) => { last = clamp(startH - (ev.clientY - startY)); setPanelHeight(last) }
    const up = () => { el.removeEventListener('pointermove', move); el.removeEventListener('pointerup', up); commit(last) }
    el.addEventListener('pointermove', move)
    el.addEventListener('pointerup', up)
  }
  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const step = e.shiftKey ? 64 : 16
    let h = panelHeight
    if (e.key === 'ArrowUp') h += step
    else if (e.key === 'ArrowDown') h -= step
    else if (e.key === 'Home') h = MIN_PANEL
    else if (e.key === 'End') h = clamp(10_000)
    else return
    e.preventDefault()
    h = clamp(h); setPanelHeight(h); commit(h)
  }

  const onTabKey = (e: React.KeyboardEvent) => {
    const i = PANELS.indexOf(activePanel)
    let j = i
    if (e.key === 'ArrowRight') j = (i + 1) % PANELS.length
    else if (e.key === 'ArrowLeft') j = (i - 1 + PANELS.length) % PANELS.length
    else if (e.key === 'Home') j = 0
    else if (e.key === 'End') j = PANELS.length - 1
    else return
    e.preventDefault()
    setActivePanel(PANELS[j])
    tabsRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[j]?.focus()
  }

  // Level 4 = V&V — full-screen panel, no diagram
  if (currentLevel === 4) {
    return <VVPanel />
  }

  const collapsed = TABLE_PANELS.has(activePanel) && !showDiagram[activePanel]
  const tabLabel = t(PANEL_LABELS[activePanel] ?? activePanel)

  return (
    <div ref={rootRef} className="c2o-wb">
      {!collapsed && (
        <div className="c2o-wb__diagram">
          <BlockDiagram />
          {TABLE_PANELS.has(activePanel) && (
            <button type="button" className="c2o-btn c2o-btn--sm c2o-wb__hide"
              onClick={() => setShowDiagram(m => ({ ...m, [activePanel]: false }))}>
              {t('Hide diagram')}
            </button>
          )}
        </div>
      )}

      {!collapsed && (
        <div
          role="separator"
          aria-orientation="horizontal"
          aria-label={t('Resize activity panel')}
          aria-valuemin={MIN_PANEL}
          aria-valuenow={Math.round(panelHeight)}
          tabIndex={0}
          className="c2o-splitter"
          onPointerDown={onPointerDown}
          onKeyDown={onKeyDown}
          onDoubleClick={() => { const h = clamp(320); setPanelHeight(h); commit(h) }}
          title={t('Drag to resize. Double-click to reset.')}
        />
      )}

      {/* Activity panel tabs + content */}
      <div className="c2o-wb__activity" style={{ height: collapsed ? undefined : panelHeight, flex: collapsed ? 1 : 'none' }}>
        <div className="c2o-wb__tabbar">
        <div ref={tabsRef} role="tablist" aria-label={t('Activity panel')} className="c2o-tabs c2o-wb__tabs"
          onKeyDown={onTabKey}>
          {PANELS.map(id => {
            const active = activePanel === id
            return (
              <button
                key={id}
                type="button"
                role="tab"
                id={`act-tab-${id}`}
                aria-selected={active}
                aria-controls="act-panel"
                tabIndex={active ? 0 : -1}
                className="c2o-tab"
                onClick={() => setActivePanel(id)}
              >
                {t(PANEL_LABELS[id] ?? id)}
              </button>
            )
          })}
        </div>
        {collapsed && (
          <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet c2o-wb__show"
            title={t('Block diagram collapsed while {{tab}} is open.', { tab: tabLabel })}
            onClick={() => setShowDiagram(m => ({ ...m, [activePanel]: true }))}>
            {t('Show diagram')}
          </button>
        )}
        </div>

        {/* Panel content */}
        <div id="act-panel" role="tabpanel" aria-labelledby={`act-tab-${activePanel}`} className="c2o-wb__panel">
          {activePanel === 'blocks' && <BlocksPanel />}
          {activePanel === 'budget' && <BudgetPanel />}
          {activePanel === 'requirements' && <RequirementsPanel />}
          {activePanel === 'functions' && <ErrorBoundary phaseName="Functions"><FunctionTree /></ErrorBoundary>}
          {activePanel === 'interfaces' && <InterfacesPanel />}
          {activePanel === 'icd' && <ErrorBoundary phaseName="ICD"><ICDTable /></ErrorBoundary>}
          {activePanel === 'trace' && <ErrorBoundary phaseName="Traceability"><div className="c2o-pane"><TraceabilityTree /></div></ErrorBoundary>}
          {activePanel === 'decide' && <DecisionPanel />}
          {activePanel === 'analyses' && <ErrorBoundary phaseName="Analyses"><AnalysesPanel /></ErrorBoundary>}
        </div>
      </div>
    </div>
  )
}
