/**
 * SVGBarChart — pure SVG bar chart. No recharts dependency.
 *
 * Supports vertical and horizontal orientation, custom colors, labels, tooltips.
 */
import { useState } from 'react'

interface BarData {
  label: string
  value: number
  color?: string
  secondary?: number  // optional second bar (e.g., generation vs demand)
  secondaryColor?: string
}

interface Props {
  data: BarData[]
  width?: number
  height?: number
  orientation?: 'vertical' | 'horizontal'
  unit?: string
  showValues?: boolean
  maxValue?: number
  title?: string
}

export function SVGBarChart({
  data, width = 400, height = 200, orientation = 'vertical',
  unit = '', showValues = true, maxValue, title,
}: Props) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null)

  if (!data.length) return null

  const max = maxValue || Math.max(...data.map(d => Math.max(d.value, d.secondary || 0)), 1)
  const padding = { top: title ? 25 : 10, right: 10, bottom: 30, left: orientation === 'horizontal' ? 80 : 35 }
  const chartW = width - padding.left - padding.right
  const chartH = height - padding.top - padding.bottom

  if (orientation === 'horizontal') {
    const barH = Math.min(20, chartH / data.length - 4)
    const gap = (chartH - barH * data.length) / Math.max(data.length - 1, 1)

    return (
      <svg width={width} height={height} style={{ display: 'block' }}>
        {title && <text x={width / 2} y={16} textAnchor="middle" fill="#d1d5db" fontSize={12} fontWeight={600}>{title}</text>}
        {data.map((d, i) => {
          const y = padding.top + i * (barH + gap)
          const barW = (d.value / max) * chartW
          const secW = d.secondary ? (d.secondary / max) * chartW : 0
          return (
            <g key={i} onMouseEnter={() => setHoveredIdx(i)} onMouseLeave={() => setHoveredIdx(null)}>
              <text x={padding.left - 4} y={y + barH / 2 + 4} textAnchor="end" fill="#9ca3af" fontSize={9}>{d.label}</text>
              {d.secondary !== undefined && (
                <rect x={padding.left} y={y} width={Math.max(secW, 1)} height={barH / 2} rx={2} fill={d.secondaryColor || '#374151'} opacity={0.5} />
              )}
              <rect x={padding.left} y={d.secondary !== undefined ? y + barH / 2 : y} width={Math.max(barW, 1)} height={d.secondary !== undefined ? barH / 2 : barH} rx={2} fill={d.color || '#3b82f6'} />
              {showValues && (
                <text x={padding.left + barW + 4} y={y + barH / 2 + 4} fill={hoveredIdx === i ? '#d1d5db' : '#6b7280'} fontSize={9} fontFamily="monospace">
                  {d.value.toFixed(1)}{unit}
                </text>
              )}
            </g>
          )
        })}
      </svg>
    )
  }

  // Vertical bars
  const barW = Math.min(30, chartW / data.length - 4)
  const gap = (chartW - barW * data.length) / Math.max(data.length - 1, 1)

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {title && <text x={width / 2} y={16} textAnchor="middle" fill="#d1d5db" fontSize={12} fontWeight={600}>{title}</text>}
      {/* Y-axis labels */}
      {[0, 0.5, 1].map(frac => (
        <g key={frac}>
          <line x1={padding.left} y1={padding.top + chartH * (1 - frac)} x2={padding.left + chartW} y2={padding.top + chartH * (1 - frac)} stroke="#374151" strokeWidth={0.5} />
          <text x={padding.left - 4} y={padding.top + chartH * (1 - frac) + 3} textAnchor="end" fill="#6b7280" fontSize={8}>{(max * frac).toFixed(0)}</text>
        </g>
      ))}
      {/* Bars */}
      {data.map((d, i) => {
        const x = padding.left + i * (barW + gap)
        const barH = (d.value / max) * chartH
        return (
          <g key={i} onMouseEnter={() => setHoveredIdx(i)} onMouseLeave={() => setHoveredIdx(null)}>
            <rect x={x} y={padding.top + chartH - barH} width={barW} height={barH} rx={2} fill={d.color || '#3b82f6'} opacity={hoveredIdx === i ? 1 : 0.85} />
            {showValues && hoveredIdx === i && (
              <text x={x + barW / 2} y={padding.top + chartH - barH - 4} textAnchor="middle" fill="#d1d5db" fontSize={9} fontFamily="monospace">
                {d.value.toFixed(1)}{unit}
              </text>
            )}
            <text x={x + barW / 2} y={height - 4} textAnchor="middle" fill="#9ca3af" fontSize={8}>{d.label}</text>
          </g>
        )
      })}
    </svg>
  )
}
