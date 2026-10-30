/**
 * Phase 3: Subsystem Design
 *
 * Equipment selection (off-the-shelf or custom), detailed budgets,
 * ground station design, constellation fleet definition.
 * This is where budgets get FILLED with real component data.
 *
 * PRIMARY VIEW: HierarchicalDesigner — starts drilled into a subsystem
 * or segment so users can immediately add components.
 * Specialized budget tools (link, power, data, thermal, etc.) are tabs.
 */
import { useState, useMemo } from 'react'
import { HierarchicalDesigner } from '../components/HierarchicalDesigner'
import { LinkBudgetTool } from '../components/LinkBudgetTool'
import { PointingBudget } from '../components/PointingBudget'
import { DataBudget } from '../components/DataBudget'
import { TimingBudget } from '../components/TimingBudget'
import { CostBreakdown } from '../components/CostBreakdown'
import { DisturbanceTorqueBudget } from '../components/DisturbanceTorqueBudget'
import { ThermalAnalysis } from '../components/ThermalAnalysis'
import { PropulsionAnalysis } from '../components/PropulsionAnalysis'
import { MassPropertiesPanel } from '../components/MassPropertiesPanel'
import { PowerDistribution } from '../components/PowerDistribution'
import { OBCInterfaceDiagram } from '../components/OBCInterfaceDiagram'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'

type SubView = 'designer' | 'link' | 'pointing' | 'power' | 'data' | 'thermal' | 'propulsion' | 'cost' | 'mass'

export function Phase3SubsystemDesign() {
  const studyId = useDesignStore(s => s.studyId)
  const [subView, setSubView] = useState<SubView>('designer')

  const elements = useModelStore(s => s.elements)

  // Find a reasonable starting element — first segment or first system
  const initialElementId = useMemo(() => {
    // Prefer first space segment
    for (const el of elements.values()) {
      if (el.element_type === 'segment' && el.segment === 'space' && !(el as any).deleted_at) {
        return el.id
      }
    }
    // Fallback: any segment
    for (const el of elements.values()) {
      if (el.element_type === 'segment' && !(el as any).deleted_at) {
        return el.id
      }
    }
    return null
  }, [elements])

  const subViews: { key: SubView; label: string }[] = [
    { key: 'designer', label: 'Designer' },
    { key: 'link', label: 'Link Budget' },
    { key: 'pointing', label: 'Pointing' },
    { key: 'power', label: 'Power' },
    { key: 'data', label: 'Data' },
    { key: 'thermal', label: 'Thermal' },
    { key: 'propulsion', label: 'Propulsion' },
    { key: 'cost', label: 'Cost' },
    { key: 'mass', label: 'Mass Properties' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab bar */}
      <div style={{
        display: 'flex', gap: '0.25rem', padding: '0.4rem 1rem',
        borderBottom: '1px solid var(--border, #374151)', flexWrap: 'wrap', alignItems: 'center',
      }}>
        {subViews.map(v => (
          <button key={v.key} onClick={() => setSubView(v.key)} style={{
            padding: '0.25rem 0.55rem', fontSize: '0.7rem', borderRadius: '4px', cursor: 'pointer',
            background: subView === v.key ? 'rgba(16,185,129,0.15)' : 'transparent',
            color: subView === v.key ? '#6ee7b7' : '#6b7280',
            border: `1px solid ${subView === v.key ? 'rgba(16,185,129,0.3)' : 'transparent'}`,
            textTransform: 'capitalize',
          }}>
            {v.label}
          </button>
        ))}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {subView === 'designer' && (
          <HierarchicalDesigner studyId={studyId} initialElementId={initialElementId} />
        )}
        {subView === 'link' && <LinkBudgetTool />}
        {subView === 'pointing' && (
          <div style={{ overflow: 'auto', height: '100%' }}>
            <PointingBudget />
            <DisturbanceTorqueBudget />
          </div>
        )}
        {subView === 'power' && <PowerDistribution />}
        {subView === 'data' && (
          <div style={{ overflow: 'auto', height: '100%' }}>
            <DataBudget />
            <TimingBudget />
            <OBCInterfaceDiagram />
          </div>
        )}
        {subView === 'thermal' && <ThermalAnalysis />}
        {subView === 'propulsion' && <PropulsionAnalysis />}
        {subView === 'cost' && <CostBreakdown studyId={studyId} />}
        {subView === 'mass' && <MassPropertiesPanel />}
      </div>
    </div>
  )
}
