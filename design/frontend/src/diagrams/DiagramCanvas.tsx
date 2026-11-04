/**
 * DiagramCanvas — draws a server diagram model as SVG with the same rules as the export
 * renderer (services/diagrams/render.py): same coordinates, shapes, line patterns per
 * interface type, legend and labels. Colours come from the C2O tokens, so the view follows
 * the light / dark theme; the documents are printed with the light values.
 *
 * Interaction: hover a block to bring its links forward (the others fade); click a block,
 * link or group to see where it comes from (provenance).
 */
import { useMemo, useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import type { DCell, DEdge, DiagramModel, DLegend, DNode, DText } from './api'

const TYPE_VAR: Record<string, string> = {
  power: 'var(--cat-4)', data: 'var(--cat-2)', rf: 'var(--cat-6)', mechanical: 'var(--cat-8)', thermal: 'var(--cat-5)',
  timing: 'var(--cat-1)', optical: 'var(--cat-1)', fluid: 'var(--cat-7)', electrical_signal: 'var(--cat-3)',
}
const FONT = 'var(--font-sans)'

/** Text of a model string in the UI language. */
export function useTx() {
  const { t, i18n } = useTranslation()
  return (v: DText) => tx(v, t, i18n.language)
}
export function tx(v: DText, t: TFunction, lang: string): string {
  if (v == null) return ''
  if (typeof v === 'string') return v
  if ('t' in v) return t(v.t, { ...(v.p ?? {}), interpolation: { escapeValue: false } }) as string
  if ('en' in v) return (lang.startsWith('fr') ? v.fr : v.en) || v.en || ''
  return ''
}

/** Approximate text width (IBM Plex Sans), the same estimate as the server (base.text_w). */
export function textW(s: string, size = 12, bold = false): number {
  const wide = [...s].filter(c => 'MWmw@%'.includes(c)).length * 0.3
  return (s.length + wide) * size * (bold ? 0.6 : 0.56)
}

function colorVar(key: string | undefined, fallback = 'var(--text-2)'): string {
  if (!key) return fallback
  if (key.startsWith('type:')) return TYPE_VAR[key.slice(5)] ?? 'var(--cat-2)'
  const m: Record<string, string> = {
    text: 'var(--text)', text2: 'var(--text-2)', text3: 'var(--text-3)', line: 'var(--line-strong)',
    caution: 'var(--status-caution)', alarm: 'var(--status-alarm)', ok: 'var(--status-ok)', accent: 'var(--interactive)',
  }
  return m[key] ?? fallback
}

export function edgeColor(e: Pick<DEdge, 'color' | 'type'>): string {
  if (e.color === 'line') return 'var(--line-strong)'
  if (e.color) return colorVar(e.color)
  return (e.type && TYPE_VAR[e.type]) || 'var(--text-3)'
}

interface NS { fill: string; stroke: string; bar: string | null; text: string; dash: string }
export function nodeStyle(style: string): NS {
  const s: NS = { fill: 'var(--surface-1)', stroke: 'var(--line-strong)', bar: null, text: 'var(--text)', dash: '' }
  if (style === 'emph') return { ...s, fill: 'var(--surface-2)', stroke: 'var(--text-3)' }
  if (style === 'accent') return { ...s, fill: 'var(--interactive-wash)', stroke: 'var(--interactive)' }
  if (style === 'ok' || style === 'caution' || style === 'alarm')
    return { ...s, fill: `var(--status-${style}-wash)`, stroke: `var(--status-${style})`, bar: `var(--status-${style})` }
  if (style === 'muted') return { ...s, fill: 'var(--surface-0)', dash: '4 3', text: 'var(--text-3)' }
  if (style.startsWith('cat')) return { ...s, bar: `var(--cat-${style.slice(3)})` }
  if (style.startsWith('type-')) { const c = TYPE_VAR[style.slice(5)] ?? 'var(--cat-2)'; return { ...s, fill: c, stroke: c } }
  if (style === 'cogbox') return { ...s, fill: 'none', stroke: 'var(--interactive)', dash: '4 3' }
  return s
}

interface CS { fill: string; stroke: string; text: string; bold: boolean; dash: string }
export function cellStyle(style: string): CS {
  const b: CS = { fill: 'var(--surface-1)', stroke: 'var(--line)', text: 'var(--text)', bold: false, dash: '' }
  if (style.startsWith('diag-')) return { ...b, fill: 'var(--surface-3)', bold: true }
  const m: Record<string, Partial<CS>> = {
    band: { fill: 'var(--surface-0)' },
    on: { fill: 'var(--interactive-wash)', text: 'var(--interactive)', bold: true },
    off: { fill: 'var(--surface-0)', text: 'var(--text-3)' },
    alarm: { fill: 'var(--status-alarm-wash)', text: 'var(--status-alarm)', bold: true },
    ok: { fill: 'var(--status-ok-wash)', text: 'var(--status-ok)' },
    caution: { fill: 'var(--status-caution-wash)', text: 'var(--status-caution)' },
    muted: { fill: 'var(--surface-2)', text: 'var(--text-3)' },
    unknown: { fill: 'var(--surface-2)', text: 'var(--text-3)', dash: '2 2' },
    total: { fill: 'var(--surface-2)', bold: true },
    grid: { fill: 'var(--line)', stroke: 'none' }, divider: { fill: 'var(--line-strong)', stroke: 'none' },
    cogbox: { fill: 'none', stroke: 'var(--interactive)', dash: '4 3' },
    'risk-low': { fill: 'var(--status-ok-wash)' }, 'risk-med': { fill: 'var(--status-caution-wash)' },
    'risk-high': { fill: 'color-mix(in srgb, var(--status-caution) 22%, var(--surface-1))' },
    'risk-vhigh': { fill: 'var(--status-alarm-wash)', text: 'var(--status-alarm)', bold: true },
  }
  return { ...b, ...(m[style] ?? {}) }
}

function groupStyle(style: string) {
  if (style === 'envelope') return { fill: 'var(--surface-0)', stroke: 'var(--text-3)', bar: null as string | null }
  if (style.startsWith('group-cat')) return { fill: 'var(--surface-0)', stroke: 'var(--line)', bar: `var(--cat-${style.slice(9)})` }
  return { fill: 'var(--surface-0)', stroke: 'var(--line)', bar: null as string | null }
}

function arrowHead(a: [number, number], b: [number, number], color: string, op: number, key: string) {
  const ang = Math.atan2(b[1] - a[1], b[0] - a[0])
  const L = 8, W = 3.6
  const p1 = [b[0] - L * Math.cos(ang) + W * Math.sin(ang), b[1] - L * Math.sin(ang) - W * Math.cos(ang)]
  const p2 = [b[0] - L * Math.cos(ang) - W * Math.sin(ang), b[1] - L * Math.sin(ang) + W * Math.cos(ang)]
  return <polygon key={key} points={`${b[0]},${b[1]} ${p1[0]},${p1[1]} ${p2[0]},${p2[1]}`} fill={color} opacity={op} />
}

function pathD(e: DEdge): string {
  const p = e.points
  if (e.curve && p.length === 3) return `M${p[0][0]},${p[0][1]} Q${p[1][0]},${p[1][1]} ${p[2][0]},${p[2][1]}`
  return 'M' + p.map(([x, y]) => `${x},${y}`).join(' L')
}

function labelPoint(e: DEdge): [number, number] {
  const p = e.points
  if (e.curve && p.length === 3) return [0.25 * p[0][0] + 0.5 * p[1][0] + 0.25 * p[2][0], 0.25 * p[0][1] + 0.5 * p[1][1] + 0.25 * p[2][1]]
  let best = 0, bl = -1
  for (let i = 0; i < p.length - 1; i++) {
    const l = Math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1])
    if (l > bl) { bl = l; best = i }
  }
  return [(p[best][0] + p[best + 1][0]) / 2, (p[best][1] + p[best + 1][1]) / 2]
}

