import { useState } from 'react'
import { useDesignStore, type MissionNeedState } from '../stores/designStore'

interface Props {
  section?: 'need' | 'concept'
  onNext?: () => void
}

const STAKEHOLDER_ROLES = [
  { value: 'sponsor', label: 'Sponsor / Funder' },
  { value: 'user', label: 'End User' },
  { value: 'operator', label: 'Mission Operator' },
  { value: 'science_pi', label: 'Science PI' },
  { value: 'regulator', label: 'Regulator' },
  { value: 'public', label: 'Public / Society' },
  { value: 'partner', label: 'Partner Organisation' },
]

const OBJECTIVE_PRIORITIES = [
  { value: 'primary', label: 'Primary (must achieve)' },
  { value: 'secondary', label: 'Secondary (should achieve)' },
  { value: 'tertiary', label: 'Tertiary (nice to have)' },
  { value: 'constraint', label: 'Constraint (hard boundary)' },
]

const ALTERNATIVE_TYPES = [
  { value: 'space_dedicated', label: 'Dedicated satellite' },
  { value: 'space_hosted', label: 'Hosted payload' },
  { value: 'space_existing', label: 'Existing satellite data (Copernicus, Landsat, commercial)' },
  { value: 'space_constellation', label: 'Constellation' },
  { value: 'aerial_drone', label: 'Drone / UAV' },
  { value: 'aerial_aircraft', label: 'Crewed aircraft' },
  { value: 'ground_sensor', label: 'Ground sensors / in-situ' },
  { value: 'ground_network', label: 'Ground network' },
  { value: 'hybrid', label: 'Hybrid (space + ground/air)' },
  { value: 'other', label: 'Other' },
]

export function MissionNeedPanel({ section = 'need', onNext }: Props) {
  const { missionNeed, setMissionNeed } = useDesignStore()

  if (section === 'concept') {
    return <ConceptSection missionNeed={missionNeed} setMissionNeed={setMissionNeed} onNext={onNext} />
  }

  return <NeedSection missionNeed={missionNeed} setMissionNeed={setMissionNeed} onNext={onNext} />
}

