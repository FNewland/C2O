import { useDesignStore, type DesignParam } from '../stores/designStore'
import { useSessionStore } from '../stores/sessionStore'
import { MissionDashboard } from './MissionDashboard'

const DOMAIN_ORDER = [
  'orbit', 'payload', 'power', 'aocs', 'thermal', 'link', 'data',
  'propulsion', 'structure', 'mass', 'cost', 'systems', 'risk', 'trl',
  'debris', 'sustainability', 'radiation', 'volume', 'reliability', 'community',
]

function formatValue(value: number | string | boolean): string {
  if (typeof value === 'number') {
    if (Math.abs(value) >= 1e6) return value.toExponential(2)
    if (Math.abs(value) >= 100) return value.toFixed(0)
    if (Math.abs(value) >= 1) return value.toFixed(2)
    if (Math.abs(value) >= 0.01) return value.toFixed(3)
    return value.toExponential(2)
  }
  return String(value)
}

function BudgetGauge({ name, budget }: { name: string; budget: any }) {
  const pct = Math.max(0, Math.min(100, 100 - budget.margin_percent))
  const colors: Record<string, string> = {
    green: 'var(--success)',
    amber: 'var(--warning)',
    red: 'var(--danger)',
    exceeded: 'var(--danger)',
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3>{name.toUpperCase()} Budget</h3>
        <span className={`badge badge-${budget.status}`}>{budget.status}</span>
      </div>
      <div className="budget-bar">
        <div
          className="budget-bar-fill"
          style={{ width: `${pct}%`, background: colors[budget.status] || 'var(--accent)' }}
        />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
        <span>{budget.total_with_margin.toFixed(1)} {budget.lines?.[0]?.unit || ''} (w/margin)</span>
        <span>{budget.allocation.toFixed(1)} allocation</span>
      </div>
      <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
        Margin: <strong style={{ color: colors[budget.status] }}>{budget.margin_percent.toFixed(1)}%</strong>
      </div>
    </div>
  )
}

function ParamTable({ params, domain }: { params: Record<string, DesignParam>; domain: string }) {
  const domainParams = Object.entries(params).filter(([_, p]) => p.domain === domain)
  if (domainParams.length === 0) return null

  return (
    <div className="domain-section">
      <div className="domain-header">{domain}</div>
      {domainParams.map(([pid, p]) => {
        const name = pid.split('.').slice(1).join(' ').replace(/_/g, ' ')
        return (
          <div className="param-row" key={pid}>
            <span className="param-name">{name}</span>
            <span>
              <span className="param-value">{formatValue(p.value)}</span>
              {p.unit && <span className="param-unit">{p.unit}</span>}
            </span>
          </div>
        )
      })}
    </div>
  )
}

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
          <p style={{ fontSize: '0.85rem' }}>{error}</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
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
        <p style={{ marginTop: '1rem', fontSize: '0.8rem' }}>
          Or click <strong>New from Template</strong> to start from a mission archetype, then <strong>Start Session</strong> to collaborate.
        </p>
      </div>
    )
  }

  return <MissionDashboard />
}
