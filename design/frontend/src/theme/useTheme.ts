/**
 * Theme: SpaceCDF defaults to the light (design-work) theme. `?theme=dark`
 * or localStorage 'c2o.theme' switches to the control-room ramp; the value is
 * written to <html data-theme> so tokens.css and React Flow agree.
 */
import { useSyncExternalStore } from 'react'

export type Theme = 'light' | 'dark'
const KEY = 'c2o.theme'

function initial(): Theme {
  try {
    const q = new URLSearchParams(window.location.search).get('theme')
    if (q === 'dark' || q === 'light') { localStorage.setItem(KEY, q); return q }
    const v = localStorage.getItem(KEY)
    if (v === 'dark' || v === 'light') return v
  } catch { /* no storage */ }
  return 'light'
}

let current: Theme = typeof window === 'undefined' ? 'light' : initial()
const listeners = new Set<() => void>()
if (typeof document !== 'undefined') document.documentElement.dataset.theme = current

export function setTheme(t: Theme): void {
  current = t
  document.documentElement.dataset.theme = t
  try { localStorage.setItem(KEY, t) } catch { /* private mode */ }
  listeners.forEach(l => l())
}

export function useTheme(): Theme {
  return useSyncExternalStore(cb => { listeners.add(cb); return () => { listeners.delete(cb) } }, () => current)
}
