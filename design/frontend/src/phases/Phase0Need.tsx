/**
 * Phase 0: Mission Need
 *
 * Define the problem, stakeholders, objectives.
 * Concept trade: is space the right answer?
 * Set mission-level budget envelopes.
 */
import { MissionNeedPanel } from '../components/MissionNeedPanel'
import { MissionTradeView } from '../components/MissionTradeView'
import { useDesignStore } from '../stores/designStore'
import { fs } from '../theme/tokens'

export function Phase0Need() {
  const missionNeed = useDesignStore(s => s.missionNeed)
  const hasNeed = !!(missionNeed?.problem_statement && missionNeed?.objectives?.length > 0)

  return (
    <div style={{ padding: '1.5rem', maxWidth: '1200px', margin: '0 auto', overflowY: 'auto', height: '100%' }}>
      <h1 style={{ fontSize: fs.title, marginBottom: '0.25rem' }}>Phase 0: Mission Need</h1>
      <p style={{ color: 'var(--text-2)', fontSize: fs.body, marginBottom: '1.5rem' }}>
        Define the problem to solve, who needs it solved, and what success looks like.
        Then assess whether space is the right answer.
      </p>

      <MissionNeedPanel />

      {hasNeed && (
        <div style={{ marginTop: '1.5rem' }}>
          <MissionTradeView />
        </div>
      )}
    </div>
  )
}
