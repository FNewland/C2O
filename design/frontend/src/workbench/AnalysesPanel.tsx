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
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
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
import { Button, Chevron, Note, Panel, StatusBadge } from '../components/ui'

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
  metrics: (summary: Record<string, any>, t: TFunction) => Metric[]
}

function fmt(v: unknown, digits = 1): string {
  if (typeof v !== 'number' || Number.isNaN(v)) return '—'
  return Number.isInteger(v) ? String(v) : v.toFixed(digits)
}
function tone(ok: boolean | null): string | undefined {
  return ok === null ? undefined : ok ? 'var(--status-ok)' : 'var(--status-alarm)'
}

// English text is the i18n key
const CARD_LABELS: Record<AnalysisId, string> = {
  design_loop: 'Design loop',
  mission_simulation: 'Mission simulation',
  ground_segment: 'Ground segment',
  physics: 'Physics (mass / AOCS / thermal)',
  vv: 'V&V',
  fmeca: 'FMECA',
}
// English text is the i18n key
const CARD_NEEDS: Record<AnalysisId, string> = {
  design_loop: 'Mission root with requirements (orbit, payload, lifetime); subsystems by domain.',
  mission_simulation: 'Operational modes (power, data rate, payload on/off), battery capacity_wh, solar array EOL power, orbit.',
  ground_segment: 'At least one selected ground station (ground segment element), TT&C band / data rate, orbit, payload data rate.',
  physics: 'Component masses and dimensions, body positions (or auto-placement in a structure envelope), a reaction wheel, pointing requirement, dissipations.',
  vv: 'Requirements with verification method / threshold parameters; analysis runs close threshold items automatically.',
  fmeca: 'Component elements with domain, quantity / redundancy, and functions allocated (critical functions drive single-point findings).',
}

