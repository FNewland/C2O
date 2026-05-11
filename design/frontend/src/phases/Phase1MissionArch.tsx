/**
 * Phase 1: Mission Architecture
 *
 * Architecture diagram is the PRIMARY view (top half).
 * ConOps (phases, modes, pipeline) below it.
 * Functions and requirements as separate sub-views.
 * Segment tabs: Space | Ground | Operations
 */
import { useState, useCallback } from 'react'
import { MissionArchitectureEditor } from '../components/MissionArchitectureEditor'
import { ConOpsEditor } from '../components/ConOpsEditor'
import { FunctionTreeView } from '../components/FunctionTreeView'
import { RequirementsEditor } from '../components/RequirementsEditor'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'
import { GroundStationDesigner } from '../components/GroundStationDesigner'
import { ConstellationDesigner } from '../components/ConstellationDesigner'
import type { Segment } from '../types/phases'

type SubView = 'arch_conops' | 'functions' | 'requirements' | 'fleet'

export function Phase1MissionArch() {
  const studyId = useDesignStore(s => s.studyId)
  const requirements = useDesignStore(s => s.requirements)
  const missionOps = useDesignStore(s => s.missionOps)
  const setMissionOps = useDesignStore(s => s.setMissionOps)
  const [segment, setSegment] = useState<Segment>('space')
  const [subView, setSubView] = useState<SubView>('arch_conops')
  const [creating, setCreating] = useState(false)

  const showFleet = (requirements.num_spacecraft || 1) > 1

  const handleCreateStudy = useCallback(async () => {
    setCreating(true)
    try {
      const newStudyId = await useDesignStore.getState().createStudy()
      if (!newStudyId) return
      // Create mission root + standard segments — user can add/remove/rename later
      const ms = useModelStore.getState()
      const missionName = useDesignStore.getState().requirements?.name || 'New Mission'
      const missionId = await ms.createElement(newStudyId, { name: missionName, element_type: 'mission', segment: 'space', diagram_x: 300, diagram_y: 10 } as any)
      if (!missionId) return
      await Promise.all([
        ms.createElement(newStudyId, { name: 'Space Segment', element_type: 'segment', segment: 'space', parent_id: missionId, diagram_x: 100, diagram_y: 100 } as any),
        ms.createElement(newStudyId, { name: 'Ground Segment', element_type: 'segment', segment: 'ground', parent_id: missionId, diagram_x: 300, diagram_y: 100 } as any),
        ms.createElement(newStudyId, { name: 'Launch Segment', element_type: 'segment', segment: 'space', parent_id: missionId, diagram_x: 500, diagram_y: 100 } as any),
        ms.createElement(newStudyId, { name: 'Operations', element_type: 'segment', segment: 'operations', parent_id: missionId, diagram_x: 300, diagram_y: 250 } as any),
      ])
    } finally {
      setCreating(false)
    }
  }, [])

  // Gate: show "Create Study" prompt if no study exists yet
  if (!studyId) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '1.5rem', color: '#d1d5db' }}>
        <h2 style={{ margin: 0, fontSize: '1.3rem', color: '#93c5fd' }}>Define Mission Architecture</h2>
        <p style={{ fontSize: '0.85rem', color: '#9ca3af', maxWidth: 500, textAlign: 'center', lineHeight: 1.6 }}>
          Create a study to start building your mission architecture.
          This will set up the element tree where you define segments, systems, and subsystems.
        </p>
        <button onClick={handleCreateStudy} disabled={creating} style={{
          padding: '0.6rem 2rem', fontSize: '0.9rem', fontWeight: 600, borderRadius: '6px',
          background: '#3b82f6', color: 'white', border: 'none', cursor: creating ? 'wait' : 'pointer',
        }}>
          {creating ? 'Creating...' : 'Create Study & Start'}
        </button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Segment + sub-view bar */}
      <div style={{ display: 'flex', gap: '0.25rem', padding: '0.4rem 1rem', borderBottom: '1px solid var(--border, #374151)', alignItems: 'center', flexWrap: 'wrap' }}>
        {(['space', 'ground', 'operations'] as Segment[]).map(s => (
          <button key={s} onClick={() => setSegment(s)} style={{
            padding: '0.3rem 0.75rem', fontSize: '0.75rem', borderRadius: '4px', cursor: 'pointer',
            background: segment === s ? '#3b82f6' : 'transparent',
            color: segment === s ? 'white' : '#9ca3af',
            border: `1px solid ${segment === s ? '#3b82f6' : '#374151'}`,
            textTransform: 'capitalize',
          }}>{s}</button>
        ))}
        <span style={{ color: '#374151', margin: '0 0.3rem' }}>|</span>
        {([
          { id: 'arch_conops' as SubView, label: 'Architecture & ConOps' },
          { id: 'functions' as SubView, label: 'Functions' },
          { id: 'requirements' as SubView, label: 'Requirements' },
          ...(showFleet ? [{ id: 'fleet' as SubView, label: 'Fleet' }] : []),
        ]).map(v => (
          <button key={v.id} onClick={() => setSubView(v.id)} style={{
            padding: '0.25rem 0.6rem', fontSize: '0.7rem', borderRadius: '3px', cursor: 'pointer',
            background: subView === v.id ? 'rgba(59,130,246,0.15)' : 'transparent',
            color: subView === v.id ? '#93c5fd' : '#6b7280',
            border: 'none',
          }}>{v.label}</button>
        ))}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {segment === 'space' && (
          <>
            {subView === 'arch_conops' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                {/* Architecture diagram — takes most of the space */}
                <div style={{ flex: '1 1 60%', minHeight: 400 }}>
                  <MissionArchitectureEditor />
                </div>
                {/* ConOps (phases, modes, data pipeline) — scrollable below */}
                <div style={{ flex: '0 0 auto', maxHeight: '50%', overflow: 'auto', borderTop: '2px solid var(--border, #374151)' }}>
                  <ConOpsEditor />
                </div>
              </div>
            )}
            {subView === 'functions' && <FunctionTreeView />}
            {subView === 'requirements' && <RequirementsEditor studyId={studyId} defaultLevel="mission" />}
            {subView === 'fleet' && <ConstellationDesigner />}
          </>
        )}
        {segment === 'ground' && (
          <>
            {subView === 'arch_conops' && <GroundStationDesigner />}
            {subView === 'functions' && (
              <div style={{ padding: '1.5rem' }}>
                <h2 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Ground Segment Functions</h2>
                <div className="card">
                  <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
                    Key ground segment functions:
                  </p>
                  <ul style={{ fontSize: '0.75rem', color: '#d1d5db', paddingLeft: '1.2rem', lineHeight: 1.8 }}>
                    <li>Receive spacecraft telemetry and payload data</li>
                    <li>Process and distribute data products to users</li>
                    <li>Generate and uplink telecommands</li>
                    <li>Monitor spacecraft health and manage anomalies</li>
                    <li>Perform orbit determination and predict passes</li>
                    <li>Archive and catalogue all mission data</li>
                    <li>Manage frequency coordination and licensing</li>
                  </ul>
                </div>
              </div>
            )}
            {subView === 'requirements' && (
              <div style={{ padding: '1.5rem' }}>
                <h2 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Ground Segment Requirements</h2>
                <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
                  Ground requirements derived from mission needs: antenna G/T, data processing throughput,
                  contact time per orbit, commanding latency, data product delivery SLA.
                </p>
                <RequirementsEditor studyId={studyId} defaultLevel="mission" />
              </div>
            )}
          </>
        )}
        {segment === 'operations' && (
          <div style={{ padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Operations Concept</h2>
            <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '1rem' }}>
              Define operations: control centre, staffing, LEOP, nominal ops, contingency.
            </p>
            <div className="card" style={{ marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>Mission Control</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.72rem', color: '#9ca3af' }}>Control Centre Location:
                  <input className="input" placeholder="e.g., Darmstadt, Germany" style={{ width: '100%', fontSize: '0.72rem' }}
                    value={missionOps.controlCentre}
                    onChange={e => setMissionOps({ ...missionOps, controlCentre: e.target.value })} />
                </label>
                <label style={{ fontSize: '0.72rem', color: '#9ca3af' }}>Staffing Model:
                  <select className="select" style={{ width: '100%', fontSize: '0.72rem' }}
                    value={missionOps.staffingModel}
                    onChange={e => setMissionOps({ ...missionOps, staffingModel: e.target.value })}>
                    <option value="24_7">24/7 (3 shifts)</option>
                    <option value="office_hours">Office hours only</option>
                    <option value="pass_based">Pass-based (attend for contacts)</option>
                    <option value="autonomous">Autonomous (periodic check)</option>
                  </select>
                </label>
              </div>
            </div>
            {subView === 'requirements' && <RequirementsEditor studyId={studyId} defaultLevel="mission" />}
          </div>
        )}
      </div>
    </div>
  )
}
