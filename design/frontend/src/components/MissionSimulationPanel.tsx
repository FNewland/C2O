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
import { SVGLineChart, type Band, type LineSeries } from '../charts/SVGLineChart'
import type { AnalysisConflict, MissionSimRun, MissionSimRunResponse, MissionSimSeries, RunSeriesResponse } from '../types/analyses'

const API = '/api'
const ANALYSIS = 'mission_simulation'

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444', major: '#f97316', minor: '#eab308', warning: '#f59e0b', info: '#3b82f6',
}
const MODE_PALETTE = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f43f5e', '#84cc16']

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

function ago(iso: string | null | undefined): string {
  if (!iso) return ''
  const s = (Date.now() - new Date(iso).getTime()) / 1000
  if (!Number.isFinite(s)) return ''
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.floor(s / 60)} min ago`
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`
  return `${Math.floor(s / 86400)} d ago`
}

const card: React.CSSProperties = {
  flex: '1 1 120px', minWidth: 110, padding: '0.4rem 0.55rem', borderRadius: 6,
  background: 'var(--bg-primary)', border: '1px solid var(--border)',
}
const btn = (primary = false): React.CSSProperties => ({
  cursor: 'pointer', fontSize: '0.66rem', padding: '0.2rem 0.6rem', borderRadius: 4,
  border: `1px solid ${primary ? '#3b82f6' : 'var(--border)'}`,
  background: primary ? '#3b82f622' : 'none', color: primary ? '#60a5fa' : 'var(--text-secondary)',
})

function Badge({ text, color, title }: { text: string; color: string; title?: string }) {
  return (
    <span title={title} style={{ fontSize: '0.58rem', padding: '0 0.35rem', borderRadius: 3, background: `${color}22`, color, border: `1px solid ${color}55`, whiteSpace: 'nowrap' }}>
      {text}
    </span>
  )
}

