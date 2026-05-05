import { useState, useMemo, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { useDesignStore } from './stores/designStore'
import { useSessionStore } from './stores/sessionStore'
import { useSessionSocket } from './hooks/useSessionSocket'
import { useCreateSession } from './hooks/useSession'
import { POSITION_OPTIONS, POSITION_COLOR } from './constants'

import { StudyStepper } from './components/StudyStepper'
import { MissionNeedPanel } from './components/MissionNeedPanel'
import { MissionTradeView } from './components/MissionTradeView'
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
import { ExportsPanel } from './components/ExportsPanel'
import { DesignStateBar } from './components/DesignStateBar'
import { ConflictReviewModal } from './components/ConflictReviewModal'
import { ChangeAuditPanel } from './components/ChangeAuditPanel'
import { SystemArchitectureEditor } from './components/SystemArchitectureEditor'
import { SystemBlockDiagram } from './components/SystemBlockDiagram'
import { EngineeringBudgets } from './components/EngineeringBudgets'\nimport { ProjectManagement } from './components/ProjectManagement'
import { ParametricEditor } from './components/ParametricEditor'
import { LinkBudgetTool } from './components/LinkBudgetTool'
import { PointingBudget } from './components/PointingBudget'
import { DataBudget } from './components/DataBudget'
import { VerificationMatrix } from './components/VerificationMatrix'
import { GateReviewPanel } from './components/GateReviewPanel'
import { PositionAnswersPanel } from './components/PositionAnswersPanel'
import { ConOpsEditor } from './components/ConOpsEditor'
import { MissionArchitectureEditor } from './components/MissionArchitectureEditor'
import { FunctionTreeView } from './components/FunctionTreeView'
import { InterfaceMatrixView } from './components/InterfaceMatrixView'
import { RequirementsEditor } from './components/RequirementsEditor'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 5_000 },
  },
})

type CenterTab = 'need' | 'concept' | 'requirements' | 'design' | 'conops' | 'functions' | 'architecture' | 'budgets' | 'pm' | 'interfaces' | 'reqs' | 'positions' | 'answers' | 'gate' | 'compliance' | 'ecss' | 'cost' | 'trade' | 'snapshots' | 'optimizer' | 'linkbudget' | 'verification' | 'exports' | 'parametric' | 'audit' | 'help'
type RightTab = 'insights' | 'conflicts' | 'exports'

