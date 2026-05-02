import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'
import { MissionNeedPanel } from './MissionNeedPanel'
import { MissionTradeView } from './MissionTradeView'
import { RequirementsPanel } from './RequirementsPanel'

type Step = 'need' | 'concept' | 'requirements' | 'design'

const STEPS: { id: Step; label: string; description: string }[] = [
  { id: 'need', label: '1. Mission Need', description: 'What problem are we solving? For whom?' },
  { id: 'concept', label: '2. Concept', description: 'Alternatives analysis — is space the right answer?' },
  { id: 'requirements', label: '3. Requirements', description: 'Mission parameters — orbit, payload, constraints' },
  { id: 'design', label: '4. Design', description: 'Run convergence and review system design' },
]

export function StudyStepper() {
  const [activeStep, setActiveStep] = useState<Step>('need')
  const { missionNeed, runDesign, isRunning, result } = useDesignStore()

  // Determine step completion
  const needComplete = !!(missionNeed.problem_statement.trim() && missionNeed.stakeholders.length > 0 && missionNeed.objectives.length > 0)
  const conceptComplete = !!(missionNeed.alternatives.length >= 2 && missionNeed.selected_alternative_id)
  const reqComplete = !!result

  const completionMap: Record<Step, boolean> = {
    need: needComplete,
    concept: conceptComplete,
    requirements: false, // Always editable
    design: reqComplete,
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Step indicator */}
      <div style={{ padding: '0.5rem', borderBottom: '1px solid var(--border, #374151)' }}>
        {STEPS.map((step, i) => {
          const isActive = activeStep === step.id
          const isComplete = completionMap[step.id]
          return (
            <button
              key={step.id}
              onClick={() => setActiveStep(step.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem', width: '100%',
                padding: '0.4rem 0.5rem', border: 'none', cursor: 'pointer', textAlign: 'left',
                background: isActive ? 'rgba(59,130,246,0.12)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--accent, #3b82f6)' : '3px solid transparent',
                borderRadius: '0 4px 4px 0', marginBottom: '0.15rem',
              }}
            >
              <span style={{
                width: 20, height: 20, borderRadius: '50%', fontSize: '0.65rem', fontWeight: 700,
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                background: isComplete ? '#10b981' : isActive ? '#3b82f6' : '#374151',
                color: 'white',
              }}>
                {isComplete ? '\u2713' : i + 1}
              </span>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: isActive ? '#f3f4f6' : '#9ca3af' }}>{step.label}</div>
                <div style={{ fontSize: '0.6rem', color: '#6b7280', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{step.description}</div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Step content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {activeStep === 'need' && (
          <MissionNeedPanel onNext={() => setActiveStep('concept')} />
        )}
        {activeStep === 'concept' && (
          <MissionTradeView onConceptSelected={() => setActiveStep('requirements')} />
        )}
        {activeStep === 'requirements' && (
          <RequirementsPanel />
        )}
        {activeStep === 'design' && (
          <div style={{ padding: '1rem' }}>
            <h2>System Design</h2>
            <p style={{ fontSize: '0.85rem', color: '#9ca3af', marginBottom: '1rem' }}>
              Run the AI concurrent design loop to size all subsystems, compute budgets,
              and identify technology innovation opportunities.
            </p>
            {!needComplete && (
              <div style={{ padding: '0.75rem', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '6px', marginBottom: '1rem', fontSize: '0.8rem', color: '#f59e0b' }}>
                Consider completing Mission Need (Step 1) first — it establishes the rationale for design decisions.
              </div>
            )}
            {!conceptComplete && needComplete && (
              <div style={{ padding: '0.75rem', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '6px', marginBottom: '1rem', fontSize: '0.8rem', color: '#3b82f6' }}>
                Consider completing Concept Exploration (Step 2) — have you considered non-space alternatives?
              </div>
            )}
            <button className="btn" onClick={runDesign} disabled={isRunning} style={{ width: '100%' }}>
              {isRunning ? 'Running Design Loop...' : 'Run Design'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
