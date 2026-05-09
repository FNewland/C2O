/**
 * SpaceCDF — App Shell (v2: Phase-driven System-V architecture)
 *
 * 6 phases as primary navigation. Margin tower always visible.
 * Anyone can connect at any time. No role assignment in the tool.
 */
import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useDesignStore } from './stores/designStore'
import { useModelStore } from './stores/modelStore'
import { useSessionStore } from './stores/sessionStore'
import { Phase0Need } from './phases/Phase0Need'
import { Phase1MissionArch } from './phases/Phase1MissionArch'
import { Phase2SystemArch } from './phases/Phase2SystemArch'
import { Phase3SubsystemDesign } from './phases/Phase3SubsystemDesign'
import { Phase4Integration } from './phases/Phase4Integration'
import { Phase5Verification } from './phases/Phase5Verification'
import { BudgetCascade } from './charts/BudgetCascade'
import { PHASE_LABELS, PHASE_SHORT, PHASE_COLORS, type Phase } from './types/phases'
import { ErrorBoundary } from './components/ErrorBoundary'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 30000 } } })

function AppShell() {
  const [activePhase, setActivePhaseRaw] = useState<Phase>(0)
  const [prevPhase, setPrevPhase] = useState<Phase>(0)
  const [showReviewBanner, setShowReviewBanner] = useState<string | null>(null)
  const setActivePhase = (p: Phase) => {
    // Show review prompt when going to a lower phase from a higher one
    if (p < activePhase && activePhase >= 2) {
      const messages: Record<number, string> = {
        0: 'Returning to Mission Need — review objectives against design results',
        1: 'Returning to Mission Architecture — review architecture against system design',
        2: 'Returning to System Architecture — review budgets and interfaces against subsystem design',
      }
      setShowReviewBanner(messages[p] || null)
      setTimeout(() => setShowReviewBanner(null), 5000)
    }
    // Show forward completion prompt when advancing to next phase
    if (p > activePhase) {
      const fwdMessages: Record<number, string> = {
        1: 'Phase 0 complete — mission need defined. Now define the mission architecture.',
        2: 'Phase 1 complete — architecture defined. Now decompose into system-level design.',
        3: 'Phase 2 complete — system architecture set. Now select subsystem equipment.',
        4: 'Phase 3 complete — subsystems designed. Now verify interfaces and integration.',
        5: 'Phase 4 complete — integration verified. Final verification and validation.',
      }
      if (fwdMessages[p]) {
        setShowReviewBanner(fwdMessages[p])
        setTimeout(() => setShowReviewBanner(null), 4000)
      }
    }
    // SYSTEM-V: When entering Phase 1 for the first time, auto-create segment elements
    if (p === 1 && activePhase === 0) {
      const sid = useDesignStore.getState().studyId
      const ms = useModelStore.getState()
      if (sid && ms.elements.size === 0) {
        // Create mission root + standard segments
        const createEl = ms.createElement
        const missionName = useDesignStore.getState().missionNeed?.problem_statement?.slice(0, 40) || 'New Mission'
        createEl(sid, { name: missionName, element_type: 'mission', segment: 'space', diagram_x: 300, diagram_y: 10 } as any).then(missionId => {
          if (!missionId) return
          createEl(sid, { name: 'Space Segment', element_type: 'segment', segment: 'space', parent_id: missionId, diagram_x: 100, diagram_y: 100 } as any)
          createEl(sid, { name: 'Ground Segment', element_type: 'segment', segment: 'ground', parent_id: missionId, diagram_x: 300, diagram_y: 100 } as any)
          createEl(sid, { name: 'Launch Segment', element_type: 'segment', segment: 'space', parent_id: missionId, diagram_x: 500, diagram_y: 100 } as any)
          createEl(sid, { name: 'Operations', element_type: 'segment', segment: 'operations', parent_id: missionId, diagram_x: 300, diagram_y: 250 } as any)
        })
      }
    }

    setPrevPhase(activePhase)
    setActivePhaseRaw(p)
  }
  // SYSTEM-V: Reload element tree when phase changes or design completes
  const studyIdForReload = useDesignStore(s => s.studyId)
  const loadModel = useModelStore(s => s.loadStudyModel)
  useEffect(() => {
    if (studyIdForReload && activePhase >= 1) {
      loadModel(studyIdForReload)
    }
  }, [activePhase, studyIdForReload])
  // Also reload after design run completes (seeds the element tree)
  useEffect(() => {
    if (!isRunning && studyIdForReload && activePhase >= 1) {
      loadModel(studyIdForReload)
    }
  }, [isRunning])

  const missionNeed = useDesignStore(s => s.missionNeed)
  const result = useDesignStore(s => s.result)
  const archReqs = useDesignStore(s => s.architectureDerivedReqs)
  const error = useDesignStore(s => s.error)
  const isRunning = useDesignStore(s => s.isRunning)
  const designStale = useDesignStore(s => s.designStale)
  const runDesign = useDesignStore(s => s.runDesign)
  const requirements = useDesignStore(s => s.requirements)

  // Phase unlock + completion logic
  const hasNeed = !!(missionNeed?.problem_statement && missionNeed?.objectives?.length > 0)
  const hasDesign = !!result
  const hasArch = (archReqs?.length || 0) > 0
  const modelElements = useModelStore(s => s.elements)
  const selectedEquipmentCount = Array.from(modelElements.values()).filter(e => e.element_type === 'component').length
  const phaseCompletion = useDesignStore(s => s.phaseCompletion)
  const setPhaseComplete = useDesignStore(s => s.setPhaseComplete)

  const phaseUnlocked = (p: Phase): boolean => {
    if (p === 0) return true
    if (p === 1) return hasNeed
    if (p === 2) return hasDesign
    if (p === 3) return hasArch
    if (p === 4) return hasArch && hasDesign
    if (p === 5) return hasArch && hasDesign
    return false
  }

  // Auto-detect phase completion from state
  const isPhaseComplete = (p: Phase): boolean => {
    if (phaseCompletion[p]) return true // Manual override
    if (p === 0) return hasNeed
    if (p === 1) return hasDesign && hasArch
    if (p === 2) return hasArch && Array.from(modelElements.values()).some(e => e.element_type === 'subsystem')
    if (p === 3) return selectedEquipmentCount > 0
    if (p === 4) return false // Integration requires manual sign-off
    if (p === 5) return false // Verification requires manual sign-off
    return false
  }

  // Quick budget summary for margin tower
  const params = result?.parameters || {}
  const get = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : 0 }
  const massUsed = get('mass.dry_mass_kg')
  const massAlloc = requirements.target_mass_kg || 6
  const massMargin = massAlloc > 0 ? ((massAlloc - massUsed) / massAlloc * 100) : 0

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary, #0a0e1a)', color: '#d1d5db' }}>
      {/* Phase sidebar */}
      <nav style={{ width: '70px', background: '#111827', borderRight: '1px solid #374151', display: 'flex', flexDirection: 'column', padding: '0.5rem 0' }}>
        <div style={{ textAlign: 'center', fontSize: '0.6rem', fontWeight: 700, color: '#3b82f6', padding: '0.3rem', marginBottom: '0.5rem' }}>
          SCDF
        </div>
        {([0, 1, 2, 3, 4, 5] as Phase[]).map(p => {
          const unlocked = phaseUnlocked(p)
          const active = activePhase === p
          return (
            <button key={p} onClick={() => unlocked && setActivePhase(p)} style={{
              padding: '0.5rem 0.25rem', margin: '0.15rem 0.25rem', borderRadius: '6px', cursor: unlocked ? 'pointer' : 'not-allowed',
              background: active ? `${PHASE_COLORS[p]}20` : 'transparent',
              border: active ? `2px solid ${PHASE_COLORS[p]}` : '2px solid transparent',
              opacity: unlocked ? 1 : 0.35, transition: 'all 0.15s',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.15rem',
            }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: active ? PHASE_COLORS[p] : '#6b7280' }}>{p}</span>
              <span style={{ fontSize: '0.5rem', color: active ? PHASE_COLORS[p] : '#6b7280', lineHeight: 1.1, textAlign: 'center' }}>
                {PHASE_SHORT[p]}
              </span>
              {/* Phase completion indicator */}
              {unlocked && (
                <span style={{
                  width: 5, height: 5, borderRadius: '50%',
                  background: isPhaseComplete(p) ? '#10b981' : unlocked ? '#f59e0b' : '#374151',
                }} title={isPhaseComplete(p) ? 'Complete' : 'In progress'} />
              )}
            </button>
          )
        })}

        <div style={{ flex: 1 }} />

        {/* Run design button */}
        <button onClick={() => runDesign()} disabled={isRunning} style={{
          margin: '0.25rem', padding: '0.4rem', borderRadius: '6px', cursor: isRunning ? 'wait' : 'pointer',
          background: designStale ? '#f59e0b' : '#374151', color: designStale ? '#000' : '#9ca3af',
          border: 'none', fontSize: '0.55rem', fontWeight: 600,
        }}>
          {isRunning ? '...' : designStale ? 'Run' : 'OK'}
        </button>

        {/* Save / Load / New — Save highlights when design is stale */}
        <button onClick={() => {
          const state = useDesignStore.getState()
          // Include element tree snapshot for offline recovery
          const elements = Array.from(useModelStore.getState().elements.values())
          const interfaces = Array.from(useModelStore.getState().interfaces.values())
          const saveData = { ...state, _elementTreeSnapshot: { elements, interfaces } }
          const blob = new Blob([JSON.stringify(saveData, null, 2)], { type: 'application/json' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a'); a.href = url
          a.download = `spacecdf-${new Date().toISOString().slice(0, 10)}.json`
          a.click(); URL.revokeObjectURL(url)
        }} style={{ margin: '0.15rem 0.25rem', padding: '0.3rem', borderRadius: '4px', background: designStale ? '#f59e0b30' : '#1f2937', border: designStale ? '1px solid #f59e0b' : '1px solid transparent', color: designStale ? '#f59e0b' : '#6b7280', fontSize: '0.5rem', cursor: 'pointer' }}>
          Save
        </button>
        <button onClick={() => {
          const input = document.createElement('input'); input.type = 'file'; input.accept = '.json'
          input.onchange = (e: any) => {
            const file = e.target.files?.[0]; if (!file) return
            const reader = new FileReader()
            reader.onload = (ev) => {
              try {
                const data = JSON.parse(ev.target?.result as string)
                // Preserve studyId so element tree can reconnect
                const savedStudyId = data.studyId
                const treeSnapshot = data._elementTreeSnapshot
                delete data._elementTreeSnapshot
                useDesignStore.setState(data)
                // Reload element tree from backend if studyId exists
                if (savedStudyId) {
                  useModelStore.getState().loadStudyModel(savedStudyId).catch(() => {
                    // Backend unavailable — restore from snapshot if available
                    if (treeSnapshot?.elements?.length) {
                      const elMap = new Map()
                      for (const el of treeSnapshot.elements) elMap.set(el.id, el)
                      const ifMap = new Map()
                      for (const i of (treeSnapshot.interfaces || [])) ifMap.set(i.id, i)
                      useModelStore.setState({ elements: elMap, interfaces: ifMap })
                    }
                  })
                }
              } catch { alert('Invalid file') }
            }
            reader.readAsText(file)
          }
          input.click()
        }} style={{ margin: '0.15rem 0.25rem', padding: '0.3rem', borderRadius: '4px', background: '#1f2937', border: 'none', color: '#6b7280', fontSize: '0.5rem', cursor: 'pointer' }}>
          Load
        </button>
        <button onClick={() => {
          const id = prompt('Enter Study ID or Mission ID:')
          if (!id) return
          // Try to load from backend by study ID
          useDesignStore.setState({ studyId: id })
          useModelStore.getState().loadStudyModel(id).then(() => {
            // Check if we got elements
            if (useModelStore.getState().elements.size > 0) {
              setActivePhaseRaw(1 as Phase) // Jump to Phase 1 since we have data
            } else {
              alert('No elements found for that ID. Check the ID and try again.')
            }
          }).catch(() => {
            alert('Could not connect to backend. Check the ID and server status.')
          })
        }} style={{ margin: '0.15rem 0.25rem', padding: '0.3rem', borderRadius: '4px', background: '#1f2937', border: 'none', color: '#6b7280', fontSize: '0.5rem', cursor: 'pointer' }}>
          Open
        </button>
        <button onClick={() => {
          if (!confirm('Start new? Save first if needed.')) return
          localStorage.removeItem('spacecdf-design-state'); window.location.reload()
        }} style={{ margin: '0.15rem 0.25rem 0.5rem', padding: '0.3rem', borderRadius: '4px', background: '#1f2937', border: 'none', color: '#6b7280', fontSize: '0.5rem', cursor: 'pointer' }}>
          New
        </button>
      </nav>

      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header: title + margin tower */}
        <header style={{ padding: '0.3rem 1rem', borderBottom: '1px solid #374151', display: 'flex', alignItems: 'center', gap: '0.75rem', background: '#111827' }}>
          <h1 style={{ fontSize: '0.9rem', margin: 0, color: '#d1d5db' }}>SpaceCDF</h1>
          <span style={{ fontSize: '0.65rem', color: '#6b7280' }}>{PHASE_LABELS[activePhase]}</span>
          {/* Prominent Run Design button */}
          <button onClick={() => runDesign()} disabled={isRunning} style={{
            padding: '0.25rem 0.75rem', borderRadius: '4px', cursor: isRunning ? 'wait' : 'pointer',
            background: designStale ? '#f59e0b' : isRunning ? '#374151' : '#10b981',
            color: designStale ? '#000' : 'white', border: 'none',
            fontSize: '0.72rem', fontWeight: 600,
          }}>
            {isRunning ? 'Running...' : designStale ? '▶ Run Design' : '✓ Design Current'}
          </button>
          <span style={{ fontSize: '0.6rem', color: '#6b7280', fontFamily: 'monospace' }}
            title="Unique mission identifier — used in requirement numbering and document references">
            {useDesignStore.getState().missionId}
          </span>
          <span style={{ flex: 1 }} />
          {/* Compact margin indicators — only show at system level and above with meaningful values */}
          {result && get('mass.dry_mass_kg') > 0 && activePhase >= 2 && (
            <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.65rem' }}>
              <span style={{ color: massMargin > 20 ? '#10b981' : massMargin > 0 ? '#f59e0b' : '#ef4444' }}>
                Mass: {massMargin.toFixed(0)}%
              </span>
              <span style={{ color: get('power.sa_power_eol_w') > get('power.total_sunlight_w') ? '#10b981' : '#ef4444' }}>
                Power: {get('power.sa_power_eol_w') > 0 ? ((get('power.sa_power_eol_w') - get('power.total_sunlight_w')) / get('power.sa_power_eol_w') * 100).toFixed(0) : '—'}%
              </span>
              <span style={{ color: get('link.ttc_margin_db') >= 3 ? '#10b981' : '#ef4444' }}>
                TTC: {get('link.ttc_margin_db').toFixed(0)}dB
              </span>
            </div>
          )}
        </header>

        {/* Error banner */}
        {error && (
          <div style={{ padding: '0.3rem 1rem', background: 'rgba(239,68,68,0.15)', borderBottom: '1px solid #ef4444', fontSize: '0.72rem', color: '#ef4444', display: 'flex', alignItems: 'center' }}>
            {error}
            <button onClick={() => useDesignStore.setState({ error: null })} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}>×</button>
          </div>
        )}

        {/* Review prompt banner (shown when navigating back to earlier phases) */}
        {showReviewBanner && (
          <div style={{ padding: '0.3rem 1rem', background: 'rgba(59,130,246,0.15)', borderBottom: '1px solid #3b82f6', fontSize: '0.72rem', color: '#93c5fd', display: 'flex', alignItems: 'center' }}>
            <span style={{ fontWeight: 600, marginRight: '0.3rem' }}>Review:</span> {showReviewBanner}
            <button onClick={() => setShowReviewBanner(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer' }}>×</button>
          </div>
        )}

        {/* Phase content — each wrapped in error boundary for resilience */}
        <main style={{ flex: 1, overflow: 'hidden' }}>
          <ErrorBoundary phaseName={PHASE_LABELS[activePhase]} key={activePhase}>
            {activePhase === 0 && <Phase0Need />}
            {activePhase === 1 && <Phase1MissionArch />}
            {activePhase === 2 && <Phase2SystemArch />}
            {activePhase === 3 && <Phase3SubsystemDesign />}
            {activePhase === 4 && <Phase4Integration />}
            {activePhase === 5 && <Phase5Verification />}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppShell />
    </QueryClientProvider>
  )
}
