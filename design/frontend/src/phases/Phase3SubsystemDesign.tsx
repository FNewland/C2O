/**
 * Phase 3: Subsystem Design
 *
 * Equipment selection (off-the-shelf or custom), detailed budgets,
 * ground station design, constellation fleet definition.
 * This is where budgets get FILLED with real component data.
 */
import { useState } from 'react'
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
import { EquipmentBrowser } from '../components/EquipmentBrowser'
import { OBCInterfaceDiagram } from '../components/OBCInterfaceDiagram'
import { ModelBlockDiagram } from '../components/ModelBlockDiagram'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'
import type { Segment } from '../types/phases'

type SubView = 'equipment' | 'link' | 'pointing' | 'power' | 'data' | 'thermal' | 'propulsion' | 'cost' | 'mass'

export function Phase3SubsystemDesign() {
  const studyId = useDesignStore(s => s.studyId)
  const [segment, setSegment] = useState<Segment>('space')
  const [subView, setSubView] = useState<SubView>('equipment')

  const modelCreateElement = useModelStore(s => s.createElement)
  const modelElements = useModelStore(s => s.elements)

  const handleEquipmentSelect = async (category: string, component: any) => {
    // Write to designStore for backward compatibility
    const existing = useDesignStore.getState().selectedEquipment
    const key = `${category}:${component.id || component.name}`
    if (!existing.find(e => `${e.category}:${e.componentId}` === key)) {
      useDesignStore.setState({
        selectedEquipment: [...existing, {
          category, componentId: component.id || component.name,
          name: component.name, mass_kg: component.mass_kg || 0,
          power_w: component.power_w || 0, cost_keur: component.cost_keur || 0,
          quantity: 1,
        }],
      })

      // SYSTEM-V: Create component element as child of the subsystem
      if (studyId) {
        // Find the subsystem element that matches this category's domain
        // Includes both space and ground segment categories
        const domainMap: Record<string, string> = {
          // Space segment
          batteries: 'power', solar_cells: 'power', solar_panels: 'power', eps_boards: 'power',
          reaction_wheels: 'aocs', star_trackers: 'aocs', magnetorquers: 'aocs', sun_sensors: 'aocs',
          transponders: 'ttc', antennas: 'ttc',
          obcs: 'obc', gps_receivers: 'obc',
          thrusters: 'propulsion',
          cubesat_structures: 'structure',
          thermal_hardware: 'thermal',
          harnesses: 'structure',
          deployers: 'structure',
          mechanical_hardware: 'structure',
          // Ground segment
          ground_antennas: 'ground_rf', ground_rf: 'ground_rf',
          ground_baseband: 'ground_rf', ground_software: 'ground_ops',
          ground_timing: 'ground_ops',
        }
        const domain = domainMap[category]
        // Determine segment from category
        const isGround = category.startsWith('ground_')
        const elementSegment = isGround ? 'ground' : 'space'

        let parentId: string | undefined
        if (domain) {
          for (const el of modelElements.values()) {
            if (el.element_type === 'subsystem' && el.subsystem_domain === domain && el.segment === elementSegment) {
              parentId = el.id
              break
            }
          }
          // Fallback: if no exact match, try any subsystem with this domain
          if (!parentId) {
            for (const el of modelElements.values()) {
              if (el.element_type === 'subsystem' && el.subsystem_domain === domain) {
                parentId = el.id
                break
              }
            }
          }
          // Last resort for ground: find any ground system element
          if (!parentId && isGround) {
            for (const el of modelElements.values()) {
              if ((el.element_type === 'system' || el.element_type === 'subsystem') && el.segment === 'ground') {
                parentId = el.id
                break
              }
            }
          }
        }

        // If no subsystem found, auto-create one
        if (!parentId && domain && studyId) {
          const DOMAIN_NAMES: Record<string, string> = {
            power: 'EPS', aocs: 'AOCS', ttc: 'TTC', thermal: 'Thermal Control',
            structure: 'Structure', propulsion: 'Propulsion', obc: 'OBC / Data Handling',
            payload: 'Payload', ground_rf: 'Ground RF', ground_ops: 'Ground Operations',
          }
          // Find system parent (Platform for space, any ground system for ground)
          let systemParentId: string | undefined
          for (const el of modelElements.values()) {
            if (el.element_type === 'system' && el.segment === elementSegment) {
              systemParentId = el.id; break
            }
          }
          // If no system, use segment
          if (!systemParentId) {
            for (const el of modelElements.values()) {
              if (el.element_type === 'segment' && el.segment === elementSegment) {
                systemParentId = el.id; break
              }
            }
          }
          // Create the subsystem
          const newSubId = await modelCreateElement(studyId, {
            name: DOMAIN_NAMES[domain] || domain,
            element_type: 'subsystem',
            subsystem_domain: domain,
            segment: elementSegment,
            parent_id: systemParentId || null,
          } as any)
          if (newSubId) parentId = newSubId
        }

        await modelCreateElement(studyId, {
          name: component.name,
          element_type: 'component',
          subsystem_domain: domain || null,
          segment: elementSegment,
          parent_id: parentId || null,
          mass_kg: component.mass_kg || null,
          power_avg_w: component.power_w || null,
          cost_recurring_keur: component.cost_keur || null,
          trl: component.trl || null,
          manufacturer: component.manufacturer || null,
          kb_component_id: component.id || null,
          quantity: 1,
        } as any)
      }

      useDesignStore.getState().markStale('equipment')
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Segment + sub-view bar */}
      <div style={{ display: 'flex', gap: '0.25rem', padding: '0.4rem 1rem', borderBottom: '1px solid var(--border, #374151)', flexWrap: 'wrap', alignItems: 'center' }}>
        {(['space', 'ground', 'operations'] as Segment[]).map(s => (
          <button key={s} onClick={() => setSegment(s)} style={{
            padding: '0.3rem 0.75rem', fontSize: '0.75rem', borderRadius: '4px', cursor: 'pointer',
            background: segment === s ? '#10b981' : 'transparent',
            color: segment === s ? 'white' : '#9ca3af',
            border: `1px solid ${segment === s ? '#10b981' : '#374151'}`,
            textTransform: 'capitalize',
          }}>{s}</button>
        ))}
        <span style={{ color: '#374151', margin: '0 0.3rem' }}>|</span>
        {(segment === 'space'
          ? ['equipment', 'link', 'pointing', 'power', 'data', 'thermal', 'propulsion', 'cost', 'mass'] as SubView[]
          : segment === 'ground'
          ? ['equipment', 'link', 'cost'] as SubView[]
          : ['equipment'] as SubView[]
        ).map(v => (
          <button key={v} onClick={() => setSubView(v)} style={{
            padding: '0.25rem 0.5rem', fontSize: '0.68rem', borderRadius: '3px', cursor: 'pointer',
            background: subView === v ? 'rgba(16,185,129,0.15)' : 'transparent',
            color: subView === v ? '#6ee7b7' : '#6b7280',
            border: 'none', textTransform: 'capitalize',
          }}>{v}</button>
        ))}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {segment === 'space' && (
          <>
            {subView === 'equipment' && <EquipmentBrowser studyId={studyId} onClose={() => setSubView('link')} onSelect={handleEquipmentSelect} mode="inline" segment={segment} />}
            {subView === 'link' && <LinkBudgetTool />}
            {subView === 'pointing' && <><PointingBudget /><DisturbanceTorqueBudget /></>}
            {subView === 'power' && <PowerDistribution />}
            {subView === 'data' && <><DataBudget /><TimingBudget /><OBCInterfaceDiagram /></>}
            {subView === 'thermal' && <ThermalAnalysis />}
            {subView === 'propulsion' && <PropulsionAnalysis />}
            {subView === 'cost' && <CostBreakdown studyId={studyId} />}
            {subView === 'mass' && <MassPropertiesPanel />}
          </>
        )}
        {segment === 'ground' && (
          <>
            {subView === 'equipment' && <EquipmentBrowser studyId={studyId} onClose={() => setSubView('link')} onSelect={handleEquipmentSelect} mode="inline" segment={segment} />}
            {subView !== 'equipment' && (
              <div style={{ padding: '1.5rem' }}>
                <h2 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Ground Segment — Subsystem Design</h2>
                <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
                  Select equipment for each ground subsystem defined at Phase 2.
                  Use the Equipment tab to browse ground antennas, RF equipment, modems, and MCS software.
                </p>
                <div style={{ height: '300px' }}>
                  <ModelBlockDiagram studyId={studyId} segment="ground" />
                </div>
              </div>
            )}
          </>
        )}
        {segment === 'operations' && (
          <div style={{ padding: '2rem', color: '#9ca3af' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Operations Segment — Subsystem Design</h3>
            <p style={{ fontSize: '0.78rem', marginBottom: '1rem' }}>
              Operations equipment and software is defined at the system level in Phase 2 (Operations tab).
              This phase focuses on verifying that operations activities have the necessary ground infrastructure.
            </p>
            <div style={{ fontSize: '0.72rem', color: '#6b7280' }}>
              <p style={{ marginBottom: '0.3rem' }}>Typical operations equipment:</p>
              <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
                <li>Mission Control Software (SCOS-2000, COSMOS) — select in Ground Equipment tab</li>
                <li>Flight Dynamics Software (GMAT) — select in Ground Equipment tab</li>
                <li>Operator Workstations — defined as ground infrastructure</li>
                <li>Network Infrastructure — VPN, dedicated links to ground stations</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
