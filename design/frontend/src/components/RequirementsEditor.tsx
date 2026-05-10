/**
 * RequirementsEditor — suggest-then-approve requirements management.
 *
 * Calls the backend to generate SMART requirements from objectives,
 * shows each with SMART validation status, lets user Accept/Edit/Reject.
 * Validates against WHAT-not-HOW rule. Shows non-compliance resolution
 * options for RED requirements.
 */
import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'

interface SuggestedReq {
  id: string; text: string; req_type: string; domain: string
  threshold: number; operator: string; unit: string
  verification_method: string; objective_id: string; function_id: string
  rationale: string; status: string
  level: string  // "mission" | "system" | "subsystem"
  parent_id: string | null
}

interface SMARTResult {
  is_smart: boolean; specific: boolean; measurable: boolean
  achievable: boolean; relevant: boolean; traceable: boolean
  is_how_not_what: boolean; issues: string[]
}

const TYPE_COLORS: Record<string, string> = {
  mission: '#8b5cf6', system: '#3b82f6', subsystem: '#06b6d4', interface: '#10b981',
  performance: '#10b981', functional: '#8b5cf6', regulatory: '#f97316', constraint: '#ef4444', process: '#ef4444',
  budget: '#3b82f6',
}

const METHOD_OPTIONS = ['analysis', 'test', 'inspection', 'demonstration']
const REQ_TYPE_OPTIONS = ['mission', 'system', 'subsystem', 'interface', 'performance', 'functional', 'regulatory', 'constraint', 'process', 'budget']