function AppContent() {
  const { result, studyId, createStudy, setStudyId, runDesign } = useDesignStore()
  const [centerTab, setCenterTab] = useState<CenterTab>('need')
  const [rightTab, setRightTab] = useState<RightTab>('insights')
  const [showEquipmentBrowser, setShowEquipmentBrowser] = useState(false)
  const [showSessionStarter, setShowSessionStarter] = useState(false)
  const [showConflictReview, setShowConflictReview] = useState(false)
  const [autoReconverge, setAutoReconverge] = useState(false)
  const [showTemplateGallery, setShowTemplateGallery] = useState(false)

  // Auto-navigate to Design tab when design run completes
  useEffect(() => {
    if (result && centerTab === 'requirements') {
      setCenterTab('design')
    }
    // Show conflict review if critical conflicts exist after convergence
    if (result?.conflicts?.some(c => c.severity === 'critical')) {
      setShowConflictReview(true)
    }
  }, [result])

  // Auto-reconverge when design is stale (if enabled)
  const designStale = useDesignStore(s => s.designStale)
  const isRunning = useDesignStore(s => s.isRunning)
  useEffect(() => {
    if (autoReconverge && designStale && !isRunning && result) {
      // Debounce: wait 1 second after last change before auto-running
      const timer = setTimeout(() => {
        if (useDesignStore.getState().designStale) {
          runDesign()
        }
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [autoReconverge, designStale, isRunning])

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
    // Create session (backend runs initial convergence)
    const data = await createSession.mutateAsync({ study_id: sid, name: `${name || pos} session` })
    setSession(data.id, pos, name || pos, positionIds)
    setShowSessionStarter(false)
    // Also run design on frontend so designStore.result is populated immediately
    // (gives dashboard data while WebSocket bootstraps the live state)
    runDesign()
  }

  const handleEquipmentSelect = (category: string, component: any) => {
    // Always persist equipment selection to designStore (upward flow)
    const existing = useDesignStore.getState().selectedEquipment
    const key = `${category}:${component.id || component.name}`
    const existingItem = existing.find(e => `${e.category}:${e.componentId}` === key)
    if (existingItem) {
      // Increment quantity
      useDesignStore.setState({
        selectedEquipment: existing.map(e =>
          `${e.category}:${e.componentId}` === key ? { ...e, quantity: e.quantity + 1 } : e
        ),
      })
    } else {
      useDesignStore.setState({
        selectedEquipment: [...existing, {
          category, componentId: component.id || component.name,
          name: component.name, mass_kg: component.mass_kg || 0,
          power_w: component.power_w || 0, cost_keur: component.cost_keur || 0,
          quantity: 1,
        }],
      })
    }
    // Mark design stale — triggers reconvergence to update budgets
    useDesignStore.getState().markStale('equipment')

    // Also send via WebSocket if session active (for real-time collaboration)
    const storeSendEdit = useSessionStore.getState().sendEdit
    if (!storeSendEdit) {
      // No session — equipment persisted to store, design marked stale, user can re-run
      return
    }

    // Rich parameter mapping: each category can produce multiple parameter edits
    const EFFECTS: Record<string, { paramId: string; extract: (c: any) => number | null }[]> = {
      batteries: [
        { paramId: 'power.battery_capacity_wh', extract: c => c.performance?.capacity_wh ?? null },
        { paramId: 'power.battery_mass_kg', extract: c => c.mass_kg ?? null },
      ],
      solar_cells: [
        { paramId: 'power.sa_power_eol_w', extract: c => c.performance?.power_w ?? null },
        { paramId: 'power.sa_mass_kg', extract: c => c.mass_kg ?? null },
      ],
      reaction_wheels: [
        { paramId: 'aocs.mass_kg', extract: c => c.mass_kg ? c.mass_kg * 4 : null },
        { paramId: 'aocs.wheel_momentum_nms', extract: c => c.performance?.momentum_nms ?? null },
      ],
      star_trackers: [
        { paramId: 'aocs.pointing_accuracy_deg', extract: c => c.performance?.accuracy_arcsec ? c.performance.accuracy_arcsec / 3600 : null },
      ],
      transponders: [
        { paramId: 'link.ttc_mass_kg', extract: c => c.mass_kg ?? null },
        { paramId: 'link.ttc_power_w', extract: c => c.power_w ?? null },
      ],
      thrusters: [
        { paramId: 'propulsion.isp_s', extract: c => c.performance?.isp_s ?? null },
        { paramId: 'propulsion.total_mass_kg', extract: c => c.mass_kg ?? null },
      ],
    }

    const effects = EFFECTS[category] || []
    for (const eff of effects) {
      const value = eff.extract(component)
      if (value !== null) {
        storeSendEdit(eff.paramId, value, {
          rationale: `Selected ${component.name} from ${component.manufacturer || 'KB'}`,
          equipmentId: component.id,
          editType: 'equipment_selection',
        })
      }
    }

    // Fallback: if no effects matched, try mass as the primary param
    if (effects.length === 0 && component.mass_kg) {
      storeSendEdit(`${category}.mass_kg`, component.mass_kg, {
        rationale: `Selected ${component.name}`,
        equipmentId: component.id,
        editType: 'equipment_selection',
      })
    }
  }

  // Tabs organized by workflow phase
  // Determine current design maturity level based on what's been completed
  const hasNeed = !!(missionNeed.problem_statement && missionNeed.objectives.length > 0)
  const hasDesignResult = !!result
  const hasArchitecture = !!(useDesignStore.getState().architectureDerivedReqs?.length > 0)
  const currentLevel = hasArchitecture ? 4 : hasDesignResult ? 3 : hasNeed ? 1 : 0

  // Tabs organized by System-V level with progressive unlock
  const centerTabs: { id: CenterTab; label: string; group?: string; level: number }[] = useMemo(() => [
    // Level 1: Mission Architecture (after need defined)
    { id: 'design', label: 'Dashboard', group: 'Mission', level: 1 },
    { id: 'conops', label: 'ConOps', level: 1 },
    { id: 'functions', label: 'Functions', level: 1 },
    { id: 'reqs', label: 'Requirements', level: 1 },
    // Level 2: System Architecture (after design run)
    { id: 'architecture', label: 'Architecture', group: 'System', level: 2 },
    { id: 'interfaces', label: 'Interfaces', level: 2 },
    { id: 'budgets', label: 'Eng. Budgets', level: 2 },
    { id: 'trade', label: 'Trade Studies', level: 2 },
    // Level 3: Subsystem Design (after architecture selected)
    { id: 'linkbudget', label: 'Link Budget', group: 'Subsystem', level: 3 },
    { id: 'optimizer', label: 'Optimizer', level: 3 },
    { id: 'cost', label: 'Cost', level: 3 },
    // Level 4: Verification (after subsystem design)
    { id: 'compliance', label: 'Compliance', group: 'Verify', level: 4 },
    { id: 'verification', label: 'V&V Matrix', level: 4 },
    { id: 'gate', label: 'Gate Review', level: 4 },\n    { id: 'pm', label: 'Project Mgmt', level: 2 },
    // Cross-cutting (always available after Level 1)
    { id: 'positions', label: 'Positions', group: 'Team', level: 1 },
    { id: 'answers', label: 'Q&A', level: 1 },
    { id: 'exports', label: 'Exports', group: 'Data', level: 2 },
    { id: 'parametric', label: 'Parametric', level: 1 },
    { id: 'audit', label: 'Changes', level: 1 },
    { id: 'help', label: 'Help', level: 0 },
  ], [])

  // Filter tabs to only show those at or below current level
  const visibleTabs = centerTabs.filter(t => t.level <= currentLevel)

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
          {(sessionId || result) && currentLevel >= 3 && (
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

      {/* Phase-adaptive layout: steps 1-3 use full center, step 4 uses 3-panel */}
      <main className={`main ${centerTab === 'design' || result ? 'phase-design' : 'phase-workflow'}`}>

        {/* Left: thin step indicator (always visible) */}
        <StudyStepper activeStep={centerTab === 'design' ? 'design' : centerTab as any} onStepClick={(step) => {
          if (step === 'design') setCenterTab('design')
          else setCenterTab(step as CenterTab)
        }} />

        {/* Center: workflow steps OR tabbed design content */}
        <div className="panel" style={{ background: 'var(--bg-primary)', padding: 0 }}>
          {/* Show workflow step content for steps 1-3 */}
          {centerTab === 'need' && (
            <div style={{ maxWidth: '800px', margin: '0 auto', padding: '1.5rem' }}>
              <MissionNeedPanel onNext={() => setCenterTab('concept' as CenterTab)} />
            </div>
          )}
          {centerTab === 'concept' && (
            <div style={{ maxWidth: '900px', margin: '0 auto', padding: '1.5rem' }}>
              <MissionTradeView onConceptSelected={() => setCenterTab('requirements' as CenterTab)} />
            </div>
          )}
          {centerTab === 'requirements' && (
            <div style={{ maxWidth: '800px', margin: '0 auto', padding: '1.5rem' }}>
              <RequirementsPanel />
            </div>
          )}

          {/* Design phase: tabbed content */}
          {!['need', 'concept', 'requirements'].includes(centerTab) && (
            <>
              {/* Level indicator */}
              <div style={{ display: 'flex', gap: '0.5rem', padding: '0.3rem 1rem', fontSize: '0.65rem', color: '#6b7280', borderBottom: '1px solid var(--border)', alignItems: 'center' }}>
                <span style={{ fontWeight: 700 }}>LEVEL:</span>
                {['Need', 'Mission Arch', 'System Arch', 'Subsystem', 'V&V'].map((lvl, i) => (
                  <span key={i} style={{
                    padding: '0.1rem 0.4rem', borderRadius: '3px', fontSize: '0.6rem',
                    background: i <= currentLevel ? ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'][i] + '22' : '#374151',
                    color: i <= currentLevel ? ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'][i] : '#4b5563',
                    fontWeight: i === currentLevel ? 700 : 400,
                  }}>{lvl}</span>
                ))}
                {currentLevel < 4 && (
                  <span style={{ color: '#9ca3af', marginLeft: '0.5rem' }}>
                    {currentLevel === 0 ? 'Define mission need to unlock Mission Architecture' :
                     currentLevel === 1 ? 'Run design to unlock System Architecture' :
                     currentLevel === 2 ? 'Select architecture options to unlock Subsystem Design' :
                     'Complete subsystem design to unlock V&V'}
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', gap: '0.2rem', padding: '0.4rem 1rem', borderBottom: '1px solid var(--border)', flexWrap: 'wrap', alignItems: 'center' }}>
                {visibleTabs.map((tab, i) => (
                  <span key={tab.id} style={{ display: 'contents' }}>
                    {tab.group && (
                      <span style={{
                        fontSize: '0.55rem', color: '#6b7280', textTransform: 'uppercase',
                        letterSpacing: '0.08em', marginLeft: i > 0 ? '0.5rem' : 0,
                        marginRight: '0.15rem', fontWeight: 700,
                      }}>{tab.group}</span>
                    )}
                    <button
                      onClick={() => setCenterTab(tab.id)}
                      style={{
                        background: centerTab === tab.id ? 'var(--accent)' : 'transparent',
                        color: centerTab === tab.id ? 'white' : 'var(--text-secondary)',
                        border: 'none', padding: '0.25rem 0.55rem', borderRadius: '4px',
                        cursor: 'pointer', fontSize: '0.68rem', fontWeight: 500,
                      }}
                    >{tab.label}</button>
                  </span>
                ))}
              </div>
              <DesignStateBar autoReconverge={autoReconverge} onToggleAuto={() => setAutoReconverge(a => !a)} />
              <div style={{ padding: '0 1rem', overflow: 'auto', flex: 1 }}>
                {centerTab === 'design' && <DesignWorkspace />}
                {centerTab === 'conops' && (
                  <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <MissionArchitectureEditor />
                    <ConOpsEditor />
                  </div>
                )}
                {centerTab === 'functions' && <FunctionTreeView />}
                {centerTab === 'reqs' && <RequirementsEditor studyId={studyId} />}
                {centerTab === 'architecture' && (
                  <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <div style={{ flex: '0 0 50%', overflow: 'auto' }}>
                      <SystemArchitectureEditor />
                    </div>
                    <div style={{ flex: '0 0 50%', borderTop: '2px solid var(--border, #374151)' }}>
                      <SystemBlockDiagram />
                    </div>
                  </div>
                )}
                {centerTab === 'interfaces' && <InterfaceMatrixView onNavigate={(tab) => setCenterTab(tab as CenterTab)} />}
                {centerTab === 'positions' && <PositionPanel />}
                {centerTab === 'answers' && <PositionAnswersPanel />}
                {centerTab === 'gate' && <GateReviewPanel studyId={studyId} onNavigate={(tab) => setCenterTab(tab as CenterTab)} />}
                {centerTab === 'compliance' && <ComplianceMatrix studyId={studyId} />}
                {centerTab === 'ecss' && <EcssCompliancePanel studyId={studyId} />}
                {centerTab === 'cost' && <CostBreakdown studyId={studyId} />}
                {centerTab === 'trade' && <TradeStudyPanel studyId={studyId} />}
                {centerTab === 'snapshots' && <SnapshotsPanel sessionId={sessionId} />}
                {centerTab === 'optimizer' && <OptimizerPanel sessionId={sessionId} />}
                {centerTab === 'exports' && <ExportsPanel studyId={studyId} />}
                {centerTab === 'budgets' && <EngineeringBudgets />}\n                {centerTab === 'pm' && <ProjectManagement />}
                {centerTab === 'linkbudget' && <LinkBudgetTool />}
                {centerTab === 'verification' && <VerificationMatrix studyId={studyId} />}
                {centerTab === 'parametric' && <ParametricEditor />}
                {centerTab === 'audit' && <ChangeAuditPanel />}
                {centerTab === 'help' && <UserManual />}
              </div>
            </>
          )}
        </div>

        {/* Right panel: only visible in design phase */}
        {(centerTab === 'design' || result) && !['need', 'concept', 'requirements'].includes(centerTab) && (
          <div className="panel">
            <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '0.75rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
              {(['insights', 'conflicts', 'exports'] as RightTab[]).map(tab => (
                <button key={tab} onClick={() => setRightTab(tab)}
                  style={{
                    background: rightTab === tab ? 'var(--accent)' : 'transparent',
                    color: rightTab === tab ? 'white' : 'var(--text-secondary)',
                    border: 'none', padding: '0.35rem 0.75rem', borderRadius: '4px',
                    cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600,
                    textTransform: 'uppercase', letterSpacing: '0.03em', position: 'relative',
                  }}>
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
            {rightTab === 'conflicts' && <><h2>Cross-Domain Conflicts</h2><ConflictsPanel /></>}
            {rightTab === 'exports' && (
              <div style={{ padding: '1rem' }}>
                <h3 style={{ marginBottom: '0.5rem' }}>Exports</h3>
                <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
                  All exports are consolidated in the center panel Exports tab.
                </p>
                <button className="btn" onClick={() => setCenterTab('exports')}
                  style={{ width: '100%', fontSize: '0.82rem' }}>
                  Open Exports Tab
                </button>
                <ExportPanel studyId={studyId} />
              </div>
            )}
          </div>
        )}
      </main>

      {/* Live toast notifications */}
      <LiveEditToast />

      {/* History drawer (edit audit trail) */}
      <HistoryDrawer sessionId={sessionId} />

      {/* Conflict review modal */}
      {showConflictReview && (
        <ConflictReviewModal onClose={() => setShowConflictReview(false)} />
      )}

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
            const c = POSITION_COLOR[p.id] || '#3b82f6'
            return (
              <label key={p.id} style={{
                display: 'flex', alignItems: 'center', gap: '0.3rem',
                fontSize: '0.78rem', padding: '0.25rem 0.6rem', borderRadius: '4px', cursor: 'pointer',
                background: active ? `${c}22` : 'transparent',
                border: `1px solid ${active ? c : 'var(--border, #374151)'}`,
                color: active ? c : 'var(--text-secondary, #9ca3af)',
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

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}
