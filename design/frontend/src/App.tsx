/**
 * SpaceCDF — Level Workbench
 *
 * Architecture designed from the System-V hierarchical decomposition process.
 * User works at the highest broken level, decomposes downward, escalates upward.
 *
 * Layout: LevelBar (top) → StatusBar → LevelWorkbench (main)
 * State: uiStore holds navigation only. All design content from server API.
 */
import { useState, useCallback } from 'react'
import { QueryClient, QueryClientProvider, useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useUIStore, type Level, type ActivityPanel } from './stores/uiStore'
import { LevelWorkbench } from './workbench/LevelWorkbench'
import { MissionWizard } from './workbench/MissionWizard'
import { ReadinessChecklist } from './workbench/ReadinessChecklist'
import { EscalationBanner } from './workbench/EscalationBanner'
import { ExportPanel } from './workbench/ExportPanel'
import { GuidancePanel } from './workbench/GuidancePanel'
import { PresenceBar } from './workbench/PresenceBar'
import { AIProvider, AIStatusIndicator } from './ai'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 2_000 } },
})

const API = '/api'

const LEVEL_LABELS: Record<Level, string> = {
  0: 'Mission',
  1: 'Systems',
  2: 'Subsystems',
  3: 'Equipment',
  4: 'V&V',
}

const LEVEL_COLORS: Record<Level, string> = {
  0: '#3b82f6',
  1: '#8b5cf6',
  2: '#06b6d4',
  3: '#10b981',
  4: '#f59e0b',
}

// ─── Study Creation Gate ───