export type Selection = { kind: 'node' | 'edge' | 'group'; item: DNode | DEdge | { id: string; label: DText; prov: DNode['prov'] } } | null

function NodeShape({ n, f, selected, onClick, onHover }: {
  n: DNode; f: (v: DText) => string; selected: boolean; onClick: () => void; onHover: (on: boolean) => void
}) {
  let st = nodeStyle(n.style)
  const { x, y, w, h, shape } = n
  const r = ({ round: 10, state: 12, pill: h / 2, chip: h / 2, band: 2, part: 1, row: 2, trunk: 2 } as Record<string, number>)[shape] ?? 3
  const label = f(n.label)
  const title = f(n.title) || label
  const common = {
    onClick, onMouseEnter: () => onHover(true), onMouseLeave: () => onHover(false), style: { cursor: 'pointer' },
    'data-node': n.id,
  }
  if (shape === 'dot') {
    return <g {...common}><title>{title}</title><circle cx={x + w / 2} cy={y + h / 2} r={w / 2} fill="var(--text)" /></g>
  }
  if (shape === 'cog') {
    const cx = x + w / 2, cy = y + h / 2
    return (
      <g {...common}><title>{title}</title>
        <circle cx={cx} cy={cy} r={w / 2} fill="var(--surface-1)" stroke="var(--interactive)" strokeWidth={1.5} />
        <path d={`M${x},${cy} L${x + w},${cy} M${cx},${y} L${cx},${y + h}`} stroke="var(--interactive)" strokeWidth={1.2} />
      </g>
    )
  }
  if (shape === 'part' && st.bar) st = { ...st, fill: `color-mix(in srgb, ${st.bar} 22%, var(--surface-1))`, stroke: st.bar }
  const out: ReactNode[] = []
  out.push(<rect key="r" x={x} y={y} width={w} height={h} rx={r} fill={st.fill} stroke={selected ? 'var(--interactive)' : (shape === 'state' && st.bar ? st.bar : st.stroke)}
    strokeWidth={selected ? 2.4 : shape === 'state' ? 1.6 : 1} strokeDasharray={st.dash || undefined} />)
  if (shape === 'trunk') return <g {...common}><title>{title}</title>{out}</g>
  let pad = 10
  if (st.bar && shape !== 'state' && !['part', 'chip', 'pill'].includes(shape)) {
    out.push(<rect key="bar" x={x} y={y} width={4} height={h} rx={1} fill={st.bar} />)
    pad = 12
  }
  const sub = f(n.sub)
  const badges = (n.badges || []).map(f).filter(Boolean)
  if (shape === 'chip' || shape === 'pill' || shape === 'part') {
    if (label) out.push(<text key="l" x={shape === 'pill' ? x + 10 : x + w / 2} y={y + h / 2 + 4} fontSize={12}
      fontWeight={shape === 'pill' ? 600 : 400} fill={st.text} textAnchor={shape === 'pill' ? 'start' : 'middle'}>{label}</text>)
    return <g {...common}><title>{title}</title>{out}</g>
  }
  if (shape === 'row') {
    out.push(<text key="l" x={x + 8} y={y + h / 2 + 4} fontSize={12} fill={st.text}>{label}</text>)
    let bx = x + w + 6
    badges.forEach((b, i) => {
      const bw = textW(b) + 10
      out.push(<rect key={`b${i}`} x={bx} y={y + 2} width={bw} height={h - 4} rx={8} fill="var(--surface-2)" stroke="var(--line)" />)
      out.push(<text key={`bt${i}`} x={bx + bw / 2} y={y + h / 2 + 4} fontSize={12} fill="var(--text-2)" textAnchor="middle">{b}</text>)
      bx += bw + 4
    })
    return <g {...common}><title>{title}</title>{out}</g>
  }
  const content = 16 + (sub ? 15 : 0) + (badges.length ? 17 : 0)
  const ty = y + (h - content) / 2
  const centre = shape === 'state' || shape === 'round' || shape === 'step'
  const tx_ = centre ? x + w / 2 : x + pad
  const anchor = centre ? 'middle' : 'start'
  out.push(<text key="l" x={tx_} y={ty + 12.5} fontSize={shape === 'step' ? 12 : 13} fontWeight={shape === 'step' ? 400 : 600}
    fill={st.text} textAnchor={anchor}>{label}</text>)
  if (sub) out.push(<text key="s" x={tx_} y={ty + 27.5} fontSize={12} fill="var(--text-2)" textAnchor={anchor}>{sub}</text>)
  if (badges.length) {
    const widths = badges.map(b => textW(b) + 10)
    const total = widths.reduce((a, b) => a + b, 0) + 4 * (badges.length - 1)
    let bx = centre ? x + (w - total) / 2 : x + pad
    const by = ty + 16 + (sub ? 15 : 0) + 1
    badges.forEach((b, i) => {
      out.push(<rect key={`b${i}`} x={bx} y={by} width={widths[i]} height={15} rx={7.5} fill="var(--surface-2)" stroke="var(--line)" />)
      out.push(<text key={`bt${i}`} x={bx + widths[i] / 2} y={by + 11.5} fontSize={12} fill="var(--text-2)" textAnchor="middle">{b}</text>)
      bx += widths[i] + 4
    })
  }
  return <g {...common}><title>{title}</title>{out}</g>
}

