/**
 * OpsSystemsArch — define operations activities and which systems are involved.
 *
 * At the system level, we define types of operations activities
 * and map which systems (space + ground) are involved in each.
 */
import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'

interface OpsActivity {
  id: string
  name: string
  description: string
  phase: string  // LEOP, commissioning, nominal, extended, disposal
  systems_involved: string[]
  staffing: string
  frequency: string
  duration: string
  automated: boolean
}

const DEFAULT_OPS_ACTIVITIES: OpsActivity[] = [
  { id: 'ops-leop', name: 'Launch & Early Orbit Phase', description: 'First contact, deployment verification, initial checkout', phase: 'LEOP', systems_involved: ['Spacecraft', 'Ground Station', 'MCC'], staffing: '24/7 (full team)', frequency: 'Continuous', duration: '3-7 days', automated: false },
  { id: 'ops-commission', name: 'Commissioning', description: 'Subsystem checkout, calibration, first light, performance verification', phase: 'Commissioning', systems_involved: ['Spacecraft', 'Ground Station', 'MCC', 'Data Processing'], staffing: 'Office hours + on-call', frequency: 'Daily', duration: '30-90 days', automated: false },
  { id: 'ops-routine', name: 'Routine Operations', description: 'Nominal data collection, commanding, housekeeping monitoring', phase: 'Nominal', systems_involved: ['Spacecraft', 'Ground Station', 'MCC'], staffing: 'Pass-based or office hours', frequency: 'Per orbit / per day', duration: 'Mission lifetime', automated: true },
  { id: 'ops-downlink', name: 'Data Downlink & Processing', description: 'Payload data reception, processing pipeline execution, QC, distribution', phase: 'Nominal', systems_involved: ['Ground Station', 'Data Processing', 'User Services'], staffing: 'Automated', frequency: 'Per pass', duration: 'Minutes per pass', automated: true },
  { id: 'ops-maint', name: 'Orbit Maintenance', description: 'Station-keeping manoeuvres, collision avoidance, RAAN maintenance', phase: 'Nominal', systems_involved: ['Spacecraft', 'MCC', 'Flight Dynamics'], staffing: 'Planned events', frequency: 'Monthly-yearly', duration: 'Minutes per manoeuvre', automated: false },
  { id: 'ops-anomaly', name: 'Anomaly Response', description: 'Safe mode recovery, fault diagnosis, workaround implementation', phase: 'Nominal', systems_involved: ['Spacecraft', 'MCC', 'All subsystem teams'], staffing: 'On-call team', frequency: 'Unplanned', duration: 'Hours-days', automated: false },
  { id: 'ops-sw-update', name: 'Software Update', description: 'Flight software patches, parameter table uploads, procedure updates', phase: 'Nominal', systems_involved: ['Spacecraft', 'MCC'], staffing: 'Planned event', frequency: 'Quarterly-yearly', duration: 'Hours', automated: false },
  { id: 'ops-disposal', name: 'End-of-Life Disposal', description: 'Passivation, deorbit manoeuvre, final data archive, frequency deregistration', phase: 'Disposal', systems_involved: ['Spacecraft', 'MCC', 'Flight Dynamics'], staffing: 'Dedicated team', frequency: 'Once', duration: 'Days-weeks', automated: false },
]

export function OpsSystemsArch() {
  const storedActivities = useDesignStore(s => s.operationsActivities)
  const persistActivities = useDesignStore(s => s.setOperationsActivities)

  const [activities, setActivitiesLocal] = useState<OpsActivity[]>(
    storedActivities.length > 0
      ? storedActivities.map(sa => ({ description: '', duration: '', automated: false, ...sa } as OpsActivity))
      : DEFAULT_OPS_ACTIVITIES
  )
  const setActivities = (updater: OpsActivity[] | ((prev: OpsActivity[]) => OpsActivity[])) => {
    setActivitiesLocal(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      persistActivities(next)
      return next
    })
  }
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const phaseColors: Record<string, string> = {
    LEOP: '#ef4444', Commissioning: '#f59e0b', Nominal: '#10b981', Extended: '#3b82f6', Disposal: '#6b7280',
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Operations — System Architecture</h2>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Define types of operations activities and which systems are involved in each.
        This drives staffing, procedures, and operations cost estimation.
      </p>

      {/* Phase summary */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {['LEOP', 'Commissioning', 'Nominal', 'Disposal'].map(phase => {
          const count = activities.filter(a => a.phase === phase).length
          return (
            <span key={phase} style={{ padding: '0.2rem 0.5rem', borderRadius: '3px', fontSize: '0.68rem', background: `${phaseColors[phase]}20`, color: phaseColors[phase], border: `1px solid ${phaseColors[phase]}40` }}>
              {phase}: {count} activities
            </span>
          )
        })}
      </div>

      {/* Activity table */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
            <th style={th}>Activity</th>
            <th style={th}>Phase</th>
            <th style={th}>Systems Involved</th>
            <th style={th}>Staffing</th>
            <th style={th}>Frequency</th>
            <th style={thC}>Auto</th>
          </tr>
        </thead>
        <tbody>
          {activities.map(a => (
            <tr key={a.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', cursor: 'pointer' }}
                onClick={() => setExpandedId(expandedId === a.id ? null : a.id)}>
              <td style={td}>
                <div style={{ fontWeight: 500 }}>{a.name}</div>
                {expandedId === a.id && (
                  <div style={{ fontSize: '0.65rem', color: '#9ca3af', marginTop: '0.2rem' }}>{a.description}</div>
                )}
              </td>
              <td style={td}>
                <span style={{ padding: '0.1rem 0.3rem', borderRadius: '3px', fontSize: '0.6rem', background: `${phaseColors[a.phase] || '#6b7280'}20`, color: phaseColors[a.phase] || '#6b7280' }}>{a.phase}</span>
              </td>
              <td style={{ ...td, fontSize: '0.65rem', color: '#9ca3af' }}>{a.systems_involved.join(', ')}</td>
              <td style={{ ...td, fontSize: '0.65rem' }}>
                <input value={a.staffing} onChange={e => { e.stopPropagation(); setActivities(prev => prev.map(aa => aa.id === a.id ? { ...aa, staffing: e.target.value } : aa)) }}
                  onClick={e => e.stopPropagation()}
                  style={{ background: 'transparent', border: 'none', color: '#d1d5db', fontSize: '0.65rem', width: '100%' }} />
              </td>
              <td style={{ ...td, fontSize: '0.65rem', color: '#6b7280' }}>{a.frequency}</td>
              <td style={tdC}>
                <span style={{ color: a.automated ? '#10b981' : '#f59e0b', fontSize: '0.7rem' }}>{a.automated ? '✓' : '—'}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <button onClick={() => setActivities(prev => [...prev, {
        id: `ops-${Date.now()}`, name: 'New Activity', description: '', phase: 'Nominal',
        systems_involved: [], staffing: 'TBD', frequency: 'TBD', duration: 'TBD', automated: false,
      }])} className="btn btn-sm" style={{ marginTop: '0.5rem', fontSize: '0.7rem', background: '#374151' }}>
        + Add Activity
      </button>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