function SummaryCard({ label, value, unit, tone, sub }: { label: string; value: string; unit?: string; tone?: string; sub?: string }) {
  return (
    <div style={card}>
      <div style={{ fontSize: '0.58rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>{label}</div>
      <div style={{ fontSize: '1rem', fontWeight: 600, color: tone || 'var(--text-primary)', fontFamily: 'ui-monospace, monospace' }}>
        {value}{unit && <span style={{ fontSize: '0.6rem', marginLeft: 2, color: 'var(--text-secondary)' }}>{unit}</span>}
      </div>
      {sub && <div style={{ fontSize: '0.56rem', color: 'var(--text-secondary)' }}>{sub}</div>}
    </div>
  )
}

export function MissionSimulationPanel({ studyId, optionId }: { studyId: string | null; optionId?: string | null }) {
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
      if (!m.has(name)) m.set(name, /safe|surviv/i.test(name) ? '#ef4444' : MODE_PALETTE[m.size % MODE_PALETTE.length])
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
      out.push({ from, to, label: series.mode[i], color: modeColors.get(series.mode[i]) || '#6b7280' })
    }
    return out
  }, [series, modeColors])

  const socSeries: LineSeries[] = series ? [{ name: 'SoC', color: '#3b82f6', points: series.t_s.map((t, i) => [toH(t), series.soc_pct[i]]) }] : []
  const powerSeries: LineSeries[] = series ? [
    { name: 'generation', color: '#10b981', points: series.t_s.map((t, i) => [toH(t), series.p_gen_w[i]]) },
    { name: 'load', color: '#f97316', points: series.t_s.map((t, i) => [toH(t), series.p_load_w[i]]) },
  ] : []
  const dataSeries: LineSeries[] = series ? [{ name: 'buffer', color: '#8b5cf6', points: series.t_s.map((t, i) => [toH(t), series.data_buffer_gb[i]]) }] : []
  const tempSeries: LineSeries[] = series?.temp_c?.length ? [{ name: 'temp', color: '#eab308', points: series.t_s.map((t, i) => [toH(t), series.temp_c[i]]) }] : []
  const minSoc = series?.inputs?.min_soc_pct as number | undefined
  const storage = series?.inputs?.storage_gb as number | null | undefined

  if (!studyId) return <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Select a study.</div>

  const s = run?.summary ?? {}
  const socTone = s.sim_min_soc_pct === undefined ? undefined : s.sim_min_soc_pct < (minSoc ?? 20) ? '#ef4444' : '#10b981'
  const ebTone = s.sim_energy_balance_wh_per_orbit === undefined ? undefined : s.sim_energy_balance_wh_per_orbit < 0 ? '#ef4444' : '#10b981'
  const safeTone = s.sim_time_in_safe_pct === undefined ? undefined : s.sim_time_in_safe_pct > 10 ? '#f59e0b' : '#10b981'
  const backlogTone = s.sim_data_backlog_end_gb === undefined ? undefined : s.sim_data_backlog_end_gb > 0.05 ? '#f59e0b' : '#10b981'

  return (
    <div style={{ fontSize: '0.7rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {/* header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
        <strong style={{ fontSize: '0.74rem' }}>Mission simulation</strong>
        {run ? (
          <>
            <Badge text={run.status === 'ok' ? `last run ${ago(run.finished_at)}` : `run ${run.status}`} color={run.status === 'ok' ? '#10b981' : '#ef4444'} title={run.finished_at || undefined} />
            {run.stale && <Badge text="stale" color="#f59e0b" title="The model changed since this run — re-run to refresh" />}
            {s.n_orbits !== undefined && <span style={{ color: 'var(--text-secondary)', fontSize: '0.6rem' }}>{s.n_orbits} orbits · {s.samples ?? '?'} samples</span>}
          </>
        ) : runQ.isLoading ? <span style={{ color: 'var(--text-secondary)' }}>loading…</span>
          : <Badge text="never run" color="#6b7280" />}
        <span style={{ flex: 1 }} />
        <label style={{ color: 'var(--text-secondary)', fontSize: '0.62rem' }}>
          orbits{' '}
          <input type="number" min={1} max={200} value={nOrbits} onChange={e => setNOrbits(Math.max(1, Math.min(200, Number(e.target.value) || 1)))}
                 style={{ width: 46, fontSize: '0.62rem', padding: '0.1rem 0.25rem', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 3, color: 'var(--text-primary)' }} />
        </label>
        <button style={btn(true)} disabled={runMut.isPending} onClick={() => runMut.mutate()}>
          {runMut.isPending ? 'Running…' : run ? 'Re-run' : 'Run'}
        </button>
      </div>
      {error && <div style={{ color: '#ef4444', fontSize: '0.64rem' }}>{error}</div>}
      {run?.status === 'failed' && s.error && <div style={{ color: '#ef4444', fontSize: '0.64rem' }}>Last run failed: {s.error}</div>}

      {/* summary cards */}
      {run && run.status === 'ok' && (
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <SummaryCard label="Min SoC" value={fmt(s.sim_min_soc_pct)} unit="%" tone={socTone}
                       sub={s.min_soc_mode ? `in ${s.min_soc_mode}${minSoc !== undefined ? ` · limit ${minSoc} %` : ''}` : undefined} />
          <SummaryCard label="Energy balance" value={(s.sim_energy_balance_wh_per_orbit ?? 0) >= 0 ? `+${fmt(s.sim_energy_balance_wh_per_orbit, 2)}` : fmt(s.sim_energy_balance_wh_per_orbit, 2)} unit="Wh/orbit" tone={ebTone}
                       sub={s.sim_heater_energy_wh_per_orbit !== undefined ? `heater ${fmt(s.sim_heater_energy_wh_per_orbit, 2)} Wh/orbit` : undefined} />
          <SummaryCard label="Data backlog" value={fmt(s.sim_data_backlog_end_gb, 2)} unit="GB" tone={backlogTone}
                       sub={s.sim_data_buffer_max_gb !== undefined ? `peak ${fmt(s.sim_data_buffer_max_gb, 2)} GB` : undefined} />
          <SummaryCard label="Time in safe" value={fmt(s.sim_time_in_safe_pct)} unit="%" tone={safeTone}
                       sub={s.guard_triggers !== undefined ? `${s.guard_triggers} guard trigger${s.guard_triggers === 1 ? '' : 's'}` : undefined} />
          {s.sim_max_dod_pct !== undefined ? (
            <SummaryCard label="Max DoD" value={fmt(s.sim_max_dod_pct)} unit="%" />
          ) : null}
        </div>
      )}

      {/* warnings */}
      {!!s.warnings?.length && (
        <ul style={{ margin: 0, paddingLeft: '1rem', color: '#f59e0b', fontSize: '0.62rem' }}>
          {s.warnings.map((w, i) => <li key={i}>{w}</li>)}
        </ul>
      )}

      {/* plots */}
      {seriesQ.isLoading && run?.status === 'ok' && <div style={{ color: 'var(--text-secondary)' }}>loading series…</div>}
      {series && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '0.5rem' }}>
          <div style={card}>
            <SVGLineChart title="Battery state of charge" series={socSeries} bands={bands} xLabel="h" yLabel="SoC [%]" yMin={0} yMax={100}
                          refLines={minSoc !== undefined ? [{ y: minSoc, label: `min ${minSoc} %` }] : []} height={190} />
          </div>
          <div style={card}>
            <SVGLineChart title="Generation vs load" series={powerSeries} xLabel="h" yLabel="W" yMin={0} height={190} />
          </div>
          <div style={card}>
            <SVGLineChart title="On-board data buffer" series={dataSeries} bands={bands} xLabel="h" yLabel="GB" yMin={0}
                          refLines={storage ? [{ y: storage, label: `storage ${fmt(storage, 1)} GB` }] : []} height={190} />
          </div>
          {tempSeries.length > 0 && (
            <div style={card}>
              <SVGLineChart title="Temperature (single node)" series={tempSeries} xLabel="h" yLabel="°C" refLines={[{ y: 0, label: 'heater on', color: '#60a5fa' }]} height={190} />
            </div>
          )}
        </div>
      )}

      {/* what limited me */}
      {run && run.status === 'ok' && (
        <div>
          <div style={{ fontSize: '0.64rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
            What limited me {conflicts.length ? `(${conflicts.length})` : ''}
          </div>
          {conflicts.length === 0 ? (
            <div style={{ color: '#10b981', fontSize: '0.64rem' }}>No limits hit: SoC, energy balance, data and safe-mode time are all within bounds.</div>
          ) : (
            <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              {conflicts.map(c => {
                const color = SEVERITY_COLORS[c.severity] || '#6b7280'
                return (
                  <li key={c.id} style={{ ...card, borderLeft: `3px solid ${color}` }}>
                    <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
                      <Badge text={c.severity} color={color} />
                      <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.58rem', color: 'var(--text-secondary)' }}>{c.code}</span>
                      <strong style={{ fontSize: '0.68rem' }}>{c.title}</strong>
                    </div>
                    {c.detail && <div style={{ fontSize: '0.62rem', color: 'var(--text-secondary)', marginTop: 2 }}>{c.detail}</div>}
                    {c.suggested_fix && (
                      <div style={{ fontSize: '0.62rem', marginTop: 2 }}>
                        <span style={{ color: '#60a5fa' }}>Fix: </span>{c.suggested_fix}
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
