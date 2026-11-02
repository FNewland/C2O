/**
 * MarginBar: a budget value drawn against its allocation (brief §1.1:
 * picture first, the number beside it).
 *
 *   ┌ label ─────┬ track ─────────────────────────┬ readout ─────────────┐
 *   │ Payload    │ ████████░░░│                    │ 1.16 / 1.30 kg  11 % │
 *   └────────────┴ nominal ▲ margin ▲ allocation ──┴──────────────────────┘
 *
 * Solid = nominal (current best estimate), hatched = maturity margin on top
 * of it, the dark tick = allocation. Grey while the margin to allocation is
 * healthy, caution below `cautionBelowPct` (20 % = the ECSS system margin, for
 * the system line; element lines use a smaller threshold), alarm at or below 0. Pass a shared `scaleMax` so rows
 * in one list are comparable.
 */
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { cx, fmtNum, marginStatus, marginToAllocation } from './util'
import { StatusBadge } from './StatusBadge'

export interface MarginBarProps {
  label: ReactNode
  /** Current best estimate without margin. */
  nominal: number | null | undefined
  /** Nominal plus maturity margin. Defaults to nominal. */
  withMargin?: number | null
  allocation?: number | null
  unit: string
  scaleMax?: number
  /** The headline row of a list: taller bar, larger figures. */
  lead?: boolean
  digits?: number
  /** Below this margin to allocation (percent) the bar turns caution. */
  cautionBelowPct?: number
  title?: string
}

export function MarginBar({ label, nominal, withMargin, allocation, unit, scaleMax, lead, digits = 2, cautionBelowPct = 20, title }: MarginBarProps) {
  const { t } = useTranslation()
  const nom = nominal ?? null
  const wm = withMargin ?? nom
  const pct = marginToAllocation(wm, allocation)
  const status = marginStatus(pct, cautionBelowPct)
  const max = Math.max(scaleMax ?? 0, (allocation ?? 0) * 1.12, (wm ?? 0) * 1.05, 1e-9)
  const x = (v: number) => `${Math.max(0, Math.min(100, v / max * 100))}%`
  const tone = status === 'alarm' ? 'c2o-mbar--alarm' : status === 'caution' ? 'c2o-mbar--caution' : ''
  const hasValue = nom != null && (nom > 0 || (wm ?? 0) > 0)

  let summary: string
  if (!hasValue) summary = t('no data')
  else if (allocation == null) summary = t('{{value}} {{unit}}, no allocation', { value: fmtNum(wm!, digits), unit })
  else summary = t('{{value}} of {{alloc}} {{unit}}, margin {{pct}} %', { value: fmtNum(wm!, digits), alloc: fmtNum(allocation, digits), unit, pct: pct!.toFixed(0) })

  return (
    <div className={cx('c2o-mbar', lead && 'c2o-mbar--lead', tone)} role="group" aria-label={typeof label === 'string' ? `${label}: ${summary}` : summary} title={title}>
      <span className="c2o-mbar__label">{label}</span>
      <span className="c2o-mbar__track" aria-hidden="true">
        {hasValue && <span className="c2o-mbar__nom" style={{ width: x(nom!) }} />}
        {hasValue && wm! > nom! && <span className="c2o-mbar__mgn" style={{ left: x(nom!), width: `calc(${x(wm!)} - ${x(nom!)})` }} />}
        {allocation != null && allocation > 0 && <span className="c2o-mbar__alloc" style={{ left: x(allocation) }} />}
      </span>
      <span className="c2o-mbar__read">
        {hasValue ? (
          <span className="c2o-mbar__val">
            {fmtNum(wm!, digits)}
            {allocation != null && <span className="c2o-mbar__of"> / {fmtNum(allocation, digits)}</span>}
            {' '}<span className="c2o-mbar__unit">{unit}</span>
          </span>
        ) : <span className="c2o-nodata">{t('no data')}</span>}
        <span className="c2o-mbar__pct">
          {pct != null
            ? <StatusBadge status={status === 'ok' ? 'neutral' : status}>{`${pct > 0 ? '+' : ''}${pct.toFixed(0)} %`}</StatusBadge>
            : <span className="c2o-nodata">{t('no allocation')}</span>}
        </span>
      </span>
    </div>
  )
}

/** Legend for a MarginBar list. */
export function MarginBarKey() {
  const { t } = useTranslation()
  return (
    <div className="c2o-mbar-key" aria-hidden="true">
      <span><span className="c2o-mbar-key__sw c2o-mbar-key__sw--nom" />{t('Nominal (current best estimate)')}</span>
      <span><span className="c2o-mbar-key__sw c2o-mbar-key__sw--mgn" />{t('Maturity margin')}</span>
      <span><span className="c2o-mbar-key__sw c2o-mbar-key__sw--alloc" />{t('Allocation')}</span>
    </div>
  )
}
