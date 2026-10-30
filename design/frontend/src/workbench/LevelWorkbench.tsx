/**
 * LevelWorkbench — The primary view.
 *
 * Levels 0-3: BlockDiagram (top) + ActivityPanel tabs (bottom)
 * Level 4: Full-screen V&V panel
 */
import { useState } from 'react'
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

const PANELS: Array<{ id: ActivityPanel; color: string }> = [
  { id: 'blocks', color: '#3b82f6' },
  { id: 'budget', color: '#f59e0b' },
  { id: 'requirements', color: '#8b5cf6' },
  { id: 'functions', color: '#a855f7' },
  { id: 'interfaces', color: '#10b981' },
  { id: 'icd', color: '#14b8a6' },
  { id: 'trace', color: '#06b6d4' },
  { id: 'decide', color: '#f59e0b' },
  { id: 'analyses', color: '#ec4899' },
]

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
  const [panelHeight] = useState(280)

  // Level 4 = V&V — full-screen panel, no diagram
  if (currentLevel === 4) {
    return <VVPanel />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Block diagram — takes remaining space */}
      <div style={{ flex: 1, minHeight: 200 }}>
        <BlockDiagram />
      </div>

      {/* Activity panel tabs + content */}
      <div style={{ height: panelHeight, borderTop: '2px solid var(--border)', display: 'flex', flexDirection: 'column' }}>
        {/* Tab bar */}
        <div style={{
          display: 'flex', gap: '1px', background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border)',
        }}>
          {PANELS.map(p => {
            const active = activePanel === p.id
            return (
              <button
                key={p.id}
                onClick={() => setActivePanel(p.id)}
                style={{
                  padding: '0.35rem 1rem', fontSize: '0.72rem', fontWeight: 600,
                  background: active ? 'var(--bg-primary)' : 'var(--bg-secondary)',
                  color: active ? p.color : 'var(--text-secondary)',
                  border: 'none', cursor: 'pointer',
                  borderBottom: active ? `2px solid ${p.color}` : '2px solid transparent',
                }}
              >
                {t(PANEL_LABELS[p.id] ?? p.id)}
              </button>
            )
          })}
        </div>

        {/* Panel content */}
        <div style={{ flex: 1, overflow: 'auto', background: 'var(--bg-primary)' }}>
          {activePanel === 'blocks' && <BlocksPanel />}
          {activePanel === 'budget' && <BudgetPanel />}
          {activePanel === 'requirements' && <RequirementsPanel />}
          {activePanel === 'functions' && <ErrorBoundary phaseName="Functions"><FunctionTree /></ErrorBoundary>}
          {activePanel === 'interfaces' && <InterfacesPanel />}
          {activePanel === 'icd' && <ErrorBoundary phaseName="ICD"><ICDTable /></ErrorBoundary>}
          {activePanel === 'trace' && <ErrorBoundary phaseName="Traceability"><div style={{ padding: '0.5rem 1rem' }}><TraceabilityTree /></div></ErrorBoundary>}
          {activePanel === 'decide' && <DecisionPanel />}
          {activePanel === 'analyses' && <ErrorBoundary phaseName="Analyses"><AnalysesPanel /></ErrorBoundary>}
        </div>
      </div>
    </div>
  )
}