function Cell({ c, f }: { c: DCell; f: (v: DText) => string }) {
  const st = cellStyle(c.style)
  const cy = c.y + c.h / 2
  const title = f(c.title)
  const kids: ReactNode[] = [<rect key="r" x={c.x} y={c.y} width={c.w} height={c.h} fill={st.fill}
    stroke={st.stroke === 'none' ? undefined : st.stroke} strokeDasharray={st.dash || undefined} />]
  if (c.codes?.length) {
    const lines: { type: string; c: string }[][] = []
    for (let i = 0; i < c.codes.length; i += 2) lines.push(c.codes.slice(i, i + 2))
    lines.forEach((line, li) => {
      const total = line.reduce((a, x) => a + textW(x.c, 12, true), 0) + 3 * (line.length - 1)
      let x = c.x + (c.w - total) / 2
      const ly = cy + 4 + (li - (lines.length - 1) / 2) * 13
      line.forEach((code, k) => {
        kids.push(<text key={`c${li}${k}`} x={x} y={ly} fontSize={12} fontWeight={600} fill={TYPE_VAR[code.type] ?? 'var(--cat-2)'}>{code.c}</text>)
        x += textW(code.c, 12, true) + 3
      })
    })
  } else if (c.text != null && c.text !== '') {
    const sub = f(c.sub)
    kids.push(<text key="t" x={c.x + c.w / 2} y={cy + (sub ? -4 : 4)} fontSize={sub ? 15 : 12} fontWeight={st.bold || sub ? 600 : 400}
      fill={st.text} textAnchor="middle">{f(c.text)}</text>)
    if (sub) kids.push(<text key="s" x={c.x + c.w / 2} y={cy + 14} fontSize={12} fill="var(--text-2)" textAnchor="middle">{sub}</text>)
  }
  return <g>{title && <title>{title}</title>}{kids}</g>
}

