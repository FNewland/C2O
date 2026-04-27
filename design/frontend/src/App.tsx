import { useState, useMemo, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { useDesignStore } from './stores/designStore'
import { useSessionStore } from './stores/sessionStore'
import { useSessionSocket } from './hooks/useSessionSocket'
import { useCreateSession } from './hooks/useSession'

import { RequirementsPanel } from './components/RequirementsPanel'
import { DesignWorkspace } from './components/DesignWorkspace'
import { InsightsPanel } from './components/InsightsPanel'
import { ConflictsPanel } from './components/ConflictsPanel'
import { ExportPanel } from './components/ExportPanel'
import { PositionPanel } from './components/PositionPanel'
import { SessionBar } from './components/SessionBar'
import { LiveEditToast } from './components/LiveEditToast'
import { EquipmentBrowser } from './components/EquipmentBrowser'
import { ComplianceMatrix } from './components/ComplianceMatrix'
import { CostBreakdown } from './components/CostBreakdown'
import { TradeStudyPanel } from './components/TradeStudyPanel'
import { HistoryDrawer } from './components/HistoryDrawer'
import { TemplateGallery } from './components/TemplateGallery'
import { EcssCompliancePanel } from './components/EcssCompliancePanel'
import { SnapshotsPanel } from './components/SnapshotsPanel'
import { OptimizerPanel } from './components/OptimizerPanel'
import { UserManual } from './components/UserManual'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 5_000 },
  },
})

type CenterTab = 'design' | 'positions' | 'compliance' | 'ecss' | 'cost' | 'trade' | 'snapshots' | 'optimizer' | 'help'
type RightTab = 'insights' | 'conflicts' | 'exports'

const POSITION_OPTIONS = [
  { id: 'systems_engineer', label: 'Systems Engineer' },
  { id: 'mission_analyst', label: 'Mission Analyst' },
  { id: 'payload_lead', label: 'Payload Lead' },
  { id: 'power_engineer', label: 'Power Engineer' },
  { id: 'aocs_engineer', label: 'AOCS Engineer' },
  { id: 'thermal_engineer', label: 'Thermal Engineer' },
  { id: 'comms_engineer', label: 'Comms Engineer' },
  { id: 'propulsion_engineer', label: 'Propulsion Engineer' },
  { id: 'structures_engineer', label: 'Structures Engineer' },
  { id: 'cost_engineer', label: 'Cost Engineer' },
]

