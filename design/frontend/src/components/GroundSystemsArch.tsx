/**
 * GroundSystemsArch — define ground segment systems at Phase 2.
 *
 * Shows the ground systems that need to be designed:
 * - Ground Station Network (per station: antenna, RF, baseband)
 * - Mission Control Centre (TM/TC, FD, planning, infrastructure)
 * - Data Processing Centre (ingest, L0-L2, QC, archive, distribution)
 * - Network Infrastructure (WAN, VPN, timing)
 *
 * Each system creates elements in the model tree as children of the Ground Segment.
 */
import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'
import { ModelBlockDiagram } from './ModelBlockDiagram'

interface GroundSystem {
  id: string
  name: string
  description: string
  subsystems: string[]
  estimatedCost: string
  selected: boolean
}

const GROUND_SYSTEMS: GroundSystem[] = [
  {
    id: 'gs_network', name: 'Ground Station Network',
    description: 'Antenna systems, RF chains, modems for spacecraft communication',
    subsystems: ['Antenna System', 'RF Chain (TX/RX)', 'Baseband / Modem', 'Tracking Mount', 'Station Infrastructure'],
    estimatedCost: '150-2000 kEUR per station', selected: true,
  },
  {
    id: 'gs_mcc', name: 'Mission Control Centre',
    description: 'Telemetry processing, commanding, flight dynamics, mission planning',
    subsystems: ['TM Processing', 'TC Generation', 'Flight Dynamics', 'Mission Planning', 'Anomaly Management', 'IT Infrastructure'],
    estimatedCost: '200-1000 kEUR', selected: true,
  },
  {
    id: 'gs_dataproc', name: 'Data Processing Centre',
    description: 'Payload data reception, processing pipeline (L0→L1→L2), quality control, archive',
    subsystems: ['Data Ingest', 'L0 Processing', 'L1/L2 Processing', 'Quality Control', 'Archive & Catalogue', 'Distribution Services'],
    estimatedCost: '100-500 kEUR', selected: true,
  },
  {
    id: 'gs_network_infra', name: 'Network Infrastructure',
    description: 'WAN connectivity between stations and MCC, VPN, timing distribution',
    subsystems: ['WAN / Fibre', 'VPN / Security', 'Time Distribution (GPS-DO)', 'Monitoring'],
    estimatedCost: '50-200 kEUR', selected: false,
  },
  {
    id: 'gs_user_services', name: 'User Services',
    description: 'Data portal, API, user accounts, SLA management',
    subsystems: ['Web Portal', 'Data API', 'User Management', 'SLA Monitoring'],
    estimatedCost: '50-300 kEUR', selected: false,
  },
]

export function GroundSystemsArch() {
  const studyId = useDesignStore(s => s.studyId)
  const createElement = useModelStore(s => s.createElement)
  const elements = useModelStore(s => s.elements)
  const [systems, setSystems] = useState(GROUND_SYSTEMS)
  const [createdIds, setCreatedIds] = useState<Set<string>>(new Set())

  // Check which ground systems already exist in the element tree
  useEffect(() => {
    const existing = new Set<string>()
    for (const el of elements.values()) {
      if (el.segment === 'ground' && el.element_type === 'system') {
        existing.add(el.name)
      }
    }
    if (existing.size > 0) {
      setSystems(prev => prev.map(s => ({ ...s, selected: existing.has(s.name) })))
    }
  }, [elements])

  const toggleSystem = async (sysId: string) => {
    setSystems(prev => prev.map(s => s.id === sysId ? { ...s, selected: !s.selected } : s))

    const sys = systems.find(s => s.id === sysId)
    if (!sys || !studyId) return

    if (!sys.selected && !createdIds.has(sysId)) {
      // Create system element in model tree
      // Find ground segment parent
      let groundParentId: string | undefined
      for (const el of elements.values()) {
        if (el.element_type === 'segment' && el.segment === 'ground') {
          groundParentId = el.id
          break
        }
      }

      const systemId = await createElement(studyId, {
        name: sys.name,
        element_type: 'system',
        segment: 'ground',
        parent_id: groundParentId || null,
        description: sys.description,
        cost_recurring_keur: parseInt(sys.estimatedCost) || null,
      } as any)

      if (systemId) {
        // Create subsystem elements
        for (const sub of sys.subsystems) {
          await createElement(studyId, {
            name: sub,
            element_type: 'subsystem',
            segment: 'ground',
            parent_id: systemId,
            subsystem_domain: 'ground',
          } as any)
        }
        setCreatedIds(prev => new Set([...prev, sysId]))
      }
    }
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Ground Segment — System Architecture</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Define which ground systems are needed. Each system will be decomposed into subsystems at Phase 3.
      </p>

      {/* System selection cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
        {systems.map(sys => (
          <div key={sys.id} onClick={() => toggleSystem(sys.id)} style={{
            padding: '0.6rem 0.75rem', borderRadius: '6px', cursor: 'pointer',
            background: sys.selected ? 'rgba(16,185,129,0.08)' : 'var(--bg-secondary, #1f2937)',
            border: `2px solid ${sys.selected ? '#10b981' : '#374151'}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
              <span style={{ width: 16, height: 16, borderRadius: 3, border: `2px solid ${sys.selected ? '#10b981' : '#6b7280'}`, background: sys.selected ? '#10b981' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.6rem', color: 'white' }}>
                {sys.selected ? '✓' : ''}
              </span>
              <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{sys.name}</span>
              <span style={{ flex: 1 }} />
              <span style={{ fontSize: '0.65rem', color: '#6b7280' }}>{sys.estimatedCost}</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.2rem', marginLeft: '1.5rem' }}>
              {sys.description}
            </div>
            <div style={{ fontSize: '0.65rem', color: '#6b7280', marginLeft: '1.5rem' }}>
              Subsystems: {sys.subsystems.join(' · ')}
            </div>
          </div>
        ))}
      </div>

      {/* Block diagram of selected ground systems */}
      <div className="card" style={{ height: '300px' }}>
        <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Ground Segment Block Diagram</h3>
        <div style={{ height: '250px' }}>
          <ModelBlockDiagram studyId={studyId} segment="ground" />
        </div>
      </div>
    </div>
  )
}