export function DiagramCanvas({ model, zoom = 1, selectedId, onSelect, ariaLabel }: {
  model: DiagramModel; zoom?: number; selectedId?: string | null; onSelect?: (s: Selection) => void; ariaLabel?: string
}) {
  const f = useTx()
  const [hover, setHover] = useState<string | null>(null)
  const touching = useMemo(() => {
    if (!hover) return null
    const s = new Set<string>()
    for (const e of model.edges) if (e.from === hover || e.to === hover) s.add(e.id)
    return s
  }, [hover, model.edges])
  const W = model.width, H = model.height
  return (
    <svg width={W * zoom} height={H * zoom} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={ariaLabel ?? f(model.title)}
      fontFamily={FONT} className="c2o-dgm__svg" data-kind={model.kind}>
      <rect x={0} y={0} width={W} height={H} fill="var(--surface-1)" />
      {model.empty != null && (
        <text x={W / 2} y={H / 2} fontSize={13} fill="var(--text-3)" textAnchor="middle" fontStyle="italic">{f(model.empty)}</text>
      )}
      {model.groups.map(g => {
        const st = groupStyle(g.style)
        return (
          <g key={g.id} onClick={() => onSelect?.({ kind: 'group', item: g })} style={{ cursor: g.ref ? 'pointer' : undefined }}>
            <rect x={g.x} y={g.y} width={g.w} height={g.h} rx={3} fill={st.fill} stroke={selectedId === g.id ? 'var(--interactive)' : st.stroke} />
            {st.bar && <rect x={g.x} y={g.y} width={g.w} height={4} fill={st.bar} />}
            {f(g.label) && <text x={g.x + 8} y={g.y + 16} fontSize={12} fontWeight={600} fill="var(--text-2)">{f(g.label)}</text>}
          </g>
        )
      })}
      {model.cells.map((c, i) => <Cell key={i} c={c} f={f} />)}
      {model.edges.map(e => {
        const col = edgeColor(e)
        const dim = touching && !touching.has(e.id)
        const op = (e.faded ? 0.45 : 1) * (dim ? 0.15 : 1)
        const p = e.points
        const sel = selectedId === e.id
        return (
          <g key={e.id} onClick={() => onSelect?.({ kind: 'edge', item: e })} style={{ cursor: 'pointer' }}>
            <path d={pathD(e)} fill="none" stroke="transparent" strokeWidth={8} />
            <path d={pathD(e)} fill="none" stroke={sel ? 'var(--interactive)' : col} strokeWidth={(e.width ?? 1.4) + (sel || (touching && !dim) ? 1 : 0)}
              strokeDasharray={e.dash || undefined} strokeLinejoin="round" opacity={op} />
            {(e.arrow === 'end' || e.arrow === 'both') && arrowHead(e.curve ? p[1] : p[p.length - 2], p[p.length - 1], col, op, 'ae')}
            {(e.arrow === 'start' || e.arrow === 'both') && arrowHead(p[1], p[0], col, op, 'as')}
          </g>
        )
      })}
      {model.nodes.map(n => (
        <NodeShape key={n.id} n={n} f={f} selected={selectedId === n.id}
          onClick={() => onSelect?.({ kind: 'node', item: n })} onHover={on => setHover(on ? n.id : null)} />
      ))}
      {model.edges.filter(e => e.label != null && e.label !== '').map(e => {
        const [lx, ly] = labelPoint(e)
        const s = f(e.label)
        const w = textW(s) + 8
        const dim = touching && !touching.has(e.id)
        return (
          <g key={`l${e.id}`} opacity={dim ? 0.2 : 1} pointerEvents="none">
            <rect x={lx - w / 2} y={ly - 9} width={w} height={17} fill="var(--surface-1)" opacity={0.92} />
            <text x={lx} y={ly + 4} fontSize={12} fill="var(--text-2)" textAnchor="middle">{s}</text>
          </g>
        )
      })}
      {model.labels.map((l, i) => (
        <text key={`t${i}`} x={l.x} y={l.y} fontSize={l.size} fontWeight={l.weight}
          fill={l.style === 'caution' ? 'var(--status-caution)' : colorVar(l.style)}
          textAnchor={l.anchor} transform={l.rotate ? `rotate(${l.rotate} ${l.x} ${l.y})` : undefined}>{f(l.text)}</text>
      ))}
    </svg>
  )
}