export function RequirementsEditor({ studyId, defaultLevel = 'all' }: { studyId: string | null; defaultLevel?: string }) {
  // Requirements read directly from designStore (persists across tab switches + page refreshes)
  const rawReqs = useDesignStore(s => s.generatedRequirements)
  const requirements: SuggestedReq[] = Array.isArray(rawReqs) ? rawReqs as any : []
  const setRequirements = (reqs: SuggestedReq[] | ((prev: SuggestedReq[]) => SuggestedReq[])) => {
    if (typeof reqs === 'function') {
      const current = Array.isArray(useDesignStore.getState().generatedRequirements) ? useDesignStore.getState().generatedRequirements as any : []
      useDesignStore.setState({ generatedRequirements: reqs(current) as any })
    } else {
      useDesignStore.setState({ generatedRequirements: reqs as any })
    }
  }
  const [smartResults, setSmartResults] = useState<Record<string, SMARTResult>>({})
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')
  const [editThreshold, setEditThreshold] = useState(0)
  const [editMethod, setEditMethod] = useState('analysis')
  const [editFunctionId, setEditFunctionId] = useState('')
  const [editReqType, setEditReqType] = useState('system')
  const functionsList = useDesignStore(s => s.functionsList)

  const generateRequirements = async () => {
    setLoading(true)
    try {
      // Try study-based generation first, fall back to POST with local data
      let data: any = null
      if (studyId) {
        const res = await fetch(`/api/lifecycle/requirements/generate/${studyId}`)
        if (res.ok) data = await res.json()
      }
      // Fallback: POST objectives and requirements context directly
      if (!data) {
        const { missionNeed, requirements: reqs } = useDesignStore.getState()
        const res = await fetch('/api/lifecycle/requirements/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            objectives: missionNeed?.objectives || [],
            mission_type: reqs?.mission_type || 'earth_observation',
            spacecraft_class: reqs?.spacecraft_class || 'nano',
            orbit: reqs?.orbit || {},
            payloads: reqs?.payloads || [],
          }),
        })
        if (res.ok) data = await res.json()
      }
      if (data) {
        setRequirements(data.suggestions || [])
        for (const req of data.suggestions || []) {
          validateReq(req)
        }
      }
    } catch {}
    setLoading(false)
  }

  const validateReq = async (req: SuggestedReq) => {
    try {
      const res = await fetch('/api/lifecycle/requirements/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })
      if (res.ok) {
        const result = await res.json()
        setSmartResults(prev => ({ ...prev, [req.id]: result }))
      }
    } catch {}
  }

  const updateStatus = (id: string, status: string) => {
    setRequirements(prev => {
      const updated = prev.map(r => {
        if (r.id !== id) return r
        // On acceptance, assign a proper mission-scoped ID if not already assigned
        if (status === 'accepted' && !r.id.includes('-MIS-') && !r.id.includes('-SYS-') && !r.id.includes('-SUB-')) {
          const level = r.level || r.req_type || 'system'
          const newId = useDesignStore.getState().nextReqId(level)
          return { ...r, status, id: newId, _originalId: r.id }
        }
        return { ...r, status }
      })
      // When accepting a requirement with a threshold, set the budget allocation
      if (status === 'accepted') {
        const req = updated.find(r => r._originalId === id || r.id === id)
        if (req && req.threshold > 0 && req.operator) {
          const allocMap: Record<string, (v: number) => void> = {
            mass: (v) => useDesignStore.setState(s => ({ requirements: { ...s.requirements, target_mass_kg: v } })),
            cost: (v) => useDesignStore.setState(s => ({ requirements: { ...s.requirements, target_cost_meur: v } })),
          }
          const setter = allocMap[req.domain]
          if (setter && req.operator === '<=') {
            setter(req.threshold)
          }
        }

        // SYSTEM-V: When accepting a mission requirement, auto-derive a system-level child
        if (req && (req.level === 'mission' || req.req_type === 'mission')) {
          const childId = useDesignStore.getState().nextReqId('system')
          if (!updated.find(r => r.parent_id === req.id && r.level === 'system')) {
            updated.push({
              ...req,
              id: childId,
              level: 'system',
              req_type: 'system',
              parent_id: req.id,
              status: 'suggested',
              text: req.text.replace('The system shall', 'The space segment shall'),
              rationale: `Derived from mission requirement ${req.id}`,
            })
          }
        }

        // SYSTEM-V: When accepting a system requirement, auto-derive subsystem-level child
        if (req && (req.level === 'system' || req.req_type === 'system')) {
          const subId = useDesignStore.getState().nextReqId('subsystem')
          if (!updated.find(r => r.parent_id === req.id && r.level === 'subsystem')) {
            // Determine which subsystem based on domain
            const domainSubsystem: Record<string, string> = {
              mass: 'structure', power: 'EPS', aocs: 'AOCS', link: 'comms',
              thermal: 'thermal', data: 'OBC', propulsion: 'propulsion',
            }
            const subsys = domainSubsystem[req.domain] || req.domain || 'subsystem'
            updated.push({
              ...req,
              id: subId,
              level: 'subsystem',
              req_type: 'subsystem',
              parent_id: req.id,
              status: 'suggested',
              text: req.text.replace(/The (?:space segment|system) shall/i, `The ${subsys} subsystem shall`),
              rationale: `Derived from system requirement ${req.id}`,
            })
          }
        }
      }
      return updated
    })
  }

  const startEdit = (req: SuggestedReq) => {
    setEditingId(req.id)
    setEditText(req.text)
    setEditThreshold(req.threshold)
    setEditMethod(req.verification_method)
    setEditFunctionId(req.function_id || '')
    setEditReqType(req.req_type || 'system')
  }

  const saveEdit = (id: string) => {
    setRequirements(prev => prev.map(r =>
      r.id === id ? { ...r, text: editText, threshold: editThreshold, verification_method: editMethod, function_id: editFunctionId, req_type: editReqType, status: 'accepted' } : r
    ))
    const updated = requirements.find(r => r.id === id)
    if (updated) validateReq({ ...updated, text: editText, threshold: editThreshold, verification_method: editMethod })
    setEditingId(null)
  }

  const splitRequirement = async (req: SuggestedReq) => {
    try {
      const res = await fetch('/api/lifecycle/requirements/split', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.was_split && data.split.length > 1) {
          // Replace original with split children
          setRequirements(prev => {
            const idx = prev.findIndex(r => r.id === req.id)
            if (idx < 0) return prev
            const newList = [...prev]
            newList.splice(idx, 1, ...data.split.map((s: any) => ({ ...s, status: 'suggested' })))
            return newList
          })
        }
      }
    } catch { /* silent — button just won't work */ }
  }

  const accepted = requirements.filter(r => r.status === 'accepted')
  const suggested = requirements.filter(r => r.status === 'suggested')
  const rejected = requirements.filter(r => r.status === 'rejected')

  const [levelFilter, setLevelFilter] = useState<string>(defaultLevel)
  const LEVELS = ['all', 'mission', 'system', 'subsystem']

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <h2 style={{ margin: 0 }}>Requirements</h2>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {requirements.length > 0 && (
            <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
              {accepted.length} accepted · {suggested.length} pending · {rejected.length} rejected
            </span>
          )}
          <button className="btn btn-sm" onClick={generateRequirements} disabled={loading || !studyId}>
            {loading ? 'Generating...' : requirements.length > 0 ? 'Regenerate' : 'Generate from Objectives'}
          </button>
        </div>
      </div>

      {/* Level filter */}
      {requirements.length > 0 && (
        <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.75rem' }}>
          {LEVELS.map(l => (
            <button key={l} onClick={() => setLevelFilter(l)} style={{
              padding: '0.2rem 0.5rem', fontSize: '0.72rem', borderRadius: '3px', cursor: 'pointer',
              background: levelFilter === l ? (TYPE_COLORS[l] || '#3b82f6') + '22' : 'transparent',
              border: `1px solid ${levelFilter === l ? TYPE_COLORS[l] || '#3b82f6' : '#374151'}`,
              color: levelFilter === l ? TYPE_COLORS[l] || '#3b82f6' : '#6b7280',
              textTransform: 'capitalize',
            }}>{l === 'all' ? 'All Levels' : l}</button>
          ))}
        </div>
      )}

      {/* Architecture-derived requirements */}
      <ArchDerivedRequirements levelFilter={levelFilter} />

      {!studyId && (
        <div style={{ color: '#6b7280', fontSize: '0.85rem', padding: '2rem', textAlign: 'center' }}>
          Create a study first (complete Steps 1-3 and run the design) to generate requirements.
        </div>
      )}

      {requirements.length === 0 && studyId && !loading && (
        <div style={{ color: '#9ca3af', fontSize: '0.85rem', padding: '2rem', textAlign: 'center' }}>
          Click "Generate from Objectives" to create SMART requirements from your mission objectives.
          Each requirement will be suggested for your approval — you can accept, edit, or reject each one.
        </div>
      )}

      {/* Pending approval */}
      {suggested.length > 0 && (
        <>
          <h3 style={{ fontSize: '0.85rem', color: '#f59e0b', marginBottom: '0.5rem' }}>
            Pending Approval ({suggested.length})
          </h3>
          {suggested.map(req => (
            <RequirementCard key={req.id} req={req} smart={smartResults[req.id]}
              editing={editingId === req.id} editText={editText} editThreshold={editThreshold} editMethod={editMethod}
              editFunctionId={editFunctionId} functionsList={functionsList}
              onAccept={() => updateStatus(req.id, 'accepted')}
              onReject={() => updateStatus(req.id, 'rejected')}
              onStartEdit={() => startEdit(req)}
              onSaveEdit={() => saveEdit(req.id)}
              onCancelEdit={() => setEditingId(null)}
              onEditText={setEditText} onEditThreshold={setEditThreshold} onEditMethod={setEditMethod}
              onEditFunctionId={setEditFunctionId} onEditReqType={setEditReqType}
              editReqType={editReqType}
              onSplit={() => splitRequirement(req)}
            />
          ))}
        </>
      )}

      {/* Accepted */}
      {accepted.length > 0 && (
        <>
          <h3 style={{ fontSize: '0.85rem', color: '#10b981', margin: '1rem 0 0.5rem' }}>
            Accepted ({accepted.length})
          </h3>
          {accepted.map(req => (
            <RequirementCard key={req.id} req={req} smart={smartResults[req.id]}
              editing={editingId === req.id} editText={editText} editThreshold={editThreshold} editMethod={editMethod}
              editFunctionId={editFunctionId} editReqType={editReqType} functionsList={functionsList}
              onStartEdit={() => startEdit(req)}
              onSaveEdit={() => saveEdit(req.id)}
              onCancelEdit={() => setEditingId(null)}
              onEditText={setEditText} onEditThreshold={setEditThreshold} onEditMethod={setEditMethod}
              onEditFunctionId={setEditFunctionId} onEditReqType={setEditReqType}
            />
          ))}
        </>
      )}

      {/* Rejected (collapsed) */}
      {rejected.length > 0 && (
        <details style={{ marginTop: '1rem' }}>
          <summary style={{ fontSize: '0.78rem', color: '#6b7280', cursor: 'pointer' }}>
            Rejected ({rejected.length})
          </summary>
          {rejected.map(req => (
            <RequirementCard key={req.id} req={req} smart={smartResults[req.id]}
              editing={false} editText="" editThreshold={0} editMethod=""
              onAccept={() => updateStatus(req.id, 'suggested')}
              onEditText={() => {}} onEditThreshold={() => {}} onEditMethod={() => {}}
            />
          ))}
        </details>
      )}
    </div>
  )
}

