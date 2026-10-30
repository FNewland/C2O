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
      {title && <text x={width / 2} y={18} textAnchor="middle" fill="#d1d5db" fontSize={12} fontWeight={600}>{title}</text>}

      {/* Grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map(frac => (
        <g key={frac}>
          <line x1={padding.left} y1={padding.top + chartH * (1 - frac)} x2={padding.left + chartW} y2={padding.top + chartH * (1 - frac)} stroke="#1f2937" strokeWidth={0.5} />
          <text x={padding.left - 4} y={padding.top + chartH * (1 - frac) + 3} textAnchor="end" fill="#6b7280" fontSize={7}>{(max * frac).toFixed(1)}</text>
        </g>
      ))}

      {/* Bars */}
      {items.filter(i => i.value > 0).map((item, idx) => {
        const x = padding.left + idx * (barW + gap)
        const barH = (item.value / max) * chartH
        const y = padding.top + chartH - (cumulative / max) * chartH - barH
        cumulative += item.value
        const color = item.color || ['#3b82f6', '#10b981', '#06b6d4', '#f59e0b', '#8b5cf6', '#ec4899', '#f97316', '#84cc16'][idx % 8]
        return (
          <g key={idx}>
            <rect x={x} y={y} width={barW} height={barH} rx={2} fill={color} opacity={0.85} />
            <text x={x + barW / 2} y={y - 3} textAnchor="middle" fill="#9ca3af" fontSize={7} fontFamily="monospace">
              {item.value.toFixed(1)}
            </text>
            <text x={x + barW / 2} y={height - 4} textAnchor="middle" fill="#9ca3af" fontSize={7}>
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
        const color = allocation && total > allocation ? '#ef4444' : '#10b981'
        return (
          <g>
            <rect x={x} y={y} width={barW} height={barH} rx={2} fill={color} opacity={0.9} />
            <text x={x + barW / 2} y={y - 3} textAnchor="middle" fill={color} fontSize={8} fontWeight={700} fontFamily="monospace">
              {total.toFixed(1)} {unit}
            </text>
            <text x={x + barW / 2} y={height - 4} textAnchor="middle" fill="#d1d5db" fontSize={7} fontWeight={600}>Total</text>
          </g>
        )
      })()}

      {/* Allocation line */}
      {allocation && allocation > 0 && (
        <g>
          <line x1={padding.left} y1={padding.top + chartH - (allocation / max) * chartH} x2={padding.left + chartW} y2={padding.top + chartH - (allocation / max) * chartH} stroke="#ef4444" strokeWidth={1.5} strokeDasharray="4 2" />
          <text x={padding.left + chartW + 2} y={padding.top + chartH - (allocation / max) * chartH + 3} fill="#ef4444" fontSize={8} fontFamily="monospace">
            {allocation.toFixed(1)} {unit}
          </text>
        </g>
      )}
    </svg>
  )
}
