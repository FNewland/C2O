/**
 * SVGLineChart — pure SVG multi-series line chart (shared, SCDF-173).
 *
 * Axes with ticks, legend, optional vertical bands (e.g. operational mode
 * per time span) and a hover read-out. No chart library.
 *
 *   <SVGLineChart
 *     series={[{ name: 'SoC', color: 'var(--interactive)', points: [[0, 80], [30, 78]] }]}
 *     bands={[{ from: 0, to: 600, label: 'Downlink', color: 'var(--status-caution)' }]}
 *     xLabel="time [h]" yLabel="SoC [%]" height={200} />
 */
import { useMemo, useState } from 'react'
import { fs } from '../theme/tokens'

export interface LineSeries {
  name: string
  color: string
  points: [number, number][]   // [x, y]
  dashed?: boolean
  width?: number
}

export interface Band {
  from: number
  to: number
  label: string
  color: string
}

export interface ReferenceLine {
  y: number
  label?: string
  color?: string
}

interface Props {
  series: LineSeries[]
  bands?: Band[]
  refLines?: ReferenceLine[]
  xLabel?: string
  yLabel?: string
  title?: string
  width?: number
  height?: number
  yMin?: number
  yMax?: number
  xFormat?: (x: number) => string
  yFormat?: (y: number) => string
  showLegend?: boolean
}

function niceTicks(min: number, max: number, count = 5): number[] {
  if (!(max > min)) return [min]
  const raw = (max - min) / count
  const mag = Math.pow(10, Math.floor(Math.log10(raw)))
  const norm = raw / mag
  const step = (norm >= 5 ? 5 : norm >= 2 ? 2 : 1) * mag
  const start = Math.ceil(min / step) * step
  const out: number[] = []
  for (let v = start; v <= max + 1e-9; v += step) out.push(Number(v.toFixed(10)))
  return out
}

const defaultFmt = (v: number) => {
  const a = Math.abs(v)
  if (a !== 0 && (a < 1e-3 || a >= 1e6)) return v.toExponential(1)
  return Number.isInteger(v) ? String(v) : v.toFixed(a < 10 ? 2 : 1).replace(/\.?0+$/, '')
}