function AppContent() {
  const { result, studyId, createStudy, setStudyId } = useDesignStore()
  const [centerTab, setCenterTab] = useState<CenterTab>('design')
  const [rightTab, setRightTab] = useState<RightTab>('insights')
  const [showEquipmentBrowser, setShowEquipmentBrowser] = useState(false)
  const [showSessionStarter, setShowSessionStarter] = useState(false)
  const [showTemplateGallery, setShowTemplateGallery] = useState(false)

  // Session state
  const sessionId = useSessionStore(s => s.sessionId)
  const positionId = useSessionStore(s => s.positionId)
  const displayName = useSessionStore(s => s.displayName)
  const setSession = useSessionStore(s => s.setSession)
  const clearSession = useSessionStore(s => s.clearSession)

  // WebSocket (only active when session is set)
  const { status: wsStatus, sendEdit } = useSessionSocket(sessionId, positionId, displayName)

  // Publish sendEdit into the session store so any component can use it
  const setSendEdit = useSessionStore(s => s.setSendEdit)
  useEffect(() => {
    setSendEdit(sessionId ? sendEdit : null)
    return () => setSendEdit(null)
  }, [sessionId, sendEdit, setSendEdit])

  const createSession = useCreateSession()

  const conflictCount = result?.conflicts?.length || 0
  const criticalCount = result?.conflicts?.filter(c => c.severity === 'critical').length || 0

  const handleStartSession = () => setShowSessionStarter(true)

  const handleLeaveSession = () => clearSession()

  const handleSessionConfirm = async (pos: string, name: string, positionIds: string[]) => {
    // Ensure study exists
    let sid = studyId
    if (!sid) sid = await createStudy()
    if (!sid) return
    // Create session
    const data = await createSession.mutateAsync({ study_id: sid, name: `${name || pos} session` })
    setSession(data.id, pos, name || pos, positionIds)
    setShowSessionStarter(false)
  }

  const handleEquipmentSelect = (category: string, component: any) => {
    // Map category to a param id to edit
    const paramMap: Record<string, string> = {
      batteries: 'power.battery_capacity_wh',
      solar_cells: 'power.sa_power_eol_w',
      reaction_wheels: 'aocs.mass_kg',
      star_trackers: 'aocs.mass_kg',
      transponders: 'link.ttc_mass_kg',
      thrusters: 'propulsion.total_mass_kg',
    }
    const paramId = paramMap[category]
    if (!paramId) {
      alert(`No param mapping for ${category}`)
      return
    }
    // Use performance field if available, else mass
    const perf = component.performance || {}
    const value = category === 'batteries' ? (perf.capacity_wh ?? component.mass_kg)
      : category === 'solar_cells' ? (perf.power_w ?? 50)
      : component.mass_kg ?? 1

    const ok = sendEdit(paramId, value, {
      rationale: `Selected ${component.name} from ${component.manufacturer || 'KB'}`,
      equipmentId: component.id,
      editType: 'equipment_selection',
    })
    if (!ok) alert('WebSocket not connected. Join a session first.')
    else setShowEquipmentBrowser(false)
  }

  const centerTabs: { id: CenterTab; label: string }[] = useMemo(() => [
    { id: 'design', label: 'Design' },
    { id: 'positions', label: 'Positions' },
    { id: 'compliance', label: 'Compliance' },
    { id: 'ecss', label: 'ECSS Gate' },
    { id: 'cost', label: 'Cost' },
    { id: 'trade', label: 'Trade Studies' },
    { id: 'snapshots', label: 'Snapshots' },
    { id: 'optimizer', label: 'Optimizer' },
    { id: 'help', label: 'Help' },
  ], [])

  const handleTemplateInstantiated = (newStudyId: string) => {
    setStudyId(newStudyId)
    setShowTemplateGallery(false)
    setCenterTab('design')
  }

  return (
    <div className="app">
      <header className="header">
        <h1>SpaceCDF</h1>
        <span className="subtitle">AI-Supported Concurrent Design Facility</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {result && (
            <>
              <span className="stat">
                {result.converged ? '✓ Converged' : '⚠ Not converged'} in{' '}
                <strong>{result.iterations}</strong> iterations
              </span>
              <span className="stat">
                <strong>{result.total_time_s}s</strong>
              </span>
              {conflictCount > 0 && (
                <span className="stat" style={{ color: criticalCount > 0 ? 'var(--danger)' : 'var(--warning)' }}>
                  {conflictCount} conflict{conflictCount !== 1 ? 's' : ''}
                </span>
              )}
            </>
          )}
          <button className="btn btn-sm" onClick={() => setShowTemplateGallery(true)}>
            New from Template
          </button>
          {sessionId && (
            <button className="btn btn-sm" onClick={() => setShowEquipmentBrowser(true)}>
              Browse Equipment
            </button>
          )}
        </div>
      </header>

      <SessionBar
        wsStatus={wsStatus}
        onStartSession={handleStartSession}
        onLeaveSession={handleLeaveSession}
      />

      <main className="main">
        <div className="panel">
          <RequirementsPanel />
        </div>

        <div className="panel" style={{ background: 'var(--bg-primary)', borderRight: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '0.75rem', padding: '0 1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', flexWrap: 'wrap' }}>
            {centerTabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setCenterTab(tab.id)}
                style={{
                  background: centerTab === tab.id ? 'var(--accent)' : 'transparent',
                  color: centerTab === tab.id ? 'white' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.03em',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
          {centerTab === 'design' && <DesignWorkspace />}
          {centerTab === 'positions' && <PositionPanel />}
          {centerTab === 'compliance' && <ComplianceMatrix studyId={studyId} />}
          {centerTab === 'ecss' && <EcssCompliancePanel studyId={studyId} />}
          {centerTab === 'cost' && <CostBreakdown studyId={studyId} />}
          {centerTab === 'trade' && <TradeStudyPanel studyId={studyId} />}
          {centerTab === 'snapshots' && <SnapshotsPanel sessionId={sessionId} />}
          {centerTab === 'optimizer' && <OptimizerPanel sessionId={sessionId} />}
          {centerTab === 'help' && <UserManual />}
        </div>

        <div className="panel">
          <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '0.75rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            {(['insights', 'conflicts', 'exports'] as RightTab[]).map(tab => (
              <button
                key={tab}
                onClick={() => setRightTab(tab)}
                style={{
                  background: rightTab === tab ? 'var(--accent)' : 'transparent',
                  color: rightTab === tab ? 'white' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.03em',
                  position: 'relative',
                }}
              >
                {tab}
                {tab === 'conflicts' && conflictCount > 0 && (
                  <span style={{
                    position: 'absolute', top: '-4px', right: '-4px',
                    background: criticalCount > 0 ? 'var(--danger)' : 'var(--warning)',
                    color: 'white', borderRadius: '50%',
                    width: '16px', height: '16px', fontSize: '0.6rem',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>{conflictCount}</span>
                )}
              </button>
            ))}
          </div>
          {rightTab === 'insights' && <InsightsPanel />}
          {rightTab === 'conflicts' && (
            <>
              <h2>Cross-Domain Conflicts</h2>
              <ConflictsPanel />
            </>
          )}
          {rightTab === 'exports' && <ExportPanel studyId={studyId} />}
        </div>
      </main>

      {/* Live toast notifications */}
      <LiveEditToast />

      {/* History drawer (edit audit trail) */}
      <HistoryDrawer sessionId={sessionId} />

      {/* Equipment browser modal */}
      {showEquipmentBrowser && (
        <EquipmentBrowser
          studyId={studyId}
          onClose={() => setShowEquipmentBrowser(false)}
          onSelect={handleEquipmentSelect}
        />
      )}

      {/* Template gallery modal */}
      {showTemplateGallery && (
        <TemplateGallery
          onClose={() => setShowTemplateGallery(false)}
          onInstantiated={handleTemplateInstantiated}
        />
      )}

      {/* Session starter modal */}
      {showSessionStarter && (
        <SessionStarterModal
          onConfirm={handleSessionConfirm}
          onCancel={() => setShowSessionStarter(false)}
          isLoading={createSession.isPending}
        />
      )}
    </div>
  )
}

function SessionStarterModal({
  onConfirm, onCancel, isLoading,
}: {
  onConfirm: (positionId: string, displayName: string, positionIds: string[]) => void
  onCancel: () => void
  isLoading: boolean
}) {
  const [selected, setSelected] = useState<string[]>(['systems_engineer'])
  const [name, setName] = useState('')

  const toggle = (id: string) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    )
  }

  const ROLE_COLORS: Record<string, string> = {
    systems_engineer: '#3b82f6', mission_analyst: '#8b5cf6', payload_lead: '#10b981',
    power_engineer: '#f59e0b', aocs_engineer: '#06b6d4', thermal_engineer: '#ef4444',
    comms_engineer: '#ec4899', propulsion_engineer: '#f97316', structures_engineer: '#84cc16',
    cost_engineer: '#a855f7',
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
      zIndex: 9000, display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onCancel}>
      <div style={{
        background: 'var(--bg-primary, #111827)', border: '1px solid var(--border, #374151)',
        borderRadius: '8px', padding: '1.5rem', maxWidth: '480px', width: '90%',
      }} onClick={e => e.stopPropagation()}>
        <h2>Join a Design Session</h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #9ca3af)', marginBottom: '0.75rem' }}>
          Select one or more positions. Small teams can claim multiple roles.
          You can edit parameters owned by any of your positions.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '1rem' }}>
          {POSITION_OPTIONS.map(p => {
            const active = selected.includes(p.id)
            return (
              <label key={p.id} style={{
                display: 'flex', alignItems: 'center', gap: '0.3rem',
                fontSize: '0.78rem', padding: '0.25rem 0.6rem', borderRadius: '4px', cursor: 'pointer',
                background: active ? `${ROLE_COLORS[p.id] || '#3b82f6'}22` : 'transparent',
                border: `1px solid ${active ? (ROLE_COLORS[p.id] || '#3b82f6') : 'var(--border, #374151)'}`,
                color: active ? (ROLE_COLORS[p.id] || '#3b82f6') : 'var(--text-secondary, #9ca3af)',
              }}>
                <input type="checkbox" checked={active} onChange={() => toggle(p.id)}
                  style={{ width: 14, height: 14 }} />
                {p.label}
              </label>
            )
          })}
        </div>
        <div className="form-group">
          <label>Display name (optional)</label>
          <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Alice" />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          <button className="btn" onClick={() => onConfirm(selected[0], name, selected)} disabled={isLoading || selected.length === 0}>
            {isLoading ? 'Creating...' : `Join as ${selected.length} position${selected.length !== 1 ? 's' : ''}`}
          </button>
          <button className="btn btn-sm" onClick={onCancel} style={{ background: 'var(--border, #374151)' }}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}

export default App