function CreateStudyGate() {
  const setStudyId = useUIStore(s => s.setStudyId)
  const [name, setName] = useState('New Mission')
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    setCreating(true)
    try {
      const res = await fetch(`${API}/studies/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: { name }, mission_need: {} }),
      })
      if (res.ok) {
        const data = await res.json()
        setStudyId(data.id)
      }
    } finally {
      setCreating(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: '1.5rem', background: 'var(--bg-primary)' }}>
      <h1 style={{ fontSize: '1.8rem', color: 'var(--accent)', fontWeight: 700 }}>SpaceCDF</h1>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', maxWidth: 420, textAlign: 'center', lineHeight: 1.6 }}>
        Concurrent Design Facility for CubeSat missions.
        Create a study to start building your mission architecture.
      </p>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="Mission name"
          style={{
            padding: '0.5rem 0.75rem', fontSize: '0.85rem', borderRadius: '4px',
            background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)',
            width: 220,
          }}
        />
        <button onClick={handleCreate} disabled={creating} style={{
          padding: '0.5rem 1.5rem', fontSize: '0.85rem', fontWeight: 600, borderRadius: '4px',
          background: 'var(--accent)', color: 'white', border: 'none',
          cursor: creating ? 'wait' : 'pointer', opacity: creating ? 0.7 : 1,
        }}>
          {creating ? 'Creating...' : 'Create Study'}
        </button>
      </div>
    </div>
  )
}

// ─── Level Bar ───

function LevelBar() {
  const currentLevel = useUIStore(s => s.currentLevel)
  const breadcrumb = useUIStore(s => s.breadcrumb)
  const goToLevel = useUIStore(s => s.goToLevel)

  return (
    <div style={{
      display: 'flex', gap: '2px', padding: '0.4rem 1rem',
      background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)',
    }}>
      {([0, 1, 2, 3, 4] as Level[]).map(level => {
        const active = currentLevel === level
        const visited = level <= breadcrumb.length || level === 4  // V&V always accessible
        const color = LEVEL_COLORS[level]
        // Show breadcrumb context in the tab label
        const contextName = level > 0 && level <= breadcrumb.length
          ? ` (${breadcrumb[level - 1].name})`
          : ''
        return (
          <button
            key={level}
            onClick={() => visited && goToLevel(level)}
            style={{
              padding: '0.4rem 0.8rem', fontSize: '0.72rem', fontWeight: 600,
              borderRadius: '4px 4px 0 0', cursor: visited ? 'pointer' : 'default',
              background: active ? `${color}20` : 'transparent',
              color: active ? color : visited ? 'var(--text-secondary)' : '#374151',
              border: 'none',
              borderBottom: active ? `2px solid ${color}` : '2px solid transparent',
              opacity: visited ? 1 : 0.3,
              transition: 'all 0.15s',
            }}
          >
            {level}: {LEVEL_LABELS[level]}
            {contextName && <span style={{ fontWeight: 400, fontSize: '0.6rem', marginLeft: '0.2rem' }}>{contextName}</span>}
          </button>
        )
      })}
    </div>
  )
}

// ─── Status Bar ───

function StatusBar() {
  const studyId = useUIStore(s => s.studyId)
  const breadcrumb = useUIStore(s => s.breadcrumb)
  const drillUp = useUIStore(s => s.drillUp)
  const analysisRunning = useUIStore(s => s.analysisRunning)
  const setAnalysisRunning = useUIStore(s => s.setAnalysisRunning)
  const qc = useQueryClient()

  const runAnalysis = useCallback(async () => {
    if (!studyId || analysisRunning) return
    setAnalysisRunning(true)
    try {
      // First fetch current elements to build a requirements context
      const elements = await fetch(`${API}/studies/${studyId}/elements`).then(r => r.json())

      const res = await fetch(`${API}/design/quick-design`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: {}, mission_need: {} }),
      })
      if (res.ok) {
        const result = await res.json()
        const params = result.parameters || {}

        // Map agent parameters back to elements by domain
        // Parameter ID patterns:
        //   {domain}.mass_kg or {domain}.*_mass_kg → mass_kg on matching element
        //   {domain}.power_w or {domain}.*_power_w → power_avg_w
        //   {domain}.cost_keur or {domain}.*_cost_keur → cost_recurring_keur
        //   mass.dry_mass_kg → mission root element mass_kg
        //   cost.total_meur → mission root element cost (converted kEUR)

        // Build index: domain → ALL matching elements (systems, subsystems, components)
        const domainElements = new Map<string, any[]>()
        let missionRoot: any = null
        for (const el of elements) {
          if (!el.parent_id) missionRoot = el
          if (el.subsystem_domain) {
            const list = domainElements.get(el.subsystem_domain) || []
            list.push(el)
            domainElements.set(el.subsystem_domain, list)
          }
        }

        // Collect all patches: { id, field, value, version }
        const patches: { id: string; field: string; value: number; version: number }[] = []

        for (const [paramId, paramData] of Object.entries(params)) {
          const pv = paramData as any
          if (pv.value == null || typeof pv.value !== 'number') continue

          const dotIdx = paramId.indexOf('.')
          if (dotIdx < 0) continue
          const domain = paramId.slice(0, dotIdx)
          const propName = paramId.slice(dotIdx + 1)

          // Special case: mission-level aggregates
          if (domain === 'mass' && propName === 'dry_mass_kg' && missionRoot && missionRoot.mass_kg == null) {
            patches.push({ id: missionRoot.id, field: 'mass_kg', value: pv.value, version: missionRoot.version })
            continue
          }
          if (domain === 'cost' && propName === 'total_meur' && missionRoot && missionRoot.cost_recurring_keur == null) {
            patches.push({ id: missionRoot.id, field: 'cost_recurring_keur', value: pv.value * 1000, version: missionRoot.version })
            continue
          }

          // Determine which element field this parameter maps to
          let field: string | null = null
          if (propName.endsWith('mass_kg')) field = 'mass_kg'
          else if (propName.endsWith('power_w')) field = 'power_avg_w'
          else if (propName.endsWith('cost_keur')) field = 'cost_recurring_keur'

          if (!field) continue

          // Apply to ALL elements with matching domain where the field is null
          const matchingEls = domainElements.get(domain) || []
          for (const el of matchingEls) {
            if (el[field] == null) {
              patches.push({ id: el.id, field, value: pv.value, version: el.version })
            }
          }
        }

        // Deduplicate: if multiple params target the same element+field, keep the first
        const seen = new Set<string>()
        const uniquePatches = patches.filter(p => {
          const key = `${p.id}:${p.field}`
          if (seen.has(key)) return false
          seen.add(key)
          return true
        })

        // Apply all patches
        for (const p of uniquePatches) {
          await fetch(`${API}/elements/${p.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [p.field]: p.value, version: p.version }),
          }).catch(() => {})
        }

        qc.invalidateQueries({ queryKey: ['elements'] })
        qc.invalidateQueries({ queryKey: ['budget'] })
        qc.invalidateQueries({ queryKey: ['escalation'] })
      }
    } finally {
      setAnalysisRunning(false)
    }
  }, [studyId, analysisRunning, setAnalysisRunning, qc])

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '0.5rem',
      padding: '0.3rem 1rem',
      background: 'var(--bg-primary)', borderBottom: '1px solid var(--border)',
      fontSize: '0.75rem',
    }}>
      {/* Breadcrumb */}
      <button
        onClick={() => drillUp(-1)}
        style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600 }}
      >
        Mission
      </button>
      {breadcrumb.map((crumb, i) => (
        <span key={crumb.id} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <span style={{ color: 'var(--border)' }}>›</span>
          <button
            onClick={() => drillUp(i)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.75rem',
              color: i === breadcrumb.length - 1 ? 'var(--text-primary)' : 'var(--accent)',
              fontWeight: i === breadcrumb.length - 1 ? 600 : 400,
            }}
          >
            {crumb.name}
          </button>
        </span>
      ))}

      <span style={{ flex: 1 }} />

      {/* Run Analysis */}
      <button
        onClick={runAnalysis}
        disabled={analysisRunning}
        style={{
          padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600,
          background: analysisRunning ? 'var(--border)' : 'var(--success)',
          color: 'white', border: 'none',
          cursor: analysisRunning ? 'wait' : 'pointer',
        }}
      >
        {analysisRunning ? 'Analysing...' : 'Run Analysis'}
      </button>

      {/* Save */}
      <button
        onClick={async () => {
          if (!studyId) return
          try {
            const [elements, interfaces, requirements, allocations, study] = await Promise.all([
              fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
              fetch(`${API}/studies/${studyId}/interfaces`).then(r => r.json()),
              fetch(`${API}/requirements/tree?study_id=${studyId}`).then(r => r.json()),
              fetch(`${API}/studies/${studyId}/allocations`).then(r => r.ok ? r.json() : []),
              fetch(`${API}/studies/${studyId}`).then(r => r.ok ? r.json() : null),
            ])
            const { breadcrumb, currentLevel, focusElementId } = useUIStore.getState()
            const uiState = { breadcrumb, currentLevel, focusElementId }
            // Also save localStorage items (risk register, pugh matrix)
            const riskRegister = JSON.parse(localStorage.getItem(`spacecdf-risks-${studyId}`) || '[]')
            const pughMatrix = JSON.parse(localStorage.getItem('spacecdf-pugh') || '{}')
            const blob = new Blob([JSON.stringify({
              studyId, elements, interfaces, requirements, allocations,
              studyMetadata: study, uiState, riskRegister, pughMatrix,
            }, null, 2)], { type: 'application/json' })
            const a = document.createElement('a')
            a.href = URL.createObjectURL(blob)
            a.download = `spacecdf_${new Date().toISOString().slice(0, 10)}.json`
            a.click()
            URL.revokeObjectURL(a.href)
          } catch { alert('Save failed') }
        }}
        style={{
          padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600,
          background: 'var(--bg-card)', color: 'var(--text-secondary)', border: '1px solid var(--border)',
          cursor: 'pointer',
        }}
      >
        Save
      </button>

      {/* Load */}
      <button
        onClick={() => {
          const input = document.createElement('input')
          input.type = 'file'
          input.accept = '.json'
          input.onchange = async (e: any) => {
            const file = e.target.files?.[0]
            if (!file) return
            try {
              const text = await file.text()
              const data = JSON.parse(text)
              if (!data.elements || !Array.isArray(data.elements)) {
                alert('Invalid save file — no elements found')
                return
              }
              // Create a new study
              const studyRes = await fetch(`${API}/studies/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ requirements: { name: 'Loaded Mission' }, mission_need: {} }),
              })
              if (!studyRes.ok) { alert('Failed to create study'); return }
              const newStudy = await studyRes.json()
              const newStudyId = newStudy.id

              // Sort elements so parents are created before children
              const sorted: any[] = []
              const remaining = [...data.elements]
              const created = new Set<string>()
              const oldToNew = new Map<string, string>()

              // First pass: roots (no parent_id)
              while (remaining.length > 0) {
                const batch = remaining.filter((el: any) =>
                  !el.parent_id || created.has(el.parent_id)
                )
                if (batch.length === 0) {
                  // Circular or orphans — just add them
                  sorted.push(...remaining)
                  break
                }
                for (const el of batch) {
                  sorted.push(el)
                  created.add(el.id)
                  remaining.splice(remaining.indexOf(el), 1)
                }
              }

              // Create elements in order
              for (const el of sorted) {
                const body: any = {
                  name: el.name,
                  element_type: el.element_type,
                  segment: el.segment || 'space',
                  parent_id: el.parent_id ? (oldToNew.get(el.parent_id) || null) : null,
                  subsystem_domain: el.subsystem_domain || undefined,
                  mass_kg: el.mass_kg, power_avg_w: el.power_avg_w, power_peak_w: el.power_peak_w,
                  cost_recurring_keur: el.cost_recurring_keur, cost_nre_keur: el.cost_nre_keur,
                  trl: el.trl, manufacturer: el.manufacturer, kb_component_id: el.kb_component_id,
                  quantity: el.quantity || 1, margin_percent: el.margin_percent ?? 20,
                  description: el.description || '',
                  in_scope: el.in_scope ?? true, frozen: el.frozen ?? false,
                  diagram_x: el.diagram_x, diagram_y: el.diagram_y,
                  performance: el.performance,
                }
                const res = await fetch(`${API}/elements/?study_id=${newStudyId}`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(body),
                })
                if (res.ok) {
                  const created = await res.json()
                  oldToNew.set(el.id, created.id)
                }
              }

              // Create interfaces
              if (data.interfaces) {
                for (const iface of data.interfaces) {
                  const fromId = oldToNew.get(iface.from_element_id)
                  const toId = oldToNew.get(iface.to_element_id)
                  if (fromId && toId) {
                    await fetch(`${API}/interfaces/?study_id=${newStudyId}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        name: iface.name, interface_type: iface.interface_type,
                        direction: iface.direction || 'bidirectional',
                        from_element_id: fromId, to_element_id: toId,
                        diagram_label: iface.diagram_label,
                      }),
                    })
                  }
                }
              }

              // Create requirements
              if (data.requirements) {
                for (const req of data.requirements) {
                  const elementId = req.element_id ? oldToNew.get(req.element_id) : undefined
                  await fetch(`${API}/requirements/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      study_id: newStudyId,
                      element_id: elementId,
                      level: req.level || 'mission',
                      code: req.code, text: req.text, rationale: req.rationale,
                      verification_method: req.verification_method,
                      status: req.status || 'draft',
                    }),
                  })
                }
              }

              // Switch to the new study
              useUIStore.getState().setStudyId(newStudyId)
              useUIStore.getState().drillUp(-1)  // reset to root

              // Restore UI state if present
              if (data.uiState && data.uiState.breadcrumb) {
                const mappedBreadcrumb = data.uiState.breadcrumb
                  .map((crumb: { id: string; name: string }) => {
                    const newId = oldToNew.get(crumb.id)
                    return newId ? { id: newId, name: crumb.name } : null
                  })
                  .filter(Boolean) as Array<{ id: string; name: string }>

                if (mappedBreadcrumb.length > 0) {
                  // Replay drill-down from root to restore breadcrumb
                  for (const crumb of mappedBreadcrumb) {
                    useUIStore.getState().drillInto(crumb.id, crumb.name)
                  }
                }
              }

              qc.invalidateQueries()
            } catch (err) {
              alert('Load failed: ' + (err as Error).message)
            }
          }
          input.click()
        }}
        style={{
          padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600,
          background: 'var(--bg-card)', color: 'var(--text-secondary)', border: '1px solid var(--border)',
          cursor: 'pointer',
        }}
      >
        Load
      </button>

      {/* Export */}
      <button
        onClick={() => useUIStore.getState().setShowExport(true)}
        style={{
          padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600,
          background: 'var(--bg-card)', color: 'var(--text-secondary)', border: '1px solid var(--border)',
          cursor: 'pointer',
        }}
      >
        Export
      </button>

      {/* Guide */}
      <button
        onClick={() => useUIStore.getState().setShowGuide(true)}
        style={{
          padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600,
          background: 'var(--bg-card)', color: '#f59e0b', border: '1px solid #f59e0b40',
          cursor: 'pointer',
        }}
      >
        Guide
      </button>
    </div>
  )
}

// ─── App Shell ───

function NamePrompt() {
  const [name, setName] = useState('')
  const setUserName = useUIStore(s => s.setUserName)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-primary)', gap: '1rem' }}>
      <h1 style={{ fontSize: '1.5rem', color: '#8B0000', margin: 0 }}>SpaceCDF</h1>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Enter your name to join the design session</p>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Your name"
          autoFocus onKeyDown={e => e.key === 'Enter' && name && setUserName(name)}
          style={{ padding: '0.5rem 0.75rem', fontSize: '0.85rem', borderRadius: '4px', background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)', width: 200 }} />
        <button onClick={() => name && setUserName(name)} disabled={!name}
          style={{ padding: '0.5rem 1.5rem', fontSize: '0.85rem', fontWeight: 600, borderRadius: '4px', background: 'var(--accent)', color: 'white', border: 'none', cursor: 'pointer' }}>
          Join
        </button>
      </div>
    </div>
  )
}

function AppShell() {
  const studyId = useUIStore(s => s.studyId)
  const userName = useUIStore(s => s.userName)
  const showExport = useUIStore(s => s.showExport)
  const showGuide = useUIStore(s => s.showGuide)

  if (!userName) return <NamePrompt />
  if (!studyId) return <MissionWizard />

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <PresenceBar />
      <LevelBar />
      <StatusBar />
      <ReadinessChecklist />
      <EscalationBanner />
      <main style={{ flex: 1, overflow: 'hidden' }}>
        <LevelWorkbench />
      </main>
      {showExport && <ExportPanel onClose={() => useUIStore.getState().setShowExport(false)} />}
      {showGuide && <GuidancePanel onClose={() => useUIStore.getState().setShowGuide(false)} />}
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AIProvider>
        <AppShell />
      </AIProvider>
    </QueryClientProvider>
  )
}
