import { useState, useEffect } from 'react'
import { useSessionStore } from '../stores/sessionStore'
import { POSITION_COLOR } from '../constants'
import { fs } from '../theme/tokens'

// Key questions from positions.yaml — hardcoded subset for the UI.
// In production these would be loaded from the /api/positions endpoint.
const KEY_QUESTIONS: { id: string; position: string; question: string; category: string }[] = [
  { id: 'sys-1', position: 'systems_engineer', question: 'Is the total dry mass within the launch-vehicle allocation?', category: 'sizing' },
  { id: 'sys-2', position: 'systems_engineer', question: 'Are all subsystem budgets closing with adequate margin?', category: 'verification' },
  { id: 'sys-3', position: 'systems_engineer', question: 'Are there unresolved cross-domain conflicts?', category: 'trade' },
  { id: 'pwr-1', position: 'power_engineer', question: 'Does the EPS provide positive power margin in all operating modes?', category: 'sizing' },
  { id: 'pwr-2', position: 'power_engineer', question: 'Is the battery sized for worst-case eclipse with adequate DoD margin?', category: 'sizing' },
  { id: 'aocs-1', position: 'aocs_engineer', question: 'Does the AOCS meet the pointing accuracy requirement?', category: 'verification' },
  { id: 'aocs-2', position: 'aocs_engineer', question: 'Is momentum storage sufficient for orbit-period disturbance accumulation?', category: 'sizing' },
  { id: 'therm-1', position: 'thermal_engineer', question: 'Are all components within their operating temperature range?', category: 'verification' },
  { id: 'comms-1', position: 'comms_engineer', question: 'Does the link close with at least 3 dB margin at minimum elevation?', category: 'verification' },
  { id: 'comms-2', position: 'comms_engineer', question: 'Can all payload data be downlinked within the daily contact window?', category: 'sizing' },
  { id: 'prop-1', position: 'propulsion_engineer', question: 'Is the propellant budget sufficient for the full delta-V requirement?', category: 'sizing' },
  { id: 'struct-1', position: 'structures_engineer', question: 'Does the structure survive launch loads with positive margin of safety?', category: 'verification' },
  { id: 'cost-1', position: 'cost_engineer', question: 'Is the total mission cost within the programmatic ceiling?', category: 'verification' },
  { id: 'mission-1', position: 'mission_analyst', question: 'Does the orbit selection satisfy all coverage and revisit requirements?', category: 'sizing' },
  { id: 'payload-1', position: 'payload_lead', question: 'Can the payload achieve the required GSD/sensitivity from this orbit?', category: 'verification' },
  // New positions
  { id: 'comp-1', position: 'compliance_engineer', question: 'Are all frequency allocations properly licensed (amateur/experimental/commercial)?', category: 'verification' },
  { id: 'comp-2', position: 'compliance_engineer', question: 'Is the export control classification complete for all components?', category: 'verification' },
  { id: 'comp-3', position: 'compliance_engineer', question: 'Is the RSSSA filing prepared (if remote sensing)?', category: 'verification' },
  { id: 'comp-4', position: 'compliance_engineer', question: 'Does the end-of-life plan meet current debris mitigation regulations (FCC 5yr / IADC 25yr)?', category: 'compliance' },
  { id: 'user-1', position: 'user_representative', question: 'Does the data product meet end-user needs (format, latency, accuracy)?', category: 'verification' },
  { id: 'user-2', position: 'user_representative', question: 'Is the data delivery mechanism suitable for the user community?', category: 'trade' },
  { id: 'user-3', position: 'user_representative', question: 'Are there accessibility considerations for the mission data?', category: 'trade' },
  { id: 'ops-1', position: 'mission_ops', question: 'Is the ground segment capable of supporting all mission phases?', category: 'verification' },
  { id: 'ops-2', position: 'mission_ops', question: 'Are automated operations procedures defined for nominal and contingency?', category: 'verification' },
  { id: 'ops-3', position: 'mission_ops', question: 'Is the staffing model sustainable for the mission duration?', category: 'sizing' },
  { id: 'gnd-1', position: 'ground_segment', question: 'Are ground station contacts sufficient for commanding and data download?', category: 'sizing' },
  { id: 'gnd-2', position: 'ground_segment', question: 'Is the ground data processing pipeline defined and resourced?', category: 'verification' },
  { id: 'sw-1', position: 'software_engineer', question: 'Is the flight software architecture defined with FDIR modes?', category: 'verification' },
  { id: 'sw-2', position: 'software_engineer', question: 'Are all telecommand/telemetry interfaces documented?', category: 'verification' },
]

