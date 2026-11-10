/**
 * SensitivityView — what the margin does when one value moves, on the study's own models
 * (wave 3, 3.H5; GET /api/studies/{id}/sensitivity and /sensitivity/altitude, services/sensitivity.py).
 *
 * Data views: the daily data-budget margin against the science target, the compression ratio, the
 * rate tier and the imaging share (with the orbit-average power and the depth of discharge); the
 * altitude view: GSD, swath, contact, decay with and without the drag device, eclipse and link margin,
 * with the regulatory lines (600 km apogee, 5-year disposal). Mounted on the Data budget page (H) and
 * in Decide (D, one line). The numbers are the services' own; nothing is typed here.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { DataTable, Note, NoData, Panel, StatusBadge, Tabs, fmtNum, type Status } from './ui'

type Param = 'science_target' | 'compression_ratio' | 'rate_tier' | 'imaging_share' | 'altitude'
// English text is the i18n key
const PARAM_LABELS: Record<Param, string> = {
  science_target: 'Science target', compression_ratio: 'Compression', rate_tier: 'Rate tier',
  imaging_share: 'Imaging share', altitude: 'Altitude',
}
const PARAMS = Object.keys(PARAM_LABELS) as Param[]

interface Point {
  x: number; margin_pct: number | null; status: string; capacity_mb?: number | null; demand_mb?: number | null
  tier?: string | null; largest_with_margin_mb_per_day?: number | null; delivered_mb?: number | null
  orbit_average_cbe_w?: number | null; dod_percent?: number | null; power_status?: string | null
}
interface DataSens {
  parameter: string; unit: string; margin_required_percent: number; status: string; rate_bps: number
  baseline: Point & { x: number | null }; points: Point[]; largest_with_margin_mb_per_day?: number | null
  needed_for_target?: number | null; raw_mb_per_day?: number | null; label: { en: string; fr: string }; warnings: string[]
}
interface AltPoint {
  altitude_km: number; gsd_m: number | null; swath_km: number | null; union_min_per_day: number | null
  longest_gap_h: number | null; eclipse_max_min: number; link_margin_db: number | null; apogee_ok: boolean
  with_device_nominal_y?: number; with_device_weak_y?: number; without_device_strong_y?: number; without_device_weak_y?: number
  disposal_ok: boolean
}
interface AltSens {
  baseline_altitude_km: number; points: AltPoint[]
  lines: { apogee_without_propulsion_km: number; disposal_years: number; max_start_altitude_5y_weak_km?: number
    max_start_altitude_5y_nominal_km?: number; max_start_altitude_5y_without_device_strong_km?: number }
  basis: { mass_kg: number; device_area_m2: number | null; start_year: number; stations: string[]; design_link_margin_db: number | null }
  warnings: string[]
}

const get = <T,>(path: string): Promise<T> => fetch(`/api${path}`).then(async r => {
  if (!r.ok) throw new Error(`${r.status}`)
  return r.json() as Promise<T>
})

const tone = (s: string | null | undefined): Status => s === 'pass' ? 'ok' : s === 'warn' ? 'caution' : s === 'fail' ? 'alarm' : 'nodata'

function fmtX(p: string, x: number | null | undefined): string {
  if (x == null) return '–'
  if (p === 'imaging_share') return `${fmtNum(x * 100, 1)} %`
  if (p === 'rate_tier') return `${fmtNum(x / 1000, 1)} kbit/s`
  if (p === 'compression_ratio') return `${fmtNum(x, 2)}:1`
  return fmtNum(x, 1)
}

/** A small margin curve: margin % against the swept value, the required margin as a line, the baseline marked. */
function MarginStrip({ points, need, base, param }: { points: Point[]; need: number; base: number | null; param: string }) {
  const { t } = useTranslation()
  const pts = points.filter(p => p.margin_pct != null)
  if (pts.length < 2) return null
  const W = 520, H = 120, L = 40, R = 10, T = 8, Bm = 22
  const xs = pts.map(p => p.x), ys = pts.map(p => p.margin_pct as number)
  const x0 = Math.min(...xs), x1 = Math.max(...xs)
  const y0 = Math.min(0, ...ys, need), y1 = Math.max(need, ...ys)
  const sx = (x: number) => L + (x1 === x0 ? 0 : (x - x0) / (x1 - x0)) * (W - L - R)
  const sy = (y: number) => T + (y1 === y0 ? 0 : (y1 - y) / (y1 - y0)) * (H - T - Bm)
  const path = pts.map((p, i) => `${i ? 'L' : 'M'}${sx(p.x).toFixed(1)},${sy(p.margin_pct as number).toFixed(1)}`).join(' ')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: W }} role="img" data-testid="sensitivity-strip"
      aria-label={t('Margin against the parameter; the line is the required margin')}>
      <line x1={L} x2={W - R} y1={sy(0)} y2={sy(0)} stroke="currentColor" strokeOpacity={0.3} />
      <line x1={L} x2={W - R} y1={sy(need)} y2={sy(need)} stroke="var(--status-caution)" strokeDasharray="4 3" />
      <text x={W - R} y={sy(need) - 3} textAnchor="end" fontSize={10} fill="currentColor">{t('{{m}} % required', { m: need })}</text>
      {base != null && base >= x0 && base <= x1 &&
        <line x1={sx(base)} x2={sx(base)} y1={T} y2={H - Bm} stroke="currentColor" strokeOpacity={0.5} strokeDasharray="2 2" />}
      <path d={path} fill="none" stroke="var(--status-info, currentColor)" strokeWidth={2} />
      {pts.map((p, i) => <circle key={i} cx={sx(p.x)} cy={sy(p.margin_pct as number)} r={3}
        fill={p.status === 'pass' ? 'var(--status-ok)' : p.status === 'warn' ? 'var(--status-caution)' : 'var(--status-alarm)'} />)}
      <text x={L - 4} y={sy(y1) + 4} textAnchor="end" fontSize={10} fill="currentColor">{fmtNum(y1, 0)} %</text>
      <text x={L - 4} y={sy(y0)} textAnchor="end" fontSize={10} fill="currentColor">{fmtNum(y0, 0)} %</text>
      <text x={L} y={H - 6} fontSize={10} fill="currentColor">{fmtX(param, x0)}</text>
      <text x={W - R} y={H - 6} textAnchor="end" fontSize={10} fill="currentColor">{fmtX(param, x1)}</text>
    </svg>
  )
}

