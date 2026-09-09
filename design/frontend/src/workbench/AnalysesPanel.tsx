/**
 * AnalysesPanel — the workbench "Analyses" tab (SCDF-178, design SCDF-170 §3).
 *
 * A card per engineering analysis (Design loop, Mission simulation, Ground
 * segment, Physics, V&V, FMECA) built from `GET /studies/{id}/analyses`
 * (last run per analysis with `stale`): last run time, status / stale badge,
 * 2–3 headline metrics from the run summary and a Run button. Clicking a
 * card opens its panel below. An "Options" section hosts `OptionCompare`.
 *
 * All requests carry `?option_id=` from optionStore (baseline sends none).
 *
 *   GET  /api/studies/{id}/analyses?option_id=
 *   POST /api/design/{id}/run?option_id=                        (design loop)
 *   POST /api/studies/{id}/analyses/{analysis}/run?option_id=   (the closures)
 *   GET  /api/studies/{id}/conflicts?option_id=                 (open conflict counts per card)
 */
import { useState, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'
import { useActiveOptionId, optionQuery } from '../stores/optionStore'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { MissionSimulationPanel } from '../components/MissionSimulationPanel'
import { GroundSegmentPanel } from '../components/GroundSegmentPanel'
import { PhysicsClosurePanel } from '../components/PhysicsClosurePanel'
import { VVPlanPanel } from '../components/VVPlanPanel'
import { FMECAPanel } from '../components/FMECAPanel'
import { OptionCompare } from '../components/OptionCompare'
import { ConflictsPanel } from '../components/ConflictsPanel'
import { BudgetPanel } from './BudgetPanel'
import type { AnalysisRun, AnalysisConflict } from '../types/analyses'

const API = '/api'

export type AnalysisId = 'design_loop' | 'mission_simulation' | 'ground_segment' | 'physics' | 'vv' | 'fmeca'

interface Metric { label: string; value: string; tone?: string }

interface CardDef {
  id: AnalysisId
  label: string
  color: string
  /** what the analysis needs from the model to be meaningful */
  needs: string
  /** POST target for the run button */
  runUrl: (studyId: string, opt: string) => string
  runBody?: unknown
  metrics: (summary: Record<string, any>) => Metric[]
}

function fmt(v: unknown, digits = 1): string {
  if (typeof v !== 'number' || Number.isNaN(v)) return '—'
  return Number.isInteger(v) ? String(v) : v.toFixed(digits)
}
function tone(ok: boolean | null): string | undefined {
  return ok === null ? undefined : ok ? '#10b981' : '#ef4444'
}

export const ANALYSIS_CARDS: CardDef[] = [
  {
    id: 'design_loop', label: 'Design loop', color: '#f59e0b',
    needs: 'Mission root with requirements (orbit, payload, lifetime); subsystems by domain.',
    runUrl: (s, opt) => `${API}/design/${s}/run${opt}`,
    runBody: { max_iterations: 50, convergence_threshold: 0.001 },
    metrics: s => [
      { label: 'converged', value: s.converged === undefined ? '—' : s.converged ? 'yes' : 'no', tone: tone(s.converged === undefined ? null : !!s.converged) },
      { label: 'iterations', value: fmt(s.iterations) },
      { label: 'conflicts', value: fmt(s.conflicts), tone: tone(typeof s.conflicts === 'number' ? s.conflicts === 0 : null) },
    ],
  },
  {
    id: 'mission_simulation', label: 'Mission simulation', color: '#3b82f6',
    needs: 'Operational modes (power, data rate, payload on/off), battery capacity_wh, solar array EOL power, orbit.',
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/mission_simulation/run${opt}`,
    metrics: s => [
      { label: 'min SoC', value: `${fmt(s.min_soc_pct ?? s.sim_min_soc_pct)} %`, tone: tone(typeof (s.min_soc_pct ?? s.sim_min_soc_pct) === 'number' ? (s.min_soc_pct ?? s.sim_min_soc_pct) >= 20 : null) },
      { label: 'energy/orbit', value: `${fmt(s.energy_balance_wh_per_orbit ?? s.sim_energy_balance_wh_per_orbit)} Wh`, tone: tone(typeof (s.energy_balance_wh_per_orbit ?? s.sim_energy_balance_wh_per_orbit) === 'number' ? (s.energy_balance_wh_per_orbit ?? s.sim_energy_balance_wh_per_orbit) >= 0 : null) },
      { label: 'backlog', value: `${fmt(s.data_backlog_end_gb ?? s.sim_data_backlog_end_gb, 2)} GB` },
    ],
  },
  {
    id: 'ground_segment', label: 'Ground segment', color: '#10b981',
    needs: 'At least one selected ground station (ground segment element), TT&C band / data rate, orbit, payload data rate.',
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/ground_segment/run${opt}`,
    metrics: s => [
      { label: 'contact', value: `${fmt(s.gs_contact_min_per_day)} min/d` },
      { label: 'returned', value: `${fmt(s.gs_data_return_gb_per_day, 2)} / ${fmt(s.gs_data_generated_gb_per_day, 2)} GB/d`, tone: tone(typeof s.gs_data_return_gb_per_day === 'number' && typeof s.gs_data_generated_gb_per_day === 'number' ? s.gs_data_return_gb_per_day >= s.gs_data_generated_gb_per_day : null) },
      { label: 'stations', value: fmt(s.gs_station_count) },
    ],
  },
  {
    id: 'physics', label: 'Physics (mass / AOCS / thermal)', color: '#8b5cf6',
    needs: 'Component masses and dimensions, body positions (or auto-placement in a structure envelope), a reaction wheel, pointing requirement, dissipations.',
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/physics/run${opt}`,
    metrics: s => [
      { label: 'mass', value: `${fmt(s.mp_total_mass_kg, 2)} kg` },
      { label: 'wheel margin', value: `${fmt(s.aocs_wheel_margin_pct)} %`, tone: tone(typeof s.aocs_wheel_margin_pct === 'number' ? s.aocs_wheel_margin_pct >= 0 : null) },
      { label: 'thermal margin', value: `${fmt(s.thermal_worst_margin_c)} °C`, tone: tone(typeof s.thermal_worst_margin_c === 'number' ? s.thermal_worst_margin_c >= 0 : null) },
    ],
  },
  {
    id: 'vv', label: 'V&V', color: '#14b8a6',
    needs: 'Requirements with verification method / threshold parameters; analysis runs close threshold items automatically.',
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/vv/run${opt}`,
    metrics: s => [
      { label: 'closure', value: `${fmt(s.vv_closure_pct)} %` },
      { label: 'passed', value: `${fmt(s.vv_items_passed)} / ${fmt(s.vv_items_total)}` },
      { label: 'failed', value: fmt(s.vv_items_failed), tone: tone(typeof s.vv_items_failed === 'number' ? s.vv_items_failed === 0 : null) },
    ],
  },
  {
    id: 'fmeca', label: 'FMECA', color: '#ec4899',
    needs: 'Component elements with domain, quantity / redundancy, and functions allocated (critical functions drive single-point findings).',
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/fmeca/run${opt}`,
    runBody: { critical: [] },
    metrics: s => [
      { label: 'modes', value: fmt(s.fmeca_modes ?? s.modes) },
      { label: 'max RPN', value: fmt(s.fmeca_max_rpn) },
      { label: 'single points', value: fmt(s.fmeca_single_point_failures), tone: tone(typeof s.fmeca_single_point_failures === 'number' ? s.fmeca_single_point_failures === 0 : null) },
    ],
  },
]

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    let msg = `${res.status}`
    try { const b = await res.json(); msg = typeof b.detail === 'string' ? b.detail : JSON.stringify(b.detail ?? b) } catch { /* noop */ }
    throw new Error(msg)
  }
  return res.json()
}

function ago(iso: string | null | undefined): string {
  if (!iso) return 'never run'
  const s = (Date.now() - new Date(iso).getTime()) / 1000
  if (!Number.isFinite(s)) return ''
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.floor(s / 60)} min ago`
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`
  return `${Math.floor(s / 86400)} d ago`
}

function Badge({ text, color, title }: { text: string; color: string; title?: string }) {
  return (
    <span title={title} style={{ fontSize: '0.56rem', padding: '0 0.35rem', borderRadius: 3, background: `${color}22`, color, border: `1px solid ${color}55`, whiteSpace: 'nowrap' }}>
      {text}
    </span>
  )
}

/** Query keys every analysis run touches. */
export function invalidateAnalysisQueries(qc: ReturnType<typeof useQueryClient>, studyId: string | null) {
  for (const key of ['analyses', 'analysis', 'conflicts', 'study-parameters', 'element-parameters', 'parameters', 'verification-items', 'physics-placement', 'option-compare', 'elements', 'element-tree', 'budget', 'escalation']) {
    qc.invalidateQueries({ queryKey: [key, studyId] })
    qc.invalidateQueries({ queryKey: [key] })
  }
}

export function useAnalysisRuns(studyId: string | null, optionId: string | null) {
  const opt = optionQuery(optionId)
  return useQuery<AnalysisRun[]>({
    queryKey: ['analyses', studyId, optionId ?? null],
    queryFn: () => fetch(`${API}/studies/${studyId}/analyses${opt}`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })
}

function AnalysisCard({ def, run, openConflicts, active, onOpen, studyId, optionId }: {
  def: CardDef; run: AnalysisRun | undefined; openConflicts: number; active: boolean; onOpen: () => void
  studyId: string; optionId: string | null
}) {
  const qc = useQueryClient()
  const setAnalysisRunning = useUIStore(s => s.setAnalysisRunning)
  const [error, setError] = useState<string | null>(null)
  const opt = optionQuery(optionId)

  const runMut = useMutation({
    mutationFn: () => fetch(def.runUrl(studyId, opt), {
      method: 'POST',
      headers: def.runBody ? { 'Content-Type': 'application/json' } : undefined,
      body: def.runBody ? JSON.stringify(def.runBody) : undefined,
    }).then(jsonOrThrow),
    onMutate: () => { setError(null); if (def.id === 'design_loop') setAnalysisRunning(true) },
    onSuccess: () => invalidateAnalysisQueries(qc, studyId),
    onError: (e: Error) => { setError(e.message); invalidateAnalysisQueries(qc, studyId) },
    onSettled: () => { if (def.id === 'design_loop') setAnalysisRunning(false) },
  })

  const summary = run?.summary || {}
  const metrics = run ? def.metrics(summary) : []
  const status = runMut.isPending || run?.status === 'running' ? 'running' : run?.status
  const running = status === 'running'

  return (
    <div
      onClick={onOpen}
      style={{
        cursor: 'pointer', borderRadius: 6, padding: '0.45rem 0.6rem', minWidth: 190, flex: '1 1 210px',
        background: active ? `${def.color}14` : 'var(--bg-card)',
        border: `1px solid ${active ? def.color : 'var(--border)'}`, borderLeft: `4px solid ${def.color}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.25rem' }}>
        <span style={{ fontSize: '0.74rem', fontWeight: 600, color: def.color }}>{def.label}</span>
        <span style={{ flex: 1 }} />
        {run?.stale && <Badge text="stale" color="#f59e0b" title="Inputs changed since this run" />}
        {status === 'failed' && <Badge text="failed" color="#ef4444" title={summary.error} />}
        {running && <Badge text="running" color="#3b82f6" />}
        {status === 'ok' && !run?.stale && <Badge text="ok" color="#10b981" />}
        {openConflicts > 0 && <Badge text={`${openConflicts} conflict${openConflicts === 1 ? '' : 's'}`} color="#f97316" />}
      </div>
      <div style={{ fontSize: '0.58rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }} title={run?.finished_at || run?.started_at || ''}>
        {run ? `last run ${ago(run.finished_at || run.started_at)}` : optionId ? 'never run in this option' : 'never run'}
      </div>
      {metrics.length > 0 ? (
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.3rem' }}>
          {metrics.map(m => (
            <div key={m.label} style={{ minWidth: 50 }}>
              <div style={{ fontSize: '0.52rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>{m.label}</div>
              <div style={{ fontSize: '0.74rem', fontWeight: 600, fontFamily: 'ui-monospace, monospace', color: m.tone || 'var(--text-primary)' }}>{m.value}</div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ fontSize: '0.56rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', fontStyle: 'italic' }} title={def.needs}>
          needs: {def.needs}
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <button
          onClick={e => { e.stopPropagation(); if (!running) runMut.mutate() }}
          disabled={running}
          style={{
            cursor: running ? 'wait' : 'pointer', fontSize: '0.62rem', padding: '0.15rem 0.55rem', borderRadius: 4,
            border: `1px solid ${def.color}`, background: `${def.color}22`, color: def.color, fontWeight: 600,
          }}
        >
          {running ? 'Running…' : run ? 'Re-run' : 'Run'}
        </button>
        {error && <span style={{ fontSize: '0.58rem', color: '#ef4444' }} title={error}>{error.slice(0, 80)}</span>}
      </div>
    </div>
  )
}

function Section({ title, color, children }: { title: string; color: string; children: ReactNode }) {
  return (
    <div style={{ marginTop: '0.6rem', borderTop: '1px solid var(--border)', paddingTop: '0.4rem' }}>
      <div style={{ fontSize: '0.66rem', fontWeight: 600, color, marginBottom: '0.35rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{title}</div>
      {children}
    </div>
  )
}

export function AnalysesPanel() {
  const studyId = useUIStore(s => s.studyId)
  const optionId = useActiveOptionId(studyId)
  const [open, setOpen] = useState<AnalysisId | null>(null)
  const [showCompare, setShowCompare] = useState(false)
  const opt = optionQuery(optionId)

  const { data: runs = [], error: runsError } = useAnalysisRuns(studyId, optionId)
  const { data: conflicts } = useQuery<{ design: AnalysisConflict[]; analysis: AnalysisConflict[] }>({
    queryKey: ['conflicts', studyId, optionId ?? null],
    queryFn: () => fetch(`${API}/studies/${studyId}/conflicts${opt}`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })

  if (!studyId) return <div style={{ padding: '0.75rem', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Select a study.</div>

  const byAnalysis = new Map(runs.map(r => [r.analysis, r]))
  const openByAnalysis = new Map<string, number>()
  for (const c of [...(conflicts?.design || []), ...(conflicts?.analysis || [])]) {
    if (c.resolved) continue
    openByAnalysis.set(c.analysis, (openByAnalysis.get(c.analysis) || 0) + 1)
  }
  const openDef = ANALYSIS_CARDS.find(d => d.id === open)

  return (
    <div style={{ padding: '0.5rem 0.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
        <span style={{ fontSize: '0.66rem', color: 'var(--text-secondary)' }}>
          Engineering analyses for this study{optionId ? ' (active option)' : ' (baseline)'} — click a card to open it; Run posts to the analysis and refreshes parameters, conflicts and margins.
        </span>
        <span style={{ flex: 1 }} />
        <button onClick={() => setShowCompare(v => !v)} style={{ cursor: 'pointer', fontSize: '0.62rem', padding: '0.15rem 0.55rem', borderRadius: 4, border: '1px solid var(--border)', background: showCompare ? '#f59e0b22' : 'none', color: showCompare ? '#f59e0b' : 'var(--text-secondary)' }}>
          Options {showCompare ? '▾' : '▸'}
        </button>
      </div>
      {runsError && <div style={{ fontSize: '0.62rem', color: '#ef4444', marginBottom: '0.3rem' }}>analyses: {(runsError as Error).message}</div>}

      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {ANALYSIS_CARDS.map(def => (
          <AnalysisCard
            key={def.id} def={def} run={byAnalysis.get(def.id)} openConflicts={openByAnalysis.get(def.id) || 0}
            active={open === def.id} onOpen={() => setOpen(o => (o === def.id ? null : def.id))}
            studyId={studyId} optionId={optionId}
          />
        ))}
      </div>

      {showCompare && (
        <Section title="Options" color="#f59e0b">
          <ErrorBoundary phaseName="Option compare"><OptionCompare studyId={studyId} /></ErrorBoundary>
        </Section>
      )}

      {openDef && (
        <Section title={openDef.label} color={openDef.color}>
          <ErrorBoundary phaseName={openDef.label}>
            {open === 'design_loop' && (
              <div>
                <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                  Budgets after the last design loop (mission root or the focused element). Cross-domain conflicts from the loop are listed under Conflicts below.
                </div>
                <BudgetPanel />
                <div style={{ marginTop: '0.5rem' }}><ConflictsPanel studyId={studyId} optionId={optionId} analysisFilter="design_loop" /></div>
              </div>
            )}
            {open === 'mission_simulation' && <MissionSimulationPanel studyId={studyId} optionId={optionId} />}
            {open === 'ground_segment' && <GroundSegmentPanel studyId={studyId} optionId={optionId} />}
            {open === 'physics' && <PhysicsClosurePanel studyId={studyId} optionId={optionId} />}
            {open === 'vv' && <VVPlanPanel studyId={studyId} optionId={optionId} />}
            {open === 'fmeca' && <FMECAPanel studyId={studyId} optionId={optionId} />}
          </ErrorBoundary>
        </Section>
      )}

      <Section title="Conflicts" color="#f97316">
        <ErrorBoundary phaseName="Conflicts"><ConflictsPanel studyId={studyId} optionId={optionId} /></ErrorBoundary>
      </Section>
    </div>
  )
}

export default AnalysesPanel
