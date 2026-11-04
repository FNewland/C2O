/**
 * Side elevation of the stack (Y-Z plane, to scale, seen from +X): the CDS envelope, the
 * stack columns with their units (body solid, standoffs hatched), the end-face items, the
 * CoG with the CDS CoG box, a millimetre ruler and the height used per column.
 *
 * Reorder: drag a unit to another slot or column, or with the keyboard: focus a unit, then
 * Alt+Arrow Up / Down (towards zenith / nadir), Alt+Arrow Left / Right (other column),
 * L to lock or unlock, Enter to select. Units anchored to an end (aperture, baffle) stay
 * at that end; locked units do not move.
 */
import { useMemo, useRef, useState, type KeyboardEvent, type PointerEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { findInColumns, moveColumnItem, subColor, type Envelope, type Evaluated, type Placement, type Spec } from './stackApi'

interface Props {
  real: Evaluated
  env: Envelope
  selected: string | null
  onSelect: (elementId: string | null) => void
  onMove: (pid: string, column: number, index: number) => void
  onToggleLock: (pid: string) => void
  readOnly?: boolean
  announce: (text: string) => void
}

const PAD = { l: 64, r: 168, t: 40, b: 46 }

export function StackElevation({ real, env, selected, onSelect, onMove, onToggleLock, readOnly, announce }: Props) {
  const { t } = useTranslation()
  const svgRef = useRef<SVGSVGElement | null>(null)
  const [, sy, sz] = env.size_mm
  const s = Math.min(1.7, 540 / sz)
  const W = PAD.l + sy * s + PAD.r
  const H = PAD.t + sz * s + PAD.b
  const X = (y: number) => PAD.l + (y + sy / 2) * s
  const Y = (z: number) => PAD.t + (sz / 2 - z) * s
  const spec: Spec = real.spec
  const colItems = useMemo(() => real.placements.filter(p => p.z_mm), [real])
  const endItems = useMemo(() => real.placements.filter(p => p.tiles && (p.face === 'pz' || p.face === 'mz')), [real])
  const [drag, setDrag] = useState<{ pid: string; y: number; z: number; target: [number, number] | null } | null>(null)

  const toBody = (e: PointerEvent): { y: number; z: number } | null => {
    const svg = svgRef.current
    if (!svg) return null
    const pt = svg.createSVGPoint()
    pt.x = e.clientX; pt.y = e.clientY
    const m = svg.getScreenCTM()
    if (!m) return null
    const p = pt.matrixTransform(m.inverse())
    return { y: (p.x - PAD.l) / s - sy / 2, z: sz / 2 - (p.y - PAD.t) / s }
  }
  const target = (pid: string, y: number, z: number): [number, number] => {
    const cols = real.columns
    const c = cols.reduce((best, col) => (Math.abs(col.cy - y) < Math.abs(cols[best].cy - y) ? col.index : best), 0)
    const others = spec.columns[c].filter(p => p !== pid)
    const centre = (p: string) => colItems.find(q => q.id === p)?.center_mm[2] ?? 0
    const idx = others.filter(p => centre(p) < z).length
    return [c, idx]
  }

  const startDrag = (p: Placement, e: PointerEvent) => {
    if (readOnly || p.locked || p.column === null) { onSelect(p.element_id); return }
    const b = toBody(e)
    if (!b) return
    ;(e.target as Element).setPointerCapture?.(e.pointerId)
    setDrag({ pid: p.id, y: b.y, z: b.z, target: null })
  }
  const moveDrag = (e: PointerEvent) => {
    if (!drag) return
    const b = toBody(e)
    if (!b) return
    setDrag({ ...drag, y: b.y, z: b.z, target: target(drag.pid, b.y, b.z) })
  }
  const endDrag = () => {
    if (!drag) return
    const at = findInColumns(spec, drag.pid)
    const changed = !!(drag.target && at) &&
      JSON.stringify(moveColumnItem(spec, drag.pid, drag.target![0], drag.target![1]).columns) !== JSON.stringify(spec.columns)
    if (changed) onMove(drag.pid, drag.target![0], drag.target![1])
    else onSelect(colItems.find(p => p.id === drag.pid)?.element_id ?? null)
    setDrag(null)
  }

  const onKey = (p: Placement, e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(p.element_id); return }
    if (readOnly) return
    if (e.key === 'l' || e.key === 'L') { e.preventDefault(); onToggleLock(p.id); return }
    if (!e.altKey || p.column === null) return
    const at = findInColumns(spec, p.id)
    if (!at) return
    let to: [number, number] | null = null
    if (e.key === 'ArrowUp') to = [at[0], at[1] + 1]
    if (e.key === 'ArrowDown') to = [at[0], at[1] - 1]
    if (e.key === 'ArrowRight' && at[0] + 1 < spec.columns.length) to = [at[0] + 1, Math.min(at[1], spec.columns[at[0] + 1].length)]
    if (e.key === 'ArrowLeft' && at[0] > 0) to = [at[0] - 1, Math.min(at[1], spec.columns[at[0] - 1].length)]
    if (!to) return
    e.preventDefault()
    if (p.locked) { announce(t('{{name}} is locked: unlock it (L) to move it.', { name: p.name })); return }
    if (p.anchor && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
      announce(t('{{name}} stays at the {{end}} end (its aperture or baffle needs it).', { name: p.name, end: p.anchor === 'nadir' ? t('nadir') : t('zenith') }))
      return
    }
    if (to[1] < 0 || to[1] > spec.columns[to[0]].length - (to[0] === at[0] ? 1 : 0)) return
    onMove(p.id, to[0], to[1])
  }

  const ticks = useMemo(() => {
    const out: number[] = []
    for (let mm = 0; mm <= sz + 0.01; mm += 50) out.push(mm)
    return out
  }, [sz])
  const lim = env.cog_limits_mm
  const cog = real.cog_mm
  const cogOk = Math.abs(cog[1]) <= lim[1] && Math.abs(cog[2]) <= lim[2] && Math.abs(cog[0]) <= lim[0]

  const insertY = (() => {
    if (!drag?.target) return null
    const [c, i] = drag.target
    const others = spec.columns[c].filter(p => p !== drag.pid).map(p => colItems.find(q => q.id === p)).filter(Boolean) as Placement[]
    const zz = i <= 0 ? (others[0]?.z_mm?.[0] ?? env.z0_mm) : (others[i - 1]?.z_mm?.[1] ?? env.z1_mm)
    const col = real.columns[c]
    return { x1: X(col.cy - col.inner_mm[1] / 2) - 4, x2: X(col.cy + col.inner_mm[1] / 2) + 4, y: Y(zz) }
  })()

  return (
    <div className="c2o-stk__elev">
      <svg ref={svgRef} viewBox={`0 0 ${W.toFixed(0)} ${H.toFixed(0)}`} width="100%" style={{ maxWidth: `${W.toFixed(0)}px` }}
        role="group" aria-label={t('Side elevation of the stack, seen from +X, zenith up')}
        onPointerMove={moveDrag} onPointerUp={endDrag} onPointerCancel={() => setDrag(null)}>
        <defs>
          <pattern id="stk-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="6" stroke="var(--line-strong)" strokeWidth="1.5" />
          </pattern>
        </defs>
        {/* ruler */}
        <g className="c2o-stk__ruler" aria-hidden="true">
          {ticks.map(mm => (
            <g key={mm}>
              <line x1={PAD.l - 10} x2={PAD.l - 2} y1={Y(-sz / 2 + mm)} y2={Y(-sz / 2 + mm)} />
              <text x={PAD.l - 13} y={Y(-sz / 2 + mm) + 4} textAnchor="end">{mm}</text>
            </g>
          ))}
          <text x={PAD.l - 13} y={PAD.t - 22} textAnchor="end">mm</text>
        </g>
        {/* envelope + end allowances */}
        <rect className="c2o-stk__env" x={X(-sy / 2)} y={Y(sz / 2)} width={sy * s} height={sz * s} />
        <rect className="c2o-stk__endzone" x={X(-sy / 2)} y={Y(sz / 2)} width={sy * s} height={env.end_allowance_mm * s} />
        <rect className="c2o-stk__endzone" x={X(-sy / 2)} y={Y(env.z0_mm)} width={sy * s} height={env.end_allowance_mm * s} />
        <text className="c2o-stk__axis" x={X(0)} y={PAD.t - 24} textAnchor="middle">{t('+Z zenith')}</text>
        <text className="c2o-stk__axis" x={X(0)} y={H - 10} textAnchor="middle">{t('−Z nadir')}</text>
        <text className="c2o-stk__axis" x={X(sy / 2)} y={H - 10} textAnchor="end">{t('+Y →')}</text>
        {/* columns */}
        {real.columns.map(c => (
          <rect key={c.index} className="c2o-stk__col" x={X(c.cy - c.inner_mm[1] / 2)} y={Y(env.z1_mm)}
            width={c.inner_mm[1] * s} height={env.internal_length_mm * s} />
        ))}
        {/* end-face items: thin bars beyond the ends */}
        {endItems.map(p => (p.tiles ?? []).map((tl, k) => {
          const u0 = tl.uv_mm[1], u1 = tl.uv_mm[3]          // end faces: (u, v) = (x, y); the elevation shows y
          const top = p.face === 'pz'
          const h = Math.max(3, (p.size_mm[2] || 3) * s)
          return (
            <rect key={`${p.id}-${k}`} className={`c2o-stk__face${selected === p.element_id ? ' is-sel' : ''}`}
              x={X(u0)} width={Math.max(2, (u1 - u0) * s)} y={top ? Y(sz / 2) - h : Y(-sz / 2)} height={h}
              style={{ fill: subColor(p.subsystem) }} onClick={() => onSelect(p.element_id)}>
              <title>{`${p.name} (${p.face})`}</title>
            </rect>
          )
        }))}
        {/* units */}
        {colItems.map(p => {
          const [z0, z1] = p.z_mm!
          const yy0 = p.column === null ? -sy / 2 + 1 : p.center_mm[1] - p.size_mm[1] / 2
          const w = p.column === null ? sy - 2 : p.size_mm[1]
          const bodyH = Math.min(p.body_h_mm ?? (z1 - z0), z1 - z0)
          const sel = selected === p.element_id
          const tall = (z1 - z0) * s >= 15
          const label = `${p.name}, ${p.column === null ? t('full-width layer') : t('column {{c}}, slot {{s}}', { c: (p.column ?? 0) + 1, s: (p.slot ?? 0) + 1 })}, ${(z1 - z0).toFixed(1)} mm${p.locked ? `, ${t('locked')}` : ''}${p.anchor ? `, ${t('anchored at the {{end}} end', { end: p.anchor === 'nadir' ? t('nadir') : t('zenith') })}` : ''}`
          return (
            <g key={p.id} className={`c2o-stk__unit${sel ? ' is-sel' : ''}${!p.fits ? ' is-bad' : ''}${drag?.pid === p.id ? ' is-drag' : ''}`}
              tabIndex={0} role="button" aria-label={label} aria-pressed={sel}
              aria-describedby="stk-elev-help" data-pid={p.id}
              onPointerDown={e => startDrag(p, e)} onKeyDown={e => onKey(p, e)}>
              <rect className="c2o-stk__slot" x={X(yy0)} y={Y(z1)} width={w * s} height={(z1 - z0) * s} fill="url(#stk-hatch)" />
              <rect className="c2o-stk__body" x={X(yy0)} y={Y(z0 + bodyH)} width={w * s} height={bodyH * s}
                style={{ fill: `color-mix(in srgb, ${subColor(p.subsystem)} 55%, var(--surface-1))` }} />
              {tall && <text className="c2o-stk__lbl" x={X(yy0) + 4} y={Y((z0 + z1) / 2) + 4}>{clip(p.name, Math.floor(w * s / 6.6) - (p.locked ? 2 : 0))}</text>}
              {p.locked && <path className="c2o-stk__lock" transform={`translate(${X(yy0 + w) - 13},${Y(z1) + 3})`}
                d="M2 5V3.5a3 3 0 0 1 6 0V5M1 5h8v6H1z" />}
              <title>{label}</title>
            </g>
          )
        })}
        {insertY && <line className="c2o-stk__insert" x1={insertY.x1} x2={insertY.x2} y1={insertY.y} y2={insertY.y} />}
        {/* CoG and the CDS box (Y-Z projection) */}
        <rect className={`c2o-stk__cogbox${cogOk ? '' : ' is-bad'}`} x={X(-lim[1])} y={Y(lim[2])} width={2 * lim[1] * s} height={2 * lim[2] * s} />
        <g className="c2o-stk__cog" transform={`translate(${X(cog[1])},${Y(cog[2])})`} aria-hidden="true">
          <circle r="6" /><line x1="-9" x2="9" y1="0" y2="0" /><line x1="0" x2="0" y1="-9" y2="9" />
          <text x="10" y="-8">{t('CoG')}</text>
        </g>
        {/* heights per column */}
        {real.columns.map((c, i) => {
          const x = X(sy / 2) + 18 + i * 72
          const frac = Math.min(1.2, c.used_mm / c.length_mm)
          const over = c.used_mm > c.length_mm + 0.05
          return (
            <g key={c.index} className={`c2o-stk__hbar${over ? ' is-bad' : ''}`}>
              <rect className="c2o-stk__htrack" x={x} y={Y(env.z1_mm)} width={10} height={env.internal_length_mm * s} />
              <rect className="c2o-stk__hfill" x={x} y={Y(env.z0_mm) - Math.min(frac, 1) * env.internal_length_mm * s} width={10}
                height={Math.min(frac, 1) * env.internal_length_mm * s} />
              <text x={x + 14} y={Y(env.z1_mm) + 10}>{t('Col {{n}}', { n: i + 1 })}</text>
              <text x={x + 14} y={Y(env.z1_mm) + 24} className="mono">{c.used_mm.toFixed(0)}/{c.length_mm.toFixed(0)}</text>
            </g>
          )
        })}
      </svg>
      <p id="stk-elev-help" className="t-12 c-3 m-0 mt-1 measure">
        {readOnly
          ? t('Seen from +X, to scale. Select a unit to see its details.')
          : t('Seen from +X, to scale. Drag a unit to another slot or column, or focus it and use Alt+Arrow keys; L locks it. Hatched: standoffs and free height.')}
      </p>
    </div>
  )
}

function clip(s: string, n: number): string {
  if (n <= 3) return ''
  return s.length > n ? `${s.slice(0, Math.max(1, n - 1))}…` : s
}