function DataSensitivity({ sid, param }: { sid: string; param: Exclude<Param, 'altitude'> }) {
  const { t, i18n } = useTranslation()
  const { data, error, isLoading } = useQuery<DataSens>({ queryKey: ['sensitivity', sid, param],
    queryFn: () => get(`/studies/${sid}/sensitivity?parameter=${param}`), staleTime: 30000 })
  if (isLoading) return <p className="t-13 c-2">{t('Loading…')}</p>
  if (error || !data) return <Note tone="alarm">{t('The sensitivity could not be computed: {{message}}', { message: String((error as Error)?.message ?? '') })}</Note>
  if (data.status === 'no_contact_plan') return <Note tone="caution">{t('No contact plan: add ground stations first.')}</Note>
  if (data.status === 'no_imaging_mode') return <Note tone="caution">{t('No imaging and nominal modes in the operational mix.')}</Note>
  const need = data.margin_required_percent
  return (
    <div className="stack gap-2">
      <p className="t-12 c-2 m-0">{i18n.language === 'fr' ? data.label.fr : data.label.en}{' · '}
        {t('baseline {{x}}: {{m}} % margin', { x: fmtX(param, data.baseline.x), m: data.baseline.margin_pct == null ? '–' : fmtNum(data.baseline.margin_pct, 1) })}</p>
      {param === 'science_target' && data.largest_with_margin_mb_per_day != null &&
        <p className="t-13 m-0" data-testid="largest-science">{t('Largest science volume that keeps {{m}} % margin: {{v}} MB/day at {{r}} kbit/s',
          { m: need, v: fmtNum(data.largest_with_margin_mb_per_day, 1), r: fmtNum(data.rate_bps / 1000, 1) })}</p>}
      {param === 'compression_ratio' && data.needed_for_target != null &&
        <p className="t-13 m-0">{t('The science target needs {{c}}:1 on the planned products ({{raw}} MB/day before compression).',
          { c: fmtNum(data.needed_for_target, 2), raw: fmtNum(data.raw_mb_per_day ?? 0, 2) })}</p>}
      <MarginStrip points={data.points} need={need} base={data.baseline.x} param={param} />
      <DataTable dense caption={t('Margin against {{p}}', { p: t(PARAM_LABELS[param]) })} rows={data.points} rowKey={r => String(r.x)}
        empty={<NoData label={t('no data')} />} columns={[
          { key: 'x', header: t(PARAM_LABELS[param]), render: r => <span className="mono">{param === 'rate_tier' && r.tier ? `${r.tier} · ` : ''}{fmtX(param, r.x)}</span> },
          ...(param === 'compression_ratio' ? [{ key: 'd', header: t('Delivered (MB/day)'), num: true, render: (r: Point) => fmtNum(r.delivered_mb ?? 0, 2) }] : []),
          { key: 'c', header: t('Capacity'), num: true, render: r => r.capacity_mb == null ? '–' : fmtNum(r.capacity_mb, 2) },
          { key: 'dm', header: t('Demand'), num: true, render: r => r.demand_mb == null ? '–' : fmtNum(r.demand_mb, 2) },
          { key: 'm', header: t('Margin'), num: true, render: r => <StatusBadge status={tone(r.status)}>{r.margin_pct == null ? '–' : `${fmtNum(r.margin_pct, 1)} %`}</StatusBadge> },
          ...(param === 'rate_tier' ? [{ key: 'l', header: t('Largest science with margin (MB/day)'), num: true,
            render: (r: Point) => r.largest_with_margin_mb_per_day == null ? '–' : fmtNum(r.largest_with_margin_mb_per_day, 1) }] : []),
          ...(param === 'imaging_share' ? [
            { key: 'p', header: t('Orbit average (W, CBE)'), num: true, render: (r: Point) => r.orbit_average_cbe_w == null ? '–' : fmtNum(r.orbit_average_cbe_w, 2) },
            { key: 'dod', header: t('Depth of discharge'), num: true, render: (r: Point) => r.dod_percent == null ? '–' : `${fmtNum(r.dod_percent, 1)} %` },
          ] : []),
        ]} />
    </div>
  )
}

