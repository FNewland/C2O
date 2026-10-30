/**
 * BudgetGauge — compact margin indicator. Pure SVG.
 *
 * Shows a horizontal bar with used/allocated, color-coded by margin status.
 */

interface Props {
  label: string
  value: number
  allocation: number
  unit?: string
  width?: number
  height?: number
}

export function BudgetGauge({ label, value, allocation, unit = '', width = 120, height = 32 }: Props) {
  const margin = allocation > 0 ? ((allocation - value) / allocation) * 100 : 0
  const pct = allocation > 0 ? Math.min(100, (value / allocation) * 100) : 0
  const color = margin > 20 ? '#10b981' : margin > 0 ? '#f59e0b' : '#ef4444'

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      <text x={0} y={10} fill="#9ca3af" fontSize={8}>{label}</text>
      <text x={width} y={10} textAnchor="end" fill={color} fontSize={8} fontFamily="monospace" fontWeight={600}>
        {margin.toFixed(0)}%
      </text>
      <rect x={0} y={14} width={width} height={6} rx={3} fill="#1f2937" />
      <rect x={0} y={14} width={width * pct / 100} height={6} rx={3} fill={color} />
      <text x={0} y={28} fill="#6b7280" fontSize={7} fontFamily="monospace">
        {value.toFixed(1)}/{allocation.toFixed(1)} {unit}
      </text>
    </svg>
  )
}
