import { useDesignStore } from '../stores/designStore'
import { useSessionStore } from '../stores/sessionStore'
import { MissionDashboard } from './MissionDashboard'
import { fs } from '../theme/tokens'





export function DesignWorkspace() {
  const { result, isRunning, error } = useDesignStore()
  const sessionParams = useSessionStore(s => s.parameters)
  const sessionId = useSessionStore(s => s.sessionId)

  // Has data from either store?
  const hasSessionData = sessionId && Object.keys(sessionParams).length > 0
  const hasData = !!result || hasSessionData

  if (error) {
    return (
      <div style={{ padding: '2rem' }}>
        <div className="card" style={{ borderColor: 'var(--danger)' }}>
          <h3 style={{ color: 'var(--danger)' }}>Error</h3>
          <p style={{ fontSize: fs.body }}>{error}</p>
          <p style={{ fontSize: fs.body, color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Make sure the SpaceCDF server is running: <code>uvicorn spacecdf_server.app:app --reload</code>
          </p>
        </div>
      </div>
    )
  }

  if (isRunning) {
    return (
      <div className="loading">
        <div className="spinner" />
        Running design convergence loop...
      </div>
    )
  }

  if (!hasData) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
        <h2 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>SpaceCDF Design Workspace</h2>
        <p>Configure mission requirements and click "Run Design" to start the AI concurrent design loop.</p>
        <p style={{ marginTop: '1rem', fontSize: fs.body }}>
          Or click <strong>New from Template</strong> to start from a mission archetype, then <strong>Start Session</strong> to collaborate.
        </p>
      </div>
    )
  }

  return <MissionDashboard />
}
