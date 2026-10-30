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

const API = '/api'
const ANALYSIS = 'physics'

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444', major: '#f97316', minor: '#eab308', warning: '#f59e0b', info: '#3b82f6',
}
// English text is the i18n key
const SEVERITY_LABELS: Record<string, string> = {
  critical: 'critical', major: 'major', minor: 'minor', warning: 'warning', info: 'info',
}
// English text is the i18n key
const NODE_KINDS: Record<string, string> = { structure: 'structure', subsystem: 'subsystem', component: 'component' }
const NODE_PALETTE = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f43f5e', '#84cc16', '#60a5fa', '#a78bfa']

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
  return m < 0 ? '#ef4444' : m < warn ? '#f59e0b' : '#10b981'
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
const th: React.CSSProperties = { padding: '0.15rem 0.4rem', textAlign: 'left', fontSize: '0.58rem', color: 'var(--text-secondary)', textTransform: 'uppercase', whiteSpace: 'nowrap' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.12rem 0.4rem', fontSize: '0.64rem', borderBottom: '1px solid var(--border)' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'ui-monospace, monospace' }
const posInput: React.CSSProperties = {
  width: 52, fontSize: '0.6rem', padding: '0.05rem 0.2rem', background: 'var(--bg-primary)', border: '1px solid var(--border)',
  borderRadius: 3, color: 'var(--text-primary)', fontFamily: 'ui-monospace, monospace', textAlign: 'right',
}

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

/** Horizontal margin gauge: 0 at the left edge of the bar, requirement / capacity marked, value bar coloured by margin. */
function MarginGauge({ label, value, limit, unit, marginText, tone, digits = 3 }: {
  label: string; value: number; limit: number | null; unit: string; marginText: string; tone: string; digits?: number
}) {
  const { t } = useTranslation()
  const max = Math.max(value, limit ?? 0, 1e-12) * 1.25
  const vw = Math.min(100, value / max * 100)
  const lw = limit !== null ? Math.min(100, limit / max * 100) : null
  return (
    <div style={card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.58rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
        <span>{label}</span><span style={{ color: tone, fontWeight: 600 }}>{marginText}</span>
      </div>
      <div style={{ position: 'relative', height: 12, background: 'var(--bg-secondary, #1f2937)', borderRadius: 3, marginTop: 4 }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${vw}%`, background: tone, opacity: 0.8, borderRadius: 3 }} />
        {lw !== null && <div title={t('limit {{value}} {{unit}}', { value: fmt(limit, digits), unit })} style={{ position: 'absolute', left: `${lw}%`, top: -2, bottom: -2, width: 2, background: '#e5e7eb' }} />}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.58rem', marginTop: 2, fontFamily: 'ui-monospace, monospace' }}>
        <span>{fmt(value, digits)} {unit}</span>
        <span style={{ color: 'var(--text-secondary)' }}>{limit !== null ? t('limit {{value}} {{unit}}', { value: fmt(limit, digits), unit }) : t('no limit')}</span>
      </div>
    </div>
  )
}

function ConflictList({ conflicts, empty }: { conflicts: AnalysisConflict[]; empty: string }) {
  const { t } = useTranslation()
  if (conflicts.length === 0) return <div style={{ color: '#10b981', fontSize: '0.64rem' }}>{empty}</div>
  return (
    <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
      {conflicts.map(c => {
        const color = SEVERITY_COLORS[c.severity] || '#6b7280'
        return (
          <li key={c.id} style={{ ...card, borderLeft: `3px solid ${color}` }}>
            <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <Badge text={t(SEVERITY_LABELS[c.severity] ?? c.severity)} color={color} />
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.58rem', color: 'var(--text-secondary)' }}>{c.code}</span>
              <strong style={{ fontSize: '0.68rem' }}>{c.title}</strong>
            </div>
            {c.detail && <div style={{ fontSize: '0.62rem', color: 'var(--text-secondary)', marginTop: 2 }}>{c.detail}</div>}
            {c.suggested_fix && <div style={{ fontSize: '0.62rem', marginTop: 2 }}><span style={{ color: '#60a5fa' }}>{t('Fix:')} </span>{c.suggested_fix}</div>}
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
      <td style={td}>{item.name}<span style={{ color: 'var(--text-secondary)', fontSize: '0.56rem', marginLeft: 4 }}>{item.domain ?? ''}</span></td>
      <td style={tdR}>{fmt(item.mass_kg, 3)}</td>
      <td style={tdR}>{item.dims_m.map(d => (d * 1000).toFixed(0)).join(' × ')}</td>
      {vals.map((v, i) => (
        <td key={i} style={tdR}>
          <input style={posInput} value={v} onChange={e => setVals(prev => { const n = [...prev] as [string, string, string]; n[i] = e.target.value; return n })} />
        </td>
      ))}
      <td style={td}>
        <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
          <Badge text={auto ? t('auto') : t('explicit')} color={auto ? '#f59e0b' : '#10b981'} title={item.source} />
          {dirty && <button style={btn(true)} disabled={busy} onClick={() => onSave(item.element_id, [Number(vals[0]), Number(vals[1]), Number(vals[2])])}>{t('save')}</button>}
          {!auto && !dirty && <button style={btn()} disabled={busy} title={t('Clear the position (back to auto-stack)')} onClick={() => onSave(item.element_id, null)}>{t('clear')}</button>}
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
      { label: 'GG', value: tq.gravity_gradient * scale, color: '#3b82f6' },
      { label: t('Aero'), value: tq.aerodynamic * scale, color: '#06b6d4' },
      { label: 'SRP', value: tq.solar_pressure * scale, color: '#f59e0b' },
      { label: 'Mag', value: tq.magnetic * scale, color: '#8b5cf6' },
      { label: 'RSS', value: tq.rss * scale, color: '#e5e7eb' },
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
    from: series.thermal.transient.eclipse_start_s / 60, to: series.thermal.transient.period_s / 60, label: t('eclipse'), color: '#6b7280',
  }] : []

  if (!studyId) return <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{t('Select a study.')}</div>

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
    <div style={{ fontSize: '0.7rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
      {/* header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
        <strong style={{ fontSize: '0.74rem' }}>{t('Physics closure')}</strong>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.6rem' }}>{t('mass properties → AOCS · thermal network')}</span>
        {run ? (
          <>
            <Badge text={run.status === 'ok' ? t('last run {{ago}}', { ago: ago(run.finished_at, t) }) : t('run {{status}}', { status: run.status })} color={run.status === 'ok' ? '#10b981' : '#ef4444'} title={run.finished_at || undefined} />
            {run.stale && <Badge text={t('stale')} color="#f59e0b" title={t('The model (masses, positions, dimensions, power, orbit) changed since this run — re-run to refresh')} />}
          </>
        ) : runQ.isLoading ? <span style={{ color: 'var(--text-secondary)' }}>{t('loading…')}</span>
          : <Badge text={t('never run')} color="#6b7280" />}
        <span style={{ flex: 1 }} />
        <button style={btn()} onClick={() => setShowPlacement(v => !v)}>{showPlacement ? t('Hide placement') : t('Placement')}</button>
        <button style={btn(true)} disabled={runMut.isPending} onClick={() => runMut.mutate()}>
          {runMut.isPending ? t('Running…') : run ? t('Re-run') : t('Run')}
        </button>
      </div>
      {error && <div style={{ color: '#ef4444', fontSize: '0.64rem' }}>{error}</div>}
      {run?.status === 'failed' && s.error && <div style={{ color: '#ef4444', fontSize: '0.64rem' }}>{t('Last run failed: {{error}}', { error: s.error })}</div>}
      {!!s.warnings?.length && (
        <ul style={{ margin: 0, paddingLeft: '1rem', color: '#f59e0b', fontSize: '0.62rem' }}>
          {s.warnings.map((w, i) => <li key={i}>{w}</li>)}
        </ul>
      )}

      {/* ── 1. mass properties ─────────────────────────────────────────── */}
      <section>
        <div style={{ fontSize: '0.66rem', fontWeight: 600, marginBottom: '0.25rem' }}>{t('1 · Mass properties')}</div>
        {run?.status === 'ok' && (
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            <SummaryCard label={t('Total mass')} value={fmt(s.mp_total_mass_kg, 3)} unit="kg" sub={t('{{placed}} placed · {{auto}} auto', { placed: s.placed ?? '?', auto: s.mp_auto_placed_count ?? s.auto_placed ?? 0 })} />
            <SummaryCard label={t('CoM (x, y, z)')} value={mp ? mp.com_m.map(v => (v * 1000).toFixed(1)).join(', ') : '—'} unit="mm"
                         sub={s.envelope_m ? t('envelope {{dims}} mm', { dims: s.envelope_m.map(v => (v * 1000).toFixed(0)).join(' × ') }) : undefined} />
            <SummaryCard label={t('CP–CG offset')} value={fmt((s.mp_cp_cg_offset_m ?? 0) * 1000, 1)} unit="mm"
                         tone={offsetPct === null ? undefined : offsetPct > 2 ? '#f59e0b' : '#10b981'}
                         sub={offsetPct !== null ? t('{{pct}} % of max dimension (warn > 2 %)', { pct: offsetPct.toFixed(1) }) : undefined} />
            <SummaryCard label="Ixx / Iyy / Izz" value={mp ? [mp.inertia.ixx, mp.inertia.iyy, mp.inertia.izz].map(v => v.toFixed(4)).join(' / ') : '—'} unit="kg m²"
                         sub={mp ? t('principal {{values}}', { values: mp.principal.map(v => v.toFixed(4)).join(' / ') }) : undefined} />
          </div>
        )}
        {mp && (
          <table style={{ borderCollapse: 'collapse', marginTop: '0.3rem' }}>
            <thead><tr><th style={th}>{t('tensor')}</th><th style={thR}>x</th><th style={thR}>y</th><th style={thR}>z</th></tr></thead>
            <tbody>
              <tr><td style={td}>x</td><td style={tdR}>{mp.inertia.ixx.toFixed(5)}</td><td style={tdR}>{mp.inertia.ixy.toFixed(5)}</td><td style={tdR}>{mp.inertia.ixz.toFixed(5)}</td></tr>
              <tr><td style={td}>y</td><td style={tdR}>{mp.inertia.ixy.toFixed(5)}</td><td style={tdR}>{mp.inertia.iyy.toFixed(5)}</td><td style={tdR}>{mp.inertia.iyz.toFixed(5)}</td></tr>
              <tr><td style={td}>z</td><td style={tdR}>{mp.inertia.ixz.toFixed(5)}</td><td style={tdR}>{mp.inertia.iyz.toFixed(5)}</td><td style={tdR}>{mp.inertia.izz.toFixed(5)}</td></tr>
            </tbody>
          </table>
        )}
        {(showPlacement || (!run && placement)) && (
          <div style={{ marginTop: '0.3rem' }}>
            {placementQ.isLoading && <span style={{ color: 'var(--text-secondary)' }}>{t('loading placement…')}</span>}
            {placement && (
              <>
                <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginBottom: 2 }}>
                  {t('Positions in m, body frame with the origin at the envelope corner, +z along the stack · envelope {{source}}', { source: placement.envelope_source })}
                  {placement.auto_placed.length > 0 && <> · <span style={{ color: '#f59e0b' }}>{t('{{n}} auto-placed', { n: placement.auto_placed.length })}</span></>}
                </div>
                <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                  <thead>
                    <tr><th style={th}>{t('Element')}</th><th style={thR}>kg</th><th style={thR}>mm</th><th style={thR}>x</th><th style={thR}>y</th><th style={thR}>z</th><th style={th}>{t('Source')}</th></tr>
                  </thead>
                  <tbody>
                    {placement.items.map(it => (
                      <PositionRow key={`${it.element_id}-${it.position_m.join(',')}-${it.source}`} item={it} busy={posMut.isPending}
                                   onSave={(id, pos) => posMut.mutate({ id, pos })} />
                    ))}
                  </tbody>
                </table>
                {'warnings' in placement && placement.warnings.map((w, i) => <div key={i} style={{ color: '#f59e0b', fontSize: '0.6rem' }}>{w}</div>)}
              </>
            )}
          </div>
        )}
        {conflicts.some(c => c.code === 'AOCS_CG_OFFSET_HIGH') && (
          <div style={{ marginTop: '0.3rem' }}><ConflictList conflicts={conflicts.filter(c => c.code === 'AOCS_CG_OFFSET_HIGH')} empty="" /></div>
        )}
      </section>

      {/* ── 2. AOCS ────────────────────────────────────────────────────── */}
      {aocs && (
        <section>
          <div style={{ fontSize: '0.66rem', fontWeight: 600, marginBottom: '0.25rem' }}>{t('2 · AOCS — disturbances, momentum, pointing')}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.5rem' }}>
            <div style={card}>
              <SVGBarChart title={t('Disturbance torques [µN m]')} data={torqueBars} height={170} width={320} unit="" />
              <div style={{ fontSize: '0.58rem', color: 'var(--text-secondary)' }}>
                {t('{{alt}} km · {{body}} · dipole {{dipole}} A m² · offset {{offset}} mm · RSS {{rss}} N m', {
                  alt: aocs.inputs.altitude_km, body: aocs.inputs.body, dipole: aocs.inputs.residual_dipole_am2,
                  offset: fmt(aocs.inputs.cp_cg_offset_used_m * 1000, 1), rss: sci(aocs.torques_nm.rss),
                })}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <MarginGauge label={t('Wheel momentum per orbit')} value={aocs.momentum_per_orbit_nms} limit={aocs.wheel_capacity_nms} unit="N m s" digits={4}
                           marginText={t('{{value}} % margin', { value: `${aocs.wheel_margin_pct >= 0 ? '+' : ''}${fmt(aocs.wheel_margin_pct, 0)}` })} tone={wheelTone} />
              <div style={{ fontSize: '0.58rem', color: 'var(--text-secondary)', marginTop: -4 }}>{t('capacity from {{source}} · {{n}} desaturation/orbit', { source: aocs.wheel_source, n: aocs.inputs.desaturations_per_orbit })}</div>
              <MarginGauge label={t('Pointing estimate')} value={aocs.pointing_est_deg} limit={aocs.pointing_req_deg} unit="deg" digits={3}
                           marginText={aocs.pointing_margin_deg === null ? t('no requirement') : t('{{value}} deg margin', { value: `${aocs.pointing_margin_deg >= 0 ? '+' : ''}${fmt(aocs.pointing_margin_deg, 3)}` })} tone={pointTone} />
              <div style={{ fontSize: '0.58rem', color: 'var(--text-secondary)', marginTop: -4 }}>
                {t('knowledge {{knowledge}} ({{source}}) · control {{control}} · actuator {{actuator}} deg', {
                  knowledge: fmt(aocs.pointing_budget.knowledge_deg, 3), source: aocs.inputs.knowledge_source,
                  control: fmt(aocs.pointing_budget.control_deg, 4), actuator: fmt(aocs.pointing_budget.actuator_deg, 3),
                })}
                {aocs.pointing_req_deg !== null && <> · {t('requirement from {{source}}', { source: aocs.pointing_req_source })}</>}
              </div>
            </div>
          </div>
          <div style={{ marginTop: '0.3rem' }}>
            <ConflictList conflicts={aocsConflicts.filter(c => c.code !== 'AOCS_CG_OFFSET_HIGH')} empty={t('Wheel momentum and pointing within margins.')} />
          </div>
        </section>
      )}

      {/* ── 3. thermal ─────────────────────────────────────────────────── */}
      {thermal && (
        <section>
          <div style={{ fontSize: '0.66rem', fontWeight: 600, marginBottom: '0.25rem' }}>
            {t('3 · Thermal network — {{nodes}} nodes, {{conductances}} conductances', { nodes: thermal.nodes.length, conductances: thermal.conductances.length })}
            <span style={{ color: marginTone(thermal.worst_margin_c), marginLeft: 8 }}>{t('worst margin {{value}} K', { value: fmt(thermal.worst_margin_c, 1) })}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '0.5rem' }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                <thead>
                  <tr>
                    <th style={th}>{t('Node')}</th><th style={thR}>{t('P hot')}</th><th style={thR}>{t('T hot')}</th><th style={thR}>{t('T cold')}</th>
                    <th style={thR}>{t('allowable')}</th><th style={thR}>{t('margin hot')}</th><th style={thR}>{t('margin cold')}</th>
                  </tr>
                </thead>
                <tbody>
                  {thermal.nodes.map(n => (
                    <tr key={n.element_id} style={{ opacity: n.kind === 'structure' ? 0.75 : 1 }}>
                      <td style={td}>
                        <span style={{ paddingLeft: n.kind === 'component' ? 10 : 0 }}>{n.name}</span>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.56rem', marginLeft: 4 }}>{t(NODE_KINDS[n.kind] ?? n.kind)}</span>
                      </td>
                      <td style={tdR}>{fmt(n.dissipation_hot_w, 1)} W</td>
                      <td style={tdR}>{fmt(n.t_hot_c, 1)}</td>
                      <td style={tdR}>{fmt(n.t_cold_c, 1)}</td>
                      <td style={tdR} title={t('from {{source}}', { source: n.allow_source })}>{n.allow_min_c} … {n.allow_max_c} °C</td>
                      <td style={{ ...tdR, color: marginTone(n.margin_hot_c), fontWeight: n.margin_hot_c < 0 ? 700 : 400 }}>{n.margin_hot_c >= 0 ? '+' : ''}{fmt(n.margin_hot_c, 1)} K</td>
                      <td style={{ ...tdR, color: marginTone(n.margin_cold_c), fontWeight: n.margin_cold_c < 0 ? 700 : 400 }}>{n.margin_cold_c >= 0 ? '+' : ''}{fmt(n.margin_cold_c, 1)} K</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ fontSize: '0.58rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                {t('hot = sunlit steady state at peak power · cold = minimum over a periodic orbit at safe-mode power ({{pct}} %) · ε {{eps}} · α {{alpha}} · {{area}} cm² external', {
                  pct: fmt(thermal.inputs.safe_power_fraction * 100, 0), eps: thermal.inputs.emissivity, alpha: thermal.inputs.absorptivity,
                  area: fmt(thermal.inputs.external_area_m2 * 1e4, 0),
                })}
              </div>
            </div>
            <div style={card}>
              <SVGLineChart title={t('Cold-case orbit (periodic)')} series={thermalSeries} bands={eclipseBand} xLabel="min" yLabel="°C" height={220} />
            </div>
          </div>
          <div style={{ marginTop: '0.3rem' }}>
            <ConflictList conflicts={thermalConflicts} empty={t('Every node inside its allowable range in both cases.')} />
          </div>
        </section>
      )}
    </div>
  )
}

export default PhysicsClosurePanel
