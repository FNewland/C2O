import { fs } from '../theme/tokens'
/**
 * SVGWaterfall — mass/power breakdown waterfall chart. Pure SVG.
 *
 * Shows per-subsystem values stacking toward a total, with allocation line.
 */

interface WaterfallItem {
  label: string
  value: number
  color?: string
}

interface Props {
  items: WaterfallItem[]
  allocation?: number
  unit?: string
  height?: number
  width?: number
  title?: string
}

export function SVGWaterfall({ items, allocation, unit = 'kg', height = 200, width = 400, title }: Props) {
  if (!items.length) return null

  const total = items.reduce((s, i) => s + i.value, 0)
  const max = Math.max(total * 1.2, allocation || 0) || 1
  const padding = { top: title ? 30 : 15, right: 10, bottom: 25, left: 45 }
  const chartW = width - padding.left - padding.right
  const chartH = height - padding.top - padding.bottom
  const barW = Math.min(28, chartW / (items.length + 1) - 4)
  const gap = (chartW - barW * (items.length + 1)) / Math.max(items.length, 1)

  let cumulative = 0

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {title && <text x={width / 2} y={18} textAnchor="middle" fill="var(--text)" fontSize={fs.label} fontWeight={600}>{title}</text>}

      {/* Grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map(frac => (
        <g key={frac}>
          <line x1={padding.left} y1={padding.top + chartH * (1 - frac)} x2={padding.left + chartW} y2={padding.top + chartH * (1 - frac)} stroke="var(--surface-2)" strokeWidth={0.5} />
          <text x={padding.left - 4} y={padding.top + chartH * (1 - frac) + 3} textAnchor="end" fill="var(--text-3)" fontSize={fs.label}>{(max * frac).toFixed(1)}</text>
        </g>
      ))}

      {/* Bars */}
      {items.filter(i => i.value > 0).map((item, idx) => {
        const x = padding.left + idx * (barW + gap)
        const barH = (item.value / max) * chartH
        const y = padding.top + chartH - (cumulative / max) * chartH - barH
        cumulative += item.value
        const color = item.color || ['var(--interactive)', 'var(--status-ok)', 'var(--interactive)', 'var(--status-caution)', 'var(--cat-2)', 'var(--cat-6)', 'var(--status-caution)', 'var(--cat-7)'][idx % 8]
        return (
          <g key={idx}>
            <rect x={x} y={y} width={barW} height={barH} rx={2} fill={color} opacity={0.85} />
            <text x={x + barW / 2} y={y - 3} textAnchor="middle" fill="var(--text-2)" fontSize={fs.label} fontFamily="monospace">
              {item.value.toFixed(1)}
            </text>
            <text x={x + barW / 2} y={height - 4} textAnchor="middle" fill="var(--text-2)" fontSize={fs.label}>
              {item.label.length > 6 ? item.label.slice(0, 5) + '.' : item.label}
            </text>
          </g>
        )
      })}

      {/* Total bar */}
      {(() => {
        const x = padding.left + items.filter(i => i.value > 0).length * (barW + gap)
        const barH = (total / max) * chartH
        const y = padding.top + chartH - barH
        const color = allocation && total > allocation ? 'var(--status-alarm)' : 'var(--status-ok)'
        return (
          <g>
            <rect x={x} y={y} width={barW} height={barH} rx={2} fill={color} opacity={0.9} />
            <text x={x + barW / 2} y={y - 3} textAnchor="middle" fill={color} fontSize={fs.label} fontWeight={700} fontFamily="monospace">
              {total.toFixed(1)} {unit}
            </text>
            <text x={x + barW / 2} y={height - 4} textAnchor="middle" fill="var(--text)" fontSize={fs.label} fontWeight={600}>Total</text>
          </g>
        )
      })()}

      {/* Allocation line */}
      {allocation && allocation > 0 && (
        <g>
          <line x1={padding.left} y1={padding.top + chartH - (allocation / max) * chartH} x2={padding.left + chartW} y2={padding.top + chartH - (allocation / max) * chartH} stroke="var(--status-alarm)" strokeWidth={1.5} strokeDasharray="4 2" />
          <text x={padding.left + chartW + 2} y={padding.top + chartH - (allocation / max) * chartH + 3} fill="var(--status-alarm)" fontSize={fs.label} fontFamily="monospace">
            {allocation.toFixed(1)} {unit}
          </text>
        </g>
      )}
    </svg>
  )
}
