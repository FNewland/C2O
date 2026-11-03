/**
 * SpaceCDF — Level Workbench
 *
 * Architecture designed from the System-V hierarchical decomposition process.
 * User works at the highest broken level, decomposes downward, escalates upward.
 *
 * Layout: LevelBar (top) → StatusBar → LevelWorkbench (main)
 * State: uiStore holds navigation only. All design content from server API.
 */
import { useState, useCallback, useEffect } from 'react'
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query'
import { useUIStore, type Level } from './stores/uiStore'
import { LevelWorkbench } from './workbench/LevelWorkbench'
import { MissionWizard } from './workbench/MissionWizard'
import { ReadinessChecklist } from './workbench/ReadinessChecklist'
import { EscalationBanner } from './workbench/EscalationBanner'
import { ExportPanel } from './workbench/ExportPanel'
import { GuidancePanel } from './workbench/GuidancePanel'
import { PresenceBar } from './workbench/PresenceBar'
import { MarginTower } from './components/MarginTower'
import { AIProvider } from './ai'
import { useTranslation } from 'react-i18next'
import i18n from './i18n'
import { LanguageToggle } from './i18n/LanguageToggle'
import { DialogHost, showAlert } from './components/ui/Dialog'
import { HomeFrame } from './components/ui/HomeFrame'
import { ThemeToggle } from './components/ui/ThemeToggle'
import { LogbookBanner, LogbookButton, LogbookRoot } from './logbook'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 2_000 } },
})

const API = '/api'

// ECSS product-tree names (ECSS-M-ST-10C): Mission → Segment → System/Element →
// Subsystem → Equipment. A tab is named after what it shows: the element type
// of the blocks at that level, falling back to the next name down the tree.
// English text is the i18n key; translate at render time with t().
const PRODUCT_TREE = ['Mission', 'Segment', 'System / element', 'Subsystem', 'Equipment'] as const
const TYPE_TO_TREE: Record<string, number> = { mission: 0, segment: 1, system: 2, subsystem: 3, component: 4, equipment: 4 }

function useLevelNames(): string[] {
  const studyId = useUIStore(s => s.studyId)
  const breadcrumb = useUIStore(s => s.breadcrumb)
  const { data: elements = [] } = useQuery<any[]>({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId,
  })
  const names: string[] = []
  let prev = -1
  for (let level = 0; level < 4; level++) {
    let idx = -1
    if (level <= breadcrumb.length) {
      const parent = level === 0 ? null : breadcrumb[level - 1].id
      const shown = Array.isArray(elements) ? elements.filter((el: any) => (parent ? el.parent_id === parent : !el.parent_id)) : []
      const counts = new Map<number, number>()
      for (const el of shown) {
        const k = TYPE_TO_TREE[el.element_type]
        if (k != null) counts.set(k, (counts.get(k) || 0) + 1)
      }
      if (counts.size) idx = [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0]
    }
    if (idx < 0) idx = Math.min(Math.max(prev + 1, level), PRODUCT_TREE.length - 1)
    names.push(PRODUCT_TREE[idx])
    prev = idx
  }
  return names
}

// ─── Level Bar ───

function LevelBar() {
  const { t } = useTranslation()
  const currentLevel = useUIStore(s => s.currentLevel)
  const breadcrumb = useUIStore(s => s.breadcrumb)
  const goToLevel = useUIStore(s => s.goToLevel)
  const names = useLevelNames()

  return (
    <div role="tablist" aria-label={t('Product tree level')} className="c2o-tabs c2o-appbar__levels">
      {([0, 1, 2, 3, 4] as Level[]).map(level => {
        const active = currentLevel === level
        const reachable = level <= breadcrumb.length || level === 4  // V&V always accessible
        const label = level === 4 ? t('V&V') : t(names[level])
        const context = level > 0 && level < 4 && level <= breadcrumb.length ? breadcrumb[level - 1].name : ''
        const reason = reachable ? undefined
          : t('Double-click a block at level {{n}} to open this level', { n: level - 1 })
        return (
          <button
            key={level}
            type="button"
            role="tab"
            className="c2o-tab"
            aria-selected={active}
            aria-disabled={!reachable || undefined}
            data-reason={reason}
            onClick={() => reachable && goToLevel(level)}
          >
            {level < 4 && <span className="c2o-tab__num">{level}</span>}
            <span>{label}</span>
            {context && <span className="c2o-tab__ctx">{t('in {{name}}', { name: context })}</span>}
            {reason && <span className="sr-only">{reason}</span>}
          </button>
        )
      })}
    </div>
  )
}

// ─── Status Bar ───

