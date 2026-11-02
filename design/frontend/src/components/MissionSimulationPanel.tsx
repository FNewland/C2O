/**
 * MissionSimulationPanel — SCDF-173 mission simulation closure.
 *
 * Run button, last-run / stale badge, summary cards (min SoC, energy
 * balance, data backlog, time in safe), SoC + mode bands / generation vs
 * load / data buffer plots (SVGLineChart) and the "what limited me" list
 * built from the run's conflicts with their suggested fixes.
 *
 *   POST /api/studies/{id}/analyses/mission_simulation/run?option_id=&n_orbits=
 *   GET  /api/studies/{id}/analyses/mission_simulation?option_id=
 *   GET  /api/analyses/runs/{run_id}/series
 *   GET  /api/studies/{id}/conflicts?option_id=   (filtered to analysis = mission_simulation)
 *
 * Not mounted here — SCDF-178 places it in the Analyses tab.
 */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { SVGLineChart, type Band, type LineSeries } from '../charts/SVGLineChart'
import type { AnalysisConflict, MissionSimRun, MissionSimRunResponse, MissionSimSeries, RunSeriesResponse } from '../types/analyses'
import { fs } from '../theme/tokens'

const API = '/api'
const ANALYSIS = 'mission_simulation'

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--status-alarm)', major: 'var(--status-caution)', minor: 'var(--status-caution)', warning: 'var(--status-caution)', info: 'var(--interactive)',
}
// English text is the i18n key
const SEVERITY_LABELS: Record<string, string> = {
  critical: 'critical', major: 'major', minor: 'minor', warning: 'warning', info: 'info',
}
const MODE_PALETTE = ['var(--interactive)', 'var(--status-ok)', 'var(--status-caution)', 'var(--cat-2)', 'var(--cat-6)', 'var(--cat-3)', 'var(--status-alarm)', 'var(--cat-7)']

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    let msg = `${res.status}`
    try {
      const b = await res.json()
      const d = b.detail
      msg = typeof d === 'string' ? d : JSON.stringify(d ?? b)
    } catch { /* noop */ }
    throw new Error(msg)
  }
  return res.status === 204 ? null : res.json()
}

function fmt(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—'
  return Number.isInteger(v) ? String(v) : v.toFixed(digits)
}

function ago(iso: string | null | undefined, t: TFunction): string {
  if (!iso) return ''
  const s = (Date.now() - new Date(iso).getTime()) / 1000
  if (!Number.isFinite(s)) return ''
  if (s < 60) return t('just now')
  if (s < 3600) return t('{{n}} min ago', { n: Math.floor(s / 60) })
  if (s < 86400) return t('{{n}} h ago', { n: Math.floor(s / 3600) })
  return t('{{n}} d ago', { n: Math.floor(s / 86400) })
}


function Badge({ text, color, title }: { text: string; color: string; title?: string }) {
  return (
    <span title={title} style={{ fontSize: fs.label, padding: '0 0.35rem', borderRadius: 3, background: `color-mix(in srgb, ${color} 13%, transparent)`, color, border: `1px solid color-mix(in srgb, ${color} 33%, transparent)`, whiteSpace: 'nowrap' }}>
      {text}
    </span>
  )
}

function SummaryCard({ label, value, unit, tone, sub }: { label: string; value: string; unit?: string; tone?: string; sub?: string }) {
  return (
    <div className="c2o-card">
      <div className="t-12 c-2 caps">{label}</div>
      <div style={{ fontSize: fs.value, fontWeight: 600, color: tone || 'var(--text-primary)', fontFamily: 'ui-monospace, monospace' }}>
        {value}{unit && <span style={{ fontSize: fs.label, marginLeft: 2, color: 'var(--text-secondary)' }}>{unit}</span>}
      </div>
      {sub && <div className="t-12 c-2">{sub}</div>}
    </div>
  )
}

