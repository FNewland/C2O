/**
 * PhysicsClosurePanel — SCDF-176 physics closure (mass properties -> AOCS,
 * thermal network from elements).
 *
 * Run button, last-run / stale badge, then three sections:
 *   1. Mass properties — CoM / CP offset read-out, inertia table, the
 *      placement table (auto-placed count, editable x/y/z that write through
 *      PATCH /api/elements/{id}/position and flag the run stale);
 *   2. AOCS — disturbance torque components (SVGBarChart), wheel-momentum and
 *      pointing margin gauges, the AOCS conflicts;
 *   3. Thermal — per-node hot / cold vs allowable table with margin colouring,
 *      one-orbit transient (SVGLineChart) and the thermal conflicts.
 *
 *   POST /api/studies/{id}/analyses/physics/run?option_id=
 *   GET  /api/studies/{id}/analyses/physics?option_id=
 *   GET  /api/studies/{id}/analyses/physics/placement?option_id=
 *   GET  /api/analyses/runs/{run_id}/series
 *   GET  /api/studies/{id}/conflicts?option_id=       (filtered to analysis = physics)
 *   PATCH /api/elements/{id}/position {x,y,z}
 *
 * Not mounted here — SCDF-178 places it in the Analyses tab.
 */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { SVGBarChart } from '../charts/SVGBarChart'
import { SVGLineChart, type Band, type LineSeries } from '../charts/SVGLineChart'
import type {
  AnalysisConflict, PhysicsRun, PhysicsRunResponse, PhysicsSeries, PlacementItem, PlacementResponse, RunSeriesResponse,
} from '../types/analyses'
import { fs } from '../theme/tokens'

