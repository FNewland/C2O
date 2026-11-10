/**
 * ImpactPreview (wave 3, 3.L6; negotiation #3): "who is affected" by a proposed change.
 *
 * POST /api/studies/{id}/impact/preview evaluates the change as a dry run (nothing is written)
 * and returns the Δ of every key number that moves (roll-up, data budget, energy, contacts,
 * disposal, allocations) with the seat that owns it. The card groups the lines by seat, so each
 * seat sees what the change asks of it before anyone accepts it.
 *
 * Mount points (one line each, by the host's owner): the pending-change card in
 * seats/SeatDrawer.tsx (D), the proposal cards of Modes (H) and Budget (A), the change records of
 * ChangesPanel (L) and the change-control card (D). Usage:
 *
 *   <ImpactPreview studyId={sid} change={{ kind: 'station', action: 'add', name: 'GS Inuvik', lat: 68.36, lon: -133.72 }} />
 *   <ImpactPreview studyId={sid} change={{ kind: 'pending_change', id: pc.id }} compact />
 *   <ImpactPreview studyId={sid} changeCode="ECP-01" />          // the record's own preview specs
 */
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Note, Tag } from './ui'
import { seatLabel } from '../seats/api'

export interface ImpactLine {
  key: string; before: unknown; after: unknown; delta: number | null; unit?: string; source?: string
  owner_seat: string; label?: string; note?: Record<string, unknown>
}
export interface ImpactResult {
  kind: string; dry_run: boolean; lines: ImpactLine[]; seats: Array<{ seat: string; keys: string[] }>
  applied?: unknown; ripple?: { mode: string; from_pct: number; to_pct: number; rule?: string } | null
  change_code?: string
}

/** A proposed change (see services/impact_preview.py for the kinds). */
export type ImpactChange = Record<string, unknown> & { kind: string }

// English text is the i18n key: literal t() calls so the i18n check sees every label.
export function keyLabel(t: TFunction, key: string): string {
  switch (key) {
    case 'mass.cbe_kg': return t('Mass, current best estimate')
    case 'mass.with_maturity_kg': return t('Mass with maturity margins')
    case 'mass.with_system_margin_kg': return t('Mass with system margin')
    case 'mass.margin_to_limit_kg': return t('Mass margin to the limit')
    case 'power.orbit_average_w': return t('Orbit-average power')
    case 'power.orbit_average_with_maturity_w': return t('Orbit-average power with maturity margins')
    case 'power.orbit_average_with_margin_w': return t('Orbit-average power with system margin')
    case 'power.comms_orbit_average_w': return t('Communications orbit-average load')
    case 'modes.downlink_share_pct': return t('Downlink share of the orbit')
    case 'modes.downlink_share_proposed_pct': return t('Downlink share from the contact time')
    case 'modes.imaging_share_pct': return t('Imaging share of the orbit')
    case 'energy.worst_dod_percent': return t('Worst depth of discharge')
    case 'energy.operational_balance_wh': return t('Energy balance of the operational orbit')
    case 'data.capacity_mb_per_day': return t('Downlink capacity')
    case 'data.demand_mb_per_day': return t('Downlink demand')
    case 'data.margin_pct': return t('Data margin')
    case 'data.science_delivered_mb_per_day': return t('Science delivered')
    case 'contacts.union_min_per_day': return t('Contact time (union of stations)')
    case 'contacts.windows_per_day': return t('Contact windows per day')
    case 'contacts.longest_gap_h': return t('Longest gap without contact')
    case 'contacts.stations': return t('Stations in the network')
    case 'link.design_margin_db': return t('Link margin of the design case')
    case 'disposal.lifetime_with_sail_worst_y': return t('Lifetime with the sail (worst cycle)')
    case 'disposal.lifetime_without_sail_worst_y': return t('Lifetime without the sail (worst cycle)')
    case 'disposal.compliant': return t('Disposal compliant')
    case 'allocation.mass': return t('Mass allocation')
    case 'allocation.power': return t('Power allocation')
    case 'allocation.mass.margin': return t('Margin to the mass allocation')
    case 'allocation.power.margin': return t('Margin to the power allocation')
    default:
      if (key.startsWith('contacts.station.')) return t('Contact time of {{station}}', { station: key.slice(17).replace(/_min_per_day$/, '').replace(/_/g, ' ') })
      return key
  }
}