function AltitudeSensitivity({ sid }: { sid: string }) {
  const { t } = useTranslation()
  const { data, error, isLoading } = useQuery<AltSens>({ queryKey: ['sensitivity', sid, 'altitude'],
    queryFn: () => get(`/studies/${sid}/sensitivity/altitude`), staleTime: 60000 })
  if (isLoading) return <p className="t-13 c-2">{t('Loading…')}</p>
  if (error || !data) return <Note tone="alarm">{t('The sensitivity could not be computed: {{message}}', { message: String((error as Error)?.message ?? '') })}</Note>
  const L = data.lines
  const y = (v: number | undefined) => v == null ? '–' : v >= 30 ? '> 30' : fmtNum(v, 1)
  return (
    <div className="stack gap-2">
      <p className="t-12 c-2 m-0">{t('Regulatory lines: apogee at most {{a}} km without propulsion; disposal within {{y}} years. With the drag device the 5-year limit is reached from {{w}} km (weak solar cycle) or {{n}} km (nominal).',
        { a: L.apogee_without_propulsion_km, y: L.disposal_years, w: L.max_start_altitude_5y_weak_km ?? '–', n: L.max_start_altitude_5y_nominal_km ?? '–' })}</p>
      <p className="t-12 c-3 m-0">{t('Decay for {{m}} kg from {{y}}; stations {{s}}.', { m: fmtNum(data.basis.mass_kg, 2), y: fmtNum(data.basis.start_year, 1), s: data.basis.stations.join(', ') })}</p>
      <DataTable dense caption={t('Altitude sweep')} rows={data.points} rowKey={r => String(r.altitude_km)}
        rowClassName={r => r.altitude_km === data.baseline_altitude_km ? 'is-selected' : ''} columns={[
          { key: 'h', header: t('Altitude (km)'), num: true, render: r => <span className="mono">{fmtNum(r.altitude_km, 0)}</span> },
          { key: 'g', header: t('GSD (m)'), num: true, render: r => r.gsd_m == null ? '–' : fmtNum(r.gsd_m, 1) },
          { key: 's', header: t('Swath (km)'), num: true, render: r => r.swath_km == null ? '–' : fmtNum(r.swath_km, 0) },
          { key: 'c', header: t('Contact (min/day)'), num: true, render: r => r.union_min_per_day == null ? '–' : fmtNum(r.union_min_per_day, 1) },
          { key: 'e', header: t('Longest eclipse (min)'), num: true, render: r => fmtNum(r.eclipse_max_min, 1) },
          { key: 'l', header: t('Link margin (dB)'), num: true, render: r => r.link_margin_db == null ? '–' : fmtNum(r.link_margin_db, 1) },
          { key: 'dn', header: t('Decay with device, nominal / weak (y)'), num: true, render: r => `${y(r.with_device_nominal_y)} / ${y(r.with_device_weak_y)}` },
          { key: 'dw', header: t('Decay without device, strong / weak (y)'), num: true, render: r => `${y(r.without_device_strong_y)} / ${y(r.without_device_weak_y)}` },
          { key: 'ok', header: t('Regulatory'), render: r => <StatusBadge status={r.apogee_ok && r.disposal_ok ? 'ok' : 'alarm'}>
            {!r.apogee_ok ? t('Apogee above the limit') : !r.disposal_ok ? t('Disposal too slow') : t('Within the limits')}</StatusBadge> },
        ]} />
    </div>
  )
}

export function SensitivityView({ studyId, initial = 'science_target' }: { studyId: string | null; initial?: Param }) {
  const { t } = useTranslation()
  const [param, setParam] = useState<Param>(initial)
  if (!studyId) return null
  return (
    <Panel title={t('Sensitivity')} meta={t('on the study’s own models')}>
      <Tabs idBase="sensitivity" variant="segmented" label={t('Sensitivity parameter')} value={param} onChange={setParam}
        items={PARAMS.map(p => ({ id: p, label: t(PARAM_LABELS[p]) }))} />
      <div className="pt-2">
        {param === 'altitude' ? <AltitudeSensitivity sid={studyId} /> : <DataSensitivity sid={studyId} param={param} />}
      </div>
    </Panel>
  )
}

export default SensitivityView
