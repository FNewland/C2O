/**
 * Phase 2: System Architecture
 *
 * Architecture decisions per subsystem, system block diagrams,
 * interfaces, budget bucket allocation, FMECA awareness.
 * Multi-lens views: mechanical / electrical / RF / thermal / data / mission.
 *
 * PRIMARY VIEW: HierarchicalDesigner — drill-down block diagram editor.
 * Lens views, interface matrix, and budget tools are overlay tabs.
 */
import { useState } from 'react'
import { HierarchicalDesigner } from '../components/HierarchicalDesigner'
import { SystemArchitectureEditor } from '../components/SystemArchitectureEditor'
import { LensView } from '../views/LensView'
import { InterfaceMatrixView } from '../components/InterfaceMatrixView'
import { SystemBudgetEditor } from '../components/SystemBudgetEditor'
import { MissionBudgetSummary } from '../components/MissionBudgetSummary'
import { useDesignStore } from '../stores/designStore'
import { LENS_LABELS, type Segment, type Lens } from '../types/phases'
import { FMECAPanel } from '../components/FMECAPanel'

type SubView = 'designer' | 'presets' | 'interfaces' | 'budgets' | 'fmeca'

export function Phase2SystemArch() {
  const studyId = useDesignStore(s => s.studyId)
  const [subView, setSubView] = useState<SubView>('designer')
  const [lens, setLens] = useState<Lens | null>(null)

  const subViews: { key: SubView; label: string }[] = [
    { key: 'designer', label: 'Designer' },
    { key: 'presets', label: 'Arch Presets' },
    { key: 'interfaces', label: 'Interface Matrix' },
    { key: 'budgets', label: 'Budgets' },
    { key: 'fmeca', label: 'FMECA' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab bar */}
      <div style={{
        display: 'flex', gap: '0.25rem', padding: '0.4rem 1rem',
        borderBottom: '1px solid var(--border, #374151)', alignItems: 'center', flexWrap: 'wrap',
      }}>
        {subViews.map(v => (
          <button key={v.key} onClick={() => { setSubView(v.key); setLens(null) }} style={{
            padding: '0.25rem 0.65rem', fontSize: '0.72rem', borderRadius: '4px', cursor: 'pointer',
            background: subView === v.key && !lens ? 'rgba(6,182,212,0.15)' : 'transparent',
            color: subView === v.key && !lens ? '#67e8f9' : '#9ca3af',
            border: `1px solid ${subView === v.key && !lens ? 'rgba(6,182,212,0.3)' : 'transparent'}`,
          }}>
            {v.label}
          </button>
        ))}
        <span style={{ color: '#374151', margin: '0 0.3rem' }}>|</span>
        {/* Lens selector */}
        <span style={{ fontSize: '0.62rem', color: '#6b7280', marginRight: '0.2rem' }}>Lens:</span>
        {(Object.entries(LENS_LABELS) as [Lens, typeof LENS_LABELS[Lens]][]).map(([l, info]) => (
          <button key={l} onClick={() => setLens(lens === l ? null : l)} style={{
            padding: '0.15rem 0.4rem', fontSize: '0.6rem', borderRadius: '3px', cursor: 'pointer',
            background: lens === l ? `${info.color}20` : 'transparent',
            color: lens === l ? info.color : '#6b7280',
            border: `1px solid ${lens === l ? `${info.color}60` : 'transparent'}`,
          }}>
            {info.name}
          </button>
        ))}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {lens ? (
          <LensView lens={lens} segment={'space' as Segment} />
        ) : subView === 'designer' ? (
          <HierarchicalDesigner studyId={studyId} />
        ) : subView === 'presets' ? (
          <SystemArchitectureEditor />
        ) : subView === 'interfaces' ? (
          <InterfaceMatrixView onNavigate={() => {}} />
        ) : subView === 'budgets' ? (
          <div style={{ overflow: 'auto', height: '100%' }}>
            <MissionBudgetSummary />
            <SystemBudgetEditor />
          </div>
        ) : subView === 'fmeca' ? (
          <FMECAPanel />
        ) : null}
      </div>
    </div>
  )
}