export function SVGLineChart({
  series, bands = [], refLines = [], xLabel, yLabel, title, width = 560, height = 200,
  yMin, yMax, xFormat = defaultFmt, yFormat = defaultFmt, showLegend = true,
}: Props) {
  const [hoverX, setHoverX] = useState<number | null>(null)

  const pad = { top: title ? 24 : 10, right: 12, bottom: xLabel ? 34 : 22, left: yLabel ? 48 : 40 }
  const legendH = showLegend && series.length > 0 ? 14 : 0
  const cw = width - pad.left - pad.right
  const ch = height - pad.top - pad.bottom - legendH

  const { x0, x1, y0, y1 } = useMemo(() => {
    let xa = Infinity, xb = -Infinity, ya = Infinity, yb = -Infinity
    for (const s of series) for (const [x, y] of s.points) {
      if (Number.isFinite(x)) { xa = Math.min(xa, x); xb = Math.max(xb, x) }
      if (Number.isFinite(y)) { ya = Math.min(ya, y); yb = Math.max(yb, y) }
    }
    for (const r of refLines) { ya = Math.min(ya, r.y); yb = Math.max(yb, r.y) }
    if (!Number.isFinite(xa)) { xa = 0; xb = 1 }
    if (!Number.isFinite(ya)) { ya = 0; yb = 1 }
    if (xb === xa) xb = xa + 1
    if (yb === ya) { ya -= 1; yb += 1 }
    const padY = (yb - ya) * 0.05
    return {
      x0: xa, x1: xb,
      y0: yMin !== undefined ? yMin : ya - padY,
      y1: yMax !== undefined ? yMax : yb + padY,
    }
  }, [series, refLines, yMin, yMax])

  if (!series.length) return null

  const sx = (x: number) => pad.left + ((x - x0) / (x1 - x0)) * cw
  const sy = (y: number) => pad.top + ch - ((y - y0) / (y1 - y0)) * ch
  const xTicks = niceTicks(x0, x1, 6)
  const yTicks = niceTicks(y0, y1, 4)

  // merge adjacent bands with the same label so the legend/labels stay readable
  const mergedBands = useMemo(() => {
    const out: Band[] = []
    for (const b of bands) {
      const last = out[out.length - 1]
      if (last && last.label === b.label && last.color === b.color && Math.abs(last.to - b.from) < 1e-9) last.to = b.to
      else out.push({ ...b })
    }
    return out
  }, [bands])
  const bandLegend = useMemo(() => {
    const seen = new Map<string, string>()
    for (const b of mergedBands) if (!seen.has(b.label)) seen.set(b.label, b.color)
    return [...seen.entries()]
  }, [mergedBands])

  const path = (s: LineSeries) => {
    let d = ''
    let pen = false
    for (const [x, y] of s.points) {
      if (!Number.isFinite(x) || !Number.isFinite(y)) { pen = false; continue }
      d += `${pen ? 'L' : 'M'}${sx(x).toFixed(1)},${sy(y).toFixed(1)}`
      pen = true
    }
    return d
  }

  // hover read-out: nearest point per series
  const readout = hoverX === null ? null : series.map(s => {
    let best: [number, number] | null = null
    let bd = Infinity
    for (const p of s.points) { const d = Math.abs(p[0] - hoverX); if (d < bd) { bd = d; best = p } }
    return { name: s.name, color: s.color, p: best }
  })
  const hoverBand = hoverX === null ? null : mergedBands.find(b => hoverX >= b.from && hoverX <= b.to)

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const px = (e.clientX - rect.left) * (width / rect.width)
    if (px < pad.left || px > pad.left + cw) { setHoverX(null); return }
    setHoverX(x0 + ((px - pad.left) / cw) * (x1 - x0))
  }

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none"
         style={{ display: 'block', maxWidth: width, height }} onMouseMove={onMove} onMouseLeave={() => setHoverX(null)}>
      {title && <text x={pad.left} y={14} fill="var(--text-primary, var(--text))" fontSize={fs.label} fontWeight={600}>{title}</text>}
      <clipPath id={`clip-${title || xLabel || 'c'}-${width}-${height}`}>
        <rect x={pad.left} y={pad.top} width={cw} height={ch} />
      </clipPath>
      {/* bands */}
      {mergedBands.map((b, i) => {
        const xa = Math.max(sx(b.from), pad.left), xb = Math.min(sx(b.to), pad.left + cw)
        if (xb <= xa) return null
        return <rect key={i} x={xa} y={pad.top} width={xb - xa} height={ch} fill={b.color} opacity={0.12}><title>{b.label}</title></rect>
      })}
      {/* grid + axes */}
      {yTicks.map(t => (
        <g key={`y${t}`}>
          <line x1={pad.left} x2={pad.left + cw} y1={sy(t)} y2={sy(t)} stroke="var(--border, var(--line))" strokeWidth={0.5} />
          <text x={pad.left - 4} y={sy(t) + 3} textAnchor="end" fill="var(--text-secondary, var(--text-2))" fontSize={fs.label}>{yFormat(t)}</text>
        </g>
      ))}
      {xTicks.map(t => (
        <g key={`x${t}`}>
          <line x1={sx(t)} x2={sx(t)} y1={pad.top + ch} y2={pad.top + ch + 3} stroke="var(--text-secondary, var(--text-2))" strokeWidth={0.5} />
          <text x={sx(t)} y={pad.top + ch + 12} textAnchor="middle" fill="var(--text-secondary, var(--text-2))" fontSize={fs.label}>{xFormat(t)}</text>
        </g>
      ))}
      <line x1={pad.left} x2={pad.left} y1={pad.top} y2={pad.top + ch} stroke="var(--text-secondary, var(--text-3))" strokeWidth={0.8} />
      <line x1={pad.left} x2={pad.left + cw} y1={pad.top + ch} y2={pad.top + ch} stroke="var(--text-secondary, var(--text-3))" strokeWidth={0.8} />
      {xLabel && <text x={pad.left + cw / 2} y={height - legendH - 4} textAnchor="middle" fill="var(--text-secondary, var(--text-2))" fontSize={fs.label}>{xLabel}</text>}
      {yLabel && (
        <text x={10} y={pad.top + ch / 2} textAnchor="middle" fill="var(--text-secondary, var(--text-2))" fontSize={fs.label}
              transform={`rotate(-90 10 ${pad.top + ch / 2})`}>{yLabel}</text>
      )}
      {/* reference lines */}
      {refLines.map((r, i) => (
        <g key={`r${i}`}>
          <line x1={pad.left} x2={pad.left + cw} y1={sy(r.y)} y2={sy(r.y)} stroke={r.color || 'var(--status-alarm)'} strokeWidth={0.8} strokeDasharray="4 3" />
          {r.label && <text x={pad.left + cw - 2} y={sy(r.y) - 2} textAnchor="end" fill={r.color || 'var(--status-alarm)'} fontSize={fs.label}>{r.label}</text>}
        </g>
      ))}
      {/* series */}
      {series.map(s => (
        <path key={s.name} d={path(s)} fill="none" stroke={s.color} strokeWidth={s.width ?? 1.4}
              strokeDasharray={s.dashed ? '5 3' : undefined} strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      ))}
      {/* hover */}
      {hoverX !== null && readout && (
        <g pointerEvents="none">
          <line x1={sx(hoverX)} x2={sx(hoverX)} y1={pad.top} y2={pad.top + ch} stroke="var(--text-secondary, var(--text-2))" strokeWidth={0.6} strokeDasharray="2 2" />
          {readout.map(r => r.p && <circle key={r.name} cx={sx(r.p[0])} cy={sy(r.p[1])} r={2.5} fill={r.color} />)}
          <g transform={`translate(${Math.min(sx(hoverX) + 6, pad.left + cw - 130)}, ${pad.top + 4})`}>
            <rect width={126} height={12 + 11 * (readout.length + (hoverBand ? 1 : 0))} rx={3} fill="var(--bg-primary, var(--surface-1))" opacity={0.92} stroke="var(--border, var(--line))" strokeWidth={0.5} />
            <text x={4} y={10} fill="var(--text-secondary, var(--text-2))" fontSize={fs.label}>{xLabel ? `${xFormat(hoverX)} ${xLabel}` : xFormat(hoverX)}</text>
            {hoverBand && <text x={4} y={21} fill={hoverBand.color} fontSize={fs.label}>{hoverBand.label}</text>}
            {readout.map((r, i) => (
              <text key={r.name} x={4} y={21 + 11 * (i + (hoverBand ? 1 : 0))} fill={r.color} fontSize={fs.label} fontFamily="ui-monospace, monospace">
                {r.name}: {r.p ? yFormat(r.p[1]) : '—'}
              </text>
            ))}
          </g>
        </g>
      )}
      {/* legend */}
      {showLegend && (
        <g transform={`translate(${pad.left}, ${height - 4})`}>
          {[...series.map(s => ({ label: s.name, color: s.color, line: true })),
            ...bandLegend.map(([label, color]) => ({ label, color, line: false }))].map((it, i, arr) => {
            const x = arr.slice(0, i).reduce((acc, p) => acc + p.label.length * 5.2 + 22, 0)
            return (
              <g key={`${it.label}-${i}`} transform={`translate(${x}, 0)`}>
                {it.line
                  ? <line x1={0} x2={12} y1={-3} y2={-3} stroke={it.color} strokeWidth={2} />
                  : <rect x={0} y={-8} width={12} height={8} fill={it.color} opacity={0.35} />}
                <text x={15} y={0} fill="var(--text-secondary, var(--text-2))" fontSize={fs.label}>{it.label}</text>
              </g>
            )
          })}
        </g>
      )}
    </svg>
  )
}
