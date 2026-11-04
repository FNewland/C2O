/**
 * Unfolded face map: the six outside faces as a cross, each seen from outside
 * (-Y | +X | +Y | -X across, +Z above and -Z below +X), to scale. Shows body-mounted
 * items, stowed deployables and the ports of internal units (aperture, baffle, nozzle).
 * Drag an item to another face; or select it and pick the face in the details panel.
 */
import { useRef, useState, type PointerEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { subColor, unitsOf, type Envelope, type Evaluated, type Face, type Placement } from './stackApi'

interface Props {
  real: Evaluated
  env: Envelope
  selected: string | null
  onSelect: (elementId: string | null) => void
  onMoveFace: (elementId: string, from: Face, to: Face) => void
  readOnly?: boolean
}

const GAP = 8

export function StackFaces({ real, env, selected, onSelect, onMoveFace, readOnly }: Props) {
  const { t } = useTranslation()
  const svgRef = useRef<SVGSVGElement | null>(null)
  const [sx, sy, sz] = env.size_mm
  const s = Math.min(1.0, 900 / (2 * sx + 2 * sy + 4 * GAP))
  // face extents (h, v) and origins (top-left, mm units before scaling)
  const ext: Record<Face, [number, number]> = { px: [sy, sz], mx: [sy, sz], py: [sx, sz], my: [sx, sz], pz: [sy, sx], mz: [sy, sx] }
  const top = sx + GAP
  const ox: Record<Face, number> = { my: 0, px: sx + GAP, py: sx + sy + 2 * GAP, mx: 2 * sx + sy + 3 * GAP, pz: sx + GAP, mz: sx + GAP }
  const oy: Record<Face, number> = { my: top, px: top, py: top, mx: top, pz: 0, mz: top + sz + GAP }
  const PADT = 22
  const W = (2 * sx + 2 * sy + 3 * GAP) * s + 2
  const H = (2 * sx + sz + 2 * GAP) * s + PADT + 24
  // face-local (u, v) -> (h, up): seen from outside
  const hv = (f: Face, u: number, v: number): [number, number] => {
    switch (f) {
      case 'px': return [u, v]
      case 'py': return [-u, v]
      case 'mx': return [-u, v]
      case 'my': return [u, v]
      case 'pz': return [v, -u]
      case 'mz': return [v, u]
    }
  }
  const rectOf = (f: Face, uv: number[]) => {
    const [H0, V0] = ext[f]
    const a = hv(f, uv[0], uv[1]), b = hv(f, uv[2], uv[3])
    const h0 = Math.min(a[0], b[0]), h1 = Math.max(a[0], b[0]), v0 = Math.min(a[1], b[1]), v1 = Math.max(a[1], b[1])
    return { x: (ox[f] + h0 + H0 / 2) * s + 1, y: (oy[f] + V0 / 2 - v1) * s + PADT, w: (h1 - h0) * s, h: (v1 - v0) * s }
  }
  const faceRect = (f: Face) => ({ x: ox[f] * s + 1, y: oy[f] * s + PADT, w: ext[f][0] * s, h: ext[f][1] * s })
  const NAME: Record<Face, string> = {
    px: '+X', mx: '−X', py: '+Y', my: '−Y', pz: t('+Z zenith'), mz: t('−Z nadir'),
  }
  const groups = real.placements.filter(p => p.tiles && p.face)
  const ports = real.placements.filter(p => p.port_rect_mm && p.face)
  const [drag, setDrag] = useState<{ p: Placement; x: number; y: number; over: Face | null } | null>(null)

  const svgPoint = (e: PointerEvent) => {
    const svg = svgRef.current
    const m = svg?.getScreenCTM()
    if (!svg || !m) return null
    const pt = svg.createSVGPoint()
    pt.x = e.clientX; pt.y = e.clientY
    return pt.matrixTransform(m.inverse())
  }
  const faceAt = (x: number, y: number): Face | null =>
    (Object.keys(ext) as Face[]).find(f => { const r = faceRect(f); return x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h }) ?? null

  return (
    <div className="c2o-stk__faces">
      <svg ref={svgRef} viewBox={`0 0 ${W.toFixed(0)} ${H.toFixed(0)}`} width="100%" style={{ maxWidth: `${W.toFixed(0)}px` }}
        role="group" aria-label={t('Unfolded faces of the spacecraft, each seen from outside')}
        onPointerMove={e => { if (!drag) return; const p = svgPoint(e); if (p) setDrag({ ...drag, x: p.x, y: p.y, over: faceAt(p.x, p.y) }) }}
        onPointerUp={() => {
          if (drag) {
            if (drag.over && drag.over !== drag.p.face) onMoveFace(drag.p.element_id, drag.p.face as Face, drag.over)
            else onSelect(drag.p.element_id)
          }
          setDrag(null)
        }}
        onPointerCancel={() => setDrag(null)}>
        <defs>
          <pattern id="stk-port" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="5" stroke="var(--text-3)" strokeWidth="1.2" />
          </pattern>
        </defs>
        {(Object.keys(ext) as Face[]).map(f => {
          const r = faceRect(f)
          return (
            <g key={f}>
              <rect className={`c2o-stk__fc${drag?.over === f ? ' is-over' : ''}`} x={r.x} y={r.y} width={r.w} height={r.h} />

            </g>
          )
        })}
        {ports.map(p => {
          const r = rectOf(p.face as Face, p.port_rect_mm!)
          return (
            <g key={`port-${p.id}`} onClick={() => onSelect(p.element_id)}>
              <rect className="c2o-stk__port" x={r.x} y={r.y} width={r.w} height={r.h} fill="url(#stk-port)" />
              <title>{t('{{name}}: port on this face', { name: p.name })}</title>
            </g>
          )
        })}
        {groups.map(p => (
          <g key={p.id} className={`c2o-stk__item${selected === p.element_id ? ' is-sel' : ''}${!p.fits ? ' is-bad' : ''}${p.mount_class === 'deployable' ? ' is-dep' : ''}`}
            tabIndex={0} role="button" aria-pressed={selected === p.element_id}
            aria-label={t('{{name}} on face {{face}}, units: {{n}}', { name: p.name, face: NAME[p.face as Face], n: unitsOf(p) })}
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(p.element_id) } }}
            onPointerDown={e => {
              if (readOnly || p.locked) { onSelect(p.element_id); return }
              const pt = svgPoint(e); if (!pt) return
              ;(e.target as Element).setPointerCapture?.(e.pointerId)
              setDrag({ p, x: pt.x, y: pt.y, over: p.face })
            }}>
            {(p.tiles ?? []).map((tl, k) => {
              const r = rectOf(p.face as Face, tl.uv_mm)
              return <rect key={k} x={r.x} y={r.y} width={Math.max(r.w, 2)} height={Math.max(r.h, 2)}
                style={{ fill: `color-mix(in srgb, ${subColor(p.subsystem)} 60%, var(--surface-1))` }} />
            })}
            <title>{`${p.name} · ${NAME[p.face as Face]}${p.locked ? ` · ${t('locked')}` : ''}`}</title>
          </g>
        ))}
        {(Object.keys(ext) as Face[]).map(f => {
          const r = faceRect(f)
          return <text key={`n-${f}`} className="c2o-stk__fcname" x={r.x + 4} y={r.y + 13}>{NAME[f]}</text>
        })}
        {drag && <circle className="c2o-stk__dragdot" cx={drag.x} cy={drag.y} r={6} />}
      </svg>
      <p className="t-12 c-3 m-0 mt-1 measure">
        {readOnly ? t('Each face seen from outside, to scale. Hatched: ports of internal units (aperture, baffle, nozzle).')
          : t('Each face seen from outside, to scale. Drag an item to another face, or select it and choose the face in the details. Hatched: ports of internal units (aperture, baffle, nozzle).')}
      </p>
    </div>
  )
}