const API = '/api'
const ANALYSIS = 'physics'

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--status-alarm)', major: 'var(--status-caution)', minor: 'var(--status-caution)', warning: 'var(--status-caution)', info: 'var(--interactive)',
}
// English text is the i18n key
const SEVERITY_LABELS: Record<string, string> = {
  critical: 'critical', major: 'major', minor: 'minor', warning: 'warning', info: 'info',
}
// English text is the i18n key
const NODE_KINDS: Record<string, string> = { structure: 'structure', subsystem: 'subsystem', component: 'component' }
const NODE_PALETTE = ['var(--interactive)', 'var(--status-ok)', 'var(--status-caution)', 'var(--cat-2)', 'var(--cat-6)', 'var(--cat-3)', 'var(--status-alarm)', 'var(--cat-7)', 'var(--interactive)', 'var(--cat-2)']

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
function sci(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—'
  return v === 0 ? '0' : v.toExponential(2)
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
function marginTone(m: number | null | undefined, warn = 5): string {
  if (m === null || m === undefined) return 'var(--text-secondary)'
  return m < 0 ? 'var(--status-alarm)' : m < warn ? 'var(--status-caution)' : 'var(--status-ok)'
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

/** Horizontal margin gauge: 0 at the left edge of the bar, requirement / capacity marked, value bar coloured by margin. */
function MarginGauge({ label, value, limit, unit, marginText, tone, digits = 3 }: {
  label: string; value: number; limit: number | null; unit: string; marginText: string; tone: string; digits?: number
}) {
  const { t } = useTranslation()
  const max = Math.max(value, limit ?? 0, 1e-12) * 1.25
  const vw = Math.min(100, value / max * 100)
  const lw = limit !== null ? Math.min(100, limit / max * 100) : null
  return (
    <div className="c2o-card">
      <div className="flex jc-sb t-12 c-2 caps">
        <span>{label}</span><span style={{ color: tone, fontWeight: 600 }}>{marginText}</span>
      </div>
      <div style={{ position: 'relative', height: 12, background: 'var(--bg-secondary, var(--surface-2))', borderRadius: 3, marginTop: 4 }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${vw}%`, background: tone, opacity: 0.8, borderRadius: 3 }} />
        {lw !== null && <div title={t('limit {{value}} {{unit}}', { value: fmt(limit, digits), unit })} style={{ position: 'absolute', left: `${lw}%`, top: -2, bottom: -2, width: 2, background: 'var(--text)' }} />}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: fs.label, marginTop: 2, fontFamily: 'ui-monospace, monospace' }}>
        <span>{fmt(value, digits)} {unit}</span>
        <span className="c-2">{limit !== null ? t('limit {{value}} {{unit}}', { value: fmt(limit, digits), unit }) : t('no limit')}</span>
      </div>
    </div>
  )
}

function ConflictList({ conflicts, empty }: { conflicts: AnalysisConflict[]; empty: string }) {
  const { t } = useTranslation()
  if (conflicts.length === 0) return <div className="c-ok t-12">{empty}</div>
  return (
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
            {c.suggested_fix && <div style={{ fontSize: fs.label, marginTop: 2 }}><span className="c-accent">{t('Fix:')} </span>{c.suggested_fix}</div>}
          </li>
        )
      })}
    </ul>
  )
}

function PositionRow({ item, onSave, busy }: { item: PlacementItem; onSave: (id: string, p: [number, number, number] | null) => void; busy: boolean }) {
  const [vals, setVals] = useState<[string, string, string]>([String(item.position_m[0]), String(item.position_m[1]), String(item.position_m[2])])
  const dirty = vals.some((v, i) => Number(v) !== item.position_m[i])
  const auto = item.source.startsWith('auto')
  const { t } = useTranslation()
  return (
    <tr>
      <td>{item.name}<span style={{ color: 'var(--text-secondary)', fontSize: fs.label, marginLeft: 4 }}>{item.domain ?? ''}</span></td>
      <td className="num">{fmt(item.mass_kg, 3)}</td>
      <td className="num">{item.dims_m.map(d => (d * 1000).toFixed(0)).join(' × ')}</td>
      {vals.map((v, i) => (
        <td key={i} className="num">
          <input className="c2o-input c2o-input--sm mono" value={v} onChange={e => setVals(prev => { const n = [...prev] as [string, string, string]; n[i] = e.target.value; return n })} />
        </td>
      ))}
      <td>
        <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
          <Badge text={auto ? t('auto') : t('explicit')} color={auto ? 'var(--status-caution)' : 'var(--status-ok)'} title={item.source} />
          {dirty && <button className="c2o-btn c2o-btn--primary c2o-btn--sm" disabled={busy} onClick={() => onSave(item.element_id, [Number(vals[0]), Number(vals[1]), Number(vals[2])])}>{t('save')}</button>}
          {!auto && !dirty && <button className="c2o-btn c2o-btn--sm" disabled={busy} title={t('Clear the position (back to auto-stack)')} onClick={() => onSave(item.element_id, null)}>{t('clear')}</button>}
        </span>
      </td>
    </tr>
  )
}

export function PhysicsClosurePanel({ studyId, optionId }: { studyId: string | null; optionId?: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [showPlacement, setShowPlacement] = useState(false)
  const opt = optionId ? `?option_id=${encodeURIComponent(optionId)}` : ''

  const runQ = useQuery<PhysicsRun | null>({
    queryKey: ['analysis', ANALYSIS, studyId, optionId ?? null],
    queryFn: async () => {
      const res = await fetch(`${API}/studies/${studyId}/analyses/${ANALYSIS}${opt}`)
      if (res.status === 404) return null
      return jsonOrThrow(res)
    },
    enabled: !!studyId, structuralSharing: false,
  })
  const run = runQ.data ?? null

  const seriesQ = useQuery<RunSeriesResponse<PhysicsSeries>>({
    queryKey: ['analysis-series', run?.id],
    queryFn: () => fetch(`${API}/analyses/runs/${run!.id}/series`).then(jsonOrThrow),
    enabled: !!run?.id && run.status === 'ok', staleTime: Infinity,
  })
  const series = seriesQ.data?.series

  const placementQ = useQuery<PlacementResponse>({
    queryKey: ['physics-placement', studyId, optionId ?? null],
    queryFn: () => fetch(`${API}/studies/${studyId}/analyses/${ANALYSIS}/placement${opt}`).then(jsonOrThrow),
    enabled: !!studyId && showPlacement, structuralSharing: false,
  })

  const conflictsQ = useQuery<{ analysis: AnalysisConflict[] }>({
    queryKey: ['conflicts', studyId, optionId ?? null],
    queryFn: () => fetch(`${API}/studies/${studyId}/conflicts${opt}`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })
  const conflicts: AnalysisConflict[] = useMemo(
    () => (run?.conflicts ?? conflictsQ.data?.analysis ?? []).filter(c => c.analysis === ANALYSIS && !c.resolved),
    [run, conflictsQ.data],
  )
  const aocsConflicts = conflicts.filter(c => c.code.startsWith('AOCS_'))
  const thermalConflicts = conflicts.filter(c => c.code.startsWith('THERMAL_'))

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['analysis', ANALYSIS, studyId] })
    qc.invalidateQueries({ queryKey: ['analyses', studyId] })
    qc.invalidateQueries({ queryKey: ['conflicts', studyId] })
    qc.invalidateQueries({ queryKey: ['physics-placement', studyId] })
    qc.invalidateQueries({ queryKey: ['element-parameters'] })
    qc.invalidateQueries({ queryKey: ['study-parameters', studyId] })
  }

  const runMut = useMutation<PhysicsRunResponse, Error>({
    mutationFn: () => fetch(`${API}/studies/${studyId}/analyses/${ANALYSIS}/run${opt}`, { method: 'POST' }).then(jsonOrThrow),
    onSuccess: () => { setError(null); invalidate() },
    onError: e => setError(e.message),
  })

  const posMut = useMutation<unknown, Error, { id: string; pos: [number, number, number] | null }>({
    mutationFn: ({ id, pos }) => fetch(`${API}/elements/${id}/position`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pos ? { x: pos[0], y: pos[1], z: pos[2] } : {}),
    }).then(jsonOrThrow),
    onSuccess: () => { setError(null); invalidate(); qc.invalidateQueries({ queryKey: ['elements', studyId] }); qc.invalidateQueries({ queryKey: ['element-tree', studyId] }) },
    onError: e => setError(e.message),
  })

  // ── derived views ─────────────────────────────────────────────────────
  const torqueBars = useMemo(() => {
    const tq = series?.aocs.torques_nm
    if (!tq) return []
    const scale = 1e6   // µN m
    return [
      { label: 'GG', value: tq.gravity_gradient * scale, color: 'var(--interactive)' },
      { label: t('Aero'), value: tq.aerodynamic * scale, color: 'var(--interactive)' },
      { label: 'SRP', value: tq.solar_pressure * scale, color: 'var(--status-caution)' },
      { label: 'Mag', value: tq.magnetic * scale, color: 'var(--cat-2)' },
      { label: 'RSS', value: tq.rss * scale, color: 'var(--text)' },
    ]
  }, [series, t])

  const thermalSeries: LineSeries[] = useMemo(() => {
    const tr = series?.thermal.transient
    if (!tr) return []
    return tr.nodes.map((n, i) => ({
      name: n.name, color: NODE_PALETTE[i % NODE_PALETTE.length], points: tr.t_s.map((t, k) => [t / 60, n.temps_c[k]] as [number, number]),
      dashed: n.kind === 'structure',
    }))
  }, [series])
  const eclipseBand: Band[] = series ? [{
    from: series.thermal.transient.eclipse_start_s / 60, to: series.thermal.transient.period_s / 60, label: t('eclipse'), color: 'var(--text-3)',
  }] : []

  if (!studyId) return <div className="t-12 c-2">{t('Select a study.')}</div>

  const s = run?.summary ?? {}
  const mp = series?.mass_properties
  const aocs = series?.aocs
  const thermal = series?.thermal
  const placement = placementQ.data ?? (series ? { ...series.placement, warnings: [] as string[] } : null)
  const offsetPct = mp && s.envelope_m ? mp.cp_cg_offset_m / Math.max(...s.envelope_m) * 100 : null
  const wheelTone = marginTone(aocs?.wheel_margin_pct, 20)
  const pointTone = aocs?.pointing_margin_deg === null || aocs?.pointing_margin_deg === undefined ? 'var(--text-secondary)'
    : marginTone(aocs.pointing_margin_deg, (aocs.pointing_req_deg ?? 1) * 0.2)

  return (
    <div className="t-12 stack gap-2">
      {/* header */}
      <div className="flex ai-c gap-2 wrap">
        <strong className="t-12">{t('Physics closure')}</strong>
        <span className="c-2 t-12">{t('mass properties → AOCS · thermal network')}</span>
        {run ? (
          <>
            <Badge text={run.status === 'ok' ? t('last run {{ago}}', { ago: ago(run.finished_at, t) }) : t('run {{status}}', { status: run.status })} color={run.status === 'ok' ? 'var(--status-ok)' : 'var(--status-alarm)'} title={run.finished_at || undefined} />
            {run.stale && <Badge text={t('stale')} color="var(--status-caution)" title={t('The model (masses, positions, dimensions, power, orbit) changed since this run — re-run to refresh')} />}
          </>
        ) : runQ.isLoading ? <span className="c-2">{t('loading…')}</span>
          : <Badge text={t('never run')} color="var(--text-3)" />}
        <span className="grow" />
        <button className="c2o-btn c2o-btn--sm" onClick={() => setShowPlacement(v => !v)}>{showPlacement ? t('Hide placement') : t('Placement')}</button>
        <button className="c2o-btn c2o-btn--primary c2o-btn--sm" disabled={runMut.isPending} onClick={() => runMut.mutate()}>
          {runMut.isPending ? t('Running…') : run ? t('Re-run') : t('Run')}
        </button>
      </div>
      {error && <div className="c-alarm t-12">{error}</div>}
      {run?.status === 'failed' && s.error && <div className="c-alarm t-12">{t('Last run failed: {{error}}', { error: s.error })}</div>}
      {!!s.warnings?.length && (
        <ul className="m-0 pl-4 c-caution t-12">
          {s.warnings.map((w, i) => <li key={i}>{w}</li>)}
        </ul>
      )}

      {/* ── 1. mass properties ─────────────────────────────────────────── */}
      <section>
        <div className="t-12 w-600 mb-1">{t('1 · Mass properties')}</div>
        {run?.status === 'ok' && (
          <div className="flex gap-2 wrap">
            <SummaryCard label={t('Total mass')} value={fmt(s.mp_total_mass_kg, 3)} unit="kg" sub={t('{{placed}} placed · {{auto}} auto', { placed: s.placed ?? '?', auto: s.mp_auto_placed_count ?? s.auto_placed ?? 0 })} />
            <SummaryCard label={t('CoM (x, y, z)')} value={mp ? mp.com_m.map(v => (v * 1000).toFixed(1)).join(', ') : '—'} unit="mm"
                         sub={s.envelope_m ? t('envelope {{dims}} mm', { dims: s.envelope_m.map(v => (v * 1000).toFixed(0)).join(' × ') }) : undefined} />
            <SummaryCard label={t('CP–CG offset')} value={fmt((s.mp_cp_cg_offset_m ?? 0) * 1000, 1)} unit="mm"
                         tone={offsetPct === null ? undefined : offsetPct > 2 ? 'var(--status-caution)' : 'var(--status-ok)'}
                         sub={offsetPct !== null ? t('{{pct}} % of max dimension (warn > 2 %)', { pct: offsetPct.toFixed(1) }) : undefined} />
            <SummaryCard label="Ixx / Iyy / Izz" value={mp ? [mp.inertia.ixx, mp.inertia.iyy, mp.inertia.izz].map(v => v.toFixed(4)).join(' / ') : '—'} unit="kg m²"
                         sub={mp ? t('principal {{values}}', { values: mp.principal.map(v => v.toFixed(4)).join(' / ') }) : undefined} />
          </div>
        )}
        {mp && (
          <table className="c2o-table c2o-table--dense">
            <thead><tr><th>{t('tensor')}</th><th className="num">x</th><th className="num">y</th><th className="num">z</th></tr></thead>
            <tbody>
              <tr><td>x</td><td className="num">{mp.inertia.ixx.toFixed(5)}</td><td className="num">{mp.inertia.ixy.toFixed(5)}</td><td className="num">{mp.inertia.ixz.toFixed(5)}</td></tr>
              <tr><td>y</td><td className="num">{mp.inertia.ixy.toFixed(5)}</td><td className="num">{mp.inertia.iyy.toFixed(5)}</td><td className="num">{mp.inertia.iyz.toFixed(5)}</td></tr>
              <tr><td>z</td><td className="num">{mp.inertia.ixz.toFixed(5)}</td><td className="num">{mp.inertia.iyz.toFixed(5)}</td><td className="num">{mp.inertia.izz.toFixed(5)}</td></tr>
            </tbody>
          </table>
        )}
        {(showPlacement || (!run && placement)) && (
          <div className="mt-1">
            {placementQ.isLoading && <span className="c-2">{t('loading placement…')}</span>}
            {placement && (
              <>
                <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: 2 }}>
                  {t('Positions in m, body frame with the origin at the envelope corner, +z along the stack · envelope {{source}}', { source: placement.envelope_source })}
                  {placement.auto_placed.length > 0 && <> · <span className="c-caution">{t('{{n}} auto-placed', { n: placement.auto_placed.length })}</span></>}
                </div>
                <table className="c2o-table c2o-table--dense">
                  <thead>
                    <tr><th>{t('Element')}</th><th className="num">kg</th><th className="num">mm</th><th className="num">x</th><th className="num">y</th><th className="num">z</th><th>{t('Source')}</th></tr>
                  </thead>
                  <tbody>
                    {placement.items.map(it => (
                      <PositionRow key={`${it.element_id}-${it.position_m.join(',')}-${it.source}`} item={it} busy={posMut.isPending}
                                   onSave={(id, pos) => posMut.mutate({ id, pos })} />
                    ))}
                  </tbody>
                </table>
                {'warnings' in placement && placement.warnings.map((w, i) => <div key={i} className="c-caution t-12">{w}</div>)}
              </>
            )}
          </div>
        )}
        {conflicts.some(c => c.code === 'AOCS_CG_OFFSET_HIGH') && (
          <div className="mt-1"><ConflictList conflicts={conflicts.filter(c => c.code === 'AOCS_CG_OFFSET_HIGH')} empty="" /></div>
        )}
      </section>

      {/* ── 2. AOCS ────────────────────────────────────────────────────── */}
      {aocs && (
        <section>
          <div className="t-12 w-600 mb-1">{t('2 · AOCS — disturbances, momentum, pointing')}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.5rem' }}>
            <div className="c2o-card">
              <SVGBarChart title={t('Disturbance torques [µN m]')} data={torqueBars} height={170} width={320} unit="" />
              <div className="t-12 c-2">
                {t('{{alt}} km · {{body}} · dipole {{dipole}} A m² · offset {{offset}} mm · RSS {{rss}} N m', {
                  alt: aocs.inputs.altitude_km, body: aocs.inputs.body, dipole: aocs.inputs.residual_dipole_am2,
                  offset: fmt(aocs.inputs.cp_cg_offset_used_m * 1000, 1), rss: sci(aocs.torques_nm.rss),
                })}
              </div>
            </div>
            <div className="stack gap-2">
              <MarginGauge label={t('Wheel momentum per orbit')} value={aocs.momentum_per_orbit_nms} limit={aocs.wheel_capacity_nms} unit="N m s" digits={4}
                           marginText={t('{{value}} % margin', { value: `${aocs.wheel_margin_pct >= 0 ? '+' : ''}${fmt(aocs.wheel_margin_pct, 0)}` })} tone={wheelTone} />
              <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginTop: -4 }}>{t('capacity from {{source}} · {{n}} desaturation/orbit', { source: aocs.wheel_source, n: aocs.inputs.desaturations_per_orbit })}</div>
              <MarginGauge label={t('Pointing estimate')} value={aocs.pointing_est_deg} limit={aocs.pointing_req_deg} unit="deg" digits={3}
                           marginText={aocs.pointing_margin_deg === null ? t('no requirement') : t('{{value}} deg margin', { value: `${aocs.pointing_margin_deg >= 0 ? '+' : ''}${fmt(aocs.pointing_margin_deg, 3)}` })} tone={pointTone} />
              <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginTop: -4 }}>
                {t('knowledge {{knowledge}} ({{source}}) · control {{control}} · actuator {{actuator}} deg', {
                  knowledge: fmt(aocs.pointing_budget.knowledge_deg, 3), source: aocs.inputs.knowledge_source,
                  control: fmt(aocs.pointing_budget.control_deg, 4), actuator: fmt(aocs.pointing_budget.actuator_deg, 3),
                })}
                {aocs.pointing_req_deg !== null && <> · {t('requirement from {{source}}', { source: aocs.pointing_req_source })}</>}
              </div>
            </div>
          </div>
          <div className="mt-1">
            <ConflictList conflicts={aocsConflicts.filter(c => c.code !== 'AOCS_CG_OFFSET_HIGH')} empty={t('Wheel momentum and pointing within margins.')} />
          </div>
        </section>
      )}

      {/* ── 3. thermal ─────────────────────────────────────────────────── */}
      {thermal && (
        <section>
          <div className="t-12 w-600 mb-1">
            {t('3 · Thermal network — {{nodes}} nodes, {{conductances}} conductances', { nodes: thermal.nodes.length, conductances: thermal.conductances.length })}
            <span style={{ color: marginTone(thermal.worst_margin_c), marginLeft: 8 }}>{t('worst margin {{value}} K', { value: fmt(thermal.worst_margin_c, 1) })}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '0.5rem' }}>
            <div style={{ overflowX: 'auto' }}>
              <table className="c2o-table c2o-table--dense">
                <thead>
                  <tr>
                    <th>{t('Node')}</th><th className="num">{t('P hot')}</th><th className="num">{t('T hot')}</th><th className="num">{t('T cold')}</th>
                    <th className="num">{t('allowable')}</th><th className="num">{t('margin hot')}</th><th className="num">{t('margin cold')}</th>
                  </tr>
                </thead>
                <tbody>
                  {thermal.nodes.map(n => (
                    <tr key={n.element_id} style={{ opacity: n.kind === 'structure' ? 0.75 : 1 }}>
                      <td>
                        <span style={{ paddingLeft: n.kind === 'component' ? 10 : 0 }}>{n.name}</span>
                        <span style={{ color: 'var(--text-secondary)', fontSize: fs.label, marginLeft: 4 }}>{t(NODE_KINDS[n.kind] ?? n.kind)}</span>
                      </td>
                      <td className="num">{fmt(n.dissipation_hot_w, 1)} W</td>
                      <td className="num">{fmt(n.t_hot_c, 1)}</td>
                      <td className="num">{fmt(n.t_cold_c, 1)}</td>
                      <td className="num" title={t('from {{source}}', { source: n.allow_source })}>{n.allow_min_c} … {n.allow_max_c} °C</td>
                      <td className="num" style={{ color: marginTone(n.margin_hot_c), fontWeight: n.margin_hot_c < 0 ? 700 : 400 }}>{n.margin_hot_c >= 0 ? '+' : ''}{fmt(n.margin_hot_c, 1)} K</td>
                      <td className="num" style={{ color: marginTone(n.margin_cold_c), fontWeight: n.margin_cold_c < 0 ? 700 : 400 }}>{n.margin_cold_c >= 0 ? '+' : ''}{fmt(n.margin_cold_c, 1)} K</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginTop: 2 }}>
                {t('hot = sunlit steady state at peak power · cold = minimum over a periodic orbit at safe-mode power ({{pct}} %) · ε {{eps}} · α {{alpha}} · {{area}} cm² external', {
                  pct: fmt(thermal.inputs.safe_power_fraction * 100, 0), eps: thermal.inputs.emissivity, alpha: thermal.inputs.absorptivity,
                  area: fmt(thermal.inputs.external_area_m2 * 1e4, 0),
                })}
              </div>
            </div>
            <div className="c2o-card">
              <SVGLineChart title={t('Cold-case orbit (periodic)')} series={thermalSeries} bands={eclipseBand} xLabel="min" yLabel="°C" height={220} />
            </div>
          </div>
          <div className="mt-1">
            <ConflictList conflicts={thermalConflicts} empty={t('Every node inside its allowable range in both cases.')} />
          </div>
        </section>
      )}
    </div>
  )
}

export default PhysicsClosurePanel
