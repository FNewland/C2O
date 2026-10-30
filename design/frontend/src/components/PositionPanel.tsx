import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useSessionStore } from '../stores/sessionStore'

interface PositionSummary {
  id: string
  name: string
  domain: string
  icon: string
  description: string
  question_count: number
  depends_on: string[]
  feeds_into: string[]
}

interface QuestionStatus {
  question_id: string
  question: string
  priority: string
  status: 'answered' | 'open' | 'warning' | 'not_applicable'
  current_value: string
  assessment: string
}

interface PositionGuidance {
  position_id: string
  position_name: string
  answered_questions: QuestionStatus[]
  open_questions: QuestionStatus[]
  warning_questions: QuestionStatus[]
  active_conflicts: string[]
  owned_parameters: Record<string, any>
  consumed_parameters: Record<string, any>
  recommendations: string[]
  completion_percent: number
}

const STATUS_ICON: Record<string, string> = {
  answered: '✓',
  open: '○',
  warning: '⚠',
  not_applicable: '–',
}

const STATUS_COLOR: Record<string, string> = {
  answered: 'var(--success)',
  open: 'var(--text-secondary)',
  warning: 'var(--warning)',
  not_applicable: 'var(--text-secondary)',
}

const PRIORITY_BADGE: Record<string, { bg: string; color: string }> = {
  must_answer: { bg: 'rgba(239,68,68,0.2)', color: 'var(--danger)' },
  should_answer: { bg: 'rgba(245,158,11,0.2)', color: 'var(--warning)' },
  nice_to_have: { bg: 'rgba(107,114,128,0.2)', color: 'var(--text-secondary)' },
}

function formatValue(val: any): string {
  if (typeof val === 'number') {
    if (Math.abs(val) >= 1000) return val.toFixed(0)
    if (Math.abs(val) >= 1) return val.toFixed(2)
    return val.toFixed(4)
  }
  return String(val)
}