function StatusBar() {
  const { t } = useTranslation()
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
    <div className="c2o-contextbar">
      {/* Breadcrumb */}
      <nav aria-label={t('Breadcrumb')} className="c2o-crumbs">
        <button type="button" className="c2o-crumb" onClick={() => drillUp(-1)}
          aria-current={breadcrumb.length === 0 ? 'page' : undefined}>
          {t('Top level')}
        </button>
        {breadcrumb.map((crumb, i) => {
          const last = i === breadcrumb.length - 1
          return (
            <span key={crumb.id} className="iflex ai-c gap-1 min0">
              <span aria-hidden="true" className="c-3">/</span>
              <button type="button" className="c2o-crumb" onClick={() => drillUp(i)}
                aria-current={last ? 'page' : undefined}>
                {crumb.name}
              </button>
            </span>
          )
        })}
      </nav>

      <ReadinessChecklist />
      <EscalationBanner />

      <span className="grow" />

      <div className="c2o-contextbar__actions">
      {/* Run Analysis */}
      <button
        type="button"
        className={analysisRunning ? 'c2o-btn c2o-btn--active' : 'c2o-btn c2o-btn--primary'}
        onClick={runAnalysis}
        aria-disabled={analysisRunning || undefined}
        aria-busy={analysisRunning}
        title={analysisRunning ? t('Analysis is running') : t('Fill empty mass, power and cost values from the design agents')}
      >
        {analysisRunning ? t('Analysing...') : t('Run Analysis')}
      </button>
      <span className="c2o-contextbar__sep" aria-hidden="true" />

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
          } catch { void showAlert(i18n.t('Save failed')) }
        }}
        type="button"
        className="c2o-btn"
      >
        {t('Save')}
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
                void showAlert(i18n.t('Invalid save file — no elements found'))
                return
              }
              // Create a new study
              const studyRes = await fetch(`${API}/studies/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ requirements: { name: 'Loaded Mission' }, mission_need: {} }),
              })
              if (!studyRes.ok) { void showAlert(i18n.t('Failed to create study')); return }
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
              void showAlert(i18n.t('Load failed: {{message}}', { message: (err as Error).message }))
            }
          }
          input.click()
        }}
        type="button"
        className="c2o-btn"
      >
        {t('Load')}
      </button>

      {/* Export */}
      <button
        onClick={() => useUIStore.getState().setShowExport(true)}
        type="button"
        className="c2o-btn"
      >
        {t('Export')}
      </button>

      {/* Guide */}
      <button
        onClick={() => useUIStore.getState().setShowGuide(true)}
        type="button"
        className="c2o-btn"
      >
        {t('Guide')}
      </button>

      {/* Close study: back to the start screen (the logbook offers its download) */}
      <button
        onClick={() => { useUIStore.getState().drillUp(-1); useUIStore.getState().setStudyId(null) }}
        type="button"
        className="c2o-btn c2o-btn--quiet"
        title={t('Leave this study and go back to the start screen. The study stays on the server.')}
      >
        {t('Close study')}
      </button>

      </div>
    </div>
  )
}

// ─── App Shell ───

function NamePrompt() {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const setUserName = useUIStore(s => s.setUserName)
  const trimmed = name.trim()
  // On c2o.live the sign-in already knows who this is: offer that name.
  useEffect(() => {
    let live = true
    fetch('/api/whoami').then(r => (r.ok ? r.json() : null)).then(d => {
      if (live && d && d.name) setName(n => n || d.name)
    }).catch(() => { /* local run: no sign-in, type a name */ })
    return () => { live = false }
  }, [])
  return (
    <>
      <HomeFrame title={t('Join the design session')} lead={t('Your name is shown to everyone working in the same study.')}>
        <form
          onSubmit={e => { e.preventDefault(); if (trimmed) setUserName(trimmed) }}
          className="flex wrap ai-e gap-2 c2o-name-form"
        >
          <label className="c2o-field c2o-name-form__field">
            <span className="c2o-field__label">{t('Your name')}</span>
            <input className="c2o-input" value={name} onChange={e => setName(e.target.value)} autoFocus autoComplete="name" />
          </label>
          <button type="submit" className="c2o-btn c2o-btn--primary c2o-btn--tall"
            aria-disabled={!trimmed || undefined} data-reason={!trimmed ? t('Enter a name first') : undefined}>
            {t('Join')}
          </button>
        </form>
      </HomeFrame>
    </>
  )
}

function AppShell() {
  const studyId = useUIStore(s => s.studyId)
  const userName = useUIStore(s => s.userName)

  if (!userName) return <><NamePrompt /><DialogHost /></>

  // One LogbookRoot for the wizard and the workbench, so it sees the study
  // being closed (it offers the logbook download then).
  return (
    <>
      {studyId ? <Workbench /> : <MissionWizard />}
      <LogbookRoot />
      <DialogHost />
    </>
  )
}

function Workbench() {
  const showExport = useUIStore(s => s.showExport)
  const showGuide = useUIStore(s => s.showGuide)
  return (
    <div className="c2o-shell">
      <header className="c2o-appbar">
        <span className="c2o-appbar__mark">SpaceCDF</span>
        <LevelBar />
        <div className="c2o-appbar__end">
          <PresenceBar />
          <LogbookButton />
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </header>
      <LogbookBanner />
      <StatusBar />
      <MarginTower />
      <main className="c2o-shell__main">
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