// --- Step 1: Mission Need ---
function NeedSection({ missionNeed: mn, setMissionNeed, onNext }: {
  missionNeed: MissionNeedState; setMissionNeed: (n: Partial<MissionNeedState>) => void; onNext?: () => void
}) {
  return (
    <div style={{ padding: '0.75rem' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Mission Need</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '1rem' }}>
        Start with the problem, not the solution. What need exists that justifies this mission?
      </p>

      {/* Problem statement */}
      <div className="card">
        <h3 style={{ fontSize: '0.85rem' }}>What problem are we trying to solve?</h3>
        <textarea
          className="input"
          rows={3}
          value={mn.problem_statement}
          onChange={e => setMissionNeed({ problem_statement: e.target.value })}
          placeholder="e.g. Farmers in sub-Saharan Africa lack timely, affordable crop health data at the field scale, leading to delayed intervention and reduced yields."
          style={{ width: '100%', resize: 'vertical', fontSize: '0.8rem' }}
        />
      </div>

      {/* Operational context */}
      <div className="card">
        <h3 style={{ fontSize: '0.85rem' }}>Operational Context</h3>
        <textarea
          className="input"
          rows={2}
          value={mn.operational_context}
          onChange={e => setMissionNeed({ operational_context: e.target.value })}
          placeholder="When, where, and how will this solution be used? Who operates it day-to-day?"
          style={{ width: '100%', resize: 'vertical', fontSize: '0.8rem' }}
        />
      </div>

      {/* Stakeholders */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <h3 style={{ fontSize: '0.85rem', margin: 0 }}>Stakeholders</h3>
          <button className="btn btn-sm" onClick={() => {
            setMissionNeed({
              stakeholders: [...mn.stakeholders, { id: `sh-${Date.now()}`, name: '', role: 'user', needs: [], constraints: [], priority: 'primary' }]
            })
          }} style={{ fontSize: '0.7rem' }}>+ Add</button>
        </div>
        {mn.stakeholders.length === 0 && (
          <p style={{ fontSize: '0.75rem', color: '#6b7280', fontStyle: 'italic' }}>No stakeholders yet. Who benefits from this mission? Who pays for it? Who operates it?</p>
        )}
        {mn.stakeholders.map((sh, i) => (
          <div key={sh.id} style={{ padding: '0.5rem', background: 'var(--bg-primary, #111827)', borderRadius: '4px', marginBottom: '0.4rem', border: '1px solid var(--border, #374151)' }}>
            <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.3rem' }}>
              <input className="input" value={sh.name} placeholder="Stakeholder name"
                onChange={e => { const s = [...mn.stakeholders]; s[i] = { ...s[i], name: e.target.value }; setMissionNeed({ stakeholders: s }) }}
                style={{ flex: 1, fontSize: '0.78rem' }} />
              <select className="select" value={sh.role}
                onChange={e => { const s = [...mn.stakeholders]; s[i] = { ...s[i], role: e.target.value }; setMissionNeed({ stakeholders: s }) }}
                style={{ width: '140px', fontSize: '0.75rem' }}>
                {STAKEHOLDER_ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
              <button onClick={() => setMissionNeed({ stakeholders: mn.stakeholders.filter((_, j) => j !== i) })}
                style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.9rem' }}>x</button>
            </div>
            <input className="input" placeholder="Key need (e.g. 'weekly 10m-resolution crop health maps')"
              value={sh.needs[0] || ''}
              onChange={e => { const s = [...mn.stakeholders]; s[i] = { ...s[i], needs: [e.target.value] }; setMissionNeed({ stakeholders: s }) }}
              style={{ width: '100%', fontSize: '0.75rem', marginBottom: '0.2rem' }} />
          </div>
        ))}
      </div>

      {/* Objectives */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <h3 style={{ fontSize: '0.85rem', margin: 0 }}>Mission Objectives</h3>
          <button className="btn btn-sm" onClick={() => {
            setMissionNeed({
              objectives: [...mn.objectives, { id: `obj-${Date.now()}`, text: '', priority: 'primary', type: 'performance', measurable_criterion: '', status: 'proposed' }]
            })
          }} style={{ fontSize: '0.7rem' }}>+ Add</button>
        </div>
        {mn.objectives.length === 0 && (
          <p style={{ fontSize: '0.75rem', color: '#6b7280', fontStyle: 'italic' }}>No objectives yet. What must this mission achieve to be considered successful?</p>
        )}
        {mn.objectives.map((obj, i) => (
          <div key={obj.id} style={{ padding: '0.5rem', background: 'var(--bg-primary, #111827)', borderRadius: '4px', marginBottom: '0.4rem', border: '1px solid var(--border, #374151)' }}>
            <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.3rem' }}>
              <select className="select" value={obj.priority}
                onChange={e => { const o = [...mn.objectives]; o[i] = { ...o[i], priority: e.target.value }; setMissionNeed({ objectives: o }) }}
                style={{ width: '170px', fontSize: '0.72rem' }}>
                {OBJECTIVE_PRIORITIES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
              <button onClick={() => setMissionNeed({ objectives: mn.objectives.filter((_, j) => j !== i) })}
                style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.9rem', marginLeft: 'auto' }}>x</button>
            </div>
            <input className="input" placeholder="Objective statement (e.g. 'Provide weekly multispectral imagery at 10m GSD')"
              value={obj.text}
              onChange={e => { const o = [...mn.objectives]; o[i] = { ...o[i], text: e.target.value }; setMissionNeed({ objectives: o }) }}
              style={{ width: '100%', fontSize: '0.78rem', marginBottom: '0.2rem' }} />
            <input className="input" placeholder="Measurable criterion (e.g. 'GSD <= 10m at nadir, revisit <= 7 days')"
              value={obj.measurable_criterion}
              onChange={e => { const o = [...mn.objectives]; o[i] = { ...o[i], measurable_criterion: e.target.value }; setMissionNeed({ objectives: o }) }}
              style={{ width: '100%', fontSize: '0.72rem', color: '#9ca3af' }} />
          </div>
        ))}
      </div>

      {onNext && (
        <button className="btn" onClick={onNext} style={{ width: '100%' }}>
          Next: Concept Exploration
        </button>
      )}
    </div>
  )
}

// --- Step 2: Concept Exploration ---
function ConceptSection({ missionNeed: mn, setMissionNeed, onNext }: {
  missionNeed: MissionNeedState; setMissionNeed: (n: Partial<MissionNeedState>) => void; onNext?: () => void
}) {
  const hasNonSpace = mn.alternatives.some(a =>
    ['aerial_drone', 'aerial_aircraft', 'ground_sensor', 'ground_network', 'space_existing'].includes(a.type)
  )

  return (
    <div style={{ padding: '0.75rem' }}>
      <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Concept Exploration</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Before committing to a spacecraft: is space the right answer? Consider all alternatives.
      </p>

      {/* Non-space prompt */}
      {!hasNonSpace && (
        <div style={{ padding: '0.75rem', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '6px', marginBottom: '1rem', fontSize: '0.8rem' }}>
          <strong style={{ color: '#f59e0b' }}>Have you considered non-space alternatives?</strong>
          <div style={{ color: '#9ca3af', marginTop: '0.2rem', fontSize: '0.75rem' }}>
            Can existing satellite data (Copernicus, Landsat, commercial providers) meet the need?
            Could ground sensors, drones, or aircraft achieve the objectives more cost-effectively?
            NASA Pre-Phase A requires an Analysis of Alternatives (AoA).
          </div>
        </div>
      )}

      {/* Alternatives */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <h3 style={{ fontSize: '0.85rem', margin: 0 }}>Alternatives ({mn.alternatives.length})</h3>
          <button className="btn btn-sm" onClick={() => {
            setMissionNeed({
              alternatives: [...mn.alternatives, {
                id: `alt-${Date.now()}`, name: '', type: 'space_dedicated', description: '',
                pros: [], cons: [], feasibility_score: 0.5, decision: 'under_review', decision_rationale: '',
              }]
            })
          }} style={{ fontSize: '0.7rem' }}>+ Add Alternative</button>
        </div>

        {mn.alternatives.map((alt, i) => {
          const isSelected = mn.selected_alternative_id === alt.id
          return (
            <div key={alt.id} style={{
              padding: '0.5rem', borderRadius: '4px', marginBottom: '0.5rem',
              background: isSelected ? 'rgba(16,185,129,0.08)' : 'var(--bg-primary, #111827)',
              border: `1px solid ${isSelected ? '#10b981' : 'var(--border, #374151)'}`,
            }}>
              <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.3rem', alignItems: 'center' }}>
                <input className="input" value={alt.name} placeholder="Alternative name"
                  onChange={e => { const a = [...mn.alternatives]; a[i] = { ...a[i], name: e.target.value }; setMissionNeed({ alternatives: a }) }}
                  style={{ flex: 1, fontSize: '0.78rem', fontWeight: 600 }} />
                <select className="select" value={alt.type}
                  onChange={e => { const a = [...mn.alternatives]; a[i] = { ...a[i], type: e.target.value }; setMissionNeed({ alternatives: a }) }}
                  style={{ width: '200px', fontSize: '0.72rem' }}>
                  {ALTERNATIVE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
                <button onClick={() => setMissionNeed({ alternatives: mn.alternatives.filter((_, j) => j !== i) })}
                  style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}>x</button>
              </div>
              <textarea className="input" rows={2} placeholder="Description — how would this alternative solve the problem?"
                value={alt.description}
                onChange={e => { const a = [...mn.alternatives]; a[i] = { ...a[i], description: e.target.value }; setMissionNeed({ alternatives: a }) }}
                style={{ width: '100%', fontSize: '0.75rem', resize: 'vertical', marginBottom: '0.3rem' }} />
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <input className="input" placeholder="Pros (comma-separated)"
                  value={alt.pros.join(', ')}
                  onChange={e => { const a = [...mn.alternatives]; a[i] = { ...a[i], pros: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }; setMissionNeed({ alternatives: a }) }}
                  style={{ flex: 1, fontSize: '0.72rem' }} />
                <input className="input" placeholder="Cons (comma-separated)"
                  value={alt.cons.join(', ')}
                  onChange={e => { const a = [...mn.alternatives]; a[i] = { ...a[i], cons: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }; setMissionNeed({ alternatives: a }) }}
                  style={{ flex: 1, fontSize: '0.72rem' }} />
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.3rem', alignItems: 'center' }}>
                {!isSelected ? (
                  <button className="btn btn-sm" onClick={() => setMissionNeed({ selected_alternative_id: alt.id })}
                    style={{ fontSize: '0.7rem' }}>Select this concept</button>
                ) : (
                  <span style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 600 }}>Selected concept</span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Selection rationale */}
      {mn.selected_alternative_id && (
        <div className="card">
          <h3 style={{ fontSize: '0.85rem' }}>Why was this alternative selected?</h3>
          <textarea className="input" rows={2}
            value={mn.selection_rationale}
            onChange={e => setMissionNeed({ selection_rationale: e.target.value })}
            placeholder="Explain why this concept was chosen over the others..."
            style={{ width: '100%', resize: 'vertical', fontSize: '0.8rem' }} />
        </div>
      )}

      {/* ConOps */}
      <div className="card">
        <h3 style={{ fontSize: '0.85rem' }}>Concept of Operations (summary)</h3>
        <textarea className="input" rows={3}
          value={mn.conops_summary}
          onChange={e => setMissionNeed({ conops_summary: e.target.value })}
          placeholder="How will the system be operated? Key modes, ground segment, data flow to end users, mission timeline..."
          style={{ width: '100%', resize: 'vertical', fontSize: '0.8rem' }} />
      </div>

      {onNext && (
        <button className="btn" onClick={onNext} style={{ width: '100%' }}
          disabled={mn.alternatives.length < 2 || !mn.selected_alternative_id}>
          {mn.alternatives.length < 2 ? 'Add at least 2 alternatives to proceed' :
           !mn.selected_alternative_id ? 'Select a concept to proceed' :
           'Next: Mission Requirements'}
        </button>
      )}
    </div>
  )
}
