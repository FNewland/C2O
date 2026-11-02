/** Types for the shared pictorial modules (src/viz/*.js, generated from shared/ui-viz; plain JS, no .d.ts there). */
declare module '*/viz/derive.js' {
  export function qty(v: unknown, units?: string, meta?: Record<string, unknown>): any
  export function periodFromAltS(altKm: number): number
  export function eclipseFraction(altKm: number, betaDeg?: number): number
  export function betaCriticalDeg(altKm: number): number
}

interface VizView { update(model: unknown): void; destroy(): void }
type VizT = (en: string, vars?: Record<string, unknown>) => string

declare module '*/viz/overview.js' {
  export function mount(el: HTMLElement, opts: { t?: VizT; title?: string; onNavigate?: (subsystemId: string) => void }): VizView
}
declare module '*/viz/powerflow.js' {
  export function mount(el: HTMLElement, opts: { t?: VizT; variant?: 'full' | 'summary'; animate?: boolean; onNavigate?: (page: string) => void }): VizView
}
declare module '*/viz/attitude3d.js' {
  export function mount(el: HTMLElement, opts: { t?: VizT; geometry?: unknown; frame?: 'lvlh' | 'inertial'; height?: number; onFallback?: (reason: string) => void; preserveDrawingBuffer?: boolean }):
    VizView & { setGeometry(g: unknown): void; setFrame(f: 'lvlh' | 'inertial'): void; fallback?: boolean }
}
