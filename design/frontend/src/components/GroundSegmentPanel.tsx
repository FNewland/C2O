/**
 * GroundSegmentPanel — SCDF-174 ground segment closure.
 *
 * Station picker (KB catalogue with lat/lon and bands; add / remove persists
 * the selection as ``segment='ground'`` elements), run button with last-run /
 * stale badge, closure gauge (data returned vs generated), per-station table
 * (contacts/day, min/day, margin, status), 24 h on-board buffer plot with the
 * contact windows as bands (SVGLineChart) and the conflicts with their fixes.
 *
 *   GET    /api/studies/{id}/ground-stations
 *   POST   /api/studies/{id}/ground-stations {kb_station_id}
 *   DELETE /api/studies/{id}/ground-stations/{element_id}
 *   POST   /api/studies/{id}/analyses/ground_segment/run?option_id=
 *   GET    /api/studies/{id}/analyses/ground_segment?option_id=
 *   GET    /api/analyses/runs/{run_id}/series
 *   GET    /api/studies/{id}/conflicts?option_id=   (filtered to analysis = ground_segment)
 *
 * Not mounted here — SCDF-178 places it in the Analyses tab.
 */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { SVGLineChart, type Band, type LineSeries } from '../charts/SVGLineChart'
import type {
  AnalysisConflict, GroundSegmentRun, GroundSegmentRunResponse, GroundSegmentSeries, GroundStationRow,
  GroundStationsResponse, KbGroundStation, RunSeriesResponse,
} from '../types/analyses'
import { fs } from '../theme/tokens'
import { serverText } from '../i18n/serverText'

const API = '/api'
const ANALYSIS = 'ground_segment'

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--status-alarm)', major: 'var(--status-caution)', minor: 'var(--status-caution)', warning: 'var(--status-caution)', info: 'var(--interactive)',
}
const STATUS_COLORS: Record<string, string> = {
  ok: 'var(--status-ok)', low_margin: 'var(--status-caution)', excluded: 'var(--status-alarm)', no_contact: 'var(--text-3)',
}
// English text is the i18n key
const SEVERITY_LABELS: Record<string, string> = {
  critical: 'critical', major: 'major', minor: 'minor', warning: 'warning', info: 'info',
}
// English text is the i18n key
const STATUS_LABEL: Record<string, string> = {
  ok: 'ok', low_margin: 'low margin', excluded: 'excluded', no_contact: 'no contact',
}
const STATION_PALETTE = ['var(--interactive)', 'var(--status-ok)', 'var(--status-caution)', 'var(--cat-2)', 'var(--cat-6)', 'var(--cat-3)', 'var(--status-alarm)', 'var(--cat-7)']

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

