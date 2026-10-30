/**
 * StudyStepper — thin vertical step indicator (60px wide).
 *
 * Shows 4 numbered steps with completion status. Clicking a step
 * navigates to that step's content (rendered in the center panel by App.tsx).
 * No longer contains step content — just the navigation.
 */
import { useDesignStore } from '../stores/designStore'

type Step = 'need' | 'concept' | 'requirements' | 'design'

const STEPS: { id: Step; label: string }[] = [
  { id: 'need', label: 'Need' },
  { id: 'concept', label: 'Concept' },
  { id: 'requirements', label: 'Reqs' },
  { id: 'design', label: 'Design' },
]

interface Props {
  activeStep: string
  onStepClick: (step: Step) => void
}

export function StudyStepper({ activeStep, onStepClick }: Props) {
  const { missionNeed, result } = useDesignStore()

  const needComplete = !!(missionNeed.problem_statement.trim() && missionNeed.stakeholders.length > 0 && missionNeed.objectives.length > 0)
  const conceptComplete = !!(missionNeed.alternatives.length >= 2 && missionNeed.selected_alternative_id)
  const designComplete = !!result

  const completionMap: Record<Step, boolean> = {
    need: needComplete,
    concept: conceptComplete,
    requirements: false,
    design: designComplete,
  }

  return (
    <div style={{
      width: '60px', background: 'var(--bg-secondary, #111827)',
      borderRight: '1px solid var(--border, #374151)',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      paddingTop: '1rem', gap: '0.25rem',
    }}>
      {STEPS.map((step, i) => {
        const isActive = activeStep === step.id
        const isComplete = completionMap[step.id]
        const isPast = STEPS.findIndex(s => s.id === activeStep) > i

        return (
          <div key={step.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.15rem' }}>
            <button
              onClick={() => onStepClick(step.id)}
              title={step.label}
              style={{
                width: 34, height: 34, borderRadius: '50%', border: 'none',
                cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.72rem', fontWeight: 700,
                background: isComplete ? '#10b981' : isActive ? '#3b82f6' : (isPast ? '#374151' : '#1f2937'),
                color: (isComplete || isActive) ? 'white' : '#6b7280',
                transition: 'all 0.15s',
              }}
            >
              {isComplete ? '\u2713' : i + 1}
            </button>
            <span style={{
              fontSize: '0.55rem', color: isActive ? '#3b82f6' : '#4b5563',
              fontWeight: isActive ? 600 : 400, textAlign: 'center',
            }}>
              {step.label}
            </span>
            {i < STEPS.length - 1 && (
              <div style={{ width: 2, height: 12, background: isPast || isComplete ? '#374151' : '#1f2937', margin: '0.1rem 0' }} />
            )}
          </div>
        )
      })}
    </div>
  )
}