function fmt(v: unknown, unit?: string): string {
  if (v === null || v === undefined) return '—'
  if (Array.isArray(v)) return v.join(', ')
  if (typeof v === 'boolean') return v ? '✓' : '✗'
  if (typeof v === 'number') return `${Math.abs(v) >= 100 ? v.toFixed(1) : Number(v.toPrecision(4))}${unit && unit !== '' ? ` ${unit}` : ''}`
  return String(v)
}

function fmtDelta(d: number | null, unit?: string): string {
  if (d === null || d === undefined) return ''
  const s = d > 0 ? '+' : d < 0 ? '−' : '±'
  return `${s}${fmt(Math.abs(d), unit)}`
}

export function useImpactPreview(studyId: string | null, change: ImpactChange | ImpactChange[] | null, changeCode?: string) {
  const [data, setData] = useState<ImpactResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const body = useMemo(() => change ? JSON.stringify(Array.isArray(change) ? { changes: change } : change) : null, [change])
  useEffect(() => {
    if (!studyId || (!body && !changeCode)) { setData(null); return }
    let cancelled = false
    setLoading(true); setError(null)
    const url = changeCode
      ? `/api/studies/${encodeURIComponent(studyId)}/changes/${encodeURIComponent(changeCode)}/preview`
      : `/api/studies/${encodeURIComponent(studyId)}/impact/preview`
    fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: changeCode ? '{}' : body! })
      .then(async r => {
        const j = await r.json().catch(() => ({}))
        if (cancelled) return
        if (!r.ok) { setError(typeof j.detail === 'string' ? j.detail : `${r.status}`); setData(null); return }
        setData(j)
      })
      .catch(e => { if (!cancelled) setError(String(e)) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [studyId, body, changeCode])
  return { data, error, loading }
}

/** The preview card: one block per affected seat, before → after (Δ) for each key number. */
export function ImpactPreview({ studyId, change, changeCode, compact, title }: {
  studyId: string | null; change?: ImpactChange | ImpactChange[] | null; changeCode?: string; compact?: boolean; title?: string
}) {
  const { t, i18n } = useTranslation()
  const { data, error, loading } = useImpactPreview(studyId, change ?? null, changeCode)
  if (loading) return <Note tone="info" role="status">{t('Evaluating the change (dry run)…')}</Note>
  if (error) return <Note tone="alarm" role="alert">{t('No impact preview: {{message}}', { message: error })}</Note>
  if (!data) return null
  const byKey = new Map(data.lines.map(l => [l.key, l]))
  return (
    <section className="stack gap-1" aria-label={title ?? t('Who is affected')} data-testid="impact-preview">
      <div className="flex ai-c gap-2 wrap">
        <strong className="t-12">{title ?? t('Who is affected')}</strong>
        <Tag>{t('Dry run: nothing is saved')}</Tag>
        {data.seats.length > 0 && <span className="t-12 c-2">{t('{{count}} seats affected', { count: data.seats.length, defaultValue_one: '{{count}} seat affected' })}</span>}
      </div>
      {data.ripple && (
        <p className="t-12 c-2 m-0">{t('Downlink share re-proposed from the contact time: {{from}} % → {{to}} % ({{rule}}).', {
          from: data.ripple.from_pct, to: data.ripple.to_pct, rule: data.ripple.rule ?? '' })}</p>
      )}
      {data.lines.length === 0 && <p className="t-12 c-2 m-0">{t('No key number moves: nobody else is affected.')}</p>}
      {data.seats.map(s => (
        <div key={s.seat} className="stack gap-0" data-testid={`impact-seat-${s.seat}`}>
          <span className="t-12 w-600">{seatLabel(s.seat, i18n.language)}</span>
          <table className="c2o-table c2o-table--dense t-12">
            {!compact && <thead><tr><th>{t('Key number')}</th><th>{t('Before')}</th><th>{t('After')}</th><th>{t('Change')}</th></tr></thead>}
            <tbody>
              {s.keys.map(k => {
                const l = byKey.get(k)
                if (!l) return null
                return (
                  <tr key={k}>
                    <td title={k}>{keyLabel(t, k)}{l.label ? ` (${l.label})` : ''}</td>
                    <td className="mono">{fmt(l.before, l.unit)}</td>
                    <td className="mono w-600">{fmt(l.after, l.unit)}</td>
                    <td className="mono">{fmtDelta(l.delta, l.unit)}{l.note && typeof l.note.margin === 'number'
                      ? ` · ${t('margin')} ${fmt(l.note.margin as number, l.unit)}` : ''}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  )
}