/** The legend as HTML (wraps with the panel width); same items as the export legend. */
export function DiagramLegend({ items }: { items: DLegend[] }) {
  const f = useTx()
  const { t } = useTranslation()
  if (!items.length) return null
  return (
    <ul className="c2o-dgm__legend list-reset" aria-label={t('Legend')}>
      {items.map((it, i) => {
        const lab = f(it.label)
        let mark: ReactNode
        if (it.kind === 'line') {
          const col = it.type && !it.color ? TYPE_VAR[it.type] : colorVar(it.color)
          mark = <svg width="30" height="10" aria-hidden="true"><line x1="1" y1="5" x2="29" y2="5" stroke={col} strokeWidth={it.width ?? 1.4}
            strokeDasharray={it.dash || undefined} opacity={it.faded ? 0.45 : 1} /></svg>
        } else if (it.kind === 'dot') {
          mark = <svg width="18" height="14" aria-hidden="true"><circle cx="9" cy="7" r="6" fill="var(--text)" /></svg>
        } else {
          const s = it.style ?? 'default'
          const cell = /^(risk|on$|off$|unknown$|cogbox$)/.test(s)
          const st = cell ? { ...cellStyle(s), bar: null as string | null } : nodeStyle(s)
          mark = <svg width="20" height="16" aria-hidden="true"><rect x="1" y="1" width="18" height="14" rx="2"
            fill={st.fill === 'none' ? 'var(--surface-1)' : st.fill} stroke={st.stroke === 'none' ? 'var(--line)' : st.stroke}
            strokeDasharray={st.dash || undefined} />{st.bar && <rect x="1" y="1" width="4" height="14" fill={st.bar} />}</svg>
        }
        return <li key={i} className="c2o-dgm__legend-item">{mark}<span>{it.code && it.code !== lab ? <b className="mono">{it.code} </b> : null}{lab}</span></li>
      })}
    </ul>
  )
}