/** Data returned vs generated as a horizontal bar. */
function ClosureGauge({ returned, generated }: { returned: number; generated: number }) {
  const { t } = useTranslation()
  const pct = generated > 0 ? Math.min(100, (100 * returned) / generated) : 100
  const tone = pct >= 95 ? 'var(--status-ok)' : pct >= 80 ? 'var(--status-caution)' : 'var(--status-alarm)'
  return (
    <div className="c2o-card" style={{ flex: '2 1 240px' }}>
      <div className="flex jc-sb t-12 c-2 caps">
        <span>{t('Data closure')}</span><span style={{ color: tone, fontFamily: 'ui-monospace, monospace' }}>{fmt(pct, 0)} %</span>
      </div>
      <div title={t('{{ret}} GB returned of {{gen}} GB generated per day', { ret: fmt(returned, 2), gen: fmt(generated, 2) })}
           style={{ position: 'relative', height: 10, marginTop: 4, borderRadius: 5, background: 'var(--bg-secondary, var(--surface-2))', border: '1px solid var(--border)', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${pct}%`, background: tone, transition: 'width 0.3s' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: fs.label, marginTop: 3, fontFamily: 'ui-monospace, monospace' }}>
        <span style={{ color: tone }}>{t('{{value}} GB/day returned', { value: fmt(returned, 2) })}</span>
        <span className="c-2">{t('{{value}} GB/day generated', { value: fmt(generated, 2) })}</span>
      </div>
    </div>
  )
}

const bandsOf = (s: KbGroundStation) => (s.bands ?? []).join('/')
const latLon = (lat: number | null | undefined, lon: number | null | undefined, t: TFunction) =>
  lat === null || lat === undefined || lon === null || lon === undefined ? '—'
    : `${Math.abs(lat).toFixed(1)}°${lat >= 0 ? 'N' : 'S'} ${Math.abs(lon).toFixed(1)}°${lon >= 0 ? 'E' : t('W', { context: 'west' })}`

export function GroundSegmentPanel({ studyId, optionId }: { studyId: string | null; optionId?: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [pick, setPick] = useState('')
  const [filter, setFilter] = useState('')
  const opt = optionId ? `?option_id=${encodeURIComponent(optionId)}` : ''

  // ── stations ────────────────────────────────────────────────────────
  const stationsQ = useQuery<GroundStationsResponse>({
    queryKey: ['ground-stations', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/ground-stations`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })
  const selected = stationsQ.data?.selected ?? []
  const catalogue = stationsQ.data?.catalogue ?? []
  const available = useMemo(() => {
    const q = filter.trim().toLowerCase()
    return catalogue.filter(s => !s.selected && (!q || s.name.toLowerCase().includes(q) || s.id.includes(q) || (s.operator ?? '').toLowerCase().includes(q) || bandsOf(s).toLowerCase().includes(q)))
  }, [catalogue, filter])

  const invalidateAll = () => {
    qc.invalidateQueries({ queryKey: ['ground-stations', studyId] })
    qc.invalidateQueries({ queryKey: ['analysis', ANALYSIS, studyId] })
    qc.invalidateQueries({ queryKey: ['analyses', studyId] })
    qc.invalidateQueries({ queryKey: ['elements', studyId] })
    qc.invalidateQueries({ queryKey: ['element-tree', studyId] })
  }
  const addMut = useMutation<unknown, Error, string>({
    mutationFn: id => fetch(`${API}/studies/${studyId}/ground-stations`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ kb_station_id: id }),
    }).then(jsonOrThrow),
    onSuccess: () => { setError(null); setPick(''); invalidateAll() },
    onError: e => setError(e.message),
  })
  const removeMut = useMutation<unknown, Error, string>({
    mutationFn: elementId => fetch(`${API}/studies/${studyId}/ground-stations/${elementId}`, { method: 'DELETE' }).then(jsonOrThrow),
    onSuccess: () => { setError(null); invalidateAll() },
    onError: e => setError(e.message),
  })

  // ── run ─────────────────────────────────────────────────────────────
  const runQ = useQuery<GroundSegmentRun | null>({
    queryKey: ['analysis', ANALYSIS, studyId, optionId ?? null],
    queryFn: async () => {
      const res = await fetch(`${API}/studies/${studyId}/analyses/${ANALYSIS}${opt}`)
      if (res.status === 404) return null
      return jsonOrThrow(res)
    },
    enabled: !!studyId, structuralSharing: false,
  })
  const run = runQ.data ?? null

  const seriesQ = useQuery<RunSeriesResponse<GroundSegmentSeries>>({
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

  const runMut = useMutation<GroundSegmentRunResponse, Error>({
    mutationFn: () => fetch(`${API}/studies/${studyId}/analyses/${ANALYSIS}/run${opt}`, { method: 'POST' }).then(jsonOrThrow),
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
  const stationColors = useMemo(() => {
    const m = new Map<string, string>()
    for (const r of (run?.summary.stations ?? series?.stations ?? []) as GroundStationRow[]) {
      if (!m.has(r.station_id)) m.set(r.station_id, STATION_PALETTE[m.size % STATION_PALETTE.length])
    }
    return m
  }, [run, series])
  const toH = (t: number) => t / 3600
  const contactBands: Band[] = useMemo(
    () => (series?.contacts ?? []).map(c => ({ from: toH(c.start_s), to: toH(c.end_s), label: c.station, color: stationColors.get(c.station_id) || 'var(--text-3)' })),
    [series, stationColors],
  )
  const bufferSeries: LineSeries[] = series ? [{ name: t('on-board data'), color: 'var(--cat-2)', points: series.buffer.t_s.map((t, i) => [toH(t), series.buffer.gb[i]]) }] : []
  const storage = series?.inputs?.storage_gb as number | null | undefined

  if (!studyId) return <div className="t-12 c-2">{t('Select a study.')}</div>

  const s = run?.summary ?? {}
  const rows: GroundStationRow[] = s.stations ?? []
  const marginTone = s.gs_min_link_margin_db === undefined ? undefined : s.gs_min_link_margin_db < 0 ? 'var(--status-alarm)' : s.gs_min_link_margin_db < 3 ? 'var(--status-caution)' : 'var(--status-ok)'
  const backlogTone = s.backlog_growth_gb_per_day === undefined ? undefined : s.backlog_growth_gb_per_day > 0.01 ? 'var(--status-caution)' : 'var(--status-ok)'

  return (
    <div className="t-12 stack gap-2">
      {/* header */}
      <div className="flex ai-c gap-2 wrap">
        <strong className="t-12">{t('Ground segment')}</strong>
        {run ? (
          <>
            <Badge text={run.status === 'ok' ? t('last run {{ago}}', { ago: ago(run.finished_at, t) }) : t('run {{status}}', { status: run.status })} color={run.status === 'ok' ? 'var(--status-ok)' : 'var(--status-alarm)'} title={run.finished_at || undefined} />
            {run.stale && <Badge text={t('stale')} color="var(--status-caution)" title={t('Stations, orbit or link parameters changed since this run — re-run to refresh')} />}
            {s.band && <span className="c-2 t-12">{t('{{band}}-band · {{rate}} Mbps · {{source}}', { band: s.band, rate: fmt(s.downlink_rate_mbps, 2), source: s.data_source })}</span>}
          </>
        ) : runQ.isLoading ? <span className="c-2">{t('loading…')}</span>
          : <Badge text={t('never run')} color="var(--text-3)" />}
        <span className="grow" />
        <button className="c2o-btn c2o-btn--primary c2o-btn--sm" disabled={runMut.isPending} onClick={() => runMut.mutate()}>
          {runMut.isPending ? t('Running…') : run ? t('Re-run') : t('Run')}
        </button>
      </div>
      {error && <div className="c-alarm t-12">{error}</div>}
      {run?.status === 'failed' && s.error && <div className="c-alarm t-12">{t('Last run failed: {{error}}', { error: s.error })}</div>}

      {/* station picker */}
      <div className="c2o-card">
        <div className="flex ai-c gap-2 wrap mb-1">
          <span className="t-12 c-2 caps">
            {t('Stations ({{n}})', { n: selected.length })}
          </span>
          <span className="grow" />
          <input placeholder={t('filter catalogue…')} value={filter} onChange={e => setFilter(e.target.value)}
                 style={{ width: 120, fontSize: fs.label, padding: '0.1rem 0.3rem', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 3, color: 'var(--text-primary)' }} />
          <select value={pick} onChange={e => setPick(e.target.value)}
                  style={{ fontSize: fs.label, padding: '0.1rem 0.3rem', maxWidth: 260, background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 3, color: 'var(--text-primary)' }}>
            <option value="">{stationsQ.isLoading ? t('loading catalogue…') : t('add from catalogue ({{n}})', { n: available.length })}</option>
            {available.map(st => (
              <option key={st.id} value={st.id}>{st.name} — {latLon(st.lat, st.lon, t)} — {bandsOf(st)}{st.operator ? ` (${st.operator})` : ''}</option>
            ))}
          </select>
          <button className="c2o-btn c2o-btn--primary c2o-btn--sm" disabled={!pick || addMut.isPending} onClick={() => pick && addMut.mutate(pick)}>{t('Add')}</button>
        </div>
        {selected.length === 0 ? (
          <div className="c-caution t-12">{t('No station selected — the closure will use the catalogue defaults and warn.')}</div>
        ) : (
          <div className="flex wrap gap-1">
            {selected.map(st => (
              <span key={st.element_id} title={`${st.kb_station_id}${st.operator ? ` · ${st.operator}` : ''}${st.g_over_t_db_k !== null ? ` · G/T ${st.g_over_t_db_k} dB/K` : ''}`}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', padding: '0.1rem 0.4rem', borderRadius: 10, border: '1px solid var(--border)', fontSize: fs.label }}>
                <span style={{ width: 7, height: 7, borderRadius: 4, background: stationColors.get(st.kb_station_id) || 'var(--text-3)', display: 'inline-block' }} />
                <strong>{st.name}</strong>
                <span className="c-2">{latLon(st.lat, st.lon, t)} · {(st.bands ?? []).join('/')}{st.min_elevation_deg !== null ? ` · ≥${st.min_elevation_deg}°` : ''}</span>
                <button title={t('Remove station')} disabled={removeMut.isPending} onClick={() => removeMut.mutate(st.element_id)}
                        className="c2o-btn c2o-btn--danger c2o-btn--sm py-0 px-1 lh-value">×</button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* closure + summary */}
      {run && run.status === 'ok' && (
        <div className="flex gap-2 wrap">
          <ClosureGauge returned={s.gs_data_return_gb_per_day ?? 0} generated={s.gs_data_generated_gb_per_day ?? 0} />
          <SummaryCard label={t('Contact')} value={fmt(s.gs_contact_min_per_day, 0)} unit={t('min/day')}
                       sub={t('{{passes}} passes · {{n}} stations', { passes: fmt(s.gs_contacts_per_day, 0), n: fmt(s.gs_station_count, 0), count: s.gs_station_count, defaultValue_one: '{{passes}} passes · {{n}} station' })} />
          <SummaryCard label={t('Min link margin')} value={fmt(s.gs_min_link_margin_db)} unit="dB" tone={marginTone} sub={t('limit 3 dB')} />
          <SummaryCard label={t('Backlog')} value={fmt(s.gs_backlog_end_gb, 2)} unit="GB" tone={backlogTone}
                       sub={s.backlog_growth_gb_per_day !== undefined ? t('{{growth}} GB/day · gap {{gap}} h', { growth: `${s.backlog_growth_gb_per_day >= 0 ? '+' : ''}${fmt(s.backlog_growth_gb_per_day, 2)}`, gap: fmt(s.max_gap_hours, 1) }) : undefined} />
        </div>
      )}

      {/* warnings */}
      {!!s.warnings?.length && (
        <ul className="m-0 pl-4 c-caution t-12">
          {s.warnings.map((w, i) => <li key={i}>{w}</li>)}
        </ul>
      )}

      {/* per-station table */}
      {rows.length > 0 && (
        <div className="c2o-card" style={{ overflowX: 'auto', padding: 0 }}>
          <table className="c2o-table c2o-table--dense">
            <thead>
              <tr>
                <th>{t('Station')}</th><th>{t('Position')}</th><th>{t('Bands')}</th>
                <th className="ta-r">{t('Passes/day')}</th><th className="ta-r">{t('Min/day')}</th>
                <th className="ta-r">{t('GB/day')}</th><th className="ta-r">G/T dB/K</th>
                <th className="ta-r">{t('Margin dB')}</th><th>{t('Status')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(r => {
                const color = STATUS_COLORS[r.status] || 'var(--text-3)'
                return (
                  <tr key={r.station_id} style={{ opacity: r.status === 'excluded' ? 0.6 : 1 }}>
                    <td>
                      <span style={{ width: 7, height: 7, borderRadius: 4, background: stationColors.get(r.station_id) || 'var(--text-3)', display: 'inline-block', marginRight: 4 }} />
                      {r.name}
                    </td>
                    <td className="c-2">{latLon(r.lat, r.lon, t)}</td>
                    <td className="c-2">{r.bands.join('/')} · {fmt(r.antenna_m, 1)} m</td>
                    <td className="num">{r.contacts_per_day}</td>
                    <td className="num">{fmt(r.contact_min_per_day, 0)}</td>
                    <td className="num">{fmt(r.data_gb_per_day, 2)}</td>
                    <td className="num">{fmt(r.g_t_db_k)}</td>
                    <td className="num" style={{ color: r.margin_db === null ? undefined : r.margin_db < 0 ? 'var(--status-alarm)' : r.margin_db < 3 ? 'var(--status-caution)' : 'var(--status-ok)' }}>{fmt(r.margin_db)}</td>
                    <td><Badge text={STATUS_LABEL[r.status] ? t(STATUS_LABEL[r.status]) : r.status} color={color} title={r.reason || undefined} /></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* buffer plot with contact bands */}
      {seriesQ.isLoading && run?.status === 'ok' && <div className="c-2">{t('loading series…')}</div>}
      {series && (
        <div className="c2o-card">
          <SVGLineChart title={t('On-board data over 24 h (bands = contact windows)')} series={bufferSeries} bands={contactBands} xLabel="h" yLabel="GB" yMin={0}
                        refLines={storage ? [{ y: storage, label: t('storage {{value}} GB', { value: fmt(storage, 1) }) }] : []} height={200} />
          {series.contacts.length > 0 && (
            <details className="mt-1">
              <summary className="cursor-p t-12 c-2">{t('{{count}} contact windows', { count: series.contacts.length, defaultValue_one: '{{count}} contact windows' })}</summary>
              <table className="c2o-table c2o-table--dense">
                <thead><tr><th>{t('Station')}</th><th className="ta-r">{t('Start')}</th><th className="ta-r">{t('End')}</th><th className="ta-r">{t('Max el °')}</th><th className="ta-r">GB</th></tr></thead>
                <tbody>
                  {series.contacts.map((c, i) => {
                    const hm = (t: number) => `${String(Math.floor(t / 3600)).padStart(2, '0')}:${String(Math.floor((t % 3600) / 60)).padStart(2, '0')}`
                    return (
                      <tr key={i}>
                        <td><span style={{ width: 7, height: 7, borderRadius: 4, background: stationColors.get(c.station_id) || 'var(--text-3)', display: 'inline-block', marginRight: 4 }} />{c.station}</td>
                        <td className="num">{hm(c.start_s)}</td><td className="num">{hm(c.end_s)}</td>
                        <td className="num">{fmt(c.max_elevation_deg, 0)}</td><td className="num">{fmt(c.data_gb, 3)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </details>
          )}
        </div>
      )}

      {/* conflicts */}
      {run && run.status === 'ok' && (
        <div>
          <div className="t-12 c-2 mb-1">
            {t('What limited me')} {conflicts.length ? `(${conflicts.length})` : ''}
          </div>
          {conflicts.length === 0 ? (
            <div className="c-ok t-12">{t('Data return closes: every selected station closes the link and the daily volume comes down.')}</div>
          ) : (
            <ul className="list-reset m-0 p-0 stack gap-1">
              {conflicts.map(c => {
                const color = SEVERITY_COLORS[c.severity] || 'var(--text-3)'
                return (
                  <li key={c.id} className="c2o-card" style={{ borderLeft: `3px solid ${color}` }}>
                    <div className="flex gap-2 ai-c wrap">
                      <Badge text={t(SEVERITY_LABELS[c.severity] ?? c.severity)} color={color} />
                      <span className="mono t-12 c-2">{c.code}</span>
                      <strong className="t-12">{serverText(c.title)}</strong>
                    </div>
                    {c.detail && <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginTop: 2 }}>{serverText(c.detail)}</div>}
                    {c.suggested_fix && (
                      <div style={{ fontSize: fs.label, marginTop: 2 }}>
                        <span className="c-accent">{t('Fix:')} </span>{serverText(c.suggested_fix)}
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

export default GroundSegmentPanel