interface Answer {
  questionId: string
  positionId: string
  text: string
  confidence: 'high' | 'medium' | 'low'
  timestamp: string
}

export function PositionAnswersPanel() {
  const sessionId = useSessionStore(s => s.sessionId)
  const storePositionIds = useSessionStore(s => s.positionIds)
  const [answers, setAnswers] = useState<Map<string, Answer>>(new Map())
  const [editingId, setEditingId] = useState<string | null>(null)
  const [draftText, setDraftText] = useState('')
  const [draftConf, setDraftConf] = useState<'high' | 'medium' | 'low'>('medium')
  const [soloPositions] = useState<string[]>(['systems_engineer'])

  // In solo mode, user can answer ALL questions; use soloPositions for "my" questions
  const isSoloMode = !sessionId
  const positionIds = isSoloMode ? soloPositions : storePositionIds

  const myQuestions = isSoloMode ? KEY_QUESTIONS : KEY_QUESTIONS.filter(q => positionIds.includes(q.position))
  const otherQuestions = isSoloMode ? [] : KEY_QUESTIONS.filter(q => !positionIds.includes(q.position))

  const startAnswer = (qid: string) => {
    const existing = answers.get(qid)
    setDraftText(existing?.text || '')
    setDraftConf(existing?.confidence || 'medium')
    setEditingId(qid)
  }

  // Load saved answers on mount
  useEffect(() => {
    fetch('/api/positions/answers')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.answers) {
          const map = new Map<string, Answer>()
          for (const a of data.answers) {
            map.set(a.question_id, {
              questionId: a.question_id, positionId: a.position_id,
              text: a.text, confidence: a.confidence, timestamp: a.timestamp,
            })
          }
          setAnswers(map)
        }
      })
      .catch(() => {})
  }, [])

  const submitAnswer = (q: typeof KEY_QUESTIONS[0]) => {
    if (!draftText.trim()) return
    const answer: Answer = {
      questionId: q.id,
      positionId: q.position,
      text: draftText,
      confidence: draftConf,
      timestamp: new Date().toISOString(),
    }
    setAnswers(prev => new Map(prev).set(q.id, answer))
    setEditingId(null)

    // Persist to backend
    fetch('/api/positions/answers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: q.id, position_id: q.position,
        text: draftText, confidence: draftConf, timestamp: answer.timestamp,
      }),
    }).catch(() => {})
  }

  // Detect conflicts using multiple heuristics
  const allAnswered = Array.from(answers.values())
  const tensions: { description: string; positions: string[]; severity: 'high' | 'medium' | 'low'; action: string }[] = []

  // Known cross-domain tension patterns
  const TENSION_PATTERNS = [
    { keywords: ['mass', 'heavy', 'weight', 'overweight'], domain: 'mass', action: 'Review mass budget' },
    { keywords: ['power', 'watt', 'energy', 'deficit'], domain: 'power', action: 'Review power budget' },
    { keywords: ['margin', 'tight', 'insufficient', 'negative'], domain: 'margin', action: 'Review system margins' },
    { keywords: ['pointing', 'jitter', 'accuracy', 'vibration'], domain: 'pointing', action: 'Review AOCS performance' },
    { keywords: ['thermal', 'temperature', 'hot', 'cold', 'radiator'], domain: 'thermal', action: 'Review thermal analysis' },
    { keywords: ['cost', 'budget', 'expensive', 'over budget'], domain: 'cost', action: 'Review cost estimate' },
  ]

  for (let i = 0; i < allAnswered.length; i++) {
    for (let j = i + 1; j < allAnswered.length; j++) {
      const a = allAnswered[i], b = allAnswered[j]
      if (a.positionId === b.positionId) continue

      const aLower = a.text.toLowerCase()
      const bLower = b.text.toLowerCase()

      // Check for low-confidence cross-position concerns
      if (a.confidence !== 'high' && b.confidence !== 'high') {
        for (const pattern of TENSION_PATTERNS) {
          const aHit = pattern.keywords.some(k => aLower.includes(k))
          const bHit = pattern.keywords.some(k => bLower.includes(k))
          if (aHit && bHit) {
            tensions.push({
              description: `${a.positionId.replace(/_/g, ' ')} and ${b.positionId.replace(/_/g, ' ')} both flag ${pattern.domain} concerns`,
              positions: [a.positionId, b.positionId],
              severity: a.confidence === 'low' || b.confidence === 'low' ? 'high' : 'medium',
              action: pattern.action,
            })
          }
        }
      }

      // Check for opposing confidence (one high, one low on related topic)
      if (a.confidence === 'high' && b.confidence === 'low' || a.confidence === 'low' && b.confidence === 'high') {
        for (const pattern of TENSION_PATTERNS) {
          const aHit = pattern.keywords.some(k => aLower.includes(k))
          const bHit = pattern.keywords.some(k => bLower.includes(k))
          if (aHit && bHit) {
            tensions.push({
              description: `Conflicting confidence on ${pattern.domain}: ${a.positionId.replace(/_/g, ' ')} (${a.confidence}) vs ${b.positionId.replace(/_/g, ' ')} (${b.confidence})`,
              positions: [a.positionId, b.positionId],
              severity: 'high',
              action: `Reconcile ${pattern.domain} assessment between positions`,
            })
          }
        }
      }
    }
  }

  // Deduplicate by description
  const seenDescs = new Set<string>()
  const conflicts = tensions.filter(t => { if (seenDescs.has(t.description)) return false; seenDescs.add(t.description); return true })


  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Position Questions & Answers</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '1rem' }}>
        Each engineering position has key questions to answer. Answers are visible to the whole team.
        Conflicting answers surface design tensions that need resolution.
      </p>

      {/* Summary */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', fontSize: fs.label }}>
        <span style={{ color: 'var(--status-ok)' }}>{answers.size} answered</span>
        <span style={{ color: 'var(--text-3)' }}>/</span>
        <span style={{ color: 'var(--text-2)' }}>{KEY_QUESTIONS.length} total</span>
        {conflicts.length > 0 && (
          <span style={{ color: 'var(--status-caution)', marginLeft: '0.5rem' }}>{conflicts.length} tension(s) detected</span>
        )}
      </div>

      {/* Tensions */}
      {conflicts.length > 0 && (
        <div style={{
          padding: '0.5rem 0.75rem', borderRadius: '6px', marginBottom: '1rem',
          background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
        }}>
          <div style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--status-caution)', marginBottom: '0.3rem' }}>
            Design Tensions ({conflicts.length})
          </div>
          {conflicts.map((t, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.2rem 0',
              borderTop: i > 0 ? '1px solid rgba(245,158,11,0.15)' : 'none',
            }}>
              <span style={{
                width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                background: t.severity === 'high' ? 'var(--status-alarm)' : t.severity === 'medium' ? 'var(--status-caution)' : 'var(--interactive)',
              }} />
              <span style={{ fontSize: fs.label, color: 'var(--text)', flex: 1 }}>{t.description}</span>
              <span style={{ fontSize: fs.label, color: 'var(--text-3)', whiteSpace: 'nowrap' }}>{t.action}</span>
            </div>
          ))}
        </div>
      )}

      {/* My questions */}
      {myQuestions.length > 0 && (
        <>
          <h3 style={{ fontSize: fs.value, margin: '0.5rem 0' }}>Your Questions ({positionIds.map(p => p.replace(/_/g, ' ')).join(', ')})</h3>
          {myQuestions.map(q => (
            <QuestionCard key={q.id} q={q} answer={answers.get(q.id)} isMine
              isEditing={editingId === q.id} draftText={draftText} draftConf={draftConf}
              onStartEdit={() => startAnswer(q.id)} onSubmit={() => submitAnswer(q)}
              onChangeText={setDraftText} onChangeConf={setDraftConf} onCancel={() => setEditingId(null)} />
          ))}
        </>
      )}

      {/* Other positions' questions */}
      <h3 style={{ fontSize: fs.value, margin: '0.75rem 0 0.5rem 0' }}>Other Positions</h3>
      {otherQuestions.map(q => (
        <QuestionCard key={q.id} q={q} answer={answers.get(q.id)} isMine={false}
          isEditing={false} draftText="" draftConf="medium"
          onStartEdit={() => {}} onSubmit={() => {}} onChangeText={() => {}} onChangeConf={() => {}} onCancel={() => {}} />
      ))}
    </div>
  )
}

