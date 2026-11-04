/**
 * ModeDiagram — the spacecraft mode machine as a simple state diagram (plain SVG).
 *
 * Columns follow the ConOps order (LEOP → commissioning → operations → fallback); each
 * transition is an arrow whose line style names its trigger (solid = ground command,
 * dashed = timer, heavy = autonomous / event), so the meaning survives greyscale. Edges
 * between the same two modes in both directions are drawn as two offset arcs.
 * The table editors next to it are the way to change the machine.
 */
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import type { Finding, Mode, Transition } from './api'
import { POINTING_LABELS, TRIGGER_LABELS } from './labels'

const COL: Record<string, number> = { leop: 0, commissioning: 1, nominal: 2, custom: 2, imaging: 3, downlink: 3, safe: 4, survival: 5 }
const BOX_W = 128
const BOX_H = 44
const GAP_X = 52
const GAP_Y = 30
const PAD = 16

export function ModeDiagram({ modes, transitions, findings, selected, onSelect }: {
  modes: Mode[]; transitions: Transition[]; findings: Finding[]
  selected?: string | null; onSelect?: (id: string) => void
}) {
  const { t } = useTranslation()
  const layout = useMemo(() => {
    const cols = new Map<number, Mode[]>()
    for (const m of modes) {
      const c = COL[m.kind] ?? 2
      cols.set(c, [...(cols.get(c) ?? []), m])
    }
    const used = [...cols.keys()].sort((a, b) => a - b)
    const pos = new Map<string, { x: number; y: number }>()
    used.forEach((c, ci) => {
      ;(cols.get(c) ?? []).forEach((m, ri) => pos.set(m.id, { x: PAD + ci * (BOX_W + GAP_X), y: PAD + 40 + ri * (BOX_H + GAP_Y) }))
    })
    const rows = Math.max(1, ...used.map(c => (cols.get(c) ?? []).length))
    return { pos, w: PAD * 2 + used.length * BOX_W + Math.max(0, used.length - 1) * GAP_X, h: PAD * 2 + 40 + rows * BOX_H + (rows - 1) * GAP_Y }
  }, [modes])

  const flagged = new Set(findings.filter(f => f.mode_id).map(f => f.mode_id))
  const badEdges = new Set(findings.filter(f => f.transition_id).map(f => f.transition_id))
  const pairs = new Set(transitions.map(tr => `${tr.from_mode_id}>${tr.to_mode_id}`))

  if (!modes.length) return null
  return (
    <figure className="m-0 stack gap-2">
      <svg role="img" aria-label={t('Mode diagram: {{n}} modes, {{m}} transitions', { n: modes.length, m: transitions.length })}
        viewBox={`0 0 ${layout.w} ${layout.h}`} width={layout.w} height={layout.h} className="mdl-svg">
        <defs>
          <marker id="mdl-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0 0 10 5 0 10Z" className="mdl-arrowhead" />
          </marker>
          <marker id="mdl-arrow-alarm" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0 0 10 5 0 10Z" className="mdl-arrowhead mdl-arrowhead--alarm" />
          </marker>
        </defs>
        {transitions.map(tr => {
          const a = layout.pos.get(tr.from_mode_id), b = layout.pos.get(tr.to_mode_id)
          if (!a || !b) return null
          const ax = a.x + BOX_W / 2, ay = a.y + BOX_H / 2, bx = b.x + BOX_W / 2, by = b.y + BOX_H / 2
          const dx = bx - ax, dy = by - ay, len = Math.hypot(dx, dy) || 1
          // clip to the box edges
          const clip = (px: number, py: number, sx: number, sy: number) => {
            const tx = Math.abs(sx) > 1e-6 ? (BOX_W / 2) / Math.abs(sx) : Infinity
            const ty = Math.abs(sy) > 1e-6 ? (BOX_H / 2) / Math.abs(sy) : Infinity
            const k = Math.min(tx, ty)
            return [px + sx * k, py + sy * k]
          }
          const ux = dx / len, uy = dy / len
          const [x1, y1] = clip(ax, ay, ux, uy)
          const [x2, y2] = clip(bx, by, -ux, -uy)
          const both = pairs.has(`${tr.to_mode_id}>${tr.from_mode_id}`)
          // same row and a box in between: arc well clear of the boxes; opposite pairs: two offset arcs
          const skips = Math.abs(dy) < 1 && Math.abs(dx) > BOX_W + GAP_X + 1
          const off = skips ? (dx > 0 ? 1 : -1) * -(BOX_H + 30) : both ? 14 : 0
          const mx = (x1 + x2) / 2 - uy * off, my = (y1 + y2) / 2 + ux * off
          const bad = badEdges.has(tr.id)
          const g = tr.guard || {}
          const guard = g.param ? `${g.param} ${g.op ?? ''} ${g.value ?? ''}${g.unit ? ' ' + g.unit : ''}` : (g.text ?? '')
          return (
            <path key={tr.id} d={`M${x1} ${y1} Q${mx} ${my} ${x2} ${y2}`}
              className={`mdl-edge mdl-edge--${tr.trigger}${bad ? ' mdl-edge--bad' : ''}`}
              markerEnd={bad ? 'url(#mdl-arrow-alarm)' : 'url(#mdl-arrow)'}>
              <title>{`${t(TRIGGER_LABELS[tr.trigger] ?? tr.trigger)}${guard ? ': ' + guard : ''}`}</title>
            </path>
          )
        })}
        {modes.map(m => {
          const p = layout.pos.get(m.id)!
          const cls = ['mdl-node', `mdl-node--${m.kind}`, selected === m.id && 'mdl-node--sel', flagged.has(m.id) && 'mdl-node--flag']
            .filter(Boolean).join(' ')
          return (
            <g key={m.id} transform={`translate(${p.x},${p.y})`} className={cls}
              role={onSelect ? 'button' : undefined} tabIndex={onSelect ? 0 : undefined}
              aria-label={m.name} onClick={() => onSelect?.(m.id)}
              onKeyDown={e => { if (onSelect && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onSelect(m.id) } }}>
              {m.initial && <path d={`M-14 ${BOX_H / 2} H-3`} className="mdl-edge mdl-edge--ground_tc" markerEnd="url(#mdl-arrow)" />}
              <rect width={BOX_W} height={BOX_H} rx={4} className="mdl-box" />
              <text x={BOX_W / 2} y={18} textAnchor="middle" className="mdl-name">{m.name.length > 18 ? m.name.slice(0, 17) + '…' : m.name}</text>
              <text x={BOX_W / 2} y={34} textAnchor="middle" className="mdl-sub">
                {m.orbit_fraction != null && m.kind !== 'leop' && m.kind !== 'commissioning' && m.kind !== 'safe' && m.kind !== 'survival'
                  ? t('{{pct}} % of orbit', { pct: Math.round(m.orbit_fraction * 100) })
                  : t(POINTING_LABELS[m.pointing] ?? m.pointing)}
              </text>
            </g>
          )
        })}
      </svg>
      <figcaption className="row wrap gap-4 t-12 c-3">
        {(['ground_tc', 'timer', 'autonomous'] as const).map(k => (
          <span key={k} className="row gap-1">
            <svg width="28" height="8" aria-hidden="true"><path d="M1 4H27" className={`mdl-edge mdl-edge--${k}`} /></svg>
            {t(TRIGGER_LABELS[k])}
          </span>
        ))}
        <span className="row gap-1"><svg width="14" height="10" aria-hidden="true"><rect x="1" y="1" width="12" height="8" rx="2" className="mdl-box mdl-legend-flag" /></svg>{t('has a finding')}</span>
      </figcaption>
    </figure>
  )
}