export function PositionPanel() {
  const { result } = useDesignStore()
  const activePositions = useSessionStore(s => s.activePositions)
  const myPositionId = useSessionStore(s => s.positionId)
  const sessionId = useSessionStore(s => s.sessionId)
  const [positions, setPositions] = useState<PositionSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [guidance, setGuidance] = useState<PositionGuidance | null>(null)
  const [loading, setLoading] = useState(false)

  // Load position list
  useEffect(() => {
    fetch('/api/positions')
      .then(r => r.json())
      .then(setPositions)
      .catch(() => setPositions([]))
  }, [])

  // Load guidance when position selected and result available
  useEffect(() => {
    if (!selectedId || !result) {
      setGuidance(null)
      return
    }
    setLoading(true)
    fetch(`/api/positions/${selectedId}/guidance`)
      .then(r => r.json())
      .then(g => { setGuidance(g); setLoading(false) })
      .catch(() => { setGuidance(null); setLoading(false) })
  }, [selectedId, result])

  // Count conflicts per position from design result
  const conflictsForPosition = (posId: string): number => {
    if (!result?.conflicts) return 0
    return result.conflicts.filter(
      (c: any) => c.position_a === posId || c.position_b === posId
    ).length
  }

  if (positions.length === 0) {
    return (
      <div style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
        <p>Loading positions... (ensure backend is running)</p>
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Engineering Positions</h2>
      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
        Select a position to see what questions need answering and which parameters you own.
      </p>

      {/* Position grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0.5rem', marginBottom: '1rem' }}>
        {positions.map(pos => {
          const conflicts = conflictsForPosition(pos.id)
          const isSelected = selectedId === pos.id
          const isOnline = activePositions.includes(pos.id)
          const isMe = myPositionId === pos.id
          return (
            <button
              key={pos.id}
              onClick={() => setSelectedId(isSelected ? null : pos.id)}
              style={{
                background: isSelected ? 'var(--accent)' : 'var(--bg-card)',
                border: `1px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}`,
                borderRadius: '8px',
                padding: '0.6rem',
                cursor: 'pointer',
                textAlign: 'center',
                color: isSelected ? 'white' : 'var(--text-primary)',
                position: 'relative',
                transition: 'all 0.15s',
              }}
            >
              <div style={{ fontSize: '1.4rem', marginBottom: '0.2rem' }}>{pos.icon}</div>
              <div style={{ fontSize: '0.7rem', fontWeight: 600 }}>{pos.name}</div>
              <div style={{ fontSize: '0.6rem', color: isSelected ? 'rgba(255,255,255,0.7)' : 'var(--text-secondary)' }}>
                {pos.question_count} questions
                {isMe && <span style={{ marginLeft: '0.25rem', color: 'var(--accent)', fontWeight: 700 }}>· YOU</span>}
              </div>
              {/* Online presence badge */}
              {isOnline && !isMe && (
                <span title="Someone is editing" style={{
                  position: 'absolute', top: '-4px', left: '-4px',
                  background: 'var(--success, #10b981)', color: 'white',
                  borderRadius: '50%', width: '14px', height: '14px',
                  fontSize: '0.55rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: '0 0 6px rgba(16,185,129,0.6)',
                }}>●</span>
              )}
              {conflicts > 0 && (
                <span style={{
                  position: 'absolute', top: '-4px', right: '-4px',
                  background: 'var(--danger)', color: 'white',
                  borderRadius: '50%', width: '16px', height: '16px',
                  fontSize: '0.6rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {conflicts}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Selected position detail */}
      {selectedId && !result && (
        <div className="card">
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Run a design first to see guidance for this position.
          </p>
        </div>
      )}

      {selectedId && loading && (
        <div className="loading"><div className="spinner" /> Loading guidance...</div>
      )}

      {selectedId && guidance && (() => {
        // canEdit: user is in a session AND selected position is their own (or they're systems_engineer)
        const canEdit = !!sessionId && (selectedId === myPositionId || myPositionId === 'systems_engineer')
        return (
        <>
          {/* Completion bar */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <h3>{guidance.position_name}</h3>
              <span style={{
                color: guidance.completion_percent >= 80 ? 'var(--success)' : guidance.completion_percent >= 50 ? 'var(--warning)' : 'var(--danger)',
                fontWeight: 600,
                fontSize: '0.85rem',
              }}>
                {guidance.completion_percent.toFixed(0)}% complete
              </span>
            </div>
            <div className="budget-bar">
              <div
                className="budget-bar-fill"
                style={{
                  width: `${guidance.completion_percent}%`,
                  background: guidance.completion_percent >= 80 ? 'var(--success)' : guidance.completion_percent >= 50 ? 'var(--warning)' : 'var(--danger)',
                }}
              />
            </div>
          </div>

          {/* Key questions */}
          <div className="card">
            <h3 style={{ marginBottom: '0.5rem' }}>Key Questions</h3>
            {[
              ...guidance.open_questions,
              ...guidance.warning_questions,
              ...guidance.answered_questions,
            ].map(q => {
              const pb = PRIORITY_BADGE[q.priority] || PRIORITY_BADGE.nice_to_have
              return (
                <div key={q.question_id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: '0.5rem',
                  padding: '0.4rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)',
                }}>
                  <span style={{ color: STATUS_COLOR[q.status], fontSize: '0.85rem', flexShrink: 0, marginTop: '0.1rem' }}>
                    {STATUS_ICON[q.status]}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.8rem' }}>{q.question}</div>
                    {q.current_value && (
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                        {q.current_value}
                      </div>
                    )}
                  </div>
                  <span style={{
                    fontSize: '0.55rem', fontWeight: 600, padding: '0.1rem 0.3rem',
                    borderRadius: '3px', background: pb.bg, color: pb.color,
                    textTransform: 'uppercase', flexShrink: 0,
                  }}>
                    {q.priority.replace('_', ' ')}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Owned parameters */}
          {Object.keys(guidance.owned_parameters).length > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: '0.5rem' }}>
                Your Parameters
                {canEdit && (
                  <span style={{ marginLeft: '0.5rem', fontSize: '0.65rem', color: 'var(--accent, #3b82f6)', fontWeight: 400 }}>
                    · Click a value to override
                  </span>
                )}
              </h3>
              {Object.entries(guidance.owned_parameters).map(([pid, val]) => (
                <ParamRow
                  key={pid}
                  paramId={pid}
                  value={val}
                  canEdit={canEdit}
                />
              ))}
            </div>
          )}

          {/* Consumed parameters (inputs from others) */}
          {Object.keys(guidance.consumed_parameters).length > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: '0.5rem' }}>Inputs From Other Positions</h3>
              {Object.entries(guidance.consumed_parameters).map(([pid, val]) => (
                <div className="param-row" key={pid}>
                  <span className="param-name">{pid.replace(/_/g, ' ')}</span>
                  <span className="param-value">{formatValue(val)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Recommendations */}
          {guidance.recommendations.length > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: '0.5rem' }}>Action Items</h3>
              {guidance.recommendations.map((rec, i) => (
                <div key={i} className="warning-item">{rec}</div>
              ))}
            </div>
          )}

          {/* Conflicts involving this position */}
          {result?.conflicts?.filter(
            (c: any) => c.position_a === selectedId || c.position_b === selectedId
          ).map((c: any) => (
            <div key={c.id} className="card" style={{ borderLeft: '4px solid var(--warning)', background: 'rgba(245,158,11,0.05)' }}>
              <h3 style={{ fontSize: '0.8rem' }}>{c.title}</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{c.description}</p>
            </div>
          ))}
        </>
        )
      })()}
    </div>
  )
}

// ── Inline parameter editor row ─────────────────────────────────────────
function ParamRow({
  paramId, value, canEdit,
}: { paramId: string; value: any; canEdit: boolean }) {
  const sendEdit = useSessionStore(s => s.sendEdit)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<string>('')
  const [status, setStatus] = useState<'idle' | 'sent' | 'error'>('idle')

  const label = paramId.split('.').slice(1).join(' ').replace(/_/g, ' ')

  const startEdit = () => {
    if (!canEdit || !sendEdit) return
    setDraft(value === null || value === undefined ? '' : String(value))
    setEditing(true)
    setStatus('idle')
  }

  const commit = () => {
    setEditing(false)
    if (!sendEdit || draft === String(value)) return
    const n = Number(draft)
    const newValue: number | string | boolean = isNaN(n) ? draft : n
    const ok = sendEdit(paramId, newValue, {
      rationale: 'Position override from PositionPanel',
      editType: 'override',
    })
    setStatus(ok ? 'sent' : 'error')
    setTimeout(() => setStatus('idle'), 2500)
  }

  const cancel = () => {
    setEditing(false)
    setStatus('idle')
  }

  return (
    <div className="param-row" style={{ alignItems: 'center' }}>
      <span className="param-name">{label}</span>
      {editing ? (
        <span style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
          <input
            className="input"
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commit}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commit()
              else if (e.key === 'Escape') cancel()
            }}
            style={{ width: '110px', padding: '0.15rem 0.35rem', fontSize: '0.8rem', textAlign: 'right', fontFamily: 'monospace' }}
          />
        </span>
      ) : (
        <span
          className="param-value"
          onClick={startEdit}
          title={canEdit ? 'Click to override' : 'Join a session in this position to edit'}
          style={{
            cursor: canEdit ? 'pointer' : 'default',
            borderBottom: canEdit ? '1px dashed var(--accent, #3b82f6)' : 'none',
            padding: '0 0.25rem',
            color: status === 'sent' ? 'var(--success, #10b981)' : status === 'error' ? 'var(--danger, #ef4444)' : undefined,
          }}
        >
          {formatValue(value)}
          {status === 'sent' && <span style={{ marginLeft: '0.25rem', fontSize: '0.65rem' }}>✓</span>}
          {status === 'error' && <span style={{ marginLeft: '0.25rem', fontSize: '0.65rem' }}>✗</span>}
        </span>
      )}
    </div>
  )
}