export function MissionSimulationPanel({ studyId, optionId }: { studyId: string | null; optionId?: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [nOrbits, setNOrbits] = useState(15)
  const [error, setError] = useState<string | null>(null)
  const opt = optionId ? `?option_id=${encodeURIComponent(optionId)}` : ''

  const runQ = useQuery<MissionSimRun | null>({
    queryKey: ['analysis', ANALYSIS, studyId, optionId ?? null],
    queryFn: async () => {
      const res = await fetch(`${API}/studies/${studyId}/analyses/${ANALYSIS}${opt}`)
      if (res.status === 404) return null
      return jsonOrThrow(res)
    },
    enabled: !!studyId, structuralSharing: false,
  })
  const run = runQ.data ?? null

  const seriesQ = useQuery<RunSeriesResponse<MissionSimSeries>>({
    queryKey: ['analysis-series', run?.id],
    queryFn: () => fetch(`${API}/analyses/runs/${run!.id}/series`).then(jsonOrThrow),
    enabled: !!run?.id && run.status === 'ok', staleTime: Infinity,
  })
  const series = seriesQ.data?.series

  const conflictsQ = useQuery<{ analysis: AnalysisConflict[] }>({
    queryKey: ['conflicts', studyId, optionId ?? null],
    queryFn: () => fetch(`${API}/studies/${studyId}/conflicts${opt}`).then(jsonOrThrow),
    enabled: !!studyId && !run?.conflicts, structuralSharing: false,
  })
  const conflicts: AnalysisConflict[] = useMemo(
    () => (run?.conflicts ?? conflictsQ.data?.analysis ?? []).filter(c => c.analysis === ANALYSIS && !c.resolved),
    [run, conflictsQ.data],
  )

  const runMut = useMutation<MissionSimRunResponse, Error>({
    mutationFn: () => fetch(`${API}/studies/${studyId}/analyses/${ANALYSIS}/run${opt ? `${opt}&` : '?'}n_orbits=${nOrbits}`, { method: 'POST' }).then(jsonOrThrow),
    onSuccess: () => {
      setError(null)
      qc.invalidateQueries({ queryKey: ['analysis', ANALYSIS, studyId] })
      qc.invalidateQueries({ queryKey: ['analyses', studyId] })
      qc.invalidateQueries({ queryKey: ['conflicts', studyId] })
      qc.invalidateQueries({ queryKey: ['element-parameters'] })
      qc.invalidateQueries({ queryKey: ['study-parameters', studyId] })
    },
    onError: e => setError(e.message),
  })

  // ── plots ───────────────────────────────────────────────────────────
  const modeColors = useMemo(() => {
    const m = new Map<string, string>()
    const names = series?.modes.map(x => x.name) ?? []
    for (const name of [...names, ...(series?.mode ?? [])]) {
      if (!m.has(name)) m.set(name, /safe|surviv/i.test(name) ? 'var(--status-alarm)' : MODE_PALETTE[m.size % MODE_PALETTE.length])
    }
    return m
  }, [series])

  const toH = (t: number) => t / 3600
  const bands: Band[] = useMemo(() => {
    if (!series) return []
    const out: Band[] = []
    for (let i = 0; i < series.t_s.length; i++) {
      const from = toH(series.t_s[i])
      const to = toH(i + 1 < series.t_s.length ? series.t_s[i + 1] : series.t_s[i] + series.dt_s)
      out.push({ from, to, label: series.mode[i], color: modeColors.get(series.mode[i]) || 'var(--text-3)' })
    }
    return out
  }, [series, modeColors])

  const socSeries: LineSeries[] = series ? [{ name: 'SoC', color: 'var(--interactive)', points: series.t_s.map((t, i) => [toH(t), series.soc_pct[i]]) }] : []
  const powerSeries: LineSeries[] = series ? [
    { name: t('generation'), color: 'var(--status-ok)', points: series.t_s.map((t, i) => [toH(t), series.p_gen_w[i]]) },
    { name: t('load', { context: 'electrical' }), color: 'var(--status-caution)', points: series.t_s.map((t, i) => [toH(t), series.p_load_w[i]]) },
  ] : []
  const dataSeries: LineSeries[] = series ? [{ name: t('buffer', { context: 'data' }), color: 'var(--cat-2)', points: series.t_s.map((t, i) => [toH(t), series.data_buffer_gb[i]]) }] : []
  const tempSeries: LineSeries[] = series?.temp_c?.length ? [{ name: t('temp'), color: 'var(--status-caution)', points: series.t_s.map((t, i) => [toH(t), series.temp_c[i]]) }] : []
  const minSoc = series?.inputs?.min_soc_pct as number | undefined
  const storage = series?.inputs?.storage_gb as number | null | undefined

  if (!studyId) return <div className="t-12 c-2">{t('Select a study.')}</div>

  const s = run?.summary ?? {}
  const socTone = s.sim_min_soc_pct === undefined ? undefined : s.sim_min_soc_pct < (minSoc ?? 20) ? 'var(--status-alarm)' : 'var(--status-ok)'
  const ebTone = s.sim_energy_balance_wh_per_orbit === undefined ? undefined : s.sim_energy_balance_wh_per_orbit < 0 ? 'var(--status-alarm)' : 'var(--status-ok)'
  const safeTone = s.sim_time_in_safe_pct === undefined ? undefined : s.sim_time_in_safe_pct > 10 ? 'var(--status-caution)' : 'var(--status-ok)'
  const backlogTone = s.sim_data_backlog_end_gb === undefined ? undefined : s.sim_data_backlog_end_gb > 0.05 ? 'var(--status-caution)' : 'var(--status-ok)'

  return (
    <div className="t-12 stack gap-2">
      {/* header */}
      <div className="flex ai-c gap-2 wrap">
        <strong className="t-12">{t('Mission simulation')}</strong>
        {run ? (
          <>
            <Badge text={run.status === 'ok' ? t('last run {{ago}}', { ago: ago(run.finished_at, t) }) : t('run {{status}}', { status: run.status })} color={run.status === 'ok' ? 'var(--status-ok)' : 'var(--status-alarm)'} title={run.finished_at || undefined} />
            {run.stale && <Badge text={t('stale')} color="var(--status-caution)" title={t('The model changed since this run — re-run to refresh')} />}
            {s.n_orbits !== undefined && <span className="c-2 t-12">{t('{{n}} orbits · {{samples}} samples', { n: s.n_orbits, samples: s.samples ?? '?' })}</span>}
          </>
        ) : runQ.isLoading ? <span className="c-2">{t('loading…')}</span>
          : <Badge text={t('never run')} color="var(--text-3)" />}
        <span className="grow" />
        <label className="c-2 t-12">
          {t('orbits')}{' '}
          <input type="number" min={1} max={200} value={nOrbits} onChange={e => setNOrbits(Math.max(1, Math.min(200, Number(e.target.value) || 1)))}
                 style={{ width: 46, fontSize: fs.label, padding: '0.1rem 0.25rem', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 3, color: 'var(--text-primary)' }} />
        </label>
        <button className="c2o-btn c2o-btn--primary c2o-btn--sm" disabled={runMut.isPending} onClick={() => runMut.mutate()}>
          {runMut.isPending ? t('Running…') : run ? t('Re-run') : t('Run')}
        </button>
      </div>
      {error && <div className="c-alarm t-12">{error}</div>}
      {run?.status === 'failed' && s.error && <div className="c-alarm t-12">{t('Last run failed: {{error}}', { error: s.error })}</div>}

      {/* summary cards */}
      {run && run.status === 'ok' && (
        <div className="flex gap-2 wrap">
          <SummaryCard label={t('Min SoC')} value={fmt(s.sim_min_soc_pct)} unit="%" tone={socTone}
                       sub={s.min_soc_mode ? (minSoc !== undefined ? t('in {{mode}} · limit {{limit}} %', { mode: s.min_soc_mode, limit: minSoc }) : t('in {{mode}}', { mode: s.min_soc_mode })) : undefined} />
          <SummaryCard label={t('Energy balance')} value={(s.sim_energy_balance_wh_per_orbit ?? 0) >= 0 ? `+${fmt(s.sim_energy_balance_wh_per_orbit, 2)}` : fmt(s.sim_energy_balance_wh_per_orbit, 2)} unit={t('Wh/orbit')} tone={ebTone}
                       sub={s.sim_heater_energy_wh_per_orbit !== undefined ? t('heater {{value}} Wh/orbit', { value: fmt(s.sim_heater_energy_wh_per_orbit, 2) }) : undefined} />
          <SummaryCard label={t('Data backlog')} value={fmt(s.sim_data_backlog_end_gb, 2)} unit="GB" tone={backlogTone}
                       sub={s.sim_data_buffer_max_gb !== undefined ? t('peak {{value}} GB', { value: fmt(s.sim_data_buffer_max_gb, 2) }) : undefined} />
          <SummaryCard label={t('Time in safe')} value={fmt(s.sim_time_in_safe_pct)} unit="%" tone={safeTone}
                       sub={s.guard_triggers !== undefined ? t('{{count}} guard triggers', { count: s.guard_triggers, defaultValue_one: '{{count}} guard trigger' }) : undefined} />
          {s.sim_max_dod_pct !== undefined ? (
            <SummaryCard label={t('Max DoD')} value={fmt(s.sim_max_dod_pct)} unit="%" />
          ) : null}
        </div>
      )}

      {/* warnings */}
      {!!s.warnings?.length && (
        <ul className="m-0 pl-4 c-caution t-12">
          {s.warnings.map((w, i) => <li key={i}>{w}</li>)}
        </ul>
      )}

      {/* plots */}
      {seriesQ.isLoading && run?.status === 'ok' && <div className="c-2">{t('loading series…')}</div>}
      {series && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '0.5rem' }}>
          <div className="c2o-card">
            <SVGLineChart title={t('Battery state of charge')} series={socSeries} bands={bands} xLabel="h" yLabel="SoC [%]" yMin={0} yMax={100}
                          refLines={minSoc !== undefined ? [{ y: minSoc, label: t('min {{value}} %', { value: minSoc }) }] : []} height={190} />
          </div>
          <div className="c2o-card">
            <SVGLineChart title={t('Generation vs load')} series={powerSeries} xLabel="h" yLabel="W" yMin={0} height={190} />
          </div>
          <div className="c2o-card">
            <SVGLineChart title={t('On-board data buffer')} series={dataSeries} bands={bands} xLabel="h" yLabel="GB" yMin={0}
                          refLines={storage ? [{ y: storage, label: t('storage {{value}} GB', { value: fmt(storage, 1) }) }] : []} height={190} />
          </div>
          {tempSeries.length > 0 && (
            <div className="c2o-card">
              <SVGLineChart title={t('Temperature (single node)')} series={tempSeries} xLabel="h" yLabel="°C" refLines={[{ y: 0, label: t('heater on'), color: 'var(--interactive)' }]} height={190} />
            </div>
          )}
        </div>
      )}

      {/* what limited me */}
      {run && run.status === 'ok' && (
        <div>
          <div className="t-12 c-2 mb-1">
            {t('What limited me')} {conflicts.length ? `(${conflicts.length})` : ''}
          </div>
          {conflicts.length === 0 ? (
            <div className="c-ok t-12">{t('No limits hit: SoC, energy balance, data and safe-mode time are all within bounds.')}</div>
          ) : (
            <ul className="list-reset m-0 p-0 stack gap-1">
              {conflicts.map(c => {
                const color = SEVERITY_COLORS[c.severity] || 'var(--text-3)'
                return (
                  <li key={c.id} className="c2o-card" style={{ borderLeft: `3px solid ${color}` }}>
                    <div className="flex gap-2 ai-c wrap">
                      <Badge text={t(SEVERITY_LABELS[c.severity] ?? c.severity)} color={color} />
                      <span className="mono t-12 c-2">{c.code}</span>
                      <strong className="t-12">{c.title}</strong>
                    </div>
                    {c.detail && <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginTop: 2 }}>{c.detail}</div>}
                    {c.suggested_fix && (
                      <div style={{ fontSize: fs.label, marginTop: 2 }}>
                        <span className="c-accent">{t('Fix:')} </span>{c.suggested_fix}
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

export default MissionSimulationPanel
