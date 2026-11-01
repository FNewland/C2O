/**
 * OpsSystemsArch — define operations activities and which systems are involved.
 *
 * At the system level, we define types of operations activities
 * and map which systems (space + ground) are involved in each.
 */
import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'

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
    LEOP: 'var(--status-alarm)', Commissioning: 'var(--status-caution)', Nominal: 'var(--status-ok)', Extended: 'var(--interactive)', Disposal: 'var(--text-3)',
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: fs.value, marginBottom: '0.25rem' }}>Operations — System Architecture</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.75rem' }}>
        Define types of operations activities and which systems are involved in each.
        This drives staffing, procedures, and operations cost estimation.
      </p>

      {/* Phase summary */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {['LEOP', 'Commissioning', 'Nominal', 'Disposal'].map(phase => {
          const count = activities.filter(a => a.phase === phase).length
          return (
            <span key={phase} style={{ padding: '0.2rem 0.5rem', borderRadius: '3px', fontSize: fs.label, background: `color-mix(in srgb, ${phaseColors[phase]} 13%, transparent)`, color: phaseColors[phase], border: `1px solid color-mix(in srgb, ${phaseColors[phase]} 25%, transparent)` }}>
              {phase}: {count} activities
            </span>
          )
        })}
      </div>

      {/* Activity table */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
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
            <tr key={a.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)', cursor: 'pointer' }}
                onClick={() => setExpandedId(expandedId === a.id ? null : a.id)}>
              <td style={td}>
                <div style={{ fontWeight: 500 }}>{a.name}</div>
                {expandedId === a.id && (
                  <div style={{ fontSize: fs.label, color: 'var(--text-2)', marginTop: '0.2rem' }}>{a.description}</div>
                )}
              </td>
              <td style={td}>
                <span style={{ padding: '0.1rem 0.3rem', borderRadius: '3px', fontSize: fs.label, background: `color-mix(in srgb, ${phaseColors[a.phase] || 'var(--text-3)'} 13%, transparent)`, color: phaseColors[a.phase] || 'var(--text-3)' }}>{a.phase}</span>
              </td>
              <td style={{ ...td, fontSize: fs.label, color: 'var(--text-2)' }}>{a.systems_involved.join(', ')}</td>
              <td style={{ ...td, fontSize: fs.label }}>
                <input value={a.staffing} onChange={e => { e.stopPropagation(); setActivities(prev => prev.map(aa => aa.id === a.id ? { ...aa, staffing: e.target.value } : aa)) }}
                  onClick={e => e.stopPropagation()}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text)', fontSize: fs.label, width: '100%' }} />
              </td>
              <td style={{ ...td, fontSize: fs.label, color: 'var(--text-3)' }}>{a.frequency}</td>
              <td style={tdC}>
                <span style={{ color: a.automated ? 'var(--status-ok)' : 'var(--status-caution)', fontSize: fs.label }}>{a.automated ? '✓' : '—'}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <button onClick={() => setActivities(prev => [...prev, {
        id: `ops-${Date.now()}`, name: 'New Activity', description: '', phase: 'Nominal',
        systems_involved: [], staffing: 'TBD', frequency: 'TBD', duration: 'TBD', automated: false,
      }])} className="btn btn-sm" style={{ marginTop: '0.5rem', fontSize: fs.label, background: 'var(--line)' }}>
        + Add Activity
      </button>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const thC: React.CSSProperties = { ...th, textAlign: 'center' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
const tdC: React.CSSProperties = { ...td, textAlign: 'center' }