function QuestionCard({ q, answer, isMine, isEditing, draftText, draftConf, onStartEdit, onSubmit, onChangeText, onChangeConf, onCancel }: {
  q: { id: string; position: string; question: string; category: string }
  answer?: Answer
  isMine: boolean
  isEditing: boolean
  draftText: string
  draftConf: 'high' | 'medium' | 'low'
  onStartEdit: () => void
  onSubmit: () => void
  onChangeText: (t: string) => void
  onChangeConf: (c: 'high' | 'medium' | 'low') => void
  onCancel: () => void
}) {
  const color = POSITION_COLOR[q.position] || 'var(--text-3)'
  const confColor = { high: 'var(--status-ok)', medium: 'var(--status-caution)', low: 'var(--status-alarm)' }

  return (
    <div style={{
      padding: '0.5rem 0.75rem', borderRadius: '6px', marginBottom: '0.4rem',
      background: 'var(--bg-secondary, var(--surface-2))', border: '1px solid var(--border, var(--line))',
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.2rem' }}>
        <span style={{ fontSize: fs.label, color, fontWeight: 600, textTransform: 'uppercase' }}>{q.position.replace(/_/g, ' ')}</span>
        <span style={{ fontSize: fs.label, color: 'var(--text-3)', background: 'var(--line)', padding: '0 0.3rem', borderRadius: '3px' }}>{q.category}</span>
      </div>
      <div style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>{q.question}</div>

      {isEditing ? (
        <div style={{ marginTop: '0.3rem' }}>
          <textarea className="input" rows={2} value={draftText} onChange={e => onChangeText(e.target.value)}
            placeholder="Your answer..." autoFocus
            style={{ width: '100%', resize: 'vertical', fontSize: fs.label, marginBottom: '0.3rem' }} />
          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
            <span style={{ fontSize: fs.label, color: 'var(--text-2)' }}>Confidence:</span>
            {(['high', 'medium', 'low'] as const).map(c => (
              <button key={c} onClick={() => onChangeConf(c)} style={{
                fontSize: fs.label, padding: '0.1rem 0.4rem', borderRadius: '3px', cursor: 'pointer',
                background: draftConf === c ? `color-mix(in srgb, ${confColor[c]} 13%, transparent)` : 'transparent',
                border: `1px solid ${draftConf === c ? confColor[c] : 'var(--line)'}`,
                color: draftConf === c ? confColor[c] : 'var(--text-3)',
              }}>{c}</button>
            ))}
            <div style={{ flex: 1 }} />
            <button className="btn btn-sm" onClick={onSubmit} style={{ fontSize: fs.label }}>Submit</button>
            <button onClick={onCancel} style={{ background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer', fontSize: fs.label }}>Cancel</button>
          </div>
        </div>
      ) : answer ? (
        <div style={{ marginTop: '0.2rem', padding: '0.3rem 0.5rem', background: 'var(--bg-primary, var(--surface-1))', borderRadius: '4px' }}>
          <div style={{ fontSize: fs.label }}>{answer.text}</div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.2rem', fontSize: fs.label, color: 'var(--text-3)' }}>
            <span style={{ color: confColor[answer.confidence] }}>Confidence: {answer.confidence}</span>
            <span>{new Date(answer.timestamp).toLocaleTimeString()}</span>
            {isMine && <button onClick={onStartEdit} style={{ background: 'none', border: 'none', color: 'var(--interactive)', cursor: 'pointer', fontSize: fs.label }}>Edit</button>}
          </div>
        </div>
      ) : isMine ? (
        <button onClick={onStartEdit} style={{
          background: 'none', border: '1px dashed var(--line)', borderRadius: '4px',
          padding: '0.3rem 0.5rem', color: 'var(--interactive)', cursor: 'pointer', fontSize: fs.label,
          width: '100%', textAlign: 'left', marginTop: '0.2rem',
        }}>
          Click to answer this question...
        </button>
      ) : (
        <div style={{ fontSize: fs.label, color: 'var(--text-3)', fontStyle: 'italic', marginTop: '0.2rem' }}>
          Not yet answered
        </div>
      )}
    </div>
  )
}
