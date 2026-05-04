/**
 * RequirementsEditor — suggest-then-approve requirements management.
 *
 * Calls the backend to generate SMART requirements from objectives,
 * shows each with SMART validation status, lets user Accept/Edit/Reject.
 * Validates against WHAT-not-HOW rule. Shows non-compliance resolution
 * options for RED requirements.
 */
import { useState } from 'react'

interface SuggestedReq {
  id: string; text: string; req_type: string; domain: string
  threshold: number; operator: string; unit: string
  verification_method: string; objective_id: string; function_id: string
  rationale: string; status: string
}

interface SMARTResult {
  is_smart: boolean; specific: boolean; measurable: boolean
  achievable: boolean; relevant: boolean; traceable: boolean
  is_how_not_what: boolean; issues: string[]
}

const TYPE_COLORS: Record<string, string> = {
  mission: '#8b5cf6', system: '#3b82f6', subsystem: '#06b6d4', interface: '#10b981',
}

const METHOD_OPTIONS = ['analysis', 'test', 'inspection', 'demonstration']

export function RequirementsEditor({ studyId }: { studyId: string | null }) {
  const [requirements, setRequirements] = useState<SuggestedReq[]>([])
  const [smartResults, setSmartResults] = useState<Record<string, SMARTResult>>({})
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')
  const [editThreshold, setEditThreshold] = useState(0)
  const [editMethod, setEditMethod] = useState('analysis')

  const generateRequirements = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      const res = await fetch(`/api/lifecycle/requirements/generate/${studyId}`)
      if (res.ok) {
        const data = await res.json()
        setRequirements(data.suggestions || [])
        // Validate each
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
    setRequirements(prev => prev.map(r => r.id === id ? { ...r, status } : r))
  }

  const startEdit = (req: SuggestedReq) => {
    setEditingId(req.id)
    setEditText(req.text)
    setEditThreshold(req.threshold)
    setEditMethod(req.verification_method)
  }

  const saveEdit = (id: string) => {
    setRequirements(prev => prev.map(r =>
      r.id === id ? { ...r, text: editText, threshold: editThreshold, verification_method: editMethod, status: 'accepted' } : r
    ))
    const updated = requirements.find(r => r.id === id)
    if (updated) validateReq({ ...updated, text: editText, threshold: editThreshold, verification_method: editMethod })
    setEditingId(null)
  }

  const accepted = requirements.filter(r => r.status === 'accepted')
  const suggested = requirements.filter(r => r.status === 'suggested')
  const rejected = requirements.filter(r => r.status === 'rejected')

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
              onAccept={() => updateStatus(req.id, 'accepted')}
              onReject={() => updateStatus(req.id, 'rejected')}
              onStartEdit={() => startEdit(req)}
              onSaveEdit={() => saveEdit(req.id)}
              onCancelEdit={() => setEditingId(null)}
              onEditText={setEditText} onEditThreshold={setEditThreshold} onEditMethod={setEditMethod}
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
              onStartEdit={() => startEdit(req)}
              onSaveEdit={() => saveEdit(req.id)}
              onCancelEdit={() => setEditingId(null)}
              onEditText={setEditText} onEditThreshold={setEditThreshold} onEditMethod={setEditMethod}
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

function RequirementCard({ req, smart, editing, editText, editThreshold, editMethod,
  onAccept, onReject, onStartEdit, onSaveEdit, onCancelEdit,
  onEditText, onEditThreshold, onEditMethod,
}: {
  req: SuggestedReq; smart?: SMARTResult
  editing: boolean; editText: string; editThreshold: number; editMethod: string
  onAccept?: () => void; onReject?: () => void
  onStartEdit?: () => void; onSaveEdit?: () => void; onCancelEdit?: () => void
  onEditText: (t: string) => void; onEditThreshold: (t: number) => void; onEditMethod: (m: string) => void
}) {
  const typeColor = TYPE_COLORS[req.req_type] || '#6b7280'
  const isHowNotWhat = smart?.is_how_not_what
  const isSmart = smart?.is_smart

  return (
    <div style={{
      padding: '0.6rem 0.75rem', borderRadius: '6px', marginBottom: '0.4rem',
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
          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
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
            <span style={{ flex: 1 }} />
            <button className="btn btn-sm" onClick={onSaveEdit} style={{ fontSize: '0.7rem', background: '#10b981' }}>Save</button>
            <button className="btn btn-sm" onClick={onCancelEdit} style={{ fontSize: '0.7rem', background: '#374151' }}>Cancel</button>
          </div>
        </div>
      ) : (
        <div style={{ fontSize: '0.82rem', marginBottom: '0.2rem' }}>{req.text}</div>
      )}

      {/* Threshold + rationale */}
      {!editing && (
        <div style={{ fontSize: '0.7rem', color: '#6b7280', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          {req.threshold !== 0 && <span>{req.operator} {req.threshold} {req.unit}</span>}
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
