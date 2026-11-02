/**
 * InterfaceGlyph — the per-type mark used on diagram edges, in the legend
 * and in every list row. Shapes stay distinct in greyscale, so the type is
 * never carried by colour alone (PRINCIPLES P6). Schematic symbols, not
 * decoration: bolt = power, two arrows = data, antenna = RF, hexagon nut =
 * mechanical, heat waves = thermal, clock = timing, lens = optical,
 * drop = fluid, square wave = discrete signal.
 */
import type { InterfaceType } from '../types/interfaces'
import { TYPE_META } from '../types/interfaces'

const PATHS: Record<InterfaceType, { d: string; fill?: boolean }> = {
  power: { d: 'M7.2 .8 2.4 7h3.4L4.8 11.2 9.6 5H6.2Z', fill: true },
  data: { d: 'M1 3.8h8.6M7 1.2l2.6 2.6L7 6.4M11 8.2H2.4M5 5.6 2.4 8.2 5 10.8' },
  rf: { d: 'M6 11.4V4.6M1.6 1.2 6 4.6l4.4-3.4M3.6 2.8 6 4.6l2.4-1.8' },
  mechanical: { d: 'M6 .9 10.4 3.4v5.1L6 11.1 1.6 8.5V3.4ZM6 4.3a1.8 1.8 0 1 0 0 3.6 1.8 1.8 0 1 0 0-3.6' },
  thermal: { d: 'M3 11c-1.6-2 1.6-3.4 0-5.4S3 2.4 3 1M6.2 11c-1.6-2 1.6-3.4 0-5.4s0-3.2 0-4.6M9.4 11c-1.6-2 1.6-3.4 0-5.4s0-3.2 0-4.6' },
  timing: { d: 'M6 1.2a4.8 4.8 0 1 0 0 9.6 4.8 4.8 0 1 0 0-9.6M6 3.2V6l2 1.4' },
  optical: { d: 'M.8 6Q6 .4 11.2 6 6 11.6.8 6ZM6 4.3a1.7 1.7 0 1 0 0 3.4 1.7 1.7 0 1 0 0-3.4' },
  fluid: { d: 'M6 .9C4.6 3 2.4 5.4 2.4 7.6a3.6 3.6 0 0 0 7.2 0C9.6 5.4 7.4 3 6 .9Z', fill: true },
  electrical_signal: { d: 'M.8 9.4h2.6V2.6h4.2v6.8h3.6' },
}

export function InterfaceGlyph({ type, size = 12, color, className }: {
  type: InterfaceType; size?: number; color?: string; className?: string
}) {
  const p = PATHS[type]
  const c = color ?? TYPE_META[type].color
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 12 12" aria-hidden="true" focusable="false"
      style={{ flex: 'none', overflow: 'visible' }}>
      <path d={p.d} fill={p.fill ? c : 'none'} stroke={c} strokeWidth={p.fill ? 0.6 : 1.3}
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
