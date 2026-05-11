/**
 * LevelWorkbench — The primary view.
 *
 * Levels 0-3: BlockDiagram (top) + ActivityPanel tabs (bottom)
 * Level 4: Full-screen V&V panel
 */
import { useState } from 'react'
import { useUIStore, type ActivityPanel } from '../stores/uiStore'
import { BlockDiagram } from './BlockDiagram'
import { BlocksPanel } from './BlocksPanel'
import { BudgetPanel } from './BudgetPanel'
import { RequirementsPanel } from './RequirementsPanel'
import { InterfacesPanel } from './InterfacesPanel'
import { DecisionPanel } from './DecisionPanel'
import { VVPanel } from './VVPanel'

const PANELS: Array<{ id: ActivityPanel; label: string; color: string }> = [
  { id: 'blocks', label: 'Blocks', color: '#3b82f6' },
  { id: 'budget', label: 'Budget', color: '#f59e0b' },
  { id: 'requirements', label: 'Requirements', color: '#8b5cf6' },
  { id: 'interfaces', label: 'Interfaces', color: '#10b981' },
  { id: 'decide', label: 'Decide', color: '#f59e0b' },
]

export function LevelWorkbench() {
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
                {p.label}
              </button>
            )
          })}
        </div>

        {/* Panel content */}
        <div style={{ flex: 1, overflow: 'auto', background: 'var(--bg-primary)' }}>
          {activePanel === 'blocks' && <BlocksPanel />}
          {activePanel === 'budget' && <BudgetPanel />}
          {activePanel === 'requirements' && <RequirementsPanel />}
          {activePanel === 'interfaces' && <InterfacesPanel />}
          {activePanel === 'decide' && <DecisionPanel />}
        </div>
      </div>
    </div>
  )
}
