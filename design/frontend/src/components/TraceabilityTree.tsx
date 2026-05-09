/**
 * TraceabilityTree — V-model bidirectional traceability view (SCDF-133).
 *
 * Shows the full chain: Need → Objective → Requirement → Function → Design Parameter.
 * Highlights violations and traces them up to the impacted stakeholder need.
 */
import { useDesignStore } from '../stores/designStore'

export function TraceabilityTree() {
  const missionNeed = useDesignStore(s => s.missionNeed)
  const rawReqs = useDesignStore(s => s.generatedRequirements)
  const reqs = Array.isArray(rawReqs) ? rawReqs : []
  const functionsList = useDesignStore(s => s.functionsList)
  const objectives = missionNeed?.objectives || []

  const acceptedReqs = reqs.filter(r => r.status === 'accepted')

  if (objectives.length === 0 && acceptedReqs.length === 0) {
    return (
      <div className="card" style={{ borderLeft: '3px solid #6b7280' }}>
        <h3 style={{ fontSize: '0.85rem', color: '#6b7280' }}>Traceability</h3>
        <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>Define objectives and requirements to see traceability.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>V-Model Traceability</h3>
      <p style={{ fontSize: '0.68rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Need → Objective → Requirement → Function → Design. {objectives.length} objectives, {acceptedReqs.length} requirements, {functionsList.length} functions.
      </p>

      {objectives.map((obj: any, i: number) => {
        const linkedReqs = acceptedReqs.filter(r => r.objective_id === obj.id)
        return (
          <div key={obj.id || i} style={{ marginBottom: '0.5rem', borderLeft: '2px solid #8b5cf6', paddingLeft: '0.5rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#a78bfa' }}>
              OBJ-{i + 1}: {obj.text}
            </div>
            {linkedReqs.length > 0 ? (
              linkedReqs.map(req => {
                const linkedFn = functionsList.find(f => f.id === req.function_id)
                return (
                  <div key={req.id} style={{ marginLeft: '0.75rem', marginTop: '0.15rem', borderLeft: '2px solid #3b82f6', paddingLeft: '0.4rem' }}>
                    <div style={{ fontSize: '0.7rem', color: '#93c5fd' }}>
                      {req.id}: {req.text?.slice(0, 80)}{req.text?.length > 80 ? '...' : ''}
                    </div>
                    {linkedFn && (
                      <div style={{ marginLeft: '0.75rem', fontSize: '0.65rem', color: '#6ee7b7', borderLeft: '2px solid #10b981', paddingLeft: '0.3rem', marginTop: '0.1rem' }}>
                        F: {linkedFn.name} → [{linkedFn.allocated_to?.join(', ')}]
                      </div>
                    )}
                  </div>
                )
              })
            ) : (
              <div style={{ marginLeft: '0.75rem', fontSize: '0.65rem', color: '#6b7280', fontStyle: 'italic' }}>
                No requirements linked to this objective
              </div>
            )}
          </div>
        )
      })}

      {/* Orphan requirements (no objective link) */}
      {(() => {
        const orphans = acceptedReqs.filter(r => !r.objective_id || !objectives.find((o: any) => o.id === r.objective_id))
        if (orphans.length === 0) return null
        return (
          <div style={{ marginTop: '0.5rem', borderTop: '1px solid #374151', paddingTop: '0.4rem' }}>
            <div style={{ fontSize: '0.68rem', color: '#f59e0b', marginBottom: '0.2rem' }}>
              {orphans.length} requirement{orphans.length > 1 ? 's' : ''} not linked to an objective
            </div>
            {orphans.slice(0, 5).map(r => (
              <div key={r.id} style={{ fontSize: '0.65rem', color: '#6b7280', marginLeft: '0.5rem' }}>
                {r.id}: {r.text?.slice(0, 60)}...
              </div>
            ))}
          </div>
        )
      })()}
    </div>
  )
}