export const ANALYSIS_CARDS: CardDef[] = [
  {
    id: 'design_loop', label: CARD_LABELS.design_loop, color: 'var(--text)',
    needs: CARD_NEEDS.design_loop,
    runUrl: (s, opt) => `${API}/design/${s}/run${opt}`,
    runBody: { max_iterations: 50, convergence_threshold: 0.001 },
    metrics: (s, t) => [
      { label: t('converged'), value: s.converged === undefined ? '—' : s.converged ? t('yes') : t('no'), tone: tone(s.converged === undefined ? null : !!s.converged) },
      { label: t('iterations'), value: fmt(s.iterations) },
      { label: t('conflicts'), value: fmt(s.conflicts), tone: tone(typeof s.conflicts === 'number' ? s.conflicts === 0 : null) },
    ],
  },
  {
    id: 'mission_simulation', label: CARD_LABELS.mission_simulation, color: 'var(--text)',
    needs: CARD_NEEDS.mission_simulation,
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/mission_simulation/run${opt}`,
    metrics: (s, t) => [
      { label: t('min SoC'), value: `${fmt(s.min_soc_pct ?? s.sim_min_soc_pct)} %`, tone: tone(typeof (s.min_soc_pct ?? s.sim_min_soc_pct) === 'number' ? (s.min_soc_pct ?? s.sim_min_soc_pct) >= 20 : null) },
      { label: t('energy/orbit'), value: `${fmt(s.energy_balance_wh_per_orbit ?? s.sim_energy_balance_wh_per_orbit)} Wh`, tone: tone(typeof (s.energy_balance_wh_per_orbit ?? s.sim_energy_balance_wh_per_orbit) === 'number' ? (s.energy_balance_wh_per_orbit ?? s.sim_energy_balance_wh_per_orbit) >= 0 : null) },
      { label: t('backlog'), value: `${fmt(s.data_backlog_end_gb ?? s.sim_data_backlog_end_gb, 2)} GB` },
    ],
  },
  {
    id: 'ground_segment', label: CARD_LABELS.ground_segment, color: 'var(--text)',
    needs: CARD_NEEDS.ground_segment,
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/ground_segment/run${opt}`,
    metrics: (s, t) => [
      { label: t('contact'), value: t('{{v}} min/d', { v: fmt(s.gs_contact_min_per_day) }) },
      { label: t('returned'), value: t('{{ret}} / {{gen}} GB/d', { ret: fmt(s.gs_data_return_gb_per_day, 2), gen: fmt(s.gs_data_generated_gb_per_day, 2) }), tone: tone(typeof s.gs_data_return_gb_per_day === 'number' && typeof s.gs_data_generated_gb_per_day === 'number' ? s.gs_data_return_gb_per_day >= s.gs_data_generated_gb_per_day : null) },
      { label: t('stations'), value: fmt(s.gs_station_count) },
    ],
  },
  {
    id: 'physics', label: CARD_LABELS.physics, color: 'var(--text)',
    needs: CARD_NEEDS.physics,
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/physics/run${opt}`,
    metrics: (s, t) => [
      { label: t('mass'), value: `${fmt(s.mp_total_mass_kg, 2)} kg` },
      { label: t('wheel margin'), value: `${fmt(s.aocs_wheel_margin_pct)} %`, tone: tone(typeof s.aocs_wheel_margin_pct === 'number' ? s.aocs_wheel_margin_pct >= 0 : null) },
      { label: t('thermal margin'), value: `${fmt(s.thermal_worst_margin_c)} °C`, tone: tone(typeof s.thermal_worst_margin_c === 'number' ? s.thermal_worst_margin_c >= 0 : null) },
    ],
  },
  {
    id: 'vv', label: CARD_LABELS.vv, color: 'var(--text)',
    needs: CARD_NEEDS.vv,
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/vv/run${opt}`,
    metrics: (s, t) => [
      { label: t('closure'), value: `${fmt(s.vv_closure_pct)} %` },
      { label: t('passed'), value: `${fmt(s.vv_items_passed)} / ${fmt(s.vv_items_total)}` },
      { label: t('failed'), value: fmt(s.vv_items_failed), tone: tone(typeof s.vv_items_failed === 'number' ? s.vv_items_failed === 0 : null) },
    ],
  },
  {
    id: 'fmeca', label: CARD_LABELS.fmeca, color: 'var(--text)',
    needs: CARD_NEEDS.fmeca,
    runUrl: (s, opt) => `${API}/studies/${s}/analyses/fmeca/run${opt}`,
    runBody: { critical: [] },
    metrics: (s, t) => [
      { label: t('modes'), value: fmt(s.fmeca_modes ?? s.modes) },
      { label: t('max RPN'), value: fmt(s.fmeca_max_rpn) },
      { label: t('single points'), value: fmt(s.fmeca_single_point_failures), tone: tone(typeof s.fmeca_single_point_failures === 'number' ? s.fmeca_single_point_failures === 0 : null) },
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

function ago(iso: string | null | undefined, t: TFunction): string {
  if (!iso) return t('never run')
  const s = (Date.now() - new Date(iso).getTime()) / 1000
  if (!Number.isFinite(s)) return ''
  if (s < 60) return t('just now')
  if (s < 3600) return t('{{n}} min ago', { n: Math.floor(s / 60) })
  if (s < 86400) return t('{{n}} h ago', { n: Math.floor(s / 3600) })
  return t('{{n}} d ago', { n: Math.floor(s / 86400) })
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
  const { t } = useTranslation()
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
  const metrics = run ? def.metrics(summary, t) : []
  const status = runMut.isPending || run?.status === 'running' ? 'running' : run?.status
  const running = status === 'running'

  const metricView = (m: Metric) => m.tone?.includes('alarm')
    ? <StatusBadge status="alarm">{m.value}</StatusBadge>
    : m.tone?.includes('caution') ? <StatusBadge status="caution">{m.value}</StatusBadge>
    : <span className="mono c-v t-15">{m.value}</span>

  return (
    <li className={active ? 'c2o-an__row is-open' : 'c2o-an__row'}>
      <button type="button" className="c2o-an__name" aria-expanded={active} onClick={onOpen}>
        <Chevron />
        <span>{t(def.label)}</span>
      </button>
      <span className="c2o-an__state">
        {running ? <StatusBadge status="info">{t('running')}</StatusBadge>
          : status === 'failed' ? <span title={summary.error}><StatusBadge status="alarm">{t('failed')}</StatusBadge></span>
          : run?.stale ? <span title={t('Inputs changed since this run')}><StatusBadge status="stale">{t('stale')}</StatusBadge></span>
          : status === 'ok' ? <StatusBadge status="ok">{t('ok')}</StatusBadge>
          : <StatusBadge status="nodata">{t('never run')}</StatusBadge>}
        {openConflicts > 0 && <StatusBadge status="caution">{t('{{count}} conflicts', { count: openConflicts, defaultValue_one: '{{count}} conflict' })}</StatusBadge>}
      </span>
      <span className="c2o-an__when t-12 c-3" title={run?.finished_at || run?.started_at || ''}>
        {run ? t('last run {{ago}}', { ago: ago(run.finished_at || run.started_at, t) }) : optionId ? t('never run in this option') : ''}
      </span>
      <span className="c2o-an__metrics">
        {metrics.length > 0 ? metrics.map(m => (
          <span key={m.label} className="c2o-an__metric">
            <span className="t-12 c-3">{m.label}</span>
            {metricView(m)}
          </span>
        )) : (
          <span className="t-12 c-2" title={t(def.needs)}>{t('needs: {{needs}}', { needs: t(def.needs) })}</span>
        )}
      </span>
      <span className="c2o-an__act">
        {error && <span title={error}><StatusBadge status="alarm">{t('error')}</StatusBadge></span>}
        <Button size="sm" onClick={() => runMut.mutate()} active={running} busy={running}>
          {running ? t('Running…') : run ? t('Re-run') : t('Run')}
        </Button>
      </span>
    </li>
  )
}

function Section({ title, children }: { title: string; color?: string; children: ReactNode }) {
  return <Panel level={3} title={title} className="mt-4">{children}</Panel>
}

export function AnalysesPanel() {
  const { t } = useTranslation()
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

  if (!studyId) return <div className="p-3 t-12 c-2">{t('Select a study.')}</div>

  const byAnalysis = new Map(runs.map(r => [r.analysis, r]))
  const openByAnalysis = new Map<string, number>()
  for (const c of [...(conflicts?.design || []), ...(conflicts?.analysis || [])]) {
    if (c.resolved) continue
    openByAnalysis.set(c.analysis, (openByAnalysis.get(c.analysis) || 0) + 1)
  }
  const openDef = ANALYSIS_CARDS.find(d => d.id === open)

  return (
    <div className="c2o-pane">
      <div className="flex ai-c gap-3 mb-2 wrap">
        <span className="t-12 c-2 measure">
          {optionId
            ? t('Engineering analyses for the active option. Open one to see its results; Run recalculates it and refreshes parameters, conflicts and margins.')
            : t('Engineering analyses for the baseline. Open one to see its results; Run recalculates it and refreshes parameters, conflicts and margins.')}
        </span>
        <span className="grow" />
        <Button size="sm" aria-pressed={showCompare} className="c2o-toggle" onClick={() => setShowCompare(v => !v)}>
          {t('Compare options')}
        </Button>
      </div>
      {runsError && <Note tone="alarm" className="mb-2">{t('analyses: {{message}}', { message: (runsError as Error).message })}</Note>}

      <ul className="list-reset c2o-an" aria-label={t('Analyses')}>
        {ANALYSIS_CARDS.map(def => (
          <AnalysisCard
            key={def.id} def={def} run={byAnalysis.get(def.id)} openConflicts={openByAnalysis.get(def.id) || 0}
            active={open === def.id} onOpen={() => setOpen(o => (o === def.id ? null : def.id))}
            studyId={studyId} optionId={optionId}
          />
        ))}
      </ul>

      {showCompare && (
        <Section title={t('Options')} color="var(--text-2)">
          <ErrorBoundary phaseName="Option compare"><OptionCompare studyId={studyId} /></ErrorBoundary>
        </Section>
      )}

      {openDef && (
        <Section title={t(openDef.label)} color={openDef.color}>
          <ErrorBoundary phaseName={openDef.label}>
            {open === 'design_loop' && (
              <div>
                <div className="t-12 c-2 mb-1">
                  {t('Budgets after the last design loop (mission root or the focused element). Cross-domain conflicts from the loop are listed under Conflicts below.')}
                </div>
                <BudgetPanel />
                <div className="mt-2"><ConflictsPanel studyId={studyId} optionId={optionId} analysisFilter="design_loop" /></div>
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

      <Section title={t('Conflicts')} color="var(--text-2)">
        <ErrorBoundary phaseName="Conflicts"><ConflictsPanel studyId={studyId} optionId={optionId} /></ErrorBoundary>
      </Section>
    </div>
  )
}

export default AnalysesPanel