function RequirementCard({ req, smart, editing, editText, editThreshold, editMethod, editFunctionId, editReqType, functionsList,
  onAccept, onReject, onStartEdit, onSaveEdit, onCancelEdit,
  onEditText, onEditThreshold, onEditMethod, onEditFunctionId, onEditReqType, onSplit,
}: {
  req: SuggestedReq; smart?: SMARTResult
  editing: boolean; editText: string; editThreshold: number; editMethod: string
  editFunctionId?: string; editReqType?: string; functionsList?: any[]
  onAccept?: () => void; onReject?: () => void
  onStartEdit?: () => void; onSaveEdit?: () => void; onCancelEdit?: () => void
  onEditText: (t: string) => void; onEditThreshold: (t: number) => void; onEditMethod: (m: string) => void
  onEditFunctionId?: (id: string) => void; onEditReqType?: (t: string) => void
  onSplit?: () => void
}) {
  const typeColor = TYPE_COLORS[req.req_type] || '#6b7280'
  const isHowNotWhat = smart?.is_how_not_what
  const isSmart = smart?.is_smart
  const isCompound = /\bshall\b.*\b(and shall|; shall)\b/i.test(req.text) || (req.text.length > 200 && (req.text.match(/\bshall\b/gi) || []).length > 1)

  // SYSTEM-V Break 5: Indentation based on requirement level
  const levelIndent = req.level === 'subsystem' ? 32 : req.level === 'system' ? 16 : 0

  return (
    <div style={{
      padding: '0.6rem 0.75rem', borderRadius: '6px', marginBottom: '0.4rem',
      marginLeft: `${levelIndent}px`,
      background: 'var(--bg-secondary, #1f2937)',
      border: `1px solid ${isHowNotWhat ? '#ef4444' : isSmart ? '#10b981' : 'var(--border, #374151)'}`,
      borderLeft: `3px solid ${typeColor}`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.65rem', fontFamily: 'monospace', color: '#6b7280' }}>{req.id}</span>
        <span style={{ fontSize: '0.6rem', padding: '0.05rem 0.3rem', borderRadius: '3px', background: `${typeColor}22`, color: typeColor, fontWeight: 600 }}>
          {req.req_type}
        </span>
        {req.domain && <span style={{ fontSize: '0.6rem', color: '#6b7280' }}>{req.domain}</span>}

        {/* SMART badge */}
        {smart && (
          <span style={{
            fontSize: '0.58rem', padding: '0.05rem 0.3rem', borderRadius: '3px', fontWeight: 600,
            background: isHowNotWhat ? 'rgba(239,68,68,0.2)' : isSmart ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.2)',
            color: isHowNotWhat ? '#ef4444' : isSmart ? '#10b981' : '#f59e0b',
          }}>
            {isHowNotWhat ? 'HOW not WHAT' : isSmart ? 'SMART' : 'Issues'}
          </span>
        )}

        {req.status === 'accepted' && <span style={{ fontSize: '0.58rem', color: '#10b981' }}>Accepted</span>}
        {req.status === 'rejected' && <span style={{ fontSize: '0.58rem', color: '#ef4444' }}>Rejected</span>}

        <span style={{ flex: 1 }} />
        {req.verification_method && (
          <span style={{ fontSize: '0.6rem', color: '#6b7280' }}>V: {req.verification_method}</span>
        )}
      </div>

      {/* Requirement text */}
      {editing ? (
        <div style={{ marginBottom: '0.3rem' }}>
          <textarea className="input" rows={2} value={editText} onChange={e => onEditText(e.target.value)}
            style={{ width: '100%', fontSize: '0.82rem', resize: 'vertical', marginBottom: '0.3rem' }} />
          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
            {onEditReqType && (
              <label style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Type:
                <select className="select" value={editReqType || 'system'} onChange={e => onEditReqType(e.target.value)}
                  style={{ width: '100px', marginLeft: '0.3rem', fontSize: '0.75rem' }}>
                  {REQ_TYPE_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </label>
            )}
            <label style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Threshold:
              <input className="input" type="number" step="any" value={editThreshold}
                onChange={e => onEditThreshold(Number(e.target.value))}
                style={{ width: '80px', marginLeft: '0.3rem', fontSize: '0.75rem' }} />
            </label>
            <label style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Method:
              <select className="select" value={editMethod} onChange={e => onEditMethod(e.target.value)}
                style={{ width: '120px', marginLeft: '0.3rem', fontSize: '0.75rem' }}>
                {METHOD_OPTIONS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </label>
            {functionsList && functionsList.length > 0 && onEditFunctionId && (
              <label style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Function:
                <select className="select" value={editFunctionId || ''} onChange={e => onEditFunctionId(e.target.value)}
                  style={{ width: '150px', marginLeft: '0.3rem', fontSize: '0.75rem' }}>
                  <option value="">— None —</option>
                  {functionsList.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
                </select>
              </label>
            )}
            <span style={{ flex: 1 }} />
            <button className="btn btn-sm" onClick={onSaveEdit} style={{ fontSize: '0.7rem', background: '#10b981' }}>Save</button>
            <button className="btn btn-sm" onClick={onCancelEdit} style={{ fontSize: '0.7rem', background: '#374151' }}>Cancel</button>
          </div>
        </div>
      ) : (
        <div style={{ fontSize: '0.82rem', marginBottom: '0.2rem' }}>{req.text}</div>
      )}

      {/* Threshold + rationale + linked function */}
      {!editing && (
        <div style={{ fontSize: '0.7rem', color: '#6b7280', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          {req.threshold !== 0 && <span>{req.operator} {req.threshold} {req.unit}</span>}
          {req.function_id && functionsList && (() => {
            const fn = functionsList.find(f => f.id === req.function_id)
            return fn ? <span style={{ color: '#8b5cf6' }}>⤷ {fn.name}</span> : null
          })()}
          {req.rationale && <span style={{ fontStyle: 'italic' }}>{req.rationale}</span>}
        </div>
      )}

      {/* SMART issues */}
      {smart && smart.issues.length > 0 && !editing && (
        <div style={{ marginTop: '0.3rem' }}>
          {smart.issues.map((issue, i) => (
            <div key={i} style={{ fontSize: '0.7rem', color: smart.is_how_not_what ? '#ef4444' : '#f59e0b', marginBottom: '0.1rem' }}>
              {issue}
            </div>
          ))}
        </div>
      )}

      {/* Action buttons */}
      {req.status === 'suggested' && !editing && (
        <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.4rem' }}>
          <button className="btn btn-sm" onClick={onAccept} style={{ fontSize: '0.68rem', background: '#10b981' }}>Accept</button>
          <button className="btn btn-sm" onClick={onStartEdit} style={{ fontSize: '0.68rem', background: '#3b82f6' }}>Edit</button>
          {isCompound && onSplit && (
            <button className="btn btn-sm" onClick={onSplit} style={{ fontSize: '0.68rem', background: '#8b5cf6' }}>Split</button>
          )}
          <button className="btn btn-sm" onClick={onReject} style={{ fontSize: '0.68rem', background: '#ef4444' }}>Reject</button>
        </div>
      )}

      {/* Edit button for accepted reqs */}
      {req.status === 'accepted' && !editing && onStartEdit && (
        <button onClick={onStartEdit}
          style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: '0.68rem', marginTop: '0.2rem' }}>
          Edit
        </button>
      )}
    </div>
  )
}


function ArchDerivedRequirements({ levelFilter }: { levelFilter: string }) {
  const archReqs = useDesignStore(s => s.architectureDerivedReqs)
  if (!archReqs || archReqs.length === 0) return null

  const filtered = levelFilter === 'all' ? archReqs : archReqs.filter(r => r.level === levelFilter)
  if (filtered.length === 0) return null

  return (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#8b5cf6', marginBottom: '0.4rem' }}>
        Architecture-Derived Requirements ({filtered.length})
      </div>
      <p style={{ fontSize: '0.68rem', color: '#6b7280', marginBottom: '0.4rem' }}>
        These requirements were automatically derived from your architecture selections in the Architecture tab.
      </p>
      {filtered.map(req => (
        <div key={req.id} style={{
          display: 'flex', alignItems: 'flex-start', gap: '0.4rem',
          padding: '0.3rem 0.5rem', marginBottom: '0.2rem', borderRadius: '4px',
          background: 'rgba(139,92,246,0.05)', borderLeft: '3px solid #8b5cf6',
        }}>
          <span style={{
            fontSize: '0.6rem', padding: '0.1rem 0.3rem', borderRadius: '3px',
            background: req.level === 'system' ? 'rgba(59,130,246,0.15)' : 'rgba(6,182,212,0.15)',
            color: req.level === 'system' ? '#3b82f6' : '#06b6d4',
            fontWeight: 600, textTransform: 'uppercase', flexShrink: 0,
          }}>{req.level}</span>
          <span style={{ fontFamily: 'monospace', fontSize: '0.65rem', color: '#6b7280', flexShrink: 0 }}>{req.id}</span>
          {(req as any).type && (
            <span style={{
              fontSize: '0.55rem', padding: '0.1rem 0.2rem', borderRadius: '2px', flexShrink: 0,
              background: (req as any).type === 'interface' ? '#f59e0b22' : (req as any).type === 'budget' ? '#3b82f622' : (req as any).type === 'functional' ? '#8b5cf622' : '#10b98122',
              color: (req as any).type === 'interface' ? '#f59e0b' : (req as any).type === 'budget' ? '#3b82f6' : (req as any).type === 'functional' ? '#8b5cf6' : '#10b981',
            }}>{(req as any).type}</span>
          )}
          <span style={{ fontSize: '0.75rem', color: '#d1d5db', flex: 1 }}>{req.text}</span>
          <span style={{ fontSize: '0.6rem', color: '#6b7280', flexShrink: 0 }}>{req.subsystem}</span>
        </div>
      ))}
    </div>
  )
}
